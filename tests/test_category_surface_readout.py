from pathlib import Path
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright
import csv
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1550,'height':1100},accept_downloads=True)
 def route(r):
  f=ROOT/unquote(urlparse(r.request.url).path).lstrip('/')
  if f.is_file():r.fulfill(path=str(f))
  else:r.abort()
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://catapult.local/DOE_Catapult_Analysis.html');page.wait_for_function('catReady&&!catBusy&&state.runs.every(r=>Number.isFinite(r.y))',timeout=60000)
 original=page.evaluate('JSON.stringify(state.runs.map(r=>r.y))')
 assert page.locator('#surfaceX option').count()==2 and page.locator('#surfaceY option').count()==2
 assert page.evaluate('![Number($("#surfaceX").value),Number($("#surfaceY").value)].some(i=>isBallFactor(i))')
 assert page.locator('#surfaceBallKind option').all_text_contents()==['乒乓球','高尔夫球']
 assert page.locator('.factor-row').first.locator('.factor-low').evaluate('(e)=>e.selectedOptions[0].textContent')=='乒乓球'
 cells=page.locator('#runTable tbody tr td:nth-child(5)').all_text_contents();assert set(cells)=={'乒乓球','高尔夫球'}
 assert page.locator('.y-input').evaluate_all(r'(els)=>els.every(el=>/^\d+\.\d$/.test(el.value))')
 means=[]
 for ball in ['乒乓球','高尔夫球']:
  page.select_option('#surfaceBallKind',ball)
  report=page.evaluate('''()=>{const d=responseGrid(33);let second=0;for(let j=0;j<33;j++)for(let i=1;i<32;i++)second=Math.max(second,Math.abs(d.grid[j][i+1]-2*d.grid[j][i]+d.grid[j][i-1]));for(let i=0;i<33;i++)for(let j=1;j<32;j++)second=Math.max(second,Math.abs(d.grid[j+1][i]-2*d.grid[j][i]+d.grid[j-1][i]));return {second,middle:d.grid[16][16],label:d.categoryName}}''')
  assert report['second']<1e-8,report;assert report['label']==ball;means.append(report['middle'])
 assert abs(means[0]-means[1])>1
 assert page.evaluate('JSON.stringify(state.runs.map(r=>r.y))')==original
 page.click('#surfacePlane');page.wait_for_function('state.fit&&state.fit.terms.every(t=>t.kind==="main")')
 assert page.evaluate('''()=>{const d=responseGrid(5);return Math.abs(d.grid[0][0]+d.grid[4][4]-d.grid[0][4]-d.grid[4][0])<1e-8}''')
 assert page.evaluate('JSON.stringify(state.runs.map(r=>r.y))')==original
 page.click('#surfaceInteractions');page.wait_for_function('state.fit&&state.fit.terms.some(t=>t.kind==="interaction")')
 page.locator('#surfaceCanvas').screenshot(path=str(ROOT/'preview-category-surface.png'))
 with page.expect_download() as dl:page.click('#csvBtn')
 rows=list(csv.reader(dl.value.path().read_text(encoding='utf-8-sig').splitlines()));assert set(r[4] for r in rows[1:])=={'乒乓球','高尔夫球'};assert all(len(r[-1].split('.')[-1])==1 for r in rows[1:])
 # A visible readout persists on the ruler through rebound, rearm and later loading.
 frame=page.frames[1];result=frame.evaluate('''()=>{applySettings([160,110,420,200,200,1]);lastShot=model(vals());lastShot.targetSnapshot=targetSnapshot();reviewing=true;draw(1,lastShot,.15);const mark=$('impact-tape-print'),raw=lastShot.distance,expected=40+(raw-(Math.max(0,Math.floor(raw/10)*10-30)))/70*920;const before=$('impactTape').innerHTML,seed=rngState,n=manual.length;const out={error:Math.abs(Number(mark.getAttribute('cx'))-expected),opacity:mark.getAttribute('opacity'),onTape:Number(mark.getAttribute('cy'))>=42&&Number(mark.getAttribute('cy'))<=107};$('recockArm').click();out.preserved=$('impactTape').innerHTML===before&&rngState===seed&&manual.length===n&&vals()[0]===vals()[1];return out}''')
 assert result['error']<1e-8 and result['opacity']=='.2' and result['onTape'] and result['preserved'],result
 assert not errors,errors
 print('Categorical ball names, continuous axes and smooth fixed-category surfaces, optional main-effect plane without Y changes, one-decimal readings/CSV, retained 80%-transparent ruler imprint PASS');browser.close()
