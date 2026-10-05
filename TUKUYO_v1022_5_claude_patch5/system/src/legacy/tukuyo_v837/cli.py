import argparse,json
from .runtime import init_runtime,run_ticks,audit,create_fork,recover

def main():
 p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd',required=True)
 a=sp.add_parser('init'); a.add_argument('root'); a.add_argument('--individual-id',default='TUKUYO-v837-organism-001'); a.add_argument('--energy',type=float,default=100.0); a.add_argument('--reserve',type=float,default=1500.0); a.add_argument('--health',type=float,default=100.0); a.add_argument('--maintenance-debt',type=float,default=0.0); a.add_argument('--experience-profile',choices=['balanced','work_favorable','exploration_favorable'],default='balanced')
 a=sp.add_parser('run'); a.add_argument('root'); a.add_argument('--ticks',type=int,required=True)
 a=sp.add_parser('audit'); a.add_argument('root')
 a=sp.add_parser('recover'); a.add_argument('root')
 a=sp.add_parser('fork'); a.add_argument('parent'); a.add_argument('child'); a.add_argument('--child-id')
 x=p.parse_args()
 if x.cmd=='init': out=init_runtime(x.root,x.individual_id,initial_energy=x.energy,initial_reserve=x.reserve,initial_health=x.health,maintenance_debt=x.maintenance_debt,experience_profile=x.experience_profile)['payload']
 elif x.cmd=='run': run_ticks(x.root,x.ticks); out=audit(x.root)
 elif x.cmd=='audit': out=audit(x.root)
 elif x.cmd=='recover': out={'recovered':recover(x.root),'audit':audit(x.root)}
 else: out=create_fork(x.parent,x.child,x.child_id)['payload']
 print(json.dumps(out,ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
