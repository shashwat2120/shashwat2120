"""Builds the animated terminal header (assets/header-light.svg, assets/header-dark.svg).

Edit LINES below, then run:  python scripts/make_header.py
Pure SVG + SMIL animation, so it plays inside a GitHub README (no JavaScript allowed there).
"""

from pathlib import Path
from xml.sax.saxutils import escape

# Each entry: (command typed after "$ ", output line as [(text, colour-key, bold)])
LINES = [
    ("whoami", [("Shashwat Mishra", "fg", True), ("  ·  software engineer @ Academian  ·  Pune, India", "muted", False)]),
    ("cat focus.txt", [("AI agents", "blue", False), ("  ·  ", "muted", False),
                       ("accessibility tech", "blue", False), ("  ·  ", "muted", False),
                       ("Indian-language tools", "blue", False)]),
    ("ls ~/shipping", [("AccessLens/   ", "purple", True), ("bharat-translate-plus/   ", "purple", True),
                       ("setu/   ", "purple", True), ("skillsphere/", "purple", True)]),
    ("cat principles.txt", [("Rules for facts.", "orange", False), (" AI for judgment.", "orange", False),
                            (" Tests for everything.", "orange", False)]),
]

THEMES = {
    "dark": dict(bg="#0d1117", bar="#161b22", border="#30363d", fg="#e6edf3", muted="#8b949e",
                 green="#3fb950", blue="#79c0ff", purple="#d2a8ff", orange="#ffa657"),
    "light": dict(bg="#ffffff", bar="#f6f8fa", border="#d0d7de", fg="#1f2328", muted="#57606a",
                  green="#1a7f37", blue="#0969da", purple="#8250df", orange="#bc4c00"),
}

FONT = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"
SIZE, CHAR_W, W = 18, 10.8, 900
TYPE_S, PAUSE_S, LINE_GAP = 0.06, 0.25, 78
ALT = ("Shashwat Mishra, software engineer at Academian in Pune, building AI agents, accessibility tech "
       "and Indian-language tools")


def build(t: dict[str, str]) -> str:
    height = 78 + LINE_GAP * len(LINES) + 40
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" aria-label="{ALT}">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<path d="M0.5 12.5a12 12 0 0 1 12-12h{W - 25}a12 12 0 0 1 12 12v31h-{W - 1}z" fill="{t["bar"]}"/>',
        f'<line x1="0.5" y1="44" x2="{W - 0.5}" y2="44" stroke="{t["border"]}"/>',
        '<circle cx="26" cy="22" r="6" fill="#ff5f57"/><circle cx="46" cy="22" r="6" fill="#febc2e"/>'
        '<circle cx="66" cy="22" r="6" fill="#28c840"/>',
        f'<text x="{W / 2}" y="27" text-anchor="middle" font-family="{FONT}" font-size="13" '
        f'fill="{t["muted"]}">shashwat@github: ~</text>',
    ]
    clock, y = 0.4, 78
    for i, (cmd, result) in enumerate(LINES):
        # Typed command: a clip rectangle that widens one character at a time.
        n = len(cmd) + 2
        widths = ";".join(f"{CHAR_W * k:.1f}" for k in range(2, n + 1))
        dur = TYPE_S * (n - 1)
        out.append(
            f'<clipPath id="c{i}"><rect x="40" y="{y}" width="{CHAR_W * 2:.1f}" height="26">'
            f'<animate attributeName="width" values="{widths}" begin="{clock:.2f}s" dur="{dur:.2f}s" '
            f'calcMode="discrete" fill="freeze"/></rect></clipPath>'
            f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{clock:.2f}s" dur="0.01s" fill="freeze"/>'
            f'<text x="40" y="{y + 18}" font-family="{FONT}" font-size="{SIZE}" clip-path="url(#c{i})" '
            f'xml:space="preserve"><tspan fill="{t["green"]}" font-weight="bold">$ </tspan>'
            f'<tspan fill="{t["fg"]}">{escape(cmd)}</tspan></text></g>'
        )
        clock += dur + PAUSE_S
        spans = "".join(
            f'<tspan fill="{t[c]}"{" font-weight=\"bold\"" if b else ""}>{escape(s)}</tspan>' for s, c, b in result
        )
        out.append(
            f'<text x="40" y="{y + 50}" font-family="{FONT}" font-size="{SIZE}" opacity="0" '
            f'xml:space="preserve">{spans}<animate attributeName="opacity" to="1" begin="{clock:.2f}s" '
            f'dur="0.35s" fill="freeze"/></text>'
        )
        clock += 0.6
        y += LINE_GAP
    # Final prompt with a blinking cursor.
    out.append(
        f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{clock:.2f}s" dur="0.01s" fill="freeze"/>'
        f'<text x="40" y="{y + 18}" font-family="{FONT}" font-size="{SIZE}" font-weight="bold" '
        f'fill="{t["green"]}">$</text><rect x="{40 + CHAR_W * 2:.1f}" y="{y + 3}" width="{CHAR_W}" '
        f'height="18" fill="{t["fg"]}"><animate attributeName="opacity" values="1;1;0;0" '
        f'keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect></g>'
    )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    assets = Path(__file__).resolve().parent.parent / "assets"
    for name, theme in THEMES.items():
        (assets / f"header-{name}.svg").write_text(build(theme), encoding="utf-8")
        print(f"wrote assets/header-{name}.svg")
