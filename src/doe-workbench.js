// Embedded offline workbench: reuse observations, never synthesize a response.
const LAB_STORAGE='catapult-doe-library-v1',LAB_BACKUP='catapult-doe-backup-v1';
let labModelMode='design',labStorageIssue='',labBackupTimer=null,labLastRemoved=null,labQualityFrame=0,labLastBackupSignature='';
const labUid=()=>crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
const labPhysicalNames=['释放角 / °','开火角 / °','球杯高度 / mm','定位销刻度','弹力绳刻度','球的种类'];
const labBounds=[[100,180],[90,120],[200,400],[0,200],[0,200],[0,1]];
const labClone=x=>JSON.parse(JSON.stringify(x));
function labRead(key,fallback){try{const s=localStorage.getItem(key);return s?JSON.parse(s):fallback}catch(e){labStorageIssue='浏览器未允许本地恢复，请导出实验包保存。';return fallback}}
function labWrite(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true}catch(e){labStorageIssue='本地保存未成功，请导出实验包保存。';return false}}
let labLibrary=labRead(LAB_STORAGE,[]);if(!Array.isArray(labLibrary))labLibrary=[];
const labInitialBackup=labRead(LAB_BACKUP,null);let labBackupProtected=!!labInitialBackup?.packet;
const labNativeCandidates=allCandidateTerms;
allCandidateTerms=function(type){
 if(labModelMode==='design')return labNativeCandidates(type);
 return labNativeCandidates('ccc').filter(t=>t.kind==='main'||labModelMode!=='main'&&t.kind==='interaction'||labModelMode==='quadratic'&&t.kind==='square');
};
function labRank(X){
 if(!X.length)return 0;const A=X.map(r=>r.slice()),n=A.length,p=A[0].length;let rank=0,max=1;
 for(const row of A)for(const v of row)max=Math.max(max,Math.abs(v));const tol=max*1e-9;
 for(let col=0;col<p&&rank<n;col++){let pivot=rank;for(let i=rank+1;i<n;i++)if(Math.abs(A[i][col])>Math.abs(A[pivot][col]))pivot=i;if(Math.abs(A[pivot][col])<tol)continue;[A[rank],A[pivot]]=[A[pivot],A[rank]];const d=A[rank][col];for(let j=col;j<p;j++)A[rank][j]/=d;for(let i=rank+1;i<n;i++){const f=A[i][col];for(let j=col;j<p;j++)A[i][j]-=f*A[rank][j]}rank++}
 return rank;
}
function labLegacyId(row,packet,index){
 const cv=row.cv??packet.cv,hasNoise=Number(cv)>0&&Number.isFinite(row.seedAfter),value=JSON.stringify([row.physics||packet.physics,row.settings||row.x,row.seedBefore,row.seedAfter,cv,Array.isArray(row.ys)?row.ys[0]:row.y,hasNoise?null:[row.std,row.rep,row.run??index]]);let a=2166136261,b=2246822519;for(let i=0;i<value.length;i++){a=Math.imul(a^value.charCodeAt(i),16777619);b=Math.imul(b^value.charCodeAt(i),3266489917)}return 'legacy-'+(a>>>0).toString(36)+'-'+(b>>>0).toString(36);
}
function labSettingsKey(v){return v.map(n=>Number(n).toFixed(7)).join('|')}
function labNoiseKey(row,packet){const cv=Number(row.cv??packet.cv);return cv>0&&Number.isFinite(row.seedAfter)?labLegacyId({physics:row.physics||packet.physics,settings:row.settings,seedAfter:row.seedAfter,cv,y:0},packet,0):null}
function labCurrentSettings(r){return Array.isArray(r._physical)?r._physical:catSettings(r.x)}
function labQuality(){
 const rows=state.runs.filter(r=>Number.isFinite(r.y)),keys=new Set(rows.map(r=>labSettingsKey(labCurrentSettings(r)))),ids=rows.map(r=>r.observationId).filter(Boolean),{X,cols}=rows.length?buildColumns(rows,selectedTerms()):{X:[],cols:[]},rank=labRank(X);
 return {total:state.runs.length,complete:rows.length,unique:keys.size,repeats:rows.length-keys.size,centers:state.runs.filter(r=>r.kind==='center').length,axes:state.runs.filter(r=>r.kind==='axial').length,rank,parameters:cols.length,df:rows.length-rank,duplicateIds:ids.length-new Set(ids).size};
}
const labNativeSnapshot=catSnapshot;
catSnapshot=function(){
 const packet=labNativeSnapshot();packet.analysisModel=labModelMode;packet.responses=labClone(state.responses);packet.activeResponse=state.activeResponse;packet.measurement='first-impact';
 packet.rows=packet.rows.map((r,i)=>{const source=state.runs[i];if(Number.isFinite(r.y)&&!source.observationId)source.observationId=labUid();return {...r,observationId:source.observationId,ys:source.ys?.slice()}});
 return packet;
};
function labHasRecoverable(){return labBackupProtected}
function labAcceptNewSession(){
 if(!labBackupProtected)return;
 labLibrary=labRead(LAB_STORAGE,labLibrary);const packet=labInitialBackup?.packet;
 if(packet&&!labLibrary.some(e=>e.signature===labFingerprint(packet))){
  if(labLibrary.length>=20)throw Error('存在未恢复进度且仓库已满，请先恢复或导出旧进度。');
  const entry={id:labUid(),title:'上次会话恢复点 · '+new Date(labInitialBackup.savedAt).toLocaleString('zh-CN'),created:labInitialBackup.savedAt,signature:labFingerprint(packet),packet};labLibrary.push(entry);labWrite(LAB_STORAGE,labLibrary);labRenderLibrary();
 }
 labBackupProtected=false;
}
function labFingerprint(packet){return JSON.stringify([packet.physics,packet.factors.map(f=>[f.physicalIndex,f.low,f.high]),packet.rows.map(r=>[r.observationId,Array.isArray(r.ys)?r.ys:r.y,r.settings,r.cv,r.block,r.phase,r.measurement]),packet.responses])}
function labArchive(title,quiet=false){
 if(!state.runs.some(r=>Number.isFinite(r.y))){if(!quiet)labMessage('没有已采集观测可保存。');return null}
 labLibrary=labRead(LAB_STORAGE,labLibrary);const packet=catSnapshot(),signature=labFingerprint(packet),existing=labLibrary.find(e=>e.signature===signature);
 if(existing){existing.packet=packet;if(title)existing.title=title;labWrite(LAB_STORAGE,labLibrary);if(!quiet)labMessage('已更新这批观测的模型选择，不重复保存观测。');labRenderLibrary(existing.id);return existing}
 if(labLibrary.length>=20){labMessage('仓库已保存20批实验，请先导出并移除不需要的快照。');return null}
 const entry={id:labUid(),title:title||`${new Date().toLocaleString('zh-CN')} · ${packet.rows.filter(r=>Number.isFinite(r.y)).length}次 · ${packet.factors.map(f=>f.name).join(' × ')}`,created:new Date().toISOString(),signature,packet};
 labLibrary.push(entry);labWrite(LAB_STORAGE,labLibrary);labRenderLibrary(entry.id);if(!quiet)labMessage(labStorageIssue||'已保存完整设置、原始响应及观测身份，可供其他设计分析或复用。');return entry;
}
function labDownload(name,text,type='application/json'){const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function labMessage(message){document.getElementById('labMessage').textContent=message}
function labRenderLibrary(selected){
 const select=document.getElementById('labDataset');if(!select)return;const value=selected||select.value;select.replaceChildren();
 for(const entry of labLibrary){const option=document.createElement('option');option.value=entry.id;option.textContent=entry.title;select.append(option)}
 if(!labLibrary.length){const option=document.createElement('option');option.value='';option.textContent='尚无快照，请先保存实验';select.append(option)}else if(labLibrary.some(e=>e.id===value))select.value=value;
 for(const id of ['labOpen','labReuse','labRemove'])document.getElementById(id).disabled=!labLibrary.length;
}
function labSelectedEntry(){const id=document.getElementById('labDataset').value;const entry=labLibrary.find(e=>e.id===id);if(!entry)throw Error('先选择已保存的实验快照。');return entry}
function labFlushBackup(){
 if(labBackupProtected||!state.runs.some(r=>Number.isFinite(r.y)))return false;
 const packet=catSnapshot(),signature=JSON.stringify(packet);if(signature===labLastBackupSignature)return true;const saved=labWrite(LAB_BACKUP,{savedAt:new Date().toISOString(),packet});if(saved)labLastBackupSignature=signature;const status=document.getElementById('labBackupStatus');
 if(status)status.textContent=saved?'已在本机保存恢复点 · '+new Date().toLocaleTimeString('zh-CN'):labStorageIssue;return saved;
}
function labScheduleBackup(){clearTimeout(labBackupTimer);if(!labBackupProtected)labBackupTimer=setTimeout(labFlushBackup,400)}
window.addEventListener('pagehide',labFlushBackup);document.addEventListener('visibilitychange',()=>{if(document.hidden)labFlushBackup()});

function labRefreshQuality(){
 const q=labQuality(),ready=q.complete===q.total&&q.total>0,estimable=q.parameters>0&&q.rank===q.parameters&&q.df>0;
 document.getElementById('labQuality').innerHTML=`<div><span>已采集</span><b>${q.complete} / ${q.total}</b></div><div><span>不同设置 / 重复观测</span><b>${q.unique} / ${q.repeats}</b></div><div><span>中心 / 轴点</span><b>${q.centers} / ${q.axes}</b></div><div><span>模型秩 / 参数 / 残差df</span><b>${q.rank} / ${q.parameters} / ${q.df}</b></div>`;
 document.getElementById('labQualityNote').textContent=q.duplicateIds?'发现重复的观测身份：同一次测量不能当作独立重复。':!ready?'先采集缺失点；已有观测不会被重新发射覆盖。':!estimable?'当前项不可完全估计或无残差自由度；减少模型项，或增加合适的实验点和独立重复。':'当前模型可估计；请继续检查残差，并以独立发射验证预测。';
 document.getElementById('labModel').value=labModelMode;
 const steps=document.querySelectorAll('#labFlow button');steps.forEach((b,i)=>{b.setAttribute('aria-current',i===(catBusy?1:ready?state.fit?2:1:0)?'step':'false')});
 document.getElementById('labProgressText').textContent=`${catBusy?'采集中':'实验进度'} ${q.complete}/${q.total} · ${catReady?'投射器已连接':'等待连接'}`;
 return q;
}
function labApplyModel(mode){
 if(catBusy)throw Error('请等待当前采集结束。');const before=JSON.stringify(state.runs.map(r=>r.y)),previous=labModelMode,selected=new Set(state.selected);labModelMode=mode;
 const terms=allCandidateTerms(document.getElementById('designType').value).filter(t=>mode!=='design'||['main','interaction','square','center'].includes(t.kind));
 state.selected=new Set(terms.map(keyOf));const q=labQuality(),allowSaturated=document.getElementById('designType').value==='pb'&&['main','design'].includes(mode);
 if(q.complete!==q.total||q.rank<q.parameters||q.df<=0&&!allowSaturated||q.duplicateIds){labModelMode=previous;state.selected=selected;labRefreshQuality();throw Error('数据不支持所选模型：需要完整数据、独立观测、满秩设计矩阵及正残差自由度。两水平数据不能单独估计全部平方项。')}
 state.fits=Array(state.responses.length).fill(null);clearOptimizerProfiles();renderModelTerms();analyze();if(!state.fit)throw Error('拟合未完成，请检查模型项。');if(before!==JSON.stringify(state.runs.map(r=>r.y)))throw Error('响应发生了意外变化');labRefreshQuality();labScheduleBackup();labMessage('已使用同一批原始响应重新拟合；设计来源、因子水平和响应值均保留。');
}
const labNativeImport=catImportExperiment;
catImportExperiment=function(packet){
 labAcceptNewSession();if(Array.isArray(packet?.rows))packet={...packet,rows:packet.rows.map((r,i)=>r&&Number.isFinite(r.y)&&!r.observationId?{...r,observationId:labLegacyId(r,packet,i)}:r)};labModelMode=['main','interaction','quadratic'].includes(packet?.analysisModel)?packet.analysisModel:'design';labNativeImport(packet);try{if(location.hash.startsWith('#catapult='))history.replaceState(null,'',location.pathname+location.search)}catch(e){}document.getElementById('catPreset').value=['screen','curve'].includes(catConfig.mode)?catConfig.mode:'import';
 if(Array.isArray(packet.responses)&&packet.responses.length&&packet.responses.length<=8&&packet.responses.every(r=>typeof r.name==='string')){
  state.responses=labClone(packet.responses);state.activeResponse=Math.min(packet.activeResponse||0,state.responses.length-1);
  state.runs.forEach((r,i)=>{const ys=packet.rows[i].ys;r.ys=Array.isArray(ys)&&ys.length===state.responses.length?ys.map(v=>Number.isFinite(v)?v:null):[r.y,...Array(state.responses.length-1).fill(null)];r.y=r.ys[state.activeResponse]});catRefresh();
 }
 labRefreshQuality();labScheduleBackup();
};
const labNativeBuild=catBuild;catBuild=function(...args){if(catBusy)return;if((args[0]||document.getElementById('catPreset').value)==='import')throw Error('先选择筛选或曲率路线再创建新实验；导入数据仍可原样分析。');labAcceptNewSession();labArchive(undefined,true);labModelMode='design';labNativeBuild(...args);labRefreshQuality()};
const labNativeCollect=catCollect;catCollect=async function(...args){if(state.activeResponse!==0)throw Error('自动采集针对首次落地距离，请先切回第一个响应。');labAcceptNewSession();return await labNativeCollect(...args)};
const labNativeValidation=catValidate;catValidate=async function(...args){if(state.activeResponse!==0)throw Error('投射器的独立验证测量首次落地距离，请先切回第一个响应。');return await labNativeValidation(...args)};
const labNativeAppend=catAppend;catAppend=async function(...args){labModelMode='design';try{return await labNativeAppend(...args)}finally{labRefreshQuality();labScheduleBackup()}};
function labScheduleQuality(){if(!labQualityFrame)labQualityFrame=requestAnimationFrame(()=>{labQualityFrame=0;labRefreshQuality()})}
function labFixedText(){const values=catConfig.fixed,map=catConfig.map,units=['°','°',' mm','格','格',''];const fixed=values.map((value,i)=>({i,value})).filter(x=>!map.includes(x.i)).map(({i,value})=>labPhysicalNames[i].split(' / ')[0]+' '+(i===5?(value===1?'高尔夫球':'乒乓球'):value+units[i]));return fixed.length?'固定条件：'+fixed.join('；')+'。':'六项物理设置均为设计因子；逐行保留实际值。'}
const labNativeRefresh=catRefresh;catRefresh=function(...args){const result=labNativeRefresh(...args);document.getElementById('catFixed').textContent=labFixedText();return result};
const labNativeProgress=catUpdateProgress;catUpdateProgress=function(){labNativeProgress();if(document.getElementById('labQuality')){labScheduleQuality();labScheduleBackup()}};
function labReuse(entry=labSelectedEntry()){
 if(catBusy)throw Error('请等待采集结束。');catAssertPhysics();if(state.activeResponse!==0)throw Error('观测复用针对首次落地距离，请先切回第一个响应。');
 labAcceptNewSession();const packet=entry.packet;if(packet.physics!==catPhysics)throw Error('源数据的物理版本不同，可以独立分析，不能混入当前设计。');
 const used=new Set(state.runs.filter(r=>Number.isFinite(r.y)).map(r=>r.observationId).filter(Boolean)),usedNoise=new Set(state.runs.filter(r=>Number.isFinite(r.y)).map(r=>labNoiseKey({...r,settings:labCurrentSettings(r)},{physics:catPhysics,cv:Number(document.getElementById('catCV').value)})).filter(Boolean)),pool=new Map(),cv=Number(document.getElementById('catCV').value),hadData=state.runs.some(r=>Number.isFinite(r.y));
 for(let i=0;i<packet.rows.length;i++){const source=packet.rows[i],sourceY=Array.isArray(source.ys)?source.ys[0]:source.y,r={...source,y:sourceY},v=r.settings,sourceCV=Number(r.cv??packet.cv);if(!Number.isFinite(r.y)||!Array.isArray(v)||v.length!==6||r.phase==='独立验证'||r.validation||r.measurement&&r.measurement!=='first-impact'||!Number.isFinite(sourceCV)||Math.abs(sourceCV-cv)>1e-12||(r.physics||packet.physics)!==catPhysics)continue;const id=r.observationId||entry.id+':'+i;const noiseKey=labNoiseKey(r,packet);if(used.has(id)||noiseKey&&usedNoise.has(noiseKey))continue;const key=labSettingsKey(v);if(!pool.has(key))pool.set(key,[]);if(!pool.get(key).some(x=>x.id===id||noiseKey&&x.noiseKey===noiseKey))pool.get(key).push({r,id,noiseKey})}
 let reused=0;for(const target of state.runs){if(Number.isFinite(target.y))continue;const v=catSettings(target.x),queue=pool.get(labSettingsKey(v));while(queue?.length&&(used.has(queue[0].id)||queue[0].noiseKey&&usedNoise.has(queue[0].noiseKey)))queue.shift();const match=queue?.shift();if(!match)continue;const r=match.r;target.y=r.y;target.ys=target.ys||Array(state.responses.length).fill(null);target.ys[0]=r.y;target._physical=v;target.seedBefore=r.seedBefore;target.seedAfter=r.seedAfter;target.cv=r.cv??packet.cv;target.physics=packet.physics;target.observationId=match.id;target.block=r.block||1;target._labReuse={dataset:entry.id,observation:match.id,sourceBlock:r.block||1};used.add(match.id);if(match.noiseKey)usedNoise.add(match.noiseKey);reused++}
 if(reused&&!hadData&&Number.isInteger(packet.seed)&&packet.seed>0)catSeed=packet.seed;
 document.getElementById('blockCount').value=Math.max(1,...state.runs.map(r=>r.block||1));catRefresh();labRefreshQuality();labScheduleBackup();labMessage(`已复用 ${reused} 条已有观测，待采集 ${state.runs.filter(r=>!Number.isFinite(r.y)).length} 条；按完整六项设置、CV和物理版本匹配，未发射、未伪造独立重复。`);if(catReady)catRPC('STORE',{experiment:catSnapshot()}).catch(e=>labMessage(e.message));return reused;
}
const labCSVHeaders=['观测ID','物理模型','设计类型','运行序','标准序','重复','区组','点类型','B_释放角_deg','C_开火角度_deg','D_球杯高度_mm','E_定位销刻度','F_弹力绳刻度','A_球的种类','距离_cm','弹性系数CV_pct','随机状态_采样前','随机状态_采样后','阶段','测量口径'];
function labEncodeCSV(packet){const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';const rows=packet.rows.map(r=>[r.observationId,r.physics||packet.physics,packet.type,r.run,r.std,r.rep,r.block,r.kind,...r.settings.slice(0,5),r.settings[5]===1?'高尔夫球':'乒乓球',Array.isArray(r.ys)?r.ys[0]:r.y,r.cv??packet.cv,r.seedBefore,r.seedAfter,r.phase||'训练观测',r.measurement||packet.measurement||'first-impact']);return '\ufeff'+[labCSVHeaders,...rows].map(r=>r.map(quote).join(',')).join('\r\n')}
function labDecodeCSV(text){
 const table=parseCSV(text);if(table.length<2||table.length>2001)throw Error('CSV应包含表头和1–2000条观测。');const header=table.shift(),index=(...names)=>names.map(n=>header.indexOf(n)).find(i=>i>=0),cols=[index('B_释放角_deg','释放角'),index('C_开火角度_deg','开火角度'),index('D_球杯高度_mm','球杯高度'),index('E_定位销刻度','定位销刻度'),index('F_弹力绳刻度','F_弹力绳位置_mm','弹力绳刻度'),index('A_球的种类','球的种类')],ycol=index('距离_cm','Y1 首次落地距离 / cm');
 if(cols.some(i=>i===undefined)||ycol===undefined)throw Error('CSV需要完整六项物理设置和距离列；可导入本页原始精度CSV或投射器记录CSV。');
 const c=name=>header.indexOf(name),number=(row,name,fallback)=>c(name)>=0&&row[c(name)]!==''?Number(row[c(name)]):fallback;
 const observations=table.map((row,i)=>{if(cols.some(col=>row[col]===undefined||row[col].trim()===''))throw Error(`第${i+2}行缺少物理设置`);const settings=cols.map((col,j)=>j===5?(row[col]==='乒乓球'?0:row[col]==='高尔夫球'?1:Number(row[col])):Number(row[col])),raw=row[ycol],y=raw===''?null:Number(raw),physics=c('物理模型')>=0?row[c('物理模型')]:'unknown-import';if(settings.some((v,j)=>!Number.isFinite(v)||j===5&&![0,1].includes(v))||y!==null&&!Number.isFinite(y))throw Error(`第${i+2}行设置或距离无效`);return {run:i+1,std:number(row,'标准序',i+1),rep:number(row,'重复',1),block:number(row,'区组',1),kind:c('点类型')>=0&&['factorial','center','axial'].includes(row[c('点类型')])?row[c('点类型')]:'factorial',settings,y,ys:[y],physics,phase:c('阶段')>=0?row[c('阶段')]:undefined,measurement:c('测量口径')>=0?row[c('测量口径')]:'first-impact',observationId:c('观测ID')>=0?row[c('观测ID')]||labUid():labUid(),cv:number(row,'弹性系数CV_pct',.5),seedBefore:number(row,'随机状态_采样前',undefined),seedAfter:number(row,'随机状态_采样后',undefined)}});
 const versions=new Set(observations.map(r=>r.physics));if(versions.size>1)throw Error('CSV含不同物理版本，请分开导入分析。');const varying=[0,1,2,3,4,5].filter(j=>new Set(observations.map(r=>r.settings[j])).size>1),map=varying.length>=2?varying:[...new Set([...varying,0,3])].slice(0,2);
 const factors=map.map(j=>{const values=observations.map(r=>r.settings[j]),lo=Math.min(...values),hi=Math.max(...values);return {name:labPhysicalNames[j],physicalIndex:j,categorical:j===5,low:lo===hi?labBounds[j][0]:lo,high:lo===hi?labBounds[j][1]:hi}});
 observations.forEach(r=>{r.x=map.map(j=>r.settings[j]);r.z=r.x.map((v,i)=>(2*v-factors[i].low-factors[i].high)/(factors[i].high-factors[i].low))});
 const type=c('设计类型')>=0?table[0][c('设计类型')]:'full';return {version:1,type:['full','fullCenter','ccc','ccf'].includes(type)?type:'full',physics:observations[0].physics,factors,fixed:observations[0].settings,rows:observations,cv:observations[0].cv,seed:observations.at(-1).seedAfter||2026,target:300,analysisModel:'main',measurement:'first-impact'};
}
const labNativeCSVImport=importCSV;
importCSV=async function(file){
 if(!file)return;const text=await file.text(),headers=parseCSV(text)[0]||[];
 if(headers.includes('B_释放角_deg')&&headers.includes('A_球的种类')){
  try{if(catBusy)throw Error('请等待采集结束。');const packet=labDecodeCSV(text);labArchive(undefined,true);catImportExperiment(packet);document.getElementById('labDataPanel').open=true;labMessage('已按完整六项设置导入原始观测，不依赖当前运行序。')}catch(e){labMessage(e.message)}
 }else return labNativeCSVImport(file);
};
// Layout: a compact workflow, grouped controls, persistent progress, readable tables and keyboard focus.
const labCSS=document.createElement('style');labCSS.textContent=`
html{scroll-padding-top:90px}.lab-workspace{font-family:"Microsoft YaHei","微软雅黑",sans-serif;color:#1b3b52}.lab-flow-bar{max-width:1500px;margin:12px auto;display:flex;align-items:center;gap:8px;position:sticky;top:0;background:#fff;z-index:20;padding:10px;border:1px solid #d8e5ee;border-radius:10px;box-shadow:0 3px 10px #254d6810}.lab-flow-bar button{min-height:40px;background:#eff5fa;border:1px solid #c7dae8;border-radius:7px;padding:8px 15px;color:#005b99}.lab-flow-bar button[aria-current=step]{background:#005b99;color:#fff}.lab-flow-bar output{margin-left:auto;font-size:13px;color:#476174}.lab-data-panel{border:1px solid #d8e5ee;border-radius:10px;padding:16px;margin:14px 0;background:#fbfdff}.lab-data-panel h3{margin:0 0 12px;font-size:17px;color:#005b99}.lab-data-row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:9px 0}.lab-data-row label{display:flex;gap:8px;align-items:center;font-size:14px}.lab-data-row input[type=file]{max-width:100%}.lab-data-row select{max-width:580px;min-height:40px;min-width:220px}.lab-data-row button{min-height:40px;border:1px solid #c2d6e5;border-radius:7px;padding:8px 13px;color:#005b99;background:#fff}.lab-data-row button.lab-primary{background:#005b99;color:#fff}.lab-quality{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:15px}.lab-quality div{background:#edf4f9;padding:12px;border-radius:8px}.lab-quality span{display:block;color:#526d80;font-size:12px}.lab-quality b{display:block;color:#005b99;font-size:19px;margin-top:6px}.lab-data-panel p{font-size:13px;line-height:1.8;color:#526d80;margin:8px 0}.lab-data-panel p[role=status]{color:#075f73;min-height:24px}.lab-toolbar-label{display:block;color:#005b99;font-weight:700;font-size:14px;margin-top:12px}#catapultLink .cat-toolbar{border-bottom:1px solid #e1eaf1;padding-bottom:12px}#catapultLink #catStop{color:#a04930}#runTable th{position:sticky;top:0;z-index:3;background:#eaf2f9}#runTable th,#runTable td{min-width:92px;padding:12px 14px}#runTable th:nth-child(-n+2),#runTable td:nth-child(-n+2){min-width:64px}#runTable th:first-child,#runTable td:first-child{position:sticky;left:0;background:#eff5fa;z-index:2}.table-wrap{min-width:0;max-width:100%;box-sizing:border-box;max-height:590px;overflow:auto}.results-grid>.card{min-width:0;max-width:100%}.card-head>div{min-width:0;max-width:100%}#labWorkspace button:focus-visible,#labWorkspace select:focus-visible{outline:3px solid #ed9e42;outline-offset:3px}#labWorkspace button:disabled{opacity:.45}#catapultLink summary{min-height:40px;line-height:2}
@media(max-width:800px){.results-grid{grid-template-columns:minmax(0,1fr)}.card-kicker,.cmp-note{white-space:normal;overflow-wrap:anywhere}.lab-flow-bar{position:static;display:grid;grid-template-columns:1fr 1fr}.lab-flow-bar output{grid-column:1/-1;margin-left:0}.lab-quality{grid-template-columns:1fr 1fr}.lab-data-row{align-items:stretch}.lab-data-row label{flex-wrap:wrap}.lab-data-row select{min-width:0;width:100%;max-width:100%}.lab-data-panel{padding:12px}#catapultLink{padding:12px!important}#catapultLink .cat-toolbar label{max-width:100%;flex-wrap:wrap}#catapultLink select{max-width:100%}#runTable th,#runTable td{min-width:82px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
`;document.head.append(labCSS);
const workspace=document.createElement('section');workspace.id='labWorkspace';workspace.className='lab-workspace';workspace.setAttribute('aria-label','跨设计实验数据工作台');
workspace.innerHTML=`<nav id="labFlow" class="lab-flow-bar" aria-label="DOE工作流程"><button type="button" data-lab-jump="catPreset">1 设计</button><button type="button" data-lab-jump="catCollect">2 采集</button><button type="button" data-lab-jump="modelCard">3 分析</button><button type="button" data-lab-jump="catValidate">4 验证</button><output id="labProgressText" aria-live="polite"></output></nav><details id="labDataPanel" class="lab-data-panel"><summary style="font-size:16px;font-weight:700;color:#005b99">实验数据仓库 · 同一批观测，多种分析</summary><div class="lab-data-row"><button id="labSave" class="lab-primary">保存当前实验快照</button><label>已保存实验<select id="labDataset" aria-label="选择实验快照"></select></label><button id="labOpen">使用所选数据分析</button><button id="labReuse">匹配复用到当前设计</button></div><div class="lab-data-row"><label>分析模型<select id="labModel"><option value="design">依原设计选择模型项</option><option value="main">主效应模型</option><option value="interaction">主效应＋两因子交互</option><option value="quadratic">连续因子二次模型</option></select></label><button id="labFit">对同一批数据重新拟合</button><button id="labExportCSV">导出首次落地CSV（原始精度）</button><label>导入完整CSV<input id="labImportCSV" type="file" accept=".csv,text/csv"></label></div><details id="labRecoveryOptions"><summary>恢复与仓库管理</summary><div class="lab-data-row"><button id="labRestore">恢复上次本机进度</button><button id="labRemove">移除所选快照</button><button id="labUndo" hidden>撤销移除</button><output id="labBackupStatus"></output></div><p>本机恢复点不会自动覆盖当前实验。重要数据请同时导出 JSON 实验包；本地存储未获允许时仍可使用下载与导入。</p></details><div id="labQuality" class="lab-quality"></div><p id="labQualityNote"></p><p id="labMessage" role="status" aria-live="polite"></p><p>复用以完整六项设置、物理版本和 CV 匹配，一次观测不重复充当独立测量。改变分析模型不会改变响应值；可估计性由实际设计矩阵检查，不将原实验冒充为另一种设计。</p></details>`;
const importedOption=document.createElement('option');importedOption.value='import';importedOption.textContent='导入数据 · 保留原映射';importedOption.disabled=true;document.getElementById('catPreset').append(importedOption);
document.getElementById('catapultLink').querySelector('h2').after(workspace);document.getElementById('catapultLink').before(document.getElementById('labFlow'));
const firstToolbar=document.querySelector('#catapultLink>.cat-toolbar'),secondToolbar=firstToolbar.nextElementSibling;const tag=document.createElement('span');tag.className='lab-toolbar-label';tag.textContent='设计与采集';firstToolbar.before(tag);
const advanced=document.createElement('details');advanced.id='labAcquisitionOptions';advanced.open=true;const summary=document.createElement('summary');summary.textContent='采集选项 · 波动、随机种子、慢镜头与区组';advanced.append(summary);secondToolbar.before(advanced);advanced.append(secondToolbar);
const on=(id,fn)=>{document.getElementById(id).onclick=async()=>{try{await fn()}catch(e){labMessage(e.message)}}};
on('labSave',()=>labArchive());on('labOpen',()=>{if(catBusy)throw Error('请等待采集结束。');const entry=labSelectedEntry();labArchive(undefined,true);catImportExperiment(labClone(entry.packet));labMessage('已载入同一批原始观测，可选择其他可估计的模型分析。')});on('labReuse',()=>labReuse());on('labFit',()=>labApplyModel(document.getElementById('labModel').value));
on('labExportCSV',()=>{const packet=catSnapshot();labDownload('Catapult_完整原始观测.csv',labEncodeCSV(packet),'text/csv;charset=utf-8')});
document.getElementById('labImportCSV').onchange=async event=>{try{if(catBusy)throw Error('请等待采集结束。');const file=event.target.files[0];if(!file)return;if(file.size>8000000)throw Error('CSV文件过大');const packet=labDecodeCSV(await file.text());labArchive(undefined,true);catImportExperiment(packet);labMessage('已按六项物理设置建立实验数据，无需先生成相同运行顺序；响应保持原始精度。')}catch(e){labMessage(e.message)}finally{event.target.value=''}};
on('labRestore',()=>{if(catBusy)throw Error('请等待采集结束。');const saved=labBackupProtected?labInitialBackup:labRead(LAB_BACKUP,null);if(!saved?.packet)throw Error('尚无可恢复的本机进度。');labArchive(undefined,true);labBackupProtected=false;catImportExperiment(saved.packet);labMessage('已恢复 '+new Date(saved.savedAt).toLocaleString('zh-CN')+' 的进度；采集将跳过已完成行。')});
on('labRemove',()=>{const entry=labSelectedEntry();labLastRemoved=entry;labLibrary=labRead(LAB_STORAGE,labLibrary).filter(e=>e.id!==entry.id);labWrite(LAB_STORAGE,labLibrary);labRenderLibrary();document.getElementById('labUndo').hidden=false;labMessage('已从本机仓库移除，当前正在分析的数据未变。可撤销此次移除。')});
on('labUndo',()=>{if(labLastRemoved){labLibrary=labRead(LAB_STORAGE,labLibrary);labLibrary.push(labLastRemoved);labWrite(LAB_STORAGE,labLibrary);labRenderLibrary(labLastRemoved.id);labLastRemoved=null;document.getElementById('labUndo').hidden=true;labMessage('已恢复被移除的快照。')}});
document.querySelectorAll('[data-lab-jump]').forEach(button=>button.onclick=()=>document.getElementById(button.dataset.labJump)?.scrollIntoView({behavior:'smooth',block:'start'}));
document.addEventListener('input',event=>{if(event.target.closest('#runTable')){labRefreshQuality();labScheduleBackup()}});document.addEventListener('change',event=>{if(event.target.closest('#modelTerms')||event.target.id==='includeBlockModel'){setTimeout(labRefreshQuality,250);labScheduleBackup()}});
document.getElementById('catFixed').textContent=labFixedText();document.getElementById('catPreset').value=['screen','curve'].includes(catConfig.mode)?catConfig.mode:'import';
document.getElementById('uploadBtn').title='完整物理CSV按六项设置导入；仅含响应列的CSV按当前计划填写';
labRenderLibrary();labRefreshQuality();if(catImport){labAcceptNewSession();catImportExperiment(labClone(catImport))}const backup=labInitialBackup;if(backup&&!catImport){document.getElementById('labDataPanel').open=true;document.getElementById('labRecoveryOptions').open=true}document.getElementById('labBackupStatus').textContent=backup?'有可恢复进度 · '+new Date(backup.savedAt).toLocaleString('zh-CN'):labStorageIssue||'首次采集后自动在本机保存恢复点';

window.addEventListener('storage',event=>{if(event.key===LAB_STORAGE){labLibrary=labRead(LAB_STORAGE,labLibrary);labRenderLibrary()}});
