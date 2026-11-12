"""jfr_top.py <`jfr print --events jdk.ExecutionSample` text>: where the game's threads spend their time (059c, the user:
"very heavy"). For the server thread and the render thread: the methods most often at the top of the stack (self), the
methods most often anywhere in it (inclusive, once per sample), and the first OROR method under each sample (who in
OROR is behind the time, whatever it called).
"""
import collections, re, sys

THREADS = {'Server thread': 'server', 'Render thread': 'render'}
FRAME = re.compile(r'^\s+([\w$.<>/]+)\(')


def main(path):
    self_c = {k: collections.Counter() for k in THREADS.values()}
    incl = {k: collections.Counter() for k in THREADS.values()}
    oror = {k: collections.Counter() for k in THREADS.values()}
    total = collections.Counter()
    thread, frames, in_stack = None, [], False
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('jdk.ExecutionSample'):
                thread, frames, in_stack = None, [], False
                continue
            s = line.strip()
            if s.startswith('sampledThread = '):
                m = re.match(r'sampledThread = "(.*?)"', s)
                thread = THREADS.get(m.group(1)) if m else None
            elif s.startswith('stackTrace = ['):
                in_stack = True
            elif in_stack and s == ']':
                in_stack = False
            elif in_stack:
                m = FRAME.match(line)
                if m:
                    frames.append(m.group(1))
            elif s == '}' and thread:
                total[thread] += 1
                if frames:
                    self_c[thread][frames[0]] += 1
                    for fr in set(frames):
                        incl[thread][fr] += 1
                    first = next((fr for fr in frames if fr.startswith('jp.oror')), None)
                    if first:
                        oror[thread][first] += 1
                thread = None
    for t in THREADS.values():
        n = max(1, total[t])
        print('== %s thread: %d samples' % (t, total[t]))
        print('-- self (top of stack)')
        for k, v in self_c[t].most_common(35):
            print('%6.2f%%  %s' % (100.0 * v / n, k))
        print('-- inclusive')
        for k, v in incl[t].most_common(60):
            print('%6.2f%%  %s' % (100.0 * v / n, k))
        print('-- first OROR frame')
        for k, v in oror[t].most_common(40):
            print('%6.2f%%  %s' % (100.0 * v / n, k))
        print()


if __name__ == '__main__':
    main(sys.argv[1])
