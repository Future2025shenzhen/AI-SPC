from pathlib import Path
from urllib.parse import urlparse, unquote
import json, math
import numpy as np
from scipy.stats import f as f_distribution
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def serve(route):
    path=ROOT/unquote(urlparse(route.request.url).path).lstrip('/')
    if path.is_file(): route.fulfill(path=str(path))
    else: route.abort()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1550,'height':1100},accept_downloads=True)
    context.route('**/*',serve)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://catapult.local/DOE_Catapult_Analysis.html')
    page.wait_for_function('catReady&&!catBusy&&state.runs.length===16&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
    assert page.evaluate('state.responses[0].name')=='Y1 首次落地距离 / cm'
    assert page.evaluate('catConfig.map.join()')=='5,0,3'
    assert page.evaluate('new Set(state.runs.map(r=>r.x.join())).size===8&&state.runs.every(r=>[0,1].includes(r.x[0]))&&state.runs.filter(r=>r.rep===1).length===8&&state.runs.filter(r=>r.rep===2).length===8')
    frame=page.frame_locator('#catapultFrame');engine=page.frames[1]
    rows=page.evaluate('state.runs.map(r=>({y:r.y,settings:r._physical,seedBefore:r.seedBefore,seedAfter:r.seedAfter,cv:r.cv}))')
    comparison=engine.evaluate('''rows=>{const saved=rngState;const out=rows.map(r=>{rngState=r.seedBefore;const s=model(r.settings,r.cv);return {error:Math.abs(s.distance-r.y),seed:rngState===r.seedAfter,record:manual.some(m=>m.y===r.y&&m.seedState===r.seedAfter&&m.vals.every((v,i)=>v===r.settings[i]))}});rngState=saved;return out}''',rows)
    assert all(r['error']<1e-12 and r['seed'] and r['record'] for r in comparison)
    # Invalid requests do not unlock an existing shot or alter measurements.
    before=engine.evaluate('({n:manual.length,seed:rngState})')
    assert page.evaluate('''async()=>{try{await catRPC('SIMULATE',{settings:[150,110,420,200,200,.5],cv:.5,seed:123});return false}catch(e){return true}}''')
    assert engine.evaluate('({n:manual.length,seed:rngState})')==before
    page.select_option('#catPreset','curve');page.click('#catBuild');page.click('#catCollect')
    page.wait_for_function('!catBusy&&state.runs.length===11&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
    assert page.evaluate('catConfig.map.join()')=='2,0,3'
    assert page.evaluate('state.runs.filter(r=>r.kind==="center").length')==3
    original=page.evaluate('JSON.stringify(state.runs.map(r=>({y:r.y,x:r.x,z:r.z,physical:r._physical,seed:r.seedBefore})))')
    curvature=page.evaluate('curvatureStats()');assert curvature['ok']
    assert abs(curvature['p']-f_distribution.sf(curvature['F'],1,curvature['df2']))<1e-10
    page.click('#catAppend');page.wait_for_function('!catBusy&&state.runs.length===17&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
    assert original==page.evaluate('JSON.stringify(state.runs.slice(0,11).map(r=>({y:r.y,x:r.x,z:r.z,physical:r._physical,seed:r.seedBefore})))')
    assert page.evaluate('state.runs.filter(r=>r.kind==="axial").length')==6
    assert abs(page.evaluate('Math.max(...state.runs.flatMap(r=>r.z.map(Math.abs)))')-8**.25)<1e-12
    native=page.evaluate('({X:state.fit.X,y:state.fit.y,beta:state.fit.beta,block:blockStats(state.fit),df:state.fit.df})')
    expected=np.linalg.lstsq(np.array(native['X']),np.array(native['y']),rcond=None)[0]
    assert np.max(np.abs(expected-np.array(native['beta'])))<1e-7
    assert abs(native['block']['p']-f_distribution.sf(native['block']['F'],1,native['df']))<1e-10
    # Configuring the optimized/center setting does not fire or advance randomness.
    n=engine.evaluate('manual.length');seed=engine.evaluate('rngState')
    page.click('#catSend');page.wait_for_function('document.getElementById("catValidation").textContent.includes("已载入")')
    assert engine.evaluate('manual.length')==n and engine.evaluate('rngState')==seed
    result=page.evaluate('catValidate(5)');assert len(result['ys'])==5 and all(math.isfinite(v) for v in result['ys'])
    assert page.evaluate('state.runs.length')==17 and engine.evaluate('manual.length')==n+5
    # Downloaded complete data package preserves all settings and unrounded Y values.
    with page.expect_download() as download:page.click('#catSaveJSON')
    payload=json.loads(download.value.path().read_text());assert len(payload['rows'])==17
    assert payload['rows'][0]['y']==page.evaluate('state.runs[0].y')
    page.set_input_files('#catLoadJSON',{'name':'roundtrip.json','mimeType':'application/json','buffer':json.dumps(payload).encode()})
    page.wait_for_function('catConfig.mode==="curve"');assert page.evaluate('state.runs.length')==17
    # Catapult -> DOE: one click opens the same training dataset, including CCC blocks.
    with page.expect_popup() as popup:engine.evaluate('openCatapultDOE()')
    linked=popup.value;linked.on('pageerror',lambda e:errors.append(str(e)));linked.wait_for_function('typeof catReady!=="undefined"&&catReady&&state.runs.length===17',timeout=60000)
    assert linked.evaluate('state.runs.map(r=>r.y)')==[r['y'] for r in payload['rows']]
    assert linked.evaluate('state.runs.map(r=>r.block)')==[r['block'] for r in payload['rows']]
    linked.close()
    # A partially collected plan resumes without resampling completed observations.
    page.select_option('#catPreset','screen');page.click('#catBuild')
    page.evaluate('''()=>{window._rpcOriginal=catRPC;catRPC=async function(command,payload){if(command==='SIMULATE')await new Promise(r=>setTimeout(r,80));return _rpcOriginal(command,payload)}}''')
    page.click('#catCollect');page.wait_for_function('state.runs.some(r=>Number.isFinite(r.y))');page.click('#catStop');page.wait_for_function('!catBusy')
    first=page.evaluate('state.runs.filter(r=>Number.isFinite(r.y)).map(r=>({run:r.run,y:r.y}))');assert 0<len(first)<16
    page.click('#catCollect');page.wait_for_function('!catBusy&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
    for r in first:assert page.evaluate('(run)=>state.runs.find(r=>r.run===run).y',r['run'])==r['y']
    page.screenshot(path=str(ROOT/'preview-linked-doe.png'),full_page=False)
    # Opaque-origin frame models the origin isolation of sibling file:// pages.
    opaque=context.new_page();opaque.on('pageerror',lambda e:errors.append(str(e)))
    opaque.add_init_script("window.sawNullOrigin=false;window.addEventListener('message',e=>{if(e.data?.protocol==='CATAPULT_DOE_V1'&&e.origin==='null')window.sawNullOrigin=true})")
    opaque.route('**/opaque.html',lambda r:r.fulfill(body=(ROOT/'DOE_Catapult_Analysis.html').read_text().replace('id="catapultFrame"','sandbox="allow-scripts allow-popups allow-downloads" id="catapultFrame"'),content_type='text/html'))
    opaque.goto('http://catapult.local/opaque.html');opaque.wait_for_function('catReady&&!catBusy&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
    assert opaque.evaluate('sawNullOrigin&&state.runs.length===16');opaque.close()
    assert not errors,errors
    print('Linked pages: 16 physical runs; 11+6 CCC preserving original Y; regression/F vs SciPy; matching Catapult records and RNG; configure/independent validation; JSON; bidirectional link; stop/resume PASS')
    browser.close()
