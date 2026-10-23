#!/usr/bin/env python3
"""Render a native Art prototype before visual locking; never infer quality."""
import argparse,hashlib,json,pathlib,subprocess,datetime,re,os

def ref(p):
    p=pathlib.Path(p).resolve()
    return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)

def font_environment(directory, font_file, font_family, fontconfig=None):
    """Bind an explicit font to this render process before any PDF conversion.

    This does not install fonts, choose a route, or prove rendered glyph quality.
    A config file is optional only when the inherited environment resolves the
    exact requested file. Always persist the resolution, including rejection.
    """
    directory=pathlib.Path(directory)
    expected=pathlib.Path(font_file).resolve(strict=True)
    if not isinstance(font_family,str) or not font_family.strip():
        raise ValueError('Explicit font family required')
    env=os.environ.copy()
    if fontconfig is not None:
        config=pathlib.Path(fontconfig).resolve(strict=True)
        env['FONTCONFIG_FILE']=str(config)
    else:
        config=pathlib.Path(env['FONTCONFIG_FILE']).resolve(strict=True) if env.get('FONTCONFIG_FILE') else None
    # Isolated writable caches/config; preserve system PATH and runtime bindings.
    env.update(XDG_CACHE_HOME=str(directory/'cache'),XDG_CONFIG_HOME=str(directory/'config'),GSETTINGS_BACKEND='memory')
    for name in ('cache','config'):(directory/name).mkdir(exist_ok=False)
    r=subprocess.run(['fc-match','--format=%{file}',font_family],capture_output=True,text=True,env=env)
    actual=pathlib.Path(r.stdout.strip()) if r.returncode==0 and r.stdout.strip() else None
    observed=ref(actual) if actual and actual.is_file() else None
    record={'requested_family':font_family,'expected_font':ref(expected),
            'fontconfig':ref(config) if config else None,'resolved_font':observed,
            'command_returncode':r.returncode,'stderr':r.stderr,
            'environment':{k:env.get(k) for k in ('FONTCONFIG_FILE','XDG_CACHE_HOME','XDG_CONFIG_HOME','GSETTINGS_BACKEND')},
            'file_identity_matches':bool(observed and observed['sha256']==ref(expected)['sha256']),
            'quality_status':'unverified','scope':'Process font resolution only; PDF fonts and page glyphs remain due.'}
    (directory/'font-environment.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    if not record['file_identity_matches']:
        raise ValueError('Requested font file does not resolve in rendering environment; PDF conversion not started')
    return env,record


def _run_observed(cmd, env, directory, *, stage, log_name=None):
    """Persist actual process evidence before propagating failure; never retry.

    This helper records only the known render command and its result. It does
    not serialize the inherited environment or choose an execution boundary.
    """
    directory = pathlib.Path(directory)
    command = list(map(str, cmd))
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = None
    failure = None
    try:
        result = subprocess.run(command, capture_output=True, text=True, env=env)
    except OSError as exc:
        failure = exc
    finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = dict(stage=stage, command=command, started_at=started,
               finished_at=finished,
               returncode=result.returncode if result is not None else None,
               stdout=result.stdout if result is not None else None,
               stderr=result.stderr if result is not None else None)
    if failure is not None:
        row['launch_error'] = dict(type=type(failure).__name__, message=str(failure))
    observations = directory / 'subprocess-observations.json'
    rows = json.loads(observations.read_text()) if observations.exists() else []
    rows.append(row)
    observations.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    combined = result.stdout + result.stderr if result is not None else str(failure)
    if log_name is not None:
        (directory / log_name).write_text(combined)
    if failure is not None:
        raise failure
    if result.returncode:
        raise RuntimeError(combined)
    return combined

def render(pptx,directory,slide_ids=None,*,font_file=None,font_family=None,fontconfig=None):
    pptx=pathlib.Path(pptx).resolve();directory=pathlib.Path(directory).resolve()
    directory.mkdir(parents=True,exist_ok=False)
    if font_file is None or font_family is None:
        raise ValueError('Native preview requires explicit font_file and font_family; bind the task font before rendering')
    env,font_record=font_environment(directory,font_file,font_family,fontconfig)
    _run_observed(['libreoffice','-env:UserInstallation=file://'+str(directory/'lo-profile'),'--headless','--convert-to','pdf','--outdir',directory,pptx], env, directory, stage='libreoffice', log_name='libreoffice.log')
    pdf=directory/pptx.with_suffix('.pdf').name
    _run_observed(['pdffonts',pdf], env, directory, stage='pdffonts', log_name='pdffonts.txt')
    _run_observed(['pdftoppm','-png','-scale-to','1600',pdf,directory/'slide'], env, directory, stage='pdftoppm')
    files=sorted(directory.glob('slide-*.png'))
    if not files: raise ValueError('native prototype produced no images')
    ids=slide_ids if slide_ids is not None else [f'S{i:02}' for i in range(1,len(files)+1)]
    if len(ids)!=len(files) or len(set(ids))!=len(ids) or any(not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',s) for s in ids):
        raise ValueError('Art slide identities must safely cover rendered physical pages once')
    for sid,p in zip(ids,files):p.rename(directory/(sid+'.png'))
    manifest=dict(contract='io.clayz.presentation.native-art-preview/1.0',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),pptx=ref(pptx),pdf=ref(pdf),backend='LibreOffice + Poppler',font_environment=ref(directory/'font-environment.json'),process_observations=ref(directory/'subprocess-observations.json'),slides=[dict(slide_id=sid,**ref(directory/(sid+'.png'))) for sid in ids],limitations=['Actual native prototype; not final Output evidence.','Rendering alone does not establish visual or content quality.','PowerPoint and WPS are not observed.'])
    (directory/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pptx',type=pathlib.Path);p.add_argument('--directory',type=pathlib.Path,required=True);p.add_argument('--art-content',type=pathlib.Path);p.add_argument('--font-file',type=pathlib.Path,required=True);p.add_argument('--font-family',required=True);p.add_argument('--fontconfig',type=pathlib.Path);a=p.parse_args()
    content=json.loads(a.art_content.read_text()) if a.art_content else None
    ids=[s['slide_id'] for s in content['slides']] if content else None
    m=render(a.pptx,a.directory,ids,font_file=a.font_file,font_family=a.font_family,fontconfig=a.fontconfig);print(json.dumps(dict(pages=len(m['slides']),manifest=str(a.directory/'manifest.json'))))
