from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  assert page.evaluate('Math.abs(diagramPose.pivot.y+PHYSICS.pivotHeight*620-503)<1e-10 && diagramPose.pivot.y===445')
  assert page.locator('#world-stand').count()==0
  assert page.locator('#base-front').evaluate('(el)=>{const b=el.getBBox();return b.width===360 && b.height===18}')
  centers=page.evaluate('''()=>{const ids=['a-arm','b-limit','protractor'];const points=ids.map(id=>new DOMPoint(0,0).matrixTransform($(id).getScreenCTM()));return Math.max(...points.map(p=>Math.hypot(p.x-points[0].x,p.y-points[0].y)))}''');assert centers<1e-8
  assert page.locator('#protractor>path').first.evaluate('(el)=>{const length=el.getTotalLength();return Array.from({length:21},(_,i)=>{const p=el.getPointAtLength(i*length/20);return Math.abs(Math.hypot(p.x,p.y)-48)}).every(e=>e<.01)}')
  assert page.locator('.rig-actions #recockArm').count()==1 and page.locator('.rig-actions #launch').count()==1
  def point(x,y):return page.evaluate('xy=>new DOMPoint(...xy).matrixTransform($("mechanism").getScreenCTM()).toJSON()',[x,y])
  def click_base():
   page.locator('#mechanism').scroll_into_view_if_needed();pt=point(450,485);page.mouse.click(pt['x'],pt['y'])
  page.fill('#noise','2');page.select_option('#motionSpeed','2');page.click('#launch');page.wait_for_function('manual.length===1&&!busy')
  snapshot=page.evaluate('({settings:vals(),seed:rngState,n:manual.length})');click_base();page.wait_for_function('!reviewing && !busy');assert snapshot==page.evaluate('({settings:vals(),seed:rngState,n:manual.length})')
  assert page.locator('#loaded-ball').get_attribute('visibility')=='visible'
  page.click('#launch');page.wait_for_function('manual.length===2&&!busy');snapshot=page.evaluate('({settings:vals(),seed:rngState,n:manual.length})')
  page.locator('#mechanism').scroll_into_view_if_needed();pt=page.evaluate('''()=>{const a=displayedArmAngle*Math.PI/180;return new DOMPoint(diagramPose.pivot.x+Math.cos(a)*160*.62,diagramPose.pivot.y-Math.sin(a)*160*.62).matrixTransform($('mechanism').getScreenCTM()).toJSON()}''')
  page.mouse.click(pt['x'],pt['y']);page.wait_for_function('!reviewing');assert snapshot==page.evaluate('({settings:vals(),seed:rngState,n:manual.length})')
  # A small hand tremor still counts as a click, and must not race the drag-release handler.
  page.locator('#mechanism').scroll_into_view_if_needed();pt=page.evaluate('''()=>{const a=displayedArmAngle*Math.PI/180;return new DOMPoint(diagramPose.pivot.x+Math.cos(a)*160*.62,diagramPose.pivot.y-Math.sin(a)*160*.62).matrixTransform($('mechanism').getScreenCTM()).toJSON()}''')
  page.mouse.move(pt['x'],pt['y']);page.mouse.down();page.mouse.move(pt['x']-2,pt['y']-2);page.mouse.up();page.wait_for_timeout(150)
  assert snapshot==page.evaluate('({settings:vals(),seed:rngState,n:manual.length})')
  # The keyboard action on the chassis must also only rearm.
  page.locator('[data-recock-body]').focus();page.keyboard.press('Enter');page.wait_for_timeout(100);assert page.evaluate('manual.length')==2
  page.keyboard.press('Space');page.wait_for_timeout(100);assert page.evaluate('manual.length')==2
  page.click('#diagramC');page.wait_for_timeout(100);assert page.evaluate('manual.length')==2
  page.evaluate('applySettings([145,100,300,200,200])');page.uncheck('#autoRelease');page.locator('#mechanism').scroll_into_view_if_needed()
  def arm(angle):return page.evaluate('a=>new DOMPoint(diagramPose.pivot.x+Math.cos(a*Math.PI/180)*160*.62,diagramPose.pivot.y-Math.sin(a*Math.PI/180)*160*.62).matrixTransform($("mechanism").getScreenCTM()).toJSON()',angle)
  start=arm(145);end=arm(165);page.mouse.move(start['x'],start['y']);page.mouse.down();page.mouse.move(end['x'],end['y'],steps=15);page.mouse.up();page.wait_for_timeout(100);assert page.evaluate('manual.length')==2
  assert abs(page.evaluate('vals()[0]')-165)<=1
  page.check('#autoRelease');start=arm(165);end=arm(175);page.mouse.move(start['x'],start['y']);page.mouse.down();page.mouse.move(end['x'],end['y'],steps=15);page.mouse.up();page.wait_for_function('manual.length===3&&!busy');assert page.evaluate('manual.length')==3
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  print(filename+': smaller/taller base, lower axis, concentric protractor, top-left buttons, click/keyboard only rearm, no RNG/record changes, drag and mobile PASS');page.close()
 b.close()
