// Vòng 22 — người TẢ THỰC cho engine html (bộ xương 'human' của rig2d.js): tỉ lệ ~7.5 đầu (Drillis & Contini), cơ bắp
// thuôn theo nhóm cơ (đùi trước/sau, bắp chân, tay), mặt nghiêng (trán–mũi–môi–cằm), quần áo thể thao, giày có đế.
// Dáng đi/chạy lấy từ đường cong góc khớp sinh cơ học (hông, gối, cổ chân theo % chu kỳ) — không phải hình sin:
// chạm đất bằng gót/giữa bàn, gối gập ~40° khi đỡ, đạp mũi chân rời đất, gập gối ~115° khi vung chân, có pha bay.
// Bàn chân chạm đất được neo theo mặt đất (không lơ lửng, không lún); chu kỳ bước khớp quãng đường (strideOf).
// Cơ quan x-ray vẽ bằng đạo cụ chi tiết (icons_detail.js): não, tim, phổi, gan, dạ dày + cột sống có đĩa đệm (p = nén),
// cơ chân (muscles), mạch máu (vessels), kho nhiên liệu glycogen (fuel, p = còn bao nhiêu).
import { DETAIL_ICONS, bikeParts } from './icons_detail.js';

const TAU = Math.PI * 2, PI = Math.PI, D = PI / 180;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const E = (x, y, rx, ry, role, o = {}) => ({ k: 'circle', x, y, r: 1, rx, ry, rot: o.rot || 0, role, ...o });
const PG = (pts, role, o = {}) => ({ k: 'poly', pts, role, ...o });
const LN = (pts, role, w, o = {}) => ({ k: 'line', pts, role, w, ...o });
const MK = (name, x, y, r) => ({ k: 'circle', x, y, r: 1, rx: r, ry: r, role: 'ink', anchor: name, fine: true, alpha: 0 });
const rot = (p, c, a) => { const s = Math.sin(a), co = Math.cos(a), x = p[0] - c[0], y = p[1] - c[1]; return [c[0] + x * co - y * s, c[1] + x * s + y * co]; };
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const along = (p, len, ang) => [p[0] + Math.sin(ang) * len, p[1] + Math.cos(ang) * len];   // ang: rad từ phương thẳng đứng, + = ra trước
function xf(prims, c, a, dx = 0, dy = 0) {
  if (!a && !dx && !dy) return prims;
  return prims.map((p) => {
    if (p.k === 'circle') { const q = rot([p.x, p.y], c, a); return { ...p, x: q[0] + dx, y: q[1] + dy, rot: (p.rot || 0) + a }; }
    return { ...p, pts: p.pts.map((q) => add(rot(q, c, a), [dx, dy])) };
  });
}

// ---------- đường cong góc khớp theo % chu kỳ (Hermite tuần hoàn qua các mốc) ----------
function cyc(keys, u) {
  u = ((u % 1) + 1) % 1;
  const n = keys.length, at = (j) => { const k = ((j % n) + n) % n, w = Math.floor(j / n); return [keys[k][0] + w, keys[k][1]]; };
  let i = 0; while (i < n - 1 && keys[i + 1][0] <= u) i++;
  if (u < keys[0][0]) i = -1;
  const k0 = at(i), k1 = at(i + 1), km = at(i - 1), k2 = at(i + 2);
  const dt = k1[0] - k0[0] || 1, t = (u - (i < 0 ? keys[n - 1][0] - 1 : k0[0])) / dt;
  const m0 = (k1[1] - km[1]) / (k1[0] - km[0]) * dt, m1 = (k2[1] - k0[1]) / (k2[0] - k0[0]) * dt;
  const t2 = t * t, t3 = t2 * t;
  return (2 * t3 - 3 * t2 + 1) * k0[1] + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * k1[1] + (t3 - t2) * m1;
}
// Chạy (độ): hông + = đùi ra trước; gối + = gập; cổ chân + = mu bàn chân gập lên. Đỡ 0–0.36, bay 0.36–0.5.
const RUN = {
  hip: [[0, 26], [0.1, 16], [0.2, 2], [0.31, -14], [0.4, -17], [0.5, -6], [0.6, 14], [0.7, 33], [0.8, 42], [0.9, 37]],
  knee: [[0, 18], [0.1, 40], [0.2, 33], [0.31, 20], [0.4, 36], [0.5, 72], [0.6, 106], [0.68, 116], [0.78, 98], [0.88, 52], [0.95, 26]],
  ankle: [[0, 4], [0.1, 18], [0.2, 16], [0.3, -6], [0.38, -28], [0.48, -18], [0.62, -4], [0.8, 6], [0.92, 6]],
  lean: 9, bob: 0.026, flight: [[0.36, 0.5], [0.86, 1.0]],
};
const WALK = {
  hip: [[0, 24], [0.15, 16], [0.3, 4], [0.5, -12], [0.6, -8], [0.7, 6], [0.8, 20], [0.9, 26]],
  knee: [[0, 3], [0.12, 16], [0.3, 6], [0.45, 4], [0.6, 36], [0.72, 62], [0.82, 42], [0.92, 10]],
  ankle: [[0, 0], [0.1, -4], [0.3, 6], [0.48, 10], [0.6, -16], [0.72, -4], [0.85, 2]],
  lean: 2, bob: 0, flight: [],
};

/** IK hai đoạn: khớp giữa của chuỗi a→(L1)→k→(L2)→b; bend = +1 gập ra trước (gối), −1 gập ra sau (khuỷu khi với ra trước). */
function ik2(a, b, L1, L2, bend = 1) {
  const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.min(L1 + L2 - 1e-4, Math.max(1e-4, Math.hypot(dx, dy)));
  const ca = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), base = Math.atan2(dy, dx), ang = base - bend * Math.acos(Math.max(-1, Math.min(1, ca)));
  return [a[0] + Math.cos(ang) * L1, a[1] + Math.sin(ang) * L1];
}
const angOf = (p, q) => Math.atan2(q[0] - p[0], q[1] - p[1]);     // góc từ phương thẳng đứng (+ = ra trước), cùng quy ước along()

// ---------- hình: chi thuôn theo hồ sơ cơ ----------
/** chi a→b: back/front = nửa bề dày theo t (0..1) ở phía sau/trước (khi chi chĩa xuống, phía sau = −x khi quay phải). */
function limb(a, b, back, front, role, o = {}) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, nx = -uy, ny = ux, m = back.length, P = [], Q = [];
  for (let i = 0; i < m; i++) { const t = i / (m - 1), px = a[0] + dx * t, py = a[1] + dy * t; P.push([px + nx * back[i], py + ny * back[i]]); Q.push([px - nx * front[i], py - ny * front[i]]); }
  const cap = (c, r0, r1, a0, dir) => Array.from({ length: 6 }, (_, k) => { const t = (k + 1) / 7, ang = a0 + dir * t * PI, rr = lerp(r0, r1, t); return [c[0] + Math.cos(ang) * rr, c[1] + Math.sin(ang) * rr]; });
  const aN = Math.atan2(ny, nx);
  return PG([...P, ...cap(b, back[m - 1], front[m - 1], aN, -1), ...Q.reverse(), ...cap(a, front[0], back[0], aN + PI, -1)], role, o);
}
const sc = (arr, k) => arr.map((v) => v * k);

// giày (gốc = khớp cổ chân, x ra trước, y xuống) — đáy giày ở y = 0.078
const SHOE_UP = [[-0.045, -0.06], [0.02, -0.066], [0.07, -0.038], [0.14, -0.008], [0.19, 0.008], [0.216, 0.03], [0.21, 0.045], [-0.066, 0.045], [-0.072, 0.0]];
const SHOE_MID = [[-0.07, 0.04], [0.214, 0.04], [0.205, 0.068], [-0.062, 0.068]];
const SHOE_OUT = [[-0.06, 0.064], [0.204, 0.064], [0.198, 0.078], [-0.056, 0.078]];
const SHOE_LOW = [[-0.056, 0.078], [0.07, 0.078], [0.198, 0.078]];
const FOOT_BARE = [[-0.04, -0.05], [0.04, -0.04], [0.17, 0.02], [0.205, 0.05], [0.19, 0.075], [-0.055, 0.075], [-0.07, 0.02]];

/** pose theo hành động → góc khớp (rad) + thân. */
function posePlan(A, t, ph, cycU) {
  const u = cycU !== undefined && cycU !== null ? ((cycU % 1) + 1) % 1 : null;
  const breath = Math.sin((t * 0.32 + ph) * TAU);
  const P = { lean: 0, hip: [2 * D, -2 * D], knee: [4 * D, 4 * D], ankle: [null, null], sh: [6 * D, -4 * D], elb: [12 * D, 10 * D], lift: 0, head: 0, whole: 0, lie: 0, flat: [1, 1], breath, gait: null };
  if (A === 'run' || A === 'walk') {
    const G = A === 'run' ? RUN : WALK, w = u ?? (t * (A === 'run' ? 1.42 : 0.95) + ph) % 1;
    P.gait = G; P.flat = [0, 0];
    for (const [i, off] of [[0, 0], [1, 0.5]]) { P.hip[i] = cyc(G.hip, w + off) * D; P.knee[i] = cyc(G.knee, w + off) * D; P.ankle[i] = cyc(G.ankle, w + off) * D; }
    P.lean = G.lean * D;
    const arm = A === 'run' ? 0.95 : 0.55;
    P.sh = [(cyc(G.hip, w + 0.5) - 10) * arm * D - 6 * D, (cyc(G.hip, w) - 10) * arm * D - 6 * D];
    P.elb = A === 'run' ? [(86 + 14 * Math.cos(w * TAU)) * D, (86 - 14 * Math.cos(w * TAU)) * D] : [22 * D, 18 * D];
    for (const [a, b] of G.flight) if (w >= a && w < b) P.lift = G.bob * Math.sin((w - a) / (b - a) * PI);
    P.head = -P.lean * 0.6;
  } else if (A === 'sit') { P.hip = [86 * D, 82 * D]; P.knee = [90 * D, 86 * D]; P.sh = [18 * D, 10 * D]; P.elb = [55 * D, 50 * D]; P.lean = -2 * D; }
  else if (A === 'sleep') { P.lie = 1; P.sh = [4 * D, 2 * D]; P.elb = [20 * D, 15 * D]; }
  else if (A === 'point') { P.sh = [82 * D, -6 * D]; P.elb = [4 * D, 14 * D]; P.head = 0.04; }
  else if (A === 'wave') { const k = Math.sin((t * 2.2 + ph) * TAU); P.sh = [150 * D + k * 0.18, -6 * D]; P.elb = [(40 + k * 22) * D, 12 * D]; }
  else if (A === 'cheer' || A === 'jump') {
    const k = Math.abs(Math.sin((t * (A === 'jump' ? 0.85 : 1.8) + ph) * PI));
    P.sh = [165 * D - k * 0.15, 160 * D - k * 0.1]; P.elb = [12 * D, 18 * D]; P.lift = k * (A === 'jump' ? 0.3 : 0.06); P.knee = [k * 30 * D, k * 34 * D]; P.hip = [k * 18 * D, k * 12 * D]; P.flat = [0, 0];
  } else if (A === 'tired') {
    const pant = Math.sin((t * 1.6 + ph) * TAU);
    P.lean = (40 + pant * 2) * D; P.hip = [44 * D, 38 * D]; P.knee = [34 * D, 30 * D]; P.sh = [20 * D, 14 * D]; P.elb = [6 * D, 8 * D]; P.head = -0.35;
  } else if (A === 'curl') {
    const k = 0.5 - 0.5 * Math.cos((t * 0.55 + ph) * TAU);
    P.sh = [4 * D, -2 * D]; P.elb = [(12 + 125 * k) * D, (12 + 125 * k) * D]; P.lean = -2 * D;
  } else if (A === 'squat') {
    const k = 0.5 - 0.5 * Math.cos((t * 0.4 + ph) * TAU);
    P.hip = [(5 + 98 * k) * D, (3 + 98 * k) * D]; P.knee = [(6 + 116 * k) * D, (6 + 116 * k) * D]; P.lean = (8 + 34 * k) * D; P.sh = [-58 * D, -60 * D]; P.elb = [140 * D, 140 * D]; P.bar = 1; P.planted = 1;
  } else if (A === 'deadlift') {                       // vòng 23: gập hông, lưng thẳng, tay thẳng đứng, đòn đi thẳng đứng sát ống chân
    const k = 0.5 - 0.5 * Math.cos((t * 0.38 + ph) * TAU), lean = (58 - 56 * k) * D;
    P.hip = [(84 - 82 * k) * D, (82 - 82 * k) * D]; P.knee = [(62 - 60 * k) * D, (60 - 60 * k) * D]; P.lean = lean;
    P.sh = [-lean + 4 * D, -lean + 2 * D]; P.elb = [0, 0]; P.dead = 1; P.planted = 1; P.head = -lean * 0.35;
  } else if (A === 'cycle') {
    const w = u ?? (t * 1.45 + ph) % 1;
    P.cycle = w * TAU; P.lean = 44 * D; P.head = 0.22; P.flat = [0, 0];
  } else if (A === 'fall') { const k = clamp(t / 0.75); P.whole = -PI * 0.5 * k * k * (3 - 2 * k); P.sh = [130 * D, 110 * D]; P.knee = [30 * D, 40 * D]; }
  return P;
}

/** stride (đơn vị toạ độ rig) của một chu kỳ — đo trực tiếp từ động học (quãng chân đỡ trượt về sau khi đỡ). */
const LEN = { thigh: 0.42, shank: 0.425, upper: 0.315, fore: 0.255 };
function footX(G, u) { const h = cyc(G.hip, u) * D, k = cyc(G.knee, u) * D; return Math.sin(h) * LEN.thigh + Math.sin(h - k) * LEN.shank; }
export const HUMAN_STRIDE = {
  run: (footX(RUN, 0.01) - footX(RUN, 0.33)) / 0.32,
  cycle: 2 * Math.PI * 0.34 * 2.6,                                  // một vòng đùi đĩa ≈ 2.6 vòng bánh (tỉ số truyền)
  walk: (footX(WALK, 0.02) - footX(WALK, 0.55)) / 0.53,
};

// ---------- đặt đạo cụ chi tiết làm cơ quan ----------
function placeIcon(name, cx, cy, half, args = {}, o = {}) {
  const fn = DETAIL_ICONS[name];
  if (!fn) return [];
  const prims = fn({ f: args.f || 0, p: args.p, role: args.role });
  return prims.map((p) => {
    const q = { ...p, ...o, alpha: (p.alpha ?? 1) * (o.alpha ?? 1), organ: 1 };
    if (p.k === 'circle') return { ...q, x: cx + p.x * half, y: cy + p.y * half, rx: (p.rx ?? p.r) * half, ry: (p.ry ?? p.r) * half, r: 1 };
    if (p.k === 'rect') { const x0 = cx + p.x * half, y0 = cy + p.y * half, w = p.w * half, h = p.h * half; return { ...q, k: 'poly', pts: [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h]] }; }
    if (p.k === 'arc') return { ...q, x: cx + p.x * half, y: cy + p.y * half, r: p.r * half, ...(p.rx ? { rx: p.rx * half, ry: p.ry * half } : {}) };
    return { ...q, pts: p.pts.map(([x, y]) => [cx + x * half, cy + y * half]) };
  });
}

/** bộ xương 'human'. S = SPECIES (build, top, bottom, female, shoe…), o = {skin, hair, pants, xray, organs, p, gaze, talk…} */
export function human(S, A, X, t, ph, body, blink, o = {}) {
  const view = o.view || S.view || 'side';                                       // vòng 23: góc nhìn side | front | back
  if ((view === 'front' || view === 'back') && FRONT_ACTIONS.includes(A)) return humanFront(S, A, X, t, ph, body, blink, o, view === 'back');
  const P = posePlan(A, t, ph, o.cycle), bd = o.build || S.build || 1, ground = 0.9;
  const skin = o.skin || 'skin', hair = o.hairRole || S.hairRole || 'hair', top = body, bottom = o.pants || S.pants || 'dim';
  const shoeRole = S.shoe || 'accent', style = o.hair || S.style || 'short';
  const outfit = o.outfit || S.top, lower = o.bottom || S.bottom, fullSleeve = outfit === 'hoodie' || outfit === 'shirt' || outfit === 'labcoat';   // vòng 23
  const xr = clamp(Number(o.xray) || 0), organs = o.organs || [], fade = (al) => al * (1 - 0.66 * xr);
  // ---- chân trong khung hông (hông = gốc), tìm điểm thấp nhất để đặt lên mặt đất ----
  const legs = [0, 1].map((i) => {
    const th = P.hip[i], sh = th - P.knee[i], hip = [0.012 * (i ? -1 : 1), 0];
    const knee = along(hip, LEN.thigh, th), ank = along(knee, LEN.shank, sh);
    const phi = P.ankle[i] !== null && !P.flat[i] ? P.ankle[i] + sh : 0;        // góc bàn chân so với mặt đất (+ = mũi chân lên)
    const toW = (q) => add(ank, rot(q, [0, 0], -phi));
    const low = Math.max(...SHOE_LOW.map((q) => toW(q)[1]));
    return { hip, knee, ank, th, sh, phi, toW, low };
  });
  let bike = null, hx = 0;
  if (P.cycle !== undefined) {                                                  // đạp xe: hông trên yên, chân bám bàn đạp (IK)
    bike = bikeParts(0.05, ground - 0.3, 1, P.cycle, S.bike || 'cold');
    hx = bike.saddle[0] + 0.02;
    const hyC = bike.saddle[1] - 0.05;
    for (const i of [0, 1]) {
      const pd = bike.pedal[i], ankW = [pd[0] - 0.035, pd[1] - 0.07], hipW2 = [hx, hyC];
      const kn = ik2(hipW2, ankW, LEN.thigh, LEN.shank, 1), th = angOf(hipW2, kn), sh = angOf(kn, ankW);   // vòng 23: gối gập ra trước (trước đây −1 = gối gập ngược)
      const L = legs[i], phi = -0.12 + 0.22 * Math.sin(P.cycle + (i ? PI : 0) + 0.6);
      L.th = th; L.sh = sh; L.phi = phi; L.hip = [0, 0]; L.knee = [kn[0] - hx, kn[1] - hyC]; L.ank = [ankW[0] - hx, ankW[1] - hyC];
      L.toW = (q) => add(L.ank, rot(q, [0, 0], -phi));
    }
  }
  if (P.planted && !bike) hx = 0.02 - (legs[0].ank[0] + legs[1].ank[0]) / 2;   // vòng 23: bàn chân đứng yên trên sàn, hông lùi ra sau
  let hy = ground - Math.max(legs[0].low, legs[1].low) - P.lift;
  if (bike) hy = bike.saddle[1] - 0.05;
  if (P.lie) hy = ground - Math.max(legs[0].low, legs[1].low);
  const T = (q) => [q[0] + hx, q[1] + hy];                                     // khung hông → toạ độ rig
  const hipW = [hx, hy];
  const tor = (q) => T(rot(q, [0, 0], P.lean));                                 // khung thân (nghiêng theo lean quanh hông)
  const out = [];
  const tone = (far) => (far ? 0.34 : 0);

  // ---- tay ----
  const arm = (i, far) => {
    const S0 = tor([-0.008, -0.47 + P.breath * 0.003]);
    let ua = P.sh[i] + P.lean, fa = ua + P.elb[i];
    if (bike) { const hand = [bike.bar[0] + 0.07 - i * 0.012, bike.bar[1] + 0.035]; const el0 = ik2(S0, hand, LEN.upper, LEN.fore + 0.03, -1); ua = angOf(S0, el0); fa = angOf(el0, hand); }   // khuỷu gập xuống/ra sau
    if (P.bar) { const hand = add(tor([-0.075, -0.49]), [0.03 - i * 0.012, 0.012]); const el0 = ik2(S0, hand, LEN.upper, LEN.fore + 0.035, 1); ua = angOf(S0, el0); fa = angOf(el0, hand); }   // squat: tay nắm đòn sau gáy, khuỷu chúi xuống
    const el = along(S0, LEN.upper, ua), wr = along(el, LEN.fore, fa), fist = along(wr, 0.035, fa);
    const R = [];
    const sl = fullSleeve ? (outfit === 'labcoat' ? 'ink' : top) : skin;
    R.push(limb(S0, el, sc([0.05, 0.054, 0.05, 0.042, 0.034], bd), sc([0.048, 0.052, 0.048, 0.04, 0.032], bd), sl, { tone: tone(far) }));
    R.push(limb(el, wr, sc([0.034, 0.04, 0.034, 0.027, 0.022], bd), sc([0.032, 0.036, 0.03, 0.024, 0.02], bd), sl, { tone: tone(far) + 0.04 }));
    R.push(E(fist[0], fist[1], 0.042 * bd, 0.04 * bd, skin, { tone: tone(far) + 0.06 }));
    if (outfit === 'tee' || outfit === 'jersey') R.push(limb(S0, along(S0, LEN.upper * 0.45, ua), sc([0.06, 0.062, 0.06], bd), sc([0.058, 0.06, 0.058], bd), top, { tone: tone(far) }));
    else if (!fullSleeve) R.push(E(S0[0], S0[1] + 0.005, 0.058 * bd, 0.05 * bd, skin, { tone: tone(far) }));
    if (!far) R.push(LN([along(S0, 0.07, ua), along(S0, 0.22, ua)], 'bg', 0.25, { fine: true, alpha: 0.18 }));
    R.push(MK(far ? 'hand_far' : 'hand', fist[0], fist[1], 0.05), MK(far ? 'elbow_far' : 'elbow', el[0], el[1], 0.04));
    if (!far) R.push(MK('shoulder', S0[0], S0[1], 0.06), MK('arm', (S0[0] + el[0]) / 2, (S0[1] + el[1]) / 2, 0.06));
    return R;
  };
  // ---- chân ----
  const leg = (i, far) => {
    const L = legs[i], hp = T(L.hip), kn = T(L.knee), an = T(L.ank), R = [];
    R.push(limb(hp, kn, sc([0.088, 0.092, 0.084, 0.074, 0.062, 0.052], bd), sc([0.066, 0.078, 0.084, 0.078, 0.064, 0.054], bd), skin, { tone: tone(far) }));
    R.push(limb(kn, an, sc([0.05, 0.072, 0.07, 0.054, 0.036, 0.028], bd), sc([0.048, 0.044, 0.04, 0.034, 0.028, 0.026], bd), skin, { tone: tone(far) + 0.04 }));
    if (!far) {
      R.push(LN([along(hp, 0.12, L.th), along(hp, 0.36, L.th)].map((q) => add(q, [Math.cos(L.th) * 0.035, -Math.sin(L.th) * 0.035])), 'bg', 0.25, { fine: true, alpha: 0.16 }));
      R.push(LN([along(kn, 0.06, L.sh), along(kn, 0.2, L.sh)].map((q) => add(q, [-Math.cos(L.sh) * 0.03, Math.sin(L.sh) * 0.03])), 'bg', 0.25, { fine: true, alpha: 0.18 }));
    }
    const shorts = lower === 'pants' ? 1.0 : lower === 'tights' ? 0.62 : 0.4;
    R.push(limb(hp, along(hp, LEN.thigh * shorts, L.th), sc([0.1, 0.1, 0.096], bd), sc([0.08, 0.088, 0.09], bd), bottom, { tone: tone(far) }));
    if (lower === 'pants') R.push(limb(kn, along(kn, LEN.shank * 0.92, L.sh), sc([0.056, 0.06, 0.05], bd), sc([0.052, 0.046, 0.042], bd), bottom, { tone: tone(far) + 0.04 }));
    const shoe = (pts, role, tn, extra = {}) => PG(pts.map((q) => T(L.toW(q))), role, { tone: tn + tone(far), ...extra });
    if (S.shoe === false) R.push(shoe(FOOT_BARE, skin, 0.06));
    else {
      R.push(shoe(SHOE_UP, shoeRole, 0), shoe(SHOE_MID, 'ink', 0.04), shoe(SHOE_OUT, 'ink', 0.55, { fine: true }));
      for (let k = 0; k < 3; k++) { const a = L.toW([0.07 + k * 0.035, -0.03 + k * 0.012]), b = L.toW([0.085 + k * 0.035, -0.012 + k * 0.012]); R.push(LN([T(a), T(b)], 'ink', 0.3, { fine: true, alpha: 0.7 })); }
      R.push(PG([[-0.045, -0.06], [0.02, -0.066], [0.026, -0.048], [-0.04, -0.044]].map((q) => T(L.toW(q))), 'ink', { fine: true, tone: 0.1 + tone(far) }));
    }
    const mid = T(L.toW([0.07, 0.078])), heel = T(L.toW([-0.05, 0.03]));
    R.push(MK(far ? 'foot_far' : 'foot', mid[0], mid[1] - 0.03, 0.08), MK(far ? 'knee_far' : 'knee', kn[0], kn[1], 0.06), MK(far ? 'sole_far' : 'sole', mid[0], mid[1], 0.06));
    if (!far) R.push(MK('thigh', (hp[0] + kn[0]) / 2, (hp[1] + kn[1]) / 2, 0.09), MK('calf', lerp(kn[0], an[0], 0.35) - 0.03, lerp(kn[1], an[1], 0.35), 0.06),
      MK('heel', heel[0], heel[1], 0.05), MK('ankle', an[0], an[1], 0.04));
    return R;
  };
  // ---- thân ----
  const back = [[-0.05, -0.565], [-0.088, -0.52], [-0.112, -0.44], [-0.11, -0.34], [-0.088, -0.22], [-0.082, -0.14], [-0.116, -0.05], [-0.102, 0.04], [-0.06, 0.078]];
  const front = S.female
    ? [[0.06, 0.066], [0.09, 0.0], [0.094, -0.08], [0.086, -0.18], [0.092, -0.27], [0.15, -0.33], [0.142, -0.4], [0.105, -0.46], [0.07, -0.53], [0.04, -0.565]]
    : [[0.06, 0.066], [0.086, 0.0], [0.095, -0.08], [0.09, -0.18], [0.1, -0.28], [0.126, -0.37], [0.112, -0.46], [0.07, -0.53], [0.04, -0.565]];
  const torsoPts = [...back, ...front].map(([x, y]) => [x * bd, y]);
  const torso = [];
  torso.push(PG(torsoPts.map(tor), top));
  torso.push(PG([[-0.03 * bd, -0.565], [0.035 * bd, -0.565], [0.07 * bd, -0.5], [0.02, -0.47], [-0.04 * bd, -0.52]].map(tor), skin));     // cổ áo khoét (da)
  if (outfit === 'singlet' || outfit === 'tank') torso.push(PG([[-0.07 * bd, -0.5], [0.04 * bd, -0.5], [0.07 * bd, -0.44], [0.02, -0.38], [-0.07 * bd, -0.4]].map(tor), skin, { alpha: 0.95 }));
  torso.push(PG([[-0.114, -0.07], [0.094, -0.07], [0.09, 0.0], [0.062, 0.07], [-0.06, 0.08], [-0.104, 0.04]].map(([x, y]) => [x * bd, y]).map(tor), bottom));
  torso.push(LN([[0.05 * bd, -0.2], [0.07 * bd, -0.1]].map(tor), 'bg', 0.22, { fine: true, alpha: 0.16 }), LN([[-0.06 * bd, -0.44], [-0.02, -0.3]].map(tor), 'bg', 0.22, { fine: true, alpha: 0.14 }));
  if (outfit === 'labcoat') torso.push(PG([[-0.118 * bd, -0.5], [0.1 * bd, -0.5], [0.13 * bd, 0.0], [0.15 * bd, 0.36], [-0.14 * bd, 0.36], [-0.122 * bd, 0.0]].map(tor), 'ink', { tone: 0.06 }), LN([[0.06 * bd, -0.5], [0.09 * bd, 0.34]].map(tor), 'bg', 0.25, { fine: true, alpha: 0.4 }));
  if (outfit === 'hoodie') torso.push(PG([[-0.1 * bd, -0.56], [-0.16 * bd, -0.5], [-0.15 * bd, -0.42], [-0.08 * bd, -0.44]].map(tor), top, { tone: 0.18 }));
  if (outfit === 'shirt') torso.push(PG([[-0.03 * bd, -0.565], [0.05 * bd, -0.555], [0.07 * bd, -0.5], [0.0, -0.52]].map(tor), 'ink', { tone: 0.12 }));
  if (outfit === 'jersey') torso.push(PG([[-0.112 * bd, -0.4], [0.12 * bd, -0.4], [0.115 * bd, -0.36], [-0.11 * bd, -0.36]].map(tor), 'ink', { tone: 0.15, alpha: 0.8 }));
  if (S.number) torso.push(PG([[-0.01, -0.3], [0.09 * bd, -0.3], [0.095 * bd, -0.2], [-0.005, -0.2]].map(tor), 'ink', { tone: 0.02 }), LN([[0.025, -0.25], [0.07 * bd, -0.25]].map(tor), 'bg', 0.4, { fine: true }));
  torso.push(MK('center', ...tor([0, -0.27]), 0.2), MK('chest', ...tor([0.05, -0.4]), 0.11), MK('heart', ...tor([0.04, -0.39]), 0.07), MK('lungs', ...tor([0.0, -0.4]), 0.13),
    MK('belly', ...tor([0.05, -0.16]), 0.1), MK('stomach', ...tor([0.045, -0.24]), 0.07), MK('liver', ...tor([0.02, -0.27]), 0.08), MK('back', ...tor([-0.1, -0.34]), 0.08),
    MK('spine', ...tor([-0.07, -0.22]), 0.1), MK('hip', ...T([0, 0]), 0.1), MK('neck', ...tor([0.0, -0.57]), 0.05));
  // ---- đầu (mặt nghiêng quay phải) ----
  const nTop = tor([0.03, -0.615]), hr = 0.104, ha = P.head + Math.sin(t * 0.8 + ph * 9) * 0.02;
  const hc = add(nTop, rot([0.015, -0.085], [0, 0], P.lean * 0.4));
  const H = [];
  const hp = (pts) => pts.map(([x, y]) => [hc[0] + x * hr, hc[1] + y * hr]);
  H.push(limb(tor([0.0, -0.53]), add(nTop, [0, 0.01]), [0.05, 0.048, 0.046], [0.042, 0.04, 0.04], skin, { tone: 0.12 }));
  if (style === 'pony') { const sw = Math.sin((t * 2.6 + ph) * TAU) * 0.25; H.push(PG(hp([[-0.85, -0.35], [-1.25, -0.2 + sw * 0.3], [-1.7, 0.35 + sw], [-1.55, 0.55 + sw], [-1.05, 0.15], [-0.8, 0.0]]), hair)); }
  if (style === 'long') H.push(PG(hp([[-0.9, -0.4], [-1.05, 0.4], [-0.9, 1.25], [-0.2, 1.2], [-0.35, 0.3]]), hair));
  if (style === 'afro') H.push(E(hc[0] - 0.15 * hr, hc[1] - 0.25 * hr, 1.35 * hr, 1.2 * hr, hair));
  H.push(PG(hp([[-0.55, 0.58], [-0.86, 0.26], [-0.96, -0.15], [-0.8, -0.6], [-0.36, -0.92], [0.15, -0.96], [0.55, -0.76], [0.78, -0.42], [0.85, -0.14], [0.8, -0.02],
    [0.9, 0.12], [0.99, 0.26], [0.86, 0.34], [0.88, 0.45], [0.8, 0.53], [0.85, 0.62], [0.75, 0.78], [0.55, 0.9], [0.18, 0.86], [-0.08, 0.64], [-0.3, 0.62]]), skin));
  H.push(PG(hp([[-0.08, 0.64], [0.18, 0.86], [0.55, 0.9], [0.4, 0.78], [0.1, 0.7]]), skin, { tone: 0.12, fine: true }));
  H.push(E(hc[0] - 0.25 * hr, hc[1] + 0.06 * hr, 0.13 * hr, 0.2 * hr, skin, { tone: 0.14 }), E(hc[0] - 0.24 * hr, hc[1] + 0.07 * hr, 0.05 * hr, 0.1 * hr, skin, { tone: 0.3, fine: true }));
  if (style === 'bald') H.push(PG(hp([[-0.9, -0.1], [-0.8, -0.55], [-0.5, -0.82], [-0.6, -0.5], [-0.75, -0.1]]), skin, { tone: 0.1, fine: true }));
  else if (style === 'cap') H.push(PG(hp([[-0.98, -0.05], [-0.9, -0.55], [-0.5, -0.95], [0.1, -1.02], [0.6, -0.8], [0.78, -0.45], [1.35, -0.38], [1.3, -0.3], [0.7, -0.32], [-0.5, -0.3]]), hair));
  else if (style === 'helmet') { H.push(PG(hp([[-1.12, 0.05], [-1.05, -0.6], [-0.55, -1.12], [0.25, -1.18], [0.85, -0.86], [1.02, -0.4], [0.86, -0.32], [-0.2, -0.36], [-0.8, -0.1]]), hair)); for (const k of [0, 1, 2]) H.push(LN(hp([[-0.6 + k * 0.45, -1.05 + k * 0.02], [-0.45 + k * 0.42, -0.45]]), 'bg', 0.3, { fine: true, alpha: 0.5 })); }
  else if (style === 'buzz') H.push(PG(hp([[-0.96, 0.05], [-0.92, -0.45], [-0.62, -0.84], [-0.1, -1.0], [0.42, -0.88], [0.7, -0.56], [0.4, -0.66], [-0.1, -0.6], [-0.5, -0.42], [-0.7, 0.05]]), hair, { alpha: 0.7 }));
  else if (style === 'afro' || style === 'curly') { H.push(PG(hp([[-0.98, 0.12], [-0.94, -0.42], [-0.62, -0.86], [-0.1, -1.04], [0.45, -0.92], [0.76, -0.56], [0.72, -0.44], [0.32, -0.62], [-0.08, -0.52], [-0.42, -0.36], [-0.56, 0.02], [-0.8, 0.2]]), hair)); for (let i = 0; i < 6; i++) { const a = -PI * 0.95 + i * PI * 0.16; H.push(E(hc[0] + Math.cos(a) * hr * 0.95, hc[1] + Math.sin(a) * hr * 0.95, 0.24 * hr, 0.22 * hr, hair)); } }
  else H.push(PG(hp([[-0.98, 0.12], [-0.94, -0.42], [-0.62, -0.86], [-0.1, -1.04], [0.45, -0.92], [0.76, -0.56], [0.72, -0.44], [0.32, -0.62], [-0.08, -0.52], [-0.42, -0.36], [-0.56, 0.02], [-0.8, 0.2]]), hair));
  if (o.beard) H.push(PG(hp(o.beard === 'stubble' ? [[-0.1, 0.5], [0.2, 0.84], [0.56, 0.9], [0.84, 0.66], [0.7, 0.62], [0.5, 0.72], [0.22, 0.66], [0.05, 0.42]]
    : [[-0.2, 0.3], [0.1, 0.92], [0.5, 1.08], [0.9, 0.72], [0.86, 0.58], [0.62, 0.66], [0.66, 0.5], [0.3, 0.52], [0.05, 0.25]]), hair, { alpha: o.beard === 'stubble' ? 0.45 : 1, fine: o.beard === 'stubble' }));
  if (o.glasses) H.push(E(hc[0] + 0.58 * hr, hc[1] - 0.04 * hr, 0.2 * hr, 0.16 * hr, 'ink', { fine: true, fill: false, w: 0.45, tone: 0.2 }), LN(hp([[0.38, -0.06], [-0.2, -0.02]]), 'ink', 0.35, { fine: true, tone: 0.2 }));
  // mắt, lông mày, miệng theo biểu cảm
  const ex = 0.56, ey = -0.04, closed = blink >= 1 || A === 'sleep' || X === 'sleepy';
  const gx = (o.gaze && o.gaze[0]) || 0, gy = (o.gaze && o.gaze[1]) || 0;
  if (closed) H.push(LN(hp([[ex - 0.12, ey + 0.02], [ex + 0.1, ey + 0.03]]), 'bg', 0.4, { fine: true }));
  else {
    const open = X === 'shock' ? 1.5 : X === 'angry' ? 0.7 : 1;
    H.push(E(hc[0] + ex * hr, hc[1] + ey * hr, 0.12 * hr, 0.062 * hr * open, 'ink', { fine: true, tone: 0.06 }));
    H.push(E(hc[0] + (ex + 0.05 + gx * 0.04) * hr, hc[1] + (ey + gy * 0.03) * hr, 0.05 * hr, 0.055 * hr * Math.min(1.2, open), 'bg', { fine: true }));
  }
  const brow = { sad: [0.08, -0.06], angry: [-0.08, 0.08], shock: [-0.1, -0.1], happy: [0, -0.03] }[X] || [0, 0];
  H.push(LN(hp([[ex - 0.16, ey - 0.16 + brow[1]], [ex + 0.12, ey - 0.17 + brow[0] + brow[1]]]), hair, 0.45, { fine: true }));
  const mx = 0.72, my = 0.56, talk = clamp(Number(o.talk) || 0);
  if (talk > 0.05 || X === 'shock') H.push(E(hc[0] + mx * hr, hc[1] + (my + 0.02) * hr, 0.08 * hr, (0.04 + 0.1 * Math.max(talk, X === 'shock' ? 0.7 : 0)) * hr, 'bg', { fine: true }));
  else if (X === 'happy' || X === 'love') H.push(LN(hp([[mx - 0.12, my - 0.04], [mx - 0.02, my + 0.04], [mx + 0.1, my + 0.0]]), 'bg', 0.4, { fine: true }));
  else if (X === 'sad') H.push(LN(hp([[mx - 0.12, my + 0.05], [mx - 0.02, my - 0.01], [mx + 0.1, my + 0.03]]), 'bg', 0.4, { fine: true }));
  else if (X === 'angry' || A === 'tired' || A === 'squat') H.push(PG(hp([[mx - 0.12, my - 0.02], [mx + 0.11, my - 0.02], [mx + 0.1, my + 0.06], [mx - 0.1, my + 0.06]]), 'ink', { fine: true, tone: 0.1 }));
  else H.push(LN(hp([[mx - 0.1, my + 0.01], [mx + 0.1, my + 0.0]]), 'bg', 0.35, { fine: true }));
  if (o.sweat > 0.05 || A === 'tired') { const k = ((t * 0.9) % 1); H.push(E(hc[0] + 0.2 * hr, hc[1] + (-0.3 + k * 1.2) * hr, 0.05 * hr, 0.08 * hr, 'cold', { fine: true, alpha: 1 - k })); }
  H.push(MK('head', hc[0], hc[1], hr * 1.05), MK('top', hc[0], hc[1] - hr * 0.95, hr * 0.3), MK('eye', hc[0] + ex * hr, hc[1] + ey * hr, hr * 0.14),
    MK('brain', hc[0] - 0.05 * hr, hc[1] - 0.3 * hr, hr * 0.6), MK('mouth', hc[0] + mx * hr, hc[1] + my * hr, hr * 0.16), MK('ear', hc[0] - 0.25 * hr, hc[1] + 0.06 * hr, hr * 0.2),
    MK('nose', hc[0] + 0.95 * hr, hc[1] + 0.24 * hr, hr * 0.1));
  const head = xf(H, nTop, ha);
  // ---- tạ đòn (squat) ----
  const bar = [], plateBack = [];
  const plate = (c, R, out) => { out.push(E(c[0], c[1], R, R, 'dim', { tone: 0.12 }), E(c[0], c[1], R * 0.86, R * 0.86, 'dim', { tone: 0.28 }), E(c[0], c[1], R * 0.62, R * 0.62, 'dim', { tone: 0.18, fine: true }), E(c[0], c[1], R * 0.12, R * 0.12, 'ink', { tone: 0.35 })); };
  if (P.bar) { const b = tor([-0.075, -0.49]); plate(b, 0.225, plateBack); bar.push(E(b[0], b[1], 0.03, 0.03, 'dim', { tone: 0.05 }), E(b[0], b[1], 0.018, 0.018, 'ink', { tone: 0.3, fine: true })); }
  if (P.dead) { const hd = along(along(tor([-0.008, -0.47]), LEN.upper, P.sh[0] + P.lean), LEN.fore + 0.035, P.sh[0] + P.lean); const c = [hd[0], Math.min(hd[1], ground - 0.225)]; plate(c, 0.225, plateBack); bar.push(E(c[0], c[1], 0.03, 0.03, 'dim', { tone: 0.05 })); }
  if (A === 'curl') for (const [i, far] of [[1, true], [0, false]]) {
    const S0 = tor([-0.008, -0.47]), ua = P.sh[i] + P.lean, el = along(S0, LEN.upper, ua), fist = along(el, LEN.fore + 0.035, ua + P.elb[i]);
    (far ? plateBack : bar).push(E(fist[0], fist[1], 0.062, 0.062, 'dim', { tone: 0.15 + (far ? 0.2 : 0) }), E(fist[0], fist[1], 0.045, 0.045, 'dim', { tone: 0.32, fine: true }), E(fist[0], fist[1], 0.012, 0.012, 'ink', { tone: 0.3, fine: true }));
  }

  // ---- ráp theo chiều sâu: tay xa, chân xa, thân, chân gần, đầu, tạ, tay gần ----
  const bk = bike ? [...bike.prims, bike.crank(1)] : [], bkNear = bike ? [bike.crank(0)] : [];
  let L = [...plateBack, ...arm(1, true), ...leg(1, true), ...bk, ...torso, ...bkNear, ...leg(0, false), ...head, ...bar, ...arm(0, false)];
  if (A === 'curl') L = [...plateBack, ...arm(1, true), ...leg(1, true), ...torso, ...leg(0, false), ...head, ...arm(0, false), ...bar];
  if (xr > 0.01) L = L.map((p) => (p.fine || p.anchor ? p : { ...p, alpha: fade(p.alpha ?? 1) }));

  // ---- cơ quan (x-ray) ----
  if (xr > 0.01 && organs.length) {
    const al = clamp(xr * 1.25), f = Math.round(t * 30), O = [];
    const orgAt = (name, q, half, args = {}, a = 0) => xf(placeIcon(name, ...tor(q), half, { f, ...args }, { alpha: al }), tor(q), P.lean + a);
    for (const nm of organs) {
      if (nm === 'lungs') O.push(...orgAt('lungs', [0.0, -0.4], 0.12, { p: 0.5 + 0.5 * P.breath }));
      else if (nm === 'heart') O.push(...orgAt('heart', [0.045, -0.385], 0.06));
      else if (nm === 'liver') O.push(...orgAt('liver', [0.025, -0.27], 0.085));
      else if (nm === 'stomach') { const q = tor([0.05, -0.235]); O.push(E(q[0], q[1], 0.05, 0.034, 'accent', { alpha: al, organ: 1, rot: P.lean - 0.5 })); }
      else if (nm === 'brain') { const q = rot(add(hc, [-0.05 * hr, -0.25 * hr]), nTop, ha); O.push(...xf(placeIcon('brain', q[0], q[1], hr * 0.82, { f }, { alpha: al }), q, ha)); }
      else if (nm === 'spine' || nm === 'skeleton') {
        const sq = clamp(Number(o.p) || 0), segs = 9;
        for (let k = 0; k < segs; k++) {
          const yy = -0.555 + k * (0.52 / segs), bx = lerp(-0.06, -0.072, Math.sin(k / segs * PI)) * bd + (k > 5 ? 0.008 * (k - 5) : 0), h = (0.52 / segs) * (1 - 0.3 * sq * 0.5);
          const vb = [[bx - 0.025, yy], [bx + 0.022, yy], [bx + 0.024, yy + h * 0.68], [bx - 0.023, yy + h * 0.68]];
          O.push(PG(vb.map(tor), 'ink', { alpha: al, tone: 0.1, organ: 1 }));
          const dyy = yy + h * 0.68, dh = h * 0.32 * (1 - 0.55 * sq);
          O.push(PG([[bx - 0.022, dyy + 0.002], [bx + 0.02, dyy + 0.002], [bx + 0.02, dyy + dh], [bx - 0.022, dyy + dh]].map(tor), 'cold', { alpha: al, organ: 1, tone: 0.1 * sq }));
        }
      } else if (nm === 'muscles') {
        for (const [i, far] of [[1, true], [0, false]]) {
          const Lg = legs[i], hp2 = T(Lg.hip), kn = T(Lg.knee), an = T(Lg.ank);
          O.push(limb(along(hp2, 0.05, Lg.th), along(hp2, LEN.thigh * 0.92, Lg.th), sc([0.05, 0.07, 0.072, 0.06, 0.04], bd), sc([0.05, 0.07, 0.075, 0.066, 0.045], bd), 'hot', { alpha: al * 0.9, tone: tone(far), organ: 1 }));
          O.push(limb(along(kn, 0.04, Lg.sh), along(kn, LEN.shank * 0.7, Lg.sh), sc([0.04, 0.058, 0.05, 0.03], bd), sc([0.02, 0.022, 0.02, 0.016], bd), 'hot', { alpha: al * 0.9, tone: tone(far) + 0.08, organ: 1 }));
          if (!far) for (let k = 0; k < 4; k++) O.push(LN([along(hp2, 0.1, Lg.th), along(hp2, 0.36, Lg.th)].map((q) => add(q, [Math.cos(Lg.th) * (k - 1.5) * 0.022, -Math.sin(Lg.th) * (k - 1.5) * 0.022])), 'bg', 0.2, { fine: true, alpha: al * 0.4, organ: 1 }));
          void an;
        }
      } else if (nm === 'vessels') {
        const hq = tor([0.045, -0.385]);
        for (const [i, far] of [[1, true], [0, false]]) {
          const Lg = legs[i], pts = [hq, tor([0.01, -0.2]), T([0.02, 0.02]), along(T(Lg.hip), LEN.thigh * 0.95, Lg.th), along(T(Lg.knee), LEN.shank * 0.9, Lg.sh), T(Lg.toW([0.12, 0.05]))];
          O.push(LN(pts, 'hot', 0.55, { alpha: al * (far ? 0.6 : 1), organ: 1 }), LN(pts.map((q) => add(q, [-0.02, 0])), 'cold', 0.45, { alpha: al * (far ? 0.5 : 0.85), organ: 1 }));
        }
      } else if (nm === 'fuel') {                                     // kho glycogen: gan + cơ đùi sáng theo p (1 = đầy, 0 = cạn)
        const lv = clamp(o.p ?? 1), glow = 0.25 + 0.75 * lv;
        O.push(...orgAt('liver', [0.025, -0.27], 0.085, { role: lv > 0.2 ? 'accent' : 'dim' }).map((p) => ({ ...p, alpha: (p.alpha ?? 1) * glow })));
        for (const [i, far] of [[1, true], [0, false]]) {
          const Lg = legs[i], hp2 = T(Lg.hip);
          O.push(limb(along(hp2, 0.05, Lg.th), along(hp2, LEN.thigh * 0.92, Lg.th), sc([0.05, 0.07, 0.072, 0.06, 0.04], bd), sc([0.05, 0.07, 0.075, 0.066, 0.045], bd), lv > 0.2 ? 'accent' : 'dim', { alpha: al * glow * (far ? 0.7 : 1), organ: 1 }));
          const n = Math.round(lv * 6);
          for (let k = 0; k < n; k++) { const q = along(hp2, 0.1 + k * 0.045, Lg.th); O.push(E(q[0] + Math.cos(Lg.th) * ((k % 2) - 0.5) * 0.05, q[1], 0.014, 0.014, 'accent', { alpha: al, fine: true, organ: 1, tone: -0.2 })); }
        }
      }
    }
    L.push(...O);
  }
  if (A === 'sleep') { L = xf(L, [0, ground], -PI / 2, 0.86, -0.13); for (let i = 0; i < 3; i++) { const u2 = ((t * 0.45 + ph) + i / 3) % 1; L.push(E(0.75 + u2 * 0.2, 0.55 - u2 * 0.5, 0.03 + u2 * 0.03, 0.03 + u2 * 0.03, 'ink', { fine: true, alpha: (1 - u2) * 0.6, fill: false, w: 0.5 })); } }
  else if (P.whole) L = xf(L, [0, ground], P.whole);
  void hipW;
  return L;
}

// ======================= vòng 23: góc CHÍNH DIỆN / SAU LƯNG =======================
// Cùng hệ toạ độ với góc nghiêng (mặt đất y = 0.9, 1 đơn vị ≈ 1 m). Góc khớp lấy từ posePlan (gập hông/gối/vai theo
// mặt phẳng dọc) rồi CHIẾU lên mặt phẳng trán: đoạn chi gập về phía máy quay ngắn lại theo cos(góc) — đùi đưa ra trước
// khi chạy ngắn đi, bàn chân nhấc lên; thân nghiêng (squat/deadlift) thấp và ngắn lại. Tạ đòn nằm ngang qua vai (squat)
// hay trước đùi (deadlift) với bánh tạ nhìn cạnh ở hai đầu — kiểu nhìn quen thuộc trong phòng gym.
export const FRONT_ACTIONS = ['idle', 'walk', 'run', 'jump', 'cheer', 'wave', 'point', 'tired', 'curl', 'squat', 'deadlift', 'sit'];

function frontHead(hc, hr, style, hair, skin, X, blink, o, back, A) {
  const H = [], rx = hr * 0.84, ry = hr * 1.04, hp = (pts) => pts.map(([x, y]) => [hc[0] + x * rx, hc[1] + y * ry]);
  const hairBack = [];
  if (style === 'long') hairBack.push(PG(hp([[-1.12, -0.3], [-1.2, 0.6], [-1.08, 1.7], [1.08, 1.7], [1.2, 0.6], [1.12, -0.3]]), hair));
  if (style === 'afro') hairBack.push(E(hc[0], hc[1] - ry * 0.25, rx * 1.55, ry * 1.25, hair));
  if (style === 'pony' && back) hairBack.push(PG(hp([[-0.25, 0.2], [0.25, 0.2], [0.18, 1.5], [-0.18, 1.5]]), hair));
  H.push(E(hc[0] - rx * 0.98, hc[1] + ry * 0.08, rx * 0.16, ry * 0.2, skin, { tone: 0.12 }), E(hc[0] + rx * 0.98, hc[1] + ry * 0.08, rx * 0.16, ry * 0.2, skin, { tone: 0.12 }));
  H.push(PG(hp([[-1, -0.25], [-0.98, 0.25], [-0.8, 0.68], [-0.42, 0.95], [0, 1.02], [0.42, 0.95], [0.8, 0.68], [0.98, 0.25], [1, -0.25], [0.8, -0.78], [0, -1.0], [-0.8, -0.78]]), skin));
  if (!back) {
    H.push(PG(hp([[-0.8, 0.68], [-0.42, 0.95], [0, 1.02], [0.42, 0.95], [0.8, 0.68], [0.5, 0.86], [0, 0.92], [-0.5, 0.86]]), skin, { tone: 0.12, fine: true }));
    if (o.beard) {
      const bp = o.beard === 'stubble'
        ? [[-0.86, 0.35], [-0.6, 0.85], [0, 1.03], [0.6, 0.85], [0.86, 0.35], [0.5, 0.62], [0, 0.72], [-0.5, 0.62]]
        : [[-0.92, 0.2], [-0.8, 0.82], [-0.3, 1.15], [0, 1.2], [0.3, 1.15], [0.8, 0.82], [0.92, 0.2], [0.55, 0.5], [0.22, 0.42], [0, 0.5], [-0.22, 0.42], [-0.55, 0.5]];
      H.push(PG(hp(bp), hair, { alpha: o.beard === 'stubble' ? 0.45 : 1, fine: o.beard === 'stubble' }));
    }
    const ey = -0.02, ex = 0.38, closed = blink >= 1 || X === 'sleepy' || A === 'sleep', open = X === 'shock' ? 1.45 : X === 'angry' ? 0.7 : 1;
    const gx = (o.gaze && o.gaze[0]) || 0, gy = (o.gaze && o.gaze[1]) || 0;
    const br = { sad: [0.06, -0.05], angry: [-0.06, 0.06], shock: [-0.08, -0.08], happy: [0, -0.03] }[X] || [0, 0];
    for (const s of [-1, 1]) {
      if (closed) H.push(LN(hp([[s * ex - 0.16, ey + 0.02], [s * ex + 0.16, ey + 0.02]]), 'bg', 0.4, { fine: true }));
      else {
        H.push(E(hc[0] + s * ex * rx, hc[1] + ey * ry, 0.17 * rx, 0.1 * ry * open, 'ink', { fine: true, tone: 0.05 }));
        H.push(E(hc[0] + (s * ex + gx * 0.06) * rx, hc[1] + (ey + gy * 0.04) * ry, 0.075 * rx, 0.085 * ry * Math.min(1.2, open), 'bg', { fine: true }));
      }
      const inner = s * (ex - 0.18), outer = s * (ex + 0.18);
      H.push(LN(hp([[inner, ey - 0.2 + br[1] + br[0]], [outer, ey - 0.22 + br[1]]]), hair, 0.45, { fine: true }));
    }
    if (o.glasses) {
      for (const s of [-1, 1]) H.push(E(hc[0] + s * ex * rx, hc[1] + ey * ry, 0.27 * rx, 0.2 * ry, 'ink', { fine: true, fill: false, w: 0.45, tone: 0.2 }));
      H.push(LN(hp([[-0.12, ey - 0.02], [0.12, ey - 0.02]]), 'ink', 0.4, { fine: true, tone: 0.2 }));
    }
    H.push(LN(hp([[0.02, 0.12], [0.1, 0.36], [-0.04, 0.4]]), skin, 0.4, { fine: true, tone: 0.32 }));
    const my = 0.62, talk = clamp(Number(o.talk) || 0);
    if (talk > 0.05 || X === 'shock') H.push(E(hc[0], hc[1] + my * ry, 0.2 * rx, (0.05 + 0.12 * Math.max(talk, X === 'shock' ? 0.7 : 0)) * ry, 'bg', { fine: true }));
    else if (X === 'happy' || X === 'love') H.push(LN(hp([[-0.24, my - 0.05], [0, my + 0.07], [0.24, my - 0.05]]), 'bg', 0.4, { fine: true }));
    else if (X === 'sad') H.push(LN(hp([[-0.22, my + 0.06], [0, my - 0.03], [0.22, my + 0.06]]), 'bg', 0.4, { fine: true }));
    else if (X === 'angry' || A === 'tired' || A === 'squat' || A === 'deadlift') H.push(PG(hp([[-0.22, my - 0.03], [0.22, my - 0.03], [0.2, my + 0.07], [-0.2, my + 0.07]]), 'ink', { fine: true, tone: 0.1 }));
    else H.push(LN(hp([[-0.18, my], [0.18, my]]), 'bg', 0.35, { fine: true }));
  }
  if (style === 'cap') {
    H.push(PG(hp([[-1.02, -0.28], [-0.95, -0.75], [-0.5, -1.06], [0.5, -1.06], [0.95, -0.75], [1.02, -0.28]]), hair));
    if (!back) H.push(PG(hp([[-0.95, -0.3], [0.95, -0.3], [0.8, -0.12], [-0.8, -0.12]]), hair, { tone: 0.2 }));
  } else if (style === 'helmet') {
    H.push(PG(hp([[-1.12, -0.18], [-1.08, -0.72], [-0.6, -1.15], [0, -1.24], [0.6, -1.15], [1.08, -0.72], [1.12, -0.18], [0.7, -0.4], [0, -0.48], [-0.7, -0.4]]), hair));
    for (const xx of [-0.45, 0, 0.45]) H.push(LN(hp([[xx, -1.12], [xx * 1.2, -0.55]]), 'bg', 0.3, { fine: true, alpha: 0.5 }));
  } else if (style !== 'bald') {
    const topPts = back ? [[-1.02, 0.55], [-1.05, -0.3], [-0.8, -0.85], [0, -1.08], [0.8, -0.85], [1.05, -0.3], [1.02, 0.55], [0.5, 0.75], [-0.5, 0.75]]
      : style === 'buzz' ? [[-1.0, -0.3], [-0.85, -0.8], [0, -1.04], [0.85, -0.8], [1.0, -0.3], [0.78, -0.62], [0, -0.78], [-0.78, -0.62]]
        : [[-1.04, -0.05], [-1.0, -0.6], [-0.6, -1.0], [0, -1.1], [0.6, -1.0], [1.0, -0.6], [1.04, -0.05], [0.86, -0.42], [0.3, -0.6], [-0.2, -0.5], [-0.7, -0.5], [-0.9, -0.3]];
    H.push(PG(hp(topPts), hair, { alpha: style === 'buzz' ? 0.75 : 1 }));
    if (style === 'curly' || style === 'afro') for (let i = 0; i < 7; i++) { const a = -PI + (i + 0.5) * PI / 7; H.push(E(hc[0] + Math.cos(a) * rx * 0.95, hc[1] + Math.sin(a) * ry * 0.88 - ry * 0.12, rx * 0.26, ry * 0.22, hair)); }
    if (style === 'bun') H.push(E(hc[0], hc[1] - ry * 1.12, rx * 0.36, ry * 0.3, hair));
    if (style === 'pony' && !back) H.push(PG(hp([[0.86, -0.2], [1.25, 0.1], [1.2, 0.7], [0.98, 0.3]]), hair));
  }
  H.push(MK('head', hc[0], hc[1], hr * 1.05), MK('top', hc[0], hc[1] - ry * 0.95, hr * 0.3), MK('eye', hc[0] + 0.38 * rx, hc[1] - 0.02 * ry, hr * 0.14),
    MK('brain', hc[0], hc[1] - 0.3 * ry, hr * 0.62), MK('mouth', hc[0], hc[1] + 0.62 * ry, hr * 0.16), MK('ear', hc[0] + rx, hc[1] + 0.08 * ry, hr * 0.2), MK('nose', hc[0], hc[1] + 0.3 * ry, hr * 0.1));
  return { back: hairBack, H };
}

/** người nhìn chính diện (back = sau lưng). S = loài, A = hành động (FRONT_ACTIONS), o như human(). */
export function humanFront(S, A, X, t, ph, body, blink, o = {}, back = false) {
  const P = posePlan(A, t, ph, o.cycle), bd = o.build || S.build || 1, ground = 0.9, fem = S.female;
  const skin = o.skin || 'skin', hair = o.hairRole || S.hairRole || 'hair', top = body, bottom = o.pants || S.pants || 'dim';
  const style = o.hair || S.style || 'short', outfit = o.outfit || S.top || 'tee', lower = o.bottom || S.bottom || 'shorts';
  const xr = clamp(Number(o.xray) || 0), organs = o.organs || [];
  const sw = (fem ? 0.165 : 0.19) * bd, hipW = (fem ? 0.1 : 0.09) * bd;
  const legs = [0, 1].map((i) => {
    const s = i ? -1 : 1, th = P.hip[i], sh = th - P.knee[i];
    const kOut = 0.01 + (A === 'squat' || A === 'sit' ? 0.07 : A === 'deadlift' ? 0.02 : 0.01) * Math.max(0, Math.sin(th));
    return { s, th, sh, kx: s * (hipW + kOut), ky: LEN.thigh * Math.cos(th), ax: s * (hipW + kOut * 0.4 + 0.012), ay: LEN.thigh * Math.cos(th) + LEN.shank * Math.cos(sh) };
  });
  const lowest = Math.max(legs[0].ay, legs[1].ay);
  const hy = ground - 0.075 - lowest - P.lift;
  const lean = P.lean, cl = Math.cos(lean), ysh = hy - 0.47 * cl, ynk = ysh - 0.035, hr = 0.104;
  const hc = [0, ynk - 0.135 + (A === 'tired' ? 0.04 : 0)];
  const fade = (al) => al * (1 - 0.66 * xr);
  const tn = (s) => (back ? (s > 0 ? 0.1 : 0.04) : (s > 0 ? 0.0 : 0.1));
  const head = frontHead(hc, hr, style, hair, skin, X, blink, o, back, A);
  // ---- chân + giày + quần ----
  const legPrims = [];
  for (const Lg of legs) {
    const hpJ = [Lg.s * hipW, hy], kn = [Lg.kx, hy + Lg.ky], an = [Lg.ax, hy + Lg.ay];
    const thick = sc([0.075, 0.08, 0.074, 0.062, 0.052], bd);
    legPrims.push(limb(hpJ, kn, thick, thick, skin, { tone: tn(Lg.s) }));
    legPrims.push(limb(kn, an, sc([0.052, 0.058, 0.05, 0.036, 0.03], bd), sc([0.05, 0.055, 0.048, 0.034, 0.028], bd), skin, { tone: tn(Lg.s) + 0.04 }));
    const cover = lower === 'pants' ? 2 : lower === 'tights' ? 1.6 : 0.42;
    if (cover >= 1) {
      legPrims.push(limb(hpJ, kn, sc([0.085, 0.088, 0.082, 0.07, 0.06], bd), sc([0.085, 0.088, 0.082, 0.07, 0.06], bd), bottom, { tone: tn(Lg.s) }));
      legPrims.push(limb(kn, [lerp(kn[0], an[0], cover - 1), lerp(kn[1], an[1], cover - 1)], sc([0.06, 0.062, 0.056], bd), sc([0.06, 0.062, 0.056], bd), bottom, { tone: tn(Lg.s) + 0.04 }));
    } else legPrims.push(limb(hpJ, [lerp(hpJ[0], kn[0], cover), lerp(hpJ[1], kn[1], cover)], sc([0.095, 0.095, 0.092], bd), sc([0.095, 0.095, 0.092], bd), bottom, { tone: tn(Lg.s) }));
    const fx = an[0] + Lg.s * 0.012, fy = an[1] + 0.035, sole = an[1] + 0.075;
    if (S.shoe === false) legPrims.push(E(fx, fy + 0.02, 0.05, 0.035, skin, { tone: 0.06 }));
    else legPrims.push(PG([[fx - 0.05, fy - 0.035], [fx + 0.05, fy - 0.035], [fx + 0.062, sole - 0.012], [fx + 0.056, sole], [fx - 0.056, sole], [fx - 0.062, sole - 0.012]], S.shoe || 'accent', { tone: tn(Lg.s) }),
      PG([[fx - 0.06, sole - 0.016], [fx + 0.06, sole - 0.016], [fx + 0.057, sole], [fx - 0.057, sole]], 'ink', { tone: 0.5, fine: true }));
    const near = (Lg.s > 0) !== back;
    legPrims.push(MK(near ? 'knee' : 'knee_far', kn[0], kn[1], 0.06), MK(near ? 'foot' : 'foot_far', fx, fy, 0.07), MK(near ? 'sole' : 'sole_far', fx, sole - 0.01, 0.05));
    if (near) legPrims.push(MK('thigh', (hpJ[0] + kn[0]) / 2, (hpJ[1] + kn[1]) / 2, 0.09), MK('calf', lerp(kn[0], an[0], 0.35), lerp(kn[1], an[1], 0.35), 0.06), MK('ankle', an[0], an[1], 0.04), MK('heel', fx, sole - 0.02, 0.04));
  }
  // ---- tạ: squat (đòn qua vai, sau gáy), deadlift (đòn trước đùi, bánh tạ chạm sàn ở đáy) ----
  const barPrims = [];
  const plateSide = (cx, cy) => {
    const sg = Math.sign(cx);
    for (const [dx, w, tone] of [[0, 0.05, 0.12], [0.055, 0.045, 0.22]]) { const x0 = cx + sg * dx; barPrims.push(PG([[x0 - w / 2, cy - 0.225], [x0 + w / 2, cy - 0.225], [x0 + w / 2, cy + 0.225], [x0 - w / 2, cy + 0.225]], 'dim', { tone })); }
    barPrims.push(PG([[cx - sg * 0.05, cy - 0.04], [cx - sg * 0.02, cy - 0.04], [cx - sg * 0.02, cy + 0.04], [cx - sg * 0.05, cy + 0.04]], 'ink', { tone: 0.3 }));
  };
  let barY = null;
  if (A === 'squat') barY = ysh - 0.015;
  if (A === 'deadlift') barY = Math.min(ysh + LEN.upper + LEN.fore + 0.03, ground - 0.225);
  if (barY !== null) { barPrims.push(LN([[-0.82, barY], [0.82, barY]], 'dim', 1.1, { tone: 0.05 })); plateSide(0.62, barY); plateSide(-0.62, barY); }
  // ---- thân ----
  const ty = (v) => hy - v * 0.47 * cl;                                     // v: 0 = hông, 1 = vai
  const wx = [hipW + 0.05 * bd, (fem ? 0.155 : 0.14) * bd, (fem ? 0.112 : 0.13) * bd, (fem ? 0.15 : 0.165) * bd, sw, 0.05];
  const wy = [-0.06, 0.1, 0.45, 0.82, 0.98, 1.04];
  const half = (sgn, xs) => xs.map((x, k) => [sgn * x, ty(wy[k])]);
  const torsoPts = [...half(-1, wx), ...half(1, wx).reverse()];
  const torso = [PG(torsoPts, skin)];
  const bare = outfit === 'tank' || outfit === 'singlet';
  const topPts = bare
    ? [[-wx[0], ty(-0.06)], [-wx[1], ty(0.1)], [-wx[2], ty(0.45)], [-(fem ? 0.14 : 0.15) * bd, ty(0.8)], [-0.1 * bd, ty(0.99)], [-0.06 * bd, ty(0.99)], [-0.04, ty(0.86)],
      [0.04, ty(0.86)], [0.06 * bd, ty(0.99)], [0.1 * bd, ty(0.99)], [(fem ? 0.14 : 0.15) * bd, ty(0.8)], [wx[2], ty(0.45)], [wx[1], ty(0.1)], [wx[0], ty(-0.06)]]
    : torsoPts.map((q, i) => (i === 5 || i === 6 ? [q[0] * 1.4, q[1] + 0.02] : q));
  torso.push(PG(topPts, top, { tone: back ? 0.06 : 0 }));
  if (outfit === 'labcoat') torso.push(PG([[-wx[0] - 0.02, ty(-0.5)], [-sw - 0.01, ty(0.98)], [-0.03, ty(0.9)], [-0.02, ty(-0.5)]], 'ink', { tone: 0.05 }), PG([[wx[0] + 0.02, ty(-0.5)], [sw + 0.01, ty(0.98)], [0.03, ty(0.9)], [0.02, ty(-0.5)]], 'ink', { tone: 0.12 }));
  if (!back && (outfit === 'shirt' || outfit === 'labcoat')) {
    torso.push(PG([[-0.06, ty(1.02)], [0, ty(0.9)], [0.06, ty(1.02)], [0.04, ty(1.05)], [0, ty(0.96)], [-0.04, ty(1.05)]], 'ink', { tone: 0.1 }));
    for (let k = 0; k < 4; k++) torso.push(E(0, ty(0.8 - k * 0.18), 0.008, 0.008, 'bg', { fine: true, alpha: 0.6 }));
  }
  if (!back && outfit === 'hoodie') torso.push(PG([[-0.08 * bd, ty(0.3)], [0.08 * bd, ty(0.3)], [0.1 * bd, ty(0.12)], [-0.1 * bd, ty(0.12)]], top, { tone: 0.14 }), LN([[-0.03, ty(0.98)], [-0.035, ty(0.78)]], 'ink', 0.3, { fine: true }), LN([[0.03, ty(0.98)], [0.035, ty(0.78)]], 'ink', 0.3, { fine: true }));
  if (outfit === 'hoodie') torso.push(PG([[-0.11, ty(1.0)], [0.11, ty(1.0)], [0.09, ty(1.12)], [-0.09, ty(1.12)]], top, { tone: 0.2 }));
  if (!back && (S.number || outfit === 'jersey')) torso.push(PG([[-0.07 * bd, ty(0.62)], [0.07 * bd, ty(0.62)], [0.07 * bd, ty(0.42)], [-0.07 * bd, ty(0.42)]], 'ink', { tone: 0.02 }), LN([[-0.035, ty(0.52)], [0.035, ty(0.52)]], 'bg', 0.4, { fine: true }));
  if (outfit === 'jersey') torso.push(PG([[-sw, ty(0.9)], [sw, ty(0.9)], [sw * 0.95, ty(0.82)], [-sw * 0.95, ty(0.82)]], 'ink', { tone: 0.15, alpha: 0.8 }));
  torso.push(PG([[-wx[0] - 0.005, ty(-0.02)], [wx[0] + 0.005, ty(-0.02)], [wx[0], ty(-0.16)], [-wx[0], ty(-0.16)]], bottom, { tone: 0.06 }));
  torso.push(limb([0, ynk + 0.04], [0, hc[1] + hr * 0.7], [0.042, 0.04, 0.04], [0.042, 0.04, 0.04], skin, { tone: 0.14 }));
  const ox = back ? -1 : 1;
  torso.push(MK('center', 0, ty(0.45), 0.2), MK('chest', 0, ty(0.78), 0.12), MK('heart', ox * 0.045, ty(0.74), 0.06), MK('lungs', 0, ty(0.75), 0.14), MK('belly', 0, ty(0.3), 0.1),
    MK('stomach', ox * 0.04, ty(0.5), 0.07), MK('liver', -ox * 0.05, ty(0.53), 0.08), MK('back', 0, ty(0.7), 0.1), MK('spine', 0, ty(0.5), 0.1), MK('hip', 0, hy, 0.12), MK('neck', 0, ynk, 0.05));
  // ---- tay (chiếu) ----
  const arms = [];
  for (const i of [0, 1]) {
    const s = i ? -1 : 1, S0 = [s * sw, ysh + 0.025];
    let el, hd;
    if (A === 'squat') { hd = [s * 0.3, barY + 0.01]; el = [s * (sw + 0.13), ysh + 0.17]; }
    else if (A === 'deadlift') { hd = [s * (sw + 0.035), barY]; el = [lerp(S0[0], hd[0], 0.5) + s * 0.012, lerp(S0[1], hd[1], 0.5)]; }
    else if (A === 'tired') { hd = [legs[i].kx * 1.05, hy + legs[i].ky - 0.02]; el = [s * (sw + 0.07), lerp(S0[1], hd[1], 0.5)]; }
    else if (A === 'point' && s > 0) { el = [S0[0] + LEN.upper * 0.98, S0[1] - 0.04]; hd = [el[0] + LEN.fore * 0.98, el[1] - 0.06]; }
    else if (A === 'wave' && s > 0) { const k = Math.sin((t * 2.2 + ph) * TAU); el = [S0[0] + 0.2, S0[1] - 0.16]; hd = [el[0] + 0.05 + k * 0.06, el[1] - 0.24]; }
    else if (A === 'cheer' || A === 'jump') { const k = Math.abs(Math.sin((t * (A === 'jump' ? 0.85 : 1.8) + ph) * PI)); el = [S0[0] + s * 0.16, S0[1] - 0.24 - k * 0.04]; hd = [el[0] + s * 0.1, el[1] - 0.26 - k * 0.03]; }
    else {
      const phi = P.sh[i] + lean, psi = phi + P.elb[i], abd = A === 'curl' ? 0.04 : A === 'run' ? 0.06 : 0.1;
      el = [S0[0] + s * (0.02 + abd * 0.5), S0[1] + LEN.upper * Math.cos(phi)];
      hd = [el[0] - s * 0.05 * Math.sin(Math.max(0, P.elb[i])), el[1] + LEN.fore * Math.cos(psi)];
    }
    const sleeve = outfit === 'hoodie' || outfit === 'shirt' || outfit === 'labcoat' ? 1.0 : outfit === 'tee' || outfit === 'jersey' ? 0.42 : 0;
    const armRole = outfit === 'labcoat' ? 'ink' : top;
    arms.push(limb(S0, el, sc([0.046, 0.05, 0.046, 0.04, 0.034], bd), sc([0.046, 0.05, 0.046, 0.04, 0.034], bd), sleeve >= 1 ? armRole : skin, { tone: tn(s) }));
    arms.push(limb(el, hd, sc([0.034, 0.038, 0.032, 0.026, 0.022], bd), sc([0.034, 0.038, 0.032, 0.026, 0.022], bd), sleeve >= 1 ? armRole : skin, { tone: tn(s) + 0.04 }));
    if (sleeve > 0 && sleeve < 1) arms.push(limb(S0, [lerp(S0[0], el[0], sleeve), lerp(S0[1], el[1], sleeve)], sc([0.058, 0.06, 0.058], bd), sc([0.058, 0.06, 0.058], bd), top, { tone: tn(s) }));
    if (bare) arms.push(E(S0[0], S0[1], 0.055 * bd, 0.05 * bd, skin, { tone: tn(s) }));
    arms.push(E(hd[0], hd[1], 0.04 * bd, 0.044 * bd, skin, { tone: tn(s) + 0.06 }));
    if (A === 'curl') {
      arms.push(PG([[hd[0] - 0.075, hd[1] - 0.012], [hd[0] + 0.075, hd[1] - 0.012], [hd[0] + 0.075, hd[1] + 0.012], [hd[0] - 0.075, hd[1] + 0.012]], 'dim', { tone: 0.3 }));
      for (const d of [-1, 1]) arms.push(PG([[hd[0] + d * 0.06, hd[1] - 0.05], [hd[0] + d * 0.1, hd[1] - 0.05], [hd[0] + d * 0.1, hd[1] + 0.05], [hd[0] + d * 0.06, hd[1] + 0.05]], 'dim', { tone: 0.12 }));
    }
    const near = (s > 0) !== back;
    arms.push(MK(near ? 'hand' : 'hand_far', hd[0], hd[1], 0.05), MK(near ? 'elbow' : 'elbow_far', el[0], el[1], 0.04));
    if (near) arms.push(MK('shoulder', S0[0], S0[1], 0.06), MK('arm', (S0[0] + el[0]) / 2, (S0[1] + el[1]) / 2, 0.06));
  }
  // ---- ráp: tóc sau, (đòn squat sau đầu), chân, (đòn deadlift), thân, đầu, tay ----
  let L = A === 'squat' ? [...head.back, ...barPrims, ...legPrims, ...torso, ...head.H, ...arms]
    : [...head.back, ...legPrims, ...barPrims, ...torso, ...head.H, ...arms];
  if (A === 'sit') L = [PG([[-0.3, hy + 0.02], [0.3, hy + 0.02], [0.3, ground], [-0.3, ground]], 'dim', { tone: 0.35 }), ...L];
  if (xr > 0.01) {
    L = L.map((p) => (p.fine || p.anchor ? p : { ...p, alpha: fade(p.alpha ?? 1) }));
    const al = clamp(xr * 1.25), f = Math.round(t * 30), O = [];
    for (const nm of organs) {
      if (nm === 'brain') O.push(...placeIcon('brain', hc[0], hc[1] - 0.03, hr * 0.82, { f }, { alpha: al }));
      else if (nm === 'heart') O.push(...placeIcon('heart', ox * 0.04, ty(0.74), 0.06, { f }, { alpha: al }));
      else if (nm === 'lungs') O.push(...placeIcon('lungs', 0, ty(0.75), 0.15, { f, p: 0.5 + 0.5 * P.breath }, { alpha: al }));
      else if (nm === 'liver') O.push(...placeIcon('liver', -ox * 0.05, ty(0.52), 0.09, { f }, { alpha: al }));
      else if (nm === 'stomach') O.push(E(ox * 0.045, ty(0.48), 0.055, 0.04, 'accent', { alpha: al, organ: 1 }));
      else if (nm === 'spine' || nm === 'skeleton') {
        for (let k = 0; k < 10; k++) {
          const yy = lerp(ynk + 0.02, hy, k / 10);
          O.push(PG([[-0.022, yy], [0.022, yy], [0.022, yy + 0.034], [-0.022, yy + 0.034]], 'ink', { alpha: al, organ: 1, tone: 0.1 }), PG([[-0.02, yy + 0.034], [0.02, yy + 0.034], [0.02, yy + 0.044], [-0.02, yy + 0.044]], 'cold', { alpha: al, organ: 1 }));
        }
      } else if (nm === 'muscles' || nm === 'fuel') {
        for (const Lg of legs) {
          const hpJ = [Lg.s * hipW, hy], kn = [Lg.kx, hy + Lg.ky], lv = nm === 'fuel' ? clamp(o.p ?? 1) : 1;
          const a0 = [lerp(hpJ[0], kn[0], 0.12), lerp(hpJ[1], kn[1], 0.12)], a1 = [lerp(hpJ[0], kn[0], 0.9), lerp(hpJ[1], kn[1], 0.9)];
          O.push(limb(a0, a1, sc([0.04, 0.06, 0.062, 0.05, 0.035], bd), sc([0.04, 0.06, 0.062, 0.05, 0.035], bd), nm === 'fuel' ? (lv > 0.2 ? 'accent' : 'dim') : 'hot', { alpha: al * (nm === 'fuel' ? 0.25 + 0.75 * lv : 0.9), organ: 1 }));
        }
      } else if (nm === 'vessels') for (const Lg of legs) O.push(LN([[ox * 0.04, ty(0.74)], [Lg.s * 0.03, hy], [Lg.kx, hy + Lg.ky], [Lg.ax, hy + Lg.ay]], 'hot', 0.5, { alpha: al, organ: 1 }));
    }
    L.push(...O);
  }
  return L;
}
