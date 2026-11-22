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


for z in jars:
    arm = [n for n in z.namelist() if 'armature' in n and 'biped' in n][:5]
    if arm:
        print('armature files', arm)
        print(z.read(arm[0]).decode('utf-8', 'replace')[:2500])

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
        row = ' '.join(f"{j}=({world[j][3]:.2f},{world[j][7]:.2f},{world[j][11]:.2f})" for j in ('Root', 'Head', 'Hand_R', 'Hand_L', 'Tool_R', 'Knee_R') if j in world)
        print(f'  t={t:.2f} {row}')
