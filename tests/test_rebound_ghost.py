from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for filename in ['DOE_Catapult_Competition.html','DOE_Catapult_Reference_Layout.html']:
  page=b.new_page(viewport={'width':1500,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/filename).read_text())
  result=page.evaluate('''()=>{applySettings([160,110,420,200,200,1]);const s=model(vals()),distance=s.distance,seed=rngState;s.targetSnapshot=targetSnapshot();reviewing=true;draw(1,s,.1);const ghost=$('world-impact-ghost'),ball=$('world-ball'),releaseX=365+s.vals[2]*.62*Math.cos(s.vals[1]*Math.PI/180),expected=releaseX+distance*6.2,p=reboundPose(s,0),last=s.path.at(-1);const out={ghostOpacity:Number(ghost.getAttribute('opacity')),ghostError:Math.abs(Number(ghost.getAttribute('cx'))-expected),moving:Number(ball.getAttribute('cy'))<503&&Number(ball.getAttribute('cx'))>expected,hiddenLine:$('world-trajectory').getAttribute('visibility')==='hidden',energy:p.vx*p.vx+p.vy*p.vy<=last.vx*last.vx+last.vy*last.vy,distanceSame:s.distance===distance,randomSame:rngState===seed};draw(1,s);out.finalBallHidden=$('world-ball').getAttribute('visibility')==='hidden';out.finalGhostVisible=ghost.getAttribute('visibility')==='visible';return out}''')
  assert result['ghostOpacity']==.8 and result['ghostError']<1e-8 and all(result[k] for k in ['moving','hiddenLine','energy','distanceSame','randomSame','finalBallHidden','finalGhostVisible']),result
  page.evaluate('''window.bounceFrames=0;window.originalDraw=draw;draw=function(progress,shot,bounceTime){originalDraw(progress,shot,bounceTime);if(progress===1&&bounceTime>=0&&bounceTime<1.2&&$('world-impact-ghost').getAttribute('visibility')==='visible')bounceFrames++};reviewing=false''')
  page.select_option('#motionSpeed','2');page.click('#launch');page.wait_for_function('manual.length===1&&!busy',timeout=30000);assert page.evaluate('bounceFrames>3&&manual.length===1&&Number.isFinite(manual[0].y)')
  if filename=='DOE_Catapult_Reference_Layout.html':
   page.evaluate('draw(1,lastShot,.12)');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-bounce.png'));page.evaluate('draw(1,lastShot)');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-flight.png'));page.click('#resetFactors');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-reference.png'));page.locator('.scene-wrap').screenshot(path=str(ROOT/'preview.png'));page.check('#xrayStructure');page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-structure.png'))
  assert not errors,errors;print(filename,': no blue trace, physically dissipative rebound animation, 20% transparent first-impact sphere, one measurement and replay/RNG preserved PASS');page.close()
 b.close()
