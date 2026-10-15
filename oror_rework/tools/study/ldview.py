"""Render Mojang-mapped LayerDefinition Java models (vanilla style: addOrReplaceChild + CubeListBuilder + PartPose)."""
import re, sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mc'))
from rig import Rig, Bone, Cube, render
from PIL import Image

NUM = r'(-?[\d.]+(?:[eE]-?\d+)?)[FfDd]?'

def fnum(s):
    s = s.strip().rstrip('FfDd')
    try:
        return float(eval(s, {'Math': math, 'PI': math.pi}, {}))
    except Exception:
        return 0.0

def split_args(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out

def call_args(s, start):
    """Return the argument string of the call whose '(' is at s[start]."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == '(':
            depth += 1
        elif s[i] == ')':
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i
    return s[start + 1:], len(s)

def load(java, tex, method=None):
    src = open(java).read()
    if method:
        i = src.find(method)
        src = src[i:i + src[i:].find('LayerDefinition.create')] + src[i + src[i:].find('LayerDefinition.create'):][:200]
    m = re.search(r'LayerDefinition\.create\(\s*\w+\s*,\s*(\d+)\s*,\s*(\d+)', src)
    W, H = (int(m.group(1)), int(m.group(2))) if m else (64, 64)
    r = Rig('study', layout=(W, H))
    var_bone = {}
    for v in re.findall(r'PartDefinition\s+(\w+)\s*=\s*\w+\.getRoot\(\)', src):
        var_bone[v] = None
    for mm in re.finditer(r'(?:PartDefinition\s+(\w+)\s*=\s*)?(\w+)\.addOrReplaceChild\(', src):
        var, parent = mm.group(1), mm.group(2)
        args, end = call_args(src, mm.end() - 1)
        parts = split_args(args)
        if len(parts) < 3:
            continue
        name = parts[0].strip().strip('"')
        cubes_src, pose_src = parts[1], ','.join(parts[2:])
        pb = var_bone.get(parent)
        if parent not in var_bone:
            pb = None
        off, rot = (0, 0, 0), (0, 0, 0)
        pm = re.search(r'PartPose\.(offsetAndRotation|offset|rotation)\((.*)\)', pose_src, re.S)
        if pm:
            vals = [fnum(x) for x in split_args(pm.group(2))]
            if pm.group(1) == 'offsetAndRotation':
                off, rot = tuple(vals[:3]), tuple(vals[3:6])
            elif pm.group(1) == 'offset':
                off = tuple(vals[:3])
            else:
                rot = tuple(vals[:3])
        base = pb.pivot if pb else (0, 0, 0)
        piv = tuple(base[i] + off[i] for i in range(3))
        b = Bone(r, name + str(len(r.bones)), pb, piv, rot, None, {})
        u = v = 0
        for cm in re.finditer(r'texOffs\(\s*(\d+)\s*,\s*(\d+)\s*\)|addBox\(', cubes_src):
            if cm.group(1) is not None:
                u, v = int(cm.group(1)), int(cm.group(2)); continue
            a, _ = call_args(cubes_src, cm.end() - 1)
            al = split_args(a)
            if al and al[0].strip().startswith('"'):
                al = al[1:]
            nums = [fnum(x) for x in al[:6]]
            g = 0.0
            dm = re.search(r'CubeDeformation\(\s*' + NUM, a)
            if dm:
                g = float(dm.group(1))
            if len(nums) == 6:
                c = Cube(b, tuple(nums[:3]), tuple(nums[3:]), None, grow=g)
                c.uv = (u, v)
                b.cubes.append(c)
        r.bones.append(b)
        if var:
            var_bone[var] = b
    return r, Image.open(tex)
