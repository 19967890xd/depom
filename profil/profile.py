import sys, os, math, cairo, importlib.util
D = os.path.dirname(os.path.abspath(__file__))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
A = load('anime', os.path.join(D, 'anime.py'))
T = load('anim1', os.path.join(D, '..', 'anim', 'anim.py'))

S = 1080
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
ctx = cairo.Context(surf)
cx = cy = S / 2
# background: retro sky in circle
ctx.rectangle(0, 0, S, S)
ctx.set_source(A.lgrad(0, 0, 0, S, [(0, '#1d1240'), (0.45, '#5a2a7a'), (0.72, '#e8507a'), (1, '#ffb347')])); ctx.fill()
A.stars(ctx, 1.0, 380, 25)
A.retro_sun(ctx, cx, 560, 330)
# horizon grid
ctx.rectangle(0, 760, S, S); ctx.set_source(A.lgrad(0, 760, 0, S, [(0, '#3a1f4f'), (1, '#140a24')])); ctx.fill()
for k in range(8):
    y = 780 + k * k * 6
    ctx.move_to(0, y); ctx.line_to(S, y); A.setc(ctx, '#ff5ea8', 0.4); ctx.set_line_width(2); ctx.stroke()
for k in range(-10, 11):
    ctx.move_to(cx + k * 30, 760); ctx.line_to(cx + k * 200, S); A.setc(ctx, '#ff5ea8', 0.3); ctx.set_line_width(2); ctx.stroke()
# glow behind book
A.glow(ctx, cx, 640, 420, '#ffe27a', 0.55)
# golden tree growing from book
T.draw_tree(ctx, cx, 760, 1.0, 0, 'gold', 0.7, s=1.12)
# open book
INK = A.INK
def page(sign):
    ctx.new_path(); ctx.move_to(cx, 770)
    ctx.curve_to(cx + sign * 120, 730, cx + sign * 230, 735, cx + sign * 330, 760)
    ctx.line_to(cx + sign * 330, 900)
    ctx.curve_to(cx + sign * 230, 875, cx + sign * 120, 870, cx, 910); ctx.close_path()
ctx.new_path(); ctx.move_to(cx - 350, 775); ctx.line_to(cx + 350, 775); ctx.line_to(cx + 350, 925); ctx.curve_to(cx + 200, 900, cx + 60, 900, cx, 935)
ctx.curve_to(cx - 60, 900, cx - 200, 900, cx - 350, 925); ctx.close_path(); A.fs(ctx, '#8b1e2e', 7)
for sg in (-1, 1):
    page(sg); A.fs(ctx, '#fff6e0', 6)
    for k in range(4):
        y = 790 + k * 26
        ctx.move_to(cx + sg * 60, y + 8); ctx.curve_to(cx + sg * 150, y - 10, cx + sg * 230, y - 8, cx + sg * 290, y + 2)
        A.setc(ctx, '#c9b48a'); ctx.set_line_width(5); ctx.stroke()
ctx.move_to(cx, 770); ctx.line_to(cx, 910); A.setc(ctx, INK); ctx.set_line_width(6); ctx.stroke()
# sparkles
for (x, y, r) in ((230, 330, 28), (850, 300, 34), (300, 600, 18), (800, 620, 22), (540, 140, 24), (170, 470, 14), (910, 480, 16)):
    A.sparkle(ctx, x, y, r, 0.95)
# film-strip ring hint (animation)
ctx.new_path(); ctx.arc(cx, cy, 520, 0, 2 * math.pi); A.setc(ctx, '#140a24'); ctx.set_line_width(36); ctx.stroke()
for k in range(36):
    a = k / 36 * 2 * math.pi
    ctx.save(); ctx.translate(cx + 520 * math.cos(a), cy + 520 * math.sin(a)); ctx.rotate(a)
    A.rrect(ctx, -6, -11, 12, 22, 3); A.setc(ctx, '#ffe14d'); ctx.fill(); ctx.restore()
surf.write_to_png(sys.argv[1])
