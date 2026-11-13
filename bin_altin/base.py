import cairo, math, json, sys, os, random
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
FPS = 24
DUR = 104.15
FY = 1330          # floor line (interior)
PI = math.pi

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sm(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def seg(t, t0, t1): return sm((t - t0) / (t1 - t0))
def win(t, t0, t1, f=0.3): return seg(t, t0, t0 + f) * (1 - seg(t, t1 - f, t1))
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
def dark(c, k=0.75): return tuple(x * k for x in hexc(c))
def setc(ctx, c, a=1.0):
    c = hexc(c); ctx.set_source_rgba(c[0], c[1], c[2], a)
INK = hexc('#1a1020')
def fs(ctx, c, lw=5, a=1.0):
    setc(ctx, c, a); ctx.fill_preserve(); setc(ctx, INK, a); ctx.set_line_width(lw); ctx.stroke()
def ell(ctx, x, y, rx, ry):
    ctx.save(); ctx.translate(x, y); ctx.scale(max(rx, .01), max(ry, .01)); ctx.new_sub_path(); ctx.arc(0, 0, 1, 0, 2 * PI); ctx.restore()
def circ(ctx, x, y, r): ctx.new_sub_path(); ctx.arc(x, y, max(r, .01), 0, 2 * PI)
def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -PI / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, PI / 2)
    ctx.arc(x + r, y + h - r, r, PI / 2, PI); ctx.arc(x + r, y + r, r, PI, 1.5 * PI); ctx.close_path()
def lgrad(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c, *a in stops:
        c = hexc(c); g.add_color_stop_rgba(o, c[0], c[1], c[2], a[0] if a else 1)
    return g
def glow(ctx, x, y, r, c, a=0.6):
    c = hexc(c); g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], a); g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g); circ(ctx, x, y, r); ctx.fill()
def sparkle(ctx, x, y, r, a=1.0, c='#fff6c8'):
    ctx.move_to(x, y - r); ctx.line_to(x + r * .22, y - r * .22); ctx.line_to(x + r, y); ctx.line_to(x + r * .22, y + r * .22)
    ctx.line_to(x, y + r); ctx.line_to(x - r * .22, y + r * .22); ctx.line_to(x - r, y); ctx.line_to(x - r * .22, y - r * .22)
    ctx.close_path(); setc(ctx, c, a); ctx.fill()
def font(ctx, size, italic=False, black=False):
    ctx.select_font_face('Inter Black' if black else 'Inter', cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)

# ---------------------------------------------------------------- audio / speakers
_a = np.fromfile(os.path.join(HERE, 'audio16k.raw'), np.float32)
_hop = 16000 / FPS
ENV = np.array([np.sqrt(np.mean(_a[int(i * _hop):int((i + 1) * _hop)] ** 2) + 1e-12) for i in range(int(len(_a) / _hop))])
ENV = np.clip((ENV / np.percentile(ENV[ENV > 0.005], 85) - 0.18) * 1.35, 0, 1)
def env(t):
    i = int(t * FPS); return float(ENV[i]) if 0 <= i < len(ENV) else 0.0
SPEAK = [(21.26, 24.38, 'imam'), (28.02, 36.8, 'mec'), (38.06, 40.24, 'imam'), (41.92, 50.72, 'mec'), (58.28, 63.8, 'mec')]
def speaker(t):
    for a, b, n in SPEAK:
        if a <= t < b: return n
    return 'nar'
def mouth_of(n, t):
    return env(t) * (0.5 + 0.5 * abs(math.sin(t * 16))) if speaker(t) == n else 0.0

# ---------------------------------------------------------------- characters
STY = {
    'mec':  dict(skin='#e8b48a', robe='#a0522d', robe2='#7a3b1e', inner='#d9b98a', hair='mess', hairc='#2a1a12',
                 beard='stubble', beardc='#3a2418', iris='#3a2a1a', w=1.0, patches=True),
    'imam': dict(skin='#f0c8a0', robe='#2b2f4a', robe2='#1d2035', inner='#f4f1e8', hair='sarik', hairc='#fbfaf4',
                 beard='long', beardc='#cfcfd6', iris='#2a2a3a', w=1.1),
    'A':    dict(skin='#e6b089', robe='#3d6e8f', robe2='#2a5070', inner='#e9e4d8', hair='takke', hairc='#ffffff',
                 beard='short', beardc='#4a2e1c', iris='#3a2a1a', w=1.0),
    'B':    dict(skin='#d99a6c', robe='#5f7f35', robe2='#465f25', inner='#efe8d6', hair='takke', hairc='#f3ead2',
                 beard='full', beardc='#1e1410', iris='#2a1a10', w=1.2),
    'C':    dict(skin='#f1c6a0', robe='#8f3d5b', robe2='#6d2b44', inner='#f2ecdf', hair='takke', hairc='#ffffff',
                 beard='none', beardc='#3a2418', iris='#4a3020', w=0.95),
    'G':    dict(skin='#f1c6a0', robe='#3f5a8f', robe2='#2c4170', inner='#f2ecdf', hair='short', hairc='#2a1a12',
                 beard='none', beardc='#3a2418', iris='#4a3020', w=0.98),
}
STY.update({
    'genc': dict(skin='#e2ad84', robe='#efe6d2', robe2='#cfc3a8', inner='#ffffff', hair='kufiye', hairc='#f7f4ec',
                 beard='short', beardc='#2a1a12', iris='#3a2a1a', w=1.0),
    'genc2': dict(skin='#e2ad84', robe='#d9cdb0', robe2='#b8aa8a', inner='#f4efe2', hair='kufiye', hairc='#f2ede0',
                  beard='stubble', beardc='#2a1a12', iris='#3a2a1a', w=0.97),
    'sahip': dict(skin='#e8b48e', robe='#2e7d4f', robe2='#1f5c39', inner='#f2c14e', hair='sarik', hairc='#f2c14e',
                  beard='long', beardc='#bdbdbd', iris='#2a2a3a', w=1.15),
    'gelin': dict(skin='#f1c6a0', robe='#b3263e', robe2='#8a1a2e', inner='#f2c14e', hair='hijab', hairc='#7a1a3a',
                  beard='none', beardc='#3a2418', iris='#5a3a20', w=0.95),
})
SEEDN = {k: i * 1.7 for i, k in enumerate(STY)}

def pose():
    return dict(face=1, bend=0.0, mouth=0.0, eyes='normal', brow=0.0, look=1.0, blush=0, sweat=0, vein=0, gloom=0,
                tremble=0, arms='down', walk=None, wood=False, smile=0.2, tilt=0.0, fa=None, ba=None)

ARMS = {  # (back a1,a2), (front a1,a2) angles from straight down, + = forward
    'down': ((-0.08, 0.1), (0.1, 0.12)),
    'fold': ((0.35, 1.9), (0.45, 1.75)),
    'tekbir': ((0.15, 2.9), (0.25, 2.85)),
    'point': ((-0.2, 0.3), (1.55, 0.0)),
    'pointup': ((-0.2, 0.3), (2.1, 0.1)),
    'explain': ((0.3, 1.2), (0.9, 0.9)),
    'hips': ((-0.6, 2.2), (0.6, -2.2)),
    'shrug': ((-1.0, 1.6), (1.0, -1.0)),
    'dua': ((0.55, 2.35), (0.7, 2.25)),
    'give': ((-0.1, 0.2), (1.35, -0.05)),
    'chest': ((0.4, 2.1), (0.5, 2.2)),
}

def arm(ctx, sx, sy, a1, a2, col, skin, lw=30):
    L1, L2 = 88, 82
    ex, ey = sx + L1 * math.sin(a1), sy + L1 * math.cos(a1)
    hx, hy = ex + L2 * math.sin(a1 + a2), ey + L2 * math.cos(a1 + a2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(sx, sy); ctx.line_to(ex, ey); ctx.line_to(hx, hy)
    setc(ctx, INK); ctx.set_line_width(lw + 10); ctx.stroke_preserve(); setc(ctx, col); ctx.set_line_width(lw); ctx.stroke()
    circ(ctx, hx, hy, 15); fs(ctx, skin, 4)
    return hx, hy

def logs_bundle(ctx, x, y, s=1.0):
    for i in range(5):
        lx = x + (i - 2) * 17 * s
        rrect(ctx, lx - 10 * s, y - 95 * s + (i % 2) * 10 * s, 20 * s, 190 * s, 9 * s); fs(ctx, '#8b5a2b', 3.5)
        ell(ctx, lx, y - 92 * s + (i % 2) * 10 * s, 8 * s, 5 * s); fs(ctx, '#d9a066', 2.5)
    for ry in (-50, 45):
        ctx.move_to(x - 48 * s, y + ry * s); ctx.line_to(x + 48 * s, y + ry * s + 6 * s)
        setc(ctx, '#e8d9a8'); ctx.set_line_width(6 * s); ctx.stroke()

def head(ctx, st, p, t, name):
    skin = st['skin']
    # back hair / sarik base
    if st['hair'] == 'mess':
        ctx.new_path(); ctx.move_to(-70, 5)
        pts = [(-82, -30), (-60, -45), (-78, -70), (-40, -70), (-45, -100), (-5, -78), (10, -108), (30, -75), (60, -92), (55, -55), (72, -40)]
        for px, py in pts: ctx.line_to(px, py)
        ctx.line_to(40, -30); ctx.close_path(); fs(ctx, st['hairc'], 5)
    if st['hair'] == 'hijab':
        ell(ctx, -8, 14, 82, 96); fs(ctx, st['hairc'], 5)
    if st['hair'] == 'kufiye':
        ctx.new_path(); ctx.move_to(-40, -60); ctx.curve_to(-100, -20, -110, 80, -90, 140); ctx.line_to(-10, 120)
        ctx.curve_to(-30, 60, -20, 0, -10, -40); ctx.close_path(); fs(ctx, st['hairc'], 5)
        ctx.move_to(-80, 20); ctx.line_to(-60, 120); setc(ctx, '#d8d0bc'); ctx.set_line_width(3); ctx.stroke()
    # face shape
    def face_path():
        ctx.new_path(); ctx.move_to(-58, 0); ctx.curve_to(-62, -72, 60, -82, 60, -8)
        ctx.curve_to(62, 25, 48, 52, 26, 64); ctx.curve_to(0, 72, -36, 52, -58, 0); ctx.close_path()
    face_path(); setc(ctx, skin); ctx.fill()
    ctx.save(); face_path(); ctx.clip()
    ell(ctx, -62, 14, 46, 70); setc(ctx, dark(skin, 0.86)); ctx.fill()        # cel shadow
    if st['beard'] == 'stubble':
        ell(ctx, 18, 46, 58, 30); setc(ctx, st['beardc'], 0.28); ctx.fill()
    ctx.restore()
    face_path(); setc(ctx, INK); ctx.set_line_width(5); ctx.stroke()
    ell(ctx, -16, 8, 11, 16); fs(ctx, skin, 4)                                 # ear
    bc = st['beardc']
    if st['beard'] in ('long', 'full', 'short'):
        tip = {'long': (22, 150), 'full': (24, 105), 'short': (26, 82)}[st['beard']]
        ctx.new_path(); ctx.move_to(-30, 18)
        ctx.curve_to(-32, 70, tip[0] - 40, tip[1] - 12, tip[0], tip[1])
        ctx.curve_to(tip[0] + 36, tip[1] - 14, 62, 50, 58, 14)
        ctx.curve_to(44, 34, 10, 40, -30, 18); ctx.close_path(); fs(ctx, bc, 4)
        for k in range(3):
            ctx.move_to(5 + k * 14, 50 + k * 4); ctx.line_to(10 + k * 12, tip[1] - 30); setc(ctx, dark(bc, 0.8)); ctx.set_line_width(2.5); ctx.stroke()
    # mouth
    mx, my = 36, 40
    m = p['mouth']
    if p['eyes'] == 'angry' and m > 0.05:
        ctx.new_path(); ctx.move_to(mx - 18, my - 4); ctx.line_to(mx + 16, my - 6); ctx.line_to(mx + 10, my + 8 + 14 * m)
        ctx.line_to(mx - 12, my + 6 + 12 * m); ctx.close_path(); fs(ctx, '#5a1020', 3)
        ctx.rectangle(mx - 14, my - 4, 26, 6); setc(ctx, '#fff'); ctx.fill()
    elif m > 0.07:
        ell(ctx, mx, my + 2, 10 + 3 * m, 3 + 13 * m); fs(ctx, '#5a1020', 3)
        ell(ctx, mx, my + 6 + 7 * m, 6, 2 + 4 * m); setc(ctx, '#e0606a'); ctx.fill()
    elif p['eyes'] == 'shock':
        ell(ctx, mx, my + 4, 7, 10); fs(ctx, '#5a1020', 3)
    else:
        s_ = p['smile']
        ctx.move_to(mx - 12, my); ctx.curve_to(mx - 4, my + 12 * s_, mx + 4, my + 12 * s_, mx + 12, my - 2 * s_)
        setc(ctx, INK); ctx.set_line_width(4); ctx.stroke()
    if st['beard'] in ('long', 'full', 'short'):
        for sg in (-1, 1):
            ctx.move_to(mx, my - 10); ctx.curve_to(mx + sg * 14, my - 18, mx + sg * 22, my - 10, mx + sg * 26, my + 2)
            ctx.curve_to(mx + sg * 16, my - 4, mx + sg * 8, my - 4, mx, my - 6); ctx.close_path(); fs(ctx, bc, 3)
    # nose
    ctx.move_to(54, 2); ctx.line_to(60, 18); ctx.line_to(52, 20); setc(ctx, INK); ctx.set_line_width(3.5); ctx.stroke()
    # blush (anime hatch)
    if p['blush'] > 0.01:
        ell(ctx, 18, 24, 22, 10); setc(ctx, '#ff6b8a', 0.45 * p['blush']); ctx.fill()
        for k in range(3):
            ctx.move_to(8 + k * 9, 30); ctx.line_to(14 + k * 9, 18); setc(ctx, '#d6336c', p['blush']); ctx.set_line_width(2.5); ctx.stroke()
    # eyes
    blink = ((t + SEEDN[name]) % 3.9) < 0.12
    e = p['eyes']
    for ex, rx, fr in ((2, 9, 0), (34, 12, 1)):
        ey = -8
        if e == 'happy' or (blink and e in ('normal', 'wide')):
            ctx.new_path(); ctx.arc(ex, ey + 6, rx, PI * 1.1, PI * 1.9) if e == 'happy' else (ctx.move_to(ex - rx, ey), ctx.line_to(ex + rx, ey))
            setc(ctx, INK); ctx.set_line_width(5); ctx.stroke(); continue
        if e == 'closed':
            ctx.new_path(); ctx.arc(ex, ey - 4, rx, PI * 0.15, PI * 0.85); setc(ctx, INK); ctx.set_line_width(5); ctx.stroke(); continue
        ry = 17 + (5 if e in ('wide', 'shock') else 0) - (5 if e == 'angry' else 0)
        ell(ctx, ex, ey, rx + (2 if e == 'wide' else 0), ry); setc(ctx, '#fff'); ctx.fill()
        if e == 'shock':
            circ(ctx, ex + 2, ey, 3); setc(ctx, INK); ctx.fill()
        else:
            ix = ex + 3 * p['look']
            ell(ctx, ix, ey + 2, rx * 0.72, ry * 0.75); setc(ctx, st['iris']); ctx.fill()
            ell(ctx, ix, ey + 4, rx * 0.4, ry * 0.42); setc(ctx, INK); ctx.fill()
            circ(ctx, ix - 3, ey - 5, 4); setc(ctx, '#fff'); ctx.fill()
            circ(ctx, ix + 3, ey + 7, 2); setc(ctx, '#fff', 0.8); ctx.fill()
        ell(ctx, ex, ey, rx + (2 if e == 'wide' else 0), ry); setc(ctx, INK); ctx.set_line_width(2.5); ctx.stroke()
        # lash
        ctx.new_path(); ctx.arc(ex, ey + 2, rx + 2, PI * 1.08, PI * 1.92)
        setc(ctx, INK); ctx.set_line_width(6); ctx.stroke()
        if e == 'angry':
            ctx.move_to(ex - rx - 2, ey - 16 + (6 if fr else -6)); ctx.line_to(ex + rx + 2, ey - 16 + (-6 if fr else 6))
            ctx.set_line_width(7); ctx.stroke()
    # brows
    b = p['brow']
    if e != 'angry':
        for ex, inner in ((2, 1), (34, -1)):
            ctx.move_to(ex - inner * 12, -34 + b * 3); ctx.line_to(ex + inner * 10, -36 - b * 8)
            setc(ctx, st['hairc'] if st['hair'] in ('mess', 'short') else bc); ctx.set_line_width(6)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    # gloom lines
    if p['gloom'] > 0.01:
        ctx.save(); face_path(); ctx.clip()
        for k in range(9):
            ctx.move_to(-40 + k * 12, -70); ctx.line_to(-40 + k * 12, -20 + (k % 3) * 8)
            setc(ctx, '#3b4cc0', 0.7 * p['gloom']); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
    # hair / hats
    hc = st['hairc']
    if st['hair'] == 'mess':
        ctx.new_path(); ctx.move_to(-58, -10)
        for px, py in [(-50, -60), (-30, -40), (-20, -78), (0, -48), (18, -80), (30, -45), (52, -66), (50, -30), (62, -22)]:
            ctx.line_to(px, py)
        ctx.curve_to(40, -70, -30, -80, -58, -10); ctx.close_path(); fs(ctx, hc, 4.5)
        ctx.move_to(-10, -60); ctx.line_to(10, -50); setc(ctx, '#6a4a3a'); ctx.set_line_width(4); ctx.stroke()
    elif st['hair'] == 'short':
        ctx.new_path(); ctx.move_to(-60, 0); ctx.curve_to(-70, -80, 50, -95, 64, -20)
        ctx.line_to(46, -30); ctx.line_to(40, -14); ctx.line_to(26, -36); ctx.line_to(10, -20); ctx.line_to(-6, -40)
        ctx.line_to(-30, -20); ctx.line_to(-38, 4); ctx.close_path(); fs(ctx, hc, 4.5)
    elif st['hair'] == 'takke':
        ctx.new_path(); ctx.arc(0, -36, 58, PI * 1.02, PI * 1.98); ctx.close_path(); fs(ctx, hc, 4.5)
        for k in range(4):
            ctx.new_path(); ctx.arc(0, -36, 58 - k * 12, PI * 1.1, PI * 1.9); setc(ctx, '#d8d0bc'); ctx.set_line_width(2); ctx.stroke()
    elif st['hair'] == 'hijab':
        ctx.new_path(); ctx.move_to(-66, 70); ctx.curve_to(-80, -20, -60, -80, 0, -86); ctx.curve_to(50, -86, 72, -50, 66, -18)
        ctx.curve_to(56, -40, 40, -52, 20, -54); ctx.curve_to(-20, -56, -40, -40, -44, -10); ctx.curve_to(-48, 30, -40, 60, -30, 72)
        ctx.close_path(); fs(ctx, hc, 5)
        ctx.new_path(); ctx.move_to(66, -18); ctx.curve_to(56, -40, 40, -52, 20, -54); ctx.curve_to(-20, -56, -40, -40, -44, -10)
        setc(ctx, '#f2c14e'); ctx.set_line_width(5); ctx.stroke()
    elif st['hair'] == 'kufiye':
        ctx.new_path(); ctx.arc(-4, -30, 66, PI * 0.98, PI * 2.0); ctx.line_to(62, -22); ctx.curve_to(30, -40, -30, -40, -70, -10)
        ctx.close_path(); fs(ctx, hc, 5)
        ell(ctx, -4, -52, 62, 13); setc(ctx, INK); ctx.set_line_width(7); ctx.stroke()
    elif st['hair'] == 'sarik':
        circ(ctx, 0, -78, 34); fs(ctx, '#8b1e2e', 4.5)
        ell(ctx, 0, -50, 82, 46); fs(ctx, hc, 5)
        ctx.save(); ell(ctx, 0, -50, 82, 46); ctx.clip()
        ell(ctx, -60, -40, 50, 60); setc(ctx, '#d8d6e6'); ctx.fill()
        for k in range(4):
            ctx.move_to(-80, -70 + k * 18); ctx.curve_to(-20, -40 + k * 14, 30, -80 + k * 18, 90, -46 + k * 14)
            setc(ctx, '#c9c6d6'); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
    # vein
    if p['vein'] > 0.01:
        vx, vy = 72, -88; a = p['vein']; s2 = 1 + 0.15 * math.sin(t * 20)
        ctx.save(); ctx.translate(vx, vy); ctx.scale(s2, s2)
        for qx, qy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            cx_, cy_ = qx * 15, qy * 15; d0 = math.atan2(-qy, -qx)
            ctx.new_path(); ctx.arc(cx_, cy_, 11, d0 - 0.95, d0 + 0.95)
            setc(ctx, '#ffffff', a); ctx.set_line_width(11); ctx.stroke_preserve()
            setc(ctx, '#e8102e', a); ctx.set_line_width(5.5); ctx.stroke()
        ctx.restore()
    if p['sweat'] > 0.01:
        sx, sy = -48, -50 + 8 * math.sin(t * 6)
        ctx.new_path(); ctx.move_to(sx, sy - 28); ctx.curve_to(sx + 18, sy, sx + 16, sy + 16, sx, sy + 16)
        ctx.curve_to(sx - 16, sy + 16, sx - 18, sy, sx, sy - 28); ctx.close_path()
        setc(ctx, '#bfe8ff', p['sweat']); ctx.fill_preserve(); setc(ctx, '#3a7ab8', p['sweat']); ctx.set_line_width(3); ctx.stroke()
        circ(ctx, sx - 4, sy + 4, 4); setc(ctx, '#fff', p['sweat']); ctx.fill()

def draw_char(ctx, name, x, y, s, p, t):
    st = STY[name]; w = st['w']; f = p['face']
    tr = p['tremble']
    ox = x + tr * 6 * math.sin(t * 61) * s
    bob = -abs(math.sin(p['walk'])) * 12 if p['walk'] is not None else 0
    oy = y + bob * s
    ctx.save(); ctx.translate(ox, oy); ctx.scale(s * f, s)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    th = p['bend'] * PI / 2 * 0.92
    hip = (0, -235)
    d = (math.sin(th), -math.cos(th))
    S = (hip[0] + 165 * d[0], hip[1] + 165 * d[1])
    ba, fa = ARMS[p['arms']]
    if p['ba']: ba = p['ba']
    if p['fa']: fa = p['fa']
    if p['bend'] > 0.3:
        ba = (lerp(ba[0], -0.5, p['bend']), lerp(ba[1], -0.2, p['bend'])); fa = (lerp(fa[0], -0.4, p['bend']), lerp(fa[1], -0.2, p['bend']))
    # back arm
    arm(ctx, S[0] - 30 * d[1] * 0 - 25, S[1], ba[0], ba[1], st['robe2'], dark(st['skin'], 0.88))
    # feet
    for i, fx in enumerate((-14, 22)):
        off = lift = 0
        if p['walk'] is not None:
            ph = p['walk'] + i * PI; off = 22 * math.sin(ph); lift = max(0, math.cos(ph)) * 10
        ell(ctx, fx + off + 8, -10 - lift, 26, 12); fs(ctx, '#3a2a28', 4)
    # skirt
    ctx.new_path(); ctx.move_to(-52 * w, -245); ctx.line_to(52 * w, -245); ctx.line_to(68 * w, -22); ctx.curve_to(20, -14, -20, -14, -68 * w, -22)
    ctx.close_path(); setc(ctx, st['robe']); ctx.fill_preserve()
    ctx.save(); ctx.clip(); ctx.rectangle(-120, -260, 80, 260); setc(ctx, st['robe2']); ctx.fill()
    if name == 'imam':
        ctx.rectangle(6, -260, 26, 260); setc(ctx, st['inner']); ctx.fill()
    if st.get('patches'):
        ctx.rectangle(10, -120, 30, 28); setc(ctx, '#c68a4a'); ctx.fill()
    ctx.restore()
    ctx.new_path(); ctx.move_to(-52 * w, -245); ctx.line_to(52 * w, -245); ctx.line_to(68 * w, -22); ctx.curve_to(20, -14, -20, -14, -68 * w, -22)
    ctx.close_path(); setc(ctx, INK); ctx.set_line_width(5.5); ctx.stroke()
    # torso (rotated)
    ctx.save(); ctx.translate(*hip); ctx.rotate(th)
    if p['wood']:
        logs_bundle(ctx, -68 * w, -95, 1.0)
    def torso():
        ctx.new_path(); ctx.move_to(-50 * w, 10); ctx.line_to(50 * w, 10); ctx.curve_to(56 * w, -80, 52 * w, -150, 40, -190)
        ctx.curve_to(15, -200, -15, -200, -40, -190); ctx.curve_to(-52 * w, -150, -56 * w, -80, -50 * w, 10); ctx.close_path()
    torso(); setc(ctx, st['robe']); ctx.fill()
    ctx.save(); torso(); ctx.clip()
    ctx.rectangle(-120, -220, 82, 240); setc(ctx, st['robe2']); ctx.fill()
    ctx.move_to(-2, -200); ctx.line_to(28, -200); ctx.line_to(18, -120); ctx.close_path(); setc(ctx, st['inner']); ctx.fill()
    if name == 'imam': ctx.rectangle(6, -200, 26, 230); setc(ctx, st['inner']); ctx.fill()
    if name == 'mec':
        ctx.move_to(-60, -30); ctx.line_to(60, -24); setc(ctx, '#d9c08a'); ctx.set_line_width(9); ctx.stroke()
        ctx.rectangle(-20, -150, 26, 24); setc(ctx, '#c68a4a'); ctx.fill()
    else:
        ctx.rectangle(-80, -40, 160, 18); setc(ctx, dark(st['robe'], 0.6)); ctx.fill()
    ctx.restore()
    torso(); setc(ctx, INK); ctx.set_line_width(5.5); ctx.stroke()
    ctx.rectangle(-16, -215, 32, 30); fs(ctx, st['skin'], 4)
    ctx.save(); ctx.translate(14, -262); ctx.rotate(p['tilt'] - th * 0.25)
    head(ctx, st, p, t, name)
    ctx.restore()
    ctx.restore()
    hand = arm(ctx, S[0] + 22, S[1], fa[0], fa[1], st['robe'], st['skin'])
    ctx.restore()
    hp = (hip[0] + 262 * d[0] + 14 * math.cos(th), hip[1] + 262 * d[1] + 14 * math.sin(th))
    return dict(head=(ox + f * s * hp[0], oy + s * hp[1]), hand=(ox + f * s * hand[0], oy + s * hand[1]),
                back=(ox - f * s * 75, oy - s * 330))

# ---------------------------------------------------------------- ghost images
def ghost(ctx, x, y, s, a, kind, t):
    if a <= 0.01: return
    y += 10 * math.sin(t * 2.2 + x * 0.01)
    glow(ctx, x, y, 170 * s, '#7fe7ff', 0.45 * a)
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.push_group()
    if kind == 'child':
        ctx.rectangle(-38, 40, 76, 80); fs(ctx, '#ffd36b', 4)
        circ(ctx, 0, 0, 58); fs(ctx, '#f6cfa8', 4)
        ctx.new_path(); ctx.arc(0, -8, 60, PI * 1.0, PI * 2.0); ctx.line_to(40, -18); ctx.line_to(20, -30); ctx.line_to(0, -14)
        ctx.line_to(-20, -32); ctx.line_to(-40, -16); ctx.close_path(); fs(ctx, '#e8b84a', 4)
        for ex in (-20, 20):
            ell(ctx, ex, 8, 13, 18); setc(ctx, '#fff'); ctx.fill()
            ell(ctx, ex, 11, 10, 14); setc(ctx, '#1e88ff'); ctx.fill()
            ell(ctx, ex, 13, 5, 7); setc(ctx, INK); ctx.fill()
            circ(ctx, ex - 4, 4, 4); setc(ctx, '#fff'); ctx.fill()
            ell(ctx, ex, 8, 13, 18); setc(ctx, INK); ctx.set_line_width(2.5); ctx.stroke()
        ctx.move_to(-8, 36); ctx.curve_to(-3, 44, 3, 44, 8, 36); setc(ctx, INK); ctx.set_line_width(3.5); ctx.stroke()
    elif kind == 'jar':
        ctx.new_path(); ctx.move_to(-40, -60); ctx.curve_to(-110, -20, -100, 90, -40, 110); ctx.line_to(40, 110)
        ctx.curve_to(100, 90, 110, -20, 40, -60); ctx.close_path(); fs(ctx, '#b5651d', 5)
        ctx.rectangle(-45, -78, 90, 22); fs(ctx, '#8b4513', 4)
        for k in range(9):
            r = random.Random(k); cx_, cy_ = r.uniform(-40, 40), -82 - r.uniform(0, 40) + abs(r.uniform(-40, 40)) * 0.3
            ell(ctx, cx_, cy_, 16, 9); fs(ctx, '#ffd23f', 2.5)
        for k in range(3): sparkle(ctx, -50 + k * 50, -130 + 15 * math.sin(t * 4 + k), 14)
    elif kind == 'house':
        ctx.rectangle(-70, -20, 140, 110); fs(ctx, '#f4e1c1', 5)
        ctx.move_to(-95, -15); ctx.line_to(0, -100); ctx.line_to(95, -15); ctx.close_path(); fs(ctx, '#d1495b', 5)
        ctx.rectangle(-20, 30, 40, 60); fs(ctx, '#8b5a2b', 4); ctx.rectangle(30, 5, 28, 28); fs(ctx, '#9be7ff', 4)
    elif kind == 'cow':
        ell(ctx, 0, 0, 150, 85); fs(ctx, '#fbfbfb', 6)
        ctx.save(); ell(ctx, 0, 0, 150, 85); ctx.clip()
        for cx_, cy_, r in ((-60, -30, 40), (40, 20, 34), (90, -40, 26)):
            ell(ctx, cx_, cy_, r * 1.2, r); setc(ctx, '#222'); ctx.fill()
        ctx.restore()
        for lx in (-100, -50, 50, 100):
            rrect(ctx, lx - 14, 50, 28, 80, 10); fs(ctx, '#fbfbfb', 5); ctx.rectangle(lx - 14, 115, 28, 15); setc(ctx, '#333'); ctx.fill()
        ell(ctx, 40, 75, 30, 18); fs(ctx, '#ffb3c6', 4)
        ctx.save(); ctx.translate(165, -50)
        for sg in (-1, 1):
            ctx.move_to(sg * 30, -40); ctx.curve_to(sg * 50, -70, sg * 70, -60, sg * 70, -80); setc(ctx, '#e8d8b0'); ctx.set_line_width(12); ctx.stroke()
        ell(ctx, 0, 0, 60, 66); fs(ctx, '#fbfbfb', 5)
        ell(ctx, 0, 40, 46, 30); fs(ctx, '#ffb3c6', 4)
        for nx in (-14, 14): ell(ctx, nx, 42, 6, 9); setc(ctx, '#7a3b4a'); ctx.fill()
        for ex in (-22, 22):
            ell(ctx, ex, -12, 10, 13); setc(ctx, '#fff'); ctx.fill(); ell(ctx, ex, -9, 6, 8); setc(ctx, INK); ctx.fill()
            circ(ctx, ex - 2, -13, 2.5); setc(ctx, '#fff'); ctx.fill()
        ctx.restore()
        ctx.move_to(-150, -10); ctx.curve_to(-190, 10, -180, 60, -200, 80); setc(ctx, INK); ctx.set_line_width(6); ctx.stroke()
    elif kind == 'coins':
        for k in range(5):
            ell(ctx, 0, 60 - k * 22, 60, 20); fs(ctx, '#ffd23f', 4)
        font(ctx, 46, black=True); ctx.move_to(-14, -38); setc(ctx, '#b8860b'); ctx.show_text('₺')
    elif kind == 'case':
        rrect(ctx, -90, -50, 180, 120, 14); fs(ctx, '#7a4a2a', 5)
        rrect(ctx, -30, -75, 60, 30, 8); setc(ctx, INK); ctx.set_line_width(6); ctx.stroke()
        ctx.rectangle(-90, -5, 180, 12); setc(ctx, '#5a3018'); ctx.fill()
    elif kind == 'phone':
        rrect(ctx, -50, -90, 100, 180, 16); fs(ctx, '#2a2a3a', 5)
        rrect(ctx, -40, -75, 80, 145, 6); setc(ctx, '#7fd3ff'); ctx.fill()
        for k in range(3):
            rrect(ctx, -32, -60 + k * 40, 64, 28, 6); setc(ctx, '#ffffff', 0.9); ctx.fill()
        circ(ctx, 45, -85, 22); fs(ctx, '#ff3b5c', 4)
        font(ctx, 26, black=True); ctx.move_to(38, -76); setc(ctx, '#fff'); ctx.show_text('9')
    elif kind == 'people':
        for k, (px, col) in enumerate(((-55, '#e07a5f'), (0, '#3d85c6'), (55, '#81b29a'))):
            circ(ctx, px, -20 - (k == 1) * 20, 30); fs(ctx, '#f1c6a0', 4)
            ctx.new_path(); ctx.arc(px, 60 - (k == 1) * 20, 45, PI, 2 * PI); ctx.close_path(); fs(ctx, col, 4)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(0.78 * a)
    ctx.restore()

def globe(ctx, x, y, s, t, mood=0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    for sg in (-1, 1):
        tap = (math.sin(t * 9) * 8 if sg == 1 else 0)
        ctx.move_to(sg * 30, 80); ctx.line_to(sg * 38, 140); setc(ctx, INK); ctx.set_line_width(9); ctx.stroke()
        ell(ctx, sg * 46, 142 - max(0, tap), 18, 9); fs(ctx, '#ff6b6b', 3)
        ctx.move_to(sg * 85, 0); ctx.line_to(sg * 120, 40 + sg * 10 * math.sin(t * 3)); ctx.stroke()
        circ(ctx, sg * 122, 42 + sg * 10 * math.sin(t * 3), 12); fs(ctx, '#fff', 3)
    circ(ctx, 0, 0, 92); fs(ctx, '#3fa7f5', 6)
    ctx.save(); circ(ctx, 0, 0, 90); ctx.clip()
    for cx_, cy_, rx, ry in ((-40, -40, 40, 26), (30, -20, 30, 44), (-20, 50, 46, 22), (60, 50, 20, 16)):
        ell(ctx, cx_, cy_, rx, ry); setc(ctx, '#5cc46a'); ctx.fill()
    ell(ctx, -50, 10, 60, 90); setc(ctx, '#000', 0.12); ctx.fill()
    ctx.restore()
    for ex in (-26, 26):
        if mood == 1:
            ctx.new_path(); ctx.move_to(ex - 14, -8); ctx.line_to(ex + 14, -8); setc(ctx, INK); ctx.set_line_width(6); ctx.stroke()
        else:
            ell(ctx, ex, -10, 13, 17); setc(ctx, '#fff'); ctx.fill(); ell(ctx, ex + 2, -6, 8, 11); setc(ctx, INK); ctx.fill()
            circ(ctx, ex - 1, -11, 3.5); setc(ctx, '#fff'); ctx.fill()
    ctx.move_to(-16, 30); ctx.curve_to(-6, 26, 6, 26, 16, 30); setc(ctx, INK); ctx.set_line_width(5); ctx.stroke()
    ctx.restore()

# ---------------------------------------------------------------- backgrounds
def retro_sky(ctx, x0, x1, y0, y1, hy):
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.set_source(lgrad(0, y0, 0, hy, [(0, '#1d1240'), (0.45, '#5a2a7a'), (0.75, '#e8507a'), (1, '#ffb347')])); ctx.fill()

def retro_sun(ctx, x, y, r):
    glow(ctx, x, y, r * 1.8, '#ff7eb3', 0.45)
    circ(ctx, x, y, r); ctx.set_source(lgrad(0, y - r, 0, y + r, [(0, '#fff27a'), (0.55, '#ff9a4d'), (1, '#ff3d7f')])); ctx.fill()
    for k in range(7):
        yy = y + r * 0.1 + k * r * 0.13; hh = 3 + k * 2.6
        ctx.rectangle(x - r - 2, yy, 2 * r + 4, hh)
        ctx.set_source(lgrad(0, y - r, 0, y + r, [(0, '#5a2a7a'), (0.6, '#e8507a'), (1, '#ffa24a')])); ctx.fill()

def stars(ctx, t, y1=900, n=60):
    rnd = random.Random(2)
    for _ in range(n):
        x, y, ph = rnd.uniform(0, W), rnd.uniform(0, y1), rnd.uniform(0, 6)
        sparkle(ctx, x, y, 3 + 3 * abs(math.sin(t * 2 + ph)), 0.8)

def mosque_sil(ctx, cx, base, col='#2a1640', door=1.0):
    setc(ctx, col)
    ctx.new_path(); ctx.arc(cx, base - 330, 230, PI, 2 * PI); ctx.fill()
    ctx.rectangle(cx - 240, base - 340, 480, 340); ctx.fill()
    ctx.rectangle(cx - 6, base - 650, 12, 100); ctx.fill()
    circ(ctx, cx, base - 560, 14); ctx.fill()
    for sx in (cx - 330, cx + 330):
        ctx.new_path(); ctx.arc(sx, base - 200, 110, PI, 2 * PI); ctx.fill(); ctx.rectangle(sx - 110, base - 200, 220, 200); ctx.fill()
    for mx in (cx - 470, cx + 470):
        ctx.rectangle(mx - 22, base - 860, 44, 860); ctx.fill()
        ctx.move_to(mx - 30, base - 860); ctx.line_to(mx, base - 1010); ctx.line_to(mx + 30, base - 860); ctx.close_path(); ctx.fill()
        ctx.rectangle(mx - 40, base - 640, 80, 18); ctx.fill()
    glow(ctx, cx, base - 90, 220, '#ffcf6b', 0.55 * door)
    ctx.new_path(); ctx.move_to(cx - 60, base); ctx.line_to(cx - 60, base - 120); ctx.arc(cx, base - 120, 60, PI, 2 * PI); ctx.line_to(cx + 60, base)
    ctx.close_path(); setc(ctx, mix('#2a1640', '#ffd27a', door)); ctx.fill()
    for k in range(5):
        wx = cx - 200 + k * 100
        ctx.new_path(); ctx.move_to(wx - 16, base - 200); ctx.line_to(wx - 16, base - 250); ctx.arc(wx, base - 250, 16, PI, 2 * PI)
        ctx.line_to(wx + 16, base - 200); ctx.close_path(); setc(ctx, '#ffcf6b', 0.85); ctx.fill()

def bg_exterior(ctx, t):
    retro_sky(ctx, -600, 1700, -400, 1350, 1300)
    stars(ctx, t, 600, 40)
    retro_sun(ctx, 540, 1060, 330)
    mosque_sil(ctx, 540, 1330)
    ctx.rectangle(-600, 1330, 2300, 1000); ctx.set_source(lgrad(0, 1330, 0, 1920, [(0, '#3a1f4f'), (1, '#140a24')])); ctx.fill()
    for k in range(10):
        y = 1360 + k * k * 9
        ctx.move_to(-600, y); ctx.line_to(1700, y); setc(ctx, '#ff5ea8', 0.35); ctx.set_line_width(2); ctx.stroke()
    for k in range(-12, 13):
        ctx.move_to(540 + k * 40, 1330); ctx.line_to(540 + k * 260, 1920); setc(ctx, '#ff5ea8', 0.25); ctx.set_line_width(2); ctx.stroke()

def bg_interior(ctx, t, beams=1.0):
    ctx.rectangle(-700, -400, 2600, 1800); ctx.set_source(lgrad(0, -200, 0, 1330, [(0, '#e9c48e'), (1, '#f6dfb6')])); ctx.fill()
    # door (left)
    ctx.new_path(); ctx.move_to(-110, 1330); ctx.line_to(-110, 820); ctx.arc(10, 820, 120, PI, 2 * PI); ctx.line_to(130, 1330); ctx.close_path()
    ctx.set_source(lgrad(0, 700, 0, 1330, [(0, '#ff8a5c'), (1, '#ffd27a')])); ctx.fill_preserve()
    setc(ctx, '#7a3b1e'); ctx.set_line_width(22); ctx.stroke()
    # windows
    for wx in (330, 760):
        ctx.new_path(); ctx.move_to(wx - 95, 860); ctx.line_to(wx - 95, 470); ctx.arc(wx, 470, 95, PI, 2 * PI); ctx.line_to(wx + 95, 860); ctx.close_path()
        ctx.set_source(lgrad(0, 370, 0, 860, [(0, '#ff9ad5'), (0.5, '#ffb36b'), (1, '#ffe39a')])); ctx.fill_preserve()
        setc(ctx, '#2f8f8a'); ctx.set_line_width(14); ctx.stroke()
        for k in range(1, 4):
            ctx.move_to(wx - 95 + k * 47.5, 400); ctx.line_to(wx - 95 + k * 47.5, 860); setc(ctx, '#2f8f8a'); ctx.set_line_width(5); ctx.stroke()
        for k in range(1, 4):
            ctx.move_to(wx - 95, 470 + k * 100); ctx.line_to(wx + 95, 470 + k * 100); ctx.stroke()
    # mihrab
    ctx.new_path(); ctx.move_to(930, 1330); ctx.line_to(930, 760); ctx.curve_to(930, 640, 1030, 600, 1060, 540); ctx.curve_to(1090, 600, 1190, 640, 1190, 760)
    ctx.line_to(1190, 1330); ctx.close_path(); fs(ctx, '#e0a83b', 6)
    ctx.new_path(); ctx.move_to(965, 1330); ctx.line_to(965, 780); ctx.curve_to(965, 690, 1040, 650, 1060, 610); ctx.curve_to(1080, 650, 1155, 690, 1155, 780)
    ctx.line_to(1155, 1330); ctx.close_path(); setc(ctx, '#1f6f6a'); ctx.fill()
    for k in range(5):
        ctx.new_path(); ctx.arc(1060, 760 + k * 110, 40, PI, 2 * PI); setc(ctx, '#7fd1c7', 0.6); ctx.set_line_width(4); ctx.stroke()
    # tiles
    ctx.rectangle(-700, 1120, 1630, 210); setc(ctx, '#2f8f8a'); ctx.fill()
    for k in range(-12, 22):
        x0 = k * 60
        if x0 > 900: break
        circ(ctx, x0, 1225, 18); setc(ctx, '#f6f1e3'); ctx.fill(); circ(ctx, x0, 1225, 7); setc(ctx, '#e8507a'); ctx.fill()
    ctx.rectangle(-700, 1110, 1630, 12); setc(ctx, '#e0a83b'); ctx.fill()
    # chandelier
    for cx_ in (540,):
        for k in range(-3, 4):
            ctx.move_to(cx_, -100); ctx.line_to(cx_ + k * 95, 330); setc(ctx, '#6a4a2a', 0.6); ctx.set_line_width(2); ctx.stroke()
        ell(ctx, cx_, 335, 300, 34); setc(ctx, '#c8963e'); ctx.set_line_width(10); ctx.stroke()
        for k in range(12):
            a = k / 12 * 2 * PI; lx, ly = cx_ + 300 * math.cos(a), 335 + 34 * math.sin(a)
            glow(ctx, lx, ly - 18, 40, '#ffe39a', 0.6); ell(ctx, lx, ly - 14, 7, 12); setc(ctx, '#fff6c8'); ctx.fill()
    # floor carpet
    ctx.rectangle(-700, 1330, 2600, 1100); setc(ctx, '#a8272d'); ctx.fill()
    for k in range(8):
        y = 1345 + k * 85
        ctx.rectangle(-700, y, 2600, 10); setc(ctx, '#e0a83b', 0.75); ctx.fill()
        for j in range(-8, 20):
            ctx.new_path(); ctx.arc(j * 110 + (k % 2) * 55, y + 60, 26, PI, 2 * PI); setc(ctx, '#d9534f'); ctx.set_line_width(5); ctx.stroke()
    # light beams
    if beams > 0:
        for wx in (330, 760):
            ctx.move_to(wx - 95, 500); ctx.line_to(wx + 95, 500); ctx.line_to(wx + 420, 1800); ctx.line_to(wx + 80, 1800); ctx.close_path()
            ctx.set_source(lgrad(0, 500, 0, 1800, [(0, '#fff1c4', 0.28 * beams), (1, '#fff1c4', 0)])); ctx.fill()
        rnd = random.Random(4)
        for k in range(26):
            px = rnd.uniform(200, 1100); py = (rnd.uniform(500, 1600) - t * 25) % 1100 + 500
            circ(ctx, px + (py - 500) * 0.25, py, rnd.uniform(1.5, 3.5)); setc(ctx, '#fff6c8', 0.5 * beams); ctx.fill()

# ---------------------------------------------------------------- fx
def speed_lines(ctx, t, a=1.0, cx=540, cy=960, col='#000'):
    if a <= 0: return
    rnd = random.Random(int(t * 12))
    for k in range(70):
        ang = rnd.uniform(0, 2 * PI); r0 = rnd.uniform(330, 520); wdt = rnd.uniform(0.006, 0.02)
        ctx.move_to(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0 * 1.5)
        ctx.line_to(cx + math.cos(ang - wdt) * 1600, cy + math.sin(ang - wdt) * 2400)
        ctx.line_to(cx + math.cos(ang + wdt) * 1600, cy + math.sin(ang + wdt) * 2400); ctx.close_path()
    setc(ctx, col, a); ctx.fill()

def burst_bg(ctx, t, c1, c2):
    ctx.rectangle(-700, -400, 2600, 2800); setc(ctx, c1); ctx.fill()
    for k in range(36):
        a0 = k / 36 * 2 * PI + t * 0.2
        ctx.move_to(540, 900); ctx.line_to(540 + math.cos(a0) * 2500, 900 + math.sin(a0) * 2500)
        ctx.line_to(540 + math.cos(a0 + 0.08) * 2500, 900 + math.sin(a0 + 0.08) * 2500); ctx.close_path()
    setc(ctx, c2); ctx.fill()

def sfx_text(ctx, txt, x, y, size, rot, a, c1='#fff27a', c2='#e8102e'):
    if a <= 0: return
    font(ctx, size, italic=True, black=True)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    e = ctx.text_extents(txt); ctx.move_to(-e[4] / 2, e[3] / 2); ctx.text_path(txt)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    setc(ctx, INK, a); ctx.set_line_width(26); ctx.stroke_preserve()
    setc(ctx, c2, a); ctx.set_line_width(12); ctx.stroke_preserve()
    setc(ctx, c1, a); ctx.fill(); ctx.restore()

# ---------------------------------------------------------------- scenes
def cam_apply(ctx, fx, fy, z, sx=0, sy=0):
    ctx.translate(W / 2 + sx, H / 2 + sy); ctx.scale(z, z); ctx.translate(-fx, -fy)

SHOTS = [(2.5, 540, 960, 1.0), (2.66, 470, 980, 1.12), (4.1, 260, 1000, 1.1), (6.9, 540, 960, 1.0),
         (11.96, 540, 990, 1.05), (14.5, 260, 1060, 1.35), (17.2, 540, 960, 1.0), (19.56, 880, 920, 1.9),
         (24.56, 150, 930, 1.9), (36.92, 880, 920, 1.9), (40.4, 520, 940, 1.0), (50.92, 520, 960, 1.05),
         (55.3, 150, 930, 1.9), (56.6, 165, 880, 2.6), (58.28, 150, 930, 1.9), (61.08, 820, 860, 1.25),
         (64.02, 880, 920, 1.9), (68.36, 540, 960, 1.0)]
def shot(t):
    cur = SHOTS[0]
    for s_ in SHOTS:
        if t >= s_[0]: cur = s_
    t0, fx, fy, z = cur
    return fx, fy, z * (1 + 0.015 * (t - t0))

POS = dict(imam=(880, FY + 25, 0.95), A=(650, FY, 0.9), B=(470, FY, 0.9), C=(300, FY, 0.9))
LOG_SPAWN = 14.45
def logs_free(ctx, t, mx):
    if t < LOG_SPAWN: return
    for i in range(6):
        r = random.Random(i * 3 + 1)
        x0 = mx + r.uniform(-60, 60); y0 = FY - 280
        vx = r.uniform(-260, 260); vy = r.uniform(-500, -200); dt = t - LOG_SPAWN
        x = x0 + vx * min(dt, 0.9) + vx * 0.15 * max(0, dt - 0.9)
        y = y0 + vy * dt + 0.5 * 2600 * dt * dt
        floor_y = FY + 30 + r.uniform(0, 70)
        rot = r.uniform(-3, 3) * min(dt, 0.8) + r.uniform(0, 3)
        if y > floor_y:
            y = floor_y - abs(math.sin(dt * 9)) * 40 * math.exp(-dt * 3)
            rot = r.uniform(0, 3) + r.uniform(-3, 3) * 0.8
        ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
        rrect(ctx, -90, -11, 180, 22, 10); fs(ctx, '#8b5a2b', 4)
        ell(ctx, 88, 0, 6, 10); fs(ctx, '#d9a066', 3)
        ctx.restore()
        if dt < 0.9 and y >= floor_y - 2:
            for k in range(3):
                circ(ctx, x + (k - 1) * 30, floor_y - 10, 18 + dt * 30); setc(ctx, '#f0e0c0', 0.5 * (1 - dt)); ctx.fill()

def scene_mosque(ctx, t, tc):
    fx, fy, z = shot(tc)
    shake = 0
    if 14.45 < tc < 16.0: shake = 22 * (1 - (tc - 14.45) / 1.55)
    if 56.6 < tc < 57.2 or 62.9 < tc < 63.6: shake = 12
    rs = random.Random(int(t * 24))
    sx, sy = rs.uniform(-shake, shake), rs.uniform(-shake, shake)
    shock = win(t, 50.92, 55.2, 0.15)
    angry = win(t, 19.56, 24.4, 0.12)
    ctx.save(); cam_apply(ctx, fx, fy, z, sx, sy)
    bg_interior(ctx, t)
    if angry > 0:
        ctx.save(); ctx.push_group(); burst_bg(ctx, t, '#ff3d3d', '#ffb347'); ctx.pop_group_to_source(); ctx.paint_with_alpha(angry * 0.85); ctx.restore()
    if shock > 0:
        ctx.save(); ctx.push_group(); burst_bg(ctx, t, '#2a1a6a', '#4b3aa8'); ctx.pop_group_to_source(); ctx.paint_with_alpha(shock * 0.9); ctx.restore()
    if 62.95 <= t < 64.5:
        ctx.save(); ctx.push_group(); burst_bg(ctx, t, '#ffe27a', '#ff9ad5'); ctx.pop_group_to_source(); ctx.paint_with_alpha(win(t, 62.95, 64.5, 0.1) * 0.8); ctx.restore()
    bend = seg(t, 13.0, 13.6) * (1 - seg(t, 17.2, 17.7))
    # ghosts behind people
    G = {'A': ('child', 43.6, 55.2), 'B': ('jar', 45.8, 55.2), 'C': ('house', 48.0, 55.2)}
    for n, (kind, g0, g1) in G.items():
        x, y, s = POS[n]
        ghost(ctx, x - 50, y - 560, 1.0, win(t, g0, g1, 0.4), kind, t)
    ghost(ctx, 760, 830, 1.05, win(t, 62.95, 70.2, 0.25), 'cow', t)
    if 62.95 <= t < 66: sfx_text(ctx, 'MÖÖÖ!', 760, 640, 110, -0.12, win(t, 63.1, 65.8, 0.15), '#ffffff', '#ff5ea8')
    people = {}
    # congregation
    for n in ('A', 'B', 'C'):
        x, y, s = POS[n]
        p = pose(); p['arms'] = 'fold'; p['eyes'] = 'closed' if 10.4 < t < 17.2 else 'normal'; p['smile'] = 0.1
        if 10.4 <= t < 11.2: p['arms'] = 'tekbir'
        p['bend'] = bend
        if 2.66 <= t < 6.9: p['eyes'] = 'normal'
        if 17.2 <= t < 24.4:
            p['face'] = -1 if t > 18.2 else 1; p['eyes'] = 'normal'; p['brow'] = -0.6; p['smile'] = -0.4; p['sweat'] = 0.8 if n == 'B' else 0
            p['arms'] = 'down'
        if 24.4 <= t:
            p['arms'] = 'down'; p['face'] = -1; p['eyes'] = 'normal'; p['look'] = 1
        if 40.4 <= t < 50.92:
            p['face'] = -1
            hit = {'A': 43.6, 'B': 45.8, 'C': 48.0}[n]
            if t >= hit: p['eyes'] = 'wide'; p['sweat'] = 1; p['blush'] = 0.6; p['smile'] = -0.3
        if 50.92 <= t < 55.3:
            p['eyes'] = 'shock'; p['gloom'] = 1; p['sweat'] = 1; p['tremble'] = 0.2
        if 55.3 <= t: p['face'] = 1 if t > 58 else -1; p['eyes'] = 'normal'
        if 62.95 <= t < 70: p['eyes'] = 'wide'; p['smile'] = 0.5
        people[n] = draw_char(ctx, n, x, y, s, p, t)
    # imam
    x, y, s = POS['imam']
    p = pose(); p['arms'] = 'fold'; p['face'] = 1; p['mouth'] = mouth_of('imam', t)
    p['eyes'] = 'closed' if 10.4 < t < 17.2 else 'normal'
    if 10.4 <= t < 11.2: p['arms'] = 'tekbir'
    p['bend'] = bend
    if 17.2 <= t < 19.56: p['arms'] = 'down'; p['eyes'] = 'normal'
    if 19.56 <= t < 36.9:
        p['face'] = -1; p['arms'] = 'hips'; p['eyes'] = 'angry' if t < 28 else 'normal'; p['vein'] = 1 if t < 30 else 0; p['brow'] = -0.4; p['smile'] = -0.3
    if 36.9 <= t < 62.9:
        p['face'] = -1; p['arms'] = 'down'; p['eyes'] = 'wide'; p['sweat'] = 0.7 if t > 40 else 0; p['smile'] = -0.2
        if speaker(t) == 'imam': p['arms'] = 'shrug'
    if 62.9 <= t:
        p['face'] = -1; p['eyes'] = 'shock' if t < 64.2 else 'wide'; p['blush'] = seg(t, 64, 64.6); p['sweat'] = 1
        p['gloom'] = 1 if t < 64.2 else 0; p['tremble'] = 0.4 if t < 66 else 0; p['arms'] = 'down'
        if t > 64.2: p['look'] = -1; p['smile'] = -0.1; p['tilt'] = 0.12
    people['imam'] = draw_char(ctx, 'imam', x, y, s, p, t)
    # meczup
    mkeys = [(2.5, 60), (4.1, 60), (5.1, -260), (6.9, -260), (9.6, 130)]
    mx = kf(t, mkeys)
    p = pose(); p['mouth'] = mouth_of('mec', t); p['smile'] = 0.6
    p['walk'] = t * 10 if moving(t, mkeys) else None
    if 4.1 <= t < 5.2: p['face'] = -1; p['walk'] = t * 22
    if 2.66 <= t < 4.1: p['look'] = math.sin(t * 4) * 1.4; p['eyes'] = 'wide'; p['smile'] = 0.1
    p['wood'] = t >= 6.0 and t < LOG_SPAWN
    if 10.36 <= t < 11.2: p['arms'] = 'tekbir'
    if 11.2 <= t < 17.2: p['arms'] = 'fold'; p['eyes'] = 'closed'
    p['bend'] = bend
    if 14.45 <= t < 17.2: p['eyes'] = 'wide'; p['sweat'] = 1
    if 17.2 <= t < 24.5: p['eyes'] = 'normal'; p['sweat'] = 0.8; p['smile'] = 0.3; p['arms'] = 'down'
    if 24.5 <= t:
        p['arms'] = 'explain' if speaker(t) == 'mec' else 'hips'; p['smile'] = 0.7
        if 24.5 <= t < 28: p['eyes'] = 'happy'
    if 30.4 <= t < 33.0: p['arms'] = 'point'
    if 41.92 <= t < 50.72:
        p['arms'] = 'pointup' if (t - 41.92) % 2.2 < 1.5 else 'point'; p['eyes'] = 'wide'
    if 55.3 <= t < 58.3: p['eyes'] = 'happy' if t < 56.6 else 'wide'; p['arms'] = 'hips'
    if 58.3 <= t < 63.8: p['arms'] = 'point'; p['eyes'] = 'normal'
    if 62.9 <= t < 70: p['eyes'] = 'happy'; p['arms'] = 'hips'
    if mx > -200:
        people['mec'] = draw_char(ctx, 'mec', mx, FY, 0.9, p, t)
    if 4.3 <= t < 5.6:
        for k in range(5):
            circ(ctx, mx + 60 + k * 35, FY - 20 - k * 6, 30 + k * 6); setc(ctx, '#f6e7c8', 0.7 * (1 - (t - 4.3) / 1.3)); ctx.fill()
    logs_free(ctx, t, 130 + 60)
    ctx.restore()
    # screen-space fx
    if 4.1 <= t < 5.2: speed_lines(ctx, t, 0.5, 300, 1000)
    if 14.45 <= t < 16.2:
        speed_lines(ctx, t, 0.7)
        sfx_text(ctx, 'PATIR', 330, 700, 150, -0.15, win(t, 14.5, 16.2, 0.1))
        sfx_text(ctx, 'KÜTÜR!', 700, 880, 150, 0.12, win(t, 14.8, 16.2, 0.1))
    if 56.6 <= t < 58.2: speed_lines(ctx, t, 0.85, 540, 900)
    if 50.92 <= t < 55.2:
        sfx_text(ctx, '!!', 540, 420, 200, 0, win(t, 51.0, 55.2, 0.15), '#ffffff', '#3b4cc0')

def scene_ext(ctx, t, tc, with_mec=True):
    z = 1.0 + 0.02 * (tc % 10)
    ctx.save(); cam_apply(ctx, 540, 1000, z)
    bg_exterior(ctx, t)
    if with_mec:
        keys = [(0, -120), (2.5, 470)]
        p = pose(); p['walk'] = t * 9; p['smile'] = 0.6; p['eyes'] = 'normal'
        draw_char(ctx, 'mec', kf(t, keys), 1480, 0.75, p, t)
    ctx.restore()

def scene_lesson(ctx, t, tc):
    # 70 - 99.6
    if t < 75.7:
        # walking with worldly pile
        ctx.save()
        ctx.rectangle(0, 0, W, H); ctx.set_source(lgrad(0, 0, 0, 1300, [(0, '#2a1a5a'), (0.7, '#c2477a'), (1, '#ff9a6b')])); ctx.fill()
        stars(ctx, t, 500, 30)
        off = (t * 220) % 1400
        for k in range(-1, 9):
            bx = k * 200 - off % 200
            r = random.Random(int((k * 200 - off) // 200) + 99)
            hh = r.uniform(300, 700)
            ctx.rectangle(bx, 1330 - hh, 180, hh); fs(ctx, r.choice(['#3a2a6a', '#4a2f7a', '#2d2257']), 4)
            for wy in range(int(1330 - hh + 30), 1300, 70):
                for wx in (bx + 25, bx + 100):
                    ctx.rectangle(wx, wy, 45, 35); setc(ctx, '#ffd27a' if r.random() > 0.4 else '#2a1a4a'); ctx.fill()
        ctx.rectangle(0, 1330, W, H); setc(ctx, '#1f1636'); ctx.fill()
        for k in range(12):
            x0 = (k * 120 - t * 220 * 1.0) % 1440 - 120
            ctx.rectangle(x0, 1420, 70, 10); setc(ctx, '#ffd27a', 0.6); ctx.fill()
        p = pose(); p['walk'] = t * 9; p['eyes'] = 'normal'; p['sweat'] = 1; p['smile'] = -0.3; p['brow'] = 0.6; p['arms'] = 'down'
        p['fa'] = (0.5, 2.6); p['ba'] = (-0.3, 2.6); p['tilt'] = 0.15
        wob = math.sin(t * 4) * 0.04
        ctx.save(); ctx.translate(430, 1060); ctx.rotate(wob)
        for k, kind in enumerate(('house', 'case', 'coins', 'phone', 'people')):
            ctx.save(); ctx.translate(-20 + ((k % 2) * 30), -k * 150); ctx.scale(0.7, 0.7)
            ctx.push_group(); ghost(ctx, 0, 0, 1.0, 1.0, kind, 0); ctx.pop_group_to_source(); ctx.paint()
            ctx.restore()
        ctx.restore()
        draw_char(ctx, 'G', 540, 1400, 1.0, p, t)
        ctx.restore()
        return
    ctx.save(); cam_apply(ctx, 540, 1000, 1.0 + 0.01 * (tc - 75.7))
    bg_interior(ctx, t, beams=1.0 + 0.6 * seg(t, 94.9, 96.5))
    # seccade
    ctx.move_to(420, 1360); ctx.line_to(820, 1360); ctx.line_to(880, 1470); ctx.line_to(360, 1470); ctx.close_path(); fs(ctx, '#1f7a4d', 5)
    ctx.move_to(450, 1375); ctx.line_to(790, 1375); ctx.line_to(838, 1455); ctx.line_to(402, 1455); ctx.close_path(); setc(ctx, '#e0a83b'); ctx.set_line_width(4); ctx.stroke()
    items = [('coins', 75.8), ('case', 81.0), ('coins', 83.4), ('phone', 84.0), ('people', 84.8)]
    drop = seg(t, 88.3, 90.0)
    door = (110, 1000)
    gx, gy = 500, 1180
    for k, (kind, t0) in enumerate(items):
        if t < t0: continue
        a = win(t, t0, 120, 0.4)
        bx, by = gx - 70 + (k % 2) * 50, gy - 120 - k * 125
        x = lerp(bx, door[0] + 20, drop); y = lerp(by, door[1], drop)
        s = lerp(0.72, 0.15, drop)
        ghost(ctx, x, y, s, a * (1 - seg(t, 89.6, 90.1)), kind, t)
    # globe at door waiting
    ga = seg(t, 89.8, 90.4)
    if ga > 0:
        ctx.save(); ctx.push_group()
        globe(ctx, 115, 1170, 0.8, t, mood=1 if 92.7 < t < 95 else 0)
        if 92.7 < t < 95:
            ctx.new_path(); ctx.move_to(185, 1060); ctx.curve_to(205, 1090, 203, 1105, 185, 1105); ctx.curve_to(167, 1105, 165, 1090, 185, 1060)
            fs(ctx, '#bfe8ff', 3)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(ga); ctx.restore()
        if 90.0 < t < 92.8:
            sfx_text(ctx, 'tık tık', 250, 1330, 54, -0.1, win(t, 90.2, 92.8, 0.2), '#ffffff', '#3b4cc0')
    p = pose(); p['arms'] = 'fold'; p['eyes'] = 'closed'; p['smile'] = 0.1
    if 75.8 <= t < 88.3:
        p['brow'] = 0.5 + 0.3 * math.sin(t * 3); p['eyes'] = 'normal'; p['look'] = math.sin(t * 2.2) * 1.4; p['sweat'] = 0.6 * seg(t, 82, 83)
    if t >= 88.3: p['smile'] = 0.4 * seg(t, 89, 90)
    draw_char(ctx, 'G', 620, 1420, 1.0, p, t)
    if t >= 94.9:
        for k in range(8):
            a = t * 0.6 + k * 0.8
            sparkle(ctx, 620 + 200 * math.cos(a), 1050 + 250 * math.sin(a * 1.3), 14, 0.8)
        glow(ctx, 640, 900, 420, '#fff1c4', 0.35 * seg(t, 94.9, 96.0))
    ctx.restore()

def scene_end(ctx, t, tc):
    scene_ext(ctx, t, tc, with_mec=False)
    a = seg(t, 101.7, 102.3)
    title(ctx, a, 560)

def title(ctx, a, y):
    if a <= 0: return
    for txt, yy, size in (('SIRTINDAKİ', y, 130), ('YÜK', y + 150, 170)):
        font(ctx, size, italic=True, black=True); e = ctx.text_extents(txt)
        x = 540 - e[4] / 2
        ctx.move_to(x + 10, yy + 10); ctx.text_path(txt); setc(ctx, '#140a24', 0.8 * a); ctx.fill()
        ctx.move_to(x, yy); ctx.text_path(txt); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        setc(ctx, INK, a); ctx.set_line_width(24); ctx.stroke_preserve()
        setc(ctx, '#e8102e', a); ctx.set_line_width(12); ctx.stroke_preserve()
        ctx.set_source(lgrad(0, yy - size, 0, yy, [(0, '#ffffff', a), (0.6, '#fff27a', a), (1, '#ffb347', a)])); ctx.fill()

# ---------------------------------------------------------------- subtitles
TEXTS = [
    "Bir gün bir meczup namaz kılmak için camiye giriyor.", "Cemaate şöyle bir bakıyor.",
    "Sonra hiçbir şey söylemeden camiden hızlıca geri çıkıyor.",
    "Dışarıdaki odunları sırtına bağlamış olarak tekrar camiye giriyor.", "O hâliyle namaza duruyor.",
    "İşte kıyamdır, rükûdur, secdedir derken", "sırtındaki o odunlar eğilince patır kütür yere dökülüyor.",
    "Tabii her yer dağılıyor.", "Cemaat huzursuz oluyor.", "İmam da sertçe adama dönüyor, diyor ki:",
    "“Yahu mübarek,", "sırtında odunlarla namaz mı kılınır?”",
    "Meczup yaptığı şeyin gayet doğru olduğunu iddia ederek:", "“Yahu hocam, ben geldim, sırtım boştu.",
    "Ama baktım ki herkesin sırtında bir şey var.", "Demek ki burada âdet böyle,",
    "ben de gidip odunlarımı alayım geleyim dedim.”", "İmam şaşırıyor tabii ki.",
    "“Ne demek, herkesin sırtında bir şeyler var?” diyor.", "Meczup başlıyor cemaati göstermeye.",
    "“Yahu hocam, bak şu adamın", "sırtında mavi gözlü bir çocuk vardı.", "Şunun sırtında bir küp altın vardı.",
    "Yahu herkesin sırtında bir şey vardı hocam.", "Hiç boş yoktu.”", "Cemaat tabii ki donup kalıyor.",
    "Çünkü meczup kime ne söylediyse doğru söylemiş.", "Sonra meczup imama dönüyor.",
    "Asıl bombayı o zaman patlatıyor.", "“Yahu hocam, en çok da sana şaşırdım.", "Yahu hocam, senin sırtında da",
    "inek vardı!”", "İmam da namaz sırasında sütten kesilen", "yaşlı ineğini satıp satmamayı düşünüyormuş.",
    "Tabii bu kıssadan bir hisse.", "Ama kardeşlerim, hikâyenin bize verdiği ders çok ağır, bak.",
    "Dünyalık işlerimizde zaten", "dünyaya dalıyoruz.", "Ama bazen Allah'ın huzuruna çıktığımızda bile",
    "dünyayı sırtımızdan indiremiyoruz.", "Bedenimiz seccadede ama aklımız ticarette.",
    "Parada, işte, telefonda, insanlarda.", "Hiç değilse kardeşlerim, o birkaç dakika boyunca",
    "dünyayı sırtımızdan indirelim.", "Dünya kapıda beklesin.", "Bir yere kaçtığı yok dünyanın.",
    "Dünyanın işi biter mi ya?", "Bitmez.", "Öyleyse biz Rabbimizin huzuruna gerçekten çıkalım.",
    "Hakiki manada çıkalım.", "Bu hikâye de bize büyük bir ders olsun.",
]

def wrap(ctx, text, maxw):
    lines = []; cur = ''
    for wd in text.split():
        cand = (cur + ' ' + wd).strip()
        if ctx.text_extents(cand)[4] > maxw and cur: lines.append(cur); cur = wd
        else: cur = cand
    if cur: lines.append(cur)
    return lines

def draw_subs(ctx, t):
    txt = None
    for i, (a, b, c) in enumerate(CUES):
        nxt = CUES[i + 1][0] if i + 1 < len(CUES) else DUR
        if a <= t < min(b + 0.4, nxt): txt = c
    if not txt: return
    font(ctx, 58)
    lines = wrap(ctx, txt, 940)
    lh = 74; y0 = 1470 - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        e = ctx.text_extents(ln); ctx.move_to(540 - e[4] / 2, y0 + i * lh + 20); ctx.text_path(ln)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    setc(ctx, '#000'); ctx.set_line_width(12); ctx.stroke_preserve(); setc(ctx, '#ffe14d'); ctx.fill()

# ---------------------------------------------------------------- VHS post
_rng = np.random.default_rng(1)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_vig = 1 - 0.55 * (((_xx - W / 2) / (W * 0.75)) ** 2 + ((_yy - H / 2) / (H * 0.72)) ** 2)
_scan = np.where((np.arange(H) % 3) == 0, 0.86, 1.0).astype(np.float32)[:, None]
MASK = (np.clip(_vig, 0.35, 1) * _scan * 256).astype(np.uint16)[:, :, None]
NOISE = [_rng.integers(-5, 6, size=(H // 3, W // 3, 1), dtype=np.int16).repeat(3, 0).repeat(3, 1) for _ in range(3)]
del _yy, _xx, _vig

def vhs(buf, t, glitch):
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 4)
    out = img.copy()
    out[:, 4:, 2] = img[:, :-4, 2]
    out[:, :-4, 0] = img[:, 4:, 0]
    rgb = (out[:, :, :3].astype(np.uint16) * MASK) >> 8
    rgb = rgb.astype(np.int16) + NOISE[int(t * 12) % 3] + 6
    out[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    r = random.Random(int(t * 24))
    if glitch > 0 or r.random() < 0.03:
        for _ in range(3 if glitch > 0 else 1):
            y = r.randint(0, H - 60); h = r.randint(8, 50); sh = r.randint(-40, 40) if glitch else r.randint(-12, 12)
            out[y:y + h] = np.roll(out[y:y + h], sh, axis=1)
            if glitch: out[y:y + h, :, :3] = np.clip(out[y:y + h, :, :3].astype(np.int16) + 40, 0, 255).astype(np.uint8)
    ty = int((t * 260) % (H + 200)) - 100
    if 0 <= ty < H - 6:
        out[ty:ty + 6, :, :3] = np.clip(out[ty:ty + 6, :, :3].astype(np.int16) + 18, 0, 255).astype(np.uint8)
    return out.tobytes()

CUTS = (2.5, 70.0, 75.7, 99.6)
def black_alpha(t):
    a = 0
    for T in CUTS: a = max(a, 1 - abs(t - T) / 0.22)
    return clamp(max(a, 1 - t / 0.4, (t - (DUR - 0.7)) / 0.7))

def render(ctx, t):
    ta = math.floor(t * 12) / 12          # animate on twos
    setc(ctx, '#000'); ctx.paint()
    ctx.save()
    if t < 2.5: scene_ext(ctx, ta, t)
    elif t < 70.0: scene_mosque(ctx, ta, t)
    elif t < 99.6: scene_lesson(ctx, ta, t)
    else: scene_end(ctx, ta, t)
    ctx.restore()
    a = black_alpha(t)
    if a > 0: setc(ctx, '#000', a); ctx.paint()
    if t < 2.6: title(ctx, seg(t, 0.2, 0.6) * (1 - seg(t, 2.1, 2.45)), 420)
    draw_subs(ctx, t)

def glitch_at(t): return any(abs(t - T) < 0.25 for T in CUTS) or 14.45 < t < 14.7 or 62.95 < t < 63.15

if __name__ == '__main__':
    import subprocess
    mode = sys.argv[1]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if mode == 'png':
        for ts in sys.argv[3:]:
            t = float(ts); ctx = cairo.Context(surf); render(ctx, t); surf.flush()
            data = vhs(bytes(surf.get_data()), t, glitch_at(t))
            s2 = cairo.ImageSurface.create_for_data(bytearray(data), cairo.FORMAT_ARGB32, W, H)
            s2.write_to_png(os.path.join(sys.argv[2], f'f_{t:07.2f}.png'))
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                               '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                               '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fr in range(f0, f1):
            t = fr / FPS; ctx = cairo.Context(surf); render(ctx, t); surf.flush()
            ff.stdin.write(vhs(bytes(surf.get_data()), t, glitch_at(t)))
        ff.stdin.close(); ff.wait()
