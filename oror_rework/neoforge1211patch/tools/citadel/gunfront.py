"""gunfront.py <template dir> [report.json]: no gun looks into a wall (059g, the user again: "砲台の前の壁消し切れてない
全部見直し"). Run after fieldfire.py.

fieldfire.py (059f) opened each gun's front over 150 degrees, keeping what goes on up past the parapet (towers, the
gates). Rays straight ahead of each gun (fire_audit.ahead_open: within 25 degrees of its facing, level and up, out to
12 blocks) still met something at ten posts, all of them standing beside a gate: a wall battery and five casemates
whose facing grazed the gate tower's flank six to ten blocks off, and four anti-aircraft guns looking into a paddock's
fence or a wall ten blocks off. A gate's towers are not to be cut, so each of these guns is turned away from what it
looked into, by the least of 5, 10, ... 40 degrees that leaves the ground straight ahead of it open (and of those the
one leaving its wider front, 45 degrees either side, the most open). CitadelUpdate turns a world's guns already at
these posts to their posts' new facing.
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_io
import fire_audit as FA

TURN = ('battery', 'casemate', 'aa', 'redoubt', 'crossfire')


def main():
    folder = sys.argv[1]
    t = template_io.Template(folder)
    gp = os.path.join(folder, 'garrison.json')
    g = json.load(open(gp))
    turned, left = [], []
    for e in g['entries']:
        if not e.get('vehicle') or e.get('post') not in TURN:
            continue
        if FA.ahead_open(t, e) >= 1.0:
            continue
        best = None
        for off in range(5, 45, 5):
            for sgn in (1, -1):
                yaw = e['yaw'] + sgn * off
                if FA.ahead_open(t, e, yaw) >= 1.0:
                    wide = FA.ahead_open(t, e, yaw, half=45)
                    if best is None or wide > best[1] + 1e-9:
                        best = (yaw, wide, sgn * off)
            if best is not None:
                break
        if best is None:
            left.append(dict(post=e['post'], x=e['x'], y=e['y'], z=e['z'], yaw=e['yaw']))
            continue
        yaw = ((best[0] + 180.0) % 360.0) - 180.0
        turned.append(dict(post=e['post'], x=e['x'], y=e['y'], z=e['z'], was=e['yaw'], yaw=round(yaw, 1), turned=best[2],
                           front45=round(best[1], 3)))
        e['yaw'] = round(yaw, 1)
    json.dump(g, open(gp, 'w'), indent=0)
    out = dict(turned=turned, left=left)
    print(json.dumps(out, indent=1))
    if len(sys.argv) > 2:
        json.dump(out, open(sys.argv[2], 'w'), indent=1)


if __name__ == '__main__':
    main()
