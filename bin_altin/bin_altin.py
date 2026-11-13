import os, sys, math, json, random, importlib.util
import cairo, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('base', os.path.join(HERE, 'base.py'))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)
from math import pi as PI
W, H, FPS = 1080, 1920, 24
DUR = 144.2
clamp, sm, lerp, seg, win, kf, moving = B.clamp, B.sm, B.lerp, B.seg, B.win, B.kf, B.moving
setc, fs, ell, circ, rrect, lgrad, glow, sparkle, font, mix = B.setc, B.fs, B.ell, B.circ, B.rrect, B.lgrad, B.glow, B.sparkle, B.font, B.mix
INK = B.INK
FY = 1330

# ---------------------------------------------------------------- speakers / mouth
SPEAK = [(3.76, 6.8, 'genc'), (10.3, 14.96, 'A'), (34.98, 37.74, 'sahip'), (62.9, 64.9, 'genc2'), (67.28, 82.08, 'gelin')]
def mouth(n, t):
    for a, b, who in SPEAK:
        if a <= t < b and who == n:
            return B.env(t) * (0.5 + 0.5 * abs(math.sin(t * 16)))
    return 0.0

def P(**kw):
    p = B.pose(); p.update(kw); return p

def char(ctx, n, x, y, s, p, t):
    return B.draw_char(ctx, n, x, y, s, p, t)

def sit(ctx, n, x, y, s, p, t):
    st = B.STY[n]; f = p['face']
    ctx.save(); ctx.rectangle(-2000, -2000, 6000, y - 70 * s + 2000); ctx.clip()
    r = char(ctx, n, x, y + 165 * s, s, p, t)
    ctx.restore()
    ell(ctx, x + f * 10 * s, y - 45 * s, 120 * s, 50 * s); fs(ctx, st['robe'], 5)
    ell(ctx, x - f * 95 * s, y - 14 * s, 34 * s, 14 * s); fs(ctx, '#3a2a28', 4)
    return r

def tinted(ctx, fn, col, amt, alpha=1.0):
    ctx.push_group(); fn()
    ctx.set_operator(cairo.OPERATOR_ATOP); setc(ctx, col, amt); ctx.paint(); ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)

# ---------------------------------------------------------------- props
def coin(ctx, x, y, r, spin=1.0, a=1.0):
    rx = max(r * abs(spin), 2)
    ell(ctx, x, y, rx, r); setc(ctx, '#ffd23f', a); ctx.fill_preserve(); setc(ctx, '#9a6a12', a); ctx.set_line_width(3); ctx.stroke()
    ell(ctx, x, y, rx * 0.62, r * 0.62); setc(ctx, '#e0a92a', a); ctx.set_line_width(2.5); ctx.stroke()
    ell(ctx, x - rx * 0.3, y - r * 0.35, rx * 0.18, r * 0.18); setc(ctx, '#fff6c8', a); ctx.fill()

def bag(ctx, x, y, s=1.0, opened=0.0, shine=0.0, t=0.0):
    if shine > 0: glow(ctx, x, y - 40 * s, 170 * s, '#ffe27a', 0.6 * shine)
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.move_to(-30, -80); ctx.curve_to(-95, -60, -100, 30, -60, 48); ctx.line_to(60, 48)
    ctx.curve_to(100, 30, 95, -60, 30, -80); ctx.close_path(); fs(ctx, '#9c6b3d', 5)
    ell(ctx, -30, 0, 20, 30); setc(ctx, '#ffffff', 0.12); ctx.fill()
    if opened > 0:
        ell(ctx, 0, -84, 42, 14 + 6 * opened); fs(ctx, '#5a3a20', 4)
        for k in range(6):
            r = random.Random(k)
            coin(ctx, r.uniform(-30, 30), -86 - r.uniform(0, 26) * opened, 13)
        for k in range(3):
            sparkle(ctx, -40 + k * 40, -130 - 10 * math.sin(t * 5 + k), 14 * opened)
    else:
        ctx.move_to(-34, -80); ctx.curve_to(-20, -100, 20, -100, 34, -80); setc(ctx, '#9c6b3d'); ctx.fill_preserve(); setc(ctx, INK); ctx.set_line_width(4); ctx.stroke()
        ctx.move_to(-36, -76); ctx.line_to(36, -76); setc(ctx, '#e8d9a8'); ctx.set_line_width(8); ctx.stroke()
    ctx.restore()

def kaaba(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    glow(ctx, 0, -200, 520, '#ffe9b0', 0.35)
    # side face
    ctx.move_to(170, 0); ctx.line_to(300, -50); ctx.line_to(300, -400); ctx.line_to(170, -360); ctx.close_path(); fs(ctx, '#1d1a22', 5)
    ctx.move_to(-230, -360); ctx.line_to(-100, -410); ctx.line_to(300, -400); ctx.line_to(170, -360); ctx.close_path(); fs(ctx, '#2a2630', 5)
    ctx.rectangle(-230, -360, 400, 360); fs(ctx, '#121016', 5)
    # gold band
    ctx.rectangle(-230, -290, 400, 34); setc(ctx, '#d9a63a'); ctx.fill()
    ctx.move_to(170, -290); ctx.line_to(300, -333); ctx.line_to(300, -299); ctx.line_to(170, -256); ctx.close_path(); setc(ctx, '#b88a2a'); ctx.fill()
    for k in range(16):
        ctx.move_to(-222 + k * 25, -282); ctx.curve_to(-214 + k * 25, -270, -206 + k * 25, -270, -200 + k * 25, -282)
        setc(ctx, '#7a5a1a'); ctx.set_line_width(2.5); ctx.stroke()
    # door
    ctx.rectangle(60, -210, 70, 150); fs(ctx, '#d9a63a', 3)
    ctx.rectangle(70, -200, 50, 130); setc(ctx, '#b88a2a'); ctx.fill()
    ctx.restore()

def mule(ctx, x, y, s, f, t, walking):
    ctx.save(); ctx.translate(x, y); ctx.scale(s * f, s)
    ph = t * 8 if walking else 0
    for k, lx in enumerate((-90, -60, 60, 90)):
        sw = 14 * math.sin(ph + k * PI / 2) if walking else 0
        ctx.save(); ctx.translate(lx, -150); ctx.rotate(sw * 0.02)
        rrect(ctx, -12, 0, 24, 150, 8); fs(ctx, '#8a7a6a', 4); ctx.rectangle(-12, 135, 24, 15); setc(ctx, '#3a2a20'); ctx.fill()
        ctx.restore()
    ell(ctx, 0, -190, 145, 72); fs(ctx, '#9a8a7a', 5)
    ctx.move_to(-140, -200); ctx.curve_to(-175, -190, -180, -150, -190, -120); setc(ctx, INK); ctx.set_line_width(6); ctx.stroke()
    ctx.move_to(110, -230); ctx.line_to(160, -320); ctx.line_to(205, -300); ctx.line_to(150, -200); ctx.close_path(); fs(ctx, '#9a8a7a', 5)
    ell(ctx, 200, -300, 52, 34); fs(ctx, '#9a8a7a', 5); ell(ctx, 238, -292, 18, 22); fs(ctx, '#c8b8a8', 4)
    for ex in (170, 190):
        ctx.move_to(ex, -320); ctx.line_to(ex - 16, -400); ctx.line_to(ex + 10, -330); ctx.close_path(); fs(ctx, '#9a8a7a', 4)
    circ(ctx, 205, -312, 6); setc(ctx, INK); ctx.fill()
    # saddle + chests
    rrect(ctx, -80, -275, 160, 40, 10); fs(ctx, '#b3263e', 4)
    for cx_, col in ((-50, '#8b4513'), (40, '#a0522d')):
        rrect(ctx, cx_ - 45, -360, 90, 85, 10); fs(ctx, col, 4)
        ctx.rectangle(cx_ - 45, -330, 90, 10); setc(ctx, '#f2c14e'); ctx.fill()
        circ(ctx, cx_, -320, 8); setc(ctx, '#f2c14e'); ctx.fill()
    ctx.restore()

def lanterns(ctx, t, y0=360, on=1.0):
    cols = ['#ff5e7e', '#ffd23f', '#7fe7ff', '#9b5cff', '#7bd389']
    ctx.move_to(-100, y0); ctx.curve_to(300, y0 + 140, 780, y0 + 140, 1180, y0)
    setc(ctx, '#3a2a20'); ctx.set_line_width(4); ctx.stroke()
    for k in range(12):
        u = (k + 0.5) / 12; x = lerp(-100, 1180, u); yy = y0 + 140 * 4 * u * (1 - u) * 0.75 + 16
        a = clamp(on * 12 - k)
        glow(ctx, x, yy + 20, 60, cols[k % 5], 0.6 * a)
        ctx.move_to(x, yy - 6); ctx.line_to(x, yy + 6); setc(ctx, '#3a2a20'); ctx.set_line_width(3); ctx.stroke()
        ell(ctx, x, yy + 24, 16, 22); fs(ctx, mix('#6a5a50', cols[k % 5], a), 3)

def bubble(ctx, bx, by, rx, ry, tail, inner):
    for fx, rr in ((0.3, 12), (0.55, 20)):
        circ(ctx, lerp(tail[0], bx, fx), lerp(tail[1], by + ry, fx), rr); fs(ctx, '#fffdf5', 4)
    ctx.new_path()
    for k in range(12):
        a = k / 12 * 2 * PI; circ(ctx, bx + math.cos(a) * rx, by + math.sin(a) * ry, 55)
    ell(ctx, bx, by, rx, ry)
    setc(ctx, INK); ctx.set_line_width(10); ctx.stroke_preserve(); setc(ctx, '#fffdf5'); ctx.fill()
    ctx.save(); ell(ctx, bx, by, rx + 20, ry + 20); ctx.clip(); inner(); ctx.restore()

# ---------------------------------------------------------------- backgrounds
def bg_haram_night(ctx, t):
    ctx.rectangle(-600, -400, 2300, 1800)
    ctx.set_source(lgrad(0, -300, 0, 1250, [(0, '#0b1030'), (0.6, '#1d2a5a'), (1, '#3a3a70')])); ctx.fill()
    B.stars(ctx, t, 700, 50)
    circ(ctx, 860, 230, 60); setc(ctx, '#fff6d8'); ctx.fill(); circ(ctx, 885, 215, 52); setc(ctx, '#0f1538'); ctx.fill()
    # arcades
    setc(ctx, '#2a2f5a')
    ctx.rectangle(-600, 850, 2300, 400); ctx.fill()
    for k in range(-6, 16):
        x0 = k * 120
        ctx.new_path(); ctx.move_to(x0 + 15, 1250); ctx.line_to(x0 + 15, 960); ctx.arc(x0 + 60, 960, 45, PI, 2 * PI); ctx.line_to(x0 + 105, 1250); ctx.close_path()
        setc(ctx, '#ffd98a', 0.55); ctx.fill()
    for mx in (-80, 1160):
        ctx.rectangle(mx - 20, 350, 40, 900); setc(ctx, '#2a2f5a'); ctx.fill()
        ctx.move_to(mx - 26, 355); ctx.line_to(mx, 250); ctx.line_to(mx + 26, 355); ctx.close_path(); ctx.fill()
        glow(ctx, mx, 500, 60, '#ffd98a', 0.6)
    ctx.rectangle(-600, 1250, 2300, 1200)
    ctx.set_source(lgrad(0, 1250, 0, 1900, [(0, '#c9cbd8'), (1, '#8f93ad')])); ctx.fill()
    for k in range(1, 9):
        ell(ctx, 540, 1255, 300 + k * 140, 30 + k * 32); setc(ctx, '#ffffff', 0.25); ctx.set_line_width(3); ctx.stroke()
    kaaba(ctx, 560, 1250, 0.95)

def bg_street_day(ctx, t, tone='#ffe9c4'):
    ctx.rectangle(-600, -400, 2300, 1800)
    ctx.set_source(lgrad(0, -300, 0, 1200, [(0, '#7ec8f0'), (1, tone)])); ctx.fill()
    glow(ctx, 900, 250, 220, '#fff2b0', 0.8); circ(ctx, 900, 250, 70); setc(ctx, '#ffe066'); ctx.fill()
    rnd = random.Random(7)
    for k in range(-4, 10):
        x0 = k * 190; hh = rnd.uniform(420, 620)
        ctx.rectangle(x0, 1250 - hh, 180, hh); fs(ctx, rnd.choice(['#e8c9a0', '#dcb88a', '#f0d6b0']), 4)
        ctx.rectangle(x0 - 6, 1250 - hh - 16, 192, 20); fs(ctx, '#c9a274', 3)
        for wy in (1250 - hh + 70, 1250 - hh + 220):
            if wy > 1150: continue
            ctx.new_path(); ctx.move_to(x0 + 60, wy + 70); ctx.line_to(x0 + 60, wy + 20); ctx.arc(x0 + 90, wy + 20, 30, PI, 2 * PI)
            ctx.line_to(x0 + 120, wy + 70); ctx.close_path(); fs(ctx, '#6a4a2a', 3)
    for px in (-60, 980):
        ctx.move_to(px, 1250); ctx.curve_to(px + 20, 1000, px - 10, 900, px + 10, 760); setc(ctx, '#8b5a2b'); ctx.set_line_width(24); ctx.stroke()
        for a in range(7):
            ang = -PI / 2 + (a - 3) * 0.45
            ctx.move_to(px + 10, 760); ctx.curve_to(px + 10 + math.cos(ang) * 80, 760 + math.sin(ang) * 80 - 30,
                                                  px + 10 + math.cos(ang) * 160, 760 + math.sin(ang) * 150, px + 10 + math.cos(ang) * 190, 760 + math.sin(ang) * 120 + 60)
            setc(ctx, '#3f9b3a'); ctx.set_line_width(18); ctx.stroke()
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#e6cf9e'); ctx.fill()
    for k in range(60):
        r = random.Random(k); ell(ctx, r.uniform(-500, 1600), r.uniform(1270, 1900), r.uniform(14, 30), r.uniform(5, 9)); setc(ctx, '#d4b880', 0.8); ctx.fill()

def bg_courtyard(ctx, t, lights=1.0):
    ctx.rectangle(-600, -400, 2300, 1800)
    ctx.set_source(lgrad(0, -300, 0, 1200, [(0, '#2a1a5a'), (0.7, '#c2477a'), (1, '#ffb36b')])); ctx.fill()
    B.stars(ctx, t, 400, 25)
    ctx.rectangle(-600, 700, 2300, 560); fs(ctx, '#e8c9a0', 5)
    for k in range(-3, 9):
        x0 = k * 200 + 40
        ctx.new_path(); ctx.move_to(x0, 1250); ctx.line_to(x0, 900); ctx.arc(x0 + 70, 900, 70, PI, 2 * PI); ctx.line_to(x0 + 140, 1250); ctx.close_path()
        fs(ctx, '#8a5a3a', 4)
        glow(ctx, x0 + 70, 1000, 90, '#ffd98a', 0.4 * lights)
    lanterns(ctx, t, 520, lights)
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#d9b07a'); ctx.fill()
    for k in range(-10, 30):
        ctx.move_to(k * 90, 1250); ctx.line_to(k * 90 - 300, 2000); setc(ctx, '#c49a62'); ctx.set_line_width(3); ctx.stroke()

# ---------------------------------------------------------------- scenes
def cam(ctx, fx, fy, z): ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-fx, -fy)

def sc_present(ctx, t, end=False):
    z = 1.0 + 0.012 * (t if t < 20 else t - 133)
    ctx.save(); cam(ctx, 540, 1000, z)
    bg_haram_night(ctx, t)
    p = P(arms='dua', eyes='closed', smile=0.3, mouth=mouth('genc', t))
    if 3.76 <= t < 6.8: p['eyes'] = 'closed'
    if 10.0 <= t < 16.3 and not end: p['eyes'] = 'normal'; p['face'] = 1; p['arms'] = 'chest' if t > 15 else 'dua'
    if 15.1 <= t < 16.4: p['smile'] = 0.6; p['eyes'] = 'happy'
    if end:
        glow(ctx, 330, 1150, 320, '#ffe9b0', 0.45 * seg(t, 133.5, 135))
        p['mouth'] = 0
    sit(ctx, 'genc', 330, 1450, 1.05, p, t)
    if not end:
        for n, keys, k in (('A', [(6.96, 1300), (9.0, 760)], 0), ('B', [(7.2, 1460), (9.4, 930)], 1)):
            x = kf(t, keys)
            if t < 6.96: continue
            q = P(face=-1, walk=t * 10 if moving(t, keys) else None, mouth=mouth(n, t), eyes='normal', brow=0.3, smile=0.2)
            if n == 'A' and 10.3 <= t < 15: q['arms'] = 'explain'
            if n == 'B' and 9.4 <= t: q['arms'] = 'shrug' if 12.7 < t < 15 else 'chest'
            char(ctx, n, x, 1480 - 30 * k, 0.95 - 0.04 * k, q, t)
    else:
        for k in range(12):
            a = t * 0.5 + k * 0.52
            sparkle(ctx, 330 + 260 * math.cos(a), 1050 + 300 * math.sin(a * 1.2), 14, 0.8)
    ctx.restore()

def sc_find(ctx, t):
    z = 1.0 if t < 21.3 else 1.35
    fx = 540 if t < 21.3 else 520
    ctx.save(); cam(ctx, fx, 1000 if t < 21.3 else 1080, z)
    bg_street_day(ctx, t)
    keys = [(16.5, -150), (19.6, 380)]
    x = kf(t, keys)
    p = P(walk=t * 9 if moving(t, keys) else None, smile=0.3)
    bx, by = 600, 1300
    if t >= 19.98: p['look'] = 1; p['eyes'] = 'wide'; p['smile'] = 0.1
    if 20.5 <= t < 21.38: p['bend'] = seg(t, 20.5, 21.0) * 0.55; p['fa'] = (1.0, -0.2)
    picked = t >= 21.1
    if picked:
        p['fa'] = (0.9, 0.9); p['ba'] = (0.6, 1.4); p['bend'] = 0
    r = char(ctx, 'genc2', x, 1350, 1.0, p, t)
    if not picked:
        bag(ctx, bx, by, 0.8, 0, 0.6 * seg(t, 19.98, 20.4) * (0.7 + 0.3 * math.sin(t * 6)), t)
    else:
        hx, hy = r['hand']
        op = seg(t, 21.6, 22.4)
        bag(ctx, hx + 10, hy + 20, 0.85, op, op, t)
        if t > 22.4:
            for k in range(10):
                a = t * 1.5 + k * 0.63
                coin(ctx, hx + 10 + 150 * math.cos(a), hy - 120 + 60 * math.sin(a), 16, math.cos(t * 6 + k))
    ctx.restore()
    if t >= 24.62:
        n = int(clamp((t - 24.62) / 1.2) * 1000)
        a = win(t, 24.62, 26.4, 0.15)
        font(ctx, 150, black=True)
        txt = f'{n}'; e = ctx.text_extents(txt)
        ctx.move_to(540 - e[4] / 2, 560); ctx.text_path(txt)
        setc(ctx, INK, a); ctx.set_line_width(20); ctx.stroke_preserve(); setc(ctx, '#ffd23f', a); ctx.fill()
        font(ctx, 70, black=True); txt = 'ALTIN'; e = ctx.text_extents(txt)
        ctx.move_to(540 - e[4] / 2, 660); ctx.text_path(txt); setc(ctx, INK, a); ctx.set_line_width(14); ctx.stroke_preserve(); setc(ctx, '#ffffff', a); ctx.fill()

def sc_conscience(ctx, t):
    ctx.save(); cam(ctx, 540, 1000, 1.15)
    bg_street_day(ctx, t)
    ctx.rectangle(-600, -400, 2300, 2400); setc(ctx, '#1a1030', 0.35); ctx.fill()
    p = P(eyes='wide', fa=(0.9, 0.9), ba=(0.6, 1.4), sweat=0.6, smile=-0.1, look=-1 if t < 29.5 else 1)
    r = char(ctx, 'genc2', 540, 1350, 1.0, p, t)
    hx, hy = r['hand']; bag(ctx, hx + 10, hy + 20, 0.85, 1, 0.8, t)
    na = win(t, 26.6, 31.2, 0.4) * (1 - seg(t, 30.0, 30.8))
    if na > 0:
        glow(ctx, 230, 900, 300, '#9b3aff', 0.45 * na)
        tinted(ctx, lambda: char(ctx, 'genc2', 230, 1250, 0.7, P(face=1, eyes='normal', smile=0.8, arms='explain',
                                                                     mouth=0.3 * abs(math.sin(t * 9))), t), '#5a1a8a', 0.55, na * 0.85)
    va = win(t, 29.4, 31.5, 0.4)
    if va > 0:
        glow(ctx, 850, 900, 300, '#fff6c8', 0.8 * va)
        tinted(ctx, lambda: char(ctx, 'genc2', 850, 1250, 0.7, P(face=-1, eyes='closed', smile=0.2, arms='chest',
                                                                     tilt=0.25 * math.sin(t * 7)), t), '#ffffff', 0.45, va * 0.9)
    ctx.restore()

def sc_return(ctx, t):
    if t < 37.84: fx, z = 540, 1.0
    elif t < 44.0: fx, z = 620, 1.1
    else: fx, z = 640, 1.3
    ctx.save(); cam(ctx, fx, 1020, z)
    bg_street_day(ctx, t)
    gkeys = [(31.6, 120), (33.3, 300), (37.84, 300), (38.9, 520)]
    gx = kf(t, gkeys)
    sx = kf(t, [(33.48, 1350), (34.9, 860)])
    sp = P(face=-1, walk=t * 10 if 33.48 < t < 34.9 else None, mouth=mouth('sahip', t), eyes='normal', brow=0.7, smile=-0.2, sweat=0.6)
    if 34.98 <= t < 37.74: sp['arms'] = 'pointup'
    if 38.94 <= t < 40.9: sp['arms'] = 'explain'; sp['mouth'] = B.env(t) * 0.8
    if 40.9 <= t: sp['eyes'] = 'happy'; sp['smile'] = 0.8; sp['sweat'] = 0; sp['blush'] = 0.7; sp['arms'] = 'give'
    gp = P(walk=t * 9 if moving(t, gkeys) else None, smile=0.3, look=math.sin(t * 3) if t < 33.4 else 1)
    gp['fa'] = (0.9, 0.9); gp['ba'] = (0.6, 1.4)
    hold = t < 42.2
    if 40.9 <= t < 42.4: gp['fa'] = (1.35, -0.1)
    if t >= 42.4: gp['fa'] = (0.12, 0.25); gp['ba'] = (-0.1, 0.15); gp['smile'] = 0.5
    if t >= 45.0: gp['arms'] = 'chest'; gp['eyes'] = 'happy'; gp['tilt'] = 0.15
    if sx < 1300: rs = char(ctx, 'sahip', sx, 1360, 1.0, sp, t)
    rg = char(ctx, 'genc2', gx, 1350, 1.0, gp, t)
    if hold:
        hx, hy = rg['hand']; bag(ctx, hx + 10, hy + 20, 0.85, 0, 0.3, t)
    elif sx < 1300:
        hx, hy = rs['hand']; bag(ctx, hx - 10, hy + 20, 0.85, 0, 0.5, t)
    if 44.4 <= t < 46.5 and sx < 1300:
        for k in range(8):
            u = clamp((t - 44.4 - k * 0.15) / 0.8)
            if u <= 0: continue
            sxh, syh = rs['hand']; ex, ey = rg['head'][0] + 40, rg['head'][1] + 280
            coin(ctx, lerp(sxh, ex, u), lerp(syh, ey, u) - 140 * math.sin(u * PI), 14, math.cos(t * 12 + k))
    if t >= 45.6:
        font(ctx, 80, black=True); a = win(t, 45.6, 47.5, 0.2); txt = '+30'
        ctx.move_to(gx - 60, 760); ctx.text_path(txt); setc(ctx, INK, a); ctx.set_line_width(14); ctx.stroke_preserve(); setc(ctx, '#ffd23f', a); ctx.fill()
    ctx.restore()

def sc_wedding(ctx, t):
    if t < 58.5: fx, fy, z = 540, 1000, 1.0
    elif t < 62.8: fx, fy, z = 700, 1100, 1.35
    elif t < 67.2: fx, fy, z = 560, 1050, 1.15
    elif t < 82.2: fx, fy, z = 540, 1020, 1.0
    else: fx, fy, z = 400, 940, 1.6
    ctx.save(); cam(ctx, fx, fy, z)
    bg_courtyard(ctx, t, seg(t, 55.5, 56.6) if t < 60 else 1.0)
    if t < 55.5:
        for n, x, k in (('A', 700, 0), ('B', 880, 1)):
            q = P(face=-1, smile=0.5, eyes='normal', arms='explain' if k == 0 else 'chest',
                  mouth=B.env(t) * 0.7 * abs(math.sin(t * 15)) if (k == 0 and 47.6 < t < 54.4) else 0)
            char(ctx, n, x, 1360 - 20 * k, 0.95, q, t)
        gp = P(smile=0.6, eyes='happy' if t > 54.5 else 'normal', blush=seg(t, 50, 51))
        char(ctx, 'genc', 330, 1350, 1.0, gp, t)
        if t > 51:
            for k in range(3):
                y = 700 - ((t * 60 + k * 80) % 240)
                ctx.save(); ctx.translate(330 + (k - 1) * 60, y); ctx.scale(1.2, 1.2)
                ctx.move_to(0, 10); ctx.curve_to(-30, -15, -12, -35, 0, -18); ctx.curve_to(12, -35, 30, -15, 0, 10)
                setc(ctx, '#ff5e7e', 0.8); ctx.fill(); ctx.restore()
        ctx.restore(); return
    # mules + dowry
    mx = kf(t, [(56.78, 1500), (58.4, 900)])
    mule(ctx, mx, 1380, 0.9, -1, t, 56.78 < t < 58.4)
    # dowry pile
    for k, (cx_, cy_, col) in enumerate(((560, 1300, '#8b4513'), (690, 1310, '#b3263e'), (620, 1220, '#a0522d'))):
        rrect(ctx, cx_ - 60, cy_ - 50, 120, 90, 10); fs(ctx, col, 4); ctx.rectangle(cx_ - 60, cy_ - 20, 120, 10); setc(ctx, '#f2c14e'); ctx.fill()
    shine = seg(t, 58.6, 59.4)
    bag_in_hand = t >= 62.9
    gp = P(smile=0.5)
    gx = kf(t, [(58.5, 330), (62.2, 470)])
    if 58.6 <= t: gp['eyes'] = 'wide'; gp['look'] = 1; gp['smile'] = 0.1
    if 59.0 <= t < 62.9: gp['walk'] = t * 9 if t < 62.2 else None
    if bag_in_hand: gp['fa'] = (0.9, 0.9); gp['ba'] = (0.6, 1.4); gp['mouth'] = mouth('genc2', t)
    if t >= 82.28: gp['eyes'] = 'wide'; gp['mouth'] = 0.25; gp['sweat'] = 0; gp['blush'] = 0.5; gp['tremble'] = 0.15
    if t >= 67.2:
        lp = P(face=-1, mouth=mouth('gelin', t), eyes='normal', smile=0.4, arms='chest' if t < 72 else 'explain')
        if 77.9 <= t: lp['eyes'] = 'happy'
        char(ctx, 'gelin', 820, 1360, 0.95, lp, t)
    r = char(ctx, 'genc', gx, 1350, 1.0, gp, t)
    if not bag_in_hand:
        bag(ctx, 760, 1270, 0.7, 0, shine * (0.7 + 0.3 * math.sin(t * 6)), t)
        if shine > 0:
            for k in range(4): sparkle(ctx, 760 + 70 * math.cos(t * 2 + k * 1.6), 1200 + 50 * math.sin(t * 2 + k * 1.6), 16, shine)
    else:
        hx, hy = r['hand']; bag(ctx, hx + 10, hy + 20, 0.8, 0, 0.5 + 0.5 * seg(t, 82.3, 84.7), t)
    if t >= 84.72:
        u = t - 84.72
        hx, hy = r['hand']
        glow(ctx, hx, hy - 40, 400, '#ffe27a', 0.5 * seg(t, 84.72, 85.5))
        for k in range(16):
            a = u * 1.4 + k * 2 * PI / 16
            rr = 260 * seg(t, 84.72, 86) * (1 - 0.6 * seg(t, 90.5, 92.2))
            coin(ctx, hx + rr * math.cos(a), hy - 40 + rr * 0.55 * math.sin(a), 18, math.cos(t * 8 + k))
    ctx.restore()
    if 72.4 <= t < 79.8:
        a = win(t, 72.4, 79.8, 0.3)
        ctx.save(); ctx.translate(540, 520); ctx.scale(a, a); ctx.translate(-540, -520)
        def inner():
            ctx.rectangle(0, 0, W, H); ctx.set_source(lgrad(0, 300, 0, 750, [(0, '#bfe3f5'), (1, '#f3dcb0')])); ctx.fill()
            char(ctx, 'genc2', 430, 760, 0.55, P(face=1, fa=(1.35, -0.1), smile=0.5), t)
            char(ctx, 'sahip', 650, 765, 0.55, P(face=-1, arms='give', eyes='happy', smile=0.8, blush=0.6), t)
            bag(ctx, 540, 640, 0.5, 0, 0.6, t)
        bubble(ctx, 540, 520, 300, 200, (760, 900), inner)
        ctx.restore()

def sc_chase(ctx, t):
    ctx.save(); cam(ctx, 540, 1000, 1.0)
    off = t * 300
    ctx.rectangle(-600, -400, 2300, 1800); ctx.set_source(lgrad(0, -200, 0, 1250, [(0, '#4a3a6a'), (1, '#c08a6a')])); ctx.fill()
    for k in range(-2, 9):
        x0 = k * 180 - off % 180
        r = random.Random(int((k * 180 - off) // 180))
        hh = r.uniform(300, 600); ctx.rectangle(x0, 1250 - hh, 160, hh); fs(ctx, r.choice(['#6a5a7a', '#5a4a6a', '#7a6a8a']), 4)
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#5a4a4a'); ctx.fill()
    for k in range(14):
        x0 = (k * 110 - off * 1.3) % 1540 - 230; ctx.rectangle(x0, 1500, 60, 10); setc(ctx, '#d9c08a', 0.7); ctx.fill()
    p = P(walk=t * 18, eyes='wide', sweat=1, brow=0.8, smile=-0.3, fa=(1.6, -0.2), ba=(-0.8, 0.4), tilt=0.1)
    char(ctx, 'C', 360, 1450, 1.0, p, t)
    for k in range(5):
        x = 720 + k * 70 + 30 * math.sin(t * 5 + k); y = 950 + 40 * math.sin(t * 7 + k * 1.3)
        tinted(ctx, lambda: coin(ctx, x, y, 26, math.cos(t * 9 + k)), '#3a1a4a', 0.45)
        for j in range(3):
            ctx.move_to(x - 40 - j * 20, y - 10 + j * 10); ctx.line_to(x - 80 - j * 20, y - 10 + j * 10)
        setc(ctx, '#ffffff', 0.7); ctx.set_line_width(4); ctx.stroke()
    ctx.restore()

def sc_path(ctx, t):
    ctx.rectangle(0, 0, W, H); ctx.set_source(lgrad(0, 0, 0, H, [(0, '#bfe9c9'), (1, '#8fd3a8')])); ctx.fill()
    pts = [(160, 300), (900, 420), (220, 700), (880, 900), (240, 1120), (640, 1280)]
    ctx.move_to(*pts[0])
    for a, b in zip(pts, pts[1:]):
        ctx.curve_to(a[0], (a[1] + b[1]) / 2, b[0], (a[1] + b[1]) / 2, b[0], b[1])
    setc(ctx, '#e6cf9e'); ctx.set_line_width(70); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke_preserve()
    setc(ctx, '#ffffff', 0.5); ctx.set_line_width(6); ctx.set_dash([20, 24]); ctx.stroke(); ctx.set_dash([])
    for k in range(9):
        r = random.Random(k + 30); x, y = r.uniform(80, 1000), r.uniform(250, 1300)
        circ(ctx, x, y, 40); circ(ctx, x + 35, y - 10, 34); setc(ctx, '#4fa864'); ctx.fill()
    # house
    hx, hy = 680, 1330
    ctx.rectangle(hx - 110, hy - 150, 220, 150); fs(ctx, '#f4e1c1', 5)
    ctx.move_to(hx - 140, hy - 145); ctx.line_to(hx, hy - 260); ctx.line_to(hx + 140, hy - 145); ctx.close_path(); fs(ctx, '#d1495b', 5)
    ctx.rectangle(hx - 30, hy - 90, 60, 90); fs(ctx, '#8b5a2b', 4)
    u = seg(t, 101.0, 106.0)
    seg_n = len(pts) - 1; v = u * seg_n; i = min(int(v), seg_n - 1); f = v - i
    a, b = pts[i], pts[i + 1]
    def bez(p0, p1, p2, p3, s): return ((1 - s) ** 3 * p0 + 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3 * p3)
    my = (a[1] + b[1]) / 2
    x = bez(a[0], a[0], b[0], b[0], f); y = bez(a[1], my, my, b[1], f)
    glow(ctx, x, y, 110, '#ffe27a', 0.8); coin(ctx, x, y, 36, math.cos(t * 6))
    if t > 105.8:
        glow(ctx, hx, hy - 120, 300, '#ffe27a', 0.7 * seg(t, 105.8, 106.6))
        for k in range(6): sparkle(ctx, hx + 160 * math.cos(t + k), hy - 150 + 100 * math.sin(t * 1.3 + k), 18)

def sc_doors(ctx, t):
    ctx.save(); cam(ctx, 540, 1000, 1.0)
    if t < 112.36:
        bg_street_day(ctx, t)
        ctx.rectangle(-600, -400, 2300, 2400); setc(ctx, '#1a1030', 0.45); ctx.fill()
        tinted(ctx, lambda: char(ctx, 'genc2', 540, 1350, 1.0, P(eyes='normal', smile=0.6, fa=(0.9, 0.9), ba=(0.6, 1.4)), t), '#3a1a5a', 0.5)
        bag(ctx, 640, 1080, 0.85, 1, 0, t)
        for k in range(3):
            ctx.move_to(560 + k * 50, 960); ctx.line_to(580 + k * 50, 1000); ctx.line_to(565 + k * 50, 1030)
            setc(ctx, '#2a1030'); ctx.set_line_width(4); ctx.stroke()
        ctx.restore(); return
    ctx.rectangle(-600, -400, 2300, 1800); ctx.set_source(lgrad(0, -200, 0, 1250, [(0, '#2a1a5a'), (1, '#6a4aa8')])); ctx.fill()
    ctx.rectangle(-600, 1250, 2300, 1200); setc(ctx, '#3a2a6a'); ctx.fill()
    for k, dx in enumerate((200, 540, 880)):
        op = seg(t, 113.0 + k * 1.6, 114.0 + k * 1.6)
        ctx.new_path(); ctx.move_to(dx - 120, 1250); ctx.line_to(dx - 120, 780); ctx.arc(dx, 780, 120, PI, 2 * PI); ctx.line_to(dx + 120, 1250); ctx.close_path()
        ctx.set_source(lgrad(0, 660, 0, 1250, [(0, '#fff6c8'), (1, '#ffd27a')])); ctx.fill_preserve(); setc(ctx, '#e0a83b'); ctx.set_line_width(14); ctx.stroke()
        glow(ctx, dx, 1000, 260, '#fff1c4', 0.6 * op)
        ctx.save(); ctx.translate(dx - 120, 0); ctx.scale(1 - 0.85 * op, 1)
        ctx.rectangle(0, 660, 240, 590); fs(ctx, '#7a3b1e', 5)
        circ(ctx, 200, 1000, 10); setc(ctx, '#f2c14e'); ctx.fill(); ctx.restore()
        if op > 0.5:
            for j in range(3):
                u = ((t - 114 - k * 1.6) * 0.5 + j / 3) % 1
                coin(ctx, lerp(dx, 540, u), lerp(1000, 1220, u) - 60 * math.sin(u * PI), 20, math.cos(t * 6 + j))
    char(ctx, 'genc', 540, 1420, 0.8, P(arms='dua', eyes='happy', smile=0.7, face=1), t)
    ctx.restore()

def sc_trust(ctx, t):
    ctx.save(); cam(ctx, 540, 1000, 1.0 + 0.01 * (t - 119.9))
    bg_haram_night(ctx, t)
    ring = seg(t, 123.0, 124.0)
    if ring > 0:
        ell(ctx, 330, 1460, 330, 80); setc(ctx, '#ffd23f', 0.9 * ring); ctx.set_line_width(10); ctx.stroke()
        glow(ctx, 330, 1420, 330, '#ffe27a', 0.35 * ring)
    if t > 124.8:
        bag(ctx, 520, 1480, 0.6, 0, 0.6 * seg(t, 124.8, 125.4), t)
    p = P(arms='dua' if t > 127.8 else 'chest', eyes='closed', smile=0.4)
    sit(ctx, 'genc', 330, 1450, 1.05, p, t)
    if t > 127.8:
        glow(ctx, 540, 300, 420, '#fff6c8', 0.5 * seg(t, 127.8, 129))
    if t > 129.36:
        u = seg(t, 129.4, 132.4)
        x = lerp(900, 380, u); y = lerp(200, 1100, u)
        glow(ctx, x, y, 100, '#ffe27a', 0.8); coin(ctx, x, y, 28, math.cos(t * 6))
    ctx.restore()

def title(ctx, a, y):
    if a <= 0: return
    for txt, yy, size in (('BİN', y, 150), ('ALTIN', y + 170, 190)):
        font(ctx, size, italic=True, black=True); e = ctx.text_extents(txt); x = 540 - e[4] / 2
        ctx.move_to(x + 10, yy + 10); ctx.text_path(txt); setc(ctx, '#0b1030', 0.7 * a); ctx.fill()
        ctx.move_to(x, yy); ctx.text_path(txt); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        setc(ctx, INK, a); ctx.set_line_width(26); ctx.stroke_preserve()
        ctx.set_source(lgrad(0, yy - size, 0, yy, [(0, '#ffffff', a), (0.5, '#ffe066', a), (1, '#f0a020', a)])); ctx.fill()

# ---------------------------------------------------------------- subtitles (big & legible)
TEXTS = [
    "Bir genç Kâbe'nin karşısında oturmuş, sürekli aynı duayı ediyormuş:",
    "“Allah'ım, beni haramdan koruduğun için sana hamd olsun.”",
    "Hep aynı duayı tekrarladığını görenler tabii merak ediyor.",
    "“Yahu kardeşim, başka dua bilmiyor musun sen?",
    "Neden sürekli bunu söylüyorsun?” diye soruyorlar.",
    "Genç anlatmaya başlıyor.",
    "“Bundan yıllar önce yine Kâbe'nin yakınlarındaydım.",
    "Yerde bir torba buldum.",
    "Açıp baktım ki içi altınla dolu.",
    "Saydım, tam bin altın var.",
    "Nefsim dedi ki: ‘Al bu altınları, hayatın kurtulsun.’",
    "Fakat vicdanım buna razı olmadı.",
    "Torbanın sahibini aramaya başladım.",
    "Bir süre sonra bir adam gördüm.",
    "‘Altın dolu torbamı bulan var mı?’ diye sesleniyordu.",
    "Yanına gittim.",
    "Adam torbayı doğru şekilde tarif edince",
    "torbayı hiç eksiltmeden kendisine teslim ettim.",
    "Adam çok duygulandı ve teşekkür etmek için bana 30 altın verdi.",
    "Bir süre sonra çevremdekiler, babası vefat etmiş, güzel ahlaklı bir tüccar kızından bahsettiler.",
    "Evlenmemizi uygun gördüler.",
    "Ben de kabul ettim.",
    "Düğün hazırlıkları yapıldı.",
    "Kızın çeyizi katırlarla getirildi.",
    "Eşyaların arasında gözüme tanıdık gelen bir torba ilişti.",
    "Torbayı elime aldım, ‘Bu torba nereden geldi?’ diye sordum. Kız şöyle cevap verdi:",
    "‘Babam yıllar önce Kâbe'nin yakınlarında, içinde bin altın bulunan bu torbayı kaybetmiş.",
    "Dürüst bir genç torbayı buluyor ve içinden tek bir altın bile almadan babama teslim ediyor.",
    "Babam da ona 30 altın veriyor.",
    "Kalan altınları da benim çeyizim için saklıyor.’",
    "Bunu duyunca olduğum yerde kalakaldım.",
    "Yıllar önce haramdan sakınarak sahibine verdiğim o altınlar, dönüp dolaşıp helal bir şekilde yeniden karşıma çıkmıştı.”",
    "Şimdi kardeşlerim, bu hikâye bize çok önemli bir hakikati hatırlatıyor.",
    "Nasip, peşinden haram yollarla koşarak yakalayacağımız bir şey değildir.",
    "Allah'ın senin için yazdığı rızık, zamanı geldiğinde öyle ya da böyle yolunu bulup sana ulaşır.",
    "O genç eğer ilk gün nefsine yenilseydi, aynı altınları haram olarak yiyecekti.",
    "Sabretti, emanete sahip çıktı ve Allah ona aynı nimeti hiç beklemediği kapılardan helal olarak nasip etti.",
    "O yüzden rızkın gecikti diye ümitsizliğe kapılma.",
    "Sen helal dairesinde kal.",
    "Emanete ihanet etme ve yapman gerekeni yap.",
    "Nedir o? Rabbine güven.",
    "Çünkü sana ait olan muhakkak seni bulacaktır.",
    "Rabbim rızkımızı helal, kazancımızı bereketli ve karşımıza çıkan nasipleri hakkımızda her daim hayırlı eylesin.",
]
_tr = json.load(open(os.path.join(HERE, 'transcript.json')))
assert len(_tr) == len(TEXTS), (len(_tr), len(TEXTS))

def build_cues():
    cues = []
    for s, text in zip(_tr, TEXTS):
        words = text.split(); chunks = []; cur = []
        for wd in words:
            cand = ' '.join(cur + [wd])
            if cur and len(cand) > 44: chunks.append(' '.join(cur)); cur = [wd]
            else:
                cur.append(wd)
                if len(cand) > 26 and wd[-1] in '.,?!:”’': chunks.append(' '.join(cur)); cur = []
        if cur: chunks.append(' '.join(cur))
        tot = sum(len(c) for c in chunks); t0 = s['start']; d = s['end'] - s['start']
        for c in chunks:
            dd = d * len(c) / tot; cues.append((t0, t0 + dd, c)); t0 += dd
    return cues
CUES = build_cues()

def draw_subs(ctx, t):
    txt = None
    for i, (a, b, c) in enumerate(CUES):
        nxt = CUES[i + 1][0] if i + 1 < len(CUES) else DUR
        if a <= t < min(b + 0.35, nxt): txt = c
    if not txt: return
    font(ctx, 66)
    lines = B.wrap(ctx, txt, 900)
    lh = 84; n = len(lines)
    widths = [ctx.text_extents(l)[4] for l in lines]
    bw = max(widths) + 70; bh = n * lh + 40
    y0 = 1500 - bh / 2
    rrect(ctx, 540 - bw / 2, y0, bw, bh, 26); setc(ctx, '#0b0814', 0.72); ctx.fill()
    for i, (ln, wdt) in enumerate(zip(lines, widths)):
        ctx.move_to(540 - wdt / 2, y0 + 20 + lh * i + 62); ctx.text_path(ln)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    setc(ctx, '#000'); ctx.set_line_width(8); ctx.stroke_preserve(); setc(ctx, '#ffffff'); ctx.fill()

# ---------------------------------------------------------------- flashback tint
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_v = np.clip(1 - 0.45 * (((_xx - W / 2) / (W * 0.8)) ** 2 + ((_yy - H / 2) / (H * 0.75)) ** 2), 0.55, 1)
VIG = (_v * 256).astype(np.uint16)[:, :, None]
del _yy, _xx, _v
def sepia(buf, amt):
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 4).copy()
    b, g, r = img[:, :, 0].astype(np.float32), img[:, :, 1].astype(np.float32), img[:, :, 2].astype(np.float32)
    L = 0.3 * r + 0.59 * g + 0.11 * b
    img[:, :, 2] = np.clip(r * (1 - amt) + (L * 1.08 + 24) * amt, 0, 255)
    img[:, :, 1] = np.clip(g * (1 - amt) + (L * 0.9 + 10) * amt, 0, 255)
    img[:, :, 0] = np.clip(b * (1 - amt) + (L * 0.62) * amt, 0, 255)
    img[:, :, :3] = ((img[:, :, :3].astype(np.uint16) * VIG) >> 8).astype(np.uint8)
    return img

CUTS = (16.4, 26.5, 31.55, 47.5, 92.35, 101.0, 107.27, 119.85, 133.2)
FLASH = (16.4, 92.35)
def render(ctx, t):
    setc(ctx, '#000'); ctx.paint()
    if t < 16.4: sc_present(ctx, t)
    elif t < 26.5: sc_find(ctx, t)
    elif t < 31.55: sc_conscience(ctx, t)
    elif t < 47.5: sc_return(ctx, t)
    elif t < 92.35: sc_wedding(ctx, t)
    elif t < 101.0: sc_chase(ctx, t)
    elif t < 107.27: sc_path(ctx, t)
    elif t < 119.85: sc_doors(ctx, t)
    elif t < 133.2: sc_trust(ctx, t)
    else: sc_present(ctx, t, end=True)

def overlay(ctx, t):
    a = 0
    for T in CUTS:
        if T in FLASH: continue
        a = max(a, 1 - abs(t - T) / 0.22)
    a = max(a, 1 - t / 0.4, (t - (DUR - 0.8)) / 0.8)
    if a > 0: setc(ctx, '#000', clamp(a)); ctx.paint()
    w = 0
    for T in FLASH: w = max(w, 1 - abs(t - T) / 0.35)
    if w > 0: setc(ctx, '#fff8e0', clamp(w)); ctx.paint()
    if t < 3.4: title(ctx, seg(t, 0.2, 0.6) * (1 - seg(t, 2.9, 3.4)), 520)
    if t > 140.8:
        a = seg(t, 140.8, 141.5); title(ctx, a, 480)
        font(ctx, 48, black=True); txt = '@animasyonhikayeai'; e = ctx.text_extents(txt)
        ctx.move_to(540 - e[4] / 2, 860); ctx.text_path(txt); setc(ctx, INK, a); ctx.set_line_width(10); ctx.stroke_preserve(); setc(ctx, '#ffffff', a); ctx.fill()
    draw_subs(ctx, t)

def frame(surf, t):
    ctx = cairo.Context(surf); render(ctx, t); surf.flush()
    if 16.4 <= t < 92.35:
        arr = sepia(bytes(surf.get_data()), 0.32)
        s2 = cairo.ImageSurface.create_for_data(bytearray(arr.tobytes()), cairo.FORMAT_ARGB32, W, H)
        ctx2 = cairo.Context(s2); overlay(ctx2, t); s2.flush(); return bytes(s2.get_data()), s2
    overlay(ctx, t); surf.flush(); return bytes(surf.get_data()), surf

if __name__ == '__main__':
    import subprocess
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if sys.argv[1] == 'png':
        for ts in sys.argv[3:]:
            t = float(ts); data, s = frame(surf, t); s.write_to_png(os.path.join(sys.argv[2], f'f_{t:07.2f}.png'))
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fr in range(f0, f1):
            data, _ = frame(surf, fr / FPS); ff.stdin.write(data)
        ff.stdin.close(); ff.wait()
