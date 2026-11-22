"""ef_fk.py <jar> [<jar> ...]: Epic Fight's biped animations, their joints' world positions by forward kinematics (each
joint's local 4x4 of the JSON, row-major, translation in the last column, times its parent's), for the idle pose and a
few frames of an attack, a guard and a parry; the frame OROR's own models need to borrow Epic Fight's motions."""
import json, sys, zipfile

TREE = {'Root': None, 'Thigh_R': 'Root', 'Leg_R': 'Thigh_R', 'Knee_R': 'Leg_R', 'Thigh_L': 'Root', 'Leg_L': 'Thigh_L', 'Knee_L': 'Leg_L',
        'Torso': 'Root', 'Chest': 'Torso', 'Head': 'Chest', 'Shoulder_R': 'Chest', 'Arm_R': 'Shoulder_R', 'Elbow_R': 'Arm_R', 'Hand_R': 'Elbow_R',
        'Tool_R': 'Hand_R', 'Shoulder_L': 'Chest', 'Arm_L': 'Shoulder_L', 'Elbow_L': 'Arm_L', 'Hand_L': 'Elbow_L', 'Tool_L': 'Hand_L'}


def mul(a, b):
    return [sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)) for r in range(4) for c in range(4)]


def at(sheet, t):
    times, mats = sheet['time'], sheet['transform']
    i = 0
    while i + 1 < len(times) and times[i + 1] <= t:
        i += 1
    return mats[i]


jars = [zipfile.ZipFile(p) for p in sys.argv[1:]]


def load(ns, path):
    name = f'assets/{ns}/animmodels/animations/{path}.json'
    for z in jars:
        if name in z.namelist():
            return {j['name']: j for j in json.loads(z.read(name))['animation']}
    return None


# (run 2) the hierarchy and the bind pose from the biped model's own file (no armature file of its own in 1.21.1)
def find_tree():
    for z in jars:
        for n in z.namelist():
            if n.startswith('assets/epicfight/animmodels/') and n.endswith('.json') and '/animations/' not in n and 'biped' in n:
                d = json.loads(z.read(n))
                arm = d.get('armature')
                if not arm:
                    continue
                print('model file', n, 'armature keys', list(arm.keys()))
                tree, bind = {}, {}
                def walk(node, parent):
                    tree[node['name']] = parent
                    if 'transform' in node:
                        bind[node['name']] = node['transform']
                    for c in node.get('children', []):
                        walk(c, node['name'])
                for root in arm.get('hierarchy', []):
                    walk(root, None)
                print('hierarchy', tree)
                return tree, bind
    return None, None


t2, BIND = find_tree()
if t2:
    TREE = t2

if BIND:
    world = {}
    for j in TREE:
        if j in BIND:
            p = TREE[j]
            world[j] = mul(world[p], BIND[j]) if p and p in world else BIND[j]
    print('bind', ' '.join(f"{j}=({world[j][3]:.2f},{world[j][7]:.2f},{world[j][11]:.2f})" for j in world))

for ns, path in [('epicfight', 'biped/living/idle'), ('epicfight', 'biped/combat/sword_auto1'), ('epicfight', 'biped/skill/guard_sword'),
                 ('epicfight', 'biped/skill/guard_sword_hit_active1'), ('efn', 'biped/nf_sword/nf_sword_auto1'), ('epicfight', 'biped/combat/hit_short')]:
    a = load(ns, path)
    if not a:
        print('no', ns, path); continue
    end = max(max(j['time']) for j in a.values())
    print('==', ns, path, 'joints', len(a), 'length', end, 'unknown joints', [k for k in a if k not in TREE])
    for t in sorted(set([0.0, end * 0.33, end * 0.66, end])):
        world = {}
        for j in TREE:
            if j not in a:
                continue
            m = at(a[j], t)
            p = TREE[j]
            world[j] = mul(world[p], m) if p and p in world else m
        row = ' '.join(f"{j}=({world[j][3]:.2f},{world[j][7]:.2f},{world[j][11]:.2f})" for j in ('Root', 'Torso', 'Chest', 'Head', 'Shoulder_R', 'Arm_R', 'Elbow_R', 'Hand_R', 'Tool_R', 'Thigh_R', 'Leg_R', 'Knee_R') if j in world)
        print(f'  t={t:.2f} {row}')

# (run 3) each joint's move from rest (world now x world rest^-1, the step forward taken out): the turn's angle and axis,
# for what OROR's models will do with it
import math


def inv_rigid(m):
    r = [[m[0], m[1], m[2]], [m[4], m[5], m[6]], [m[8], m[9], m[10]]]
    t = [m[3], m[7], m[11]]
    rt = [[r[j][i] for j in range(3)] for i in range(3)]
    ti = [-sum(rt[i][k] * t[k] for k in range(3)) for i in range(3)]
    return [rt[0][0], rt[0][1], rt[0][2], ti[0], rt[1][0], rt[1][1], rt[1][2], ti[1], rt[2][0], rt[2][1], rt[2][2], ti[2], 0, 0, 0, 1]


def angle_axis(m):
    tr = m[0] + m[5] + m[10]
    a = math.degrees(math.acos(max(-1, min(1, (tr - 1) / 2))))
    ax = (m[9] - m[6], m[2] - m[8], m[4] - m[1])
    n = math.sqrt(sum(x * x for x in ax)) or 1
    return a, tuple(round(x / n, 2) for x in ax)


if BIND:
    bw = {}
    for j in TREE:
        if j in BIND:
            p = TREE[j]
            bw[j] = mul(bw[p], BIND[j]) if p and p in bw else BIND[j]
    for ns, path in [('efn', 'biped/nf_sword/nf_sword_auto1'), ('efn', 'biped/nf_sword/nf_sword_auto2'), ('epicfightx', 'biped/combat/fist_auto1'),
                     ('epicfight', 'biped/combat/sword_auto1')]:
        a = load(ns, path)
        if not a:
            print('no', ns, path); continue
        print('== moves', ns, path)
        for t in (0.15, 0.3, 0.5, 0.8):
            world = {}
            for j in TREE:
                if j in a:
                    m = at(a[j], t)
                elif j in bw:
                    pj = TREE[j]
                    m = mul(inv_rigid(bw[pj]), bw[j]) if pj else bw[j]
                else:
                    continue
                p = TREE[j]
                world[j] = mul(world[p], m) if p and p in world else m
            row = []
            for j in ('Root', 'Torso', 'Chest', 'Head', 'Arm_R', 'Hand_R', 'Thigh_R'):
                if j in world and j in bw:
                    d = mul(world[j], inv_rigid(bw[j]))
                    ang, ax = angle_axis(d)
                    row.append(f'{j} {ang:.0f}deg{ax}')
            print(f'  t={t}: ' + '; '.join(row))

# (run 4) Epic Fight keeps a joint's pose at runtime as its change from rest (rest local^-1 x animation local): the same
# for nf_sword_auto1, to set beside the husk's logged pose (look 'motion', efpose lines)
def quat(m):
    r = [[m[0], m[1], m[2]], [m[4], m[5], m[6]], [m[8], m[9], m[10]]]
    tr = r[0][0] + r[1][1] + r[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return ((r[2][1] - r[1][2]) / s, (r[0][2] - r[2][0]) / s, (r[1][0] - r[0][1]) / s, 0.25 * s)
    if r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        s = math.sqrt(1.0 + r[0][0] - r[1][1] - r[2][2]) * 2
        return (0.25 * s, (r[0][1] + r[1][0]) / s, (r[0][2] + r[2][0]) / s, (r[2][1] - r[1][2]) / s)
    if r[1][1] > r[2][2]:
        s = math.sqrt(1.0 + r[1][1] - r[0][0] - r[2][2]) * 2
        return ((r[0][1] + r[1][0]) / s, 0.25 * s, (r[1][2] + r[2][1]) / s, (r[0][2] - r[2][0]) / s)
    s = math.sqrt(1.0 + r[2][2] - r[0][0] - r[1][1]) * 2
    return ((r[0][2] + r[2][0]) / s, (r[1][2] + r[2][1]) / s, 0.25 * s, (r[1][0] - r[0][1]) / s)


if BIND:
    a = load('efn', 'biped/nf_sword/nf_sword_auto1')
    for t in (0.13, 0.267, 0.456):
        row = []
        for j in ('Root', 'Torso', 'Chest', 'Arm_R', 'Hand_R', 'Tool_R', 'Thigh_R'):
            if j in a and j in BIND:
                d = mul(inv_rigid(BIND[j]), at(a[j], t))
                q = quat(d)
                row.append(f'{j} t({d[3]:.2f},{d[7]:.2f},{d[11]:.2f}) q({q[0]:.2f},{q[1]:.2f},{q[2]:.2f},{q[3]:.2f})')
                b = BIND[j]; qb = quat(b)
                row.append(f'[rest {j} t({b[3]:.2f},{b[7]:.2f},{b[11]:.2f}) q({qb[0]:.2f},{qb[1]:.2f},{qb[2]:.2f},{qb[3]:.2f})]')
        print(f'delta t={t}: ' + ' '.join(row))
