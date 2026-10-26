from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  assert page.evaluate('factors.map(f=>[f.min,f.max])')==[[100,185],[90,120],[200,440],[0,200],[100,200]]
  assert page.locator('#loaded-ball').get_attribute('data-drag-factor')=='C'
  # Check actual drawn controls at the entire corner set; expanded ranges must not clip or overlap.
  failures=page.evaluate('''()=>{const failures=[];for(let mask=0;mask<32;mask++){applySettings(factors.map((f,i)=>mask>>i&1?f.max:f.min));const box=$('mechanism').getBoundingClientRect(),rings=[...$('mechanism').querySelectorAll('[data-factor] .handle-ring')].map(e=>({id:e.parentElement.dataset.factor,r:e.getBoundingClientRect()}));for(const {id,r} of rings)if(r.left<box.left||r.right>box.right||r.top<box.top||r.bottom>box.bottom)failures.push({mask,id,reason:'clipped'});for(let i=0;i<rings.length;i++)for(let j=i+1;j<rings.length;j++){const a=rings[i],b=rings[j];if(Math.hypot((a.r.left+a.r.right-b.r.left-b.r.right)/2,(a.r.top+a.r.bottom-b.r.top-b.r.bottom)/2)<(a.r.width+b.r.width)/2)failures.push({mask,ids:a.id+b.id,reason:'overlap'})}const g=mechanismGeometry(vals());if(g.returnLength<0||Math.abs(g.returnLength-Math.abs(g.pin.y-g.tie.y))>1e-12)failures.push('negative return length')}return failures}''');assert not failures,failures
  page.evaluate('applySettings([145,100,300,200,200])');page.uncheck('#autoRelease');page.locator('#loaded-ball').scroll_into_view_if_needed()
  rect=page.locator('#loaded-ball').bounding_box();x=rect['x']+rect['width']/2;y=rect['y']+rect['height']/2
  delta=page.evaluate('''()=>{const a=-factors[0].value*Math.PI/180,svg=$('mechanism'),p=new DOMPoint(0,0).matrixTransform(svg.getScreenCTM()),q=new DOMPoint(Math.cos(a)*140*.62,Math.sin(a)*140*.62).matrixTransform(svg.getScreenCTM());return {x:q.x-p.x,y:q.y-p.y}}''')
  page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+delta['x'],y+delta['y'],steps=18);page.mouse.up();assert abs(page.evaluate('vals()[2]')-440)<=1
  assert page.evaluate('manual.length')==0
  # Highest cup is 20 mm below the 460 mm arm tip.
  assert page.evaluate('Math.abs(PHYSICS.armLength-factors[2].max/1000-.02)<1e-12')
  page.evaluate('applySettings([145,120,380,0,200])');assert page.evaluate('vals()[1]===120 && vals()[3]===0');assert page.evaluate('Number.isFinite(mechanismGeometry(vals()).returnLength)')
  page.evaluate('applySettings([145,100,300,200,200])');page.check('#autoRelease');page.select_option('#motionSpeed','2');page.locator('#mechanism').scroll_into_view_if_needed()
  def arm(a):return page.evaluate('a=>new DOMPoint(diagramPose.pivot.x+Math.cos(a*Math.PI/180)*160*.62,diagramPose.pivot.y-Math.sin(a*Math.PI/180)*160*.62).matrixTransform($("mechanism").getScreenCTM()).toJSON()',a)
  start=arm(145);end=arm(165);page.mouse.move(start['x'],start['y']);page.mouse.down();page.mouse.move(end['x'],end['y'],steps=18);page.mouse.up();page.wait_for_function('manual.length===1&&!busy');assert abs(page.evaluate('manual[0].vals[0]')-165)<=1
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  print(filename+': expanded ranges, 32 corner control bounds, nonnegative cord length, actual ball drag to 440, arm release fires once, mobile PASS');page.close()
 b.close()
