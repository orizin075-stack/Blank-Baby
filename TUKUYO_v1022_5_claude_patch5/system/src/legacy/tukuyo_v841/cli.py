import argparse,json
from pathlib import Path
from .social import init,audit,make_public_packet,receive_packet,receive_ack,record_private_note,peer_model

def _j(x):print(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True))
def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
 q=sp.add_parser('init');q.add_argument('root');q.add_argument('individual_id')
 q=sp.add_parser('audit');q.add_argument('root')
 q=sp.add_parser('packet');q.add_argument('root');q.add_argument('recipient');q.add_argument('--message',default='');q.add_argument('--out',required=True)
 q=sp.add_parser('receive');q.add_argument('root');q.add_argument('packet');q.add_argument('--ack-out',required=True)
 q=sp.add_parser('ack');q.add_argument('root');q.add_argument('packet');q.add_argument('ack')
 q=sp.add_parser('private-note');q.add_argument('root');q.add_argument('peer');q.add_argument('note')
 q=sp.add_parser('peer');q.add_argument('root');q.add_argument('peer');q.add_argument('--private',action='store_true')
 a=p.parse_args()
 if a.cmd=='init':_j(init(a.root,a.individual_id))
 elif a.cmd=='audit':_j(audit(a.root))
 elif a.cmd=='packet':
  x=make_public_packet(a.root,a.recipient,public_message=a.message);Path(a.out).write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')));_j({'ok':True,'out':a.out})
 elif a.cmd=='receive':
  x=json.loads(Path(a.packet).read_text());ack=receive_packet(a.root,x);Path(a.ack_out).write_text(json.dumps(ack,ensure_ascii=False,sort_keys=True,separators=(',',':')));_j({'ok':True,'ack_out':a.ack_out})
 elif a.cmd=='ack':_j({'ok':receive_ack(a.root,json.loads(Path(a.packet).read_text()),json.loads(Path(a.ack).read_text()))})
 elif a.cmd=='private-note':_j({'note_sha256':record_private_note(a.root,a.peer,a.note)})
 elif a.cmd=='peer':_j(peer_model(a.root,a.peer,include_private=a.private))
