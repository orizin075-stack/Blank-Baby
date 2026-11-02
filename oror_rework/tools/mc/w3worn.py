"""The gear worn on the body (052, Curios): each piece is the item's own 3D model at the size it is worn, with what holds
it on (a chain, a ribbon, a bracer, a glove, the harness of a back banner), as one OBJ, drawn by the patch's worn-gear
layer on the body part it hangs from (WornGearLayer: the part's ModelPart.translateAndRotate, then turned over about x
so that the model's up is up and its front is the wearer's front).

Design space: texels (32 to the block) from the part's pivot; u up, v to the wearer's left, w forward (the OBJ's y, x,
z: obj = 0.5 + (v, u, w) / 32). The parts, as HumanoidModel has them (standing): body and head pivot at the neck (body
u 0..-24, v -8..8, w -4..4; head u 0..16, v -8..8, w -8..8); the right arm's pivot 2 px under the shoulder top, 5 px to
the right (the arm v -6..2, u 4..-20, w -4..4: centred at v -2); the left arm mirrored (v -2..6, centred at v 2).

  python3 w3worn.py <assets root> [ids...]     models/item/gear3d/worn_<id>.obj (+ texture) and models/item/worn_<id>.json
  python3 w3worn.py --preview <png> [ids...]   each piece on a figure, from the front, the side and behind
"""
import json, math, os, sys
import numpy as np
from PIL import Image
import forge3d as F
import held as Hd
from forge3d import W3D
from paint import M
from w3parts import Mt, octo, front_plate, gem
import w3gear as G

NS = G.NS
TPB = 32.0


# ----------------------------------------------------------------------------------------------------- geometry help
def R3(rx=0.0, ry=0.0, rz=0.0):
    """Rotation in OBJ space (degrees about x = v, y = u, z = w), applied z, then y, then x."""
    return Hd.rot_xyz(rx, ry, rz)[:3, :3]


def obj_to_rig(Q):
    return np.stack([(Q[..., 0] - 0.5) * TPB, -(Q[..., 1] - 0.5) * TPB, -(Q[..., 2] - 0.5) * TPB], -1)


def placed(quads, k, R, at, pivot=None):
    """The item's quads (rig coords) with the pivot (design texels u, v, w of the item; default its middle) moved to
    `at` (design texels u, v, w of the piece), scaled k and turned R (OBJ space) about it."""
    allp = np.concatenate([F.to_obj_space(P) for P, *_ in quads])
    if pivot is None:
        c = (allp.min(0) + allp.max(0)) / 2
    else:
        c = 0.5 + np.array([pivot[1], pivot[0], pivot[2]], float) / TPB
    t = 0.5 + np.array([at[1], at[0], at[2]], float) / TPB
    out = []
    for P, UV, N, e in quads:
        Q = F.to_obj_space(P)
        Q = ((Q - c) * k) @ R.T + t
        n = np.array([N[0], -N[1], -N[2]], float) @ R.T
        out.append((obj_to_rig(Q), UV, np.array([n[0], -n[1], -n[2]]), e))
    return out


def merge(*parts):
    """(quads, atlas) pairs into one: the atlases side by side (16-texel aligned), the UVs moved with them."""
    W = sum(int(math.ceil(a.shape[1] / 16.0)) * 16 for _, a in parts)
    H = max(int(math.ceil(a.shape[0] / 16.0)) * 16 for _, a in parts)
    atlas = np.zeros((H, W, 4), np.uint8)
    quads, x = [], 0
    for q, a in parts:
        atlas[:a.shape[0], x:x + a.shape[1]] = a
        for P, UV, N, e in q:
            quads.append((P, np.asarray(UV, float) + np.array([x, 0.0]), N, e))
        x += int(math.ceil(a.shape[1] / 16.0)) * 16
    return quads, atlas, (W, H)


def item(rid):
    w, _, _ = G.build(rid)
    q, a, _ = w.build()
    return q, a


def seg(g, a, b, t, mat, name, d=None):
    """A strand (chain, strap, cord) from a to b (u, v, w), t thick across, d deep (default t)."""
    a, b = np.array(a, float), np.array(b, float)
    m = (a + b) / 2
    du, dv, dw = b - a
    L = math.sqrt(du * du + dv * dv + dw * dw)
    # turn the box's length (its u) onto the strand: about w by the lean in the u-v plane, then about v for the depth
    lean = math.degrees(math.atan2(dv, du))
    tip = math.degrees(math.atan2(dw, math.hypot(du, dv)))
    gg = g.group(m[0], m[1], m[2], rot=(0, 0, 0), name=name + '_at')
    gg = gg.group(0, 0, 0, rot=(0, 0, -lean), name=name + '_lean')
    gg = gg.group(0, 0, 0, rot=(0, tip, 0), name=name + '_tip')
    gg.box(0, 0, 0, L, t, t if d is None else d, mat, name=name)


def chain(g, pts, mat, name, t=0.9):
    for i in range(len(pts) - 1):
        seg(g, pts[i], pts[i + 1], t, mat, f'{name}{i}')


def shell(g, u, v, w, du, dv, dw, mat, name):
    """A band round a limb: a box a little bigger than the limb (the limb inside it is hidden)."""
    g.box(u, v, w, du, dv, dw, mat, name=name)


# ---------------------------------------------------------------------------------------------------- the pieces
def h_necklace(w, mat, front=4.5, back=-4.5, drop=8.5, top=6.0):
    """A chain (or ribbon) from under the head down over the chest to the pendant, and a little of it on the back."""
    chain(w, [(0.0, -top, front), (-drop * 0.55, -top * 0.45, front + 0.2), (-drop, 0.0, front + 0.3)], mat, 'l')
    chain(w, [(0.0, top, front), (-drop * 0.55, top * 0.45, front + 0.2), (-drop, 0.0, front + 0.3)], mat, 'r')
    chain(w, [(0.0, -top, back), (-3.0, 0.0, back - 0.2), (0.0, top, back)], mat, 'b')


def p_rewind_talisman(state=None):
    w = W3D('worn_rewind_talisman')
    h_necklace(w, Mt('metal', '#b8843a').b(), drop=7.5)
    gem(w, -7.8, 0, 4.8, 0.9, '#d8a456', name='bail', facet=False)
    hq, ha = w.build()[:2]
    iq, ia = item('rewind_talisman')
    return merge((hq, ha), (placed(iq, 0.27, R3(), (-11.6, 0, 5.1)), ia))


def p_villager_king_token(state=None):
    w = W3D('worn_villager_king_token')
    rib = M('cloth', '#9c1c26')
    for s in (-1, 1):
        seg(w, (0.0, s * 6.0, 4.5), (-8.4, s * 1.1, 4.8), 1.8, rib, f'rib{s}', d=0.5)
        seg(w, (0.0, s * 6.0, -4.5), (-3.0, s * 1.0, -4.7), 1.8, rib, f'back{s}', d=0.5)
    hq, ha = w.build()[:2]
    iq, ia = item('villager_king_token')
    # the medal, its own ribbon tails up into the ribbon round the neck
    return merge((hq, ha), (placed(iq, 0.3, R3(), (-12.6, 0, 5.1)), ia))


def p_parry_emblem(state=None):
    """The emblem worn on the left forearm as a small buckler, strapped on a leather bracer, its face outward."""
    w = W3D('worn_parry_emblem')
    leather = M('cloth', '#6a4a30')
    strap = M('cloth', '#3e2a1c')
    shell(w, -13.0, 2.0, 0.0, 9.0, 9.0, 9.0, leather, 'bracer')
    for k, u in enumerate((-9.6, -16.4)):
        shell(w, u, 2.0, 0.0, 1.6, 9.8, 9.8, strap, f'strap{k}')
    w.box(-13.0, 6.9, 0.0, 6.0, 1.0, 5.0, M('metal', '#8c95a4'), name='mount')
    hq, ha = w.build()[:2]
    rid = {'active': 'parry_emblem_active', 'recharging': 'parry_emblem_recharging'}.get(state, 'parry_emblem')
    iq, ia = item(rid)
    return merge((hq, ha), (placed(iq, 0.42, R3(0, 90, 0), (-13.0, 8.3, 0.0)), ia))


def p_dodge_talon(state=None):
    """The talon worn on the right hand: a dark glove, the iron foot on the back of the hand, the three claws out past
    the knuckles."""
    w = W3D('worn_dodge_talon')
    glove = M('cloth', '#2e2830')
    shell(w, -17.0, -2.0, 0.0, 7.0, 8.8, 8.8, glove, 'glove')
    shell(w, -13.4, -2.0, 0.0, 1.6, 9.4, 9.4, M('cloth', '#4a3c46'), 'cuff')
    hq, ha = w.build()[:2]
    rid = {'active': 'dodge_talon_active', 'recharging': 'dodge_talon_recharging'}.get(state, 'dodge_talon')
    iq, ia = item(rid)
    return merge((hq, ha), (placed(iq, 0.62, R3(0, 0, 180), (-18.5, -2.0, 5.2)), ia))


POLE_V = 7.0


def p_squad_banner(state=None):
    """The banner worn on the back (a sashimono): its pole in two brackets behind the back, clear of the head, the
    flag over the head; a harness crossed over the chest and the back."""
    w = W3D('worn_squad_banner')
    strap = M('cloth', '#5a3e28')
    iron = M('metal', '#596170')
    for s, f in ((-1, 4.5), (1, 4.5), (-1, -4.5), (1, -4.5)):
        seg(w, (0.0, s * 6.0, f), (-21.0, -s * 6.0, f + (0.2 if f > 0 else -0.2)), 1.6, strap, f'x{s}{f > 0}', d=0.5)
    for k, u in enumerate((-17.0, -5.0)):
        w.box(u, POLE_V, -6.8, 2.0, 2.0, 6.0, iron, name=f'bracket{k}')
        w.box(u, POLE_V, -9.6, 2.4, 3.2, 3.2, iron, name=f'ring{k}')
    hq, ha = w.build()[:2]
    rid = {'active': 'squad_banner_active', 'recharging': 'squad_banner_recharging'}.get(state, 'squad_banner')
    iq, ia = item(rid)
    # the pole's foot (item u -10) at the small of the back, behind the head, over the left shoulder blade; turned
    # about so that the flag hangs from it across the back to the right, over the head
    return merge((hq, ha), (placed(iq, 1.0, R3(0, 180, 0), (-21.0, POLE_V, -9.6), pivot=(-10.0, 0.0, 0.0)), ia))


def p_last_bloom(state=None):
    """The last bloom worn in the hair above the right ear, its face outward, its stem into the hair; a bud while it
    recharges."""
    rid = 'last_bloom_closed' if state == 'recharging' else 'last_bloom'
    iq, ia = item(rid)
    return merge((placed(iq, 0.5, R3(0, 0, 90), (11.0, -9.0, 1.0), pivot=(1.0, 0.0, 0.0)), ia))


PIECES = {  # id: (builder, the part it is worn on, its states)
    'rewind_talisman': (p_rewind_talisman, 'body', ()),
    'villager_king_token': (p_villager_king_token, 'body', ()),
    'parry_emblem': (p_parry_emblem, 'left_arm', ('active', 'recharging')),
    'dodge_talon': (p_dodge_talon, 'right_arm', ('active', 'recharging')),
    'squad_banner': (p_squad_banner, 'body', ('active', 'recharging')),
    'last_bloom': (p_last_bloom, 'head', ('recharging',)),
}


def variants():
    for rid, (fn, part, states) in PIECES.items():
        yield rid, None, fn, part
        for s in states:
            yield rid, s, fn, part


def name(rid, state):
    return 'worn_' + rid + ('_' + state if state else '')


def export(root, ids):
    md = os.path.join(root, 'models', 'item', 'gear3d')
    td = os.path.join(root, 'textures', 'item', 'gear3d')
    os.makedirs(md, exist_ok=True)
    os.makedirs(td, exist_ok=True)
    for rid, state, fn, part in variants():
        if ids and rid not in ids:
            continue
        nm = name(rid, state)
        quads, atlas, S = fn(state)
        F.write_obj(os.path.join(md, nm + '.obj'), quads, S)
        Image.fromarray(atlas, 'RGBA').save(os.path.join(td, nm + '.png'), optimize=True)
        model = {'loader': 'neoforge:obj', 'model': f'{NS}:models/item/gear3d/{nm}.obj', 'flip_v': False,
                 'emissive_ambient': True, 'automatic_culling': False,
                 'textures': {'tex': f'{NS}:item/gear3d/{nm}', 'particle': f'{NS}:item/{rid}'}}
        with open(os.path.join(root, 'models', 'item', nm + '.json'), 'w') as fh:
            json.dump(model, fh, indent=1)
        print(nm, part, len(quads), S, flush=True)


def worn_overrides(rid):
    """The item model's overrides for being worn (oror_supreme_bosses:worn = 1, set by the worn-gear layer while it
    draws), after its own state overrides so that they win (the last override that matches is used)."""
    fn, part, states = PIECES[rid]
    out = [{'predicate': {f'{NS}:worn': 1}, 'model': f'{NS}:item/{name(rid, None)}'}]
    level = {'recharging': 0.5, 'active': 1.0}
    for s in sorted(states, key=lambda s: level[s]):
        out.append({'predicate': {f'{NS}:worn': 1, f'{NS}:state': level[s]}, 'model': f'{NS}:item/{name(rid, s)}'})
    return out


# ----------------------------------------------------------------------------------------------------------- preview
ARM_SWING = {'right_arm': (-math.pi / 10, 0, 0)}
PARTS = {'body': ((0, 0, 0), (0, 0, 0)), 'head': ((0, 0, 0), (0, 0, 0)),
         'right_arm': (Hd.ARM_R['pivot'], (0, 0, 0)), 'left_arm': (Hd.ARM_L['pivot'], (0, 0, 0))}


def piece_matrix(part):
    piv, rot = PARTS[part]
    rot = ARM_SWING.get(part, rot) if part == 'right_arm' else rot
    return Hd.entity_base() @ Hd.part_matrix(piv, rot) @ Hd.Rx(math.pi) @ Hd.T(-0.5, -0.5, -0.5)


def preview(png, ids, frame=(0, 1.25, 3.4), size=(360, 520), yaws=(-20, 70, 160, -110)):
    body = Hd.player_quads()
    items = []
    for rid, state, fn, part in variants():
        if state or (ids and rid not in ids):
            continue
        quads, atlas, S = fn(None)
        items += F.world_quads(quads, atlas, piece_matrix(part))
    tiles = [F.render_quads(items + body, size, F.view_matrix(yaw, 8), frame=frame) for yaw in yaws]
    sheet = Image.new('RGB', (size[0] * len(tiles), size[1]), (30, 30, 36))
    for i, t in enumerate(tiles):
        sheet.paste(t if t.mode == 'RGB' else t.convert('RGB'), (i * size[0], 0))
    sheet.save(png)


if __name__ == '__main__':
    if sys.argv[1] == '--preview':
        preview(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] == '--close':
        # close up: --close <png> <x> <y> <span> ids...
        x, y, span = map(float, sys.argv[3:6])
        preview(sys.argv[2], sys.argv[6:], frame=(x, y, span), size=(420, 420), yaws=(-25, 25, 155, 205))
    else:
        export(sys.argv[1], sys.argv[2:])
