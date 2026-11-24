// Texture vẽ tay bằng Canvas2D (xác định theo seed) — cùng phong cách "phẳng + đường nối tối" của
// cartoon-short-kit/engine/paint.js (rng, tex, radial lấy từ đó), thêm bộ texture phòng thí nghiệm trên nền đen.
import * as THREE from '../../vendor/three/three.module.js';

export const rng = (seed) => { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };
const cv = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; };
export const tex = (c, rx = 1, ry = 1) => {
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
};
export function radial(col = '0,0,0', a = 0.55) {
  const [c, g] = cv(128, 128), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(0.55, `rgba(${col},${a * 0.6})`); gr.addColorStop(1, `rgba(${col},0)`);
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return c;
}
/** mặt bàn thí nghiệm (laminate tối, đường nối, vệt xước) */
export function benchTop(seed = 1, base = '#2a3340', seam = '#151a22') {
  const [c, g] = cv(512, 512), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(255,255,255,${0.02 + r() * 0.04})`; g.lineWidth = 1 + r() * 2; g.beginPath(); const y = r() * 512; g.moveTo(0, y); g.lineTo(512, y + r() * 10 - 5); g.stroke(); }
  g.fillStyle = seam; g.fillRect(0, 0, 512, 5); g.fillRect(0, 0, 5, 512);
  return c;
}
/** gạch men tường lab: ô vuông có ron tối */
export function tiles(seed = 2, base = '#1d2430', grout = '#0b0e13', n = 8) {
  const [c, g] = cv(512, 512), r = rng(seed), s = 512 / n;
  g.fillStyle = grout; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const L = (r() - 0.5) * 6; g.fillStyle = shadeHex(base, L); g.fillRect(i * s + 3, j * s + 3, s - 6, s - 6);
    g.fillStyle = 'rgba(255,255,255,0.05)'; g.fillRect(i * s + 6, j * s + 6, s - 12, 4);
  }
  return c;
}
/** kim loại chải (giá đỡ, cân) */
export function metal(seed = 3, base = '#c9ced6') {
  const [c, g] = cv(256, 256), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 160; i++) { g.strokeStyle = `rgba(${r() < 0.5 ? '0,0,0' : '255,255,255'},${0.03 + r() * 0.05})`; g.lineWidth = 1; g.beginPath(); const y = r() * 256; g.moveTo(0, y); g.lineTo(256, y); g.stroke(); }
  return c;
}
/** bảng đen (chalkboard) có vệt phấn mờ */
export function chalkboard(seed = 4, base = '#10161a') {
  const [c, g] = cv(1024, 512), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, 1024, 512);
  for (let i = 0; i < 40; i++) { g.fillStyle = `rgba(255,255,255,${0.015 + r() * 0.03})`; g.beginPath(); g.ellipse(r() * 1024, r() * 512, 60 + r() * 160, 10 + r() * 30, r() * 3, 0, 7); g.fill(); }
  return c;
}
/** vạch chia nhiệt kế: vạch + số, đọc đúng chiều (kiểm tra không lật gương bằng OCR) */
export function thermoScale({ lo = -10, hi = 30, step = 10, minor = 2, unit = '°C', font = 'sans-serif', ink = '#000000', bg = null,
  highlight = null, hiColor = '#1849F7', w = 256, h = 1024 } = {}) {
  const [c, g] = cv(w, h);
  if (bg) { g.fillStyle = bg; g.fillRect(0, 0, w, h); }
  const y = (v) => h * 0.94 - (v - lo) / (hi - lo) * h * 0.88;
  g.strokeStyle = ink; g.fillStyle = ink; g.lineCap = 'round';
  for (let v = lo; v <= hi + 1e-6; v += minor) {
    const major = Math.abs((v - lo) % step) < 1e-6; g.lineWidth = major ? 9 : 5;
    g.beginPath(); g.moveTo(w * 0.06, y(v)); g.lineTo(w * (major ? 0.36 : 0.22), y(v)); g.stroke();
  }
  g.textBaseline = 'middle'; g.textAlign = 'left';
  for (let v = lo; v <= hi + 1e-6; v += step) {
    const isHi = highlight !== null && Math.abs(v - highlight) < 1e-6;
    g.font = `${isHi ? 92 : 70}px "${font}"`; g.fillStyle = isHi ? hiColor : ink;
    g.fillText(isHi ? `${v}${unit}` : `${v}`, w * 0.42, y(v) + 4);
  }
  return c;
}
/** bóng tròn dưới vật kiểu máy thời 90: lõi đặc, mép mềm */
export function blob(px = 64) {
  const [c, g] = cv(px, px), gr = g.createRadialGradient(px / 2, px / 2, 0, px / 2, px / 2, px / 2);
  gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.5, 'rgba(0,0,0,0.85)'); gr.addColorStop(0.8, 'rgba(0,0,0,0.35)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = gr; g.fillRect(0, 0, px, px); return c;
}
// ---------- bối cảnh (set) meadow / tabletop / street: texture thấp kiểu thời 90, tất định theo seed ----------
const dots = (g, w, h, r, n, cols, rmin, rmax) => {
  for (let i = 0; i < n; i++) { g.fillStyle = cols[Math.floor(r() * cols.length)]; g.beginPath(); g.ellipse(r() * w, r() * h, rmin + r() * (rmax - rmin), (rmin + r() * (rmax - rmin)) * 0.7, r() * 3, 0, 7); g.fill(); }
};
/** cỏ: nền rêu đêm trưởng thành + đốm sáng/tối dịu + nét lá ngắn */
export function grass(seed = 5, base = '#2B4C3B', px = 128) {
  const [c, g] = cv(px, px), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, px, px);
  dots(g, px, px, r, px * 0.45, [shadeHex(base, -7), shadeHex(base, 6), shadeHex(base, -4)], px * 0.015, px * 0.04);
  g.lineCap = 'round';
  for (let i = 0; i < px * 0.75; i++) {
    const x = r() * px, y = r() * px; g.strokeStyle = shadeHex(base, r() < 0.5 ? 10 : -10); g.lineWidth = Math.max(1, px / 96);
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + (r() - 0.5) * px * 0.03, y - px * (0.02 + r() * 0.03)); g.stroke();
  }
  return c;
}
/** đất/đá (vách đảo, đường đất) */
export function dirt(seed = 6, base = '#3F362E', px = 64) {
  const [c, g] = cv(px, px), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, px, px);
  dots(g, px, px, r, px * 0.75, [shadeHex(base, -18), shadeHex(base, 12), shadeHex(base, -8)], px * 0.02, px * 0.07);
  return c;
}
/** cụm cỏ (nền trong suốt) — dán lên 2 mặt phẳng chéo */
export function tuft(seed = 7, base = '#365C47', px = 64) {
  const [c, g] = cv(px, px), r = rng(seed);
  for (let i = 0; i < 9; i++) {
    const x = px * (0.18 + 0.64 * r()), h = px * (0.45 + 0.5 * r()), lean = (r() - 0.5) * px * 0.35, w = px * (0.05 + 0.04 * r());
    g.fillStyle = shadeHex(base, (r() - 0.5) * 24);
    g.beginPath(); g.moveTo(x - w, px); g.quadraticCurveTo(x + lean * 0.3, px - h * 0.6, x + lean, px - h); g.quadraticCurveTo(x + lean * 0.3 + w * 0.6, px - h * 0.5, x + w, px); g.closePath(); g.fill();
  }
  return c;
}
/** gỗ ván (mặt bàn) */
export function planks(seed = 8, base = '#735036', px = 128, n = 4) {
  const [c, g] = cv(px, px), r = rng(seed), hp = px / n;
  for (let i = 0; i < n; i++) {
    g.fillStyle = shadeHex(base, (r() - 0.5) * 16); g.fillRect(0, i * hp, px, hp);
    for (let k = 0; k < 7; k++) { g.strokeStyle = shadeHex(base, -18 - r() * 14); g.lineWidth = Math.max(1, px / 128); g.beginPath(); const y = i * hp + r() * hp; g.moveTo(0, y); g.bezierCurveTo(px * 0.3, y + (r() - 0.5) * hp * 0.4, px * 0.7, y + (r() - 0.5) * hp * 0.4, px, y); g.stroke(); }
    g.fillStyle = shadeHex(base, -40); g.fillRect(0, i * hp, px, Math.max(1, px / 96));
  }
  return c;
}
/** nhựa đường + vạch đứt giữa đường (theo trục u) */
export function asphalt(seed = 9, base = '#2A2E36', line = '#C9B15A', px = 128) {
  const [c, g] = cv(px, px), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, px, px);
  dots(g, px, px, r, px * 1.1, [shadeHex(base, -14), shadeHex(base, 14)], px * 0.006, px * 0.02);
  g.fillStyle = line; for (let i = 0; i < 2; i++) g.fillRect(i * px / 2 + px * 0.08, px * 0.47, px * 0.3, px * 0.06);
  return c;
}
/** gạch lát vỉa hè / tường phòng */
export function tilesFlat(seed = 10, base = '#6A6D73', grout = '#42454B', px = 64, n = 4) {
  const [c, g] = cv(px, px), r = rng(seed), s = px / n;
  g.fillStyle = grout; g.fillRect(0, 0, px, px);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { g.fillStyle = shadeHex(base, (r() - 0.5) * 10); g.fillRect(i * s + 1, j * s + 1, s - 2, s - 2); }
  return c;
}
/** mặt tiền nhà: tường + ô cửa sổ (một số sáng đèn) */
export function facade(seed = 11, base = '#7E5343', win = '#1D2433', lit = '#DFBA6E', px = 64) {
  const [c, g] = cv(px, px), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, px, px);
  dots(g, px, px, r, px * 0.4, [shadeHex(base, -10), shadeHex(base, 8)], px * 0.01, px * 0.03);
  for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) {
    g.fillStyle = r() < 0.3 ? lit : win; g.fillRect(px * (0.14 + i * 0.5), px * (0.14 + j * 0.5), px * 0.24, px * 0.28);
    g.fillStyle = shadeHex(base, -26); g.fillRect(px * (0.12 + i * 0.5), px * (0.42 + j * 0.5), px * 0.28, px * 0.03);
  }
  return c;
}
export function shadeHex(hex, dl) {
  const n = parseInt(hex.slice(1), 16), k = 1 + dl / 100;
  const ch = (v) => Math.max(0, Math.min(255, Math.round(v * k))).toString(16).padStart(2, '0');
  return `#${ch((n >> 16) & 255)}${ch((n >> 8) & 255)}${ch(n & 255)}`;
}
/** đường chạy cao su tartan (đất nung trầm hạt cao su mịn + vạch làn kem ấm) */
export function tartanTrack(seed = 21, base = '#943F30', line = '#E6E2D8', px = 256, lanes = 4) {
  const [c, g] = cv(px, px), r = rng(seed);
  g.fillStyle = base; g.fillRect(0, 0, px, px);
  dots(g, px, px, r, px * 2.2, [shadeHex(base, -10), shadeHex(base, 9), shadeHex(base, -6)], px * 0.004, px * 0.012);
  const lw = Math.max(2, Math.round(px * 0.014));
  g.fillStyle = line;
  for (let i = 0; i <= lanes; i++) {
    const y = Math.round((i / lanes) * (px - lw));
    g.fillRect(0, y, px, lw);
  }
  return c;
}
/** cỏ sân vận động kẻ sọc cắt cỏ luân phiên (mowed turf stripes tông rêu đêm) */
export function stadiumGrass(seed = 22, base = '#244535', px = 256, stripes = 6) {
  const [c, g] = cv(px, px), r = rng(seed), sw = px / stripes;
  for (let i = 0; i < stripes; i++) {
    g.fillStyle = i % 2 === 0 ? base : shadeHex(base, -10);
    g.fillRect(i * sw, 0, Math.ceil(sw), px);
  }
  dots(g, px, px, r, px * 1.0, [shadeHex(base, -12), shadeHex(base, 8)], px * 0.005, px * 0.015);
  return c;
}
/** vạch xuất phát / vạch đích ô cờ kem-than chì */
export function checkeredStrip(px = 128, rows = 8) {
  const [c, g] = cv(px, px), cell = px / rows;
  for (let y = 0; y < rows; y++) for (let x = 0; x < 2; x++) {
    g.fillStyle = (x + y) % 2 === 0 ? '#E6E2D8' : '#161920';
    g.fillRect(x * (px / 2), y * cell, px / 2, cell);
  }
  return c;
}
