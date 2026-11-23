// lib/motion — thư viện chuyển động dùng chung (bản JS cho engine code-shot).
// Port từ cartoon-short-kit/engine/motion.js; bản Python cùng API nằm ở lib/motion/__init__.py
// (tests/test_motion_lib.py đối chiếu hai bản bằng node). Mọi hàm thuần theo frame → render song song được.
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const lerp3 = (a, b, t) => a.map((v, i) => lerp(v, b[i], t));
export const ramp = (f, a, b) => clamp((f - a) / (b - a));
export const M = {
  smooth: (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); },           // smootherstep (lướt)
  easeOut: (t) => 1 - Math.pow(1 - clamp(t), 3),                                          // nhanh rồi đáp nhẹ
  easeIn: (t) => Math.pow(clamp(t), 3),
  back: (t, s = 1.7) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; },        // vượt rồi về (pop)
  anticip: (t, s = 0.12) => { t = clamp(t); return t < 0.25 ? -s * Math.sin(t / 0.25 * Math.PI) : M.back((t - 0.25) / 0.75); },
  spring: (t, freq = 3, damp = 5) => { t = Math.max(0, t); return 1 - Math.exp(-damp * t) * Math.cos(freq * 2 * Math.PI * t); }, // t tính bằng giây
  linear: (t) => clamp(t),
  // bộ easing chuẩn (đường cong Penner — cùng tên/hình với GSAP, Anime.js, Motion), viết lại không phụ thuộc thư viện
  bounceOut: (t) => {                                                                      // rơi chạm đất nảy 3 lần
    t = clamp(t); const n = 7.5625, d = 2.75;
    if (t < 1 / d) return n * t * t;
    if (t < 2 / d) { t -= 1.5 / d; return n * t * t + 0.75; }
    if (t < 2.5 / d) { t -= 2.25 / d; return n * t * t + 0.9375; }
    t -= 2.625 / d; return n * t * t + 0.984375;
  },
  elastic: (t) => { t = clamp(t); return t <= 0 ? 0 : t >= 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI / 3)) + 1; }, // lò xo vượt nhiều lần
  expoOut: (t) => { t = clamp(t); return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t); },       // phóng rất nhanh rồi phanh gắt
  circOut: (t) => { t = clamp(t) - 1; return Math.sqrt(1 - t * t); },
  sine: (t) => -(Math.cos(Math.PI * clamp(t)) - 1) / 2,                                    // vào/ra êm nhất
  backIn: (t, s = 1.70158) => { t = clamp(t); return (s + 1) * t * t * t - s * t * t; },  // lùi lấy đà rồi phóng
  steps: (t, n = 5) => { t = clamp(t); return t >= 1 ? 1 : Math.floor(t * n) / n; },     // nhảy bậc (đồng hồ, máy đếm)
};
/** Catmull-Rom qua các điểm 3D; u ∈ [0,1] trên toàn đường. */
export const spline = (pts, u) => {
  const n = pts.length - 1, x = clamp(u) * n, i = Math.min(n - 1, Math.floor(x)), t = x - i;
  const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n, i + 2)];
  return p1.map((_, k) => 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t * t * t));
};
/** Rung "lật" 7 frame cho va chạm: trả về s ∈ [-a, a] (đổi dấu mỗi frame, tắt dần). 0 ngoài cửa sổ. */
export const kickAt = (f, kicks = []) => {
  let s = 0;
  for (const k of kicks) { const d = f - k.f; if (d >= 0 && d < 7) s += (d % 2 ? -1 : 1) * k.a * (1 - d / 7); }
  return s;
};
/** Camera từ keys {f,pos,look,fov,roll,ease?,path?}. Mọi đoạn giữ đều creep (push-in) nên không bao giờ đứng hình;
 *  kicks [{f,a}] cho va chạm (roll = s·20°, look lệch s·[0,3,2]). */
export const camFromKeys = (K, f, { creep = 0.0012, kicks = [] } = {}) => {
  let c;
  if (f <= K[0].f) c = { ...K[0] };
  else if (f >= K[K.length - 1].f) c = { ...K[K.length - 1] };
  else {
    const i = K.findIndex((k, j) => f >= k.f && f <= K[j + 1].f), a = K[i], b = K[i + 1];
    const ease = M[b.ease || 'smooth'], t = ease((f - a.f) / (b.f - a.f));
    if (b.path) {
      const pts = [a.pos, ...b.path, b.pos]; c = { pos: spline(pts, t), look: lerp3(a.look, b.look, t), fov: lerp(a.fov, b.fov, t), roll: lerp(a.roll || 0, b.roll || 0, t) };
    } else c = { pos: lerp3(a.pos, b.pos, t), look: lerp3(a.look, b.look, t), fov: lerp(a.fov, b.fov, t), roll: lerp(a.roll || 0, b.roll || 0, t) };
  }
  c = { ...c, look: [...c.look], pos: [...c.pos] };
  c.fov *= 1 - creep * Math.max(0, f - K[0].f) * 0.15;
  const s = kickAt(f, kicks);
  if (s) { c.look = [c.look[0], c.look[1] + s * 3, c.look[2] + s * 2]; c.roll = (c.roll || 0) + s * 20; }
  return c;
};
/** Sống khi đứng yên: thở + lắc nhẹ, xác định theo seed. Dùng cho MỌI nhân vật trên màn hình. */
export const idle = (f, seed = 1) => ({
  bob: 0.006 * Math.sin((f + seed * 11) * 0.11),
  tilt: 1.2 * Math.sin((f + seed * 7) * 0.05),
  headTilt: 1.5 * Math.sin((f + seed * 5) * 0.037 + 1),
});
/** Chớp mắt: mí 4 frame, mỗi 1.3–2.3 s. */
export const blinkAt = (f, seed) => { const per = 38 + (seed * 17) % 31, ph = (((f + seed * 13) % per) + per) % per; return ph < 2 ? 0.5 : ph < 4 ? 1 : 0; };
/** Đi bộ: quãng đường + pha bước. speed m/s, stride m. */
export const walk = (f, f0, speed = 1.1, stride = 0.8) => { const t = Math.max(0, f - f0) / 30; return { dist: t * speed, phase: (t * speed / (2 * stride)) % 1 }; };
/** Làm tròn giá trị trong key của card để canvas chỉ vẽ lại khi dáng đổi thấy được. */
export const q = (x, n = 2) => Math.round(x * 10 ** n) / 10 ** n;

// ================= ĐỘNG TỪ CHUYỂN ĐỘNG (verb) — vòng 10 =================
// verb(name, t, args) → delta {x,y,z,sx,sy,sz,rot,alpha,glow,blur,reveal}; bản Python cùng API: lib/motion/verbs.py
// (tests/test_motion_depth.py đối chiếu từng verb bằng node). t = GIÂY kể từ lúc verb bắt đầu (âm = chưa bắt đầu).
// Đơn vị: x/y/z theo "cỡ vật" (1 = một lần chiều cao vật), y HƯỚNG LÊN, z hướng về camera; rot độ, dương = ngược chiều
// kim đồng hồ; sx/sy/sz/alpha/reveal NHÂN (1 = giữ nguyên); glow/blur CỘNG (0..1); reveal = phần đã lộ (nét vẽ, chữ gõ,
// mặt nạ iris) — engine chưa hỗ trợ reveal thì bỏ qua, alpha đã có dự phòng. Nhóm: in (trước t=0 ẩn) · accent (nhấn, về
// nguyên dạng khi xong) · out (xong thì ẩn) · idle (nghỉ/phụ, lặp tới khi hết args.dur). Mọi verb là hàm thuần (t, args):
// ngẫu nhiên chỉ qua hash01(seed) → worker nào cũng ra cùng giá trị.
export const IDENTITY = () => ({ x: 0, y: 0, z: 0, sx: 1, sy: 1, sz: 1, rot: 0, alpha: 1, glow: 0, blur: 0, reveal: 1 });
/** Hạt giống từ số hoặc chuỗi (FNV-1a trên mã UTF-16) — Python seed_of() ra cùng số. */
export const seedOf = (s) => {
  if (typeof s === 'number') return Number.isFinite(s) ? (Math.trunc(s) >>> 0) : 0;
  const str = String(s ?? ''); let h = 0x811C9DC5;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  return h >>> 0;
};
/** Băm số nguyên 32-bit → [0,1) (không Math.random). */
export const hash01 = (a, b = 0) => {
  let x = (Math.imul(a >>> 0, 0x9E3779B1) ^ Math.imul(((b | 0) + 0x7F4A7C15) >>> 0, 0x85EBCA77)) >>> 0;
  x ^= x >>> 15; x = Math.imul(x, 0x2C1B3C6D) >>> 0; x ^= x >>> 12; x = Math.imul(x, 0x297A2D39) >>> 0; x ^= x >>> 15;
  return (x >>> 0) / 4294967296;
};
const TAU_ = Math.PI * 2;
const bell = (x, c, w) => (Math.abs(x - c) < w ? 0.5 + 0.5 * Math.cos(Math.PI * (x - c) / w) : 0);
const DIRS = { left: [-1, 0], right: [1, 0], up: [0, 1], top: [0, 1], down: [0, -1], bottom: [0, -1] };
const dirv = (d, def) => (Array.isArray(d) ? [Number(d[0]) || 0, Number(d[1]) || 0] : DIRS[d] || DIRS[def]);
const outA = (p, a0) => 1 - clamp((p - a0) / (1 - a0));             // ra: mờ ở đoạn cuối
const sd = (a, k) => hash01(seedOf(a.seed), k);
// Bảng từ vựng: g = nhóm, dur = thời lượng mặc định (s; null = lặp), args = tham số mặc định. Python có cùng bảng + mô tả.
export const VERBS = {
  // ---- vào (in)
  pop: { g: 'in', dur: 0.35, args: { over: 2.2 } },
  drop_bounce: { g: 'in', dur: 0.8, args: { h: 3 } },
  slide_overshoot: { g: 'in', dur: 0.5, args: { from: 'left', dist: 4 } },
  unfold: { g: 'in', dur: 0.6, args: { axis: 'y' } },
  draw_on: { g: 'in', dur: 0.9, args: {} },
  iris: { g: 'in', dur: 0.5, args: {} },
  typewriter: { g: 'in', dur: 0.8, args: { chars: 12 } },
  assemble: { g: 'in', dur: 0.7, args: { seed: 1 } },
  grow_from: { g: 'in', dur: 0.6, args: { anchor: 'bottom' } },
  shatter_in: { g: 'in', dur: 0.55, args: { seed: 1 } },
  fade_up: { g: 'in', dur: 0.5, args: { dist: 0.6 } },
  spin_in: { g: 'in', dur: 0.6, args: { turns: 1 } },
  swing_in: { g: 'in', dur: 0.9, args: { deg: 80 } },
  stamp_in: { g: 'in', dur: 0.4, args: {} },
  zoom_in: { g: 'in', dur: 0.5, args: {} },
  flip_in: { g: 'in', dur: 0.5, args: {} },
  emerge: { g: 'in', dur: 0.5, args: { dist: 1 } },
  // ---- nhấn (accent)
  pulse: { g: 'accent', dur: 0.5, args: { amp: 0.15, count: 1 } },
  shake: { g: 'accent', dur: 0.4, args: { amp: 0.08, freq: 18 } },
  squash: { g: 'accent', dur: 0.45, args: { amp: 0.3 } },
  wobble: { g: 'accent', dur: 0.7, args: { amp: 0.12 } },
  jiggle: { g: 'accent', dur: 0.5, args: { deg: 12 } },
  heartbeat: { g: 'accent', dur: null, args: { bpm: 72, amp: 0.14 } },
  flip: { g: 'accent', dur: 0.5, args: {} },
  flash: { g: 'accent', dur: 0.25, args: {} },
  ripple: { g: 'accent', dur: 0.8, args: { amp: 0.08 } },
  nod: { g: 'accent', dur: 0.5, args: { amp: 0.08 } },
  hop: { g: 'accent', dur: 0.5, args: { h: 0.6 } },
  recoil: { g: 'accent', dur: 0.5, args: { dir: 'left', dist: 0.4 } },
  swell: { g: 'accent', dur: 1.0, args: { amp: 0.3 } },
  shrink: { g: 'accent', dur: 1.0, args: { amp: 0.3 } },
  spin: { g: 'accent', dur: 0.8, args: { turns: 1 } },
  glitch: { g: 'accent', dur: 0.4, args: { seed: 1, amp: 0.3 } },
  stretch: { g: 'accent', dur: 0.35, args: { amp: 0.35, axis: 'y' } },
  highlight: { g: 'accent', dur: 0.6, args: {} },
  // ---- ra (out)
  fly_off: { g: 'out', dur: 0.5, args: { dir: 'right', dist: 5 } },
  fall_away: { g: 'out', dur: 0.7, args: { dist: 4, seed: 1 } },
  dissolve: { g: 'out', dur: 0.6, args: {} },
  fold: { g: 'out', dur: 0.5, args: { axis: 'y' } },
  shrink_out: { g: 'out', dur: 0.35, args: {} },
  burst_out: { g: 'out', dur: 0.45, args: { seed: 1 } },
  sink: { g: 'out', dur: 0.6, args: { dist: 1.2 } },
  evaporate: { g: 'out', dur: 1.0, args: { dist: 1 } },
  slide_out: { g: 'out', dur: 0.45, args: { dir: 'left', dist: 4 } },
  vanish: { g: 'out', dur: 0.35, args: {} },
  zoom_out: { g: 'out', dur: 0.5, args: {} },
  // ---- nghỉ / chuyển động phụ (idle)
  breathe: { g: 'idle', dur: null, args: { rate: 16, amp: 0.03 } },
  float: { g: 'idle', dur: null, args: { amp: 0.08, period: 2.6, seed: 1 } },
  sway: { g: 'idle', dur: null, args: { deg: 6, period: 2.4, seed: 1 } },
  follow_through: { g: 'idle', dur: 1.0, args: { deg: 10 } },
  orbit: { g: 'idle', dur: null, args: { r: 0.5, period: 4, seed: 1 } },
  drift: { g: 'idle', dur: null, args: { amp: 0.1, seed: 1 } },
  flicker: { g: 'idle', dur: null, args: { rate: 12, amp: 0.3, seed: 1 } },
  wag: { g: 'idle', dur: null, args: { freq: 2.5, deg: 18 } },
  shiver: { g: 'idle', dur: null, args: { amp: 0.02 } },
  bob: { g: 'idle', dur: null, args: { spm: 120, amp: 0.06 } },
  spin_loop: { g: 'idle', dur: null, args: { rpm: 10 } },
  tick: { g: 'idle', dur: null, args: { rate: 1, step: 6 } },
};
export const VERB_ALIASES = { pop_in: 'pop', drop: 'drop_bounce', fade_in: 'fade_up', fade_out: 'dissolve', draw: 'draw_on',
  type: 'typewriter', pop_out: 'shrink_out', shatter_out: 'burst_out', heart: 'heartbeat', bounce: 'hop', cadence: 'bob',
  rotate: 'spin_loop', slide_in: 'slide_overshoot', wipe_in: 'iris', settle: 'follow_through', fade: 'dissolve' };
/** Tên verb chuẩn (chấp nhận gạch nối/khoảng trắng/bí danh) hoặc null. */
export const verbName = (name) => {
  const n = String(name ?? '').trim().toLowerCase().replace(/[-\s]+/g, '_');
  return VERBS[n] ? n : (VERB_ALIASES[n] || null);
};
// Thân verb: (D, p, t, a) — p = tiến độ 0..1 (verb lặp: p = 0), t giây, a = args đã gộp mặc định. Sửa D tại chỗ.
const VF = {
  pop: (D, p, t, a) => { const k = Math.max(0, M.back(p, a.over)); D.sx = D.sy = D.sz = k; D.alpha = clamp(p * 4); },
  drop_bounce: (D, p, t, a) => {
    const e = M.bounceOut(p), q = 0.22 * bell(p, 0.3636, 0.06) + 0.12 * bell(p, 0.7273, 0.05) + 0.06 * bell(p, 0.9091, 0.04);
    D.y = a.h * (1 - e) - q * 0.5; D.sy = 1 - q; D.sx = D.sz = 1 + q * 0.8; D.alpha = clamp(p * 12);
  },
  slide_overshoot: (D, p, t, a) => {
    const e = M.back(p, 1.6), v = dirv(a.from, 'left');
    D.x = v[0] * a.dist * (1 - e); D.y = v[1] * a.dist * (1 - e); D.rot = v[0] * 10 * Math.sin(Math.PI * p) * (1 - p); D.alpha = clamp(p * 5);
  },
  unfold: (D, p, t, a) => {
    const k = p < 0.5 ? 0.5 * M.smooth(p * 2) : 0.5 + 0.5 * M.back((p - 0.5) * 2, 1.2);
    if (a.axis === 'x') D.sx = k; else D.sy = k;
    D.reveal = clamp(p * 1.25); D.alpha = clamp(p * 4);
  },
  draw_on: (D, p) => { D.reveal = M.smooth(p); D.alpha = clamp(p * 6); D.glow = 0.35 * Math.sin(Math.PI * p); },
  iris: (D, p) => { const e = M.easeOut(p); D.reveal = e; D.sx = D.sy = 0.92 + 0.08 * e; },
  typewriter: (D, p, t, a) => { D.reveal = M.steps(p, Math.max(1, Math.round(a.chars))); D.alpha = p > 0 ? 1 : 0; },
  assemble: (D, p, t, a) => {
    const e = M.easeOut(p), r = sd(a, 7) - 0.5;
    D.sx = D.sy = 1 + 0.25 * (1 - e); D.rot = 50 * r * (1 - e); D.blur = (1 - e) * 0.8; D.alpha = clamp(p * 2.5); D.reveal = e;
  },
  grow_from: (D, p, t, a) => {
    const k = Math.max(0, M.back(p, 1.4)); D.sy = k; D.sx = D.sz = lerp(0.7, 1, M.easeOut(p));
    D.y = a.anchor === 'top' ? (1 - k) * 0.5 : a.anchor === 'center' ? 0 : -(1 - k) * 0.5; D.alpha = clamp(p * 5);
  },
  shatter_in: (D, p, t, a) => {
    const e = M.easeOut(p);
    D.x = (sd(a, 1) - 0.5) * 0.8 * (1 - e); D.y = (sd(a, 2) - 0.5) * 0.8 * (1 - e); D.rot = (sd(a, 3) - 0.5) * 90 * (1 - e);
    D.sx = D.sy = 1 + 0.6 * (1 - e); D.blur = (1 - p) * (1 - p); D.alpha = clamp(p * 3);
  },
  fade_up: (D, p, t, a) => { D.y = -a.dist * (1 - M.easeOut(p)); D.alpha = M.smooth(p); D.blur = 0.6 * (1 - p); },
  spin_in: (D, p, t, a) => { D.rot = 360 * a.turns * (1 - M.back(p, 1.3)); D.sx = D.sy = M.easeOut(p); D.alpha = clamp(p * 4); },
  swing_in: (D, p, t, a) => { D.rot = a.deg * Math.exp(-5 * p) * Math.cos(3 * Math.PI * p) * (1 - p); D.alpha = clamp(p * 6); },
  stamp_in: (D, p) => {
    const i = 0.45;
    if (p < i) { D.sx = D.sy = lerp(2.4, 1, M.easeIn(p / i)); } else {
      const q = (p - i) / (1 - i);
      D.sx = D.sy = 1 + 0.12 * Math.exp(-6 * q) * Math.cos(15 * q) * (1 - q);
      D.x = 0.05 * Math.exp(-8 * q) * Math.sin(40 * q) * (1 - q); D.glow = Math.max(0, 1 - q * 4) * 0.9;
    }
    D.alpha = clamp(p * 5);
  },
  zoom_in: (D, p) => { const e = M.expoOut(p); D.z = -3 * (1 - e); D.sx = D.sy = lerp(0.2, 1, e); D.blur = (1 - p) * 0.8; D.alpha = clamp(p * 4); },
  flip_in: (D, p) => { D.sx = Math.cos((1 - M.easeOut(p)) * Math.PI / 2); D.alpha = p > 0 ? 1 : 0; },
  emerge: (D, p, t, a) => { const e = M.easeOut(p); D.y = -a.dist * (1 - e); D.reveal = e; D.alpha = clamp(p * 8); },

  pulse: (D, p, t, a) => {
    const q = (p * Math.max(1, Math.round(a.count))) % 1, w = Math.sin(Math.PI * q);
    D.sx = D.sy = D.sz = 1 + a.amp * w; D.glow = 0.5 * w;
  },
  shake: (D, p, t, a) => {
    const d = 1 - p; D.x = a.amp * Math.sin(TAU_ * a.freq * t) * d; D.rot = 3 * Math.sin(TAU_ * a.freq * t * 0.7 + 1) * d;
  },
  squash: (D, p, t, a) => {
    const k = a.amp * Math.exp(-7 * p) * Math.cos(4 * Math.PI * p) * (1 - p);
    D.sy = 1 - k; D.sx = D.sz = 1 + k * 0.8; D.y = -k * 0.5;
  },
  wobble: (D, p, t, a) => { const k = a.amp * Math.exp(-4 * p) * Math.sin(6 * Math.PI * p); D.sx = 1 + k; D.sy = 1 - k; },
  jiggle: (D, p, t, a) => { D.rot = a.deg * Math.exp(-5 * p) * Math.sin(8 * Math.PI * p); },
  heartbeat: (D, p, t, a) => {
    const per = 60 / Math.max(1, a.bpm), ph = (t % per) / per, e = bell(ph, 0.08, 0.08) + 0.6 * bell(ph, 0.34, 0.08);
    D.sx = D.sy = D.sz = 1 + a.amp * e; D.glow = 0.6 * e;
  },
  flip: (D, p) => { D.sx = Math.cos(TAU_ * M.smooth(p)); },
  flash: (D, p) => { D.glow = 1 - p; D.sx = D.sy = 1 + 0.06 * (1 - p); },
  ripple: (D, p, t, a) => { D.sx = D.sy = 1 + a.amp * Math.sin(4 * Math.PI * p) * (1 - p); D.glow = 0.6 * Math.sin(Math.PI * p); },
  nod: (D, p, t, a) => { const w = Math.sin(4 * Math.PI * p) * (1 - p); D.y = -a.amp * w; D.rot = 4 * w; },
  hop: (D, p, t, a) => {
    const sq = 0.15 * bell(p, 0.075, 0.075) + 0.18 * bell(p, 0.9, 0.1), x = (p - 0.15) / 0.65;
    D.y = (p > 0.15 && p < 0.8 ? a.h * 4 * x * (1 - x) : 0) - sq * 0.5; D.sy = 1 - sq; D.sx = D.sz = 1 + sq * 0.8;
  },
  recoil: (D, p, t, a) => {
    const k = p < 0.2 ? M.easeOut(p / 0.2) : 1 - M.smooth((p - 0.2) / 0.8), v = dirv(a.dir, 'left');
    D.x = v[0] * a.dist * k; D.y = v[1] * a.dist * k; D.rot = -v[0] * 8 * k;
  },
  swell: (D, p, t, a) => { D.sx = D.sy = D.sz = 1 + a.amp * M.smooth(p); },
  shrink: (D, p, t, a) => { D.sx = D.sy = D.sz = 1 - a.amp * M.smooth(p); },
  spin: (D, p, t, a) => { D.rot = 360 * a.turns * M.smooth(p); },
  glitch: (D, p, t, a) => {
    if (p >= 1) return;
    const n = Math.floor(t * 24); D.x = (hash01(seedOf(a.seed), n) - 0.5) * a.amp * (1 - p);
    D.alpha = hash01(seedOf(a.seed), n + 101) > 0.2 ? 1 : 0.35;
  },
  stretch: (D, p, t, a) => {
    const w = Math.sin(Math.PI * p);
    if (a.axis === 'x') { D.sx = 1 + a.amp * w; D.sy = 1 - a.amp * 0.5 * w; } else { D.sy = 1 + a.amp * w; D.sx = 1 - a.amp * 0.5 * w; }
  },
  highlight: (D, p) => { const w = Math.sin(Math.PI * p); D.glow = w; D.sx = D.sy = 1 + 0.04 * w; },

  fly_off: (D, p, t, a) => {
    const e = M.backIn(p), v = dirv(a.dir, 'right');
    D.x = v[0] * a.dist * e; D.y = v[1] * a.dist * e; D.rot = -v[0] * 15 * p; D.alpha = outA(p, 0.75);
  },
  fall_away: (D, p, t, a) => { const s = sd(a, 3) > 0.5 ? 1 : -1; D.y = -a.dist * p * p; D.rot = s * 40 * p * p; D.alpha = outA(p, 0.6); },
  dissolve: (D, p) => { D.alpha = 1 - M.smooth(p); D.blur = p; D.sx = D.sy = 1 + 0.08 * p; D.glow = 0.2 * Math.sin(Math.PI * p); },
  fold: (D, p, t, a) => { const k = 1 - M.smooth(p); if (a.axis === 'x') D.sx = k; else D.sy = k; D.reveal = 1 - p; D.alpha = outA(p, 0.8); },
  shrink_out: (D, p) => { D.sx = D.sy = D.sz = Math.max(0, 1 - M.backIn(p, 2.2)); D.alpha = outA(p, 0.85); },
  burst_out: (D, p, t, a) => {
    const e = M.easeOut(p);
    D.sx = D.sy = 1 + 0.8 * e; D.blur = p; D.alpha = 1 - e; D.glow = 0.8 * (1 - p) * clamp(p * 8); D.rot = (sd(a, 5) - 0.5) * 40 * e;
  },
  sink: (D, p, t, a) => { const e = M.easeIn(p); D.y = -a.dist * e; D.reveal = 1 - e; D.alpha = outA(p, 0.9); },
  evaporate: (D, p, t, a) => { D.y = a.dist * M.easeOut(p); D.alpha = 1 - M.smooth(p); D.blur = p; D.sx = 1 + 0.3 * p; D.sy = 1 - 0.2 * p; },
  slide_out: (D, p, t, a) => { const e = M.easeIn(p), v = dirv(a.dir, 'left'); D.x = v[0] * a.dist * e; D.y = v[1] * a.dist * e; D.alpha = outA(p, 0.8); },
  vanish: (D, p) => { D.reveal = 1 - M.easeIn(p); D.sx = D.sy = 1 - 0.1 * p; D.alpha = outA(p, 0.9); },
  zoom_out: (D, p) => { const e = M.easeIn(p); D.z = -3 * e; D.sx = D.sy = lerp(1, 0.2, e); D.blur = 0.8 * p; D.alpha = outA(p, 0.6); },

  breathe: (D, p, t, a) => {
    const w = Math.sin(TAU_ * t / (60 / Math.max(1, a.rate)));
    D.sy = 1 + a.amp * w; D.sx = D.sz = 1 + a.amp * 0.5 * w; D.y = a.amp * w * 0.5;
  },
  float: (D, p, t, a) => { const ph = sd(a, 9) * TAU_; D.y = a.amp * Math.sin(TAU_ * t / a.period + ph); D.rot = 2 * Math.sin(TAU_ * t / (a.period * 1.3) + ph); },
  sway: (D, p, t, a) => { D.rot = a.deg * Math.sin(TAU_ * t / a.period + sd(a, 9) * TAU_); },
  follow_through: (D, p, t, a) => {
    const e = Math.exp(-5 * p); D.rot = a.deg * e * Math.sin(6 * Math.PI * p); D.sx = 1 + 0.04 * e * Math.sin(6 * Math.PI * p + 1) * (1 - p);
  },
  orbit: (D, p, t, a) => {
    const ph = sd(a, 9) * TAU_, w = TAU_ * t / a.period + ph;
    D.x = a.r * (Math.cos(w) - Math.cos(ph)); D.y = 0.35 * a.r * (Math.sin(w) - Math.sin(ph)); D.z = a.r * (Math.sin(w) - Math.sin(ph));
  },
  drift: (D, p, t, a) => {
    const ph = sd(a, 9) * TAU_;
    D.x = a.amp * (Math.sin(0.9 * t + ph) + 0.5 * Math.sin(2.3 * t + 2 * ph) - Math.sin(ph) - 0.5 * Math.sin(2 * ph)) / 1.5;
    D.y = a.amp * (Math.sin(0.7 * t + 3 * ph) + 0.5 * Math.sin(1.9 * t + ph) - Math.sin(3 * ph) - 0.5 * Math.sin(ph)) / 1.5;
  },
  flicker: (D, p, t, a) => { const r = hash01(seedOf(a.seed), Math.floor(t * a.rate)); D.alpha = 1 - a.amp * 0.5 * r; D.glow = a.amp * r; },
  wag: (D, p, t, a) => { D.rot = a.deg * Math.sin(TAU_ * a.freq * t); },
  shiver: (D, p, t, a) => {
    D.x = a.amp * (Math.sin(TAU_ * 23 * t) + 0.7 * Math.sin(TAU_ * 31 * t + 1) - 0.7 * Math.sin(1)); D.rot = 1.5 * Math.sin(TAU_ * 19 * t);
  },
  bob: (D, p, t, a) => {
    const per = 60 / Math.max(1, a.spm); D.y = a.amp * Math.abs(Math.sin(Math.PI * ((t % per) / per))); D.rot = 2 * Math.sin(Math.PI * t / per);
  },
  spin_loop: (D, p, t, a) => { D.rot = -360 * a.rpm / 60 * t; },
  tick: (D, p, t, a) => {
    const q = (t * a.rate) % 1; D.rot = -a.step * Math.floor(t * a.rate) - a.step * 0.15 * Math.exp(-q * 12) * Math.sin(q * 30);
  },
};
/** Một động từ ở thời điểm t (giây kể từ lúc bắt đầu). Tên lạ → không đổi gì (validate ở Python: verb_errors). */
export function verb(name, t, args = {}) {
  const D = IDENTITY(), n = verbName(name);
  if (!n) return D;
  const meta = VERBS[n], a = { ...meta.args, ...(args || {}) }, dur = a.dur ?? meta.dur;
  t = Number(t) || 0;
  if (a.sec !== undefined && a.sec !== null) t = Number(a.sec) || 0;     // gọi kiểu (tiến độ, {sec}) của beats.js: sec = giây thật
  if (t < 0) { if (meta.g === 'in') VF[n](D, 0, 0, a); return D; }
  if (dur === null || dur === undefined) { VF[n](D, 0, t, a); return D; }      // lặp vô hạn
  if (meta.dur === null && t >= dur) return D;                                 // verb lặp có args.dur: hết giờ → dừng
  VF[n](D, dur > 0 ? clamp(t / dur) : 1, t, a);
  return D;
}
/** Gộp nhiều delta: x/y/z/rot/glow/blur cộng, sx/sy/sz/alpha/reveal nhân. */
export function compose(...ds) {
  const o = IDENTITY();
  for (const d of ds.flat()) {
    if (!d) continue;
    for (const k of ['x', 'y', 'z', 'rot', 'glow', 'blur']) o[k] += d[k] ?? 0;
    for (const k of ['sx', 'sy', 'sz', 'alpha', 'reveal']) o[k] *= d[k] ?? 1;
  }
  return o;
}
export const STAGGERS = ['cascade', 'reverse', 'center_out', 'edges_in', 'wave', 'random', 'diagonal'];
/** Độ trễ (giây) của phần tử i trong n phần tử theo một mẫu so le. args: each (s, 0.08), seed, cols. */
export function stagger(pattern, i, n, args = {}) {
  const each = args.each ?? 0.08, m = (n - 1) / 2, pat = String(pattern || 'cascade').replace(/-/g, '_');
  if (pat === 'reverse') return (n - 1 - i) * each;
  if (pat === 'center_out') return Math.abs(i - m) * each;
  if (pat === 'edges_in') return (m - Math.abs(i - m)) * each;
  if (pat === 'wave') return (n - 1) * each * M.sine(i / Math.max(1, n - 1));
  if (pat === 'random' || pat === 'seeded_random') return hash01(seedOf(args.seed ?? 1), i) * (n - 1) * each;
  if (pat === 'diagonal') { const c = args.cols || Math.ceil(Math.sqrt(n)); return ((i % c) + Math.floor(i / c)) * each; }
  return i * each;
}
/** Chạy danh sách `do: [{u | t | f, verb, dur?, args?, stagger?}]` ở frame f của shot N frame → một delta đã gộp.
 *  u = 0..1 của shot (ưu tiên — shot co giãn theo giọng), t = giây, f = frame. i/n: phần tử thứ i trong nhóm n (so le). */
export function play(items, f, N, fps = 30, i = 0, n = 1) {
  const ds = [];
  for (const it of items || []) {
    if (!it || !it.verb) continue;
    let t0 = it.t ?? (it.f !== undefined ? it.f / fps : (it.u ?? 0) * Math.max(0, N - 1) / fps);
    if (it.stagger) t0 += stagger(it.stagger, i, n, it.args || {});
    ds.push(verb(it.verb, f / fps - t0, { ...(it.args || {}), ...(it.dur !== undefined ? { dur: it.dur } : {}) }));
  }
  return compose(ds);
}
/** Delta → toạ độ canvas 2D (y xuống, rot radian theo chiều kim đồng hồ). size = chiều cao vật (px). */
export const canvasDelta = (d, size) => ({ dx: d.x * size, dy: -d.y * size, dz: d.z * size, sx: d.sx, sy: d.sy, rot: -d.rot * Math.PI / 180,
  alpha: clamp(d.alpha), glow: Math.max(0, d.glow), blur: Math.max(0, d.blur), reveal: clamp(d.reveal) });
/** Delta → three.js (y lên, rot.z radian ngược chiều kim đồng hồ). h = chiều cao vật (m). */
export const threeDelta = (d, h) => ({ dx: d.x * h, dy: d.y * h, dz: d.z * h, sx: d.sx, sy: d.sy, sz: d.sz, rotZ: d.rot * Math.PI / 180,
  alpha: clamp(d.alpha), glow: Math.max(0, d.glow), blur: Math.max(0, d.blur), reveal: clamp(d.reveal) });
