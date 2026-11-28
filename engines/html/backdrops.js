// Vòng 22 — bối cảnh BAN ĐÊM nhiều lớp cho beat `scene` (darkmode có chiều sâu thay vì nền đen trơn):
// city | gym | bedroom | track | office | studio | lab. Mỗi bối cảnh là danh sách mảng ở toạ độ thế giới (x, y 0..1 của khung,
// z = độ sâu) → beat chiếu qua camera của cảnh (thị sai + DOF + tối dần theo độ sâu), vẽ bằng bút của look (vai màu + tone).
// Tối có chủ đích: tường/đồ vật ở tone 0.5–0.9 (gần màu nền), điểm sáng (đèn, cửa sổ, trăng) mới sáng → vật chính nổi lên.
// params.backdrop: "gym" | {kind, floor (y sàn 0..1, mặc định 0.8), seed, dim (0..1, mặc định 0.85), lamps (true/false)}
export const BACKDROPS = ['city', 'road', 'gym', 'bedroom', 'track', 'office', 'studio', 'lab'];

const h1 = (i, s) => { const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return x - Math.floor(x); };

/** → [{z, k: rect|poly|circle|line|glow|cone|sky|floor, …}] (toạ độ thế giới) — tất định theo seed. */
export function backdropItems(kind, o = {}) {
  const seed = o.seed ?? 7, F = o.floor ?? 0.8, out = [];
  const R = (z, x, y, w, h, role, tone, extra = {}) => out.push({ z, k: 'rect', x, y, w, h, role, tone, ...extra });
  const C = (z, x, y, r, role, tone, extra = {}) => out.push({ z, k: 'circle', x, y, r, role, tone, ...extra });
  const LN = (z, pts, role, tone, w = 0.4, extra = {}) => out.push({ z, k: 'line', pts, role, tone, w, ...extra });
  const PG = (z, pts, role, tone, extra = {}) => out.push({ z, k: 'poly', pts, role, tone, ...extra });
  const GLOW = (z, x, y, r, role, a = 0.35) => out.push({ z, k: 'glow', x, y, r, role, a });
  const CONE = (z, x, y, w0, w1, h, role, a = 0.1) => out.push({ z, k: 'cone', x, y, w0, w1, h, role, a });
  const skyline = (z, x0, x1, base, hmin, hmax, tone, lit = 0.5, sd = 1) => {
    let x = x0, i = 0;
    while (x < x1 && i < 60) {
      const w = 0.04 + 0.07 * h1(i, seed + sd), hh = hmin + (hmax - hmin) * h1(i + 9, seed + sd);
      R(z, x, base - hh, w, hh + 0.01, 'cold', tone);
      const cols = Math.max(1, Math.floor(w / 0.016)), rows = Math.max(1, Math.floor(hh / 0.022));
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) if (h1(i * 31 + r * 7 + c, seed + sd + 3) < lit * 0.45)
        R(z, x + 0.005 + c * (w - 0.01) / cols, base - hh + 0.01 + r * hh / rows, Math.min(0.008, (w - 0.01) / cols * 0.6), 0.008, 'accent', 0.25, { a: 0.75, fine: true });
      x += w + 0.004; i++;
    }
  };
  const stars = (n, y1 = 0.45) => { for (let i = 0; i < n; i++) C(8, -0.6 + 2.2 * h1(i, seed + 40), 0.02 + y1 * h1(i, seed + 41), 0.0012 + 0.0016 * h1(i, seed + 42), 'ink', 0.1, { a: 0.35 + 0.5 * h1(i, seed + 43), twinkle: i }); };
  const moon = (x, y, z = 7) => { GLOW(z, x, y, 0.09, 'ink', 0.16); C(z, x, y, 0.026, 'ink', 0.05, { a: 0.92 }); C(z, x + 0.008, y - 0.006, 0.007, 'ink', 0.25, { a: 0.5, fine: true }); C(z, x - 0.01, y + 0.008, 0.005, 'ink', 0.25, { a: 0.5, fine: true }); };
  const floorLines = (role, tone, n = 7, z0 = 2.4) => { for (let i = 0; i <= n; i++) { const z = z0 * (1 - i / n); LN(z, [[-1.2, F], [2.2, F]], role, tone, 0.3, { a: 0.5 }); } };
  const room = (wallRole, wallTone, z = 2.4) => { out.push({ z: 9, k: 'sky', role: 'cold', a: 0.07 }); R(z, -1.2, -0.4, 3.4, F + 0.41, wallRole, wallTone); out.push({ z, k: 'floor', y: F, role: wallRole, tone: Math.min(0.95, wallTone + 0.06) }); };

  if (kind === 'city' || kind === 'track') {
    out.push({ z: 9, k: 'sky', role: 'cold', a: 0.14 });
    stars(70); moon(0.78, 0.16);
    skyline(5, -0.8, 1.9, F - 0.06, 0.08, 0.3, 0.72, 0.5, 1);
    skyline(3.2, -0.6, 1.7, F - 0.02, 0.05, 0.2, 0.82, 0.35, 2);
    out.push({ z: 3, k: 'floor', y: F, role: kind === 'track' ? 'hot' : 'dim', tone: kind === 'track' ? 0.78 : 0.9 });
    if (kind === 'track') {
      for (const [x, s] of [[-0.25, 1], [1.25, -1]]) { LN(3, [[x, F - 0.02], [x, F - 0.46]], 'dim', 0.55, 0.6); R(3, x - 0.045, F - 0.5, 0.09, 0.04, 'ink', 0.2); GLOW(3, x, F - 0.48, 0.12, 'ink', 0.3); CONE(3, x, F - 0.47, 0.03, 0.5, 0.5, 'ink', 0.05 * s * s); }
      PG(2.6, [[-0.9, F - 0.02], [2, F - 0.02], [2, F - 0.12], [-0.9, F - 0.1]], 'dim', 0.82);
      for (let i = 0; i < 4; i++) LN(2.6, [[-0.9, F - 0.03 - i * 0.022], [2, F - 0.035 - i * 0.022]], 'dim', 0.7, 0.25, { a: 0.6 });
      for (let i = 0; i < 6; i++) { const z = 2.4 * (1 - i / 6); LN(z, [[-1.4, F], [2.4, F]], 'ink', 0.55, 0.35, { a: 0.55 }); }
    } else {
      for (const x of [0.06, 0.94]) { LN(1.6, [[x, F], [x, F - 0.36], [x + 0.04, F - 0.37]], 'dim', 0.5, 0.5); GLOW(1.6, x + 0.045, F - 0.365, 0.08, 'accent', 0.28); CONE(1.6, x + 0.045, F - 0.36, 0.01, 0.16, 0.36, 'accent', 0.06); }
      floorLines('dim', 0.75, 5, 2.4);
    }
  } else if (kind === 'road') {                       // đường chạy marathon ban đêm: mặt đường hội tụ, rào chắn, khán giả, đèn đường
    out.push({ z: 9, k: 'sky', role: 'cold', a: 0.12 });
    stars(40, 0.3); moon(0.2, 0.14);
    skyline(5.5, -0.9, 2.0, F - 0.1, 0.1, 0.34, 0.74, 0.55, 31);
    out.push({ z: 4, k: 'floor', y: F, role: 'dim', tone: 0.9 });
    for (let i = 0; i < 9; i++) { const z = 3.6 * (1 - i / 9); LN(z, [[0.42, F], [0.58, F]], 'ink', 0.35, 0.5, { a: 0.7 }); }
    for (const side of [-1, 1]) {
      for (let i = 0; i < 7; i++) {
        const z = 3.4 - i * 0.5, x = side < 0 ? -0.35 : 1.35;
        R(z, side < 0 ? x - 0.4 : x, F - 0.07, 0.4, 0.07, 'hot', 0.55);
        for (let k = 0; k < 6; k++) { const hx = (side < 0 ? x - 0.38 : x + 0.02) + k * 0.065; C(z, hx, F - 0.12 - 0.02 * h1(k + i * 7, seed + 90), 0.022, 'dim', 0.62); R(z, hx - 0.025, F - 0.1, 0.05, 0.05, 'dim', 0.66); }
      }
      for (let i = 0; i < 3; i++) { const z = 3 - i * 1.1, x = side < 0 ? -0.15 : 1.15; LN(z, [[x, F], [x, F - 0.42]], 'dim', 0.5, 0.5); GLOW(z, x, F - 0.43, 0.08, 'accent', 0.3); CONE(z, x, F - 0.42, 0.01, 0.2, 0.42, 'accent', 0.05); }
    }
    R(2.6, 0.62, F - 0.22, 0.05, 0.12, 'ink', 0.3); R(2.6, 0.6, F - 0.26, 0.09, 0.05, 'accent', 0.3);
  } else if (kind === 'gym') {
    room('dim', 0.86);
    for (const wx of [0.02, 0.36, 0.7]) {
      R(2.38, wx, 0.12, 0.26, 0.42, 'cold', 0.86);
      skyline(2.37, wx + 0.005, wx + 0.255, 0.54, 0.05, 0.22, 0.74, 0.55, 5 + Math.round(wx * 10));
      for (const fx of [0.13]) LN(2.36, [[wx + fx, 0.12], [wx + fx, 0.54]], 'dim', 0.6, 0.35);
      LN(2.36, [[wx, 0.33], [wx + 0.26, 0.33]], 'dim', 0.6, 0.3);
      R(2.36, wx - 0.005, 0.115, 0.27, 0.43, 'dim', 0.55, { fill: false, sw: 0.45 });
    }
    moon(0.8, 0.2, 2.39);
    R(2.3, -0.3, F - 0.12, 1.6, 0.012, 'dim', 0.6);
    for (const rx of [0.12]) { R(1.7, rx - 0.07, F - 0.42, 0.012, 0.42, 'dim', 0.5); R(1.7, rx + 0.06, F - 0.42, 0.012, 0.42, 'dim', 0.5); R(1.7, rx - 0.075, F - 0.43, 0.15, 0.01, 'dim', 0.45); LN(1.7, [[rx - 0.16, F - 0.3], [rx + 0.16, F - 0.3]], 'ink', 0.45, 0.5); C(1.7, rx - 0.14, F - 0.3, 0.035, 'hot', 0.5); C(1.7, rx + 0.14, F - 0.3, 0.035, 'hot', 0.5); C(1.7, rx - 0.12, F - 0.3, 0.028, 'dim', 0.35); C(1.7, rx + 0.12, F - 0.3, 0.028, 'dim', 0.35); }
    R(1.4, 0.68, F - 0.2, 0.36, 0.014, 'dim', 0.5); R(1.4, 0.68, F - 0.11, 0.36, 0.014, 'dim', 0.5); LN(1.4, [[0.69, F - 0.2], [0.69, F]], 'dim', 0.5, 0.4); LN(1.4, [[1.03, F - 0.2], [1.03, F]], 'dim', 0.5, 0.4);
    for (let i = 0; i < 5; i++) for (const yy of [F - 0.225, F - 0.135]) { const x = 0.71 + i * 0.065; R(1.4, x, yy, 0.04, 0.008, 'dim', 0.35); C(1.4, x, yy + 0.004, 0.012, 'ink', 0.55); C(1.4, x + 0.04, yy + 0.004, 0.012, 'ink', 0.55); }
    for (const px of [0.48, 0.56]) C(1.9, px, F - 0.08, 0.06, 'dim', 0.55, { rim: 1 });
    if (o.lamps !== false) for (const lx of [0.25, 0.75]) { LN(1.6, [[lx, -0.3], [lx, 0.05]], 'dim', 0.6, 0.25); PG(1.6, [[lx - 0.05, 0.08], [lx + 0.05, 0.08], [lx + 0.025, 0.05], [lx - 0.025, 0.05]], 'dim', 0.4); GLOW(1.6, lx, 0.085, 0.07, 'accent', 0.35); CONE(1.6, lx, 0.085, 0.05, 0.42, F - 0.085, 'accent', 0.07); }
    floorLines('dim', 0.7, 6, 2.3);
  } else if (kind === 'bedroom') {
    room('cold', 0.88);
    R(2.38, 0.56, 0.1, 0.32, 0.4, 'cold', 0.7);
    for (let i = 0; i < 22; i++) C(2.37, 0.57 + 0.3 * h1(i, seed + 61), 0.11 + 0.3 * h1(i, seed + 62), 0.0015, 'ink', 0.1, { a: 0.6, twinkle: i });
    moon(0.8, 0.2, 2.37);
    LN(2.36, [[0.72, 0.1], [0.72, 0.5]], 'dim', 0.55, 0.45); LN(2.36, [[0.56, 0.3], [0.88, 0.3]], 'dim', 0.55, 0.4);
    PG(2.3, [[0.52, 0.06], [0.6, 0.06], [0.58, 0.56], [0.5, 0.58]], 'hot', 0.72); PG(2.3, [[0.84, 0.06], [0.92, 0.06], [0.94, 0.58], [0.86, 0.56]], 'hot', 0.72);
    CONE(2.2, 0.72, 0.5, 0.15, 0.42, F - 0.5, 'cold', 0.06);
    R(2.3, 0.08, 0.2, 0.14, 0.11, 'dim', 0.6, { fill: false, sw: 0.5 }); R(2.3, 0.095, 0.215, 0.11, 0.08, 'accent', 0.75);
    R(1.4, 0.0, F - 0.15, 0.12, 0.15, 'dim', 0.55); R(1.4, 0.04, F - 0.25, 0.04, 0.1, 'dim', 0.45); PG(1.4, [[0.02, F - 0.25], [0.1, F - 0.25], [0.085, F - 0.3], [0.035, F - 0.3]], 'accent', 0.35);
    GLOW(1.4, 0.06, F - 0.27, 0.12, 'accent', 0.32);
    floorLines('dim', 0.7, 6, 2.3);
  } else if (kind === 'office') {
    room('dim', 0.87);
    R(2.38, 0.08, 0.1, 0.5, 0.38, 'cold', 0.84); skyline(2.37, 0.085, 0.575, 0.48, 0.06, 0.26, 0.72, 0.6, 21); moon(0.48, 0.17, 2.37);
    R(2.36, 0.075, 0.095, 0.51, 0.39, 'dim', 0.5, { fill: false, sw: 0.5 });
    R(1.3, 0.62, F - 0.18, 0.5, 0.02, 'dim', 0.45); LN(1.3, [[0.66, F - 0.16], [0.66, F]], 'dim', 0.5, 0.45); LN(1.3, [[1.08, F - 0.16], [1.08, F]], 'dim', 0.5, 0.45);
    R(1.3, 0.72, F - 0.38, 0.26, 0.17, 'ink', 0.8); R(1.3, 0.73, F - 0.37, 0.24, 0.15, 'cold', 0.45); GLOW(1.3, 0.85, F - 0.3, 0.22, 'cold', 0.22);
    for (let i = 0; i < 5; i++) R(1.29, 0.745, F - 0.36 + i * 0.026, 0.06 + 0.1 * h1(i, seed + 70), 0.008, ['accent', 'hot', 'ink', 'cold', 'accent'][i], 0.2, { a: 0.8, fine: true });
    R(1.3, 0.84, F - 0.21, 0.02, 0.03, 'dim', 0.4); R(1.3, 0.76, F - 0.2, 0.17, 0.012, 'dim', 0.3);
    C(1.5, 0.2, F - 0.08, 0.05, 'cold', 0.65); for (let i = 0; i < 5; i++) PG(1.5, [[0.2, F - 0.12], [0.2 + Math.cos(-1.2 - i * 0.18) * 0.1, F - 0.12 + Math.sin(-1.2 - i * 0.18) * 0.1], [0.21, F - 0.11]], 'cold', 0.55);
    floorLines('dim', 0.72, 6, 2.3);
  } else if (kind === 'studio') {
    room('dim', 0.86);
    for (let i = 0; i < 6; i++) { const x = 0.06 + (i % 3) * 0.17, y = 0.12 + Math.floor(i / 3) * 0.17; R(2.36, x, y, 0.13, 0.15, 'ink', 0.62, { rot: (h1(i, seed) - 0.5) * 0.1 }); C(2.35, x + 0.065, y + 0.01, 0.004, 'hot', 0.3); LN(2.35, [[x + 0.03, y + 0.11], [x + 0.06, y + 0.05 + 0.03 * h1(i, 3)], [x + 0.1, y + 0.1]], 'bg', 0.3, 0.3, { a: 0.6 }); C(2.35, x + 0.06, y + 0.05, 0.012, 'bg', 0.3, { fill: false, w: 0.25, a: 0.6 }); }
    PG(1.3, [[0.62, F - 0.16], [1.12, F - 0.16], [1.16, F - 0.12], [0.58, F - 0.12]], 'dim', 0.45); PG(1.3, [[0.66, F - 0.22], [1.04, F - 0.22], [1.08, F - 0.16], [0.62, F - 0.16]], 'ink', 0.35);
    GLOW(1.3, 0.85, F - 0.19, 0.2, 'ink', 0.2);
    LN(1.25, [[0.66, F - 0.12], [0.68, F - 0.5], [0.78, F - 0.56]], 'dim', 0.5, 0.45); PG(1.25, [[0.76, F - 0.58], [0.84, F - 0.54], [0.82, F - 0.5], [0.75, F - 0.53]], 'accent', 0.45); CONE(1.25, 0.8, F - 0.52, 0.02, 0.14, 0.3, 'accent', 0.08);
    C(2.0, 0.85, 0.22, 0.07, 'dim', 0.6); for (let i = 0; i < 5; i++) C(2.0, 0.85 + Math.cos(i * 1.256) * 0.035, 0.22 + Math.sin(i * 1.256) * 0.035, 0.014, 'bg', 0.0);
    floorLines('dim', 0.72, 6, 2.3);
  } else if (kind === 'lab') {
    room('cold', 0.88);
    for (const yy of [0.2, 0.36]) { R(2.3, 0.02, yy, 0.6, 0.012, 'dim', 0.5); for (let i = 0; i < 6; i++) { const x = 0.05 + i * 0.095, hh = 0.05 + 0.05 * h1(i, seed + yy * 10); R(2.3, x, yy - hh, 0.04, hh, ['cold', 'accent', 'hot'][i % 3], 0.6, { rad: 0.3 }); } }
    R(2.38, 0.7, 0.1, 0.24, 0.34, 'cold', 0.75); moon(0.85, 0.18, 2.37);
    R(1.3, -0.2, F - 0.17, 1.4, 0.03, 'dim', 0.5); R(1.3, -0.2, F - 0.14, 1.4, 0.14, 'dim', 0.7);
    GLOW(1.3, 0.2, F - 0.2, 0.08, 'accent', 0.25);
    floorLines('dim', 0.75, 5, 2.3);
  }
  return out;
}
