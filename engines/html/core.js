// Engine `html` (vòng 7) — motion graphics Canvas 2D trên nền đen, engine thứ ba của `mode: code`.
// Cùng hợp đồng với engine three.js (vidlib/coderender.py): ?job=<url job.json> → window.ready, window.renderFrame(f),
// canvas #c, window.meta {cues, texts}, window.textBoxes(). Mọi frame là hàm thuần của f (render song song + RESUME).
//
// Ba tầng, tách dữ liệu khỏi máy vẽ:
//   look  (looks.js)  — "ngữ pháp phong cách": bút vẽ (pen), nền, kiểu chữ, luật nhịp. Token đến từ styles/<id>.json → html.
//   beat  (beats.js)  — "ngữ pháp giải thích": title, drop, counter, compare, graph, process, scale, callout, fact, outro.
//   icon  (icons.js)  — đạo cụ vẽ bằng primitive có vai màu (ink/hot/cold/accent/dim) để look nào cũng tô được.
// Không có nội dung video nào nằm trong mã: chữ, số, đạo cụ, mốc thời gian đều đến từ job.params (storyboard).
import * as MO from '../../lib/motion/motion.js';
import { ICONS, iconFor, partsIcon } from './icons.js';
import { LOOKS, mergeLook } from './looks.js';
import { BEATS, TOOLS } from './beats.js';
import { loadMedia } from './media.js';
import { rigPrims, isRig } from './rig2d.js';
import { makePost2D } from './post2d.js';

window.stage = 'job';
const qs = new URLSearchParams(location.search);
const JOB = await (await fetch(qs.get('job'), { cache: 'no-store' })).json();
const W = JOB.width || 1080, H = JOB.height || 1920, N = Math.max(1, JOB.frames | 0), FPS = JOB.fps || 30;
window.stage = 'fonts';
await Promise.all((JOB.fonts || []).map(async (f) => {
  const ff = new FontFace(f.family, `url(${f.url})`, f.weight ? { weight: f.weight } : {});
  await ff.load(); document.fonts.add(ff);
}));
window.stage = 'canvas';
const canvas = document.getElementById('c');
canvas.width = W; canvas.height = H;
const g = canvas.getContext('2d', { willReadFrequently: false });
const L = mergeLook(JOB.look || {});
const pal = L.palette;
const P = JOB.params || {};

// ---------- số ngẫu nhiên có hạt giống + easing ----------
export const hash = (a, b = 0, c = 0) => {
  let h = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263) + Math.imul(c | 0, 2147483647)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
};
const noise = (a, b = 0, c = 0) => hash(a, b, c) * 2 - 1;
const strSeed = (s) => { let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h | 0; };
const clamp = MO.clamp, lerp = MO.lerp;
const bez = (x1, y1, x2, y2) => (t) => {           // cubic-bezier(x1,y1,x2,y2) giải bằng chia đôi
  t = clamp(t); let a = 0, b = 1, u = t;
  for (let i = 0; i < 18; i++) { u = (a + b) / 2; const x = 3 * (1 - u) * (1 - u) * u * x1 + 3 * (1 - u) * u * u * x2 + u * u * u; if (x < t) a = u; else b = u; }
  return 3 * (1 - u) * (1 - u) * u * y1 + 3 * (1 - u) * u * u * y2 + u * u * u;
};
const EASE = {
  ...MO.M,                                            // bộ chung của lib/motion (bounceOut, elastic, steps…); tên riêng html ghi đè bên dưới
  snap: bez(0.7, 0, 0.2, 1),                          // chính xác như máy in: không vượt, không nảy
  bounce: (t) => MO.M.back(t, 1.56),                  // vượt rồi về (flat vector)
  expo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp(t))),
  smooth: MO.M.smooth, linear: MO.M.linear, out: MO.M.easeOut, in: MO.M.easeIn,
  spring: (t) => (t <= 0 ? 0 : t >= 1 ? 1 : 1 - Math.exp(-6 * t) * Math.cos(9 * t)),
  dead: (t) => 1 - Math.pow(1 - clamp(t), 2),         // trượt rồi "dừng chết" đúng nhịp
};
const E = EASE[L.motion.ease] || EASE.smooth;

// ---------- màu ----------
const hex = (h) => { const s = h.replace('#', ''); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16)); };
const mix = (a, b, t) => { const A = hex(a), B = hex(b); return '#' + A.map((v, i) => Math.round(lerp(v, B[i], t)).toString(16).padStart(2, '0')).join(''); };
const col = (role) => {
  if (!role) return pal.ink;
  if (role[0] === '#') return role;
  const r = (L.roles && L.roles[role]) || role;
  if (pal[r]) return pal[r];
  if (r === 'dim') return mix(pal.bg, pal.ink, 0.42);
  return pal.ink;
};
const shade = (c, t = 0.45) => mix(c, pal.bg, t);

// ---------- bút vẽ: primitive → polyline → vẽ theo look ----------
const TAU = Math.PI * 2;
function sample(p, seg) {
  const out = [];
  if (p.k === 'circle') {
    const rx = p.rx ?? p.r, ry = p.ry ?? p.r, cr = Math.cos(p.rot || 0), sr = Math.sin(p.rot || 0);   // rot: elip xoay (lá, cánh)
    for (let i = 0; i < seg; i++) {
      const a = i / seg * TAU - Math.PI / 2, ex = Math.cos(a) * rx, ey = Math.sin(a) * ry;
      out.push([p.x + ex * cr - ey * sr, p.y + ex * sr + ey * cr]);
    }
    return { pts: out, closed: true };
  }
  if (p.k === 'arc') {
    const n = Math.max(4, Math.round(seg * Math.abs(p.a1 - p.a0) / TAU));
    for (let i = 0; i <= n; i++) { const a = lerp(p.a0, p.a1, i / n); out.push([p.x + Math.cos(a) * (p.rx ?? p.r), p.y + Math.sin(a) * (p.ry ?? p.r)]); }
    return { pts: out, closed: false };
  }
  if (p.k === 'rect') {
    const r = Math.min(p.rad || 0, p.w / 2, p.h / 2), x = p.x, y = p.y, w = p.w, h = p.h;
    if (r <= 0) return { pts: [[x, y], [x + w, y], [x + w, y + h], [x, y + h]], closed: true };
    const cs = [[x + w - r, y + r, -Math.PI / 2], [x + w - r, y + h - r, 0], [x + r, y + h - r, Math.PI / 2], [x + r, y + r, Math.PI]];
    for (const [cx, cy, a0] of cs) for (let i = 0; i <= 5; i++) { const a = a0 + i / 5 * Math.PI / 2; out.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
    return { pts: out, closed: true };
  }
  return { pts: p.pts.map((q) => q.slice()), closed: p.k === 'poly' };
}
function subdivide(pts, closed, maxLen) {
  const out = [], n = pts.length;
  for (let i = 0; i < (closed ? n : n - 1); i++) {
    const a = pts[i], b = pts[(i + 1) % n], d = Math.hypot(b[0] - a[0], b[1] - a[1]), k = Math.max(1, Math.ceil(d / maxLen));
    for (let j = 0; j < k; j++) out.push([lerp(a[0], b[0], j / k), lerp(a[1], b[1], j / k)]);
  }
  if (!closed) out.push(pts[n - 1]);
  return out;
}
function truncate(pts, closed, k) {            // lấy phần đầu của nét theo tỉ lệ độ dài (vẽ dần)
  const src = closed ? pts.concat([pts[0]]) : pts;
  let total = 0; const seg = [];
  for (let i = 1; i < src.length; i++) { const d = Math.hypot(src[i][0] - src[i - 1][0], src[i][1] - src[i - 1][1]); seg.push(d); total += d; }
  let left = total * clamp(k); const out = [src[0]];
  for (let i = 1; i < src.length && left > 0; i++) {
    if (seg[i - 1] <= left) { out.push(src[i]); left -= seg[i - 1]; } else { const t = left / seg[i - 1]; out.push([lerp(src[i - 1][0], src[i][0], t), lerp(src[i - 1][1], src[i][1], t)]); left = 0; }
  }
  return out;
}
const pathOf = (pts, closed) => { const p = new Path2D(); pts.forEach((q, i) => (i ? p.lineTo(q[0], q[1]) : p.moveTo(q[0], q[1]))); if (closed) p.closePath(); return p; };

let cur = { f: 0, fs: 0, drawK: 1, kick: 0 };
// màu của một mảnh: vai → màu; tone (chân xa, mặt khuất của nhân vật rig) tối dần về nền
const colOf = (p) => (p.tone ? shade(col(p.role), p.tone) : col(p.role));
/** Look giới hạn màu mỗi vật (sprite 8-bit kiểu NES): giữ ≤ n màu kể cả đen, vai thừa → màu gần nhất đã giữ. */
function limitColors(prims, n) {
  const keep = [], dist = (a, b) => { const A = hex(a), B = hex(b); return (A[0] - B[0]) ** 2 + (A[1] - B[1]) ** 2 + (A[2] - B[2]) ** 2; };
  for (const p of prims) { const c = colOf(p); if (c !== pal.bg && !keep.includes(c) && keep.length < n - 1) keep.push(c); }
  return prims.map((p) => {
    const c = colOf(p); if (c === pal.bg || keep.includes(c) || !keep.length) return p;
    let best = keep[0]; for (const q of keep) if (dist(q, c) < dist(best, c)) best = q;
    return { ...p, role: best, tone: 0 };
  });
}
let paperTile = null;                                  // vân giấy (sợi + đốm) cho look cắt giấy — sinh một lần, tất định
function paperPattern() {
  if (paperTile) return paperTile;
  const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d'), d = x.createImageData(256, 256);
  for (let j = 0; j < 256; j++) for (let i = 0; i < 256; i++) {
    const fib = Math.sin(i * 0.11 + hash(j >> 3, 9) * 6) * 0.5 + 0.5, n = hash(i, j, 31) * 0.6 + hash(i >> 2, j >> 2, 32) * 0.4;
    const v = 255 - Math.round(38 * n + 14 * fib * hash(j, 4));
    const q = (j * 256 + i) * 4; d.data[q] = v; d.data[q + 1] = v - 3; d.data[q + 2] = v - 9; d.data[q + 3] = 255;
  }
  x.putImageData(d, 0, 0); paperTile = g.createPattern(c, 'repeat'); return paperTile;
}
/** Vẽ danh sách primitive (toạ độ đơn vị) tại (x,y) cỡ s px. o: {x,y,s,sx,sy,rot,seed,k,alpha,plain,z}
 *  Cờ của mảnh: fine (chi tiết nhỏ — chỉ tô, không viền/rung/bóng) · tone · pin (đinh khớp, chỉ look pen.pins) · alpha.
 *  o.z (chiều sâu, 0 = mặt phẳng chính) chỉ đổi độ lệch bóng giấy của look cắt giấy. */
function draw(prims, o = {}) {
  const st = L.pen, s = o.s ?? 100, sx = (o.sx ?? 1) * s, sy = (o.sy ?? 1) * s;
  const tick = Math.floor(cur.fs / (st.every || 2)), seed = o.seed ?? 1;
  let x0 = o.x ?? 0, y0 = o.y ?? 0, rot = o.rot || 0;
  if (st.nudge && !o.plain) {                         // stop-motion: mỗi lần chụp, mảnh bị đặt lại lệch một chút (tất định)
    x0 += noise(seed, tick, 41) * st.nudge[0]; y0 += noise(seed, tick, 43) * st.nudge[0]; rot += noise(seed, tick, 47) * (st.nudge[1] || 0);
  }
  if (!st.pins) prims = prims.filter((p) => !p.pin);
  if (st.limit) prims = limitColors(prims, st.limit);
  const cr = Math.cos(rot), sr = Math.sin(rot);
  const k = Math.min(o.k ?? 1, cur.drawK), partial = k < 1;
  const shapes = prims.map((p, pi) => {
    let { pts, closed } = sample(p, st.seg || 44);
    pts = pts.map(([px, py]) => { const X = px * sx, Y = py * sy; return [x0 + X * cr - Y * sr, y0 + X * sr + Y * cr]; });
    const wob = (st.boil || 0) + (st.jitter || 0);
    if (wob > 0 && !o.plain && !p.fine) {
      pts = subdivide(pts, closed, st.wobLen || 46);
      pts = pts.map(([px, py], i) => [
        px + noise(seed * 131 + pi, i, 7) * (st.jitter || 0) + noise(seed * 131 + pi, i, 100 + tick) * (st.boil || 0),
        py + noise(seed * 137 + pi, i, 9) * (st.jitter || 0) + noise(seed * 137 + pi, i, 200 + tick) * (st.boil || 0)]);
    }
    return { p, pts, closed, fillable: closed && p.fill !== false };
  });
  g.save();
  if (o.alpha !== undefined) g.globalAlpha *= o.alpha;
  g.lineJoin = st.join || 'round'; g.lineCap = st.cap || 'round';
  const lw = (p) => (p.k === 'rect' ? (p.sw || 1) : (p.w || 1)) * (st.stroke || st.line || 6) * (o.lw || 1);   // rect: w là chiều rộng
  const A0 = g.globalAlpha, al = (sh) => { g.globalAlpha = A0 * (sh.p.alpha ?? 1); };
  if (st.silhouette && !o.plain) {                   // rối bóng: mọi mảnh là bóng đen đặc, chỉ viền sáng mảnh ở mép ngoài vật
    const si = st.silhouette, rim = (si.rim ?? 2) * (o.lw || 1), rc = col(si.role || 'ink'), solid = shapes.filter((sh) => !sh.p.fine);
    g.strokeStyle = rc; g.fillStyle = rc;
    for (const sh of solid) { al(sh); const pa = pathOf(partial ? truncate(sh.pts, sh.closed, k) : sh.pts, sh.closed && !partial); g.lineWidth = (sh.fillable && !partial ? 0 : lw(sh.p)) + rim * 2; g.stroke(pa); }
    g.fillStyle = pal.bg; g.strokeStyle = pal.bg;
    for (const sh of solid) {
      al(sh); const pa = pathOf(partial ? truncate(sh.pts, sh.closed, k) : sh.pts, sh.closed && !partial);
      if (sh.fillable && !partial) g.fill(pa); else { g.lineWidth = lw(sh.p); g.stroke(pa); }
    }
    for (const sh of shapes) if (sh.p.fine && !partial && (sh.p.pin || (si.eyes && sh.p.role === 'ink'))) {   // đinh khớp kiểu rối + (tuỳ chọn) lỗ mắt khoét
      al(sh); g.fillStyle = rc; g.fill(pathOf(sh.pts, true));
    }
    g.restore();
    return;
  }
  const body = shapes.filter((sh) => !sh.p.fine);   // mảnh chính (chi tiết mặt nhỏ không có viền/bóng/nhãn dán)
  if (!partial && !o.plain) {
    if (st.sticker) {                                 // viền trắng dày + bóng: mọi mảnh thành "nhãn dán"
      g.save(); g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = 22; g.shadowOffsetY = 10;
      g.fillStyle = g.strokeStyle = col(st.stickerRole || 'ink'); g.lineWidth = st.sticker * 2;
      for (const sh of body) { const pa = pathOf(sh.pts, sh.closed); g.stroke(pa); if (sh.fillable) g.fill(pa); }
      g.restore();
    }
    if (st.shadow) {                                  // bóng giấy lệch, không nhoè
      g.fillStyle = st.shadow[2] ? col(st.shadow[2]) : shade(pal.ink, 0.86);
      for (const sh of body) if (sh.fillable) { g.save(); g.translate(st.shadow[0], st.shadow[1]); g.fill(pathOf(sh.pts, true)); g.restore(); }
    }
    if (st.cut && st.cut.shadow) {                    // cắt giấy: bóng mềm lệch theo độ sâu lớp (o.z) — chỉ thấy khi đè lên lớp giấy sáng hơn
      const [dx, dy, bl] = st.cut.shadow, zz = 1 + Math.max(-0.6, Math.min(3, o.z || 0)) * 0.6;
      g.save(); g.fillStyle = 'rgba(0,0,0,0.55)'; g.filter = `blur(${(bl * zz).toFixed(1)}px)`; g.translate(dx * zz, dy * zz);
      for (const sh of body) if (sh.fillable) g.fill(pathOf(sh.pts, true));
      g.restore();
    }
    if (st.slab) {                                    // độ dày 2.5D: chồng mặt cắt xuống dưới bằng màu tối hơn
      for (const sh of body) if (sh.fillable) {
        g.fillStyle = shade(colOf(sh.p), 0.5);
        for (let d = st.slab; d >= 2; d -= 2) { g.save(); g.translate(0, d); g.fill(pathOf(sh.pts, true)); g.restore(); }
      }
    }
  }
  for (const sh of shapes) {
    const c = colOf(sh.p), fine = !!sh.p.fine;
    const pts = partial ? truncate(sh.pts, sh.closed, k) : sh.pts;
    const pa = pathOf(pts, sh.closed && !partial);
    al(sh);
    if (fine && !partial) {                           // chi tiết nhỏ (mắt, miệng, đinh khớp): luôn tô đặc, look nét (không tô) dùng màu mực
      if (sh.fillable) { g.fillStyle = (!st.fill && sh.p.role === 'bg') ? col('ink') : c; g.fill(pa); }
      else { g.lineWidth = lw(sh.p); g.strokeStyle = c; g.stroke(pa); }
      continue;
    }
    if (sh.fillable && !partial) {
      if (st.cut && !o.plain) {                       // cắt giấy: lõi giấy trắng ở mép (viền sáng mảnh phía ngoài) → tô màu → vân giấy nhân
        g.save(); g.strokeStyle = mix(c, '#ffffff', 0.62); g.lineWidth = (st.cut.edge ?? 3) * 2; g.stroke(pa); g.restore();
      }
      if (st.fill) {
        g.fillStyle = sh.p.hole ? pal.bg : c;          // lỗ (SVG nhập): khoét bằng màu nền, viền vẫn màu vật
        if (st.misreg && !sh.p.hole) { g.save(); g.translate(st.misreg, st.misreg * 0.7); g.globalAlpha *= st.tint ?? 1; g.fill(pa); g.restore(); } else g.fill(pa);
        if (st.cel && !sh.p.hole && !o.plain) {      // tô khối kiểu sprite: mảng tối cùng tông phía dưới-phải (ánh sáng từ trên-trái)
          g.save(); g.clip(pa); g.fillStyle = shade(c, st.cel[2] ?? 0.45); g.fill(pa); g.translate(-st.cel[0], -st.cel[1]); g.fillStyle = c; g.fill(pa); g.restore();
        }
        if (st.cut && st.cut.grain && !sh.p.hole) {
          const pt = paperPattern(); pt.setTransform(new DOMMatrix().translateSelf(x0 + (seed % 97) * 3, y0 + (seed % 89) * 2).rotateSelf(rot * 57.3));
          g.save(); g.globalCompositeOperation = 'multiply'; g.globalAlpha *= st.cut.grain; g.fillStyle = pt; g.fill(pa); g.restore();
        }
      } else {
        g.fillStyle = pal.bg; g.fill(pa);             // che phần phía sau (nét không xuyên qua vật)
        if (st.tint && sh.p.role && sh.p.role !== 'ink' && !sh.p.hole) { g.save(); g.globalAlpha *= st.tint; g.fillStyle = c; g.fill(pa); g.restore(); }
      }
      if (st.hatch && (sh.p.shade || sh.p.role === 'dim')) {
        g.save(); g.clip(pa); g.strokeStyle = c; g.lineWidth = 2; g.beginPath();
        for (let d = -H; d < W + H; d += st.hatch) { g.moveTo(d, 0); g.lineTo(d - H * 0.6, H); }
        g.stroke(); g.restore();
      }
    }
    const stroked = !sh.fillable || st.stroke > 0 || partial;
    if (stroked) {
      g.save();
      g.lineWidth = lw(sh.p);
      // viền của mảnh tô: màu vai cố định (strokeRole) hoặc chính màu mảnh tối đi (strokeTone — kiểu "selout" của pixel art)
      g.strokeStyle = (st.fill && sh.fillable && st.strokeTone) ? shade(c, st.strokeTone) : (st.fill && sh.fillable && st.strokeRole) ? col(st.strokeRole) : c;
      if (sh.p.dash) g.setLineDash(sh.p.dash.map((d) => d * (st.stroke || st.line || 6)));
      if (st.glow) { g.shadowColor = c; g.shadowBlur = st.glow; g.stroke(pa); if (st.glow2) { g.shadowBlur = st.glow2; g.globalAlpha *= 0.55; } }
      g.stroke(pa); g.restore();
    }
  }
  g.restore();
}

// ---------- chữ ----------
let boxes = [], overlaps = [];
function boxOverlapRatio(a, b) {
  const iw = Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0]));
  const ih = Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  if (iw <= 0 || ih <= 0) return 0;
  const areaA = Math.max(0, a[2] - a[0]) * Math.max(0, a[3] - a[1]);
  const areaB = Math.max(0, b[2] - b[0]) * Math.max(0, b[3] - b[1]);
  return (iw * ih) / Math.max(1, Math.min(areaA, areaB));
}
const fontOf = (o) => `${o.weight || L.type.weight || 700} ${Math.round(o.size)}px "${o.font === 'mono' ? 'StyleMono' : 'StyleFont'}", sans-serif`;
const fmtNum = (v, dec = 0) => Number(v).toLocaleString(JOB.locale || 'en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
function wrap(str, o) {
  const out = [];
  for (const para of String(str).split('\n')) {
    let line = '';
    for (const w of para.split(/\s+/).filter(Boolean)) {
      const t = line ? line + ' ' + w : w;
      if (line && o.maxW && g.measureText(t).width > o.maxW) { out.push(line); line = w; } else line = t;
    }
    out.push(line);
  }
  return out;
}
/** Vẽ chữ. o: {size, role, align, font, weight, k, maxW, lh, upper, enter, rot, track, quiet, bare}. Trả về khung bao px. */
// Look có lớp vẽ lại cả khung (tranh chấm, halftone, pixel, truyện tranh): chữ + nhãn/bóng thoại vẽ SAU lớp đó (luôn sắc
// nét, OCR đọc được). Mỗi lệnh hoãn nhớ ma trận + alpha + quyền ghi khung OCR lúc gọi (ô hàng xóm của cú máy liền không ghi).
let deferred = [], replaying = false;
const defers = () => L.deferText && !replaying;
function later(fn) {                                  // vẽ một thứ (khung chú thích, bóng thoại) cùng lúc với chữ hoãn
  if (defers()) deferred.push({ m: g.getTransform(), a: g.globalAlpha, rec: recordBoxes, fn });
  else fn();
}
function text(str, x, y, o = {}) {
  if (defers() && (o.k ?? 1) > 0) {
    deferred.push({ m: g.getTransform(), a: g.globalAlpha, rec: recordBoxes, fn: () => textImpl(str, x, y, o) });
    return textImpl(str, x, y, { ...o, k: 0 });
  }
  return textImpl(str, x, y, o);
}
function replay() {
  replaying = true;
  const rb = recordBoxes;
  for (const d of deferred) { g.save(); g.setTransform(d.m); g.globalAlpha = d.a; recordBoxes = d.rec; d.fn(); g.restore(); }
  recordBoxes = rb; replaying = false; deferred = [];
}
// chữ pixel (font lưới: Press Start 2P = 8 điểm/em): cỡ chữ trên màn hình làm tròn về bội số của (em × type.px) và gốc chữ
// rơi đúng lưới type.px → mỗi điểm của font = đúng một khối pixel (không nhoè).
const pxSize = (size) => {
  const T = L.type; if (!T.px) return size;
  const m = g.getTransform(), sc = Math.hypot(m.a, m.b) || 1, unit = (T.pxEm || 8) * T.px;
  return Math.max(unit, Math.round(size * sc / unit) * unit) / sc;
};
const pxSnap = (x, y) => {
  const T = L.type; if (!T.px) return;
  const m = g.getTransform(), X = m.a * x + m.c * y + m.e, Y = m.b * x + m.d * y + m.f, det = m.a * m.d - m.b * m.c || 1;
  const tx = Math.round(X / T.px) * T.px - X, ty = Math.round(Y / T.px) * T.px - Y;
  g.translate((m.d * tx - m.c * ty) / det, (-m.b * tx + m.a * ty) / det);
};
function textImpl(str, x, y, o = {}) {
  if (str === undefined || str === null || str === '') return { x0: x, y0: y, x1: x, y1: y, h: 0, lines: 0 };
  const T = L.type;
  let s = String(str);
  if (o.upper ?? (o.font === 'mono' ? T.monoUpper : T.upper)) s = s.toUpperCase();
  let size = pxSize(o.size || 80);
  // look căn trái (swiss) mà beat đặt chữ đúng tâm khung (x = A.cx) không ghi align → ý là căn giữa;
  // căn trái từ tâm sẽ tràn mép phải (vd số khổng lồ của counter giant)
  const k = clamp(o.k ?? 1), align = o.align || (T.align && T.align !== 'center' && Math.abs(x - A.cx) < 1 ? 'center' : T.align) || 'center';
  g.save();
  g.font = fontOf({ ...o, size });
  if ('letterSpacing' in g) g.letterSpacing = `${(o.track ?? (o.font === 'mono' ? 0.04 : T.track || 0)) * size}px`;
  let lines = wrap(s, o);
  for (let i = 0; i < 6 && o.maxW && Math.max(...lines.map((ln) => g.measureText(ln).width)) > o.maxW; i++) {   // một từ quá dài → thu nhỏ
    size *= 0.9; g.font = fontOf({ ...o, size }); lines = wrap(s, o);
  }
  if (T.px) { const ps = pxSize(size); if (ps !== size) { size = ps; g.font = fontOf({ ...o, size }); lines = wrap(s, o); } }
  const lh = size * (o.lh || T.lh || 1.08), widths = lines.map((ln) => g.measureText(ln).width), wmax = Math.max(...widths);
  const bx = align === 'center' ? x - wmax / 2 : align === 'right' ? x - wmax : x;
  const makeBox = (yy) => ({
    x0: bx, y0: yy - size * 0.82, x1: bx + wmax, y1: yy + lh * (lines.length - 1) + size * 0.24,
    h: lh * lines.length, lines: lines.length, size,
  });
  let box = makeBox(y);
  if (k <= 0) { g.restore(); return box; }
  const mCur = g.getTransform(), syCur = Math.hypot(mCur.c, mCur.d) || 1;
  const screenBoxOf = (b) => {
    const cs = [[b.x0, b.y0], [b.x1, b.y0], [b.x1, b.y1], [b.x0, b.y1]]
      .map(([px, py]) => [mCur.a * px + mCur.c * py + mCur.e, mCur.b * px + mCur.d * py + mCur.f]);
    return [
      Math.min(cs[0][0], cs[1][0], cs[2][0], cs[3][0]),
      Math.min(cs[0][1], cs[1][1], cs[2][1], cs[3][1]),
      Math.max(cs[0][0], cs[1][0], cs[2][0], cs[3][0]),
      Math.max(cs[0][1], cs[1][1], cs[2][1], cs[3][1]),
    ];
  };
  let sbox = screenBoxOf(box);
  if (!o.quiet && recordBoxes && !o.allowOverlap && o.autoNudge !== false && boxes.length) {
    const pad = size * 0.35 * syCur;
    for (let pass = 0; pass < 4; pass++) {
      let hit = null, bestR = 0.05;
      for (const prev of boxes) {
        const r = boxOverlapRatio(sbox, prev.box);
        if (r > bestR) { bestR = r; hit = prev; }
      }
      if (!hit) break;
      const dyDown = (hit.box[3] + pad - sbox[1]) / syCur;
      const dyUp = (hit.box[1] - pad - sbox[3]) / syCur;
      const downBot = sbox[3] + dyDown * syCur, upTop = sbox[1] + dyUp * syCur;
      let nextY = y;
      if (downBot <= A.bottom + 8) nextY = y + dyDown;
      else if (upTop >= A.top - 8) nextY = y + dyUp;
      else {
        const overDown = Math.max(0, downBot - A.bottom), overUp = Math.max(0, A.top - upTop);
        nextY = overDown <= overUp ? y + dyDown : y + dyUp;
      }
      if (Math.abs(nextY - y) < 0.5) break;
      y = nextY;
      box = makeBox(y);
      sbox = screenBoxOf(box);
    }
  }
  const enter = o.enter || T.enter || 'mask', c = col(o.role || 'ink'), e = E(k);
  g.textAlign = align; g.textBaseline = 'alphabetic';
  const seed = strSeed(s);
  const boil = (L.type.boil || 0) && !o.quiet ? L.type.boil : 0, tick = Math.floor(cur.fs / (L.pen.every || 2));
  lines.forEach((ln, i) => {
    const ly = y + i * lh, kk = clamp(k * (1 + 0.25 * (lines.length - 1)) - 0.25 * i);
    g.save();
    if (o.rot ?? T.jaunty) { const r = (o.rot ?? (T.jaunty * (i % 2 ? -1 : 1))) * Math.PI / 180; g.translate(x, ly); g.rotate(r); g.translate(-x, -ly); }
    if (boil) g.translate(noise(seed, i, tick) * boil, noise(seed, i + 9, tick) * boil);
    let shown = ln;
    if (enter === 'mask') {                           // trồi lên từ khe cắt dưới baseline (không fade)
      g.beginPath(); g.rect(bx - 40, ly - size * 1.0, wmax + 80, size * 1.3); g.clip();
      g.translate(0, (1 - EASE.expo(kk)) * size * 1.15);
    } else if (enter === 'wipe' || enter === 'write') {
      const ww = (wmax + 60) * EASE.linear(kk); g.beginPath(); g.rect(bx - 30, ly - size * 1.1, ww, size * 1.6); g.clip();
    } else if (enter === 'type') {
      const nch = Math.floor(ln.length * kk); shown = ln.slice(0, nch) + (kk < 1 && (cur.f >> 2) % 2 ? '▌' : '');
      if (align !== 'left') { g.textAlign = 'left'; g.translate(align === 'center' ? -widths[i] / 2 : -widths[i], 0); }
    } else if (enter === 'pop') {
      const sc = MO.M.back(kk, 1.9); g.translate(x, ly - size * 0.3); g.scale(sc, sc); g.translate(-x, -(ly - size * 0.3));
    } else if (enter === 'slam') {
      const sc = lerp(1.7, 1, EASE.out(kk)); g.translate(x, ly - size * 0.3); g.scale(sc, sc); g.translate(-x, -(ly - size * 0.3)); g.globalAlpha *= clamp(kk * 3);
    } else if (enter === 'flicker') {
      const on = kk >= 1 || [1, 0, 1, 1, 0, 1][Math.floor(kk * 6)]; g.globalAlpha *= on ? 1 : 0.12;
    } else if (enter === 'slide') {
      g.translate((1 - EASE.dead(kk)) * -(i % 2 ? -1 : 1) * 220, 0); g.beginPath(); g.rect(0, ly - size * 1.1, W, size * 1.6); g.clip();
    }
    pxSnap(x, ly);
    if (T.chrome && !o.plain && size >= 90) {         // chữ crôm nhiều nấc (synthwave)
      const gr = g.createLinearGradient(0, ly - size * 0.8, 0, ly + size * 0.1);
      gr.addColorStop(0, pal.ink); gr.addColorStop(0.48, col('cold')); gr.addColorStop(0.5, pal.bg); gr.addColorStop(0.56, col('accent')); gr.addColorStop(1, pal.ink);
      g.fillStyle = gr; g.strokeStyle = pal.ink; g.lineWidth = 3; g.shadowColor = col('accent'); g.shadowBlur = 26;
      g.fillText(shown, x, ly); g.shadowBlur = 0; g.strokeText(shown, x, ly);
    } else {
      if (T.glow && !o.noGlow) { g.shadowColor = c; g.shadowBlur = T.glow; }
      // o.bare: chữ trong hộp chú thích/bóng thoại — không bóng đổ, không viền của look
      if (T.shadow && size >= 60 && !o.bare) { g.fillStyle = col(T.shadow[2] || 'accent'); g.fillText(shown, x + T.shadow[0], ly + T.shadow[1]); }
      if (T.drop && !o.bare) { g.fillStyle = col(T.drop[2] || 'bg'); g.fillText(shown, x + T.drop[0], ly + T.drop[1]); }   // bóng đổ mọi cỡ (chữ game)
      if (T.outline && !o.bare) { g.strokeStyle = pal.bg; g.lineWidth = size * T.outline; g.lineJoin = 'round'; g.strokeText(shown, x, ly); }
      g.fillStyle = c; g.fillText(shown, x, ly);
    }
    g.restore();
  });
  if (o.under && k >= 1) { g.fillStyle = col(o.under); g.fillRect(box.x0, box.y1 + 6, wmax, Math.max(4, size * 0.07)); }
  if (k >= 1 && !o.quiet && recordBoxes) {                           // chữ đã hiện đủ → báo khung bao cho QA OCR + kiểm tra chồng chữ
    const txtJoined = lines.join('\n');
    if (!o.allowOverlap) {
      for (const prev of boxes) {
        const r = boxOverlapRatio(sbox, prev.box);
        if (r > 0.05) overlaps.push({ a: prev.text, b: txtJoined, ratio: Number(r.toFixed(3)) });
      }
    }
    boxes.push({ text: txtJoined, box: sbox,
                 lines, font: fontOf({ ...o, size: Math.max(72, size) }), track: (o.track ?? (o.font === 'mono' ? 0.04 : T.track || 0)) });
  }
  g.restore();
  return box;
}

// ---------- ngữ cảnh cho look/beat ----------
const LEAD = L.motion.lead ?? 9;
const SAFE = JOB.safe || { top: 220, bottom: 384, left: 60, right_icons_x: 940, right_icons_from_y: 700 };
const GRID = JOB.layout_grid || { header: [250, 370], stage: [390, 1240], captions: [1340, 1460] };
const CAPTIONS_ON = JOB.captions_on !== false;
const STAGE_BOTTOM = CAPTIONS_ON
  ? Math.min(H - SAFE.bottom - 20, (GRID.stage && GRID.stage[1]) || 1240)
  : H - SAFE.bottom - 20;
const A = {
  x0: Math.max(84, SAFE.left + 24), x1: W - Math.max(84, SAFE.left + 24),
  top: SAFE.top + 20, bottom: STAGE_BOTTOM, stageBottom: STAGE_BOTTOM,
  stageTop: (GRID.stage && GRID.stage[0]) || 390,
  header: GRID.header || [250, 370], captions: GRID.captions || [1340, 1460],
  captionsOn: CAPTIONS_ON, cx: W / 2,
  xr: (y) => (y > SAFE.right_icons_from_y ? Math.min(W - 84, SAFE.right_icons_x - 10) : W - 84),
};
function enter(k, box, fn, kind) {
  k = clamp(k); if (k <= 0) return;
  const [bx, by, bw, bh] = box, cx = bx + bw / 2, cy = by + bh / 2, mode = kind || L.motion.enter || 'pop';
  g.save();
  const prev = cur.drawK;
  if (mode === 'pop') { const s = Math.max(0.001, EASE.bounce(k)); g.translate(cx, cy); g.scale(s, s); g.translate(-cx, -cy); }
  else if (mode === 'grow') { const s = Math.max(0.001, EASE.bounce(k)); g.translate(cx, by + bh); g.scale(lerp(0.85, 1, clamp(k * 2)), s); g.translate(-cx, -(by + bh)); }
  else if (mode === 'wipe') { g.beginPath(); g.rect(bx - 30, by - 30, (bw + 60) * EASE.snap(k), bh + 60); g.clip(); }
  else if (mode === 'snap') { g.translate((1 - EASE.snap(k)) * -(bx + bw + 40), 0); }
  else if (mode === 'slide') { g.translate(0, (1 - EASE.dead(k)) * (H - by + 40)); }
  else if (mode === 'draw') { cur.drawK = k; }
  else if (mode === 'flicker') { g.globalAlpha *= k >= 1 || [1, 0, 1, 1, 0, 1][Math.floor(k * 6)] ? 1 : 0.1; }
  else if (mode === 'lock') { const s = lerp(1.4, 1, EASE.out(k)); g.translate(cx, cy); g.scale(s, s); g.translate(-cx, -cy); g.globalAlpha *= clamp(k * 4); }
  fn(k);
  cur.drawK = prev;
  g.restore();
}
const DEFAULT_EDITORIAL = (L.rig && L.rig.editorial !== undefined)
  ? !!L.rig.editorial
  : !!(JOB.design_system && JOB.design_system.character_style === 'editorial');
function drawHeatHalo(x, y, s, heat) {
  const h = clamp(heat);
  if (h <= 0.05) return;
  const r = Math.max(24, s * (1.15 + 0.35 * h)), [cr, cg, cb] = hex(col('hot'));
  g.save();
  const gr = g.createRadialGradient(x, y, r * 0.12, x, y, r);
  gr.addColorStop(0, `rgba(${cr},${cg},${cb},${(0.42 * h).toFixed(3)})`);
  gr.addColorStop(0.55, `rgba(${cr},${cg},${cb},${(0.18 * h).toFixed(3)})`);
  gr.addColorStop(1, `rgba(${cr},${cg},${cb},0)`);
  g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill();
  g.restore();
}
const icon = (name, o = {}) => {
  const heat = clamp(o.heat ?? (o.args && o.args.heat) ?? 0);
  if (heat > 0.05 && !o.noHeatHalo) drawHeatHalo(o.x ?? 0, o.y ?? 0, o.s ?? 100, heat);
  const applyHeat = (prims) => {
    if (heat <= 0.05) return prims;
    const cHot = col('hot'), k = heat * 0.6;
    return prims.map((p) => (p.fine || p.hole || p.role === 'bg' ? p : { ...p, role: mix(colOf(p), cHot, k), tone: 0 }));
  };
  if (name && typeof name === 'object') {            // icon tự ghép từ storyboard: {"parts": [...]}
    draw(applyHeat(partsIcon(name)), { ...o, seed: o.seed ?? strSeed(JSON.stringify(name).slice(0, 64)) });
    return;
  }
  if (isRig(name)) {                                  // nhân vật hoạt hình 2D "rig:<loài>[:hành động][:biểu cảm]" (rig2d.js)
    const seed = o.seed ?? strSeed(name);
    const args = { editorial: DEFAULT_EDITORIAL, heat, ...(o.args || {}) };
    draw(applyHeat(rigPrims(name, { f: cur.fs, fps: FPS, seed, role: o.role, args })), { ...o, seed });
    return;
  }
  const fn = ICONS[iconFor(name)] || ICONS.dot;
  draw(applyHeat(fn({ f: cur.fs, p: o.p ?? 0, role: o.role, heat, hash, ...o.args })), { ...o, seed: o.seed ?? strSeed(name) });
};
function makeCtx(f, n = N, p = P) {
  const step = L.motion.step || 1, fs = Math.floor(f / step) * step;
  cur.f = f; cur.fs = fs; cur.drawK = 1;
  return { g, W, H, N: n, FPS, f, fs, t: f / FPS, u: f / Math.max(1, n - 1), pal, L, P: p, A, SAFE, GRID, E, EASE, MO, clamp, lerp, hash, noise, strSeed,
           col, shade, mix, draw, text, later, enter, icon, fmtNum, TAU, K: lookMod, media: MEDIA, kick: cur.kick,
           // LEAD: mọi phần tử 'vào sớm' vài frame → frame 0 của shot đã có hình (cắt cứng không lộ frame đen)
           k: (f0, dur, stepped = true) => clamp(((stepped ? fs : f) + LEAD - f0) / Math.max(1, dur)) };
}

// ---------- hậu kỳ theo look ----------
const grainTile = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d'), d = x.createImageData(256, 256);
  for (let i = 0; i < 256 * 256; i++) { const v = hash(i, 17) * 255; d.data[i * 4] = d.data[i * 4 + 1] = d.data[i * 4 + 2] = v; d.data[i * 4 + 3] = 255; }
  x.putImageData(d, 0, 0); return c;
})();
function post(c) {
  const po = L.post || {};
  g.setTransform(1, 0, 0, 1, 0, 0);
  if (po.scanlines) { g.fillStyle = `rgba(0,0,0,${po.scanlines})`; for (let y = (c.f % 2); y < H; y += 4) g.fillRect(0, y, W, 2); }
  if (po.vignette) {
    const gr = g.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.72);
    gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, `rgba(0,0,0,${po.vignette})`); g.fillStyle = gr; g.fillRect(0, 0, W, H);
  }
  if (po.grain) {                                     // hạt đổi mỗi frame → không frame nào trùng frame trước
    g.save(); g.globalAlpha = po.grain; g.globalCompositeOperation = 'overlay';
    const ox = Math.floor(hash(c.f, 3) * 256), oy = Math.floor(hash(c.f, 5) * 256);
    for (let y = -oy; y < H; y += 256) for (let x = -ox; x < W; x += 256) g.drawImage(grainTile, x, y);
    g.restore();
  }
}

// hậu kỳ in/pixel của look (post.pixel/halftone/misregister/paper → post2d.js, WebGL2, một pass) — null nếu look không cần
const GLP = makePost2D(L.post || {}, { ...pal, dim: pal.dim || mix(pal.bg, pal.ink, 0.42) }, W, H);
const HOLD = Math.max(1, L.motion.hold | 0);           // stop-motion / sprite: giữ cả khung on 2s/3s (≤ 3 → không vi phạm luật 4 frame)

window.stage = 'media';                                // Lottie/Rive của actor (chỉ nạp khi job có)
const MEDIA = await loadMedia(JOB, { g, col, bg: pal.bg });
window.stage = 'scene';
const lookMod = LOOKS[L.look] || LOOKS.flat;
const beatFn = BEATS[JOB.scene] || TOOLS[JOB.scene];
if (!beatFn) throw new Error(`engine html: không có beat '${JOB.scene}' (có: ${Object.keys(BEATS).join(', ')})`);
const S = beatFn(makeCtx(0), P);
const kicks = (S.cues || []).filter((q) => q.kick).map((q) => ({ f: q.f, a: q.kick }));

// ---------- "một cú máy liền" (spine): các shot là các ô trên một canvas lớn, camera bay liền qua điểm cắt ----------
// JOB.spine = {L, prev?, next?} — prev/next = {scene, params, n, tile:{x,y,s,r}} là ô hàng xóm TƯƠNG ĐỐI với ô của shot này
// (ô này = đồng nhất, tâm ở gốc). Camera là hàm của thời gian toàn video, tính trong hệ toạ độ chung → frame cuối shot trước
// và frame đầu shot sau trùng khít dù mỗi shot render riêng (song song + RESUME vẫn giữ).
const SP = JOB.spine || null;
const SPL = SP ? Math.max(4, SP.L || 9) : 0;
const ID_TILE = { x: 0, y: 0, s: 1, r: 0 };
const nb = (side) => {
  const o = SP && SP[side];
  if (!o) return null;
  const p = o.params || {};
  // "ô ma" (shot của engine khác, vd Manim): camera vẫn bay tới/từ ô đó nhưng không vẽ lại nội dung bằng html
  if (o.ghost || !BEATS[o.scene]) return { ...o, p, S: null };
  return { ...o, p, S: BEATS[o.scene](makeCtx(0, o.n, p), p) };
};
const PREV = nb('prev'), NEXT = nb('next');
const sm = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const tEase = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };   // in-out cubic
function rest(T, lf, ln) {                            // tư thế camera khi đứng trên ô T (tính trong toạ độ của ô)
  // trôi nhẹ + "khung lại" giữa shot: đẩy về phía vật chính (FOCUS) như người quay nhấn vào chủ thể (motion.reframe)
  const u = lf / Math.max(1, ln - 1), rf = (L.motion.reframe ?? 0.11) * sm(0.22, 0.62, u);
  const dx = Math.sin(lf * 0.021 + 1.3) * 16, dy = Math.cos(lf * 0.017) * 20 + 150 * rf / 0.11 * 0.6;
  const cr = Math.cos(T.r), sr = Math.sin(T.r);
  return { cx: T.x + T.s * (dx * cr - dy * sr), cy: T.y + T.s * (dx * sr + dy * cr),
           z: (1 / T.s) * (1 + (L.motion.creep ?? 0.025) * u + rf + Math.sin(lf * 0.03) * 0.006),
           rot: T.r + Math.sin(lf * 0.013) * 0.008 + rf * 0.12 * (hash(Math.round(T.x), Math.round(T.y)) > 0.5 ? 1 : -1) };
}
function interp(a, b, e, same) {
  const lz = Math.log(a.z) + (Math.log(b.z) - Math.log(a.z)) * e, z = Math.exp(lz);
  const w = Math.abs(a.z - b.z) > 1e-4 ? (1 / a.z - 1 / z) / (1 / a.z - 1 / b.z) : e;
  return { cx: lerp(a.cx, b.cx, w), cy: lerp(a.cy, b.cy, w), z: same ? z * (1 - 0.16 * Math.sin(Math.PI * e)) : z, rot: lerp(a.rot, b.rot, e) };
}
function spineCam(f) {                                // → {cam, win:{nb, e, src, dst}|null}
  const self = rest(ID_TILE, f, N);
  if (PREV && f < SPL) {
    const e = tEase((f + SPL) / (2 * SPL)), same = Math.abs(PREV.tile.s - 1) < 1e-3;
    return { cam: interp(rest(PREV.tile, PREV.n + f, PREV.n), self, e, same), win: { nb: PREV, e, src: 'nb', same } };
  }
  if (NEXT && f >= N - SPL) {
    const e = tEase((f - (N - SPL)) / (2 * SPL)), same = Math.abs(NEXT.tile.s - 1) < 1e-3;
    return { cam: interp(self, rest(NEXT.tile, f - N, NEXT.n), e, same), win: { nb: NEXT, e, src: 'self', same } };
  }
  return { cam: self, win: null };
}
const applyCam = (cam, kk) => { g.translate(W / 2 + kk * 16, H / 2 + kk * 11); g.rotate(-cam.rot + kk * 0.012); g.scale(cam.z, cam.z); g.translate(-cam.cx, -cam.cy); };
const applyTile = (T) => { g.translate(T.x, T.y); g.rotate(T.r); g.scale(T.s, T.s); g.translate(-W / 2, -H / 2); };
let recordBoxes = true;
function worldDots(cam) {                             // lưới chấm mờ trong toạ độ THẾ GIỚI → thấy rõ camera đang bay
  const sp = L.spine || {};
  if (sp.dots === false) return;
  const step = 150, half = Math.hypot(W, H) / 2 / cam.z;
  if (step * cam.z < 26 || step * cam.z > 900) return;
  g.save(); applyCam(cam, 0);
  g.fillStyle = col('dim'); g.globalAlpha = sp.dots_alpha ?? 0.22;
  const r = 2.2 / cam.z, x0 = Math.floor((cam.cx - half) / step), x1 = Math.ceil((cam.cx + half) / step);
  const y0 = Math.floor((cam.cy - half) / step), y1 = Math.ceil((cam.cy + half) / step);
  for (let i = x0; i <= x1; i++) for (let j = y0; j <= y1; j++) g.fillRect(i * step - r, j * step - r, 2 * r, 2 * r);
  g.restore();
}
function drawTile(T, beat, lf, ln, lp, cam, kk, alpha, fill, isSelf) {
  if (alpha <= 0.005) return;
  g.save(); applyCam(cam, kk); applyTile(T);
  if (fill > 0) {                                     // ô nhỏ chuyển tiếp: nền đặc mềm không vẽ khung chữ nhật cứng đè chữ
    g.globalAlpha = fill; g.fillStyle = pal.bg; g.fillRect(-30, -30, W + 60, H + 60);
  }
  g.globalAlpha = alpha;
  recordBoxes = isSelf;
  if (beat) beat.draw(makeCtx(lf, ln, lp));
  recordBoxes = true;
  g.restore();
}

window.meta = { cues: [...(S.cues || []).map((q) => ({ f: q.f, name: q.name })), ...(NEXT ? [{ f: Math.max(0, N - SPL), name: 'whoosh' }] : [])],
                texts: S.texts || [], frames: N, scene: JOB.scene, engine: 'html', look: L.look, spine: !!SP, media: MEDIA.info,
                post2d: GLP ? GLP.info : null, hold: HOLD, captions_on: CAPTIONS_ON, stage_bottom: STAGE_BOTTOM };
window.renderFrame = (f0) => {
  boxes = []; overlaps = []; deferred = [];
  const f = HOLD > 1 ? Math.floor(f0 / HOLD) * HOLD : f0;
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.shadowBlur = 0; g.filter = 'none';
  g.fillStyle = pal.bg; g.fillRect(0, 0, W, H);
  let kk = MO.kickAt(f, kicks);
  if (L.motion.shake_px) kk = Math.round(kk * 16 / L.motion.shake_px) * L.motion.shake_px / 16;   // rung màn theo lưới pixel
  cur.kick = kk;
  const c = makeCtx(f);
  if (!SP) {
    if (lookMod.bg && !P.no_bg) { g.save(); lookMod.bg(c); g.restore(); }   // no_bg: bảng xem đạo cụ
    const z = 1 + (L.motion.creep ?? 0.025) * c.u;
    g.save();
    g.translate(W / 2 + kk * 16, H / 2 + kk * 11); g.scale(z, z); g.rotate(kk * 0.012); g.translate(-W / 2, -H / 2);
    S.draw(c);
    g.restore();
  } else {
    const { cam, win } = spineCam(f);
    if (lookMod.bg) {                                 // nền của look ở toạ độ màn hình, trượt nhẹ theo hướng bay (thị sai)
      g.save();
      if (win) {
        const k = Math.sin(Math.PI * win.e), dir = Math.atan2(win.nb.tile.y, win.nb.tile.x) + (win.src === 'nb' ? Math.PI : 0);
        g.translate(W / 2 - Math.cos(dir) * 90 * k, H / 2 - Math.sin(dir) * 90 * k); g.scale(1.08, 1.08); g.translate(-W / 2, -H / 2);
      }
      lookMod.bg(makeCtx(f)); g.restore();
    }
    worldDots(cam);
    const tiles = [{ T: ID_TILE, beat: S, lf: f, ln: N, lp: P, self: true }];
    let nbAlpha = 1, selfAlpha = 1, nbFill = 0, selfFill = 0;
    if (win) {
      const o = win.nb, lf = o === PREV ? PREV.n + f : f - N;
      // chuyển cỡ (dive/pull): ô đi ra mờ sớm & ô đi vào hiện dần êm — không tạo "cửa sổ cắt ngang chữ" ở giữa màn
      const fadeOut = 1 - sm(0.18, 0.68, win.e);
      const fadeIn = sm(0.22, 0.72, win.e);
      if (!win.same) {                                // lao vào / kéo ra
        if (win.src === 'self') { selfAlpha = fadeOut; nbAlpha = fadeIn; }
        else { nbAlpha = fadeOut; selfAlpha = fadeIn; }
        if (o.tile.s < 1) nbFill = fadeIn * 0.92; else selfFill = fadeIn * 0.92;
      }
      tiles.push({ T: o.tile, beat: o.S, lf, ln: o.n, lp: o.p, self: false });
    }
    tiles.sort((a, b) => b.T.s - a.T.s);              // ô lớn vẽ trước, ô nhỏ (cổng) đè lên
    for (const t of tiles) {
      drawTile(t.T, t.beat, t.lf, t.ln, t.lp, cam, t.self ? kk : 0, t.self ? selfAlpha : nbAlpha, t.self ? selfFill : nbFill, t.self);
    }
    makeCtx(f);
  }
  // thứ tự cố định: lớp vẽ lại của look (paint) → tiền cảnh (fg) → hậu kỳ in/pixel (GLP) → chữ/nhãn hoãn → hạt/vignette
  if (lookMod.paint) { g.save(); lookMod.paint(c); g.restore(); }
  if (lookMod.fg) { g.save(); lookMod.fg(c); g.restore(); }
  if (GLP) GLP.apply(canvas, g);
  if (deferred.length) replay();
  post(c);
};
window.textBoxes = () => boxes.map((b) => {         // + texture phẳng trắng/trong suốt của chữ để OCR không phụ thuộc hiệu ứng
  const c = document.createElement('canvas'), x = c.getContext('2d');
  x.font = b.font; const px = parseFloat(b.font.match(/(\d+)px/)[1]);
  if ('letterSpacing' in x) x.letterSpacing = `${b.track * px}px`;
  const w = Math.max(...b.lines.map((ln) => x.measureText(ln).width));
  c.width = Math.ceil(w + 80); c.height = Math.ceil(px * 1.25 * b.lines.length + 60);
  x.font = b.font; if ('letterSpacing' in x) x.letterSpacing = `${b.track * px}px`;
  x.fillStyle = '#fff'; x.textBaseline = 'alphabetic';
  b.lines.forEach((ln, i) => x.fillText(ln, 40, 30 + px * 0.9 + i * px * 1.25));
  return { text: b.text, box: b.box, tex: c.toDataURL('image/png') };
});
window.overlapPairs = () => overlaps.slice();
window.glInfo = 'canvas2d';
window.ready = true;
