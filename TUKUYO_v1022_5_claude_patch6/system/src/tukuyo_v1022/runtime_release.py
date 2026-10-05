"""Explicit re-pinning of the runtime release used by existing child processes."""
from pathlib import Path
from tukuyo_v1019.transaction import transactional
from tukuyo_v977.startup_guard import verify_distribution
from tukuyo_common.atomic_fs import atomic_write_bytes

@transactional()
def rebind(data,current_trust_file,previous_trust_file):
    if current_trust_file is None:raise ValueError('RUNTIME_REBIND_EXTERNAL_TRUST_REQUIRED')
    current=Path(current_trust_file).read_bytes()
    previous=Path(previous_trust_file).read_text().strip()
    verify_distribution(Path(__file__).resolve().parents[2],current_trust_file)
    files=[Path(data)/forest/'RUNTIME_TRUST.txt' for forest in ('v1021','v1022_ecology') if (Path(data)/forest/'RUNTIME_TRUST.txt').is_file()]
    if not files:raise ValueError('RUNTIME_REBIND_NO_ECOLOGY')
    if any(p.read_text().strip()!=previous for p in files):raise ValueError('RUNTIME_REBIND_PREVIOUS_PIN_MISMATCH')
    for p in files:atomic_write_bytes(p,current)
    return {'ok':True,'previous_public_key':previous,'current_public_key':current.decode().strip(),
            'updated_forests':[p.parent.name for p in files],
            'claim_boundary':{'explicit_external_repin':True,'publisher_key_continuity_proven':False,'individual_keys_rotated':False}}
