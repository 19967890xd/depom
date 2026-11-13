import cairo, math, json, sys, os, random
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
FPS = 24
DUR = 165.9
FLOOR = 1250
PI = math.pi

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sm(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def seg(t, t0, t1): return sm((t - t0) / (t1 - t0))
def kf(t, keys):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1: return lerp(v0, v1, sm((t - t0) / (t1 - t0)))
    return keys[-1][1]
def moving(t, keys):
    return any(t0 < t < t1 and v0 != v1 for (t0, v0), (t1, v1) in zip(keys, keys[1:]))
def hexc(h):
    if not isinstance(h, str): return h
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def mix(a, b, t):
    a, b = hexc(a), hexc(b); return tuple(lerp(x, y, t) for x, y in zip(a, b))
def dark(c, k=0.75):
    c = hexc(c); return tuple(x * k for x in c)
def setc(ctx, c, a=1.0):
    c = hexc(c); ctx.set_source_rgba(c[0], c[1], c[2], a)
OUT = hexc('#2b1d16')
def fs(ctx, c, lw=5, a=1.0):
    setc(ctx, c, a); ctx.fill_preserve(); setc(ctx, OUT, a); ctx.set_line_width(lw); ctx.stroke()
def ell(ctx, x, y, rx, ry):
    ctx.save(); ctx.translate(x, y); ctx.scale(max(rx, 0.01), max(ry, 0.01)); ctx.arc(0, 0, 1, 0, 2 * PI); ctx.restore()
def circ(ctx, x, y, r): ctx.new_sub_path(); ctx.arc(x, y, max(r, 0.01), 0, 2 * PI)
def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -PI / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, PI / 2)
    ctx.arc(x + r, y + h - r, r, PI / 2, PI); ctx.arc(x + r, y + r, r, PI, 1.5 * PI); ctx.close_path()
def lgrad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c, *a in stops:
        c = hexc(c); g.add_color_stop_rgba(o, c[0], c[1], c[2], a[0] if a else 1)
    return g
def glow(ctx, x, y, r, c, a=0.6):
    c = hexc(c); g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], a); g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g); circ(ctx, x, y, r); ctx.fill()

# ---------------------------------------------------------------- audio envelope (mouth)
_a = np.fromfile(os.path.join(HERE, 'audio16k.raw'), np.float32)
_hop = 16000 / FPS
_n = int(len(_a) / _hop)
ENV = np.array([np.sqrt(np.mean(_a[int(i * _hop):int((i + 1) * _hop)] ** 2) + 1e-12) for i in range(_n)])
_p = np.percentile(ENV[ENV > 0.005], 85)
ENV = np.clip((ENV / _p - 0.18) * 1.35, 0, 1)
def env(t):
    i = int(t * FPS); return float(ENV[i]) if 0 <= i < len(ENV) else 0.0

SPEAK = [(0, 12.8, 'nar'), (12.8, 15.7, 'c1'), (15.7, 22.42, 'pad'), (22.42, 30.7, 'adam'),
         (30.7, 36.06, 'pad'), (36.06, 39.4, 'adam'), (39.4, 41.62, 'pad'), (41.62, 47.44, 'nar'),
         (47.44, 52.9, 'adam'), (52.9, 61.56, 'pad'), (61.56, 63.6, 'adam'), (63.6, 64.98, 'pad'),
         (64.98, 87.74, 'adam'), (87.74, 89.8, 'nar'), (89.8, 96.48, 'pad'), (96.48, 100.22, 'nar'),
         (100.22, 108.16, 'vezir'), (108.16, 116.84, 'nar'), (116.84, 124.84, 'pad'),
         (124.84, 129.06, 'nar'), (129.06, 132.28, 'pad'), (132.28, 999, 'nar')]
def speaker(t):
    for a, b, n in SPEAK:
        if a <= t < b: return n
    return 'nar'
def mouth_of(name, t):
    if speaker(t) != name: return 0.0
    return env(t) * (0.55 + 0.45 * abs(math.sin(t * 17)))

# ---------------------------------------------------------------- characters
STY = {
    'adam': dict(skin='#e0a882', robe='#8a6a4a', trim='#6b4f35', sash='#5a4030', pants='#5b4a3a', shoe='#3a2a20',
                 hat='cap', hatc='#7a5c3e', beard='stubble', beardc='#4a3426', w=1.0, patches=True),
    'pad': dict(skin='#f0c09a', robe='#7b2d8e', trim='#f2c14e', sash='#f2c14e', pants='#4a1a55', shoe='#c9302c',
                hat='bigturban', hatc='#fbf6ea', beard='long', beardc='#3b2a20', w=1.22),
    'vezir': dict(skin='#e8b48e', robe='#2e7d4f', trim='#c9e4c5', sash='#b8862b', pants='#1f4d33', shoe='#6b3e1e',
                  hat='kavuk', hatc='#f4ecd8', beard='pointy', beardc='#a0a0a0', w=1.05),
    'veznedar': dict(skin='#e6b089', robe='#1f5f8b', trim='#e8d27a', sash='#8b1e1e', pants='#163b57', shoe='#3a2a20',
                     hat='fez', hatc='#b3262e', beard='short', beardc='#2a1e18', w=1.12),
    'c1': dict(skin='#d99a6c', robe='#c75b39', trim='#f0d9a8', sash='#6b3a22', pants='#4a3a2a', shoe='#3a2a20',
               hat='turban', hatc='#f0e6d2', beard='short', beardc='#3a2a20', w=1.05),
    'c2': dict(skin='#f1c6a0', robe='#d9a43b', trim='#8a3b2b', sash='#8a3b2b', pants='#6b4a2a', shoe='#5a2a20',
               hat='scarf', hatc='#3d6fb6', beard='none', beardc='#000', w=1.0),
    'c3': dict(skin='#c98d62', robe='#4f6d7a', trim='#e6e0c8', sash='#2c3e46', pants='#2c3e46', shoe='#2a2a2a',
               hat='fez', hatc='#8e2a2a', beard='mustache', beardc='#2a1e18', w=1.0),
}
SEED = {k: i * 1.37 for i, k in enumerate(STY)}

def base_pose():
    return dict(face=1, mouth=0, smile=0.15, brow=0, look=1, fa=(0.12, 0.25), ba=(-0.1, 0.15), walk=None,
                tremble=0, sweat=0, item=None, bite=0, wide=0, blink=None)

def arm(ctx, sx, sy, a1, a2, col, skin):
    L1, L2 = 92, 86
    ex, ey = sx + L1 * math.sin(a1), sy + L1 * math.cos(a1)
    hx, hy = ex + L2 * math.sin(a1 + a2), ey + L2 * math.cos(a1 + a2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(sx, sy); ctx.line_to(ex, ey); ctx.line_to(hx, hy)
    setc(ctx, OUT); ctx.set_line_width(44); ctx.stroke_preserve()
    setc(ctx, col); ctx.set_line_width(34); ctx.stroke()
    circ(ctx, hx, hy, 18); fs(ctx, skin, 4)
    return hx, hy

def robe_path(ctx, w):
    ctx.new_path()
    ctx.move_to(-62 * w, -305)
    ctx.curve_to(-75 * w, -200, -95 * w, -120, -100 * w, -45)
    ctx.curve_to(-40 * w, -28, 40 * w, -28, 100 * w, -45)
    ctx.curve_to(95 * w, -120, 75 * w, -200, 62 * w, -305)
    ctx.curve_to(30, -322, -30, -322, -62 * w, -305)
    ctx.close_path()

def draw_pear(ctx, x, y, r, bite=0.0):
    ctx.push_group()
    ctx.new_path(); circ(ctx, x, y, r); circ(ctx, x, y - r * 0.95, r * 0.62)
    setc(ctx, '#c9d64a'); ctx.fill()
    ctx.move_to(x - r * 0.6, y - r * 1.2); ctx.curve_to(x - r * 1.05, y - r * 0.3, x - r, y + r, x, y + r)
    ctx.curve_to(x + r, y + r, x + r * 1.05, y - r * 0.3, x + r * 0.6, y - r * 1.2)
    ctx.curve_to(x + r * 0.5, y - r * 1.75, x - r * 0.5, y - r * 1.75, x - r * 0.6, y - r * 1.2)
    setc(ctx, '#c9d64a'); ctx.fill_preserve(); setc(ctx, OUT); ctx.set_line_width(3); ctx.stroke()
    circ(ctx, x - r * 0.35, y - r * 0.2, r * 0.22); setc(ctx, '#f4f7b0', 0.7); ctx.fill()
    ctx.move_to(x, y - r * 1.55); ctx.line_to(x + r * 0.15, y - r * 2.0); setc(ctx, '#5a3a20'); ctx.set_line_width(4); ctx.stroke()
    k = int(bite * 4.999)
    if k:
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        for i in range(k):
            circ(ctx, x + r * 1.0, y - r * 1.2 + i * r * 0.6, r * 0.45); ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source(); ctx.paint()

def draw_coin(ctx, x, y, r, spin=1.0, a=1.0):
    rx = max(r * abs(spin), 2)
    ell(ctx, x, y, rx, r); setc(ctx, '#f5c542', a); ctx.fill_preserve(); setc(ctx, '#9a6a12', a); ctx.set_line_width(3); ctx.stroke()
    ell(ctx, x, y, rx * 0.65, r * 0.65); setc(ctx, '#e0a92a', a); ctx.set_line_width(2.5); ctx.stroke()
    ell(ctx, x - rx * 0.3, y - r * 0.35, rx * 0.18, r * 0.18); setc(ctx, '#fff6c8', a); ctx.fill()

def draw_seeds(ctx, x, y, s=1.0, t=0.0):
    glow(ctx, x, y - 8 * s, 70 * s, '#ffe27a', 0.55 + 0.15 * math.sin(t * 5))
    for i, (dx, dy, ang) in enumerate([(-14, -6, .4), (0, -14, -.3), (14, -5, .8), (-6, 4, -.9), (9, 6, .2)]):
        ctx.save(); ctx.translate(x + dx * s, y + dy * s - 10 * s); ctx.rotate(ang)
        ell(ctx, 0, 0, 6 * s, 9 * s); setc(ctx, '#5b3517'); ctx.fill_preserve(); setc(ctx, '#2a160a'); ctx.set_line_width(1.5); ctx.stroke()
        ctx.restore()
    for k in range(3):
        a = t * 2 + k * 2.1
        sx, sy = x + math.cos(a) * 34 * s, y - 12 * s + math.sin(a * 1.3) * 26 * s
        sparkle(ctx, sx, sy, 7 * s, 0.8)

def sparkle(ctx, x, y, r, a=1.0):
    ctx.move_to(x, y - r); ctx.line_to(x + r * 0.25, y - r * 0.25); ctx.line_to(x + r, y); ctx.line_to(x + r * 0.25, y + r * 0.25)
    ctx.line_to(x, y + r); ctx.line_to(x - r * 0.25, y + r * 0.25); ctx.line_to(x - r, y); ctx.line_to(x - r * 0.25, y - r * 0.25)
    ctx.close_path(); setc(ctx, '#fff3b0', a); ctx.fill()

def draw_person(ctx, name, x, y, s, p, t):
    st = STY[name]
    f = p['face']; w = st['w']; skin = st['skin']
    tr = p['tremble']
    dx = tr * 7 * math.sin(t * 57); dy = tr * 3 * math.sin(t * 43)
    bob = 0.0
    if p['walk'] is not None: bob = -abs(math.sin(p['walk'])) * 12
    ox, oy = x + dx * s, y + (dy + bob) * s
    ctx.save(); ctx.translate(ox, oy); ctx.scale(s * f, s)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    # back arm
    arm(ctx, -38 * w, -285, p['ba'][0], p['ba'][1], dark(st['robe'], 0.72), dark(skin, 0.88))
    # legs
    for i, sg in ((0, -1), (1, 1)):
        off = lift = 0
        if p['walk'] is not None:
            ph = p['walk'] + i * PI
            off = 24 * math.sin(ph); lift = max(0, math.cos(ph)) * 12
        lx = sg * 22 + off
        ctx.rectangle(lx - 15, -130, 30, 120 - lift); fs(ctx, st['pants'], 4)
        ell(ctx, lx + 12, -12 - lift, 30, 14); fs(ctx, st['shoe'], 4)
    # robe
    robe_path(ctx, w); setc(ctx, st['robe']); ctx.fill()
    ctx.save(); robe_path(ctx, w); ctx.clip()
    ctx.rectangle(6, -330, 22, 300); setc(ctx, st['trim']); ctx.fill()
    ctx.rectangle(-150, -64, 300, 30); setc(ctx, st['trim']); ctx.fill()
    ctx.rectangle(-150, -190, 300, 30); setc(ctx, st['sash']); ctx.fill()
    if st.get('patches'):
        ctx.rectangle(-60, -130, 34, 30); setc(ctx, '#a8865a'); ctx.fill()
        ctx.rectangle(40, -250, 28, 26); setc(ctx, '#6e5236'); ctx.fill()
        setc(ctx, OUT, 0.5); ctx.set_line_width(2)
        ctx.rectangle(-60, -130, 34, 30); ctx.stroke(); ctx.rectangle(40, -250, 28, 26); ctx.stroke()
    ctx.rectangle(-150, -330, 75, 300); setc(ctx, '#000', 0.08); ctx.fill()
    ctx.restore()
    robe_path(ctx, w); setc(ctx, OUT); ctx.set_line_width(6); ctx.stroke()
    # neck & head
    ctx.rectangle(-18, -330, 36, 34); fs(ctx, skin, 4)
    hx, hy, R = 8, -385, 70
    if st['hat'] == 'scarf':
        ell(ctx, hx - 6, hy + 10, R + 20, R + 30); fs(ctx, st['hatc'], 5)
    circ(ctx, hx, hy, R); fs(ctx, skin, 5)
    if st['hat'] != 'scarf':
        ell(ctx, hx - 34, hy + 8, 12, 17); fs(ctx, skin, 4)
    bc = st['beardc']
    if st['beard'] == 'stubble':
        ctx.save(); circ(ctx, hx, hy, R - 2); ctx.clip()
        ell(ctx, hx + 18, hy + 45, 62, 40); setc(ctx, bc, 0.35); ctx.fill(); ctx.restore()
    elif st['beard'] in ('long', 'pointy', 'short'):
        tip = {'long': (hx + 18, hy + 135), 'pointy': (hx + 34, hy + 120), 'short': (hx + 22, hy + 82)}[st['beard']]
        ctx.move_to(hx - 42, hy + 8)
        ctx.curve_to(hx - 40, hy + 60, tip[0] - 40, tip[1] - 10, tip[0], tip[1])
        ctx.curve_to(tip[0] + 40, tip[1] - 10, hx + 72, hy + 60, hx + 66, hy + 18)
        ctx.curve_to(hx + 50, hy + 40, hx + 10, hy + 40, hx - 42, hy + 8)
        ctx.close_path(); fs(ctx, bc, 4)
    # mouth
    mx, my = hx + 32, hy + 38
    m = p['mouth']
    if m > 0.08:
        ell(ctx, mx, my, 12 + 4 * m, 3 + 14 * m); fs(ctx, '#6b1d1d', 3)
        ell(ctx, mx, my + 4 + 6 * m, 7 + 2 * m, 2 + 4 * m); setc(ctx, '#d0605e'); ctx.fill()
    else:
        sm_ = p['smile']
        ctx.move_to(mx - 15, my); ctx.curve_to(mx - 6, my + 13 * sm_, mx + 6, my + 13 * sm_, mx + 15, my)
        setc(ctx, '#5a1d18'); ctx.set_line_width(4.5); ctx.stroke()
    if st['beard'] in ('long', 'pointy', 'short', 'mustache'):
        for sgn in (-1, 1):
            ctx.move_to(mx, my - 12); ctx.curve_to(mx + sgn * 14, my - 20, mx + sgn * 26, my - 12, mx + sgn * 30, my)
            ctx.curve_to(mx + sgn * 20, my - 6, mx + sgn * 10, my - 6, mx, my - 8); ctx.close_path(); fs(ctx, bc, 3)
    # nose
    ell(ctx, hx + 56, hy + 12, 14, 12); fs(ctx, dark(skin, 0.93), 4)
    # cheeks
    circ(ctx, hx + 2, hy + 24, 11); setc(ctx, '#e06a5a', 0.25); ctx.fill()
    # eyes
    blink = p['blink'] if p['blink'] is not None else ((t + SEED[name]) % 3.7) < 0.13
    wide = p['wide']
    for ex in (hx + 2, hx + 36):
        ey = hy - 8
        if blink:
            ctx.move_to(ex - 11, ey); ctx.line_to(ex + 11, ey); setc(ctx, OUT); ctx.set_line_width(4); ctx.stroke()
        else:
            ell(ctx, ex, ey, 11 + 2 * wide, 14 + 4 * wide); fs(ctx, '#ffffff', 3)
            circ(ctx, ex + 3.5 * p['look'], ey + 1, 6.5 - wide * 1.5); setc(ctx, '#1b120e'); ctx.fill()
            circ(ctx, ex + 3.5 * p['look'] + 2, ey - 2, 2); setc(ctx, '#fff'); ctx.fill()
    b = p['brow']
    for ex, inner in ((hx + 2, 1), (hx + 36, -1)):
        ey = hy - 30 - 4 * wide
        ix, ox_ = ex + inner * 12, ex - inner * 12
        ctx.move_to(ox_, ey + b * 3); ctx.line_to(ix, ey - b * 9)
        setc(ctx, bc if st['beard'] != 'none' else '#3a2418'); ctx.set_line_width(6); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    # hats
    hat = st['hat']; hc = st['hatc']
    if hat == 'cap':
        ctx.new_path(); ctx.arc(hx, hy - 8, R + 5, PI * 1.0, PI * 2.0); ctx.close_path(); fs(ctx, hc, 5)
        ctx.rectangle(hx - R - 6, hy - 18, 2 * R + 12, 16); fs(ctx, dark(hc, 0.8), 4)
    elif hat == 'bigturban':
        circ(ctx, hx, hy - 128, 30); fs(ctx, '#b5202a', 4)
        ell(ctx, hx, hy - 78, 98, 62); fs(ctx, hc, 5)
        for k in range(3):
            ctx.new_path(); ctx.arc(hx - 10, hy - 10 + k * 18 - 40, 95 - k * 12, PI * 1.15, PI * 1.85)
            setc(ctx, '#d8cfb8'); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(hx + 40, hy - 85); ctx.curve_to(hx + 10, hy - 150, hx + 60, hy - 190, hx + 30, hy - 225)
        ctx.curve_to(hx + 95, hy - 180, hx + 70, hy - 130, hx + 48, hy - 85); ctx.close_path(); fs(ctx, '#3fb1a8', 4)
        circ(ctx, hx + 44, hy - 78, 16); fs(ctx, '#f2c14e', 4); circ(ctx, hx + 44, hy - 78, 9); setc(ctx, '#d62828'); ctx.fill()
    elif hat == 'kavuk':
        rrect(ctx, hx - 46, hy - 190, 92, 130, 30); fs(ctx, hc, 5)
        ctx.move_to(hx - 46, hy - 100); ctx.line_to(hx + 46, hy - 160); setc(ctx, '#c8a04a'); ctx.set_line_width(12); ctx.stroke()
        ell(ctx, hx, hy - 62, 84, 34); fs(ctx, '#2e7d4f', 5)
    elif hat == 'turban':
        ell(ctx, hx, hy - 66, 84, 50); fs(ctx, hc, 5)
        ctx.new_path(); ctx.arc(hx - 6, hy - 50, 70, PI * 1.15, PI * 1.85); setc(ctx, '#cfc3a8'); ctx.set_line_width(4); ctx.stroke()
    elif hat == 'fez':
        ctx.move_to(hx - 52, hy - 50); ctx.line_to(hx + 52, hy - 50); ctx.line_to(hx + 40, hy - 125); ctx.line_to(hx - 40, hy - 125)
        ctx.close_path(); fs(ctx, hc, 5)
        ctx.move_to(hx, hy - 125); ctx.curve_to(hx - 30, hy - 125, hx - 50, hy - 105, hx - 52, hy - 80)
        setc(ctx, '#1b120e'); ctx.set_line_width(5); ctx.stroke(); circ(ctx, hx - 52, hy - 76, 7); setc(ctx, '#1b120e'); ctx.fill()
    elif hat == 'scarf':
        ctx.new_path(); ctx.arc(hx - 4, hy + 2, R + 14, PI * 1.02, PI * 1.98); ctx.close_path(); fs(ctx, hc, 5)
    # sweat
    if p['sweat'] > 0.01:
        for k, sx in enumerate((-35, 15, 62)):
            ph = (t * 1.1 + k / 3) % 1
            yy = hy - 45 + ph * 85; a = p['sweat'] * (1 - ph)
            ctx.move_to(hx + sx, yy - 14); ctx.curve_to(hx + sx + 9, yy, hx + sx + 9, yy + 8, hx + sx, yy + 8)
            ctx.curve_to(hx + sx - 9, yy + 8, hx + sx - 9, yy, hx + sx, yy - 14)
            setc(ctx, '#8fd3ff', a); ctx.fill_preserve(); setc(ctx, '#2a6a9a', a); ctx.set_line_width(2); ctx.stroke()
    # front arm + item
    hxl, hyl = arm(ctx, 40 * w, -285, p['fa'][0], p['fa'][1], st['robe'], skin)
    if p['item'] == 'pear':
        draw_pear(ctx, hxl + 4, hyl - 22, 22, p['bite'])
    ctx.restore()
    return dict(hand=(ox + f * s * hxl, oy + s * hyl), head=(ox + f * s * hx, oy + s * (hy - R)),
                mouth=(ox + f * s * mx, oy + s * my))

# ---------------------------------------------------------------- trees
def draw_tree(ctx, x, y, g, wither, kind, t, s=1.0):
    if g <= 0.01: return
    th = 330 * s * g
    ctx.move_to(x - 30 * s * g, y); ctx.curve_to(x - 18 * s * g, y - th * 0.5, x - 14 * s * g, y - th * 0.8, x - 10 * s * g, y - th)
    ctx.line_to(x + 10 * s * g, y - th); ctx.curve_to(x + 14 * s * g, y - th * 0.8, x + 18 * s * g, y - th * 0.5, x + 30 * s * g, y)
    ctx.close_path(); fs(ctx, '#7a4a2a', 5 * s)
    cy = y - th - 40 * s * g + wither * 40 * s
    base = '#3f9b3a' if kind == 'gold' else '#5b2a6e'
    col = mix(base, '#8a6a3a', wither)
    r = 105 * s * g * (1 - 0.25 * wither)
    blobs = [(0, -60), (-95, 0), (95, 0), (-55, 55), (55, 55), (0, 25), (-60, -45), (60, -45)]
    for bx, by in blobs:
        circ(ctx, x + bx * s * g, cy + by * s * g, r); setc(ctx, OUT); ctx.set_line_width(8 * s); ctx.stroke()
    for bx, by in blobs:
        circ(ctx, x + bx * s * g, cy + by * s * g, r); setc(ctx, col); ctx.fill()
    for bx, by in blobs[:5]:
        circ(ctx, x + bx * s * g - r * 0.3, cy + by * s * g - r * 0.3, r * 0.35); setc(ctx, '#ffffff', 0.12); ctx.fill()
    fg = seg(g, 0.75, 1.0)
    if fg > 0:
        fruits = [(-90, 30), (-30, -60), (40, 10), (95, 40), (-40, 80), (60, -70), (10, 85)]
        for i, (fx, fy) in enumerate(fruits):
            px, py = x + fx * s, cy + fy * s
            fall = wither ** 1.5 * (500 + i * 60) * s
            a = 1 - wither
            if a <= 0: continue
            if kind == 'gold':
                glow(ctx, px, py + fall, 40 * s * fg, '#ffe27a', 0.5 * a)
                ctx.save(); ctx.translate(px, py + fall); ctx.scale(fg * s * 1.1, fg * s * 1.1)
                ctx.push_group()
                circ(ctx, 0, 0, 20); circ(ctx, 0, -18, 13); setc(ctx, '#f5c542'); ctx.fill()
                ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
                circ(ctx, 0, 0, 20); circ(ctx, 0, -18, 13); setc(ctx, '#9a6a12', a); ctx.set_line_width(3); ctx.stroke()
                circ(ctx, -6, -4, 5); setc(ctx, '#fff6c8', a); ctx.fill()
                ctx.restore()
                sparkle(ctx, px + 22 * s * math.cos(t * 3 + i), py - 20 * s + 10 * s * math.sin(t * 4 + i), 9 * s * fg, 0.9 * a)
            else:
                circ(ctx, px, py + fall, 22 * s * fg); fs(ctx, '#7d2e9e', 3 * s, a)
                circ(ctx, px, py + fall - 2 * s, 10 * s * fg); setc(ctx, '#f0f0f0', a); ctx.fill()
                for ddx in (-4, 4):
                    circ(ctx, px + ddx * s * fg, py + fall - 4 * s, 2.6 * s * fg); setc(ctx, '#111', a); ctx.fill()

# ---------------------------------------------------------------- backgrounds
def cloud(ctx, x, y, s):
    for dx, dy, r in ((0, 0, 60), (60, -20, 70), (130, 0, 55), (60, 20, 60)):
        circ(ctx, x + dx * s, y + dy * s, r * s)
    setc(ctx, '#ffffff', 0.9); ctx.fill()

def bg_market(ctx, t):
    ctx.rectangle(-500, -900, 2600, 2100)
    ctx.set_source(lgrad(ctx, 0, -700, 0, 1150, [(0, '#7ec8f0'), (1, '#fde8c0')])); ctx.fill()
    glow(ctx, 1250, 60, 260, '#fff2b0', 0.8); circ(ctx, 1250, 60, 90); setc(ctx, '#ffd166'); ctx.fill()
    for cx0, cy, s in ((100, 120, 1.0), (750, -80, 1.3), (1400, 260, 0.9)):
        cloud(ctx, (cx0 + t * 14) % 2400 - 450, cy, s)
    sil = '#e3c49b'
    setc(ctx, sil)
    ctx.new_path(); ctx.arc(1150, 960, 150, PI, 2 * PI); ctx.fill()
    ctx.rectangle(980, 940, 340, 220); ctx.fill()
    for mxp in (930, 1370):
        ctx.rectangle(mxp - 14, 640, 28, 520); ctx.fill()
        ctx.move_to(mxp - 20, 645); ctx.line_to(mxp, 560); ctx.line_to(mxp + 20, 645); ctx.close_path(); ctx.fill()
    setc(ctx, '#d9b183')
    for i, (hx, hh, hw) in enumerate(((-300, 260, 220), (-60, 330, 200), (180, 230, 230), (450, 300, 190), (1500, 280, 230))):
        ctx.rectangle(hx, 1160 - hh, hw, hh); setc(ctx, '#d9b183'); ctx.fill()
        for wx in range(hx + 30, hx + hw - 40, 70):
            rrect(ctx, wx, 1160 - hh + 50, 34, 50, 12); setc(ctx, '#9b6f45'); ctx.fill()
    for sx, col in ((-280, '#3d6fb6'), (60, '#2e7d4f'), (1080, '#c75b39'), (1400, '#7b2d8e')):
        ctx.rectangle(sx + 10, 1000, 10, 160); ctx.rectangle(sx + 230, 1000, 10, 160); setc(ctx, '#7a5230'); ctx.fill()
        for k in range(5):
            ctx.rectangle(sx + k * 50, 960, 50, 50); setc(ctx, col if k % 2 == 0 else '#f6efe0'); ctx.fill()
        ctx.rectangle(sx, 1090, 250, 70); fs(ctx, '#a87a4d', 4)
        for k in range(6):
            circ(ctx, sx + 25 + k * 40, 1088, 16); setc(ctx, ['#e85d3f', '#f5a623', '#7bb342'][k % 3]); ctx.fill()
    ctx.rectangle(-500, 1150, 2600, 1300); setc(ctx, '#d4ad74'); ctx.fill()
    rnd = random.Random(3)
    for _ in range(140):
        ell(ctx, rnd.uniform(-450, 2000), rnd.uniform(1170, 2300), rnd.uniform(12, 28), rnd.uniform(5, 10))
        setc(ctx, '#c19a62', 0.7); ctx.fill()
    # main stall
    for px in (600, 920):
        ctx.rectangle(px - 9, 760, 18, 400); fs(ctx, '#7a5230', 4)
    for k in range(7):
        ctx.new_path(); ctx.move_to(570 + k * 54, 720); ctx.line_to(624 + k * 54, 720); ctx.line_to(624 + k * 54, 790)
        ctx.arc(597 + k * 54, 790, 27, 0, PI); ctx.close_path(); fs(ctx, '#d64545' if k % 2 == 0 else '#fbf3e4', 4)
    ctx.rectangle(610, 1080, 300, 150); fs(ctx, '#9c6b3d', 5)
    for k in range(1, 3):
        ctx.move_to(610, 1080 + k * 50); ctx.line_to(910, 1080 + k * 50); setc(ctx, OUT, 0.4); ctx.set_line_width(3); ctx.stroke()
    ell(ctx, 840, 1075, 62, 22); fs(ctx, '#b8864b', 4)
    for k in range(5):
        circ(ctx, 800 + k * 20, 1052 - (k % 2) * 10, 18); fs(ctx, '#d93a2b', 3)
    for (px, py) in ((660, 1050), (690, 1040), (715, 1052)):
        draw_pear(ctx, px, py, 18)
    if t < 3.75:
        draw_pear(ctx, 742, 1046, 18)
    ell(ctx, 690, 1075, 66, 22); fs(ctx, '#b8864b', 4)

def bg_palace(ctx, t):
    ctx.rectangle(-500, -900, 2600, 2100)
    ctx.set_source(lgrad(ctx, 0, -600, 0, 1150, [(0, '#f6e2bb'), (1, '#e6bf8a')])); ctx.fill()
    for wx in (180, 1320):
        ctx.new_path(); ctx.move_to(wx - 120, 920); ctx.line_to(wx - 120, 420); ctx.arc(wx, 420, 120, PI, 2 * PI)
        ctx.line_to(wx + 120, 920); ctx.close_path()
        ctx.set_source(lgrad(ctx, 0, 300, 0, 920, [(0, '#8fd3f4'), (1, '#e6f6ff')])); ctx.fill_preserve()
        setc(ctx, '#c8963e'); ctx.set_line_width(14); ctx.stroke()
        ctx.save(); ctx.new_path(); ctx.move_to(wx - 120, 920); ctx.line_to(wx - 120, 420); ctx.arc(wx, 420, 120, PI, 2 * PI)
        ctx.line_to(wx + 120, 920); ctx.close_path(); ctx.clip()
        setc(ctx, '#b07a2e', 0.8); ctx.set_line_width(5)
        for k in range(-8, 9):
            ctx.move_to(wx + k * 40 - 300, 300); ctx.line_to(wx + k * 40 + 300, 920); ctx.stroke()
            ctx.move_to(wx + k * 40 + 300, 300); ctx.line_to(wx + k * 40 - 300, 920); ctx.stroke()
        ctx.restore()
    ctx.rectangle(-500, 960, 2600, 200); setc(ctx, '#2f6f9f'); ctx.fill()
    for k in range(-10, 40):
        x0 = k * 70
        ctx.move_to(x0, 1000); ctx.line_to(x0 + 30, 1060); ctx.line_to(x0, 1120); ctx.line_to(x0 - 30, 1060); ctx.close_path()
        setc(ctx, '#e9f1f7'); ctx.fill()
        circ(ctx, x0 + 35, 1060, 8); setc(ctx, '#f2c14e'); ctx.fill()
    ctx.rectangle(-500, 950, 2600, 14); setc(ctx, '#c8963e'); ctx.fill()
    for cx_ in (-30, 470, 1030, 1530):
        ctx.rectangle(cx_ - 32, -700, 64, 1860)
        ctx.set_source(lgrad(ctx, cx_ - 32, 0, cx_ + 32, 0, [(0, '#c98f45'), (0.5, '#f1c879'), (1, '#b97e36')])); ctx.fill()
        ctx.rectangle(cx_ - 48, 1100, 96, 60); fs(ctx, '#c8963e', 4)
        ctx.rectangle(cx_ - 48, 200, 96, 40); fs(ctx, '#c8963e', 4)
    for k in range(-4, 16):
        ctx.new_path(); ctx.arc(k * 160 + 80, 100, 80, 0, PI); setc(ctx, '#a3202a'); ctx.set_line_width(28); ctx.stroke()
    ctx.rectangle(-500, -900, 2600, 1000); setc(ctx, '#a3202a'); ctx.fill()
    ctx.rectangle(-500, 90, 2600, 12); setc(ctx, '#f2c14e'); ctx.fill()
    for lx in (620, 900):
        ctx.move_to(lx, 100); ctx.line_to(lx, 330); setc(ctx, '#7a5a2a'); ctx.set_line_width(4); ctx.stroke()
        glow(ctx, lx, 370, 140 + 10 * math.sin(t * 3 + lx), '#ffd98a', 0.5)
        ctx.move_to(lx - 30, 340); ctx.line_to(lx + 30, 340); ctx.line_to(lx + 18, 400); ctx.line_to(lx - 18, 400); ctx.close_path()
        fs(ctx, '#d9a03b', 4)
    # throne
    ctx.new_path(); ctx.move_to(610, 1170); ctx.line_to(610, 800); ctx.curve_to(610, 700, 700, 650, 750, 600)
    ctx.curve_to(800, 650, 890, 700, 890, 800); ctx.line_to(890, 1170); ctx.close_path(); fs(ctx, '#e0a83b', 6)
    ctx.new_path(); ctx.move_to(645, 1170); ctx.line_to(645, 820); ctx.curve_to(645, 740, 715, 700, 750, 665)
    ctx.curve_to(785, 700, 855, 740, 855, 820); ctx.line_to(855, 1170); ctx.close_path(); fs(ctx, '#b5202a', 4)
    circ(ctx, 750, 610, 22); fs(ctx, '#3fb1a8', 4)
    for ax in (570, 860):
        rrect(ctx, ax, 1010, 70, 160, 14); fs(ctx, '#e0a83b', 5)
    # floor
    ctx.rectangle(-500, 1150, 2600, 1300); setc(ctx, '#b07a4f'); ctx.fill()
    setc(ctx, '#9a6a42'); ctx.set_line_width(3)
    for k in range(-10, 40):
        ctx.move_to(k * 90, 1150); ctx.line_to(k * 90 - 200, 2300); ctx.stroke()
    ctx.rectangle(-500, 1195, 2600, 150); setc(ctx, '#9b1d20'); ctx.fill()
    ctx.rectangle(-500, 1205, 2600, 8); ctx.rectangle(-500, 1327, 2600, 8); setc(ctx, '#f2c14e'); ctx.fill()
    for k in range(-10, 40):
        x0 = k * 110
        ctx.move_to(x0, 1235); ctx.line_to(x0 + 30, 1270); ctx.line_to(x0, 1305); ctx.line_to(x0 - 30, 1270); ctx.close_path()
        setc(ctx, '#e8b44a', 0.8); ctx.fill()

# ---------------------------------------------------------------- scene logic
def shot(t, shots):
    cur = shots[0]
    for s_ in shots:
        if t >= s_[0]: cur = s_
    t0, cx, z, Fs = cur
    z *= 1 + 0.012 * (t - t0)
    return cx, z, Fs

def apply_cam(ctx, cx, z, Fs):
    ctx.translate(W / 2, Fs); ctx.scale(z, z); ctx.translate(-cx, -FLOOR)

def to_screen(p, cam):
    cx, z, Fs = cam
    return (W / 2 + (p[0] - cx) * z, Fs + (p[1] - FLOOR) * z)

def gest(t, k):
    return (0.45 + 0.35 * math.sin(t * 2.3 + k), 0.7 + 0.45 * math.sin(t * 3.1 + 2 * k))

def walkph(t, keys, speed=9.0):
    return t * speed if moving(t, keys) else None

def exclaim(ctx, x, y, a):
    if a <= 0: return
    ctx.save(); ctx.translate(x, y)
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(90)
    ctx.move_to(-14, 0); ctx.text_path('!'); setc(ctx, '#d62828', a); ctx.fill_preserve()
    setc(ctx, '#fff', a); ctx.set_line_width(4); ctx.stroke(); ctx.restore()

def scene_market(ctx, t):
    akeys = [(0, -150), (3.0, 560)]
    ax = kf(t, akeys)
    if t < 6.8:
        cx = clamp(ax + 80, 540, 960); cam = (cx, 1.0, 1350)
    elif t < 7.9:
        cam = (600, 1.35 * (1 + 0.03 * (t - 6.8)), 1520)
    else:
        cam = (720, 0.75, 1300)
    ctx.save(); apply_cam(ctx, *cam)
    bg_market(ctx, t)
    # crowd
    people = []
    c1k = [(7.9, 1150), (9.8, 700)]; c2k = [(8.1, 1290), (10.0, 830)]; c3k = [(8.3, 1420), (10.6, 420)]
    for name, keys, idle_face, k in (('c1', c1k, 1, 0), ('c2', c2k, -1, 1), ('c3', c3k, -1, 2)):
        p = base_pose(); x = kf(t, keys)
        p['walk'] = walkph(t, keys, 11)
        if t < 7.5:
            p['face'] = idle_face; p['smile'] = 0.4
            p['fa'] = (0.3 + 0.2 * math.sin(t * 2 + k), 0.6)
        else:
            p['face'] = -1 if not (name == 'c3' and t > 10.6) else 1
            p['brow'] = -0.7; p['smile'] = -0.4; p['wide'] = 0.6
            if t > 9.6: p['fa'] = (1.3, -0.2); p['ba'] = (0.9, 0.2)
            elif t > 7.6 and t < 8.5 and name == 'c1': p['fa'] = (1.7, -0.1)
        people.append((name, x, p))
    p = base_pose(); p['walk'] = walkph(t, akeys, 9)
    p['smile'] = 0.2; p['brow'] = 0.3
    if 3.0 <= t < 3.8:
        u = seg(t, 3.0, 3.5); p['fa'] = (lerp(0.12, 1.22, u), lerp(0.25, -0.3, u)); p['look'] = 1
    elif 3.8 <= t < 6.7:
        u = seg(t, 3.8, 4.3); p['fa'] = (lerp(1.22, 0.3, u), lerp(-0.3, 3.0, u))
        p['item'] = 'pear'; p['bite'] = clamp((t - 4.3) / 2.3)
        if t > 4.3: p['mouth'] = 0.3 * abs(math.sin(t * 9)); p['smile'] = 0.6
    if 6.7 <= t < 7.9:
        p['look'] = math.sin(t * 6) * 1.3; p['smile'] = -0.3; p['brow'] = 0.8
    if t >= 7.9:
        p['tremble'] = 0.35; p['brow'] = 1; p['wide'] = 0.8; p['mouth'] = 0.35; p['look'] = 1.2
        p['ba'] = (-0.6, 1.2); p['fa'] = (0.9, 1.6)
    people.append(('adam', ax, p))
    heads = {}
    for name, x, pp in people:
        r = draw_person(ctx, name, x, FLOOR, 1.0, pp, t); heads[name] = r['head']
    for name in ('c1', 'c2', 'c3'):
        a = seg(t, 7.55, 7.75) * (1 - seg(t, 8.8, 9.1))
        exclaim(ctx, heads[name][0] - 10, heads[name][1] - 70, a)
    ctx.restore()
    return None

PAL_SHOTS = [
    (12.0, 600, .72, 1300), (15.7, 720, 1.25, 1520), (22.42, 330, 1.25, 1520), (30.7, 720, 1.25, 1520),
    (36.06, 330, 1.25, 1520), (39.4, 720, 1.25, 1520), (41.62, 380, 1.5, 1640), (47.44, 430, .95, 1360),
    (52.9, 720, 1.25, 1520), (61.56, 330, 1.25, 1520), (63.6, 720, 1.25, 1520), (64.98, 330, 1.2, 1500),
    (71.0, 430, .95, 1360), (77.48, 610, .9, 1330), (87.74, 740, 1.3, 1540), (93.4, 850, .95, 1350),
    (96.48, 960, 1.25, 1520), (104.54, 1060, .95, 1350), (108.16, 1160, 1.25, 1520), (112.78, 750, .72, 1300),
    (116.84, 620, .85, 1330), (124.84, 750, .72, 1300), (129.06, 620, .9, 1330)]

THROWS = [(120.6, 'pad'), (125.2, 'pad'), (125.7, 'vezir'), (126.2, 'veznedar'), (127.0, 'pad'),
          (127.6, 'vezir'), (128.0, 'veznedar'), (128.4, 'pad'), (128.7, 'vezir')]
SEED_HOLD = [(41.62, 'adam'), (88.6, 'pad'), (95.2, 'vezir'), (107.3, 'veznedar'), (113.0, None)]

def pile_pos(i, ax):
    r = random.Random(i * 7 + 1)
    return (ax + 60 + r.uniform(-55, 55), FLOOR - 6 - (i // 5) * 9 + r.uniform(-4, 4))

def scene_palace(ctx, t):
    cam = shot(t, PAL_SHOTS)
    ctx.save(); apply_cam(ctx, *cam)
    bg_palace(ctx, t)
    people = []
    # crowd escort
    if t < 18.5:
        for name, ink, outk, k in (('c3', [(12, -150), (13.4, 20)], [(16.4, 20), (17.8, -420)], 2),
                                   ('c2', [(12, -60), (13.4, 120)], [(16.2, 120), (17.6, -360)], 1),
                                   ('c1', [(12, 300), (13.4, 470)], [(16.0, 470), (18.2, -300)], 0)):
            p = base_pose()
            if t < 16.0:
                x = kf(t, ink); p['walk'] = walkph(t, ink, 11); p['face'] = 1
            else:
                x = kf(t, outk); p['walk'] = walkph(t, outk, 11); p['face'] = -1
            p['mouth'] = mouth_of(name, t)
            if name == 'c1' and 12.8 < t < 15.7: p['fa'] = (1.5 + 0.15 * math.sin(t * 4), -0.2)
            people.append((name, x, p, 0.96))
    # adam
    akeys = [(12, 140), (13.4, 280), (77.5, 280), (79.0, 470)]
    ax = kf(t, akeys)
    p = base_pose(); p['walk'] = walkph(t, akeys, 9); p['mouth'] = mouth_of('adam', t); p['face'] = 1
    if t < 22.42: p['brow'] = 0.8; p['smile'] = -0.3
    if mouth_of('adam', t) > 0 or speaker(t) == 'adam':
        p['ba'] = gest(t, 1)[0] * -1, 0.5
    if 41.62 <= t < 88.8:
        u = seg(t, 41.62, 42.3)
        p['fa'] = (lerp(0.12, 1.0, u) + 0.05 * math.sin(t * 2), lerp(0.25, -0.15, u))
        if 77.5 <= t: p['fa'] = (lerp(1.0, 1.45, seg(t, 77.5, 78.2)), -0.1)
    if 112.78 <= t < 116.84: p['smile'] = -0.1; p['brow'] = 0.4
    if 120.9 <= t:
        p['smile'] = 0.8; p['wide'] = 0.3; p['brow'] = -0.1
        p['fa'] = (0.95, 0.7); p['ba'] = (-0.95, -0.4)
        if speaker(t) == 'adam': p['smile'] = 0.6
    people.append(('adam', ax, p, 1.0))
    # padisah
    p = base_pose(); p['face'] = -1; p['mouth'] = mouth_of('pad', t)
    if speaker(t) == 'pad': p['fa'] = gest(t, 0)
    if 15.7 <= t < 22.42 or 30.7 <= t < 36.06: p['brow'] = -0.7; p['smile'] = -0.3
    if 39.4 <= t < 41.62: p['brow'] = 0.4
    if 77.48 <= t < 87.74: p['brow'] = 0.8; p['wide'] = 0.6; p['smile'] = -0.4
    if 87.74 <= t < 96.48:
        p['sweat'] = 1; p['tremble'] = 0.25; p['brow'] = 1; p['smile'] = -0.4
    if 88.0 <= t < 93.4: p['fa'] = (lerp(0.2, 1.3, seg(t, 88.0, 88.5)), -0.1)
    if 93.4 <= t < 112.78:
        p['face'] = 1; p['look'] = 1
        if t < 95.6: p['fa'] = (lerp(0.5, 1.3, seg(t, 93.6, 94.4)), -0.1)
        p['sweat'] = max(p['sweat'], 0.6 * (1 - seg(t, 100, 104)))
    if 112.78 <= t < 116.84: p['brow'] = 0.5; p['smile'] = -0.1; p['blink'] = (t % 2.0) < 0.15
    if t >= 116.84: p['smile'] = 0.55
    for tt, who in THROWS:
        if who == 'pad':
            sw = math.exp(-((t - tt) / 0.28) ** 2)
            if sw > 0.02: p['fa'] = (lerp(p['fa'][0], 1.8, sw), lerp(p['fa'][1], -0.4, sw))
    people.append(('pad', 750, p, 1.0))
    # vezir
    vkeys = [(93.6, 1060), (94.8, 950)]
    vx = kf(t, vkeys)
    p = base_pose(); p['face'] = -1; p['mouth'] = mouth_of('vezir', t); p['walk'] = walkph(t, vkeys, 10)
    p['fa'] = (0.1, 1.4); p['ba'] = (-0.1, 1.4); p['smile'] = 0.1
    if 87.74 <= t < 93.4: p['brow'] = 0.5; p['look'] = -1
    if 94.6 <= t < 112.78:
        p['tremble'] = 0.7 if t >= 96.48 else 0; p['brow'] = 1; p['sweat'] = 0.6; p['wide'] = 0.7; p['smile'] = -0.5
        p['fa'] = (lerp(0.1, 1.3, seg(t, 94.6, 95.1)), -0.1) if t < 96.5 else (0.85, -0.1)
        if t >= 104.3: p['face'] = 1
        if 106.5 <= t < 107.6: p['fa'] = (1.35, -0.1)
        if t >= 107.6: p['fa'] = (0.2, 0.3)
    if speaker(t) == 'vezir': p['ba'] = (-0.3 - 0.3 * math.sin(t * 3), 0.6)
    if t >= 116.84: p['smile'] = 0.4; p['fa'] = (0.12, 0.25); p['ba'] = (-0.1, 0.15)
    for tt, who in THROWS:
        if who == 'vezir':
            sw = math.exp(-((t - tt) / 0.28) ** 2)
            if sw > 0.02: p['fa'] = (lerp(p['fa'][0], 1.8, sw), -0.4 * sw)
    people.append(('vezir', vx, p, 1.0))
    # veznedar
    zkeys = [(105.8, 1300), (107.0, 1160)]
    zx = kf(t, zkeys)
    p = base_pose(); p['face'] = -1; p['walk'] = walkph(t, zkeys, 10)
    p['fa'] = (0.1, 1.4); p['ba'] = (-0.1, 1.4)
    if 96.48 <= t < 106.0: p['look'] = -1; p['brow'] = 0.4
    if 106.8 <= t < 112.78:
        p['fa'] = (lerp(0.2, 1.3, seg(t, 106.8, 107.2)), -0.1) if t < 107.8 else (0.85, -0.1)
        if t >= 107.6: p['tremble'] = 0.8; p['brow'] = 1; p['sweat'] = 0.7; p['wide'] = 0.8; p['smile'] = -0.5
        if t >= 109.5: p['look'] = math.sin(t * 7) * 1.4
    if 112.78 <= t < 116.84: p['fa'] = (0.1, 1.4); p['brow'] = 0.5
    if t >= 116.84: p['smile'] = 0.4; p['fa'] = (0.12, 0.25); p['ba'] = (-0.1, 0.15)
    for tt, who in THROWS:
        if who == 'veznedar':
            sw = math.exp(-((t - tt) / 0.28) ** 2)
            if sw > 0.02: p['fa'] = (lerp(p['fa'][0], 1.8, sw), -0.4 * sw)
    people.append(('veznedar', zx, p, 1.0))

    info = {}
    for name, x, pp, s in sorted(people, key=lambda q: q[3]):
        y = FLOOR - (15 if s < 1 else 0)
        info[name] = draw_person(ctx, name, x, y, s, pp, t)
    # seeds
    holder = None; prev = None; tchange = -10
    for tt, who in SEED_HOLD:
        if t >= tt: prev, holder, tchange = holder, who, tt
    if holder or (prev and t - tchange < 0.6):
        tgt = info[holder]['hand'] if holder else None
        if prev and t - tchange < 0.6 and holder:
            u = sm((t - tchange) / 0.6); a, b = info[prev]['hand'], tgt
            pos = (lerp(a[0], b[0], u), lerp(a[1], b[1], u) - 60 * math.sin(u * PI) - 28)
            draw_seeds(ctx, pos[0], pos[1], 1.0, t)
        elif holder:
            sc = seg(t, 41.62, 42.3) if holder == 'adam' else 1.0
            draw_seeds(ctx, tgt[0], tgt[1] - 28 * sc, sc, t)
    # coins
    landed = 0
    for i, (tt, who) in enumerate(THROWS):
        if t < tt: continue
        if t >= tt + 0.75:
            landed += 1; continue
        u = (t - tt) / 0.75
        st_ = (dict(pad=750, vezir=950, veznedar=1160)[who] - 90, FLOOR - 330)
        en = pile_pos(i, ax)
        x = lerp(st_[0], en[0], u); y = lerp(st_[1], en[1], u) - 260 * math.sin(u * PI)
        glow(ctx, x, y, 40, '#ffe27a', 0.5)
        draw_coin(ctx, x, y, 18, math.cos(t * 16))
    for i in range(landed):
        px, py = pile_pos(i, ax); ell(ctx, px, py + 4, 20, 7); setc(ctx, '#000', 0.15); ctx.fill()
        draw_coin(ctx, px, py, 16, 1.0)
        if i == landed - 1: sparkle(ctx, px + 10, py - 20, 12 * abs(math.sin(t * 5)), 0.9)
    ctx.restore()
    # thought bubbles (screen space)
    for t0, t1, kind in ((47.6, 52.8, 'gold'), (71.2, 77.3, 'poison')):
        if t0 <= t < t1:
            pop = seg(t, t0, t0 + 0.35) * (1 - seg(t, t1 - 0.3, t1))
            hs = to_screen(info['adam']['head'], cam)
            bx = clamp(hs[0] + 260, 330, 760); by = max(hs[1] - 330, 330)
            ctx.save(); ctx.translate(bx, by); ctx.scale(pop, pop); ctx.translate(-bx, -by)
            for k, (fx, r) in enumerate(((0.25, 14), (0.45, 22), (0.65, 30))):
                circ(ctx, lerp(hs[0] + 40, bx, fx), lerp(hs[1] - 20, by + 200, fx), r); fs(ctx, '#ffffff', 4)
            ctx.new_path()
            for k in range(12):
                a = k / 12 * 2 * PI
                circ(ctx, bx + math.cos(a) * 205, by + math.sin(a) * 175, 62)
            circ(ctx, bx, by, 200)
            setc(ctx, OUT); ctx.set_line_width(10); ctx.stroke_preserve(); setc(ctx, '#fffdf5'); ctx.fill()
            ctx.save(); ell(ctx, bx, by, 225, 195); ctx.clip()
            ell(ctx, bx, by + 175, 260, 50); setc(ctx, '#7a5230' if kind == 'gold' else '#4a3a3a'); ctx.fill()
            g = seg(t, t0 + 0.4, t0 + 2.8)
            draw_tree(ctx, bx, by + 150, g, 0, kind, t, s=0.55)
            ctx.restore(); ctx.restore()

def scene_field(ctx, t):
    dk = seg(t, 139.6, 141.8)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lgrad(ctx, 0, 0, 0, 1200, [(0, mix('#7ec8f0', '#2d2f45', dk)), (1, mix('#fde8c0', '#6b5a6e', dk))])); ctx.fill()
    a = 1 - dk
    glow(ctx, 850, 380, 260, '#fff2b0', 0.8 * a); circ(ctx, 850, 380, 95); setc(ctx, '#ffd166', a); ctx.fill()
    for cx0, cy, s in ((60, 300, 1.0), (600, 180, 1.2)):
        x = (cx0 + (t - 132) * 16) % 1400 - 250
        for dx, dy, r in ((0, 0, 60), (60, -20, 70), (130, 0, 55)):
            circ(ctx, x + dx * s, cy + dy * s, r * s)
        setc(ctx, mix('#ffffff', '#55556a', dk), 0.9); ctx.fill()
    ell(ctx, 200, 1250, 600, 260); setc(ctx, mix('#7fbf5a', '#6a6a50', dk)); ctx.fill()
    ell(ctx, 900, 1270, 600, 230); setc(ctx, mix('#5fa846', '#5a5a44', dk)); ctx.fill()
    ctx.rectangle(0, 1240, W, H); setc(ctx, mix('#7a5230', '#4a3a2a', dk)); ctx.fill()
    for k in range(6):
        y = 1300 + k * 110
        ctx.move_to(0, y); ctx.curve_to(300, y - 20, 700, y + 20, W, y); setc(ctx, '#5e3d22', 0.6); ctx.set_line_width(8); ctx.stroke()
    ell(ctx, 540, 1250, 120, 30); setc(ctx, '#5e3d22'); ctx.fill()
    if t < 134.2:
        y = kf(t, [(132.5, 250), (134.0, 1235)])
        draw_seeds(ctx, 540, y, 1.4, t)
    g = seg(t, 134.0, 139.0)
    draw_tree(ctx, 540, 1250, g, seg(t, 139.8, 143.6), 'gold', t, s=1.25)
    if t < 134.0:
        glow(ctx, 540, 1240, 120 * seg(t, 133.6, 134.0), '#ffe27a', 0.6)

def scene_factory(ctx, t):
    on = seg(t, 153.9, 156.0)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lgrad(ctx, 0, 0, 0, 1150, [(0, mix('#8a9097', '#7ec8f0', on)), (1, mix('#c3c6c9', '#fde8c0', on))])); ctx.fill()
    glow(ctx, 860, 300, 240, '#fff2b0', 0.8 * on); circ(ctx, 860, 300, 85); setc(ctx, '#ffd166', on); ctx.fill()
    ctx.rectangle(0, 1150, W, 200); setc(ctx, mix('#8c8c7a', '#7fbf5a', on)); ctx.fill()
    # smoke
    for ch in (300, 430):
        for k in range(6):
            ph = (t * 0.35 + k / 6) % 1
            circ(ctx, ch + ph * 120 + 15 * math.sin(t + k), 520 - ph * 420, 30 + ph * 60)
            setc(ctx, '#e8e8e8', on * (1 - ph) * 0.9); ctx.fill()
        ctx.rectangle(ch - 32, 520, 64, 300); fs(ctx, mix('#6f7176', '#a8453a', on), 5)
        ctx.rectangle(ch - 32, 560, 64, 20); setc(ctx, '#ffffff', 0.5); ctx.fill()
    body = mix('#8d8f94', '#c4553f', on)
    ctx.new_path(); ctx.move_to(130, 1170); ctx.line_to(130, 800)
    for k in range(5):
        x0 = 130 + k * 160
        ctx.line_to(x0 + 160, 720); ctx.line_to(x0 + 160, 800)
    ctx.line_to(930, 1170); ctx.close_path(); fs(ctx, body, 6)
    for row in range(2):
        for k in range(5):
            x0 = 170 + k * 150; y0 = 850 + row * 120
            ctx.rectangle(x0, y0, 90, 75); fs(ctx, mix('#3b3f45', '#ffd866', on), 4)
            if on < 0.5 and (k + row) % 3 == 0:
                ctx.move_to(x0 + 10, y0 + 10); ctx.line_to(x0 + 50, y0 + 45); ctx.line_to(x0 + 30, y0 + 70)
                setc(ctx, '#ffffff', 0.6); ctx.set_line_width(3); ctx.stroke()
            if on > 0.5:
                glow(ctx, x0 + 45, y0 + 37, 80, '#ffd866', 0.3 * on)
    rrect(ctx, 470, 1060, 120, 110, 8); fs(ctx, '#5a4030', 5)
    rrect(ctx, 420, 1000, 220, 60, 10)
    lab = 'ÜRETİM' if on > 0.5 else 'KAPALI'
    fs(ctx, '#2e8b57' if on > 0.5 else '#c0392b', 4)
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(40)
    e = ctx.text_extents(lab); ctx.move_to(530 - e[2] / 2 - e[0], 1030 - e[3] / 2 - e[1]); setc(ctx, '#ffffff'); ctx.show_text(lab)
    # gear
    ctx.save(); ctx.translate(840, 640); ctx.rotate(on * (t - 153.9) * 2.0)
    ctx.new_path()
    for k in range(10):
        a = k / 10 * 2 * PI
        ctx.save(); ctx.rotate(a); ctx.rectangle(-16, -95, 32, 30); ctx.restore()
    circ(ctx, 0, 0, 72); fs(ctx, mix('#6f7176', '#f2c14e', on), 5)
    circ(ctx, 0, 0, 22); fs(ctx, '#ffffff', 4)
    ctx.restore()
    # sea + ship
    ctx.rectangle(0, 1340, W, H); setc(ctx, mix('#4d6f86', '#3b8dc4', on)); ctx.fill()
    for k in range(8):
        y = 1380 + k * 70
        ctx.move_to(0, y)
        for xx in range(0, W + 60, 60):
            ctx.line_to(xx, y + 8 * math.sin(xx * 0.05 + t * 2 + k))
        setc(ctx, '#ffffff', 0.25); ctx.set_line_width(4); ctx.stroke()
    if 150.3 <= t < 158.0:
        sx = kf(t, [(150.3, 1500), (153.6, 620), (154.5, 620), (157.5, -700)])
        sy = 1400 + 6 * math.sin(t * 2)
        cols = ['#d64545', '#3d6fb6', '#f5a623', '#2e8b57', '#7b2d8e', '#d64545']
        for k in range(6):
            ctx.rectangle(sx - 220 + (k % 3) * 120, sy - 110 - (k // 3) * 70, 110, 66); fs(ctx, cols[k], 4)
        ctx.move_to(sx - 300, sy - 40); ctx.line_to(sx + 300, sy - 40); ctx.line_to(sx + 240, sy + 50); ctx.line_to(sx - 260, sy + 50)
        ctx.close_path(); fs(ctx, '#2c3e50', 5)
        ctx.set_font_size(42); e = ctx.text_extents('İTHALAT')
        ctx.move_to(sx - e[2] / 2, sy + 20); setc(ctx, '#ffffff'); ctx.show_text('İTHALAT')
    g = seg(t, 155.0, 159.5)
    draw_tree(ctx, 980, 1180, g, 0, 'gold', t, s=0.55)

def scene_end(ctx, t):
    ctx.rectangle(0, 0, W, H)
    g = cairo.RadialGradient(540, 900, 50, 540, 900, 1100)
    g.add_color_stop_rgb(0, *hexc('#6b3a1e')); g.add_color_stop_rgb(1, *hexc('#1e0f08')); ctx.set_source(g); ctx.fill()
    rnd = random.Random(5)
    for _ in range(40):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H); ph = rnd.uniform(0, 6)
        sparkle(ctx, x, (y - t * 30) % H, 6 + 4 * math.sin(t * 3 + ph), 0.5)
    ell(ctx, 540, 1150, 260, 40); setc(ctx, '#3a2414'); ctx.fill()
    draw_tree(ctx, 540, 1150, 1.0, 0, 'gold', t, s=1.15)
    a = seg(t, 162.0, 162.8)
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    for txt, y, size in (('Ben söyledim,', 1380, 84), ('anlayan anlasın.', 1490, 84)):
        ctx.set_font_size(size); e = ctx.text_extents(txt)
        ctx.move_to(540 - e[2] / 2 - e[0], y); ctx.text_path(txt)
        setc(ctx, '#1e0f08', a); ctx.set_line_width(12); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
        setc(ctx, '#f5c542', a); ctx.fill()

# ---------------------------------------------------------------- subtitles
TEXTS = [
    "Zamanın birinde aç bir insan pazardan geçerken canı armut istemiş. Bir iki tane armut almış ve yemiş.",
    "Yani hırsızlık yapmış.",
    "Bunu gören pazar halkı onu yakalamış, saraya çıkarmışlar. “Hırsızı yakaladık, size getirdik padişahım” demişler.",
    "Padişah da adama sormuş: “Niye yaptın oğlum? Hırsızlığın kötü olduğunu bildiğin hâlde nasıl böyle bir şey yaparsın?”",
    "“Padişahım, vallahi açtım, çok canım çekti, yedim. Ama devletimizin ekonomisini düze çıkaracak bir bilgiye sahibim” demiş.",
    "“Hadi git!” demiş padişah. “Sen aç geziyorsun, bir de bütün ülkenin ekonomisini düzeltecek bilgim var diyorsun.”",
    "“Padişahım, gerçekten çok değerli bir bilgi” demiş. Padişah merak etmiş: “Söyle bakalım, elindeki bilgi ne?”",
    "Yediği armutların çekirdeklerini cebinden çıkarıp avucunda padişaha sunmuş.",
    "“Bu tohumları ekersen üç gün içinde olgunlaşacak, meyvesi altın olarak sana dönecek” demiş.",
    "“Öyle bir şey varsa oğlum, git hemen bahçelerimizden birine ek. Üç gün içinde kanıtlanırsa sana hem hediyeler veririm hem de seni serbest bırakırım.”",
    "“Ama padişahım, bunun bir sihri var.” “Sihri ne ki oğlum?”",
    "“Hırsızlık yapmamış, yalan söylememiş, halkına ihanet etmemiş birinin ekmesi lazım.”",
    "“Bu özellikler bende olmadığı için ben ekersem, bu ağaç bana zehir olarak dönecek ve beni öldürecek.”",
    "“Bunu ekebilecek tek insan olarak sizi görüyorum padişahım.”",
    "“Çünkü sen hırsızlık yapmış olamazsın, yalan söylemiş olamazsın, halkına ihanet etmiş olamazsın. Ekerse ekerse sen ekersin.”",
    "Padişah duraksamış, onu bir ter basmış. “Oğlum, ben bahçıvan mıyım? Ben eker miyim böyle bir şey?”",
    "“Hele ver bizim baş vezire, o eksin” demiş.",
    "Vezir bunu duyunca eli ayağı titremiş, padişaha dönmüş:",
    "“Padişahım, ben hayatımda ağaç nasıl ekilir, nasıl sulanır bilmem.”",
    "“En iyisi baş veznedarımıza verelim, o eksin” demiş.",
    "Veznedara gitmişler. Aynı korkuyu yaşayan veznedar da aynı tepkiyi vermiş.",
    "Uzun bir sessizlikten sonra padişah “Hadi çocuklar” demiş.",
    "“Bu adamın meyvesinin altına dönüştüğünü kanıtlayalım.”",
    "Cebinden bir altın çıkarıp adamın kucağına atmış. “Siz de verin” demiş.",
    "Herkes elinden geldiğince ceplerinden altın çıkarıp adama vermiş.",
    "Ve adama “Sen bize çok iyi bir ders verdin” demiş.",
    "Şuna gelmek istiyorum: Türkiye'de ne zaman bu tohumu ekebilecek yöneticilerimiz olursa, ekonomimiz düzlüğe çıkacak.",
    "Eğer bu tohumu ekebilecek yöneticilere sahip olamazsak, böyle batıp gideceğiz.",
    "Ekonominin bu durumda olması üretememe sorunudur.",
    "Eğer üretebilseydik zaten bu durumda olmazdık.",
    "Biz ithalata öncelik verdik, üretimi bitirdik.",
    "Yöneticilerimiz o tohumu ekebilecek duruma, yani dürüstlüğe ve hırsızlık yapamayacak duruma gelirse,",
    "ekonomimiz düzlüğe çıkmış olacak inşallah.",
    "Ben söyledim, anlayan anlasın.",
]
_tr = json.load(open(os.path.join(HERE, 'transcript.json')))
assert len(_tr) == len(TEXTS), (len(_tr), len(TEXTS))

def build_cues():
    cues = []
    for segm, text in zip(_tr, TEXTS):
        words = text.split(); chunks = []; cur = []
        for wd in words:
            cand = ' '.join(cur + [wd])
            if cur and len(cand) > 46:
                chunks.append(' '.join(cur)); cur = [wd]
            else:
                cur.append(wd)
                if len(cand) >= 22 and wd[-1] in '.,?!:”' and len(cand) > 28:
                    chunks.append(' '.join(cur)); cur = []
        if cur: chunks.append(' '.join(cur))
        tot = sum(len(c) for c in chunks); t0 = segm['start']; dur = segm['end'] - segm['start']
        for c in chunks:
            d = dur * len(c) / tot
            cues.append((t0, t0 + d, c)); t0 += d
    return cues
CUES = build_cues()

def wrap(ctx, text, maxw):
    lines = []; cur = ''
    for wd in text.split():
        cand = (cur + ' ' + wd).strip()
        if ctx.text_extents(cand)[4] > maxw and cur:
            lines.append(cur); cur = wd
        else: cur = cand
    if cur: lines.append(cur)
    return lines

def draw_subs(ctx, t):
    if t >= 161.6: return
    txt = None
    for a, b, c in CUES:
        if a <= t < b + 0.15: txt = c
    if not txt: return
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(60)
    lines = wrap(ctx, txt, 930)
    lh = 76; y0 = 1440 - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        e = ctx.text_extents(ln)
        ctx.move_to(540 - e[4] / 2, y0 + i * lh + 20); ctx.text_path(ln)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    setc(ctx, '#111111'); ctx.set_line_width(13); ctx.stroke_preserve()
    setc(ctx, '#ffffff'); ctx.fill()

def draw_title(ctx, t):
    a = seg(t, 0.2, 0.7) * (1 - seg(t, 3.2, 3.8))
    if a <= 0: return
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(120)
    txt = 'ALTIN TOHUM'; e = ctx.text_extents(txt)
    sc = 0.9 + 0.1 * seg(t, 0.2, 0.9)
    ctx.save(); ctx.translate(540, 330); ctx.scale(sc, sc)
    ctx.move_to(-e[4] / 2, 40); ctx.text_path(txt)
    setc(ctx, '#3a1f0e', a); ctx.set_line_width(18); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    setc(ctx, '#f5c542', a); ctx.fill(); ctx.restore()

def black_alpha(t):
    a = 0
    for T in (12.0, 132.3, 144.5, 161.7):
        a = max(a, 1 - abs(t - T) / 0.3)
    a = max(a, 1 - t / 0.4, (t - (DUR - 0.8)) / 0.8)
    return clamp(a)

def render(ctx, t):
    ctx.save()
    setc(ctx, '#000'); ctx.paint()
    if t < 12.0: scene_market(ctx, t)
    elif t < 132.3: scene_palace(ctx, t)
    elif t < 144.5: scene_field(ctx, t)
    elif t < 161.7: scene_factory(ctx, t)
    else: scene_end(ctx, t)
    ctx.restore()
    a = black_alpha(t)
    if a > 0: setc(ctx, '#000', a); ctx.paint()
    draw_title(ctx, t)
    draw_subs(ctx, t)

if __name__ == '__main__':
    import subprocess
    mode = sys.argv[1]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if mode == 'png':
        for ts in sys.argv[3:]:
            t = float(ts); ctx = cairo.Context(surf); render(ctx, t)
            surf.write_to_png(os.path.join(sys.argv[2], f'f_{t:07.2f}.png'))
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                               '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                               '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fr in range(f0, f1):
            ctx = cairo.Context(surf); render(ctx, fr / FPS); surf.flush()
            ff.stdin.write(bytes(surf.get_data()))
        ff.stdin.close(); ff.wait()
