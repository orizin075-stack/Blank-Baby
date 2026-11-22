"""server_fix.py <mods dir> <server log> <crash dir> <removed.txt>: after a NightfallCraft (Forge 1.20.1) dedicated server
failed to come up, find the mod jars that stopped it and move them out (to <mods dir>/../mods_off), noting each with its
reason in removed.txt. Exit 0 if something was taken out (try again), 1 if nothing could be found (stop).

What it looks for:
  * a client-only mod: "Attempted to load class net/minecraft/client/... for invalid dist DEDICATED_SERVER" with the
    mod's class in the trace, or a crash report's "Mod File:" when the cause is a client class;
  * a mod whose mandatory dependency is missing or of the wrong version (Forge's "Missing or unsupported mandatory
    dependencies" list): the dependent mod is taken out;
  * any other failure Forge pins on one mod file (the crash report's "Mod File:" / "Failure message:").
Nothing is downloaded or run; jars are read as zip files only.
"""
import glob, os, re, shutil, sys, zipfile

mods, log_path, crash_dir, removed = sys.argv[1:5]
off = os.path.join(os.path.dirname(os.path.abspath(mods)), 'mods_off')
os.makedirs(off, exist_ok=True)


def mod_ids(jar):
    try:
        z = zipfile.ZipFile(jar)
        t = z.read('META-INF/mods.toml').decode('utf-8', 'replace')
    except Exception:
        return []
    return re.findall(r'^\s*modId\s*=\s*"([^"]+)"', t, flags=re.M)


def packages(jar):
    try:
        names = zipfile.ZipFile(jar).namelist()
    except Exception:
        return set()
    out = set()
    for n in names:
        if n.endswith('.class') and '/' in n and not n.startswith('META-INF'):
            out.add('/'.join(n.split('/')[:3]))
    return out


jars = sorted(glob.glob(os.path.join(mods, '*.jar')))
by_id = {}
for j in jars:
    for i in mod_ids(j):
        by_id.setdefault(i, j)

text = open(log_path, encoding='utf-8', errors='replace').read() if os.path.exists(log_path) else ''
crashes = sorted(glob.glob(os.path.join(crash_dir, '*.txt')), key=os.path.getmtime)
crash = open(crashes[-1], encoding='utf-8', errors='replace').read() if crashes else ''
both = text + '\n' + crash
take = {}

# missing / wrong-version mandatory dependencies: "Mod ID: 'x', Requested by: 'y', Expected range: ..., Actual version: ..."
for m in re.finditer(r"Mod ID: '([^']+)', Requested by: '([^']+)', Expected range: '([^']*)', Actual version: '([^']*)'", both):
    dep, by, rng, have = m.groups()
    if by in by_id:
        take[by_id[by]] = f'needs {dep} {rng}, has {have or "none"}'

# client classes loaded on the server: the mod whose class asked for it
for m in re.finditer(r'Attempted to load class (net/minecraft/client/[^\s]+) for invalid dist DEDICATED_SERVER', both):
    start = max(0, m.start() - 200)
    window = both[m.start(): m.start() + 6000]
    frames = re.findall(r'at ([a-zA-Z_][\w$]*(?:\.[\w$]+)+)\.[\w$<>]+\(', window)
    for f in frames:
        if f.startswith(('net.minecraft', 'net.minecraftforge', 'java.', 'jdk.', 'cpw.', 'org.spongepowered', 'sun.', 'com.mojang')):
            continue
        pkg = '/'.join(f.split('.')[:3])
        hit = [j for j in jars if pkg in packages(j)]
        if hit:
            take.setdefault(hit[0], f'client class {m.group(1)} from {f}')
            break

# the crash report's own verdict
for m in re.finditer(r'Mod File: (\S+\.jar)', crash):
    path = m.group(1)
    name = os.path.basename(path)
    j = os.path.join(mods, name)
    if os.path.exists(j) and j not in take:
        why = re.search(r'Failure message: (.*)', crash)
        take[j] = 'crash report: ' + (why.group(1).strip()[:200] if why else 'mod file named')
        break

# mixin failures naming a mod's config ("Mixin apply for mod x failed")
for m in re.finditer(r"Mixin (?:apply|prepare) (?:for mod |failed for )?'?([a-z0-9_]+)'? failed", both):
    i = m.group(1)
    if i in by_id and by_id[i] not in take:
        take[by_id[i]] = 'mixin failed'
        break

if not take:
    print('nothing to take out')
    sys.exit(1)
with open(removed, 'a', encoding='utf-8') as f:
    for j, why in take.items():
        if os.path.exists(j):
            shutil.move(j, os.path.join(off, os.path.basename(j)))
            f.write(f'{os.path.basename(j)}\t{why}\n')
            print('taken out:', os.path.basename(j), '-', why)
sys.exit(0)
