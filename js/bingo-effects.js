/* 抽選の本体には触れず、ボタンのクリックを演出完了まで待機させる */
(() => {
  'use strict';
  const draw = document.getElementById('draw');
  const ball = document.getElementById('ball');
  if (!draw || !ball) return;
  let busy = false, replaying = false, audio;
  const DURATION = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 250 : 1650;
  function sound() {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      audio ||= new Ctx();
      if (audio.state === 'suspended') audio.resume().catch(() => {});
      const t = audio.currentTime + .02;
      const len = Math.round(audio.sampleRate * 1.1);
      const buf = audio.createBuffer(1, len, audio.sampleRate);
      const data = buf.getChannelData(0);
      for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
      const noise = audio.createBufferSource(); noise.buffer = buf;
      const low = audio.createBiquadFilter(); low.type = 'bandpass'; low.frequency.value = 430; low.Q.value = .65;
      const vol = audio.createGain();
      vol.gain.setValueAtTime(.001,t);
      vol.gain.linearRampToValueAtTime(.055,t+.13);
      vol.gain.setValueAtTime(.055,t+.75);
      vol.gain.exponentialRampToValueAtTime(.001,t+1.08);
      noise.connect(low); low.connect(vol); vol.connect(audio.destination);
      noise.start(t); noise.stop(t+1.1);
      for (const [offset, pitch, gainValue] of [[1.10,215,.12],[1.34,175,.16],[1.54,135,.20]]) {
        const osc = audio.createOscillator(), gain = audio.createGain();
        osc.type = 'sine'; osc.frequency.setValueAtTime(pitch,t+offset);
        osc.frequency.exponentialRampToValueAtTime(pitch*.55,t+offset+.11);
        gain.gain.setValueAtTime(gainValue,t+offset);
        gain.gain.exponentialRampToValueAtTime(.001,t+offset+.14);
        osc.connect(gain); gain.connect(audio.destination);
        osc.start(t+offset); osc.stop(t+offset+.15);
      }
    } catch (_) { /* ブラウザが音声を拒否しても抽選は続ける */ }
  }
  // capture: 元の抽選処理を起動する前に演出する。
  document.addEventListener('click', (event) => {
    if (event.target !== draw && !draw.contains(event.target)) return;
    if (replaying) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (busy || draw.disabled) return;
    busy = true;
    const previous = ball.textContent;
    const previousDisabled = draw.disabled;
    draw.disabled = true;
    ball.classList.remove('bingo-landed');
    ball.classList.add('bingo-rolling');
    sound();
    const started = performance.now();
    let lastChange = 0;
    function tick(now) {
      const elapsed = now - started;
      if (elapsed < DURATION) {
        if (elapsed-lastChange >= (elapsed < 950 ? 70 : 145)) {
          const limitField = document.getElementById('maximum');
          const max = Math.max(1, Math.min(9999, Number(limitField?.value) || 75));
          ball.textContent = String(1 + Math.floor(Math.random() * max));
          lastChange = elapsed;
        }
        requestAnimationFrame(tick);
        return;
      }
      ball.textContent = previous;
      ball.classList.remove('bingo-rolling');
      draw.disabled = previousDisabled;
      replaying = true;
      try { draw.click(); } finally { replaying = false; busy = false; }
      ball.classList.add('bingo-landed');
      setTimeout(() => ball.classList.remove('bingo-landed'), 250);
    }
    requestAnimationFrame(tick);
  }, true);
})();
