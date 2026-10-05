def choose(m):
    a=float(m['a']); b=float(m['b']); c=float(m['c'])
    if (a - b) <= -0.093679475981:
        if (a + b) <= 0.580032131811:
            return 'propose'
        else:
            if c <= 0.241794990133:
                if c <= 0.120863288778:
                    if (a * b) <= 0.087494271397:
                        return 'propose'
                    else:
                        if b <= 0.440811268475:
                            return 'audit'
                        else:
                            return 'audit'
                else:
                    if b <= 0.454668723862:
                        return 'propose'
                    else:
                        return 'propose'
            else:
                return 'audit'
    else:
        if a <= 0.319842303008:
            if (a + b) <= 0.575480305426:
                if (a - b) <= -0.079165893964:
                    return 'hold'
                else:
                    return 'hold'
            else:
                return 'audit'
        else:
            if (a * b) <= 0.081933067359:
                if (a + b) <= 0.578384922971:
                    if a <= 0.327573645553:
                        return 'probe'
                    else:
                        return 'probe'
                else:
                    return 'probe'
            else:
                if c <= 0.116919115103:
                    return 'audit'
                else:
                    if c <= 0.238484660156:
                        if c <= 0.139610161972:
                            return 'probe'
                        else:
                            return 'probe'
                    else:
                        if (b - c) <= 0.15369147595:
                            return 'audit'
                        else:
                            return 'audit'
