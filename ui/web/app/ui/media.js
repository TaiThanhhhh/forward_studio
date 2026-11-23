// Media: Player (video + transport kiểu NLE), Waveform (canvas từ file audio), Timeline (lane video/chữ/VO/nhạc/SFX).
import { h, clear } from '../core/dom.js';
import { icon } from '../core/icons.js';
import * as keys from '../core/keys.js';
import { tc } from '../core/format.js';
import { Btn } from './kit.js';

const FPS = 30;

/** Player: { el, video, seek(t), t(), setMarkers([{t, done}]), inOut, onTime(fn) }. Phím (đăng ký theo trang):
 *  Space play/pause · J/K/L lùi/dừng/tiến (bấm lặp = nhanh hơn) · ←/→ 1 frame · Shift+←/→ 10 frame · I/O điểm vào/ra. */
export function Player(src, { ink = false, registerKeys = true } = {}) {
  const video = h('video', { src, preload: 'auto', playsinline: true, 'aria-label': 'Video' });
  const canvas = ink ? h('canvas.ink', { 'aria-hidden': 'true' }) : null;
  const stage = h('div.player.grow', video, canvas);
  const tcEl = h('span.tc.mono', tc(0));
  const durEl = h('span.mono.dim', tc(0));
  const fill = h('div.fill');
  const marksEl = h('div');
  const ioEl = h('div.io', { hidden: true });
  const scrub = h('div.scrub', { role: 'slider', tabindex: 0, 'aria-label': 'Vị trí phát', 'aria-valuemin': 0, 'aria-valuemax': 0, 'aria-valuenow': 0 }, h('div.rail'), ioEl, fill, marksEl);
  const playBtn = Btn('', { kind: 'ghost', ico: 'play', title: 'Phát / dừng (Space)', onClick: () => toggle() });
  const transport = h('div.transport', playBtn, Btn('', { kind: 'ghost', ico: 'rewind', title: 'Lùi 1 frame (←)', onClick: () => step(-1) }),
    Btn('', { kind: 'ghost', ico: 'forward', title: 'Tiến 1 frame (→)', onClick: () => step(1) }), tcEl, scrub, durEl);
  const el = h('div.col.grow', { style: { gap: 0, minHeight: 0 } }, stage, transport);
  const st = { rate: 0, inT: null, outT: null, listeners: [], marks: [] };
  const dur = () => (Number.isFinite(video.duration) ? video.duration : 0);
  const seek = (t) => { video.currentTime = Math.max(0, Math.min(dur() || 0, t)); };
  const step = (n) => { video.pause(); st.rate = 0; seek(Math.round(video.currentTime * FPS + n) / FPS); };
  const toggle = () => { if (video.paused) { video.playbackRate = 1; video.play(); } else video.pause(); };
  const jkl = (dir) => {
    if (dir === 0) { video.pause(); st.rate = 0; return; }
    st.rate = Math.sign(st.rate) === dir ? Math.min(8, Math.abs(st.rate) * 2) * dir : dir;
    if (st.rate > 0) { video.playbackRate = st.rate; video.play(); } else {        // lùi: tua từng bước (trình duyệt không phát ngược)
      video.pause();
      const back = () => { if (st.rate >= 0) return; seek(video.currentTime + st.rate / FPS * 2); if (video.currentTime > 0) setTimeout(back, 1000 / FPS); };
      back();
    }
  };
  const draw = () => {
    const d = dur() || 1;
    fill.style.width = `${(video.currentTime / d) * 100}%`;
    tcEl.textContent = tc(video.currentTime);
    scrub.setAttribute('aria-valuenow', video.currentTime.toFixed(2));
    scrub.setAttribute('aria-valuetext', tc(video.currentTime));
    if (st.inT !== null || st.outT !== null) {
      const a = st.inT ?? 0, b = st.outT ?? d;
      Object.assign(ioEl.style, { left: `${(a / d) * 100}%`, width: `${Math.max(0, (b - a) / d) * 100}%` });
      ioEl.hidden = false;
    } else ioEl.hidden = true;
    if (st.outT !== null && video.currentTime >= st.outT && !video.paused) { video.pause(); seek(st.inT ?? 0); }
    for (const f of st.listeners) f(video.currentTime);
  };
  const drawMarks = () => {
    clear(marksEl);
    const d = dur() || 1;
    for (const m of st.marks) marksEl.append(h(`div.mark${m.done ? '.done' : ''}`, { style: { left: `${(m.t / d) * 100}%` }, title: tc(m.t) }));
  };
  video.addEventListener('timeupdate', draw);
  video.addEventListener('seeked', draw);
  video.addEventListener('loadedmetadata', () => { durEl.textContent = tc(dur()); scrub.setAttribute('aria-valuemax', dur().toFixed(2)); drawMarks(); draw(); fitInk(); });
  video.addEventListener('play', () => { clear(playBtn).append(icon('pause')); });
  video.addEventListener('pause', () => { clear(playBtn).append(icon('play')); });
  const fromX = (x) => { const r = scrub.getBoundingClientRect(); return ((x - r.left) / r.width) * (dur() || 0); };
  scrub.addEventListener('pointerdown', (e) => {
    scrub.setPointerCapture(e.pointerId); seek(fromX(e.clientX));
    const mv = (ev) => seek(fromX(ev.clientX));
    scrub.addEventListener('pointermove', mv);
    scrub.addEventListener('pointerup', () => scrub.removeEventListener('pointermove', mv), { once: true });
  });
  scrub.addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { step((e.key === 'ArrowRight' ? 1 : -1) * (e.shiftKey ? 10 : 1)); e.preventDefault(); e.stopPropagation(); } });
  // ---- lớp vẽ khoanh (Review)
  function fitInk() {
    if (!canvas) return;
    const vr = video.getBoundingClientRect(), sr = stage.getBoundingClientRect();
    Object.assign(canvas.style, { left: `${vr.left - sr.left}px`, top: `${vr.top - sr.top}px`, width: `${vr.width}px`, height: `${vr.height}px` });
    canvas.width = Math.round(vr.width); canvas.height = Math.round(vr.height);
    redraw();
  }
  let strokes = [], shown = [], drawing = false;
  const redraw = () => {
    if (!canvas) return;
    const g = canvas.getContext('2d');
    g.clearRect(0, 0, canvas.width, canvas.height);
    g.lineWidth = 3; g.lineCap = 'round'; g.lineJoin = 'round';
    const paint = (list, color) => { g.strokeStyle = color; for (const s of list) { g.beginPath(); s.forEach(([x, y], i) => (i ? g.lineTo(x * canvas.width, y * canvas.height) : g.moveTo(x * canvas.width, y * canvas.height))); g.stroke(); } };
    paint(shown, '#d6a01e');
    paint(strokes, '#f2554b');
  };
  if (canvas) {
    window.addEventListener('resize', fitInk);
    new ResizeObserver(fitInk).observe(stage);
    const pt = (e) => { const r = canvas.getBoundingClientRect(); return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; };
    canvas.addEventListener('pointerdown', (e) => { if (!canvas.classList.contains('on')) return; drawing = true; video.pause(); strokes.push([pt(e)]); canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', (e) => { if (drawing) { strokes[strokes.length - 1].push(pt(e)); redraw(); } });
    canvas.addEventListener('pointerup', () => { drawing = false; });
  }
  if (registerKeys) {
    keys.register('page', 'Space', () => toggle(), 'Phát / dừng', { group: 'Player' });
    keys.register('page', 'K', () => jkl(0), 'Dừng', { group: 'Player' });
    keys.register('page', 'L', () => jkl(1), 'Tiến (bấm lặp = nhanh ×2)', { group: 'Player' });
    keys.register('page', 'J', () => jkl(-1), 'Lùi (bấm lặp = nhanh ×2)', { group: 'Player' });
    keys.register('page', 'ArrowRight', () => step(1), 'Tiến 1 frame', { group: 'Player' });
    keys.register('page', 'ArrowLeft', () => step(-1), 'Lùi 1 frame', { group: 'Player' });
    keys.register('page', 'Shift+ArrowRight', () => step(10), 'Tiến 10 frame', { group: 'Player' });
    keys.register('page', 'Shift+ArrowLeft', () => step(-10), 'Lùi 10 frame', { group: 'Player' });
    keys.register('page', 'I', () => { st.inT = video.currentTime; draw(); }, 'Đặt điểm vào', { group: 'Player' });
    keys.register('page', 'O', () => { st.outT = video.currentTime; draw(); }, 'Đặt điểm ra', { group: 'Player' });
    keys.register('page', 'Alt+X', () => { st.inT = st.outT = null; draw(); }, 'Xoá điểm vào/ra', { group: 'Player' });
  }
  return {
    el, video, seek, step, toggle, t: () => video.currentTime, dur,
    setMarkers: (m) => { st.marks = m; drawMarks(); },
    onTime: (f) => st.listeners.push(f),
    inOut: () => ({ in: st.inT, out: st.outT }),
    ink: { on: (v) => canvas && canvas.classList.toggle('on', v), take: () => { const s = strokes; strokes = []; redraw(); return s; }, show: (s) => { shown = s || []; redraw(); }, clear: () => { strokes = []; redraw(); } },
    src: (u) => { video.src = u; },
  };
}

// ---------- waveform ----------
const decoded = new Map();
export async function peaks(url, buckets = 1200) {
  const k = `${url}|${buckets}`;
  if (decoded.has(k)) return decoded.get(k);
  const buf = await (await fetch(url)).arrayBuffer();
  const ctx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 2, 44100);
  const audio = await ctx.decodeAudioData(buf);
  const ch = audio.getChannelData(0);
  const step = Math.max(1, Math.floor(ch.length / buckets));
  const out = new Float32Array(buckets);
  for (let i = 0; i < buckets; i++) {
    let m = 0;
    for (let j = i * step, e = Math.min(ch.length, (i + 1) * step); j < e; j += 4) m = Math.max(m, Math.abs(ch[j]));
    out[i] = m;
  }
  const r = { peaks: out, duration: audio.duration };
  decoded.set(k, r);
  return r;
}

export function drawWave(canvas, data, { color = '#8a8a8a', from = 0, to = null } = {}) {
  const w = canvas.width = canvas.clientWidth * devicePixelRatio, hgt = canvas.height = canvas.clientHeight * devicePixelRatio;
  const g = canvas.getContext('2d');
  g.clearRect(0, 0, w, hgt);
  g.fillStyle = color;
  const end = to ?? data.duration;
  const n = data.peaks.length;
  for (let x = 0; x < w; x++) {
    const t = from + (x / w) * (end - from);
    const i = Math.floor((t / data.duration) * n);
    const v = i >= 0 && i < n ? data.peaks[i] : 0;
    const bh = Math.max(1, v * hgt * 0.9);
    g.fillRect(x, (hgt - bh) / 2, 1, bh);
  }
}

/** Waveform đơn có mốc từ (word timings) — trang Script. */
export function Waveform(url, { words = [], height = 64, onSeek } = {}) {
  const canvas = h('canvas.wave', { style: { width: '100%', height: `${height}px`, display: 'block', background: '#000', borderRadius: '2px' }, 'aria-hidden': 'true' });
  const wordsEl = h('div', { style: { position: 'relative', height: '18px', fontSize: '11px', overflow: 'hidden' } });
  const el = h('div', canvas, wordsEl);
  peaks(url).then((d) => {
    drawWave(canvas, d, { color: '#a8a8a8' });
    for (const w of words) {
      wordsEl.append(h('span.mono', { style: { position: 'absolute', left: `${(w.start / d.duration) * 100}%`, color: 'var(--t3)', whiteSpace: 'nowrap', cursor: 'pointer' },
        title: `${w.w} · ${w.start.toFixed(2)}s`, on: { click: () => onSeek && onSeek(w.start) } }, w.w));
    }
  }).catch(() => el.replaceChildren(h('span.dim', 'Không giải mã được audio.')));
  canvas.addEventListener('click', (e) => { const r = canvas.getBoundingClientRect(); onSeek && peaks(url).then((d) => onSeek(((e.clientX - r.left) / r.width) * d.duration)); });
  return el;
}

/** Timeline nhiều lane. lanes: [{name, kind:'clips'|'wave', items:[{id,start,end,label,cls}], url}]. */
export function Timeline({ duration, lanes, onSelect, selected = null, onSeek }) {
  const el = h('div.tl', { role: 'group', 'aria-label': 'Timeline' });
  const ruler = h('div.ruler');
  const tracks = [];
  const head = h('div.lane', { style: { height: '20px' } }, h('div.name', ''), h('div.track', ruler));
  el.append(head);
  const pct = (t) => `${(t / duration) * 100}%`;
  for (let s = 0; s <= duration; s += duration > 40 ? 5 : 2) ruler.append(h('span', { style: { left: pct(s) } }, `${s}s`));
  for (const lane of lanes) {
    const track = h('div.track');
    const row = h(`div.lane${lane.kind === 'wave' ? '.tall' : ''}`, h('div.name', lane.name), track);
    if (lane.kind === 'wave' && lane.url) {
      const cv = h('canvas.wave');
      track.append(cv);
      peaks(lane.url, 2000).then((d) => drawWave(cv, d, { color: lane.color || '#6f6f6f', from: 0, to: duration })).catch(() => {});
    }
    for (const it of lane.items || []) {
      track.append(h(`div.clip${it.cls ? '.' + it.cls : ''}`, { style: { left: pct(it.start), width: pct(Math.max(0.05, it.end - it.start)) }, title: it.title || it.label,
        tabindex: lane.selectable ? 0 : -1, role: lane.selectable ? 'button' : null, 'aria-pressed': lane.selectable ? String(selected === it.id) : null, dataset: { id: it.id },
        on: { click: (e) => { e.stopPropagation(); if (lane.selectable && onSelect) onSelect(it.id); if (onSeek) onSeek(it.start); }, keydown: (e) => { if (e.key === 'Enter' && onSelect) onSelect(it.id); } } }, it.label));
    }
    tracks.push(track);
    el.append(row);
  }
  const playhead = h('div.playhead');
  el.append(playhead);
  el.addEventListener('click', (e) => {
    const r = tracks[0] ? tracks[0].getBoundingClientRect() : el.getBoundingClientRect();
    if (e.clientX < r.left) return;
    onSeek && onSeek(((e.clientX - r.left) / r.width) * duration);
  });
  return Object.assign(el, {
    at: (t) => {
      const r = tracks[0] ? tracks[0].getBoundingClientRect() : null, base = el.getBoundingClientRect();
      if (!r) return;
      playhead.style.left = `${r.left - base.left + (t / duration) * r.width}px`;
    },
    select: (id) => el.querySelectorAll('.clip[role=button]').forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.id === id))),
  });
}
