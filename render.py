#!/usr/bin/env python3
"""Draw the 24 November 2026 world-news front page (1024x1024) and save entry.png.

Layout (locked by the Gate 1 design review): masthead with the date dominant,
one full-width black lead panel, a 2-column grid of story panels, and an ALSO
box filling the last grid cell. Every text string is measured before it is
drawn; any overflow raises instead of silently clipping. Run: python3 render.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
PAPER = (250, 247, 240)   # #FAF7F0
INK = (20, 20, 20)        # #141414
BLUE = (27, 79, 138)      # #1B4F8A
SKY = (111, 168, 220)     # light blue, only on the black lead panel
AMBER = (232, 163, 61)    # blast accent, lead panel only
WHITE = (255, 255, 255)
GREY = (90, 90, 90)

W = H = 1024
MARGIN = 32
LIVE = W - 2 * MARGIN  # 960


def font(bold, size):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def text_w(f, s):
    return f.getbbox(s)[2]


def spaced_w(f, s, tracking):
    return sum(text_w(f, ch) + tracking for ch in s) - tracking


def draw_spaced(d, x, y, s, f, fill, tracking=0):
    """Draw left-aligned text with extra tracking between characters."""
    cx = x
    for ch in s:
        d.text((cx, y), ch, font=f, fill=fill)
        cx += text_w(f, ch) + tracking
    return cx


def draw_centred_spaced(d, cx, y, s, f, fill, tracking=0):
    x = cx - spaced_w(f, s, tracking) // 2
    draw_spaced(d, x, y, s, f, fill, tracking)
    return x


def wrap_two_lines(s, f, max_w):
    """Greedy word wrap, at most two lines; raise if it does not fit."""
    words = s.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(f, trial) <= max_w:
            cur = trial
        else:
            if not cur:
                raise ValueError("single word too wide: %r" % word)
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        raise ValueError("headline needs %d lines: %r" % (len(lines), s))
    for line in lines:
        if text_w(f, line) > max_w:
            raise ValueError("line too wide: %r" % line)
    return lines


def check_one_line(s, f, max_w, label):
    if text_w(f, s) > max_w:
        raise ValueError("%s too wide (%d > %d): %r" % (label, text_w(f, s), max_w, s))


# ---- icons: simple PIL primitives, one shape + one accent each -------------
def icon_tower(d, x, y, s, col, accent):
    # A skyscraper: three stacked tiers with visible steps, an antenna,
    # and a small blast star at the top corner.
    w = s * 44 // 100
    x0 = x + (s - w) // 2
    gap = max(2, s // 40)
    d.rectangle([x0, y + s * 48 // 100, x0 + w, y + s], fill=col)
    d.rectangle([x0 + w // 8, y + s * 28 // 100, x0 + w * 7 // 8,
                 y + s * 48 // 100 - gap], fill=col)
    d.rectangle([x0 + w // 4, y + s * 12 // 100, x0 + w * 3 // 4,
                 y + s * 28 // 100 - gap], fill=col)
    d.line([x0 + w // 2, y + s * 2 // 100, x0 + w // 2, y + s * 12 // 100],
           fill=col, width=max(3, s // 22))
    cx, cy = x0 + w // 2 - w // 4, y + s * 12 // 100
    r = s * 15 // 100
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        d.line([cx, cy, cx + dx * r, cy + dy * r], fill=accent, width=max(3, s // 18))


def icon_chart(d, x, y, s, col, accent):
    # Rising market line with an arrowhead, over a baseline.
    d.line([x + s // 10, y + s * 85 // 100, x + s * 90 // 100, y + s * 85 // 100],
           fill=col, width=max(3, s // 20))
    pts = [(x + s * 8 // 100, y + s * 70 // 100), (x + s * 35 // 100, y + s * 55 // 100),
           (x + s * 52 // 100, y + s * 62 // 100), (x + s * 88 // 100, y + s * 15 // 100)]
    d.line(pts, fill=accent, width=max(4, s // 14), joint="curve")
    tip = pts[-1]
    d.polygon([(tip[0], tip[1] - s // 8), (tip[0] + s // 10, tip[1] + s // 12),
               (tip[0] - s // 12, tip[1] + s // 10)], fill=accent)


def icon_halt(d, x, y, s, col, accent):
    # Three rising bars crossed by a horizontal halt bar (the sidecar pause).
    bw = s // 6
    for i, hfrac in enumerate((45, 65, 85)):
        bx = x + s // 10 + i * (bw + s // 12)
        by = y + s - hfrac * s // 100
        d.rectangle([bx, by, bx + bw, y + s * 92 // 100], fill=col)
    d.rectangle([x + s // 10, y + s * 38 // 100, x + s * 90 // 100, y + s * 50 // 100],
                fill=accent)


def icon_jet(d, x, y, s, col, accent):
    # A jet seen from above: fuselage triangle, swept wings, tail.
    d.polygon([(x + s // 2, y), (x + s * 62 // 100, y + s * 55 // 100),
               (x + s // 2, y + s * 45 // 100), (x + s * 38 // 100, y + s * 55 // 100)],
              fill=col)
    d.polygon([(x + s * 30 // 100, y + s * 40 // 100), (x + s * 8 // 100, y + s * 88 // 100),
               (x + s * 38 // 100, y + s * 62 // 100)], fill=col)
    d.polygon([(x + s * 70 // 100, y + s * 40 // 100), (x + s * 92 // 100, y + s * 88 // 100),
               (x + s * 62 // 100, y + s * 62 // 100)], fill=col)
    d.polygon([(x + s * 42 // 100, y + s * 62 // 100), (x + s * 38 // 100, y + s * 92 // 100),
               (x + s * 58 // 100, y + s * 62 // 100), (x + s * 62 // 100, y + s * 92 // 100)],
              fill=accent)


def icon_ballot(d, x, y, s, col, accent):
    # A ballot box with a paper slip and a check mark.
    d.rectangle([x + s * 12 // 100, y + s * 45 // 100, x + s * 88 // 100, y + s * 95 // 100],
                outline=col, width=max(4, s // 16))
    d.line([x + s * 35 // 100, y + s * 45 // 100, x + s * 65 // 100, y + s * 45 // 100],
           fill=col, width=max(3, s // 20))
    d.polygon([(x + s * 30 // 100, y + s * 8 // 100), (x + s * 70 // 100, y + s * 8 // 100),
               (x + s * 62 // 100, y + s * 45 // 100), (x + s * 38 // 100, y + s * 45 // 100)],
              fill=accent)
    d.line([(x + s * 30 // 100, y + s * 72 // 100), (x + s * 45 // 100, y + s * 85 // 100),
            (x + s * 72 // 100, y + s * 55 // 100)], fill=accent,
           width=max(4, s // 14), joint="curve")


def icon_train(d, x, y, s, col, accent):
    # A front-on train: body, windows, headlight, wheels, rails.
    d.rectangle([x + s * 15 // 100, y + s * 10 // 100, x + s * 85 // 100, y + s * 78 // 100],
                fill=col)
    for wx in (28, 52):
        d.rectangle([x + wx * s // 100, y + s * 22 // 100,
                     x + (wx + 16) * s // 100, y + s * 42 // 100], fill=PAPER)
    d.rectangle([x + s * 38 // 100, y + s * 52 // 100, x + s * 62 // 100, y + s * 68 // 100],
                fill=accent)
    for cx in (30, 70):
        d.ellipse([x + cx * s // 100 - s // 12, y + s * 78 // 100,
                   x + cx * s // 100 + s // 12, y + s * 78 // 100 + s // 6], fill=INK)
    d.line([x, y + s * 95 // 100, x + s, y + s * 95 // 100], fill=col, width=max(3, s // 20))


ICONS = {"tower": icon_tower, "chart": icon_chart, "halt": icon_halt,
         "jet": icon_jet, "ballot": icon_ballot, "train": icon_train}


def draw_story_panel(d, x, y, w, h, kicker, headline, subline, icon, accent=BLUE):
    """One 470x196 white story panel: blue top bar, kicker + icon band,
    headline (max 2 lines), subline."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=WHITE, outline=INK, width=2)
    d.rectangle([x + 2, y + 2, x + w - 3, y + 7], fill=BLUE)
    inner = x + 16
    inner_w = w - 32
    kf = font(True, 24)
    check_one_line(kicker, kf, inner_w - 76, "kicker %r" % kicker)
    draw_spaced(d, inner, y + 14, kicker, kf, BLUE, tracking=2)
    ICONS[icon](d, x + w - 16 - 56, y + 10, 56, INK, accent)
    hf = font(True, 40)
    lines = wrap_two_lines(headline, hf, inner_w)
    ly = y + 68
    for line in lines:
        d.text((inner, ly), line, font=hf, fill=INK)
        ly += 44
    sf = font(False, 28)
    check_one_line(subline, sf, inner_w, "subline %r" % subline)
    d.text((inner, y + 160), subline, font=sf, fill=GREY)


def draw_also_box(d, x, y, w, h, lines):
    """The ALSO box: same panel frame, three short one-liners."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=WHITE, outline=INK, width=2)
    d.rectangle([x + 2, y + 2, x + w - 3, y + 7], fill=BLUE)
    kf = font(True, 24)
    draw_spaced(d, x + 16, y + 14, "ALSO", kf, BLUE, tracking=2)
    lf = font(False, 26)
    ly = y + 56
    for line in lines:
        check_one_line(line, lf, w - 32, "also line %r" % line)
        d.text((x + 16, ly), line, font=lf, fill=INK)
        ly += 40


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead: title, then the date, dominant by design ----------------
    title = "THE WORLD IN ONE DAY"
    tf = font(True, 36)
    check_one_line(title, tf, LIVE, "title")
    draw_centred_spaced(d, W // 2, 30, title, tf, INK, tracking=4)
    date = "TUESDAY, 24 NOVEMBER 2026"
    df = font(True, 54)
    check_one_line(date, df, LIVE, "date")
    draw_centred_spaced(d, W // 2, 76, date, df, INK, tracking=1)
    d.rectangle([MARGIN, 148, W - MARGIN, 151], fill=BLUE)

    # ---- lead panel: the Riyadh tower strike, black box, full width ---------
    lx, ly, lw, lh = MARGIN, 162, LIVE, 196
    d.rectangle([lx, ly, lx + lw - 1, ly + lh - 1], fill=INK)
    d.rectangle([lx, ly, lx + lw - 1, ly + 5], fill=BLUE)
    lk = font(True, 24)
    draw_spaced(d, lx + 24, ly + 16, "MIDDLE EAST", lk, SKY, tracking=2)
    lhf = font(True, 48)
    check_one_line("RIYADH TOWER HIT", lhf, lw - 48 - 130, "lead headline")
    d.text((lx + 24, ly + 52), "RIYADH TOWER HIT", font=lhf, fill=WHITE)
    lsf = font(False, 30)
    sub = "Houthi strike, second in a week, 11 hurt"
    check_one_line(sub, lsf, lw - 48 - 130, "lead subline")
    d.text((lx + 24, ly + 118), sub, font=lsf, fill=(225, 225, 225))
    d.text((lx + 24, ly + 156), "PIF tower in the financial district",
           font=font(False, 26), fill=(180, 180, 180))
    icon_tower(d, lx + lw - 24 - 100, ly + 48, 100, WHITE, AMBER)

    # ---- grid: 2 cols x 3 rows of 470x196, last cell is the ALSO box --------
    pw, ph, gx, gy = 470, 196, 20, 16
    gy0 = 374
    stories = [
        ("MARKETS", "NIKKEI SOARS 3.9%", "Best gain since July 31", "chart"),
        ("MARKETS", "KOSPI TOPS 5,000", "Up 6.3%; buys halted 5 min", "halt"),
        ("SECURITY", "KOREA SCRAMBLES JETS", "Russian planes enter ADIZ", "jet"),
        ("PACIFIC", "PNG VOTES ON BOUGAINVILLE", "Vote begins on 2019 result", "ballot"),
        ("SOUTH ASIA", "FIRST TRAIN TO JANAKPUR", "Ayodhya-Janakpur link opens", "train"),
    ]
    for i, (kicker, headline, subline, icon) in enumerate(stories):
        row, col = divmod(i, 2)
        x = MARGIN + col * (pw + gx)
        y = gy0 + row * (ph + gy)
        draw_story_panel(d, x, y, pw, ph, kicker, headline, subline, icon)
    ax = MARGIN + 1 * (pw + gx)
    ay = gy0 + 2 * (ph + gy)
    draw_also_box(d, ax, ay, pw, ph, [
        "Trump tariff findings due",
        "Dhaka garment clashes",
        "Ukraine defends Libya strike",
    ])

    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG")
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
