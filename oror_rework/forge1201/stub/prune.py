"""Remove from the Forge skeletons every declaration javac cannot resolve (types of libraries we do not stub).
Class headers lose the unresolved extends/implements; members on the reported line are dropped."""
import re, sys, collections
log, root = sys.argv[1], sys.argv[2]
errs = collections.defaultdict(set)
for m in re.finditer(r'^(\S+\.java):(\d+): error: (.*)$', open(log, encoding='utf-8', errors='ignore').read(), re.M):
    f, ln = m.group(1), int(m.group(2))
    if f.startswith(root):
        errs[f].add(ln)
n = 0
for f, lines in errs.items():
    src = open(f, encoding='utf-8').read().split('\n')
    for ln in sorted(lines, reverse=True):
        i = ln - 1
        s = src[i]
        hm = re.search(r'\b(class|interface|enum|record)\s+\w+', s)
        if hm and s.rstrip().endswith('{'):
            line = s.rstrip()[:-1]
            j = hm.end()
            tparams = ''
            if j < len(line) and line[j] == '<':
                depth, k = 0, j
                while True:
                    depth += {'<': 1, '>': -1}.get(line[k], 0)
                    k += 1
                    if depth == 0: break
                # unbounded type parameters: bounds may name types we do not stub
                names = [re.match(r'\s*(\w+)', x).group(1) for x in re.split(r',(?![^<]*>)', line[j + 1:k - 1])]
                tparams = '<' + ', '.join(names) + '>'
                j = k
            head = line[:hm.end()] + tparams + ' {'
            if head == s.rstrip():
                continue
            src[i] = head
        elif s.strip().startswith('import '):
            src[i] = ''
        elif s.strip() != '}' and (s.rstrip().endswith(';') or s.rstrip().endswith('}')):
            src[i] = ''
        else:
            continue
        n += 1
    open(f, 'w', encoding='utf-8').write('\n'.join(src))
print('pruned', n)
