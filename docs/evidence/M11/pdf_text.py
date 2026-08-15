"""Minimal PDF text extractor for the M11 deliverable audit.

Why this exists: both PDFs draw every glyph with hex strings against subset fonts
(5 846 and 19 430 text-showing operators, zero literal strings). A naive extractor
that only reads `(literal)` strings returns nothing at all - and then every
"no raw markup on the page" check passes vacuously, which is worse than no check.

So the codes are decoded properly, through each font's /ToUnicode CMap, with the
font tracked per content stream via the page's /Resources. No third-party
dependency: adding one would move pins in the validated environment.
"""

from __future__ import annotations

import bisect
import re
import zlib

OBJ_START = re.compile(rb"(?:^|[\r\n>\s])(\d+)\s+(\d+)\s+obj\b")

# One flat alternation over the operators that matter, so no group can backtrack
# into another. Every hex string in a text object is a glyph run; T*/Td/TD/ET are
# position breaks and become a space.
TEXT_OP = re.compile(
    rb"/([A-Za-z0-9]+)\s+[\d.-]+\s+Tf"      # 1: font selection
    rb"|<([0-9A-Fa-f\s]*)>"                 # 2: a hex glyph run
    rb"|\bT\*|\bTd\b|\bTD\b|\bET\b"         # 3: a break
)


def _objects(raw: bytes) -> dict[int, bytes]:
    """Map object number -> object body, in one linear pass.

    A lazy `(.*?)endobj` regex is quadratic here: `\\d+ \\d+ obj` matches at many
    incidental offsets inside the compressed image data, and every false start
    then scans forward to the next `endobj`. Pairing pre-computed start and end
    offsets instead keeps this linear.
    """
    ends = [m.start() for m in re.finditer(rb"endobj", raw)]
    objs: dict[int, bytes] = {}
    for m in OBJ_START.finditer(raw):
        start = m.end()
        i = bisect.bisect_left(ends, start)
        if i < len(ends):
            objs[int(m.group(1))] = raw[start:ends[i]]
    return objs


def _stream_of(body: bytes) -> bytes | None:
    m = re.search(rb"stream\r?\n", body)
    if not m:
        return None
    end = body.rfind(b"endstream")
    if end == -1:
        return None
    data = body[m.end():end]
    if b"/FlateDecode" in body[:m.start()]:
        try:
            return zlib.decompress(data)
        except zlib.error:
            try:
                return zlib.decompressobj().decompress(data)
            except zlib.error:
                return None
    return data


def _resolve(objs: dict[int, bytes], token: bytes) -> bytes:
    """Follow `N 0 R` one level; otherwise return the token unchanged."""
    m = re.fullmatch(rb"\s*(\d+)\s+\d+\s+R\s*", token)
    return objs.get(int(m.group(1)), b"") if m else token


def _value_after(body: bytes, key: bytes) -> bytes:
    """The value of `key` in a PDF dictionary, with nesting handled.

    A lazy `<<.*?>>` is wrong here and silently so: `/Resources <</ExtGState <<…>>
    /Font <<…>>>>` closes on the ExtGState's `>>`, so the font dictionary is never
    reached and every page decodes to nothing. Delimiters are counted instead.
    """
    i = body.find(key)
    if i == -1:
        return b""
    j = i + len(key)
    while j < len(body) and body[j:j + 1].isspace():
        j += 1
    if body[j:j + 2] == b"<<":
        depth, k = 0, j
        while k < len(body) - 1:
            pair = body[k:k + 2]
            if pair == b"<<":
                depth += 1
                k += 2
            elif pair == b">>":
                depth -= 1
                k += 2
                if depth == 0:
                    return body[j:k]
            else:
                k += 1
        return body[j:]
    m = re.match(rb"\s*(\d+\s+\d+\s+R|\[[^\]]*\])", body[i + len(key):])
    return m.group(1) if m else b""


def _tounicode(cmap: bytes) -> dict[bytes, str]:
    """Parse bfchar and bfrange sections of a ToUnicode CMap."""
    out: dict[bytes, str] = {}

    def utf16(h: bytes) -> str:
        try:
            return bytes.fromhex(h.decode("ascii")).decode("utf-16-be", errors="replace")
        except ValueError:
            return ""

    for block in re.findall(rb"beginbfchar(.*?)endbfchar", cmap, re.S):
        for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            out[bytes.fromhex(src.decode())] = utf16(dst)

    for block in re.findall(rb"beginbfrange(.*?)endbfrange", cmap, re.S):
        # <lo> <hi> <dstStart>
        for lo, hi, dst in re.findall(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block
        ):
            width = len(lo) // 2
            start, end = int(lo, 16), int(hi, 16)
            base = int(dst, 16)
            for i in range(min(end - start + 1, 65536)):
                out[(start + i).to_bytes(width, "big")] = chr(base + i) if base + i < 0x110000 else ""
        # <lo> <hi> [ <d1> <d2> ... ]
        for lo, hi, arr in re.findall(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", block, re.S
        ):
            width = len(lo) // 2
            start = int(lo, 16)
            for i, d in enumerate(re.findall(rb"<([0-9A-Fa-f]+)>", arr)):
                out[(start + i).to_bytes(width, "big")] = utf16(d)
    return out


def _font_maps(objs: dict[int, bytes], resources: bytes,
               cache: dict[int, dict[bytes, str]]) -> dict[bytes, dict[bytes, str]]:
    """name -> code->unicode, for every font in a /Resources dictionary.

    `cache` is keyed by ToUnicode object number: the same CMap is referenced by
    every page that uses the font, and parsing it once per page made this
    unusably slow on a 91-page document.
    """
    maps: dict[bytes, dict[bytes, str]] = {}
    raw_font = _value_after(resources, b"/Font")
    if not raw_font:
        return maps
    fdict = _resolve(objs, raw_font)
    for name, num in re.findall(rb"/([A-Za-z0-9]+)\s+(\d+)\s+\d+\s+R", fdict):
        body = objs.get(int(num), b"")
        tu = re.search(rb"/ToUnicode\s+(\d+)\s+\d+\s+R", body)
        if not tu:
            # A Type0 font may carry it on the descendant; try one hop.
            desc = re.search(rb"/DescendantFonts\s*\[\s*(\d+)\s+\d+\s+R", body)
            if desc:
                body2 = objs.get(int(desc.group(1)), b"")
                tu = re.search(rb"/ToUnicode\s+(\d+)\s+\d+\s+R", body2)
        if not tu:
            continue
        ref = int(tu.group(1))
        if ref not in cache:
            cm = _stream_of(objs.get(ref, b""))
            cache[ref] = _tounicode(cm) if cm else {}
        maps[name] = cache[ref]
    return maps


def _decode_run(chunk: bytes, cmap: dict[bytes, str], width: int) -> str:
    out = []
    for hexs in re.findall(rb"<([0-9A-Fa-f\s]*)>", chunk):
        h = re.sub(rb"\s", b"", hexs)
        try:
            data = bytes.fromhex(h.decode("ascii"))
        except ValueError:
            continue
        for i in range(0, len(data) - width + 1, width):
            out.append(cmap.get(data[i:i + width], ""))
    return "".join(out)


def page_texts(raw: bytes) -> list[str]:
    """Return the decoded visible text of each page, in page order."""
    objs = _objects(raw)
    pages: list[str] = []
    cmap_cache: dict[int, dict[bytes, str]] = {}

    for num, body in objs.items():
        if not re.search(rb"/Type\s*/Page\b(?!s)", body):
            continue

        resources = _resolve(objs, _value_after(body, b"/Resources"))
        fmaps = _font_maps(objs, resources, cmap_cache)

        # Contents: a single ref or an array of refs.
        cont_nums: list[int] = []
        cm = re.search(rb"/Contents\s*(\d+)\s+\d+\s+R", body)
        if cm:
            cont_nums.append(int(cm.group(1)))
        else:
            ca = re.search(rb"/Contents\s*\[(.*?)\]", body, re.S)
            if ca:
                cont_nums += [int(n) for n in re.findall(rb"(\d+)\s+\d+\s+R", ca.group(1))]

        stream = b"".join(_stream_of(objs.get(n, b"")) or b"" for n in cont_nums)

        # Walk text-showing operators, tracking the selected font.
        text: list[str] = []
        active: dict[bytes, str] = {}
        width = 1
        for m in TEXT_OP.finditer(stream):
            if m.group(1) is not None:            # /Fn <size> Tf
                active = fmaps.get(m.group(1), {})
                keys = [k for k in active if k]
                width = len(keys[0]) if keys else 1
            elif m.group(2) is not None:          # <hex> string, inside TJ or before Tj
                text.append(_decode_run(b"<" + m.group(2) + b">", active, width))
            else:                                 # T*, Td, TD, ET - a break
                text.append(" ")

        pages.append("".join(text))

    return pages
