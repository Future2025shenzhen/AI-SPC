from pathlib import Path
from playwright.sync_api import sync_playwright
import math, shutil
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  result=page.evaluate('''()=>{
    const shot=model(vals());shot.targetSnapshot=targetSnapshot();const boundary=shot.armTime/(shot.armTime+shot.t);
    draw(0,shot);const loaded=$('loaded-ball'),identity=$('a-arm');
    const samples=[0,.2,.5,.8,1].map(t=>{const progress=t*boundary;draw(progress,shot);const angle=Number($('mechanism').dataset.angleDeg)*Math.PI/180;const expected={x:diagramPose.pivot.x+shot.vals[2]*.62*Math.cos(angle),y:diagramPose.pivot.y-shot.vals[2]*.62*Math.sin(angle)};return Math.hypot(Number(loaded.getAttribute('cx'))-expected.x,Number(loaded.getAttribute('cy'))-expected.y)});
    const geometry=mechanismGeometry(shot.vals),tension=shot.effectiveSpringK*Math.max(0,Math.hypot(shot.vals[4]/1000*Math.cos(shot.vals[1]*Math.PI/180)-geometry.pin.x,shot.vals[4]/1000*Math.sin(shot.vals[1]*Math.PI/180)-geometry.pin.y)+geometry.returnLength-PHYSICS.springRest);
    const displayedTension=Number($('bandTension').textContent.split(' ')[0]);
    const release=motionPose(boundary,shot),ballVisible=loaded.getAttribute('visibility');
    const continuity=Math.abs(PHYSICS.pivotHeight+shot.vals[2]/1000*Math.sin(release.angle*Math.PI/180)-shot.path[0].y);
    const begin=performance.now();for(let i=0;i<120;i++)draw(i/120,shot);const drawMs=performance.now()-begin;
    const sameNode=identity===$('a-arm');reviewing=true;draw(1,shot);
    const finalAngle=Number($('mechanism').dataset.angleDeg);reviewing=false;
    return {maxBallError:Math.max(...samples),continuity,ballVisible,sameNode,drawMs,finalAngle,tensionError:Math.abs(tension-displayedTension),B:shot.vals[1],tr:lastArenaTransform};
  }''')
  assert result['maxBallError']<1e-8 and result['continuity']<1e-10,result
  assert result['ballVisible']=='hidden' and result['sameNode'],result
  assert abs(result['finalAngle']-result['B'])<1e-8 and result['tensionError']<.006,result
  assert result['drawMs']<2500,result
  # The arena stores a SINGLE physical scale used for both x and y.
  assert result['tr']['scale']>0
  page.click('#recockArm');page.select_option('#motionSpeed','2');page.click('#launch');page.wait_for_function('manual.length===1 && !busy')
  assert page.evaluate('recentShots.length===1 && reviewing')
  original=page.evaluate('({n:manual.length,r:rngState,v:vals()})')
  page.click('#recockArm');assert page.evaluate('!reviewing');assert original==page.evaluate('({n:manual.length,r:rngState,v:vals()})')
  # Directly grabbing the post-shot yellow arm must use the displayed B angle.
  page.evaluate('reviewing=true;draw(1,lastShot)');page.locator('#mechanism').scroll_into_view_if_needed()
  point=page.evaluate('''()=>{const angle=displayedArmAngle*Math.PI/180,pt=new DOMPoint(diagramPose.pivot.x+Math.cos(angle)*160*.62,diagramPose.pivot.y-Math.sin(angle)*160*.62);return pt.matrixTransform($('mechanism').getScreenCTM()).toJSON()}''')
  page.mouse.move(point['x'],point['y']);page.mouse.down();assert page.evaluate('Math.abs(factors[0].value-Math.max(100,factors[1].value))<=1');page.mouse.up();page.wait_for_function('manual.length===2 && !busy')
  # Changed target must immediately show the chosen goal rather than an old snapshot.
  page.click('[data-select-target="2"]');assert page.evaluate('!reviewing && activeTarget===2')
  page.evaluate('applySettings([145,100,300,200,200])');page.select_option('#playbackMode','physical');page.click('#launch');page.wait_for_function('!busy && manual.length===3');assert page.evaluate('recentShots.length===3')
  page.check('#compareTrajectories');assert not errors,errors
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  print(filename, 'PASS',result)
  page.close()
 b.close()
