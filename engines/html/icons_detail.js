// Vòng 22 — đạo cụ CHI TIẾT (nhìn là nhận ra): vẽ bằng path kiểu SVG trong hộp 0..200 (y xuống), lấy mẫu thành poly của
// engine nên mọi look (flat, boil, sketch, neon, cắt giấy…) vẫn tô bằng bút của nó và three.js ép khối được (icon3d).
// Tô khối bằng `tone` (tối dần về nền) + `alpha` thay cho màu cụ thể → hợp mọi bảng màu. Ghi đè icon đơn giản cùng tên
// (laptop, phone, chip, film, brain, bloodcell, muscle, mitochondria, cup, bed, shoe…) và thêm vật mới (macrophage có miệng
// đớp, fatcell, glycogen, spine có p = độ nén đĩa đệm, capillary có p = độ ép…). Thêm icon = một hàm + từ khoá ở cuối file.

const U = (v) => (v - 100) / 100;                                     // 0..200 → -1..1
const TAU = Math.PI * 2, PI = Math.PI;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

// ---------- path SVG → điểm (M L H V C S Q T Z, tuyệt đối + tương đối) ----------
function pathPts(d) {
  const tok = String(d).match(/[MmLlHhVvCcSsQqTtZz]|-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/g) || [];
  const subs = []; let cur = null, x = 0, y = 0, sx = 0, sy = 0, cmd = '', lc = null, lq = null, i = 0;
  const num = () => parseFloat(tok[i++]);
  const push = (px, py) => { if (!cur) { cur = { pts: [[x, y]], closed: false }; subs.push(cur); } cur.pts.push([px, py]); };
  const cubic = (x1, y1, x2, y2, x3, y3) => {
    const n = 10;
    for (let k = 1; k <= n; k++) { const t = k / n, u = 1 - t; push(u * u * u * x + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3, u * u * u * y + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3); }
    lc = [x2, y2]; lq = null; x = x3; y = y3;
  };
  const quad = (x1, y1, x2, y2) => {
    const n = 8;
    for (let k = 1; k <= n; k++) { const t = k / n, u = 1 - t; push(u * u * x + 2 * u * t * x1 + t * t * x2, u * u * y + 2 * u * t * y1 + t * t * y2); }
    lq = [x1, y1]; lc = null; x = x2; y = y2;
  };
  while (i < tok.length) {
    if (/[A-Za-z]/.test(tok[i])) cmd = tok[i++];
    const rel = cmd === cmd.toLowerCase(), C = cmd.toUpperCase(), ox = rel ? x : 0, oy = rel ? y : 0;
    if (C === 'Z') { if (cur) { cur.closed = true; x = sx; y = sy; } cur = null; lc = lq = null; continue; }
    if (C === 'M') { x = num() + ox; y = num() + oy; sx = x; sy = y; cur = { pts: [[x, y]], closed: false }; subs.push(cur); cmd = rel ? 'l' : 'L'; lc = lq = null; continue; }
    if (C === 'L') { x = num() + ox; y = num() + oy; push(x, y); lc = lq = null; continue; }
    if (C === 'H') { x = num() + ox; push(x, y); lc = lq = null; continue; }
    if (C === 'V') { y = num() + oy; push(x, y); lc = lq = null; continue; }
    if (C === 'C') { const a = num() + ox, b = num() + oy, c = num() + ox, e = num() + oy, f = num() + ox, h = num() + oy; cubic(a, b, c, e, f, h); continue; }
    if (C === 'S') { const r = lc ? [2 * x - lc[0], 2 * y - lc[1]] : [x, y], c = num() + ox, e = num() + oy, f = num() + ox, h = num() + oy; cubic(r[0], r[1], c, e, f, h); continue; }
    if (C === 'Q') { const a = num() + ox, b = num() + oy, c = num() + ox, e = num() + oy; quad(a, b, c, e); continue; }
    if (C === 'T') { const r = lq ? [2 * x - lq[0], 2 * y - lq[1]] : [x, y], c = num() + ox, e = num() + oy; quad(r[0], r[1], c, e); continue; }
    i++;                                                              // lệnh không hỗ trợ (A): bỏ một số, tránh lặp vô hạn
  }
  return subs.filter((s) => s.pts.length > 1);
}
const toU = (pts) => pts.map(([a, b]) => [U(a), U(b)]);
/** Vùng tô từ path: mỗi subpath một poly; o.holes → subpath thứ 2 trở đi là lỗ. */
const F = (d, role, o = {}) => { const { holes, ...q } = o; return pathPts(d).map((s, i) => ({ k: 'poly', pts: toU(s.pts), role, ...q, ...(holes && i ? { hole: true } : {}) })); };
/** Nét (không tô) từ path; w = độ dày theo đơn vị bút của look. */
const S = (d, role, w = 0.6, o = {}) => pathPts(d).map((s) => ({ k: s.closed ? 'poly' : 'line', pts: toU(s.pts), role, w, ...(s.closed ? { fill: false } : {}), ...o }));
const c = (x, y, r, role, o = {}) => ({ k: 'circle', x: U(x), y: U(y), r: r / 100, role, ...o });
const e = (x, y, rx, ry, role, o = {}) => ({ k: 'circle', x: U(x), y: U(y), r: 1, rx: rx / 100, ry: ry / 100, role, ...o });
const r = (x, y, w, h, rad, role, o = {}) => { const { w: sw, ...rest } = o; return { k: 'rect', x: U(x), y: U(y), w: w / 100, h: h / 100, rad: rad / 100, role, ...rest, ...(sw !== undefined ? { sw } : {}) }; };
const pg = (pts, role, o = {}) => ({ k: 'poly', pts: toU(pts), role, ...o });
const ln = (pts, role, w = 0.6, o = {}) => ({ k: 'line', pts: toU(pts), role, w, ...o });
const range = (n, fn) => Array.from({ length: n }, (_, i) => fn(i));
/** băm số nguyên 3 chiều → 0..1 (không tương quan theo đường chéo như sin-hash) */
const ihash = (a, b, c) => { let h = Math.imul(a + 1, 0x27d4eb2d) ^ Math.imul(b + 7, 0x165667b1) ^ Math.imul(c + 13, 0x9e3779b9); h = Math.imul(h ^ (h >>> 15), 0x85ebca6b); h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35); h ^= h >>> 16; return (h >>> 0) / 4294967296; };
const wig = (x0, y0, x1, y1, amp, n, ph = 0) => range(n + 1, (i) => {     // nếp nhăn (rãnh não, vân cơ): đường lượn vuông góc hướng đi
  const t = i / n, dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1, s = Math.sin(t * PI * 3 + ph) * amp * Math.sin(t * PI);
  return [x0 + dx * t - dy / L * s, y0 + dy * t + dx / L * s];
});
const hexPts = (cx, cy, rr, rot = 0) => range(6, (i) => [cx + Math.cos(rot + i * PI / 3) * rr, cy + Math.sin(rot + i * PI / 3) * rr]);
const blob = (cx, cy, rr, bumps, amp, ph = 0, a0 = 0, a1 = TAU, n = 48) => range(n + 1, (i) => {
  const a = a0 + (a1 - a0) * i / n, k = 1 + amp * Math.sin(a * bumps + ph) + amp * 0.4 * Math.sin(a * (bumps + 3) + ph * 1.7);
  return [cx + Math.cos(a) * rr * k, cy + Math.sin(a) * rr * k];
});
const keyRow = (y0, y1, xl0, xr0, xl1, xr1, n, role, o = {}) => range(n, (i) => {   // một hàng phím phối cảnh (hình thang)
  const a = i / n + 0.012, b = (i + 1) / n - 0.012;
  return pg([[xl0 + (xr0 - xl0) * a, y0], [xl0 + (xr0 - xl0) * b, y0], [xl1 + (xr1 - xl1) * b, y1], [xl1 + (xr1 - xl1) * a, y1]], role, o);
});


/** Xe đạp đua nhìn nghiêng (đầu xe bên phải) trong toạ độ đơn vị: gốc = trục giữa (bottom bracket) tại (ox, oy), k = tỉ lệ
 *  (1 = bánh 0.34 — xe thật so với người 1.72 của rig 'human'), a = góc quay đùi đĩa (rad). Trả {prims, pts} (điểm yên/ghi đông/bàn đạp). */
export function bikeParts(ox, oy, k = 1, a = 0, role = 'cold', o = {}) {
  const P = (x, y) => [ox + x * k, oy + y * k], wr = 0.34 * k, rear = P(-0.41, -0.06), front = P(0.6, -0.06);
  const seatTop = P(-0.12, -0.5), saddle = P(-0.15, -0.6), headTop = P(0.47, -0.5), headBot = P(0.5, -0.36), bar = P(0.5, -0.58), bb = P(0, 0);
  const out = [], tone = o.tone || 0, al = o.alpha ?? 1;
  const wheel = (c, spin) => {
    out.push({ k: 'circle', x: c[0], y: c[1], r: 1, rx: wr, ry: wr, role: 'ink', tone: 0.82, fill: false, w: 1.6, alpha: al });
    out.push({ k: 'circle', x: c[0], y: c[1], r: 1, rx: wr * 0.9, ry: wr * 0.9, role: 'dim', tone: 0.15 + tone, fill: false, w: 0.5, alpha: al });
    for (let i = 0; i < 12; i++) { const t = spin + i * Math.PI / 6; out.push({ k: 'line', pts: [[c[0], c[1]], [c[0] + Math.cos(t) * wr * 0.88, c[1] + Math.sin(t) * wr * 0.88]], role: 'dim', tone: 0.35, w: 0.12, fine: true, alpha: al }); }
    out.push({ k: 'circle', x: c[0], y: c[1], r: 1, rx: 0.025 * k, ry: 0.025 * k, role: 'dim', tone: 0.1, alpha: al });
  };
  const tube = (p1, p2, w = 0.9, r = role) => out.push({ k: 'line', pts: [p1, p2], role: r, tone, w, alpha: al });
  if (!o.noWheels) { wheel(rear, a * 0.42); wheel(front, a * 0.42); }
  tube(bb, rear, 0.6); tube(seatTop, rear, 0.55); tube(bb, seatTop, 1.0); tube(seatTop, headTop, 0.85); tube(bb, headBot, 1.1); tube(headTop, headBot, 1.1);
  tube(headBot, front, 0.75); tube(P(-0.12, -0.5), P(-0.14, -0.58), 0.6, 'dim');
  out.push({ k: 'poly', pts: [P(-0.27, -0.61), P(-0.06, -0.61), P(-0.04, -0.58), P(-0.22, -0.57)], role: 'ink', tone: 0.75, alpha: al });
  tube(headTop, bar, 0.7, 'dim'); out.push({ k: 'line', pts: [bar, P(0.6, -0.59), P(0.62, -0.5), P(0.57, -0.46)], role: 'ink', tone: 0.7, w: 0.7, alpha: al });
  out.push({ k: 'circle', x: bb[0], y: bb[1], r: 1, rx: 0.1 * k, ry: 0.1 * k, role: 'dim', tone: 0.25, alpha: al });
  out.push({ k: 'line', pts: [[bb[0], bb[1] - 0.1 * k], [rear[0], rear[1] - 0.04 * k], [rear[0], rear[1] + 0.04 * k], [bb[0], bb[1] + 0.1 * k]], role: 'dim', tone: 0.45, w: 0.25, fine: true, alpha: al });
  const ped = (sgn) => [bb[0] + Math.cos(a + (sgn > 0 ? 0 : Math.PI)) * 0.17 * k, bb[1] + Math.sin(a + (sgn > 0 ? 0 : Math.PI)) * 0.17 * k];
  return { prims: out, saddle, bar, bb, pedal: [ped(1), ped(-1)], crank: (i) => ({ k: 'line', pts: [bb, ped(i ? -1 : 1)], role: 'dim', tone: 0.1, w: 0.5, alpha: al }) };
}
// ---------- vật ----------
export const DETAIL_ICONS = {
  // ======= công nghệ =======
  laptop: ({ f = 0 }) => [
    r(28, 20, 144, 98, 9, 'dim'), r(36, 28, 128, 84, 4, 'bg', { fine: true }),
    c(100, 24, 1.6, 'bg', { fine: true }),
    ...range(7, (i) => r(44 + (i % 3) * 6, 36 + i * 10, [52, 34, 70, 44, 60, 28, 48][i], 4.5, 2,
      ['cold', 'accent', 'ink', 'hot', 'cold', 'accent', 'ink'][i], { fine: true, alpha: 0.85, tone: i % 2 ? 0.1 : 0 })),
    r(50 + [52, 34, 70, 44, 60, 28, 48][6] + 4, 96, 3, 4.5, 0, 'ink', { fine: true, alpha: (f >> 3) % 2 ? 1 : 0.2 }),
    pg([[28, 118], [172, 118], [194, 160], [6, 160]], 'dim', { tone: -0.05 }),
    pg([[6, 160], [194, 160], [192, 167], [8, 167]], 'dim', { tone: 0.38 }),
    ...keyRow(123, 128.5, 36, 164, 34.4, 165.6, 13, 'bg', { fine: true, alpha: 0.75 }),
    ...keyRow(130, 135.5, 34.2, 165.8, 32.6, 167.4, 13, 'bg', { fine: true, alpha: 0.75 }),
    ...keyRow(137, 142.5, 32.4, 167.6, 30.8, 169.2, 12, 'bg', { fine: true, alpha: 0.75 }),
    pg([[62, 144], [138, 144], [139, 149], [61, 149]], 'bg', { fine: true, alpha: 0.75 }),
    pg([[80, 151], [120, 151], [122, 158], [78, 158]], 'dim', { tone: 0.25, fine: true }),
    ln([[30, 118.5], [170, 118.5]], 'dim', 0.35, { tone: 0.45, fine: true }),
  ],
  phone: ({ f = 0, role }) => {
    const apps = ['hot', 'cold', 'accent', 'ink', 'cold', 'hot', 'accent', 'cold', 'ink', 'accent', 'hot', 'cold'];
    return [
      r(58, 6, 84, 188, 20, role || 'dim', { tone: 0.05 }), r(62, 10, 76, 180, 16, 'bg', { fine: true }),
      r(65, 13, 70, 174, 13, 'cold', { tone: 0.72, fine: true }),
      r(88, 18, 24, 7, 3.5, 'bg', { fine: true }),
      r(70, 19, 10, 3, 1, 'ink', { fine: true, alpha: 0.7 }), r(121, 19, 9, 3, 1, 'ink', { fine: true, alpha: 0.7 }),
      r(74, 34, 52, 12, 3, 'ink', { fine: true, alpha: 0.55 }),
      ...apps.map((ro, i) => r(72 + (i % 4) * 14.5, 56 + Math.floor(i / 4) * 17, 11, 11, 3.2, ro, { fine: true, tone: 0.05 })),
      r(70, 160, 60, 18, 7, 'ink', { fine: true, alpha: 0.18 }),
      ...range(4, (i) => r(73 + i * 14.5, 163.5, 11, 11, 3.2, ['cold', 'accent', 'hot', 'ink'][i], { fine: true })),
      r(92, 182, 16, 1.8, 1, 'ink', { fine: true, alpha: 0.8 }),
      r(55.5, 46, 3, 18, 1.5, role || 'dim', { tone: 0.2 }), r(55.5, 70, 3, 18, 1.5, role || 'dim', { tone: 0.2 }), r(141.5, 58, 3, 26, 1.5, role || 'dim', { tone: 0.2 }),
    ];
  },
  chip: ({ f = 0, role }) => {
    const pins = [];
    for (let i = 0; i < 10; i++) {
      const t = 46 + i * 11.6;
      pins.push(r(t - 2.6, 22, 5.2, 18, 1, 'accent', { tone: 0.1 }), r(t - 2.6, 160, 5.2, 18, 1, 'accent', { tone: 0.1 }),
        r(22, t - 2.6, 18, 5.2, 1, 'accent', { tone: 0.1 }), r(160, t - 2.6, 18, 5.2, 1, 'accent', { tone: 0.1 }));
    }
    const glow = 0.5 + 0.5 * Math.sin(f * 0.15);
    const traces = [];
    for (let i = 0; i < 5; i++) {
      traces.push(ln([[70, 76 + i * 12], [58, 76 + i * 12], [52, 70 + i * 14]], 'accent', 0.32, { fine: true, alpha: 0.7 }),
        ln([[130, 76 + i * 12], [142, 76 + i * 12], [148, 70 + i * 14]], 'accent', 0.32, { fine: true, alpha: 0.7 }));
    }
    return [...pins, r(38, 38, 124, 124, 8, 'ink', { tone: 0.82 }), r(42, 42, 116, 116, 6, 'dim', { tone: 0.55, fine: true }), ...traces,
      r(70, 70, 60, 60, 3, role || 'cold', { tone: 0.15 }),
      ...range(16, (i) => r(73 + (i % 4) * 14, 73 + Math.floor(i / 4) * 14, 12, 12, 1, role || 'cold', { fine: true, tone: (i * 7 % 5) * 0.08 + (i === (f >> 2) % 16 ? -0.2 : 0.12), alpha: 0.9 })),
      ln([[70, 100], [130, 100]], 'bg', 0.25, { fine: true, alpha: 0.5 }), ln([[100, 70], [100, 130]], 'bg', 0.25, { fine: true, alpha: 0.5 }),
      c(52, 52, 3.5, 'bg', { fine: true }), r(70, 70, 60, 60, 3, 'ink', { fine: true, fill: false, w: 0.3, alpha: 0.25 + 0.3 * glow })];
  },
  keyboard: () => [
    pg([[22, 70], [178, 70], [196, 140], [4, 140]], 'dim', { tone: 0.05 }), pg([[4, 140], [196, 140], [194, 148], [6, 148]], 'dim', { tone: 0.4 }),
    ...keyRow(76, 86, 28, 172, 25.6, 174.4, 14, 'ink', { tone: 0.72, fine: true }),
    ...keyRow(89, 99, 25, 175, 22.4, 177.6, 14, 'ink', { tone: 0.72, fine: true }),
    ...keyRow(102, 112, 22, 178, 19.4, 180.6, 13, 'ink', { tone: 0.72, fine: true }),
    ...keyRow(115, 125, 19, 181, 16.4, 183.6, 12, 'ink', { tone: 0.72, fine: true }),
    pg([[60, 128], [140, 128], [141.4, 136], [58.6, 136]], 'ink', { tone: 0.72, fine: true }),
  ],
  server: ({ f = 0 }) => [
    r(40, 10, 120, 180, 6, 'dim', { tone: 0.35 }),
    ...range(6, (i) => [r(46, 18 + i * 28, 108, 24, 3, 'dim', { tone: 0.05 }), ...range(8, (j) => r(54 + j * 7, 24 + i * 28, 4, 12, 1, 'bg', { fine: true, alpha: 0.7 })),
      c(132, 30 + i * 28, 3, ((f >> 2) + i * 3) % 7 < 4 ? 'accent' : 'cold', { fine: true }), c(142, 30 + i * 28, 3, ((f >> 3) + i) % 3 ? 'cold' : 'hot', { fine: true, tone: 0.2 })]).flat(),
  ],
  gpu: ({ f = 0 }) => {
    const fan = (cx) => [c(cx, 100, 34, 'ink', { tone: 0.8 }), ...range(7, (i) => { const a = f * 0.35 + i * TAU / 7; return pg([[cx + Math.cos(a) * 6, 100 + Math.sin(a) * 6], [cx + Math.cos(a + 0.5) * 31, 100 + Math.sin(a + 0.5) * 31], [cx + Math.cos(a + 0.95) * 28, 100 + Math.sin(a + 0.95) * 28]], 'dim', { tone: 0.15 }); }), c(cx, 100, 8, 'dim', { tone: 0.3 })];
    return [r(8, 52, 184, 96, 8, 'ink', { tone: 0.65 }), r(12, 56, 176, 88, 6, 'dim', { tone: 0.45, fine: true }), ...fan(58), ...fan(142),
      r(40, 148, 120, 10, 1, 'cold', { tone: 0.45 }), ...range(22, (i) => r(44 + i * 5.2, 150, 3.2, 8, 0.5, 'accent', { fine: true })),
      r(186, 46, 8, 110, 2, 'dim', { tone: 0.1 })];
  },
  // ======= hoạt hình & phim =======
  film: ({ f = 0, p }) => {
    const off = ((f * 0.9) % 60), out = [r(0, 48, 200, 104, 2, 'accent', { tone: 0.62 })];
    for (let i = -1; i < 9; i++) { const x = i * 25 - off * (25 / 60) * 2; out.push(r(x + 6, 53, 12, 9, 2, 'bg', { fine: true }), r(x + 6, 138, 12, 9, 2, 'bg', { fine: true })); }
    const poses = [[0.5, -0.4], [0.15, -0.1], [-0.3, 0.35], [-0.45, 0.5], [-0.1, 0.1], [0.35, -0.35]];
    for (let i = -1; i < 4; i++) {
      const x = i * 60 - (off % 60) + 8, k = ((i + 1 + Math.floor(f * 0.9 / 60)) % poses.length + poses.length) % poses.length, [la, aa] = poses[k];
      if (x > 200 || x + 52 < 0) continue;
      out.push(r(x, 66, 52, 68, 2, 'ink', { tone: 0.06 }));
      const hx = x + 26, hy = 82, hip = [hx, 108];
      out.push(c(hx, hy, 6, 'bg', { fine: true }), ln([[hx, hy + 6], hip], 'bg', 0.5, { fine: true }),
        ln([hip, [hx + Math.sin(la) * 13, 108 + Math.cos(la) * 13], [hx + Math.sin(la) * 13 + 3, 126]], 'bg', 0.5, { fine: true }),
        ln([hip, [hx - Math.sin(la) * 13, 108 + Math.cos(la) * 13], [hx - Math.sin(la) * 13 - 3, 126]], 'bg', 0.5, { fine: true }),
        ln([[hx - 11 * Math.sin(aa) - 4, 98], [hx, 93], [hx + 11 * Math.sin(aa) + 4, 98]], 'bg', 0.5, { fine: true }));
      if (p !== undefined && p > 0 && k % 2) out.push(r(x, 66, 52, 68, 2, 'hot', { fill: false, w: 0.6, fine: true, alpha: clamp(p) }));
    }
    return out;
  },
  reel: ({ f = 0 }) => [c(100, 100, 92, 'dim', { tone: 0.1 }), c(100, 100, 84, 'accent', { tone: 0.62 }),
    ...range(5, (i) => { const a = f * 0.05 + i * TAU / 5; return c(100 + Math.cos(a) * 46, 100 + Math.sin(a) * 46, 20, 'bg', { fine: true }); }),
    c(100, 100, 14, 'dim', { tone: 0.2 }), c(100, 100, 5, 'bg', { fine: true })],
  drawing: ({ p = 0, f = 0 }) => {                                  // giấy vẽ hoạt hình (3 lỗ chốt) + nét chì một tư thế; p = khung 0..1
    const k = Math.max(0, Math.min(4, Math.floor((p || 0) * 5))), la = [0.55, 0.2, -0.25, -0.5, -0.1][k], ya = [0, 4, 8, 4, 0][k], hx = 100 + (k - 2) * 6;
    return [pg([[30, 14], [170, 10], [176, 186], [26, 190]], 'ink', { tone: 0.04 }),
      ...[70, 100, 130].map((x) => c(x, 24, x === 100 ? 4 : 3, 'bg', { fine: true })),
      c(hx, 62 + ya, 15, 'bg', { fine: true, fill: false, w: 0.5 }), ln([[hx, 77 + ya], [hx - 4, 120 + ya]], 'bg', 0.55, { fine: true }),
      ln([[hx - 4, 120 + ya], [hx - 4 + Math.sin(la) * 26, 145 + ya], [hx - 4 + Math.sin(la) * 26 + 8, 170]], 'bg', 0.55, { fine: true }),
      ln([[hx - 4, 120 + ya], [hx - 4 - Math.sin(la) * 26, 145 + ya], [hx - 4 - Math.sin(la) * 26 - 6, 170]], 'bg', 0.55, { fine: true }),
      ln([[hx - 2, 88 + ya], [hx + 22 * Math.sin(-la) + 4, 110 + ya]], 'bg', 0.5, { fine: true }), ln([[hx - 2, 88 + ya], [hx - 22 * Math.sin(-la) - 4, 108 + ya]], 'bg', 0.5, { fine: true }),
      ...range(3, (i) => ln(wig(40, 172 + i * 4, 70, 172 + i * 4, 0.6, 4, f * 0.01 + i), 'dim', 0.25, { fine: true, alpha: 0.5 })),
      r(140, 172, 26, 10, 2, 'dim', { fine: true, alpha: 0.6 })];
  },
  pencil: () => [pg([[30, 150], [150, 30], [170, 50], [50, 170]], 'accent'), pg([[150, 30], [160, 20], [180, 40], [170, 50]], 'hot', { tone: 0.15 }),
    pg([[30, 150], [50, 170], [18, 182]], 'ink', { tone: 0.15 }), pg([[22, 176], [18, 182], [26, 178]], 'bg'),
    ln([[38, 158], [158, 38]], 'accent', 0.3, { tone: 0.3, fine: true })],
  // ======= cơ thể =======
  brain: ({ role, f = 0 }) => {
    const R0 = role || 'hot';
    const out = [
      ...F('M38 104 C30 70 52 36 92 30 C118 20 158 30 172 58 C188 78 186 108 168 120 C160 132 140 140 120 134 C104 142 84 140 74 130 C58 134 42 124 38 104 Z', R0),
      ...F('M150 108 C130 98 100 94 76 102 C74 118 88 132 110 134 C134 137 156 126 150 108 Z', R0, { tone: 0.2 }),
      ...F('M38 104 C34 82 42 64 60 52 C66 72 70 92 74 104 C64 110 48 112 38 104 Z', R0, { tone: 0.12 }),
      ...F('M92 30 C108 24 122 24 126 26 C118 50 112 74 108 96 C96 96 84 98 76 102 C70 80 66 60 62 50 C70 40 80 33 92 30 Z', R0, { tone: 0.06 }),
      ...F('M80 128 C66 132 52 140 50 150 C52 162 74 166 92 156 C100 148 98 136 92 130 Z', R0, { tone: 0.3 }),
      ...F('M96 136 C100 150 102 166 104 184 L116 184 C114 166 112 150 112 136 Z', R0, { tone: 0.24 }),
    ];
    const sul = [[126, 26, 108, 96, 4], [150, 108, 78, 102, 2], [140, 40, 160, 90, 3], [100, 40, 92, 80, 3], [70, 64, 76, 92, 3], [158, 70, 132, 96, 3],
      [118, 112, 92, 122, 2], [132, 118, 108, 128, 2], [48, 88, 62, 100, 2], [84, 44, 70, 56, 2]];
    sul.forEach(([a, b, x, y, amp], i) => out.push(ln(wig(a, b, x, y, amp, 12, i), 'bg', 0.42, { fine: true, alpha: 0.55 })));
    for (let i = 0; i < 4; i++) out.push(ln(range(9, (k) => { const t = k / 8; return [56 + t * 38, 140 + i * 5 + Math.sin(t * PI) * 4 - i * 1.5]; }), 'bg', 0.3, { fine: true, alpha: 0.45 }));
    out.push(e(140, 50, 18, 8, 'ink', { alpha: 0.12 + 0.03 * Math.sin(f * 0.05), fine: true, rot: 0.4 }));
    return out;
  },
  neuron: ({ f = 0, role }) => {
    const R0 = role || 'accent', pulse = ((f * 0.02) % 1);
    const out = [];
    const den = [[48, 70, 18, 40], [44, 96, 10, 100], [50, 124, 22, 160], [64, 64, 50, 18], [66, 136, 60, 186]];
    den.forEach(([x0, y0, x1, y1], i) => { out.push(ln(wig(62, 100, x1, y1, 2, 8, i), R0, 0.9, { tone: 0.05 })); out.push(ln([[x0 + (x1 - x0) * 0.55, y0 + (y1 - y0) * 0.55], [x1 + (i % 2 ? -14 : 12), y1 + 10]], R0, 0.5, { tone: 0.1 })); });
    out.push(ln([[70, 100], [178, 100]], R0, 0.8, { tone: 0.05 }));
    for (let i = 0; i < 4; i++) out.push(r(86 + i * 22, 94, 18, 12, 6, 'ink', { tone: 0.15 }));
    for (const [dx, dy] of [[194, 84], [196, 100], [192, 116]]) { out.push(ln([[178, 100], [dx - 6, dy]], R0, 0.5)); out.push(c(dx - 4, dy, 4, R0)); }
    out.push(c(62, 100, 20, R0), c(60, 98, 8, R0, { tone: 0.35 }), c(58, 96, 3, 'ink', { alpha: 0.35, fine: true }));
    out.push(c(86 + pulse * 100, 100, 4, 'ink', { fine: true, alpha: 0.9 }));
    return out;
  },
  bloodcell: ({ f = 0, role }) => {                               // hồng cầu: đĩa lõm hai mặt — mặt chính diện, nghiêng, mặt cắt
    const R0 = role || 'hot', w = Math.sin(f * 0.06) * 2;
    return [
      c(78, 86, 60, R0), e(78, 90, 30, 28, R0, { tone: 0.32 }), e(70, 82, 20, 16, R0, { tone: 0.18 }),
      { k: 'arc', x: U(78), y: U(86), r: 0.52, a0: -2.7, a1: -1.5, role: 'ink', w: 0.6, alpha: 0.35, fine: true },
      e(150, 150, 40, 22, R0, { rot: -0.5 + w * 0.01, tone: 0.06 }), e(152, 149, 20, 10, R0, { rot: -0.5, tone: 0.34 }),
      ...F('M128 30 C128 18 146 16 156 24 C162 28 170 28 176 24 C186 16 202 20 200 32 C198 44 184 46 176 40 C170 36 162 36 156 40 C146 46 128 44 128 30 Z', R0, { tone: 0.12 }),
    ];
  },
  rbc: ({ role, p = 0 }) => {                                     // một hồng cầu; p = bị ép (0 tròn → 1 dẹt + vỡ)
    const R0 = role || 'hot', sq = clamp(p), sx = 1 + sq * 0.35, sy = 1 - sq * 0.55;
    const out = [e(100, 100, 84 * sx, 84 * sy, R0), e(100, 104, 42 * sx, 40 * sy, R0, { tone: 0.32 }), e(92, 96, 26 * sx, 22 * sy, R0, { tone: 0.16 }),
      { k: 'arc', x: 0, y: 0, r: 1, rx: 0.72 * sx, ry: 0.72 * sy, a0: -2.7, a1: -1.5, role: 'ink', w: 0.7, alpha: 0.35, fine: true }];
    if (sq > 0.75) out.push(...range(5, (i) => c(100 + Math.cos(i * 1.3) * 100 * sx, 100 + Math.sin(i * 1.3) * 40, 5, R0, { alpha: (sq - 0.75) * 4, tone: 0.2 })));
    return out;
  },
  macrophage: ({ f = 0, p, role }) => {                           // bạch cầu (đại thực bào) có "miệng" đớp: p > 0.5 = tự đớp, p ≤ 0.5 = mở p×2
    const R0 = role || 'ink', auto = p === undefined || p === null || p > 0.5;
    const open = auto ? 0.5 + 0.5 * Math.sin(f * 0.42) : clamp(p * 2);              // p > 0.5 (mặc định của scene): đớp liên tục
    const m = 0.08 + open * 0.62, body = blob(100, 100, 74, 5, 0.07, f * 0.03, m, TAU - m, 60);
    return [pg([[100, 100], ...body], R0, { tone: 0.12 }),
      pg(blob(96, 98, 64, 5, 0.06, f * 0.03 + 1, m + 0.12, TAU - m - 0.12, 50).concat([[100, 100]]), R0, { tone: 0.02, alpha: 0.9 }),
      ...F('M60 72 C70 58 92 60 96 72 C100 82 90 88 84 90 C92 96 96 108 88 118 C78 128 60 122 58 110 C56 102 64 98 66 94 C58 90 54 80 60 72 Z', 'accent', { tone: 0.25 }),
      ...range(9, (i) => c(70 + (i * 37 % 60), 70 + (i * 53 % 70), 3, 'accent', { tone: 0.05, fine: true, alpha: 0.8 })),
      c(112, 64, 5, 'bg', { fine: true, alpha: 0.85 })];
  },
  chomper: ({ f = 0, p, role }) => {                               // protein "dọn dẹp" (vd haptoglobin) có miệng đớp — p như macrophage
    const R0 = role || 'cold', auto = p === undefined || p === null || p > 0.5, open = auto ? 0.5 + 0.5 * Math.sin(f * 0.5) : clamp(p * 2);
    const m = 0.06 + open * 0.6, body = blob(100, 100, 70, 7, 0.05, 1.3, m, TAU - m, 56);
    return [pg([[100, 100], ...body], R0, { tone: 0.1 }),
      ...S('M60 70 C80 50 110 60 104 80 C98 100 70 96 72 118 C74 138 108 140 120 128', 'ink', 0.5, { alpha: 0.35, fine: true }),
      ...S('M50 110 C60 130 80 150 100 148', 'ink', 0.4, { alpha: 0.3, fine: true }), c(96, 62, 6, 'bg', { fine: true, alpha: 0.85 })];
  },
  fatcell: ({ role, p = 0 }) => {                                 // tế bào mỡ: giọt lipid lớn chiếm gần hết tế bào; p = co lại (đốt mỡ)
    const k = 1 - clamp(p) * 0.45, R0 = role || 'accent';
    return [c(100, 100, 86, 'ink', { tone: 0.55 }), c(100, 100, 80, 'ink', { tone: 0.35 }),
      c(104, 98, 72 * k, R0), e(84 - 6 * (1 - k), 74, 26 * k, 14 * k, 'ink', { alpha: 0.35, fine: true, rot: -0.5 }),
      ...F('M150 150 C162 136 170 118 172 100 C176 116 172 140 160 156 C156 158 150 156 150 150 Z', 'cold', { tone: 0.15 })];
  },
  fat: ({ role, p = 0, f = 0 }) => {                              // mô mỡ: chùm tế bào mỡ xếp sát (mặt cắt), p = co lại
    const R0 = role || 'accent', k = 1 - clamp(p) * 0.45;
    const cells = [[62, 66, 46], [140, 60, 44], [100, 132, 48], [36, 140, 34], [168, 136, 34], [100, 26, 26]];
    const out = [];
    for (const [x, y, rr] of cells) out.push(c(x, y, rr + 4, 'ink', { tone: 0.5 }));
    cells.forEach(([x, y, rr], i) => {
      out.push(c(x, y, rr, 'ink', { tone: 0.32 }), c(x + 2, y, rr * 0.88 * k, R0, { tone: i % 2 ? 0.06 : 0 }),
        e(x - rr * 0.3, y - rr * 0.35, rr * 0.3 * k, rr * 0.15 * k, 'ink', { alpha: 0.3, fine: true, rot: -0.5 }),
        e(x + rr * 0.72, y + rr * 0.45, rr * 0.16, rr * 0.07, 'cold', { tone: 0.15, rot: 1, fine: true }));
    });
    if (p > 0.05) out.push(...range(6, (i) => { const u = ((f * 0.02 + i / 6) % 1); return c(100 + Math.cos(i * 2.1) * (60 + u * 50), 100 + Math.sin(i * 2.1) * (60 + u * 50), 4 * (1 - u), R0, { alpha: clamp(p) * (1 - u) }); }));
    return out;
  },
  glycogen: ({ role, p = 0, f = 0 }) => {                         // hạt glycogen: chuỗi glucose (lục giác) phân nhánh quanh lõi; p = đã dùng hết
    const R0 = role || 'cold', used = clamp(p), out = [], nodes = [], bonds = [];
    for (let b = 0; b < 6; b++) {
      const a = b * TAU / 6 + 0.3, chain = [[100, 100]];
      for (let k = 1; k <= 4; k++) chain.push([100 + Math.cos(a) * k * 19, 100 + Math.sin(a) * k * 19]);
      chain.slice(1).forEach((q, k) => { nodes.push(q); bonds.push([chain[k], q]); });
      const root = chain[2], a2 = a + (b % 2 ? 0.75 : -0.75);
      let prev = root;
      for (let k = 1; k <= 2; k++) { const q = [root[0] + Math.cos(a2) * k * 19, root[1] + Math.sin(a2) * k * 19]; nodes.push(q); bonds.push([prev, q]); prev = q; }
    }
    const gone = (i) => used * nodes.length > nodes.length - 1 - (i * 31 % nodes.length);
    bonds.forEach(([a, q]) => { const i = nodes.indexOf(q); if (!gone(i)) out.push(ln([a, q], 'ink', 0.5, { tone: 0.3 })); });
    nodes.forEach(([x, y], i) => { if (!gone(i)) out.push(pg(hexPts(x, y, 9, 0.5), R0, { tone: (i % 3) * 0.06 }), pg(hexPts(x, y, 4.2, 0.5), 'bg', { fine: true, alpha: 0.45 })); });
    out.push(c(100, 100, 12, 'ink', { tone: 0.15 }), c(100, 100, 5, 'bg', { fine: true, alpha: 0.6 + 0.2 * Math.sin(f * 0.1) }));
    return out;
  },
  glucose: ({ role }) => {
    const R0 = role || 'cold', P = hexPts(100, 100, 50, PI / 6);
    return [pg(P, 'ink', { fill: false, w: 1.2 }), c(P[0][0], P[0][1], 12, 'hot'), ...P.slice(1).map(([x, y]) => c(x, y, 7, 'ink', { tone: 0.3 })),
      ...[[1, 0], [2, 1], [3, 0], [4, 1]].map(([i, up]) => ln([P[i], [P[i][0] + (P[i][0] - 100) * 0.45, P[i][1] + (P[i][1] - 100) * 0.45]], 'ink', 0.8, { tone: 0.2 })),
      ...[1, 2, 3, 4].map((i) => c(P[i][0] + (P[i][0] - 100) * 0.55, P[i][1] + (P[i][1] - 100) * 0.55, 8, R0))];
  },
  bread: () => [
    ...F('M38 166 L38 84 C22 78 20 44 52 36 C72 18 128 18 148 36 C180 44 178 78 162 84 L162 166 C162 172 158 176 152 176 L48 176 C42 176 38 172 38 166 Z', 'accent', { tone: 0.45 }),
    ...F('M48 164 L48 88 C34 82 34 52 58 46 C76 30 124 30 142 46 C166 52 166 82 152 88 L152 164 Z', 'ink', { tone: 0.12 }),
    ...[[70, 80, 7, 5], [108, 66, 5, 4], [128, 100, 8, 5], [84, 120, 6, 4], [118, 138, 7, 4], [66, 148, 5, 3], [98, 96, 4, 3], [136, 66, 4, 3]].map(([x, y, a, b]) => e(x, y, a, b, 'accent', { tone: 0.55, fine: true, alpha: 0.6 })),
  ],
  pasta: ({ f = 0 }) => [
    ...F('M14 96 L186 96 C184 140 150 170 100 172 C50 170 16 140 14 96 Z', 'ink', { tone: 0.08 }), e(100, 96, 86, 16, 'ink', { tone: 0.3 }),
    ...range(9, (i) => ln(wig(30 + i * 3, 92 - (i % 3) * 6, 170 - i * 4, 90 - (i % 2) * 8, 6, 10, i + f * 0.02), 'accent', 0.9, { tone: (i % 3) * 0.08 })),
    e(100, 80, 18, 8, 'hot', { tone: 0.1 }), ...F('M140 40 L132 86 M150 42 L140 88 M160 44 L148 90', 'dim', 0.6),
  ],
  vertebra: ({ role }) => {                                        // đốt sống thắt lưng nhìn nghiêng (trước = phải)
    const R0 = role || 'ink';
    return [...F('M98 62 C98 54 104 50 112 50 L158 50 C166 50 172 56 172 64 L172 124 C172 132 166 138 158 138 L112 138 C104 138 98 132 98 124 Z', R0, { tone: 0.1 }),
      ...F('M100 72 L74 70 C66 70 60 76 62 84 L66 112 C68 120 76 122 84 120 L100 116 Z', R0, { tone: 0.2 }),
      ...F('M66 86 L34 102 C24 108 22 120 32 122 C44 124 56 116 68 108 Z', R0, { tone: 0.16 }),
      ...F('M76 70 L70 52 C70 46 78 44 82 50 L88 70 Z', R0, { tone: 0.22 }), ...F('M80 120 L76 138 C76 144 84 146 88 140 L92 120 Z', R0, { tone: 0.22 }),
      ...range(5, (i) => ln([[106, 62 + i * 15], [164, 64 + i * 15]], 'bg', 0.25, { fine: true, alpha: 0.35 }))];
  },
  spine: ({ role, p = 0, f = 0 }) => {                            // đoạn cột sống nghiêng: 3 đốt + 2 đĩa đệm; p = đĩa bị nén (mất nước)
    const R0 = role || 'ink', sq = clamp(p), dh = 26 * (1 - 0.42 * sq), vh = 40, out = [];
    let y = 100 - (3 * vh + 2 * dh) / 2;
    for (let i = 0; i < 3; i++) {
      out.push(...F(`M86 ${y + 6} C86 ${y + 2} 90 ${y} 94 ${y} L160 ${y} C164 ${y} 168 ${y + 3} 168 ${y + 7} L168 ${y + vh - 7} C168 ${y + vh - 3} 164 ${y + vh} 160 ${y + vh} L94 ${y + vh} C90 ${y + vh} 86 ${y + vh - 2} 86 ${y + vh - 6} Z`, R0, { tone: 0.1 }),
        ...F(`M88 ${y + 10} L62 ${y + 8} C56 ${y + 9} 54 ${y + 14} 56 ${y + 20} L58 ${y + 30} C60 ${y + 35} 66 ${y + 36} 72 ${y + 34} L88 ${y + 30} Z`, R0, { tone: 0.2 }),
        ...F(`M58 ${y + 18} L30 ${y + 30} C22 ${y + 34} 22 ${y + 42} 30 ${y + 42} C40 ${y + 42} 50 ${y + 36} 60 ${y + 30} Z`, R0, { tone: 0.16 }),
        ln([[96, y + vh * 0.35], [158, y + vh * 0.35]], 'bg', 0.25, { fine: true, alpha: 0.3 }), ln([[96, y + vh * 0.7], [158, y + vh * 0.7]], 'bg', 0.25, { fine: true, alpha: 0.3 }));
      y += vh;
      if (i < 2) {
        const bulge = sq * 7;
        out.push(...F(`M90 ${y + 2} L164 ${y + 2} C${170 + bulge} ${y + 4} ${170 + bulge} ${y + dh - 4} 164 ${y + dh - 2} L90 ${y + dh - 2} C${84 - bulge * 0.6} ${y + dh - 4} ${84 - bulge * 0.6} ${y + 4} 90 ${y + 2} Z`, 'cold', { tone: 0.18 }),
          e(127, y + dh / 2, 22 + sq * 6, dh * 0.3, 'cold', { tone: -0.1 }), e(122, y + dh / 2 - dh * 0.12, 8, dh * 0.08, 'ink', { alpha: 0.35, fine: true }));
        if (sq > 0.05) for (let k = 0; k < 3; k++) { const u = (f * 0.025 + k / 3 + i * 0.4) % 1; out.push(...F(`M${176 + u * 18} ${y + dh / 2 - 4 - k * 3} C${180 + u * 18} ${y + dh / 2 + 2} ${172 + u * 18} ${y + dh / 2 + 2} ${176 + u * 18} ${y + dh / 2 - 4 - k * 3} Z`, 'cold', { alpha: sq * (1 - u) })); }
        y += dh;
      }
    }
    return out;
  },
  disc: ({ role, p = 0 }) => {                                     // đĩa đệm nhìn từ trên: vòng sợi + nhân nhầy; p = mất nước
    const R0 = role || 'cold', k = 1 - clamp(p) * 0.35;
    return [e(100, 104, 90, 74, R0, { tone: 0.3 }), ...range(6, (i) => e(100, 104, 88 - i * 8, 72 - i * 6.5, R0, { fill: false, w: 0.35, tone: 0.05, alpha: 0.8 })),
      e(100, 104, 36 * k, 28 * k, R0, { tone: -0.15 }), e(92, 98, 12 * k, 7 * k, 'ink', { alpha: 0.35, fine: true }),
      ...F('M70 168 C80 160 120 160 130 168 L124 184 L76 184 Z', 'ink', { tone: 0.2 })];
  },
  muscle: ({ role, p = 0 }) => {                                   // bắp cơ hình thoi + gân hai đầu + thớ cơ; p = vết rách nhỏ
    const R0 = role || 'hot', out = [
      ...F('M20 100 C26 86 30 84 40 82 C70 54 130 54 160 82 C170 84 174 86 180 100 C174 114 170 116 160 118 C130 146 70 146 40 118 C30 116 26 114 20 100 Z', R0),
      ...F('M4 96 L28 92 L28 108 L4 104 Z', 'ink', { tone: 0.15 }), ...F('M196 96 L172 92 L172 108 L196 104 Z', 'ink', { tone: 0.15 }),
      ...F('M42 112 C70 136 130 136 158 112 C130 126 70 126 42 112 Z', R0, { tone: 0.22 }),
    ];
    for (let i = 0; i < 7; i++) { const yy = 74 + i * 9; out.push(ln(range(13, (k) => { const t = k / 12, x = 36 + t * 128; return [x, 100 + (yy - 100) * Math.sin(t * PI) * 1.05]; }), 'bg', 0.3, { fine: true, alpha: 0.45 })); }
    const tears = Math.round(clamp(p) * 6);
    for (let i = 0; i < tears; i++) { const x = 60 + i * 15, y = 84 + (i * 23 % 32); out.push(ln([[x, y], [x + 4, y + 5], [x - 1, y + 9], [x + 3, y + 14]], 'accent', 0.5, { fine: true }), c(x + 2, y + 7, 5, 'accent', { alpha: 0.35, fine: true })); }
    out.push(e(84, 76, 26, 6, 'ink', { alpha: 0.18, fine: true, rot: -0.1 }));
    return out;
  },
  musclefiber: ({ role, p = 0 }) => {                             // mặt cắt ngang bắp cơ: bao cơ → bó sợi → sợi cơ
    const R0 = role || 'hot', out = [c(100, 100, 92, R0, { tone: 0.38 }), c(100, 100, 86, R0, { tone: 0.3 })];
    const fas = [[100, 100], ...range(6, (i) => [100 + Math.cos(i * PI / 3) * 50, 100 + Math.sin(i * PI / 3) * 50])];
    fas.forEach(([x, y], j) => {
      out.push(c(x, y, 26, R0, { tone: 0.12 }));
      for (let i = 0; i < 7; i++) { const [fx, fy] = i ? [x + Math.cos(i * PI / 3 + j) * 14, y + Math.sin(i * PI / 3 + j) * 14] : [x, y]; const hurt = p > 0 && ((i + j * 3) % 5 === 0) && p > (j / 7); out.push(c(fx, fy, 6.4, hurt ? 'accent' : R0, { tone: hurt ? 0 : -0.06, fine: true })); }
    });
    return out;
  },
  fiber: ({ role, p = 0, f = 0 }) => {                             // một sợi cơ dọc: vân sáng/tối (sarcomere) + tơ cơ; p = vi chấn thương
    const R0 = role || 'hot', out = [r(4, 62, 192, 76, 38, R0, { tone: 0.15 })];
    for (let i = 0; i < 16; i++) out.push(r(10 + i * 11.6, 64, 5.5, 72, 2, R0, { tone: 0.34, fine: true, alpha: 0.85 }));
    for (let i = 0; i < 5; i++) out.push(ln([[8, 72 + i * 14], [192, 72 + i * 14]], 'ink', 0.2, { fine: true, alpha: 0.22 }));
    const n = Math.round(clamp(p) * 4);
    for (let i = 0; i < n; i++) {
      const x = 40 + i * 38;
      out.push(pg([[x - 3, 62], [x + 5, 76], [x - 2, 92], [x + 6, 108], [x - 1, 124], [x + 4, 138], [x + 12, 138], [x + 7, 124], [x + 12, 108], [x + 5, 92], [x + 12, 76], [x + 5, 62]], 'bg'),
        c(x + 4, 100, 16 + 3 * Math.sin(f * 0.2 + i), 'accent', { alpha: 0.22, fine: true }));
    }
    out.push(r(14, 66, 172, 8, 4, 'ink', { alpha: 0.15, fine: true }));
    return out;
  },
  mitochondria: ({ role, f = 0 }) => {
    const R0 = role || 'accent', out = [e(100, 100, 94, 56, R0, { tone: 0.2 }), e(100, 100, 86, 48, R0, { tone: 0.42 })];
    for (let i = 0; i < 7; i++) {
      const x = 32 + i * 22, top = i % 2 === 0, h = 30 + (i % 3) * 6;
      out.push(r(x - 6, top ? 100 - 48 * Math.sqrt(1 - ((x - 100) / 86) ** 2) - 2 : 100 + 48 * Math.sqrt(1 - ((x - 100) / 86) ** 2) - h + 2, 12, h, 6, R0, { tone: 0.04 }));
    }
    out.push(...range(10, (i) => c(40 + (i * 37 % 120), 80 + (i * 29 % 40), 2.4, 'ink', { alpha: 0.35 + 0.2 * Math.sin(f * 0.1 + i), fine: true })));
    out.push(e(80, 64, 30, 6, 'ink', { alpha: 0.16, fine: true, rot: -0.1 }));
    return out;
  },
  heart: ({ role, f = 0, p }) => {                                // tim giải phẫu cách điệu: thất, động mạch chủ, động mạch phổi, mạch vành
    const R0 = role || 'hot', beat = p === undefined ? Math.max(0, Math.sin(f * 0.21)) ** 6 : 0, k = 1 + beat * 0.05;
    const out = [
      ...S('M98 72 C98 40 104 28 122 26 C140 24 150 36 150 54', R0, 2.6, { tone: 0.05 }),
      ...S('M112 28 L110 10 M124 26 L126 8 M136 30 L144 14', R0, 1.1, { tone: 0.1 }),
      ...S('M88 74 C84 56 74 46 58 44', 'cold', 2.2, { tone: 0.15 }),
      ...S('M132 70 L134 34', 'cold', 2.0, { tone: 0.3 }),
    ];
    const sc = (d) => d.replace(/(-?\d+\.?\d*) (-?\d+\.?\d*)/g, (_, a, b) => `${100 + (a - 100) * k} ${110 + (b - 110) * k}`);
    out.push(...F(sc('M70 74 C52 88 46 122 70 152 C86 170 106 182 120 184 C136 166 162 140 164 108 C166 84 150 68 130 66 C114 60 88 62 70 74 Z'), R0),
      ...F(sc('M120 184 C136 166 162 140 164 108 C166 90 158 78 146 72 C150 100 140 140 120 184 Z'), R0, { tone: 0.18 }),
      ...S(sc('M106 72 C112 100 112 140 120 182'), 'accent', 0.45, { tone: 0.2, alpha: 0.8 }),
      ...S(sc('M80 90 C76 110 82 130 94 146 M140 82 C146 96 146 116 140 130'), 'accent', 0.3, { tone: 0.25, alpha: 0.7 }),
      e(84, 96, 14, 8, 'ink', { alpha: 0.18, fine: true, rot: -0.6 }));
    return out;
  },
  lungs: ({ role, f = 0, p }) => {
    const R0 = role || 'hot', b = 1 + (p === undefined ? Math.sin(f * 0.06) * 0.03 : clamp(p) * 0.06);
    const L = (d, o) => F(d.replace(/(-?\d+\.?\d*) (-?\d+\.?\d*)/g, (_, a, c2) => `${100 + (a - 100) * b} ${110 + (c2 - 110) * b}`), R0, o);
    const out = [
      ...L('M86 52 C60 50 30 80 24 124 C20 156 30 180 50 182 C70 184 84 172 88 150 L90 70 C90 60 90 54 86 52 Z', { tone: 0.05 }),
      ...L('M114 52 C140 50 170 80 176 124 C180 156 170 180 150 182 C130 184 120 174 114 156 C120 150 120 140 112 134 L110 70 C110 60 110 54 114 52 Z', { tone: 0.12 }),
      r(94, 8, 12, 56, 5, 'ink', { tone: 0.2 }), ...range(7, (i) => ln([[94, 14 + i * 7], [106, 14 + i * 7]], 'bg', 0.3, { fine: true, alpha: 0.5 })),
    ];
    out.push(...S('M100 62 L86 76 L66 96 M86 76 L80 110 M66 96 L50 112 M66 96 L60 136 M80 110 L66 150', 'bg', 0.4, { fine: true, alpha: 0.6 }),
      ...S('M100 62 L114 76 L134 96 M114 76 L120 110 M134 96 L150 112 M134 96 L140 136 M120 110 L134 150', 'bg', 0.4, { fine: true, alpha: 0.6 }),
      ...S('M30 120 C50 116 70 122 86 128 M118 112 C140 108 160 114 172 122 M120 146 C140 144 158 150 170 158', 'bg', 0.3, { fine: true, alpha: 0.35 }));
    return out;
  },
  liver: ({ role }) => {
    const R0 = role || 'hot';
    return [...F('M18 84 C30 52 110 40 182 52 C194 58 190 74 170 88 C140 110 100 128 64 136 C40 140 22 128 18 110 C16 100 16 92 18 84 Z', R0, { tone: 0.32 }),
      ...F('M110 48 C150 46 180 50 182 52 C194 58 190 74 170 88 C150 102 128 112 112 118 C118 96 118 70 110 48 Z', R0, { tone: 0.42 }),
      ...S('M110 48 C118 70 118 96 112 118', 'bg', 0.4, { fine: true, alpha: 0.6 }),
      ...F('M96 122 C94 136 100 150 110 152 C118 152 120 140 114 126 Z', 'cold', { tone: 0.3 }),
      e(70, 70, 34, 9, 'ink', { alpha: 0.12, fine: true, rot: -0.15 })];
  },
  capillary: ({ f = 0, p = 0, role }) => {                        // mao mạch dọc + hồng cầu trôi; p = bị ép ở giữa (bàn chân chạm đất)
    const R0 = role || 'hot', sq = clamp(p), pinch = (x) => 24 - sq * 16 * Math.exp(-(((x - 100) / 36) ** 2));
    const top = range(41, (i) => [i * 5, 100 - pinch(i * 5) - 8]), bot = range(41, (i) => [200 - i * 5, 100 + pinch(200 - i * 5) + 8]);
    const out = [pg([...range(41, (i) => [i * 5, 100 - pinch(i * 5) - 20]), ...range(41, (i) => [200 - i * 5, 100 - pinch(200 - i * 5) - 8])], R0, { tone: 0.42 }),
      pg([...range(41, (i) => [i * 5, 100 + pinch(i * 5) + 8]), ...range(41, (i) => [200 - i * 5, 100 + pinch(200 - i * 5) + 20])], R0, { tone: 0.42 }),
      pg([...top, ...bot], R0, { tone: 0.7 })];
    for (let i = 0; i < 6; i++) {
      const x = ((f * 1.6 + i * 38) % 236) - 18, h = pinch(x), squish = clamp(1 - h / 24), burst = sq > 0.7 && Math.abs(x - 100) < 22 && i % 2 === 0;
      if (burst) { out.push(...range(5, (k) => c(x + Math.cos(k * 1.4) * 10, 100 + Math.sin(k * 1.4) * 6, 3, R0, { tone: 0.1 }))); continue; }
      out.push(e(x, 100, 14 + squish * 8, Math.max(5, 15 - squish * 9), R0), e(x, 101, 6 + squish * 4, Math.max(2, 6 - squish * 4), R0, { tone: 0.32, fine: true }));
    }
    return out;
  },
  vesselwall: ({ role, f = 0 }) => {                              // thành mao mạch não (hàng rào máu–não): tế bào nội mô khít + mối nối chặt
    const R0 = role || 'cold', out = [];
    for (let i = 0; i < 5; i++) { const x = 4 + i * 39; out.push(r(x, 84, 37, 32, 10, R0, { tone: 0.15 }), e(x + 18, 100, 10, 6, R0, { tone: 0.4, fine: true })); out.push(r(x + 36, 86, 5, 28, 1, 'ink', { tone: 0.6, fine: true })); }
    out.push(...range(4, (i) => e(30 + i * 46 + Math.sin(f * 0.05 + i) * 6, 52, 12, 5, 'hot', { tone: 0.1 })),
      ...range(3, (i) => c(40 + i * 60, 150, 5, 'accent', { tone: 0.2, alpha: 0.6 })));
    return out;
  },
  peptide: ({ role, f = 0 }) => {                                 // chuỗi peptide (endorphin ~31 axit amin): chuỗi hạt cuộn
    const R0 = role || 'accent', roles = [R0, 'cold', 'hot', 'ink'];
    return range(31, (i) => { const t = i / 30, a = t * PI * 3.2 + f * 0.01; return c(30 + t * 140 + Math.cos(a * 2) * 6, 100 + Math.sin(a) * 50 * (0.4 + 0.6 * Math.sin(t * PI)), 9, roles[(i * 7) % 4], { tone: (i % 3) * 0.1 }); })
      .reduce((acc, p, i, arr) => { if (i) acc.push({ k: 'line', pts: [[arr[i - 1].x, arr[i - 1].y], [p.x, p.y]], role: 'dim', w: 0.6 }); acc.push(p); return acc; }, []);
  },
  lipidchain: ({ role }) => {                                      // phân tử lipid (anandamide/endocannabinoid): đầu phân cực + đuôi dài gấp khúc
    const R0 = role || 'accent', pts = range(16, (i) => [44 + i * 9.6, 100 + (i % 2 ? 9 : -9) + (i > 9 ? (i - 9) * 4 : 0)]);
    return [ln(pts, 'ink', 1.0, { tone: 0.1 }), ...pts.map(([x, y]) => c(x, y, 3, 'ink', { tone: 0.25, fine: true })), c(30, 92, 16, R0), c(30, 92, 7, 'hot', { tone: 0.1 }), c(36, 116, 8, 'cold')];
  },
  caffeine: ({ role }) => {                                        // 1,3,7-trimethylxanthine: vòng 6 + vòng 5, N = xanh, O = đỏ
    const v = [[80, 64], [111, 82], [111, 118], [80, 136], [49, 118], [49, 82]], N7 = [145, 70], C8 = [163, 100], N9 = [145, 130];
    const bond = (a, b, dbl) => [ln([a, b], 'ink', 1.1, { tone: 0.1 }), ...(dbl ? [ln([[a[0] + (b[1] - a[1]) * 0.12, a[1] - (b[0] - a[0]) * 0.12], [b[0] + (b[1] - a[1]) * 0.12, b[1] - (b[0] - a[0]) * 0.12]], 'ink', 0.7, { tone: 0.1 })] : [])];
    return [
      ...bond(v[0], v[1]), ...bond(v[1], v[2], true), ...bond(v[2], v[3]), ...bond(v[3], v[4]), ...bond(v[4], v[5]), ...bond(v[5], v[0]),
      ...bond(v[1], N7), ...bond(N7, C8), ...bond(C8, N9, true), ...bond(N9, v[2]),
      ...bond(v[0], [80, 30], true), ...bond(v[4], [20, 135], true), ...bond(v[5], [18, 66]), ...bond(v[3], [80, 172]), ...bond(N7, [162, 44]),
      ...[v[5], v[3], N7, N9].map(([x, y]) => c(x, y, 10, role || 'cold')), c(80, 30, 10, 'hot'), c(20, 135, 10, 'hot'),
      ...[[18, 66], [80, 172], [162, 44]].map(([x, y]) => c(x, y, 7, 'ink', { tone: 0.3 })),
    ];
  },
  adenosine: ({ role }) => {                                       // adenine (vòng 6 + 5, nhóm NH2) gắn đường ribose — hình na ná caffeine
    const v = [[80, 54], [111, 72], [111, 108], [80, 126], [49, 108], [49, 72]], N7 = [145, 60], C8 = [163, 90], N9 = [145, 120];
    const b = (a, c2) => ln([a, c2], 'ink', 1.1, { tone: 0.1 });
    const rib = [[145, 120], [160, 150], [140, 178], [116, 172], [118, 142]];
    return [b(v[0], v[1]), b(v[1], v[2]), b(v[2], v[3]), b(v[3], v[4]), b(v[4], v[5]), b(v[5], v[0]), b(v[1], N7), b(N7, C8), b(C8, N9), b(N9, v[2]), b(v[0], [80, 22]),
      pg(rib, 'ink', { fill: false, w: 1.1, tone: 0.1 }), b(rib[2], [140, 196]), b(rib[3], [100, 186]), b(rib[1], [184, 156]),
      ...[v[5], v[3], N7, N9].map(([x, y]) => c(x, y, 10, role || 'cold')), c(80, 22, 10, role || 'cold', { tone: 0.2 }), c(118, 142, 9, 'hot'),
      ...[[140, 196], [100, 186]].map(([x, y]) => c(x, y, 8, 'hot', { tone: 0.15 }))];
  },
  receptor: ({ role, f = 0, p = 0 }) => {                         // thụ thể trên màng tế bào: túi gắn phía trên; p = đang bị chiếm (sáng)
    const R0 = role || 'accent', out = [];
    for (let i = 0; i < 14; i++) { const x = 7 + i * 14.2; if (x > 66 && x < 134) continue; out.push(c(x, 112, 6.4, 'cold', { tone: 0.2 }), c(x, 156, 6.4, 'cold', { tone: 0.2 }), ln([[x - 2, 118], [x - 2, 150]], 'cold', 0.3, { tone: 0.4, fine: true }), ln([[x + 2, 118], [x + 2, 150]], 'cold', 0.3, { tone: 0.4, fine: true })); }
    out.push(...F('M68 176 L68 96 C68 76 78 64 88 64 L88 92 C88 104 112 104 112 92 L112 64 C122 64 132 76 132 96 L132 176 C132 184 124 188 116 188 L84 188 C76 188 68 184 68 176 Z', R0, { tone: 0.1 }),
      ...S('M80 120 L80 170 M100 116 L100 172 M120 120 L120 170', 'bg', 0.35, { fine: true, alpha: 0.45 }),
      e(100, 92, 10, 6, 'ink', { alpha: 0.2 + 0.5 * clamp(p) * (0.7 + 0.3 * Math.sin(f * 0.3)), fine: true }));
    return out;
  },
  // ======= đời sống =======
  cup: ({ f = 0 }) => [
    e(100, 176, 76, 14, 'ink', { tone: 0.25 }),
    ...F('M48 72 L152 72 L144 164 C142 176 58 176 56 164 Z', 'ink', { tone: 0.06 }),
    ...S('M150 92 C178 88 182 132 146 136', 'ink', 2.2, { tone: 0.06 }),
    e(100, 72, 52, 13, 'ink', { tone: 0.3 }), e(100, 75, 46, 9.5, 'accent', { tone: 0.58 }), e(92, 74, 18, 3.2, 'accent', { tone: 0.25, fine: true }),
    ...F('M60 120 L140 120 L137 152 L63 152 Z', 'hot', { tone: 0.1, alpha: 0.9 }),
    ...range(3, (i) => ln(range(12, (k) => { const t = k / 11; return [82 + i * 18 + Math.sin(t * 5 + f * 0.12 + i) * 6, 58 - t * 48]; }), 'dim', 0.6, { alpha: 0.7 })),
  ],
  coffeebean: ({ role }) => [e(100, 100, 56, 80, role || 'accent', { tone: 0.55, rot: 0.35 }), ...S('M88 30 C120 70 80 120 112 170', 'bg', 1.4, { alpha: 0.85 }), e(78, 70, 12, 26, 'ink', { alpha: 0.15, rot: 0.35, fine: true })],
  bed: ({ f = 0 }) => [
    r(14, 70, 16, 112, 4, 'dim', { tone: 0.25 }), r(170, 112, 14, 70, 4, 'dim', { tone: 0.25 }),
    r(20, 128, 160, 34, 6, 'ink', { tone: 0.35 }), r(26, 118, 150, 18, 7, 'ink', { tone: 0.05 }),
    e(56, 112, 26, 11, 'ink', { tone: 0.0 }),
    e(62, 100, 15, 14, 'ink', { tone: 0.42 }), ...F('M47 96 C50 82 74 82 77 96 C70 90 56 90 47 96 Z', 'dim', { tone: 0.6 }),
    ...S('M58 104 C61 106 64 106 67 104', 'bg', 0.4, { fine: true }),
    ...F(`M70 106 C96 ${94 + Math.sin(f * 0.07) * 2.5} 150 ${96 + Math.sin(f * 0.07) * 2} 176 112 L176 132 L70 132 Z`, 'cold', { tone: 0.25 }),
    ...S('M90 112 C110 108 140 108 170 116', 'bg', 0.35, { fine: true, alpha: 0.35 }),
    ln([[20, 182], [184, 182]], 'dim', 0.6, { tone: 0.3 }),
  ],
  bike: ({ f = 0, role }) => { const b = bikeParts(-0.05, 0.38, 1.45, f * 0.18, role || 'cold'); return [...b.prims, b.crank(0), b.crank(1)]; },
  shoe: ({ role }) => {                                            // giày chạy nhìn nghiêng (mũi bên phải)
    const R0 = role || 'hot';
    return [...F('M10 150 L176 150 C192 150 196 138 186 130 L18 130 C8 132 6 146 10 150 Z', 'ink', { tone: 0.05 }),
      ...F('M8 150 L178 150 C186 150 190 156 184 160 L14 160 C6 160 4 154 8 150 Z', 'ink', { tone: 0.55 }),
      ...range(9, (i) => r(18 + i * 18, 158, 9, 4, 1, 'bg', { fine: true, alpha: 0.6 })),
      ...F('M18 130 C14 110 18 88 34 76 C48 66 64 70 74 78 C88 84 104 90 120 98 C150 104 176 112 186 130 Z', R0),
      ...F('M18 130 C14 110 18 88 34 76 C40 72 44 72 46 74 C40 92 40 112 44 130 Z', R0, { tone: 0.22 }),
      ...F('M60 126 C90 106 120 104 160 112 C140 116 104 122 80 130 Z', 'ink', { tone: 0.1, alpha: 0.85 }),
      ...range(5, (i) => ln([[78 + i * 12, 84 + i * 3.5], [86 + i * 12, 94 + i * 3]], 'ink', 0.55, { tone: 0.05 })),
      ...F('M70 76 C80 66 96 70 100 80 L84 88 Z', R0, { tone: 0.3 }), ln([[30, 82], [26, 100]], 'ink', 0.4, { tone: 0.3, fine: true })];
  },
  paper: ({ role }) => [r(36, 8, 128, 184, 4, 'ink', { tone: 0.04 }), r(48, 20, 104, 9, 2, role || 'ink', { tone: role ? 0 : 0.7 }), ...(role ? [r(36, 8, 128, 184, 4, role, { fill: false, sw: 1.6 })] : []), r(60, 34, 80, 4, 1, 'ink', { tone: 0.5 }),
    ...range(8, (i) => r(48, 46 + i * 7, i === 7 ? 30 : 48, 3, 1, 'ink', { tone: 0.6, fine: true })), ...range(8, (i) => r(102, 46 + i * 7, i === 7 ? 26 : 50, 3, 1, 'ink', { tone: 0.6, fine: true })),
    r(48, 108, 104, 46, 2, 'ink', { tone: 0.14 }), ln([[56, 146], [76, 130], [96, 136], [116, 118], [144, 114]], 'hot', 0.6, { fine: true }),
    ...range(5, (i) => r(48, 162 + i * 6, 104 - (i === 4 ? 40 : 0), 3, 1, 'ink', { tone: 0.6, fine: true }))],
  denoise: ({ p = 0, f = 0 }) => {                                // khung ảnh từ nhiễu → cảnh (diffusion): p = 0 nhiễu thuần → 1 cảnh sạch
    const cols = 18, rows = 24, cw = 160 / cols, ch = 200 / rows, out = [r(18, 0, 164, 200, 4, 'ink', { tone: 0.85 })];
    const roles = ['ink', 'dim', 'cold', 'hot', 'accent'];
    const target = (cx, cy) => {                                    // cảnh đích: trời đêm, trăng, núi, đường ướt có đèn
      const x = cx / cols, y = cy / rows;
      if (Math.hypot(x - 0.72, y - 0.16) < 0.09) return ['ink', 0.05];
      const ridge = 0.42 + 0.08 * Math.sin(x * 9) + 0.05 * Math.sin(x * 23);
      if (y < ridge) return ['cold', 0.55 + 0.25 * (1 - y / ridge)];
      if (y < 0.6) return ['dim', 0.55];
      const road = Math.abs(x - 0.5) < 0.08 + (y - 0.6) * 0.9;
      if (road) return (Math.abs(x - 0.5) < 0.012 + (y - 0.6) * 0.05 && Math.floor(y * 30) % 2) ? ['accent', 0.1] : ['dim', 0.75];
      return ['hot', 0.62 + 0.1 * Math.sin(cx)];
    };
    const k = clamp(p), ff = Math.floor(f / 2);
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
      const n = ihash(i, j, ff), thr = ihash(i, j, 977);          // băm số nguyên: nhiễu không sọc
      const [tr, tt] = target(i, j), clean = thr < k * 1.15 - 0.1;
      const role = clean ? tr : roles[Math.floor(n * 5)], tone = clean ? tt : 0.2 + 0.7 * n;
      out.push(r(18 + i * cw, j * ch, cw + 0.3, ch + 0.3, 0, role, { tone, fine: true }));
    }
    return out;
  },
  bits: ({ p = 0, role }) => {                                     // thanh ghi 8 bit: ô sáng = 1; p = giá trị 0..255 (hoặc 0..1 × 255)
    const v = p > 1 ? Math.round(p) : Math.round(p * 255);
    return range(8, (i) => { const on = (v >> (7 - i)) & 1; return r(6 + i * 24, 76, 20, 48, 3, on ? (role || 'accent') : 'dim', { tone: on ? 0 : 0.55 }); })
      .concat(range(8, (i) => r(10 + i * 24, 132, 12, 3, 1, 'dim', { fine: true, alpha: 0.5 })));
  },
};

export const DETAIL_ALIASES = [
  [['notebook computer', 'macbook', 'laptop'], 'laptop'], [['smartphone', 'cell phone', 'mobile phone'], 'phone'],
  [['cpu', 'processor', 'microchip', 'silicon chip'], 'chip'], [['rack', 'data center', 'datacenter'], 'server'],
  [['graphics card', 'gpu', 'video card'], 'gpu'], [['film', 'film strip', 'filmstrip', 'film frame', 'frames', 'movie', 'cinema'], 'film'], [['film reel', 'reel'], 'reel'],
  [['animation paper', 'drawing', 'sketch', 'flipbook', 'frame drawing'], 'drawing'], [['pencil'], 'pencil'],
  [['neuron', 'nerve cell', 'nerve'], 'neuron'], [['red blood cell', 'rbc', 'erythrocyte'], 'rbc'],
  [['haptoglobin', 'cleanup protein', 'chomper'], 'chomper'], [['bicycle', 'road bike', 'bike', 'cycling'], 'bike'],
  [['white blood cell', 'macrophage', 'immune cell', 'pac-man', 'pacman', 'phagocyte'], 'macrophage'],
  [['fat cell', 'adipocyte'], 'fatcell'], [['body fat', 'fat', 'adipose', 'lipid', 'fat stores'], 'fat'],
  [['glycogen', 'carb stores', 'stored carbs'], 'glycogen'], [['glucose', 'blood sugar'], 'glucose'],
  [['carbs', 'carb', 'carbohydrate', 'carbohydrates', 'bread', 'toast'], 'bread'], [['pasta', 'spaghetti', 'noodles'], 'pasta'],
  [['vertebra', 'vertebrae'], 'vertebra'], [['spine', 'spinal column', 'backbone'], 'spine'], [['spinal disc', 'intervertebral disc', 'disc', 'disk'], 'disc'],
  [['muscle fiber', 'muscle fibre', 'fiber', 'fibre', 'myofibril', 'sarcomere'], 'fiber'], [['muscle cross section', 'fascicle'], 'musclefiber'],
  [['liver'], 'liver'], [['capillary', 'blood vessel', 'vessel', 'artery', 'vein'], 'capillary'],
  [['blood brain barrier', 'blood-brain barrier', 'vessel wall'], 'vesselwall'],
  [['endorphin', 'peptide', 'protein chain', 'hormone'], 'peptide'], [['endocannabinoid', 'anandamide', 'cannabinoid'], 'lipidchain'],
  [['caffeine molecule', 'caffeine'], 'caffeine'], [['adenosine'], 'adenosine'], [['receptor', 'adenosine receptor', 'binding site'], 'receptor'],
  [['coffee bean', 'bean'], 'coffeebean'], [['running shoe', 'sneaker', 'trainer'], 'shoe'],
  [['research paper', 'study', 'journal', 'paper'], 'paper'], [['noise', 'static', 'diffusion', 'denoise', 'latent image'], 'denoise'], [['bits', 'binary', 'register', 'byte'], 'bits'],
];
export const DETAIL_GROUP = ['laptop', 'phone', 'chip', 'keyboard', 'server', 'gpu', 'film', 'reel', 'drawing', 'pencil', 'brain', 'neuron', 'bloodcell',
  'rbc', 'macrophage', 'chomper', 'bike', 'fatcell', 'fat', 'glycogen', 'glucose', 'bread', 'pasta', 'vertebra', 'spine', 'disc', 'muscle', 'musclefiber', 'fiber',
  'mitochondria', 'heart', 'lungs', 'liver', 'capillary', 'vesselwall', 'peptide', 'lipidchain', 'caffeine', 'adenosine', 'receptor', 'cup',
  'coffeebean', 'bed', 'shoe', 'paper', 'bits', 'denoise'];
