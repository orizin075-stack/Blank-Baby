from __future__ import annotations
import base64,functools,hashlib,json,os,re,shutil,tempfile,time,uuid
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from tukuyo_v977.whole_state import canon,_live_identity,audit as whole_audit
from tukuyo_v989.temporal_identity import audit as identity_audit
from tukuyo_v1013.realtime_continuity import audit as realtime_audit
from tukuyo_common.atomic_fs import atomic_write_bytes,atomic_write_text,atomic_write_json,durable_unlink,maybe_crash,_fsync_dir

SCHEMA='tukuyo.v1014.recovery_checkpoint/1'
RECEIPT_SCHEMA='tukuyo.v1014.recovery_receipt/1'
CHECKPOINT_TXN_SCHEMA='tukuyo.v1014_2.checkpoint_txn/1'
RESTORE_TXN_SCHEMA='tukuyo.v1014_2.restore_txn/1'
MAX_BYTES=32*1024*1024
EXCLUDE_PARTS={'__pycache__','.pytest_cache','private','recovery_checkpoints','recovery_blobs','.lineage_transaction'}
# Private cryptographic material survives a checkpoint restore by design, but
# transient transaction markers must not.  In particular this matters for
# nested runtime trees whose startup recovery is not necessarily invoked before
# the owner resumes them in a later process.
EPHEMERAL_PRIVATE_NAMES={'PENDING_MUTATION.json','REALTIME_PENDING.json','EPISODE_TXN.json','CONVERSATION_TXN.json','CHECKPOINT_TXN.json'}

def _is_ephemeral_private_name(name):
 return name in EPHEMERAL_PRIVATE_NAMES or name.endswith('_TXN.json') or name.endswith('_PENDING.json')

def _locked(fn):
 @functools.wraps(fn)
 def call(data,*args,**kwargs):
  from tukuyo_v1019.transaction import _writer_lock
  with _writer_lock(data):return fn(data,*args,**kwargs)
 return call

def _clear_private_ephemera(data):
 removed=[]
 for p in Path(data).rglob('*'):
  if not p.is_file() or p.is_symlink() or 'private' not in p.relative_to(data).parts:continue
  if _is_ephemeral_private_name(p.name) and not (p.parent==root(data)/'private' and p.name=='RESTORE_TXN.json'):
   durable_unlink(p);removed.append(p.relative_to(data).as_posix())
 # A prepared lineage redo can contain every byte of a later generation.
 # It is superseded by the explicitly restored checkpoint, including on
 # nested children. Leaving it behind would resurrect the future at startup.
 for p in sorted(Path(data).rglob('.lineage_transaction'),key=lambda q:len(q.parts),reverse=True):
  if p.is_dir() and not p.is_symlink():
   shutil.rmtree(p);_fsync_dir(p.parent);removed.append(p.relative_to(data).as_posix())
 return sorted(removed)

def _projection_errors(data,stage,targets,ignore_receipt=False):
 errs=[];data=Path(data);stage=Path(stage)
 actual=set()
 for p in data.rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  rel=p.relative_to(data)
  if any(x in EXCLUDE_PARTS for x in rel.parts):continue
  actual.add(rel.as_posix())
 expected=set(targets)
 if ignore_receipt:
  actual.discard('v1014/LAST_RECOVERY_RECEIPT.json');expected.discard('v1014/LAST_RECOVERY_RECEIPT.json')
 if actual!=expected:
  for x in sorted(actual-expected)[:20]:errs.append('RESTORE_EXTRA_FILE:'+x)
  for x in sorted(expected-actual)[:20]:errs.append('RESTORE_MISSING_FILE:'+x)
 for rel in sorted(expected):
  a=data/rel;b=stage/rel
  if not a.is_file() or not b.is_file() or _sha(a.read_bytes())!=_sha(b.read_bytes()):errs.append('RESTORE_BYTE_DRIFT:'+rel)
 return errs

def root(data):return Path(data)/'v1014'
def _key_paths(data):return root(data)/'private'/'recovery.key',root(data)/'recovery.pub'
def _checkpoint_dir(data):return root(data)/'recovery_checkpoints'
def _blob_dir(data):return root(data)/'recovery_blobs'
def _checkpoint_txn_path(data):return root(data)/'private'/'CHECKPOINT_TXN.json'
def _restore_txn_path(data):return root(data)/'private'/'RESTORE_TXN.json'
def _canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def _sha(b):return hashlib.sha256(b).hexdigest()
def _write(p,o,crashpoint=None):atomic_write_bytes(p,_canon(o)+b'\n',crashpoint=crashpoint)

def _ensure_key(data):
 skp,pkp=_key_paths(data);skp.parent.mkdir(parents=True,exist_ok=True)
 if skp.exists():
  sk64=skp.read_text().strip()
  try:sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64,validate=True))
  except Exception as e:raise ValueError('RECOVERY_PRIVATE_KEY_INVALID:'+type(e).__name__)
  derived=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
  if pkp.exists():
   published=pkp.read_text().strip()
   if published!=derived:raise ValueError('RECOVERY_KEYPAIR_MISMATCH')
  else:atomic_write_text(pkp,derived)
  os.chmod(skp,0o600);return sk64,derived
 if pkp.exists():raise ValueError('RECOVERY_PRIVATE_KEY_MISSING')
 sk=Ed25519PrivateKey.generate();sk64=base64.b64encode(sk.private_bytes_raw()).decode();pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
 atomic_write_text(skp,sk64,mode=0o600);atomic_write_text(pkp,pub);return sk64,pub

def _collect(data):
 data=Path(data);files={};total=0;bd=_blob_dir(data);bd.mkdir(parents=True,exist_ok=True)
 for p in sorted(data.rglob('*')):
  if not p.is_file() or p.is_symlink():continue
  rel=p.relative_to(data)
  if any(x in EXCLUDE_PARTS for x in rel.parts):continue
  if rel.as_posix()=='v1001/knowledge_index.sqlite3':continue
  b=p.read_bytes();h=_sha(b);total+=len(b);bp=bd/h
  if not bp.is_file():atomic_write_bytes(bp,b)
  elif _sha(bp.read_bytes())!=h:raise ValueError('RECOVERY_BLOB_HASH_COLLISION_OR_CORRUPTION')
  files[rel.as_posix()]={'sha256':h,'size':len(b),'blob_sha256':h}
 return files,total

@_locked
def recover_checkpoint_commit(data):
 m=_checkpoint_txn_path(data)
 if not m.is_file():return {'ok':True,'version':'v1014.2','recovered':False}
 try:tx=json.loads(m.read_text(encoding='utf-8'))
 except Exception as e:raise ValueError('CHECKPOINT_TXN_MALFORMED:'+type(e).__name__)
 if tx.get('schema')!=CHECKPOINT_TXN_SCHEMA:raise ValueError('CHECKPOINT_TXN_SCHEMA')
 out=_checkpoint_dir(data)/tx['checkpoint_file']
 if not out.is_file() or _sha(out.read_bytes())!=tx.get('checkpoint_sha256'):
  durable_unlink(m);return {'ok':True,'version':'v1014.2','recovered':False,'rolled_back':True}
 _write(root(data)/'LATEST_RECOVERY_CHECKPOINT.json',tx['latest'])
 durable_unlink(m)
 return {'ok':True,'version':'v1014.2','recovered':True,'checkpoint_id':tx.get('checkpoint_id')}

@_locked
def create_checkpoint(data,note=''):
 recover_checkpoint_commit(data)
 ia=identity_audit(data);wa=whole_audit(data);ra=realtime_audit(data,subaudits=True)
 if not ia.get('ok') or not wa.get('ok') or not ra.get('ok'):raise ValueError('RECOVERY_CHECKPOINT_PRECHECK_FAILED')
 sk64,pub=_ensure_key(data);files,total=_collect(data);ident=_live_identity(data);cid='rc-'+uuid.uuid4().hex[:16]
 payload={'schema':SCHEMA,'version':'v1014.2','checkpoint_id':cid,'created_utc_ns':time.time_ns(),'identity':ident,'note':str(note)[:240],
  'realtime':{'run_id':ra.get('run_id'),'events':ra.get('events'),'head_sha256':ra.get('head_sha256')},
  'temporal_identity':{'origin_soul_sha256':ia.get('origin_soul_sha256'),'current_soul_sha256':ia.get('current_soul_sha256'),'transition_count':ia.get('transition_count'),'transition_head_sha256':ia.get('transition_head_sha256')},
  'files':files,'file_count':len(files),'total_bytes':total,'storage_mode':'content_addressed_delta_v1014_4'}
 sig=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64)).sign(_canon(payload));env={'payload':payload,'public_key':pub,'signature':base64.b64encode(sig).decode()}
 out=_checkpoint_dir(data)/(cid+'.json');raw=_canon(env)+b'\n';latest={'schema':'tukuyo.v1014.latest/1','checkpoint_id':cid,'path':out.name,'sha256':_sha(raw)}
 tx={'schema':CHECKPOINT_TXN_SCHEMA,'checkpoint_id':cid,'checkpoint_file':out.name,'checkpoint_sha256':_sha(raw),'latest':latest,'created_utc_ns':time.time_ns()}
 _write(_checkpoint_txn_path(data),tx)
 atomic_write_bytes(out,raw,crashpoint='checkpoint_file');maybe_crash('checkpoint:after_checkpoint')
 _write(root(data)/'LATEST_RECOVERY_CHECKPOINT.json',latest);durable_unlink(_checkpoint_txn_path(data))
 return {'ok':True,'version':'v1014.4','checkpoint_id':cid,'path':str(out),'file_count':len(files),'total_bytes':total,'storage_mode':'content_addressed_delta_v1014_4','blob_count':len({m.get('blob_sha256') for m in files.values() if m.get('blob_sha256')}),'realtime_seq':ra.get('events'),'realtime_head_sha256':ra.get('head_sha256')}

def _verify_env(path,trust_file=None):
 env=json.loads(Path(path).read_text(encoding='utf-8'));p=env.get('payload',{});errs=[]
 try:
  if p.get('schema')!=SCHEMA:errs.append('CHECKPOINT_SCHEMA')
  if not re.fullmatch(r'rc-[A-Za-z0-9_-]{1,80}',str(p.get('checkpoint_id',''))):errs.append('CHECKPOINT_ID')
  pub=env.get('public_key','')
  if trust_file is not None and Path(trust_file).read_text().strip()!=pub:errs.append('CHECKPOINT_TRUST_ROOT')
  Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(env.get('signature',''),validate=True),_canon(p))
 except Exception as e:errs.append('CHECKPOINT_SIGNATURE:'+type(e).__name__)
 files=p.get('files',{});total=0
 checkpoint_path=Path(path).resolve();data_root=checkpoint_path.parent.parent.parent
 for rel,m in files.items():
  q=Path(rel)
  if q.is_absolute() or '..' in q.parts or any(x in EXCLUDE_PARTS for x in q.parts):errs.append('CHECKPOINT_PATH:'+rel);continue
  if 'b64' in m:
   try:b=base64.b64decode(m['b64'],validate=True)
   except Exception:errs.append('CHECKPOINT_B64:'+rel);continue
  elif 'blob_sha256' in m:
   h=str(m.get('blob_sha256'));bp=data_root/'v1014'/'recovery_blobs'/h
   if not bp.is_file():errs.append('CHECKPOINT_BLOB_MISSING:'+rel);continue
   try:b=bp.read_bytes()
   except Exception:errs.append('CHECKPOINT_BLOB_READ:'+rel);continue
   if _sha(b)!=h:errs.append('CHECKPOINT_BLOB_HASH:'+rel)
  else:
   errs.append('CHECKPOINT_STORAGE:'+rel);continue
  total+=len(b)
  if len(b)!=m.get('size') or _sha(b)!=m.get('sha256'):errs.append('CHECKPOINT_HASH:'+rel)
 if total!=p.get('total_bytes') or len(files)!=p.get('file_count'):errs.append('CHECKPOINT_COUNTS')
 return env,sorted(set(errs))

def audit_checkpoint(path,trust_file=None):
 env,errs=_verify_env(path,trust_file);p=env.get('payload',{})
 return {'ok':not errs,'version':'v1014.2','errors':errs,'checkpoint_id':p.get('checkpoint_id'),'identity':p.get('identity'),'file_count':p.get('file_count'),'total_bytes':p.get('total_bytes'),'realtime':p.get('realtime')}

def _safe_txn_stage(data,name):
 parent=Path(data).parent;candidate=parent/name
 if candidate.is_symlink():raise ValueError('RESTORE_STAGE_SYMLINK')
 stage=candidate.resolve()
 if stage.parent!=parent.resolve() or not stage.name.startswith('.tukuyo-v1014-restore-'):raise ValueError('RESTORE_STAGE_PATH')
 return stage

def _validate_restore_stage(data,tx,stage):
 if Path(stage).is_symlink():raise ValueError('RESTORE_STAGE_SYMLINK')
 # The prepared after-image is authenticated independently of the mutable
 # stage directory. A crash never grants permission to replay changed bytes.
 auth=tx.get('authentication',{});body=dict(tx);body.pop('authentication',None)
 pub=(root(data)/'recovery.pub').read_text().strip()
 try:
  if auth.get('public_key')!=pub:raise ValueError('TRUST')
  Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(
   base64.b64decode(auth.get('signature',''),validate=True),_canon(body))
 except Exception as e:raise ValueError('RESTORE_TXN_AUTHENTICATION') from e
 metadata=tx.get('file_metadata',{})
 if set(tx.get('files',[]))!=set(metadata):raise ValueError('RESTORE_TXN_FILE_BINDING')
 from tukuyo_v1019.transaction import _reject_symlinks
 _reject_symlinks(stage)
 for rel,m in metadata.items():
  q=Path(rel)
  if q.is_absolute() or not q.parts or '..' in q.parts or q.as_posix()!=rel or '\\' in rel or any(x in EXCLUDE_PARTS for x in q.parts):raise ValueError('RESTORE_TXN_PATH')
  p=stage/q
  if not p.is_file() or p.stat().st_size!=m['size'] or _sha(p.read_bytes())!=m['sha256']:raise ValueError('RESTORE_STAGE_HASH:'+rel)
 errs=_projection_errors(stage,stage,metadata)
 if errs:raise ValueError('RESTORE_STAGE_PROJECTION:'+','.join(errs))

def _retire_orphan_runtimes(data,tx):
 # A child born after the checkpoint must not be re-initialized with leftover
 # private keys. Retain its private material outside the active runtime forest.
 keep={Path(*Path(rel).parts[:-2]).as_posix() for rel in tx['files'] if Path(rel).parts[-2:]==('state','integration_state.json')}
 retired=[]
 for forest in ('v1021','v1022_ecology'):
  directory=Path(data)/forest/'runtimes'
  if not directory.is_dir():continue
  for p in sorted(directory.iterdir()):
   rel=p.relative_to(data).as_posix()
   if p.is_dir() and rel not in keep:
    target=root(data)/'private'/'retired_runtimes'/tx['checkpoint_id']/forest/(p.name+'-'+uuid.uuid4().hex)
    target.parent.mkdir(parents=True,exist_ok=True)
    os.replace(p,target);_fsync_dir(p.parent);_fsync_dir(target.parent)
    retired.append(rel)
 return retired

def _materialize_projection(data,tx,stage):
 # This function operates only on an unpublished full-root replacement.
 data=Path(data);targets=set(tx['files'])
 # Remove stale managed files. Secret/private and checkpoint stores are never part of this commit.
 for q in sorted(data.rglob('*'),reverse=True):
  if not q.is_file() or q.is_symlink():continue
  rel=q.relative_to(data)
  if any(x in EXCLUDE_PARTS for x in rel.parts):continue
  if rel.as_posix()=='v1014/recovery.pub':continue
  if rel.as_posix() not in targets:
   for _attempt in range(3):
    durable_unlink(q)
    if not q.exists():break
   else:raise ValueError('RESTORE_DELETE_VERIFY:'+rel.as_posix())
 copied=0
 for rel in sorted(targets):
  src=stage/rel;dst=data/rel
  if not src.is_file():raise ValueError('RESTORE_STAGE_FILE_MISSING:'+rel)
  raw=src.read_bytes()
  for _attempt in range(3):
   atomic_write_bytes(dst,raw)
   if dst.is_file() and dst.read_bytes()==raw:break
  else:raise ValueError('RESTORE_WRITE_VERIFY:'+rel)
  copied+=1
 retired=_retire_orphan_runtimes(data,tx)
 # A later tick may have materialized an optional component. Removing its
 # files but leaving its directory makes legacy audits create a new default
 # state, outside the checkpoint's signed head. Remove empty managed paths.
 for q in sorted(data.rglob('*'),key=lambda q:len(q.parts),reverse=True):
  if q.is_dir() and not q.is_symlink() and not any(x in EXCLUDE_PARTS for x in q.relative_to(data).parts):
   try:q.rmdir()
   except OSError:pass
 # Rollback semantics include nested private WAL/transaction markers. Keys and
 # delegation secrets survive; only non-authoritative pending work is removed.
 _clear_private_ephemera(data)
 errs=_projection_errors(data,stage,targets)
 if errs:raise ValueError('RESTORE_PROJECTION:'+','.join(errs))
 live_pub=tx['recovery_public_key'];atomic_write_text(data/'v1014'/'recovery.pub',live_pub)
 receipt={'schema':RECEIPT_SCHEMA,'version':'v1014.2','checkpoint_id':tx['checkpoint_id'],'restored_utc_ns':time.time_ns(),'identity':tx['identity'],'realtime_head_sha256':tx.get('realtime_head_sha256'),'anchor_checked':bool(tx.get('anchor_checked')),'recovery_public_key':live_pub,'atomic_recovery':True,'prepared_afterimage_verified':True,'directory_namespace_swap':True,'retired_future_runtimes':retired}
 _write(root(data)/'LAST_RECOVERY_RECEIPT.json',receipt)
 durable_unlink(_restore_txn_path(data))
 return copied

def _swap_marker(data):
 data=Path(data).absolute()
 return data.parent/('.tukuyo-v1014-swap-'+_sha(str(data).encode())+'.json')

def _safe_backup(data,name):
 if not isinstance(name,str) or Path(name).name!=name or not name.startswith('.tukuyo-v1014-before-'):raise ValueError('RESTORE_SWAP_BACKUP_PATH')
 p=Path(data).parent/name
 if p.is_symlink():raise ValueError('RESTORE_SWAP_BACKUP_SYMLINK')
 return p

def _image_hashes(image):
 if Path(image).is_symlink():raise ValueError('RESTORE_IMAGE_ROOT_SYMLINK')
 from tukuyo_v1019.transaction import _reject_symlinks
 _reject_symlinks(image)
 return {p.relative_to(image).as_posix():_sha(p.read_bytes()) for p in Path(image).rglob('*') if p.is_file()}

def _flush_image(image):
 for p in Path(image).rglob('*'):
  if p.is_file():
   with p.open('rb') as f:os.fsync(f.fileno())
 for p in sorted(Path(image).rglob('*'),key=lambda q:len(q.parts),reverse=True):
  if p.is_dir():_fsync_dir(p)
 _fsync_dir(image);_fsync_dir(Path(image).parent)

def _sign_control(data,body):
 sk,pub=_ensure_key(data)
 return {'body':body,'public_key':pub,'signature':base64.b64encode(Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk)).sign(_canon(body))).decode()}

def _completion_path(data,control):
 return root(data)/'private'/'completed_restores'/(_sha(_canon(control['body']))+'.json')

def _completed_swap(data,control,pub):
 p=_completion_path(data,control)
 if p.is_symlink():raise ValueError('RESTORE_COMPLETION_SYMLINK')
 if not p.is_file():return False
 try:
  ack=json.loads(p.read_text());body=ack['body']
  expected={'schema':'tukuyo.v1022_4.restore_completion/1','data_root':str(Path(data).absolute()),'control_sha256':_sha(_canon(control['body']))}
  if body!=expected or ack.get('public_key')!=pub or (root(data)/'recovery.pub').read_text().strip()!=pub:raise ValueError('BINDING')
  Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(ack['signature'],validate=True),_canon(body))
 except Exception as e:raise ValueError('RESTORE_COMPLETION_AUTHENTICATION') from e
 return True

def _finish_swap(data,control,backup,stage_root,already_published=False):
 # The acknowledgement survives cleanup and explicit checkpoint rollback.
 # Only an exact verified publication reaches this point. A replayed prepare
 # record must not undo later legitimate changes to the same individual.
 body={'schema':'tukuyo.v1022_4.restore_completion/1','data_root':str(Path(data).absolute()),'control_sha256':_sha(_canon(control['body']))}
 _write(_completion_path(data,control),_sign_control(data,body))
 if not _completed_swap(data,control,control['public_key']):raise ValueError('RESTORE_COMPLETION_READBACK')
 durable_unlink(_swap_marker(data))
 shutil.rmtree(backup,ignore_errors=True);shutil.rmtree(stage_root,ignore_errors=True)
 return {'ok':True,'version':'v1014.2','recovered':True,'checkpoint_id':control['body']['transaction']['checkpoint_id'],'copied_files':len(control['body']['transaction']['files']),'directory_namespace_swap':True,'already_published_afterimage_verified':already_published}

def _resume_swap(data,control,inject=False):
 data=Path(data).absolute();body=control.get('body',{})
 if data.is_symlink():raise ValueError('RESTORE_LIVE_ROOT_SYMLINK')
 if body.get('schema')!='tukuyo.v1022_4.restore_namespace_swap/1' or body.get('data_root')!=str(data):raise ValueError('RESTORE_SWAP_BINDING')
 tx=body['transaction'];stage_root=_safe_txn_stage(data,tx['stage_dir']);stage=stage_root/'stage';image=stage_root/'live'
 backup=_safe_backup(data,body['backup_dir'])
 authority=data if (root(data)/'recovery.pub').is_file() else backup
 try:
  pub=(root(authority)/'recovery.pub').read_text().strip()
  if control.get('public_key')!=pub:raise ValueError('TRUST')
  Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(control['signature'],validate=True),_canon(body))
 except Exception as e:raise ValueError('RESTORE_SWAP_AUTHENTICATION') from e
 if data.is_dir() and _completed_swap(data,control,pub):
  durable_unlink(_swap_marker(data))
  shutil.rmtree(backup,ignore_errors=True);shutil.rmtree(stage_root,ignore_errors=True)
  return {'ok':True,'version':'v1014.2','recovered':False,'previously_completed_restore':True,'checkpoint_id':tx['checkpoint_id']}
 # A crash or delayed cleanup may leave a partial disposable image even
 # though the signed after-image has already become the live root. Prefer
 # that independently authenticated full-root match over staging existence.
 if data.is_dir() and _image_hashes(data)==body['image_file_hashes']:
  return _finish_swap(data,control,backup,stage_root,already_published=True)
 _validate_restore_stage(authority,tx,stage)
 if image.is_dir():
  if _image_hashes(image)!=body['image_file_hashes']:raise ValueError('RESTORE_SWAP_IMAGE_HASH')
  if backup.exists():
   if data.exists():raise ValueError('RESTORE_SWAP_AMBIGUOUS_ROOTS')
  else:
   if not data.is_dir():raise ValueError('RESTORE_SWAP_SOURCE_MISSING')
   os.replace(data,backup);_fsync_dir(data.parent)
   if inject:maybe_crash('restore:mid_commit')
  os.replace(image,data);_fsync_dir(data.parent)
  if inject:maybe_crash('restore:after_namespace_swap')
 elif not backup.is_dir() or not data.is_dir():raise ValueError('RESTORE_SWAP_IMAGE_MISSING')
 # A retained sidecar is authoritative even when the live path temporarily
 # does not exist. Acknowledge only the exact prepared full-root after-image.
 if _image_hashes(data)!=body['image_file_hashes']:raise ValueError('RESTORE_SWAP_READBACK')
 errs=_projection_errors(data,stage,tx['files'],ignore_receipt=True)
 if errs:raise ValueError('RESTORE_SWAP_PROJECTION:'+','.join(errs))
 return _finish_swap(data,control,backup,stage_root)

def _commit_restore_transaction(data,tx,inject=False):
 data=Path(data).absolute();stage_root=_safe_txn_stage(data,tx['stage_dir']);stage=stage_root/'stage'
 if not stage.is_dir():raise ValueError('RESTORE_STAGE_MISSING')
 _validate_restore_stage(data,tx,stage)
 image=stage_root/'live'
 if image.exists():shutil.rmtree(image)
 shutil.copytree(data,image,ignore=shutil.ignore_patterns('.lineage_transaction'))
 _materialize_projection(image,tx,stage)
 _flush_image(image)
 body={'schema':'tukuyo.v1022_4.restore_namespace_swap/1','data_root':str(data),
       'transaction':tx,'backup_dir':'.tukuyo-v1014-before-'+uuid.uuid4().hex,'image_file_hashes':_image_hashes(image)}
 control=_sign_control(data,body);_write(_swap_marker(data),control)
 if inject:maybe_crash('restore:before_namespace_swap')
 return _resume_swap(data,control,inject)

@_locked
def recover_incomplete_restore(data):
 sidecar=_swap_marker(data)
 if sidecar.is_symlink():raise ValueError('RESTORE_SWAP_MARKER_SYMLINK')
 if sidecar.is_file():return _resume_swap(data,json.loads(sidecar.read_text()),inject=False)
 m=_restore_txn_path(data)
 if not m.is_file():return {'ok':True,'version':'v1014.2','recovered':False}
 try:tx=json.loads(m.read_text(encoding='utf-8'))
 except Exception as e:raise ValueError('RESTORE_TXN_MALFORMED:'+type(e).__name__)
 if tx.get('schema')!=RESTORE_TXN_SCHEMA:raise ValueError('RESTORE_TXN_SCHEMA')
 # Missing prepared bytes cannot be called a rollback: a prior commit may
 # already have written a prefix. Retain the marker and fail closed.
 return _commit_restore_transaction(data,tx,inject=False)

@_locked
def restore(data,checkpoint,trust_file=None,anchor_file=None,dry_run=False):
 recover_incomplete_restore(data);recover_checkpoint_commit(data)
 env,errs=_verify_env(checkpoint,trust_file);p=env.get('payload',{})
 if errs:return {'ok':False,'version':'v1014.2','phase':'checkpoint_verify','errors':errs}
 data=Path(data);parent=data.parent
 try:_sk,live_pub=_ensure_key(data)
 except Exception as e:return {'ok':False,'version':'v1014.2','phase':'recovery_trust','errors':[str(e)]}
 if live_pub!=env.get('public_key'):return {'ok':False,'version':'v1014.2','phase':'recovery_trust','errors':['RECOVERY_LIVE_SIGNER_MISMATCH']}
 td=tempfile.mkdtemp(prefix='.tukuyo-v1014-validate-',dir=str(parent));stage=Path(td)/'stage';stage.mkdir()
 try:
  for rel in p['files']:
   parts=Path(rel).parts
   if parts[-2:]!=('state','integration_state.json'):continue
   runtime=Path(*parts[:-2])
   for version in ('v977','v1013','v1014','v1017','v1018'):
    secret=data/runtime/version/'private'
    if secret.is_symlink():raise ValueError('RECOVERY_SECRET_SYMLINK')
    if secret.is_dir():shutil.copytree(secret,stage/runtime/version/'private',dirs_exist_ok=True,ignore=lambda _d,names:{n for n in names if _is_ephemeral_private_name(n)})
  live_recovery_pub=data/'v1014'/'recovery.pub'
  if live_recovery_pub.exists():
   q=stage/'v1014'/'recovery.pub';q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(live_recovery_pub,q)
  for rel,m in p['files'].items():
   if 'b64' in m:b=base64.b64decode(m['b64'])
   else:
    h=str(m.get('blob_sha256',''));bp=_blob_dir(data)/h
    if not bp.is_file():return {'ok':False,'version':'v1014.4','phase':'checkpoint_blob','errors':['CHECKPOINT_BLOB_MISSING:'+rel]}
    b=bp.read_bytes()
    if _sha(b)!=m.get('sha256') or len(b)!=m.get('size'):return {'ok':False,'version':'v1014.4','phase':'checkpoint_blob','errors':['CHECKPOINT_BLOB_HASH:'+rel]}
   q=stage/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
  try:ia=identity_audit(stage);wa=whole_audit(stage);ra=realtime_audit(stage,anchor_file=anchor_file,subaudits=True)
  except Exception as e:return {'ok':False,'version':'v1014.2','phase':'staged_audit','errors':['STAGED_AUDIT:'+type(e).__name__]}
  if not ia.get('ok') or not wa.get('ok') or not ra.get('ok'):
   return {'ok':False,'version':'v1014.2','phase':'staged_audit','errors':['STAGED_IDENTITY' if not ia.get('ok') else None,'STAGED_WHOLE' if not wa.get('ok') else None,*ra.get('errors',[])], 'realtime':ra}
  # Auditing a checkpoint must not silently rewrite any checkpointed byte.
  drift=[]
  for rel,m in p['files'].items():
   q=stage/rel
   if not q.is_file() or q.stat().st_size!=m.get('size') or _sha(q.read_bytes())!=m.get('sha256'):drift.append(rel)
  if drift:return {'ok':False,'version':'v1014.4','phase':'staged_determinism','errors':['STAGED_CHECKPOINT_DRIFT:'+x for x in drift[:20]]}
  if _live_identity(stage)!=p.get('identity'):return {'ok':False,'version':'v1014.2','phase':'identity','errors':['CHECKPOINT_IDENTITY_MISMATCH']}
  if dry_run:return {'ok':True,'version':'v1014.2','dry_run':True,'checkpoint_id':p['checkpoint_id'],'realtime':ra,'identity':p['identity']}
  txn_root=Path(tempfile.mkdtemp(prefix='.tukuyo-v1014-restore-',dir=str(parent)));txn_stage=txn_root/'stage';shutil.copytree(stage,txn_stage)
  tx={'schema':RESTORE_TXN_SCHEMA,'checkpoint_id':p['checkpoint_id'],'identity':p['identity'],'realtime_head_sha256':ra.get('head_sha256'),'anchor_checked':anchor_file is not None,'recovery_public_key':live_pub,'stage_dir':txn_root.name,'files':sorted(p['files']),
      'file_metadata':{rel:{'sha256':m['sha256'],'size':m['size']} for rel,m in p['files'].items()},'created_utc_ns':time.time_ns()}
  tx['authentication']={'public_key':live_pub,'signature':base64.b64encode(Ed25519PrivateKey.from_private_bytes(base64.b64decode(_sk)).sign(_canon(tx))).decode()}
  _write(_restore_txn_path(data),tx);maybe_crash('restore:after_txn_marker')
  r=_commit_restore_transaction(data,tx,inject=True)
  return {'ok':True,'version':'v1014.2','restored':True,'checkpoint_id':p['checkpoint_id'],'identity':p['identity'],'realtime':ra,'anchor_checked':anchor_file is not None,'atomic_commit':True,**{k:v for k,v in r.items() if k=='copied_files'}}
 finally:shutil.rmtree(td,ignore_errors=True)

def status(data):
 recover_checkpoint_commit(data);recover_incomplete_restore(data)
 d=_checkpoint_dir(data);items=[]
 if d.exists():
  for p in sorted(d.glob('rc-*.json')):
   a=audit_checkpoint(p);items.append({'file':p.name,'ok':a['ok'],'checkpoint_id':a.get('checkpoint_id'),'realtime':a.get('realtime')})
 return {'ok':all(x['ok'] for x in items),'version':'v1014.2','checkpoints':items,'count':len(items),'claim_boundary':{'72h_completed':False,'recovery_mechanism_proven_bounded':bool(items),'atomic_restore_commit':True,'write_in_progress_crash_tested':True,'literal_life_established':False,'consciousness_established':False}}
