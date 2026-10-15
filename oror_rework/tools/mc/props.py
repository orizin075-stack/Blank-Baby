"""Hand-held weapons and tools. Each prop lives on a bone at the palm (named prop_r / prop_l) so it
follows the arm through every animation; the renderer hides it while the entity holds a real item."""
import math
from paint import M

def hand(h, side='r', rot=(0.0, 0.0, 0.0)):
    arm = h.arm_r if side == 'r' else h.arm_l
    px = arm.pivot[0]
    y = h.top + h.arm_len - 1.5
    b = h.rig.bone('prop_' + side, arm, (px, y, 0), rot=rot)
    return b, (px, y, 0)

# all blades are modelled pointing "up" (-y) from the grip; the bone rotation aims them
POINT_FORWARD = (1.25, 0.0, 0.0)      # vanilla-like hold: blade forward and a little up
POINT_DOWN = (2.9, 0.0, 0.0)          # reverse grip / lowered blade
UPRIGHT = (0.12, 0.0, 0.0)            # staffs: held upright beside the body

def upright(side, lean=0.28):
    """Staff aim for the given hand: upright, top leaning outward away from the head."""
    return (0.12, 0.0, -lean if side == 'r' else lean)

def sword(b, at, blade, guard, grip, length=14, width=2, guard_w=4, pommel=None, edge=None):
    x, y, z = at
    b.box((x - 0.5, y - 1.5, z - 0.5), (1, 3, 1), grip, name='grip')
    if pommel:
        b.box((x - 0.5, y + 1.5, z - 0.5), (1, 1, 1), pommel, name='pommel')
    b.box((x - guard_w / 2, y - 2.5, z - 1), (guard_w, 1, 2), guard, name='guard')
    b.box((x - 0.5, y - 2.5 - length, z - width / 2), (1, length, width), blade, name='blade')
    b.box((x - 0.5, y - 3.5 - length, z - width / 2 + 0.5), (1, 1, max(1, width - 1)), blade, name='tip')
    if edge:
        b.box((x - 0.5, y - 2.5 - length, z - width / 2 - 0.25), (1, length, 0), edge, name='edge')

def katana(b, at, blade, tsuba, tsuka, length=15):
    x, y, z = at
    b.box((x - 0.5, y - 1.5, z - 0.5), (1, 4, 1), tsuka, name='tsuka')
    b.box((x - 1, y - 2.5, z - 1), (2, 1, 2), tsuba, name='tsuba')
    half = length // 2
    b.box((x - 0.5, y - 2.5 - half, z - 1), (1, half, 2), blade, name='blade')
    tip = b.rig.bone(b.name + '_curve', b, (x, y - 2.5 - half, z), rot=(0.1, 0, 0))
    tip.box((x - 0.5, y - 2.5 - length, z - 1), (1, length - half - 1, 2), blade, name='blade2')
    tip.box((x - 0.5, y - 3.5 - length + 1, z), (1, 1, 1), blade, name='kissaki')

def staff(b, at, shaft, length=26, below=9):
    x, y, z = at
    b.box((x - 0.5, y - (length - below), z - 0.5), (1, length, 1), shaft, name='shaft')
    return (x, y - (length - below), z)          # top of the shaft

def orb_head(b, top, orb, prong):
    x, y, z = top
    b.box((x - 1, y - 3, z - 1), (2, 2, 2), orb, grow=0.25, name='orb')
    b.box((x - 1.5, y - 1, z - 0.5), (3, 1, 1), prong, name='collar')
    for sx in (-1, 1):
        b.box((x + sx * 1.5 - 0.5, y - 4, z - 0.5), (1, 3, 1), prong, name='prong')

def star_head(b, top, star, ring):
    x, y, z = top
    b.box((x - 3, y - 7, z), (6, 6, 0), ring, name='ring')
    b.box((x - 1, y - 5, z - 1), (2, 2, 2), star, name='star')

def cross_head(b, top, metal, gem):
    x, y, z = top
    b.box((x - 0.5, y - 6, z - 0.5), (1, 6, 1), metal, name='cross_v')
    b.box((x - 2.5, y - 4.5, z - 0.5), (5, 1, 1), metal, name='cross_h')
    b.box((x - 1, y - 5, z - 1), (2, 2, 2), gem, name='gem')

def dragon_head(b, top, metal, gem):
    x, y, z = top
    b.box((x - 1, y - 3, z - 1.5), (2, 3, 3), metal, name='dragon')
    b.box((x - 0.5, y - 2.5, z - 3), (1, 1, 2), metal, name='snout')
    b.box((x - 0.5, y - 4, z - 0.5), (1, 1, 1), gem, name='pearl')

def crook_head(b, top, wood, gem):
    x, y, z = top
    b.box((x - 0.5, y - 2, z - 0.5), (1, 2, 1), wood, name='crook1')
    b.box((x - 0.5, y - 3, z - 2.5), (1, 1, 3), wood, name='crook2')
    b.box((x - 0.5, y - 2, z - 3.5), (1, 2, 1), wood, name='crook3')
    b.box((x - 1, y - 2.5, z - 2.5), (2, 2, 2), gem, name='gem')

def wrench(b, at, metal, grip):
    x, y, z = at
    b.box((x - 0.5, y - 1.5, z - 0.5), (1, 3, 1), grip, name='grip')
    b.box((x - 0.5, y - 9, z - 0.5), (1, 8, 1), metal, name='shaft')
    b.box((x - 1, y - 11, z - 1.5), (2, 2, 3), metal, name='jaw')
    b.box((x - 1, y - 12, z - 1.5), (2, 1, 1), metal, name='tooth')

def hammer(b, at, head, handle):
    x, y, z = at
    b.box((x - 0.5, y - 9, z - 0.5), (1, 11, 1), handle, name='handle')
    b.box((x - 1.5, y - 12, z - 2.5), (3, 3, 5), head, name='head')

def flask(b, at, glass, liquid):
    x, y, z = at
    b.box((x - 1, y - 2, z - 1.5), (2, 3, 2), liquid, name='liquid')
    b.box((x - 0.5, y - 4, z - 1), (1, 2, 1), glass, name='neck')

def lantern(b, at, light, frame):
    x, y, z = at
    b.box((x - 0.5, y - 1, z - 0.5), (1, 3, 1), frame, name='hook')
    b.box((x - 1.5, y + 2, z - 1.5), (3, 4, 3), light, name='lamp')
    b.box((x - 1.5, y + 2, z - 1.5), (3, 1, 3), frame, grow=0.25, name='cap')

def book(b, at, cover, pages):
    x, y, z = at
    b.box((x - 2, y - 1, z - 2.5), (1, 5, 4), cover, name='cover')
    b.box((x - 1, y - 0.5, z - 2), (1, 4, 3), pages, name='pages')

def scroll(b, at, paper, rod):
    x, y, z = at
    b.box((x - 0.5, y - 2, z - 2), (1, 1, 4), rod, name='rod')
    b.box((x - 0.5, y - 1, z - 1.5), (0, 5, 3), paper, name='paper')

def claws(h, side, mat, length=3):
    """Three blade-like claws growing from the fingertips."""
    b, (x, y, z) = hand(h, side, (0.25, 0, 0))
    for k, dz in enumerate((-1.5, -0.5, 0.5)):
        b.box((x - 0.5 + (k - 1) * 0.0, y + 1.5, z + dz - 0.5), (1, length, 0), mat, name='claw')
    return b
