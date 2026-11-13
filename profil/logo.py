import sys, os, math, cairo, importlib.util
D = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('anime', os.path.join(D, 'anime.py'))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
S = 1080; cx = cy = S / 2; PI = math.pi; INK = A.INK

def spaced(ctx, txt, size, y, track, italic=False, black=True):
    A.font(ctx, size, italic=italic, black=black)
    widths = [ctx.text_extents(ch)[4] for ch in txt]
    total = sum(widths) + track * (len(txt) - 1)
    x = cx - total / 2
    ctx.new_path()
    for ch, w in zip(txt, widths):
        ctx.move_to(x, y); ctx.text_path(ch); x += w + track
    return total

def make(path, variant):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); ctx = cairo.Context(surf)
    g = cairo.RadialGradient(cx, 470, 60, cx, cy, 780)
    for o, c in ((0, '#3a1660'), (0.6, '#1a0d3a'), (1, '#0a0618')):
        g.add_color_stop_rgb(o, *A.hexc(c))
    ctx.rectangle(0, 0, S, S); ctx.set_source(g); ctx.fill()
    A.stars(ctx, 3.0, S, 45)
    # emblem: play-button inside a film-frame speech bubble
    A.glow(ctx, cx, 300, 260, '#ff5ea8', 0.35)
    ctx.save(); ctx.translate(cx, 300)
    ctx.new_path(); ctx.save(); ctx.scale(175, 125); ctx.arc(0, 0, 1, 0, 2 * PI); ctx.restore()
    ctx.move_to(-70, 105); ctx.line_to(-120, 185); ctx.line_to(10, 120); ctx.close_path()
    A.setc(ctx, INK); ctx.set_line_width(22); ctx.stroke_preserve()
    ctx.set_source(A.lgrad(0, -125, 0, 125, [(0, '#fff6e0'), (1, '#ffd9a8')])); ctx.fill()
    ctx.move_to(-48, -70); ctx.line_to(78, 0); ctx.line_to(-48, 70); ctx.close_path(); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    A.setc(ctx, INK); ctx.set_line_width(20); ctx.stroke_preserve()
    ctx.set_source(A.lgrad(0, -70, 0, 70, [(0, '#ffcc33'), (1, '#ff7a1a')])); ctx.fill()
    ctx.move_to(-30, -38); ctx.line_to(20, -10); A.setc(ctx, '#ffffff', 0.75); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.restore()
    A.sparkle(ctx, cx + 215, 190, 34, 1.0, '#ffe14d'); A.sparkle(ctx, cx - 220, 380, 22, 1.0, '#7fe7ff')
    # ANİMASYON
    spaced(ctx, 'ANİMASYON', 92, 590, 10)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    A.setc(ctx, INK); ctx.set_line_width(16); ctx.stroke_preserve()
    ctx.set_source(A.lgrad(0, 520, 0, 590, [(0, '#7fe7ff'), (1, '#2e9bff')])); ctx.fill()
    # HİKAYE
    y = 790
    spaced(ctx, 'HİKAYE', 205, y + 14, 4, italic=True); A.setc(ctx, '#ff2e88'); ctx.fill()
    spaced(ctx, 'HİKAYE', 205, y, 4, italic=True)
    A.setc(ctx, INK); ctx.set_line_width(28); ctx.stroke_preserve()
    ctx.set_source(A.lgrad(0, y - 160, 0, y, [(0, '#ffffff'), (0.45, '#fff27a'), (1, '#ffa24a')])); ctx.fill()
    ctx.save(); spaced(ctx, 'HİKAYE', 205, y, 4, italic=True); ctx.clip()
    for k in range(10): ctx.rectangle(0, y - 160 + k * 18, S, 5)
    A.setc(ctx, '#ffffff', 0.2); ctx.fill(); ctx.restore()
    # AI badge
    bw, bh, by = 230, 104, 850
    A.rrect(ctx, cx - bw / 2, by, bw, bh, bh / 2)
    A.setc(ctx, INK); ctx.set_line_width(16); ctx.stroke_preserve()
    ctx.set_source(A.lgrad(cx - bw / 2, 0, cx + bw / 2, 0, [(0, '#9b5cff'), (1, '#ff5ea8')])); ctx.fill()
    spaced(ctx, 'AI', 74, by + 79, 8); A.setc(ctx, '#ffffff'); ctx.fill()
    A.sparkle(ctx, cx + bw / 2 - 10, by + 4, 26, 1.0, '#ffffff')
    A.sparkle(ctx, cx - bw / 2 + 4, by + bh - 6, 16, 1.0, '#ffe14d')
    if variant == 'ring':
        ctx.new_path(); ctx.arc(cx, cy, 522, 0, 2 * PI); A.setc(ctx, '#ffe14d'); ctx.set_line_width(14); ctx.stroke()
    surf.write_to_png(path)

make(os.path.join(sys.argv[1], 'logo.png'), 'ring')
