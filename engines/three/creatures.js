// Kho nhân vật 3D của cảnh `stage` — SINH THỦ TỤC từ bảng dữ liệu loài (không tải mô hình): con vật + người chung chung
// (không người thật, không nhân vật có bản quyền). Mỗi loài = tỉ lệ thân/đầu/chân + kiểu tai/đuôi/mõm + vai màu; mặt VẼ
// TRÊN TEXTURE (mắt có chấm sáng, lông mày, miệng) theo biểu cảm, chớp mắt tất định. Dáng đi/hành động là HÀM THUẦN của
// frame (bảng pha/tốc độ/hướng tính MỘT LẦN từ keyframe lúc dựng → worker nào cũng ra y hệt), tai/đuôi trễ pha.
// Chạy trong mọi look3d: khối chính qua ctx.THREE (facet của look) + ctx.toon (chất liệu của look); texture qua ctx.lookTex.
// Python đọc SPECIES/ALIASES/GAITS/EXPRS/HAIRS ở đây để kiểm storyboard (engines/adapter.py → creature_vocab).
import * as THREE from '../../vendor/three/three.module.js';

export const GAITS = ['idle', 'walk', 'trot', 'run', 'sniff', 'sit', 'jump', 'hop', 'wag', 'eat', 'sleep', 'fall', 'swim'];
export const EXPRS = ['neutral', 'happy', 'shock', 'sad', 'angry', 'sleepy', 'sniff', 'love', 'wink'];
export const HAIRS = ['short', 'bob', 'pony', 'spiky', 'curly', 'bald'];

// màu mặc định theo token (style ghi đè bằng world.colors.<token>; prop ghi đè bằng color)
export const TONES = {
  fur_orange: '#E87A2C', fur_peach: '#F6AC66', fur_rust: '#B9541E', fur_tan: '#C88A4C', fur_brown: '#7B4A26',
  fur_dark: '#3A2A22', fur_cream: '#F4E0B6', fur_grey: '#8C8E98', fur_silver: '#C4C6CE', fur_white: '#F5F2EA',
  fur_black: '#2A2A30', fur_red: '#DA5A24', pink: '#F59DB6', pink_dark: '#DC6C8A', skin: '#EBB48C', leaf: '#62BE3C',
  frog: '#6CCB3C', shell: '#8A9A3A', shell_dark: '#56601F', dino: '#57B848', dino_belly: '#EADF8C', beak: '#F6A623',
  comb: '#E23B2E', horn: '#EFE4CA', hoof: '#3A302C', fish: '#FF8A2A', fish_fin: '#FFC94A', penguin: '#25272F',
  bird: '#3D8BEA', duck: '#F7D44A', nose: '#17161A', eye_white: '#FFFFFF', pupil: '#16161B', brow: '#2B1E18',
  mouth: '#5C1E24', tongue: '#F26B80', blush: '#F48CA2', hair_brown: '#5C3822', hair_black: '#25201E',
  hair_blond: '#E9C35C', shirt: '#3D7BE0', shirt2: '#E8483C', pants: '#2F3E66', shoes: '#F2F2F2', wool: '#F7F2E6',
  sheep_face: '#3B332E',
};

// bảng màu trưởng thành giảm bão hoà cho chế độ editorial (Vox/Fern/Cleo Abram — không màu kẹo/đồ chơi)
const EDITORIAL_TONES = {
  fur_orange: '#B8693E', fur_peach: '#C9956B', fur_rust: '#8E492D', fur_tan: '#A07E5B', fur_brown: '#6E4C38',
  fur_dark: '#2A2524', fur_cream: '#DDD2BE', fur_grey: '#6D737F', fur_silver: '#9FA5B0', fur_white: '#ECEAE2',
  fur_black: '#22242B', fur_red: '#A84E36', pink: '#BE8492', pink_dark: '#9E6271', skin: '#D9B394', leaf: '#355E47',
  frog: '#3F6A4C', shell: '#677442', shell_dark: '#414A2A', dino: '#436B4D', dino_belly: '#C7BE84', beak: '#C98A32',
  comb: '#B84336', horn: '#D6CCB8', hoof: '#2B2624', fish: '#C4723C', fish_fin: '#CFA44C', penguin: '#20242C',
  bird: '#3D6A92', duck: '#C4A54B', nose: '#1C1D22', eye_white: '#ECEAE2', pupil: '#181A20', brow: '#2C2522',
  mouth: '#4B282B', tongue: '#B55B68', blush: '#C67E8D', hair_brown: '#4A3528', hair_black: '#232224',
  hair_blond: '#C4A85C', shirt: '#3C6282', shirt2: '#9E463B', pants: '#232833', shoes: '#1D2028', wool: '#E3DEC8',
  sheep_face: '#312C2A',
};

// Bảng loài (mét, scale 1; +Z = phía trước). kind: quad | biped | bird | fish.
// len/r/w = thân dài / bán kính / tỉ lệ rộng · leg/legR = chân (đất → hông) / bán kính · hind = hệ số chân sau
// head = bán kính đầu · hs = tỉ lệ đầu [x,y,z] · neck = [dài, góc ngẩng rad] · snout = [long|short|cone|disc|flat|beak|none,
// dài, bán kính] · ears = [flop|point|round|long|small|none, cỡ] · tail = [thin|bushy|puff|curly|stub|brush|thick|fan|none,
// dài, góc dựng rad] · pattern = plain|belly|patches|stripes|saddle|tux|mask · extras = horns mane wool shell spikes comb
// wattle whiskers eyebumps · face = {gap, y, r, my} mắt/miệng trên mặt nhìn thẳng (0..1) · walk = dáng thay khi di chuyển
// · tones = vai màu → token (body belly snout ear ear_in nose paw tail tail_tip patch mane extra beak skin shirt pants shoes hair)
export const SPECIES = {
  dog: { kind: 'quad', len: 0.6, r: 0.13, w: 0.95, leg: 0.27, legR: 0.042, head: 0.125, neck: [0.07, 0.75],
    snout: ['long', 0.11, 0.058], ears: ['flop', 0.14], tail: ['thin', 0.24, 0.7], pattern: 'belly',
    tones: { body: 'fur_tan', belly: 'fur_cream', snout: 'fur_cream', ear: 'fur_brown', paw: 'fur_cream' } },
  dachshund: { kind: 'quad', len: 0.64, r: 0.1, w: 0.92, leg: 0.1, legR: 0.03, head: 0.1, neck: [0.06, 0.55],
    snout: ['long', 0.13, 0.048], ears: ['flop', 0.15], tail: ['thin', 0.22, 0.45], pattern: 'belly',
    tones: { body: 'fur_orange', belly: 'fur_peach', snout: 'fur_orange', ear: 'fur_rust', paw: 'fur_orange' } },
  cat: { kind: 'quad', len: 0.42, r: 0.095, w: 0.9, leg: 0.2, legR: 0.028, head: 0.1, neck: [0.05, 0.8],
    snout: ['short', 0.03, 0.045], ears: ['point', 0.075], tail: ['thin', 0.34, 1.25], pattern: 'stripes', extras: ['whiskers'],
    tones: { body: 'fur_grey', belly: 'fur_silver', snout: 'fur_white', ear_in: 'pink', paw: 'fur_white', patch: 'fur_dark', nose: 'pink' } },
  fox: { kind: 'quad', len: 0.55, r: 0.1, w: 0.9, leg: 0.24, legR: 0.03, head: 0.105, neck: [0.06, 0.7],
    snout: ['long', 0.12, 0.045], ears: ['point', 0.1], tail: ['bushy', 0.36, 0.4], pattern: 'mask',
    tones: { body: 'fur_red', belly: 'fur_white', snout: 'fur_white', ear_in: 'fur_dark', paw: 'fur_dark', tail_tip: 'fur_white' } },
  wolf: { kind: 'quad', len: 0.9, r: 0.16, w: 0.9, leg: 0.4, legR: 0.05, head: 0.15, neck: [0.09, 0.6],
    snout: ['long', 0.17, 0.07], ears: ['point', 0.12], tail: ['bushy', 0.45, 0.15], pattern: 'belly',
    tones: { body: 'fur_grey', belly: 'fur_silver', snout: 'fur_silver', ear_in: 'fur_dark', paw: 'fur_silver' } },
  bear: { kind: 'quad', len: 1.0, r: 0.3, w: 1.0, leg: 0.34, legR: 0.1, head: 0.22, neck: [0.06, 0.3],
    snout: ['short', 0.1, 0.1], ears: ['round', 0.11], tail: ['stub', 0.08, 0.5], pattern: 'plain',
    tones: { body: 'fur_brown', snout: 'fur_tan', ear_in: 'fur_dark', paw: 'fur_dark' } },
  rabbit: { kind: 'quad', len: 0.3, r: 0.1, w: 0.9, leg: 0.08, hind: 1.5, legR: 0.03, head: 0.09, neck: [0.03, 0.9],
    snout: ['short', 0.025, 0.04], ears: ['long', 0.16], tail: ['puff', 0.06, 0.6], pattern: 'belly', extras: ['whiskers'], walk: 'hop',
    tones: { body: 'fur_silver', belly: 'fur_white', snout: 'fur_white', ear_in: 'pink', nose: 'pink', tail: 'fur_white' } },
  mouse: { kind: 'quad', len: 0.17, r: 0.052, w: 0.9, leg: 0.045, legR: 0.014, head: 0.052, neck: [0.02, 0.5],
    snout: ['cone', 0.05, 0.026], ears: ['round', 0.05], tail: ['thin', 0.2, 0.25], pattern: 'belly', extras: ['whiskers'],
    tones: { body: 'fur_grey', belly: 'fur_silver', snout: 'fur_grey', ear_in: 'pink', nose: 'pink', paw: 'pink', tail: 'pink' } },
  pig: { kind: 'quad', len: 0.75, r: 0.22, w: 1.0, leg: 0.18, legR: 0.06, head: 0.16, neck: [0.03, 0.2],
    snout: ['disc', 0.06, 0.075], ears: ['small', 0.08], tail: ['curly', 0.06, 0.8], pattern: 'plain', face: { my: 0.8 },
    tones: { body: 'pink', snout: 'pink_dark', ear: 'pink', paw: 'pink_dark' } },
  cow: { kind: 'quad', len: 1.6, r: 0.36, w: 0.95, leg: 0.62, legR: 0.08, head: 0.24, neck: [0.16, 0.35],
    snout: ['flat', 0.16, 0.14], ears: ['small', 0.14], tail: ['brush', 0.6, -0.3], pattern: 'patches', extras: ['horns'],
    tones: { body: 'fur_white', patch: 'fur_black', snout: 'pink', paw: 'hoof', tail: 'fur_black', extra: 'horn' } },
  horse: { kind: 'quad', len: 1.5, r: 0.3, w: 0.85, leg: 0.85, legR: 0.07, head: 0.17, hs: [0.9, 1, 1.1], neck: [0.55, 1.0],
    snout: ['long', 0.3, 0.1], ears: ['point', 0.12], tail: ['brush', 0.7, -0.2], pattern: 'plain', extras: ['mane'],
    tones: { body: 'fur_brown', snout: 'fur_brown', ear_in: 'fur_dark', paw: 'hoof', tail: 'fur_dark', mane: 'fur_dark' } },
  sheep: { kind: 'quad', len: 0.85, r: 0.27, w: 1.0, leg: 0.36, legR: 0.045, head: 0.13, neck: [0.08, 0.45],
    snout: ['long', 0.1, 0.07], ears: ['small', 0.1], tail: ['stub', 0.06, 0.3], pattern: 'plain', extras: ['wool'],
    tones: { body: 'wool', head: 'sheep_face', snout: 'sheep_face', ear: 'sheep_face', paw: 'sheep_face', brow: 'fur_grey' } },
  chicken: { kind: 'bird', len: 0.3, r: 0.12, w: 0.9, leg: 0.14, legR: 0.013, head: 0.07, neck: [0.09, 1.25],
    snout: ['beak', 0.05, 0.025], ears: ['none'], tail: ['fan', 0.12, 1.0], pattern: 'plain', extras: ['comb', 'wattle'],
    tones: { body: 'fur_white', beak: 'beak', paw: 'beak', extra: 'comb' } },
  bird: { kind: 'bird', len: 0.16, r: 0.06, w: 0.9, leg: 0.06, legR: 0.007, head: 0.05, neck: [0.03, 1.0],
    snout: ['beak', 0.03, 0.013], ears: ['none'], tail: ['fan', 0.09, 0.5], pattern: 'belly',
    tones: { body: 'bird', belly: 'fur_cream', beak: 'beak', paw: 'beak' } },
  duck: { kind: 'bird', len: 0.34, r: 0.11, w: 0.95, leg: 0.08, legR: 0.012, head: 0.075, neck: [0.1, 1.2],
    snout: ['bill', 0.07, 0.035], ears: ['none'], tail: ['fan', 0.07, 0.8], pattern: 'plain',
    tones: { body: 'duck', beak: 'beak', paw: 'beak' } },
  penguin: { kind: 'bird', upright: true, len: 0.5, r: 0.17, w: 0.85, leg: 0.05, legR: 0.03, head: 0.115, neck: [0.02, 1.4],
    snout: ['beak', 0.06, 0.025], ears: ['none'], tail: ['stub', 0.04, 0], pattern: 'tux', wings: 'flipper',
    tones: { body: 'penguin', belly: 'fur_white', head: 'penguin', beak: 'beak', paw: 'beak' } },
  fish: { kind: 'fish', len: 0.36, r: 0.09, w: 0.55, head: 0.082, snout: ['none'], ears: ['none'], tail: ['none'],
    pattern: 'belly', tones: { body: 'fish', belly: 'fur_cream', fin: 'fish_fin' } },
  frog: { kind: 'quad', len: 0.16, r: 0.065, w: 1.3, leg: 0.045, hind: 2.0, legR: 0.022, head: 0.085, hs: [1.3, 0.8, 1.0],
    neck: [0, 0.3], snout: ['none'], ears: ['none'], tail: ['none'], pattern: 'belly', extras: ['eyebumps'], walk: 'hop',
    face: { gap: 0.2, y: 0.36, r: 0.1, my: 0.66, wide: true }, tones: { body: 'frog', belly: 'fur_cream' } },
  turtle: { kind: 'quad', len: 0.3, r: 0.075, w: 1.1, leg: 0.06, legR: 0.026, head: 0.055, neck: [0.08, 0.35],
    snout: ['none'], ears: ['none'], tail: ['stub', 0.04, 0], pattern: 'plain', extras: ['shell'], speed: 0.6,
    tones: { body: 'leaf', shell: 'shell', patch: 'shell_dark' } },
  dino: { kind: 'biped', lean: 1.0, len: 0.9, r: 0.24, w: 0.85, leg: 0.5, legR: 0.075, head: 0.17, neck: [0.18, 0.9],
    snout: ['long', 0.18, 0.11], ears: ['none'], tail: ['thick', 0.95, 0.12], pattern: 'belly', arms: 'tiny', extras: ['spikes'],
    tones: { body: 'dino', belly: 'dino_belly', snout: 'dino', extra: 'shell_dark', paw: 'dino' } },
  kid: { kind: 'biped', human: true, height: 1.15, head: 0.165, hair: 'short', blush: true, ears: ['human', 0.03],
    snout: ['none'], tail: ['none'], tones: { skin: 'skin', shirt: 'shirt', pants: 'pants', shoes: 'shoes', hair: 'hair_brown' } },
  adult: { kind: 'biped', human: true, height: 1.72, head: 0.125, hair: 'short', ears: ['human', 0.025], long_pants: true,
    snout: ['none'], tail: ['none'], tones: { skin: 'skin', shirt: 'shirt2', pants: 'pants', shoes: 'fur_dark', hair: 'hair_black' } },
};

// bí danh dùng thẳng làm `type` của prop (không có "mouse" vì trùng nghĩa chuột máy tính — dùng creature + species)
export const ALIASES = {
  dog: 'dog', puppy: 'dog', dachshund: 'dachshund', cat: 'cat', kitten: 'cat', fox: 'fox', wolf: 'wolf', bear: 'bear',
  rabbit: 'rabbit', bunny: 'rabbit', pig: 'pig', cow: 'cow', horse: 'horse', sheep: 'sheep', chicken: 'chicken',
  hen: 'chicken', duck: 'duck', penguin: 'penguin', fish: 'fish', frog: 'frog', turtle: 'turtle', dino: 'dino',
  dinosaur: 'dino', kid: 'kid', child: 'kid', adult: 'adult', rat: 'mouse',
};

// dáng → biểu cảm mặc định khi storyboard không ghi expr
const GAIT_EXPR = { idle: 'neutral', walk: 'neutral', trot: 'happy', run: 'happy', sniff: 'sniff', sit: 'happy', jump: 'happy',
  hop: 'happy', wag: 'happy', eat: 'happy', sleep: 'sleepy', fall: 'shock', swim: 'neutral' };
const CYCLIC = { walk: [1.5, 1.6], trot: [2.2, 2.4], run: [3.4, 3.1], swim: [2.0, 1.4] };   // [sải chân × leg, nhịp tại chỗ Hz]
const WAG = { idle: [0.25, 0.7], walk: [0.3, 1.6], trot: [0.35, 2.2], run: [0.2, 3], sniff: [0.55, 2.2], sit: [0.35, 1.4],
  jump: [0.3, 2], hop: [0.3, 2], wag: [0.95, 3.6], eat: [0.3, 1.2], sleep: [0.04, 0.3], fall: [0.1, 1], swim: [0.6, 2.4] };

const HAS_DOM = typeof document !== 'undefined';
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => { const x = clamp(t); return x * x * (3 - 2 * x); };
const TAU = Math.PI * 2;
const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const fract = (x) => x - Math.floor(x);
const hash = (i, s = 1) => fract(Math.sin(i * 127.1 + s * 311.7) * 43758.5453);

/** Các loài có trong bảng (cho công cụ/test). */
export const speciesNames = () => Object.keys(SPECIES);

// ----------------------------------------------------------------------------------------------------------------------
// texture vẽ bằng code (mặt nhìn thẳng, thân quấn quanh trục) — độ phân giải theo look (ctx.texPx), lọc theo look
// ----------------------------------------------------------------------------------------------------------------------
const cv = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; };
const shade = (hex, k) => {           // k < 1 tối hơn, > 1 sáng hơn (giữ sắc độ)
  const n = parseInt(hex.slice(1, 7), 16), f = (v) => Math.max(0, Math.min(255, Math.round(k < 1 ? v * k : v + (255 - v) * (k - 1))));
  return `#${[(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => f(v).toString(16).padStart(2, '0')).join('')}`;
};
const mixHex = (a, b, t) => {
  const na = parseInt(a.slice(1, 7), 16), nb = parseInt(b.slice(1, 7), 16);
  const ch = (sh) => Math.max(0, Math.min(255, Math.round(lerp((na >> sh) & 255, (nb >> sh) & 255, t)))).toString(16).padStart(2, '0');
  return `#${ch(16)}${ch(8)}${ch(0)}`;
};
const ell = (g, x, y, rx, ry, rot = 0) => { g.beginPath(); g.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), rot, 0, TAU); };
const speckle = (g, w, h, base, seed, n = 60, k = 0.06) => {   // vân lông/da nhẹ (tất định) → texture "vẽ tay" thời 90
  for (let i = 0; i < n; i++) {
    g.fillStyle = shade(base, hash(i, seed) < 0.5 ? 1 - k : 1 + k);
    ell(g, hash(i, seed + 1) * w, hash(i, seed + 2) * h, w * (0.01 + 0.02 * hash(i, seed + 3)), h * (0.02 + 0.03 * hash(i, seed + 4)));
    g.fill();
  }
};

/** Thân: u quanh trục (bụng ở u = 0.5), v dọc thân (0 = đuôi, 1 = đầu; canvas y = 0 là đầu). */
function paintBody(T, H, pattern, c, seed) {
  const [cn, g] = cv(T, H);
  g.fillStyle = c.body; g.fillRect(0, 0, T, H);
  speckle(g, T, H, c.body, seed, 70, 0.05);
  const band = (x0, w, col, soft = 0.12) => {
    const gr = g.createLinearGradient((x0 - w / 2 - soft) * T, 0, (x0 + w / 2 + soft) * T, 0);
    gr.addColorStop(0, col + '00'); gr.addColorStop(soft / (w + 2 * soft), col); gr.addColorStop(1 - soft / (w + 2 * soft), col); gr.addColorStop(1, col + '00');
    g.fillStyle = gr; g.fillRect((x0 - w / 2 - soft) * T, 0, (w + 2 * soft) * T, H);
  };
  if (pattern === 'belly' || pattern === 'mask') band(0.5, 0.26, c.belly);
  if (pattern === 'tux') band(0.5, 0.42, c.belly, 0.04);
  if (pattern === 'mask') { g.fillStyle = c.belly; ell(g, 0.5 * T, 0.05 * H, 0.3 * T, 0.22 * H); g.fill(); }
  if (pattern === 'saddle') { band(0, 0.3, c.patch || shade(c.body, 0.6)); band(1, 0.3, c.patch || shade(c.body, 0.6)); }
  if (pattern === 'patches') {
    g.fillStyle = c.patch;
    for (let i = 0; i < 7; i++) {
      const x = hash(i, seed + 9) * T, y = (0.1 + 0.8 * hash(i, seed + 10)) * H, r = (0.08 + 0.08 * hash(i, seed + 11)) * T;
      if (Math.abs(x / T - 0.5) < 0.12) continue;                       // bụng trắng
      for (let k = 0; k < 4; k++) { ell(g, x + (hash(k, i + seed) - 0.5) * r, y + (hash(k, i + seed + 5) - 0.5) * r * 0.8, r * 0.6, r * 0.5, hash(k, i)); g.fill(); }
    }
  }
  if (pattern === 'stripes') {
    g.strokeStyle = c.patch; g.lineCap = 'round';
    for (let i = 1; i < 7; i++) {
      const y = (i / 7) * H; g.lineWidth = H * 0.035;
      for (const [a, b] of [[-0.02, 0.33], [0.67, 1.02]]) {
        g.beginPath(); g.moveTo(a * T, y + H * 0.02); g.quadraticCurveTo((a + b) / 2 * T, y - H * 0.03, b * T, y + H * 0.02); g.stroke();
      }
    }
  }
  return cn;
}

/** Mặt nhìn thẳng (canvas vuông, đường tròn đầu bán kính 0.49): mắt + lông mày (+ miệng khi không có mõm). */
function paintFace(T, F, st) {
  const [cn, g] = cv(T, T), c = F.c, s = (v) => v * T, ed = !!F.editorial;
  g.fillStyle = c.head; g.fillRect(0, 0, T, T);
  speckle(g, T, T, c.head, F.seed, ed ? 12 : 26, ed ? 0.02 : 0.04);
  if (F.mask) { g.fillStyle = c.belly; ell(g, s(0.5), s(0.74), s(0.3), s(0.2)); g.fill(); }
  if (F.blush && !ed) { g.fillStyle = c.blush + '99'; for (const k of [-1, 1]) { ell(g, s(0.5 + k * 0.25), s(0.6), s(0.07), s(0.04)); g.fill(); } }
  const e = st.expr, er = F.r, lineW = Math.max(1.2, s(0.025));
  const eye = (k) => {
    const cx = s(0.5 + k * F.gap), cy = s(F.y), rx = s(er * (e === 'shock' ? 1.12 : 0.92)), ry = s(er * (e === 'shock' ? 1.2 : 1.05));
    const closed = st.blink >= 1 || e === 'sniff' || (e === 'wink' && k > 0) || st.sleep;
    g.lineCap = 'round'; g.lineJoin = 'round';
    if (ed) {                                        // mắt editorial tối giản: chấm tối tinh gọn, không lòng trắng googly/đốm sáng
      if (closed) {
        g.strokeStyle = c.pupil; g.lineWidth = lineW * 0.85; g.beginPath();
        g.moveTo(cx - rx * 0.55, cy); g.lineTo(cx + rx * 0.55, cy); g.stroke(); return;
      }
      const dr = s(er * (e === 'shock' ? 0.48 : 0.42));
      const px = cx + st.look[0] * rx * 0.22, py = cy + st.look[1] * ry * 0.18 + (e === 'sad' ? dr * 0.15 : 0);
      g.fillStyle = c.pupil; ell(g, px, py, dr, dr * 1.08); g.fill();
      const lid = Math.max(st.blink >= 0.5 ? 0.55 : 0, e === 'sleepy' ? 0.48 : 0, e === 'angry' ? 0.28 : 0);
      if (lid > 0) {
        const tilt = e === 'angry' ? 0.3 : 0, yl = py - dr + 2 * dr * lid;
        g.fillStyle = c.head; g.beginPath();
        g.moveTo(px - dr * 1.4, py - dr * 1.5); g.lineTo(px + dr * 1.4, py - dr * 1.5);
        g.lineTo(px + dr * 1.4, yl + k * tilt * dr); g.lineTo(px - dr * 1.4, yl - k * tilt * dr); g.closePath(); g.fill();
      }
      return;
    }
    if (closed) {                                    // mắt nhắm: ∩ (vui/đánh hơi) hoặc ⌣ (ngủ/chớp)
      const happy = e === 'sniff' || e === 'wink' || e === 'happy' || e === 'love';
      g.strokeStyle = c.pupil; g.lineWidth = lineW * 1.25; g.beginPath();
      if (happy && !st.sleep && st.blink < 1) g.arc(cx, cy + ry * 0.35, rx * 0.85, Math.PI * 1.15, Math.PI * 1.85);
      else g.arc(cx, cy - ry * 0.25, rx * 0.85, Math.PI * 0.15, Math.PI * 0.85);
      g.stroke(); return;
    }
    if (e === 'love') {                              // mắt tim
      g.fillStyle = c.heart; const r = rx * 0.75;
      g.beginPath(); g.moveTo(cx, cy + r * 0.9); g.bezierCurveTo(cx - r * 1.6, cy - r * 0.2, cx - r * 0.6, cy - r * 1.3, cx, cy - r * 0.45);
      g.bezierCurveTo(cx + r * 0.6, cy - r * 1.3, cx + r * 1.6, cy - r * 0.2, cx, cy + r * 0.9); g.fill(); return;
    }
    g.fillStyle = c.eye; ell(g, cx, cy, rx, ry); g.fill();
    g.strokeStyle = c.brow; g.lineWidth = lineW * 0.6; ell(g, cx, cy, rx, ry); g.stroke();
    const pr = Math.min(rx, ry) * (e === 'shock' ? 0.42 : 0.62);
    const px = cx + st.look[0] * rx * 0.38, py = cy + st.look[1] * ry * 0.3 + (e === 'sad' ? ry * 0.15 : 0);
    g.save(); ell(g, cx, cy, rx, ry); g.clip();
    g.fillStyle = c.pupil; ell(g, px, py, pr, pr * 1.06); g.fill();
    g.fillStyle = '#FFFFFF'; ell(g, px - pr * 0.36, py - pr * 0.4, pr * 0.34, pr * 0.34); g.fill();   // chấm sáng
    ell(g, px + pr * 0.32, py + pr * 0.36, pr * 0.14, pr * 0.14); g.fill();
    // mí trên: nửa nhắm (chớp 0.5 / buồn ngủ) hoặc nghiêng theo cảm xúc (giận: phía trong thấp; buồn: phía ngoài thấp)
    const lid = Math.max(st.blink >= 0.5 ? 0.55 : 0, e === 'sleepy' ? 0.5 : 0, e === 'angry' ? 0.3 : 0, e === 'sad' ? 0.25 : 0);
    if (lid > 0) {
      const tilt = e === 'angry' ? 0.35 : e === 'sad' ? -0.3 : 0, yl = cy - ry + 2 * ry * lid;
      g.fillStyle = c.head; g.beginPath();
      g.moveTo(cx - rx * 1.2, cy - ry * 1.3); g.lineTo(cx + rx * 1.2, cy - ry * 1.3);
      g.lineTo(cx + rx * 1.2, yl + k * tilt * ry); g.lineTo(cx - rx * 1.2, yl - k * tilt * ry); g.closePath(); g.fill();
      g.strokeStyle = c.brow; g.lineWidth = lineW * 0.8; g.beginPath(); g.moveTo(cx - rx * 1.1, yl - k * tilt * ry); g.lineTo(cx + rx * 1.1, yl + k * tilt * ry); g.stroke();
    }
    g.restore();
  };
  eye(-1); eye(1);
  // lông mày: [nâng (âm = lên), nghiêng phía trong (dương = nhíu)]
  const B = { neutral: [0, 0], happy: [-0.04, -0.01], shock: [-0.08, -0.02], sad: [-0.03, -0.06], angry: [0.01, 0.07],
    sleepy: [0.02, 0], sniff: [-0.02, 0], love: [-0.04, 0], wink: [-0.02, 0.02] }[e] || [0, 0];
  if (F.brows !== false) {
    g.strokeStyle = c.brow; g.lineWidth = lineW * (ed ? 0.82 : 1.3); g.lineCap = 'round';
    for (const k of [-1, 1]) {
      const cx = s(0.5 + k * F.gap), y0 = s(F.y - er * (ed ? 1.12 : 1.55) + B[0] * (ed ? 0.7 : 1));
      const bw = s(er * (ed ? 0.62 : 0.85));
      g.beginPath(); g.moveTo(cx - k * bw, y0 + s(B[1] * (ed ? 0.7 : 1))); g.lineTo(cx + k * bw, y0 - s(B[1] * (ed ? 0.3 : 0.4))); g.stroke();
    }
  }
  if (F.mouth) paintMouth(g, T, s(0.5), s(F.my), s(F.wide ? 0.2 : 0.1), st, c, lineW, ed);
  return cn;
}

/** Miệng theo biểu cảm (dùng cho mặt người/ếch/cá và cho mõm). w = nửa bề rộng (px). */
function paintMouth(g, T, x, y, w, st, c, lw, editorial = false) {
  const e = st.expr, open = st.jaw > 0.5 || e === 'happy' || e === 'love';
  g.lineCap = 'round'; g.lineJoin = 'round'; g.strokeStyle = c.mouth; g.fillStyle = c.mouth; g.lineWidth = lw * (editorial ? 0.85 : 1.2);
  if (editorial) {
    if (e === 'shock') { ell(g, x, y + w * 0.1, w * 0.24, w * 0.32); g.fill(); return; }
    if (e === 'sad' || e === 'angry') { g.beginPath(); g.moveTo(x - w * 0.65, y + w * 0.18); g.quadraticCurveTo(x, y - w * 0.15, x + w * 0.65, y + w * 0.18); g.stroke(); return; }
    if (e === 'happy' || e === 'love') { g.beginPath(); g.moveTo(x - w * 0.72, y); g.quadraticCurveTo(x, y + w * 0.42, x + w * 0.72, y); g.stroke(); return; }
    g.beginPath(); g.moveTo(x - w * 0.55, y + w * 0.04); g.lineTo(x + w * 0.55, y + w * 0.04); g.stroke();
    return;
  }
  if (e === 'shock') { ell(g, x, y + w * 0.15, w * 0.42, w * 0.55); g.fill(); return; }
  if (e === 'sad' || e === 'angry') { g.beginPath(); g.arc(x, y + w * 0.9, w * 0.8, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); return; }
  if (e === 'sleepy' || (e === 'sniff' && !open)) { ell(g, x, y + w * 0.1, w * 0.22, w * 0.16); g.fill(); return; }
  if (open) {                                      // cười há miệng + lưỡi
    g.beginPath(); g.moveTo(x - w, y - w * 0.1); g.quadraticCurveTo(x, y + w * 1.25, x + w, y - w * 0.1); g.closePath(); g.fill();
    g.save(); g.clip(); g.fillStyle = c.tongue; ell(g, x, y + w * 0.75, w * 0.5, w * 0.38); g.fill(); g.restore();
    return;
  }
  g.beginPath(); g.moveTo(x - w, y); g.quadraticCurveTo(x, y + w * 0.6, x + w, y); g.stroke();      // cười mỉm
}

/** Mõm nhìn thẳng: màu mõm + miệng "ω" dưới mũi + (lỗ mũi / ria) — miệng đổi theo biểu cảm. */
function paintSnout(T, F, st) {
  const [cn, g] = cv(T, T), c = F.c, s = (v) => v * T, lw = Math.max(1.2, s(0.03)), ed = !!F.editorial;
  g.fillStyle = c.snout; g.fillRect(0, 0, T, T);
  speckle(g, T, T, c.snout, F.seed + 7, ed ? 6 : 12, ed ? 0.02 : 0.04);
  if (F.nostrils) { g.fillStyle = shade(c.snout, 0.45); for (const k of [-1, 1]) { ell(g, s(0.5 + k * 0.15), s(0.42), s(0.055), s(0.08)); g.fill(); } }
  if (F.whiskers) {
    g.strokeStyle = shade(c.snout, 0.55); g.lineWidth = lw * 0.5;
    for (const k of [-1, 1]) for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(s(0.5 + k * 0.2), s(0.56 + i * 0.05)); g.lineTo(s(0.5 + k * 0.48), s(0.5 + i * 0.09)); g.stroke(); }
  }
  if (F.mouth === false) return cn;
  if (ed) {
    g.strokeStyle = shade(c.snout, 0.42); g.lineCap = 'round'; g.lineWidth = lw * 0.7;
    g.beginPath(); g.moveTo(s(0.38), s(0.68)); g.quadraticCurveTo(s(0.5), s(0.71), s(0.62), s(0.68)); g.stroke();
    return cn;
  }
  const e = st.expr, y = s(0.66), w = s(0.17), open = st.jaw > 0.5 || e === 'happy' || e === 'love';
  g.strokeStyle = c.mouth; g.fillStyle = c.mouth; g.lineCap = 'round'; g.lineWidth = lw;
  if (!F.nostrils) { g.beginPath(); g.moveTo(s(0.5), s(0.46)); g.lineTo(s(0.5), y); g.stroke(); }
  if (open && e !== 'shock') {
    g.beginPath(); g.moveTo(s(0.5) - w * 1.1, y - w * 0.15); g.quadraticCurveTo(s(0.5), y + w * 1.5, s(0.5) + w * 1.1, y - w * 0.15); g.closePath(); g.fill();
    g.save(); g.clip(); g.fillStyle = c.tongue; ell(g, s(0.5), y + w * 0.95, w * 0.6, w * 0.5); g.fill(); g.restore();
  } else if (e === 'shock') { ell(g, s(0.5), y + w * 0.3, w * 0.4, w * 0.55); g.fill(); }
  else if (e === 'sad' || e === 'angry') { g.beginPath(); g.arc(s(0.5), y + w * 1.1, w * 0.9, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); }
  else { for (const k of [-1, 1]) { g.beginPath(); g.arc(s(0.5) + k * w * 0.5, y, w * 0.5, 0, Math.PI, false); g.stroke(); } }   // ω
  return cn;
}

/** Mũi bóng: đen + chấm sáng (editorial: lì tinh tế, không bóng loáng hoạt hình). */
function paintNose(T, col, editorial = false) {
  const [cn, g] = cv(T, T);
  g.fillStyle = col; g.fillRect(0, 0, T, T);
  g.fillStyle = editorial ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.85)';
  ell(g, T * 0.38, T * 0.3, T * 0.13, T * 0.09, -0.4); g.fill();
  return cn;
}

/** Mai rùa: tấm lục giác. */
function paintShell(T, c) {
  const [cn, g] = cv(T, T);
  g.fillStyle = c.shell; g.fillRect(0, 0, T, T);
  g.strokeStyle = c.patch; g.lineWidth = T * 0.03;
  for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) {
    const cx = (i + (j % 2) * 0.5) * T / 3.5, cy = j * T / 3.5, r = T * 0.13;
    g.beginPath(); for (let k = 0; k <= 6; k++) { const a = k / 6 * TAU; g[k ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * r, cy + Math.sin(a) * r); } g.stroke();
  }
  return cn;
}

// ----------------------------------------------------------------------------------------------------------------------
// hình học
// ----------------------------------------------------------------------------------------------------------------------
/** Nửa cầu trước (z ≥ 0, UV chiếu phẳng từ phía trước → mặt nhìn thẳng) hoặc nửa sau. Cùng đường nối → Gouraud liền. */
function halfSphere(r, ws, hs, front) {
  const geo = new THREE.SphereGeometry(r, ws, hs, front ? 0 : Math.PI, Math.PI);
  if (front) {
    const pa = geo.attributes.position, uv = geo.attributes.uv;
    for (let i = 0; i < pa.count; i++) uv.setXY(i, 0.5 + 0.49 * pa.getX(i) / r, 0.5 + 0.49 * pa.getY(i) / r);
  }
  return geo;
}
/** Thân tiện dọc trục Z (đuôi → đầu): u quanh trục (bụng u = 0.5), v dọc thân. */
function latheBody(len, r, rear, front, boxy, rings, segs) {
  const pts = [];
  for (let i = 0; i <= rings; i++) {
    const t = i / rings, k = lerp(rear, front, t) * Math.pow(Math.max(0, Math.sin(Math.PI * t)), 1 / boxy);
    pts.push(new THREE.Vector2(Math.max(1e-4, r * k), -len / 2 + t * len));
  }
  const geo = new THREE.LatheGeometry(pts, segs, Math.PI, TAU);
  geo.rotateX(Math.PI / 2);
  return geo;
}
const ROLE_DEFAULT = { belly: 'body', snout: 'body', ear: 'body', paw: 'body', tail: 'body', tail_tip: 'tail', head: 'body',
  shell: 'body', fin: 'body', mane: 'body', beak: 'body', ear_in: 'ear', patch: 'body', extra: 'body' };

// ----------------------------------------------------------------------------------------------------------------------
/**
 * Dựng một nhân vật. p = prop của stage: {species, gait, expr, look, color, hair, face, seed, …}.
 * → {g, update(f, env), bind(keys, poseFn), set, species, S}
 */
export function creature(ctx, p = {}) {
  const sp = SPECIES[p.species] ? p.species : SPECIES[ALIASES[p.species]] ? ALIASES[p.species] : 'dog';
  const S = { hind: 1, hs: [1, 1, 1], neck: [0.05, 0.6], snout: ['none'], ears: ['none'], tail: ['none'], extras: [], ...SPECIES[sp] };
  const LK = ctx.look3d || {}, FPS = ctx.fps || 30, N = ctx.N || 1;
  const worldCfg = (ctx.job && ctx.job.world) || {}, wCol = worldCfg.colors || {};
  const isRetroLook = LK.kind === 'retro90' || LK.kind === 'psx' || LK.mat === 'gouraud';
  const charStyle = worldCfg.character_style || (isRetroLook ? 'cartoon' : 'editorial');
  const isEditorial = charStyle === 'editorial' && !isRetroLook;
  if (isEditorial && sp === 'adult') S.head = S.head * 0.94;
  const seed = p.seed ?? ((Object.keys(SPECIES).indexOf(sp) + 1) * 7 + Math.round(((p.at || [0])[0] || 0) * 13));
  const plainOnly = LK.mat === 'wire' || LK.mat === 'xray';
  // ---- màu theo vai: prop.color (chuỗi = thân; object = từng vai) > editorial world.colors > style world.colors > TONES
  const edOverrides = {};
  if (isEditorial) {
    if (sp === 'adult') {
      const aCol = wCol.actor_a || wCol.water;
      edOverrides.shirt = /^#[0-9a-fA-F]{6}/.test(aCol || '') ? mixHex(aCol, '#2E3A4A', 0.22) : EDITORIAL_TONES.shirt;
      edOverrides.pants = /^#[0-9a-fA-F]{6}/.test(wCol.iron || '') ? wCol.iron : EDITORIAL_TONES.pants;
      edOverrides.skin = EDITORIAL_TONES.skin;
      edOverrides.shoes = EDITORIAL_TONES.shoes;
      edOverrides.hair = EDITORIAL_TONES.hair_black;
    } else if (sp === 'horse') {
      const bCol = wCol.actor_b || wCol.accent;
      const baseHorse = /^#[0-9a-fA-F]{6}/.test(bCol || '') ? mixHex('#78523B', bCol, 0.28) : EDITORIAL_TONES.fur_brown;
      edOverrides.body = baseHorse;
      edOverrides.snout = shade(baseHorse, 0.88);
    }
  }
  const propColObj = p.color && typeof p.color === 'object' ? p.color : p.color ? (S.human ? { shirt: p.color } : { body: p.color }) : {};
  const roles = { eye: 'eye_white', pupil: 'pupil', mouth: 'mouth', tongue: 'tongue', blush: 'blush', nose: 'nose', heart: 'comb', ...S.tones,
    ...edOverrides, ...propColObj };
  const hex = (role) => {
    let t = roles[role];
    if (t === undefined) return ROLE_DEFAULT[role] ? hex(ROLE_DEFAULT[role]) : '#888888';
    const c = ctx.C ? ctx.C(t) : t;
    if (typeof c === 'string' && c !== t && /^#/.test(c)) return c;
    if (isEditorial && EDITORIAL_TONES[t]) return EDITORIAL_TONES[t];
    return TONES[t] || (/^#[0-9a-fA-F]{6}/.test(t) ? t : '#888888');
  };
  const col = {};
  for (const r of ['body', 'belly', 'snout', 'ear', 'ear_in', 'paw', 'tail', 'tail_tip', 'head', 'patch', 'mane', 'extra', 'beak', 'shell',
    'fin', 'eye', 'pupil', 'mouth', 'tongue', 'blush', 'nose', 'heart', 'skin', 'shirt', 'pants', 'shoes', 'hair']) col[r] = hex(r);
  if (S.human) { col.head = col.skin; col.body = col.shirt; }
  col.brow = roles.brow ? hex('brow') : shade(S.human ? col.hair : col.head, 0.42);

  const TH = ctx.THREE || THREE;
  const facet = LK.facet || 0, seg = facet ? Math.max(6, facet) : 18, hseg = Math.max(3, Math.ceil(seg / 2)), vseg = Math.max(4, Math.round(seg * 0.62));
  const texPx = Math.max(32, ctx.texPx || 256);
  const MC = {};
  const M = (hx, o) => { if (o) return ctx.toon(hx, o); return MC[hx] || (MC[hx] = ctx.toon(hx)); };
  const tex = (canvas) => { if (!canvas) return null; const t = ctx.lookTex ? ctx.lookTex(canvas) : new THREE.CanvasTexture(canvas); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.ClampToEdgeWrapping; return t; };
  const add = (geo, m, parent, x = 0, y = 0, z = 0) => ctx.add(geo, m, x, y, z, parent);
  const grp = (parent, x = 0, y = 0, z = 0) => ctx.group(parent, x, y, z);
  const sph = (r, parent, hx, x, y, z, sc) => { const m = add(new TH.SphereGeometry(r, seg, vseg), M(hx), parent, x, y, z); if (sc) m.scale.set(...sc); return m; };
  const cyl = (r0, r1, h, parent, hx, x, y, z) => add(new TH.CylinderGeometry(r0, r1, h, seg), M(hx), parent, x, y, z);
  const cone = (r, h, parent, hx, x, y, z) => add(new TH.ConeGeometry(r, h, Math.max(5, Math.round(seg * 0.7))), M(hx), parent, x, y, z);

  const g = grp(ctx.world);
  const turn = grp(g);                                   // hướng theo đường đi (face: path)
  const rig = grp(turn);                                 // nhún/lăn/ngồi
  const J = { rig };                                     // khớp

  // ---- mặt (texture vẽ lại khi biểu cảm/chớp/con ngươi đổi)
  const F = { c: { ...col }, seed, gap: 0.2, y: 0.37, r: 0.125, my: 0.68, mouth: false, mask: S.pattern === 'mask', blush: S.blush, editorial: isEditorial, ...(S.face || {}) };
  const heatMats = [];
  const regHeatMat = (m) => {
    if (!m) return;
    heatMats.push({
      m,
      base: m.color ? m.color.clone() : new THREE.Color(0xffffff),
      baseEm: m.emissive ? m.emissive.clone() : new THREE.Color(0x000000),
    });
  };
  const faceState = { key: '', tex: null, snoutTex: null, snoutKey: '' };
  const faceCanvas = HAS_DOM && !plainOnly ? cv(texPx, texPx)[0] : null;
  const snoutCanvas = HAS_DOM && !plainOnly ? cv(Math.max(32, texPx >> 1), Math.max(32, texPx >> 1))[0] : null;
  const faceBall = (r, parent, front, back, sc) => {     // front: material có map (mặt) · back: màu trơn
    const gg = grp(parent);
    add(halfSphere(r, hseg, vseg, true), front, gg); add(halfSphere(r, hseg, vseg, false), back, gg);
    if (sc) gg.scale.set(...sc);
    return gg;
  };
  const texMat = (canvas, fallback, dedicated = false) => {
    if (!canvas) return { m: dedicated ? ctx.toon(fallback) : M(fallback), t: null };
    const t = tex(canvas); return { m: ctx.toon('#ffffff', { map: t }), t };
  };

  // ---- đầu (dùng chung cho mọi kind): head group ở cuối cổ
  const snoutK = S.snout[0], hasSnout = snoutK !== 'none';
  F.mouth = !hasSnout || snoutK === 'disc' || snoutK === 'beak' || snoutK === 'bill' ? (snoutK === 'beak' || snoutK === 'bill' ? false : true) : false;
  if (S.human) Object.assign(F, { gap: 0.17, y: 0.46, r: 0.085, my: 0.72 });
  const buildHead = (parent) => {
    const H = S.head, head = grp(parent);
    const fm = texMat(faceCanvas, col.head);
    faceState.tex = fm.t;
    J.headMesh = faceBall(H, head, fm.m, M(col.head), S.hs);
    if (hasSnout) {
      const [k, L, R] = S.snout;
      const sg = grp(head, 0, -H * (k === 'short' || k === 'cone' ? 0.32 : k === 'disc' ? 0.12 : 0.22) * S.hs[1], H * 0.7 * S.hs[2]);
      J.snout = sg;
      if (k === 'beak' || k === 'bill') {
        const up = add(new TH.ConeGeometry(R, L, Math.max(4, Math.round(seg * 0.5))), M(col.beak), sg, 0, 0, L * 0.4);
        up.rotation.x = Math.PI / 2; if (k === 'bill') up.scale.set(1.6, 1, 0.55);
        const jaw = grp(sg, 0, -R * 0.25, 0); J.jaw = jaw;
        const lo = add(new TH.ConeGeometry(R * 0.8, L * 0.8, Math.max(4, Math.round(seg * 0.5))), M(shade(col.beak, 0.85)), jaw, 0, -R * 0.2, L * 0.32);
        lo.rotation.x = Math.PI / 2; if (k === 'bill') lo.scale.set(1.5, 1, 0.45);
      } else {
        const sm = texMat(snoutCanvas, col.snout); faceState.snoutTex = sm.t;
        const scl = k === 'disc' ? [1, 0.82, 0.55] : k === 'flat' ? [1.25, 0.8, L / R] : k === 'cone' ? [0.85, 0.8, L / R] : [1, 0.86, Math.max(0.8, L / R)];
        faceBall(R, sg, sm.m, M(col.snout), scl);
        if (k !== 'disc' && k !== 'flat' && S.snoutNose !== false && sp !== 'horse') {
          const nr = R * (k === 'short' ? 0.42 : 0.38), nm = texMat(HAS_DOM && !plainOnly ? paintNose(32, col.nose, isEditorial) : null, col.nose);
          faceBall(nr, sg, nm.m, M(col.nose), [1.25, 0.9, 0.85]).position.set(0, R * 0.55 * scl[1], R * scl[2] * 0.92);
        }
      }
    } else if (S.human) {
      sph(H * 0.12, head, col.skin, 0, -H * 0.12, H * 0.97, [1, 0.9, 0.8]);   // mũi người
    }
    // tai
    const [ek, es] = S.ears;
    const earM = M(col.ear), inM = M(col.ear_in);
    J.ears = [];
    for (const k of [-1, 1]) {
      let ep;
      if (ek === 'flop') {
        ep = grp(head, k * H * 0.7, H * 0.4, -H * 0.16);
        const m = sph(es * 0.5, ep, col.ear, 0, -es * 0.42, 0, [0.3, 1, 0.66]); m.rotation.z = k * 0.16;
      } else if (ek === 'point') {
        ep = grp(head, k * H * 0.5, H * 0.72, -H * 0.08); ep.rotation.z = -k * 0.32;
        add(new TH.ConeGeometry(es * 0.42, es, 5), earM, ep, 0, es * 0.42, 0);
        const i = add(new TH.ConeGeometry(es * 0.24, es * 0.7, 5), inM, ep, 0, es * 0.36, es * 0.1); i.scale.z = 0.5;
      } else if (ek === 'round') {
        ep = grp(head, k * H * 0.62, H * 0.68, -H * 0.12); ep.rotation.z = -k * 0.4;
        sph(es * 0.5, ep, col.ear, 0, es * 0.25, 0, [1, 1, 0.38]);
        sph(es * 0.32, ep, col.ear_in, 0, es * 0.25, es * 0.12, [1, 1, 0.3]);
      } else if (ek === 'long') {
        ep = grp(head, k * H * 0.32, H * 0.78, -H * 0.15); ep.rotation.z = -k * 0.12;
        sph(es * 0.5, ep, col.ear, 0, es * 0.48, 0, [0.3, 1, 0.16]);
        sph(es * 0.4, ep, col.ear_in, 0, es * 0.48, es * 0.05, [0.2, 0.92, 0.1]);
      } else if (ek === 'small') {
        ep = grp(head, k * H * 0.82, H * 0.38, -H * 0.12); ep.rotation.z = -k * 1.1;
        sph(es * 0.5, ep, col.ear, 0, es * 0.4, 0, [0.42, 1, 0.24]);
      } else if (ek === 'human') {
        ep = grp(head, k * H * 0.98, 0, -H * 0.05);
        sph(es, ep, col.skin, 0, 0, 0, [0.5, 1, 0.8]);
      } else continue;
      J.ears.push({ g: ep, k, kind: ek, rz: ep.rotation.z });
    }
    // phụ kiện trên đầu
    const ex = S.extras;
    if (ex.includes('horns')) for (const k of [-1, 1]) { const h = cone(H * 0.1, H * 0.42, head, col.extra, k * H * 0.55, H * 0.78, -H * 0.1); h.rotation.z = -k * 0.7; }
    if (ex.includes('comb')) for (let i = 0; i < 3; i++) sph(H * 0.2, head, col.extra, 0, H * (0.95 + (i === 1 ? 0.12 : 0)), H * (0.25 - i * 0.28), [0.5, 1, 0.9]);
    if (ex.includes('wattle')) sph(H * 0.18, head, col.extra, 0, -H * 0.62, H * 0.75, [0.6, 1, 0.6]);
    if (ex.includes('eyebumps')) for (const k of [-1, 1]) sph(H * 0.3, head, col.body, k * H * 0.48, H * 0.55, H * 0.42, [1, 0.8, 1]);
    if (S.human) buildHair(head, H);
    return head;
  };
  const buildHair = (head, H) => {
    const kind = p.hair && HAIRS.includes(p.hair) ? p.hair : S.hair || 'short';
    if (kind === 'bald') return;
    const hm = M(col.hair);
    const cap = add(new THREE.SphereGeometry(H * 1.06, seg, vseg, 0, TAU, 0, Math.PI * (kind === 'bob' ? 0.6 : 0.46)), hm, head, 0, H * 0.04, -H * 0.06);
    cap.rotation.x = -0.25;
    if (kind === 'bob') { const b = sph(H * 0.95, head, col.hair, 0, -H * 0.1, -H * 0.2, [1.1, 0.75, 0.9]); b.position.y = -H * 0.05; }
    if (kind === 'pony') { const t = sph(H * 0.32, head, col.hair, 0, H * 0.1, -H * 1.1, [0.8, 1.4, 0.8]); t.rotation.x = 0.6; }
    if (kind === 'spiky') for (let i = 0; i < 5; i++) { const c = cone(H * 0.2, H * 0.5, head, col.hair, (i - 2) * H * 0.3, H * 0.95, -H * 0.1); c.rotation.z = -(i - 2) * 0.3; c.rotation.x = -0.3; }
    if (kind === 'curly') for (let i = 0; i < 7; i++) sph(H * 0.3, head, col.hair, Math.cos(i / 7 * TAU) * H * 0.75, H * 0.55 + Math.sin(i * 2.1) * H * 0.12, Math.sin(i / 7 * TAU) * H * 0.6 - H * 0.1);
  };

  // ---- đuôi: chuỗi đốt (trễ pha) hoặc một khối
  const buildTail = (parent) => {
    const [tk, tl, tup] = S.tail;
    J.tail = [];
    if (tk === 'none') return;
    const base = grp(parent); J.tailBase = base; J.tailUp = tup || 0;
    if (tk === 'thin' || tk === 'thick') {
      const n = 4, sl = tl / n, r0 = tk === 'thick' ? S.r * 0.55 : Math.max(S.legR * 0.55, tl * 0.06);
      let par = base;
      for (let i = 0; i < n; i++) {
        const sg = grp(par, 0, 0, i ? -sl : 0); J.tail.push(sg);
        const rA = r0 * (1 - i / n * 0.75), rB = r0 * (1 - (i + 1) / n * 0.75);
        const m = add(new TH.CylinderGeometry(rB, rA, sl * 1.08, Math.max(5, Math.round(seg * 0.6))), M(i === n - 1 && roles.tail_tip ? col.tail_tip : col.tail), sg, 0, 0, -sl / 2);
        m.rotation.x = Math.PI / 2;
        if (tk === 'thick' && S.extras.includes('spikes')) { const c = cone(rA * 0.5, rA * 0.9, sg, col.extra, 0, rA * 0.9, -sl * 0.5); c.rotation.x = -0.4; }
        par = sg;
      }
    } else {
      const sg = grp(base); J.tail.push(sg);
      if (tk === 'bushy') {
        sph(tl * 0.5, sg, col.tail, 0, 0, -tl * 0.5, [0.34, 0.34, 1]);
        sph(tl * 0.2, sg, col.tail_tip, 0, 0, -tl * 0.94, [0.75, 0.75, 0.9]);
      } else if (tk === 'puff' || tk === 'stub') sph(tl * 0.5, sg, col.tail, 0, 0, -tl * 0.3);
      else if (tk === 'curly') { const m = add(new TH.TorusGeometry(tl * 0.5, tl * 0.16, 5, Math.max(6, seg)), M(col.tail), sg, 0, tl * 0.4, -tl * 0.4); m.rotation.y = Math.PI / 2; }
      else if (tk === 'brush') { const m = cone(S.r * 0.18, tl, sg, col.tail, 0, -tl * 0.5, -S.r * 0.15); m.rotation.x = Math.PI + 0.25; }
      else if (tk === 'fan') for (let i = -1; i <= 1; i++) { const m = sph(tl * 0.5, sg, i ? col.tail : shade(col.tail, 0.85), i * tl * 0.22, tl * 0.15, -tl * 0.45, [0.35, 0.12, 1]); m.rotation.y = i * 0.35; }
    }
  };

  // ---- chân: hông → gối → bàn
  const buildLeg = (parent, x, y, z, L, R, pawHex, hoof) => {
    const hip = grp(parent, x, y, z);
    const up = L * 0.5;
    add(new TH.CylinderGeometry(R * 0.9, R * 1.08, up, Math.max(5, Math.round(seg * 0.7))), M(col.body), hip, 0, -up / 2, 0);
    const knee = grp(hip, 0, -up, 0);
    const lo = L - up - R * 0.7;
    add(new TH.CylinderGeometry(R * 0.78, R * 0.9, lo, Math.max(5, Math.round(seg * 0.7))), M(pawHex === col.paw && !hoof ? col.body : pawHex), knee, 0, -lo / 2, 0);
    if (hoof) add(new TH.CylinderGeometry(R * 0.85, R * 0.95, R * 1.2, Math.max(5, Math.round(seg * 0.7))), M(col.paw), knee, 0, -lo - R * 0.1, 0);
    else sph(R * 1.05, knee, col.paw, 0, -lo - R * 0.05, R * 0.25, [1, 0.72, 1.3]);
    return { hip, knee };
  };

  // ====================================================================================================================
  const footprint = [S.r * (S.w || 1) * 2, S.len || 0.3];
  if (S.kind === 'quad') {
    const L = S.leg, D = S.len * 0.62, r = S.r, w = S.w || 1;
    J.torso = grp(rig, 0, L, -D / 2);
    const bodyCanvas = HAS_DOM && !plainOnly ? paintBody(Math.max(32, texPx >> 1), Math.max(32, texPx >> 1), S.pattern, col, seed) : null;
    const bm = texMat(bodyCanvas, col.body, true);
    regHeatMat(bm.m);
    J.body = add(latheBody(S.len, r, 0.9, 1.05, sp === 'pig' || sp === 'sheep' || sp === 'bear' ? 2 : 2.8, facet ? 7 : 12, seg), bm.m, J.torso, 0, r * 0.35, D / 2);
    J.body.scale.x = w;
    const xs = r * w * 0.55, hoof = col.paw === TONES.hoof || (roles.paw === 'hoof');
    J.legs = [buildLeg(J.torso, -xs, 0, D, L, S.legR, col.paw, hoof), buildLeg(J.torso, xs, 0, D, L, S.legR, col.paw, hoof),
      buildLeg(J.torso, -xs, 0, 0, L * S.hind, S.legR * (S.hind > 1.2 ? 1.25 : 1), col.paw, hoof),
      buildLeg(J.torso, xs, 0, 0, L * S.hind, S.legR * (S.hind > 1.2 ? 1.25 : 1), col.paw, hoof)];
    if (S.hind > 1.2) J.legs.slice(2).forEach((lg) => { lg.hip.position.y = (L - L * S.hind) * 0.55; });   // chân sau to gập (thỏ, ếch)
    // cổ + đầu
    const [nl, na] = S.neck;
    J.neck = grp(J.torso, 0, r * 0.55, D / 2 + S.len * 0.36);
    J.neckVec = [0, Math.sin(na) * nl, Math.cos(na) * nl];
    if (nl > 0.02) {
      const nm = add(new TH.CylinderGeometry(S.head * 0.5, r * 0.6, nl + S.head * 0.5, seg), M(col.body), J.neck, 0, J.neckVec[1] / 2, J.neckVec[2] / 2);
      nm.rotation.x = Math.PI / 2 - na;
    }
    J.headPivot = grp(J.neck, 0, J.neckVec[1] + S.head * 0.25, J.neckVec[2] + S.head * 0.35);
    buildHead(J.headPivot);
    J.tailPivot = grp(J.torso, 0, r * 0.6, D / 2 - S.len * 0.46);
    buildTail(J.tailPivot);
    if (S.extras.includes('mane')) for (let i = 0; i < 6; i++) {
      const t = i / 5, m = add(new TH.BoxGeometry(S.head * 0.18, S.head * 0.55, nl / 5.5), M(col.mane), J.neck, 0, J.neckVec[1] * t + S.head * 0.42, J.neckVec[2] * t - S.head * 0.12);
      m.rotation.x = -na + Math.PI / 2 - 0.2;
    }
    if (S.extras.includes('wool')) for (let i = 0; i < 10; i++) {
      const a = i / 10 * TAU, zz = (hash(i, 3) - 0.5) * S.len * 0.7;
      sph(r * 0.42, J.torso, col.body, Math.cos(a) * r * w * 0.75, r * 0.35 + Math.sin(a) * r * 0.72 + r * 0.1, D / 2 + zz, [1, 0.85, 1]);
    }
    if (S.extras.includes('shell')) {
      const st = texMat(HAS_DOM && !plainOnly ? paintShell(Math.max(32, texPx >> 1), col) : null, col.shell);
      const sh = add(new THREE.SphereGeometry(r * 1.7, seg, Math.max(3, Math.round(vseg * 0.6)), 0, TAU, 0, Math.PI * 0.5), st.m, J.torso, 0, r * 0.1, D / 2);
      sh.scale.set(w * 0.95, 0.9, S.len / (r * 3.2));
      const rimM = add(new TH.TorusGeometry(r * 1.7, r * 0.12, 4, Math.max(8, seg)), M(shade(col.shell, 0.7)), J.torso, 0, r * 0.12, D / 2);
      rimM.rotation.x = Math.PI / 2; rimM.scale.set(w * 0.95, S.len / (r * 3.2), 1);
    }
    footprint[0] = r * w * 2.2; footprint[1] = S.len * 1.25;
    // góc ngồi: thân ngẩng tới khi chân trước chạm đất (chân ngắn → ngồi xin ăn), rút gọn theo loài
    J.sitT = clamp(Math.asin(clamp((L - 0.45 * r) / D, 0, 1)), 0.22, 0.75);
    // góc cúi cổ khi đánh hơi/ăn: mũi xuống gần đất trước mặt
    const hN = L + r * 0.55, Y = J.neckVec[1] + S.head * 0.25 - S.head * 0.3, Z = J.neckVec[2] + S.head * 0.35 + S.head * 0.7 + (S.snout[1] || 0);
    const R0 = Math.hypot(Y, Z), beta = Math.atan2(Y, Z);
    J.sniffP = clamp(beta + Math.asin(clamp((hN - 0.03) / R0, -1, 1)), 0.2, 1.35);
    J.reachOk = (hN - 0.03) / R0 <= 1;
  } else if (S.kind === 'biped') {
    buildBiped();
  } else if (S.kind === 'bird') {
    buildBird();
  } else {
    buildFish();
  }

  function buildBiped() {
    const human = S.human;
    const Ht = human ? S.height : S.leg + S.r * 2 + S.head * 2;
    const L = human ? Ht * (sp === 'kid' ? 0.4 : 0.46) : S.leg;
    const torsoL = human ? Ht * 0.3 : S.len, R = human ? Ht * (sp === 'kid' ? 0.11 : 0.1) : S.r;
    const legR = human ? R * 0.42 : S.legR;
    J.L = L; J.torsoL = torsoL;
    J.pelvis = grp(rig, 0, L, 0);
    J.torso = grp(J.pelvis);
    J.lean0 = human ? 0 : S.lean || 0;
    if (human) {
      const bodyCanvas = HAS_DOM && !plainOnly ? paintBody(32, 32, 'plain', { ...col, body: col.shirt }, seed) : null;
      const bm = texMat(bodyCanvas, col.shirt, true);
      regHeatMat(bm.m);
      const ch = add(latheBody(torsoL * 1.15, R, 0.95, 1.0, 3.2, facet ? 6 : 10, seg), bm.m, J.torso, 0, torsoL * 0.5, 0);
      ch.rotation.x = -Math.PI / 2; ch.scale.x = isEditorial && sp === 'adult' ? 1.08 : 1.15;
      J.body = ch;
      sph(R * 0.95, J.pelvis, col.pants, 0, 0, 0, [isEditorial && sp === 'adult' ? 1.08 : 1.15, 0.6, 0.9]);
    } else {
      const bodyCanvas = HAS_DOM && !plainOnly ? paintBody(Math.max(32, texPx >> 1), Math.max(32, texPx >> 1), S.pattern, col, seed) : null;
      const bm = texMat(bodyCanvas, col.body, true);
      regHeatMat(bm.m);
      const b = add(latheBody(torsoL, R, 1.05, 0.85, 2.4, facet ? 7 : 12, seg), bm.m, J.torso, 0, R * 0.2, torsoL * 0.12);
      b.scale.x = S.w || 1;
      J.body = b;
      if (S.extras.includes('spikes')) for (let i = 0; i < 5; i++) { const c = cone(R * 0.16, R * 0.35, J.torso, col.extra, 0, R * 1.08, torsoL * (0.32 - i * 0.16)); c.rotation.x = -0.25; }
    }
    // cổ + đầu
    const neckBase = human ? [0, torsoL * 1.02, 0] : [0, R * 0.7, torsoL * 0.48];
    J.neck = grp(J.torso, ...neckBase);
    const [nl, na] = human ? [S.head * 0.45, Math.PI / 2] : S.neck;
    J.neckVec = [0, Math.sin(na) * nl, Math.cos(na) * nl];
    if (!human) { const nm = add(new TH.CylinderGeometry(S.head * 0.55, R * 0.55, nl + S.head * 0.4, seg), M(col.body), J.neck, 0, J.neckVec[1] / 2, J.neckVec[2] / 2); nm.rotation.x = Math.PI / 2 - na; }
    else cyl(S.head * 0.32, S.head * 0.36, nl * 1.4, J.neck, col.skin, 0, nl * 0.5, 0);
    J.headPivot = grp(J.neck, 0, J.neckVec[1] + S.head * (human ? 0.75 : 0.2), J.neckVec[2] + S.head * (human ? 0 : 0.35));
    buildHead(J.headPivot);
    // tay
    J.arms = [];
    const armK = S.arms || 'arms';
    for (const k of [-1, 1]) {
      const sh = grp(J.torso, k * R * (human ? 1.2 : 0.7), human ? torsoL * 0.88 : R * 0.1, human ? 0 : torsoL * 0.4);
      const al = human ? Ht * 0.17 : R * 0.45, ar = human ? R * 0.3 : R * 0.12;
      add(new TH.CylinderGeometry(ar * 0.9, ar, al, Math.max(5, Math.round(seg * 0.6))), M(human ? col.shirt : col.body), sh, 0, -al / 2, 0);
      const el = grp(sh, 0, -al, 0);
      add(new TH.CylinderGeometry(ar * 0.75, ar * 0.85, al * 0.95, Math.max(5, Math.round(seg * 0.6))), M(human ? col.skin : col.body), el, 0, -al * 0.47, 0);
      sph(ar * 1.05, el, human ? col.skin : col.paw, 0, -al * 0.98, 0);
      J.arms.push({ sh, el, k });
    }
    J.armK = armK;
    // chân
    J.legs = [];
    for (const k of [-1, 1]) {
      const hip = grp(J.pelvis, k * R * (human ? 0.5 : 0.55), 0, 0);
      const up = L * 0.5;
      add(new TH.CylinderGeometry(legR * 0.9, legR * 1.05, up, Math.max(5, Math.round(seg * 0.7))), M(human ? col.pants : col.body), hip, 0, -up / 2, 0);
      const knee = grp(hip, 0, -up, 0);
      const lo = L - up - legR * 0.6;
      add(new TH.CylinderGeometry(legR * 0.75, legR * 0.88, lo, Math.max(5, Math.round(seg * 0.7))), M(human ? (S.long_pants ? col.pants : col.skin) : col.body), knee, 0, -lo / 2, 0);
      sph(legR * 1.15, knee, human ? col.shoes : col.paw, 0, -lo - legR * 0.1, legR * 0.6, [1, 0.6, 1.7]);
      J.legs.push({ hip, knee, k });
    }
    J.tailPivot = grp(J.pelvis, 0, R * 0.25, -R * 0.5);
    buildTail(J.tailPivot);
    footprint[0] = R * 2.6; footprint[1] = human ? R * 2.2 : torsoL * 1.6 + (S.tail[1] || 0);
    J.sitY = -(L - R * 0.55);
  }

  function buildBird() {
    const L = S.leg, R = S.r, up = Boolean(S.upright);
    J.L = L; J.lean0 = up ? -Math.PI / 2 + 0.12 : -0.35;
    J.pelvis = grp(rig, 0, L + (up ? R * 0.45 : R * 0.6), 0);
    J.torso = grp(J.pelvis);
    const bodyCanvas = HAS_DOM && !plainOnly ? paintBody(Math.max(32, texPx >> 1), Math.max(32, texPx >> 1), S.pattern, col, seed) : null;
    const bm = texMat(bodyCanvas, col.body, true);
    regHeatMat(bm.m);
    J.body = add(latheBody(S.len, R, up ? 1.0 : 0.85, up ? 0.7 : 1.0, 2.2, facet ? 7 : 12, seg), bm.m, J.torso, 0, 0, up ? S.len * 0.2 : S.len * 0.1);
    J.body.scale.x = S.w || 1;
    J.neck = grp(J.torso, 0, up ? 0 : R * 0.55, up ? S.len * 0.62 : S.len * 0.42);
    const [nl, na] = S.neck;
    J.neckVec = [0, Math.sin(na) * nl, Math.cos(na) * nl];
    if (nl > 0.03) { const nm = add(new TH.CylinderGeometry(S.head * 0.55, R * 0.45, nl + S.head * 0.3, seg), M(col.body), J.neck, 0, J.neckVec[1] / 2, J.neckVec[2] / 2); nm.rotation.x = Math.PI / 2 - na; }
    J.headPivot = grp(J.neck, 0, J.neckVec[1] + S.head * 0.3, J.neckVec[2] + S.head * 0.1);
    buildHead(J.headPivot);
    J.arms = [];
    for (const k of [-1, 1]) {                           // cánh / chân chèo
      const sh = grp(J.torso, k * R * (S.w || 1) * 0.85, R * 0.25, S.len * 0.18);
      const wl = S.wings === 'flipper' ? R * 1.6 : R * 1.5;
      const m = sph(wl * 0.5, sh, S.wings === 'flipper' ? col.body : shade(col.body, 0.88), 0, -wl * 0.15, -wl * 0.35, [0.16, 0.5, 1]);
      m.rotation.x = 0.3;
      J.arms.push({ sh, el: grp(sh), k });
    }
    J.armK = 'wings';
    J.legs = [];
    for (const k of [-1, 1]) {
      const hip = grp(rig, k * R * 0.42, L, 0);
      const knee = grp(hip, 0, -L * 0.5, 0);
      add(new TH.CylinderGeometry(S.legR, S.legR * 1.2, L * 0.5, 4), M(col.paw), hip, 0, -L * 0.25, 0);
      add(new TH.CylinderGeometry(S.legR, S.legR, L * 0.5, 4), M(col.paw), knee, 0, -L * 0.25, 0);
      for (let i = -1; i <= 1; i++) { const t = add(new TH.BoxGeometry(S.legR * 1.6, S.legR * 1.2, L * 0.32 + R * 0.25), M(col.paw), knee, i * S.legR * 2.2, -L * 0.5, R * 0.12); t.rotation.y = i * 0.45; }
      J.legs.push({ hip, knee, k });
    }
    J.tailPivot = grp(J.torso, 0, up ? 0 : R * 0.3, -S.len * (up ? 0.25 : 0.42));
    buildTail(J.tailPivot);
    footprint[0] = R * 2.4; footprint[1] = up ? R * 2.2 : S.len * 1.4;
  }

  function buildFish() {
    const R = S.r, L = S.len;
    J.torso = grp(rig, 0, R * 1.05, 0);
    const bodyCanvas = HAS_DOM && !plainOnly ? paintBody(Math.max(32, texPx >> 1), Math.max(32, texPx >> 1), S.pattern, col, seed) : null;
    const bm = texMat(bodyCanvas, col.body, true);
    regHeatMat(bm.m);
    J.body = add(latheBody(L, R, 0.55, 1.05, 2.0, facet ? 7 : 12, seg), bm.m, J.torso, 0, 0, -L * 0.08);
    J.body.scale.x = S.w;
    J.headPivot = grp(J.torso, 0, R * 0.05, L * 0.24);
    buildHead(J.headPivot);
    J.tail = [];
    let par = grp(J.torso, 0, 0, -L * 0.5); J.tailBase = par; J.tailUp = 0;
    for (let i = 0; i < 2; i++) { const sg = grp(par, 0, 0, i ? -L * 0.12 : 0); J.tail.push(sg); par = sg; }
    const fin = sph(R * 0.9, par, col.fin, 0, 0, -R * 0.75, [0.12, 1, 0.9]); fin.rotation.x = 0;
    const dor = sph(R * 0.55, J.torso, col.fin, 0, R * 0.95, -L * 0.05, [0.1, 0.8, 1.3]); dor.rotation.x = -0.3;
    J.fins = [];
    for (const k of [-1, 1]) { const fp = grp(J.torso, k * R * S.w * 0.95, -R * 0.25, L * 0.08); sph(R * 0.4, fp, col.fin, 0, 0, -R * 0.3, [0.1, 0.55, 1]); J.fins.push({ g: fp, k }); }
    footprint[0] = R * 1.6; footprint[1] = L * 1.2;
  }

  J.headBase = J.headPivot ? J.headPivot.position.clone() : null;

  // ---- hiệu ứng nhiệt gắn thân (Grounded Thermal Glow, set.heat 0..1 — tạo lười khi heat > 0 để không lệch Box3)
  const heatHex = wCol.heat_glow || (worldCfg.design_system && worldCfg.design_system.heat_glow) || '#E8523A';
  const heatCol = new THREE.Color(heatHex);
  const heatGlowSize = S.kind === 'biped' && S.human ? (J.torsoL || 0.5) * 1.4 : Math.max(S.r || 0.2, (S.len || 0.4) * 0.42) * 1.65;
  const heatGlowY = S.kind === 'biped' && S.human ? (J.torsoL || 0.5) * 0.52 : S.kind === 'quad' ? S.r * 0.35 : 0;
  const heatGlowZ = S.kind === 'quad' ? S.len * 0.34 : 0.04;
  let heatGlow = null;

  // ====================================================================================================================
  // bảng theo frame (tính MỘT LẦN từ keyframe): vị trí → tốc độ, hướng, dáng tự chọn, pha chân, pha vẫy đuôi
  // ====================================================================================================================
  const tl = { gait: [], speed: new Float32Array(N), head: new Float32Array(N), ph: new Float64Array(N), wag: new Float64Array(N),
    st: [], face: p.face || null };
  const legL = S.kind === 'quad' ? S.leg : S.kind === 'fish' ? S.len * 0.5 : (J.L || 0.3);
  const gaitAuto = (v, sc) => {
    const rel = v / Math.max(1e-3, legL * sc);
    if (S.kind === 'fish') return rel < 0.4 ? 'idle' : 'swim';
    if (rel < 0.35) return 'idle';
    const walkAs = S.walk || 'walk';
    if (walkAs === 'hop') return 'hop';
    return rel < 3.6 ? 'walk' : rel < 7 ? 'trot' : 'run';
  };
  const normGait = (gt) => {
    if (S.kind === 'fish' && (gt === 'walk' || gt === 'trot' || gt === 'run')) return 'swim';
    if (gt === 'swim' && S.kind !== 'fish') return 'walk';
    return GAITS.includes(gt) ? gt : 'idle';
  };
  const bind = (keys = [{ f: 0 }], poseFn = null) => {
    const pos = [], sc = [];
    for (let f = 0; f < N; f++) {
      const ps = poseFn ? poseFn(f) : { at: p.at || [0, 0, 0], sc: [1, 1, 1] };
      pos.push(ps.at); sc.push(Math.abs(ps.sc[0] || 1));
    }
    const sp0 = [];
    for (let f = 0; f < N; f++) {
      const a = pos[Math.max(0, f - 1)], b = pos[Math.min(N - 1, f + 1)], d = (f > 0 && f < N - 1) ? 2 : 1;
      sp0.push(Math.hypot(b[0] - a[0], b[2] - a[2]) * FPS / d);
    }
    // gait theo key (bậc), 'auto'/không ghi → theo tốc độ
    const gk = keys.filter((k) => k.gait !== undefined).map((k) => ({ f: k.f, v: k.gait })).sort((a, b) => a.f - b.f);
    const gaitAt = (f) => {
      let v = p.gait || 'auto';
      for (const k of gk) if (k.f <= f + 1e-6) v = k.v;
      return v === 'auto' ? gaitAuto(tl.speed[f], sc[f]) : normGait(v);
    };
    let firstH = null;
    for (let f = 0; f < N; f++) {
      tl.speed[f] = (sp0[Math.max(0, f - 1)] + sp0[f] + sp0[Math.min(N - 1, f + 1)]) / 3;
      if (firstH === null && tl.speed[f] > 0.03) { const a = pos[Math.max(0, f - 1)], b = pos[Math.min(N - 1, f + 1)]; firstH = Math.atan2(b[0] - a[0], b[2] - a[2]); }
    }
    const hasYaw = keys.some((k) => Array.isArray(k.rot) && Math.abs(k.rot[1] || 0) > 1e-6);
    const facePath = (tl.face || (hasYaw ? 'fixed' : 'path')) === 'path' && firstH !== null;
    let h = firstH ?? 0;
    for (let f = 0; f < N; f++) {
      if (facePath && tl.speed[f] > 0.03) {
        const a = pos[Math.max(0, f - 1)], b = pos[Math.min(N - 1, f + 1)];
        h += wrapA(Math.atan2(b[0] - a[0], b[2] - a[2]) - h) * (f === 0 ? 1 : 0.22);
      }
      tl.head[f] = facePath ? h : 0;
    }
    // trạng thái pha trộn dáng: A (hiện tại, bắt đầu fa) ← B (trước, fb), trọng số theo thời gian từ lúc đổi
    let A = gaitAt(0), fa = 0, Bg = A, fb = 0, sw = -999;
    let ph = 0, wph = 0;
    const blendF = Math.round(FPS * 0.28);
    for (let f = 0; f < N; f++) {
      const gNow = gaitAt(f);
      if (gNow !== A) { Bg = A; fb = fa; A = gNow; fa = f; sw = f; }
      const w = smooth((f - sw) / blendF);
      tl.st.push({ A, fa, B: Bg, fb, w });
      const rate = (gg) => {
        const cy = CYCLIC[gg];
        if (!cy) return 0;
        const v = tl.speed[f], stride = cy[0] * legL * sc[f];
        return v > 0.03 ? v / Math.max(1e-3, stride) : cy[1] * (S.speed || 1) / Math.sqrt(Math.max(0.3, sc[f] * legL / 0.25));
      };
      ph += (rate(A) * w + rate(Bg) * (1 - w)) / FPS;
      const wa = WAG[A] || WAG.idle, wb = WAG[Bg] || WAG.idle;
      wph += (wa[1] * w + wb[1] * (1 - w)) / FPS;
      tl.ph[f] = ph; tl.wag[f] = wph;
    }
    tl.bound = true;
  };

  // ====================================================================================================================
  // dáng (pose) theo kind — số thuần, pha trộn tuyến tính
  // ====================================================================================================================
  const Z4 = () => [[0, 0], [0, 0], [0, 0], [0, 0]];
  const baseQ = () => ({ y: 0, pitch: 0, roll: 0, yaw: 0, x: 0, br: 0, nP: 0, nY: 0, hP: 0, hY: 0, hR: 0, legs: Z4(), tailUp: J.tailUp || 0,
    wagA: 0, jaw: 0, tw: 0, earF: 0, sleep: 0, arms: [[0, 0, 0], [0, 0, 0]], fin: 0, flap: 0 });
  const legCycle = (phase, A, K) => [A * Math.sin(TAU * phase), K * Math.max(0, Math.cos(TAU * phase))];
  const jumpCurve = (s) => {             // s 0..1 → {y 0..1 (cao), crouch 0..1, air 0..1, land 0..1}
    if (s < 0.22) return { y: 0, c: Math.sin(s / 0.22 * Math.PI / 2), air: 0, land: 0 };
    if (s < 0.78) { const u = (s - 0.22) / 0.56; return { y: 4 * u * (1 - u), c: 0, air: u, land: 0 }; }
    if (s < 1) return { y: 0, c: 0, air: 0, land: Math.sin((s - 0.78) / 0.22 * Math.PI) };
    return { y: 0, c: 0, air: 0, land: 0 };
  };

  function poseQuad(gt, f, f0) {
    const P0 = baseQ(), t = f / FPS, ph = tl.ph[cf(f)], lt = Math.max(0, (f - f0) / FPS), L = S.leg;
    const br = Math.sin(TAU * 0.32 * t + seed);
    P0.br = br * 0.022;
    P0.wagA = (WAG[gt] || WAG.idle)[0];
    if (gt === 'idle' || gt === 'wag') {
      P0.nY = 0.16 * Math.sin(TAU * 0.09 * t + seed) ; P0.nP = 0.05 * Math.sin(TAU * 0.13 * t);
      if (gt === 'wag') { P0.yaw = 0.07 * Math.sin(TAU * 3.6 * t); P0.hR = 0.12; P0.y = 0.01 * L * Math.abs(Math.sin(TAU * 1.8 * t)); }
    } else if (gt === 'walk' || gt === 'trot' || gt === 'run') {
      const W = { walk: [[0.25, 0.75, 0, 0.5], 0.42, 0.65, 0.035, 0.04], trot: [[0, 0.5, 0.5, 0], 0.55, 0.95, 0.07, 0.03], run: [[0, 0.1, 0.5, 0.6], 0.85, 1.1, 0.16, 0.12] }[gt];
      const [off, A, K, bob, pit] = W;
      P0.legs = off.map((o) => legCycle(ph + o, A, K));
      P0.y = gt === 'run' ? bob * L * Math.max(0, Math.sin(TAU * ph)) : bob * L * Math.abs(Math.cos(TAU * ph * 2));
      P0.pitch = pit * Math.sin(TAU * ph + (gt === 'run' ? 0 : 1));
      P0.nP = -0.06 * Math.sin(TAU * ph * 2) - (gt === 'run' ? 0.15 : 0);
      P0.earF = gt === 'run' ? 0.6 : gt === 'trot' ? 0.25 : 0;
      P0.br *= 0.3;
    } else if (gt === 'sniff' || gt === 'eat') {
      P0.nP = J.sniffP * (gt === 'eat' ? 1.05 : 0.95) + (J.reachOk ? 0 : 0.1);
      P0.pitch = J.reachOk ? 0.05 : 0.16;
      P0.legs = [[0.18, 0.25], [0.18, 0.25], [-0.05, 0.1], [-0.05, 0.1]];
      P0.nY = 0.2 * Math.sin(TAU * 0.4 * t + seed);
      P0.tw = gt === 'sniff' ? Math.sin(TAU * 7.5 * t) * (0.5 + 0.5 * Math.sin(TAU * 0.9 * t)) : 0;
      P0.jaw = gt === 'eat' ? (Math.sin(TAU * 2.6 * t) > 0.1 ? 1 : 0) : 0;
      if (gt === 'eat') P0.hP = 0.1 * Math.max(0, Math.sin(TAU * 2.6 * t));
      P0.tailUp += 0.2;
    } else if (gt === 'sit') {
      const th = J.sitT, hs = 0.45 * S.r;
      P0.pitch = -th; P0.y = hs - L;
      P0.legs = [[-th + 0.05, 0.1], [-th + 0.05, 0.1], [1.4 - th, 2.5], [1.4 - th, 2.5]];
      P0.nP = -th * 0.75 + 0.05 * Math.sin(TAU * 0.13 * t); P0.nY = 0.12 * Math.sin(TAU * 0.09 * t + seed);
      P0.tailUp = -0.4;
    } else if (gt === 'sleep') {
      P0.y = 0.62 * S.r - L; P0.sleep = 1;
      P0.legs = [[1.35, 0.5], [1.35, 0.5], [-1.2, -0.4], [-1.2, -0.4]];
      P0.nP = 0.55; P0.nY = 0.35; P0.hR = 0.25; P0.br = br * 0.035; P0.tailUp = -0.2;
      P0.legs = P0.legs.map(([a, k]) => [a, k]);
    } else if (gt === 'jump' || gt === 'hop') {
      const dur = gt === 'jump' ? 0.85 : 0.5, s = gt === 'jump' ? lt / dur : fract(lt / dur);
      const H = Math.max(0.9 * L, 0.32 * S.len) * (gt === 'hop' ? 0.55 : 1), jc = jumpCurve(s);
      P0.y = H * jc.y - 0.28 * L * jc.c - 0.12 * L * jc.land;
      P0.pitch = jc.air ? -0.25 * Math.cos(Math.PI * jc.air) : 0.08 * jc.c;
      const st = jc.air ? Math.sin(Math.PI * jc.air) : 0;
      P0.legs = [[0.25 * jc.c + 0.55 * st, 0.5 * jc.c + 0.2 * st], [0.25 * jc.c + 0.55 * st, 0.5 * jc.c + 0.2 * st],
        [-0.3 * jc.c - 0.6 * st, -0.2 * jc.c + 0.15], [-0.3 * jc.c - 0.6 * st, -0.2 * jc.c + 0.15]];
      P0.earF = st * 0.5; P0.nP = -0.15 * st;
    } else if (gt === 'fall') {
      const s = clamp(lt / 0.5), e = s < 1 ? 1 - Math.pow(1 - s, 2) : 1, bounce = s >= 1 ? 0 : Math.sin(s * Math.PI) * 0;
      P0.roll = e * Math.PI / 2 + 0.06 * Math.sin(Math.min(1, lt / 0.9) * Math.PI * 3) * (1 - clamp(lt - 0.5));
      const Hc = L + 0.35 * S.r;
      P0.y = (S.r * (S.w || 1)) * Math.sin(P0.roll) - Hc * (1 - Math.cos(P0.roll)) * 0 + bounce;
      P0.x = Hc * Math.sin(P0.roll) * 0.7;
      P0.legs = [[0.2, 0], [0.2, 0], [-0.2, 0], [-0.2, 0]].map(([a, k]) => [a + 0.15 * Math.sin(TAU * 3 * t), k]);
      P0.nP = -0.2; P0.tailUp = 0;
    }
    return P0;
  }

  function poseBiped(gt, f, f0) {
    const P0 = baseQ(), t = f / FPS, ph = tl.ph[cf(f)], lt = Math.max(0, (f - f0) / FPS), human = S.human, bird = S.kind === 'bird';
    const br = Math.sin(TAU * 0.3 * t + seed), L = J.L;
    P0.br = br * 0.02; P0.legs = [[0, 0], [0, 0]];
    P0.arms = [[0.05, 0.15, 0.08], [0.05, 0.15, 0.08]];
    P0.wagA = (WAG[gt] || WAG.idle)[0];
    P0.pitch = J.lean0 || 0;
    if (gt === 'idle') {
      P0.nY = 0.18 * Math.sin(TAU * 0.08 * t + seed); P0.nP = 0.04 * Math.sin(TAU * 0.12 * t);
      P0.arms = P0.arms.map(([a, e, o], i) => [a + 0.04 * Math.sin(TAU * 0.3 * t + i), e, o]);
    } else if (gt === 'walk' || gt === 'trot' || gt === 'run') {
      const W = { walk: [0.45, 0.7, 0.022, 0.04, 0.4, 0.3], trot: [0.62, 1.05, 0.03, 0.12, 0.65, 1.1], run: [0.85, 1.5, 0.05, 0.22, 0.85, 1.5] }[gt];
      const [A, K, bob, lean, armA, armE] = W;
      P0.legs = [legCycle(ph, A, K), legCycle(ph + 0.5, A, K)];
      P0.arms = [[-armA * Math.sin(TAU * ph) * (bird ? 0.2 : 1), armE, 0.1], [-armA * Math.sin(TAU * (ph + 0.5)) * (bird ? 0.2 : 1), armE, 0.1]];
      P0.y = bob * L * 4 * Math.abs(Math.cos(TAU * ph));
      P0.pitch += lean; P0.roll = S.wings === 'flipper' ? 0.16 * Math.sin(TAU * ph) : 0.03 * Math.sin(TAU * ph);
      P0.nP = -lean * 0.6 + (bird && !S.upright ? 0 : 0);
      if (bird && !S.upright) P0.hz = 0.35 * Math.sin(TAU * ph * 2);          // gà gật đầu khi đi
    } else if (gt === 'sniff' || gt === 'eat') {
      P0.pitch += human ? 0.35 : 0.25; P0.nP = human ? 0.35 : 0.6;
      if (bird) { P0.nP = 0.9 * Math.max(0, Math.sin(TAU * 1.6 * t)) + 0.3; }
      P0.arms = human ? [[-0.5, 0.7, 0.15], [-0.5, 0.7, 0.15]] : P0.arms;
      if (human && gt === 'eat') { P0.pitch -= 0.3; P0.nP = 0.1; P0.arms[1] = [1.3, 2.1 + 0.15 * Math.sin(TAU * 2 * t), 0.15]; }
      P0.jaw = gt === 'eat' ? (Math.sin(TAU * 2.6 * t) > 0.1 ? 1 : 0) : 0;
      P0.tw = gt === 'sniff' ? Math.sin(TAU * 7 * t) * 0.6 : 0;
    } else if (gt === 'sit') {
      P0.y = J.sitY ?? -(L * 0.85); P0.legs = [[1.45, 0.25], [1.45, 0.25]];
      P0.arms = [[0.45, 0.6, 0.25], [0.45, 0.6, 0.25]]; P0.pitch = (J.lean0 || 0) * 0.4 - 0.05;
    } else if (gt === 'jump' || gt === 'hop') {
      const dur = gt === 'jump' ? 0.8 : 0.5, s = gt === 'jump' ? lt / dur : fract(lt / dur), jc = jumpCurve(s);
      const H = L * (gt === 'hop' ? 0.35 : 0.7);
      P0.y = H * jc.y - 0.22 * L * jc.c - 0.1 * L * jc.land;
      const st = jc.air ? Math.sin(Math.PI * jc.air) : 0;
      P0.legs = [[0.5 * jc.c + 0.3 * st, 1.0 * jc.c + 0.4 * st], [0.5 * jc.c + 0.1 * st, 1.0 * jc.c + 0.6 * st]];
      P0.arms = [[-0.4 * jc.c + 2.6 * st, 0.2, 0.3], [-0.4 * jc.c + 2.6 * st, 0.2, 0.3]];
      P0.pitch += 0.25 * jc.c;
      if (bird) P0.flap = st;
    } else if (gt === 'wag') {                       // vẫy tay (người) / vỗ cánh (chim) / vẫy đuôi (khủng long)
      if (human) P0.arms[1] = [0.2, 0.6 + 0.45 * Math.sin(TAU * 2.4 * t), 2.5];
      else if (bird) P0.flap = 0.5 + 0.5 * Math.sin(TAU * 4 * t);
      P0.hR = 0.1; P0.nY = 0.1 * Math.sin(TAU * 0.5 * t);
    } else if (gt === 'sleep') {
      P0.sleep = 1; P0.br = br * 0.03;
      if (human) { P0.pitch = -Math.PI / 2; P0.y = 0.12 * S.height * 0.5 - L; P0.z = -L * 0.0; P0.arms = [[0.1, 0.1, 0.15], [0.1, 0.1, 0.15]]; }
      else { P0.y = -L * 0.75; P0.legs = [[1.2, 2.2], [1.2, 2.2]]; P0.nP = 0.5; P0.pitch = (J.lean0 || 0) * 0.5; }
    } else if (gt === 'fall') {
      const s = clamp(lt / 0.55), e = s * s;
      P0.pitch = lerp(J.lean0 || 0, -Math.PI / 2 * (human ? 1 : 0.9), e) + 0.05 * Math.sin(clamp((lt - 0.55) / 0.5) * Math.PI) ;
      P0.y = lerp(0, human ? 0.1 * S.height * 0.6 - L : -L * 0.6, e);
      P0.arms = [[2.4 * (1 - e) + 1.4 * e, 0.3, 0.6], [2.4 * (1 - e) + 1.4 * e, 0.3, 0.6]];
      P0.legs = [[0.5 * e, 0.2], [0.3 * e, 0.4]];
    }
    return P0;
  }

  function poseFish(gt, f, f0) {
    const P0 = baseQ(), t = f / FPS, ph = tl.ph[cf(f)], lt = Math.max(0, (f - f0) / FPS);
    P0.br = 0.015 * Math.sin(TAU * 0.6 * t);
    P0.y = 0.015 * Math.sin(TAU * 0.5 * t + seed);
    P0.wagA = gt === 'swim' ? 0.55 : 0.25; P0.fin = 0.4 * Math.sin(TAU * 2.2 * t);
    if (gt === 'swim') { P0.yaw = 0.1 * Math.sin(TAU * ph); P0.fin *= 1.4; }
    else if (gt === 'jump' || gt === 'hop') {
      const dur = gt === 'jump' ? 0.9 : 0.6, s = gt === 'jump' ? lt / dur : fract(lt / dur), jc = jumpCurve(s);
      P0.y += S.len * 1.2 * jc.y; P0.pitch = jc.air ? -0.9 * Math.cos(Math.PI * jc.air) : 0; P0.wagA = 0.8;
    } else if (gt === 'fall' || gt === 'sleep') {
      const s = clamp(lt / 0.4);
      P0.roll = Math.PI / 2 * (gt === 'fall' ? s : 0.9 * s); P0.y = -S.r * 0.4 * s; P0.sleep = gt === 'sleep' ? 1 : 0;
      P0.wagA = gt === 'fall' ? 0.7 * (1 - clamp(lt - 0.6)) : 0.05;
    } else if (gt === 'eat' || gt === 'sniff') { P0.jaw = Math.sin(TAU * 2.4 * t) > 0 ? 1 : 0; P0.pitch = 0.2; }
    return P0;
  }

  const cf = (f) => Math.max(0, Math.min(N - 1, Math.round(f)));
  const poseOf = (gt, f, f0) => (S.kind === 'quad' ? poseQuad : S.kind === 'fish' ? poseFish : poseBiped)(gt, f, f0);
  const mixP = (a, b, w) => {
    if (typeof a === 'number') return lerp(a, typeof b === 'number' ? b : a, w);
    if (Array.isArray(a)) return a.map((v, i) => mixP(v, b[i], w));
    if (a && typeof a === 'object') { const o = {}; for (const k of Object.keys(a)) o[k] = mixP(a[k], b[k] ?? a[k], w); for (const k of Object.keys(b)) if (!(k in o)) o[k] = b[k]; return o; }
    return w < 0.5 ? a : b;
  };
  const poseAt = (f) => {
    if (!tl.bound) bind();
    const st = tl.st[cf(f)], fa = Math.max(f, 0);
    const pa = poseOf(st.A, fa, st.fa);
    if (st.w >= 1 || st.A === st.B) return pa;
    return mixP(poseOf(st.B, fa, st.fb), pa, st.w);
  };

  // ====================================================================================================================
  // áp dáng + nhìn theo điểm + tai/đuôi trễ pha + mặt
  // ====================================================================================================================
  const cur = { expr: p.expr, look: p.look || null, heat: 0 };
  const applyHeat = (v) => {
    const h = clamp(Number(v) || 0, 0, 1);
    cur.heat = h;
    for (const entry of heatMats) {
      if (entry.m.color) entry.m.color.copy(entry.base).lerp(heatCol, h * 0.62);
      if (entry.m.emissive) {
        entry.m.emissive.copy(entry.baseEm).lerp(heatCol, h * 0.58);
        if ('emissiveIntensity' in entry.m) entry.m.emissiveIntensity = 1.0;
      }
    }
    if (h > 0.01 && !heatGlow && ctx.glow && J.torso) {
      heatGlow = ctx.glow(heatHex, heatGlowSize, J.torso, 0, heatGlowY, heatGlowZ, 0);
      if (heatGlow) heatGlow.userData.noFrame = true;
    }
    if (heatGlow) {
      heatGlow.visible = h > 0.01;
      const gs = h > 0.01 ? heatGlowSize * (0.65 + 0.35 * h) : 0.001;
      heatGlow.scale.set(gs, gs, 1);
      if (heatGlow.material) heatGlow.material.opacity = h * 0.34;
    }
  };
  if (p.heat !== undefined) applyHeat(p.heat);
  const v3 = new THREE.Vector3(), v4 = new THREE.Vector3(), qInv = new THREE.Quaternion();
  const apply = (P) => {
    rig.position.set(P.x || 0, P.y, P.z || 0); rig.rotation.set(0, P.yaw, P.roll);
    if (S.kind === 'quad') {
      J.torso.rotation.set(P.pitch, 0, 0);
      J.body.scale.set(S.w * (1 + P.br * 0.6), 1 + P.br, 1);
      J.legs.forEach((lg, i) => { lg.hip.rotation.set(-(P.legs[i][0] + P.pitch), 0, 0); lg.knee.rotation.set(P.legs[i][1], 0, 0); });
    } else if (S.kind === 'fish') {
      J.torso.rotation.set(P.pitch, 0, 0);
      (J.fins || []).forEach(({ g: fg, k }) => { fg.rotation.set(0, k * (0.5 + P.fin), 0); });
    } else {
      J.torso.rotation.set(P.pitch, 0, P.roll * 0.3);
      J.legs.forEach((lg, i) => { lg.hip.rotation.set(-(P.legs[i][0] + (S.kind === 'bird' ? 0 : 0)), 0, 0); lg.knee.rotation.set(P.legs[i][1], 0, 0); });
      if (S.kind === 'biped') J.legs.forEach((lg, i) => { lg.hip.rotation.x = -(P.legs[i][0]) - (P.pitch - (J.lean0 || 0)) * (P.sleep || Math.abs(P.pitch) > 1.2 ? 0 : 1); });
      (J.arms || []).forEach((am, i) => {
        const [a, e, o] = P.arms[i] || [0, 0, 0];
        if (J.armK === 'wings') { am.sh.rotation.set(0, 0, am.k * (0.1 + 1.3 * (P.flap || 0) * (0.5 + 0.5 * Math.sin(TAU * 8 * curT)))); return; }
        if (J.armK === 'tiny') { am.sh.rotation.set(-0.9 - a * 0.3, 0, am.k * 0.2); am.el.rotation.set(-1.2, 0, 0); return; }
        am.sh.rotation.set(-a, 0, am.k * o); am.el.rotation.set(-e, 0, 0);
      });
    }
    if (J.neck) J.neck.rotation.set(P.nP, P.nY, 0);
    if (J.headPivot) { J.headPivot.rotation.set(P.hP, P.hY, P.hR); if (J.headBase) J.headPivot.position.set(J.headBase.x, J.headBase.y, J.headBase.z + (P.hz || 0) * S.head); }
    if (J.snout) J.snout.scale.set(1 + P.tw * 0.06, 1 - P.tw * 0.05, 1 + P.tw * 0.04);
    if (J.jaw) J.jaw.rotation.x = 0.35 * Math.max(P.jaw, curOpen);
  };
  let curT = 0, curOpen = 0;
  const lookAt = (target, wGait) => {             // quay cổ + đầu về điểm (toạ độ thế giới), phần còn lại → con ngươi
    if (!target || !J.neck || !J.headPivot) return [0, 0];
    let res = [0, 0];
    for (let it = 0; it < 2; it++) {
      J.headPivot.updateWorldMatrix(true, false);
      J.headPivot.getWorldPosition(v3);
      v4.set(...target).sub(v3);
      J.neck.parent.getWorldQuaternion(qInv); qInv.invert(); v4.applyQuaternion(qInv);
      const yaw = Math.atan2(v4.x, v4.z), pit = Math.atan2(-v4.y, Math.hypot(v4.x, v4.z));
      const yC = clamp(yaw, -1.25, 1.25), pC = clamp(pit, -0.8, 1.35);
      J.neck.rotation.y = lerp(J.neck.rotation.y, yC * 0.6, wGait); J.headPivot.rotation.y = lerp(J.headPivot.rotation.y, yC * 0.4, wGait);
      J.neck.rotation.x = lerp(J.neck.rotation.x, pC * 0.65, wGait); J.headPivot.rotation.x = lerp(J.headPivot.rotation.x, pC * 0.35, wGait);
      res = [clamp((yaw - yC) / 0.5 + yaw * 0.25, -1, 1), clamp(pit * 0.6, -1, 1)];
    }
    return res;
  };
  const follow = (P, f) => {                       // tai + đuôi: tín hiệu trễ pha (follow-through), hàm thuần của frame
    const lag = poseAt(f - 3), lag2 = poseAt(f - 6);
    const dy = (P.y - lag.y) / Math.max(0.05, S.leg || 0.3), dn = P.nP - lag.nP, dyaw = P.nY - lag.nY;
    for (const e of J.ears || []) {
      if (e.kind === 'flop') e.g.rotation.set(clamp(-dn * 1.4 + dy * 1.2 - P.earF * 0.8, -1, 1), 0, e.k * clamp(0.15 + P.earF * 0.5 + dy * 0.6 - e.k * dyaw * 0.8, -0.3, 1.1));
      else if (e.kind === 'long') e.g.rotation.set(clamp(-dn * 0.8 + dy * 0.6 + P.earF * 0.9 + (P.sleep ? 0.9 : 0), -0.6, 1.4), 0, e.rz - e.k * dyaw * 0.4);
      else e.g.rotation.set(clamp(-dn * 0.3 + P.earF * 0.4, -0.4, 0.6), 0, e.rz - e.k * dyaw * 0.25);
    }
    if (J.tailBase) {
      const up = P.tailUp + (lag.y - lag2.y) / Math.max(0.05, S.leg || 0.3) * 1.5 - (P.pitch - lag.pitch) * 1.2;
      J.tailBase.rotation.set(-up, 0, 0);
      const wa = P.wagA, ph = tl.wag[cf(f)];
      J.tail.forEach((sg, i) => {
        const a = wa * Math.sin(TAU * ph - i * 0.85) * (J.tail.length > 1 ? 0.55 : 1);
        sg.rotation.y = a; if (i) sg.rotation.x = -0.06 * up;
      });
    }
  };
  const redrawFace = (expr, blink, look, jaw, sleep) => {
    if (!faceCanvas) return;
    const st = { expr, blink, look: [Math.round(look[0] * 4) / 4, Math.round(look[1] * 4) / 4], jaw: jaw > 0.5 ? 1 : 0, sleep: sleep > 0.5 };
    const key = `${st.expr}|${st.blink}|${st.look}|${st.jaw}|${st.sleep}`;
    if (key !== faceState.key) {
      faceState.key = key;
      const fc = paintFace(faceCanvas.width, F, st), g2 = faceCanvas.getContext('2d');
      g2.clearRect(0, 0, faceCanvas.width, faceCanvas.height); g2.drawImage(fc, 0, 0);
      if (faceState.tex) faceState.tex.needsUpdate = true;
      if (snoutCanvas && faceState.snoutTex) {
        const sc = paintSnout(snoutCanvas.width, { ...F, nostrils: S.snout[0] === 'disc' || S.snout[0] === 'flat' || sp === 'horse',
          whiskers: S.extras.includes('whiskers'), mouth: S.snout[0] === 'disc' ? false : undefined }, st);
        const g3 = snoutCanvas.getContext('2d'); g3.clearRect(0, 0, snoutCanvas.width, snoutCanvas.height); g3.drawImage(sc, 0, 0);
        faceState.snoutTex.needsUpdate = true;
      }
    }
  };

  const update = (f, env = {}) => {
    if (!tl.bound) bind();
    curT = f / FPS;
    turn.rotation.y = tl.head[cf(f)];
    const st = tl.st[cf(f)], P = poseAt(f);
    const gaitNow = st.w >= 0.5 ? st.A : st.B;
    const exprBase = cur.expr || GAIT_EXPR[gaitNow] || 'neutral';
    curOpen = exprBase === 'happy' || exprBase === 'shock' || exprBase === 'love' ? 1 : 0;
    apply(P);
    let look = null;                               // điểm nhìn: toạ độ như `at` của prop (y đo từ mặt set) hoặc camera
    if (cur.look === 'camera') look = env.cam ? env.cam.pos : null;
    else if (Array.isArray(cur.look) && cur.look.length === 3) look = [cur.look[0], cur.look[1] + (env.base || 0), cur.look[2]];
    let pupil = [0, 0];
    const sleepW = P.sleep;
    if (look && sleepW < 0.5 && gaitNow !== 'fall') pupil = lookAt(look, 1);
    follow(P, f);
    const blink = sleepW > 0.5 ? 1 : ctx.MO && ctx.MO.blinkAt ? ctx.MO.blinkAt(f, seed % 23 + 3) : 0;
    redrawFace(exprBase, blink, pupil, P.jaw, sleepW);
  };

  return {
    g, update, bind, species: sp, S, footprint,
    set: { expr: (v) => { cur.expr = v; }, look: (v) => { cur.look = v; }, heat: applyHeat },
    joints: J,
  };
}
