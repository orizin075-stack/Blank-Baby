#!/usr/bin/env python3
import os,subprocess,sys
os.environ['PYTHONDONTWRITEBYTECODE']='1'
r=subprocess.run([sys.executable,'-m','pytest','-q','tests'],env=os.environ.copy())
raise SystemExit(r.returncode)
