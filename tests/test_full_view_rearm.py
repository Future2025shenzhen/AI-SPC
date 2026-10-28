from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Reference_Layout.html','DOE_Catapult_Competition.html']:
  page=b.new_page(viewport={'width':1500,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  for viewport in [{'width':1500,'height':1100},{'width':390,'height':844}]:
   page.set_viewport_size(viewport)
   report=page.evaluate('''()=>{let maxShift=0,outside=0,tapeError=0;for(const kind of [0,1]){applySettings([175,115,420,200,200,kind]);const seed=rngState,n=manual.length;lastShot=model(vals());lastShot.targetSnapshot=targetSnapshot();reviewing=true;const s=lastShot;draw(0,s);const base=new DOMPoint(365,470).matrixTransform($('mechanism').getScreenCTM()).y;for(let i=0;i<=40;i++){const progress=i/40;draw(progress,s);const view=$('mechanism').viewBox.baseVal,pivot=new DOMPoint(365,470).matrixTransform($('mechanism').getScreenCTM());maxShift=Math.max(maxShift,Math.abs(pivot.y-base));const pose=motionPose(progress,s);if(pose.time>=s.armTime){for(const pt of s.path){const x=365+ballMountPose(s.vals,s.vals[1]).x*620+pt.x*620,y=503-pt.y*620;if(x<view.x||x>view.x+view.width||y<view.y||y>view.y+view.height)outside++}for(const pt of [[273,503],[510,503],[365,470]])if(pt[0]<view.x||pt[0]>view.x+view.width||pt[1]<view.y||pt[1]>view.y+view.height)outside++}}const band=$('tape-target-range'),rx=365+ballMountPose(s.vals,s.vals[1]).x*620;tapeError=Math.max(tapeError,Math.abs(Number(band.getAttribute('x'))-rx-(targets[activeTarget]-15)*6.2),Math.abs(Number(band.getAttribute('width'))-30*6.2));$('recockArm').click();if(vals()[0]!==vals()[1]||vals()[2]!==420||manual.length!==n||rngState!==seed)throw Error('rearm changed records/noise or did not reset angle');if(!$('launch').disabled)throw Error('unarmed launch enabled')}return {maxShift,outside,tapeError}}''')
   assert report['maxShift']<1e-3 and report['outside']==0 and report['tapeError']<1e-8,report
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert not errors,errors
  print(filename,'full physical trajectory and launcher in frame, pivot screen Y fixed, colored tape calibrated, every rearm resets angles/no RNG/records, desktop/mobile PASS');page.close()
 b.close()
