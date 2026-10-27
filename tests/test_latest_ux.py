from pathlib import Path
from urllib.parse import urlparse,unquote
from statistics import median
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1550,'height':1100})
 def route(r):
  f=ROOT/unquote(urlparse(r.request.url).path).lstrip('/')
  if f.is_file():r.fulfill(path=str(f))
  else:r.abort()
 ctx.route('**/*',route);errors=[];page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://catapult.local/DOE_Catapult_Analysis.html');page.wait_for_function('catReady&&!catBusy&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
 engine=page.frames[1];assert engine.locator('.flight-view').count()==0 and engine.locator('#scene').count()==0
 assert page.locator('#catProgress').get_attribute('max')=='16' and page.locator('#catProgress').get_attribute('value')=='16'
 assert page.locator('#catConnection').text_content()=='已连接'
 geometry=page.evaluate('''()=>{let parallel=0,outside=0;for(const w of [240,600,1200])for(const yaw of [-3,-1,0,1,3])for(const pitch of [-.95,-.4,.4,.95])for(const zoom of [.65,1,1.1]){const q=surfaceProjector(w,392,{yaw,pitch,zoom}).project;for(const x of [-1,1])for(const y of [-1,1])for(const z of [-1,1]){const pt=q(x,y,z);if(!Number.isFinite(pt.x)||!Number.isFinite(pt.y)||pt.x<0||pt.x>w||pt.y<0||pt.y>392)outside++}const a=q(-1,-1,-1),bb=q(1,-1,-1),c=q(-1,1,-1),d=q(1,1,-1);parallel=Math.max(parallel,Math.abs((bb.x-a.x)-(d.x-c.x)),Math.abs((bb.y-a.y)-(d.y-c.y)))}return {parallel,outside}}''')
 assert geometry['outside']==0 and geometry['parallel']<1e-8,geometry
 page.evaluate('drawCube()');assert page.locator('#cubeCanvas').get_attribute('data-soft-faces')=='3'
 page.locator('#cubeCanvas').screenshot(path=str(ROOT/'preview-cube-gradient.png'));page.locator('#surfaceCanvas').screenshot(path=str(ROOT/'preview-stable-surface.png'))
 page.select_option('#catPreset','curve');page.click('#catBuild');page.click('#catCollect');page.wait_for_function('!catBusy&&state.runs.every(r=>Number.isFinite(r.y))');page.click('#catAppend');page.wait_for_function('!catBusy&&state.runs.length===17&&state.runs.every(r=>Number.isFinite(r.y))')
 before=page.evaluate('({ys:state.runs.map(r=>r.y),blocks:state.runs.map(r=>r.block),df:state.fit.df})');assert page.locator('#includeBlockModel').is_checked()
 page.uncheck('#includeBlockModel');page.wait_for_function('state.fit&&!state.fit.cols.some(c=>c.kind==="block")');assert page.evaluate('state.fit.df')==before['df']+1
 assert page.evaluate('state.runs.map(r=>r.y)')==before['ys'] and page.evaluate('state.runs.map(r=>r.block)')==before['blocks']
 reduced=page.evaluate('({X:state.fit.X,y:state.fit.y,beta:state.fit.beta})');expected=np.linalg.lstsq(np.array(reduced['X']),np.array(reduced['y']),rcond=None)[0];assert np.max(np.abs(expected-np.array(reduced['beta'])))<1e-7
 # Both standalone launchers preserve model choice, dataset and selected physical settings.
 with page.expect_popup() as pop:page.click('#catOpenRig')
 rig=pop.value;rig.on('pageerror',lambda e:errors.append(str(e)));rig.wait_for_function('typeof linkedExperiment!=="undefined"&&linkedExperiment?.rows.length===17');assert rig.evaluate('linkedExperiment.includeBlocks') is False
 assert rig.locator('#openLinkedDOE').is_visible()
 with rig.expect_popup() as pop2:rig.click('#openLinkedDOE')
 analysis=pop2.value;analysis.on('pageerror',lambda e:errors.append(str(e)));analysis.wait_for_function('typeof catReady!=="undefined"&&catReady&&state.runs.length===17');assert analysis.evaluate('state.includeBlocks') is False
 assert analysis.evaluate('state.runs.map(r=>r.y)')==before['ys']
 page.check('#includeBlockModel');page.wait_for_function('state.fit&&state.fit.cols.some(c=>c.kind==="block")');page.click('#catOpenRig');rig.wait_for_function('linkedExperiment.includeBlocks===true');rig.click('#openLinkedDOE');analysis.wait_for_function('state.includeBlocks===true&&state.runs.length===17');assert analysis.evaluate('state.runs.map(r=>r.y)')==before['ys'];analysis.close();rig.close()
 # A real animation reaches the landing window at quarter rate, then rebounds once.
 standalone=ctx.new_page();standalone.on('pageerror',lambda e:errors.append(str(e)));standalone.goto('http://catapult.local/DOE_Catapult_Competition.html');standalone.evaluate('''()=>{applySettings([160,110,420,200,200,0]);$('noise').value=0;window.rateSamples=[];const render=draw;draw=function(progress,shot,bounce){render(progress,shot,bounce);if(shot&&progress<1){const t=motionPose(progress,shot).time,q=(t-shot.armTime)/shot.t;rateSamples.push({now:performance.now(),t,q,rate:Number($('mechanism').dataset.landingRate)})}}}''');standalone.select_option('#motionSpeed','2');standalone.click('#launch');standalone.wait_for_function('manual.length===1&&!busy',timeout=30000)
 samples=standalone.evaluate('rateSamples');normal=[];slow=[]
 for a,c in zip(samples,samples[1:]):
  if c['now']-a['now']<1:continue
  rate=(c['t']-a['t'])/((c['now']-a['now'])/1000)
  if .2<a['q']<c['q']<.6:normal.append(rate)
  if .82<a['q']<c['q']<.96:slow.append(rate)
 assert len(slow)>5 and .15<median(slow)/median(normal)<.4,(len(slow),median(slow),median(normal))
 assert standalone.locator('#world-impact-ghost').get_attribute('opacity')=='.8' and standalone.locator('#impact-tape-print').get_attribute('opacity')=='.8'
 old=standalone.locator('#impactTape').inner_html();standalone.click('#recockArm');assert standalone.locator('#impactTape').inner_html()==old
 standalone.locator('.rig-stage').screenshot(path=str(ROOT/'preview-rig-compact.png'));standalone.close()
 assert not errors,errors
 print('Removed panorama; real quarter-speed landing; 20% transparency; block term toggles without Y changes and matches SciPy; rigid orthographic cube at 180 orientations; gradient faces; roundtrip standalone navigation/model preservation PASS');b.close()
