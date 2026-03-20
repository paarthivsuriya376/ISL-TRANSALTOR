"""
utils/isl_animator.py
─────────────────────────────────────────────────────
ISL Hand Gesture Animator — Illustrated Vector Style
─────────────────────────────────────────────────────
Renders realistic illustrated hands with gradient skin tones,
smooth rounded segments, highlighted knuckles — similar in
quality to vector/stock-art sign language reference charts.
All 26 letters A-Z have distinct, unique poses.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math, os

# ── Canvas ───────────────────────────────────────────────────────────────────
W, H = 400, 400
BG   = (245, 245, 250)          # light neutral background (like the reference)

# ── Skin palette (warm peachy gradient, like the Shutterstock style) ─────────
SKIN_BASE  = (238, 175, 132)    # main skin
SKIN_LIGHT = (252, 210, 170)    # highlight / top of finger
SKIN_DARK  = (200, 130,  90)    # shadow / underside
SKIN_LINE  = (180, 110,  75)    # outline / creases
NAIL_COL   = (248, 220, 195)    # fingernail
NAIL_LINE  = (210, 170, 140)

ACCENT    = (90, 100, 220)
WHITE     = (255, 255, 255)
TEXT_DARK = (40,  40,  80)

# ── Utility helpers ──────────────────────────────────────────────────────────
def _lerp(a, b, t):
    return a + (b - a) * t

def _lerp_color(c1, c2, t):
    return tuple(int(_lerp(a, b, t)) for a, b in zip(c1, c2))

def _rot_pt(x, y, angle_deg, cx=0, cy=0):
    rad = math.radians(angle_deg)
    px, py = x - cx, y - cy
    rx = px * math.cos(rad) - py * math.sin(rad)
    ry = px * math.sin(rad) + py * math.cos(rad)
    return int(cx + rx), int(cy + ry)

def _rot_pts(pts, angle_deg, cx=0, cy=0):
    return [_rot_pt(x, y, angle_deg, cx, cy) for x, y in pts]

# ── Base canvas ───────────────────────────────────────────────────────────────
def _base_frame(label="", sub=""):
    img = Image.new("RGBA", (W, H), (*BG, 255))
    d   = ImageDraw.Draw(img)

    # Soft gradient circle behind hand (like reference style)
    for r in range(155, 0, -5):
        alpha = int(28 * (r / 155))
        col = (220 - alpha, 225 - alpha, 255 - alpha, 255)
        d.ellipse([W//2 - r, H//2 - 20 - r, W//2 + r, H//2 - 20 + r], fill=col[:3])

    # Bottom label bar
    d.rectangle([0, H - 62, W, H], fill=(230, 232, 255))
    d.line([(0, H - 63), (W, H - 63)], fill=ACCENT, width=3)

    try:
        font_main = ImageFont.truetype("arialbd.ttf", 28)
        font_sub  = ImageFont.truetype("arial.ttf", 13)
    except:
        font_main = ImageFont.load_default()
        font_sub  = font_main

    if label:
        bbox = d.textbbox((0, 0), label, font=font_main)
        tw = bbox[2] - bbox[0]
        d.text(((W - tw) // 2, H - 54), label, fill=TEXT_DARK, font=font_main)
    if sub:
        bbox = d.textbbox((0, 0), sub, font=font_sub)
        tw = bbox[2] - bbox[0]
        d.text(((W - tw) // 2, H - 24), sub, fill=ACCENT, font=font_sub)

    return img.convert("RGB"), d


# ═══════════════════════════════════════════════════════════════════════════════
#  Core Hand Drawing Engine
# ═══════════════════════════════════════════════════════════════════════════════

class HandDrawer:
    """
    Draws a single illustrated hand on a PIL ImageDraw object.
    Produces smooth, gradient-shaded vector-style hands.
    """
    def __init__(self, img: Image.Image, cx: int, cy: int,
                 scale: float = 1.0, rotation: float = 0.0):
        self.img  = img
        self.d    = ImageDraw.Draw(img)
        self.cx   = cx
        self.cy   = cy
        self.s    = scale
        self.rot  = rotation   # overall hand rotation in degrees

    # ── Coordinate helpers ────────────────────────────────────────────────────
    def _p(self, x, y):
        """Scale + rotate + translate a point."""
        sx, sy = x * self.s, y * self.s
        return _rot_pt(self.cx + int(sx), self.cy + int(sy),
                       self.rot, self.cx, self.cy)

    def _poly(self, pts, fill, outline=None, width=2):
        tp = [self._p(x, y) for x, y in pts]
        self.d.polygon(tp, fill=fill, outline=outline)

    def _ellipse_at(self, cx, cy, rx, ry, fill, outline=None):
        p = self._p(cx, cy)
        rs = int(rx * self.s)
        ry2 = int(ry * self.s)
        self.d.ellipse([p[0]-rs, p[1]-ry2, p[0]+rs, p[1]+ry2],
                       fill=fill, outline=outline)

    # ── Rounded segment (finger bone) ────────────────────────────────────────
    def _segment(self, x, y_start, y_end, width, color_top, color_bot,
                 outline_col=None):
        """Draw one finger segment as a rounded capsule with gradient."""
        hw   = width // 2
        pts  = [
            (x - hw + 2, y_start),
            (x + hw - 2, y_start),
            (x + hw,     y_start + 4),
            (x + hw,     y_end   - 4),
            (x + hw - 2, y_end),
            (x - hw + 2, y_end),
            (x - hw,     y_end   - 4),
            (x - hw,     y_start + 4),
        ]
        # Gradient: blend top to bottom
        steps = max(abs(y_end - y_start), 4)
        for step in range(steps):
            t   = step / steps
            col = _lerp_color(color_top, color_bot, t)
            ys  = y_start + step
            xw  = hw - max(0, int(step * 0.01))
            self.d.line([self._p(x - xw, ys), self._p(x + xw, ys)], fill=col)

        # Subtle highlight strip on left side
        for step in range(steps):
            ys = y_start + step
            self.d.point(self._p(x - hw + 3, ys), fill=_lerp_color(SKIN_LIGHT, color_top, 0.4))

        self._poly(pts, fill=None, outline=outline_col or SKIN_LINE, width=1)

    # ── Fingertip with nail ───────────────────────────────────────────────────
    def _fingertip(self, x, y_top, width):
        hw = width // 2 - 1
        # Rounded tip
        for dy in range(12):
            t   = dy / 12
            xw  = int(hw * math.sin(math.pi * (1 - t * 0.5)))
            col = _lerp_color(SKIN_LIGHT, SKIN_BASE, t)
            self.d.line([self._p(x - xw, y_top + dy), self._p(x + xw, y_top + dy)],
                        fill=col)
        # Ellipse nail
        nail_y = y_top + 5
        nail_h = 10
        nail_w = hw - 2
        for dy in range(nail_h):
            t   = dy / nail_h
            xw  = int(nail_w * math.sin(math.pi * (1 - t * 0.4)))
            col = _lerp_color(NAIL_COL, NAIL_LINE, t)
            self.d.line([self._p(x - xw, nail_y + dy), self._p(x + xw, nail_y + dy)],
                        fill=col)
        outline_pts = [(x - hw + 1, y_top), (x + hw - 1, y_top),
                       (x + hw, y_top + 6), (x + hw - 2, y_top + 14),
                       (x - hw + 2, y_top + 14), (x - hw, y_top + 6)]
        self._poly(outline_pts, fill=None, outline=SKIN_LINE, width=1)

    # ── Single straight finger ────────────────────────────────────────────────
    def _finger_straight(self, x, y_base, total_len, width):
        """Draw a fully extended finger (3 segments + tip)."""
        seg1 = int(total_len * 0.38)
        seg2 = int(total_len * 0.30)
        seg3 = int(total_len * 0.20)

        # Seg 1 (proximal) - darkest
        self._segment(x, y_base - seg1, y_base,
                      width, SKIN_BASE, SKIN_DARK)
        # Knuckle joint
        self._ellipse_at(x, y_base - seg1, width//2 + 1, 4,
                         SKIN_DARK, SKIN_LINE)
        self._ellipse_at(x, y_base - seg1, width//2 - 1, 3,
                         _lerp_color(SKIN_LIGHT, SKIN_BASE, 0.5))
        # Seg 2 (middle)
        self._segment(x, y_base - seg1 - seg2, y_base - seg1,
                      width - 2, SKIN_LIGHT, SKIN_BASE)
        # Second knuckle
        self._ellipse_at(x, y_base - seg1 - seg2, width//2, 3,
                         SKIN_DARK, SKIN_LINE)
        # Seg 3 (distal)
        self._segment(x, y_base - seg1 - seg2 - seg3, y_base - seg1 - seg2,
                      width - 4, SKIN_LIGHT, SKIN_BASE)
        # Fingertip
        self._fingertip(x, y_base - seg1 - seg2 - seg3 - 12, width - 4)

    # ── Curled finger ─────────────────────────────────────────────────────────
    def _finger_curled(self, x, y_base, width):
        """Draw a fully curled/closed finger shown as a rounded knuckle bump."""
        bump_r  = width // 2 + 3
        bump_cy = y_base - bump_r - 2
        for dy in range(-bump_r - 2, bump_r + 2):
            t   = abs(dy) / (bump_r + 2)
            xw  = int(bump_r * math.sqrt(max(0, 1 - t * t)))
            col = _lerp_color(SKIN_BASE, SKIN_DARK, t * 0.7)
            self.d.line([self._p(x - xw, bump_cy + dy),
                         self._p(x + xw, bump_cy + dy)], fill=col)
        self._ellipse_at(x, bump_cy, bump_r, bump_r + 1, None, SKIN_LINE)
        self._ellipse_at(x, bump_cy - 2, bump_r - 3, bump_r - 4,
                         _lerp_color(SKIN_LIGHT, SKIN_BASE, 0.6))

    # ── Half-bent finger ──────────────────────────────────────────────────────
    def _finger_bent(self, x, y_base, total_len, width, bend=60):
        """Draw a finger bent at middle knuckle."""
        seg1 = int(total_len * 0.40)
        seg2 = int(total_len * 0.35)

        # Proximal segment straight up
        self._segment(x, y_base - seg1, y_base, width, SKIN_BASE, SKIN_DARK)
        self._ellipse_at(x, y_base - seg1, width//2, 4, SKIN_DARK, SKIN_LINE)
        self._ellipse_at(x, y_base - seg1, width//2 - 2, 3,
                         _lerp_color(SKIN_LIGHT, SKIN_BASE, 0.5))

        # Middle segment bends inward
        rad    = math.radians(bend)
        tip_dx = int(seg2 * math.sin(rad))
        tip_dy = int(seg2 * math.cos(rad))
        bx, by = x + tip_dx, y_base - seg1 - tip_dy

        # Draw bent segment as a line with width
        for i in range(max(abs(tip_dy), abs(tip_dx))):
            t   = i / max(abs(tip_dy), abs(tip_dx), 1)
            ix  = x   + int(tip_dx * t)
            iy  = (y_base - seg1) - int(tip_dy * t)
            col = _lerp_color(SKIN_LIGHT, SKIN_BASE, t)
            self.d.ellipse([self._p(ix - width//2 + 2, iy - 2),
                            self._p(ix + width//2 - 2, iy + 2)], fill=col)

        # Fingertip bump
        self._ellipse_at(bx, by, width//2 + 1, width//2 + 1,
                         SKIN_LIGHT, SKIN_LINE)

    # ── Palm ──────────────────────────────────────────────────────────────────
    def _palm(self, y_top=-10, y_bot=75, wide=70):
        """Draw a realistic palm trapezoid."""
        hw = wide // 2
        pts = [
            (-hw + 8, y_top), (hw - 8, y_top),
            (hw + 4,  y_top + 20),
            (hw,      y_bot  - 10),
            (hw - 8,  y_bot),
            (-hw + 8, y_bot),
            (-hw,     y_bot  - 10),
            (-hw - 4, y_top  + 20),
        ]
        # Gradient fill top→bottom
        height = y_bot - y_top
        for i in range(height):
            t   = i / height
            col = _lerp_color(SKIN_BASE, SKIN_DARK, t * 0.6)
            xw  = int(_lerp(hw + 4, hw - 8, t))
            self.d.line([self._p(-xw, y_top + i), self._p(xw, y_top + i)], fill=col)
        # Side highlight
        for i in range(height):
            self.d.point(self._p(-hw - 2 + int(i*0.02), y_top+i),
                         fill=SKIN_LINE)
        self._poly(pts, fill=None, outline=SKIN_LINE, width=2)

    # ── Wrist ─────────────────────────────────────────────────────────────────
    def _wrist(self, y_top=72, y_bot=108):
        for i in range(y_bot - y_top):
            t   = i / (y_bot - y_top)
            col = _lerp_color(SKIN_DARK, SKIN_BASE, t * 0.3)
            xw  = int(_lerp(32, 25, t))
            self.d.line([self._p(-xw, y_top + i), self._p(xw, y_top + i)], fill=col)
        pts = [(-34, y_top), (34, y_top), (27, y_bot), (-27, y_bot)]
        self._poly(pts, fill=None, outline=SKIN_LINE, width=2)

    # ── Thumb helpers ─────────────────────────────────────────────────────────
    def _thumb_out(self, curl=0.0):
        """Thumb pointing to the left side (L-shape, A, Y etc.)"""
        # Thumb base
        base_pts = [(-38, 10), (-42, 30), (-58, 25), (-54, 5)]
        for i in range(22):
            t   = i / 22
            col = _lerp_color(SKIN_BASE, SKIN_DARK, t * 0.5)
            self.d.line([self._p(-38 - int(t*8), 12 + i), self._p(-38, 12 + i)], fill=col)
        self._poly(base_pts, fill=None, outline=SKIN_LINE, width=1)

        if curl < 0.5:
            # Distal thumb segment extends outward
            seg_pts = [(-54, 5), (-58, 25), (-74, 18), (-70, 0)]
            for i in range(20):
                t   = i / 20
                col = _lerp_color(SKIN_LIGHT, SKIN_BASE, t)
                x0  = -54 - int(t * 16)
                y0  = 5  + int(t * 13)
                self.d.line([self._p(x0, y0 - 6), self._p(x0, y0 + 6)], fill=col)
            self._poly(seg_pts, fill=None, outline=SKIN_LINE, width=1)
            # Thumbnail
            self._ellipse_at(-70, 8, 6, 9, NAIL_COL, NAIL_LINE)

    def _thumb_up_alongside(self, curl=0.0):
        """Thumb resting alongside the index (B, H, U etc.)"""
        base_pts = [(-38, 5), (-42, 40), (-30, 42), (-28, 5)]
        for i in range(38):
            t   = i / 38
            col = _lerp_color(SKIN_BASE, SKIN_DARK, t * 0.4)
            xw  = 6 - int(t * 1)
            self.d.line([self._p(-34 - xw, 5 + i), self._p(-34 + xw, 5 + i)], fill=col)
        self._poly(base_pts, fill=None, outline=SKIN_LINE, width=1)
        self._fingertip(-34, -8, 14)

    def _thumb_tucked(self):
        """Thumb tucked under fingers (S, E etc.)"""
        pts = [(-38, 20), (-42, 50), (-22, 52), (-18, 20)]
        for i in range(32):
            t   = i / 32
            col = _lerp_color(SKIN_DARK, SKIN_BASE, t * 0.5)
            xw  = 10 - int(t*2)
            self.d.line([self._p(-30 - xw, 22 + i), self._p(-30 + xw, 22 + i)],
                        fill=col)
        self._poly(pts, fill=None, outline=SKIN_LINE, width=1)


# ═══════════════════════════════════════════════════════════════════════════════
#  Letter Renderers
# ═══════════════════════════════════════════════════════════════════════════════

def _render_letter(draw_fn, label, sub="ISL Fingerspelling",
                   n_frames=8, motion="bob"):
    frames = []
    for i in range(n_frames):
        t  = i / max(n_frames - 1, 1)
        dy, dx, drot, dscale = 0, 0, 0.0, 1.0

        if   motion == "bob":    dy = int(7 * math.sin(t * math.pi)); dscale = 1 + 0.02 * math.sin(t * math.pi)
        elif motion == "wave":   drot = 14 * math.sin(t * math.pi * 2); dy = int(3 * math.cos(t * math.pi * 2))
        elif motion == "nod":    drot = 10 * math.sin(t * math.pi * 2)
        elif motion == "shake":  dx = int(8 * math.sin(t * math.pi * 3))
        elif motion == "draw_j": drot = -25 * t + 20 * t * t; dy = int(8 * t)
        elif motion == "draw_z": dx = int(10 * math.sin(t * math.pi)); dy = int(5 * t)

        img, _ = _base_frame(label, sub)
        hd = HandDrawer(img, W // 2 + dx, H // 2 - 20 + dy,
                        scale=dscale, rotation=drot)
        draw_fn(hd)
        frames.append(img)
    return frames


# ─── Every letter calls _render_letter with a unique draw_fn ─────────────────

def _hand_A(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.0)
    for x, w in [(-23, 14), (-8, 15), (8, 15), (23, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_B(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 95), (8, 15, 88), (22, 13, 72)]:
        hd._finger_straight(x, -8, l, w)

def _hand_C(hd: HandDrawer):
    # C-shape: all fingers + thumb form a C
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.3)
    for x, w, l in [(-22, 14, 80), (-7, 15, 90), (8, 15, 82), (22, 13, 68)]:
        hd._finger_bent(x, -8, l, w, bend=55)

def _hand_D(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.6)
    hd._finger_straight(-22, -8, 88, 14)   # index up
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_E(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 95), (8, 15, 88), (22, 13, 72)]:
        hd._finger_bent(x, -8, l, w, bend=75)

def _hand_F(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.3)
    hd._finger_bent(-22, -8, 85, 14, bend=70)   # index+thumb circle
    for x, w, l in [(-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_straight(x, -8, l, w)

def _hand_G(hd: HandDrawer):
    # Hand rotated 90° — index points sideways
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot - 85)
    hd2._palm(); hd2._wrist()
    hd2._thumb_out()
    hd2._finger_straight(-22, -8, 85, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd2._finger_curled(x, -8, w)

def _hand_H(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot - 85)
    hd2._palm(); hd2._wrist()
    hd2._thumb_tucked()
    hd2._finger_straight(-22, -8, 85, 14)
    hd2._finger_straight(-7,  -8, 92, 15)
    for x, w in [(8, 15), (22, 13)]:
        hd2._finger_curled(x, -8, w)

def _hand_I(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w in [(-22, 14), (-7, 15), (8, 15)]:
        hd._finger_curled(x, -8, w)
    hd._finger_straight(22, -8, 70, 13)   # pinky up

def _hand_J(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w in [(-22, 14), (-7, 15), (8, 15)]:
        hd._finger_curled(x, -8, w)
    hd._finger_straight(22, -8, 70, 13)

def _hand_K(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.4)
    hd._finger_straight(-22, -8, 88, 14)
    hd._finger_straight(-7,  -8, 95, 15)
    for x, w in [(8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_L(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out()
    hd._finger_straight(-22, -8, 88, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_M(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85)]:
        hd._finger_bent(x, -8, l, w, bend=80)
    hd._finger_curled(22, -8, 13)

def _hand_N(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92)]:
        hd._finger_bent(x, -8, l, w, bend=80)
    for x, w in [(8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_O(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.4)
    for x, w, l in [(-22, 14, 85), (-7, 15, 95), (8, 15, 88), (22, 13, 72)]:
        hd._finger_bent(x, -8, l, w, bend=60)

def _hand_P(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot + 150)
    hd2._palm(); hd2._wrist()
    hd2._thumb_out()
    hd2._finger_straight(-22, -8, 88, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd2._finger_curled(x, -8, w)

def _hand_Q(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot + 160)
    hd2._palm(); hd2._wrist()
    hd2._thumb_out()
    hd2._finger_straight(-22, -8, 88, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd2._finger_curled(x, -8, w)

def _hand_R(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    # Index + middle crossed (R shape): draw them closer together
    hd._finger_straight(-18, -8, 88, 14)
    hd._finger_straight(-4,  -8, 95, 15)
    for x, w in [(10, 15), (24, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_S(hd: HandDrawer):
    hd._palm(); hd._wrist()
    for x, w in [(-22, 14), (-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)
    # Thumb over fingers (S = fist with thumb wrapped over)
    thumb_pts = [(-38, 10), (-42, 28), (-2, 22), (-2, 6)]
    for i in range(18):
        t = i / 18
        col = _lerp_color(SKIN_BASE, SKIN_DARK, t * 0.5)
        y0 = 6 + int(t * 16)
        x0 = -38 + int(t * 36)
        hd.d.line([hd._p(x0 - 6, y0), hd._p(x0 + 6, y0)], fill=col)
    hd._poly(thumb_pts, fill=None, outline=SKIN_LINE, width=1)

def _hand_T(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.5)
    hd._finger_bent(-22, -8, 85, 14, bend=70)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_U(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    hd._finger_straight(-22, -8, 88, 14)
    hd._finger_straight(-7,  -8, 95, 15)
    for x, w in [(8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_V(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    # index + middle spread apart (peace/V)
    hd._finger_straight(-26, -8, 88, 14)
    hd._finger_straight(-4,  -8, 95, 15)
    for x, w in [(12, 15), (26, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_W(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    hd._finger_straight(-24, -8, 88, 14)
    hd._finger_straight(-7,  -8, 95, 15)
    hd._finger_straight(10,  -8, 88, 15)
    hd._finger_curled(24, -8, 13)

def _hand_X(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    hd._finger_bent(-22, -8, 85, 14, bend=45)   # hooked index
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_Y(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out()
    for x, w in [(-22, 14), (-7, 15), (8, 15)]:
        hd._finger_curled(x, -8, w)
    hd._finger_straight(22, -8, 70, 13)   # pinky + thumb shaka

def _hand_Z(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    hd._finger_straight(-22, -8, 88, 14)   # index traces Z
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)


# ── Letter → render function map ─────────────────────────────────────────────
_LETTER_FN = {
    'A': (_hand_A, "bob"),    'B': (_hand_B, "bob"),
    'C': (_hand_C, "bob"),    'D': (_hand_D, "bob"),
    'E': (_hand_E, "bob"),    'F': (_hand_F, "bob"),
    'G': (_hand_G, "wave"),   'H': (_hand_H, "wave"),
    'I': (_hand_I, "bob"),    'J': (_hand_J, "draw_j"),
    'K': (_hand_K, "bob"),    'L': (_hand_L, "bob"),
    'M': (_hand_M, "bob"),    'N': (_hand_N, "bob"),
    'O': (_hand_O, "bob"),    'P': (_hand_P, "wave"),
    'Q': (_hand_Q, "wave"),   'R': (_hand_R, "bob"),
    'S': (_hand_S, "bob"),    'T': (_hand_T, "bob"),
    'U': (_hand_U, "bob"),    'V': (_hand_V, "bob"),
    'W': (_hand_W, "bob"),    'X': (_hand_X, "bob"),
    'Y': (_hand_Y, "bob"),    'Z': (_hand_Z, "draw_z"),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Word Signs
# ═══════════════════════════════════════════════════════════════════════════════

def _hand_HELLO(hd: HandDrawer):
    hd._palm(y_top=-8, y_bot=70, wide=68); hd._wrist()
    hd._thumb_out()
    for x, w, l in [(-22, 14, 88), (-7, 15, 95), (8, 15, 88), (22, 13, 72)]:
        hd._finger_straight(x, -8, l, w)

def _hand_YES(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.4)
    for x, w in [(-22, 14), (-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_NO(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    hd._finger_straight(-22, -8, 88, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_GOOD(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out()
    hd._finger_straight(-22, -8, 88, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_BAD(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot + 180)
    hd2._palm(); hd2._wrist()
    hd2._thumb_out()
    hd2._finger_straight(-22, -8, 88, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd2._finger_curled(x, -8, w)

def _hand_SORRY(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.3)
    for x, w in [(-22, 14), (-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_PLEASE(hd: HandDrawer):
    hd._palm(y_top=-8, y_bot=70, wide=68); hd._wrist()
    hd._thumb_out(curl=0.2)
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_straight(x, -8, l, w)

def _hand_LOVE(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out()
    for x, w in [(-22, 14), (-7, 15), (8, 15)]:
        hd._finger_curled(x, -8, w)
    hd._finger_straight(22, -8, 70, 13)

def _hand_THANK(hd: HandDrawer):
    hd._palm(y_top=-8, y_bot=70, wide=68); hd._wrist()
    hd._thumb_up_alongside()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_straight(x, -8, l, w)

def _hand_HELP(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out()
    for x, w in [(-22, 14), (-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_WHAT(hd: HandDrawer):
    hd._palm(y_top=-8, y_bot=70, wide=68); hd._wrist()
    hd._thumb_out(curl=0.5)
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_straight(x, -8, l, w)

def _hand_YOU(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    hd._finger_straight(-22, -8, 90, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_I_WORD(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w in [(-22, 14), (-7, 15), (8, 15)]:
        hd._finger_curled(x, -8, w)
    hd._finger_straight(22, -8, 70, 13)

def _hand_WATER(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85)]:
        hd._finger_bent(x, -8, l, w, bend=40)
    hd._finger_curled(22, -8, 13)

def _hand_FOOD(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.3)
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_bent(x, -8, l, w, bend=50)

def _hand_HOME(hd: HandDrawer):
    hd._palm(y_top=-8, y_bot=70, wide=68); hd._wrist()
    hd._thumb_out(curl=0.3)
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_straight(x, -8, l, w)

def _hand_COME(hd: HandDrawer):
    hd._palm(); hd._wrist()
    hd._thumb_out(curl=0.1)
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_bent(x, -8, l, w, bend=45)

def _hand_GO(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot - 45)
    hd2._palm(); hd2._wrist(); hd2._thumb_tucked()
    hd2._finger_straight(-22, -8, 90, 14)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd2._finger_curled(x, -8, w)

def _hand_SITTING(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot + 90)
    hd2._palm(); hd2._wrist(); hd2._thumb_tucked()
    hd2._finger_bent(-22, -8, 80, 14, bend=90)
    hd2._finger_bent(-7,  -8, 85, 15, bend=90)
    for x, w in [(8, 15), (22, 13)]:
        hd2._finger_curled(x, -8, w)

def _hand_STANDING(hd: HandDrawer):
    hd._palm(); hd._wrist(); hd._thumb_tucked()
    hd._finger_straight(-15, -8, 90, 14)
    hd._finger_straight(0,   -8, 95, 15)
    for x, w in [(15, 15), (25, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_STOP(hd: HandDrawer):
    hd._palm(y_top=-15, y_bot=60, wide=80); hd._wrist()
    hd._thumb_out()
    for x, w, l in [(-25, 16, 90), (-8, 18, 100), (8, 18, 95), (25, 15, 80)]:
        hd._finger_straight(x, -15, l, w)

def _hand_SLEEP(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot + 60)
    hd2._palm(); hd2._wrist(); hd2._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd2._finger_bent(x, -8, l, w, bend=40)

def _hand_WORK(hd: HandDrawer):
    hd._palm(); hd._wrist()
    for x, w in [(-22, 14), (-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_SCHOOL(hd: HandDrawer):
    hd._palm(); hd._wrist(); hd._thumb_out(curl=0.5)
    hd._finger_straight(-22, -8, 85, 14)
    hd._finger_straight(-7,  -8, 90, 15)
    for x, w in [(8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_HAPPY(hd: HandDrawer):
    hd._palm(y_top=-10, y_bot=70, wide=75); hd._wrist()
    hd._thumb_out()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_straight(x, -8, l, w)

def _hand_SAD(hd: HandDrawer):
    hd2 = HandDrawer(hd.img, hd.cx, hd.cy, hd.s, hd.rot + 180)
    hd2._palm(); hd2._wrist(); hd2._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd2._finger_bent(x, -8, l, w, bend=30)

def _hand_FRIEND(hd: HandDrawer):
    hd._palm(); hd._wrist(); hd._thumb_out(curl=0.2)
    hd._finger_bent(-22, -8, 85, 14, bend=45)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

def _hand_MY(hd: HandDrawer):
    hd._palm(); hd._wrist(); hd._thumb_tucked()
    for x, w, l in [(-22, 14, 85), (-7, 15, 92), (8, 15, 85), (22, 13, 70)]:
        hd._finger_straight(x, -8, l, w)

def _hand_TIME(hd: HandDrawer):
    hd._palm(); hd._wrist(); hd._thumb_tucked()
    hd._finger_bent(-22, -8, 85, 14, bend=60)
    for x, w in [(-7, 15), (8, 15), (22, 13)]:
        hd._finger_curled(x, -8, w)

_WORD_FN = {
    # Greetings & Courtesies
    "HELLO":   (_hand_HELLO,  "wave"),
    "HI":      (_hand_HELLO,  "wave"),
    "GOODBYE": (_hand_HELLO,  "wave"),
    "BYE":     (_hand_HELLO,  "wave"),
    "WELCOME": (_hand_HELLO,  "wave"),
    "YES":     (_hand_YES,    "nod"),
    "NO":      (_hand_NO,     "shake"),
    "GOOD":    (_hand_GOOD,   "bob"),
    "BAD":     (_hand_BAD,    "bob"),
    "SORRY":   (_hand_SORRY,  "bob"),
    "PLEASE":  (_hand_PLEASE, "bob"),
    "THANK":   (_hand_THANK,  "bob"),
    "THANKS":  (_hand_THANK,  "bob"),
    "HELP":    (_hand_HELP,   "wave"),
    "LOVE":    (_hand_LOVE,   "bob"),
    "HATE":    (_hand_BAD,    "shake"),

    # Pronouns
    "I":       (_hand_I_WORD, "bob"),
    "YOU":     (_hand_YOU,    "bob"),
    "ME":      (_hand_I_WORD, "bob"),
    "MY":      (_hand_MY,     "nod"),
    "MINE":    (_hand_MY,     "nod"),
    "YOUR":    (_hand_YOU,    "bob"),
    "YOURS":   (_hand_YOU,    "bob"),
    "WE":      (_hand_HELLO,  "wave"),
    "OUR":     (_hand_HELLO,  "wave"),
    "THEY":    (_hand_GO,     "wave"),
    "THEM":    (_hand_GO,     "wave"),

    # Questions
    "WHAT":    (_hand_WHAT,   "wave"),
    "WHERE":   (_hand_NO,     "shake"),
    "WHY":     (_hand_WHAT,   "shake"),
    "WHEN":    (_hand_TIME,   "nod"),
    "WHO":     (_hand_SORRY,  "bob"),
    "HOW":     (_hand_WHAT,   "wave"),

    # Actions & States
    "COME":     (_hand_COME,     "wave"),
    "COMEHERE": (_hand_COME,     "wave"),
    "GO":       (_hand_GO,       "wave"),
    "NOW":      (_hand_STOP,     "nod"),
    "STOP":     (_hand_STOP,     "nod"),
    "SITTING":  (_hand_SITTING,  "bob"),
    "SIT":      (_hand_SITTING,  "bob"),
    "STANDING": (_hand_STANDING, "bob"),
    "STAND":    (_hand_STANDING, "bob"),
    "SLEEP":    (_hand_SLEEP,    "nod"),
    "WORK":     (_hand_WORK,     "bob"),
    "PLAY":     (_hand_Y,        "wave"),
    "EAT":      (_hand_FOOD,     "bob"),
    "FOOD":     (_hand_FOOD,     "bob"),
    "DRINK":    (_hand_WATER,    "bob"),
    "WATER":    (_hand_WATER,    "bob"),
    "THIRSTY":  (_hand_WATER,    "bob"),
    "HUNGRY":   (_hand_FOOD,     "bob"),
    "AGAIN":    (_hand_COME,     "wave"),
    "MORE":     (_hand_STOP,     "bob"),
    "DONE":     (_hand_PLEASE,   "wave"),
    "FINISH":   (_hand_PLEASE,   "wave"),
    "FINISHED": (_hand_PLEASE,   "wave"),

    # Objects & Places
    "HOME":    (_hand_HOME,   "bob"),
    "HOUSE":   (_hand_HOME,   "bob"),
    "SCHOOL":  (_hand_SCHOOL, "bob"),
    "TIME":    (_hand_TIME,   "nod"),
    "TODAY":   (_hand_TIME,   "nod"),
    "TOMORROW":(_hand_GO,     "wave"),
    "FRIEND":  (_hand_FRIEND, "bob"),
    "FAMILY":  (_hand_O,      "wave"),
    "COFFEE":  (_hand_FOOD,   "bob"),
    "TEA":     (_hand_FOOD,   "bob"),
    "MILK":    (_hand_FOOD,   "bob"),

    # Emotions
    "HAPPY":   (_hand_HAPPY,  "bob"),
    "SAD":     (_hand_SAD,    "bob"),
    "ANGRY":   (_hand_BAD,    "shake"),
    "FINE":    (_hand_GOOD,   "bob"),
    "OK":      (_hand_GOOD,   "bob"),

    # People
    "MAN":     (_hand_D,      "bob"),
    "BOY":     (_hand_D,      "bob"),
    "WOMAN":   (_hand_I,      "bob"),
    "GIRL":    (_hand_I,      "bob"),
    "TEACHER": (_hand_L,      "bob"),
    "STUDENT": (_hand_E,      "bob"),
    "NAME":    (_hand_H,      "bob"),

    # Misc
    "SEE":     (_hand_V,      "bob"),
    "LOOK":    (_hand_V,      "bob"),
    "KNOW":    (_hand_D,      "nod"),
    "THINK":   (_hand_D,      "nod"),
    "WANT":    (_hand_COME,   "bob"),
    "NEED":    (_hand_COME,   "bob"),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def get_frames_for_word(word: str):
    key = word.upper().strip()

    if key in _WORD_FN:
        fn, motion = _WORD_FN[key]
        return _render_letter(fn, key, "ISL Word Sign", n_frames=14, motion=motion)

    # Fingerspell
    frames = []
    for ch in key:
        if ch in _LETTER_FN:
            fn, motion = _LETTER_FN[ch]
            frames.extend(_render_letter(fn, ch, "ISL Fingerspelling",
                                         n_frames=8, motion=motion))
        elif ch == ' ':
            img, _ = _base_frame("[ SPACE ]", "")
            frames.append(img)
    return frames


def get_frames_for_sentence(sentence: str):
    result = []
    for word in sentence.strip().split():
        clean = ''.join(c for c in word.upper() if c.isalpha())
        if clean:
            frames = get_frames_for_word(clean)
            if frames:
                result.append((clean, frames))
    return result
