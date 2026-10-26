from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  assert page.evaluate('!FRAME_FOLLOWS_B && PHYSICS.postRakeDegrees===0 && PHYSICS.postLength===.22 && factors[2].max===420 && vals()[2]===420')
  invariants=page.evaluate('''()=>{let error=0;for(const B of [90,100,110,120])for(const D of [0,100,200]){applySettings([145,B,420,D,200]);const g=mechanismGeometry(vals());error=Math.max(error,Math.abs(g.foot.x-.20),Math.abs(g.foot.y+15/620),Math.abs(g.pin.x-g.foot.x),Math.abs(g.pin.y-g.foot.y-D/1000));const shell=$('d-post-shell'),parent=shell.parentElement,m=parent.getScreenCTM(),bottom=new DOMPoint(PHYSICS.supportFootX*620,0).matrixTransform(m),base=new DOMPoint(489,485).matrixTransform($('mechanism').getScreenCTM());error=Math.max(error,Math.hypot(bottom.x-base.x,bottom.y-base.y));const length=shell.getTotalLength(),pt=shell.getPointAtLength(length-1);error=Math.max(error,Math.abs(pt.y));}return error}''');assert invariants<1e-4,invariants
  assert page.locator('#base-front').evaluate('(e)=>{const b=e.getBBox();return b.width===237 && b.height===18}')
  assert page.evaluate('Math.abs(PHYSICS.postLength-.2-.02)<1e-12')
  line=page.locator('#world-ground-line').get_attribute('d').split();assert float(line[1])==365
  # Expanded teaching targets remain available after moving the spring anchor inward.
  assert page.evaluate('model([185,120,420,200,200]).distance>=700')
  page.click('#resetFactors');page.locator('#loaded-ball').scroll_into_view_if_needed();rect=page.locator('#loaded-ball').bounding_box();assert rect['width']>0
  page.select_option('#motionSpeed','2');page.click('#launch');page.wait_for_function('manual.length===1&&!busy');assert page.evaluate('manual[0].vals[2]===420')
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  print(filename+': vertical fixed D, rectangular foot flush with base, 20mm cap, inward post, shorter base, trimmed ground line, C420, target700 reachable, launch/mobile PASS');page.close()
 b.close()
