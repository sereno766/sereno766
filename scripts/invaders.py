#!/usr/bin/env python3
"""Gera invaders.svg: uma nave estilo Space Invaders destruindo o gráfico de contribuições."""
import re, sys, urllib.request, datetime

USER = sys.argv[1] if len(sys.argv) > 1 else "sereno766"
OUT = sys.argv[2] if len(sys.argv) > 2 else "invaders.svg"

BG, BAR, BRD = "#0d1117", "#161b22", "#30363d"
TX, MU, GR, RD, OR, BL = "#e6edf3", "#8b949e", "#3fb950", "#f85149", "#d29922", "#58a6ff"
LEV = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
FONT = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# ── 1. ler o calendário ──
req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "invaders"})
html = urllib.request.urlopen(req, timeout=30).read().decode()
cells = {}
for m in re.finditer(r'<td[^>]*?data-date="([\d-]+)"[^>]*?id="contribution-day-component-(\d)-(\d+)"[^>]*?data-level="(\d)"', html):
    date, d, w, lv = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    cells[(w, d)] = (lv, date)
counts = {}
for m in re.finditer(r'for="contribution-day-component-(\d)-(\d+)"[^>]*>\s*(\d+|No) contributions?', html):
    counts[(int(m.group(2)), int(m.group(1)))] = 0 if m.group(3) == "No" else int(m.group(3))
m = re.search(r'([\d,]+)\s+contributions?\s+in the last year', html)
total = m.group(1) if m else "?"
weeks = max(w for w, _ in cells) + 1

# ── 2. geometria ──
W = 1000
P, C = 17, 13                      # passo e tamanho da célula
GX, GY = 62, 92                    # origem do grid
SHIP_Y = GY + 7*P + 74             # topo da nave
H = SHIP_Y + 70
cx = lambda w: GX + w*P + C/2
cy = lambda d: GY + d*P + C/2

# ── 3. roteiro do jogo ──
# cada bloco tem HP = nível (1 a 4): os mais verdes aguentam mais tiros
FIRE, BUL, MOVE, START = 0.15, 0.22, 0.045, 1.2
t = START
ship_kf = [(0, cx(0)), (START, cx(0))]
shots = []                          # (w, d, t_fire, t_hit)
targets_hp = []                     # (w, d, lv, [t_hit...])
last_w = 0
for w in range(weeks):
    col = sorted([d for d in range(7) if cells.get((w, d), (0,))[0] > 0], reverse=True)
    if not col: continue
    t += abs(w - last_w) * MOVE
    ship_kf.append((t, cx(w)))
    for d in col:
        lv = cells[(w, d)][0]
        tb = BUL * (SHIP_Y - cy(d)) / 200
        hits = []
        for _ in range(lv):
            shots.append((w, d, t, t + tb))
            hits.append(t + tb)
            t += FIRE
        targets_hp.append((w, d, lv, hits))
    ship_kf.append((t, cx(w)))
    last_w = w
END = t + 0.6
CLEAR = 2.6
t_back = END + CLEAR
ship_kf += [(END, ship_kf[-1][1]), (t_back, cx(0))]
T = t_back + 0.8
pct = lambda s: f"{100*s/T:.3f}%"

css, body = [], []
def kf(name, frames):
    css.append(f"@keyframes {name}{{" + "".join(f"{p}{{{v}}}" for p, v in frames) + "}")

# ── 4. desenho ──
body.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="8" fill="{BG}" stroke="{BRD}"/>')
body.append(f'<path d="M.5 32V8.5a8 8 0 0 1 8-8H{W-8.5}a8 8 0 0 1 8 8V32Z" fill="{BAR}"/><line x1="0" y1="32" x2="{W}" y2="32" stroke="{BRD}"/>')
body += [f'<circle cx="{18+i*18}" cy="16.5" r="5.5" fill="{c}"/>' for i, c in enumerate([RD, OR, GR])]
body.append(f'<text x="{W/2}" y="21" font-size="12.5" fill="{MU}" text-anchor="middle">space_invaders — git log --since="1 year ago"</text>')
body.append(f'<text x="20" y="60" font-size="13" fill="{TX}" font-weight="700">SCORE</text>')
SCORE_X, SCORE_Y, DW, LHd = 74, 61, 11, 22   # odômetro (desenhado depois do roteiro)
body.append(f'<text x="{W-20}" y="60" font-size="13" fill="{MU}" text-anchor="end">HI-SCORE <tspan fill="{OR}" font-weight="700">{total.replace(",", "").zfill(4)}</tspan>  <tspan fill="{MU}">· {total} contributions in the last year</tspan></text>')

# meses
seen = set()
for w in range(weeks):
    lv, date = cells.get((w, 0), cells.get((w, 6), (0, None)))
    if not date: continue
    dt = datetime.date.fromisoformat(date)
    if dt.day <= 7 and (dt.year, dt.month) not in seen and w < weeks - 2:
        seen.add((dt.year, dt.month))
        body.append(f'<text x="{GX + w*P}" y="{GY-8}" font-size="11" fill="{MU}">{dt.strftime("%b")}</text>')
for d, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    body.append(f'<text x="{GX-8}" y="{cy(d)+4}" font-size="11" fill="{MU}" text-anchor="end">{lab}</text>')

# células vazias (fundo)
body.append("".join(f'<rect x="{GX+w*P}" y="{GY+d*P}" width="{C}" height="{C}" rx="2.5" fill="{LEV[0]}"/>'
                    for (w, d) in cells))

# alvos (com vida)
for i, (w, d, lv, hits) in enumerate(targets_hp):
    x, y = GX + w*P, GY + d*P
    fr = [("0%", "opacity:0;transform:scale(.4)"), (pct(0.5), f"opacity:1;transform:scale(1);fill:{LEV[lv]}")]
    for k, th in enumerate(hits[:-1]):             # tiros que só causam dano
        cur, nxt = LEV[lv-k], LEV[lv-k-1]
        fr += [(pct(th), f"opacity:1;transform:scale(1);fill:{cur}"),
               (pct(th+0.02), "opacity:1;transform:scale(1.25) translateY(-1px);fill:#ffffff"),
               (pct(th+0.11), f"opacity:1;transform:scale(1);fill:{nxt}")]
    th = hits[-1]                                   # tiro final: explosão
    fr += [(pct(th), f"opacity:1;transform:scale(1);fill:{LEV[1]}"),
           (pct(th+0.02), "opacity:1;transform:scale(1.4);fill:#ffffff"),
           (pct(th+0.22), "opacity:0;transform:scale(1.9);fill:#ffffff"),
           ("100%", "opacity:0;transform:scale(.4)")]
    kf(f"c{i}", fr)
    body.append(f'<rect class="t" style="animation-name:c{i}" x="{x}" y="{y}" width="{C}" height="{C}" rx="2.5" fill="{LEV[lv]}"/>')
    # faíscas na explosão (maiores para blocos mais fortes)
    kf(f"s{i}", [("0%", "opacity:0;transform:scale(.2)"), (pct(th), "opacity:0;transform:scale(.2)"),
                 (pct(th+0.01), "opacity:1;transform:scale(.6)"), (pct(th+0.3), f"opacity:0;transform:scale({1.2+lv*0.25:.2f})"),
                 ("100%", "opacity:0")])
    sx, sy = x + C/2, y + C/2
    body.append(f'<g class="t" style="animation-name:s{i};transform-box:view-box;transform-origin:{sx}px {sy}px" opacity="0" fill="{LEV[4]}">'
                + "".join(f'<rect x="{sx+dx-1.5}" y="{sy+dy-1.5}" width="3" height="3"/>' for dx, dy in ((-11,0),(11,0),(0,-11),(0,11),(-8,-8),(8,8),(-8,8),(8,-8)))
                + "</g>")

# balas
for i, (w, d, tf, th) in enumerate(shots):
    y = GY + d*P
    dist = SHIP_Y - 4 - (y + C)
    kf(f"b{i}", [("0%", "opacity:0;transform:translateY(0)"), (pct(tf), "opacity:0;transform:translateY(0)"),
                 (pct(tf+0.001), "opacity:1;transform:translateY(0)"),
                 (pct(th), f"opacity:1;transform:translateY(-{dist:.1f}px)"),
                 (pct(th+0.001), f"opacity:0;transform:translateY(-{dist:.1f}px)"), ("100%", "opacity:0")])
    body.append(f'<rect class="b" opacity="0" style="animation-name:b{i}" x="{cx(w)-1.5}" y="{SHIP_Y-14}" width="3" height="10" rx="1.5" fill="{BL}"/>')

# placar dinâmico: soma os commits reais de cada bloco destruído
events = sorted((hits[-1], counts.get((w, d)) or lv, w, d) for (w, d, lv, hits) in targets_hp)
for j, (th, n, w, d) in enumerate(events):
    x, y = GX + w*P + C/2, GY + d*P
    kf(f"pt{j}", [("0%", "opacity:0;transform:translateY(0)"), (pct(th), "opacity:0;transform:translateY(0)"),
                  (pct(th+0.02), "opacity:1;transform:translateY(-4px)"), (pct(th+0.9), "opacity:0;transform:translateY(-22px)"),
                  ("100%", "opacity:0")])
    body.append(f'<text class="b" opacity="0" style="animation-name:pt{j}" x="{x}" y="{y-2}" font-size="11" font-weight="700" fill="{TX}" text-anchor="middle">+{n}</text>')

timeline, acc = [], 0
for th, n, _, _ in events:
    acc += n; timeline.append((th, acc))
final = acc
body.append(f'<clipPath id="odo"><rect x="{SCORE_X-2}" y="{SCORE_Y-16}" width="{4*DW+4}" height="21"/></clipPath>')
odo = []
for pl in range(4):
    div = 10**(3-pl)
    dig = lambda v: (v // div) % 10
    fr, cur = [("0%", "transform:translateY(0)")], 0
    for th, v in timeline:
        nd = dig(v)
        if nd != cur:
            fr += [(pct(th), f"transform:translateY(-{cur*LHd}px)"), (pct(th+0.001), f"transform:translateY(-{nd*LHd}px)")]
            cur = nd
    fr += [(pct(T-0.05), f"transform:translateY(-{cur*LHd}px)"), ("100%", "transform:translateY(0)")]
    kf(f"od{pl}", fr)
    odo.append(f'<g class="b" style="animation-name:od{pl}">' + "".join(
        f'<text x="{SCORE_X+pl*DW}" y="{SCORE_Y+k*LHd}" font-size="16" font-weight="700" fill="{GR}">{k}</text>' for k in range(10)) + "</g>")
body.append(f'<g clip-path="url(#odo)">{"".join(odo)}</g>')

# nave
ship_px = ["......#......", ".....###.....", ".....###.....", ".#.#######.#.", "#############", "#############", "##.##...##.##"]
S = 2.4
ship = "".join(f'<rect x="{-6.5*S + c*S:.1f}" y="{r*S:.1f}" width="{S+.2:.1f}" height="{S+.2:.1f}"/>'
               for r, row in enumerate(ship_px) for c, ch in enumerate(row) if ch == "#")
kf("ship", [(pct(tk), f"transform:translateX({xk:.1f}px)") for tk, xk in ship_kf] + [("100%", f"transform:translateX({cx(0):.1f}px)")])
body.append(f'<g class="ship"><g transform="translate(0 {SHIP_Y})" fill="{GR}">{ship}</g>'
            f'<rect class="flame" x="-3" y="{SHIP_Y+18}" width="6" height="5" rx="2" fill="{OR}"/></g>')

# legenda HP
lx = W - 20 - 5*16 - 70
body.append(f'<text x="{lx}" y="{H-14}" font-size="11" fill="{MU}">HP</text>')
for k in range(1, 5):
    body.append(f'<rect x="{lx+24+(k-1)*16}" y="{H-24}" width="11" height="11" rx="2" fill="{LEV[k]}"/>')
body.append(f'<text x="{lx+24+4*16+2}" y="{H-14}" font-size="11" fill="{MU}">1→4 hits</text>')

# chão + STAGE CLEAR
body.append(f'<line x1="20" y1="{SHIP_Y+30}" x2="{W-20}" y2="{SHIP_Y+30}" stroke="{BRD}" stroke-dasharray="4 4"/>')
kf("clear", [("0%", "opacity:0"), (pct(END), "opacity:0"), (pct(END+0.3), "opacity:1"),
             (pct(END+CLEAR-0.3), "opacity:1"), (pct(END+CLEAR), "opacity:0"), ("100%", "opacity:0")])
body.append(f'<text class="clear" opacity="0" x="{W/2}" y="{GY+3.5*P+8}" font-size="26" font-weight="700" fill="{GR}" text-anchor="middle" letter-spacing="6">STAGE CLEAR</text>')
body.append(f'<text class="clear" opacity="0" x="{W/2}" y="{GY+3.5*P+32}" font-size="12" fill="{MU}" text-anchor="middle">FINAL SCORE {final} · {len(targets_hp)} blocks · {len(shots)} shots · respawning...</text>')
body.append(f'<text x="20" y="{H-14}" font-size="11" fill="{MU}">sereno@node:~$ ./invaders --user {USER}</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<style>
text{{font-family:{FONT};white-space:pre}}
.t{{transform-box:fill-box;transform-origin:center;animation-duration:{T:.2f}s;animation-timing-function:linear;animation-iteration-count:infinite}}
.b{{animation-duration:{T:.2f}s;animation-timing-function:linear;animation-iteration-count:infinite}}
.ship{{animation:ship {T:.2f}s linear infinite}}
.clear{{opacity:0;animation:clear {T:.2f}s linear infinite}}
.flame{{animation:fl .15s steps(1) infinite}}
@keyframes fl{{50%{{opacity:.3}}}}
{chr(10).join(css)}
</style>
{chr(10).join(body)}
</svg>'''
open(OUT, "w").write(svg)
print(f"{OUT}: {len(targets_hp)} alvos, {len(shots)} tiros, loop {T:.1f}s, {len(svg)//1024} KB")
