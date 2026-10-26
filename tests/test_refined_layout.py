from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name in ['DOE_Catapult_Reference_Layout.html','DOE_Catapult_Competition.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/name).read_text())
  assert not page.locator('.rig-hud').is_visible()
  assert page.evaluate('PHYSICS.postLength===.264')
  assert page.locator('#mechanism .badge-face').evaluate_all('(els)=>els.every(e=>getComputedStyle(e).opacity==="0")')
  page.locator('#rangeD').scroll_into_view_if_needed();r=page.locator('#rangeD').bounding_box();page.mouse.move(r['x']+r['width']*.8,r['y']+r['height']/2);page.mouse.down()
  assert page.locator('#mechanism [data-factor="D"] .badge-face').evaluate('(e)=>getComputedStyle(e).opacity==="1"')
  page.mouse.up();assert page.locator('#mechanism .badge-face').evaluate_all('(els)=>els.every(e=>getComputedStyle(e).opacity==="0")')
  page.click('[data-select-target="2"]');assert page.locator('[role="radio"][aria-checked="true"]').count()==1
  assert '远目标' in page.locator('#landingBoard').text_content() and '近目标' not in page.locator('#landingBoard').text_content()
  assert page.locator('#verificationRows tr').count()==1
  assert page.locator('.target-card').evaluate('(e)=>!!(e.compareDocumentPosition(document.querySelector(".verification-summary"))&Node.DOCUMENT_POSITION_FOLLOWING)')
  page.click('#resetFactors');page.select_option('#motionSpeed','2');page.click('#launch');page.wait_for_function('manual.length===1&&!busy')
  assert page.evaluate('manual[0].targetSnapshot.index===2')
  assert page.evaluate('$("mechanism").viewBox.baseVal.width<=715.001')
  assert page.locator('.history .scroll').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  if name.startswith('DOE_Catapult_Reference'):
   page.locator('.scene-wrap').screenshot(path=str(ROOT/'preview-flight.png'));page.click('#recockArm');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-reference.png'));page.locator('.scene-wrap').screenshot(path=str(ROOT/'preview.png'));page.check('#xrayStructure');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-structure.png'))
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert page.locator('.history .scroll').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
  assert not errors,errors
  print(name+': conditional badges, single target, wide table, capped zoom, launch and mobile PASS');page.close()
 b.close()
