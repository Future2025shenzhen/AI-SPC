from pathlib import Path
from playwright.sync_api import sync_playwright
from scipy.stats import f as fd
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name in ['DOE_Catapult_Reference_Layout.html','DOE_Catapult_Competition.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());page.set_content((ROOT/name).read_text())
  assert not page.locator('.rig-tools').is_visible()
  assert page.locator('#front-guard').evaluate('(e)=>e.getBBox().width>=180')
  assert page.evaluate('factors.length===6&&factors[5].id==="A"')
  for F,d1,d2 in [(4.2,1,20),(8,2,68),(.02,44,68),(100,2,10)]:
   actual=page.evaluate('v=>fTail(...v)',[F,d1,d2]);assert abs(actual-fd.sf(F,d1,d2))<1e-10
  page.click('[data-tab="doe"]')
  for t,count,k in [('full',134,22),('half',70,22),('ccf',154,42),('iccc',154,42)]:
   page.select_option('#designType',t);page.click('#generate');assert page.evaluate('plan.length')==count
   assert page.evaluate('plan.every(r=>[0,1].includes(r.vals[5])&&r.vals.every((v,i)=>v>=factors[i].min&&v<=factors[i].max))')
   if t=='half':assert page.evaluate('plan.filter(r=>r.kind==="corner").every(r=>Math.abs(r.codes.reduce((a,b)=>a*b,1)-1)<1e-10)')
   page.evaluate('while(plan.some(r=>r.y===null))nextRun();renderAnalysis()');assert page.evaluate('plan.every(r=>Number.isFinite(r.y))&&fitModel.k')==k
   assert page.evaluate('!fitModel.spec.some(t=>t.powers.filter(v=>v===5).length>1)')
   if t=='iccc':assert page.evaluate('Math.abs(plan.find(r=>r.kind==="corner").codes[0])')<.448
  page.click('#localRSM');page.click('#generate');page.evaluate('while(plan.some(r=>r.y===null))nextRun();renderAnalysis()');assert page.evaluate('fitModel.k')==42
  print(name,'local fit:',page.evaluate('({rmse:fitModel.rmse,pLof:fitModel.inference.pLof})'))
  page.click('[data-tab="lab"]');page.select_option('#ballType','1');page.fill('#valueB','145');page.locator('#valueB').press('Tab');page.select_option('#motionSpeed','2');page.click('#launch');page.wait_for_function('manual.length===1&&!busy',timeout=30000)
  assert page.evaluate('manual[0].vals[5]===1');assert '高尔夫球' in page.locator('#manualRows').text_content()
  page.evaluate('draw(1,lastShot)');assert page.evaluate('$("mechanism").viewBox.baseVal.x<=65.001')
  with page.expect_download() as dl:page.click('#exportManual')
  path=dl.value.path();import csv
  rows=list(csv.reader(path.read_text(encoding='utf-8-sig').splitlines()));assert len(rows[0])==len(rows[1])
  if name.startswith('DOE_Catapult_Reference'):
   page.locator('.scene-wrap').screenshot(path=str(ROOT/'preview-flight.png'));page.click('#recockArm');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-reference.png'));page.locator('.scene-wrap').screenshot(path=str(ROOT/'preview.png'));page.check('#xrayStructure');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-structure.png'))
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  print(name+': six factors, real ball types, all four designs, stats vs SciPy, models, CSV, slow launch and mobile PASS');page.close()
 b.close()
