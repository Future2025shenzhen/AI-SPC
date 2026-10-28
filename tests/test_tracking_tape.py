from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name in ['DOE_Catapult_Reference_Layout.html','DOE_Catapult_Competition.html']:
  page=b.new_page(viewport={'width':1500,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/name).read_text())
  assert page.evaluate('vals()[0]===vals()[1]&&vals()[2]===420&&!model(vals()).valid')
  assert page.locator('#launch').is_disabled()
  assert page.evaluate('factors[0].max===180')
  assert page.locator('#limit-ghost').count()==0
  assert page.locator('#ballType option').all_text_contents()==['乒乓球','高尔夫球']
  panel=page.locator('.factor-panel').bounding_box();rig=page.locator('.mechanism-view').bounding_box();assert panel['y']>=rig['y']+rig['height']-1
  assert page.locator('#factors').evaluate('(e)=>getComputedStyle(e).gridTemplateColumns.split(" ").length')==6
  for kind in [0,1]:
   result=page.evaluate('''kind=>{applySettings([175,115,420,200,200,kind]);const shot=model(vals());shot.targetSnapshot=targetSnapshot();reviewing=true;let error=0,outside=0,pan=0;for(let i=0;i<=30;i++){const t=shot.armTime+shot.t*i/30;draw(t/(shot.armTime+shot.t),shot);const ball=samplePath(shot.path,shot.t*i/30),box=$('mechanism').viewBox.baseVal,x=Number($('world-ball').getAttribute('cx')),y=Number($('world-ball').getAttribute('cy'));error=Math.max(error,Math.abs(y-(503-620*ball.y)));if(x<box.x||x>box.x+box.width||y<box.y||y>box.y+box.height)outside++;pan=Math.max(pan,box.x)}const releaseX=365+ballMountPose(shot.vals,shot.vals[1]).x*620,needle=$('tape-impact-pointer').getAttribute('d').split(' '),tick=$('world-ruler').querySelector('[data-tape-cm]'),tickCm=Number(tick.dataset.tapeCm),tickX=Number(tick.getAttribute('d').split(' ')[1]);return {error,outside,pan,distance:shot.distance,needleError:Math.abs(Number(needle[1])-releaseX-shot.distance*6.2),tickError:Math.abs(tickX-releaseX-tickCm*6.2),texture:$('world-ball').getAttribute('fill')}}''',kind)
   assert result['error']<1e-5 and result['outside']==0 and result['pan']>=65,result
   assert result['needleError']<1e-8 and result['tickError']<1e-8,result
   assert page.locator('#world-target-band').get_attribute('height')=='0'
   assert page.locator('#tape-target-range').get_attribute('height')=='51'
   assert page.locator('#world-impact').get_attribute('visibility')=='hidden'
   assert page.locator('#golfBall rect').get_attribute('fill')=='#fafcfd'
   assert result['texture']==('url(#golfBall)' if kind else 'url(#pingBall)'),result
  page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-flight.png'));page.click('#resetFactors');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-reference.png'));page.locator('.scene-wrap').screenshot(path=str(ROOT/'preview.png'));page.check('#xrayStructure');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-structure.png'))
  page.click('[data-tab="doe"]');page.click('#localRSM');page.click('#generate');page.evaluate('while(plan.some(r=>r.y===null))nextRun();renderAnalysis()');page.click('[data-tab="analysis"]');assert '失拟' not in page.locator('#analysis').text_content();assert page.evaluate('fitModel.k===42')
  page.set_viewport_size({'width':390,'height':844});page.click('[data-tab="lab"]');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert not errors,errors
  print(name, 'horizontal controls, textures, physical follow camera, calibrated tape and landing pointer, analysis/mobile PASS');page.close()
 b.close()
