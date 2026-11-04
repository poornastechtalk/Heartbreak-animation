import math as m
import random as r
import turtle as t
import tkinter.font as tkf

SC = 21
OY = 20
DURATION = 8          # seconds for the heart to write itself
TICK = 16
ANIM = 42
LIFT = 34
GAP = 7
SIZES = (9, 10, 11, 12)
FONT = "Arial"
BG = "#050309"

HOLD = 55             # ticks the whole heart stays intact
CRACK = 55            # ticks for the crack to run down the heart
SPLIT = 110           # ticks for the halves to drift apart
PAUSE = 45
SEP = 34              # how far each half moves sideways
GRAVITY = 0.22

s = t.Screen()
s.setup(800, 800)
s.bgcolor(BG)
s.title("Heartbreak")
s.tracer(0)

cv = s.getcanvas()
rng = r.Random(11)

PHRASES = [
    "I miss you", "Te extraño", "Tu me manques", "Ich vermisse dich",
    "Mi manchi", "Sinto sua falta", "Я скучаю по тебе", "보고 싶어",
    "会いたい", "我想你", "Μου λείπεις", "Ik mis je", "Jag saknar dig",
    "Tęsknię za tobą", "ฉันคิดถึงเธอ", "Anh nhớ em", "Aku rindu kamu",
    "Я сумую за тобою", "Seni özledim", "Goodbye", "Adiós", "Please stay",
]

_fonts = {}


def font_for(size):
    if size not in _fonts:
        _fonts[size] = tkf.Font(root=cv, family=FONT, size=size, weight="bold")
    return _fonts[size]


def heart(a):
    x = 16 * (m.sin(a) ** 3)
    y = (13 * m.cos(a) - 5 * m.cos(2 * a)
         - 2 * m.cos(3 * a) - m.cos(4 * a))
    return x * SC, y * SC + OY


def hx(c):
    return "#%02x%02x%02x" % tuple(int(max(0, min(1, v)) * 255) for v in c)


def mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def dim(c, k):
    return tuple(v * k for v in c)


def clamp(v):
    return max(0.0, min(1.0, v))


POLY = [heart(2 * m.pi * i / 720) for i in range(720)]
EDGES = list(zip(POLY, POLY[1:] + POLY[:1]))
YMAX = max(p[1] for p in POLY)
YMIN = min(p[1] for p in POLY)
CY = (YMAX + YMIN) / 2
BGC = tuple(int(BG[i:i + 2], 16) / 255 for i in (1, 3, 5))

# ---- the crack: a jagged line from the top notch to the bottom tip ----
_top, _bot = heart(0)[1], heart(m.pi)[1]
_n = 11
CK = []
for _i in range(_n + 1):
    _y = _top + (_bot - _top) * _i / _n
    _x = 0 if _i in (0, _n) else ((-1) ** _i) * rng.uniform(8, 26)
    CK.append((_x, _y))


def crack_x(y):
    if y >= CK[0][1]:
        return CK[0][0]
    for (xa, ya), (xb, yb) in zip(CK, CK[1:]):
        if yb <= y <= ya:
            return xa + (y - ya) * (xb - xa) / (yb - ya)
    return CK[-1][0]


def spans(y):
    xs = []
    for (x1, y1), (x2, y2) in EDGES:
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))


def intersect(A, B):
    out = []
    for a in A:
        for b in B:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 14:
                out.append((lo, hi))
    return out


def phrase_cycle():
    while True:
        order = PHRASES[:]
        rng.shuffle(order)
        yield from order


def radial(x, y):
    return m.hypot(x / (16 * SC), (y - CY) / (14.5 * SC))


def build():
    cycle = phrase_cycle()
    row_h = max(font_for(z).metrics("linespace") for z in SIZES) + 4
    half = row_h / 2
    placed = []

    y = YMAX - half
    while y > YMIN + half:
        row = intersect(spans(y + half), spans(y - half))
        c = max(crack_x(y + half), crack_x(y - half)) * 0 + crack_x(y)

        for lo0, hi0 in row:
            # split every row at the crack so words never straddle it
            segs = [(lo0, min(hi0, c - 6)), (max(lo0, c + 6), hi0)]
            for lo, hi in segs:
                if hi - lo <= 20:
                    continue
                side = -1 if (lo + hi) / 2 < c else 1
                lo += 4
                hi -= 4
                cur = lo + rng.uniform(0, 8)
                line = []

                while True:
                    fit = None
                    for _ in range(10):
                        text = next(cycle)
                        size = rng.choice(SIZES)
                        w = font_for(size).measure(text)
                        if cur + w <= hi:
                            fit = (text, size, w)
                            break
                    if not fit:
                        break
                    text, size, w = fit
                    line.append([cur + w / 2, text, size, w])
                    cur += w + GAP

                if not line:
                    continue

                if len(line) > 1:
                    left = hi - (line[-1][0] + line[-1][3] / 2)
                    for i, it in enumerate(line):
                        it[0] += left * i / (len(line) - 1)
                else:
                    line[0][0] = (lo + hi) / 2

                for i, (x, text, size, w) in enumerate(line):
                    edge = i == 0 or i == len(line) - 1
                    placed.append(dict(x=x, y=y, text=text, size=size,
                                       edge=edge, side=side))
        y -= row_h

    wine = (0.58, 0.0, 0.09)
    crimson = (0.90, 0.05, 0.14)
    blood = (0.98, 0.10, 0.16)
    cold = (0.40, 0.44, 0.62)          # what love turns into
    for p in placed:
        rad = min(1.0, radial(p["x"], p["y"]))
        base = mix(wine, crimson, 0.25 + 0.75 * rad)
        base = mix(base, blood,
                   rng.uniform(0, 0.35) + (0.3 if p["edge"] else 0))
        p["color"] = tuple(min(1, v) for v in base)
        p["rad"] = rad
        # words nearest the crack stay a little red, like they're bleeding
        near = clamp(1 - abs(p["x"] - crack_x(p["y"])) / 110)
        p["cold"] = mix(cold, (0.8, 0.12, 0.2), 0.45 * near)
        p["bx"], p["by"] = p["x"], -p["y"]

    edges = [p for p in placed if p["edge"]]
    inner = [p for p in placed if not p["edge"]]
    edges.sort(key=lambda p: m.atan2(p["x"], p["y"] - CY) % (2 * m.pi))
    inner.sort(key=lambda p: -p["rad"] + rng.uniform(0, 0.08))
    return edges + inner


FLASH = (1.0, 0.78, 0.78)
ORDER = build()
RATE = len(ORDER) / (DURATION * 1000 / TICK)

active = []
items = iter(())
acc = 0.0
spawning = True
phase = "build"
clock = 0
crack_lines = []
can_rotate = True


def put(p, x, y):
    cv.coords(p["shadow"], x + 2, y + 3)
    cv.coords(p["halo"], x, y)
    cv.coords(p["main"], x, y)


def spawn(p):
    x, y = p["bx"], p["by"]
    size, text = p["size"], p["text"]
    font = (FONT, size, "bold")
    big = (FONT, size + 1, "bold")
    p["shadow"] = cv.create_text(x + 2, y + 3, text=text, font=font, fill=BG)
    p["halo"] = cv.create_text(x, y, text=text, font=big, fill=BG)
    p["main"] = cv.create_text(x, y - LIFT, text=text, font=font, fill=BG)
    p["f"] = 0
    p["dx"] = rng.uniform(-10, 10)
    active.append(p)


def animate_in(p):
    p["f"] += 1
    u = clamp(p["f"] / ANIM)
    e = 1 - (1 - u) ** 3
    c = p["color"]
    x, y = p["bx"], p["by"]
    px = x + p["dx"] * (1 - e)
    py = y - (1 - e) * LIFT

    cv.itemconfig(p["shadow"], fill=hx(mix(BGC, dim(c, 0.30), e)))
    cv.itemconfig(p["halo"], fill=hx(mix(BGC, dim(c, 0.20), e * e)))
    cv.coords(p["halo"], px, py)

    flash = 0.75 * m.sin(m.pi * clamp((u - 0.55) / 0.45))
    cv.itemconfig(p["main"], fill=hx(mix(mix(BGC, c, e ** 1.5), FLASH, flash)))
    cv.coords(p["main"], px, py)

    if u >= 1:
        put(p, x, y)
        cv.itemconfig(p["main"], fill=hx(c))
        return False
    return True


def reset():
    global items, acc, spawning, phase, clock, active, crack_lines
    cv.delete("all")
    items = iter(ORDER)
    acc = 0.0
    spawning = True
    active = []
    crack_lines = []
    phase = "build"
    clock = 0


def go(name):
    global phase, clock
    phase = name
    clock = 0


def step():
    global spawning, acc, clock, crack_lines, can_rotate
    clock += 1

    if phase == "build":
        if spawning:
            acc += RATE
            try:
                while acc >= 1:
                    acc -= 1
                    spawn(next(items))
            except StopIteration:
                spawning = False
        active[:] = [p for p in active if animate_in(p)]
        if not spawning and not active:
            go("hold")

    elif phase == "hold":
        # a faint, nervous heartbeat before it breaks
        beat = 0.5 + 0.5 * m.sin(clock * 0.35)
        for p in ORDER[::3]:
            cv.itemconfig(p["main"], fill=hx(mix(p["color"], FLASH, 0.25 * beat)))
        if clock >= HOLD:
            for p in ORDER:
                cv.itemconfig(p["main"], fill=hx(p["color"]))
            glow = cv.create_line(0, 0, 0, 0, fill="#3a0612", width=9,
                                  capstyle="round", joinstyle="round")
            core = cv.create_line(0, 0, 0, 0, fill="#ffe3e3", width=2,
                                  joinstyle="miter")
            crack_lines = [glow, core]
            go("crack")

    elif phase == "crack":
        k = max(2, int(len(CK) * clock / CRACK) + 1)
        pts = []
        for x, y in CK[:k]:
            pts += [x, -y]
        for ln in crack_lines:
            cv.coords(ln, *pts)
        if clock >= CRACK:
            for ln in crack_lines:
                cv.delete(ln)
            crack_lines = []
            go("split")

    elif phase == "split":
        u = clamp(clock / SPLIT)
        e = u * u * (3 - 2 * u)
        for p in ORDER:
            sd = p["side"]
            put(p, p["bx"] + sd * SEP * e, p["by"] - sd * 10 * e)
            cv.itemconfig(p["main"], fill=hx(mix(p["color"], p["cold"], e)))
            cv.itemconfig(p["halo"], fill=hx(mix(BGC, dim(p["cold"], 0.2), e)))
        if u >= 1:
            go("pause")

    elif phase == "pause":
        if clock >= PAUSE:
            for p in ORDER:
                sd = p["side"]
                p["fx"] = p["bx"] + sd * SEP
                p["fy"] = p["by"] - sd * 10
                p["y0"] = p["fy"]
                p["vx"] = rng.uniform(-0.5, 0.5) + sd * 0.35
                p["vy"] = 0.0
                p["ang"] = 0.0
                p["spin"] = rng.uniform(-3, 3)
                p["alive"] = True
                # words closest to the crack let go first
                d = abs(p["bx"] - crack_x(-p["by"])) / (16 * SC)
                p["delay"] = int(d * 260 + rng.uniform(0, 45))
                cv.delete(p["shadow"])
                cv.delete(p["halo"])
            go("fall")

    elif phase == "fall":
        left = 0
        for p in ORDER:
            if not p["alive"]:
                continue
            left += 1
            if clock < p["delay"]:
                continue
            p["vy"] += GRAVITY
            p["fx"] += p["vx"]
            p["fy"] += p["vy"]
            k = clamp((p["fy"] - p["y0"]) / 280)
            cv.coords(p["main"], p["fx"], p["fy"])
            cv.itemconfig(p["main"], fill=hx(mix(p["cold"], BGC, k ** 0.8)))
            if can_rotate:
                p["ang"] += p["spin"]
                try:
                    cv.itemconfig(p["main"], angle=p["ang"])
                except Exception:
                    can_rotate = False
            if k >= 1:
                cv.delete(p["main"])
                p["alive"] = False
        if left == 0:
            go("end")

    elif phase == "end":
        if clock >= 100:
            reset()

    cv.after(TICK, step)


try:
    reset()
    cv.after(200, step)
    t.done()
except (t.Terminator, Exception):
    pass
