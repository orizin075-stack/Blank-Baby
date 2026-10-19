"""Third mechanical pass: Forge 1.20.1 event posting, effect objects, burning, taming, item breaking, mixin casts."""
import os, re, sys
ROOT = sys.argv[1]

def close(s, i):
    """index after the parenthesis group that starts at s[i] == '('"""
    depth = 0
    while True:
        if s[i] == '(':
            depth += 1
        elif s[i] == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1

def posts(s):
    # ((X)MinecraftForge.EVENT_BUS.post(new X(...))).isCanceled()  ->  MinecraftForge.EVENT_BUS.post(new X(...))
    out, i = [], 0
    pat = re.compile(r'\(\((\w+)\)MinecraftForge\.EVENT_BUS\.post\(')
    while True:
        m = pat.search(s, i)
        if not m:
            out.append(s[i:]); break
        start = m.start()
        call = m.end() - 1
        end_call = close(s, call)
        rest = s[end_call:]
        mm = re.match(r'\)\s*\.isCanceled\(\)', rest)
        if not mm:
            out.append(s[i:m.end()]); i = m.end(); continue
        out.append(s[i:start])
        out.append('MinecraftForge.EVENT_BUS.post' + s[call:end_call])
        i = end_call + mm.end()
    return ''.join(out)

n = 0
for base, dirs, files in os.walk(ROOT):
    for f in files:
        if not f.endswith('.java'): continue
        p = os.path.join(base, f); s = open(p, encoding='utf-8').read(); o = s
        s = posts(s)
        s = s.replace('.setTame(true, true)', '.setTame(true)')
        s = re.sub(r'\.igniteForSeconds\(([^;]*?)\);', r'.setSecondsOnFire((int) (\1));', s)
        s = re.sub(r'\(\(MobEffect\)\s*([\w.()]+?)\.getEffect\(\)\.value\(\)\)', r'\1.getEffect()', s)
        s = re.sub(r'LivingEntity\.getSlotForHand\(([^;]*?)\)\);', r'x -> x.broadcastBreakEvent(\1));', s)
        s = s.replace('PositionCheck.Result.FAIL', 'net.minecraftforge.eventbus.api.Event.Result.DENY')
        s = s.replace('new ArrayList(p.getActiveEffects())', 'new ArrayList<>(p.getActiveEffects())')
        s = s.replace('e.getOriginalDamage()', 'e.getAmount()')
        if '/mixin/' in p.replace(os.sep, '/'):
            s = re.sub(r'\((AbstractArrow|Villager|Mob)\)this\b', r'(\1)(Object)this', s)
        if s != o:
            open(p, 'w', encoding='utf-8').write(s); n += 1
print('files', n)
