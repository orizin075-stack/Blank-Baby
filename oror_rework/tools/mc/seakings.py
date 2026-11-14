"""059g: the two sea kings remade after the user's design sheets (the user: "じゃあ海の王様二体も見直してみて").

  * 淵煌 Enkou, 災極海獣 (sheet 15): an abyssal shark-beast. A massive head that is mostly maw, opened wide on rows
    of long white teeth, a glowing ice-blue eye under a heavy brow and a rune ring on its crown; a thick body tapering
    into a long tail ending in a forked crescent fin; jagged blades of dark crystal down its back, swept back and
    getting smaller toward the tail, jagged pectoral and pelvic fins; dark navy scales with white-blue lightning veins
    over everything and a pale belly.
  * バハムート Bahamut, 大海皇鯨 (sheet 18): a humpback whale and the sea's emperor. A long head with a rounded jaw,
    the white grooved throat and belly, a crown of blue crystal and gold over the brow; deep blue hide patterned with
    gold lines and diamond marks; pectoral fins as long as its body, feathered like wings (blue to white), hung with
    lanterns; on its back the ruins of a temple with pillars and arches among pink and violet coral, kelp and
    waterfalls running down its flanks; tail flukes feathered like the fins.
Model space: pixels, y down, the front -z; one texel to a pixel. Bones as the shipped rigs have them (root, body,
head, jaw, fin_r/fin_l, tail1..n), so the game animates them as before.
"""
import math
import numpy as np
from paint import M
import creatures_ia as CI
from dragons_sheet import V, rseg, spike

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


def fin_blades(bone, root, back, out, n, L0, L1, w, mats, spread=0.5, droop=0.0):
    """A jagged fin as Minecraft builds sheet 15's: blades fanned from root, from pointing `back` to pointing `out`."""
    back, out = np.asarray(back, float), np.asarray(out, float)
    for i in range(n):
        t = i / max(1, n - 1)
        d = back * (1 - t) + out * t
        d = d / np.linalg.norm(d) + V(0, droop * t, 0)
        L = L0 + (L1 - L0) * math.sin(t * math.pi) if spread else L0 + (L1 - L0) * t
        p = V(*root) + (out / np.linalg.norm(out)) * (t * spread * 2.0)
        spike(bone, p, p + d * L, w, mats[i % len(mats)])


def feather_plane(bone, base, A, B, n, span, L, w, cols, edge=None, lantern=None, every=3, curve=None):
    """A broad fin of overlapping feathers (sheet 18's wings and flukes): n feathers along A (the leading edge, `span`
    long) each running back along B for L(t), split into len(cols) bands of colour from the root (dark) to the tip
    (light); a gold leading edge; lanterns hung from every `every`th feather's tip."""
    A = np.asarray(A, float); A = A / np.linalg.norm(A)
    B = np.asarray(B, float); B = B - (B @ A) * A; B = B / np.linalg.norm(B)
    N = np.cross(A, B)
    base = np.asarray(base, float)
    for i in range(n):
        t = i / max(1, n - 1)
        p = base + A * (span * t)
        Lt = L(t)
        Bt = B if curve is None else (B + A * curve * t); Bt = Bt / np.linalg.norm(Bt)
        k = len(cols)
        for j in range(k):
            q0 = p + Bt * (Lt * j / k)
            q1 = p + Bt * (Lt * (j + 1) / k + 0.4)
            CI.seg(bone, tuple(q0), tuple(q1), w * (1.0 - 0.25 * j / k), 0.9, cols[j], up=tuple(N))
        if lantern is not None and i % every == every - 1:
            tip = p + Bt * Lt
            CI.seg(bone, tuple(tip), tuple(tip + V(0, 3.0, 0)), 0.5, 0.5, edge, up=(0, 0, 1))
            CI.cbox(bone, tuple(tip + V(0, 5.0, 0)), (1.8, 3.2, 1.8), lantern)
            CI.cbox(bone, tuple(tip + V(0, 3.2, 0)), (2.2, 0.6, 2.2), edge)
            CI.cbox(bone, tuple(tip + V(0, 6.8, 0)), (2.2, 0.6, 2.2), edge)
    if edge is not None:
        CI.seg(bone, tuple(base), tuple(base + A * span), 1.4, 2.0, edge, up=tuple(N), ext=0.6)


# ===================================================================================================== Enkou
@recipe
def enkou():
    r = CI.rig('enkou', td=1)
    hide = M('scale', '#141a2c', belly='#c8d0dc', scale_size=1.1, contrast=0.9)
    vein_hide = M('scale', '#18203a', belly='#18203a', scale_size=1.1, contrast=0.95)
    belly = M('scale', '#c8d0dc', belly='#e4eaf0', scale_size=1.6, contrast=0.4)
    crystal = M('gem', '#2a3858', glow=False)
    crystal2 = M('gem', '#4a6a9a', glow=False)
    edge = M('gem', '#9fd8ff', glow=True)
    tooth = M('tooth', '#eef2f6')
    mouth = M('simple', '#1a0c18')
    vein = M('energy', '#7ab8f0', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.5, speed=0.05)
    body = r.bone('body', root, (0, -6, 0), anim='sway', ax=1, amp=0.05, speed=0.06)
    # ------------------------------------------------------------------ the body: deep at the shoulders, tapering back
    for (z0, z1, w, h, y) in ((-12.0, 4.0, 19.0, 21.0, -7.0), (2.0, 14.0, 16.0, 17.5, -7.0), (12.0, 22.0, 12.5, 13.5, -7.5)):
        rseg(body, V(0, y, z0), V(0, y, z1), w, h, vein_hide, up=(0, -1, 0), bevel=3.6)
        hb = h * 0.34                                                                               # the pale belly
        rseg(body, V(0, y + h / 2 - hb / 2 + 0.25, z0 + 0.6), V(0, y + h / 2 - hb / 2 + 0.25, z1 - 0.6), w - 1.2, hb, belly, up=(0, -1, 0),
             bevel=min(3.0, hb * 0.4))
    # lightning veins: branching lines of light over the flanks (irregular, as sheet 15's)
    import random
    rnd = random.Random(15)
    for sx in (-1, 1):
        for (y0, z0, n) in ((-14.0, -11.0, 7), (-5.0, -8.0, 6), (-12.0, 4.0, 6), (-4.0, 9.0, 4)):
            p = V(sx * 9.6, y0, z0)
            for k in range(n):
                q = p + V(0, rnd.uniform(-2.6, 2.6), rnd.uniform(1.6, 3.4))
                xw = 9.6 if q[2] < 4 else (8.1 if q[2] < 14 else 6.4)
                q[0] = sx * (xw + 0.05)
                CI.seg(body, tuple(p), tuple(q), 0.12, 0.4, vein, up=(sx, 0, 0))
                if rnd.random() < 0.35:                                                            # a branch
                    b = q + V(0, rnd.choice((-1, 1)) * rnd.uniform(1.5, 3.0), rnd.uniform(0.5, 2.0))
                    b[0] = q[0]
                    CI.seg(body, tuple(q), tuple(b), 0.12, 0.4, vein, up=(sx, 0, 0))
                p = q
    # the crystal blades down the back: flat shards swept back, largest over the shoulders, light along their edges
    def blade(bone, base, tip, w, mat, side=(1, 0, 0)):
        base, tip = np.asarray(base, float), np.asarray(tip, float)
        mid = base + (tip - base) * 0.55
        CI.seg(bone, tuple(base), tuple(mid), w, 1.2, mat, up=side, ext=0.4)
        CI.seg(bone, tuple(mid), tuple(tip), w * 0.5, 1.0, mat, up=side, ext=0.3)
        CI.seg(bone, tuple(base + (tip - base) * 0.2), tuple(tip), 0.5, 1.3, edge, up=side)
    for k, (z, h) in enumerate(((-9.0, 10.0), (-4.0, 14.0), (1.0, 12.0), (5.5, 10.0), (10.0, 8.0), (14.0, 6.5), (18.0, 5.0))):
        y = -18.0 + max(0.0, z) * 0.12
        blade(body, V(0, y + 1.5, z), V(0, y - h, z + h * 0.6), 5.0 - k * 0.35, crystal if k % 2 else crystal2)
        for sx in (-1, 1):
            if k < 5:
                blade(body, V(sx * 4.5, y + 3.0, z + 1.0), V(sx * 7.5, y - h * 0.45, z + h * 0.55), 3.0, crystal2,
                      side=(1, 0.6 * sx, 0))
    # ------------------------------------------------------------------ the fins: jagged, swept back
    for sx in (-1, 1):
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, (sx * 8.5, 0.0, -5.0), rot=(0.0, 0.0, 0.0), anim='sway', ax=2,
                    amp=0.12, speed=0.08)
        # a broad fin of jagged blades (sheet 15: 胸びれ), swept back and down, blue light along each blade
        for i in range(7):
            t = i / 6
            d = V(sx * (0.95 - 0.45 * t), 0.5 + 0.25 * t, 0.45 + 1.0 * t)
            d = d / np.linalg.norm(d)
            L = 17.0 - 7.0 * t
            p = V(sx * 8.5, -1.0 + t * 2.0, -6.0 + t * 5.0)
            spike(fb, p, p + d * L, 4.2 - t * 1.0, crystal if i % 2 else hide)
            CI.seg(fb, tuple(p + d * L * 0.25), tuple(p + d * L * 0.9), 0.4, 0.4, edge, up=(0, -1, 0))
        for i in range(3):                                                                         # the pelvic fins
            d = V(sx * 0.5, 0.8, 0.8 + i * 0.3)
            p = V(sx * 6.0, 1.0, 12.0 + i * 1.6)
            spike(body, p, p + d / np.linalg.norm(d) * (9.0 - i * 1.5), 2.8, crystal2)
    # ------------------------------------------------------------------ the head: a massive maw
    head = r.bone('head', body, (0, -7.0, -12.0), anim='head')
    H = lambda x, y, z: (x, y, z)
    for i in range(6):                                                                              # the skull to a pointed snout
        t0, t1 = i / 6, (i + 1) / 6
        tm = (t0 + t1) / 2
        w = 20.0 - 9.0 * tm ** 1.2
        top = -18.5 + 8.5 * tm ** 1.3
        z0, z1 = -9.0 - 22.0 * t0 + (0.6 if i else 0), -9.0 - 22.0 * t1
        rseg(head, V(0, (top - 5.0) / 2, z0), V(0, (top - 5.0) / 2, z1), w, -5.0 - top, vein_hide, up=(0, -1, 0), bevel=min(3.0, w * 0.18))
    CI.box(head, (-9.4, -5.2, -30.0), (9.4, -5.0, -9.0), mouth)                                    # the palate
    for sx in (-1, 1):
        CI.box(head, (sx * 3.0, -20.0, -23.0), (sx * 10.6, -16.5, -13.0), crystal, rot=(0.2, 0, sx * 0.1), pivot=(sx * 7.0, -18.0, -13.0))  # brow
        CI.cbox(head, (sx * 10.1, -13.0, -18.5), (0.4, 2.6, 4.2), M('energy', '#bff6ff', glow=True))          # a glowing eye
        CI.cbox(head, (sx * 10.2, -13.0, -18.5), (0.4, 1.2, 1.6), M('energy', '#4fb8ff', glow=True))
        # long teeth hanging along the upper jaw, two rows
        for k in range(9):                                                                          # long uneven fangs, two rows
            z = -29.0 + k * 2.2
            x = sx * (8.6 - max(0.0, -z - 24.0) * 0.6)
            L = (4.2 if k % 2 == 0 else 2.6) * (1.2 if k < 3 else 1.0)
            spike(head, V(x, -5.4, z), V(x - sx * 0.6, -5.0 + L, z - 0.4), 1.5, tooth)
            if k % 2:
                spike(head, V(x - sx * 2.0, -5.4, z + 0.8), V(x - sx * 2.3, -5.0 + L * 0.7, z + 0.5), 1.1, tooth)
        # gill slits behind the jaw
        for g in range(3):
            CI.box(head, (sx * 10.05 - 0.1, -12.0 + g * 0.4, -9.0 + g * 1.8), (sx * 10.05 + 0.1, -6.0, -8.4 + g * 1.8), vein)
    for k in range(5):
        x = -4.0 + k * 2.0
        spike(head, V(x, -5.4, -30.6), V(x * 1.1, -5.0 + (3.6 if k % 2 == 0 else 2.4), -31.2), 1.5, tooth)
    # the rune ring on its crown
    CI.hoop(head, (0, -18.1, -18.0), 3.2, 0.5, vein, axis='y', n=20)
    CI.seg(head, (0, -18.15, -22.5), (0, -18.15, -13.5), 0.4, 0.4, vein, up=(0, -1, 0))
    jaw = r.bone('jaw', head, (0, -5.0, -9.0), rot=(0.55, 0, 0), anim='jaw')
    CI.rbox(jaw, (-9.0, -5.0, -29.0), (9.0, 1.5, -8.0), vein_hide, bevel=2.0)
    CI.box(jaw, (-6.5, 1.3, -26.0), (6.5, 1.7, -9.0), belly)                                       # pale under the jaw
    CI.box(jaw, (-8.0, -5.1, -28.0), (8.0, -4.9, -9.0), mouth)
    for sx in (-1, 1):
        for k in range(8):
            z = -27.5 + k * 2.3
            x = sx * (7.8 - max(0.0, -z - 23.0) * 0.6)
            L = 3.8 if k % 2 else 2.4
            spike(jaw, V(x, -4.6, z), V(x - sx * 0.5, -4.6 - L, z + 0.4), 1.4, tooth)
        spike(jaw, V(sx * 8.0, 1.0, -14.0), V(sx * 10.5, 5.0, -10.0), 1.6, crystal2)               # spines under the jaw
    for k in range(4):
        x = -3.0 + k * 2.0
        spike(jaw, V(x, -4.6, -28.6), V(x * 1.1, -4.6 - (3.2 if k % 2 == 0 else 2.2), -29.2), 1.4, tooth)
    # ------------------------------------------------------------------ the tail: long and tapering, a forked crescent fin
    def tail_extra(bone, p, q, w, i):
        m = (p + q) / 2
        if i < 4:
            spike(bone, m + V(0, -w * 0.4, 0), m + V(0, -w * 0.4 - (5.0 - i), 3.0), 2.0, crystal if i % 2 else crystal2)
        for sx in (-1, 1):
            if i % 2 == 0:
                spike(bone, m + V(sx * w * 0.42, 0.5, 0), m + V(sx * (w * 0.42 + 2.6), 2.0, 2.5), 1.2, crystal2)
    from dragons_sheet import tail_chain
    last, tip = tail_chain(r, body, (0, -7.5, 21.0), 5, 30.0, 10.0, 3.0, vein_hide, lambda t: 0.0, amp=0.18, extra=tail_extra)
    for sgn in (-1, 1):                                                                             # the crescent's two lobes
        for j in range(6):
            t = j / 5
            ang = math.radians(25 + 40 * t)
            d = V(0, -sgn * math.sin(ang), math.cos(ang))
            L = 16.0 - 6.0 * abs(t - 0.6) * 1.6
            p = tip + V(0, -sgn * t * 1.5, -t * 2.0)
            spike(last, p, p + d * L, 3.6 - t * 1.2, crystal if j % 2 else hide)
            CI.seg(last, tuple(p + d * L * 0.3), tuple(p + d * L * 0.9), 0.35, 0.35, edge, up=(1, 0, 0))
    r.height = 24.0 - (-18.0 - 13.0 - 6.0)
    return r


# ===================================================================================================== Bahamut
@recipe
def bahamut():
    import random
    rnd = random.Random(18)
    r = CI.rig('bahamut', td=1)
    blue = M('scale', '#1c3c80', belly='#1c3c80', scale_size=1.4, contrast=0.55)
    throat = M('scale', '#e6eef8', belly='#e6eef8', scale_size=1.2, contrast=0.35)
    groove = M('simple', '#7fa0d0')
    gold = M('metal', '#d8b060')
    crystal = M('gem', '#5fc8ff', glow=True)
    crystal2 = M('gem', '#2e7fd8', glow=False)
    fcols = [M('scale', '#1e4592', belly='#1e4592', scale_size=1.0, contrast=0.5), M('scale', '#3a6cc0', belly='#3a6cc0', scale_size=1.0, contrast=0.5),
             M('scale', '#8ab0e4', belly='#8ab0e4', scale_size=1.0, contrast=0.4), M('scale', '#e8f0fa', belly='#e8f0fa', scale_size=1.0, contrast=0.3)]
    stone = M('rock', '#7d8890')
    stone2 = M('rock', '#9aa3aa')
    coral = [M('gem', c, glow=False) for c in ('#e060c0', '#9a60e0', '#f080a0', '#40c0e0')]
    kelp = M('leaf', '#2e8a4e')
    water = M('simple', '#6ac8ff')
    lantern = M('energy', '#7fe8ff', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.04)
    body = r.bone('body', root, (0, -8, 0), anim='sway', ax=1, amp=0.03, speed=0.04)
    # ------------------------------------------------------------------ the body: a whale's, deep in front, tapering back;
    # its lower part white and grooved from the chin back (the throat's pleats)
    segs = ((-16.0, 2.0, 24.0, 24.0, -6.0), (0.0, 16.0, 21.0, 21.0, -7.0), (14.0, 28.0, 15.0, 15.0, -8.5))
    for (z0, z1, w, h, y) in segs:
        rseg(body, V(0, y, z0), V(0, y, z1), w, h, blue, up=(0, -1, 0), bevel=5.0)
        hb = h * 0.5
        rseg(body, V(0, y + h / 2 - hb / 2 + 0.2, z0 + 0.5), V(0, y + h / 2 - hb / 2 + 0.2, z1 - 0.5), w + 0.3, hb, throat, up=(0, -1, 0),
             bevel=min(4.0, hb * 0.45))
        for g in range(int(w // 2.4)):                                                                # the grooves underneath
            x = -w / 2 + 1.6 + g * 2.4
            CI.box(body, (x - 0.25, y + h / 2 + 0.1, z0 + 2.0), (x + 0.25, y + h / 2 + 0.35, z1 - 2.0), groove)
        for sx in (-1, 1):                                                                            # and along the flanks' white
            for g in range(3):
                yy = y + h / 2 - hb + 1.5 + g * (hb - 2.5) / 3
                CI.box(body, (sx * (w / 2 + 0.2) - 0.15, yy, z0 + 2.0), (sx * (w / 2 + 0.2) + 0.15, yy + 0.5, z1 - 2.0), groove)
    # gold lines and diamond marks on the flanks (sheet 18's embroidery)
    for sx in (-1, 1):
        for (z0, z1, x, y) in ((-14.0, 2.0, 12.2, -11.0), (2.0, 15.0, 10.7, -11.5), (15.0, 26.0, 7.7, -12.0)):
            CI.box(body, (sx * x - 0.12, y, z0), (sx * x + 0.12, y + 0.6, z1), gold)
        for (z, x, y) in ((-6.0, 12.2, -11.0), (9.0, 10.7, -11.5), (21.0, 7.7, -12.0)):
            CI.cbox(body, (sx * x, y + 0.3, z), (0.5, 3.4, 3.4), gold, rot=(0.785, 0, 0))
            CI.cbox(body, (sx * (x + 0.1), y + 0.3, z), (0.5, 1.8, 1.8), crystal, rot=(0.785, 0, 0))
            CI.box(body, (sx * x - 0.12, y + 0.3, z - 0.3), (sx * x + 0.12, y + 5.0, z + 0.3), gold)
    # ------------------------------------------------------------------ the ruins on its back, coral, kelp, waterfalls
    top = -18.0
    CI.rbox(body, (-8.0, top - 1.5, 0.0), (8.0, top + 0.8, 16.0), stone, bevel=0.8)                    # the temple's floor
    for i, x in enumerate((-6.0, -2.0, 2.0, 6.0)):                                                     # pillars, some broken
        for j, z in enumerate((2.0, 13.0)):
            h = 9.0 if (i + j) % 3 else 5.5
            CI.box(body, (x - 0.8, top - h - 1.5, z - 0.8), (x + 0.8, top - 1.5, z + 0.8), stone2)
            if h > 6:
                CI.box(body, (x - 1.2, top - h - 2.5, z - 1.2), (x + 1.2, top - h - 1.5, z + 1.2), stone)
    for z in (2.0,):                                                                                   # an arch left standing
        CI.box(body, (-7.0, top - 13.0, z - 1.2), (3.0, top - 11.5, z + 1.2), stone)
        for x in (-4.0, 0.0):
            CI.box(body, (x - 1.0, top - 11.5, z - 0.6), (x + 1.0, top - 10.5, z + 0.6), stone2)
    CI.box(body, (-7.0, top - 13.0, 2.0), (-5.0, top - 11.5, 13.0), stone)
    CI.box(body, (-2.5, top - 15.0, 6.0), (2.5, top - 13.0, 10.0), stone2)                             # a broken pediment
    for _ in range(30):                                                                                # coral and kelp
        x, z = rnd.uniform(-10.0, 10.0), rnd.uniform(-12.0, 24.0)
        y = (top - 1.5) if -8 <= x <= 8 and 0 <= z <= 16 else -17.0 + max(0.0, z - 2) * 0.12 + abs(x) * 0.25
        if rnd.random() < 0.55:
            c = coral[rnd.randrange(len(coral))]
            CI.box(body, (x - 0.5, y - 3.0, z - 0.5), (x + 0.5, y, z + 0.5), c)
            CI.box(body, (x - 1.5, y - 2.5, z - 0.4), (x - 0.5, y - 1.7, z + 0.4), c)
            CI.box(body, (x + 0.5, y - 3.6, z - 0.4), (x + 1.5, y - 2.8, z + 0.4), c)
        else:
            h = rnd.uniform(4.0, 10.0)
            CI.box(body, (x - 0.4, y - h, z - 0.4), (x + 0.4, y, z + 0.4), kelp)
    for sx in (-1, 1):                                                                                 # kelp hanging down the flanks
        for k in range(9):
            z = -10.0 + k * 3.6 + rnd.uniform(-1, 1)
            x = sx * (12.3 if z < 2 else (10.8 if z < 15 else 7.9))
            L = rnd.uniform(5.0, 14.0)
            CI.box(body, (x - 0.4, -15.0, z - 0.4), (x + 0.4, -15.0 + L, z + 0.4), kelp)
        for z in (5.0, 10.0):                                                                          # waterfalls down the flanks
            x = sx * 10.9
            CI.box(body, (x - 0.3, top + 0.5, z - 1.5), (x + 0.3, top + 15.0, z + 1.5), water)
    # ------------------------------------------------------------------ the pectoral fins: long feathered wings, lanterns
    for sx in (-1, 1):
        base = V(sx * 11.5, 4.0, -9.0)
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, tuple(base), anim='sway', ax=2, amp=0.1, speed=0.05)
        feather_plane(fb, base, V(sx * 0.35, 0.8, 0.5), V(sx * 0.12, -0.35, 1.0), 12, 38.0,
                      lambda t: 10.0 + 12.0 * math.sin(min(1.0, t * 1.15) * math.pi * 0.9), 3.8, fcols, edge=gold, lantern=lantern, every=4)
    # ------------------------------------------------------------------ the head: long, rounded, white below; the crown
    head = r.bone('head', body, (0, -6.0, -16.0), anim='head')
    for i in range(6):                                                                                  # slices narrowing and lowering forward
        t0, t1 = i / 6, (i + 1) / 6
        tm = (t0 + t1) / 2
        w = 22.0 - 8.0 * tm ** 1.3
        top = -17.0 + 9.0 * tm ** 1.4
        z0, z1 = -14.0 - 26.0 * t0 + (0.6 if i else 0), -14.0 - 26.0 * t1
        rseg(head, V(0, (top + 1.0) / 2, z0), V(0, (top + 1.0) / 2, z1), w, 1.0 - top, blue, up=(0, -1, 0), bevel=min(4.0, w * 0.2))
    for sx in (-1, 1):
        CI.eye(head, (sx * 10.6, -7.0, -22.0), 3.0, 1.6, 'left' if sx > 0 else 'right',
               M('eye', '#7fe0ff', pupil='round', mood='calm', lid='#1c3c80', glow_amount=0.6))
        CI.box(head, (sx * 10.7 - 0.12, -11.0, -30.0), (sx * 10.7 + 0.12, -10.4, -16.0), gold)
        CI.cbox(head, (sx * 10.7, -10.7, -26.0), (0.5, 3.0, 3.0), gold, rot=(0.785, 0, 0))
    # the crown: blue crystals and gold blades leaning back in a ring over the back of the head
    for k in range(13):
        a = math.pi * k / 12
        x, z = -math.cos(a) * 8.5, -18.0 - math.sin(a) * 2.5
        h = 5.0 + 6.0 * math.sin(a) ** 2
        lean = V(x * 0.1, -1.0, 0.75)
        spike(head, V(x, -15.5, z), V(x, -15.5, z) + lean / np.linalg.norm(lean) * h, 2.6, (crystal, gold, crystal2)[k % 3])
    CI.box(head, (-9.0, -17.4, -20.0), (9.0, -16.0, -17.0), gold)
    CI.cbox(head, (0, -17.8, -21.5), (3.0, 3.6, 1.2), crystal, rot=(0, 0, 0.785))
    jaw = r.bone('jaw', head, (0, 1.0, -14.0), rot=(0.0, 0, 0), anim='jaw')
    CI.rbox(jaw, (-10.6, 0.0, -38.5), (10.6, 7.0, -14.0), throat, bevel=3.2)
    for g in range(8):                                                                                 # the throat's grooves
        x = -8.4 + g * 2.4
        CI.box(jaw, (x - 0.25, 6.95, -35.0), (x + 0.25, 7.2, -15.0), groove)
    for sx in (-1, 1):
        for g in range(3):
            CI.box(jaw, (sx * 10.65 - 0.15, 1.5 + g * 1.8, -35.0), (sx * 10.65 + 0.15, 2.0 + g * 1.8, -15.0), groove)
    # ------------------------------------------------------------------ the tail: tapering to feathered flukes
    from dragons_sheet import tail_chain
    last, tip = tail_chain(r, body, (0, -8.5, 27.0), 3, 20.0, 12.0, 5.0, blue, lambda t: -0.6 * t, amp=0.12)
    for sx in (-1, 1):
        feather_plane(last, tip - V(0, 0, 2.0), V(sx * 1.0, -0.55, 0.35), V(0, 0, 1.0), 9, 18.0,
                      lambda t: 7.0 + 9.0 * math.sin(t * math.pi * 0.85), 3.2, fcols, edge=gold, curve=0.0)
    r.height = 24.0 - (-18.0 - 15.0 - 6.0)
    return r
