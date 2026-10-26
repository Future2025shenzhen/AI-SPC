from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  assert page.evaluate('Math.abs(diagramPose.pivot.y+PHYSICS.pivotHeight*620-503)<1e-10')
  assert page.locator('#world-stand').count()==0
  def point(x,y):return page.evaluate('xy=>new DOMPoint(...xy).matrixTransform($("mechanism").getScreenCTM()).toJSON()',[x,y])
  def click_base():
   page.locator('#mechanism').scroll_into_view_if_needed();pt=point(450,480);page.mouse.click(pt['x'],pt['y'])
  page.fill('#noise','0');page.select_option('#motionSpeed','2');page.click('#launch');page.wait_for_function('manual.length===1&&!busy')
  settings=page.evaluate('vals()');click_base();page.wait_for_function('manual.length===2&&!busy');assert page.evaluate('manual[1].vals')==settings
  # A click on the displayed arm must restore the configured pullback before refiring.
  page.locator('#mechanism').scroll_into_view_if_needed()
  pt=page.evaluate('''()=>{const a=displayedArmAngle*Math.PI/180;return new DOMPoint(diagramPose.pivot.x+Math.cos(a)*160*.62,diagramPose.pivot.y-Math.sin(a)*160*.62).matrixTransform($('mechanism').getScreenCTM()).toJSON()}''')
  page.mouse.click(pt['x'],pt['y']);page.wait_for_function('manual.length===3&&!busy');assert page.evaluate('manual[2].vals')==settings
  page.click('#diagramC');page.wait_for_timeout(100);assert page.evaluate('manual.length')==3
  page.evaluate('applySettings([145,100,300,200,200])');page.uncheck('#autoRelease');page.locator('#mechanism').scroll_into_view_if_needed()
  def arm(angle):
   import math
   return point(365+math.cos(math.radians(angle))*160*.62,425-math.sin(math.radians(angle))*160*.62)
  start=arm(145);end=arm(165);page.mouse.move(start['x'],start['y']);page.mouse.down();page.mouse.move(end['x'],end['y'],steps=15);page.mouse.up();page.wait_for_timeout(100);assert page.evaluate('manual.length')==3
  assert abs(page.evaluate('vals()[0]')-165)<=1
  # A real pull-and-release must create exactly one shot, rather than a drag shot plus a click shot.
  page.check('#autoRelease');start=arm(165);end=arm(175);page.mouse.move(start['x'],start['y']);page.mouse.down();page.mouse.move(end['x'],end['y'],steps=15);page.mouse.up();page.wait_for_function('manual.length===4&&!busy');page.wait_for_timeout(100);assert page.evaluate('manual.length')==4
  assert page.evaluate('manual.every(r=>r.vals[0]>r.vals[1])')
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  print(filename+': grounded geometry, body click, arm click, unchanged settings, no control/drag misfire, one shot per release, mobile PASS');page.close()
 b.close()
