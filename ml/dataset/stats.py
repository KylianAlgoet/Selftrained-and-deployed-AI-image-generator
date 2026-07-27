"""Dataset statistics: per-style counts, licences, resolutions, splits."""

from collections import Counter


def compute_stats(rows: list[dict[str, str]]) -> dict:
    styles = Counter(row["style"] for row in rows)
    licences = Counter(row["licence"] for row in rows)
    splits = Counter(row["split"] for row in rows)
    sources = Counter(row["source"].split("/")[2] if "://" in row["source"] else row["source"] for row in rows)
    widths = [int(row["width"]) for row in rows]
    heights = [int(row["height"]) for row in rows]
    short_sides = [min(w, h) for w, h in zip(widths, heights)]
    return {
        "total": len(rows),
        "styles": dict(styles),
        "licences": dict(licences),
        "splits": dict(splits),
        "sources": dict(sources),
        "min_short_side": min(short_sides) if rows else 0,
        "max_short_side": max(short_sides) if rows else 0,
    }


def render_stats_markdown(stats: dict, title: str = "Dataset statistics") -> str:
    lines = [f"# {title}", "", f"**Total items:** {stats['total']}", ""]
    for section in ("styles", "licences", "splits", "sources"):
        lines.append(f"## {section.capitalize()}")
        lines.append("")
        lines.append("| value | count |")
        lines.append("|---|---|")
        for key, count in sorted(stats[section].items()):
            lines.append(f"| {key} | {count} |")
        lines.append("")
    lines.append(f"**Short side range:** {stats['min_short_side']}–{stats['max_short_side']} px")
    lines.append("")
    return "\n".join(lines)
