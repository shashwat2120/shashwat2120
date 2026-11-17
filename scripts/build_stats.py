"""Builds a self-hosted stats card from the GitHub API (no third-party stats service).

Writes <out>/stats.svg and <out>/stats-dark.svg. Standard library only.
Usage: GITHUB_TOKEN=... python scripts/build_stats.py <github-user> <out-dir>
"""

import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape

API = "https://api.github.com"
SKIP_LANGS = {"HTML", "CSS", "Jupyter Notebook", "Batchfile", "Dockerfile", "Makefile", "Shell", "PowerShell"}
TOP_N = 6
COLORS = {
    "Python": "#3572A5", "Java": "#b07219", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Kotlin": "#A97BFF", "PHP": "#4F5D95", "Go": "#00ADD8", "C++": "#f34b7d", "C": "#555555",
    "Rust": "#dea584", "SQL": "#e38c00", "PLpgSQL": "#336790", "Dart": "#00B4AB",
}
THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", fg="#e6edf3", muted="#8b949e", accent="#d2a8ff", track="#21262d"),
    "light": dict(bg="#ffffff", border="#d0d7de", fg="#1f2328", muted="#57606a", accent="#8250df", track="#eaeef2"),
}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def call(path: str, body: dict | None = None) -> object:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode() if body else None,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-stats-card",
                 "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def collect(user: str) -> dict:
    repos = [r for r in call(f"/users/{user}/repos?per_page=100&type=owner") if not r["fork"]]
    langs: Counter[str] = Counter()
    for r in repos:
        for lang, n in call(f"/repos/{user}/{r['name']}/languages").items():
            if lang not in SKIP_LANGS:
                langs[lang] += n
    year = datetime.now(UTC).year
    q = ("query($u:String!,$from:DateTime!){user(login:$u){contributionsCollection(from:$from)"
         "{contributionCalendar{totalContributions}}}}")
    gql = call("/graphql", {"query": q, "variables": {"u": user, "from": f"{year}-01-01T00:00:00Z"}})
    contributions = gql["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    latest = max(repos, key=lambda r: r["pushed_at"])
    return {"repos": len(repos), "langs": langs, "contributions": contributions, "year": year,
            "latest": latest["name"], "latest_at": latest["pushed_at"][:10]}


def card(d: dict, t: dict[str, str]) -> str:
    w, h = 900, 200
    total = sum(d["langs"].values()) or 1
    top = d["langs"].most_common(TOP_N)
    other = total - sum(n for _, n in top)
    if other / total >= 0.001:
        top.append(("Other", other))
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
         f'aria-label="GitHub stats: {d["repos"]} repositories, {d["contributions"]} contributions in {d["year"]}">',
         f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<style>text{{font-family:{FONT}}}.n{{font-size:30px;font-weight:700;fill:{t["fg"]}}}'
         f'.l{{font-size:13px;fill:{t["muted"]}}}.g{{font-size:12px;fill:{t["fg"]}}}</style>']
    # Left column: three headline numbers.
    stats = [(str(d["repos"]), "original repositories"), (str(d["contributions"]), f"contributions in {d['year']}"),
             (d["latest"], f"latest push · {d['latest_at']}")]
    for i, (num, label) in enumerate(stats):
        y = 52 + i * 52
        size = ' style="font-size:18px"' if i == 2 else ""
        s.append(f'<text x="32" y="{y}" class="n"{size}>{escape(num)}</text>'
                 f'<text x="32" y="{y + 18}" class="l">{escape(label)}</text>')
    # Right column: animated language bar + legend.
    x0, bw = 360, 508
    s.append(f'<text x="{x0}" y="40" class="l" style="font-weight:600;fill:{t["accent"]}">LANGUAGES I SHIP IN</text>')
    # The bar fills left to right: a SMIL-animated clip (CSS transforms are unreliable in SVG <img>).
    s.append(f'<clipPath id="r"><rect x="{x0}" y="56" width="0" height="12" rx="6">'
             f'<animate attributeName="width" from="0" to="{bw}" dur="1.2s" fill="freeze" '
             f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.2 1"/></rect></clipPath>'
             f'<rect x="{x0}" y="56" width="{bw}" height="12" rx="6" fill="{t["track"]}"/>'
             f'<g clip-path="url(#r)"><g>')
    x = x0
    for lang, n in top:
        seg = bw * n / total
        s.append(f'<rect x="{x:.1f}" y="56" width="{seg + 0.5:.1f}" height="12" fill="{COLORS.get(lang, t["muted"])}"/>')
        x += seg
    s.append("</g></g>")
    for i, (lang, n) in enumerate(top):
        lx, ly = x0 + (i % 3) * 170, 100 + (i // 3) * 30
        s.append(f'<circle cx="{lx + 6}" cy="{ly - 4}" r="6" fill="{COLORS.get(lang, t["muted"])}"/>'
                 f'<text x="{lx + 18}" y="{ly}" class="g">{escape(lang)} '
                 f'<tspan style="fill:{t["muted"]}">{100 * n / total:.1f}%</tspan></text>')
    s.append(f'<text x="{w - 20}" y="{h - 14}" text-anchor="end" class="l" style="font-size:11px">'
             f'auto-updated daily · excludes forks and markup</text></svg>')
    return "\n".join(s)


if __name__ == "__main__":
    user, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    data = collect(user)
    (out / "stats.svg").write_text(card(data, THEMES["light"]), encoding="utf-8")
    (out / "stats-dark.svg").write_text(card(data, THEMES["dark"]), encoding="utf-8")
    print(f"wrote stats cards to {out}")
