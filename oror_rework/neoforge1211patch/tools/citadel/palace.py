"""palace.py <template dir> [report.json]: the royal palace of the capital rebuilt as a palace (059, the user's report).

What was there: inside the keep's outer walls (x and z within 41 of the castle's centre) four storeys of a labyrinth
(196 chambers, dead ends, pit traps down into the undercroft, ladders), and above it a hall with the throne in a round
tower 73 blocks over the town: the king sat at the top of a maze no one would walk. The palace's terrace stood ten
blocks over the town on all four sides with no stair up to it.

What it is now (all within the keep's own walls and roof, which stay; the town and the walls are untouched):
* four grand staircases from the town up to the terrace, on the palace's four axes;
* the main door in the south front, into the audience hall: 29 wide, 72 long, 22 high, two rows of pillars, a red
  carpet to a three-step dais and the throne (gold, with a canopy of banners and a rose window behind it); the court
  stands about it (the king on the throne, bodyguards and the sage and archmage on the dais, generals at its foot,
  the imperial guard down the carpet);
* behind the throne the treasury (its stair goes down to the vault under the palace) and the king's antechamber;
* the two wings beside the hall, each with a gallery along the hall and rooms on the outside: the sage's library,
  the mages' hall, the guard room (west); the war room, the imperial guard's hall, the armoury (east); an upper storey
  over them reached by stairs in the galleries;
* in the four corners, wide stairs round a solid core from the ground floor to the top (no ladders anywhere);
* the upper floors: chapel, gallery and music room (second floor); the king's bedchamber, his study, the wardrobe,
  servants' rooms, storerooms and the bath (third floor); the great ballroom under the roof (fourth floor);
* the chests of the old maze and hall (and their contents) are not lost: the richest go to the treasury, the rest to
  the armoury, the kitchen and the storerooms by what they hold.

The garrison table (garrison.json) gets the court's new posts; CitadelData's throne moves with them.
"""
import sys, os, json, collections, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_io, anvil

R = 41          # the interior: x, z within R of the centre (the keep's outer walls are at 42 to 46)
Y0, YTOP = 72, 145   # the interior from the old maze's floor to under the roof's ceiling (146)
G, U1, F2, F3, F4 = 75, 85, 100, 110, 120   # walking heights: ground, the wings' upper storey, the floors above
HALL_X = 14     # the audience hall: x within 14
HALL_TOP = 96   # its ceiling
THRONE = (0, 79, -28)   # where the king stands (on the gold seat block at y 78)

AIR = 'minecraft:air'
QB, QS, QP, QC = 'minecraft:quartz_bricks', 'minecraft:smooth_quartz', 'minecraft:quartz_pillar[axis=y]', 'minecraft:chiseled_quartz_block'
DS, DT, PB = 'minecraft:polished_deepslate', 'minecraft:deepslate_tiles', 'minecraft:polished_blackstone_bricks'
GOLD, DO = 'minecraft:gold_block', 'minecraft:dark_oak_planks'
LANTERN = 'minecraft:lantern[hanging=true,waterlogged=false]'
LANTERN_UP = 'minecraft:lantern[hanging=false,waterlogged=false]'
CHAIN = 'minecraft:chain[axis=y,waterlogged=false]'
SEA = 'minecraft:sea_lantern'


def stairs(mat, facing, half='bottom'):
    return f'minecraft:{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]'


def slab(mat, kind='bottom'):
    return f'minecraft:{mat}_slab[type={kind},waterlogged=false]'


def fence(mat='dark_oak'):
    return f'minecraft:{mat}_fence[east=false,north=false,south=false,waterlogged=false,west=false]'


OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


class Palace:
    def __init__(self, t):
        self.t = t
        self.stats = collections.Counter()
        self.posts = []
        self.chests = []    # (theme, items list) to place
        self.places = collections.defaultdict(list)   # theme -> [(x, y, z, facing)] chest spots
        self.rng = random.Random(59)

    # ------------------------------------------------------------------------------------------------ primitives

    def put(self, x, y, z, s):
        if self.t.set(x, y, z, s):
            self.stats['blocks'] += 1

    def fill(self, x0, x1, y0, y1, z0, z1, s):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.put(x, y, z, s)

    def get(self, x, y, z):
        return self.t.get(x, y, z) or AIR

    # ------------------------------------------------------------------------------------------------ survey

    def survey_chests(self):
        """Every container of the old maze and hall, with what it holds; dispensers (its traps) go."""
        for x, y, z, be in self.t.block_entities_in(-R, R, Y0, YTOP, -R, R):
            bid = anvil.val(be['id'])
            if bid not in ('minecraft:chest', 'minecraft:barrel', 'minecraft:trapped_chest'):
                self.stats['dropped ' + bid] += 1
                continue
            items = be.get('Items') or []
            loot = be.get('LootTable')
            self.chests.append((self.theme(items, loot), items, loot))
        self.stats['chests surveyed'] = len(self.chests)

    @staticmethod
    def theme(items, loot):
        ids = [anvil.val(i.get('id', '')) for i in items]
        def has(*words):
            return sum(1 for i in ids if any(w in i for w in words))
        value = has('diamond', 'netherite', 'emerald', 'gold', 'totem', 'enchanted_golden', 'nether_star', 'elytra', 'beacon', 'oror_supreme_bosses')
        if value >= 2 or (loot is not None and 'treasure' in str(anvil.val(loot))):
            return 'treasury'
        if has('sword', 'axe', 'bow', 'crossbow', 'arrow', 'helmet', 'chestplate', 'leggings', 'boots', 'shield', 'trident', 'tacz', 'superbwarfare', 'jeg'):
            return 'armoury'
        if has('bread', 'beef', 'pork', 'mutton', 'chicken', 'potato', 'carrot', 'wheat', 'apple', 'fish', 'cod', 'salmon', 'stew', 'cake', 'cookie', 'pie', 'melon', 'berries', 'sugar', 'egg', 'milk'):
            return 'kitchen'
        if has('book', 'paper', 'map', 'compass', 'clock', 'ink', 'feather', 'potion', 'brewing', 'glowstone', 'redstone', 'lapis'):
            return 'library'
        return 'store'

    # ------------------------------------------------------------------------------------------------ clearing

    def clear(self):
        """The maze, its traps and the old hall: the interior is emptied down to the old maze floor (72)."""
        self.fill(-R, R, Y0, YTOP, -R, R, AIR)
        # the pit traps' shafts under the maze (ladders down to water over the vault) are closed with the podium's stone
        for x in range(-R, R + 1):
            for z in range(-R, R + 1):
                for y in range(60, Y0):
                    s = self.get(x, y, z)
                    if 'ladder' in s or ('water' in s and y >= 62):
                        self.put(x, y, z, 'minecraft:stone_bricks')
                        self.stats['shaft blocks closed'] += 1

    # ------------------------------------------------------------------------------------------------ the shell

    def floors(self):
        # the ground floor: a patterned floor; the hall's border of deepslate tiles
        for x in range(-R, R + 1):
            for z in range(-R, R + 1):
                self.put(x, Y0, z, 'minecraft:stone_bricks')
                self.put(x, Y0 + 1, z, 'minecraft:stone_bricks')
                inner = abs(x) <= HALL_X
                if inner:
                    s = QS if (x // 3 + z // 3) % 2 == 0 else 'minecraft:polished_diorite'
                    if abs(x) >= HALL_X - 1:
                        s = DT
                else:
                    s = 'minecraft:spruce_planks' if abs(x) > 20 else DS
                self.put(x, G - 1, z, s)
        # the wings' upper storey floor (one slab: 84) and the floors above, over all but the hall where it is open
        for x in range(-R, R + 1):
            for z in range(-R, R + 1):
                if abs(x) > HALL_X:
                    self.put(x, U1 - 1, z, 'minecraft:spruce_planks')
                for y in (F2 - 3, F2 - 2):
                    self.put(x, y, z, 'minecraft:stone_bricks')
                self.put(x, F2 - 1, z, DO if (x + z) % 2 else 'minecraft:spruce_planks')
                for y in (F3 - 3, F3 - 2):
                    self.put(x, y, z, 'minecraft:stone_bricks')
                self.put(x, F3 - 1, z, 'minecraft:spruce_planks')
                for y in (F4 - 3, F4 - 2):
                    self.put(x, y, z, 'minecraft:stone_bricks')
                self.put(x, F4 - 1, z, QS if (x // 4 + z // 4) % 2 == 0 else 'minecraft:polished_andesite')
        # the hall's ceiling: dark oak coffers with quartz ribs, under the second floor
        for x in range(-HALL_X, HALL_X + 1):
            for z in range(-R, R + 1):
                rib = x % 5 == 0 or z % 6 == 0
                self.put(x, HALL_TOP, z, QS if rib else DO)

    def wall(self, x0, x1, z0, z1, y0, y1, s=QB):
        self.fill(x0, x1, y0, y1, z0, z1, s)

    def arch(self, x0, x1, z0, z1, y0, h):
        """A doorway through a wall (inclusive box in x, z), h high, with a stone trim over it."""
        self.fill(x0, x1, y0, y0 + h - 1, z0, z1, AIR)

    # ------------------------------------------------------------------------------------------------ rooms

    def room_walls(self):
        """The plan of every floor: the hall's walls, the galleries, the side rooms, the corner stair halls."""
        # the hall's side walls (both wing storeys): x = +-15, from the front to the back
        for sx in (-1, 1):
            self.wall(sx * 15, sx * 15, -R, R, G, HALL_TOP - 1)
            # galleries' outer walls: x = +-20, with the rooms beyond
            self.wall(sx * 20, sx * 20, -R, R, G, F2 - 4)
            # the rooms of the band: walls across at z -30, -10, 10, 30
            for zw in (-30, -10, 10, 30):
                self.wall(sx * 20, sx * R, zw, zw, G, F2 - 4)
        # behind the throne: z = -31 across the hall, the treasury and antechamber beyond, split at x = 0
        self.wall(-HALL_X, HALL_X, -31, -31, G, HALL_TOP - 1)
        self.wall(0, 0, -R, -32, G, HALL_TOP - 1)
        # the upper floors: the same bands; the centre (x within 14) split at z -16 and 16
        for y0, y1 in ((F2, F3 - 4), (F3, F4 - 4)):
            for sx in (-1, 1):
                self.wall(sx * 15, sx * 15, -R, R, y0, y1)
                self.wall(sx * 20, sx * 20, -R, R, y0, y1)
                for zw in (-30, -10, 10, 30):
                    self.wall(sx * 20, sx * R, zw, zw, y0, y1)
            for zw in (-16, 16):
                self.wall(-14, 14, zw, zw, y0, y1)

    def doors(self):
        """Arches: hall to galleries, galleries to rooms, rooms of the centre to the galleries, behind the throne."""
        for sx in (-1, 1):
            for z in (-24, -12, 0, 12, 24, 36):
                self.arch(sx * 15, sx * 15, z - 1, z + 1, G, 5)
            for zc in (-36, -20, 0, 20, 36):
                for y in (G, U1, F2, F3):
                    self.arch(sx * 20, sx * 20, zc - 1, zc + 1, y, 4)
            for zc in (-28, 0, 28):
                for y in (F2, F3):
                    self.arch(sx * 15, sx * 15, zc - 1, zc + 1, y, 4)
        # behind the throne: from the aisles (x +-11) into the treasury and the antechamber
        self.arch(-12, -10, -31, -31, G, 4)
        self.arch(10, 12, -31, -31, G, 4)
        # the main door through the keep's south front (x within 2, 7 high), the floor before it made good
        self.fill(-2, 2, G, G + 6, R + 1, 49, AIR)
        self.fill(-2, 2, Y0, G - 1, R + 1, 49, 'minecraft:stone_bricks')
        self.fill(-3, 3, G + 7, G + 7, R + 1, 46, QC)
        for sx in (-1, 1):
            self.fill(sx * 3, sx * 3, G, G + 6, R + 1, 46, QP)

    # ------------------------------------------------------------------------------------------------ the hall

    def hall(self):
        # two rows of pillars, every six blocks, with capitals and lanterns on their faces to the aisles
        for z in range(-18, 41, 6):
            for sx in (-1, 1):
                x = sx * 9
                for xx in (x, x + sx):
                    for zz in (z, z + 1):
                        self.fill(xx, xx, G, HALL_TOP - 2, zz, zz, QP)
                        self.put(xx, HALL_TOP - 1, zz, QC)
                        self.put(xx, G, zz, QC)
                self.put(x + 2 * sx, G + 4, z, LANTERN_UP)
                self.put(x + 2 * sx, G + 3, z, fence('dark_oak'))
        # the carpet from the door to the dais, gold-bordered
        for z in range(-21, R + 1):
            for x in range(-3, 4):
                self.put(x, G, z, 'minecraft:yellow_carpet' if abs(x) == 3 else 'minecraft:red_carpet')
        # the dais: three steps up to the platform (walk 78), its edges in gold and blackstone
        for x in range(-9, 10):
            self.put(x, G, -22, stairs('polished_blackstone_brick', 'north'))
            self.put(x, G, -23, PB)
            self.put(x, G + 1, -23, stairs('polished_blackstone_brick', 'north'))
            for z in range(-30, -23):
                self.fill(x, x, G, G + 1, z, z, PB)
                self.put(x, G + 2, z, QS if abs(x) < 9 else GOLD)
            self.put(x, G + 2, -24, stairs('quartz', 'north'))
        for x in range(-6, 7):
            for z in range(-30, -24):
                self.put(x, G + 3, z, 'minecraft:red_carpet' if abs(x) < 6 else 'minecraft:yellow_carpet')
        # the throne: a gold seat with quartz arms and a high gold back crowned in chiseled quartz
        tx, ty, tz = THRONE
        self.put(tx, ty - 1, tz, GOLD)
        self.put(tx - 1, ty - 1, tz, stairs('quartz', 'east'))
        self.put(tx + 1, ty - 1, tz, stairs('quartz', 'west'))
        self.fill(tx - 1, tx + 1, ty - 1, ty + 4, tz - 1, tz - 1, GOLD)
        self.put(tx, ty + 5, tz - 1, QC)
        self.put(tx - 1, ty + 5, tz - 1, stairs('quartz', 'east'))
        self.put(tx + 1, ty + 5, tz - 1, stairs('quartz', 'west'))
        self.put(tx, ty + 2, tz - 1, 'minecraft:diamond_block')
        # the canopy over it, banners hung from it; the wall behind with a rose window lit from behind
        self.fill(tx - 3, tx + 3, ty + 8, ty + 8, tz - 2, tz + 1, PB)
        for x in range(tx - 3, tx + 4):
            self.put(x, ty + 7, tz + 1, 'minecraft:red_wall_banner[facing=south]')
        for x, y in ((-6, 82), (6, 82), (-10, 84), (10, 84)):
            self.put(x, y, -30, 'minecraft:blue_wall_banner[facing=south]')
            self.put(x, y - 1, -30, AIR)
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx * dx + dy * dy <= 17:
                    glass = 'minecraft:yellow_stained_glass' if dx * dx + dy * dy <= 4 else ('minecraft:red_stained_glass' if (dx + dy) % 2 else 'minecraft:purple_stained_glass')
                    self.put(tx + dx, 89 + dy, -31, glass)
                    self.put(tx + dx, 89 + dy, -32, SEA)
        # chandeliers: lanterns hung on chains in three lines down the hall, and in the aisles
        for z in range(-20, 41, 8):
            for x in (-5, 0, 5):
                for y in range(88, HALL_TOP):
                    self.put(x, y, z, CHAIN)
                self.put(x, 87, z, LANTERN)
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    self.put(x + dx, 88, z + dz, LANTERN)
                    self.put(x + dx, 89, z + dz, 'minecraft:chain[axis=y,waterlogged=false]')
            for x in (-12, 12):
                for y in range(90, HALL_TOP):
                    self.put(x, y, z, CHAIN)
                self.put(x, 89, z, LANTERN)
        # banners down the hall's walls between the arches
        for z in range(-27, 41, 12):
            for sx, f in ((-1, 'east'), (1, 'west')):
                self.put(sx * 14, G + 8, z, f'minecraft:red_wall_banner[facing={f}]')
                self.put(sx * 14, G + 12, z, f'minecraft:yellow_wall_banner[facing={f}]')
        # the court: the king on the throne, the bodyguards and the wise on the dais, generals at its foot, the
        # imperial guard down the carpet
        P = self.posts
        P.append(dict(role='KING', x=tx, y=ty, z=tz, yaw=0, post='throne'))
        for x in (-4, 4):
            for z in (-29, -26):
                P.append(dict(role='BODYGUARD', x=x, y=78, z=z, yaw=0, post='throne'))
        for x in (-7, 7):
            P.append(dict(role='BODYGUARD', x=x, y=78, z=-28, yaw=0, post='throne'))
        P.append(dict(role='SAGE', x=2, y=78, z=-25, yaw=0, post='throne'))
        P.append(dict(role='ARCHMAGE', x=-2, y=78, z=-25, yaw=0, post='throne'))
        P.append(dict(role='GENERAL', x=-6, y=G, z=-19, yaw=-90, post='throne'))
        P.append(dict(role='GENERAL', x=6, y=G, z=-19, yaw=90, post='throne'))
        for z in (-14, -6, 2, 10, 18, 26):
            P.append(dict(role='IMPERIAL', x=-5, y=G, z=z, yaw=-90, post='throne'))
            P.append(dict(role='IMPERIAL', x=5, y=G, z=z, yaw=90, post='throne'))
        for z in (34, 38):
            P.append(dict(role='GUARD', x=-4, y=G, z=z, yaw=0, post='throne'))
            P.append(dict(role='GUARD', x=4, y=G, z=z, yaw=0, post='throne'))
        self.stats['court posts'] = len(P)

    # ------------------------------------------------------------------------------------------------ the rooms

    def lights(self, x0, x1, z0, z1, y_floor, y_ceil, step=5):
        """Lanterns hung from a ceiling (y_ceil: the ceiling block's height), one every few blocks, on a chain where the
        room is tall."""
        for x in range(x0 + 2, x1 - 1, step):
            for z in range(z0 + 2, z1 - 1, step):
                if y_ceil - y_floor >= 7:
                    self.put(x, y_ceil - 1, z, CHAIN)
                    self.put(x, y_ceil - 2, z, LANTERN)
                else:
                    self.put(x, y_ceil - 1, z, LANTERN)

    def along_walls(self, x0, x1, z0, z1, y, every=1, skip_doors=True):
        """The cells along a room's walls (inside it), with the way they face into the room."""
        out = []
        for x in range(x0, x1 + 1, every):
            out.append((x, z0, 'south'))
            out.append((x, z1, 'north'))
        for z in range(z0 + 1, z1, every):
            out.append((x0, z, 'east'))
            out.append((x1, z, 'west'))
        free = []
        for x, z, f in out:
            if skip_doors:
                # not before an arch (the cell beyond the wall is open)
                bx, bz = {'south': (x, z - 1), 'north': (x, z + 1), 'east': (x - 1, z), 'west': (x + 1, z)}[f]
                if self.get(bx, y, bz) == AIR:
                    continue
                # nor beside one
                ok = True
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, nz = bx + dx, bz + dz
                    if (nx, nz) != (x, z) and self.get(nx, y, nz) == AIR and not (x0 <= nx <= x1 and z0 <= nz <= z1):
                        ok = False
                if not ok:
                    continue
            free.append((x, z, f))
        return free

    def furnish(self, kind, x0, x1, z0, z1, y, y_ceil):
        """A room's furniture by its kind; chest spots are kept for the chests of the old palace."""
        put = self.put
        walls = self.along_walls(x0, x1, z0, z1, y)
        cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
        if kind == 'library':
            for x, z, f in walls:
                for dy in range(0, min(4, y_ceil - y)):
                    put(x, y + dy, z, 'minecraft:bookshelf')
            for x in range(x0 + 3, x1 - 2, 4):
                for z in range(z0 + 3, z1 - 2, 5):
                    put(x, y, z, f'minecraft:lectern[facing=south,has_book=false,powered=false]')
            put(cx, y, cz, 'minecraft:enchanting_table')
            for x, z in ((cx - 2, cz), (cx + 2, cz), (cx, cz - 2), (cx, cz + 2)):
                put(x, y, z, 'minecraft:bookshelf')
        elif kind in ('war', 'study'):
            for x in range(cx - 3, cx + 4):
                for z in range(cz - 2, cz + 3):
                    put(x, y, z, 'minecraft:cartography_table' if (x + z) % 3 else 'minecraft:spruce_planks')
            for x, z, f in walls[::3]:
                put(x, y + 2, z, f'minecraft:red_wall_banner[facing={f}]')
            for x, z, f in walls[1::6]:
                self.places['library' if kind == 'study' else 'armoury'].append((x, y, z, f))
        elif kind in ('guards', 'barracks', 'servants'):
            bed = {'guards': 'blue', 'barracks': 'red', 'servants': 'white'}[kind]
            for x, z, f in walls[::3]:
                if f in ('east', 'west'):
                    hx = x + (1 if f == 'east' else -1)
                    if x0 <= hx <= x1 and self.get(hx, y, z) == AIR:
                        put(hx, y, z, f'minecraft:{bed}_bed[facing={OPPOSITE[f]},occupied=false,part=foot]')
                        put(x, y, z, f'minecraft:{bed}_bed[facing={OPPOSITE[f]},occupied=false,part=head]')
            for x, z, f in walls[1::5]:
                if self.get(x, y, z) == AIR:
                    self.places['armoury' if kind != 'servants' else 'store'].append((x, y, z, f))
            for x in range(cx - 2, cx + 3):
                put(x, y, cz, 'minecraft:spruce_planks')
        elif kind == 'armoury':
            for x, z, f in walls:
                if (x + z) % 4 == 0:
                    put(x, y, z, 'minecraft:smithing_table' if (x + z) % 8 else f'minecraft:anvil[facing={"east" if f in ("north", "south") else "north"}]')
                else:
                    self.places['armoury'].append((x, y, z, f))
        elif kind == 'mages':
            for x, z, f in walls[::4]:
                put(x, y, z, 'minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]')
            for x, z, f in walls[2::4]:
                put(x, y, z, 'minecraft:cauldron')
            for x, z, f in walls[1::4]:
                self.places['library'].append((x, y, z, f))
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    if 7 <= dx * dx + dz * dz <= 12:
                        put(cx + dx, y - 1, cz + dz, 'minecraft:amethyst_block')
            put(cx, y, cz, 'minecraft:enchanting_table')
        elif kind == 'kitchen':
            for x, z, f in walls:
                k = (x + z) % 5
                put(x, y, z, ('minecraft:smoker[facing=%s,lit=false]' % f) if k == 0 else
                    ('minecraft:barrel[facing=up,open=false]' if k == 1 else ('minecraft:crafting_table' if k == 2 else 'minecraft:spruce_planks')))
                if k >= 3:
                    self.places['kitchen'].append((x, y + 1, z, f))
            for x in range(cx - 4, cx + 5):
                put(x, y, cz, 'minecraft:spruce_planks')
        elif kind == 'banquet':
            for x in range(x0 + 3, x1 - 2):
                for z in (cz - 1, cz, cz + 1):
                    put(x, y, z, 'minecraft:dark_oak_planks')
                put(x, y, cz - 2, stairs('spruce', 'north'))
                put(x, y, cz + 2, stairs('spruce', 'south'))
            for x in range(x0 + 4, x1 - 3, 4):
                put(x, y + 1, cz, 'minecraft:candle[candles=3,lit=true,waterlogged=false]')
        elif kind == 'chapel':
            for x in range(x0 + 2, x1 - 1):
                for z in range(cz - 6, cz + 7, 3):
                    if abs(x - cx) > 1:
                        put(x, y, z, stairs('dark_oak', 'south'))
            put(cx, y, z0 + 2, 'minecraft:lectern[facing=south,has_book=false,powered=false]')
            for x in range(x0, x1 + 1):
                if (x - x0) % 3 == 1:
                    for dy in range(1, min(6, y_ceil - y - 1)):
                        put(x, y + dy, z0 - 1, 'minecraft:light_blue_stained_glass')
                        put(x, y + dy, z0 - 2, SEA)
            for z in range(z0 + 1, z1, 4):
                put(x0, y + 1, z, 'minecraft:candle[candles=4,lit=true,waterlogged=false]')
                put(x1, y + 1, z, 'minecraft:candle[candles=4,lit=true,waterlogged=false]')
        elif kind == 'music':
            for x, z, f in walls[::2]:
                put(x, y, z, 'minecraft:note_block[instrument=harp,note=0,powered=false]')
            put(cx, y, cz, 'minecraft:jukebox[has_record=false]')
        elif kind == 'gallery':
            for x, z, f in walls[::3]:
                put(x, y + 1, z, f'minecraft:{self.rng.choice(["red", "blue", "yellow", "purple", "green"])}_wall_banner[facing={f}]')
            for x in range(x0 + 2, x1 - 1, 5):
                for z in range(z0 + 2, z1 - 1, 5):
                    put(x, y, z, 'minecraft:potted_azure_bluet' if (x + z) % 2 else 'minecraft:potted_red_tulip')
        elif kind == 'bedchamber':
            # the king's bed (two side by side, under a canopy), wardrobes, carpets
            for x in (cx - 1, cx):
                put(x, y, z0 + 1, 'minecraft:red_bed[facing=south,occupied=false,part=head]')
                put(x, y, z0 + 2, 'minecraft:red_bed[facing=south,occupied=false,part=foot]')
            self.fill(cx - 2, cx + 1, y + 3, y + 3, z0 + 1, z0 + 3, 'minecraft:red_wool')
            for x, z in ((cx - 2, z0 + 3), (cx + 1, z0 + 3)):
                for dy in range(0, 3):
                    put(x, y + dy, z, fence('dark_oak'))
            for x in range(x0 + 1, x1):
                for z in range(z0 + 4, z1):
                    put(x, y, z, 'minecraft:purple_carpet' if (x + z) % 2 else 'minecraft:magenta_carpet')
            for x, z, f in walls[::4]:
                if self.get(x, y, z) == AIR or 'carpet' in self.get(x, y, z):
                    self.places['treasury'].append((x, y, z, f))
        elif kind == 'wardrobe':
            for x, z, f in walls[::2]:
                self.places['store'].append((x, y, z, f))
            for x, z, f in walls[1::2]:
                put(x, y, z, 'minecraft:barrel[facing=up,open=false]')
        elif kind == 'bath':
            for x in range(cx - 4, cx + 5):
                for z in range(cz - 3, cz + 4):
                    edge = abs(x - cx) == 4 or abs(z - cz) == 3
                    put(x, y - 1, z, QB if edge else 'minecraft:water[level=0]')
                    put(x, y - 2, z, QB)
            for x, z, f in walls[::4]:
                put(x, y, z, 'minecraft:potted_fern')
        elif kind in ('store', 'antechamber'):
            for x, z, f in walls:
                self.places['store' if kind == 'store' else 'treasury'].append((x, y, z, f))
        elif kind == 'treasury':
            for x, z, f in walls:
                self.places['treasury'].append((x, y, z, f))
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    put(x, y - 1, z, GOLD)
        elif kind == 'scribe':
            for x, z, f in walls[::2]:
                put(x, y, z, 'minecraft:bookshelf')
            put(cx, y, cz, 'minecraft:lectern[facing=south,has_book=false,powered=false]')
        self.lights(x0, x1, z0, z1, y, y_ceil)
        self.stats['rooms'] += 1
        self.stats['room ' + kind] += 1

    def rooms(self):
        bands = ((-29, -11), (-9, 9), (11, 29))
        # the ground floor's wings: west (library, mages, guards), east (war room, imperial guard, armoury)
        for (z0, z1), w, e in zip(bands, ('library', 'mages', 'guards'), ('war', 'barracks', 'armoury')):
            self.furnish(w, -R, -21, z0, z1, G, U1 - 1)
            self.furnish(e, 21, R, z0, z1, G, U1 - 1)
        # the wings' upper storey: servants' rooms, scribes, stores
        for (z0, z1), w, e in zip(bands, ('scribe', 'servants', 'store'), ('store', 'servants', 'kitchen')):
            self.furnish(w, -R, -21, z0, z1, U1, F2 - 3)
            self.furnish(e, 21, R, z0, z1, U1, F2 - 3)
        # behind the throne
        self.furnish('treasury', -14, -1, -R, -32, G, HALL_TOP)
        self.furnish('antechamber', 1, 14, -R, -32, G, HALL_TOP)
        # the second floor: chapel, gallery and music in the centre; guest rooms, banquet hall, kitchen in the wings
        self.furnish('chapel', -14, 14, -R, -17, F2, F3 - 3)
        self.furnish('gallery', -14, 14, -15, 15, F2, F3 - 3)
        self.furnish('music', -14, 14, 17, R, F2, F3 - 3)
        for (z0, z1), w, e in zip(bands, ('servants', 'banquet', 'servants'), ('kitchen', 'banquet', 'store')):
            self.furnish(w, -R, -21, z0, z1, F2, F3 - 3)
            self.furnish(e, 21, R, z0, z1, F2, F3 - 3)
        # the third floor: the king's own (bedchamber, study, wardrobe); stores, the bath, servants
        self.furnish('bedchamber', -14, 14, -R, -17, F3, F4 - 3)
        self.furnish('study', -14, 14, -15, 15, F3, F4 - 3)
        self.furnish('wardrobe', -14, 14, 17, R, F3, F4 - 3)
        for (z0, z1), w, e in zip(bands, ('store', 'bath', 'store'), ('store', 'servants', 'store')):
            self.furnish(w, -R, -21, z0, z1, F3, F4 - 3)
            self.furnish(e, 21, R, z0, z1, F3, F4 - 3)
        # the galleries' lights, all storeys
        for sx in (-1, 1):
            for y0, y1 in ((G, U1 - 1), (U1, F2 - 3), (F2, F3 - 3), (F3, F4 - 3)):
                for z in range(-38, 39, 6):
                    if abs(z) > 12:
                        self.put(sx * 17 + (0 if sx < 0 else 1), y1 - 1, z, LANTERN)
        # the stairs in the galleries from the ground floor to the wings' upper storey (both sides, both ends)
        for sx in (-1, 1):
            xs = (sx * 16, sx * 17)
            for zstart, dz, face in ((-1, -1, 'north'), (1, 1, 'south')):
                for i in range(U1 - G):
                    z = zstart + dz * i
                    for x in xs:
                        self.put(x, G + i, z, stairs('spruce', face))
                        if i > 0:
                            self.put(x, G + i - 1, z, 'minecraft:spruce_planks')
                        for y in range(G + i + 1, G + i + 4):
                            if y >= U1 - 1:
                                self.put(x, y, z, AIR)
        # the fourth floor: the ballroom under the roof, pillars and chandeliers
        for x in range(-30, 31, 10):
            for z in range(-30, 31, 10):
                if x == 0 and z == 0:
                    continue
                self.fill(x, x, F4, YTOP, z, z, QP)
        for x in range(-25, 26, 10):
            for z in range(-25, 26, 10):
                for y in range(136, YTOP + 1):
                    self.put(x, y, z, CHAIN)
                self.put(x, 135, z, LANTERN)
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    self.put(x + dx, 136, z + dz, LANTERN)
        self.furnish('gallery', -R + 12, R - 12, -R + 12, R - 12, F4, YTOP + 1)

    # ------------------------------------------------------------------------------------------------ corner stairs

    def corner_stairs(self):
        """In each corner a stair hall (11 square): stairs three wide round a solid core, a landing at each corner of
        the square every five steps; doors where a landing meets a floor."""
        for ox, oz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x0 = -R if ox < 0 else R - 10
            z0 = -R if oz < 0 else R - 10
            # its own walls on the keep's inner side, the shaft cleared from the ground floor up
            ix = x0 + 11 if ox < 0 else x0 - 1
            iz = z0 + 11 if oz < 0 else z0 - 1
            self.fill(x0, x0 + 10, G - 1, YTOP, z0, z0 + 10, AIR)
            self.fill(x0, x0 + 10, G - 1, G - 1, z0, z0 + 10, DS)
            self.fill(ix, ix, G, YTOP, z0, z0 + 10, QB)
            self.fill(x0, x0 + 10, G, YTOP, iz, iz, QB)
            self.put(ix, YTOP, iz, QB)
            # the core
            self.fill(x0 + 3, x0 + 7, G, YTOP, z0 + 3, z0 + 7, QB)
            for y in range(G + 3, YTOP, 6):
                for x, z in ((x0 + 5, z0 + 2), (x0 + 5, z0 + 8), (x0 + 2, z0 + 5), (x0 + 8, z0 + 5)):
                    self.put(x + (1 if x == x0 + 2 else -1 if x == x0 + 8 else 0), y, z + (1 if z == z0 + 2 else -1 if z == z0 + 8 else 0), SEA)
            # the four corner squares, from the inner one (toward the keep's centre) round
            c_in = (x0 + (8 if ox < 0 else 0), z0 + (8 if oz < 0 else 0))
            c_out = (x0 + (0 if ox < 0 else 8), z0 + (0 if oz < 0 else 8))
            c_a = (c_out[0], c_in[1])   # beside the inner wall across z (iz)
            c_b = (c_in[0], c_out[1])   # beside the inner wall across x (ix)
            order = [c_in, c_b, c_out, c_a]
            h = G
            k = 0
            landings = {}
            while h <= F4:
                cxz = order[k % 4]
                for x in range(cxz[0], cxz[0] + 3):
                    for z in range(cxz[1], cxz[1] + 3):
                        self.put(x, h - 1, z, QS)
                        for y in range(h, h + 4):
                            self.put(x, y, z, AIR)
                landings[h] = cxz
                if h == F4:
                    break
                nxt = order[(k + 1) % 4]
                # the run between: five cells along the side, rising one a cell
                dx = (nxt[0] - cxz[0]) // 8 if nxt[0] != cxz[0] else 0
                dz = (nxt[1] - cxz[1]) // 8 if nxt[1] != cxz[1] else 0
                face = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}[(dx, dz)]
                for i in range(5):
                    w = h + i + 1
                    for j in range(3):
                        if dx:
                            x = cxz[0] + (3 if dx > 0 else -1) + dx * i if dx > 0 else cxz[0] - 1 - i
                            x = cxz[0] + 3 + i if dx > 0 else cxz[0] - 1 - i
                            z = cxz[1] + j
                        else:
                            z = cxz[1] + 3 + i if dz > 0 else cxz[1] - 1 - i
                            x = cxz[0] + j
                        if i < 4:
                            self.put(x, w - 1, z, stairs('quartz', face))
                            self.put(x, w - 2, z, stairs('quartz', OPPOSITE[face], 'top'))
                        else:
                            self.put(x, w - 1, z, QS)
                        for y in range(w, w + 4):
                            self.put(x, y, z, AIR)
                h += 5
                k += 1
            # doors: at the floors' heights, through an inner wall the landing touches
            for floor in (G, F2, F3, F4):
                cxz = landings.get(floor)
                if cxz is None:
                    continue
                touches_ix = (cxz[0] == x0 + 8) if ox < 0 else (cxz[0] == x0)
                touches_iz = (cxz[1] == z0 + 8) if oz < 0 else (cxz[1] == z0)
                if touches_ix:
                    self.fill(ix, ix, floor, floor + 3, cxz[1], cxz[1] + 2, AIR)
                    self.stats['stair doors'] += 1
                if touches_iz:
                    self.fill(cxz[0], cxz[0] + 2, floor, floor + 3, iz, iz, AIR)
                    self.stats['stair doors'] += 1
            self.stats['stair halls'] += 1

    # ------------------------------------------------------------------------------------------------ the treasury's way down

    def vault_stair(self):
        """From the treasury (behind the throne) down to the vault under the palace (its floor at 54): a stair of
        three, under the hall's floor, lit, its walls of polished deepslate."""
        x0, x1 = -12, -10
        z = -38
        y = G - 1   # the first step's block
        top = G
        while y >= 54:
            for x in range(x0 - 1, x1 + 2):
                for yy in range(y, y + 5):
                    edge = x in (x0 - 1, x1 + 1) or yy == y + 4
                    if yy > G - 1 and not edge:
                        continue
                    if edge:
                        if yy <= G - 2 and solid(self.get(x, yy, z)):
                            self.put(x, yy, z, DS)
                    else:
                        self.put(x, yy, z, AIR)
            for x in range(x0, x1 + 1):
                self.put(x, y, z, stairs('polished_deepslate', 'north'))
                self.put(x, y - 1, z, DS)
            if (G - y) % 5 == 0 and solid(self.get(x1 + 1, y + 3, z)):
                self.put(x1 + 1, y + 3, z, SEA)
            y -= 1
            z += 1
        # the landing into the vault
        for x in range(x0, x1 + 1):
            for zz in range(z, z + 3):
                self.put(x, 53, zz, DS)
                for yy in range(54, 58):
                    self.put(x, yy, zz, AIR)
        self.stats['vault stair steps'] = G - 54
        # the opening in the treasury's floor over the stair's head
        for x in range(x0, x1 + 1):
            self.put(x, G - 1, -38, AIR)

    # ------------------------------------------------------------------------------------------------ the approaches

    def approaches(self):
        """A grand stair from the town up to the palace terrace on each of the four axes: found by walking out from
        the keep along the axis to where the terrace (or the wing's floor) ends, then down to the town's ground."""
        def walk_height(x, z, lo=60, hi=100):
            out = []
            for y in range(lo, hi):
                a, b, c = self.get(x, y, z), self.get(x, y + 1, z), self.get(x, y + 2, z)
                if solid(a) and not solid(b) and not solid(c):
                    out.append(y + 1)
            return out
        for ax, az, face in ((0, 1, 'north'), (0, -1, 'south')):
            # out from the keep along the terrace's own floor (each step within a block of the last), to its end
            level, edge = G, None
            for d in range(50, 112):
                x, z = ax * d, az * d
                near = [h for h in walk_height(x, z) if abs(h - level) <= 1]
                if not near:
                    break
                level = min(near, key=lambda h: abs(h - level))
                edge = (d, level)
            if not edge:
                self.stats['approach skipped'] += 1
                continue
            d0, top = edge
            ground = 65
            for d in range(d0 + 1, d0 + 30):
                hs = [h for h in walk_height(ax * d, az * d) if h <= 70]
                if hs:
                    ground = max(hs)
                    break
            rise = top - ground
            half = 8
            for i in range(rise + 2):
                d = d0 + 1 + i
                w = max(ground, top - 1 - i)
                for s in range(-half, half + 1):
                    x, z = (s, az * d) if ax == 0 else (ax * d, s)
                    # the steps on solid stone down to the ground, clear above
                    for y in range(ground - 2, w - 1):
                        self.put(x, y, z, 'minecraft:stone_bricks')
                    self.put(x, w - 1, z, stairs('stone_brick', face) if w > ground else 'minecraft:stone_bricks')
                    for y in range(w, w + 5):
                        if y > ground or i > 0:
                            self.put(x, y, z, AIR)
                    if abs(s) == half:
                        # balustrades and lamps
                        self.put(x, w, z, 'minecraft:stone_brick_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]')
                        if i % 3 == 0:
                            self.put(x, w + 1, z, 'minecraft:lantern[hanging=false,waterlogged=false]')
            # the top of the flight through any parapet at the terrace's edge
            for s in range(-half + 1, half):
                x, z = (s, az * d0) if ax == 0 else (ax * d0, s)
                for y in range(top, top + 4):
                    self.put(x, y, z, AIR)
            self.stats['approach stairs'] += 1
            self.stats['approach rise %d,%d' % (ax, az)] = rise

    # ------------------------------------------------------------------------------------------------ the chests

    def place_chests(self):
        by = collections.defaultdict(list)
        for theme, items, loot in self.chests:
            by[theme].append((items, loot))
        fallback = ['store', 'armoury', 'kitchen', 'library', 'treasury']
        placed = 0
        for theme in ('treasury', 'armoury', 'kitchen', 'library', 'store'):
            for items, loot in by[theme]:
                spot = None
                for th in [theme] + fallback:
                    while self.places[th]:
                        cand = self.places[th].pop(0)
                        x, y, z, f = cand
                        if self.get(x, y, z) in (AIR, 'minecraft:red_carpet', 'minecraft:purple_carpet', 'minecraft:magenta_carpet', 'minecraft:yellow_carpet'):
                            spot = cand
                            break
                    if spot:
                        break
                if not spot:
                    self.stats['chests without a place'] += 1
                    continue
                x, y, z, f = spot
                self.put(x, y, z, f'minecraft:chest[facing={f},type=single,waterlogged=false]')
                be = {'id': 'minecraft:chest'}
                if items:
                    be['Items'] = items
                if loot is not None:
                    be['LootTable'] = loot
                self.t.set_be(x, y, z, be)
                placed += 1
        self.stats['chests placed'] = placed

    # ------------------------------------------------------------------------------------------------ all

    def build(self):
        self.survey_chests()
        self.clear()
        self.floors()
        self.room_walls()
        self.doors()
        self.hall()
        self.rooms()
        self.corner_stairs()
        self.vault_stair()
        self.approaches()
        self.place_chests()
        return self.stats


SOFT = ('air', 'carpet', 'torch', 'lantern', 'button', 'pressure_plate', 'sign', 'banner', 'flower', 'short_grass', 'tall_grass',
        'fern', 'rail', 'vine', 'chain', 'ladder', 'snow', 'water', 'lava', 'cobweb', 'potted', 'candle')


def solid(s):
    if s is None:
        return False
    n = s.split(':')[1].split('[')[0]
    return n not in ('air', 'cave_air') and not any(k in n for k in SOFT[1:])


def posts(garrison_path, court):
    """The garrison table with the old throne posts replaced by the new court."""
    g = json.load(open(garrison_path))
    old = [e for e in g['entries'] if e.get('post') == 'throne']
    g['entries'] = [e for e in g['entries'] if e.get('post') != 'throne'] + court
    json.dump(g, open(garrison_path, 'w'), indent=0)
    return len(old), len(court)


if __name__ == '__main__':
    folder = sys.argv[1]
    t = template_io.Template(folder)
    p = Palace(t)
    stats = p.build()
    n = t.save(folder)
    gp = os.path.join(folder, 'garrison.json')
    removed, added = posts(gp, p.posts)
    stats['chunks saved'] = n
    stats['throne posts'] = f'{removed} -> {added}'
    out = dict(stats)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if len(sys.argv) > 2:
        json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
