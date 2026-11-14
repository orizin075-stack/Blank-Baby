"""fieldclear.py <template dir> [report.json]: no field under anything that stands in the capital's farmland (059g, the user
again: "畑に塔があったりするの何とかして 置くんだったらその場所から畑をなくして"). Run after fieldfire.py.

fieldfire.py (059f) paved only the nine blocks round each anti-aircraft gun in a field. Looked at from above, the farm
ring between the third and the outermost wall still has the kingdom's own buildings standing in its fields: four stone
towers (silos) 37 blocks high with dark oak caps, watchtowers under copper roofs, barns, depots and storehouses, the
anti-aircraft guns' pads, and the outermost wall's round towers and buttresses reaching into the fields along it.

Every field plot (its farmland and its water channels, between the hedges and lanes) is checked for anything standing on
it (any block from the farmland's level up that is not a crop, water, grass, a flower, a hedge's leaves, a fence, a
light or a hay bale), and for an anti-aircraft gun's post:
* when a building stands in the plot (forty columns of it or more inside the plot, not just at its edge), or the field
  would lose a third of itself round it anyway, the plot stops being a field: its farmland becomes grass, its crops
  go, its water channels are filled with grass;
* round anything smaller (the outer wall's lamp pillars, three by three, a post) or anything that only reaches in at
  the plot's edge (a wall's tower, a building next door), the field is cut back to three blocks from it, the same way.
The hedges, the lanes and every other field stay as they were.
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import template_io

X0, X1, Z0, Z1 = -640, 640, -640, 640
YLO, YHI = 60, 110
MARGIN = 3
BIG = 40                      # a building (not a lamp pillar or a post): its plot stops being a field
RING = 335                    # the farm ring: outside the third wall (the town's gardens inside it are the houses' own)
CROPS = ('wheat', 'carrots', 'potatoes', 'beetroots', 'melon_stem', 'pumpkin_stem', 'attached_melon_stem', 'attached_pumpkin_stem',
         'melon', 'pumpkin', 'sweet_berry_bush')
DECOR = set(CROPS) | {'air', 'cave_air', 'light', 'water', 'short_grass', 'tall_grass', 'fern', 'large_fern', 'farmland', 'dirt', 'grass_block',
                      'dirt_path', 'coarse_dirt', 'hay_block', 'composter', 'torch', 'wall_torch', 'lantern', 'soul_lantern', 'poppy',
                      'dandelion', 'cornflower', 'allium', 'azure_bluet', 'oxeye_daisy', 'blue_orchid', 'lily_of_the_valley', 'snow',
                      'red_tulip', 'orange_tulip', 'white_tulip', 'pink_tulip', 'sugar_cane', 'lily_pad', 'seagrass', 'bubble_column',
                      'carved_pumpkin', 'jack_o_lantern'}


def name(st):
    return st.split('[')[0].split(':')[-1]


def decor(nm):
    return nm in DECOR or nm.endswith(('_leaves', '_fence', '_fence_gate', '_carpet', '_sapling', '_button', '_pressure_plate'))


class Fields:
    def __init__(self, t, garrison):
        self.t = t
        self.g = garrison
        self.stats = collections.Counter()

    def scan(self):
        """Per column of the farm ring: farmland (and its level), water at that level, anything standing above it."""
        W = X1 - X0
        self.farm = np.zeros((W, W), bool)
        self.water = np.zeros((W, W), bool)
        self.level = np.zeros((W, W), np.int16)
        self.stand = np.zeros((W, W), bool)
        lut = {}
        for cx in range(X0 // 16, X1 // 16):
            for cz in range(Z0 // 16, Z1 // 16):
                if not self.t.has_chunk(cx, cz):
                    continue
                b = self.t.box(cx * 16, cx * 16 + 15, YLO, YHI, cz * 16, cz * 16 + 15)
                keys, inv = np.unique(b, return_inverse=True)
                inv = inv.reshape(b.shape)
                for k in keys:
                    if k not in lut:
                        nm = name(k)
                        lut[k] = (nm == 'farmland', nm == 'water', not decor(nm))
                table = np.array([lut[k] for k in keys], bool)
                fm, wm, sm = table[inv, 0], table[inv, 1], table[inv, 2]
                xs = slice(cx * 16 - X0, cx * 16 - X0 + 16)
                zs = slice(cz * 16 - Z0, cz * 16 - Z0 + 16)
                has_f = fm.any(axis=1)
                lvl = np.where(has_f, fm.argmax(axis=1) + YLO, 0)
                self.farm[xs, zs] = has_f
                self.level[xs, zs] = lvl
                # water at the fields' own level (their channels), and what stands above the ground there
                ground = 64
                self.water[xs, zs] = wm[:, ground - YLO, :] | wm[:, ground - 1 - YLO, :]
                self.stand[xs, zs] = sm[:, ground + 1 - YLO:, :].any(axis=1)
        # an anti-aircraft gun's post stands on its pad (fieldfire.py): its nine by nine counts as standing
        for e in self.g['entries']:
            if e.get('post') == 'aa' and 'x' in e:
                i, k = e['x'] - X0, e['z'] - Z0
                self.stand[i - 4:i + 5, k - 4:k + 5] = True
        self.stats['farmland in the ring'] = int(self.farm.sum())

    def plan(self):
        """The plots (farmland joined across its channels), and for each what goes: the whole plot or a margin."""
        plot_area = self.farm | (self.water & ndimage.binary_dilation(self.farm, iterations=1))
        lab, n = ndimage.label(ndimage.binary_closing(plot_area, iterations=1))
        near = ndimage.binary_dilation(self.stand, structure=np.ones((3, 3), bool), iterations=MARGIN)
        self.clear = np.zeros_like(self.farm)
        self.report = []
        for i in range(1, n + 1):
            m = lab == i
            f = m & self.farm
            if f.sum() < 20:
                continue
            ci, ck = np.argwhere(m).mean(axis=0)
            if max(abs(ci + X0), abs(ck + Z0)) < RING:
                continue                                  # a garden in the town: the house's own
            on = self.stand & ndimage.binary_dilation(m, iterations=1)
            if not on.any():
                continue
            xs, zs = np.nonzero(m)
            x0, x1, z0, z1 = xs.min(), xs.max(), zs.min(), zs.max()
            inner = np.zeros_like(m)
            inner[x0 + 2:x1 - 1, z0 + 2:z1 - 1] = True
            cut = near & m
            whole = bool((on & inner).sum() >= BIG or (cut & self.farm).sum() > f.sum() / 3)
            gone = m if whole else cut
            self.clear |= gone
            sx, sz = np.nonzero(on)
            self.report.append(dict(box=[int(x0 + X0), int(x1 + X0), int(z0 + Z0), int(z1 + Z0)], farmland=int(f.sum()),
                                    whole=whole, cleared=int((gone & self.farm).sum()),
                                    standing=[int(sx.min() + X0), int(sx.max() + X0), int(sz.min() + Z0), int(sz.max() + Z0)]))
            self.stats['plots made grass' if whole else 'plots cut back from what stands at their edge'] += 1

    def apply(self):
        xs, zs = np.nonzero(self.clear)
        for i, k in zip(xs, zs):
            x, z = int(i + X0), int(k + Z0)
            if self.farm[i, k]:
                y = int(self.level[i, k])
                above = self.t.get(x, y + 1, z)
                if name(above) in CROPS:
                    self.t.set(x, y + 1, z, 'minecraft:air')
                    self.stats['crops taken up'] += 1
                self.t.set(x, y, z, 'minecraft:grass_block[snowy=false]')
                self.stats['farmland made grass'] += 1
            elif self.water[i, k]:
                for y in (64, 63):
                    if name(self.t.get(x, y, z)) == 'water':
                        self.t.set(x, y, z, 'minecraft:grass_block[snowy=false]' if y == 64 else 'minecraft:dirt')
                        self.stats['channel water filled'] += 1


if __name__ == '__main__':
    folder = sys.argv[1]
    t = template_io.Template(folder)
    g = json.load(open(os.path.join(folder, 'garrison.json')))
    F = Fields(t, g)
    F.scan()
    F.plan()
    F.apply()
    F.stats['chunks saved'] = t.save(folder)
    print(json.dumps(F.stats, ensure_ascii=False, indent=1))
    if len(sys.argv) > 2:
        json.dump(dict(stats=F.stats, plots=F.report), open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
