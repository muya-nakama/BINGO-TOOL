(()=>{'use strict';
const key='bingo-draw-v1', $=id=>document.getElementById(id);
const drum=$('drum'), crank=document.querySelector('.crank'), ball=$('ball');
let max=75,drawn=[],busy=false,muted=false;
try{muted=localStorage.getItem('bingo-muted')==='1';}catch{}
try{const saved=JSON.parse(localStorage.getItem(key));if(saved&&Number.isInteger(saved.max)&&saved.max>=1&&saved.max<=9999&&Array.isArray(saved.drawn)&&saved.drawn.every(n=>Number.isInteger(n)&&n>=1&&n<=saved.max)&&new Set(saved.drawn).size===saved.drawn.length){max=saved.max;drawn=saved.drawn;}}catch{}
function save(){try{localStorage.setItem(key,JSON.stringify({max,drawn}));}catch{}}
const playingSounds=new Set();
function stopSounds(){for(const a of playingSounds){a.pause();a.currentTime=0;}playingSounds.clear();}
function sound(kind){if(muted)return null;try{const uri=window.BINGO_SOUNDS?.[kind];if(!uri)return null;const a=new Audio(uri);a.volume=kind==='spin'?.72:.85;playingSounds.add(a);a.addEventListener('ended',()=>playingSounds.delete(a),{once:true});a.play().catch(()=>playingSounds.delete(a));return a;}catch{return null;}}
function updateMute(){$('mute').textContent=muted?'音 OFF':'音 ON';$('mute').setAttribute('aria-pressed',String(muted));}
function render(){const last=drawn.at(-1);$('maximum').value=max;ball.textContent=last??'?';ball.classList.toggle('empty',last===undefined);const remaining=max-drawn.length;$('status').textContent=remaining===0?'すべて抽選完了！':last===undefined?'次の番号は？':'抽選された番号';$('draw').disabled=busy||remaining===0;$('draw').textContent=remaining===0?'抽選完了':'抽選する';$('counter').textContent=`抽選済み ${drawn.length} / ${max} ・ 残り ${remaining}`;$('count').textContent=`(${drawn.length})`;$('bar').style.width=(drawn.length/max*100)+'%';$('progress').setAttribute('aria-valuemax',String(max));$('progress').setAttribute('aria-valuenow',String(drawn.length));const parent=$('history');parent.replaceChildren();if(!drawn.length){const p=document.createElement('p');p.textContent='まだ抽選されていません。';parent.append(p);}else{const fragment=document.createDocumentFragment();for(const n of [...drawn].reverse()){const chip=document.createElement('span');chip.className='chip';chip.textContent=n;fragment.append(chip);}parent.append(fragment);}}

let drumFrame=0;
function drumPose(degrees){
 const angle=(-67.5+degrees)*Math.PI/180;
 const vertices=Array.from({length:8},(_,i)=>[245+Math.cos(angle+i*Math.PI/4)*141,176+Math.sin(angle+i*Math.PI/4)*141]);
 const points=vertices.map(p=>p.join(',')).join(' ');
 $('face-mask').setAttribute('points',points);$('face-outline').setAttribute('points',points);
 $('face-inset').setAttribute('points',vertices.map(([x,y])=>[245+(x-245)*135/141,176+(y-176)*135/141].join(',')).join(' '));
 $('face-grain').setAttribute('transform',`rotate(${degrees} 245 176)`);
 const project=([x,y])=>[.92*x+17,.08*x+.96*y-5];
 document.querySelectorAll('[data-facet]').forEach((node,i)=>{
  const a=project(vertices[i]),b=project(vertices[(i+1)%8]);
  node.setAttribute('points',[a,b,[b[0]+62,b[1]-28],[a[0]+62,a[1]-28]].map(p=>p.join(',')).join(' '));
 });
 // Keep the outlet inside the same side panel; the front face occludes it when the panel turns away.
 const a=project(vertices[2]),b=project(vertices[3]);
 const panel=[a,b,[b[0]+62,b[1]-28],[a[0]+62,a[1]-28]];
 $('outlet-panel-mask').setAttribute('points',panel.map(p=>p.join(',')).join(' '));
 const x=(a[0]+b[0])/2+31,y=(a[1]+b[1])/2-14;
 $('outlet').setAttribute('cx',x);$('outlet').setAttribute('cy',y);

}
function ballFrames(){
 const svg=document.querySelector('.lottery-machine');
 const matrix=svg.getScreenCTM?.();
 const bounds=ball.getBoundingClientRect();
 const holeX=Number($('outlet').getAttribute('cx')),holeY=Number($('outlet').getAttribute('cy'));
 const point=(x,y)=>matrix?[matrix.a*x+matrix.c*y+matrix.e-bounds.left-bounds.width/2,matrix.b*x+matrix.d*y+matrix.f-bounds.top-bounds.height/2]:[78+(x-377)*.7,-104+(y-263)*.7];
 const transform=(x,y,scale)=>{const p=point(x,y);return `translate(${p[0]}px,${p[1]}px) scale(${scale})`;};
 return [{transform:transform(holeX,holeY,.16),opacity:0},{transform:transform(384,340,.19),opacity:1,offset:.27},{transform:transform(365,350,.32),opacity:1,offset:.48},{transform:'translate(0,3px) scale(1.04)',opacity:1,offset:.88},{transform:'translate(0,0) scale(1)',opacity:1}];
}
function startDrum(duration){
 const start=performance.now();
 function frame(now){const progress=Math.min(1,(now-start)/duration);const eased=1-Math.pow(1-progress,1.55);drumPose(eased*1080);if(progress<1)drumFrame=requestAnimationFrame(frame);}
 drumFrame=requestAnimationFrame(frame);
}
function stopDrum(){cancelAnimationFrame(drumFrame);drumPose(0);}

function randBelow(n){const data=new Uint32Array(1);const limit=Math.floor(4294967296/n)*n;do{crypto.getRandomValues(data)}while(data[0]>=limit);return data[0]%n;}
function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms));}
function lock(state){busy=state;$('apply').disabled=state;$('clear').disabled=state;$('maximum').disabled=state;$('draw').disabled=state;}
$('draw').addEventListener('click',async()=>{if(busy||drawn.length===max)return;lock(true);const used=new Set(drawn),remain=[];for(let n=1;n<=max;n++)if(!used.has(n))remain.push(n);const picked=remain[randBelow(remain.length)];$('message').textContent='ガラガラ…';ball.style.opacity='0';const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;const duration=reduced?450:1800;if(!reduced){startDrum(duration);crank.classList.add('spinning');}const spinning=sound('spin');await sleep(duration);stopDrum();crank.classList.remove('spinning');if(spinning){spinning.pause();spinning.currentTime=0;playingSounds.delete(spinning);}sound('drop');$('message').textContent='玉を取り出しています…';ball.textContent='';ball.classList.remove('empty');ball.style.opacity='1';if(ball.animate){const animation=ball.animate(ballFrames(),{duration:reduced?100:850,easing:'cubic-bezier(.22,.8,.25,1)'});await animation.finished.catch(()=>{});}else await sleep(650);drawn.push(picked);save();lock(false);$('message').textContent='';render();});
$('apply').addEventListener('click',()=>{if(busy)return;const raw=$('maximum').value.trim(),next=Number(raw);if(!raw||!Number.isInteger(next)||next<1||next>9999){$('message').textContent='最大値は1〜9999の整数で入力してね。';$('maximum').value=max;return;}if(next===max){$('message').textContent='現在の最大値と同じです。';return;}if(drawn.length&&!confirm('最大値を変更すると、現在の抽選履歴がすべて消えます。変更しますか？')){$('maximum').value=max;return;}max=next;drawn=[];$('message').textContent='最大値を設定しました。';save();render();});
$('clear').addEventListener('click',()=>{if(busy)return;if(!drawn.length){$('message').textContent='クリアする履歴はありません。';return;}if(!confirm('抽選履歴と除外番号をすべてクリアしますか？'))return;drawn=[];$('message').textContent='履歴をクリアしました。';save();render();});
$('mute').addEventListener('click',()=>{muted=!muted;if(muted)stopSounds();try{localStorage.setItem('bingo-muted',muted?'1':'0');}catch{}updateMute();});
$('maximum').addEventListener('keydown',event=>{if(event.key==='Enter')$('apply').click();});drumPose(0);updateMute();render();
})();
