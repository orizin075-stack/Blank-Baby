import sys
from rig import Rig
from paint import M, paint_rig
from humanoid import Humanoid, tail
from sheet import sheet

def kokuhaku():
    r = Rig('kokuhaku', layout=(128, 128))
    h = Humanoid(r, 'woman', skin='#f4f1f6', accent='#80d8ff')
    white = M('cloth', '#eef2fa', accent='#6fb8f0', pattern='kimono', trim=2)
    hakama = M('cloth', '#26335a', accent='#3fa9ff', fold=4, trim=2)
    h.body(top_mat=white, bottom_mat=hakama, legs_mat=hakama, boots_mat=M('cloth', '#e9edf5'), arms_mat=M('cloth', '#eef2fa', accent='#6fb8f0', trim=2),
           hands_mat=M('skin', '#f4f1f6'), neck='v')
    h.obi(M('cloth', '#33467e', accent='#cfe6ff', pattern='band'), knot=M('cloth', '#33467e', accent='#cfe6ff'))
    h.skirt(M('cloth', '#26335a', accent='#7fd0ff', trim=2, pattern='flame', pattern_glow=True), length=14, flare=0.6, tiers=1)
    h.kimono_sleeves(M('cloth', '#eef2fa', accent='#6fb8f0', trim=2), drop=3)
    h.head_cube({'iris': '#2b55c8', 'iris2': '#ffd45a', 'style': 'normal', 'glow_eyes': True})
    h.hair('#f4f6fb', style='very_long', length=18, tip='#cfe2ff')
    h.horns(M('horn', '#f4f0e0', tip='#8fe3ff', glow=True), kind='dragon', length=11, spread=0.3, base=2)
    tail(r, h.hips, (0, h.hip_y - 1, 2), M('scale', '#eef2fb'), segments=5, length=3, width=3, taper=0.8, droop=0.25, tip_mat=M('scale', '#bfe6ff'))
    return r

r = kokuhaku().pack()
tex, glow = paint_rig(r)
tex.save('/tmp/claude-0/-home-user-Blank-Baby/604d9462-06d6-550f-ad6a-fa3404aa3d62/scratchpad/mc_out_tex.png')
sheet(r, tex, glow, sys.argv[1], 'kokuhaku')
print(len(r.bones), len(r.cubes()))
