from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1600,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  assert page.evaluate('vals()[0]===120 && vals()[2]===420 && PHYSICS.armLength===.46 && PHYSICS.postLength===.22')
  assert page.evaluate('diagramPose.pivot.y===470 && Math.abs(PHYSICS.pivotHeight*620+470-503)<1e-10')
  assert page.locator('#mechanism').text_content().find('DOE LAB')==-1
  assert page.locator('#cup-leader,#bungee-leader,#arm-a-leader').count()==0
  assert page.locator('[data-factor] .handle-ring').evaluate_all('(es)=>es.length===5 && es.every(e=>e.getAttribute("r")==="20")')
  assert page.locator('[data-factor] .badge-face').evaluate_all('(es)=>es.every(e=>getComputedStyle(e).animationName==="badgeHover")')
  assert page.locator('#loaded-ball').get_attribute('r')=='16'
  assert 'scale(1.45)' in page.locator('#cup-assembly').get_attribute('transform')
  assert page.locator('#front-guard').evaluate('(e)=>Math.abs(e.getBBox().width-301*.6)<1e-3')
  assert page.locator('#rear-guard').evaluate('(e)=>Math.abs(e.getBBox().width-323*.6)<1e-3')
  concentric=page.evaluate('''()=>{const O=diagramPose.pivot;return [['front-guard',60],['rear-guard',67]].every(([id,r])=>{const path=$(id);for(let i=0;i<=20;i++){const pt=path.getPointAtLength(13+Math.PI*r*.5*i/20);if(Math.abs(Math.hypot(pt.x-O.x,pt.y-O.y)-r)>.03)return false}return true})}''');assert concentric
  page.evaluate('applySettings([145,100,300,200,200])');page.click('#resetFactors');assert page.evaluate('vals()[0]===120 && vals()[2]===420')
  page.click('#launch');page.wait_for_function('manual.length===1&&!busy');assert page.evaluate('manual[0].vals[0]===120 && manual[0].vals[2]===420')
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
  print(filename+': default120, longer arms, larger cup/ball, equal transparent floating badges/no leaders, 40% shorter concentric guards, lower axis, default shot and mobile PASS');page.close()
 b.close()
