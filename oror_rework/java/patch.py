import sys
def patch(path, old, new, count=1):
    s = open(path, encoding='utf-8').read()
    n = s.count(old)
    if n != count:
        raise SystemExit(f'{path}: expected {count} match(es), found {n}:\n{old[:200]}')
    s = s.replace(old, new)
    open(path, 'w', encoding='utf-8').write(s)
