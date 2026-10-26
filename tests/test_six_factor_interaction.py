from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1500,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/'DOE_Catapult_Reference_Layout.html').read_text())
 # Release continuity and exact physical trajectory despite capped close camera.
 report=page.evaluate('''()=>{applySettings([120,100,420,200,200,0]);const s=model(vals());reviewing=true;s.targetSnapshot=targetSnapshot();const boundary=s.armTime/(s.armTime+s.t);draw(boundary,s);const release=motionPose(boundary,s),expected=diagramPose.pivot.y-620*(s.path[0].y-PHYSICS.pivotHeight);let error=Math.abs(Number($('world-ball').getAttribute('cy'))-expected);for(let i=0;i<=20;i++){const t=s.armTime+s.t*i/20;draw(t/(s.armTime+s.t),s);const pt=samplePath(s.path,s.t*i/20);error=Math.max(error,Math.abs(Number($('world-ball').getAttribute('cy')) - (503-620*pt.y)))}reviewing=false;draw(1,null);return error}''');assert report<1e-5,report
 page.locator('#a-arm').scroll_into_view_if_needed()
 points=page.evaluate('''()=>{const o=diagramPose.pivot,m=$('mechanism').getScreenCTM();return [120,155].map(deg=>{const t=deg*Math.PI/180,p=new DOMPoint(o.x+150*Math.cos(t),o.y-150*Math.sin(t)).matrixTransform(m);return {x:p.x,y:p.y}})}''')
 page.mouse.move(**points[0]);page.mouse.down();assert page.locator('[data-factor="B"] .badge-face').evaluate('(e)=>getComputedStyle(e).opacity==="1"');page.mouse.move(**points[1],steps=12);page.mouse.up();page.wait_for_function('manual.length===1&&!busy',timeout=30000)
 old=page.evaluate('({n:manual.length,r:rngState})');page.click('#recockArm');assert page.evaluate('({n:manual.length,r:rngState})')==old
 # Tall post scale/physics alignment and sufficient extreme-arm left margin.
 assert page.evaluate('Math.abs(mechanismGeometry([120,100,420,200,200,0]).pin.y-(-15/620+.244))<1e-12')
 assert page.evaluate('PHYSICS.postLength-.244')<.020001
 page.evaluate('updateFactor(factors[0],180)');assert page.locator('#a-arm').evaluate('(e)=>e.getBoundingClientRect().left>document.querySelector("#mechanism").getBoundingClientRect().left')
 assert not errors,errors
 print('Actual drag/release, rearm, conditional badge, physical trajectory continuity, post calibration and left margin PASS');b.close()
