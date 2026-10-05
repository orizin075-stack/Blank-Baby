def choose(m):
    a=float(m['a']); b=float(m['b']); c=float(m['c'])
    if (b + c) <= 0.532718181841:
        if a <= 0.303297258799:
            if (a - b) <= 0.152839847187:
                if (b + c) <= 0.521445504185:
                    if (a + b) <= 0.645627760307:
                        if (a - b) <= 0.131458652087:
                            return 'hold'
                        else:
                            return 'hold'
                    else:
                        return 'hold'
                else:
                    return 'hold'
            else:
                if c <= 0.144607321234:
                    if b <= 0.031765041501:
                        return 'hold'
                    else:
                        return 'hold'
                else:
                    return 'audit'
        else:
            if c <= 0.140460539113:
                if (a + b) <= 0.590713463412:
                    if a <= 0.445277878559:
                        if a <= 0.404840578582:
                            return 'hold'
                        else:
                            return 'hold'
                    else:
                        return 'probe'
                else:
                    if a <= 0.347249381272:
                        return 'probe'
                    else:
                        if a <= 0.375215650431:
                            return 'probe'
                        else:
                            return 'probe'
            else:
                if (a - b) <= 0.148936227857:
                    return 'hold'
                else:
                    if (a - b) <= 0.178191707462:
                        return 'audit'
                    else:
                        return 'audit'
    else:
        if (a - b) <= 0.135138084296:
            return 'propose'
        else:
            return 'audit'
