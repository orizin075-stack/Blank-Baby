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


# ===================================================================================================== hulls

def profile(keys):
    """(z, w, h, y) keys, z ascending: the hull's width, height and centre at any z, eased between keys."""
    ks = sorted(keys)

    def at(z):
        if z <= ks[0][0]:
            return ks[0][1:]
        for (z0, *a), (z1, *b) in zip(ks, ks[1:]):
            if z <= z1:
                t = (z - z0) / (z1 - z0)
                t = t * t * (3 - 2 * t)
                return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
        return ks[-1][1:]
    return at


def hull(prof, z0, z1, dz, bone_at, top, belly, belly_frac, jaw=None):
    """A smooth body of slices dz long from z0 to z1 (each a bevelled box, rounder where it is small), dark above and
    pale below (the countershading of a shark or a whale). bone_at(z) gives each slice's bone. jaw = (z_from, z_to,
    frac, bone, mat): there the lower `frac` of each slice belongs to the jaw bone."""
    z = z0
    while z < z1 - 1e-6:
        zz = min(z1, z + dz)
        w, h, y = prof((z + zz) / 2)
        b = bone_at((z + zz) / 2)
        bev = min(w, h) * 0.34
        p0, p1 = V(0, y, z), V(0, y, zz + 0.25)
        if jaw is not None and jaw[0] <= (z + zz) / 2 <= jaw[1]:
            jf = jaw[2]
            hu = h * (1 - jf)
            yu = y - h / 2 + hu / 2
            rseg(b, V(0, yu, z), V(0, yu, zz + 0.25), w, hu, top, up=(0, -1, 0), bevel=min(bev, hu * 0.45))
            hl = h * jf
            yl = y + h / 2 - hl / 2
            rseg(jaw[3], V(0, yl, z), V(0, yl, zz + 0.25), w * 0.94, hl, jaw[4], up=(0, -1, 0), bevel=min(bev, hl * 0.45))
        else:
            rseg(b, p0, p1, w, h, top, up=(0, -1, 0), bevel=bev)
            if belly is not None:
                hb = h * belly_frac
                yb = y + h / 2 - hb / 2 + 0.12
                rseg(b, V(0, yb, z + 0.05), V(0, yb, zz + 0.2), w + 0.25, hb, belly, up=(0, -1, 0), bevel=min(bev, hb * 0.45))
        z = zz


def plate_fin(bone, root, A, B, span, n, chord, sweep, mat, edge=None, thick=1.0, jag=0.0, tip_mats=None):
    """A flat fin of strips: along A (the span) n strips, each running back along B for chord(t), set back by sweep(t);
    a glowing line along the leading edge; jag makes the trailing edge saw-toothed (a crystal fin)."""
    A = np.asarray(A, float); A = A / np.linalg.norm(A)
    B = np.asarray(B, float); B = B - (B @ A) * A; B = B / np.linalg.norm(B)
    N = np.cross(A, B)
    root = np.asarray(root, float)
    lead = []
    for i in range(n):
        t = (i + 0.5) / n
        p = root + A * (span * t) + B * sweep(t)
        L = chord(t) + (jag if i % 2 else -jag * 0.3)
        if L <= 0.3:
            continue
        m = mat if tip_mats is None or t < 0.7 else tip_mats[i % len(tip_mats)]
        CI.seg(bone, tuple(p), tuple(p + B * L), span / n * 1.25, thick * (1.0 - 0.5 * t), m, up=tuple(N))
        lead.append(p)
    if edge is not None and len(lead) > 1:
        for p, q in zip(lead, lead[1:]):
            CI.seg(bone, tuple(p - B * 0.2), tuple(q - B * 0.2), 0.5, thick * 0.9, edge, up=tuple(N), ext=0.3)
    return N


# ===================================================================================================== Enkou
@recipe
def enkou():
    """淵煌 as a shark (the user: "怪獣は化け物すぎる この子のモデルサメよ", "もうちょい凝って"): a streamlined body from a
    pointed snout to a crescent tail, dark navy above and pale below; the mouth under the snout, a little open on rows
    of white triangular teeth; a small glowing eye; five gill slits; one tall dorsal fin with a crystal edge and a saw
    of shards on its trailing edge, a small second dorsal, long sickle pectoral fins, pelvic and anal fins; the tail's
    upper lobe longer; sheet 15's marks kept: the rune ring on its crown, branching veins of light, crystal shards
    along its back toward the tail."""
    import random
    rnd = random.Random(15)
    r = CI.rig('enkou', td=1)
    hide = M('scale', '#1a2440', belly='#1a2440', scale_size=0.9, contrast=0.9)
    belly = M('scale', '#c9d2de', belly='#c9d2de', scale_size=1.2, contrast=0.35)
    fin = M('scale', '#162038', belly='#162038', scale_size=0.8, contrast=0.8)
    crystal = M('gem', '#3a5688', glow=False)
    crystal2 = M('gem', '#6a90c8', glow=False)
    edge = M('energy', '#8fd0ff', glow=True)
    vein = M('energy', '#7ab8f0', glow=True)
    tooth = M('tooth', '#f2f4f8')
    mouth = M('simple', '#1a0c18')
    gill = M('simple', '#0a0e1a')
    prof = profile([(-37, 6.0, 5.5, -8.4), (-33, 11.5, 10.0, -8.8), (-26, 15.5, 14.0, -9.4), (-18, 18.5, 17.0, -9.8), (-8, 20.0, 18.5, -10.0),
                    (4, 18.0, 17.0, -10.0), (14, 15.0, 13.5, -10.0), (22, 11.0, 9.5, -10.0), (30, 7.0, 6.0, -10.0), (36, 4.6, 4.4, -10.0),
                    (41, 3.6, 3.8, -10.0)])
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.5, speed=0.05)
    body = r.bone('body', root, (0, -10, 0), anim='sway', ax=1, amp=0.05, speed=0.06)
    head = r.bone('head', body, (0, -10, -16), anim='head')
    w_m, h_m, y_m = prof(-17)
    jaw = r.bone('jaw', head, (0, y_m + h_m * 0.22, -17), rot=(0.42, 0, 0), anim='jaw')
    tails, prev = [], body
    for i, zt in enumerate((8.0, 18.0, 27.0, 35.0)):
        prev = r.bone(f'tail{i + 1}', prev, (0, -10, zt), anim='tail', i=i, amp=0.14, speed=0.08)
        tails.append((zt, prev))

    def bone_at(z):
        if z < -16:
            return head
        b = body
        for zt, tb in tails:
            if z >= zt:
                b = tb
        return b
    # ------------------------------------------------------------------ the hull, the mouth under the snout
    hull(prof, -37.0, 41.0, 2.0, bone_at, hide, belly, 0.42, jaw=(-33.0, -16.0, 0.34, jaw, belly))
    zm0, zm1 = -33.0, -16.5
    for z in np.arange(zm0, zm1, 1.5):                                                           # the mouth's dark inside
        w, h, y = prof(z + 0.75)
        ym = y + h / 2 - h * 0.34
        CI.box(head, (-w * 0.42, ym - 0.15, z), (w * 0.42, ym + 0.05, z + 1.6), mouth)
        CI.box(jaw, (-w * 0.4, ym - 0.05, z), (w * 0.4, ym + 0.15, z + 1.6), mouth)
    for side in (-1, 1):                                                                           # rows of long uneven fangs
        for kk in range(11):
            z = zm0 + 0.8 + kk * 1.45
            w, h, y = prof(z)
            ym = y + h / 2 - h * 0.34
            x = side * (w * 0.42 - 0.4)
            L = (3.6 if kk % 2 == 0 else 2.2) * (1.25 if kk in (1, 2, 3) else 1.0)
            spike(head, V(x, ym - 0.2, z), V(x - side * 0.4, ym + L, z - 0.3), 1.3, tooth)
            spike(jaw, V(x * 0.95, ym + 0.2, z + 0.7), V(x * 0.95 - side * 0.3, ym - L * 0.85, z + 0.9), 1.2, tooth)
            if kk % 2 == 1 and kk < 9:
                spike(head, V(x - side * 1.8, ym - 0.2, z + 0.5), V(x - side * 2.0, ym + L * 0.6, z + 0.3), 0.9, tooth)
    for kk in range(5):                                                                            # and across the front
        x = -3.2 + kk * 1.6
        w, h, y = prof(zm0 + 0.3)
        ym = y + h / 2 - h * 0.34
        L = 3.2 if kk % 2 == 0 else 2.2
        spike(head, V(x, ym - 0.2, zm0 + 0.4), V(x * 1.1, ym + L, zm0 + 0.1), 1.2, tooth)
        spike(jaw, V(x * 0.9, ym + 0.2, zm0 + 1.0), V(x, ym - L * 0.8, zm0 + 0.7), 1.1, tooth)
    # ------------------------------------------------------------------ eyes, gills, the rune ring, veins of light
    for sx in (-1, 1):
        w, h, y = prof(-26.0)
        CI.cbox(head, (sx * (w / 2 - 0.25), y - h * 0.12, -26.0), (0.5, 2.6, 3.4), M('simple', '#070a14'))
        CI.cbox(head, (sx * (w / 2 - 0.15), y - h * 0.12, -26.0), (0.5, 1.8, 2.4), M('energy', '#c8f8ff', glow=True))
        CI.cbox(head, (sx * (w / 2 - 0.05), y - h * 0.12, -25.8), (0.5, 0.9, 1.0), M('energy', '#3aa0ff', glow=True))
        bx = sx * (w / 2 - 1.2)
        CI.seg(head, (bx, y - h * 0.12 - 1.6, -29.5), (bx + sx * 0.6, y - h * 0.12 - 2.4, -22.0), 2.4, 1.6, crystal, up=(0, -1, 0))  # a heavy brow
        for j, (dz, L) in enumerate(((-18.5, 5.0), (-16.5, 4.0), (-14.5, 3.0))):                    # spines swept back from the cheeks
            wc, hc, yc = prof(dz)
            spike(head if dz < -16 else body, V(sx * (wc / 2 - 0.4), yc - hc * 0.05, dz), V(sx * (wc / 2 + 2.2), yc - hc * 0.05 - 1.0, dz + L), 1.6, crystal2)
        wj, hj, yj = prof(-24.0)
        spike(jaw, V(sx * (wj * 0.4), yj + hj / 2 - 0.5, -24.0), V(sx * (wj * 0.4 + 2.0), yj + hj / 2 + 2.6, -20.0), 1.6, crystal)  # under the jaw
        for g in range(5):                                                                         # gill slits
            z = -14.5 + g * 1.5
            w, h, y = prof(z)
            x = sx * (w / 2 + 0.05)
            CI.box(body, (x - 0.12, y - h * 0.22, z), (x + 0.12, y + h * 0.18, z + 0.45), gill)
            CI.box(body, (x - 0.13, y - h * 0.22, z + 0.45), (x + 0.13, y + h * 0.18, z + 0.6), vein)
        p = None
        for (y0, z0, n) in ((-15.0, -12.0, 10), (-9.0, -6.0, 8), (-14.0, 8.0, 7), (-11.0, -26.0, 4), (-7.0, 18.0, 5)):   # branching veins
            p = V(0, y0, z0)
            for k in range(n):
                q = p + V(0, rnd.uniform(-1.8, 1.8), rnd.uniform(1.8, 3.2))
                w, h, y = prof(q[2])
                q[1] = min(max(q[1], y - h * 0.42), y + h * 0.05)
                q[0] = sx * (w / 2 + 0.06)
                pp = V(sx * (prof(p[2])[0] / 2 + 0.06), p[1], p[2])
                CI.seg(bone_at(p[2]), tuple(pp), tuple(q), 0.12, 0.35, vein, up=(sx, 0, 0))
                if rnd.random() < 0.3:
                    bq = q + V(0, rnd.choice((-1, 1)) * rnd.uniform(1.2, 2.4), rnd.uniform(0.6, 1.6))
                    bq[0] = q[0]
                    CI.seg(bone_at(q[2]), tuple(q), tuple(bq), 0.12, 0.35, vein, up=(sx, 0, 0))
                p = q
    fleck = M('scale', '#5a7ab0', belly='#5a7ab0', scale_size=0.6, contrast=0.5)
    for _ in range(24):
        z = rnd.uniform(-30.0, 38.0)
        w, h, y = prof(z)
        sx = rnd.choice((-1, 1))
        yy = rnd.uniform(y - h * 0.48, y + h * 0.05)
        top_side = yy < y - h * 0.38
        if top_side:
            CI.box(bone_at(z), (rnd.uniform(-w * 0.3, w * 0.3) - 0.4, y - h / 2 - 0.12, z - 0.5), (rnd.uniform(-w * 0.3, w * 0.3) + 0.4, y - h / 2 + 0.1, z + 0.5), fleck)
        else:
            x = sx * (w / 2 + 0.03)
            CI.box(bone_at(z), (x - 0.1, yy - 0.4, z - 0.6), (x + 0.1, yy + 0.4, z + 0.6), fleck)
    w, h, y = prof(-22.0)
    CI.hoop(head, (0, y - h / 2 - 0.05, -22.0), 2.6, 0.4, vein, axis='y', n=20)
    CI.seg(head, (0, y - h / 2 - 0.08, -25.6), (0, y - h / 2 - 0.08, -18.4), 0.35, 0.3, vein, up=(0, -1, 0))
    CI.seg(head, (-3.6, y - h / 2 - 0.08, -22.0), (3.6, y - h / 2 - 0.08, -22.0), 0.35, 0.3, vein, up=(0, -1, 0))
    # ------------------------------------------------------------------ the fins
    w, h, y = prof(0.0)
    top = y - h / 2
    H = 15.0
    for k in range(int(H)):                                                                         # the dorsal fin, strip by strip
        t = k / H
        zf = -6.0 + 13.0 * t ** 0.85
        zb = 9.0 - 4.5 * math.sin(math.pi * t) - 2.5 * t + (0.8 if k % 2 else -0.4) * (t > 0.25)
        if zb - zf < 0.6:
            zb = zf + 0.6
        th = 1.8 - 1.0 * t
        CI.box(body, (-th / 2, top - k - 1.05, zf), (th / 2, top - k + 0.4, zb), crystal if (k // 3) % 2 else fin)
        CI.box(body, (-th / 2 - 0.1, top - k - 1.05, zf - 0.5), (th / 2 + 0.1, top - k + 0.4, zf), edge)
    w2, h2, y2 = prof(25.0)
    for k in range(5):                                                                              # the second dorsal
        t = k / 5
        CI.box(tails[1][1], (-0.5, y2 - h2 / 2 - k - 1.0, 23.0 + 3.0 * t), (0.5, y2 - h2 / 2 - k + 0.3, 27.0 - 1.0 * t), fin)
    for (z, hh, lean) in ((-20.0, 6.0, 0.7), (-15.0, 8.0, 0.65), (-10.0, 7.0, 0.6), (12.0, 7.5, 0.7), (16.5, 6.0, 0.7), (21.0, 4.5, 0.75),
                          (30.0, 4.0, 0.8), (33.5, 3.2, 0.8)):                                         # crystal blades along the back
        wz, hz, yz = prof(z)
        base = V(0, yz - hz / 2 + 0.6, z)
        tip = base + V(0, -hh, hh * lean)
        bb = bone_at(z)
        CI.seg(bb, tuple(base), tuple(base + (tip - base) * 0.55), 3.4, 1.2, crystal if int(z) % 2 else crystal2, up=(1, 0, 0), ext=0.3)
        CI.seg(bb, tuple(base + (tip - base) * 0.55), tuple(tip), 1.6, 1.0, crystal2, up=(1, 0, 0), ext=0.2)
        CI.seg(bb, tuple(base + (tip - base) * 0.25), tuple(tip), 0.4, 1.2, edge, up=(1, 0, 0))
    for sx in (-1, 1):
        w, h, y = prof(-10.0)
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, (sx * (w / 2 - 1.0), y + h * 0.18, -10.0), anim='sway', ax=2, amp=0.12, speed=0.08)
        plate_fin(fb, V(sx * (w / 2 - 1.0), y + h * 0.18, -11.0), V(sx * 0.55, 0.8, 0.3), V(0, 0.05, 1.0), 18.0, 13,
                  lambda t: 10.0 * (1 - t) ** 0.75 + 1.2, lambda t: 7.0 * t ** 1.3, fin, edge=edge, thick=1.3, jag=1.8,
                  tip_mats=[crystal, crystal2])
        w, h, y = prof(16.0)                                                                       # pelvic fins
        plate_fin(tails[0][1], V(sx * (w / 2 - 1.5), y + h / 2 - 1.0, 15.0), V(sx * 0.6, 0.8, 0.3), V(0, 0.2, 1.0), 6.0, 5,
                  lambda t: 4.0 * (1 - t) + 0.8, lambda t: 2.5 * t, fin, thick=0.9)
    w, h, y = prof(29.0)                                                                           # the anal fin
    for k in range(4):
        CI.box(tails[2][1], (-0.4, y + h / 2 + k - 0.2, 28.0 + k * 0.6), (0.4, y + h / 2 + k + 0.8, 31.0 - k * 0.2), fin)
    # the tail: a crescent, the upper lobe longer, crystal shards on its trailing edge
    tb = tails[3][1]
    plate_fin(tb, V(0, -11.0, 38.0), V(0, -0.85, 0.55), V(0, 0.2, 1.0), 21.0, 13, lambda t: 10.0 * (1 - t) ** 0.8 + 1.0,
              lambda t: 1.0 * t, fin, edge=edge, thick=1.4, jag=2.0, tip_mats=[crystal, crystal2])
    plate_fin(tb, V(0, -8.5, 38.0), V(0, 0.8, 0.5), V(0, -0.15, 1.0), 13.0, 9, lambda t: 8.0 * (1 - t) ** 0.8 + 1.0,
              lambda t: 0.5 * t, fin, edge=edge, thick=1.4, jag=1.6, tip_mats=[crystal2, crystal])
    r.height = 24.0 - (top - H)
    r.palette = True                    # 256-colour texture (build_bb.save_palette)
    return r


# ===================================================================================================== Bahamut
@recipe
def bahamut():
    """バハムート (sheet 18; "もうちょい凝って"): a humpback on a smooth hull - a long head blunt at the snout with knobs
    (tubercles) along it, the deepest body behind the fins, tapering to the flukes; deep blue above, white below
    with the grooves of a humpback's throat running from the chin to the navel; gold embroidery along the line
    between them, gold and crystal diamonds, a gold circlet round the eye; a crown of crystal and gold blades at the
    back of the head; pectoral fins as long as the body, feathered blue to white with a gold edge and lanterns on
    chains; a small dorsal hump; on its back the ruins of a temple (pillars, an arch, a broken pediment, steps) among
    coral, sea grass and kelp, two waterfalls running down its flanks; flukes feathered like the fins."""
    import random
    rnd = random.Random(18)
    r = CI.rig('bahamut', td=1)
    blue = M('scale', '#1d3e86', belly='#1d3e86', scale_size=1.2, contrast=0.6)
    deep = M('scale', '#152f68', belly='#152f68', scale_size=1.2, contrast=0.6)
    throat = M('scale', '#e9f0f8', belly='#e9f0f8', scale_size=1.1, contrast=0.3)
    groove = M('simple', '#8aa8d4')
    gold = M('metal', '#d8b060')
    crystal = M('gem', '#5fc8ff', glow=True)
    crystal2 = M('gem', '#2e7fd8', glow=False)
    knob = M('scale', '#2a54a8', belly='#2a54a8', scale_size=0.8, contrast=0.4)
    fcols = [M('scale', '#1e4592', belly='#1e4592', scale_size=1.0, contrast=0.5), M('scale', '#3a6cc0', belly='#3a6cc0', scale_size=1.0, contrast=0.5),
             M('scale', '#8ab0e4', belly='#8ab0e4', scale_size=1.0, contrast=0.4), M('scale', '#eef4fb', belly='#eef4fb', scale_size=1.0, contrast=0.3)]
    stone = M('rock', '#7d8890')
    stone2 = M('rock', '#9aa3aa')
    moss = M('leaf', '#3e8a52')
    coral = [M('gem', c, glow=False) for c in ('#e060c0', '#9a60e0', '#f080a0', '#40c0e0', '#ff9a60')]
    kelp = M('leaf', '#2e8a4e')
    kelp2 = M('leaf', '#4aa860')
    water = M('simple', '#6ac8ff')
    foam = M('simple', '#dff2ff')
    lantern = M('energy', '#7fe8ff', glow=True)
    prof = profile([(-46, 9.0, 8.0, -6.5), (-42, 16.0, 13.5, -6.8), (-34, 21.0, 19.0, -7.2), (-22, 24.5, 23.5, -7.6), (-8, 26.0, 25.0, -8.0),
                    (6, 23.5, 22.0, -8.5), (18, 18.0, 16.5, -9.0), (28, 12.0, 10.5, -9.5), (37, 7.0, 6.0, -9.8), (44, 5.0, 4.4, -10.0)])
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.04)
    body = r.bone('body', root, (0, -8, 0), anim='sway', ax=1, amp=0.03, speed=0.04)
    head = r.bone('head', body, (0, -7.6, -20), anim='head')
    w_j, h_j, y_j = prof(-21.0)
    jaw = r.bone('jaw', head, (0, y_j + h_j * 0.1, -21.0), rot=(0.0, 0, 0), anim='jaw')
    tails, prev = [], body
    for i, zt in enumerate((18.0, 28.0, 37.0)):
        prev = r.bone(f'tail{i + 1}', prev, (0, -9, zt), anim='tail', i=i, amp=0.12, speed=0.04)
        tails.append((zt, prev))

    def bone_at(z):
        if z < -20:
            return head
        b = body
        for zt, tb in tails:
            if z >= zt:
                b = tb
        return b
    # ------------------------------------------------------------------ the hull: blue above, the white grooved belly
    hull(prof, -46.0, 45.0, 2.0, bone_at, blue, throat, 0.48, jaw=(-45.0, -20.0, 0.42, jaw, throat))
    # the grooves: long lines under the throat and along the white flanks, each a few long pieces following the hull
    zs = list(np.arange(-44.0, 12.1, 4.0))
    for a_, b_ in zip(zs, zs[1:]):
        w0, h0, y0 = prof(a_)
        w1, h1, y1 = prof(b_)
        bb = jaw if b_ <= -20 else bone_at(a_)
        for g in range(7):
            f = -0.33 + g * 0.11
            CI.seg(bb, (w0 * f, y0 + h0 / 2 + 0.16, a_), (w1 * f, y1 + h1 / 2 + 0.16, b_), 0.45, 0.25, groove, up=(0, 1, 0), ext=0.1)
        for sx in (-1, 1):
            for g in range(4):
                fy = 0.04 + g * 0.11
                CI.seg(bb, (sx * (w0 / 2 + 0.16), y0 + h0 * fy, a_), (sx * (w1 / 2 + 0.16), y1 + h1 * fy, b_), 0.45, 0.25, groove,
                       up=(sx, 0, 0), ext=0.1)
    # gold embroidery along the line between the blue and the white, and diamonds
    for sx in (-1, 1):
        pts = []
        for z in np.arange(-40.0, 36.0, 2.0):
            w, h, y = prof(z)
            pts.append(V(sx * (w / 2 + 0.2), y + h / 2 - h * 0.48 - 0.4, z))
        for p, q in zip(pts, pts[1:]):
            CI.seg(bone_at(p[2]) if p[2] >= -20 else head, tuple(p), tuple(q), 0.2, 0.7, gold, up=(sx, 0, 0), ext=0.2)
        for z in (-30.0, -12.0, 2.0, 16.0, 28.0):
            w, h, y = prof(z)
            c = V(sx * (w / 2 + 0.2), y - h * 0.12, z)
            b = bone_at(z)
            CI.cbox(b, tuple(c), (0.5, 3.6, 3.6), gold, rot=(0.785, 0, 0))
            CI.cbox(b, tuple(c + V(sx * 0.1, 0, 0)), (0.5, 2.0, 2.0), crystal, rot=(0.785, 0, 0))
            for d in (-1, 1):                                                                         # the motif's arms
                CI.seg(b, tuple(c + V(0, 0, d * 2.4)), tuple(c + V(0, -1.6, d * 5.5)), 0.2, 0.6, gold, up=(sx, 0, 0))
                CI.seg(b, tuple(c + V(0, 0, d * 2.4)), tuple(c + V(0, 1.6, d * 5.5)), 0.2, 0.6, gold, up=(sx, 0, 0))
    # tubercles along the head's top and the jaw's line
    for z in np.arange(-45.0, -26.0, 2.6):
        w, h, y = prof(z)
        for x in (-w * 0.22, 0.0, w * 0.22):
            CI.cbox(head, (x + rnd.uniform(-0.4, 0.4), y - h / 2 - 0.3, z + rnd.uniform(-0.4, 0.4)), (1.2, 0.9, 1.2), knob)
    # the eye with a gold circlet
    for sx in (-1, 1):
        w, h, y = prof(-26.0)
        ey = y + h * 0.05
        CI.cbox(head, (sx * (w / 2 - 0.1), ey, -26.0), (0.5, 1.8, 2.6), M('simple', '#0c1430'))
        CI.cbox(head, (sx * (w / 2), ey, -26.0), (0.5, 1.0, 1.4), M('energy', '#9fe8ff', glow=True))
        for k in range(10):
            a0, a1 = 2 * math.pi * k / 10, 2 * math.pi * (k + 1) / 10
            p0 = V(sx * (w / 2 + 0.15), ey + math.sin(a0) * 2.0, -26.0 + math.cos(a0) * 2.6)
            p1 = V(sx * (w / 2 + 0.15), ey + math.sin(a1) * 2.0, -26.0 + math.cos(a1) * 2.6)
            CI.seg(head, tuple(p0), tuple(p1), 0.2, 0.5, gold, up=(sx, 0, 0), ext=0.2)
        CI.seg(head, (sx * (w / 2 + 0.15), ey, -28.6), (sx * (prof(-38)[0] / 2 + 0.15), ey + 1.0, -38.0), 0.2, 0.5, gold, up=(sx, 0, 0))
    # ------------------------------------------------------------------ the crown at the back of the head
    w, h, y = prof(-22.0)
    ct = y - h / 2
    for k in range(15):
        a = math.pi * k / 14
        x, z = -math.cos(a) * (w * 0.36), -22.0 - math.sin(a) * 3.0
        hh = 4.5 + 7.5 * math.sin(a) ** 2 + (1.5 if k % 2 == 0 else 0.0)
        lean = V(x * 0.08, -1.0, 0.7)
        mat = (crystal, gold, crystal2)[k % 3]
        spike(head, V(x, ct + 0.8, z), V(x, ct + 0.8, z) + lean / np.linalg.norm(lean) * hh, 2.6 if k % 3 != 1 else 1.8, mat)
    CI.box(head, (-w * 0.38, ct - 0.6, -23.5), (w * 0.38, ct + 0.6, -20.5), gold)
    CI.cbox(head, (0, ct - 1.8, -25.6), (3.2, 3.8, 1.2), crystal, rot=(0, 0, 0.785))
    CI.cbox(head, (0, ct - 1.8, -25.4), (4.6, 5.2, 0.8), gold, rot=(0, 0, 0.785))
    # ------------------------------------------------------------------ the dorsal hump, the ruins, coral, kelp, waterfalls
    w, h, y = prof(24.0)
    for k in range(4):
        CI.box(tails[0][1], (-0.8, y - h / 2 - k - 0.8, 22.5 + k * 0.8), (0.8, y - h / 2 - k + 0.4, 27.0 - k * 0.3), blue)
    w, h, y = prof(4.0)
    top = y - h / 2 + 0.6
    CI.rbox(body, (-8.5, top - 1.6, -4.0), (8.5, top + 0.6, 14.0), stone, bevel=0.8)                      # the temple's floor
    for k in range(3):                                                                                   # steps down its front
        CI.box(body, (-4.0 + k * 0.6, top - 1.0 + k * 0.6, -5.0 - k * 1.2), (4.0 - k * 0.6, top - 0.4 + k * 0.6, -4.0 - k * 1.2), stone2)
    for i, x in enumerate((-6.5, -2.2, 2.2, 6.5)):                                                       # pillars, some broken
        for j, z in enumerate((-1.5, 11.5)):
            hh = 9.5 if (i + j) % 3 else 5.0
            CI.box(body, (x - 0.8, top - hh - 1.6, z - 0.8), (x + 0.8, top - 1.6, z + 0.8), stone2)
            CI.box(body, (x - 1.1, top - 2.4, z - 1.1), (x + 1.1, top - 1.6, z + 1.1), stone)              # the base
            if hh > 6:
                CI.box(body, (x - 1.2, top - hh - 2.6, z - 1.2), (x + 1.2, top - hh - 1.6, z + 1.2), stone)  # the capital
            CI.box(body, (x - 0.85, top - hh * 0.5 - 1.6, z - 0.85), (x + 0.85, top - hh * 0.5 - 1.2, z + 0.85), moss)
    z = -1.5                                                                                             # an arch left standing
    CI.box(body, (-7.7, top - 12.6, z - 1.2), (3.4, top - 11.0, z + 1.2), stone)
    for x in (-4.35, 0.0):
        for k in range(3):
            CI.box(body, (x - 1.4 + k * 0.4, top - 11.0 + k * 0.5, z - 0.6), (x + 1.4 - k * 0.4, top - 10.5 + k * 0.5, z + 0.6), stone2)
    CI.box(body, (-7.7, top - 12.6, -1.5), (-5.3, top - 11.0, 11.5), stone)
    CI.box(body, (-2.5, top - 14.6, 4.0), (2.5, top - 12.6, 8.0), stone2)                                 # a broken pediment
    CI.box(body, (-1.5, top - 15.6, 5.0), (1.5, top - 14.6, 7.0), stone2)
    for _ in range(46):                                                                                  # coral and sea grass
        z = rnd.uniform(-14.0, 30.0)
        w, h, y = prof(z)
        x = rnd.uniform(-w * 0.32, w * 0.32)
        yb = (top - 1.6) if -8.5 <= x <= 8.5 and -4 <= z <= 14 else y - h / 2 + 0.6
        if rnd.random() < 0.5:
            c = coral[rnd.randrange(len(coral))]
            hh = rnd.uniform(2.0, 4.0)
            CI.box(bone_at(z), (x - 0.5, yb - hh, z - 0.5), (x + 0.5, yb, z + 0.5), c)
            CI.box(bone_at(z), (x - 1.6, yb - hh * 0.8, z - 0.4), (x - 0.5, yb - hh * 0.55, z + 0.4), c)
            CI.box(bone_at(z), (x + 0.5, yb - hh * 1.15, z - 0.4), (x + 1.6, yb - hh * 0.9, z + 0.4), c)
            CI.box(bone_at(z), (x - 1.6, yb - hh * 1.1, z - 0.4), (x - 1.0, yb - hh * 0.8, z + 0.4), c)
        else:
            hh = rnd.uniform(4.0, 11.0)
            CI.box(bone_at(z), (x - 0.4, yb - hh, z - 0.4), (x + 0.4, yb, z + 0.4), kelp if rnd.random() < 0.5 else kelp2)
    for sx in (-1, 1):                                                                                   # kelp hanging down the flanks
        for k in range(14):
            z = -14.0 + k * 3.2 + rnd.uniform(-1, 1)
            w, h, y = prof(z)
            x = sx * (w / 2 + 0.3)
            L = rnd.uniform(5.0, 15.0)
            CI.box(bone_at(z), (x - 0.4, y - h * 0.35, z - 0.4), (x + 0.4, y - h * 0.35 + L, z + 0.4), kelp if k % 2 else kelp2)
        for z in (2.0, 9.0):                                                                             # waterfalls down the flanks
            w, h, y = prof(z)
            x = sx * (w / 2 + 0.35)
            CI.box(body, (x - 0.3, top - 0.4, z - 1.6), (x + 0.3, y + h * 0.2, z + 1.6), water)
            CI.box(body, (x - 0.6, y + h * 0.2 - 1.0, z - 2.2), (x + 0.6, y + h * 0.2, z + 2.2), foam)
    # ------------------------------------------------------------------ the pectoral fins: long feathered wings, lanterns
    for sx in (-1, 1):
        w, h, y = prof(-16.0)
        base = V(sx * (w / 2 - 1.0), y + h * 0.18, -16.0)
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, tuple(base), anim='sway', ax=2, amp=0.1, speed=0.05)
        feather_plane(fb, base, V(sx * 0.35, 0.8, 0.5), V(sx * 0.12, -0.35, 1.0), 13, 42.0,
                      lambda t: 10.0 + 13.0 * math.sin(min(1.0, t * 1.15) * math.pi * 0.9), 3.9, fcols, edge=gold, lantern=lantern, every=4)
    # ------------------------------------------------------------------ the flukes, feathered
    zt, tb = tails[-1]
    w, h, y = prof(43.0)
    for sx in (-1, 1):
        feather_plane(tb, V(0, y, 41.0), V(sx * 1.0, -0.5, 0.35), V(0, 0, 1.0), 10, 20.0,
                      lambda t: 7.0 + 10.0 * math.sin(t * math.pi * 0.85), 3.2, fcols, edge=gold)
    r.height = 24.0 - (top - 16.0)
    r.palette = True                    # 256-colour texture (build_bb.save_palette)
    return r
