// Nhân vật của kênh (thiết kế riêng, KHÔNG dùng lại lính La Mã của kit): nhà khoa học đầu tròn, mắt to,
// kính bảo hộ tròng accent, tay chân là ống trắng nét đen — khớp model sheet REF_SCIENTIST của pipeline Flow.
// Vẽ trên canvas thiết kế 800×1000 (tâm x=400, đế giày y≈975) bằng Pen của toon.ts (mromidev/claude-animated-shorts, MIT),
// mực/viền rim theo palette của style. Mọi tham số là số → key card làm tròn bằng q() để chỉ vẽ lại khi đổi thấy được.
import { Pen } from '../../vendor/claude-animated-shorts/toonbase.js';

const rad = (d) => d * Math.PI / 180;

class InkPen extends Pen {
  constructor(g, ink, rim, rimW) { super(g); this.ink = ink; this.rimC = rim; this.rimW = rimW; this.rimPass = false; }
  _stroke(w) { const g = this.g; g.lineJoin = 'round'; g.lineCap = 'round'; g.lineWidth = this.rimPass ? w + 2 * this.rimW : w; g.strokeStyle = this.rimPass ? this.rimC : this.ink; g.stroke(); }
  poly(pts, fill, ol) {
    const w = ol ?? this.ol; this.path(pts, true);
    if (this.rimPass) { if (fill || w) { this.g.fillStyle = this.rimC; this.g.fill(); this._stroke(w || 0.1); } return; }
    if (fill) { this.g.fillStyle = fill; this.g.fill(); }
    if (w) this._stroke(w);
  }
  tube(pts, fill, w) {                         // chi: ống tròn đầu, viền mực
    const g = this.g; g.lineCap = 'round'; g.lineJoin = 'round';
    this.path(pts, false); g.lineWidth = w + 2 * this.ol + (this.rimPass ? 2 * this.rimW : 0); g.strokeStyle = this.rimPass ? this.rimC : this.ink; g.stroke();
    if (this.rimPass) return;
    this.path(pts, false); g.lineWidth = w; g.strokeStyle = fill; g.stroke();
  }
  circ(cx, cy, r, fill, ol) {
    const pts = []; for (let i = 0; i <= 48; i++) pts.push([cx + r * Math.cos(i / 48 * 2 * Math.PI), cy + r * Math.sin(i / 48 * 2 * Math.PI)]);
    this.poly(pts, fill, ol);
  }
  rrect(x0, y0, x1, y1, r, fill, ol) {
    const pts = [];
    for (const [cx, cy, a] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]])
      for (let i = 0; i <= 8; i++) pts.push([cx + r * Math.cos(rad(a + 90 * i / 8)), cy + r * Math.sin(rad(a + 90 * i / 8))]);
    this.poly(pts, fill, ol);
  }
  mark(pts, w) { if (this.rimPass) return; this.stroke(pts, w, this.ink); }
}

export const DEFAULT_PAL = { body: '#ffffff', shade: '#cfcfcf', ink: '#000000', rim: '#ffffff', accent: '#1849F7',
  lensHi: '#6f90ff', strap: '#8a8a8a', glove: '#ffffff', boot: '#e9e9e9', mouth: '#1a1a1a' };

const ARM = { // [vai→khuỷu góc°, khuỷu→tay góc°] (0° = sang phải, 90° = xuống), tay phải; tay trái lật gương
  hang: [82, 88], hip: [120, 30], wave: [-60, -95], up: [-80, -95], point: [10, 4], hold: [110, 200],
  shrug: [150, 230], cheer: [-45, -70], think: [100, 215], present: [40, -20],
};

/** Vẽ nhà khoa học. o: expr, look [-1..1, -1..1], blink 0..1, armL/armR (tên ARM), wave 0..1, tilt, headTilt, bob, prop, pal. */
export function scientist(g, o = {}) {
  const pal = { ...DEFAULT_PAL, ...(o.pal || {}) };
  const ol = o.ol ?? 9, rimW = o.rimW ?? 4.5;
  const p = new InkPen(g, pal.ink, pal.rim, rimW); p.ol = ol;
  const cx = 400, bob = (o.bob || 0) * 1000, tilt = o.tilt || 0, ht = o.headTilt || 0;
  const hipY = 700 + bob * 0.3, shY = 420 + bob, headC = [cx, 285 + bob];
  g.save(); g.translate(cx, 975); g.rotate(rad(tilt)); g.translate(-cx, -975);
  const armPts = (side, name, wave) => {
    const a = ARM[name] || ARM.hang; let a0 = a[0], a1 = a[1];
    if (name === 'wave') { const w = Math.sin((wave || 0) * Math.PI * 2) * 22; a1 += w; a0 += w * 0.3; }
    const s = side === 'R' ? 1 : -1, sx = cx + s * 100, sy = shY + 12;
    const flip = (ang) => (s > 0 ? ang : 180 - ang);
    const e = [sx + 118 * Math.cos(rad(flip(a0))), sy + 118 * Math.sin(rad(flip(a0)))];
    const h = [e[0] + 112 * Math.cos(rad(flip(a1))), e[1] + 112 * Math.sin(rad(flip(a1)))];
    return [[sx, sy], e, h];
  };
  const armR = armPts('R', o.armR || 'hang', o.wave), armL = armPts('L', o.armL || 'hang', o.wave);
  const draw = () => {
    // chân
    for (const s of [-1, 1]) { p.tube([[cx + s * 46, hipY - 20], [cx + s * 50, 930]], pal.body, 46); p.rrect(cx + s * 50 - 44, 918, cx + s * 50 + 44, 972, 22, pal.boot, ol); }
    // tay sau thân (trái)
    p.tube(armL, pal.body, 44); p.circ(armL[2][0], armL[2][1], 27, pal.glove, ol);
    // thân: áo blouse
    const body = rrectPts(cx - 112, shY - 20, cx + 112, hipY + 18, 70);
    p.poly(body, pal.body, ol);
    if (!p.rimPass) {
      g.save(); p.path(body, true); g.clip();
      g.fillStyle = pal.shade; g.globalAlpha = 0.55; g.fillRect(cx + 40, shY - 20, 80, hipY - shY + 40); g.restore();
      p.mark([[cx, shY + 30], [cx, hipY + 8]], 6);                        // nẹp áo
      p.mark([[cx - 52, shY - 8], [cx, shY + 40], [cx + 52, shY - 8]], 6); // cổ áo
      p.circ(cx + 52, shY + 120, 7, pal.ink, 0);
    }
    // đầu (nghiêng theo headTilt)
    g.save(); g.translate(headC[0], headC[1] + 110); g.rotate(rad(ht)); g.translate(-headC[0], -headC[1] - 110);
    p.circ(headC[0], headC[1], 128, pal.body, ol);
    if (!p.rimPass) {
      g.save(); p.path(ellPts(headC[0], headC[1], 128), true); g.clip(); g.globalAlpha = 0.5; g.fillStyle = pal.shade;
      g.beginPath(); g.arc(headC[0] - 70, headC[1] - 40, 190, 0, 7); g.rect(0, 0, 800, 1000); g.fill('evenodd'); g.restore();
    }
    face(p, g, headC, pal, o, ol);
    g.restore();
    // tay trước (phải) + đạo cụ
    if (o.prop === 'tongs') tongs(p, armR[2], pal, ol);
    if (o.prop === 'clipboard') clipboard(p, armR[2], pal, ol);
    p.tube(armR, pal.body, 44); p.circ(armR[2][0], armR[2][1], 27, pal.glove, ol);
  };
  p.rimPass = true; draw(); p.rimPass = false; draw();
  g.restore();
}

const rrectPts = (x0, y0, x1, y1, r) => {
  const pts = [];
  for (const [cx, cy, a] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]])
    for (let i = 0; i <= 8; i++) pts.push([cx + r * Math.cos(rad(a + 90 * i / 8)), cy + r * Math.sin(rad(a + 90 * i / 8))]);
  return pts;
};
/** Độ dày nét (đơn vị thiết kế) để nét card ≈ px pixel trên khung 1080×1920 ở khoảng cách dist (m), fov dọc (độ). */
export const olFor = (dist, fov = 40, px = 7, H = 1920) => {
  const unitsPerPx = 1000 / 2.25 / (H / (2 * dist * Math.tan(fov * Math.PI / 360)));
  return Math.round(px * unitsPerPx * 2) / 2;
};
const ellPts = (cx, cy, r) => { const a = []; for (let i = 0; i <= 48; i++) a.push([cx + r * Math.cos(i / 48 * 2 * Math.PI), cy + r * Math.sin(i / 48 * 2 * Math.PI)]); return a; };

function face(p, g, [hx, hy], pal, o, ol) {
  const e = o.expr || 'neutral', look = o.look || [0, 0], blink = o.blink || 0;
  const gy = hy + 8;
  // dây kính
  p.rrect(hx - 140, gy - 22, hx + 140, gy + 22, 12, pal.strap, ol * 0.8);
  // gọng + tròng
  p.rrect(hx - 120, gy - 58, hx + 120, gy + 58, 46, pal.body, ol);
  for (const s of [-1, 1]) {
    p.rrect(hx + s * 58 - 50, gy - 44, hx + s * 58 + 50, gy + 44, 34, pal.accent, ol * 0.75);
    if (p.rimPass) continue;
    g.save(); g.globalAlpha = 0.55; p.mark([[hx + s * 58 - 30, gy - 30], [hx + s * 58 - 6, gy - 34]], 7); g.restore();
    // mắt: tròng trắng + con ngươi (nhìn theo look), chớp = mí
    const r = e === 'shock' ? 36 : 32, pr = e === 'shock' ? 11 : 15;
    const ex = hx + s * 58, ey = gy + 2;
    p.circ(ex, ey, r, '#ffffff', ol * 0.7);
    if (blink < 0.75) p.circ(ex + look[0] * 12, ey + look[1] * 10, pr, pal.ink, 0);
    if (blink > 0) { g.save(); p.path(ellPts(ex, ey, r), true); g.clip(); g.fillStyle = pal.body; g.fillRect(ex - r, ey - r, 2 * r, 2 * r * Math.min(1, blink)); g.restore(); p.circ(ex, ey, r, null, ol * 0.7); }
  }
  if (p.rimPass) return;
  // lông mày (biểu cảm) phía trên gọng
  const brow = { neutral: [0, 0], shock: [-16, 0], grin: [-10, -2], worried: [-10, -16], stern: [6, 16], excited: [-14, 4], smug: [-4, 10] }[e] || [0, 0];
  // brow = [nâng cả cặp (âm = lên), nghiêng đầu trong (âm = đầu trong nhướn lên → lo lắng; dương = nhíu)]
  for (const s of [-1, 1]) p.mark([[hx + s * 30, gy - 78 + brow[0] + brow[1]], [hx + s * 88, gy - 78 + brow[0] - brow[1] * 0.4]], 10);
  // miệng
  const my = hy + 92;
  if (e === 'shock') p.circ(hx, my + 4, 15, pal.mouth, ol * 0.6);
  else if (e === 'grin' || e === 'excited') { p.poly([[hx - 38, my - 6], [hx + 38, my - 6], [hx + 22, my + 20], [hx - 22, my + 20]], pal.mouth, ol * 0.6); }
  else if (e === 'worried' || e === 'stern') p.mark([[hx - 26, my + 6], [hx, my - 2], [hx + 26, my + 6]], 8);
  else if (e === 'smug') p.mark([[hx - 22, my + 2], [hx + 4, my + 6], [hx + 28, my - 6]], 8);
  else p.mark([[hx - 22, my], [hx, my + 6], [hx + 22, my]], 8);
}

function tongs(p, [hx, hy], pal, ol) {
  p.tube([[hx, hy], [hx + 150, hy - 120]], pal.body, 12); p.tube([[hx + 6, hy + 8], [hx + 162, hy - 104]], pal.body, 12);
}
function clipboard(p, [hx, hy], pal, ol) {
  p.rrect(hx - 70, hy - 150, hx + 60, hy + 20, 10, '#d8d8d8', ol); p.rrect(hx - 30, hy - 160, hx + 20, hy - 136, 6, pal.strap, ol * 0.7);
  for (let i = 0; i < 4; i++) p.mark([[hx - 50, hy - 110 + i * 30], [hx + 40, hy - 110 + i * 30]], 6);
}

/** key ổn định cho card: chỉ đổi khi dáng đổi thấy được */
export const keyOf = (o) => JSON.stringify(o, (k, v) => (typeof v === 'number' ? Math.round(v * 100) / 100 : v));
export const ARMS = Object.keys(ARM);
export const EXPRS = ['neutral', 'shock', 'grin', 'worried', 'stern', 'excited', 'smug'];
