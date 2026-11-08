"""(054) Build the villager king's form rigs (king3d) with build_bb's pipeline: rigs.json entries, meshes, textures,
glow textures and preview sheets.

  python3 build_king.py <out dir> [names...]"""
import json, os, sys
import build_bb as BB
import king3d
import azazel3d   # (056) Azazel registers his recipe with king3d.RECIPES


def main(outdir, names=None):
    names = names or list(king3d.RECIPES)
    rp = os.path.join(outdir, 'rigs.json')
    rigs = json.load(open(rp)) if os.path.exists(rp) else {}
    for n in names:
        j, q, d, size = BB.build_one(n, king3d.RECIPES[n], outdir)
        rigs[n] = j
        print(f'{n}: {q} quads, atlas {size}, bones {len(j["bones"])}, height {j["height"]}', flush=True)
    json.dump(rigs, open(rp, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:] or None)
