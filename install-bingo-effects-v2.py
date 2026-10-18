#!/usr/bin/env python3
from pathlib import Path
import re,sys
root=Path.home()/'storage/downloads/ゲーム/BINGO-TOOL'
html=root/'index.html'
if not html.is_file(): sys.exit('エラー: index.html がありません')
page=html.read_text(encoding='utf-8')
jsfile=root/'js/script.js'
cssfile=root/'css/style.css'
js_target=jsfile if jsfile.is_file() and 'src="js/script.js"' in page else html
css_target=cssfile if cssfile.is_file() and 'href="css/style.css"' in page else html
js=js_target.read_text(encoding='utf-8')
css=css_target.read_text(encoding='utf-8')
if 'bingoDrawWithEffect' in js: sys.exit('演出は既に導入済みです。')
if not all(x in js for x in ['randBelow','drawn','render()','save()']):
 sys.exit('エラー: 抽選処理が確認できません。変更なし')
if not re.search(r"\$\(['\"]draw['\"]\)\.addEventListener\(['\"]click['\"]",js):
 sys.exit('エラー: 抽選ボタンの処理が確認できません。変更なし')
# Add the new handler inside the existing closure, without matching exact old source.
ends=list(re.finditer(r'\}\)\(\);',js))
if not ends: sys.exit('エラー: JavaScript終端が見つかりません。変更なし')
idx=ends[-1].start()
newjs=js[:idx]+ '\n'+"\n// 画像・音声ファイル不要: Web Audio APIで「ガラガラ…コンッ、コンッ」を合成\nlet bingoAudioContext;\nfunction bingoSound() {\n  try {\n    const AudioClass = window.AudioContext || window.webkitAudioContext;\n    if (!AudioClass) return;\n    if (!bingoAudioContext) bingoAudioContext = new AudioClass();\n    const ctx = bingoAudioContext;\n    if (ctx.state === 'suspended') ctx.resume().catch(()=>{});\n    const start = ctx.currentTime + .02;\n    const len = Math.floor(ctx.sampleRate * 1.0);\n    const noise = ctx.createBuffer(1, len, ctx.sampleRate);\n    const data = noise.getChannelData(0);\n    for(let i=0;i<len;i++) data[i]=(Math.random()*2-1)*.30;\n    const src=ctx.createBufferSource();src.buffer=noise;\n    const filter=ctx.createBiquadFilter();filter.type='bandpass';filter.frequency.value=420;filter.Q.value=.7;\n    const gain=ctx.createGain();gain.gain.setValueAtTime(.001,start);\n    gain.gain.linearRampToValueAtTime(.17,start+.10);\n    gain.gain.setValueAtTime(.17,start+.70);\n    gain.gain.exponentialRampToValueAtTime(.001,start+1.0);\n    src.connect(filter);filter.connect(gain);gain.connect(ctx.destination);\n    src.start(start);src.stop(start+1.0);\n    function knock(at, pitch, volume){\n      const osc=ctx.createOscillator(), g=ctx.createGain();\n      osc.type='sine';osc.frequency.setValueAtTime(pitch,at);\n      osc.frequency.exponentialRampToValueAtTime(pitch*.52,at+.09);\n      g.gain.setValueAtTime(volume,at);\n      g.gain.exponentialRampToValueAtTime(.001,at+.12);\n      osc.connect(g);g.connect(ctx.destination);osc.start(at);osc.stop(at+.13);\n    }\n    knock(start+1.02,230,.18);\n    knock(start+1.29,180,.22);\n    knock(start+1.50,140,.30);\n  } catch(e) { /* 音が使えなくても抽選は続行 */ }\n}\nlet bingoBusy=false;\nfunction bingoDrawWithEffect(){\n  if(bingoBusy || drawn.length===max) return;\n  bingoBusy=true;\n  const drawButton=$('draw'), applyButton=$('apply'), clearButton=$('clear'), ball=$('ball');\n  drawButton.disabled=true;applyButton.disabled=true;clearButton.disabled=true;\n  $('message').textContent='ガラガラ…';\n  ball.classList.remove('empty','is-settling');\n  ball.classList.add('is-rolling');\n  bingoSound();\n  const used=new Set(drawn), remain=[];\n  for(let i=1;i<=max;i++) if(!used.has(i)) remain.push(i);\n  // 開始時に当選番号を決定。演出中の数字は見た目だけ。\n  const winner=remain[randBelow(remain.length)];\n  let startTime=null, lastTick=-100;\n  function animate(now){\n    if(startTime===null)startTime=now;\n    const elapsed=now-startTime;\n    if(elapsed<1580){\n      if(elapsed-lastTick> (elapsed<850?65:150)){\n        ball.textContent=remain[Math.floor(Math.random()*remain.length)];\n        lastTick=elapsed;\n      }\n      requestAnimationFrame(animate);\n    }else{\n      drawn.push(winner);save();render();\n      ball.classList.remove('is-rolling');\n      ball.classList.add('is-settling');\n      $('message').textContent='';\n      bingoBusy=false;\n      applyButton.disabled=false;clearButton.disabled=false;\n      setTimeout(()=>ball.classList.remove('is-settling'),260);\n    }\n  }\n  requestAnimationFrame(animate);\n}\n\n$('draw').addEventListener('click', function(e){ e.stopImmediatePropagation(); bingoDrawWithEffect(); }, true);\n"+'\n'+js[idx:]
if css_target==html:
 if '</style>' not in css: sys.exit('エラー: CSSタグなし。変更なし')
 newcss=css.replace('</style>','\n/* BINGO-TOOL: 抽選機の軽量演出 */\n.ball.is-rolling { animation:bingo-rattle .13s linear infinite alternate; }\n.ball.is-settling { animation:bingo-settle .22s ease-out; }\n@keyframes bingo-rattle {\n  from {transform:translate(-3px,1px) rotate(-3deg);filter:brightness(1.08)}\n  to {transform:translate(3px,-2px) rotate(3deg);filter:brightness(.96)}\n}\n@keyframes bingo-settle {\n  0%{transform:translateY(-13px) scale(1.06)}\n  60%{transform:translateY(3px) scale(.97)}\n  100%{transform:translateY(0) scale(1)}\n}\n@media (prefers-reduced-motion: reduce) {\n  .ball.is-rolling,.ball.is-settling {animation:none}\n}\n'+'\n</style>',1)
else: newcss=css+'\n'+'\n/* BINGO-TOOL: 抽選機の軽量演出 */\n.ball.is-rolling { animation:bingo-rattle .13s linear infinite alternate; }\n.ball.is-settling { animation:bingo-settle .22s ease-out; }\n@keyframes bingo-rattle {\n  from {transform:translate(-3px,1px) rotate(-3deg);filter:brightness(1.08)}\n  to {transform:translate(3px,-2px) rotate(3deg);filter:brightness(.96)}\n}\n@keyframes bingo-settle {\n  0%{transform:translateY(-13px) scale(1.06)}\n  60%{transform:translateY(3px) scale(.97)}\n  100%{transform:translateY(0) scale(1)}\n}\n@media (prefers-reduced-motion: reduce) {\n  .ball.is-rolling,.ball.is-settling {animation:none}\n}\n'
if js_target==css_target:
 newjs=newjs.replace('</style>','\n/* BINGO-TOOL: 抽選機の軽量演出 */\n.ball.is-rolling { animation:bingo-rattle .13s linear infinite alternate; }\n.ball.is-settling { animation:bingo-settle .22s ease-out; }\n@keyframes bingo-rattle {\n  from {transform:translate(-3px,1px) rotate(-3deg);filter:brightness(1.08)}\n  to {transform:translate(3px,-2px) rotate(3deg);filter:brightness(.96)}\n}\n@keyframes bingo-settle {\n  0%{transform:translateY(-13px) scale(1.06)}\n  60%{transform:translateY(3px) scale(.97)}\n  100%{transform:translateY(0) scale(1)}\n}\n@media (prefers-reduced-motion: reduce) {\n  .ball.is-rolling,.ball.is-settling {animation:none}\n}\n'+'\n</style>',1)
 writes=[(js_target,newjs)]
else: writes=[(js_target,newjs),(css_target,newcss)]
for file,content in writes:
 backup_dir=Path.home()/'bingo-tool-backups'
 backup_dir.mkdir(exist_ok=True)
 backup=backup_dir/(file.parent.name+'-'+file.name+'.bak')
 if not backup.exists(): backup.write_text(file.read_text(encoding='utf-8'),encoding='utf-8')
 file.write_text(content,encoding='utf-8')
print('成功: 抽選のガラガラ・コンコン演出を追加しました。')
print('動作確認後に uploadbingo を実行してください。')
