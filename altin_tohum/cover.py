import sys, math, cairo
sys.path.insert(0, __import__('os').path.dirname(__file__))
from anim import *

t = 50.0
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surf)
cam = (610, 1.25, 1720)
ctx.save(); apply_cam(ctx, *cam)
bg_palace(ctx, t)
ctx.restore()
# warm vignette focus
g = cairo.RadialGradient(540, 900, 200, 540, 900, 1250)
g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.12, 0.05, 0.02, 0.75)
ctx.set_source(g); ctx.paint()
glow(ctx, 540, 760, 520, '#ffe27a', 0.45)

ctx.save(); apply_cam(ctx, *cam)
# adam: hopeful, offering glowing seeds
p = base_pose(); p['face'] = 1; p['smile'] = 0.7; p['brow'] = 0.2; p['blink'] = False
p['fa'] = (1.35, -0.25); p['ba'] = (-0.2, 0.3)
a = draw_person(ctx, 'adam', 400, FLOOR, 1.0, p, t)
# padisah: sweating, worried
p = base_pose(); p['face'] = -1; p['sweat'] = 1.0; p['brow'] = 1; p['wide'] = 0.8; p['smile'] = -0.5
p['blink'] = False; p['look'] = 1; p['fa'] = (0.5, 2.4); p['ba'] = (-0.2, 0.4)
draw_person(ctx, 'pad', 830, FLOOR, 1.0, p, 0.35)
draw_seeds(ctx, a['hand'][0], a['hand'][1] - 30, 1.6, t)
for i in range(14):
    r = random.Random(i * 11)
    draw_coin(ctx, r.uniform(150, 1100), FLOOR + r.uniform(20, 120), 18, r.uniform(0.4, 1.0))
ctx.restore()

# thought bubble with golden tree
bx, by = 540, 830
hs = to_screen(a['head'], cam)
for fx, rr in ((0.3, 14), (0.55, 22)):
    circ(ctx, lerp(hs[0] + 40, bx - 120, fx), lerp(hs[1] - 10, by + 170, fx), rr); fs(ctx, '#fffdf5', 4)
ctx.new_path()
for k in range(12):
    an = k / 12 * 2 * PI
    circ(ctx, bx + math.cos(an) * 190, by + math.sin(an) * 150, 58)
circ(ctx, bx, by, 185)
setc(ctx, OUT); ctx.set_line_width(10); ctx.stroke_preserve(); setc(ctx, '#fffdf5'); ctx.fill()
ctx.save(); ell(ctx, bx, by, 210, 170); ctx.clip()
glow(ctx, bx, by - 20, 220, '#ffe27a', 0.5)
ell(ctx, bx, by + 155, 240, 45); setc(ctx, '#7a5230'); ctx.fill()
draw_tree(ctx, bx, by + 135, 1.0, 0, 'gold', 0.6, s=0.55)
ctx.restore()

def big_text(txt, y, size, fill, stroke, lw):
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    e = ctx.text_extents(txt)
    ctx.move_to(540 - e[4] / 2, y); ctx.text_path(txt)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    setc(ctx, stroke); ctx.set_line_width(lw); ctx.stroke_preserve()
    ctx.set_source(lgrad(ctx, 0, y - size, 0, y, fill) if isinstance(fill, list) else cairo.SolidPattern(*hexc(fill)))
    ctx.fill()

big_text('ALTIN TOHUM', 430, 128, [(0, '#fff3b0'), (0.5, '#f5c542'), (1, '#d08a1a')], '#3a1f0e', 24)
for k, (sx, sy) in enumerate(((150, 300), (930, 330), (960, 230), (120, 200))):
    sparkle(ctx, sx, sy, 22, 0.95)
big_text('Bu tohumu kim ekebilir?', 545, 60, '#ffffff', '#111111', 13)
surf.write_to_png(sys.argv[1])
