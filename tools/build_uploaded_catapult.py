"""Build the user's self-contained HTML without changing its calibrated response model."""
from pathlib import Path
import base64
ROOT=Path(__file__).resolve().parents[1]
outer=(ROOT/'src/uploaded-catapult-base.html').read_text()
analyzer=(ROOT/'src/uploaded-analyzer-base.html').read_text()
outer=outer.replace("set('world-ball',{visibility:flying?'visible':'hidden',r:20*(1-blend)+Math.max(20,8/pixelScale)*blend", "const visualBallRadius=Math.max(20,8/pixelScale);\n set('world-ball',{visibility:flying?'visible':'hidden',r:visualBallRadius")
outer=outer.replace('const ghostRadius=Math.max(20,8/pixelScale);','const ghostRadius=visualBallRadius;')
outer=outer.replace("const shot=model(options.settings||vals(),cv);", "const seedBefore=rngState;const shot=model(options.settings||vals(),cv,options.responseOrder||null);")
outer=outer.replace("manual.push({vals:shot.vals", "manual.push({observationId:crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+'-'+Math.random().toString(36).slice(2),physics:PHYSICS_VERSION,measurement:'first-impact',seedBefore,vals:shot.vals")
outer=outer.replace("const phase=options.phase||'探索',series=options.series||'';", "const phase=options.phase||'探索',series=options.series||'';if(phase==='探索')linkedExperimentFresh=false;")
outer=outer.replace("function nextRun(){const r=plan.find(r=>r.y===null);if(!r)return false;const shot=model", "function nextRun(){const r=plan.find(r=>r.y===null);if(!r)return false;linkedExperimentFresh=false;r.observationId=crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);r.seedBefore=rngState;const shot=model")
outer=outer.replace("let linkedExperiment=null,catBridgeSession=null;", "let linkedExperiment=null,linkedExperimentFresh=false,catBridgeSession=null,uploadedAnalysisWindow=null;const uploadedSessions=new Map();")
outer=outer.replace("if(linkedExperiment&&!plan.length&&!manual.length)", "if(linkedExperiment&&(linkedExperimentFresh||!plan.length&&!manual.length))")
outer=outer.replace("y:r.y,physics:PHYSICS_VERSION,settings:r.vals", "y:r.y,observationId:r.observationId,seedBefore:r.seedBefore,phase:r.phase,measurement:'first-impact',physics:PHYSICS_VERSION,settings:r.vals")
outer=outer.replace("function openCatapultDOE(){", "function openCatapultDOE(options={}){")
outer=outer.replace("if(!payload.rows.some(r=>Number.isFinite(r.y)))return", "if(!options.allowEmpty&&!payload.rows.some(r=>Number.isFinite(r.y)))return")
outer=outer.replace("const opened=window.open('','catapult-doe-analysis');if(!opened)", "const opened=window.open('','catapult-doe-analysis');uploadedAnalysisWindow=opened;if(!opened)")
outer=outer.replace("const d=event.data;if(parent===window||event.source!==parent||!d||d.protocol!=='CATAPULT_DOE_V1')return;", "const d=event.data,allowed=(parent!==window&&event.source===parent)||event.source===uploadedAnalysisWindow||(event.source===window.opener&&event.origin===location.origin);if(!allowed||!d||d.protocol!=='CATAPULT_DOE_V1')return;")
outer=outer.replace("catBridgeSession=d.session;reply(true,{version:1,physics:PHYSICS_VERSION,", "catBridgeSession=d.session;uploadedSessions.set(event.source,d.session);reply(true,{version:1,physics:PHYSICS_VERSION,responseOrder:$('responseOrder').value,")
outer=outer.replace('if(d.session!==catBridgeSession)return;','if(d.session!==uploadedSessions.get(event.source))return;')
outer=outer.replace("linkedExperiment=structuredClone(d.experiment);reply", "linkedExperiment=structuredClone(d.experiment);linkedExperimentFresh=true;reply")
outer=outer.replace("const base=model(v);", "if(d.responseOrder!==undefined&&!['linear','quadratic'].includes(d.responseOrder))throw Error('响应定义无效');const base=model(v);")
outer=outer.replace("phase:d.validation?'独立验证':'DOE 联动'", "responseOrder:d.responseOrder,phase:d.validation?'独立验证':'DOE 联动'")
outer=outer.replace("physics:PHYSICS_VERSION,measurement:'first-impact',record:manual.length", "physics:PHYSICS_VERSION,observationId:manual.at(-1).observationId,sigma:shot.distanceSigma,responseOrder:shot.responseOrder,measurement:'first-impact',record:manual.length")
outer=outer.replace("catBridgeButton.textContent='一键导入 DOE 分析'", "catBridgeButton.textContent='一键打开 DOE 工作台'")
analyzer=analyzer.replace("delete window.__CATAPULT_IMPORT__;", "window.__UPLOADED_SOURCE_PACKET__=payload;delete window.__CATAPULT_IMPORT__;")
analyzer=analyzer.replace('const blocks=Math.max(...rows.map(r=>r.block));\n  for(let b=2;b<=blocks;b++)cols.push', 'const blockLevels=[...new Set(rows.map(r=>r.block))].sort((a,b)=>a-b);\n  for(const b of state.includeBlocks===false?[]:blockLevels.slice(1))cols.push')
analyzer=analyzer.replace('曲率显著 → 一键升级 RSM','曲率检查 → 按需升级 RSM')
adapter=(ROOT/'src/uploaded-analyzer-adapter.js').read_text()
workbench=(ROOT/'src/uploaded-doe-workbench.js').read_text()
finish="""
if(!uploadedPacket?.rows?.length)catBuild('screen');
catEl('uploadedFilterOrder').onclick=catSafe(()=>{const selected=catEl('uploadedResponseOrder').value,p=catSnapshot();labArchive('筛选前完整实验',true);p.rows=p.rows.filter(r=>r.responseOrder===selected);if(!p.rows.length)throw Error('没有所选响应定义的观测。');p.responseOrder=selected;p.rows.forEach((r,i)=>r.run=i+1);catImportExperiment(p);labMessage('已保留所选响应定义；原完整快照在仓库中，响应原值不变。')});
if(uploadedRig)uploadedConnect().catch(e=>catStatus(e.message));else{catEl('catConnection').textContent='未连接';catStatus('可直接导入已有数据分析；需要补充发射时，请打开投射器窗口。')}
window.uploadedWorkbench={snapshot:()=>catSnapshot(),quality:()=>labQuality(),getConfig:()=>({...catConfig}),getLibrary:()=>labClone(labLibrary),build:(...a)=>catBuild(...a),collect:(...a)=>catCollect(...a),append:(...a)=>catAppend(...a),reuse:(...a)=>labReuse(...a),save:(...a)=>labArchive(...a),fit:(...a)=>labApplyModel(...a),importPacket:(...a)=>catImportExperiment(...a),decodeCSV:(...a)=>labDecodeCSV(...a),encodeCSV:(...a)=>labEncodeCSV(...a),validate:(...a)=>catValidate(...a),getReady:()=>catReady,getBusy:()=>catBusy};
"""
code="(()=>{function initializeUploadedWorkbench(){\n"+adapter+'\n'+workbench+'\n'+finish+"\n}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initializeUploadedWorkbench,{once:true});else initializeUploadedWorkbench()})();"
assert '</script' not in code.lower()
pos=analyzer.rfind('</body>');analyzer=analyzer[:pos]+'<script>\n'+code+'\n</script>\n'+analyzer[pos:]
outer=outer.replace('__EMBEDDED_DOE_ANALYZER__',base64.b64encode(analyzer.encode()).decode())
enhancement=(ROOT/'src/uploaded-catapult-experience.js').read_text()+"\nconst openExistingDOE=document.createElement('button');openExistingDOE.id='openExistingDOE';openExistingDOE.textContent='导入与分析已有数据';openExistingDOE.onclick=()=>openCatapultDOE({allowEmpty:true});document.querySelector('.rig-actions').append(openExistingDOE);\n"
assert '</script' not in enhancement.lower()
pos=outer.rfind('</body>');outer=outer[:pos]+'<script>\n'+enhancement+'\n</script>\n'+outer[pos:]
(ROOT/'投射器实验_优化版.html').write_text(outer)
(ROOT/'投射器实验_DOE分析_优化版.html').write_text(analyzer)
print('Built attachment-based standalone HTML and its embedded DOE analyzer')
