"""Stats of the 41 characters (v0.17.6: "make them far more dangerous").

Reads the original roster (characters.json of the original jar) and writes the tuned copy into the overlay:
  health   x1.25, capped at 1024 (CharacterSpec rejects more; vanilla max health tops out there too)
  damage   x1.5   (melee and every ability that scales with it)
  mana     x1.5, regen x1.5 (abilities come round more often)
  cooldown x0.8, never below 20 ticks
  speed    0.29 -> 0.33
Lore soul pools (loreHealth / loreMana) are kept as they are. BossPowers.java adds the signature attacks, the
awakening and the resolve against huge single hits.
Usage: python3 -I boss_tuning.py <original characters.json> <overlay assets dir>"""
import json, os, sys


def tune(c):
    c = dict(c)
    c['health'] = float(min(1024.0, round(c['health'] * 1.25)))
    c['damage'] = round(c['damage'] * 1.5, 1)
    c['mana'] = round(c['mana'] * 1.5, 1)
    c['regen'] = round(c['regen'] * 1.5, 2)
    c['cooldown'] = max(20, int(round(c['cooldown'] * 0.8)))
    c['speed'] = max(c['speed'], 0.33)
    return c


def main(src, assets):
    roster = json.load(open(src, encoding='utf-8'))
    tuned = [tune(c) for c in roster]
    for c in tuned:
        assert 0 < c['health'] <= 1024 and c['cooldown'] >= 20 and c['mana'] > 0, c['id']
    with open(os.path.join(assets, 'characters.json'), 'w', encoding='utf-8') as fh:
        json.dump(tuned, fh, ensure_ascii=False, indent=2)
    for a, b in list(zip(roster, tuned))[:3]:
        print(a['id'], {k: (a[k], b[k]) for k in ('health', 'damage', 'mana', 'regen', 'cooldown', 'speed')})
    print('characters', len(tuned))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
