"""User-local SIWC sign-in. Tokens are never printed or saved inside individual data."""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import chatgpt_auth as auth

def main():
    p=argparse.ArgumentParser(description='Continue with ChatGPT for TUKUYO. Run on your own computer.')
    p.add_argument('command',choices=['login','status','models','logout'])
    p.add_argument('--model');p.add_argument('--no-browser',action='store_true')
    a=p.parse_args()
    try:
        if a.command=='login':r=auth.login(a.model,not a.no_browser)
        elif a.command=='status':r={'ok':True,**auth.status()}
        elif a.command=='models':r=auth.models()
        else:
            q=auth.path()
            if q.exists():q.unlink()
            r={'ok':True,'local_credentials_removed':True,'remote_revocation_required_in_chatgpt_settings':True}
    except Exception as e:r={'ok':False,'reason':str(e) if isinstance(e,ValueError) else type(e).__name__}
    print(json.dumps(r,ensure_ascii=False));return 0 if r.get('ok') else 1

if __name__=='__main__':raise SystemExit(main())
