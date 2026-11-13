import sys, os, math, cairo, importlib.util, random
D = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('anime', os.path.join(D, 'anime.py'))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
S = 1080; cx = cy = S / 2; PI = math.pi; INK = A.INK

def rays(ctx, c1, c2, n=28, ox=cx, oy=cy):
    ctx.rectangle(0, 0, S, S); A.setc(ctx, c1); ctx.fill()
    for k in range(n):
        a = k / n * 2 * PI
        ctx.move_to(ox, oy); ctx.line_to(ox + 1600 * math.cos(a), oy + 1600 * math.sin(a))
        ctx.line_to(ox + 1600 * math.cos(a + PI / n), oy + 1600 * math.sin(a + PI / n)); ctx.close_path()
    A.setc(ctx, c2); ctx.fill()

def halftone(ctx, col, a=0.25):
    for y in range(0, S, 36):
        for x in range(0, S, 36):
            d = math.hypot(x - cx, y - cy) / 760
            r = 3 + 9 * d
            A.circ(ctx, x + (18 if (y // 36) % 2 else 0), y, r)
    A.setc(ctx, col, a); ctx.fill()

# ---------- 1: meddah storyteller mascot
def opt1(path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); ctx = cairo.Context(surf)
    rays(ctx, '#ffcc33', '#ffb020')
    halftone(ctx, '#ff7a00', 0.18)
    st = dict(skin='#f3c9a3', hair='short', hairc='#2a1a12', beard='short', beardc='#3a2418', iris='#2e7d6a', w=1.0)
    p = A.pose(); p['eyes'] = 'happy'; p['mouth'] = 0.7; p['blush'] = 0.6; p['look'] = 1
    # body
    ctx.new_path(); ctx.move_to(240, S); ctx.curve_to(250, 820, 380, 760, 540, 760); ctx.curve_to(700, 760, 830, 820, 840, S); ctx.close_path()
    A.fs(ctx, '#c0392b', 9)
    ctx.move_to(540, 770); ctx.line_to(500, S); ctx.line_to(580, S); ctx.close_path(); A.setc(ctx, '#f5e6c8'); ctx.fill()
    ctx.rectangle(240, 960, 600, 40); A.setc(ctx, '#f2c14e'); ctx.fill()
    ctx.save(); ctx.translate(500, 560); ctx.scale(3.5, 3.5)
    A.head(ctx, st, p, 0.5, 'G')
    # fez
    ctx.move_to(-52, -48); ctx.line_to(48, -56); ctx.line_to(38, -118); ctx.line_to(-38, -112); ctx.close_path(); A.fs(ctx, '#c0392b', 4)
    ctx.move_to(0, -116); ctx.curve_to(-30, -118, -50, -100, -55, -72); A.setc(ctx, INK); ctx.set_line_width(4); ctx.stroke()
    A.circ(ctx, -55, -68, 6); A.setc(ctx, '#f2c14e'); ctx.fill()
    ctx.restore()
    # raised hand with handkerchief (meddah mendili)
    ctx.move_to(800, 900); ctx.curve_to(860, 820, 880, 720, 880, 640); A.setc(ctx, INK); ctx.set_line_width(70); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.move_to(800, 900); ctx.curve_to(860, 820, 880, 720, 880, 640); A.setc(ctx, '#c0392b'); ctx.set_line_width(56); ctx.stroke()
    A.circ(ctx, 880, 610, 42); A.fs(ctx, '#f3c9a3', 7)
    ctx.new_path(); ctx.move_to(890, 580); ctx.curve_to(960, 480, 1010, 520, 1000, 430); ctx.curve_to(1040, 520, 980, 600, 905, 640); ctx.close_path(); A.fs(ctx, '#ffffff', 6)
    for x, y, r in ((170, 200, 40), (930, 230, 30), (150, 640, 24)):
        A.sparkle(ctx, x, y, r, 1.0, '#ffffff')
    surf.write_to_png(path)

# ---------- 2: retro anime monogram
def opt2(path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); ctx = cairo.Context(surf)
    ctx.rectangle(0, 0, S, S); ctx.set_source(A.lgrad(0, 0, 0, S, [(0, '#0f0a2a'), (0.6, '#3a1660'), (1, '#e8507a')])); ctx.fill()
    A.stars(ctx, 2.0, 500, 30)
    A.retro_sun(ctx, cx, 640, 300)
    ctx.rectangle(0, 800, S, S); A.setc(ctx, '#120822'); ctx.fill()
    for k in range(-10, 11):
        ctx.move_to(cx + k * 30, 800); ctx.line_to(cx + k * 220, S); A.setc(ctx, '#2ee6ff', 0.5); ctx.set_line_width(3); ctx.stroke()
    for k in range(7):
        y = 815 + k * k * 7; ctx.move_to(0, y); ctx.line_to(S, y); A.setc(ctx, '#2ee6ff', 0.5); ctx.stroke()
    A.font(ctx, 440, italic=True, black=True)
    txt = 'AH'; e = ctx.text_extents(txt); x = cx - e[4] / 2 - 10; y = 700
    ctx.move_to(x + 22, y + 22); ctx.text_path(txt); A.setc(ctx, '#ff2e88', 0.9); ctx.fill()
    ctx.move_to(x, y); ctx.text_path(txt); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    A.setc(ctx, INK); ctx.set_line_width(34); ctx.stroke_preserve()
    A.setc(ctx, '#2ee6ff'); ctx.set_line_width(14); ctx.stroke_preserve()
    ctx.set_source(A.lgrad(0, y - 330, 0, y, [(0, '#ffffff'), (0.5, '#fff27a'), (1, '#ff9a4d')])); ctx.fill()
    for k in range(4):
        ctx.move_to(x + 40, y - 300 + k * 80); ctx.line_to(x + e[4] - 40, y - 300 + k * 80)
    ctx.save(); ctx.move_to(x, y); ctx.text_path(txt); ctx.clip()
    for k in range(18):
        ctx.rectangle(0, y - 340 + k * 22, S, 6)
    A.setc(ctx, '#ffffff', 0.18); ctx.fill(); ctx.restore()
    A.sparkle(ctx, 860, 330, 46, 1.0); A.sparkle(ctx, 200, 820, 30, 1.0)
    surf.write_to_png(path)

# ---------- 3: speech bubble + play button (flat, modern)
def opt3(path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); ctx = cairo.Context(surf)
    ctx.rectangle(0, 0, S, S); ctx.set_source(A.lgrad(0, 0, S, S, [(0, '#12b3a8'), (1, '#0b6e8a')])); ctx.fill()
    halftone(ctx, '#ffffff', 0.08)
    # back film frame
    ctx.save(); ctx.translate(cx + 40, cy + 30); ctx.rotate(0.12)
    A.rrect(ctx, -330, -260, 660, 500, 50); A.fs(ctx, '#1a1020', 10)
    for k in range(6):
        A.rrect(ctx, -290 + k * 108, -240, 60, 34, 8); A.setc(ctx, '#ffe14d'); ctx.fill()
        A.rrect(ctx, -290 + k * 108, 186, 60, 34, 8); A.setc(ctx, '#ffe14d'); ctx.fill()
    ctx.restore()
    # speech bubble
    ctx.new_path(); ctx.new_sub_path(); ctx.save(); ctx.translate(510, 465); ctx.scale(330, 245); ctx.arc(0, 0, 1, 0, 2 * PI); ctx.restore()
    ctx.move_to(330, 640); ctx.line_to(250, 840); ctx.line_to(470, 680); ctx.close_path()
    A.setc(ctx, INK); ctx.set_line_width(26); ctx.stroke_preserve(); A.setc(ctx, '#fff6e0'); ctx.fill()
    # play triangle
    ctx.move_to(440, 340); ctx.line_to(660, 465); ctx.line_to(440, 590); ctx.close_path()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); A.setc(ctx, INK); ctx.set_line_width(30); ctx.stroke_preserve(); A.setc(ctx, '#ffb020'); ctx.fill()
    ctx.move_to(470, 390); ctx.line_to(560, 440); A.setc(ctx, '#ffffff', 0.7); ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    for x, y, r in ((860, 230, 44), (880, 820, 30), (170, 300, 26)):
        A.sparkle(ctx, x, y, r, 1.0, '#ffe14d')
    surf.write_to_png(path)

opt1(os.path.join(sys.argv[1], 'secenek1.png'))
opt2(os.path.join(sys.argv[1], 'secenek2.png'))
opt3(os.path.join(sys.argv[1], 'secenek3.png'))
