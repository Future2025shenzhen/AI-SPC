from pathlib import Path
from urllib.parse import urlparse,unquote
from statistics import median
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1550,'height':1100})
 def route(r):
  f=ROOT/unquote(urlparse(r.request.url).path).lstrip('/')
  if f.is_file():r.fulfill(path=str(f))
  else:r.abort()
 ctx.route('**/*',route);errors=[];rig=ctx.new_page();rig.on('pageerror',lambda e:errors.append(str(e)));rig.goto('http://catapult.local/DOE_Catapult_Competition.html')
 rig.evaluate('''()=>{applySettings([160,110,420,200,200,0]);$('noise').value=0;window.reboundSamples=[];const render=draw;draw=function(progress,shot,bounce){render(progress,shot,bounce);if(progress===1&&Number.isFinite(bounce)&&bounce>0&&bounce<1.2)reboundSamples.push({now:performance.now(),t:bounce})}}''');rig.select_option('#motionSpeed','2')
 rates=[]
 for slow in [True,False]:
  rig.set_checked('#slowLanding',slow);rig.evaluate('reboundSamples=[]');rig.click('#launch');rig.wait_for_function('!busy&&manual.length>0',timeout=30000)
  samples=rig.evaluate('reboundSamples');vel=[]
  for a,c in zip(samples,samples[1:]):
   if .2<a['t']<c['t']<1 and c['now']-a['now']>1:vel.append((c['t']-a['t'])/((c['now']-a['now'])/1000))
  assert len(vel)>3;rates.append(median(vel))
 assert .18<rates[0]/rates[1]<.35,rates
 assert rig.evaluate('manual.length===2&&manual[0].y===manual[1].y')
 assert rig.locator('#impact-tape-print').get_attribute('opacity')=='.8'
 page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://catapult.local/DOE_Catapult_Analysis.html');page.wait_for_function('catReady&&!catBusy&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
 before=page.evaluate('JSON.stringify(state.runs.map(r=>r.y))');page.click('#optimizeBtn');page.wait_for_selector('#profile_0');canvas=page.locator('#profile_0');canvas.scroll_into_view_if_needed()
 for viewport in [{'width':1550,'height':1100},{'width':800,'height':1000}]:
  page.set_viewport_size(viewport);page.evaluate('refreshOptimizerLive()');canvas.scroll_into_view_if_needed()
  points=canvas.evaluate('''e=>{const rect=e.getBoundingClientRect(),g=optimizerPanelGeometry(e.clientWidth,state.factors.length,1),screen=x=>rect.left+x/e.clientWidth*rect.width;return {low:screen(g.plotL),high:screen(g.plotR),y:rect.top+80,padding:g.padding,leftGap:g.plotL-g.boxL,rightGap:g.boxR-g.plotR}}''')
  assert points['leftGap']>0 and abs(points['leftGap']-points['rightGap'])<1e-8
  for key,expected in [('low',-1),('high',1)]:
   assert abs(canvas.evaluate('(e,x)=>optimizerFactorAt(e,x).code',points[key])-expected)<1e-8
   page.mouse.move(points[key]+(-1 if key=='low' else 1),points['y']);page.mouse.down();page.mouse.up();assert abs(page.evaluate('optimizerLive.z[1]')-expected)<1e-7
  assert page.evaluate('JSON.stringify(state.runs.map(r=>r.y))')==before
 page.set_viewport_size({'width':1550,'height':1100});page.wait_for_timeout(250);page.evaluate('refreshOptimizerLive()');page.locator('#profile_0').screenshot(path=str(ROOT/'preview-optimizer-padding.png'))
 assert not errors,errors
 print('Rebound enabled/disabled measured rate ratio ≈0.25; same first-impact Y; optimizer symmetric endpoint padding and real pointer mapping at both endpoints across viewport sizes; no training changes PASS');b.close()
