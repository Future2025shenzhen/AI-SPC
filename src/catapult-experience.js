// Embedded by tools/embed_enhancements.py; no network dependencies.
function vacuumFlight(shot){
  const time=(shot.vy+Math.sqrt(shot.vy*shot.vy+2*PHYSICS.g*shot.h))/PHYSICS.g;
  return {time,distance:shot.vx*time,at:t=>({x:shot.vx*t,y:shot.h+shot.vy*t-.5*PHYSICS.g*t*t})};
}
document.body.classList.add('lab-experience');
const experienceCSS=document.createElement('style');
experienceCSS.textContent=`
.lab-experience{background:#f3f6fa;color:#183449}.lab-experience .card{border-radius:12px;box-shadow:0 2px 8px #153b5710}
.lab-flow{max-width:1660px;margin:14px auto;display:flex;gap:8px;padding:8px 16px;flex-wrap:wrap}.lab-flow button{border:1px solid #c5d8e5;background:#fff;color:#005b99;border-radius:8px;padding:10px 18px;min-height:44px}.lab-flow button[aria-current=step]{background:#005b99;color:#fff}
body.lab-experience>nav:not(.lab-flow){display:none}.physics-console{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:14px 0;padding:14px;background:#f4f8fc;border:1px solid #d9e5ee;border-radius:10px}.physics-console label{font-size:14px;display:block;color:#526d80}.physics-console output{display:block;margin-top:5px;font-size:19px;font-weight:700;color:#005b99}.physics-options{display:flex;gap:20px;flex-wrap:wrap;padding:8px 0;font-size:14px}.physics-options label{display:flex;align-items:center;gap:7px;min-height:32px;cursor:pointer}.physics-caption{margin:0;color:#5a7182;font-size:13px;line-height:1.8}
.lab-experience button:focus-visible,.lab-experience input:focus-visible{outline:3px solid #f09b43;outline-offset:3px}.lab-experience .history thead th,.lab-experience .scroll thead th{position:sticky;top:0;z-index:2;background:#edf4f9}.lab-experience .history th,.lab-experience .history td{min-width:72px;padding:12px 10px}.lab-experience .history th:first-child,.lab-experience .history td:first-child{position:sticky;left:0;background:#f5f9fc;z-index:1}.lab-experience .rig-actions{gap:9px;flex-wrap:wrap}.lab-experience .rig-actions button{min-height:42px}
@media(max-width:760px){.physics-console{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.lab-flow{display:grid;grid-template-columns:1fr 1fr;padding:6px 12px}.lab-flow button{padding:10px}.physics-options{gap:10px}.physics-console output{font-size:17px}}
@media(prefers-reduced-motion:reduce){.lab-experience *{scroll-behavior:auto!important}}
`;
document.head.append(experienceCSS);
const flow=document.querySelector('nav[aria-label="实验导航"]')||document.createElement('nav');flow.replaceChildren();flow.className='lab-flow';flow.setAttribute('aria-label','实验流程');
for(const [label,panel,selector] of [['1 · 操作与观察','lab','#mechanism'],['2 · 设计与采集','doe','#doe'],['3 · 数据分析','analysis','#analysis'],['4 · 目标验证','lab','.verify-controls'],['教学指南','guide','#guide']]){
 const button=document.createElement('button');button.type='button';button.textContent=label;if(selector!=='.verify-controls')button.dataset.tab=panel;
 button.onclick=()=>{tab(panel);document.querySelector(selector)?.scrollIntoView({block:'start',behavior:'smooth'});flow.querySelectorAll('button').forEach(b=>{b.removeAttribute('aria-current');b.classList.remove('active')});button.classList.add('active');button.setAttribute('aria-current','step')};flow.append(button);
}
flow.firstChild.setAttribute('aria-current','step');document.querySelector('header').after(flow);
const physicalPanel=document.createElement('section');physicalPanel.id='physicalInspector';physicalPanel.setAttribute('aria-label','抛体运动教学观察');
physicalPanel.innerHTML=`<div class="physics-options"><label><input id="showPhysicsDots" type="checkbox" checked>显示离散轨迹点</label><label><input id="showVacuum" type="checkbox">对照理想抛物线（无空气阻力）</label></div><details id="physicsReadouts"><summary style="font-size:14px;color:#355c76;cursor:pointer">展开物理读数与抛物线说明</summary><div class="physics-console"><div><label>上次离杯速度</label><output id="physicalSpeed">—</output></div><div><label>上次出射仰角</label><output id="physicalAngle">—</output></div><div><label>重力加速度</label><output>9.81 m/s²</output></div><div><label id="physicalFourthLabel">飞行条件</label><output id="physicalFourth">重力＋空气阻力</output></div></div><p class="physics-caption">有空气阻力的轨迹由运动方程积分；无空气阻力的理想轨迹为抛物线。比较开关与慢放只改变显示，实验响应始终为实际模型的首次落地距离。</p></details>`;
document.querySelector('.rig-stage-foot').before(physicalPanel);
let physicalRenderKey='';
function renderPhysicalOverlay(){
 const svg=$('mechanism'),s=currentViewShot||lastShot,valid=!!s?.valid,active=valid&&(reviewing||motionPlaying),pose=valid?motionPose(currentViewProgress,s):null;
 $('physicalSpeed').textContent=valid?s.speed.toFixed(1)+' m/s':'—';$('physicalAngle').textContent=valid?s.launchAngle.toFixed(1)+'°':'—';
 const ideal=valid?vacuumFlight(s):null,compare=$('showVacuum').checked;
 $('physicalFourthLabel').textContent=compare?'理想首次落地距离':'飞行条件';$('physicalFourth').textContent=compare&&valid?(ideal.distance*100).toFixed(1)+' cm':'重力＋空气阻力';
 let host=$('physics-overlay');if(!host){host=document.createElementNS('http://www.w3.org/2000/svg','g');host.id='physics-overlay';host.setAttribute('pointer-events','none');svg.querySelector('#launch-foreground').insertBefore(host,$('world-ball'));physicalRenderKey=''}
 if(!active||!pose||pose.time<s.armTime){host.replaceChildren();physicalRenderKey='';return}
 const elapsed=Math.min(s.t,Math.max(0,pose.time-s.armTime)),M=svg.getScreenCTM(),scale=Math.max(.01,Math.hypot(M.a,M.b)),O=diagramPose.pivot,releaseX=O.x+ballMountPose(s.vals,s.vals[1]).x*620,floor=O.y+PHYSICS.pivotHeight*620;
 const key=[s.distance,s.speed,s.releaseAngle,Math.floor(elapsed/s.t*36),$('showPhysicsDots').checked,compare,scale].join('|');if(key===physicalRenderKey)return;physicalRenderKey=key;
 let html='';if($('showPhysicsDots').checked){for(let i=0;i<=36;i++){const t=s.t*i/36;if(t>elapsed+1e-9)break;const p=samplePath(s.path,t);html+=`<circle data-physical-dot="${t}" cx="${releaseX+p.x*620}" cy="${floor-p.y*620}" r="${2.1/scale}" fill="#396f8d" opacity=".48"/>`}}
 if(compare){const points=[];for(let i=0;i<=80;i++){const p=ideal.at(ideal.time*i/80);points.push(`${i?'L':'M'} ${releaseX+p.x*620} ${floor-Math.max(0,p.y)*620}`)}html+=`<path id="ideal-parabola" d="${points.join(' ')}" fill="none" stroke="#aa7d28" stroke-width="${1.5/scale}" stroke-dasharray="${6/scale} ${6/scale}"/>`}
 host.innerHTML=html;
}
const physicalBaseDraw=draw;draw=function(...args){physicalBaseDraw(...args);renderPhysicalOverlay()};
for(const id of ['showPhysicsDots','showVacuum'])$(id).onchange=()=>{if(id==='showVacuum'&&$(id).checked)$('physicsReadouts').open=true;draw(currentViewProgress,currentViewShot,currentBounceTime)};
const snapshotButton=document.createElement('button');snapshotButton.id='saveRigSnapshot';snapshotButton.type='button';snapshotButton.textContent='保存实验包';snapshotButton.title='保留实际设置与原始精度距离，供 DOE 继续分析';
snapshotButton.onclick=()=>{const data=catExportExperiment();if(!data.rows.length)return toast('先完成发射或创建实验计划，再保存实验包。');const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='Catapult_实验快照.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
document.querySelector('.rig-actions').append(snapshotButton);draw(currentViewProgress,currentViewShot,currentBounceTime);
