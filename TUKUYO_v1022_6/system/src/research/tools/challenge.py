import argparse,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tukuyo_research_v937.challenge import sign_evaluation,verify
if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 ev=sub.add_parser('evaluate');ev.add_argument('--root',default=str(ROOT));ev.add_argument('--task',required=True);ev.add_argument('--dataset',required=True);ev.add_argument('--signer-key-file',required=True);ev.add_argument('--out',required=True);ev.add_argument('--evaluator-declaration',required=True)
 vr=sub.add_parser('verify');vr.add_argument('--root',default=str(ROOT));vr.add_argument('--task',required=True);vr.add_argument('--dataset',required=True);vr.add_argument('--receipt',required=True);vr.add_argument('--result-rows',required=True);vr.add_argument('--trusted-evaluator-pubkey-b64',required=True)
 args=p.parse_args()
 try:
  if args.command=='evaluate':r=sign_evaluation(args.root,args.task,args.dataset,args.signer_key_file,args.out,args.evaluator_declaration)
  else:r=verify(args.root,args.task,args.dataset,args.result_rows,args.receipt,args.trusted_evaluator_pubkey_b64)
  print(json.dumps(r,ensure_ascii=False));sys.exit(0 if args.command=='evaluate' or r['ok'] else 1)
 except Exception as e:print(json.dumps({'ok':False,'error':type(e).__name__+':'+str(e)}));sys.exit(1)
