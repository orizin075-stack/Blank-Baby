#!/usr/bin/env python3
# Independent resource-system log generator. No tukuyo_v965 import.
def tier(x):
    x=abs(int(x)); level=0; threshold=1; delta=3
    while threshold<=x:
        level+=1; threshold+=delta; delta+=2
    return level
def rows(n=61,offset=0):
    out=[]
    for i in range(n):
        resource=((i*17+offset)%401)-200; adjustment=((i*7+3)%23)-11
        out.append({'schema':'tukuyo.v966.resource_event/1','resource':resource,'adjustment':adjustment,'observed_score':tier(resource)+adjustment})
    return out
