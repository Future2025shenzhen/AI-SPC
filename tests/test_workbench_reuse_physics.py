from pathlib import Path
from urllib.parse import urlparse,unquote,quote
import json
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=b.new_context(viewport={'width':1550,'height':1100},accept_downloads=True)
 def serve(route):
  path=ROOT/unquote(urlparse(route.request.url).path).lstrip('/')
  if path.is_file():route.fulfill(path=str(path))
  else:route.abort()
 context.route('**/*',serve);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://catapult.local/DOE_Catapult_Analysis.html');page.wait_for_function('catReady&&!catBusy&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
 engine=page.frames[1]
 physics=engine.evaluate('''()=>{const seed=rngState,n=manual.length;const shot=model([160,110,400,200,200,0]);shot.targetSnapshot=targetSnapshot();reviewing=true;const ideal=vacuumFlight(shot);let error=0;for(let i=0;i<=100;i++){const pt=ideal.at(ideal.time*i/100);error=Math.max(error,Math.abs(pt.y-(shot.h+shot.vy/shot.vx*pt.x-PHYSICS.g*pt.x*pt.x/(2*shot.vx*shot.vx))))}$('showVacuum').checked=true;draw((shot.armTime+shot.t*.6)/(shot.armTime+shot.t),shot);let dots=0,dotError=0;const release=365+ballMountPose(shot.vals,shot.vals[1]).x*620;for(const el of document.querySelectorAll('[data-physical-dot]')){dots++;const pt=samplePath(shot.path,Number(el.dataset.physicalDot));dotError=Math.max(dotError,Math.abs(Number(el.getAttribute('cx'))-release-620*pt.x),Math.abs(Number(el.getAttribute('cy'))-503+620*pt.y))}const view=$('mechanism').viewBox.baseVal,idealEnd=release+ideal.distance*620;const report={error,dots,dotError,endInView:idealEnd<=view.x+view.width,drag:shot.distance<ideal.distance*100,untouched:seed===rngState&&n===manual.length,noSolid:$('world-trajectory').getAttribute('visibility')==='hidden',dashed:!!$('ideal-parabola').getAttribute('stroke-dasharray')};$('showVacuum').checked=false;reviewing=false;draw(1,null);return report}''')
 assert physics['error']<1e-10 and physics['dotError']<1e-8 and physics['dots']>10 and all(physics[k] for k in ['endInView','drag','untouched','noSolid','dashed']),physics
 # Save the same real observations, and change only the analysis family.
 page.locator('#labDataPanel>summary').click();page.click('#labSave')
 original=page.evaluate('JSON.stringify(state.runs.map(r=>({id:r.observationId,y:r.y,settings:r._physical})))')
 assert page.evaluate('new Set(state.runs.map(r=>r.observationId)).size')==16
 page.select_option('#labModel','main');page.click('#labFit');assert page.evaluate('state.fit.p')==4
 page.select_option('#labModel','quadratic');page.click('#labFit');assert '不支持' in page.locator('#labMessage').text_content()
 assert page.evaluate('JSON.stringify(state.runs.map(r=>({id:r.observationId,y:r.y,settings:r._physical})))')==original
 assert page.evaluate('labModelMode')=='main'
 multi=page.evaluate("""()=>{const p=catSnapshot();p.responses.push({id:'Y2',name:'Y2 课堂评分',goal:'maximize',lower:0,target:10,upper:10,weight:1,enabled:true});p.activeResponse=1;p.rows.forEach((r,i)=>{r.ys=[r.y,1000+i];r.y=1000+i});return p}""")

 with page.expect_download() as dl:page.click('#labExportCSV')
 csv=dl.value.path().read_text(encoding='utf-8-sig');assert '乒乓球' in csv and '高尔夫球' in csv
 packet=page.evaluate('text=>labDecodeCSV(text)',csv)
 assert [r['y'] for r in packet['rows']]==page.evaluate('state.runs.map(r=>r.y)')
 assert [r['settings'] for r in packet['rows']]==page.evaluate('state.runs.map(r=>r._physical)')
 bad_csv=page.evaluate(r"""text=>{const rows=parseCSV(text);rows[1][8]='';return rows.map(r=>r.map(v=>'"'+v.replaceAll('"','""')+'"').join(',')).join('\n')}""",csv)
 assert page.evaluate("text=>{try{labDecodeCSV(text);return false}catch(e){return e.message.includes('缺少物理设置')}}",bad_csv)
 page.set_input_files('#labImportCSV',{'name':'physical.csv','mimeType':'text/csv','buffer':csv.encode()})
 page.wait_for_function('catConfig.map.join()==="0,3,5"')
 assert page.evaluate('state.runs.map(r=>r.y)')==[r['y'] for r in packet['rows']]

 # Six-factor matching is independent of target run ordering and source coding.
 before=engine.evaluate('({n:manual.length,seed:rngState})');page.evaluate("catBuild('screen')")
 assert page.evaluate('labReuse()')==16
 assert engine.evaluate('({n:manual.length,seed:rngState})')==before
 source=json.loads(original);actual=page.evaluate('state.runs.map(r=>({id:r.observationId,y:r.y,settings:r._physical}))')
 assert sorted(actual,key=lambda x:x['id'])==sorted(source,key=lambda x:x['id'])
 page.evaluate("document.getElementById('replicates').value=4;generateDesign()")
 assert page.evaluate('state.runs.length')==32 and page.evaluate('labReuse()')==16
 assert page.evaluate('new Set(state.runs.filter(r=>Number.isFinite(r.y)).map(r=>r.observationId)).size')==16
 page.evaluate("""()=>{catBuild('screen');state.responses.push({id:'Y2',name:'Y2 课堂评分',goal:'maximize',lower:0,target:10,upper:10,weight:1,enabled:true});state.runs.forEach(r=>r.ys=[null,500+r.run])}""")
 assert page.evaluate("p=>labReuse({id:'multi-response',packet:p})",multi)==16
 assert page.evaluate('state.runs.every(r=>r.y<1000&&r.ys[1]===500+r.run)')
 bad_cv=json.loads(json.dumps(multi));bad_cv.pop('cv',None)
 for r in bad_cv['rows']:r.pop('cv',None)
 page.evaluate("catBuild('screen')")
 assert page.evaluate("p=>labReuse({id:'missing-cv',packet:p})",bad_cv)==0

 # Reimporting an older package without observation IDs must not create new repeats.
 legacy=page.evaluate("""p=>{const q=structuredClone(p);q.activeResponse=0;q.responses=q.responses.slice(0,1);q.rows.forEach(r=>{delete r.observationId;r.ys=[r.ys[0]];r.y=r.ys[0]});return q}""",multi)
 page.evaluate('p=>catImportExperiment(p)',legacy);first_ids=page.evaluate('state.runs.map(r=>r.observationId)');legacy_entry=page.evaluate('labArchive("legacy")')
 page.evaluate('p=>catImportExperiment(p)',legacy);assert page.evaluate('state.runs.map(r=>r.observationId)')==first_ids
 page.evaluate("catBuild('screen');document.getElementById('replicates').value=4;generateDesign()")
 assert page.evaluate('e=>labReuse(e)',legacy_entry)==16 and page.evaluate('e=>labReuse(e)',legacy_entry)==0
 assert page.evaluate("p=>labReuse({id:'modern-copy',packet:p})",multi)==0
 validation_packet=page.evaluate("""p=>{const v=structuredClone(p);v.rows.forEach(r=>{r.phase='独立验证';r.ys=[r.ys[0]];r.y=r.ys[0]});return labDecodeCSV(labEncodeCSV(v))}""",multi)
 assert all(r['phase']=='独立验证' for r in validation_packet['rows'])
 page.evaluate("catBuild('screen')")
 assert page.evaluate("p=>labReuse({id:'validation',packet:p})",validation_packet)==0
 # Eleven existing physical points fill eleven matching CCC rows; only six new shots.
 page.evaluate("catBuild('curve')");page.evaluate('catCollect()')
 curve=page.evaluate('labArchive("11次曲率实验")');ys={r['observationId']:r['y'] for r in curve['packet']['rows']}
 page.evaluate("document.getElementById('designType').value='ccc';generateDesign()")
 assert page.evaluate('state.runs.length')==17
 before=engine.evaluate('manual.length');assert page.evaluate('labReuse()')==11
 assert engine.evaluate('manual.length')==before
 page.evaluate('catCollect()');assert engine.evaluate('manual.length')==before+6
 for row in page.evaluate('state.runs'):
  if row['observationId'] in ys:assert row['y']==ys[row['observationId']]
 page.evaluate("labApplyModel('quadratic')")
 fit=page.evaluate('({X:state.fit.X,y:state.fit.y,beta:state.fit.beta})')
 expected=np.linalg.lstsq(np.array(fit['X']),np.array(fit['y']),rcond=None)[0]
 assert np.max(np.abs(expected-np.array(fit['beta'])))<1e-7
 retained=page.evaluate('state.runs.map(r=>r.y)');page.wait_for_function('JSON.parse(localStorage.getItem(LAB_BACKUP)).packet.rows.length===17')
 page.reload();page.wait_for_function('catReady');assert page.evaluate('labHasRecoverable()')
 assert page.frames[1].evaluate('manual.length')==0
 page.click('#labRestore');assert page.evaluate('state.runs.map(r=>r.y)')==retained
 assert page.evaluate('labModelMode')=='quadratic'
 page.click('#labRemove');page.click('#labUndo');assert page.evaluate('state.runs.map(r=>r.y)')==retained
 linked_packet=page.evaluate("""()=>{const p=catSnapshot();p.responses.push({id:'Y2',name:'Y2课堂评分',goal:'maximize',lower:0,target:10,upper:10,weight:1,enabled:true});p.activeResponse=1;p.rows.forEach(r=>r.ys=[r.y,1000+r.run]);return p}""")
 linked=context.new_page();linked.on('pageerror',lambda e:errors.append(str(e)));linked.goto('http://catapult.local/DOE_Catapult_Analysis.html#catapult='+quote(json.dumps(linked_packet),safe=''));linked.wait_for_function('catReady&&state.fit')
 assert linked.evaluate('labModelMode')=='quadratic' and linked.evaluate('state.activeResponse')==1
 assert linked.evaluate('state.runs.map(r=>r.ys[0])')==retained and linked.evaluate('state.runs.every(r=>r.y===1000+r.run)')
 assert linked.frames[1].evaluate('manual.length')==0
 assert linked.evaluate("!location.hash.startsWith('#catapult=')")
 assert linked.evaluate("async()=>{try{await catValidate();return false}catch(e){return e.message.includes('第一个响应')}}")
 linked.close()
 page.screenshot(path=str(ROOT/'preview-workbench.png'),full_page=False)
 for w in [800,390]:
  page.set_viewport_size({'width':w,'height':1000});page.wait_for_timeout(250)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),w
 assert not errors,errors
 print('Analytic parabola and true drag dots; immutable Y across model choice; full CSV; unique reuse16/32; existing11→CCC17 with6 shots; NumPy regression; protected restore without resampling; responsive layout PASS')
 b.close()
