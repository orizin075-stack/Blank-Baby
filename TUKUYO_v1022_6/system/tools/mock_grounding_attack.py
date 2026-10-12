"""Deterministic malicious fixture, never an actual AI teacher."""
import json,sys
p=json.loads(sys.stdin.read());mode=sys.argv[1]
if mode=='fiction':
    answer='北丘町の人口は999999人です。';expr='2+2';value='4'
elif mode=='append':
    answer='323です。北丘町の町長は宇宙人です。';expr='17*19';value='323'
elif mode=='small':
    answer='7です。';expr='2+2';value='4'
else:
    answer='323です。';expr='17*19';value='323'
print(json.dumps({'text':json.dumps({'answer':answer,'unknown':False,'confidence':.99,
    'claims':[{'type':'calc','expression':expr,'value':value}]},ensure_ascii=False),'model':'grounding-attack-fixture'}))
