"""Icons for all 164 relics. Weapons come from relic_art designs; focus and charm items are drawn from
archetypes picked by the item's name and coloured with its character's palette; legends are the
character's weapon in an awakened form (radiant aura, brighter glow)."""
import math, json, os, sys
import numpy as np
from PIL import Image
from pixart import Art, mat, icon_frame
import relic_art as R

# primary, secondary, accent (glow) per character
PAL = {
    'kokuhaku': ('#d6dde8', '#253058', '#9fe8ff'), 'riha': ('#fffaf0', '#b0335c', '#ffcf5a'), 'tenki': ('#f6f2e8', '#e2b33e', '#9fd8ff'),
    'chaos': ('#3a2050', '#24142e', '#ff6fd0'), 'berit': ('#2a2833', '#d5a449', '#7df0c8'), 'elseria': ('#f6f9ff', '#7fbde6', '#9fe6ff'),
    'valeria': ('#7a8088', '#c8a050', '#ffbf5a'), 'huang_linghua': ('#23202a', '#d8b754', '#8ad8b0'), 'ferdinand': ('#c8a050', '#3c3a52', '#8bcfe2'),
    'mels': ('#bfefff', '#5ab0d0', '#ffffff'), 'hephaistos': ('#5a7088', '#435b71', '#52e8d6'), 'nortia': ('#ff8fb0', '#5a6ad8', '#f4d06f'),
    'lucifara': ('#1e1826', '#c54573', '#ff4a7a'), 'taika': ('#2a1a24', '#e44c49', '#ff9a6a'), 'mary_sue': ('#faf3e7', '#f2bb5b', '#2fa07a'),
    'savior': ('#f8f9fc', '#dac36c', '#fff3b0'), 'gokuka': ('#2a1a2a', '#af55bb', '#e070f0'), 'merlinus': ('#492565', '#c8c8e8', '#b294ee'),
    'enkou': ('#141b28', '#cfdce6', '#7fdcff'), 'kurma': ('#7a7466', '#5e9a3a', '#c8f08a'), 'teia': ('#b8c4d8', '#4a5468', '#b5ffff'),
    'bahamut': ('#2f6f8a', '#e4efe8', '#9fe8d0'), 'nun': ('#1c1426', '#f4f0e8', '#a681d9'), 'arcana': ('#f4f2ea', '#dabd72', '#7a6ad8'),
    'eomaia': ('#b8935a', '#5a3a22', '#ffe9a0'), 'demiurgos': ('#1b2033', '#2c2648', '#ae8ff4'), 'hakyoku': ('#211e2e', '#e0dcec', '#ff627f'),
    'shinra': ('#f3eadf', '#bb5476', '#ff3a6a'), 'ain_sof_aur': ('#f3ecfa', '#a791ee', '#cbbcff'), 'angra_mainyu': ('#1c1822', '#8a6248', '#c0303a'),
    'magna_mater': ('#5a8a40', '#dbb685', '#ffe0f0'), 'ouroboros': ('#3a455e', '#dfb971', '#8ab0e8'), 'yggdrasil': ('#8a6a48', '#6aa04a', '#d8ff8a'),
    'miyohime': ('#f8f4fc', '#c02a4a', '#ba84f0'), 'innocence': ('#f6f6ff', '#c993ff', '#ffd76a'), 'brutality': ('#4a4048', '#8a2a1a', '#ff5030'),
    'cursed_love': ('#351f36', '#aa4b71', '#e06a90'), 'relentless_research': ('#f2f5f6', '#4a8a7a', '#8bdbc7'),
    'forbidden_arcana': ('#281f48', '#5a5070', '#a883ee'), 'fallen_savior': ('#e8ecf4', '#b8a868', '#fff6b0'), 'sweet_pact': ('#d8b175', '#424153', '#ffcf6a'),
}

# focus items that reuse a full design, and renamed focus items
FOCUS_ART = {'tenki': 'tenki_focus', 'demiurgos': 'demiurgos_focus', 'hephaistos': 'hephaistos_focus', 'ain_sof_aur': 'ain_sof_aur_focus',
             'brutality': 'brutality_focus', 'forbidden_arcana': 'forbidden_arcana_focus', 'eomaia': 'eomaia_focus', 'magna_mater': 'magna_mater_focus'}
RENAME = {'elseria_focus': '星脈の天球儀', 'huang_linghua_focus': '三界龍文の霊符', 'arcana_focus': '幸福編成の天羽',
          'yggdrasil_focus': '九界魔流の神実', 'ouroboros_focus': '輪廻記憶の砂時計'}

# ----------------------------------------------------------------------------------- archetypes (upright, u=0 bottom .. 100 top)
def gemstone(a, u, v, r, c, z=6):
    a.ell(u, v, r, r, mat('gem', c, glow=0.6), z)

def a_scabbard(a, p, s, g):
    a.poly([(10, -7), (88, -6), (96, 0), (88, 6), (10, 7)], mat('metal', s), 1)
    for u in (16, 50, 80):
        a.poly([(u, -8), (u + 5, -8), (u + 5, 8), (u, 8)], mat('metal', '#d8b050'), 2)
    a.poly([(4, -5), (10, -6), (10, 6), (4, 5)], mat('metal', p), 2)
    a.curve((50, 8), (40, 22), (24, 20), 2.4, mat('cloth', p), 3)
    a.stroke([(20, 0), (84, 0)], 0.8, mat('energy', g, glow=0.7, outline=False), 3)

def a_ring(a, p, s, g, gem=True, studs=False):
    a.ring(42, 0, 30, 22, mat('metal', s), 1, rv_scale=0.9)
    if studs:
        for k in range(10):
            ang = 2 * math.pi * k / 10
            a.dot(42 + math.cos(ang) * 26, math.sin(ang) * 23.4, mat('metal', '#ffffff'), 3)
    if gem:
        a.poly([(64, -10), (80, -12), (88, 0), (80, 12), (64, 10)], mat('metal', p), 2)
        gemstone(a, 76, 0, 9, g, 4)

def a_crown(a, p, s, g, points=5, kind='crown'):
    a.poly([(10, -40), (34, -40), (34, 40), (10, 40)], mat('metal', s), 2)
    for k in range(points):
        v = -36 + k * 72 / (points - 1)
        tall = 30 + (12 if k == points // 2 else 0)
        if kind == 'horn':
            a.curve((30, v), (30 + tall * 0.6, v * 1.1), (34 + tall, v * 0.7), 6, mat('cloth', p), 1, taper=(8, 1))
        elif kind == 'leaf':
            a.ell(34 + tall * 0.5, v, tall * 0.5, 7, mat('cloth', '#6aa04a'), 1)
        else:
            a.poly([(30, v - 7), (34 + tall, v), (30, v + 7)], mat('metal', s), 1)
            a.ell(34 + tall, v, 3.4, 3.4, mat('gem', g, glow=0.6), 3)
    gemstone(a, 22, 0, 8, g, 4)
    for v in (-24, 24):
        gemstone(a, 22, v, 5, p, 4)

def a_talisman(a, p, s, g, card=False):
    if card:
        a.poly([(8, -26), (92, -26), (92, 26), (8, 26)], mat('cloth', '#f8f0dc'), 1)
        a.poly([(16, -18), (84, -18), (84, 18), (16, 18)], mat('cloth', s), 2)
        a.ring(50, 0, 14, 10, mat('metal', p), 3)
        gemstone(a, 50, 0, 6, g, 4)
    else:
        a.poly([(4, -16), (96, -16), (96, 16), (4, 16)], mat('cloth', '#fbf6e8'), 1)
        a.poly([(84, -16), (96, -16), (96, 16), (84, 16)], mat('cloth', s), 2)
        for k in range(4):
            u = 20 + k * 15
            a.stroke([(u, -8), (u + 6, 4), (u + 10, -6)], 1.6, mat('energy', p if p != '#fbf6e8' else s, glow=0.5, outline=False), 3)
        a.ell(50, 0, 7, 7, mat('energy', g, glow=0.8, outline=False), 2)

def a_pendant(a, p, s, g, motif='gem'):
    a.curve((96, -20), (70, 0), (96, 20), 1.6, mat('metal', '#d8b050', outline=False), 1)
    a.poly([(66, -4), (72, -4), (72, 4), (66, 4)], mat('metal', '#d8b050'), 2)
    if motif == 'feather':
        a.sym([(4, 0.1), (20, 10), (50, 12), (64, 4), (66, 0.1)], mat('cloth', p), 3)
        a.stroke([(6, 0), (64, 0)], 1.0, mat('cloth', s, outline=False), 4)
    elif motif == 'horn':
        for v in (-8, 8):
            a.curve((64, v * 0.5), (36, v * 1.6), (10, v * 0.8), 6, mat('cloth', p), 3, taper=(8, 1))
    elif motif == 'scale':
        a.sym([(14, 0.1), (24, 16), (50, 20), (64, 10), (66, 0.1)], mat('scale', p), 3)
    elif motif == 'claw':
        for v in (-10, 0, 10):
            a.curve((62, v * 0.5), (40, v), (14, v * 1.4 + 6), 5, mat('cloth', '#f0e8d8'), 3, taper=(6, 1))
    elif motif == 'wing':
        for k in range(4):
            a.poly([(64, 0), (60 - k * 12, -8 - k * 5), (44 - k * 12, -2 - k * 4)], mat('cloth', p), 3)
            a.poly([(64, 0), (60 - k * 12, 8 + k * 5), (44 - k * 12, 2 + k * 4)], mat('cloth', p), 3)
    elif motif == 'heart':
        a.sym([(12, 0.1), (30, 14), (50, 20), (62, 10), (58, 0.1)], mat('gem', g, glow=0.7), 3)
        a.ring(40, 0, 16, 13, mat('metal', s), 4)
    elif motif == 'flower':
        for k in range(5):
            ang = 2 * math.pi * k / 5
            a.ell(38 + math.cos(ang) * 14, math.sin(ang) * 14, 11, 9, mat('cloth', p), 3)
        gemstone(a, 38, 0, 7, g, 5)
    else:
        a.sym([(14, 0.1), (24, 16), (46, 20), (64, 10), (66, 0.1)], mat('metal', s), 3)
        gemstone(a, 40, 0, 12, g, 4)

def a_badge(a, p, s, g):
    for v in (-10, 10):
        a.poly([(60, v - 7), (98, v - 6), (98, v + 6), (60, v + 7)], mat('cloth', s), 1)
    star = [(40 + math.cos(2 * math.pi * k / 16) * (34 if k % 2 == 0 else 22), math.sin(2 * math.pi * k / 16) * (34 if k % 2 == 0 else 22)) for k in range(16)]
    a.poly(star, mat('metal', p), 2)
    a.ring(40, 0, 18, 14, mat('metal', s), 3)
    gemstone(a, 40, 0, 10, g, 4)

def a_staff(a, p, s, g, head='orb'):
    a.poly([(2, -3.5), (70, -3.5), (70, 3.5), (2, 3.5)], mat('wood' if head in ('flower', 'coral') else 'metal', s), 1)
    if head == 'coral':
        for k, c in enumerate(('#ff7a8a', '#ffb07a', '#c88aff')):
            a.curve((70, 0), (82, (k - 1) * 16), (98, (k - 1) * 22), 5, mat('cloth', c), 2, taper=(6, 2))
    elif head == 'flower':
        for k in range(6):
            ang = 2 * math.pi * k / 6
            a.ell(84 + math.cos(ang) * 10, math.sin(ang) * 10, 9, 7, mat('cloth', p), 2)
        gemstone(a, 84, 0, 7, g, 4)
    elif head == 'crystal':
        a.sym([(66, 8), (80, 14), (100, 0.1)], mat('gem', g, glow=0.5), 2)
        a.sym([(70, 4), (84, 7), (96, 0.1)], mat('gem', '#ffffff', glow=0.5), 3)
    elif head == 'cross':
        a.poly([(66, -4), (100, -4), (100, 4), (66, 4)], mat('metal', p), 2)
        a.poly([(80, -16), (88, -16), (88, 16), (80, 16)], mat('metal', p), 2)
        a.ring(84, 0, 16, 13, mat('metal', g, glow=0.4), 3)
        gemstone(a, 84, 0, 5, g, 4)
    else:
        a.ring(84, 0, 16, 12, mat('metal', p), 2)
        gemstone(a, 84, 0, 10, g, 3)

def a_book(a, p, s, g, kind='book'):
    if kind == 'page':
        a.poly([(6, -24), (94, -20), (94, 24), (6, 22)], mat('cloth', '#fff8e8'), 1)
        for k in range(6):
            a.stroke([(20 + k * 12, -14), (22 + k * 12, 14)], 1.2, mat('energy', p, glow=0.4, outline=False), 2)
        a.curve((94, -20), (80, -26), (70, -22), 2, mat('cloth', '#e8dcc0'), 2)
    elif kind == 'bookmark':
        a.poly([(20, -10), (98, -10), (98, 10), (20, 10), (8, 0)], mat('cloth', p), 1)
        a.ell(80, 0, 6, 6, mat('gem', g, glow=0.7), 3)
        a.curve((98, 0), (104, -14), (96, -24), 2.4, mat('cloth', s), 2)
    elif kind == 'scroll':
        a.poly([(10, -26), (90, -26), (90, 26), (10, 26)], mat('cloth', '#f6ead0'), 1)
        for u in (6, 94):
            a.poly([(u - 4, -32), (u + 4, -32), (u + 4, 32), (u - 4, 32)], mat('metal', s), 2)
        for k in range(5):
            a.stroke([(24 + k * 12, -16), (24 + k * 12, 16)], 1.0, mat('cloth', '#8a7060', outline=False), 2)
        a.ell(30, 18, 8, 8, mat('cloth', '#c03040'), 3)
        a.dot(30, 18, mat('gem', g, glow=0.6), 4)
    else:
        a.poly([(8, -30), (92, -28), (92, 28), (8, 30)], mat('cloth', p), 1)
        a.poly([(8, 24), (92, 24), (92, 30), (8, 30)], mat('cloth', '#e8e0c8'), 0)
        a.poly([(8, -30), (92, -28), (92, -22), (8, -24)], mat('metal', s), 2)
        a.ring(52, 0, 18, 14, mat('metal', s), 3)
        a.poly([(52, -10), (60, 0), (52, 10), (44, 0)], mat('gem', g, glow=0.7), 4)

def a_bottle(a, p, s, g):
    a.ell(36, 0, 32, 30, mat('gem', '#e8f4ff', glow=0.1), 1)
    a.ell(30, 0, 24, 24, mat('energy', p if p not in ('#1e1826', '#2a1a2a', '#141b28') else g, glow=0.6), 2)
    a.poly([(64, -9), (86, -8), (86, 8), (64, 9)], mat('gem', '#e8f4ff', glow=0.1), 1)
    a.poly([(86, -11), (98, -11), (98, 11), (86, 11)], mat('wood', '#8a6040'), 2)
    a.dot(44, -12, mat('energy', '#ffffff', glow=0.9), 4, r=2)
    a.ring(66, 0, 9, 6, mat('metal', s), 3)

def a_orb(a, p, s, g):
    a.poly([(4, -20), (24, -26), (24, 26), (4, 20)], mat('metal', s), 1)
    for v in (-22, 0, 22):
        a.curve((22, v), (34, v * 1.4), (44, v * 1.1), 5, mat('metal', s), 3, taper=(6, 2))
    a.ell(56, 0, 34, 34, mat('gem', p, glow=0.4), 2)
    a.ell(56, 0, 16, 16, mat('energy', g, glow=0.9, outline=False), 3)
    a.dot(70, -14, mat('energy', '#ffffff', glow=1.0), 4, r=3)

def a_mirror(a, p, s, g):
    a.poly([(2, -6), (34, -6), (34, 6), (2, 6)], mat('metal', s), 1)
    a.ell(66, 0, 32, 30, mat('metal', s), 2)
    a.ell(66, 0, 26, 24, mat('gem', p, glow=0.25), 3)
    a.stroke([(52, -14), (80, 12)], 2.4, mat('energy', '#ffffff', glow=0.6, outline=False), 4)
    gemstone(a, 98, 0, 5, g, 5)

def a_chalice(a, p, s, g):
    a.poly([(2, -26), (10, -28), (10, 28), (2, 26)], mat('metal', s), 1)
    a.poly([(10, -5), (50, -5), (50, 5), (10, 5)], mat('metal', s), 1)
    a.sym([(48, 6), (60, 20), (90, 32), (98, 32), (98, 0.1)], mat('metal', s), 2)
    a.poly([(92, -28), (100, -28), (100, 28), (92, 28)], mat('energy', g if p in ('#1c1822', '#1e1826') else p, glow=0.7), 3)
    gemstone(a, 72, 0, 8, g, 4)

def a_furnace(a, p, s, g):
    a.poly([(2, -32), (70, -30), (70, 30), (2, 32)], mat('metal', s), 1)
    a.poly([(70, -20), (92, -14), (92, 14), (70, 20)], mat('metal', s), 1)
    a.poly([(92, -6), (100, -6), (100, 6), (92, 6)], mat('metal', p), 2)
    a.ell(34, 0, 16, 18, mat('dark', '#1a1018'), 2)
    a.ell(30, 0, 12, 14, mat('energy', g, glow=0.9, outline=False), 3)
    for v in (-26, 26):
        a.poly([(10, v - 3), (64, v - 3), (64, v + 3), (10, v + 3)], mat('metal', p), 3)

def a_clock(a, p, s, g):
    a.ring(44, 0, 38, 32, mat('metal', s), 1)
    a.ell(44, 0, 32, 32, mat('cloth', '#fff8e8'), 2)
    for k in range(12):
        ang = 2 * math.pi * k / 12
        a.dot(44 + math.cos(ang) * 26, math.sin(ang) * 26, mat('metal', p), 3)
    a.stroke([(44, 0), (64, 6)], 2, mat('metal', p, outline=False), 4)
    a.stroke([(44, 0), (52, -18)], 2, mat('metal', p, outline=False), 4)
    a.poly([(82, -6), (96, -6), (96, 6), (82, 6)], mat('metal', s), 1)
    a.ring(100, 0, 6, 3, mat('metal', s), 1)
    gemstone(a, 44, 0, 4, g, 5)

def a_dice(a, p, s, g):
    a.poly([(10, -30), (70, -40), (98, -10), (40, 0)], mat('cloth', '#ffffff'), 2)
    a.poly([(10, -30), (40, 0), (34, 36), (4, 4)], mat('cloth', '#e8e8f8'), 2)
    a.poly([(40, 0), (98, -10), (92, 28), (34, 36)], mat('cloth', '#d8d8f0'), 2)
    for (u, v, c) in ((60, -20, p), (24, -6, s), (20, 12, s), (66, 10, g), (56, 22, g), (78, 2, g)):
        a.ell(u, v, 4, 4, mat('cloth', c), 3)

def a_mask(a, p, s, g):
    a.sym([(6, 0.1), (16, 26), (50, 36), (84, 30), (96, 0.1)], mat('cloth', p), 1)
    for v in (-14, 14):
        a.poly([(58, v - 8), (66, v), (58, v + 8), (50, v)], mat('energy', g, glow=0.9), 3)
    a.curve((26, -12), (18, 0), (26, 12), 2.4, mat('cloth', s, outline=False), 3)
    a.curve((90, -30), (100, -40), (96, -46), 3, mat('cloth', s), 2)

def a_box(a, p, s, g):
    a.poly([(4, -34), (62, -34), (62, 34), (4, 34)], mat('cloth', p), 1)
    a.poly([(60, -38), (78, -36), (78, 36), (60, 38)], mat('cloth', s), 2)
    for k in range(4):
        a.poly([(10 + k * 13, -28), (14 + k * 13, -28), (14 + k * 13, 28), (10 + k * 13, 28)], mat('cloth', s), 2)
    for (u, v, c) in ((86, -14, '#ffd76a'), (92, 10, '#6a8aff'), (98, -2, '#c993ff')):
        a.ell(u, v, 6, 6, mat('gem', c, glow=0.6), 3)
    a.poly([(30, -6), (42, -6), (42, 6), (30, 6)], mat('metal', '#d8b050'), 3)

def a_eye(a, p, s, g):
    a.ring(50, 0, 40, 34, mat('metal', s), 1)
    a.sym([(18, 0.1), (36, 22), (64, 22), (82, 0.1)], mat('cloth', '#f4f0e8'), 2)
    a.ell(50, 0, 14, 14, mat('energy', g, glow=0.9), 3)
    a.ell(50, 0, 6, 3, mat('dark', '#100810'), 4)
    for k in range(8):
        ang = 2 * math.pi * k / 8
        a.dot(50 + math.cos(ang) * 37, math.sin(ang) * 37, mat('metal', p), 2)

def a_stele(a, p, s, g):
    a.poly([(2, -30), (80, -26), (92, -12), (96, 0), (92, 12), (80, 26), (2, 30)], mat('dark', '#7a7466'), 1)
    a.poly([(0, -34), (10, -34), (10, 34), (0, 34)], mat('cloth', '#5e9a3a'), 2)
    for k in range(4):
        a.stroke([(26 + k * 14, -14), (30 + k * 14, 0), (26 + k * 14, 14)], 1.6, mat('energy', g, glow=0.9, outline=False), 3)

def a_shell(a, p, s, g):
    a.sym([(4, 0.1), (10, 30), (40, 40), (80, 32), (96, 0.1)], mat('scale', p), 1)
    for k in range(4):
        a.stroke([(16 + k * 18, -30 + k * 2), (24 + k * 18, 0), (16 + k * 18, 30 - k * 2)], 1.6, mat('metal', s, outline=False), 2)
    gemstone(a, 50, 0, 8, g, 3)

def a_feather(a, p, s, g):
    a.curve((2, 0), (50, 8), (98, -4), 1, mat('cloth', p), 1, taper=(4, 1))
    for k in range(10):
        u = 24 + k * 7
        a.poly([(u, 2), (u + 10, 18 - k), (u + 6, 2)], mat('cloth', p), 2)
        a.poly([(u, -2), (u + 10, -16 + k), (u + 6, -2)], mat('cloth', p), 2)
    a.stroke([(4, 0), (96, -3)], 1.2, mat('cloth', s, outline=False), 3)
    a.dot(90, 6, mat('energy', g, glow=1.0), 4, r=2)

def a_catalyst(a, p, s, g):
    for (u, v, h, w, c) in ((20, -14, 60, 10, g), (14, 6, 76, 13, p), (18, 22, 46, 8, g), (10, -30, 38, 7, s)):
        a.poly([(u, v - w / 2), (u + h * 0.8, v - w / 2), (u + h, v), (u + h * 0.8, v + w / 2), (u, v + w / 2)], mat('gem', c, glow=0.5), 2)
    a.poly([(2, -36), (16, -36), (16, 36), (2, 36)], mat('dark', '#3a3040'), 1)

def a_tool(a, p, s, g):
    a.poly([(4, -5), (70, -5), (70, 5), (4, 5)], mat('metal', s), 1)
    a.ring(80, 0, 16, 9, mat('metal', p), 2)
    a.poly([(88, -6), (100, -6), (100, 6), (88, 6)], mat('energy', '#00000000' if False else '#2a2a30'), 3)
    for k in range(8):
        ang = 2 * math.pi * k / 8
        a.poly([(30 + math.cos(ang) * 10, math.sin(ang) * 10), (30 + math.cos(ang + 0.3) * 15, math.sin(ang + 0.3) * 15),
                (30 + math.cos(ang + 0.6) * 10, math.sin(ang + 0.6) * 10)], mat('metal', p), 2)
    a.ell(30, 0, 9, 9, mat('metal', p), 2)
    gemstone(a, 30, 0, 4, g, 3)

def a_armillary(a, p, s, g):
    a.poly([(2, -18), (12, -18), (12, 18), (2, 18)], mat('metal', s), 1)
    a.poly([(12, -3), (26, -3), (26, 3), (12, 3)], mat('metal', s), 1)
    for k, rv in enumerate((1.0, 0.35, 0.7)):
        a.ring(60, 0, 34, 31, mat('metal', p if k != 1 else s), 2 + k, rv_scale=rv)
    gemstone(a, 60, 0, 10, g, 6)
    a.dot(88, 10, mat('energy', '#ffffff', glow=1.0), 7, r=1.6)

def a_hourglass(a, p, s, g):
    for u in (4, 90):
        a.poly([(u, -34), (u + 8, -34), (u + 8, 34), (u, 34)], mat('metal', s), 3)
    a.poly([(12, -26), (48, -4), (48, 4), (12, 26)], mat('gem', '#e8f4ff', glow=0.1), 1)
    a.poly([(52, -4), (90, -26), (90, 26), (52, 4)], mat('gem', '#e8f4ff', glow=0.1), 1)
    a.poly([(12, -18), (36, -6), (36, 6), (12, 18)], mat('energy', g, glow=0.8), 2)
    a.poly([(70, -6), (88, -14), (88, 14), (70, 6)], mat('energy', g, glow=0.8), 2)
    a.stroke([(36, 0), (70, 0)], 1.2, mat('energy', g, glow=0.8, outline=False), 2)

def a_fruit(a, p, s, g):
    a.ell(44, 0, 34, 32, mat('gem', g, glow=0.4), 1)
    a.ell(44, 0, 16, 16, mat('energy', '#ffffff', glow=0.7, outline=False), 2)
    a.stroke([(76, 0), (96, 4)], 3, mat('wood', '#8a6a48'), 2)
    a.ell(88, -14, 8, 14, mat('cloth', '#6aa04a'), 2)
    for k in range(9):
        ang = 2 * math.pi * k / 9
        a.dot(44 + math.cos(ang) * 24, math.sin(ang) * 22, mat('energy', ['#ffd06a', '#8ad0ff', '#ff8aa8'][k % 3], glow=1.0), 3)

def a_cube_ring(a, p, s, g):
    a.ring(50, 0, 40, 30, mat('metal', s), 1)
    for k in range(12):
        ang = 2 * math.pi * k / 12
        a.stroke([(50 + math.cos(ang) * 30, math.sin(ang) * 30), (50 + math.cos(ang) * 40, math.sin(ang) * 40)], 1.4, mat('energy', g, glow=0.8, outline=False), 2)
    a.poly([(38, -12), (62, -12), (62, 12), (38, 12)], mat('gem', p, glow=0.5), 3)

ARCH = {'scabbard': a_scabbard, 'ring': a_ring, 'bracelet': lambda a, p, s, g: a_ring(a, p, s, g, gem=False, studs=True),
        'crown': a_crown, 'horn_crown': lambda a, p, s, g: a_crown(a, p, s, g, kind='horn', points=4),
        'leaf_crown': lambda a, p, s, g: a_crown(a, p, s, g, kind='leaf', points=6), 'talisman': a_talisman,
        'card': lambda a, p, s, g: a_talisman(a, p, s, g, card=True), 'pendant': a_pendant, 'badge': a_badge, 'staff': a_staff,
        'book': a_book, 'bottle': a_bottle, 'orb': a_orb, 'mirror': a_mirror, 'chalice': a_chalice, 'furnace': a_furnace,
        'clock': a_clock, 'dice': a_dice, 'mask': a_mask, 'box': a_box, 'eye': a_eye, 'stele': a_stele, 'shell': a_shell,
        'feather': a_feather, 'catalyst': a_catalyst, 'tool': a_tool, 'armillary': a_armillary, 'hourglass': a_hourglass,
        'fruit': a_fruit, 'calc_ring': a_cube_ring}

def archetype(name):
    """Pick (archetype, options) from the item's name."""
    rules = [('鞘', 'scabbard', {}), ('天球儀', 'armillary', {}), ('砂時計', 'hourglass', {}), ('神実', 'fruit', {}),
             ('演算環', 'calc_ring', {}), ('角冠', 'horn_crown', {}), ('若葉冠', 'leaf_crown', {}), ('冠', 'crown', {}),
             ('腕輪', 'bracelet', {}), ('指輪', 'ring', {}), ('尾環', 'ring', {}), ('旅環', 'ring', {}), ('王環', 'ring', {}),
             ('母環', 'ring', {}), ('骨環', 'bracelet', {}), ('術環', 'ring', {}), ('の環', 'ring', {}),
             ('運命札', 'card', {}), ('リトライの札', 'card', {}), ('結界札', 'talisman', {}), ('霊符', 'talisman', {}),
             ('羽根', 'feather', {}), ('天羽', 'feather', {}), ('羽飾り', 'pendant', {'motif': 'feather'}), ('翼飾り', 'pendant', {'motif': 'wing'}),
             ('角飾り', 'pendant', {'motif': 'horn'}), ('鱗飾り', 'pendant', {'motif': 'scale'}), ('爪飾り', 'pendant', {'motif': 'claw'}),
             ('心臓飾り', 'pendant', {'motif': 'heart'}), ('花飾り', 'pendant', {'motif': 'flower'}), ('髪飾り', 'pendant', {'motif': 'flower'}),
             ('耳飾り', 'pendant', {}), ('龍鱗', 'pendant', {'motif': 'scale'}), ('鬼角', 'pendant', {'motif': 'horn'}),
             ('護符', 'pendant', {}), ('胸章', 'badge', {}), ('聖印', 'badge', {}), ('珊瑚杖', 'staff', {'head': 'coral'}),
             ('花杖', 'staff', {'head': 'flower'}), ('結晶杖', 'staff', {'head': 'crystal'}), ('祈祷杖', 'staff', {'head': 'cross'}),
             ('杖', 'staff', {}), ('栞', 'book', {'kind': 'bookmark'}), ('頁', 'book', {'kind': 'page'}), ('契約書', 'book', {'kind': 'scroll'}),
             ('詠譜', 'book', {'kind': 'page'}), ('書', 'book', {}), ('液瓶', 'bottle', {}), ('瓶', 'bottle', {}), ('杯', 'chalice', {}),
             ('炉', 'furnace', {}), ('時計', 'clock', {}), ('骰子', 'dice', {}), ('仮面', 'mask', {}), ('玩具箱', 'box', {}),
             ('解析眼', 'eye', {}), ('石碑', 'stele', {}), ('外殻', 'shell', {}), ('殻', 'shell', {}), ('触媒', 'catalyst', {}),
             ('工具', 'tool', {}), ('鏡', 'mirror', {}), ('手甲', 'orb', {}), ('キューブ', 'orb', {}),
             ('核', 'orb', {}), ('珠', 'orb', {})]
    for key, arch, opt in rules:
        if key in name:
            return arch, opt
    return 'pendant', {}

def awaken(base_rgba, base_glow, accent, size):
    """Legend form: radiant aura and sparkles behind the weapon, brighter glow."""
    a = Art(icon_frame(size, upright=True))
    a.ring(50, 0, 46, 40, mat('energy', accent, glow=0.8, outline=False), 0)
    for k in range(8):
        ang = 2 * math.pi * k / 8 + 0.2
        a.poly([(50 + math.cos(ang) * 40, math.sin(ang) * 40), (50 + math.cos(ang + 0.08) * 52, math.sin(ang + 0.08) * 52),
                (50 + math.cos(ang + 0.16) * 40, math.sin(ang + 0.16) * 40)], mat('energy', accent, glow=0.9, outline=False), 0)
    bg, bglow = a.render(outline=False)
    out = bg.copy()
    m = base_rgba[..., 3] > 0
    out[m] = base_rgba[m]
    glow = np.maximum(bglow, base_glow)
    glow[m] = np.maximum(base_glow[m], base_glow[m] * 1.0)
    for (x, y) in ((4, 5), (27, 7), (25, 27), (6, 24)):
        if 0 <= y < size and 0 <= x < size and out[y, x, 3] == 0:
            out[y, x] = (255, 255, 240, 255)
            glow[y, x] = (255, 255, 240, 255)
    return out, glow

def render_relic(rid, slot, char, name, size=32):
    p, s, g = PAL[char]
    if slot == 'weapon':
        return R.render_icon(char, size)
    if slot == 'legend':
        rgba, glow = R.render_icon(char, size)
        return awaken(rgba, glow, g, size)
    if slot == 'focus' and char in FOCUS_ART:
        return R.render_icon(FOCUS_ART[char], size)
    arch, opt = archetype(name)
    a = Art(icon_frame(size, upright=True))
    ARCH[arch](a, p, s, g, **opt)
    return a.render()

def all_relics(relics_json):
    rows = json.load(open(relics_json))
    out = []
    for r in rows:
        name = RENAME.get(r['id'], r['name'])
        if r['slot'] == 'weapon' and r['character'] in R.DESIGNS:
            name = R.DESIGNS[r['character']]['title']
        out.append((r['id'], r['slot'], r['character'], name))
    return out

if __name__ == '__main__':
    from PIL import ImageDraw, ImageFont
    rows = all_relics(sys.argv[1])
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 11)
    S, cols = 96, 12
    sheet = Image.new('RGBA', (cols * (S + 8) + 8, ((len(rows) + cols - 1) // cols) * (S + 30) + 8), (44, 46, 56, 255))
    d = ImageDraw.Draw(sheet)
    for k, (rid, slot, char, name) in enumerate(rows):
        rgba, glow = render_relic(rid, slot, char, name)
        Image.fromarray(rgba, 'RGBA').save(os.path.join(outdir, rid + '.png'))
        x, y = 8 + (k % cols) * (S + 8), 8 + (k // cols) * (S + 30)
        im = Image.fromarray(rgba, 'RGBA').resize((S, S), Image.NEAREST)
        d.rectangle([x - 1, y - 1, x + S + 1, y + S + 1], fill=(58, 60, 72, 255))
        sheet.paste(im, (x, y), im)
        d.text((x, y + S + 2), name[:9], fill=(235, 235, 235, 255), font=font)
        d.text((x, y + S + 15), slot, fill=(160, 160, 170, 255), font=font)
    sheet.save(os.path.join(outdir, '..', 'relic_sheet.png'))
