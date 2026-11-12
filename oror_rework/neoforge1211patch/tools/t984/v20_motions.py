"""(059c) The 984 techniques' motions as V20 rewrote them (01_gods_984_fx.md), over the parsed design v2 (t984_full.json).

Usage: v20_motions.py <01_gods_984_fx.md> <t984_full.json> <out.json>
       v20_motions.py merge <shipped waza984.json> <built waza984.json>   (the built table's colours and arcs into the
       shipped one, which keeps what apply_v20.py read from V20 for the rest)

For each technique V20 gives, besides its registered values, a 動作・モーション改稿 (the parts that move in its windup, what
they do, its blows at the hit ticks, the recovery) and a 粒子・光・音の改稿 (what is shown before, during, on a hit and
after, in its colours). The out table is the v2 one with:
* V20's timing, reach, behaviour and hits (relative to the end of the windup, as the table counts them): the motion's
  strikes then fall on the ticks the server strikes at (the 52 techniques V20 gave other hits kept their old motions in
  059a/b, their blades swinging at the old moments);
* the motion's text (motion_v20): V20's action (its timing words taken out) with the v2 description, V20's first where
  V20 gave the technique another behaviour, so that its primitives (cut, thrust, cast, summon...) are V20's; what the
  technique does (verbs, kind, count, props) is still read from the v2 text alone;
* the parts V20 names (blade, sheath, wings, tail, fist, gaze...) added to the parts the motion stresses (bones_v20);
* the look: V20's telegraph colours before v2's, so the colours of its warning, its ribbons and its burst are V20's.
build_waza.py makes the table and the motions from it; apply_v20.py then sets V20's registered shape, count and kind.
"""
import json, re, sys

ENTRY = re.compile(r'#### (.+?)（`([a-z_]+_\d+)`）\s*\n\*\*現行登録値\*\*：([A-Z]+)／予兆(\d+)tick、作用(\d+)tick、復帰(\d+)tick、CD(\d+)tick。'
                   r'射程([\d.]+)ブロック、形状コード(\d+)、count=(\d+)、発動基準イベント(\[[\d, ]*\]|個別指定なし)。')
PARA = re.compile(r'\*\*(動作・モーション改稿|当たり判定・効果改稿|粒子・光・音の改稿)\*\*：(.*)')
# V20's words for the parts that move -> the rig's bones (build_waza.BONE_ROLES)
PARTS = [(r'刀|剣|刃|槍|斧|槌|杖|鎌|武器|銃|砲身|弓', ['grip_r', 'arm_r', 'fore_r']), (r'鞘|腰', ['hips']),
         (r'拳|腕|手先|手首|掌|指|爪|鉤', ['arm_r', 'fore_r']), (r'両手|両腕', ['arm_r', 'arm_l']),
         (r'翼|羽', ['wing_r', 'wing_l']), (r'尾', ['tail1']), (r'首|頭|角|視線|目|瞳|顔', ['head', 'neck']),
         (r'顎|口|牙', ['jaw']), (r'脚|足|蹄', ['leg_r', 'leg_l']), (r'胸|胴|背|身体|肩|重心', ['torso', 'body']),
         (r'鰭', ['fin_r', 'fin_l'])]


def read(doc):
    out = {}
    matches = list(ENTRY.finditer(doc))
    for k, m in enumerate(matches):
        name, tid, beh, wu, ac, rc, cd, rng, shape, cnt, ev = m.groups()
        end = matches[k + 1].start() if k + 1 < len(matches) else len(doc)
        paras = {p.group(1): p.group(2).strip() for p in PARA.finditer(doc[m.end():end])}
        out[tid] = dict(name=name, beh=beh, wu=int(wu), ac=int(ac), rc=int(rc), cd=int(cd), rng=float(rng),
                        hits=json.loads(ev) if ev.startswith('[') else [], motion=paras.get('動作・モーション改稿', ''),
                        effect=paras.get('当たり判定・効果改稿', ''), fx=paras.get('粒子・光・音の改稿', ''))
    return out


def action(motion):
    """V20's motion without its timing words: the parts that move and what they do."""
    m = re.sub(r'予兆\d+～\d+tickで', '', motion)
    m = re.sub(r'発動[\d, ～]+tick(?:の有効時間)?に[^。]*。', '', m)
    m = re.sub(r'作用区間\d+～\d+tickを抜けると、\d+～\d+tickで姿勢を収める。', '', m)
    return m.strip()


def parts(motion):
    head = re.match(r'予兆\d+～\d+tickで(.*?)が動き', motion)
    words = head.group(1) if head else ''
    bones = []
    for pat, bs in PARTS:
        if re.search(pat, words):
            bones += [b for b in bs if b not in bones]
    return bones


def telegraph(fx):
    m = re.search(r'先行表示：(.*?)の外縁', fx)
    return m.group(1) if m else ''


def main(doc_path, full_path, out_path):
    v20 = read(open(doc_path, encoding='utf-8').read())
    d = json.load(open(full_path, encoding='utf-8'))
    assert len(v20) == len(d['techniques']) == 984, (len(v20), len(d['techniques']))
    changed = timing = 0
    for t in d['techniques']:
        r = v20[t['id']]
        assert (t['windup'], t['active'], t['recovery'], t['cooldown']) == (r['wu'], r['ac'], r['rc'], r['cd']), t['id']
        hits = [h - r['wu'] for h in r['hits']]
        if hits != t['hits']:
            timing += 1
        other = t['behaviour'] != r['beh']
        changed += other
        t['behaviour'], t['range'], t['hits'] = r['beh'], r['rng'], hits
        act = action(r['motion'])
        # the motion only: what the technique does (its verbs, kind, count, props) stays as the design's text has it
        t['motion_v20'] = (act + '。' + t['motion']) if other else (t['motion'] + '。' + act)
        t['bones_v20'] = list(dict.fromkeys(t['bones'] + parts(r['motion'])))
        tel = telegraph(r['fx'])
        if tel:
            look = t['look']
            first, rest = (look.split('／', 1) + [''])[:2] if '／' in look else ('', look)
            t['look'] = first + '／' + tel + '、' + rest
    json.dump(d, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False)
    print('techniques', len(d['techniques']), 'with another behaviour', changed, 'with other hits', timing)


def merge(shipped, built):
    cur = json.load(open(shipped, encoding='utf-8'))
    new = json.load(open(built, encoding='utf-8'))
    for a, b in zip(cur['techniques'], new['techniques']):
        assert a[0] == b[0] and a[5] == b[5] and a[11] == b[11], a[0]
        a[16], a[21] = b[16], b[21]
    json.dump(cur, open(shipped, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    if sys.argv[1] == 'merge':
        merge(*sys.argv[2:4])
    else:
        main(*sys.argv[1:4])
