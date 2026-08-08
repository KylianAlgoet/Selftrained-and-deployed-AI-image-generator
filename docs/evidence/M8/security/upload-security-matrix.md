# Upload security — rule, test, result

**Date:** 2026-08-09 · **Milestone:** M8 (phase M8.2) · **All tests pass.**
**Suites:** `apps/api/tests/test_uploads.py` (46), `apps/api/tests/test_env_example.py` (5),
`apps/web/src/generate/GenerateForm.test.tsx` (preflight block).

The three acceptance criteria named in issue #9 — **malicious filename**, **oversize file**,
**wrong MIME** — were already met by M7 and are marked as such below rather than re-evidenced.
M8 closed the narrower gaps around them.

## The mechanism being tested

`apps/api/uploads.py` validates in a deliberate order: cheap checks reject obvious junk, but
**the decode is what decides**. An extension and a `Content-Type` header are both
attacker-controlled strings; the only trustworthy statement about a byte stream is what a decoder
reports when it reads it.

The filename is **never** sanitised for reuse, because it is never reused. It is read for its
extension with a single `rpartition(".")` and discarded. Nothing user-supplied is written to disk
by this service at any point.

## Matrix

| # | rule | attack it stops | test | added | result |
|---:|---|---|---|---|---|
| 1 | non-empty body | empty POST | `test_empty_upload_is_rejected` | M7 | PASS |
| 2 | byte limit before decode | **oversize file** (criterion) | `test_oversize_upload_is_rejected_before_decoding` | M7 | PASS |
| 3 | extension allowlist | `.svg`, `.exe` payloads | `test_disallowed_extension_is_rejected`, `test_executable_extension_is_rejected` | M7 | PASS |
| 4 | content-type agreement | **wrong MIME** (criterion) | `test_content_type_disagreeing_with_extension_is_rejected` | M7 | PASS |
| 5 | decode `verify()` | corrupt stream | `test_bytes_that_are_not_an_image_are_rejected` | M7 | PASS |
| 6 | truncation detection | half-written PNG | `test_a_truncated_png_is_rejected` | M7 | PASS |
| 7 | decoded-format allowlist | GIF renamed `.png` | `test_a_gif_renamed_to_png_is_rejected_on_its_contents` | M7 | PASS |
| 8 | dimension cap (4096) | huge real image | `test_an_image_wider_than_the_cap_is_rejected` | M7 | PASS |
| 9 | total-pixel cap | **decompression bomb** | `test_a_decompression_bomb_header_is_rejected` | M7 | PASS |
| 10 | filename is a label | **malicious filename** (criterion) | `test_a_traversal_filename_cannot_reach_the_filesystem` | M7 | PASS |
| 11 | **no filesystem access at all** | any filename-borne attack | `test_a_hostile_filename_never_reaches_the_filesystem` (12 cases) | **M8** | PASS |
| 12 | guard sensitivity | a guard that cannot fail | `test_the_no_filesystem_guard_is_actually_sensitive` | **M8** | PASS |
| 13 | no extension | `passwd` with no dot | `test_a_filename_with_no_extension_is_rejected` | **M8** | PASS |
| 14 | absent filename | `None` filename | `test_a_missing_filename_is_rejected_by_the_extension_rule` | **M8** | PASS |
| 15 | case-insensitive extension | valid `.PNG` wrongly refused | `test_uppercase_and_mixed_case_extensions_are_accepted` (4) | **M8** | PASS |
| 16 | last-extension semantics | `decal.png.exe` | `test_only_the_last_extension_decides` | **M8** | PASS |
| 17 | content-type normalisation | `image/png; charset=…` | `test_a_content_type_with_parameters_or_casing_is_normalised` (4) | **M8** | PASS |
| 18 | WEBP accepted | third format never positively tested | `test_a_valid_webp_is_accepted` | **M8** | PASS |
| 19 | absent content-type | header stripped by a proxy | `test_an_absent_content_type_falls_through_to_the_decode` | **M8** | PASS |
| 20 | temp storage released | leak on the rejection path | `test_the_upload_is_closed_on_every_path` (AST) | **M8** | PASS |
| 21 | filename not echoed | reflected-name disclosure | `test_the_users_filename_never_appears_in_the_response_or_on_disk` | **M8** | PASS |
| 22 | no name collision | overwrite by repeat name | `test_two_uploads_with_the_same_filename_do_not_collide` | **M8** | PASS |
| 23 | output isolation | write outside the output dir | `test_a_generation_is_written_only_inside_the_configured_output_dir` | **M8** | PASS |
| 24 | id is a registry key | path traversal in `/api/generated/{id}` | `test_a_generation_id_is_a_registry_key_not_a_path`, `test_malformed_generation_ids_are_rejected` (5) | M7 | PASS |
| 25 | safe error messages | path/stack-trace leakage | `test_metadata_never_exposes_a_filesystem_path`, `test_missing_checkpoint_is_503_and_says_nothing_about_paths` | M7 | PASS |
| 26 | settings file is truthful | configuring rules that do not exist | `test_env_example.py` (5 tests) | **M8** | PASS |
| 27 | client preflight | wrong type / size before upload | `preflightReference` block, 7 tests (3 M7 + 4 M8) | **M8** | PASS |

### The 12 hostile filenames in row 11

POSIX traversal · Windows traversal (`..\..\..\windows\win.ini.png`) · absolute Windows path ·
absolute POSIX path · UNC path (`\\server\share\…`) · a name resembling a production checkpoint
path · embedded null byte · CR/LF control characters · RTL-override (U+202E) · emoji and CJK ·
300-character name · extension-only (`.png`).

## What row 11 actually proves, and why it replaced a weaker claim

The M7 traversal test asserted that a temporary directory stayed empty. That shows nothing landed
in **one** directory — it does not show the filename could not act somewhere else.

The M8 test patches `builtins.open`, `Path.open`, `Path.write_bytes` and `Path.mkdir` to raise, then
runs every hostile name through validation. Any filesystem access at all fails the test. Rejection
is also a pass: what matters is that no name reaches an OS call by either route.

Row 12 exists because **a guard that cannot fail is not evidence.** It asserts the patched
environment really does raise, following the same companion-assertion pattern the frozen-kit hash
locks use.

## Row 20 is structural on purpose

The endpoint closes the upload in a `finally`, so a rejected upload releases its temporary storage
exactly like an accepted one. No HTTP-level test can observe that — Starlette owns the
`SpooledTemporaryFile`. The test therefore parses `main.py` with `ast`, locates the single `try`
whose handler catches `UploadRejected`, and asserts its `finalbody` contains a `.close()` call.
This follows the existing AST import-boundary precedent. A future edit moving the close into the
success branch would leak a temp file on every rejection while every other test still passed.

## Findings

**No defect was found.** All 35 new backend assertions passed on first run against the existing
implementation, which is a result worth stating plainly: the M7 upload path was already correct
under conditions it had not been tested against.

**One real documentation defect was found and fixed** (row 26). `.env.example` advertised
`MODEL_CACHE_DIR`, `BASE_MODEL_ID`, `LORA_WEIGHTS_PATH`, `ALLOWED_UPLOAD_EXTENSIONS` and
`UPLOAD_TMP_DIR` — **none of which any code reads.** Two are actively misleading in a security
context: they imply the upload extension allowlist and a temporary upload directory are
configurable. The allowlist is frozen in `uploads.py` on purpose, and there is no temporary upload
directory because nothing user-supplied is written to disk. The file now documents only real keys,
and a pytest derives the permitted set from `config.py` by AST so it cannot drift again.

## Deliberately not tested, and why

- **Antivirus / content scanning of accepted images.** Out of scope for a local single-user
  research application, and claiming it without implementing it would be worse than its absence.
- **Rate limiting.** The single-flight lock already refuses concurrent work with 409; the service
  binds to `127.0.0.1` and is not exposed.
- **Filename sanitisation.** Deliberately absent. Sanitising a name implies it will be reused;
  it is not, and row 11 is the evidence.

## Suite totals after M8.2

| suite | before | after |
|---|---:|---:|
| pytest | 406 | **441** |
| vitest | 165 | **169** |
