#!/usr/bin/env python3
import html
import sys
from pathlib import Path


STAFF_TOP = 64
STAFF_GAP = 12
STAFF_LINES = 5
COUNT_Y = 154
LEFT_MARGIN = 116
RIGHT_MARGIN = 28
BAR_GAP = 16

Y_POSITIONS = {
    "c": STAFF_TOP - 32,
    "hh": STAFF_TOP - 16,
    "oh": STAFF_TOP - 16,
    "ohs": STAFF_TOP - 16,
    "s": STAFF_TOP + STAFF_GAP * 2,
    "k": STAFF_TOP + STAFF_GAP * 4,
}

def parse_steps(value):
    if not value:
        return []
    return [int(step) for step in value.split(",") if step]


def parse_pattern(pattern_spec):
    bars = []
    for bar_spec in pattern_spec.split("|"):
        bar = {"c": [], "hh": [], "oh": [], "ohs": [], "s": [], "k": []}
        for part in bar_spec.split(";"):
            if not part:
                continue
            key, _, value = part.partition("=")
            if key not in bar:
                raise ValueError(f"unknown pattern key: {key}")
            bar[key] = parse_steps(value)
        bars.append(bar)
    return bars


def counts_for(subdivision):
    if subdivision == 8:
        return ["1", "&", "2", "&", "3", "&", "4", "&"]
    if subdivision == 16:
        return ["1", "e", "&", "a", "2", "e", "&", "a", "3", "e", "&", "a", "4", "e", "&", "a"]
    raise ValueError("subdivision must be 8 or 16")


def bar_width(subdivision):
    return 360 if subdivision == 8 else 560


def step_x(bar_index, step, subdivision):
    width = bar_width(subdivision)
    steps = subdivision
    bar_left = LEFT_MARGIN + bar_index * (width + BAR_GAP)
    usable = width - 34
    return bar_left + 18 + step * usable / (steps - 1)


def draw_staff(svg, bar_index, subdivision):
    width = bar_width(subdivision)
    x1 = LEFT_MARGIN + bar_index * (width + BAR_GAP)
    x2 = x1 + width

    for line in range(STAFF_LINES):
        y = STAFF_TOP + line * STAFF_GAP
        svg.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="staff" />')

    svg.append(f'<line x1="{x1}" y1="{STAFF_TOP}" x2="{x1}" y2="{STAFF_TOP + STAFF_GAP * 4}" class="barline" />')
    svg.append(f'<line x1="{x2}" y1="{STAFF_TOP}" x2="{x2}" y2="{STAFF_TOP + STAFF_GAP * 4}" class="barline" />')

    for beat in range(4):
        step = beat * (subdivision // 4)
        x = step_x(bar_index, step, subdivision)
        svg.append(f'<line x1="{x}" y1="{STAFF_TOP - 24}" x2="{x}" y2="{COUNT_Y - 12}" class="beat" />')

    count_labels = counts_for(subdivision)
    for step, label in enumerate(count_labels):
        x = step_x(bar_index, step, subdivision)
        svg.append(f'<text x="{x}" y="{COUNT_Y}" class="count">{html.escape(label)}</text>')


def draw_percussion_clef(svg):
    x = 72
    y1 = STAFF_TOP + 4
    y2 = STAFF_TOP + STAFF_GAP * 4 - 4
    svg.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="clef" />')
    svg.append(f'<line x1="{x + 8}" y1="{y1}" x2="{x + 8}" y2="{y2}" class="clef" />')
    svg.append(f'<text x="22" y="{Y_POSITIONS["c"] + 4}" class="voice-label">Crash</text>')
    svg.append(f'<text x="22" y="{Y_POSITIONS["hh"] + 4}" class="voice-label">Hi-hat</text>')
    svg.append(f'<text x="22" y="{Y_POSITIONS["s"] + 4}" class="voice-label">Snare</text>')
    svg.append(f'<text x="22" y="{Y_POSITIONS["k"] + 4}" class="voice-label">Kick</text>')


def draw_x_note(svg, x, y, open_note=False):
    size = 7
    svg.append(f'<line x1="{x - size}" y1="{y - size}" x2="{x + size}" y2="{y + size}" class="note" />')
    svg.append(f'<line x1="{x - size}" y1="{y + size}" x2="{x + size}" y2="{y - size}" class="note" />')
    if open_note:
        svg.append(f'<circle cx="{x}" cy="{y}" r="11" class="open" />')


def draw_filled_note(svg, x, y):
    svg.append(f'<ellipse cx="{x}" cy="{y}" rx="8" ry="6" class="filled-note" transform="rotate(-20 {x} {y})" />')


def draw_note(svg, x, key):
    y = Y_POSITIONS[key]
    if key in ("c", "hh", "oh", "ohs"):
        draw_x_note(svg, x, y, key in ("oh", "ohs"))
        if key == "ohs":
            svg.append(f'<text x="{x + 18}" y="{y - 10}" class="mark">sizzle</text>')
    else:
        draw_filled_note(svg, x, y)
        if key == "k":
            svg.append(f'<line x1="{x - 7}" y1="{y}" x2="{x - 7}" y2="{y + 24}" class="stem" />')
        else:
            svg.append(f'<line x1="{x + 7}" y1="{y}" x2="{x + 7}" y2="{STAFF_TOP - 2}" class="stem" />')


def render(title, subdivision, pattern_spec):
    bars = parse_pattern(pattern_spec)
    width = LEFT_MARGIN + len(bars) * bar_width(subdivision) + max(0, len(bars) - 1) * BAR_GAP + RIGHT_MARGIN
    height = 168
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title>{html.escape(title)}</title>',
        '<desc>Drum set staff notation showing hi-hat, snare, and kick placements.</desc>',
        "<style>",
        ".page{fill:#fff}.staff{stroke:#111;stroke-width:1.2}.barline{stroke:#111;stroke-width:1.8}.beat{stroke:#b9bec7;stroke-width:1;stroke-dasharray:3 5}.clef,.stem,.note{stroke:#111;stroke-width:2;stroke-linecap:round}.filled-note{fill:#111}.open{fill:none;stroke:#111;stroke-width:1.6}.count,.voice-label,.mark{font-family:Arial,Helvetica,sans-serif;fill:#111}.count{font-size:13px;text-anchor:middle}.voice-label{font-size:11px;text-anchor:start}.mark{font-size:10px}",
        "</style>",
        f'<rect width="{width}" height="{height}" class="page" />',
    ]

    draw_percussion_clef(svg)
    for bar_index in range(len(bars)):
        draw_staff(svg, bar_index, subdivision)

    for bar_index, bar in enumerate(bars):
        for key in ("c", "hh", "oh", "ohs", "s", "k"):
            for step in bar[key]:
                draw_note(svg, step_x(bar_index, step, subdivision), key)

    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def main():
    if len(sys.argv) != 5:
        print("usage: generate_notation_svg.py TITLE SUBDIVISION PATTERN_SPEC OUTPUT_PATH", file=sys.stderr)
        return 2

    title = sys.argv[1]
    subdivision = int(sys.argv[2])
    pattern_spec = sys.argv[3]
    output_path = Path(sys.argv[4])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render(title, subdivision, pattern_spec), encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
