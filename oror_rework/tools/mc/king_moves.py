"""(055) The villager king's motions: one for each of his seventy weapon moves (KingArsenal.MOVES) and for each deed that
had none of its own, written here once and turned into jp.oror.reborn.king.KingMotions (export_java) and into
preview sheets of his real rigs (sheets).

A motion is a windup key (w), a strike key (s), an optional second strike key (a) the strikes alternate with, how many
strikes (beats) and how many ticks apart (step, as the server lands them: MULTI 5, SHOT 6, LOB 8, a leap's landing 12,
a pull's yank 8), and whether to pull back between strikes (recoil).

A key names only what it moves. The upper arms' and forearms' x turns are absolute (KingRig takes the stance's hold off
them at run time); every other value is an offset on the idle pose:
  ar, al   right / left upper arm (x, y, z): x < 0 raises it forward (-1.57 level, -3.1 straight up); for the right arm
           y > 0 swings it out to his right and y < 0 across his chest (mirrored for the left); z > 0 lifts the right arm
           out sideways (z < 0 the left)
  fr, fl   forearms (x): < 0 bends the elbow, bringing the forearm up and forward
  t        torso (x, y[, z]): x > 0 bows forward, y > 0 turns his chest to his right, z bends him sideways
  h        head (x[, y, z]): x > 0 looks down
  hy       hips (y): turns his whole body (spins: -6.28 one turn to his left)
  lr, ll   legs (x): < 0 forward;  sr, sl  shins (x): > 0 bends the knee
  dn       height (pixels, > 0 lower: a crouch)
  Lr, Ll   the weapon's tip in the world (0 upright, > 0 tipped forward, 1.57 level ahead, 3.14 point down); turned
           into the weapon bones' x from the arm, forearm and torso (wr, wl give the bone's turn directly instead)
"""
import math

SLOTS = ['ar.x', 'ar.y', 'ar.z', 'al.x', 'al.y', 'al.z', 't.x', 't.y', 'h.x', 'dn', 'fr', 'fl', 'wr', 'wl',
         'lr', 'll', 'sr', 'sl', 'hy', 't.z', 'h.y', 'h.z']
N = len(SLOTS)
IX = {s: i for i, s in enumerate(SLOTS)}
TURNS = ('hy', 't.y', 'wr', 'wl', 'h.y')        # whole turns allowed: KingRig takes them modulo a turn on the way back

PI = math.pi
TURN = 2 * PI

# The weapons: the rig shown, the stance's hold (upper arm, forearm x; right then left), and each hand's weapon bone as
# made in the rig (its tip's lean in the world = torso x + arm x + forearm x + base + the bone's added x).
HOLD = {
    'clubs': (-0.2, -0.45, -0.2, -0.45),
    'scythe': (-0.3, -1.25, 0.0, 0.0),
    'twin': (-0.25, -0.6, -0.25, -0.6),
    'spear': (-0.3, -1.2, 0.0, 0.0),
    'bow': (0.0, 0.0, -0.3, -1.25),
}
LEAN0 = {  # king3d.stance_arms: the lean each weapon was set to stand at in the hold
    'clubs': (0.75, 0.75), 'scythe': (0.15, None), 'twin': (1.85, 1.85), 'spear': (0.1, None), 'bow': (None, 0.05)}
SWORD_TILT = -1.15          # king3d: the hero's sword hangs blade down from the fist, tipped forward by this

WEAPONS = {  # KingArsenal weapon ids
    'sword': dict(rig='villager_king_hero', stance=None),
    'broken': dict(rig='villager_king_broken', stance=None),
    'clubs': dict(rig='villager_king_divine', stance='clubs'),
    'scythe': dict(rig='villager_king_divine', stance='scythe'),
    'twin': dict(rig='villager_king_divine', stance='twin'),
    'spear': dict(rig='villager_king_divine', stance='spear'),
    'bow': dict(rig='villager_king_divine', stance='bow'),
}


def base(weapon, side):
    """The weapon bone's own turn under the forearm (as built), for the lean sums; None if no weapon in that hand."""
    st = WEAPONS[weapon]['stance']
    if st is None:
        if side == 'r':
            return SWORD_TILT + PI          # a blade hanging down: its tip's lean is the bone's turn plus half a turn
        return None
    l0 = LEAN0[st][0 if side == 'r' else 1]
    if l0 is None:
        return None
    ar, fr, al, fl = HOLD[st]
    return l0 - ((ar + fr) if side == 'r' else (al + fl))


def K(**kw):
    """A key: only what it names."""
    return kw


def vec(key, weapon, rest=None):
    """The key as a full vector (absolute arm/forearm x: unnamed ones stay at the hold or, for a stance-less weapon,
    at rest), weapon leans resolved into the bones' turns."""
    st = WEAPONS[weapon]['stance'] if weapon in WEAPONS else None
    hold = HOLD[st] if st else (0.0, 0.0, 0.0, 0.0)
    v = [0.0] * N
    v[IX['ar.x']], v[IX['fr']], v[IX['al.x']], v[IX['fl']] = hold[0], hold[1], hold[2], hold[3]
    for k, val in key.items():
        if k in ('ar', 'al'):
            x, y, z = (tuple(val) + (0, 0, 0))[:3]
            v[IX[k + '.x']], v[IX[k + '.y']], v[IX[k + '.z']] = x, y, z
        elif k == 't':
            x, y, z = (tuple(val) + (0, 0, 0))[:3]
            v[IX['t.x']], v[IX['t.y']], v[IX['t.z']] = x, y, z
        elif k == 'h':
            x, y, z = ((tuple(val) if isinstance(val, (tuple, list)) else (val,)) + (0, 0, 0))[:3]
            v[IX['h.x']], v[IX['h.y']], v[IX['h.z']] = x, y, z
        elif k in ('Lr', 'Ll'):
            continue
        else:
            v[IX[k]] = float(val)
    if weapon in WEAPONS:
        for side, L in (('r', key.get('Lr')), ('l', key.get('Ll'))):
            if L is None:
                continue
            b = base(weapon, side)
            if b is None:
                continue
            arm = v[IX['ar.x']] + v[IX['fr']] if side == 'r' else v[IX['al.x']] + v[IX['fl']]
            v[IX['w' + side]] = L - (v[IX['t.x']] + arm + b)
    return v


# --------------------------------------------------------------------------------------------------------------------
# The seventy. (Damage, reach and timing stay KingArsenal's; length is given only where the strikes outlast it.)
# --------------------------------------------------------------------------------------------------------------------
M = {}


def mv(id_, weapon, w, s, a=None, beats=1, step=5, recoil=False, length=None):
    M[id_] = dict(weapon=weapon, w=w, s=s, a=a, beats=beats, step=step, recoil=recoil, length=length)


# ---- the hero: a true knight of the sword and the tower shield, every blow from the hips and the feet
SH = dict(al=(-1.0, 0.15, -0.1), fl=-0.7)                    # the shield kept up before him
mv('sword_sweep', 'sword',
   K(ar=(-1.45, 1.15, 0.25), fr=-0.35, Lr=1.6, t=(0.05, 0.6), hy=0.15, ll=-0.25, sl=0.2, lr=0.15, dn=1, **SH),
   K(ar=(-1.5, -1.15, 0.0), fr=-0.1, Lr=1.6, t=(0.2, -0.75), hy=-0.25, ll=-0.55, sl=0.45, lr=0.3, dn=2.5,
     al=(-0.7, 0.4, -0.1), fl=-0.5))
mv('sword_return', 'sword',
   K(ar=(-1.3, -1.25, -0.1), fr=-0.6, Lr=1.6, t=(0.1, -0.7), hy=-0.2, al=(-0.5, 0.0, -0.25), fl=-0.4, dn=1),
   K(ar=(-1.4, 1.25, 0.35), fr=-0.05, Lr=1.45, t=(0.15, 0.65), hy=0.25, lr=-0.5, sr=0.4, ll=0.3, dn=2,
     al=(-0.4, 0.0, -0.35), fl=-0.3))
mv('sword_cleave', 'sword',
   K(ar=(-2.85, 0.45, 0.55), fr=-0.45, Lr=-0.5, t=(-0.2, 0.4), h=-0.25, dn=0, **SH),
   K(ar=(-0.65, -0.75, -0.15), fr=-0.1, Lr=2.3, t=(0.45, -0.5), h=0.15, ll=-0.6, sl=0.55, lr=0.35, dn=3,
     al=(-0.8, 0.3, -0.2), fl=-0.6))
mv('sword_rising', 'sword',
   K(ar=(0.35, -0.5, 0.0), fr=-0.2, Lr=2.6, t=(0.45, -0.45), dn=4, lr=-0.45, sr=0.7, ll=-0.15, sl=0.5, **SH),
   K(ar=(-2.95, 0.35, 0.3), fr=-0.15, Lr=-0.3, t=(-0.3, 0.35), h=-0.35, dn=-1, lr=0.2, ll=-0.1,
     al=(-0.6, 0.0, -0.4), fl=-0.4))
mv('sword_thrust', 'sword',
   K(ar=(-1.0, 0.45, 0.1), fr=-1.25, Lr=1.6, t=(0.0, 0.55), al=(-1.35, -0.1, 0.0), fl=-0.8, lr=0.3, ll=-0.2, dn=1),
   K(ar=(-1.6, -0.05, 0.0), fr=0.0, Lr=1.57, t=(0.3, -0.35), lr=-0.95, sr=0.6, ll=0.45, sl=0.3, dn=3.5,
     al=(-0.5, 0.2, -0.3), fl=-0.6))
mv('sword_bash', 'sword',
   K(al=(-0.75, -0.35, -0.1), fl=-0.7, t=(0.05, -0.55), ar=(-0.7, 0.45, 0.35), fr=-0.6, Lr=0.4, dn=1.5, ll=0.25),
   K(al=(-1.65, 0.35, 0.0), fl=-0.05, wl=-0.25, t=(0.3, 0.6), ar=(-0.4, 0.5, 0.45), fr=-0.5, Lr=0.6,
     ll=-0.75, sl=0.5, lr=0.35, dn=2.5))
mv('sword_spin', 'sword',
   K(ar=(-1.45, 1.3, 0.45), fr=-0.2, Lr=1.6, t=(0.15, 0.85), hy=0.4, dn=3, lr=-0.3, sr=0.5, ll=-0.3, sl=0.5,
     al=(-0.4, 0.0, -0.6), fl=-0.4),
   K(ar=(-1.55, 0.2, 0.55), fr=0.0, Lr=1.6, t=(0.15, -0.2), hy=-TURN, dn=3, lr=-0.3, sr=0.5, ll=-0.3, sl=0.5,
     al=(-0.4, 0.0, -0.8), fl=-0.3))
mv('sword_leap', 'sword',
   K(ar=(-3.0, 0.2, 0.25), fr=-0.5, Lr=-0.8, al=(-0.9, 0.0, -0.5), fl=-0.6, t=(0.35, 0.0), dn=6,
     lr=-0.75, sr=1.3, ll=-0.75, sl=1.3),
   K(ar=(-3.05, 0.1, 0.2), fr=-0.2, Lr=-0.2, al=(-1.6, 0.0, -0.6), fl=-0.2, t=(-0.3, 0.0), h=-0.3, dn=-3,
     lr=-1.0, sr=1.5, ll=-0.6, sl=1.6),
   a=K(ar=(-0.65, 0.0, 0.0), fr=-0.1, Lr=2.5, t=(0.7, 0.0), h=0.3, dn=5, lr=-0.85, sr=0.8, ll=0.55, sl=0.7,
       al=(-0.6, 0.0, -0.5), fl=-0.4),
   beats=2, step=12)
mv('sword_dash', 'sword',
   K(ar=(0.55, 0.4, 0.25), fr=-0.25, Lr=2.4, t=(0.5, 0.3), al=(-1.25, 0.0, 0.0), fl=-0.6, dn=2.5,
     ll=-0.65, sl=0.6, lr=0.5, sr=0.3),
   K(ar=(-1.45, -1.3, 0.0), fr=0.0, Lr=1.55, t=(0.45, -0.85), hy=-0.4, lr=-0.75, sr=0.5, ll=0.6, sl=0.9,
     al=(-0.3, 0.3, -0.5), fl=-0.5, dn=3))
mv('sword_wave', 'sword',
   K(ar=(-3.1, -0.3, 0.0), fr=-0.3, Lr=-0.6, al=(-3.0, 0.35, 0.0), fl=-0.4, t=(-0.35, 0.0), h=-0.4, dn=-1),
   K(ar=(-1.05, -0.2, 0.0), fr=0.0, Lr=1.9, al=(-1.0, 0.25, 0.0), fl=-0.1, t=(0.45, 0.0), h=0.1, dn=3,
     lr=-0.7, sr=0.45, ll=0.35))

# ---- the broken one: a box of tricks, every joint where no joint should go
mv('broken_shard', 'broken',
   K(ar=(1.0, 2.0, 0.6), fr=0.6, wr=1.5, t=(-0.2, 0.9, 0.5), h=(0.6, -0.8, 0.4), hy=0.5, dn=1, al=(-0.9, -1.2, -1.4), fl=-1.8),
   K(ar=(-1.65, -2.4, 0.5), fr=-0.2, wr=-1.5, t=(0.3, -1.25, -0.4), h=(-0.3, 1.1, -0.5), hy=0.8, dn=2,
     al=(0.4, 0.8, -0.3), fl=-0.2, ll=-0.6, lr=0.7))
mv('broken_lag', 'broken',
   K(ar=(-1.4, 1.35, 0.3), fr=-0.3, Lr=1.6, t=(0.1, 0.75), dn=1, h=(0.0, 0.0, 0.3)),
   K(ar=(-1.5, -0.15, 0.1), fr=-0.1, Lr=1.6, t=(0.2, -0.05), dn=2, h=(0.0, 0.6, -0.4)),
   a=K(ar=(-1.5, -1.4, 0.0), fr=0.0, Lr=1.6, t=(0.25, -0.85), hy=-0.2, dn=2, h=(0.4, -0.5, 0.6), ll=-0.4),
   beats=2, step=12)
mv('broken_blink', 'broken',
   K(ar=(0.8, 0.0, 0.6), fr=-0.4, Lr=3.0, t=(-0.85, 0.0, 0.3), h=-0.9, dn=-3, al=(0.6, 0.0, -1.0), fl=-1.5,
     lr=0.4, ll=0.6, sr=0.9, sl=1.2),
   K(ar=(-1.6, 0.0, 0.0), fr=0.0, Lr=1.57, t=(0.6, 0.0, -0.3), h=(-0.4, 2.6, 0.0), dn=2.5, ll=-1.0, sl=0.6, lr=0.6,
     al=(-2.4, -0.6, -0.9), fl=-0.3))
mv('broken_multi', 'broken',
   K(ar=(-2.4, 0.6, 0.8), fr=-0.6, Lr=0.5, t=(0.0, 0.3, 0.6), h=(0.3, 0.0, -0.6), al=(-2.6, -0.4, -0.9), fl=-1.2),
   K(ar=(-1.6, -1.25, 0.6), fr=-0.1, Lr=1.6, t=(0.2, -0.8, 0.3), h=(0.0, 0.9, 0.4), hy=0.3, dn=2,
     al=(0.3, 0.9, -1.2), fl=-1.4),
   a=K(ar=(-1.0, 1.4, -0.3), fr=-0.5, Lr=2.2, t=(0.3, 0.9, -0.4), h=(0.5, -1.0, -0.4), hy=-0.4, dn=1,
       al=(-1.9, 1.1, 0.5), fl=0.4),
   beats=5, step=5, length=36)
mv('broken_rewind', 'broken',      # played backwards: the cut done first, the windup last
   K(ar=(-0.75, -1.05, 0.0), fr=-0.1, Lr=2.3, t=(0.35, -0.6), h=0.2, dn=3, al=(-0.4, 0.0, -0.3), fl=-0.6, ll=-0.5),
   K(ar=(-2.9, 0.6, 0.6), fr=-0.5, Lr=-0.4, t=(-0.3, 0.5), h=-0.4, dn=0, al=(-1.75, -0.6, -0.4), fl=-0.2,
     lr=0.3),
   a=K(ar=(-2.6, 0.9, 0.9), fr=-0.6, Lr=-0.2, t=(-0.45, 0.6), h=(-0.5, 0.0, 0.5), dn=-1, al=(-0.7, 0.5, 0.2), fl=-1.7,
       lr=0.5, sr=0.4),
   beats=2, step=8)
mv('broken_blocks', 'broken',
   K(ar=(-2.9, 0.4, 0.6), fr=-0.8, Lr=-0.2, t=(-0.2, 0.8), al=(-1.4, -0.3, -0.2), fl=-0.4, ll=-0.4),
   K(ar=(-1.0, -0.45, 0.0), fr=-0.05, Lr=2.2, t=(0.35, -0.6), al=(-2.7, 0.3, -0.6), fl=-0.8, lr=-0.3, dn=1),
   a=K(al=(-1.0, 0.45, 0.0), fl=-0.05, ar=(-2.7, 0.3, 0.6), fr=-0.8, Lr=-0.1, t=(0.35, 0.6), ll=-0.3, dn=1),
   beats=3, step=8, length=36)
mv('broken_grab', 'broken',
   K(al=(-1.95, -0.85, -0.6), fl=0.1, t=(0.35, 0.65), ar=(-1.2, 0.6, 0.3), fr=-0.6, Lr=1.4, ll=-0.7, sl=0.5, dn=2,
     h=(0.0, -0.4, 0.0)),
   K(al=(-1.95, -0.85, -0.6), fl=0.1, t=(0.35, 0.65), ar=(-1.2, 0.6, 0.3), fr=-0.6, Lr=1.4, ll=-0.7, sl=0.5, dn=2,
     h=(0.2, -0.4, 0.5)),
   a=K(al=(-0.85, 0.65, 0.25), fl=-1.7, t=(-0.45, -0.65), ar=(-1.6, -0.2, 0.0), fr=-0.1, Lr=1.6, lr=0.5, ll=0.2,
       dn=1, h=(-0.3, 0.3, -0.6)),
   beats=2, step=8)
mv('broken_echo', 'broken',
   K(ar=(-2.8, 0.7, 0.5), fr=-0.4, Lr=-0.4, al=(-2.8, -0.7, -0.5), fl=-0.4, t=(-0.25, 0.0, 0.4), h=(-0.2, 0.0, -0.5)),
   K(ar=(-0.7, -0.95, -0.3), fr=-0.05, Lr=2.4, al=(-0.7, 0.95, 0.3), fl=-0.05, t=(0.45, 0.0, -0.3), h=(0.3, 0.0, 0.6),
     dn=3, ll=-0.6, sl=0.5))
mv('broken_hitbox', 'broken',
   K(ar=(-0.3, 0.0, 1.55), fr=0.0, Lr=1.57, al=(-0.3, 0.0, -1.55), fl=0.0, t=(0.0, 0.6, 0.35), dn=1,
     h=(0.0, 0.0, -0.6)),
   K(ar=(-0.25, 0.0, 1.65), fr=0.0, Lr=1.57, al=(-0.25, 0.0, -1.65), fl=0.0, t=(0.0, 0.0, -0.35), hy=TURN, dn=1,
     h=(0.0, 1.5, 0.6), lr=-0.4, ll=0.4))
mv('broken_nan', 'broken',
   K(ar=(0.4, 0.0, 0.2), fr=0.0, Lr=2.4, al=(0.4, 0.0, -0.2), fl=0.0, t=(0.6, 0.0), h=0.7, dn=6,
     lr=-0.8, sr=1.5, ll=-0.8, sl=1.5),
   K(ar=(-3.1, 0.0, 0.1), fr=0.0, Lr=0.0, al=(-3.1, 0.0, -0.1), fl=0.0, t=(-0.35, 0.0), h=-0.7, dn=-4,
     lr=0.3, ll=0.3),
   a=K(ar=(-3.1, 0.0, 0.6), fr=0.0, Lr=0.0, al=(-3.1, 0.0, -0.6), fl=0.0, t=(-0.35, 0.0, 0.8), h=(-0.7, 3.1, 0.0),
       dn=-4, lr=0.3, ll=0.3),
   beats=2, step=10)

# ---- the thunder clubs (Yagrush right, Aymur left)
mv('clubs_smite', 'clubs',
   K(ar=(-3.0, 0.3, 0.4), fr=-0.35, Lr=-0.6, al=(-0.8, 0.0, 0.0), fl=-0.7, Ll=0.6, t=(-0.2, 0.45), dn=0),
   K(ar=(-0.85, -0.25, 0.0), fr=-0.15, Lr=2.2, al=(-0.5, 0.0, -0.2), fl=-0.5, Ll=0.5, t=(0.5, -0.3), dn=2.5,
     ll=-0.55, sl=0.5, lr=0.3))
mv('clubs_flurry', 'clubs',
   K(ar=(-1.6, 0.6, 0.3), fr=-1.2, Lr=0.3, al=(-1.6, -0.6, -0.3), fl=-1.2, Ll=0.3, t=(0.25, 0.0), dn=2,
     lr=-0.3, sr=0.4, ll=-0.3, sl=0.4),
   K(ar=(-1.65, -0.65, 0.0), fr=-0.2, Lr=1.8, al=(-1.25, -0.45, -0.2), fl=-1.4, Ll=0.2, t=(0.3, -0.55), dn=2.5,
     ll=-0.4, sl=0.4),
   a=K(al=(-1.65, 0.65, 0.0), fl=-0.2, Ll=1.8, ar=(-1.25, 0.45, 0.2), fr=-1.4, Lr=0.2, t=(0.3, 0.55), dn=2.5,
       lr=-0.4, sr=0.4),
   beats=4, step=5, length=30)
mv('clubs_rise', 'clubs',
   K(al=(0.5, -0.3, -0.2), fl=-0.2, Ll=2.6, ar=(-1.4, 0.3, 0.2), fr=-1.0, Lr=0.3, t=(0.4, -0.55), dn=4,
     lr=-0.4, sr=0.7, ll=-0.2, sl=0.6),
   K(al=(-2.95, 0.2, -0.1), fl=-0.35, Ll=-0.3, ar=(-1.0, 0.2, 0.3), fr=-1.2, Lr=0.6, t=(-0.3, 0.45), h=-0.4, dn=-1.5,
     lr=0.2, ll=-0.2))
mv('clubs_quake', 'clubs',
   K(ar=(-3.1, 0.2, 0.3), fr=-0.2, Lr=-0.3, al=(-3.1, -0.2, -0.3), fl=-0.2, Ll=-0.3, t=(-0.3, 0.0), h=-0.4, dn=-1.5),
   K(ar=(-0.45, -0.2, 0.1), fr=0.0, Lr=2.9, al=(-0.45, 0.2, -0.1), fl=0.0, Ll=2.9, t=(0.9, 0.0), h=0.5, dn=6,
     lr=-0.45, sr=0.8, ll=-0.45, sl=0.8))
mv('clubs_spin', 'clubs',
   K(ar=(-1.4, 1.3, 0.6), fr=-0.2, Lr=1.5, al=(-1.4, -1.3, -0.6), fl=-0.2, Ll=1.5, t=(0.1, 0.75), hy=0.3, dn=1.5),
   K(ar=(-1.5, 0.9, 1.2), fr=0.0, Lr=1.57, al=(-1.5, -0.9, -1.2), fl=0.0, Ll=1.57, t=(0.1, 0.0), hy=-TURN, dn=1.5,
     lr=-0.3, ll=0.3))
mv('clubs_throw', 'clubs',
   K(ar=(-3.0, 0.5, 0.5), fr=-0.85, Lr=-0.9, al=(-1.55, 0.0, 0.0), fl=0.0, Ll=1.3, t=(-0.2, 0.85), ll=-0.4, dn=1),
   K(ar=(-1.3, -0.6, 0.0), fr=0.0, Lr=1.8, al=(-0.4, -0.3, -0.4), fl=-0.6, Ll=0.6, t=(0.45, -0.7), lr=0.45,
     ll=-0.65, sl=0.45, dn=1.5))
mv('clubs_cross', 'clubs',
   K(ar=(-2.4, 1.0, 0.6), fr=-0.2, Lr=0.0, al=(-2.4, -1.0, -0.6), fl=-0.2, Ll=0.0, t=(-0.2, 0.0), h=-0.2),
   K(ar=(-1.4, -1.0, -0.3), fr=-0.3, Lr=1.5, al=(-1.4, 1.0, 0.3), fl=-0.3, Ll=1.5, t=(0.35, 0.0), dn=2,
     ll=-0.5, sl=0.4))
mv('clubs_leap', 'clubs',
   K(ar=(-3.0, 0.2, 0.4), fr=-1.4, Lr=-2.0, al=(-3.0, -0.2, -0.4), fl=-1.4, Ll=-2.0, t=(0.5, 0.0), dn=6,
     lr=-1.0, sr=1.6, ll=-1.0, sl=1.6),
   K(ar=(-3.05, 0.2, 0.5), fr=-0.6, Lr=-1.0, al=(-3.05, -0.2, -0.5), fl=-0.6, Ll=-1.0, t=(-0.3, 0.0), h=-0.3,
     dn=-3, lr=-1.1, sr=1.5, ll=-0.7, sl=1.7),
   a=K(ar=(-1.0, 0.0, 0.1), fr=0.0, Lr=2.4, al=(-1.0, 0.0, -0.1), fl=0.0, Ll=2.4, t=(0.75, 0.0), h=0.3, dn=5,
       lr=-0.9, sr=0.5, ll=0.6, sl=0.6),
   beats=2, step=12)
mv('clubs_chain', 'clubs',
   K(ar=(-3.1, 0.0, 0.1), fr=0.0, Lr=0.0, al=(-0.4, 0.0, -0.6), fl=-0.3, Ll=0.4, t=(-0.3, 0.0), h=-0.65),
   K(ar=(-3.1, 0.0, 0.25), fr=0.0, Lr=0.15, al=(-1.6, 0.05, 0.0), fl=0.0, Ll=1.55, t=(0.1, 0.45), h=0.0,
     ll=-0.4, dn=1))
mv('clubs_shock', 'clubs',
   K(ar=(-1.0, -1.0, -0.2), fr=-1.6, Lr=0.2, al=(-1.0, 1.0, 0.2), fl=-1.6, Ll=0.2, t=(0.45, 0.0), h=0.5, dn=3.5,
     lr=-0.3, sr=0.6, ll=-0.3, sl=0.6),
   K(ar=(-0.6, 0.0, 1.7), fr=0.0, Lr=2.4, al=(-0.6, 0.0, -1.7), fl=0.0, Ll=2.4, t=(-0.4, 0.0), h=-0.55, dn=-1))

# ---- the fly lord's scythe (in the right fist; the left hand comes to the haft for the great cuts)
mv('scythe_reap', 'scythe',
   K(ar=(-1.0, 1.4, 0.4), fr=-0.6, Lr=1.3, t=(0.1, 0.9), hy=0.3, dn=2, al=(-1.2, 0.8, 0.4), fl=-0.6),
   K(ar=(-1.3, -1.3, 0.0), fr=-0.6, Lr=1.3, t=(0.2, -0.9), hy=-0.3, dn=2.5, al=(-1.0, -0.4, 0.0), fl=-0.8,
     lr=0.4, ll=-0.6, sl=0.4))
mv('scythe_return', 'scythe',
   K(ar=(-1.2, -1.5, 0.0), fr=-0.9, Lr=1.5, t=(0.15, -0.9), al=(-0.3, 0.0, -0.6), fl=-0.4, dn=1),
   K(ar=(-1.1, 1.5, 0.4), fr=-0.4, Lr=1.2, t=(0.1, 0.9), hy=0.25, ll=0.4, lr=-0.5, sr=0.4, dn=2,
     al=(-0.3, 0.0, -0.8), fl=-0.4))
mv('scythe_neck', 'scythe',
   K(ar=(-3.0, 0.2, 0.3), fr=-0.2, Lr=0.6, t=(-0.4, 0.0), h=-0.4, al=(-1.6, 0.4, 0.0), fl=0.0, dn=-0.5),
   K(ar=(-1.4, -0.3, 0.0), fr=-1.4, Lr=2.4, t=(0.6, 0.0), h=0.3, dn=3.5, al=(-0.9, 0.5, 0.2), fl=-1.2,
     ll=-0.5, sl=0.5))
mv('scythe_hook', 'scythe',
   K(ar=(-1.8, 0.2, 0.0), fr=0.0, Lr=2.2, t=(0.6, 0.0), ll=-0.75, sl=0.4, lr=0.3, dn=2.5, al=(-0.6, 0.0, -0.4), fl=-0.4),
   K(ar=(-1.85, 0.2, 0.0), fr=-0.05, Lr=2.5, t=(0.65, 0.1), ll=-0.85, sl=0.4, lr=0.35, dn=3,
     al=(-0.6, 0.0, -0.4), fl=-0.4),
   a=K(ar=(-0.4, 0.6, 0.3), fr=-1.6, Lr=0.9, t=(-0.5, 0.6), ll=0.2, lr=-0.3, sr=0.3, dn=1, al=(-1.3, 0.5, 0.1), fl=-0.9),
   beats=2, step=8)
mv('scythe_spin', 'scythe',
   K(ar=(-1.5, 1.4, 0.6), fr=-0.5, Lr=1.5, al=(-1.3, 0.6, 0.4), fl=-0.7, t=(0.2, 1.0), hy=0.4, dn=3,
     lr=-0.3, sr=0.6, ll=-0.3, sl=0.6),
   K(ar=(-1.6, 0.6, 0.6), fr=-0.2, Lr=1.6, al=(-1.3, 0.2, 0.0), fl=-0.6, t=(0.2, 0.0), hy=-2 * TURN, dn=3,
     lr=-0.3, sr=0.6, ll=-0.3, sl=0.6))
mv('scythe_throw', 'scythe',
   K(ar=(-2.9, 0.6, 0.8), fr=-0.6, Lr=-0.5, t=(-0.3, 1.0), al=(-1.4, -0.2, 0.0), fl=0.0, ll=-0.4, dn=0.5),
   K(ar=(-1.0, -1.0, -0.2), fr=0.0, Lr=2.4 + TURN, t=(0.5, -0.9), lr=0.5, ll=-0.6, sl=0.45, dn=1.5,
     al=(-0.3, 0.3, -0.5), fl=-0.5))
mv('scythe_wave', 'scythe',
   K(ar=(-0.4, -1.0, -0.3), fr=-1.0, Lr=2.0, t=(0.4, -0.8), dn=3, al=(-0.9, 0.4, 0.0), fl=-1.0,
     lr=-0.3, sr=0.6, ll=-0.2, sl=0.5),
   K(ar=(-2.6, 1.2, 0.7), fr=-0.3, Lr=0.4, t=(-0.3, 0.9), h=-0.4, dn=-0.5, al=(-0.6, 0.0, -0.5), fl=-0.4, lr=0.2))
mv('scythe_soul', 'scythe',
   K(ar=(-0.2, 0.4, 0.3), fr=-0.4, Lr=2.3, al=(-0.2, 0.0, -0.3), fl=-0.6, t=(0.4, 0.2), dn=2.5),
   K(ar=(-2.0, 0.2, 0.2), fr=-1.2, Lr=0.3, al=(-1.85, 0.0, -0.1), fl=0.0, t=(-0.3, -0.25), h=-0.3, dn=0,
     ll=-0.4))
mv('scythe_low', 'scythe',
   K(ar=(-0.6, 1.3, 0.5), fr=-0.4, Lr=2.7, t=(0.7, 0.7), dn=7, lr=-0.8, sr=1.4, ll=0.2, sl=1.0,
     al=(-0.5, 0.0, -0.6), fl=-0.3),
   K(ar=(-0.6, -1.4, 0.0), fr=-0.4, Lr=2.7, t=(0.7, -0.8), hy=-0.4, dn=7, lr=-0.8, sr=1.4, ll=0.2, sl=1.0,
     al=(-0.5, 0.0, -0.9), fl=-0.3))
mv('scythe_leap', 'scythe',
   K(ar=(-3.1, 0.3, 0.4), fr=-0.2, Lr=0.6, t=(0.4, 0.0), al=(0.4, 0.0, -0.4), fl=-0.2, dn=5.5,
     lr=-0.8, sr=1.4, ll=-0.8, sl=1.4),
   K(ar=(-3.1, 0.3, 0.6), fr=-0.4, Lr=0.2, t=(-0.4, 0.0), h=-0.4, al=(-2.4, 0.0, -0.6), fl=-0.3, dn=-3,
     lr=-1.0, sr=1.5, ll=-0.6, sl=1.6),
   a=K(ar=(-1.2, 0.0, 0.0), fr=-1.6, Lr=2.8, t=(0.8, 0.0), h=0.3, dn=5, lr=-0.8, sr=0.6, ll=0.6, sl=0.8,
       al=(-1.0, 0.4, 0.0), fl=-1.0),
   beats=2, step=12)

# ---- the twin swords (Seraph right, Beelzebub left)
mv('twin_double', 'twin',
   K(ar=(-1.5, 1.1, 0.3), fr=-0.4, Lr=1.4, al=(-1.5, -1.1, -0.3), fl=-0.4, Ll=1.4, dn=1.5),
   K(ar=(-1.5, -1.0, 0.0), fr=-0.1, Lr=1.6, al=(-1.4, -1.0, -0.3), fl=-0.4, Ll=1.4, t=(0.15, -0.6), dn=2,
     ll=-0.4, sl=0.3),
   a=K(al=(-1.5, 1.0, 0.0), fl=-0.1, Ll=1.6, ar=(-1.4, 0.8, 0.3), fr=-0.4, Lr=1.4, t=(0.15, 0.6), dn=2,
       lr=-0.4, sr=0.3),
   beats=2, step=5, length=20)
mv('twin_cross', 'twin',
   K(ar=(-2.6, -0.6, -0.2), fr=-0.4, Lr=-0.3, al=(-2.6, 0.6, 0.2), fl=-0.4, Ll=-0.3, t=(-0.2, 0.0), h=-0.2),
   K(ar=(-0.6, 0.9, 0.6), fr=0.0, Lr=2.3, al=(-0.6, -0.9, -0.6), fl=0.0, Ll=2.3, t=(0.45, 0.0), dn=2.5,
     ll=-0.5, sl=0.4))
mv('twin_stabs', 'twin',
   K(ar=(-0.2, 0.3, 0.0), fr=-1.5, Lr=1.57, al=(-0.2, -0.3, 0.0), fl=-1.5, Ll=1.57, t=(0.2, 0.0), dn=2.5,
     lr=-0.3, sr=0.4, ll=0.2),
   K(ar=(-1.6, 0.0, 0.0), fr=0.0, Lr=1.57, al=(-0.2, -0.3, 0.0), fl=-1.5, Ll=1.57, t=(0.3, -0.45), dn=3,
     ll=-0.5, sl=0.4),
   a=K(al=(-1.6, 0.0, 0.0), fl=0.0, Ll=1.57, ar=(-0.2, 0.3, 0.0), fr=-1.5, Lr=1.57, t=(0.3, 0.45), dn=3,
       lr=-0.5, sr=0.4),
   beats=4, step=5, length=30)
mv('twin_whirl', 'twin',
   K(ar=(-1.5, 1.4, 0.5), fr=-0.1, Lr=1.57, al=(-1.5, -1.4, -0.5), fl=-0.1, Ll=1.57, t=(0.1, 0.6), hy=0.3, dn=1.5),
   K(ar=(-1.55, 1.3, 0.6), fr=0.0, Lr=1.6, al=(-1.55, -1.3, -0.6), fl=0.0, Ll=1.6, t=(0.1, 0.0), hy=-TURN, dn=1.5,
     lr=-0.3, ll=0.3),
   a=K(ar=(-1.55, 1.3, 0.6), fr=0.0, Lr=1.6, al=(-1.55, -1.3, -0.6), fl=0.0, Ll=1.6, t=(0.1, 0.0), hy=-2 * TURN,
       dn=1.5, lr=0.3, ll=-0.3),
   beats=2, step=5)
mv('twin_leap', 'twin',
   K(ar=(-3.0, -0.4, 0.3), fr=-1.0, Lr=-1.6, al=(-3.0, 0.4, -0.3), fl=-1.0, Ll=-1.6, t=(0.4, 0.0), dn=5.5,
     lr=-0.8, sr=1.4, ll=-0.8, sl=1.4),
   K(ar=(-3.05, -0.4, 0.4), fr=-0.6, Lr=-1.0, al=(-3.05, 0.4, -0.4), fl=-0.6, Ll=-1.0, t=(-0.3, 0.0), h=-0.3, dn=-3,
     lr=-1.0, sr=1.5, ll=-0.6, sl=1.6),
   a=K(ar=(-0.8, -0.7, -0.2), fr=0.0, Lr=2.3, al=(-0.8, 0.7, 0.2), fl=0.0, Ll=2.3, t=(0.7, 0.0), h=0.2, dn=4.5,
       lr=-0.8, sr=0.5, ll=0.6, sl=0.6),
   beats=2, step=12)
mv('twin_slide', 'twin',
   K(ar=(0.6, 0.5, 0.3), fr=-0.3, Lr=2.4, al=(0.6, -0.5, -0.3), fl=-0.3, Ll=2.4, t=(0.6, 0.0), dn=3,
     lr=-0.7, sr=0.4, ll=0.6, sl=0.8),
   K(ar=(-1.4, -0.9, 0.0), fr=0.0, Lr=1.6, al=(-0.6, -1.2, -0.6), fl=0.0, Ll=2.0, t=(0.3, -0.6), dn=7,
     ll=-1.2, sl=0.2, lr=0.8, sr=1.6))
mv('twin_rise', 'twin',      # reverse grip in the left fist, the blade down along the forearm
   K(al=(0.4, -0.4, -0.2), fl=-0.3, Ll=3.0, ar=(-1.4, 0.3, 0.4), fr=-1.0, Lr=0.6, t=(0.35, -0.6), dn=3.5,
     lr=-0.4, sr=0.6, ll=-0.2, sl=0.5),
   K(al=(-2.9, 0.4, -0.1), fl=-0.3, Ll=-2.9, ar=(-1.4, 0.3, 0.4), fr=-1.0, Lr=0.8, t=(-0.25, 0.5), h=-0.4,
     dn=-1.5, lr=0.2, ll=-0.2))
mv('twin_xwave', 'twin',
   K(ar=(-2.4, 1.2, 0.8), fr=-0.6, Lr=-0.8, al=(-2.4, -1.2, -0.8), fl=-0.6, Ll=-0.8, t=(-0.3, 0.0), h=-0.3),
   K(ar=(-1.5, -0.6, -0.2), fr=0.0, Lr=1.57, al=(-1.5, 0.6, 0.2), fl=0.0, Ll=1.57, t=(0.5, 0.0), dn=2.5,
     ll=-0.7, sl=0.5, lr=0.3))
mv('twin_behind', 'twin',
   K(ar=(-0.8, 0.6, 0.4), fr=-1.0, Lr=1.2, al=(-0.8, -0.6, -0.4), fl=-1.0, Ll=1.2, hy=1.2, t=(0.4, 0.0), dn=3.5,
     lr=-0.4, sr=0.7, ll=0.3, sl=0.7),
   K(ar=(-1.4, -1.2, 0.0), fr=0.0, Lr=1.6, al=(-1.0, -1.6, -0.5), fl=0.0, Ll=1.9, hy=-0.6, t=(0.3, -1.0), dn=2.5,
     ll=-0.5, sl=0.5, lr=0.4))
mv('twin_hundred', 'twin',
   K(ar=(-1.2, 0.2, 0.0), fr=-1.2, Lr=1.3, al=(-1.2, -0.2, 0.0), fl=-1.2, Ll=1.3, t=(0.3, 0.0), dn=2.5,
     lr=-0.3, sr=0.4, ll=0.2),
   K(ar=(-1.8, -0.5, 0.0), fr=-0.1, Lr=1.7, al=(-1.0, -0.2, 0.0), fl=-1.4, Ll=1.2, t=(0.35, -0.5), dn=3,
     ll=-0.4, sl=0.4),
   a=K(al=(-1.8, 0.5, 0.0), fl=-0.1, Ll=1.7, ar=(-1.0, 0.2, 0.0), fr=-1.4, Lr=1.2, t=(0.35, 0.5), dn=3,
       lr=-0.4, sr=0.4),
   beats=10, step=5, length=62)

# ---- the thunder spear (in the right fist; the left hand rides the shaft)
mv('spear_thrust', 'spear',
   K(ar=(-0.6, 0.3, 0.2), fr=-0.6, Lr=1.57, t=(0.0, 0.6), al=(-1.0, 0.5, 0.0), fl=-0.8, lr=0.4, dn=1),
   K(ar=(-1.5, 0.0, 0.0), fr=0.0, Lr=1.57, t=(0.3, -0.4), al=(-1.4, 0.4, 0.0), fl=-0.2, ll=-0.8, sl=0.5, lr=0.5, dn=3))
mv('spear_double', 'spear',
   K(ar=(-0.6, 0.3, 0.2), fr=-0.6, Lr=1.57, t=(0.0, 0.6), al=(-1.0, 0.5, 0.0), fl=-0.8, lr=0.4, dn=1),
   K(ar=(-1.75, 0.0, 0.0), fr=0.0, Lr=1.35, t=(0.2, -0.4), al=(-1.5, 0.4, 0.0), fl=-0.2, ll=-0.7, sl=0.5, lr=0.5, dn=2),
   a=K(ar=(-1.2, 0.0, 0.0), fr=0.0, Lr=1.95, t=(0.5, -0.4), al=(-1.1, 0.4, 0.0), fl=-0.2, ll=-0.9, sl=0.6, lr=0.6,
       dn=4.5),
   beats=2, step=5, recoil=True)
mv('spear_sweep', 'spear',
   K(ar=(-1.3, 1.4, 0.5), fr=-0.2, Lr=1.57, al=(-1.2, 0.9, 0.4), fl=-0.5, t=(0.1, 0.9), dn=2),
   K(ar=(-1.3, -1.3, 0.0), fr=-0.2, Lr=1.57, al=(-1.0, -0.6, 0.0), fl=-0.5, t=(0.15, -0.9), hy=-0.3, dn=2.5,
     ll=-0.4, sl=0.3))
mv('spear_butt', 'spear',
   K(ar=(-1.4, 0.0, 0.0), fr=-0.2, Lr=1.57, al=(-1.2, 0.4, 0.0), fl=-0.4, t=(0.1, 0.2)),
   K(ar=(0.6, 0.4, 0.4), fr=-1.0, Lr=1.57, al=(-0.2, 0.0, -0.3), fl=-0.4, t=(0.0, 0.9), h=(-0.2, 1.0, 0.0),
     lr=0.6, sr=0.2, dn=1.5))
mv('spear_twirl', 'spear',
   K(ar=(-1.5, 0.0, 0.3), fr=-0.2, Lr=1.57, al=(-1.5, 0.0, -0.3), fl=-0.2, t=(0.1, 0.0), dn=1),
   K(ar=(-1.5, 0.0, 0.3), fr=-0.2, Lr=1.57 + 2 * TURN, al=(-1.5, 0.0, -0.3), fl=-0.2, t=(0.1, 0.3), dn=1.5,
     ll=-0.3, lr=0.3))
mv('spear_dive', 'spear',
   K(ar=(-3.0, 0.2, 0.3), fr=-0.3, Lr=2.3, t=(0.3, 0.0), dn=6, lr=-0.8, sr=1.5, ll=-0.8, sl=1.5,
     al=(-0.6, 0.0, -0.5), fl=-0.4),
   K(ar=(-3.05, 0.2, 0.3), fr=-0.3, Lr=2.5, t=(-0.3, 0.0), h=0.2, dn=-3, lr=-1.0, sr=1.5, ll=-0.6, sl=1.6,
     al=(-1.8, 0.0, -0.6), fl=-0.2),
   a=K(ar=(-1.0, 0.0, 0.0), fr=-0.4, Lr=2.7, t=(0.8, 0.0), h=0.3, dn=5, lr=-0.8, sr=0.6, ll=0.6, sl=0.8,
       al=(-1.0, 0.3, 0.0), fl=-0.9),
   beats=2, step=12)
mv('spear_rush', 'spear',
   K(ar=(-0.9, 0.2, 0.2), fr=-0.9, Lr=1.6, al=(-1.0, 0.4, 0.0), fl=-0.9, t=(0.6, 0.0), dn=3, ll=-0.6, sl=0.6, lr=0.5),
   K(ar=(-1.5, 0.0, 0.0), fr=0.0, Lr=1.57, al=(0.6, 0.0, -0.3), fl=-0.6, t=(0.8, -0.2), dn=4,
     ll=-1.1, sl=0.3, lr=0.9, sr=1.0))
mv('spear_throw', 'spear',
   K(ar=(-2.9, 0.5, 0.6), fr=-0.6, Lr=1.3, t=(-0.3, 1.0), al=(-1.6, -0.2, 0.0), fl=0.0, ll=-0.5, dn=0.5),
   K(ar=(-1.3, -0.4, 0.0), fr=0.0, Lr=1.9, t=(0.5, -0.8), lr=0.6, ll=-0.7, sl=0.5, dn=1.5,
     al=(-0.4, 0.3, -0.5), fl=-0.5))
mv('spear_bristle', 'spear',
   K(ar=(-2.8, 0.0, 0.2), fr=-0.4, Lr=PI, al=(-2.8, 0.0, -0.2), fl=-0.4, t=(-0.2, 0.0), h=-0.3, dn=-1),
   K(ar=(-0.8, 0.0, 0.0), fr=-0.6, Lr=PI, al=(-0.8, 0.1, 0.0), fl=-0.6, t=(0.7, 0.0), h=0.4, dn=4.5,
     lr=-0.4, sr=0.7, ll=-0.4, sl=0.7))
mv('spear_heaven', 'spear',
   K(ar=(0.2, 0.0, 0.2), fr=-1.6, Lr=0.6, t=(0.4, 0.0), dn=4.5, lr=-0.5, sr=0.9, ll=-0.5, sl=0.9,
     al=(-0.5, 0.0, -0.4), fl=-0.4),
   K(ar=(-3.1, 0.0, 0.1), fr=0.0, Lr=0.0, t=(-0.4, 0.0), h=-0.7, dn=-2.5, al=(-0.6, 0.0, -0.6), fl=-0.2,
     lr=0.15, ll=0.15))

# ---- the rainbow bow (in the left fist; the right hand draws)
mv('bow_quick', 'bow',
   K(al=(-0.9, 0.3, 0.0), fl=-0.6, Ll=0.3, ar=(-0.9, -0.6, 0.0), fr=-1.0, t=(0.1, 0.2)),
   K(al=(-1.4, 0.0, 0.0), fl=-0.2, Ll=0.0, ar=(-1.0, 0.45, 0.3), fr=-0.6, t=(0.05, 0.45), dn=1))
mv('bow_double', 'bow',
   K(al=(-1.57, 0.0, 0.0), fl=0.0, Ll=0.0, ar=(-1.6, -0.7, 0.0), fr=-1.6, t=(0.0, 0.8), hy=0.4, dn=1),
   K(al=(-1.57, 0.0, 0.0), fl=0.0, Ll=0.0, ar=(-1.6, 0.5, 0.3), fr=-0.6, t=(0.0, 0.8), hy=0.4, dn=1),
   beats=2, step=6, recoil=True)
mv('bow_fan', 'bow',
   K(al=(-1.5, -0.7, 0.0), fl=0.0, Ll=-0.3, ar=(-1.5, -1.2, 0.0), fr=-1.6, t=(0.0, -0.4), dn=1),
   K(al=(-1.5, 0.75, 0.0), fl=0.0, Ll=0.3, ar=(-1.5, 0.4, 0.6), fr=-0.4, t=(0.0, 0.6), dn=1.5))
mv('bow_lob', 'bow',
   K(al=(-2.6, 0.0, 0.0), fl=0.0, Ll=-0.9, ar=(-2.6, -0.7, 0.0), fr=-1.6, t=(-0.4, 0.3), h=-0.6, lr=0.3),
   K(al=(-2.6, 0.0, 0.0), fl=0.0, Ll=-0.9, ar=(-2.5, 0.4, 0.4), fr=-0.6, t=(-0.4, 0.3), h=-0.7, lr=0.3))
mv('bow_pierce', 'bow',
   K(al=(-1.57, 0.0, 0.0), fl=0.0, Ll=0.0, ar=(-1.4, -0.4, 0.5), fr=-2.2, t=(0.1, 1.1), hy=0.5, dn=3,
     lr=-0.5, sr=0.7, ll=0.4, sl=0.6),
   K(al=(-1.8, 0.0, 0.0), fl=0.0, Ll=-0.2, ar=(-1.2, 1.0, 0.8), fr=-0.2, t=(-0.2, 1.1), hy=0.5, dn=2.5,
     lr=-0.5, sr=0.7, ll=0.4, sl=0.6))
mv('bow_retreat', 'bow',
   K(al=(-0.6, 0.0, 0.0), fl=-1.2, Ll=0.2, ar=(-0.6, 0.0, 0.0), fr=-0.6, t=(0.5, 0.0), dn=4.5,
     lr=-0.7, sr=1.3, ll=-0.7, sl=1.3),
   K(al=(-1.8, 0.0, 0.0), fl=0.0, Ll=-0.25, ar=(-1.8, -0.6, 0.0), fr=-1.6, t=(-0.5, 0.0), dn=-2.5,
     lr=-0.6, sr=0.8, ll=-0.3, sl=1.0),
   a=K(al=(-1.7, 0.0, 0.0), fl=0.0, Ll=-0.2, ar=(-1.5, 0.6, 0.5), fr=-0.5, t=(-0.3, 0.0), dn=0, lr=-0.2, ll=0.2),
   beats=2, step=8)
mv('bow_rainbow', 'bow',
   K(al=(-3.0, 0.0, 0.0), fl=0.0, Ll=-1.4, ar=(-3.0, -0.5, 0.0), fr=-1.4, h=-0.8, t=(-0.4, 0.2)),
   K(al=(-1.6, 0.0, 0.0), fl=0.0, Ll=0.0, ar=(-1.5, 0.6, 0.6), fr=-0.4, h=0.0, t=(0.0, 0.5), dn=1))
mv('bow_pin', 'bow',
   K(al=(-1.1, 0.0, 0.0), fl=0.0, Ll=0.45, ar=(-1.1, -0.7, 0.0), fr=-1.6, t=(0.3, 0.6), h=0.4, dn=6.5,
     lr=-1.4, sr=1.5, ll=0.4, sl=1.6),
   K(al=(-1.1, 0.0, 0.0), fl=0.0, Ll=0.45, ar=(-1.0, 0.5, 0.4), fr=-0.5, t=(0.3, 0.6), h=0.4, dn=6.5,
     lr=-1.4, sr=1.5, ll=0.4, sl=1.6))
mv('bow_burst', 'bow',
   K(al=(-1.6, 0.0, 0.0), fl=0.0, Ll=-0.4, ar=(-1.9, -0.6, 0.0), fr=-1.8, t=(0.0, 0.7), h=-0.2, dn=1.5),
   K(al=(-2.0, 0.2, 0.0), fl=0.0, Ll=-0.7, ar=(-1.4, 1.2, 0.9), fr=-0.3, t=(-0.5, 0.7), ll=-0.3, lr=0.5, dn=0))
mv('bow_strike', 'bow',
   K(al=(-2.6, -0.8, -0.5), fl=-0.4, Ll=-0.6, ar=(-0.8, 0.3, 0.3), fr=-0.8, t=(0.0, -0.7), dn=1),
   K(al=(-1.2, 1.2, 0.2), fl=-0.2, Ll=0.8, ar=(-0.6, 0.6, 0.5), fr=-0.6, t=(0.2, 0.8), ll=-0.5, sl=0.4, dn=2))

# --------------------------------------------------------------------------------------------------------------------
# The deeds that had no pose of their own (KingArsenal.DEED_STYLE), and the bow's rain and triple shot (their windup
# and strike were the same pose). No weapon leans: they are done in any of his stances.
# --------------------------------------------------------------------------------------------------------------------
D = {}


def dd(id_, w, s, a=None, beats=1, step=5, recoil=False, weapon='spear'):
    """weapon: only the rig and stance its preview is drawn with."""
    D[id_] = dict(weapon=weapon, w=w, s=s, a=a, beats=beats, step=step, recoil=recoil, length=None)


dd('backstep', K(t=(0.3, 0.0), dn=2.5, lr=-0.3, sr=0.6, ll=-0.3, sl=0.6),
   K(t=(-0.45, 0.0), h=-0.2, dn=-2, lr=-0.5, sr=0.9, ll=-0.2, sl=0.7, ar=(-0.9, 0.0, 0.3), al=(-0.9, 0.0, -0.3)))
dd('sidestep', K(t=(0.2, 0.0, 0.3), dn=2.5, lr=-0.2, sr=0.5, ll=0.2, sl=0.5),
   K(t=(0.1, 0.0, -0.45), dn=0.5, lr=0.0, ll=-0.5, sl=0.6, ar=(-0.6, 0.0, 0.9), al=(-0.4, 0.0, -0.4)))
dd('guard', K(al=(-1.6, 0.4, 0.0), fl=-0.5, ar=(-0.6, 0.3, 0.2), fr=-0.6, t=(0.15, -0.3), dn=2, ll=-0.3, sl=0.3),
   K(al=(-1.65, 0.45, 0.0), fl=-0.55, ar=(-0.6, 0.3, 0.2), fr=-0.7, t=(0.2, -0.35), dn=2.5, ll=-0.35, sl=0.35),
   weapon='sword')
dd('summon', K(ar=(-3.0, 0.0, 0.2), fr=0.0, al=(-3.0, 0.0, -0.2), fl=0.0, h=-0.6, t=(-0.3, 0.0)),
   K(ar=(-0.5, 0.0, 1.4), fr=0.0, al=(-0.5, 0.0, -1.4), fl=0.0, h=-0.3, t=(0.1, 0.0), dn=1))
dd('chains', K(ar=(-1.5, -0.9, 0.0), fr=-0.8, al=(-1.5, 0.9, 0.0), fl=-0.8, t=(0.3, 0.0), dn=1.5),
   K(ar=(0.5, 0.5, 0.6), fr=-1.6, al=(0.5, -0.5, -0.6), fl=-1.6, t=(-0.5, 0.0), dn=1.5, ll=-0.6, sl=0.3, lr=0.4),
   a=K(ar=(-1.3, -0.4, 0.2), fr=-0.6, al=(-1.3, 0.4, -0.2), fl=-0.6, t=(0.2, 0.0), dn=2, ll=-0.5, sl=0.4),
   beats=3, step=10, recoil=False)
dd('wormwood', K(ar=(-3.0, 0.2, 0.4), fr=0.0, h=-0.8, t=(-0.4, 0.0), al=(-0.5, 0.0, -0.5), fl=-0.3),
   K(ar=(-1.0, -0.3, 0.0), fr=0.0, h=0.4, t=(0.5, -0.2), dn=2, al=(-0.3, 0.0, -0.7), fl=-0.3, ll=-0.4))
dd('bowls', K(ar=(-1.7, -0.3, 0.0), fr=-0.9, al=(-1.7, 0.3, 0.0), fl=-0.9, h=0.2),
   K(ar=(-2.4, 0.2, 0.9), fr=-0.3, al=(-2.4, -0.2, -0.9), fl=-0.3, h=-0.5, t=(-0.2, 0.0)),
   a=K(ar=(-1.9, -0.2, 0.3), fr=-0.6, al=(-1.9, 0.2, -0.3), fl=-0.6, h=-0.1, t=(0.0, 0.0), dn=1),
   beats=7, step=20)
dd('veil', K(ar=(-1.2, -1.2, -0.2), fr=-1.8, al=(-1.2, 1.2, 0.2), fl=-1.8, t=(0.5, 0.0), h=0.6, dn=2.5),
   K(ar=(-0.8, 0.0, 1.6), fr=0.0, al=(-0.8, 0.0, -1.6), fl=0.0, t=(-0.5, 0.0), h=-0.8, dn=-1))
dd('soul', K(ar=(-1.7, -0.2, 0.0), fr=0.0, t=(0.4, 0.1), h=0.1, ll=-0.5, sl=0.4, dn=1.5, al=(-0.4, 0.0, -0.5), fl=-0.4),
   K(ar=(-1.2, -0.5, 0.0), fr=-2.2, t=(-0.2, 0.1), h=-0.3, al=(-0.4, 0.0, -0.8), fl=-0.2, dn=0.5))
dd('halo', K(ar=(-1.4, 1.4, 0.6), fr=-0.3, t=(0.1, 1.1), hy=0.4, dn=2, al=(-0.8, 0.0, -0.4), fl=-0.4),
   K(ar=(-1.5, -1.3, 0.0), fr=0.0, t=(0.25, -1.0), hy=-0.3, ll=-0.6, sl=0.4, dn=2, al=(-0.3, 0.3, -0.6), fl=-0.4))
dd('feathers', K(ar=(-2.6, 0.0, 1.4), fr=0.0, al=(-2.6, 0.0, -1.4), fl=0.0, t=(-0.4, 0.0), h=-0.5),
   K(ar=(-1.0, -0.6, 0.5), fr=-0.2, al=(-1.0, 0.6, -0.5), fl=-0.2, t=(0.6, 0.0), dn=2.5),
   beats=3, step=8, recoil=True)
dd('crucify', K(ar=(0.0, 0.0, 1.57), fr=0.0, al=(0.0, 0.0, -1.57), fl=0.0, h=-0.3),
   K(ar=(-3.0, 0.2, 0.4), fr=0.0, al=(0.3, 0.0, -0.9), fl=0.0, h=-0.5, t=(-0.2, 0.0), dn=-0.5))
dd('creation', K(ar=(-1.3, -0.8, 0.0), fr=-1.3, al=(-1.3, 0.8, 0.0), fl=-1.3, h=0.5, t=(0.2, 0.0)),
   K(ar=(-2.4, 0.0, 1.0), fr=0.0, al=(-2.4, 0.0, -1.0), fl=0.0, h=-0.6, t=(-0.3, 0.0), dn=-1))
dd('dawn', K(ar=(-3.1, 0.0, 0.1), fr=-0.6, al=(-3.1, 0.0, -0.1), fl=-0.6, t=(-0.5, 0.0), h=-0.5, dn=-1),
   K(ar=(-0.9, 0.0, 0.0), fr=0.0, al=(-0.9, 0.05, 0.0), fl=0.0, t=(0.7, 0.0), dn=3.5, lr=-0.8, sr=0.5, ll=0.4),
   weapon='sword')
dd('swords', K(ar=(-3.1, 0.0, 0.0), fr=0.0, al=(-0.6, 0.0, -0.5), fl=-0.3, h=-0.6),
   K(ar=(-1.5, 0.0, 0.0), fr=0.0, al=(-0.6, 0.0, -0.5), fl=-0.3, t=(0.3, 0.0), h=0.0, dn=1),
   weapon='sword')
dd('overflow', K(ar=(-2.0, 2.4, 1.6), fr=0.6, al=(0.8, -2.0, -1.4), fl=-1.9, t=(0.0, 0.3, 0.8), h=(0.0, 1.2, 0.0)),
   K(ar=(-1.6, -2.0, 0.4), fr=-0.2, al=(-2.6, 1.5, -0.6), fl=0.4, t=(0.2, -1.0, -0.3), h=(0.3, -0.8, -0.8), dn=1),
   a=K(ar=(0.6, 1.8, 1.4), fr=-1.5, al=(-0.6, -1.9, -1.2), fl=0.3, t=(-0.3, 1.0, 0.5), h=(-0.4, 1.4, 0.8), dn=2),
   beats=5, step=4, weapon='broken')
dd('panic', K(ar=(0.0, 0.0, 1.57), fr=0.0, al=(0.0, 0.0, -1.57), fl=0.0),
   K(ar=(-3.0, 0.0, 2.2), fr=0.6, al=(-3.0, 0.0, -2.2), fl=0.6, t=(-0.6, 0.0), h=(-1.0, 3.1, 0.0), dn=-2,
     lr=-0.5, ll=0.5), weapon='broken')
dd('leapin', K(ar=(0.8, 0.0, 0.3), al=(0.8, 0.0, -0.3), t=(0.4, 0.0), dn=6, lr=-0.8, sr=1.5, ll=-0.8, sl=1.5),
   K(ar=(-2.6, 0.0, 0.6), al=(-2.6, 0.0, -0.6), t=(0.2, 0.0), dn=-3, lr=-1.2, sr=1.6, ll=-1.0, sl=1.4))
dd('rain', K(al=(-3.0, 0.0, 0.0), fl=0.0, ar=(-3.0, -0.5, 0.0), fr=-1.5, h=-0.9, t=(-0.45, 0.3)),
   K(al=(-3.0, 0.0, 0.0), fl=0.0, ar=(-2.6, 0.7, 0.8), fr=-0.3, h=-0.9, t=(-0.4, 0.3)), weapon='bow')
dd('triple', K(al=(-1.57, 0.0, 0.0), fl=0.0, ar=(-1.6, -0.7, 0.0), fr=-1.7, t=(0.0, 0.9), hy=0.3, dn=1.5),
   K(al=(-1.57, -0.35, 0.0), fl=0.0, ar=(-1.5, 0.45, 0.4), fr=-0.6, t=(0.0, 0.6), hy=0.3, dn=1.5),
   a=K(al=(-1.57, 0.35, 0.0), fl=0.0, ar=(-1.5, 0.75, 0.5), fr=-0.6, t=(0.0, 1.1), hy=0.3, dn=1.5),
   beats=3, step=6, weapon='bow')


ALL = dict(M)
ALL.update(D)


# --------------------------------------------------------------------------------------------------------------------
def keys(mo):
    """The motion's keys as full vectors: windup, then one per strike (the strikes alternate s and a)."""
    w = vec(mo['w'], mo['weapon'])
    s = vec(mo['s'], mo['weapon'])
    a = vec(mo['a'], mo['weapon']) if mo['a'] else None
    return w, s, a


def render_pose(v, weapon):
    """A vector as sculpt.render's pose (absolute arm turns; the rig's weapon bones get their added turn)."""
    st = WEAPONS[weapon]['stance']
    g = lambda s: v[IX[s]]
    p = {
        'arm_r': (g('ar.x'), g('ar.y'), g('ar.z')), 'arm_l': (g('al.x'), g('al.y'), g('al.z')),
        'fore_r': (g('fr'), 0, 0), 'fore_l': (g('fl'), 0, 0),
        'torso': (g('t.x'), g('t.y'), g('t.z')), 'head': (g('h.x'), g('h.y'), g('h.z')),
        'hips': (0, g('hy'), 0), 'leg_r': (g('lr'), 0, 0), 'leg_l': (g('ll'), 0, 0),
        'shin_r': (g('sr'), 0, 0), 'shin_l': (g('sl'), 0, 0),
        'root': (0, 0, 0, 0, g('dn'), 0),
    }
    if st:
        for side in ('r', 'l'):
            p[f'arms_{st}_{side}'] = (g('w' + side), 0, 0)
    else:
        p['sword'] = (g('wr'), 0, 0)
        p['shield'] = (g('wl'), 0, 0)
    return p


def sheet_spec(weapon, ids=None, frames=('w', 's', 'a')):
    """posesheet.py's spec for one weapon's motions (windup, strike and the second strike when there is one)."""
    st = WEAPONS[weapon]['stance']
    hide = []
    if WEAPONS[weapon]['rig'] == 'villager_king_divine':
        hide = [f'arms_{o}_' for o in HOLD if o != st] + ['wing', 'veil_', 'fly_', 'flies', 'souls', 'lightnings',
                                                           'seven_stars', 'ophan', 'corona', 'halo']
    poses = []
    for id_, mo in ALL.items():
        if mo['weapon'] != weapon or (ids and id_ not in ids):
            continue
        w, s, a = keys(mo)
        for f, v in (('w', w), ('s', s), ('a', a)):
            if v is not None and f in frames:
                poses.append([f'{id_} {f}', {k: list(x) for k, x in render_pose(v, weapon).items()}])
    return dict(poses=poses, hide=hide)


# --------------------------------------------------------------------------------------------------------------------
def export_java(path):
    """jp.oror.reborn.king.KingMotions: every motion's keys (absolute arm/forearm x), beats, step and recoil."""
    def arr(v):
        return 'new float[]{' + ', '.join(f'{x:.3f}F' for x in v) + '}'
    lines = []
    for id_, mo in ALL.items():
        w, s, a = keys(mo)
        aa = arr(a) if a is not None else 'null'
        L = mo['length'] if mo['length'] else 0
        lines.append(f'        put("{id_}", {arr(w)},\n            {arr(s)},\n            {aa}, {mo["beats"]}, {mo["step"]}, '
                     f'{str(mo["recoil"]).lower()}, {L});')
    body = '\n'.join(lines)
    src = f'''package jp.oror.reborn.king;

import java.util.HashMap;
import java.util.Map;

/**
 * (055) Generated by tools/mc/king_moves.py, not edited by hand: the villager king's motions, one for each of his
 * seventy weapon moves (KingArsenal.MOVES) and each deed that had no pose of its own. Each is a windup key, a strike
 * key, an optional second strike key the strikes alternate with, how many strikes, how many ticks apart, and whether
 * he pulls back between them; and, where the strikes outlast it, the move's length. A key holds {N} values:
 * {', '.join(SLOTS)}. The upper arms' and forearms' x are absolute (KingRig takes the stance's hold off them); the
 * rest are offsets on the idle pose.
 */
public final class KingMotions {{
    public record Motion(float[] windup, float[] strike, float[] alt, int beats, int step, boolean recoil, int length) {{
    }}

    public static final int SLOTS = {N};
    private static final Map<String, Motion> ALL = new HashMap<>();

    private KingMotions() {{
    }}

    private static void put(String id, float[] w, float[] s, float[] a, int beats, int step, boolean recoil, int length) {{
        ALL.put(id, new Motion(w, s, a, beats, step, recoil, length));
    }}

    /** The motion of a move or deed by its id (sword_sweep, veil...), or null. */
    public static Motion get(String id) {{
        return ALL.get(id);
    }}

    static {{
{body}
    }}
}}
'''
    open(path, 'w').write(src)
    return len(ALL)


if __name__ == '__main__':
    import sys, json
    if sys.argv[1] == 'java':
        print(export_java(sys.argv[2]), 'motions')
    elif sys.argv[1] == 'spec':
        weapon, out = sys.argv[2], sys.argv[3]
        ids = sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] else None
        json.dump(sheet_spec(weapon, ids), open(out, 'w'))
        print(len(sheet_spec(weapon, ids)['poses']), 'poses')


# --------------------------------------------------------------------------------------------------------------------
def timeline(mo, t, windup, length):
    """KingRig.motion, the same steps: the full vector (absolute arms) at tick t of the move."""
    import math as _m
    hold = HOLD.get(WEAPONS[mo['weapon']]['stance'] or '', (0.0, 0.0, 0.0, 0.0))
    rest = vec({}, mo['weapon'])
    w, s, a = keys(mo)
    beats = max(1, mo['beats'])
    step = float(max(1, mo['step']))
    room = length - windup - 4.0
    if beats > 1 and (beats - 1) * step > room:
        step = max(2.0, room / (beats - 1))
    sw = min(4.0, max(2.0, windup / 3.0))
    lerp = lambda p, q, f: [x + (y - x) * f for x, y in zip(p, q)]
    ts, ks = [0.0, max(1.0, windup - sw)], [rest, w]
    prev, last = w, float(windup)
    for k in range(beats):
        hit = windup + k * step
        key = a if (a is not None and k % 2 == 1) else s
        swing = sw if k == 0 else min(sw, step * 0.6)
        if k > 0 and (a is None or mo['recoil']) and step >= 4:
            r = lerp(prev, w, 0.6)
            ts += [hit - step + min(step * 0.35, 2.0), hit - swing]
            ks += [prev, r]
            prev = r
        elif hit - swing > ts[-1]:
            ts.append(hit - swing); ks.append(prev)
        ts.append(hit); ks.append(key)
        prev, last = key, hit
    hold_end = min(length - 1.0, last + max(2.0, (length - last) * 0.35))
    if hold_end > last:
        ts.append(hold_end); ks.append(prev)
    wrapped = list(prev)
    for nm in TURNS:
        i = IX[nm]
        wrapped[i] = (wrapped[i] + _m.pi) % (2 * _m.pi) - _m.pi
    ts.append(max(hold_end, last)); ks.append(wrapped)
    ts.append(float(max(length, last + 2))); ks.append(rest)
    if t <= 0:
        return rest
    sm = lambda x: x * x * (3 - 2 * x)
    for i in range(len(ts) - 1):
        if ts[i] <= t < ts[i + 1] and ts[i + 1] > ts[i]:
            return lerp(ks[i], ks[i + 1], sm((t - ts[i]) / (ts[i + 1] - ts[i])))
    return rest
