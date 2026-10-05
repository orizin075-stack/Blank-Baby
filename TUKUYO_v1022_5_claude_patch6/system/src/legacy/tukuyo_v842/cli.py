import argparse,json
from .society import audit

def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True);a=sp.add_parser('audit');a.add_argument('--society',required=True);args=p.parse_args()
 if args.cmd=='audit':print(json.dumps(audit(args.society),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
