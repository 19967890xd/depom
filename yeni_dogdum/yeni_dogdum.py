import os, sys, math, json, random, importlib.util
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('base', os.path.join(HERE, 'base.py'))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)
from math import pi as PI
W, H, FPS = 1080, 1920, 24
DUR = 95.7
clamp, sm, lerp, seg, win, kf, moving = B.clamp, B.sm, B.lerp, B.seg, B.win, B.kf, B.moving
setc, fs, ell, circ, rrect, lgrad, glow, sparkle, font, mix = B.setc, B.fs, B.ell, B.circ, B.rrect, B.lgrad, B.glow, B.sparkle, B.font, B.mix
INK = B.INK

SPEAK = [(5.6, 7.72, 'cal1'), (21.24, 24.18, 'es'), (64.96, 69.24, 'es'), (69.4, 71.92, 'torun'), (72.16, 77.28, 'dede')]
def mouth(n, t):
    for a, b, who in SPEAK:
        if a <= t < b and who == n: return B.env(t) * (0.5 + 0.5 * abs(math.sin(t * 16)))
    return 0.0
def P(**kw):
    p = B.pose(); p.update(kw); return p
def char(ctx, n, x, y, s, p, t): return B.draw_char(ctx, n, x, y, s, p, t)
def cam(ctx, fx, fy, z): ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-fx, -fy)
def tinted(ctx, fn, col, amt, alpha=1.0):
    ctx.push_group(); fn(); ctx.set_operator(cairo.OPERATOR_ATOP); setc(ctx, col, amt); ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER); ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)

def text_c(ctx, txt, x, y, size, fill, stroke=INK, lw=12, a=1.0, italic=False, black=True):
    font(ctx, size, italic=italic, black=black); e = ctx.text_extents(txt)
    ctx.move_to(x - e[4] / 2, y); ctx.text_path(txt); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if lw: setc(ctx, stroke, a); ctx.set_line_width(lw); ctx.stroke_preserve()
    setc(ctx, fill, a); ctx.fill()

# ---------------------------------------------------------------- props
def armchair(ctx, x, y, s=1.0, front=False):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    if not front:
        rrect(ctx, -200, -430, 330, 340, 60); fs(ctx, '#a0522d', 6)
        for k in range(3): ctx.move_to(-150 + k * 100, -400); ctx.line_to(-150 + k * 100, -120); setc(ctx, '#7a3b1e'); ctx.set_line_width(4); ctx.stroke()
        rrect(ctx, -220, -140, 380, 110, 30); fs(ctx, '#b5653a', 6)
        for lx in (-190, 120): ctx.rectangle(lx, -30, 30, 30); fs(ctx, '#5a3018', 4)
    else:
        rrect(ctx, 100, -240, 90, 220, 36); fs(ctx, '#b5653a', 6)
    ctx.restore()

def tea(ctx, x, y, s=1.0, steam_t=None):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ell(ctx, 0, 10, 70, 16); fs(ctx, '#d9a63a', 4)
    ctx.move_to(-26, -70); ctx.curve_to(-12, -40, -12, -30, -24, 0); ctx.line_to(24, 0); ctx.curve_to(12, -30, 12, -40, 26, -70); ctx.close_path()
    fs(ctx, '#c0392b', 3); ctx.move_to(-24, -70); ctx.line_to(24, -70); setc(ctx, INK); ctx.set_line_width(3); ctx.stroke()
    ctx.move_to(-24, -62); ctx.line_to(24, -62); setc(ctx, '#ffffff', 0.5); ctx.set_line_width(6); ctx.stroke()
    if steam_t is not None:
        for k in range(3):
            ph = (steam_t * 0.8 + k / 3) % 1
            ctx.move_to(-10 + k * 10, -80 - ph * 80); ctx.curve_to(0 + k * 10, -95 - ph * 80, -20 + k * 10, -110 - ph * 80, -8 + k * 10, -125 - ph * 80)
            setc(ctx, '#ffffff', 0.6 * (1 - ph)); ctx.set_line_width(5); ctx.stroke()
    ctx.restore()

def baglama(ctx, x, y, s=1.0, rot=-0.5):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    rrect(ctx, -12, -420, 24, 330, 6); fs(ctx, '#6b3a1e', 4)
    for k in range(10): ctx.move_to(-12, -400 + k * 30); ctx.line_to(12, -400 + k * 30); setc(ctx, '#e8d9a8'); ctx.set_line_width(2); ctx.stroke()
    rrect(ctx, -18, -470, 36, 60, 8); fs(ctx, '#5a3018', 4)
    for k in range(3): circ(ctx, -26, -455 + k * 18, 6); fs(ctx, '#e8d9a8', 2)
    ctx.new_path(); ctx.move_to(0, -110); ctx.curve_to(-120, -90, -110, 80, 0, 90); ctx.curve_to(110, 80, 120, -90, 0, -110); ctx.close_path(); fs(ctx, '#a0602e', 5)
    ctx.save(); ctx.new_path(); ctx.move_to(0, -110); ctx.curve_to(-120, -90, -110, 80, 0, 90); ctx.curve_to(110, 80, 120, -90, 0, -110); ctx.clip()
    for k in range(-5, 6): ctx.move_to(k * 22, -120); ctx.line_to(k * 22, 100); setc(ctx, '#7a4a20'); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()
    ell(ctx, 0, 0, 76, 60); fs(ctx, '#e8c48a', 4)
    for k in (-6, 0, 6): ctx.move_to(k, -440); ctx.line_to(k * 1.5, 40); setc(ctx, '#f6f1e3'); ctx.set_line_width(2); ctx.stroke()
    ctx.restore()

def notebook(ctx, x, y, s=1.0, opened=0.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    if opened < 0.5:
        rrect(ctx, -90, -120, 180, 240, 10); fs(ctx, '#7a2e3a', 5)
        rrect(ctx, -60, -60, 120, 40, 6); fs(ctx, '#e8d9a8', 3)
    else:
        rrect(ctx, -280, -200, 560, 400, 14); fs(ctx, '#5a2a30', 6)
        for sg in (-1, 1):
            ctx.new_path(); ctx.move_to(0, -180); ctx.curve_to(sg * 90, -200, sg * 200, -195, sg * 262, -182)
            ctx.line_to(sg * 262, 182); ctx.curve_to(sg * 200, 172, sg * 90, 172, 0, 186); ctx.close_path(); fs(ctx, '#f6ecd2', 4)
        ctx.move_to(0, -180); ctx.line_to(0, 186); setc(ctx, INK); ctx.set_line_width(4); ctx.stroke()
    ctx.restore()

def thought(ctx, bx, by, rx, ry, tail, inner, a=1.0):
    if a <= 0.01: return
    ctx.save(); ctx.translate(bx, by); ctx.scale(a, a); ctx.translate(-bx, -by)
    for fx, rr in ((0.3, 12), (0.55, 20)):
        circ(ctx, lerp(tail[0], bx, fx), lerp(tail[1], by + ry, fx), rr); fs(ctx, '#fffdf5', 4)
    ctx.new_path()
    for k in range(10):
        an = k / 10 * 2 * PI; circ(ctx, bx + math.cos(an) * rx, by + math.sin(an) * ry, 44)
    ell(ctx, bx, by, rx, ry); setc(ctx, INK); ctx.set_line_width(8); ctx.stroke_preserve(); setc(ctx, '#fffdf5'); ctx.fill()
    ctx.save(); ell(ctx, bx, by, rx + 10, ry + 10); ctx.clip(); inner(); ctx.restore()
    ctx.restore()

def icon(ctx, kind, x, y, s=1.0, t=0.0):
    if s < 0.01: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    if kind == 'pill':
        rrect(ctx, -40, -60, 80, 110, 14); fs(ctx, '#ffffff', 4); rrect(ctx, -46, -78, 92, 26, 8); fs(ctx, '#e8507a', 4)
        ctx.rectangle(-30, -20, 60, 30); setc(ctx, '#7fd3ff'); ctx.fill()
        ctx.save(); ctx.translate(55, 30); ctx.rotate(0.6); rrect(ctx, -26, -11, 52, 22, 11); fs(ctx, '#ffd23f', 3); ctx.restore()
    elif kind == 'bill':
        rrect(ctx, -60, -70, 120, 140, 8); fs(ctx, '#ffffff', 4)
        for k in range(4): ctx.move_to(-40, -40 + k * 24); ctx.line_to(30, -40 + k * 24); setc(ctx, '#9a9aa2'); ctx.set_line_width(5); ctx.stroke()
        text_c(ctx, '₺', 0, 62, 54, '#e8102e', INK, 6)
    elif kind == 'cloud':
        for dx, dy, r in ((-30, 0, 34), (10, -16, 40), (44, 4, 30)): circ(ctx, dx, dy, r)
        fs(ctx, '#8a8fa8', 4)
        for k in range(4): ctx.move_to(-30 + k * 22, 40); ctx.line_to(-38 + k * 22, 70); setc(ctx, '#3a7ab8'); ctx.set_line_width(5); ctx.stroke()
    elif kind == 'school':
        rrect(ctx, -55, -50, 110, 110, 16); fs(ctx, '#ff7a3a', 4); rrect(ctx, -30, -72, 60, 30, 10); setc(ctx, INK); ctx.set_line_width(5); ctx.stroke()
        rrect(ctx, -35, -10, 70, 40, 8); fs(ctx, '#ffd23f', 3)
    elif kind == 'clock':
        circ(ctx, 0, 0, 60); fs(ctx, '#ffffff', 5)
        for k in range(12):
            a = k / 12 * 2 * PI; ctx.move_to(50 * math.cos(a), 50 * math.sin(a)); ctx.line_to(56 * math.cos(a), 56 * math.sin(a))
        setc(ctx, INK); ctx.set_line_width(3); ctx.stroke()
        for ln, sp, wd in ((40, 4.0, 5), (28, 0.4, 7)):
            a = t * sp - PI / 2; ctx.move_to(0, 0); ctx.line_to(ln * math.cos(a), ln * math.sin(a)); setc(ctx, INK); ctx.set_line_width(wd); ctx.stroke()
    elif kind == 'q':
        text_c(ctx, '?', 0, 50, 150, '#ffffff', INK, 14)
    elif kind == 'book':
        rrect(ctx, -60, -45, 120, 90, 8); fs(ctx, '#3d6fb6', 4); ctx.move_to(0, -45); ctx.line_to(0, 45); setc(ctx, INK); ctx.set_line_width(4); ctx.stroke()
    elif kind == 'laptop':
        rrect(ctx, -60, -60, 120, 80, 8); fs(ctx, '#2a2a3a', 4); rrect(ctx, -50, -52, 100, 62, 4); setc(ctx, '#7fd3ff'); ctx.fill()
        ctx.move_to(-80, 30); ctx.line_to(80, 30); ctx.line_to(66, 44); ctx.line_to(-66, 44); ctx.close_path(); fs(ctx, '#9a9aa2', 4)
    elif kind == 'coin':
        ell(ctx, 0, 0, 44, 44); fs(ctx, '#ffd23f', 4); text_c(ctx, '₺', 0, 18, 50, '#b8860b', INK, 0)
    elif kind == 'heart':
        ctx.move_to(0, 40); ctx.curve_to(-70, -10, -40, -70, 0, -30); ctx.curve_to(40, -70, 70, -10, 0, 40); fs(ctx, '#ff5e7e', 5)
    elif kind == 'ring':
        circ(ctx, 0, 10, 40); setc(ctx, '#f2c14e'); ctx.set_line_width(14); ctx.stroke(); ctx.move_to(-14, -36); ctx.line_to(0, -54); ctx.line_to(14, -36); ctx.close_path(); fs(ctx, '#7fe7ff', 3)
    elif kind == 'case':
        rrect(ctx, -70, -40, 140, 90, 12); fs(ctx, '#7a4a2a', 4); rrect(ctx, -24, -60, 48, 24, 6); setc(ctx, INK); ctx.set_line_width(5); ctx.stroke()
    elif kind == 'mom':
        circ(ctx, 0, -20, 34); fs(ctx, '#f0c8a0', 4); ctx.new_path(); ctx.arc(0, -20, 40, PI * 1.0, PI * 2.0); ctx.close_path(); fs(ctx, '#9a9aa2', 4)
        ctx.new_path(); ctx.arc(0, 60, 50, PI, 2 * PI); ctx.close_path(); fs(ctx, '#7a5a9a', 4)
    elif kind == 'kid':
        circ(ctx, 0, -14, 30); fs(ctx, '#f6cfa8', 4); ctx.new_path(); ctx.arc(0, 56, 42, PI, 2 * PI); ctx.close_path(); fs(ctx, '#ffb020', 4)
    ctx.restore()

# ---------------------------------------------------------------- backgrounds
def retro_window(ctx, x, y, w, h):
    ctx.rectangle(x, y, w, h); ctx.set_source(lgrad(0, y, 0, y + h, [(0, '#6a5ad8'), (0.55, '#ff8ab8'), (1, '#ffd9a0')])); ctx.fill_preserve()
    setc(ctx, '#5a3a2a'); ctx.set_line_width(16); ctx.stroke()
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip(); B.retro_sun(ctx, x + w * 0.65, y + h * 0.7, w * 0.28)
    rnd = random.Random(int(x))
    for k in range(6):
        bw = rnd.uniform(40, 80); bh = rnd.uniform(60, h * 0.5); bx = x + k * w / 6
        ctx.rectangle(bx, y + h - bh, bw, bh); setc(ctx, '#3a2a6a'); ctx.fill()
    ctx.restore()
    ctx.move_to(x + w / 2, y); ctx.line_to(x + w / 2, y + h); setc(ctx, '#5a3a2a'); ctx.set_line_width(10); ctx.stroke()

def bg_office(ctx, t):
    ctx.rectangle(-600, -400, 2300, 1800); ctx.set_source(lgrad(0, 0, 0, 1250, [(0, '#c9d6ec'), (1, '#e9eef8')])); ctx.fill()
    retro_window(ctx, 120, 420, 360, 460); retro_window(ctx, 600, 420, 360, 460)
    # banner
    ctx.move_to(60, 230); ctx.curve_to(400, 330, 680, 330, 1020, 230); ctx.line_to(1020, 330); ctx.curve_to(680, 430, 400, 430, 60, 330); ctx.close_path(); fs(ctx, '#e8507a', 5)
    font(ctx, 52, black=True); txt = 'İYİ EMEKLİLİKLER!'; e = ctx.text_extents(txt)
    ctx.move_to(540 - e[4] / 2, 345); ctx.text_path(txt); setc(ctx, '#ffffff'); ctx.fill()
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#8a9ab8'); ctx.fill()
    for k in range(-10, 30): ctx.move_to(k * 100, 1250); ctx.line_to(k * 100 - 250, 2000); setc(ctx, '#7a8aa8'); ctx.set_line_width(3); ctx.stroke()
    rrect(ctx, 650, 1060, 420, 200, 10); fs(ctx, '#8b5a2b', 5)
    rrect(ctx, 760, 960, 160, 110, 8); fs(ctx, '#2a2a3a', 4); rrect(ctx, 770, 970, 140, 88, 4); setc(ctx, '#7fd3ff'); ctx.fill()
    # cake
    rrect(ctx, 960, 990, 110, 70, 10); fs(ctx, '#ffd9e6', 4); ctx.rectangle(960, 1010, 110, 12); setc(ctx, '#e8507a'); ctx.fill()
    for k in range(3):
        ctx.rectangle(980 + k * 30, 960, 8, 30); setc(ctx, '#7fe7ff'); ctx.fill(); glow(ctx, 984 + k * 30, 952, 16, '#ffd23f', 0.9)

def bg_home(ctx, t, evening=False):
    top = '#f6d9b8' if not evening else '#d8b8d8'
    ctx.rectangle(-600, -400, 2300, 1800); ctx.set_source(lgrad(0, 0, 0, 1250, [(0, top), (1, '#fbe9d2')])); ctx.fill()
    for k in range(-6, 20):
        ctx.rectangle(k * 90, -400, 45, 1650); setc(ctx, '#ffffff', 0.12); ctx.fill()
    retro_window(ctx, 640, 400, 340, 440)
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#b07a4f'); ctx.fill()
    ell(ctx, 540, 1400, 520, 120); setc(ctx, '#b3263e'); ctx.fill(); ell(ctx, 540, 1400, 470, 100); setc(ctx, '#e0a83b'); ctx.set_line_width(6); ctx.stroke()
    # frames
    for fx_, fy_, c in ((120, 520, '#7fd3ff'), (300, 470, '#ffd23f')):
        rrect(ctx, fx_, fy_, 130, 160, 6); fs(ctx, '#8b5a2b', 6); ctx.rectangle(fx_ + 15, fy_ + 15, 100, 130); setc(ctx, c); ctx.fill()
        circ(ctx, fx_ + 65, fy_ + 70, 26); setc(ctx, '#f0c8a0'); ctx.fill()

def bg_door(ctx, t):
    ctx.rectangle(-600, -400, 2300, 1800); ctx.set_source(lgrad(0, 0, 0, 1250, [(0, '#e9d6c0'), (1, '#f6e7d2')])); ctx.fill()
    rrect(ctx, 600, 330, 360, 920, 12); fs(ctx, '#7a3b1e', 8)
    for k in range(3): rrect(ctx, 640, 380 + k * 280, 280, 230, 8); setc(ctx, '#5a2a14'); ctx.set_line_width(6); ctx.stroke()
    circ(ctx, 650, 820, 22); fs(ctx, '#f2c14e', 4)
    ctx.rectangle(300, 600, 30, 220); fs(ctx, '#5a3018', 4)
    for k, c in enumerate(('#3a4a6a', '#8a3a3a')):
        ctx.move_to(315, 640); ctx.curve_to(260 + k * 60, 700, 250 + k * 70, 860, 280 + k * 50, 960); ctx.line_to(340 + k * 50, 960)
        ctx.curve_to(360 + k * 40, 860, 350, 700, 315, 640); ctx.close_path(); fs(ctx, c, 4)
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#a0704a'); ctx.fill()

def bg_attic(ctx, t):
    ctx.rectangle(-600, -400, 2300, 1800); setc(ctx, '#5a4060'); ctx.fill()
    ctx.move_to(-600, 600); ctx.line_to(540, -100); ctx.line_to(1700, 600); ctx.line_to(1700, -400); ctx.line_to(-600, -400); ctx.close_path(); setc(ctx, '#3a2840'); ctx.fill()
    for k in range(-4, 12):
        ctx.move_to(540, -100); ctx.line_to(k * 150, 1250); setc(ctx, '#4a3450'); ctx.set_line_width(14); ctx.stroke()
    # round window + beam
    circ(ctx, 540, 380, 110); ctx.set_source(lgrad(0, 270, 0, 490, [(0, '#ff9ad5'), (1, '#ffd9a0')])); ctx.fill_preserve(); setc(ctx, '#6a4a2a'); ctx.set_line_width(16); ctx.stroke()
    ctx.move_to(540, 270); ctx.line_to(540, 490); ctx.move_to(430, 380); ctx.line_to(650, 380); setc(ctx, '#6a4a2a'); ctx.set_line_width(8); ctx.stroke()
    ctx.move_to(450, 400); ctx.line_to(630, 400); ctx.line_to(900, 1500); ctx.line_to(250, 1500); ctx.close_path()
    ctx.set_source(lgrad(0, 400, 0, 1500, [(0, '#fff1c4', 0.35), (1, '#fff1c4', 0)])); ctx.fill()
    rnd = random.Random(9)
    for k in range(30):
        px = rnd.uniform(300, 800); py = (rnd.uniform(400, 1400) + t * 20) % 1000 + 400
        circ(ctx, px + (py - 400) * 0.1, py, rnd.uniform(2, 4)); setc(ctx, '#fff6c8', 0.6); ctx.fill()
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#6a4a3a'); ctx.fill()
    for k in range(-6, 20): ctx.move_to(-600, 1270 + k * 60); ctx.line_to(1700, 1270 + k * 60); setc(ctx, '#5a3a2a'); ctx.set_line_width(4); ctx.stroke()
    for bx, by, bw, bh in ((-40, 1050, 260, 200), (60, 900, 200, 150), (850, 1080, 260, 180), (900, 940, 180, 140)):
        rrect(ctx, bx, by, bw, bh, 6); fs(ctx, '#c49a62', 5); ctx.move_to(bx, by + bh / 2); ctx.line_to(bx + bw, by + bh / 2); setc(ctx, '#e8d9a8'); ctx.set_line_width(10); ctx.stroke()

# ---------------------------------------------------------------- scenes
def sc_office(ctx, t):
    z = 1.0 + 0.01 * t
    ctx.save(); cam(ctx, 540, 1000, z)
    bg_office(ctx, t)
    clap = 0.6 + 0.6 * abs(math.sin(t * 9))
    char(ctx, 'cal2', 180, 1330, 0.92, P(face=1, eyes='happy', smile=0.8, fa=(1.1, clap), ba=(0.7, clap + 0.3)), t)
    char(ctx, 'cal1', 760, 1340, 0.98, P(face=-1, eyes='happy' if t < 5.6 else 'normal', smile=0.7, mouth=mouth('cal1', t),
                                        arms='give' if 3.2 < t < 5.0 else ('explain' if t > 5.6 else 'down')), t)
    r = char(ctx, 'dede', 450, 1340, 1.0, P(face=1, smile=0.6 + 0.2 * seg(t, 4.5, 5), eyes='happy' if t > 4.6 else 'normal',
                                          blush=0.5 * seg(t, 4.6, 5.2), fa=(0.9, 0.9) if t > 4.6 else (0.12, 0.25), ba=(0.6, 1.4) if t > 4.6 else (-0.1, 0.15)), t)
    hx, hy = r['hand']
    px, py = (lerp(700, hx + 10, seg(t, 3.6, 4.6)), lerp(1000, hy - 30, seg(t, 3.6, 4.6))) if t > 3.2 else (None, None)
    if px:
        glow(ctx, px, py, 120, '#ffe27a', 0.5)
        rrect(ctx, px - 70, py - 90, 140, 180, 10); fs(ctx, '#5a3018', 5); rrect(ctx, px - 50, py - 70, 100, 140, 6); fs(ctx, '#f2c14e', 3)
        text_c(ctx, '40', px, py + 20, 54, '#7a5a1a', INK, 0)
    rnd = random.Random(int(t * 12))
    for k in range(40):
        r_ = random.Random(k); x = r_.uniform(0, 1080); y = (r_.uniform(0, 1300) + t * 160) % 1500 - 100
        ctx.save(); ctx.translate(x, y); ctx.rotate(t * 3 + k); ctx.rectangle(-8, -4, 16, 8)
        setc(ctx, ['#ff5e7e', '#ffd23f', '#7fe7ff', '#9b5cff', '#7bd389'][k % 5]); ctx.fill(); ctx.restore()
    ctx.restore()

def sc_morning(ctx, t):
    if t < 9.5:      # alarm clock
        ctx.rectangle(0, 0, W, H); ctx.set_source(lgrad(0, 0, 0, H, [(0, '#3a2a6a'), (1, '#ff9ad5')])); ctx.fill()
        B.speed_lines(ctx, t, 0.35, 540, 820, '#ffffff')
        sh = 10 * math.sin(t * 60)
        ctx.save(); ctx.translate(540 + sh, 820); ctx.scale(2.6, 2.6)
        for sg in (-1, 1): circ(ctx, sg * 42, -58, 22); fs(ctx, '#e8507a', 4)
        icon(ctx, 'clock', 0, 0, 1.2, 0.0)
        ctx.restore()
        text_c(ctx, '06:00', 540, 1150, 110, '#fff27a', INK, 16)
        B.sfx_text(ctx, 'ZIRRR!', 540, 420, 120, -0.08, 1.0)
        return
    ctx.save(); cam(ctx, 540, 900, 1.45)
    bg_home(ctx, t)
    p = P(face=1, eyes='normal', smile=0.2)
    if t < 11.5:
        p['fa'] = (0.4, 2.6); p['ba'] = (-0.1, 0.15)
    elif t < 13.0:
        p['fa'] = (0.45, 2.2); p['ba'] = (0.45, 2.1)
    else:
        p['fa'] = (0.55, 1.9); p['ba'] = (0.2, 2.0)
    r = char(ctx, 'dede', 470, 1330, 1.0, p, t)
    hx, hy = r['head']
    if t < 11.5:
        for k in range(6):
            circ(ctx, hx + 10 + k * 14, hy + 150 + (k % 2) * 12, 18); setc(ctx, '#ffffff'); ctx.fill()
        ctx.move_to(r['hand'][0], r['hand'][1]); ctx.line_to(r['hand'][0] + 30, r['hand'][1] - 50); setc(ctx, '#7fd3ff'); ctx.set_line_width(14); ctx.stroke()
    if t >= 13.0:
        ax, ay = r['hand']; ell(ctx, ax, ay - 5, 24, 20); fs(ctx, '#f2c14e', 4); circ(ctx, ax, ay - 5, 12); fs(ctx, '#ffffff', 2)
        sparkle(ctx, ax + 30, ay - 30, 16)
    ctx.restore()

def sc_door(ctx, t):
    ctx.save(); cam(ctx, 600, 950, 1.15)
    bg_door(ctx, t)
    stop = t > 16.2
    p = P(face=1, smile=0.3, fa=(1.25, -0.2) if t > 15.3 else (0.12, 0.25), eyes='normal')
    x = kf(t, [(14.94, 330), (15.9, 480)])
    p['walk'] = t * 9 if 14.94 < t < 15.9 else None
    if stop: p['eyes'] = 'wide'; p['smile'] = -0.2; p['sweat'] = 0.6; p['fa'] = (1.1, -0.1)
    if t > 17.4: p['eyes'] = 'normal'; p['brow'] = 0.8; p['smile'] = -0.4; p['fa'] = (0.12, 0.25); p['gloom'] = 0.6; p['tilt'] = 0.15
    if t >= 19.0:
        p['fa'] = (0.6, 2.4); p['ba'] = (-0.4, 2.4)
    char(ctx, 'dede', x, 1330, 1.0, p, t)
    ctx.restore()
    if 16.2 < t < 17.6: B.sfx_text(ctx, '!', 820, 520, 180, 0, win(t, 16.2, 17.6, 0.1), '#ffffff', '#e8102e')
    if 17.6 < t < 19.0: text_c(ctx, '...', 820, 560, 140, '#ffffff', INK, 14, win(t, 17.6, 19.0, 0.2))

def sc_living(ctx, t):
    if t < 24.4: fx, z = 560, 1.05
    else: fx, z = 540, 1.0
    ctx.save(); cam(ctx, fx, 960, z)
    bg_home(ctx, t)
    armchair(ctx, 360, 1330, 1.0)
    p = P(face=1, eyes='normal', smile=0.2, fa=(0.5, 1.4), ba=(-0.2, 1.2))
    if t >= 24.4: p['eyes'] = 'normal'; p['brow'] = 0.7; p['smile'] = -0.2; p['look'] = -1 if t < 32 else 1
    if t >= 32.0: p['sweat'] = 0.8
    ctx.save(); ctx.rectangle(-2000, -2000, 6000, 1290 - 60 + 2000); ctx.clip()
    r = char(ctx, 'dede', 330, 1330 + 150, 1.0, p, t)
    ctx.restore()
    ell(ctx, 380, 1270, 120, 46); fs(ctx, B.STY['dede']['robe2'], 5)
    armchair(ctx, 360, 1330, 1.0, front=True)
    if t >= 21.24:
        ex = kf(t, [(21.24, 1200), (22.6, 760)])
        q = P(face=-1, walk=t * 9 if 21.24 < t < 22.6 else None, mouth=mouth('es', t), eyes='normal', smile=0.6, fa=(1.0, 0.6))
        er = char(ctx, 'es', ex, 1340, 0.96, q, t)
        if t < 23.2:
            tea(ctx, er['hand'][0] - 10, er['hand'][1] - 6, 0.9, t)
    if t >= 23.2: tea(ctx, 560, 1240, 0.9, t)
    if t >= 23.2:
        rrect(ctx, 470, 1250, 200, 20, 6); fs(ctx, '#8b5a2b', 4)
    hx, hy = r['head']
    if t >= 25.62:
        items = [('pill', 25.8), ('bill', 27.6), ('cloud', 29.2), ('school', 30.6)]
        for k, (kind, t0) in enumerate(items):
            if t < t0: continue
            a = seg(t, t0, t0 + 0.35) * (1 - seg(t, 33.4, 33.9))
            bx, by = [(230, 560), (530, 470), (830, 560), (680, 760)][k]
            def inner(kind=kind, bx=bx, by=by):
                icon(ctx, kind, bx, by, 0.95, t)
                if kind in ('pill', 'school'): icon(ctx, 'clock', bx + 70, by + 50, 0.4, t)
            thought(ctx, bx, by, 115, 95, (hx + 40, hy - 10), inner, a)
        if 32.0 <= t < 34.0:
            a = seg(t, 32.0, 32.3)
            def inner2():
                icon(ctx, 'q', 330, 760, 1.0, t)
            thought(ctx, 330, 720, 110, 95, (hx, hy - 30), inner2, a)
    ctx.restore()

def sc_roles(ctx, t):
    ctx.rectangle(0, 0, W, H); ctx.set_source(lgrad(0, 0, 0, H, [(0, '#2a1a5a'), (0.6, '#8a2a7a'), (1, '#ff9a6b')])); ctx.fill()
    B.stars(ctx, t, 700, 30)
    if t < 40.5:
        rot = 0.15 * (t - 34)
        roles = [('mom', 34.3), ('ring', 35.7), ('kid', 37.0), ('case', 38.5)]
        for k, (kind, t0) in enumerate(roles):
            if t < t0: continue
            a = seg(t, t0, t0 + 0.3)
            ang = -PI / 2 + k * PI / 2 + rot
            x, y = 540 + 330 * math.cos(ang), 860 + 330 * math.sin(ang)
            glow(ctx, x, y, 120, '#ffe27a', 0.4 * a)
            circ(ctx, x, y, 92 * a); fs(ctx, '#fffdf5', 7)
            icon(ctx, kind, x, y, 1.0 * a, t)
            sparkle(ctx, x + 70, y - 70, 18 * a)
        char(ctx, 'dede', 540, 1180, 0.85, P(face=1, smile=0.5, eyes='happy', arms='hips'), t)
        return
    # herkese yetişmiş, kendine geç kalmış: running, clock spinning
    B.speed_lines(ctx, t, 0.4, 540, 700, '#ffffff')
    ctx.save(); ctx.translate(540, 600); ctx.scale(3.0, 3.0); icon(ctx, 'clock', 0, 0, 1.0, t * 6); ctx.restore()
    char(ctx, 'dede', 400, 1330, 0.9, P(face=1, walk=t * 16, sweat=1, eyes='wide', brow=0.8, smile=-0.3, fa=(1.4, -0.2), ba=(-0.8, 0.4)), t)
    if t > 41.6:
        tinted(ctx, lambda: char(ctx, 'dede', 900, 1330, 0.6, P(face=-1, eyes='normal', smile=0.1, arms='down'), t), '#ffffff', 0.55, 0.6 * seg(t, 41.6, 42.2))

def sc_attic(ctx, t):
    if t < 48.1: fx, fy, z = 540, 1000, 1.0
    else: fx, fy, z = 540, 900, 1.0
    ctx.save(); cam(ctx, fx, fy, z)
    bg_attic(ctx, t)
    if t < 48.1:
        p = P(face=1, eyes='wide', smile=0.5, fa=(0.9, 0.9), ba=(0.6, 1.4), bend=0.2 * (1 - seg(t, 44, 45)))
        r = char(ctx, 'dede', 420, 1330, 1.0, p, t)
        baglama(ctx, 760, 1260, 0.75, 0.25)
        hx, hy = r['hand']
        a = seg(t, 45.5, 46.2)
        notebook(ctx, lerp(300, hx + 10, a), lerp(1290, hy, a), 0.5, 0)
        glow(ctx, 760, 1100, 200, '#ffe27a', 0.35 * seg(t, 43.5, 44.5))
        ctx.restore(); return
    ctx.restore()
    ctx.save(); ctx.rectangle(0, 0, W, H); setc(ctx, '#000', 0.35); ctx.fill(); ctx.restore()
    notebook(ctx, 540, 820, 1.5, 1)
    font(ctx, 46, italic=True)
    lines = ['Evladım,', 'ekmeğini', 'kazanırken', 'kendini', 'kaybetme.']
    a = seg(t, 50.6, 52.0)
    for k, ln in enumerate(lines):
        aa = clamp(a * 5 - k)
        x = 230 if k < 3 else 580
        y = 640 + (k % 3) * 90 + (0 if k < 3 else 60)
        ctx.move_to(x, y); ctx.text_path(ln); setc(ctx, '#3a2a6a', aa); ctx.fill()
    ctx.move_to(250, 560); ctx.line_to(470, 560); setc(ctx, '#b3263e', 0.6); ctx.set_line_width(3); ctx.stroke()
    circ(ctx, 820, 990, 30); setc(ctx, '#ff5e7e', 0.35 * a); ctx.fill()

def sc_play(ctx, t):
    if t < 62.42: fx, z = 470, 1.25
    else: fx, z = 600, 1.0
    ctx.save(); cam(ctx, fx, 960 if t < 62.42 else 980, z)
    bg_home(ctx, t, evening=True)
    if t >= 62.42:
        ex = 870
        q = P(face=-1, eyes='happy' if t > 66 else 'normal', smile=0.7, mouth=mouth('es', t), arms='chest', blush=0.5)
        char(ctx, 'es', ex, 1340, 0.96, q, t)
    armchair(ctx, 360, 1330, 1.0)
    strum = 0.2 * math.sin(t * 10)
    p = P(face=1, eyes='closed' if t > 58.5 else 'normal', smile=0.35 if t < 58.5 else -0.1, mouth=0.35 * abs(math.sin(t * 5)) if t > 58.5 else 0,
          fa=(0.9, 1.0 + strum), ba=(0.9, 1.6), brow=0.6 if t > 58.5 else 0)
    ctx.save(); ctx.rectangle(-2000, -2000, 6000, 1230 + 2000); ctx.clip()
    r = char(ctx, 'dede', 330, 1480, 1.0, p, t)
    ctx.restore()
    ell(ctx, 380, 1270, 120, 46); fs(ctx, B.STY['dede']['robe2'], 5)
    baglama(ctx, 390, 1130, 0.62, -0.9)
    armchair(ctx, 360, 1330, 1.0, front=True)
    hx, hy = r['head']
    if t > 58.5:
        for k in range(2):
            ph = (t * 0.7 + k * 0.5) % 1
            x = hx + 32 + k * 6; y = hy + 85 + ph * 70
            ctx.move_to(x, y - 12); ctx.curve_to(x + 9, y, x + 9, y + 8, x, y + 8); ctx.curve_to(x - 9, y + 8, x - 9, y, x, y - 12)
            setc(ctx, '#9fe0ff', 1 - ph); ctx.fill()
    for k in range(5):
        ph = (t * 0.4 + k / 5) % 1
        x = 520 + k * 60 + 40 * math.sin(t * 2 + k); y = 1050 - ph * 600
        col = ['#ff5e7e', '#9b5cff', '#ffd23f'][k % 3]; al = 1 - ph
        heads = [(0, 0)] if k % 2 else [(0, 0), (44, -12)]
        for hx_, hy_ in heads:
            ctx.save(); ctx.translate(x + hx_, y + hy_); ctx.rotate(-0.4); ell(ctx, 0, 0, 16, 11); ctx.restore()
            setc(ctx, col, al); ctx.fill_preserve(); setc(ctx, INK, al); ctx.set_line_width(3); ctx.stroke()
            ctx.move_to(x + hx_ + 14, y + hy_ - 4); ctx.line_to(x + hx_ + 14, y + hy_ - 70); setc(ctx, INK, al); ctx.set_line_width(5); ctx.stroke()
        if k % 2:
            ctx.move_to(x + 14, y - 70); ctx.curve_to(x + 40, y - 56, x + 44, y - 40, x + 34, y - 26); setc(ctx, INK, al); ctx.set_line_width(5); ctx.stroke()
        else:
            ctx.move_to(x + 14, y - 70); ctx.line_to(x + 58, y - 82); setc(ctx, INK, al); ctx.set_line_width(10); ctx.stroke()
    ctx.restore()

def sc_age(ctx, t):
    ctx.save(); cam(ctx, 540, 980, 1.05)
    bg_home(ctx, t, evening=True)
    char(ctx, 'torun', 760, 1340, 0.62, P(face=-1, mouth=mouth('torun', t), eyes='wide', smile=0.5, arms='pointup' if t < 72 else 'down'), t)
    char(ctx, 'dede', 420, 1340, 1.0, P(face=1, mouth=mouth('dede', t), eyes='happy' if t > 72.2 else 'normal', smile=0.8, arms='explain' if t > 72.2 else 'down'), t)
    ctx.restore()
    if t > 72.6:
        a = seg(t, 72.6, 73.0)
        cx_, cy_ = 300, 560
        rrect(ctx, cx_ - 160, cy_ - 100, 320, 200, 18); fs(ctx, '#e9f1f7', 6, a)
        rrect(ctx, cx_ - 140, cy_ - 70, 90, 110, 8); setc(ctx, '#9ab8d8', a); ctx.fill()
        for k in range(3): ctx.move_to(cx_ - 30, cy_ - 50 + k * 34); ctx.line_to(cx_ + 130, cy_ - 50 + k * 34); setc(ctx, '#9a9aa2', a); ctx.set_line_width(8); ctx.stroke()
        text_c(ctx, '63', cx_, cy_ + 175, 110, '#ffffff', INK, 14, a)
    if t > 74.6 and seg(t, 74.6, 75.1) > 0.01:
        a = seg(t, 74.6, 75.1)
        glow(ctx, 790, 560, 220, '#ffe27a', 0.6 * a)
        ctx.save(); ctx.translate(790, 600); ctx.scale(a, a)
        ctx.new_path(); ctx.arc(0, 0, 120, PI, 2 * PI); ctx.close_path(); ctx.set_source(lgrad(0, -120, 0, 0, [(0, '#fff27a'), (1, '#ff7a3a')])); ctx.fill()
        for k in range(9):
            an = PI + k * PI / 8; ctx.move_to(140 * math.cos(an), 140 * math.sin(an)); ctx.line_to(190 * math.cos(an), 190 * math.sin(an))
        setc(ctx, '#ffd23f'); ctx.set_line_width(10); ctx.stroke()
        ctx.move_to(0, 0); ctx.curve_to(0, -40, -10, -60, -40, -80); setc(ctx, '#3f9b3a'); ctx.set_line_width(8); ctx.stroke()
        ell(ctx, -50, -84, 24, 12); setc(ctx, '#5cc46a'); ctx.fill(); ell(ctx, 16, -70, 22, 11); setc(ctx, '#5cc46a'); ctx.fill()
        ctx.restore()
        text_c(ctx, 'YENİ!', 790, 775, 90, '#fff27a', INK, 14, a)

def sc_lesson(ctx, t):
    ctx.rectangle(0, 0, W, H); ctx.set_source(lgrad(0, 0, 0, H, [(0, '#1d1240'), (0.6, '#5a2a7a'), (1, '#e8507a')])); ctx.fill()
    B.stars(ctx, t, 900, 40)
    if t < 85.1:
        cx_, cy_ = 540, 1000
        circ(ctx, cx_, cy_, 330); setc(ctx, '#2a1650'); ctx.fill_preserve(); setc(ctx, '#ffd23f'); ctx.set_line_width(16); ctx.stroke()
        for k in range(16):
            a = k / 16 * 2 * PI + t * 2
            ctx.move_to(cx_, cy_); ctx.line_to(cx_ + 320 * math.cos(a), cy_ + 320 * math.sin(a)); setc(ctx, '#ffd23f', 0.4); ctx.set_line_width(5); ctx.stroke()
        char(ctx, 'G', 540, 1330, 0.9, P(face=1, walk=t * 16, sweat=1, eyes='wide', brow=0.6, fa=(1.2, -0.2), ba=(-0.8, 0.4)), t)
        for k, kind in enumerate(('book', 'laptop', 'coin', 'kid', 'case')):
            a = t * 1.2 + k * 2 * PI / 5
            x, y = cx_ + 420 * math.cos(a), 760 + 200 * math.sin(a)
            circ(ctx, x, y, 80); fs(ctx, '#fffdf5', 5); icon(ctx, kind, x, y, 0.8, t)
        return
    B.speed_lines(ctx, t, 0.5, 540, 900, '#ffffff')
    if t < 89.5:
        char(ctx, 'G', 540, 1330, 1.0, P(face=1, eyes='wide', sweat=1, smile=-0.3, brow=0.8, arms='down', tremble=0.2), t)
        icon(ctx, 'q', 540, 420, 2.0 * seg(t, 85.4, 85.8), t)
        return
    # final question
    B.retro_sun(ctx, 540, 1150, 330)
    a1 = seg(t, 90.8, 91.3); a2 = seg(t, 91.9, 92.4)
    text_c(ctx, 'Doğdun, tamam.', 540, 520, 84, '#ffffff', INK, 14, a1, italic=True)
    text_c(ctx, 'Peki ne zaman', 540, 700, 100, '#fff27a', INK, 16, a2, italic=True)
    text_c(ctx, 'kendin oldun?', 540, 830, 100, '#fff27a', INK, 16, a2, italic=True)

def sc_end(ctx, t):
    ctx.rectangle(0, 0, W, H); ctx.set_source(lgrad(0, 0, 0, H, [(0, '#1d1240'), (0.6, '#5a2a7a'), (1, '#e8507a')])); ctx.fill()
    B.stars(ctx, t, 900, 40); B.retro_sun(ctx, 540, 1150, 330)
    a = seg(t, 93.3, 93.9)
    title(ctx, a, 600)
    text_c(ctx, '@animasyonhikayeai', 540, 990, 48, '#ffffff', INK, 10, a)

def title(ctx, a, y):
    if a <= 0: return
    for txt, yy, size in (('YENİ', y, 150), ('DOĞDUM', y + 175, 170)):
        font(ctx, size, italic=True, black=True); e = ctx.text_extents(txt); x = 540 - e[4] / 2
        ctx.move_to(x + 10, yy + 10); ctx.text_path(txt); setc(ctx, '#140a24', 0.7 * a); ctx.fill()
        ctx.move_to(x, yy); ctx.text_path(txt); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        setc(ctx, INK, a); ctx.set_line_width(24); ctx.stroke_preserve()
        setc(ctx, '#e8102e', a); ctx.set_line_width(10); ctx.stroke_preserve()
        ctx.set_source(lgrad(0, yy - size, 0, yy, [(0, '#ffffff', a), (0.55, '#fff27a', a), (1, '#ffb347', a)])); ctx.fill()

# ---------------------------------------------------------------- subtitles
TEXTS = [
    "Bir adam 40 yıl çalıştıktan sonra emekli olmuş.",
    "Son iş gününde arkadaşları ona bir plaket vermiş ve “Artık dinlenmeyi hak ettin” demiş.",
    "Ertesi sabah adam her zamanki gibi erkenden kalkmış, tıraşını olmuş, gömleğini giymiş, saatini takmış.",
    "Tam kapıdan çıkacakken durmuş, çünkü artık gidecek bir işi yokmuş.",
    "Ceketini çıkarıp salona oturmuş.",
    "Karısı çayını getirip “Bugün ne yapmak istersin?” diye sormuş.",
    "Adam cevap verememiş.",
    "Karısının ilaç saatlerini, oğlunun borcunu, kızının derdini, torununun okul saatini biliyormuş ama kendisinin ne istediğini bilmiyormuş.",
    "Çünkü bir ömür boyu iyi bir evlat, iyi bir eş, iyi bir baba, iyi bir çalışan olmuş.",
    "Herkese yetişmiş, bir tek kendine geç kalmış.",
    "Bir gün çatı katında eski bağlamasını ve annesinden kalan bir defter bulmuş.",
    "Defterin ilk sayfasında şu yazıyormuş:",
    "“Evladım, ekmeğini kazanırken kendini kaybetme.”",
    "Adam bağlamayı eline almış. Parmakları zorlanmış, sesi biraz çatallı çıkmış ama ilk söylediği türküde ağlamaya başlamış.",
    "Karısı kapıdan onu izleyip şöyle demiş:",
    "“Her gün eve geldiğini gördüm ama bugün ilk defa kendine geldiğini gördüm.”",
    "Torunu bir gün “Dede, kaç yaşındasın?” diye sormuş.",
    "Adam gülümsemiş ve “Nüfusa göre 63, ama kendime göre daha yeni doğdum” demiş.",
    "Sözün özü:",
    "Doğum tarihimiz var diye yaşadığımızı zannediyoruz.",
    "Okuyoruz, çalışıyoruz, borç ödüyoruz, herkese yetişiyoruz.",
    "Ama biri çıkıp “Sen ne istiyorsun be adam?” dediğinde cevap veremiyoruz.",
    "Şimdi sana soruyorum:",
    "Doğdun, tamam.",
    "Peki ne zaman kendin oldun?",
]
_tr = json.load(open(os.path.join(HERE, 'transcript.json')))
assert len(_tr) == len(TEXTS), (len(_tr), len(TEXTS))
def build_cues():
    cues = []
    for s, text in zip(_tr, TEXTS):
        words = text.split(); chunks = []; cur = []
        for wd in words:
            cand = ' '.join(cur + [wd])
            if cur and len(cand) > 56: chunks.append(' '.join(cur)); cur = [wd]
            else:
                cur.append(wd)
                if len(cand) > 26 and wd[-1] in '.,?!:”': chunks.append(' '.join(cur)); cur = []
        if cur: chunks.append(' '.join(cur))
        tot = sum(len(c) for c in chunks); t0 = s['start']; d = s['end'] - s['start']
        for c in chunks:
            dd = d * len(c) / tot; cues.append((t0, t0 + dd, c)); t0 += dd
    return cues
CUES = build_cues()
def draw_subs(ctx, t):
    if 89.4 < t: return            # final question is shown as big on-screen text
    txt = None
    for i, (a, b, c) in enumerate(CUES):
        nxt = CUES[i + 1][0] if i + 1 < len(CUES) else DUR
        if a <= t < min(b + 0.35, nxt): txt = c
    if not txt: return
    font(ctx, 54)
    lines = B.wrap(ctx, txt, 900); lh = 70
    y0 = 1500 - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        e = ctx.text_extents(ln); ctx.move_to(540 - e[4] / 2, y0 + i * lh + 18); ctx.text_path(ln)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    setc(ctx, '#111111'); ctx.set_line_width(11); ctx.stroke_preserve()
    setc(ctx, '#ffffff'); ctx.fill()

# ---------------------------------------------------------------- render
CUTS = (7.96, 9.5, 14.94, 19.0, 34.04, 43.3, 54.54, 69.4, 77.6, 93.2)
def render(ctx, t):
    setc(ctx, '#000'); ctx.paint()
    if t < 7.96: sc_office(ctx, t)
    elif t < 14.94: sc_morning(ctx, t)
    elif t < 19.0: sc_door(ctx, t)
    elif t < 34.04: sc_living(ctx, t)
    elif t < 43.3: sc_roles(ctx, t)
    elif t < 54.54: sc_attic(ctx, t)
    elif t < 69.4: sc_play(ctx, t)
    elif t < 77.6: sc_age(ctx, t)
    elif t < 93.2: sc_lesson(ctx, t)
    else: sc_end(ctx, t)

def grade(ctx):
    setc(ctx, '#ff7ab8', 0.07); ctx.paint()
    g = cairo.RadialGradient(540, 960, 500, 540, 960, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.1, 0.02, 0.15, 0.35); ctx.set_source(g); ctx.paint()

def frame(surf, t):
    ta = math.floor(t * 12) / 12
    ctx = cairo.Context(surf); render(ctx, ta); grade(ctx)
    a = 0
    for T in CUTS: a = max(a, 1 - abs(t - T) / 0.2)
    a = max(a, 1 - t / 0.4, (t - (DUR - 0.6)) / 0.6)
    if a > 0: setc(ctx, '#000', clamp(a)); ctx.paint()
    if t < 3.0: title(ctx, seg(t, 0.2, 0.6) * (1 - seg(t, 2.5, 3.0)), 560)
    draw_subs(ctx, t)
    surf.flush(); return bytes(surf.get_data())

if __name__ == '__main__':
    import subprocess
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if sys.argv[1] == 'png':
        for ts in sys.argv[3:]:
            frame(surf, float(ts)); surf.write_to_png(os.path.join(sys.argv[2], f'f_{float(ts):07.2f}.png'))
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fr in range(f0, f1): ff.stdin.write(frame(surf, fr / FPS))
        ff.stdin.close(); ff.wait()
