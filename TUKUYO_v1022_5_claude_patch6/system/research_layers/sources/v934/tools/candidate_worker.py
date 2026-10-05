import json,sys,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(1,1));resource.setrlimit(resource.RLIMIT_AS,(128*1024*1024,128*1024*1024));resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
src=Path(sys.argv[1]).read_text();m=json.loads(sys.argv[2]);ns={'__builtins__':{}};exec(compile(src,'<candidate>','exec'),ns);print(json.dumps({'prediction':ns['choose'](m)}))
