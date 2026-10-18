#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path.home() / 'storage/downloads/ゲーム/BINGO-TOOL'
html = root / 'index.html'
cssfile = root / 'css/style.css'
jsfile = root / 'js/script.js'
if not html.is_file():
    sys.exit('エラー: BINGO-TOOL/index.html がありません')

style = r'''
/* BINGO-TOOL: 抽選機の軽量演出 */
.ball.is-rolling { animation:bingo-rattle .13s linear infinite alternate; }
.ball.is-settling { animation:bingo-settle .22s ease-out; }
@keyframes bingo-rattle {
  from {transform:translate(-3px,1px) rotate(-3deg);filter:brightness(1.08)}
  to {transform:translate(3px,-2px) rotate(3deg);filter:brightness(.96)}
}
@keyframes bingo-settle {
  0%{transform:translateY(-13px) scale(1.06)}
  60%{transform:translateY(3px) scale(.97)}
  100%{transform:translateY(0) scale(1)}
}
@media (prefers-reduced-motion: reduce) {
  .ball.is-rolling,.ball.is-settling {animation:none}
}
'''
logic = r'''
// 画像・音声ファイル不要: Web Audio APIで「ガラガラ…コンッ、コンッ」を合成
let bingoAudioContext;
function bingoSound() {
  try {
    const AudioClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioClass) return;
    if (!bingoAudioContext) bingoAudioContext = new AudioClass();
    const ctx = bingoAudioContext;
    if (ctx.state === 'suspended') ctx.resume().catch(()=>{});
    const start = ctx.currentTime + .02;
    const len = Math.floor(ctx.sampleRate * 1.0);
    const noise = ctx.createBuffer(1, len, ctx.sampleRate);
    const data = noise.getChannelData(0);
    for(let i=0;i<len;i++) data[i]=(Math.random()*2-1)*.30;
    const src=ctx.createBufferSource();src.buffer=noise;
    const filter=ctx.createBiquadFilter();filter.type='bandpass';filter.frequency.value=420;filter.Q.value=.7;
    const gain=ctx.createGain();gain.gain.setValueAtTime(.001,start);
    gain.gain.linearRampToValueAtTime(.17,start+.10);
    gain.gain.setValueAtTime(.17,start+.70);
    gain.gain.exponentialRampToValueAtTime(.001,start+1.0);
    src.connect(filter);filter.connect(gain);gain.connect(ctx.destination);
    src.start(start);src.stop(start+1.0);
    function knock(at, pitch, volume){
      const osc=ctx.createOscillator(), g=ctx.createGain();
      osc.type='sine';osc.frequency.setValueAtTime(pitch,at);
      osc.frequency.exponentialRampToValueAtTime(pitch*.52,at+.09);
      g.gain.setValueAtTime(volume,at);
      g.gain.exponentialRampToValueAtTime(.001,at+.12);
      osc.connect(g);g.connect(ctx.destination);osc.start(at);osc.stop(at+.13);
    }
    knock(start+1.02,230,.18);
    knock(start+1.29,180,.22);
    knock(start+1.50,140,.30);
  } catch(e) { /* 音が使えなくても抽選は続行 */ }
}
let bingoBusy=false;
function bingoDrawWithEffect(){
  if(bingoBusy || drawn.length===max) return;
  bingoBusy=true;
  const drawButton=$('draw'), applyButton=$('apply'), clearButton=$('clear'), ball=$('ball');
  drawButton.disabled=true;applyButton.disabled=true;clearButton.disabled=true;
  $('message').textContent='ガラガラ…';
  ball.classList.remove('empty','is-settling');
  ball.classList.add('is-rolling');
  bingoSound();
  const used=new Set(drawn), remain=[];
  for(let i=1;i<=max;i++) if(!used.has(i)) remain.push(i);
  // 開始時に当選番号を決定。演出中の数字は見た目だけ。
  const winner=remain[randBelow(remain.length)];
  let startTime=null, lastTick=-100;
  function animate(now){
    if(startTime===null)startTime=now;
    const elapsed=now-startTime;
    if(elapsed<1580){
      if(elapsed-lastTick> (elapsed<850?65:150)){
        ball.textContent=remain[Math.floor(Math.random()*remain.length)];
        lastTick=elapsed;
      }
      requestAnimationFrame(animate);
    }else{
      drawn.push(winner);save();render();
      ball.classList.remove('is-rolling');
      ball.classList.add('is-settling');
      $('message').textContent='';
      bingoBusy=false;
      applyButton.disabled=false;clearButton.disabled=false;
      setTimeout(()=>ball.classList.remove('is-settling'),260);
    }
  }
  requestAnimationFrame(animate);
}
'''
original = "$('draw').addEventListener('click',()=>{if(drawn.length===max)return;const used=new Set(drawn),remain=[];for(let i=1;i<=max;i++)if(!used.has(i))remain.push(i);drawn.push(remain[randBelow(remain.length)]);$('message').textContent='';save();render()});"
replacement = "$('draw').addEventListener('click',bingoDrawWithEffect);"
if jsfile.is_file() and 'src="js/script.js"' in html.read_text(encoding='utf-8'):
    js_target=jsfile
else:
    js_target=html
if cssfile.is_file() and 'href="css/style.css"' in html.read_text(encoding='utf-8'):
    css_target=cssfile
else:
    css_target=html

js=js_target.read_text(encoding='utf-8')
if 'bingoDrawWithEffect' in js:
    sys.exit('既に演出を導入済みです。変更していません。')
if original not in js:
    sys.exit('エラー: 抽選処理の構造が想定と違います。変更は行いません。')
css=css_target.read_text(encoding='utf-8')
if css_target==html:
    if '</style>' not in css:
        sys.exit('エラー: styleタグがありません。変更は行いません。')
    css=css.replace('</style>',style+'\n</style>',1)
else:
    css += '\n'+style
js=js.replace(original,logic+'\n'+replacement,1)
if js_target==css_target:
    js=css.replace(original,logic+'\n'+replacement,1)
    js_target.with_suffix('.html.bak').write_text(js_target.read_text(encoding='utf-8'),encoding='utf-8')
    js_target.write_text(js,encoding='utf-8')
else:
    for target,newdata in [(css_target,css),(js_target,js)]:
        target.with_name(target.name+'.bak').write_text(target.read_text(encoding='utf-8'),encoding='utf-8')
        target.write_text(newdata,encoding='utf-8')
print('BINGO-TOOL: ガラガラ・コンコン演出を導入しました')
print('変更内容を確認後、uploadbingo でアップロードしてください。')
