"""Generate the GeoCities / Netscape-style SVGs for the GitHub profile README.

Usage: pip install fonttools brotli; python scripts/make_svgs.py <geist-pixel-square.woff2> assets

Every SVG is self-contained: the pixel font is subset to ASCII and embedded as a
data URI, and all motion is CSS inside the SVG (switched off for reduced motion).
"""
import base64
import io
import random
import sys
import textwrap
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)


def pixel_font_b64():
    font = TTFont(FONT_SRC)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = []
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(chr(c) for c in range(32, 127)))
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


FONT = pixel_font_b64()
SILVER, HI, LO, DK, NAVY, BLUE = "#c0c0c0", "#ffffff", "#808080", "#404040", "#000080", "#1084d0"
MONO = "'Courier New', Courier, monospace"

BASE_CSS = f"""
@font-face {{ font-family: 'Px'; src: url(data:font/woff2;base64,{FONT}) format('woff2'); }}
.px {{ font-family: 'Px', {MONO}; }}
.mono {{ font-family: {MONO}; }}
@keyframes twinkle {{ 0%, 100% {{ opacity: .15; }} 50% {{ opacity: 1; }} }}
@keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
.tw {{ animation: twinkle 2.8s ease-in-out infinite; }}
.blink {{ animation: blink 1.1s steps(1) infinite; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
"""


def bevel(x, y, w, h, fill=SILVER, inset=False):
    """A Windows 98 style bevelled rectangle."""
    a, b = (DK, HI) if inset else (HI, DK)
    c, d = (LO, "#dfdfdf") if inset else ("#dfdfdf", LO)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
        f'<path d="M{x} {y+h}V{y}H{x+w}" fill="none" stroke="{a}"/>'
        f'<path d="M{x+w} {y}V{y+h}H{x}" fill="none" stroke="{b}"/>'
        f'<path d="M{x+1} {y+h-1}V{y+1}H{x+w-1}" fill="none" stroke="{c}"/>'
        f'<path d="M{x+w-1} {y+1}V{y+h-1}H{x+1}" fill="none" stroke="{d}"/>'
    )


def titlebar(x, y, w, title, h=24):
    grad_id = f"tb{abs(hash(title)) % 10**6}"
    btns = ""
    for i, glyph in enumerate(["_", "o", "x"]):
        bx = x + w - 3 - (3 - i) * 20
        btns += bevel(bx, y + 4, 18, h - 8)
        if glyph == "_":
            btns += f'<rect x="{bx+5}" y="{y+h-10}" width="7" height="2" fill="#000"/>'
        elif glyph == "o":
            btns += f'<rect x="{bx+4.5}" y="{y+7.5}" width="9" height="8" fill="none" stroke="#000"/><rect x="{bx+4}" y="{y+7}" width="10" height="2" fill="#000"/>'
        else:
            btns += f'<path d="M{bx+5} {y+8}l8 8M{bx+13} {y+8}l-8 8" stroke="#000" stroke-width="1.6"/>'
    return (
        f'<defs><linearGradient id="{grad_id}"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient></defs>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{grad_id})"/>'
        f'<text x="{x+8}" y="{y+h-7}" class="px" font-size="14" fill="#fff" letter-spacing=".5">{escape(title)}</text>'
        + btns
    )


def stars(x, y, w, h, n, seed):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        sx, sy = x + rnd.random() * w, y + rnd.random() * h
        r = rnd.choice([0.6, 0.8, 1, 1.2, 1.6])
        col = rnd.choice(["#ffffff", "#ffffff", "#cfe3ff", "#fff6c2", "#b9c8ff"])
        cls = ' class="tw"' if i % 3 == 0 else ""
        delay = f' style="animation-delay:{rnd.random()*2.8:.2f}s"' if cls else ""
        out.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r}" fill="{col}"{cls}{delay}/>')
    return "".join(out)


def wordart(cx, y, text, size):
    layers = [("#7a00a8", 6), ("#7a00a8", 5), ("#e0004d", 4), ("#e0004d", 3), ("#ff7a00", 2), ("#ff7a00", 1)]
    out = "".join(
        f'<text x="{cx+d}" y="{y+d}" text-anchor="middle" class="px" font-size="{size}" fill="{c}">{escape(text)}</text>'
        for c, d in layers
    )
    out += f'<text x="{cx}" y="{y}" text-anchor="middle" class="px" font-size="{size}" fill="url(#wa)">{escape(text)}</text>'
    return out


def svg(w, h, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><style>{BASE_CSS}</style>"
        '<defs><linearGradient id="wa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff27a"/><stop offset=".55" stop-color="#ffde00"/><stop offset="1" stop-color="#ffb000"/></linearGradient></defs>'
        f"{body}</svg>"
    )


def hero():
    W, H = 960, 400
    b = bevel(0, 0, W, H)
    b += titlebar(3, 3, W - 6, "Chakravarthi's Homepage - Netscape Navigator")
    # Menu bar
    menu = ["File", "Edit", "View", "Go", "Bookmarks", "Options", "Directory", "Window", "Help"]
    mx = 12
    for m in menu:
        b += f'<text x="{mx}" y="44" class="mono" font-size="13" fill="#000"><tspan text-decoration="underline">{m[0]}</tspan>{m[1:]}</text>'
        mx += len(m) * 8 + 18
    # Toolbar
    tools = ["Back", "Forward", "Home", "Reload", "Images", "Print", "Find", "Stop"]
    tx = 10
    for t in tools:
        b += bevel(tx, 54, 64, 40)
        b += f'<text x="{tx+32}" y="79" text-anchor="middle" class="mono" font-size="12" fill="{"#808080" if t in ("Forward", "Stop") else "#000"}">{t}</text>'
        tx += 68
    # Throbber: a tiny night sky instead of Netscape's N
    b += bevel(W - 74, 52, 62, 44, fill="#05051c", inset=True)
    b += stars(W - 72, 54, 58, 40, 16, 7)
    b += f'<text x="{W-43}" y="80" text-anchor="middle" class="px" font-size="20" fill="#ffde00">C</text>'
    # Location bar
    b += f'<text x="12" y="118" class="mono" font-size="13" fill="#000">Location:</text>'
    b += bevel(88, 103, W - 100, 22, fill="#fff", inset=True)
    b += f'<text x="96" y="119" class="mono" font-size="13" fill="#000">http://vanitascaesar1.github.io/</text>'
    # Page area
    py, ph = 132, 236
    b += bevel(6, py, W - 12, ph, fill="#05051c", inset=True)
    b += stars(9, py + 3, W - 18, ph - 40, 140, 42)
    b += wordart(W / 2, py + 72, "Welcome to Chakravarthi's", 40)
    b += wordart(W / 2, py + 120, "Homepage!", 46)
    b += f'<text x="{W/2}" y="{py+156}" text-anchor="middle" class="mono" font-size="17" font-weight="bold" fill="#39ff14">full-stack + mobile engineer. co-founder/CTO @ Treato.</text>'
    # Blinking sticker
    b += f'<g transform="translate({W-176} {py+20}) rotate(8)"><g class="blink"><rect width="132" height="30" fill="#ff2bd6" stroke="#000" stroke-width="2"/><text x="66" y="21" text-anchor="middle" class="px" font-size="15" fill="#fff">NOW BUILDING!</text></g></g>'
    # Under-construction stripe on the left
    b += f'<g transform="translate(26 {py+18}) rotate(-8)"><defs><pattern id="hz" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="16" fill="#ffde00"/><rect x="8" width="8" height="16" fill="#141414"/></pattern></defs><rect width="158" height="30" fill="url(#hz)" stroke="#000"/><rect x="6" y="6" width="146" height="18" fill="#ffde00"/><text x="79" y="20" text-anchor="middle" class="px" font-size="11" fill="#000">UNDER CONSTRUCTION</text></g>'
    # Marquee
    mq_y = py + ph - 34
    b += f'<rect x="9" y="{mq_y}" width="{W-18}" height="28" fill="{NAVY}"/>'
    msg = "*** Thanks for stopping by! *** I build apps, APIs and the servers under them *** Building Treato, care for Indian families, doctors and clinics *** Sign my guestbook below! "
    mw = 1300
    b += f'<defs><clipPath id="mqc"><rect x="9" y="{mq_y}" width="{W-18}" height="28"/></clipPath></defs>'
    b += (
        f'<g clip-path="url(#mqc)"><g class="mq">'
        f'<text x="20" y="{mq_y+19}" class="mono" font-size="15" font-weight="bold" fill="#ffde00" textLength="{mw}" lengthAdjust="spacing">{escape(msg)}</text>'
        f'<text x="{20+mw}" y="{mq_y+19}" class="mono" font-size="15" font-weight="bold" fill="#ffde00" textLength="{mw}" lengthAdjust="spacing">{escape(msg)}</text>'
        "</g></g>"
    )
    b += f"<style>@keyframes mq {{ to {{ transform: translateX(-{mw}px); }} }} .mq {{ animation: mq 26s linear infinite; }}</style>"
    # Status bar
    b += bevel(6, H - 28, W - 240, 22, inset=True)
    b += f'<text x="14" y="{H-12}" class="mono" font-size="12" fill="#000">Document: Done</text>'
    b += bevel(W - 230, H - 28, 150, 22, inset=True)
    b += f'<rect x="{W-227}" y="{H-25}" width="144" height="16" fill="{NAVY}"/>'
    b += bevel(W - 76, H - 28, 70, 22, inset=True)
    b += f'<text x="{W-41}" y="{H-12}" text-anchor="middle" class="mono" font-size="12" fill="#000">100%</text>'
    return svg(W, H, b, "Welcome to Chakravarthi's Homepage! Full-stack and mobile engineer, co-founder and CTO at Treato.")


def card(slug, title, lang, lang_color, desc, extra=None, new=False):
    W, H = 460, 196
    b = bevel(0, 0, W, H)
    b += titlebar(3, 3, W - 6, f"{slug}.exe")
    b += bevel(8, 32, W - 16, H - 40, fill="#ececec", inset=True)
    b += f'<text x="22" y="66" class="px" font-size="24" fill="{NAVY}">{escape(title)}</text>'
    if new:
        tx = 22 + len(title) * 13.6 + 14
        b += f'<g transform="translate({tx:.0f} 44) rotate(-6)" class="blink"><rect width="48" height="20" fill="#ff2bd6"/><text x="24" y="15" text-anchor="middle" class="px" font-size="12" fill="#fff">NEW!</text></g>'
    lines = textwrap.wrap(desc, 50)
    for i, line in enumerate(lines[:4]):
        b += f'<text x="22" y="{92 + i*19}" class="mono" font-size="14" fill="#111">{escape(line)}</text>'
    # Footer chips
    b += f'<rect x="22" y="{H-38}" width="{len(lang)*9+26}" height="22" fill="{lang_color}" stroke="#000"/>'
    b += f'<text x="{22 + (len(lang)*9+26)/2}" y="{H-22}" text-anchor="middle" class="px" font-size="12" fill="#fff">{escape(lang.upper())}</text>'
    if extra:
        ex = 22 + len(lang) * 9 + 36
        b += f'<text x="{ex}" y="{H-22}" class="mono" font-size="13" fill="{NAVY}" text-decoration="underline">{escape(extra)}</text>'
    return svg(W, H, b, f"{title}: {desc}")


def treato():
    W, H = 960, 330
    b = bevel(0, 0, W, H)
    b += titlebar(3, 3, W - 6, "System Properties - Treato")
    # Tabs
    for i, (t, on) in enumerate([("General", True), ("Device Manager", False), ("Performance", False)]):
        x = 12 + i * 132
        b += bevel(x, 34 if on else 37, 128, 26 if on else 23)
        b += f'<text x="{x+64}" y="{52}" text-anchor="middle" class="mono" font-size="13" fill="#000">{t}</text>'
    b += bevel(8, 58, W - 16, H - 66)
    b += f'<text x="30" y="98" class="px" font-size="30" fill="{NAVY}">Treato</text>'
    b += f'<text x="30" y="124" class="mono" font-size="14" fill="#111">A care platform for India. Families, doctors and clinics</text>'
    b += '<text x="30" y="143" class="mono" font-size="14" fill="#111">share one health record. I&#39;m co-founder, CTO and the</text>'
    b += f'<text x="30" y="162" class="mono" font-size="14" fill="#111">only engineer: about 3,700 commits since March 2025.</text>'
    b += bevel(30, 180, 380, 120, fill="#05051c", inset=True)
    for i, (k, v) in enumerate([("commits", "3,700+"), ("apps", "4"), ("migrations", "~360"), ("engineers", "1")]):
        yy = 206 + i * 26
        b += f'<text x="46" y="{yy}" class="mono" font-size="14" fill="#39ff14">C:\\TREATO&gt; count {k}</text>'
        b += f'<text x="392" y="{yy}" text-anchor="end" class="px" font-size="16" fill="#ffde00">{v}</text>'
    rows = [
        ("Mobile", "React Native + Expo"),
        ("API", "Go (Fiber) + PostgreSQL"),
        ("Auth", "Rust: OTP + passkeys"),
        ("Chat", "Elixir + Phoenix"),
        ("Video", "self-hosted LiveKit"),
        ("AI", "Maya, on Claude"),
        ("Web + desk", "Next.js + Tauri"),
        ("Infra", "Docker on a VPS"),
    ]
    b += f'<text x="540" y="92" class="mono" font-size="13" fill="#000">Computer:</text>'
    for i, (k, v) in enumerate(rows):
        yy = 118 + i * 24
        b += f'<text x="556" y="{yy}" class="mono" font-size="14" font-weight="bold" fill="{NAVY}">{escape(k)}</text>'
        b += f'<text x="666" y="{yy}" class="mono" font-size="14" fill="#111">{escape(v)}</text>'
    b += bevel(W - 120, H - 44, 96, 26)
    b += f'<text x="{W-72}" y="{H-26}" text-anchor="middle" class="mono" font-size="13" fill="#000">OK</text>'
    return svg(W, H, b, "Treato: a care platform for India. Co-founder, CTO and only engineer. React Native, Go, Rust, Elixir, LiveKit, Claude, Next.js, Tauri, Docker.")


def badges():
    items = [
        ("GO", "powered", "#00add8", "#00728f", "#fff"),
        ("RUST", "inside", "#f0a070", "#b7410e", "#1b0b00"),
        ("ELIXIR", "phoenix", "#8a5bb5", "#4b275f", "#fde9ff"),
        ("EXPO", "react native", "#ffffff", "#d7d7d7", "#000020"),
        ("TYPESCRIPT", "strict mode", "#4a8fdc", "#235a97", "#fff"),
        ("POSTGRES", "since day 1", "#5b8fc4", "#336791", "#fff"),
        ("KOTLIN", "compose", "#b07cf0", "#6b3fb3", "#fff"),
        ("DOCKER", "self-hosted", "#2fa8ee", "#0b6ba8", "#fff"),
        ("CLAUDE", "ai pair", "#e8a27c", "#b8603c", "#fff"),
        ("ANY", "best viewed in", "#ffef7a", "#e2b800", "#200"),
    ]
    W, H = 5 * 88 + 4 * 10, 2 * 31 + 10
    b = ""
    for i, (big, small, c1, c2, fg) in enumerate(items):
        x, y = (i % 5) * 98, (i // 5) * 41
        gid = f"bg{i}"
        b += f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
        b += f'<rect x="{x+.5}" y="{y+.5}" width="87" height="30" fill="url(#{gid})" stroke="#000"/>'
        b += f'<path d="M{x+1.5} {y+29.5}V{y+1.5}H{x+86.5}" fill="none" stroke="#fff" stroke-opacity=".5"/>'
        if big == "ANY":
            b += f'<text x="{x+44}" y="{y+12}" text-anchor="middle" class="mono" font-size="7.5" font-weight="bold" fill="{fg}">BEST VIEWED IN</text>'
            b += f'<text x="{x+44}" y="{y+25}" text-anchor="middle" class="px" font-size="11" fill="{fg}">ANY BROWSER</text>'
        else:
            b += f'<text x="{x+44}" y="{y+15}" text-anchor="middle" class="px" font-size="{12 if len(big) < 9 else 10.5}" fill="{fg}">{big}</text>'
            b += f'<text x="{x+44}" y="{y+25}" text-anchor="middle" class="mono" font-size="7.5" font-weight="bold" fill="{fg}">{small.upper()}</text>'
    return svg(W, H, b, "Powered by Go, Rust, Elixir, Expo, TypeScript, PostgreSQL, Kotlin, Docker and Claude. Best viewed in any browser.")


(OUT / "hero.svg").write_text(hero())
(OUT / "treato.svg").write_text(treato())
(OUT / "badges.svg").write_text(badges())
cards = [
    ("expo-hot-toast", "expo-hot-toast", "TypeScript", "#235a97", "The react-hot-toast API for Expo. Real Liquid Glass on iOS 26, Material 3 snackbars on Android, frosted glass on the web.", "try the demo >>", True),
    ("zvault", "ZVault", "Rust", "#b7410e", "A secrets manager that keeps API keys away from AI coding tools. AES-256-GCM, installed from a Homebrew tap.", None, False),
    ("butterui", "ButterUI", "TypeScript", "#235a97", "Smooth screen transitions and native portals for React Native, packaged as agent skills for Claude Code, Cursor and Codex.", None, False),
    ("murkysql", "murkysql", "Rust", "#b7410e", "Vector search inside SQLite. HNSW and IVF indexes, quantization, SIMD. A SQLite extension written in Rust.", None, False),
    ("seer", "Seer", "Kotlin", "#6b3fb3", "A privacy-first Android keyboard. Suggestions stay on the device, and it ships with no internet permission at all.", None, False),
    ("homepage", "My homepage", "HTML", "#e0004d", "My portfolio, built like it's 1997: starfield, WordArt, a hit counter and a guestbook. Treato, resume and more.", "visit >>", False),
]
for slug, title, lang, color, desc, extra, new in cards:
    (OUT / f"card-{slug}.svg").write_text(card(slug, title, lang, color, desc, extra, new))
for p in sorted(OUT.glob("*.svg")):
    print(p.name, p.stat().st_size)
