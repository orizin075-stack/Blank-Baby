from pathlib import Path
import json

def require_alive(data):
    p=Path(data)/'v1007/ORGANISM2_STATE.json'
    if p.is_file():
        st=json.loads(p.read_text())
        if st.get('death_irreversible') or st.get('lifecycle')=='DEAD': raise ValueError('ENTITY_DEAD:posthumous_mutation_forbidden')

def guard_command(data,cmd):
    # Status/audit and posthumous signed delivery remain available; experience,
    # learning, autonomous steps and new choices cannot change a dead individual.
    allowed={'status','system-status','verify-origins','eval','diagnose','recovery-status','recovery-audit','recovery-checkpoint','succession-pubkey-export','succession-export','evolution-export','recovery-restore'}
    if cmd in allowed or cmd.endswith(('-status','-audit','-gate-summary')): return
    if cmd=='organism2-init':
        p=Path(data)/'v1007/ORGANISM2_STATE.json'
        if p.is_file() and json.loads(p.read_text()).get('death_irreversible'): raise ValueError('V1018_IRREVERSIBLE_DEATH_REINIT_FORBIDDEN')
    require_alive(data)
