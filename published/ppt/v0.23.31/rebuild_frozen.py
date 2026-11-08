"""Rebuild the selected ZIP from exact source bytes and original ZIP metadata."""
from pathlib import Path
import hashlib,json,sys,zipfile
spec_path, source, out = map(Path,sys.argv[1:]);spec=json.loads(spec_path.read_text());out.mkdir(parents=True,exist_ok=True);target=out/spec['archive']['name']
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=spec['compression_level']) as bundle:
 bundle.comment=bytes.fromhex(spec['comment_hex'])
 for row in spec['entries']:
  raw=(source/row['filename']).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  info=zipfile.ZipInfo(row['filename'],tuple(row['date_time']))
  for key in ['compress_type','create_system','create_version','extract_version','flag_bits','external_attr','internal_attr','volume']:
   setattr(info,key,row[key])
  info.extra=bytes.fromhex(row['extra_hex']);info.comment=bytes.fromhex(row['comment_hex']);bundle.writestr(info,raw,compresslevel=spec['compression_level'])
assert target.stat().st_size==spec['archive']['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest()==spec['archive']['sha256'],'Rebuilt ZIP differs from frozen original'
print(json.dumps({'status':'exact-frozen-zip-rebuilt','bytes':target.stat().st_size,'sha256':spec['archive']['sha256']}))
