import sys,runpy
sys.path.insert(0,sys.argv[1])
import tukuyo_v1023r.agent as A
A.INVENT_DEFAULT=(sys.argv[3]=='1') if len(sys.argv)>3 else False
sys.argv=sys.argv[:3]
runpy.run_path(sys.argv[0].replace('eco_fp_noinv.py','eco_fingerprint.py'),run_name='__main__')
