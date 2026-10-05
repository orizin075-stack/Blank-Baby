def utility(p,dist):
 pb,qb=p; amb,out=dist; return 1-amb*(1-min(pb,4)/4)-out*(1-min(qb,4)/4)-0.02*(pb+qb)
def neighbors(p):
 a,b=p; return sorted({(max(1,min(4,a+da)),max(1,min(4,b+db))) for da,db in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]})
def improve(p,dist): return max(neighbors(p),key=lambda q:(utility(q,dist),-sum(q),q))
