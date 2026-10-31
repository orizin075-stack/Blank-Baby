"""Where the server thread spends the hundred-man battle: the JFR execution samples of "Server thread" between the
war's start and its result (times from the console log), as the methods most often on top of the stack (self) and the
methods most often anywhere in it (inclusive), and the same grouped by mod package.

  python3 -I jfr_hot.py <recording.jfr> <console.log>
"""
import collections, re, subprocess, sys

rec, console = sys.argv[1:3]
start = end = None
for line in open(console, errors='replace'):
    m = re.match(r'\[(\d\d:\d\d:\d\d)\]', line)
    if not m:
        continue
    if 'CI running /oror war start' in line:
        start = m.group(1)
    elif 'WAR-RESULT' in line and start:
        end = m.group(1)
print('war window', start, end)
PACKAGES = ['jp.oror', 'yesman.epicfight', 'com.nameless', 'io.redspace', 'com.hm.efn', 'com.atsuishio', 'software.bernie', 'net.minecraft',
            'net.neoforged', 'com.github.alexthe666', 'dev.shadowsoffire', 'top.theillusivec4']
proc = subprocess.Popen(['jfr', 'print', '--events', 'jdk.ExecutionSample', '--stack-depth', '48', rec], stdout=subprocess.PIPE, text=True,
                        errors='replace')
self_n, incl_n, pkg_n = collections.Counter(), collections.Counter(), collections.Counter()
total = 0
event = None
for line in proc.stdout:
    s = line.strip()
    if s.startswith('jdk.ExecutionSample'):
        event = {'stack': []}
    elif event is None:
        continue
    elif s.startswith('startTime'):
        event['time'] = s.split('=')[1].strip()[:8]
    elif s.startswith('sampledThread'):
        event['thread'] = s
    elif s.startswith('stackTrace') or s in ('[', ']', '...'):
        continue
    elif s == '}':
        if '"Server thread"' in event.get('thread', '') and (start is None or end is None or start <= event.get('time', '') <= end):
            total += 1
            frames = event['stack']
            if frames:
                self_n[frames[0]] += 1
            for f in set(frames):
                incl_n[f] += 1
            for p in {next((p for p in PACKAGES if f.startswith(p)), None) for f in frames} - {None}:
                pkg_n[p] += 1
        event = None
    else:
        frame = re.sub(r'\s+line:.*$', '', s)
        frame = re.sub(r'\(.*\)$', '', frame)
        event['stack'].append(frame)
proc.wait()
print('server thread samples in the window', total)
print('\n== packages anywhere in the stack (share of samples)')
for p, n in pkg_n.most_common():
    print(f'{n / max(1, total):6.1%}  {p}')
print('\n== on top of the stack (self)')
for f, n in self_n.most_common(40):
    print(f'{n / max(1, total):6.1%}  {f}')
print('\n== anywhere in the stack (inclusive), mods only')
k = 0
for f, n in incl_n.most_common():
    if f.startswith(('net.minecraft', 'java.', 'jdk.', 'net.neoforged', 'it.unimi', 'com.google', 'org.spongepowered', 'cpw.', 'sun.')):
        continue
    print(f'{n / max(1, total):6.1%}  {f}')
    k += 1
    if k >= 70:
        break
print('\n== anywhere in the stack (inclusive), Minecraft')
k = 0
for f, n in incl_n.most_common():
    if f.startswith('net.minecraft'):
        print(f'{n / max(1, total):6.1%}  {f}')
        k += 1
        if k >= 40:
            break
