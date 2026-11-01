from pathlib import Path
from urllib.parse import urlparse,unquote
import json,base64,re
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'src/uploaded-catapult-base.html'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=b.new_context(viewport={'width':1500,'height':1100},accept_downloads=True)
 def route(r):
  f=ROOT/unquote(urlparse(r.request.url).path).lstrip('/')
  if f.is_file():r.fulfill(path=str(f))
  else:r.abort()
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://catapult.local/'+ '投射器实验_优化版.html');page.wait_for_function('typeof vacuumFlight==="function"')
 # Keep the attachment's response calibration and noise law byte-for-byte.
 before=INPUT.read_text();after=(ROOT/'投射器实验_优化版.html').read_text()
 a='function responseMean(';z='function samplePath('
 assert before[before.index(a):before.index(z)]==after[after.index(a):after.index(z)]
 for width in [1500,800,390]:
  page.set_viewport_size({'width':width,'height':1000})
  result=page.evaluate('''()=>{const saved=rngState;applySettings([160,110,280,150,150,0]);const shot=model(vals(),0,'quadratic');shot.targetSnapshot=targetSnapshot();lastShot=shot;reviewing=true;const radii=[];let trajectoryError=0;for(const fraction of [.75,.99,.99999,1]){const t=shot.armTime+shot.t*fraction;draw(t/(shot.armTime+shot.t),shot,fraction===1?.04:Infinity);const moving=$('world-ball').getBoundingClientRect(),ghost=$('world-impact-ghost').getBoundingClientRect();radii.push({w:moving.width,g:ghost.width});if(fraction===1&&Math.abs(moving.width-ghost.width)>.01||Math.abs(Number($('world-ball').getAttribute('r'))-Number($('world-impact-ghost').getAttribute('r')))>1e-9)throw Error(JSON.stringify({moving:moving.width,ghost:ghost.width,r:$('world-ball').getAttribute('r'),g:$('world-impact-ghost').getAttribute('r')}))}for(const point of shot.path){const expected=shot.h+shot.vy/shot.vx*point.x-PHYSICS.g*point.x*point.x/(2*shot.vx*shot.vx);trajectoryError=Math.max(trajectoryError,Math.abs(expected-point.y),Math.abs(point.vx-shot.vx),Math.abs(point.vy-(shot.vy-PHYSICS.g*point.t)))}const result={radii,trajectoryError,rngUnchanged:saved===rngState,defaultFree:activeTarget===-1};reviewing=false;draw(1,null);return result}''')
  assert max(abs(r['w']-result['radii'][0]['w']) for r in result['radii'])<.01,result
  assert result['trajectoryError']<1e-9 and result['rngUnchanged'] and result['defaultFree'],result
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
 page.set_viewport_size({'width':1500,'height':1100})
 # Actual independent observations from the uploaded response model.
 page.evaluate('''async()=>{for(const A of [0,1])for(const B of [140,170])for(const E of [100,180])for(let rep=0;rep<2;rep++)await shootOnce({settings:[B,110,280,E,150,A],animate:false});}''')
 assert page.evaluate('manual.length')==16
 original=page.evaluate('manual.map(r=>({y:r.y,settings:r.vals,id:r.observationId}))')
 with page.expect_popup() as popup:page.click('#openLinkedDOE')
 analysis=popup.value;analysis.on('pageerror',lambda e:errors.append(str(e)));analysis.wait_for_function('window.uploadedWorkbench?.getReady()',timeout=30000)
 assert analysis.evaluate('state.runs.length')==16
 assert analysis.evaluate('state.runs.map(r=>r.y)')==[r['y'] for r in original]
 fit=analysis.evaluate('({X:state.fit.X,y:state.fit.y,beta:state.fit.beta,sigmas:state.runs.map(r=>r.catapultSigma)})')
 expected=np.linalg.lstsq(np.array(fit['X']),np.array(fit['y']),rcond=None)[0]
 assert np.max(np.abs(expected-np.array(fit['beta'])))<1e-7
 analysis.locator('#labDataPanel').evaluate('(e)=>e.open=true')
 entry=analysis.evaluate('uploadedWorkbench.save("附件16次实测")')
 before=page.evaluate('({n:manual.length,seed:rngState})')
 analysis.evaluate('uploadedWorkbench.build("screen")')
 assert analysis.evaluate('e=>uploadedWorkbench.reuse(e)',entry)==0
 analysis.evaluate('p=>uploadedWorkbench.importPacket(p)',entry['packet'])
 analysis.evaluate("document.getElementById('designType').value='full';document.getElementById('replicates').value=2;generateDesign()")
 wrong_order=json.loads(json.dumps(entry));wrong_order['packet']['responseOrder']='linear'
 for row in wrong_order['packet']['rows']:row['responseOrder']='linear'
 assert analysis.evaluate('e=>uploadedWorkbench.reuse(e)',wrong_order)==0
 validation_only=json.loads(json.dumps(entry))
 for row in validation_only['packet']['rows']:row['phase']='验证'
 assert analysis.evaluate('e=>uploadedWorkbench.reuse(e)',validation_only)==0
 reused=analysis.evaluate('e=>uploadedWorkbench.reuse(e)',entry)
 assert reused==16,analysis.evaluate('e=>({reused:document.getElementById("labMessage").textContent,config:uploadedWorkbench.getConfig(),source:e.packet.rows[0],sourceOrder:e.packet.responseOrder,cv:document.getElementById("catCV").value,physics:e.packet.physics,target:uploadedWorkbench.snapshot().rows[0]})',entry)
 assert page.evaluate('({n:manual.length,seed:rngState})')==before
 analysis.evaluate('uploadedWorkbench.fit("main")')
 assert analysis.evaluate('state.fit.p')==4
 assert analysis.evaluate('()=>{try{uploadedWorkbench.fit("quadratic");return false}catch{return true}}')
 with analysis.expect_download() as download:analysis.click('#labExportCSV')
 csv=download.value.path().read_text(encoding='utf-8-sig');decoded=analysis.evaluate('s=>uploadedWorkbench.decodeCSV(s)',csv)
 assert all(r['responseOrder']=='quadratic' for r in decoded['rows'])
 assert sorted(r['y'] for r in decoded['rows'])==sorted(r['y'] for r in original)
 # Eleven observations can be reused into another CCC plan; only six new shots.
 analysis.evaluate('uploadedWorkbench.build("curve")');analysis.evaluate('uploadedWorkbench.collect()')
 curve=analysis.evaluate('uploadedWorkbench.save("附件11次曲率")');ys={r['observationId']:r['y'] for r in curve['packet']['rows']}
 analysis.evaluate("document.getElementById('designType').value='ccc';generateDesign()")
 assert analysis.evaluate('state.runs.length')==17
 n=page.evaluate('manual.length');assert analysis.evaluate('e=>uploadedWorkbench.reuse(e)',curve)==11
 analysis.evaluate('uploadedWorkbench.collect()');assert page.evaluate('manual.length')==n+6
 for r in analysis.evaluate('state.runs'):
  if r['observationId'] in ys:assert r['y']==ys[r['observationId']]
 analysis.evaluate('uploadedWorkbench.fit("quadratic")')
 training=analysis.evaluate('state.runs.map(r=>r.y)');n=page.evaluate('manual.length')
 result=analysis.evaluate('uploadedWorkbench.validate(3)');assert len(result['ys'])==3 and page.evaluate('manual.length')==n+3
 assert analysis.evaluate('state.runs.map(r=>r.y)')==training
 # The originating single file receives the latest training snapshot, not validation data.
 exported=page.evaluate('catExportExperiment()');assert [r['y'] for r in exported['rows']]==training
 analysis.screenshot(path=str(ROOT/'preview-uploaded-workbench.png'),full_page=False)
 analysis.close()
 page.evaluate("()=>{applySettings([160,110,280,150,150,0]);lastShot=model(vals(),0);lastShot.targetSnapshot=targetSnapshot();reviewing=true;draw(1,lastShot,.05)}")
 page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-uploaded-landing.png'))
 assert not errors,errors
 offline=b.new_context(offline=True);offline.route('**/*',route);local=offline.new_page();local.on('pageerror',lambda e:errors.append(str(e)))
 local.goto('http://catapult.local/投射器实验_优化版.html')
 with local.expect_popup() as popup:local.click('#openExistingDOE')
 local_analysis=popup.value;local_analysis.on('pageerror',lambda e:errors.append(str(e)));local_analysis.wait_for_function('window.uploadedWorkbench?.getReady()',timeout=30000)
 local_analysis.evaluate('uploadedWorkbench.collect()')
 assert local_analysis.evaluate('state.runs.length===16&&state.runs.every(r=>Number.isFinite(r.y))')
 assert local.evaluate('manual.length')==16
 assert not errors,errors
 offline.close()
 print('Offline single-file collection; Attachment kernel preserved; equal ball/ghost size before+after+rebound at3 widths; analytic parabola; 16 raw observations; original OLS vs NumPy; CSV context; unique reuse; 11→17 only6 shots; independent validation/training separation; latest snapshot roundtrip PASS')
 b.close()
