// Kho nhân vật hoạt hình 2D (vòng 10) — người/con vật sinh ra PRIMITIVE giống icon (circle/poly + vai màu ink|dim|hot|
// cold|accent|bg) để bút của MỌI look tự biến chúng thành tô phẳng, nét, pixel, halftone, bóng đen, cắt giấy…
// Gọi bằng tên icon "rig:<loài>[:<hành động>][:<biểu cảm>][:left|right]" (thứ tự tự do sau tên loài, vd "rig:dog:walk:happy")
// hoặc args {action, expr, face, t0} qua đường vẽ icon của core.js — mọi beat dùng được ngay.
// Dáng là hàm thuần của frame (thở, chớp mắt, chu kỳ đi/chạy, tai/đuôi trễ pha) → render song song/RESUME ra y hệt.
// Dữ liệu loài là bảng (không vẽ tay từng loài): thêm loài = thêm một dòng SPECIES. Python đọc SPECIES/ACTIONS/EXPRS/
// RIG_ALIASES ở chính file này (engines/html/rig2d.py) — một nguồn sự thật, test đối chiếu.
// Hệ toạ độ như icon: [-1,1], y xuống, mặt đất y = 0.9, mặc định quay mặt sang phải.
// Cờ primitive dùng chung với bút (core.js): fine (chi tiết mặt: chỉ tô, không viền/rung) · tone (tối đi về nền, chân xa)
// · pin (đinh khớp kiểu rối — chỉ look có pen.pins mới vẽ) · alpha.

// plan = bộ xương; body [nửa dài, nửa cao]; legs = chiều dài chân; head = bán kính đầu; snout [dài, cao]; ears/tail = kiểu.
// role = vai màu thân (ghi đè bằng role của icon), belly/muzzle/spots = vai màu phụ.
export const SPECIES = {
  dog: { plan: 'quad', body: [0.46, 0.21], legs: 0.34, legw: 0.07, head: 0.25, snout: [0.2, 0.12], ears: 'floppy', tail: 'wag', role: 'accent', belly: 'ink', nose: 'bg' },
  cat: { plan: 'quad', body: [0.43, 0.17], legs: 0.31, legw: 0.055, head: 0.23, snout: [0.07, 0.08], ears: 'pointy', tail: 'long', role: 'dim', belly: 'ink', nose: 'hot', whiskers: 1 },
  fox: { plan: 'quad', body: [0.44, 0.17], legs: 0.3, legw: 0.055, head: 0.22, snout: [0.24, 0.09], ears: 'tall', tail: 'bushy', role: 'hot', belly: 'ink', nose: 'bg' },
  wolf: { plan: 'quad', body: [0.5, 0.2], legs: 0.38, legw: 0.065, head: 0.24, snout: [0.25, 0.11], ears: 'tall', tail: 'bushy', role: 'dim', belly: 'ink', nose: 'bg' },
  bear: { plan: 'quad', body: [0.56, 0.31], legs: 0.27, legw: 0.12, head: 0.29, snout: [0.13, 0.12], ears: 'round', tail: 'stub', role: 'hot', belly: 'accent', nose: 'bg', heavy: 1 },
  rabbit: { plan: 'quad', body: [0.34, 0.22], legs: 0.22, legw: 0.07, head: 0.23, snout: [0.05, 0.07], ears: 'long', tail: 'puff', role: 'ink', belly: 'ink', nose: 'hot', hop: 1 },
  mouse: { plan: 'quad', body: [0.33, 0.16], legs: 0.15, legw: 0.04, head: 0.19, snout: [0.13, 0.07], ears: 'big', tail: 'thin', role: 'dim', belly: 'ink', nose: 'hot', whiskers: 1 },
  cow: { plan: 'quad', body: [0.56, 0.27], legs: 0.4, legw: 0.09, head: 0.22, snout: [0.12, 0.15], ears: 'side', tail: 'tuft', role: 'ink', belly: 'ink', nose: 'hot', spots: 'bg', horns: 1, hooves: 1 },
  pig: { plan: 'quad', body: [0.47, 0.28], legs: 0.22, legw: 0.075, head: 0.25, snout: [0.07, 0.11], ears: 'flop', tail: 'curl', role: 'hot', belly: 'hot', nose: 'hot', disc: 1, hooves: 1 },
  horse: { plan: 'quad', body: [0.54, 0.22], legs: 0.5, legw: 0.07, head: 0.19, snout: [0.3, 0.13], ears: 'pointy', tail: 'hair', role: 'accent', belly: 'accent', nose: 'bg', mane: 1, neck: 0.34, hooves: 1 },
  sheep: { plan: 'quad', body: [0.45, 0.27], legs: 0.27, legw: 0.055, head: 0.19, snout: [0.1, 0.1], ears: 'side', tail: 'stub', role: 'ink', belly: 'ink', nose: 'bg', wool: 1, face: 'bg', hooves: 1 },
  lion: { plan: 'quad', body: [0.5, 0.22], legs: 0.36, legw: 0.08, head: 0.25, snout: [0.12, 0.11], ears: 'round', tail: 'tuft', role: 'accent', belly: 'accent', nose: 'bg', lionmane: 'hot' },
  bird: { plan: 'bird', body: [0.36, 0.25], legs: 0.26, head: 0.2, role: 'cold', belly: 'ink', beak: 'accent' },
  fish: { plan: 'fish', body: [0.55, 0.32], head: 0.3, role: 'accent', belly: 'ink', fins: 'hot' },
  frog: { plan: 'frog', body: [0.42, 0.28], legs: 0.34, head: 0.3, role: 'cold', belly: 'ink', mouth: 'bg' },
  kid: { plan: 'biped', head: 0.31, body: [0.2, 0.25], legs: 0.34, role: 'hot', skin: 'ink', hair: 'accent', pants: 'cold', style: 'short' },
  adult: { plan: 'biped', head: 0.22, body: [0.2, 0.32], legs: 0.5, role: 'cold', skin: 'ink', hair: 'dim', pants: 'dim', style: 'long' },
};
export const PLANS = ['quad', 'bird', 'fish', 'frog', 'biped'];
export const ACTIONS = ['idle', 'walk', 'run', 'jump', 'point', 'cheer', 'sit', 'sniff', 'sleep', 'eat', 'fall', 'wave'];
export const EXPRS = ['neutral', 'happy', 'sad', 'angry', 'shock', 'sleepy', 'sniff', 'love'];
export const HAIRS = ['short', 'long', 'bun', 'curly', 'cap', 'bald'];
export const RIG_ALIASES = { puppy: 'dog', hound: 'dog', dachshund: 'dog', kitten: 'cat', kitty: 'cat', bunny: 'rabbit', hare: 'rabbit', rat: 'mouse', hamster: 'mouse', calf: 'cow', bull: 'cow', piglet: 'pig', pony: 'horse', lamb: 'sheep', cub: 'bear', toad: 'frog', goldfish: 'fish', chick: 'bird', pigeon: 'bird', child: 'kid', boy: 'kid', girl: 'kid', man: 'adult', woman: 'adult', person: 'adult', human: 'adult' };
const FACES = ['left', 'right'];
const DEF_EXPR = { sleep: 'sleepy', fall: 'shock', cheer: 'happy', sniff: 'sniff', eat: 'happy', jump: 'happy', run: 'neutral' };

/** "rig:dog:walk:happy" → {species, action, expr, face, bad:[token lạ]} (null nếu không phải tên rig). */
export function parseRig(name) {
  const s = String(name || '').trim().toLowerCase();
  if (!s.startsWith('rig:')) return null;
  const [raw, ...rest] = s.slice(4).split(':').map((x) => x.trim()).filter(Boolean);
  const species = SPECIES[raw] ? raw : RIG_ALIASES[raw] || null;
  const out = { species, raw, action: null, expr: null, face: null, bad: [] };
  for (const tok of rest) {
    if (ACTIONS.includes(tok)) out.action = tok;
    else if (EXPRS.includes(tok)) out.expr = tok;
    else if (FACES.includes(tok)) out.face = tok;
    else if (HAIRS.includes(tok)) out.hair = tok;
    else out.bad.push(tok);
  }
  return out;
}

// ---------- hình học: primitive trong toạ độ đơn vị ----------
const TAU = Math.PI * 2, PI = Math.PI;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const sm = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const E = (x, y, rx, ry, role, o = {}) => ({ k: 'circle', x, y, r: 1, rx, ry, rot: o.rot || 0, role, ...o });
const PG = (pts, role, o = {}) => ({ k: 'poly', pts, role, ...o });
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const pol = (p, r, a) => [p[0] + Math.cos(a) * r, p[1] + Math.sin(a) * r];
/** ống thuôn qua các điểm (bán kính ra → rb), hai đầu tròn → một poly kín (chân, đuôi, cổ, tay). */
function tube(pts, ra, rb = ra, role = 'ink', o = {}) {
  const n = pts.length, L = [], R = [];
  if (n < 2) return E(pts[0][0], pts[0][1], ra, ra, role, o);
  const rad = (i) => lerp(ra, rb, i / (n - 1));
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)], d = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const nx = -(b[1] - a[1]) / d, ny = (b[0] - a[0]) / d, r = rad(i);
    L.push([pts[i][0] + nx * r, pts[i][1] + ny * r]); R.push([pts[i][0] - nx * r, pts[i][1] - ny * r]);
  }
  const ang = (p, q) => Math.atan2(q[1] - p[1], q[0] - p[0]);
  const capE = [], capS = [], ae = ang(pts[n - 2], pts[n - 1]), as = ang(pts[1], pts[0]);
  for (let i = 1; i < 6; i++) { capE.push(pol(pts[n - 1], rb, ae + PI / 2 - i / 6 * PI)); capS.push(pol(pts[0], ra, as + PI / 2 - i / 6 * PI)); }
  return PG([...L, ...capE, ...R.reverse(), ...capS], role, o);
}
const seg2 = (a, l1, a1, l2, a2) => { const k = [a[0] + Math.sin(a1) * l1, a[1] + Math.cos(a1) * l1]; return [a, k, [k[0] + Math.sin(a2) * l2, k[1] + Math.cos(a2) * l2]]; };
/** đường cong bậc hai a→b với điểm điều khiển c (đuôi, tai cong). */
const curve = (a, c, b, n = 8) => Array.from({ length: n + 1 }, (_, i) => { const t = i / n, u = 1 - t; return [u * u * a[0] + 2 * u * t * c[0] + t * t * b[0], u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]]; });
const crescent = (cx, cy, rx, ry, a0, a1, th, role, o = {}) => {            // trăng khuyết mảnh (miệng cười, mí nhắm, lông mày cong)
  const n = 10, outP = [], inP = [];
  for (let i = 0; i <= n; i++) { const a = lerp(a0, a1, i / n), w = Math.sin(i / n * PI); outP.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); inP.push([cx + Math.cos(a) * (rx - th * w), cy + Math.sin(a) * (ry - th * w)]); }
  return PG([...outP, ...inP.reverse()], role, o);
};
const heartPts = (cx, cy, s) => Array.from({ length: 24 }, (_, i) => { const t = i / 24 * TAU; return [cx + s * 0.06 * 16 * Math.sin(t) ** 3, cy - s * 0.06 * (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t))]; });
const zee = (x, y, s, role, alpha) => PG([[x, y], [x + s, y], [x + s, y + s * 0.22], [x + s * 0.3, y + s * 0.78], [x + s, y + s * 0.78], [x + s, y + s], [x, y + s], [x, y + s * 0.78], [x + s * 0.7, y + s * 0.22], [x, y + s * 0.22]], role, { fine: true, alpha });

// ---------- biến đổi cả nhóm primitive (xoay/tịnh tiến/đối xứng) ----------
const rotAbout = (p, c, a) => { const s = Math.sin(a), co = Math.cos(a), x = p[0] - c[0], y = p[1] - c[1]; return [c[0] + x * co - y * s, c[1] + x * s + y * co]; };
function xform(prims, c, a, dx = 0, dy = 0) {
  if (!a && !dx && !dy) return prims;
  return prims.map((p) => {
    if (p.k === 'circle') { const q = rotAbout([p.x, p.y], c, a); return { ...p, x: q[0] + dx, y: q[1] + dy, rot: (p.rot || 0) + a }; }
    return { ...p, pts: p.pts.map((q) => { const r = rotAbout(q, c, a); return [r[0] + dx, r[1] + dy]; }) };
  });
}
const mirror = (prims) => prims.map((p) => (p.k === 'circle' ? { ...p, x: -p.x, rot: -(p.rot || 0) } : { ...p, pts: p.pts.map((q) => [-q[0], q[1]]) }));

// ---------- lõi nhiệt gắn thân (Grounded Thermal Glow, heat 0..1) ----------
function thermalCore(cx, cy, rx, ry, heat, breath = 0) {
  if (!(heat > 0.05)) return [];
  const k = clamp(heat, 0, 1), pulse = 1 + breath * 0.06;
  return [
    E(cx, cy, rx * 0.78 * pulse, ry * 0.72 * pulse, 'hot', { fine: true, alpha: k * 0.32 }),
    E(cx, cy, rx * 0.48 * pulse, ry * 0.46 * pulse, 'hot', { fine: true, alpha: k * 0.65 }),
  ];
}

// ---------- mặt: mắt (lòng trắng, con ngươi, đốm sáng), mí, lông mày, miệng — theo biểu cảm + chớp mắt ----------
// F = {eyes:[[x,y,r],…] (mắt gần trước), brow, mouth:[x,y,w], look:[dx,dy], skin (vai màu da quanh mắt)}
function face(F, X, blink, t, o = {}) {
  const out = [], [lx, ly] = F.look || [0.25, 0];
  const closed = blink >= 1 || X === 'sniff' || o.asleep, happyEye = X === 'happy' && !o.openHappy, half = X === 'sleepy' ? 0.55 : X === 'angry' ? 0.32 : blink > 0 ? 0.6 : 0;
  if (o.editorial) {                                   // chế độ người lớn tối giản (Vox/Fern/Kurzgesagt): không mắt tròn trắng googly + đốm sáng
    F.eyes.forEach(([x, y, r], i) => {
      const er = r * 0.44;
      if (closed) {
        out.push(tube([[x - er * 1.35, y], [x + er * 1.35, y]], er * 0.28, er * 0.28, 'bg', { fine: true }));
        return;
      }
      const px = x + lx * r * 0.22, py = y + ly * r * 0.18;
      out.push(E(px, py, er, er * (X === 'shock' ? 1.2 : 1.08), 'bg', { fine: true }));
      if (F.brow !== false && (X === 'angry' || X === 'sad' || X === 'shock')) {
        const inner = i === 0 ? -1 : 1, ang = { sad: -0.28, angry: 0.36, shock: -0.05 }[X] ?? 0;
        const dy = { shock: -0.42, sad: -0.05, angry: 0.1 }[X] ?? 0;
        const cy = y - r * 1.05 + dy * r * 1.4, w = r * 0.72, a = ang * inner * (F.browFlip ? -1 : 1);
        out.push(tube([[x - w, cy - Math.sin(a) * w * -inner], [x + w, cy + Math.sin(a) * w * -inner]], r * 0.11, r * 0.11, F.browRole || 'bg', { fine: true, alpha: 0.82 }));
      }
    });
    if (F.mouth) {
      const [mx, my, mw] = F.mouth;
      if (X === 'shock') out.push(E(mx, my + mw * 0.1, mw * 0.18, mw * 0.24, 'bg', { fine: true, alpha: 0.85 }));
      else if (X === 'sad' || X === 'angry') out.push(tube([[mx - mw * 0.32, my + mw * 0.08], [mx + mw * 0.32, my - (X === 'angry' ? mw * 0.04 : 0)]], mw * 0.065, mw * 0.065, 'bg', { fine: true, alpha: 0.8 }));
      else if (X === 'happy' || X === 'love') out.push(crescent(mx, my - mw * 0.12, mw * 0.36, mw * 0.22, 0.45, PI - 0.45, mw * 0.08, 'bg', { fine: true, alpha: 0.85 }));
      else out.push(tube([[mx - mw * 0.26, my], [mx + mw * 0.26, my]], mw * 0.055, mw * 0.055, 'bg', { fine: true, alpha: 0.72 }));
    }
    return out;
  }
  F.eyes.forEach(([x, y, r], i) => {
    const big = X === 'shock' ? 1.22 : 1;
    if (closed || happyEye) {                        // mắt nhắm (–) hoặc mắt cười (^)
      const up = happyEye ? -1 : 1;
      out.push(crescent(x, y + (happyEye ? r * 0.35 : 0), r * 1.05, r * 0.6, up > 0 ? 0.15 : PI + 0.15, up > 0 ? PI - 0.15 : TAU - 0.15, r * 0.32, 'bg', { fine: true }));
      if (X === 'sniff') out.push(crescent(x, y, r * 0.9, r * 0.5, PI + 0.4, TAU - 0.4, r * 0.25, 'bg', { fine: true }));
      return;
    }
    out.push(E(x, y, r * big, r * 1.12 * big, 'ink', { fine: true }));
    const pr = X === 'shock' ? r * 0.3 : r * 0.56, px = x + lx * r * 0.45, py = y + (X === 'sad' ? r * 0.3 : ly * r * 0.4);
    if (X === 'love') out.push(PG(heartPts(px, py - pr * 0.1, pr * 1.1), 'hot', { fine: true }));
    else { out.push(E(px, py, pr, pr * 1.08, 'bg', { fine: true })); out.push(E(px - pr * 0.35, py - pr * 0.4, pr * 0.32, pr * 0.32, 'ink', { fine: true })); }
    if (half > 0) {                                  // mí trên (màu da) kéo xuống: buồn ngủ, cáu, đang chớp
      const tilt = X === 'angry' ? (i === 0 ? -0.45 : 0.45) * (o.mir ? -1 : 1) : 0, top = y - r * 1.2 * big, cut = y - r * 1.12 * big + half * 2.24 * r * big;
      out.push(PG(xform([PG([[x - r * 1.4, top - r * 0.3], [x + r * 1.4, top - r * 0.3], [x + r * 1.4, cut], [x - r * 1.4, cut]], F.skin)], [x, cut], tilt)[0].pts, F.skin, { fine: true }));
    }
  });
  // lông mày: góc theo biểu cảm (vui nhướng, buồn chụm trong lên, cáu chụm trong xuống, sốc nhướng cao)
  if (F.brow !== false) F.eyes.forEach(([x, y, r], i) => {
    const inner = i === 0 ? -1 : 1, ang = { sad: -0.35, angry: 0.45, shock: -0.05, happy: -0.12, love: -0.12 }[X] ?? 0;
    const dy = { shock: -0.55, happy: -0.18, sad: -0.05, angry: 0.12, sleepy: 0.2 }[X] ?? 0;
    const cy = y - r * 1.65 + dy * r * 2, w = r * 1.05, a = ang * inner * (F.browFlip ? -1 : 1);
    const ends = [[x - w, cy - Math.sin(a) * w * -inner], [x + w, cy + Math.sin(a) * w * -inner]];
    out.push(tube(ends, r * 0.17, r * 0.17, F.browRole || 'bg', { fine: true }));
  });
  if (F.mouth) {
    const [mx, my, mw] = F.mouth, chew = o.chew ? (Math.sin(t * TAU * 2.6) > 0 ? 1 : 0.35) : 0;
    if (X === 'shock' || chew) out.push(E(mx, my + mw * 0.15, mw * 0.32, mw * (0.42 * (chew || 1)), 'bg', { fine: true }));
    else if (X === 'happy' || X === 'love' || X === 'sniff') {
      out.push(PG([...Array.from({ length: 9 }, (_, i) => { const a = i / 8 * PI; return [mx + Math.cos(a) * mw * 0.55, my + Math.sin(a) * mw * 0.5]; }), [mx - mw * 0.55, my]], 'bg', { fine: true }));
      if (!F.noTongue) out.push(E(mx + mw * 0.08, my + mw * 0.3, mw * 0.25, mw * 0.15, 'hot', { fine: true }));
    } else if (X === 'sad') out.push(crescent(mx, my + mw * 0.45, mw * 0.5, mw * 0.4, PI + 0.4, TAU - 0.4, mw * 0.14, 'bg', { fine: true }));
    else if (X === 'angry') out.push(tube([[mx - mw * 0.45, my + mw * 0.12], [mx + mw * 0.45, my - mw * 0.04]], mw * 0.09, mw * 0.09, 'bg', { fine: true }));
    else out.push(crescent(mx, my - mw * 0.15, mw * 0.42, mw * 0.32, 0.5, PI - 0.5, mw * 0.11, 'bg', { fine: true }));
    if (X === 'sad' && F.eyes[0]) { const [x, y, r] = F.eyes[0]; const ty = y + r * 1.6 + ((t * 1.2) % 1) * r * 2; out.push(PG([[x + r * 0.3, ty - r * 0.7], ...Array.from({ length: 9 }, (_, i) => { const a = -0.3 + i / 8 * (PI + 0.6); return [x + r * 0.3 + Math.cos(a) * r * 0.35, ty + Math.sin(a) * r * 0.35]; })], 'cold', { fine: true })); }
  }
  if (X === 'love' || X === 'happy' || o.blush) F.eyes.slice(0, 1).forEach(([x, y, r]) => out.push(E(x - r * 0.2, y + r * 1.65, r * 0.75, r * 0.42, 'hot', { fine: true, alpha: 0.55 })));
  return out;
}

// ---------- chu kỳ hành động chung ----------
function motion(action, t, ph) {                       // → các pha/biên độ dùng cho mọi bộ xương
  const w = (hz) => (t * hz + ph) % 1;
  return {
    breath: Math.sin((t * 0.32 + ph) * TAU), walk: w(1.45), run: w(2.5), hop: w(1.9), jump: w(0.85), wag: Math.sin((t * (action === 'run' ? 3.4 : 2.6) + ph) * TAU),
    twitch: Math.sin((t * 7 + ph) * TAU), cheer: w(1.8), wave: Math.sin((t * 2.2 + ph) * TAU), sleepZ: w(0.45),
  };
}
const jumpY = (u) => (u < 0.18 ? sm(u / 0.18) * 0.05 : u < 0.78 ? -Math.sin((u - 0.18) / 0.6 * PI) * 0.55 : (1 - sm((u - 0.78) / 0.22)) * 0.04);
const fallK = (t) => clamp(t / 0.75);                 // ngã: 0 → 1 trong 0.75 s rồi nằm ngửa giãy chân

// ================= bộ xương bốn chân =================
function quad(S, A, X, t, ph, body, blink, opt = {}) {
  const m = motion(A, t, ph), out = [], ground = 0.9, ed = !!opt.editorial, edHorse = ed && opt.species === 'horse';
  const [L, Hh] = edHorse ? [0.57, 0.2] : S.body, legL = edHorse ? 0.54 : S.legs, lw = edHorse ? 0.058 : S.legw, hr = edHorse ? 0.155 : S.head, belly = S.belly || body;
  let dy = 0, pitch = 0, headDrop = 0, headRot = 0, tailBase = -0.5, tailAmp = 0.25, earSwing = 0, lie = 0, whole = 0;
  const legs = [                                     // [x hông/vai theo thân, trước?, xa?, pha]
    { x: 0.62, front: 1, far: 1, ph: 0.5 }, { x: -0.6, front: 0, far: 1, ph: 0 },
    { x: 0.62, front: 1, far: 0, ph: 0 }, { x: -0.6, front: 0, far: 0, ph: 0.5 },
  ].map((l) => ({ ...l, th: l.front ? 0.06 : -0.06, kn: 0 }));
  const cyc = (u, amp, lift) => legs.forEach((l) => { const a = (u + l.ph) * TAU; l.th = amp * Math.sin(a) + (l.front ? 0.04 : -0.04); l.kn = lift * Math.max(0, Math.cos(a)); });
  const bre = m.breath * 0.012;
  if (S.hop && (A === 'walk' || A === 'run')) {    // thỏ: nhảy cóc — hai chân sau đạp cùng lúc, thân vồng
    const u = A === 'run' ? m.run : m.hop, air = Math.max(0, Math.sin(u * TAU)), hgt = A === 'run' ? 0.2 : 0.11;
    dy = -air * hgt; pitch = -Math.cos(u * TAU) * 0.12;
    legs.forEach((l) => { l.th = l.front ? 0.15 + 0.5 * air : -0.25 - 0.75 * air; l.kn = l.front ? 0.2 : 0.9 * (1 - air); });
    earSwing = -0.5 * air; tailAmp = 0.05;
  } else if (A === 'walk') { cyc(m.walk, 0.42, 0.75); dy = Math.sin(m.walk * TAU * 2) * 0.014; tailAmp = 0.35; headDrop = Math.sin(m.walk * TAU * 2 - 0.8) * 0.012; }
  else if (A === 'run') {
    const u = m.run; legs.forEach((l) => { l.ph = l.front ? (l.far ? 0.1 : 0) : (l.far ? 0.6 : 0.5); }); cyc(u, 0.85, 1.1);
    pitch = Math.sin(u * TAU) * 0.1; dy = -Math.abs(Math.sin(u * TAU)) * 0.06; earSwing = -0.6; tailBase = -0.1; tailAmp = 0.12;
  } else if (A === 'jump' || A === 'cheer') {
    const u = A === 'jump' ? m.jump : m.cheer, air = A === 'jump' ? jumpY(u) : -Math.abs(Math.sin(u * PI)) * 0.14;
    dy = air; const up = clamp(-air / 0.4);
    legs.forEach((l) => { l.th = l.front ? 0.2 + 0.6 * up : -0.2 - 0.7 * up; l.kn = A === 'jump' && u < 0.2 ? 0.9 : 0.25; });
    pitch = A === 'jump' ? -0.25 * up : 0; tailAmp = 0.5; earSwing = -0.4 * up;
    if (A === 'cheer') { legs[2].th = 0.9 + 0.4 * Math.sin(u * TAU * 2); legs[2].kn = 1.3; }
  } else if (A === 'sit') {
    pitch = -0.42; dy = legL * 0.28;
    legs.forEach((l) => { if (!l.front) { l.th = 1.25; l.kn = 2.5; } else { l.th = 0.42; l.kn = 0; } });
    tailBase = 0.9; tailAmp = 0.12;
  } else if (A === 'sniff' || A === 'eat') {
    headDrop = 0.22 + (A === 'eat' ? 0.06 : 0); headRot = 0.55; tailAmp = A === 'sniff' ? 0.45 : 0.25; earSwing = 0.25;
    if (A === 'sniff') { legs[2].th = 0.18 + 0.08 * Math.sin(t * TAU * 0.7); }
  } else if (A === 'sleep') {
    lie = 1; dy = legL * 0.92 - Hh * 0.05 + m.breath * 0.006; headDrop = 0.1; headRot = 0.18; tailBase = 0.4; tailAmp = 0.02;
    legs.forEach((l) => { l.th = l.front ? 1.45 : -1.45; l.kn = 0; });
  } else if (A === 'fall') {
    const k = fallK(t); whole = PI * sm(k); dy = -Math.sin(k * PI) * 0.25 + sm(k) * (legL * 0.35);
    legs.forEach((l, i) => { l.th = (l.front ? 0.5 : -0.5) + (k >= 1 ? Math.sin(t * TAU * 3 + i * 1.7) * 0.4 : 0); l.kn = 0.3; });
  } else if (A === 'point' || A === 'wave') {
    legs[2].th = A === 'wave' ? 1.0 + 0.45 * m.wave : 1.05; legs[2].kn = A === 'wave' ? 0.6 : 1.5; tailBase = -0.95; tailAmp = A === 'point' ? 0.02 : 0.3; headDrop = -0.03;
  } else { tailAmp = 0.22; headDrop = Math.sin(m.breath * PI) * 0.01; }
  const bx = -0.04, by = ground - legL - Hh * 0.5 + dy;
  const piv = [bx, by];
  // ---- chân xa (tối hơn) ----
  const legPrims = (far) => legs.filter((l) => !!l.far === far).map((l) => {
    const hip = rotAbout([bx + l.x * L, by + Hh * 0.35], piv, pitch), u1 = legL * 0.54, u2 = legL * 0.54;
    const dir = l.front ? -1 : 1, pts = seg2(hip, u1, l.th, u2, l.th + dir * l.kn * (lie ? 0 : 1));
    const leg = tube(pts, lw * (S.heavy ? 1.2 : 1.05), lw * 0.85, l.far ? body : body, { tone: far ? 0.32 : 0 });
    const foot = pts[2], paw = S.hooves ? E(foot[0] + 0.01, foot[1] + lw * 0.2, lw * 1.0, lw * 0.6, 'bg', { tone: 0 }) : E(foot[0] + 0.02, foot[1] + lw * 0.15, lw * 1.15, lw * 0.75, far ? body : belly, { tone: far ? 0.32 : 0 });
    return [leg, paw, { ...E(hip[0], hip[1], 0.025, 0.025, 'ink'), pin: true, fine: true }];
  }).flat();
  let P = [...legPrims(true)];
  // ---- đuôi (trễ pha so với thân: follow-through) ----
  const rump = rotAbout([bx - L * 0.92, by - Hh * 0.25], piv, pitch), wag = m.wag * tailAmp;
  const tA = tailBase + wag, tl = { wag: 0.34, long: 0.5, bushy: 0.42, stub: 0.08, puff: 0.07, thin: 0.55, tuft: 0.42, curl: 0.16, hair: 0.45 }[S.tail] || 0.3;
  const tip = [rump[0] - Math.cos(tA) * tl, rump[1] + Math.sin(tA) * tl], ctl = [rump[0] - Math.cos(tA - 0.6) * tl * 0.6, rump[1] + Math.sin(tA - 0.6 - wag * 0.8) * tl * 0.6];
  if (S.tail === 'bushy') { P.push(tube(curve(rump, ctl, tip), 0.05, 0.11, body)); P.push(E(tip[0] - 0.02, tip[1], 0.1, 0.075, 'ink', { rot: -tA })); }
  else if (S.tail === 'puff' || S.tail === 'stub') P.push(E(rump[0] - 0.03, rump[1] + 0.02, S.tail === 'puff' ? 0.09 : 0.07, S.tail === 'puff' ? 0.09 : 0.06, S.tail === 'puff' ? 'ink' : body));
  else if (S.tail === 'curl') P.push(tube(Array.from({ length: 12 }, (_, i) => pol([rump[0] - 0.08, rump[1] - 0.04], 0.07 - i * 0.004, i / 11 * TAU * 1.1 + m.wag * 0.4)), 0.025, 0.018, body));
  else if (S.tail === 'hair') { P.push(tube(curve(rump, [rump[0] - 0.22, rump[1] + 0.05], [tip[0] - 0.05, Math.max(tip[1], rump[1] + 0.35)]), 0.06, 0.035, 'dim')); }
  else { P.push(tube(curve(rump, ctl, tip), S.tail === 'thin' ? 0.018 : 0.04, S.tail === 'thin' ? 0.01 : 0.028, body)); if (S.tail === 'tuft') P.push(E(tip[0], tip[1], 0.055, 0.075, 'bg', { rot: -tA })); }
  // ---- thân ----
  const torso = [E(bx, by, L, Hh * (1 + bre), body)];
  if (belly !== body) torso.push(E(bx + L * 0.1, by + Hh * 0.38, L * 0.72, Hh * 0.5, belly));
  if (S.spots) torso.push(E(bx - L * 0.35, by - Hh * 0.2, L * 0.24, Hh * 0.42, S.spots, { rot: 0.4 }), E(bx + L * 0.3, by - Hh * 0.35, L * 0.18, Hh * 0.3, S.spots, { rot: -0.3 }));
  if (S.wool) for (let i = 0; i < 7; i++) torso.push(E(bx - L * 0.8 + i * L * 0.27, by - Hh * (0.75 - (i % 2) * 0.12), Hh * 0.42, Hh * 0.36, 'ink'));
  if (opt.heat > 0.05) torso.push(...thermalCore(bx + L * 0.12, by, L * 0.68, Hh * 0.86, opt.heat, m.breath));
  P.push(...xform(torso, piv, pitch));
  P.push(...legPrims(false));
  // ---- cổ + đầu ----
  const neckL = edHorse ? 0.4 : (S.neck || 0.1), sh = rotAbout([bx + L * 0.78, by - Hh * 0.45], piv, pitch);
  let hc = [sh[0] + 0.06 + (S.neck ? neckL * 0.45 : 0), sh[1] - hr * 0.55 - neckL * 0.75 + headDrop * 1.6];
  if (headRot > 0) hc = [hc[0] + headRot * hr * 0.75, hc[1] + headRot * hr * 1.5 + legL * headRot * 0.55];
  if (lie) hc = [bx + L * 0.95, ground - hr * 0.95];
  P.push(tube([[sh[0] - 0.05, sh[1] + 0.06], [hc[0] - hr * 0.25, hc[1] + hr * 0.2]], edHorse ? 0.088 : S.neck ? 0.1 : lw * 1.6, edHorse ? 0.068 : S.neck ? 0.085 : lw * 1.4, body));
  if (S.mane) for (let i = 0; i < 5; i++) { const q = [lerp(sh[0] - 0.08, hc[0] - hr * 0.5, i / 4), lerp(sh[1] - 0.04, hc[1] - hr * 0.6, i / 4)]; P.push(E(q[0] - 0.03, q[1], 0.07, 0.05, 'dim', { rot: -0.9 + Math.sin(t * 3 + i) * 0.08 })); }
  if (S.lionmane) for (let i = 0; i < 12; i++) { const a = i / 12 * TAU + Math.sin(t * 2 + i) * 0.03; P.push(E(hc[0] + Math.cos(a) * hr * 1.0, hc[1] + Math.sin(a) * hr * 1.0, hr * 0.42, hr * 0.3, S.lionmane, { rot: a })); }
  const head = [], hdTilt = headRot * 0.6 + (A === 'idle' ? Math.sin(t * 0.9 + ph * 7) * 0.05 : 0) + (lie ? 0.15 : 0);
  // tai sau (trễ pha theo đầu)
  const ear = (far) => {
    const sw = earSwing + Math.sin(t * TAU * 1.3 - 0.9 + ph * 5) * 0.07, base = [hc[0] - hr * (far ? 0.05 : 0.38), hc[1] - hr * 0.72], role = far ? body : body;
    const o = { tone: far ? 0.3 : 0 };
    switch (S.ears) {
      case 'floppy': return [tube(curve(base, [base[0] - hr * 0.5, base[1] + hr * 0.1], [base[0] - hr * 0.55 + sw * 0.2, base[1] + hr * 1.05]), hr * 0.18, hr * 0.32, 'dim', o)];
      case 'pointy': case 'tall': { const h = S.ears === 'tall' ? 0.85 : 0.6; return [PG([[base[0] - hr * 0.28, base[1] + hr * 0.2], rotAbout([base[0] - hr * 0.1, base[1] - hr * h], base, sw * 0.5), [base[0] + hr * 0.3, base[1] + hr * 0.15]], role, o), ...(far ? [] : [PG([[base[0] - hr * 0.13, base[1] + hr * 0.1], rotAbout([base[0] - hr * 0.08, base[1] - hr * h * 0.6], base, sw * 0.5), [base[0] + hr * 0.14, base[1] + hr * 0.08]], 'hot', { fine: true })])]; }
      case 'long': { const tipE = rotAbout([base[0] - hr * 0.2, base[1] - hr * 1.6], base, -0.15 + sw * 0.6); return [tube(curve(base, [base[0] - hr * 0.05, base[1] - hr * 0.8], tipE), hr * 0.17, hr * 0.2, role, o), ...(far ? [] : [tube(curve(base, [base[0] - hr * 0.05, base[1] - hr * 0.8], tipE), hr * 0.07, hr * 0.09, 'hot', { fine: true })])]; }
      case 'round': case 'big': { const r = hr * (S.ears === 'big' ? 0.5 : 0.3); return [E(base[0], base[1] + r * 0.2, r, r, role, o), ...(far ? [] : [E(base[0], base[1] + r * 0.25, r * 0.55, r * 0.55, 'hot', { fine: true })])]; }
      case 'side': return [E(base[0] - hr * 0.35, base[1] + hr * 0.45, hr * 0.32, hr * 0.13, role, { ...o, rot: 0.35 + sw * 0.3 })];
      case 'flop': return [PG([[base[0] - hr * 0.3, base[1] + hr * 0.15], [base[0] + hr * 0.15, base[1] - hr * 0.35], [base[0] + hr * 0.45 + sw * 0.1, base[1] + hr * 0.3]], role, o)];
      default: return [];
    }
  };
  head.push(...ear(true));
  if (S.horns) head.push(tube(curve([hc[0] - hr * 0.2, hc[1] - hr * 0.85], [hc[0] - hr * 0.1, hc[1] - hr * 1.3], [hc[0] + hr * 0.25, hc[1] - hr * 1.35]), hr * 0.1, hr * 0.05, 'ink'));
  head.push(E(hc[0], hc[1], hr * (S.ears === 'side' ? 0.92 : 1), hr * 0.92, S.face || body));
  const sn = S.snout, snc = [hc[0] + hr * 0.72 + sn[0] * 0.5, hc[1] + hr * 0.28];
  if (S.disc) head.push(E(hc[0] + hr * 0.95, hc[1] + hr * 0.2, sn[0] * 0.9, sn[1] * 1.05, 'hot', { tone: 0.18 }), E(hc[0] + hr * 1.05, hc[1] + hr * 0.12, 0.018, 0.03, 'bg', { fine: true }), E(hc[0] + hr * 1.05, hc[1] + hr * 0.3, 0.018, 0.03, 'bg', { fine: true }));
  else {
    head.push(E(snc[0], snc[1], hr * 0.35 + sn[0] * 0.55, sn[1] + hr * 0.12, S.muzzle || (S.face ? S.face : belly === 'ink' ? 'ink' : body)));
    const nose = [snc[0] + hr * 0.3 + sn[0] * 0.5 + (A === 'sniff' ? m.twitch * 0.008 : 0), snc[1] - sn[1] * 0.55];
    head.push(E(nose[0], nose[1], hr * 0.14, hr * 0.1, S.nose || 'bg', { fine: true }));
  }
  head.push(...ear(false));
  const fc = face({ eyes: [[hc[0] + hr * 0.44, hc[1] - hr * 0.2, hr * 0.25], [hc[0] - hr * 0.04, hc[1] - hr * 0.24, hr * 0.21]], mouth: S.disc ? [hc[0] + hr * 0.55, hc[1] + hr * 0.6, hr * 0.42] : [snc[0] + sn[0] * 0.1, snc[1] + sn[1] * 0.55, hr * 0.42], skin: S.face || body, look: [0.4, headRot > 0 ? 0.6 : 0] }, X, blink, t, { asleep: A === 'sleep', chew: A === 'eat', editorial: ed });
  head.push(...fc);
  if (S.whiskers) for (const s of [-1, 1]) head.push(tube([[snc[0] + 0.02, snc[1] + s * 0.01], [snc[0] + 0.24, snc[1] - 0.02 + s * 0.05]], 0.005, 0.003, 'ink', { fine: true }));
  P.push(...xform(head, [hc[0] - hr * 0.3, hc[1] + hr * 0.5], hdTilt));
  if (A === 'sleep') for (let i = 0; i < 3; i++) { const u = (m.sleepZ + i / 3) % 1; P.push(zee(hc[0] + 0.1 + u * 0.25, hc[1] - hr - 0.1 - u * 0.5, 0.06 + u * 0.05, 'ink', 1 - u)); }
  return whole ? xform(P, [bx, by], whole) : P;
}

// ================= chim =================
function bird(S, A, X, t, ph, body, blink, opt = {}) {
  const m = motion(A, t, ph), out = [], [L, Hh] = S.body, hr = S.head, ground = 0.9;
  let dy = 0, flap = Math.sin(t * TAU * 0.6 + ph * 5) * 0.15, peck = 0, legK = 1, whole = 0, tilt = 0;
  if (A === 'walk' || A === 'run') { const u = A === 'run' ? m.run : m.hop; dy = -Math.abs(Math.sin(u * PI)) * (A === 'run' ? 0.12 : 0.06); }
  else if (A === 'jump' || A === 'cheer') { const u = A === 'jump' ? m.jump : m.cheer; dy = A === 'jump' ? jumpY(u) * 1.2 - 0.05 : -0.08 - Math.abs(Math.sin(u * TAU)) * 0.08; flap = Math.sin(t * TAU * 5) * 1.0; legK = 0.4; }
  else if (A === 'sniff' || A === 'eat') { peck = Math.max(0, Math.sin((t * 2.2 + ph) * TAU)); tilt = 0.5 * peck; }
  else if (A === 'sit' || A === 'sleep') { dy = S.legs * 0.75; legK = 0.15; }
  else if (A === 'fall') { const k = fallK(t); whole = PI * 0.9 * sm(k); dy = sm(k) * 0.2 - Math.sin(k * PI) * 0.2; flap = Math.sin(t * TAU * 6) * 0.8 * (1 - k); }
  else if (A === 'point' || A === 'wave') flap = A === 'wave' ? 0.9 + Math.sin(t * TAU * 2.2) * 0.5 : 1.2;
  const bx = -0.08, by = ground - S.legs * legK - Hh * 0.7 + dy + Math.sin(m.breath * PI) * 0.006;
  const P = [];
  for (const s of [1, 0]) {                        // chân mảnh
    const hip = [bx + (s ? 0.06 : -0.06), by + Hh * 0.6], foot = [hip[0] + 0.02, hip[1] + S.legs * legK];
    P.push(tube([hip, foot], 0.022, 0.018, 'accent', { tone: s ? 0.3 : 0 }), tube([foot, [foot[0] + 0.09, foot[1]]], 0.016, 0.014, 'accent', { tone: s ? 0.3 : 0 }));
  }
  P.push(PG([[bx - L * 0.8, by - Hh * 0.1], [bx - L * 1.45, by - Hh * 0.55 + Math.sin(t * 3) * 0.02], [bx - L * 1.5, by + Hh * 0.15], [bx - L * 0.7, by + Hh * 0.3]], body, { tone: 0.15 }));
  P.push(E(bx, by, L, Hh, body, { rot: -0.12 }), E(bx + L * 0.2, by + Hh * 0.35, L * 0.6, Hh * 0.55, S.belly, { rot: -0.1 }));
  if (opt.heat > 0.05) P.push(...thermalCore(bx, by, L * 0.72, Hh * 0.78, opt.heat, m.breath));
  const wingBase = [bx + L * 0.05, by - Hh * 0.15];
  P.push(...xform([E(wingBase[0] - L * 0.35, wingBase[1] + Hh * 0.1, L * 0.62, Hh * 0.48, body, { tone: 0.22, rot: 0.25 })], wingBase, -flap));
  const hc0 = [bx + L * 0.85, by - Hh * 0.95], hp = [hc0[0] + peck * 0.18, hc0[1] + peck * 0.42];
  const head = [E(hp[0], hp[1], hr, hr, body),
    PG([[hp[0] + hr * 0.82, hp[1] - hr * 0.22], [hp[0] + hr * 1.75, hp[1] + hr * 0.05], [hp[0] + hr * 0.82, hp[1] + hr * 0.3]], S.beak || 'accent'),
    ...face({ eyes: [[hp[0] + hr * 0.38, hp[1] - hr * 0.2, hr * 0.3], [hp[0] - hr * 0.12, hp[1] - hr * 0.25, hr * 0.24]], brow: X === 'neutral' ? false : true, mouth: null, skin: body }, X, blink, t, { asleep: A === 'sleep', editorial: !!opt.editorial })];
  P.push(...xform(head, hp, tilt));
  if (A === 'sleep') for (let i = 0; i < 3; i++) { const u = (m.sleepZ + i / 3) % 1; P.push(zee(hp[0] + 0.1 + u * 0.25, hp[1] - hr - 0.1 - u * 0.5, 0.06 + u * 0.05, 'ink', 1 - u)); }
  return whole ? xform(P, [bx, by], whole) : P;
}

// ================= cá =================
function fish(S, A, X, t, ph, body, blink, opt = {}) {
  const m = motion(A, t, ph), [L, Hh] = S.body, hr = S.head;
  const hz = { run: 3.2, walk: 1.8, cheer: 3.6, jump: 2.4 }[A] || 0.9, amp = { run: 0.35, cheer: 0.45 }[A] || 0.22;
  let dy = Math.sin(t * TAU * 0.5 + ph * 4) * 0.03, whole = Math.sin(t * TAU * 0.5 + ph) * 0.04;
  if (A === 'jump') { const u = m.jump; dy = jumpY(u) * 1.1; whole = -0.6 * Math.cos(u * PI) * (u > 0.15 && u < 0.85 ? 1 : 0); }
  if (A === 'fall') whole = PI * sm(fallK(t));
  if (A === 'sleep' || A === 'sit') dy += 0.05;
  const bx = 0.05, by = 0.15 + dy, beat = Math.sin((t * hz + ph) * TAU) * amp;
  const P = [];
  const tailBase = [bx - L * 0.85, by];
  P.push(...xform([PG([[tailBase[0] + 0.05, by], [tailBase[0] - 0.4, by - 0.32], [tailBase[0] - 0.3, by], [tailBase[0] - 0.4, by + 0.32]], S.fins || body)], tailBase, beat));
  P.push(PG([[bx - L * 0.3, by - Hh * 0.85], [bx + L * 0.1, by - Hh * 1.45 + beat * 0.05], [bx + L * 0.35, by - Hh * 0.85]], S.fins || body, { tone: 0.15 }));
  P.push(E(bx, by, L, Hh, body), E(bx + L * 0.1, by + Hh * 0.45, L * 0.7, Hh * 0.42, S.belly));
  if (opt.heat > 0.05) P.push(...thermalCore(bx, by, L * 0.65, Hh * 0.78, opt.heat, m.breath));
  for (let i = 0; i < 3; i++) P.push({ ...E(bx - L * 0.25 + i * 0.13, by - Hh * 0.05, 0.07, Hh * 0.55, 'bg', { alpha: 0.18 }), fine: true });
  P.push(...xform([E(bx + L * 0.15, by + Hh * 0.3, 0.14, 0.06, S.fins || body, { rot: 0.5 })], [bx + L * 0.25, by + Hh * 0.2], Math.sin(t * TAU * 2) * 0.4));
  const ex = bx + L * 0.55, ey = by - Hh * 0.2;
  P.push(...face({ eyes: [[ex, ey, hr * 0.32]], brow: X !== 'neutral', mouth: [bx + L * 0.88, by + Hh * 0.25, hr * 0.38], skin: body, noTongue: true, look: [0.5, 0] }, X, blink, t, { asleep: A === 'sleep', chew: A === 'eat', editorial: !!opt.editorial }));
  if (A === 'eat' || A === 'sleep' || A === 'idle') for (let i = 0; i < 3; i++) { const u = ((t * 0.6 + ph + i / 3) % 1); P.push(E(bx + L * 1.0 + Math.sin(u * 9 + i) * 0.05, by - u * 0.9, 0.03 + u * 0.03, 0.03 + u * 0.03, 'ink', { fine: true, alpha: 1 - u, fill: false })); }
  return whole ? xform(P, [bx, by], whole) : P;
}

// ================= ếch =================
function frog(S, A, X, t, ph, body, blink, opt = {}) {
  const m = motion(A, t, ph), [L, Hh] = S.body, hr = S.head, ground = 0.9;
  let dy = 0, ext = 0, whole = 0, tongue = 0, armUp = 0, throat = (Math.sin(t * TAU * 1.6) + 1) * 0.5;
  if (A === 'walk' || A === 'run' || A === 'jump' || A === 'cheer') {
    const u = A === 'jump' ? m.jump : A === 'run' ? m.run : A === 'cheer' ? m.cheer : m.hop, hgt = A === 'jump' ? 1 : A === 'run' ? 0.5 : 0.25;
    dy = jumpY(u) * hgt; ext = clamp(-dy / (0.55 * hgt) * 1.4); if (A === 'cheer') armUp = 1;
  } else if (A === 'eat') tongue = Math.max(0, Math.sin((t * 1.4 + ph) * TAU));
  else if (A === 'fall') { whole = PI * sm(fallK(t)); }
  else if (A === 'point' || A === 'wave') armUp = A === 'wave' ? 0.6 + 0.4 * m.wave : 0.7;
  const bx = 0, by = ground - Hh * 0.8 + dy, P = [];
  for (const far of [1, 0]) {                      // chân sau gập/duỗi
    const hip = [bx - L * 0.55, by + Hh * 0.3], o = { tone: far ? 0.3 : 0 };
    const pts = ext > 0 ? [hip, [hip[0] - 0.25 * ext - 0.05, hip[1] + 0.12], [hip[0] - 0.48 * ext - 0.08, hip[1] + 0.25]] : [hip, [hip[0] + 0.28, hip[1] + 0.02], [hip[0] + 0.12, hip[1] + Hh * 0.75]];
    P.push(tube(pts, 0.085, 0.06, body, o), E(pts[2][0] + 0.05, pts[2][1] + 0.03, 0.11, 0.045, body, o));
  }
  P.push(E(bx, by, L, Hh * (1 + Math.sin(m.breath * PI) * 0.02), body, { rot: -0.15 }), E(bx + L * 0.15, by + Hh * 0.45, L * 0.62, Hh * 0.45, S.belly, { rot: -0.1 }));
  if (opt.heat > 0.05) P.push(...thermalCore(bx, by, L * 0.72, Hh * 0.78, opt.heat, m.breath));
  P.push(E(bx + L * 0.55, by + Hh * 0.62, 0.16 * (0.75 + throat * 0.25), 0.1 * (0.7 + throat * 0.3), S.belly, { tone: 0.12 }));
  for (const far of [1, 0]) {                      // tay trước
    const sh = [bx + L * 0.5 + (far ? -0.08 : 0), by + Hh * 0.3], hand = armUp && !far ? [sh[0] + 0.25, sh[1] - 0.35 * armUp] : [sh[0] + 0.08, ground - 0.02];
    P.push(tube([sh, hand], 0.05, 0.04, body, { tone: far ? 0.3 : 0 }), E(hand[0] + 0.03, hand[1], 0.07, 0.03, body, { tone: far ? 0.3 : 0 }));
  }
  const ey = by - Hh * 0.85;
  for (const [x, r] of [[bx + L * 0.12, 0.13], [bx + L * 0.62, 0.15]]) P.push(E(x, ey, r, r, body));
  P.push(...face({ eyes: [[bx + L * 0.62, ey, 0.1], [bx + L * 0.12, ey, 0.085]], mouth: null, skin: body, brow: X !== 'neutral', look: [0.3, 0] }, X, blink, t, { asleep: A === 'sleep', editorial: !!opt.editorial }));
  const mx = bx + L * 0.6, my = by - Hh * 0.05;
  P.push(crescent(mx - 0.05, my - 0.08, 0.28, 0.12, 0.25, PI - 0.6, 0.035, 'bg', { fine: true }));
  if (tongue > 0.02) P.push(tube([[mx + 0.15, my], [mx + 0.15 + tongue * 0.55, my - tongue * 0.12]], 0.03, 0.035, 'hot', { fine: true }));
  if (A === 'sleep') for (let i = 0; i < 3; i++) { const u = (m.sleepZ + i / 3) % 1; P.push(zee(bx + 0.4 + u * 0.25, ey - 0.15 - u * 0.5, 0.06 + u * 0.05, 'ink', 1 - u)); }
  return whole ? xform(P, [bx, by], whole) : P;
}

// ================= người (kid/adult) =================
function biped(S, A, X, t, ph, body, blink, opt = {}) {
  const m = motion(A, t, ph), ed = !!opt.editorial, edAdult = ed && opt.species === 'adult';
  const hr = edAdult ? 0.18 : (ed ? S.head * 0.9 : S.head);
  const legL = edAdult ? 0.54 : S.legs, [tw, th] = edAdult ? [0.175, 0.335] : S.body, ground = 0.9, skin = opt.skin || S.skin, pants = opt.pants || S.pants;
  const hair = opt.hairRole || S.hair, style = opt.hair || (edAdult ? 'short' : S.style);
  let dy = 0, lean = 0, whole = 0, legA = [0.04, -0.04], kn = [0, 0], armA = [0.12, -0.12], elb = [0.1, 0.1], headTilt = Math.sin(t * 0.8 + ph * 9) * 0.04, sit = 0, lie = 0;
  if (A === 'walk' || A === 'run') {
    const u = A === 'run' ? m.run : m.walk, amp = A === 'run' ? 0.75 : 0.38, a = u * TAU;
    legA = [amp * Math.sin(a), -amp * Math.sin(a)]; kn = [Math.max(0, Math.cos(a)) * (A === 'run' ? 1.3 : 0.6), Math.max(0, -Math.cos(a)) * (A === 'run' ? 1.3 : 0.6)];
    armA = [-amp * 0.9 * Math.sin(a), amp * 0.9 * Math.sin(a)]; elb = A === 'run' ? [1.3, 1.3] : [0.25, 0.25];
    dy = -Math.abs(Math.sin(a)) * (A === 'run' ? 0.06 : 0.02); lean = A === 'run' ? 0.2 : 0.04;
  } else if (A === 'jump' || A === 'cheer') {
    const u = A === 'jump' ? m.jump : m.cheer; dy = A === 'jump' ? jumpY(u) : -Math.abs(Math.sin(u * PI)) * 0.12; const up = clamp(-dy / 0.4);
    kn = [0.4 + up * 0.8, 0.4 + up * 0.8]; legA = [0.25 * up, -0.1 * up];
    armA = A === 'cheer' ? [2.45 + Math.sin(u * TAU * 2) * 0.25, -2.45 - Math.sin(u * TAU * 2 + 1) * 0.25] : [PI * 0.8 * up + 0.2, -PI * 0.8 * up - 0.2]; elb = [0.1, 0.1];
  } else if (A === 'point') { armA = [1.45, -0.15]; elb = [0, 0.15]; headTilt = 0.05; lean = 0.03; }
  else if (A === 'wave') { armA = [PI - 0.4 + m.wave * 0.35, -0.12]; elb = [0.35 + m.wave * 0.25, 0.1]; }
  else if (A === 'sit') { sit = 1; legA = [1.45, 1.35]; kn = [1.5, 1.45]; armA = [0.5, 0.3]; elb = [0.5, 0.6]; }
  else if (A === 'sniff') { lean = 0.32; headTilt = 0.25; armA = [0.3, -0.5]; elb = [1.2, 0.4]; }
  else if (A === 'eat') { const u = Math.max(0, Math.sin((t * 1.3 + ph) * TAU)); armA = [0.9 + u * 0.9, -0.1]; elb = [1.6 + u * 0.9, 0.1]; }
  else if (A === 'sleep') { lie = 1; }
  else if (A === 'fall') { const k = fallK(t); whole = -PI * 0.5 * sm(k); dy = -Math.sin(k * PI) * 0.18; armA = [PI * 0.7, -PI * 0.7]; legA = [0.5 + Math.sin(t * TAU * 3) * 0.3 * k, -0.2 + Math.sin(t * TAU * 3 + 1) * 0.3 * k]; kn = [0.6, 0.6]; }
  else { armA = [0.1 + m.breath * 0.03, -0.1 - m.breath * 0.03]; }
  const hipY = ground - legL + dy + (sit ? legL * 0.45 : 0), hip = [0, hipY], neck = rotAbout([0, hipY - th * 2], hip, lean);
  const P = [];
  const leg = (i, far) => {
    const top = [hip[0] + (i ? -0.05 : 0.05), hip[1]], pts = seg2(top, legL * 0.52, legA[i], legL * 0.52, legA[i] - kn[i]);
    const ra = edAdult ? tw * 0.3 : tw * 0.33, rb = edAdult ? tw * 0.23 : tw * 0.28;
    return [tube(pts, ra, rb, pants, { tone: far ? 0.3 : 0 }), E(pts[2][0] + 0.06, pts[2][1] + 0.02, edAdult ? 0.095 : 0.1, edAdult ? 0.042 : 0.05, 'bg', { tone: 0 }), { ...E(top[0], top[1], 0.02, 0.02, 'ink'), pin: true, fine: true }];
  };
  const arm = (i, far) => {
    const sh = rotAbout([0.02 * (i ? -1 : 1), hipY - th * 1.75], hip, lean), pts = seg2(sh, th * 0.75, armA[i], th * 0.72, armA[i] + elb[i] * (armA[i] >= 0 ? 1 : -1));
    const ra = edAdult ? tw * 0.22 : tw * 0.24, rb = edAdult ? tw * 0.17 : tw * 0.2;
    const out = [tube(pts, ra, rb, body, { tone: far ? 0.38 : 0.16 }), E(pts[2][0], pts[2][1], edAdult ? tw * 0.22 : tw * 0.26, edAdult ? tw * 0.22 : tw * 0.26, skin, { tone: far ? 0.3 : 0 }), { ...E(sh[0], sh[1], 0.02, 0.02, 'ink'), pin: true, fine: true }];
    if (A === 'point' && i === 0) out.push(tube([pts[2], [pts[2][0] + Math.sin(armA[0]) * 0.12, pts[2][1] + Math.cos(armA[0]) * 0.12]], 0.025, 0.02, skin));
    return out;
  };
  P.push(...arm(1, true), ...leg(1, true), ...leg(0, false));
  const torso = edAdult
    ? PG([[-tw * 1.06, hipY - th * 1.98], [tw * 1.06, hipY - th * 1.98], [tw * 0.86, hipY + 0.02], [-tw * 0.86, hipY + 0.02]], body)
    : PG([[-tw * 0.95, hipY - th * 1.95], [tw * 0.95, hipY - th * 1.95], [tw * 1.05, hipY + 0.02], [-tw * 1.05, hipY + 0.02]], body);
  const torsoGrp = [torso, E(0, hipY, edAdult ? tw * 0.92 : tw * 1.05, tw * 0.42, pants)];
  if (opt.heat > 0.05) torsoGrp.push(...thermalCore(0, hipY - th * 1.05, tw * 0.92, th * 0.72, opt.heat, m.breath));
  P.push(...xform(torsoGrp, hip, lean));
  const hc = [neck[0] + Math.sin(lean) * hr * 0.6, neck[1] - hr * 0.82 + Math.sin(m.breath * PI) * 0.004];
  const H = [];
  if (style === 'long') H.push(PG([[hc[0] - hr * 1.02, hc[1] - hr * 0.2], [hc[0] + hr * 0.7, hc[1] - hr * 0.3], [hc[0] + hr * 0.2, hc[1] + hr * 1.25], [hc[0] - hr * 1.05, hc[1] + hr * 1.2 + Math.sin(t * 2) * 0.01]], hair));
  if (style === 'bun') H.push(E(hc[0] - hr * 0.6, hc[1] - hr * 0.85, hr * 0.38, hr * 0.38, hair));
  H.push(tube([[hc[0] + hr * 0.05, hc[1] + hr * 0.75], [neck[0], neck[1] + 0.02]], hr * 0.3, tw * 0.35, skin));
  H.push(E(hc[0], hc[1], hr, hr * 1.02, skin));
  H.push(E(hc[0] - hr * 0.88, hc[1] + hr * 0.05, hr * 0.17, hr * 0.24, skin, { tone: 0.15 }));
  if (style === 'curly') for (let i = 0; i < 9; i++) { const a = PI + 0.1 + i / 8 * (PI - 0.2); H.push(E(hc[0] + Math.cos(a) * hr * 0.92, hc[1] + Math.sin(a) * hr * 0.92, hr * 0.32, hr * 0.32, hair)); }
  else if (style === 'cap') H.push(PG([...Array.from({ length: 11 }, (_, i) => { const a = PI + i / 10 * PI; return [hc[0] + Math.cos(a) * hr * 1.03, hc[1] - hr * 0.12 + Math.sin(a) * hr * 1.0]; })], hair), PG([[hc[0] + hr * 0.6, hc[1] - hr * 0.2], [hc[0] + hr * 1.55, hc[1] - hr * 0.1], [hc[0] + hr * 0.9, hc[1] - hr * 0.35]], hair, { tone: 0.2 }));
  else if (style !== 'bald') H.push(PG([...Array.from({ length: 11 }, (_, i) => { const a = PI + 0.05 + i / 10 * (PI - 0.1); return [hc[0] + Math.cos(a) * hr * 1.06, hc[1] + Math.sin(a) * hr * 1.06]; }), [hc[0] + hr * 0.5, hc[1] - hr * 0.42], [hc[0] - hr * 0.2, hc[1] - hr * 0.5], [hc[0] - hr * 0.9, hc[1] + hr * 0.1]], hair));
  H.push(...face({ eyes: [[hc[0] + hr * 0.42, hc[1] + hr * 0.02, hr * 0.19], [hc[0] - hr * 0.16, hc[1] + hr * 0.0, hr * 0.16]], mouth: [hc[0] + hr * 0.2, hc[1] + hr * 0.5, hr * 0.4], skin, look: [0.5, A === 'sniff' ? 0.5 : 0] }, X, blink, t, { asleep: A === 'sleep', chew: A === 'eat', editorial: ed }));
  if (!ed) H.push(E(hc[0] + hr * 0.66, hc[1] + hr * 0.28, hr * 0.09, hr * 0.07, skin, { tone: 0.25, fine: true }));
  P.push(...xform(H, [hc[0], hc[1] + hr], headTilt));
  P.push(...arm(0, false));
  let out = P;
  if (lie) out = xform(P, [0, ground], -PI / 2, 0.35, -0.05);
  else if (whole) out = xform(P, [0, ground], whole, 0, 0);
  if (A === 'sleep') for (let i = 0; i < 3; i++) { const u = (m.sleepZ + i / 3) % 1; out.push(zee(0.1 + u * 0.25, 0.2 - u * 0.5, 0.06 + u * 0.05, 'ink', 1 - u)); }
  return out;
}

const PLAN_FN = { quad, bird, fish, frog, biped };
const blinkAt = (f, seed) => { const per = 46 + (((seed % 31) + 31) % 31), q = (((f + seed * 13) % per) + per) % per; return q < 2 ? 0.5 : q < 4 ? 1 : 0; };

/** Primitive của một nhân vật. name = "rig:<loài>…"; o = {f, fps, seed, role, args:{action, expr, face, t0, hair, colors}}.
 *  Tên sai → chấm tròn + nhân vật mặc định (Python kiểm trước khi render: engines/html/rig2d.py). */
export function rigPrims(name, o = {}) {
  const r = parseRig(name) || { species: null, bad: [] }, a = o.args || {};
  const sp = SPECIES[(a.species && (SPECIES[a.species] ? a.species : RIG_ALIASES[a.species])) || r.species] ? ((a.species && (SPECIES[a.species] ? a.species : RIG_ALIASES[a.species])) || r.species) : 'dog';
  const S = SPECIES[sp], action = ACTIONS.includes(a.action) ? a.action : r.action || 'idle';
  const expr = EXPRS.includes(a.expr) ? a.expr : r.expr || DEF_EXPR[action] || 'neutral';
  const fps = o.fps || 30, seed = (o.seed ?? 1) | 0, ph = ((seed * 0.6180339) % 1 + 1) % 1;
  const f = (o.f ?? 0) - (a.t0 ? a.t0 * fps : 0), t = Math.max(0, f) / fps;
  const blink = blinkAt(Math.round(f), seed);
  const body = (a.colors && a.colors.body) || o.role || S.role;
  const editorial = Boolean(
    a.editorial ?? o.editorial ?? (o.look && o.look.rig && o.look.rig.editorial)
      ?? (a.style === 'editorial' || o.style === 'editorial' || a.face === 'editorial')
  );
  const heat = clamp(Number(a.heat ?? o.heat ?? 0) || 0, 0, 1);
  let prims = PLAN_FN[S.plan](S, action, expr, t, ph, body, blink, {
    species: sp, hair: a.hair || r.hair, skin: a.colors?.skin, pants: a.colors?.pants,
    hairRole: a.colors?.hair, editorial, heat,
  });
  if (a.colors) prims = prims.map((p) => (a.colors[p.role] ? { ...p, role: a.colors[p.role] } : p));
  const faceDir = a.face === 'editorial' ? r.face : (a.face || r.face);
  return faceDir === 'left' ? mirror(prims) : prims;
}
export const isRig = (name) => typeof name === 'string' && name.trim().toLowerCase().startsWith('rig:');
export const RIG_NAMES = Object.keys(SPECIES);
