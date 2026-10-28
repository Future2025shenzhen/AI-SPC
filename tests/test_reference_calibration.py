from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse,unquote
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1500,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/'DOE_Catapult_Competition.html').read_text());page.locator('#mechanism').scroll_into_view_if_needed();page.evaluate("$('autoRelease').checked=false")
 assert page.locator('[data-arm-mark]').evaluate_all('(es)=>es.map(e=>Number(e.dataset.armMark))')==list(range(100,301,10))
 assert page.locator('[data-pin-mark]').evaluate_all('(es)=>es.map(e=>Number(e.dataset.pinMark))')==list(range(100,201,10))
 report=page.evaluate('''()=>{const p=diagramPose.pivot,m=ballMountPose(vals(),100),axis={x:420*.62*Math.cos(100*Math.PI/180),y:-420*.62*Math.sin(100*Math.PI/180)},ball={x:Number($('loaded-ball').getAttribute('cx'))-p.x,y:Number($('loaded-ball').getAttribute('cy'))-p.y};return {ballRight:ball.x>axis.x+15,default:vals(),label:$('a-arm').querySelector('[data-arm-mark="200"] path').getAttribute('d'),hook:$('bungee-hardware').getAttribute('transform'),limit:$('b-limit').getAttribute('transform')}}''')
 assert report['ballRight'] and report['default']==[100,100,420,200,200,0]
 assert 'rotate(-100)' in report['limit']
 # Real pointer drags follow the two engraved rail calibrations, not raw pixels.
 def drag(id,start_value,end_value):
  page.evaluate('([id,v])=>updateFactor(factors.find(f=>f.id===id),v)',[id,start_value])
  points=page.evaluate('''([id,d])=>{const a=100*Math.PI/180,M=$('mechanism').getScreenCTM(),node=$(id==='D'?'loaded-ball':id==='E'?'pin-hardware':'bungee-hardware');let x,y;if(id==='D'){x=Number(node.getAttribute('cx'))+8;y=Number(node.getAttribute('cy'))}else{const t=node.transform.baseVal.consolidate().matrix;x=t.e;y=t.f}const scale=id==='F'?1.15:id==='E'?1.35:1,dx=id==='E'?0:d*.62*scale*Math.cos(a),dy=id==='E'?-d*.62*scale:-d*.62*scale*Math.sin(a),pt=(x,y)=>{const p=new DOMPoint(x,y).matrixTransform(M);return {x:p.x,y:p.y}};return [pt(x,y),pt(x+dx,y+dy)]}''',[id,end_value-start_value])
  page.mouse.move(**points[0]);page.mouse.down();page.mouse.move(**points[1],steps=8);page.mouse.up();assert page.evaluate('id=>factors.find(f=>f.id===id).value',id)==end_value,(id,page.evaluate('vals()'))
 drag('D',400,420);drag('F',180,200);drag('E',180,200)
 # Cup appearance and projectile use one position at release for both balls and all limits.
 error=page.evaluate('''()=>{let error=0;for(const A of [0,1])for(const C of [90,100,120])for(const D of [300,420]){const v=[160,C,D,200,180,A],s=model(v);if(!s.valid)throw Error(s.reason);s.targetSnapshot=targetSnapshot();reviewing=true;const t=s.armTime/(s.armTime+s.t);draw(t,s);const x=Number($('loaded-ball').getAttribute('cx')),y=Number($('loaded-ball').getAttribute('cy')),xx=Number($('world-ball').getAttribute('cx')),yy=Number($('world-ball').getAttribute('cy'));error=Math.max(error,Math.abs(x-xx),Math.abs(y-yy))}reviewing=false;applySettings([100,100,420,200,200,0]);return error}''')
 assert error<1e-7,error
 page.locator('.rig-stage').screenshot(path=str(ROOT/'preview-rig-compact.png'))
 rect=page.evaluate('''()=>{const M=$('mechanism').getScreenCTM(),a=new DOMPoint(275,145).matrixTransform(M),b=new DOMPoint(530,510).matrixTransform(M);return {x:a.x,y:a.y,width:b.x-a.x,height:b.y-a.y}}''');page.screenshot(path=str(ROOT/'preview-reference-match.png'),clip=rect)
 assert not errors,errors
 # Preserve old data for analysis while preventing cross-version new sampling.
 context=b.new_context();analysis=context.new_page()
 def local_route(route):
  path=ROOT/unquote(urlparse(route.request.url).path).lstrip('/')
  if path.is_file():route.fulfill(path=str(path))
  else:route.abort()
 context.route('**/*',local_route);analysis.goto('http://catapult.local/DOE_Catapult_Analysis.html');analysis.wait_for_function('catReady&&!catBusy&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
 versions=analysis.evaluate("""async()=>{const current=catSnapshot(),ys=state.runs.map(r=>r.y),old=structuredClone(current);old.physics='rigid-rk4-v1';old.rows.forEach(r=>r.physics='rigid-rk4-v1');catImportExperiment(old);const errors=[];for(const f of [catCollect,catAppend,catValidate])try{await f()}catch(e){errors.push(e.message)}const preserved=state.runs.every((r,i)=>r.y===ys[i]);catImportExperiment(current);return {errors,preserved,restored:catDataPhysics===catPhysics,version:current.physics}}""")
 assert len(versions['errors'])==3 and versions['preserved'] and versions['restored'] and versions['version']=='rigid-rk4-reference-v2',versions
 print('Reference native engraving, right-side cup, 100-degree default stop, real cup/pin/bungee rail drags, exact ball-to-projectile continuity across both balls and firing limits PASS');b.close()
