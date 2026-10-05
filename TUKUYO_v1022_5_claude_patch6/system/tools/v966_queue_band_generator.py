#!/usr/bin/env python3
# Independent queue simulator. Computes bands by explicit capacity-boundary iteration.
def band(depth):
    x=abs(int(depth)); k=0; boundary=1
    while True:
        nxt=(k+2)*(k+2)
        if x<nxt: return k+1 if x>=boundary else k
        k+=1; boundary=(k+1)*(k+1)
def rows(n=67,offset=0):
    out=[]
    for i in range(n):
        depth=((i*29+offset)%529)-264; penalty=((i*13+5)%19)-9
        # explicit independent oracle: floor sqrt(abs(depth)) + penalty
        import math
        observed=math.isqrt(abs(depth))+penalty
        out.append({'schema':'tukuyo.v966.queue_sample/1','depth':depth,'penalty':penalty,'observed_priority':observed})
    return out
