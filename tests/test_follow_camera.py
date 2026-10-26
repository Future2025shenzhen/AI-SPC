from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  report=page.evaluate('''()=>{const failures=[];let maxPositionError=0,maxReleaseGap=0,maxBlendStep=0;const countBefore=manual.length,seedBefore=rngState;
    for(const settings of [[145,100,300,200,200],[180,110,300,200,200],[111,110,300,200,200]]){
      applySettings(settings);const shot=model(settings);shot.targetSnapshot=targetSnapshot();lastShot=shot;reviewing=true;const release=shot.armTime/(shot.armTime+shot.t);
      draw(release-1e-9,shot);const before={x:Number($('loaded-ball').getAttribute('cx')),y:Number($('loaded-ball').getAttribute('cy'))};draw(release,shot);
      const after={x:Number($('world-ball').getAttribute('cx')),y:Number($('world-ball').getAttribute('cy'))};maxReleaseGap=Math.max(maxReleaseGap,Math.hypot(after.x-before.x,after.y-before.y));
      let prior=0;for(let i=0;i<=120;i++){const time=shot.armTime+shot.t*i/120,progress=time/(shot.armTime+shot.t);draw(progress,shot);const point=samplePath(shot.path,time-shot.armTime),expectedX=diagramPose.pivot.x+shot.vals[2]*.62*Math.cos(shot.vals[1]*Math.PI/180)+point.x*620,expectedY=diagramPose.pivot.y+PHYSICS.pivotHeight*620-point.y*620;
       maxPositionError=Math.max(maxPositionError,Math.abs(Number($('world-ball').getAttribute('cx'))-expectedX),Math.abs(Number($('world-ball').getAttribute('cy'))-expectedY));const box=$('mechanism').viewBox.baseVal,x=Number($('world-ball').getAttribute('cx')),y=Number($('world-ball').getAttribute('cy'));if(x<box.x||x>box.x+box.width||y<box.y||y>box.y+box.height)failures.push({settings,i,x,y,box:[box.x,box.y,box.width,box.height]});const blend=Number($('mechanism').dataset.cameraBlend);if(blend<prior)failures.push('camera moved backwards');maxBlendStep=Math.max(maxBlendStep,blend-prior);prior=blend;
      }
      if($('world-impact').getAttribute('visibility')!=='visible')failures.push('missing first impact');
    }return {failures,maxPositionError,maxReleaseGap,maxBlendStep,noExtraRecords:manual.length===countBefore,noRandomConsumed:rngState===seedBefore}}''')
  assert not report['failures'],report
  assert report['maxPositionError']<1e-8 and report['maxReleaseGap']<1e-4,report
  assert report['maxBlendStep']<.1 and report['noExtraRecords'] and report['noRandomConsumed'],report
  original=page.evaluate('({v:vals(),n:manual.length,r:rngState,d:model(vals()).distance})')
  page.check('#xrayStructure');assert page.locator('#mechanism').evaluate('(el)=>el.classList.contains("structure-xray")')
  assert original==page.evaluate('({v:vals(),n:manual.length,r:rngState,d:model(vals()).distance})')
  page.uncheck('#followLaunch');assert page.evaluate('Number($("mechanism").dataset.cameraBlend)')==0
  page.click('#recockArm');assert page.evaluate('!reviewing');assert page.locator('#world-ball').get_attribute('visibility')=='hidden'
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  print(filename+': continuous release, all samples in camera, smooth camera, correct impact, xray/no data or RNG changes/mobile PASS',report)
  page.close()
 b.close()
