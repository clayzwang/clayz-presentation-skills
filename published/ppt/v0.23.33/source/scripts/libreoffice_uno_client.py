#!/usr/bin/env python3
"""Attach to an explicitly owned UNO listener; export one PPTX or shut it down.
No automatic Office startup, CLI conversion, export retry or global configuration.
"""
from pathlib import Path
import argparse,json,os,sys,time,hashlib,datetime,traceback

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def identity(pid):
 p=Path('/proc')/str(pid);raw=(p/'stat').read_text();rest=raw.rsplit(')',1)[1].split();argv=[x.decode(errors='replace')for x in(p/'cmdline').read_bytes().split(b'\0')if x];return {'pid':pid,'start_ticks':rest[19],'state':rest[0],'argv':argv}
def assert_engine(a):
 x=identity(a.expected_pid)
 if x['start_ticks']!=a.expected_start_ticks or x['state']=='Z' or not x['argv']or Path(x['argv'][0]).name!='soffice.bin' or '-env:UserInstallation='+Path(a.expected_profile).resolve().as_uri()not in x['argv']:raise RuntimeError('Expected owned engine identity/profile does not match; no UNO operation performed')
 return x
p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['ready','export','shutdown']);p.add_argument('--pipe',required=True);p.add_argument('--expected-pid',type=int);p.add_argument('--expected-start-ticks');p.add_argument('--expected-profile',required=True);p.add_argument('--source');p.add_argument('--output');p.add_argument('--receipt',required=True);p.add_argument('--connect-timeout',type=float,default=8.0);a=p.parse_args()
receipt=Path(a.receipt).resolve()
if receipt.exists():raise SystemExit('Refusing to overwrite receipt')
v={'operation':a.operation,'started_at':now(),'argv':sys.argv,'script':ref(__file__),'usage':None,'cost':None,'connection_attempts':[],'desktop_terminate_called':False,'document_close_called':False};doc=None;close_attempted=False;ok=False
try:
 if not a.pipe.replace('_','').isalnum():raise ValueError('Use a simple unique pipe identifier')
 if a.operation!='ready':
  if a.expected_pid is None or not a.expected_start_ticks:raise ValueError('Export/shutdown require the ready-bound PID and start ticks')
  v['engine_before']=assert_engine(a)
 import uno,pyuno
 v['bridge']={'uno':ref(uno.__file__),'pyuno':ref(pyuno.__file__)}
 local=uno.getComponentContext();resolver=local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local);deadline=time.monotonic()+a.connect_timeout;ctx=None
 while ctx is None:
  try:
   ctx=resolver.resolve('uno:pipe,name='+a.pipe+';urp;StarOffice.ComponentContext');v['connection_attempts'].append({'at':now(),'status':'connected'})
  except Exception as e:
   v['connection_attempts'].append({'at':now(),'status':'not-ready','error_type':type(e).__name__,'error':str(e)})
   if time.monotonic()>=deadline:raise
   time.sleep(.1)
 desktop=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
 if a.operation=='ready':
  v['service_ready_at']=now();v['desktop_service_available']=desktop is not None;ok=v['desktop_service_available']
 elif a.operation=='shutdown':
  assert_engine(a);v['desktop_terminate_called']=True;v['desktop_terminate_result']=bool(desktop.terminate());ok=v['desktop_terminate_result']
 else:
  v['engine_after_connect_before_load']=assert_engine(a)
  if not a.source or not a.output:raise ValueError('export requires --source and --output')
  source=Path(a.source).resolve(strict=True);target=Path(a.output).resolve()
  if source.suffix.lower()!='.pptx' or target.suffix.lower()!='.pdf':raise ValueError('This helper exports PPTX to PDF only')
  if target.exists()or Path(a.output).is_symlink():raise FileExistsError('Refusing to overwrite PDF')
  target.parent.mkdir(parents=True,exist_ok=True);v['source_before']=ref(source)
  def prop(name,value):x=uno.createUnoStruct('com.sun.star.beans.PropertyValue');x.Name=name;x.Value=value;return x
  load_props=(prop('Hidden',True),prop('ReadOnly',True),prop('UpdateDocMode',uno.getConstantByName('com.sun.star.document.UpdateDocMode.NO_UPDATE')),prop('MacroExecutionMode',uno.getConstantByName('com.sun.star.document.MacroExecMode.NEVER_EXECUTE')))
  v['load_started_at']=now();doc=desktop.loadComponentFromURL(source.as_uri(),'_blank',0,load_props)
  if doc is None:raise RuntimeError('UNO load returned no document')
  v['load_completed_at']=now();v['document_location_before']=doc.getLocation();v['document_read_only']=bool(doc.isReadonly());v['store_started_at']=now()
  doc.storeToURL(target.as_uri(),(prop('FilterName','impress_pdf_Export'),prop('Overwrite',False)))
  v['store_completed_at']=now();v['document_location_after']=doc.getLocation();close_attempted=True;v['document_close_called']=True;doc.close(True);doc=None;v['close_completed_at']=now()
  raw=target.read_bytes()
  if not raw.startswith(b'%PDF-')or b'%%EOF'not in raw[-1024:]:raise RuntimeError('Export lacks complete PDF markers')
  v['pdf']=ref(target);v['source_after']=ref(source);v['engine_after']=assert_engine(a)
  if v['source_before']!=v['source_after']:raise RuntimeError('Source bytes changed')
  if v['document_location_before']!=v['document_location_after']:raise RuntimeError('storeToURL unexpectedly changed document source location')
  ok=True
 v['status']='completed'if ok else'failed'
except BaseException as e:
 v.update(status='failed',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
finally:
 if doc is not None and not close_attempted:
  try:v['document_close_called']=True;doc.close(True);v['cleanup_close_status']='closed'
  except BaseException as e:v['cleanup_close_status']=type(e).__name__+': '+str(e)
 v['finished_at']=now();receipt.parent.mkdir(parents=True,exist_ok=True)
 with receipt.open('x')as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'receipt':str(receipt),'operation':a.operation,'status':v['status'],'error':v.get('error'),'pdf':v.get('pdf'),'desktop_terminate_called':v['desktop_terminate_called']}));raise SystemExit(0 if ok else 1)
