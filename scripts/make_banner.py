"""Generate the profile banner (light and dark) in the style of the 2026 homepage.

Usage: pip install fonttools brotli
       python scripts/make_banner.py <manrope.woff2> <geist-mono.woff2> assets [commits]

The fonts are subset to the characters used and embedded, so the SVG renders the
same inside GitHub's image proxy. The commit count is also updated daily by
scripts/update-commits.mjs, which rewrites the number in place.
"""
import base64
import io
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

MANROPE, MONO, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
COMMITS = sys.argv[4] if len(sys.argv) > 4 else "3,368"
OUT.mkdir(parents=True, exist_ok=True)

HEAD = "I can’t stop building."
EYEBROW = "CHAKRAVARTHI CHINTAPATLA · CO-FOUNDER AND CTO, TREATO · INDIA"
LAYERS = ["PIXEL", "APP", "SERVICE", "DATA", "MACHINE", "BEDROCK"]


def font_b64(src, text, variable_weight=None):
    font = TTFont(src)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    s = subset.Subsetter(opts)
    s.populate(text=text)
    s.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


sans_text = HEAD + "0123456789,"
mono_text = EYEBROW + " COMMITS SINCE MARCH 2025" + "".join(LAYERS) + "0123456789,"
SANS = font_b64(MANROPE, sans_text)
MONOF = font_b64(MONO, mono_text)

THEMES = {
    "light": dict(bg="#F5F4F0", fg="#0B0C10", fg2="#6B6C71",
                  sheets=["#ECEAE4", "#DCD9D1", "#24262D", "#17181D", "#0E0F13", "#050507"]),
    "dark": dict(bg="#0B0C10", fg="#F2F1EC", fg2="#8E8F94",
                 sheets=["#2A2C33", "#22242A", "#1A1C21", "#141519", "#0E0F12", "#060608"]),
}


def banner(t):
    W, H = 1280, 400
    css = f"""
@font-face{{font-family:M;src:url(data:font/woff2;base64,{SANS}) format("woff2");font-weight:200 800}}
@font-face{{font-family:G;src:url(data:font/woff2;base64,{MONOF}) format("woff2")}}
.h{{font:800 92px M;letter-spacing:-4.5px;fill:{t['fg']}}}
.e{{font:400 15px G;letter-spacing:1.4px;fill:{t['fg2']}}}
.c{{font:400 15px G;letter-spacing:1.4px;fill:{t['fg2']}}}
.n{{fill:{t['fg']};font-weight:600}}
.l{{font:400 12px G;letter-spacing:1.4px}}
.dot{{fill:#22C55E;animation:p 2s ease-out infinite;transform-origin:72px 336px}}
@keyframes p{{0%{{opacity:1}}50%{{opacity:.35}}100%{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.dot{{animation:none}}}}
"""
    body = f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>'
    # the stack of layers, sinking toward the bottom right
    for i, (c, name) in enumerate(zip(t["sheets"], LAYERS)):
        x, y = 930 + i * 20, 64 + i * 54
        light = i < 2 and t is THEMES["light"]
        body += (f'<g>'
                 f'<rect x="{x}" y="{y}" width="{W - x + 40}" height="{H}" rx="22" fill="{c}"'
                 f' stroke="{t["bg"]}" stroke-opacity=".25"/>'
                 f'<text x="{x + 24}" y="{y + 28}" class="l" fill="{"#0B0C10" if light else "#F2F1EC"}">{name}</text></g>')
    body += f'<text x="72" y="96" class="e">{EYEBROW}</text>'
    body += f'<text x="66" y="200" class="h">I can’t stop</text>'
    body += f'<text x="66" y="290" class="h">building.</text>'
    body += f'<circle class="dot" cx="76" cy="337" r="5"/>'
    body += (f'<text x="92" y="342" class="c"><tspan class="n" id="commits">{COMMITS}</tspan>'
             f' COMMITS SINCE MARCH 2025</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img"'
            f' aria-label="Chakravarthi Chintapatla, co-founder and CTO of Treato, India. I can’t stop building.">'
            f'<style>{css}</style>{body}</svg>')


for name, theme in THEMES.items():
    p = OUT / f"banner-{name}.svg"
    p.write_text(banner(theme))
    print(p.name, p.stat().st_size)
