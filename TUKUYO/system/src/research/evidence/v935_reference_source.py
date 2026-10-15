def choose(m):
    a=float(m['a']); b=float(m['b']); c=float(m['c'])
    if c <= 0.218473645556:
        if (a - b) <= -0.001436886831:
            if b <= 0.196645015167:
                return 'hold'
            else:
                if (a * c) <= 0.055689094037:
                    if (a * c) <= 0.042771859262:
                        if b <= 0.21602248356:
                            return 'propose'
                        else:
                            return 'propose'
                    else:
                        return 'propose'
                else:
                    return 'audit'
        else:
            if a <= 0.198779460064:
                return 'hold'
            else:
                if (b * c) <= 0.060854265148:
                    if (b * c) <= 0.04550943928:
                        if (a - b) <= 0.015985984894:
                            return 'probe'
                        else:
                            return 'probe'
                    else:
                        return 'probe'
                else:
                    return 'audit'
    else:
        if c <= 0.22218370385:
            return 'audit'
        else:
            return 'audit'
