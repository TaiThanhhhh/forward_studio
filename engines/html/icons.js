import { CHANNEL_ALIASES, CHANNEL_ICONS, GROUPS } from './icons_channel.js';

// Thư viện đạo cụ của engine html — mỗi icon là danh sách primitive trong hệ đơn vị [-1,1] (y xuống dưới), mỗi mảnh có
// "vai màu" (ink | dim | hot | cold | accent | bg) thay vì màu cụ thể → look nào cũng tô được theo bảng màu của nó
// (tô phẳng, chỉ nét, neon, cắt giấy, nhãn dán…). Icon nhận {f, p, role}: f = frame (đã lượng tử theo look), p = trạng thái
// 0..1 (mực nước, nhiệt, độ nứt…). Thêm icon = thêm một hàm + (tuỳ chọn) từ khoá trong ALIASES; không sửa beat/look.
const C = (x, y, r, role, o = {}) => ({ k: 'circle', x, y, r, role, ...o });
const R = (x, y, w, h, rad, role, o = {}) => {                    // o.w = độ dày nét (không phải chiều rộng)
  const { w: sw, ...rest } = o; return { k: 'rect', x, y, w, h, rad, role, ...rest, ...(sw !== undefined ? { sw } : {}) };
};
const PG = (pts, role, o = {}) => ({ k: 'poly', pts, role, ...o });
const LN = (pts, role, o = {}) => ({ k: 'line', pts, role, ...o });
const ARC = (x, y, r, a0, a1, role, o = {}) => ({ k: 'arc', x, y, r, a0, a1, role, ...o });
const wave = (x0, x1, y, amp, n, ph) => Array.from({ length: n + 1 }, (_, i) => [x0 + (x1 - x0) * i / n, y + Math.sin(i / n * Math.PI * 2 * 1.5 + ph) * amp]);
const tear = (cx, cy, r, tip) => {                 // giọt/ngọn lửa: nửa tròn dưới + đỉnh nhọn
  const pts = [[cx, cy - tip]];
  for (let i = 0; i <= 16; i++) { const a = -Math.PI * 0.12 + i / 16 * Math.PI * 1.24; pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
  return pts;
};
const star = (cx, cy, r0, r1, n, rot = 0) => Array.from({ length: n * 2 }, (_, i) => { const a = rot + i / (n * 2) * Math.PI * 2, r = i % 2 ? r0 : r1; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; });

export const ICONS = {
  dot: ({ role }) => [C(0, 0, 0.72, role || 'ink')],
  ball: ({ role }) => [C(0, 0, 0.8, role || 'ink'), ARC(0, 0, 0.56, -2.5, -1.7, 'bg', { w: 0.9 })],
  glass: ({ p = 0.62, f = 0 }) => {                  // cốc thuỷ tinh: p = mực nước
    const top = 0.78 - 1.5 * p, ph = f * 0.12;
    const surf = wave(-0.62, 0.62, top, 0.03, 10, ph);
    return [PG([...surf, [0.56, 0.8], [-0.56, 0.8]], 'cold'),
            LN([[-0.74, -0.86], [-0.6, 0.86], [0.6, 0.86], [0.74, -0.86]], 'ink', { w: 1.2 })];
  },
  ice: ({ role }) => [PG([[-0.62, -0.3], [0, -0.65], [0.62, -0.3], [0, 0.05]], 'ink'),          // khối đá đẳng trục: mặt trên sáng
                      PG([[-0.62, -0.3], [0, 0.05], [0, 0.8], [-0.62, 0.45]], role || 'cold'),
                      PG([[0.62, -0.3], [0, 0.05], [0, 0.8], [0.62, 0.45]], 'dim'), LN([[-0.42, -0.08], [-0.42, 0.3]], 'bg', { w: 0.7 })],
  flame: ({ f = 0 }) => { const w = Math.sin(f * 0.5) * 0.06; return [PG(tear(w, 0.2, 0.62, 1.15), 'hot'), PG(tear(-w * 0.5, 0.42, 0.32, 0.62), 'accent')]; },
  drop: ({ role }) => [PG(tear(0, 0.22, 0.6, 1.05), role || 'cold')],
  thermo: ({ p = 0.5 }) => {                         // nhiệt kế: p = mức thuỷ ngân
    const h = 1.2 * Math.max(0.04, Math.min(1, p));
    return [R(-0.16, -0.95, 0.32, 1.5, 0.16, 'ink', { fill: false }), R(-0.07, 0.42 - h, 0.14, h + 0.1, 0.05, 'hot'),
            C(0, 0.62, 0.32, 'hot'), ...[0, 1, 2, 3].map((i) => LN([[0.26, -0.7 + i * 0.3], [0.44, -0.7 + i * 0.3]], 'dim', { w: 0.6 }))];
  },
  steam: ({ f = 0 }) => [-0.5, 0, 0.5].map((x, i) => LN(wave(-0.8, 0.8, 0, 0.16, 12, f * 0.18 + i * 1.7).map(([a, b]) => [x + b, -a]), 'dim', { w: 0.8 })),
  burst: ({ f = 0, role }) => [PG(star(0, 0, 0.42, 0.95, 12, f * 0.05), role || 'accent')],
  crack: ({ p = 1 }) => {                                              // khe nứt: nêm răng cưa thuôn dần + 2 nhánh
    const path = [[0.05, -0.95], [-0.12, -0.5], [0.16, -0.15], [-0.1, 0.25], [0.12, 0.6], [-0.02, 0.95]].slice(0, 2 + Math.round(4 * p));
    const n = path.length, wd = (i) => 0.11 * (1 - i / (n - 1)) + 0.012;
    const poly = [...path.map(([x, y], i) => [x - wd(i), y]), ...path.slice().reverse().map(([x, y], j) => [x + wd(n - 1 - j), y])];
    return [PG(poly, 'ink'), LN([[0.16, -0.15], [0.45, -0.05], [0.58, -0.22]], 'ink', { w: 0.7 }), LN([[-0.1, 0.25], [-0.4, 0.38]], 'ink', { w: 0.6 })];
  },
  bolt: () => [PG([[0.1, -0.95], [-0.5, 0.1], [-0.05, 0.1], [-0.22, 0.95], [0.5, -0.18], [0.04, -0.18]], 'accent')],
  magnet: () => [PG([[-0.7, -0.8], [-0.3, -0.8], [-0.3, 0.1], [0.3, 0.1], [0.3, -0.8], [0.7, -0.8], [0.7, 0.2], [0.4, 0.8], [-0.4, 0.8], [-0.7, 0.2]], 'hot'),
                 R(-0.7, -0.8, 0.4, 0.34, 0, 'ink'), R(0.3, -0.8, 0.4, 0.34, 0, 'ink')],
  rocket: ({ f = 0 }) => [PG(tear(0, 1.1 + Math.sin(f) * 0.05, 0.2, 0.5).map(([x, y]) => [x, 1.9 - y]), 'hot'),
                          PG([[0, -0.95], [0.34, -0.3], [0.34, 0.5], [-0.34, 0.5], [-0.34, -0.3]], 'ink'),
                          PG([[-0.34, 0.1], [-0.7, 0.62], [-0.34, 0.5]], 'accent'), PG([[0.34, 0.1], [0.7, 0.62], [0.34, 0.5]], 'accent'), C(0, -0.2, 0.15, 'cold')],
  planet: ({ role }) => [C(0, 0, 0.62, role || 'cold'), { k: 'arc', x: 0, y: 0, r: 1, rx: 0.98, ry: 0.26, a0: -0.25, a1: Math.PI + 0.25, role: 'ink', w: 0.8 }],
  atom: ({ f = 0 }) => [C(0, 0, 0.2, 'hot'), ...[0, 1, 2].map((i) => ({ k: 'poly', fill: false, role: 'ink', w: 0.6,
    pts: Array.from({ length: 36 }, (_, j) => { const a = j / 36 * Math.PI * 2, r = i * Math.PI / 3 + f * 0.01, x = Math.cos(a) * 0.92, y = Math.sin(a) * 0.32; return [x * Math.cos(r) - y * Math.sin(r), x * Math.sin(r) + y * Math.cos(r)]; }) }))],
  person: ({ role }) => [C(0, -0.68, 0.22, role || 'ink'), R(-0.24, -0.4, 0.48, 0.7, 0.2, role || 'ink'),
                         LN([[-0.14, 0.3], [-0.18, 0.95]], role || 'ink', { w: 2.4 }), LN([[0.14, 0.3], [0.18, 0.95]], role || 'ink', { w: 2.4 }),
                         LN([[-0.3, -0.3], [-0.52, 0.22]], role || 'ink', { w: 1.9 }), LN([[0.3, -0.3], [0.52, 0.22]], role || 'ink', { w: 1.9 })],
  clock: ({ f = 0 }) => [C(0, 0, 0.82, 'ink', { fill: false }), LN([[0, 0], [Math.sin(f * 0.2) * 0.6, -Math.cos(f * 0.2) * 0.6]], 'accent', { w: 0.9 }),
                         LN([[0, 0], [Math.sin(f * 0.017) * 0.4, -Math.cos(f * 0.017) * 0.4]], 'ink', { w: 1.1 })],
  weight: () => [PG([[-0.5, -0.3], [0.5, -0.3], [0.8, 0.85], [-0.8, 0.85]], 'ink'), C(0, -0.52, 0.24, 'ink', { fill: false })],
  cube: ({ role }) => [R(-0.7, -0.7, 1.4, 1.4, 0.08, role || 'ink')],
  sun: ({ f = 0 }) => [PG(star(0, 0, 0.62, 0.95, 14, f * 0.01), 'accent'), C(0, 0, 0.5, 'hot')],
  bulb: () => [C(0, -0.2, 0.6, 'accent'), R(-0.22, 0.36, 0.44, 0.4, 0.08, 'ink')],
  battery: ({ p = 0.7 }) => [R(-0.45, -0.8, 0.9, 1.6, 0.1, 'ink', { fill: false }), R(-0.16, -0.95, 0.32, 0.15, 0.04, 'ink'),
                             R(-0.33, 0.68 - 1.36 * p, 0.66, 1.36 * p, 0.05, 'accent')],
  snow: () => [0, 1, 2, 3, 4, 5].flatMap((i) => {                      // bông tuyết 6 cánh, mỗi cánh có nhánh chữ V
    const a = i * Math.PI / 3 - Math.PI / 2, ux = Math.cos(a), uy = Math.sin(a), at = (r, d) => [ux * r + Math.cos(a + d) * 0.24, uy * r + Math.sin(a + d) * 0.24];
    return [LN([[0, 0], [ux * 0.92, uy * 0.92]], 'cold', { w: 1.1 }), LN([at(0.5, 0.9), [ux * 0.5, uy * 0.5], at(0.5, -0.9)], 'cold', { w: 0.9 })];
  }),
  bubble: ({ f = 0 }) => [[-0.4, 0.4, 0.3], [0.3, 0, 0.42], [-0.1, -0.55, 0.22]].map(([x, y, r], i) => C(x, y + Math.sin(f * 0.1 + i) * 0.06, r, 'cold', { fill: false, w: 0.8 })),
  coin: () => [C(0, 0, 0.8, 'accent'), C(0, 0, 0.55, 'bg', { fill: false, w: 0.7 })],
  egg: ({ role }) => [{ k: 'circle', x: 0, y: 0.05, r: 1, rx: 0.6, ry: 0.82, role: role || 'ink' }],
  balloon: ({ role }) => [{ k: 'circle', x: 0, y: -0.25, r: 1, rx: 0.56, ry: 0.68, role: role || 'hot' }, LN([[0, 0.43], [0.08, 0.7], [-0.06, 0.95]], 'dim', { w: 0.6 })],
  arrow: ({ role }) => [LN([[-0.9, 0], [0.6, 0]], role || 'ink', { w: 1.4 }), PG([[0.95, 0], [0.5, -0.3], [0.5, 0.3]], role || 'ink')],
  // ---- vòng 7b: đồ vật đời thường, cơ thể, sinh vật, thiên nhiên, công nghệ, xe cộ (vẫn chỉ primitive + vai màu)
  phone: ({ role }) => [R(-0.46, -0.9, 0.92, 1.8, 0.16, role || 'ink'), R(-0.36, -0.72, 0.72, 1.32, 0.04, 'bg'),
                        R(-0.36, -0.72, 0.72, 0.5, 0.04, 'cold'), C(0, 0.78, 0.07, 'bg')],
  laptop: () => [R(-0.72, -0.62, 1.44, 0.98, 0.06, 'ink'), R(-0.62, -0.52, 1.24, 0.78, 0.02, 'cold'), PG([[-0.95, 0.42], [0.95, 0.42], [0.82, 0.62], [-0.82, 0.62]], 'dim')],
  car: ({ role }) => [PG([[-0.95, 0.25], [-0.85, -0.05], [-0.45, -0.1], [-0.25, -0.45], [0.35, -0.45], [0.6, -0.1], [0.92, -0.02], [0.95, 0.25]], role || 'hot'),
                      PG([[-0.18, -0.36], [0.3, -0.36], [0.46, -0.1], [-0.36, -0.1]], 'cold'), C(-0.55, 0.3, 0.22, 'ink'), C(0.55, 0.3, 0.22, 'ink')],
  plane: () => [{ k: 'circle', x: 0, y: 0, r: 1, rx: 0.95, ry: 0.16, role: 'ink' }, PG([[-0.1, 0], [0.25, -0.7], [0.4, -0.7], [0.25, 0]], 'dim'),
                PG([[-0.1, 0], [0.25, 0.7], [0.4, 0.7], [0.25, 0]], 'dim'), PG([[-0.8, 0], [-0.95, -0.4], [-0.8, -0.4], [-0.6, 0]], 'accent')],
  ship: () => [PG([[-0.95, 0.1], [0.95, 0.1], [0.65, 0.55], [-0.7, 0.55]], 'ink'), R(-0.4, -0.35, 0.7, 0.45, 0.04, 'dim'), R(-0.05, -0.75, 0.2, 0.4, 0.04, 'hot'),
               LN(wave(-0.95, 0.95, 0.72, 0.05, 12, 0), 'cold', { w: 0.8 })],
  train: () => [R(-0.9, -0.6, 1.8, 1.05, 0.12, 'ink'), R(-0.72, -0.42, 0.5, 0.36, 0.04, 'cold'), R(0.2, -0.42, 0.5, 0.36, 0.04, 'cold'),
                C(-0.5, 0.6, 0.18, 'dim'), C(0.5, 0.6, 0.18, 'dim')],
  bike: () => [C(-0.55, 0.3, 0.4, 'ink', { fill: false, w: 0.8 }), C(0.55, 0.3, 0.4, 'ink', { fill: false, w: 0.8 }),
               LN([[-0.55, 0.3], [-0.1, -0.3], [0.4, -0.3], [0.55, 0.3]], 'hot', { w: 1 }), LN([[-0.1, -0.3], [0.05, 0.3], [-0.55, 0.3]], 'hot', { w: 1 })],
  house: ({ role }) => [PG([[-0.8, -0.05], [0, -0.85], [0.8, -0.05]], 'hot'), R(-0.62, -0.05, 1.24, 0.9, 0.02, role || 'ink'), R(-0.16, 0.35, 0.32, 0.5, 0.02, 'bg'),
                        R(0.24, 0.1, 0.24, 0.22, 0.02, 'cold')],
  building: () => [R(-0.55, -0.95, 1.1, 1.9, 0.03, 'ink'), ...[0, 1, 2, 3, 4].flatMap((r) => [-1, 1].map((s) => R(s > 0 ? 0.1 : -0.38, -0.78 + r * 0.34, 0.28, 0.18, 0.02, (r + s) % 3 ? 'cold' : 'bg')))],
  tree: () => [R(-0.1, 0.2, 0.2, 0.75, 0.04, 'dim'), C(0, -0.25, 0.6, 'cold'), C(-0.35, 0.05, 0.38, 'cold'), C(0.38, 0.0, 0.4, 'cold')],
  mountain: () => [PG([[-0.95, 0.8], [-0.2, -0.75], [0.4, 0.8]], 'ink'), PG([[-0.1, 0.8], [0.45, -0.25], [0.95, 0.8]], 'dim'),
                   PG([[-0.2, -0.75], [-0.38, -0.38], [-0.02, -0.38]], 'cold')],
  volcano: ({ f = 0 }) => [PG([[-0.95, 0.85], [-0.25, -0.35], [0.25, -0.35], [0.95, 0.85]], 'ink'), PG(tear(Math.sin(f * 0.4) * 0.05, -0.55, 0.26, 0.6), 'hot'),
                           LN([[-0.18, -0.3], [-0.3, 0.2], [-0.22, 0.6]], 'hot', { w: 1.1 })],
  cloud: ({ role }) => [C(-0.42, 0.12, 0.36, role || 'ink'), C(0.05, -0.12, 0.48, role || 'ink'), C(0.48, 0.12, 0.34, role || 'ink'), R(-0.78, 0.1, 1.56, 0.36, 0.18, role || 'ink')],
  wave: ({ f = 0 }) => [LN(wave(-0.95, 0.95, -0.2, 0.22, 16, f * 0.15), 'cold', { w: 1.3 }), LN(wave(-0.95, 0.95, 0.25, 0.18, 16, f * 0.15 + 1.4), 'cold', { w: 1 }),
                        LN(wave(-0.95, 0.95, 0.65, 0.12, 16, f * 0.15 + 2.6), 'dim', { w: 0.8 })],
  tornado: ({ f = 0 }) => [0, 1, 2, 3, 4].map((i) => ({ k: 'circle', x: Math.sin(f * 0.15 + i) * 0.08 * i, y: -0.75 + i * 0.36, r: 1, rx: 0.85 - i * 0.16, ry: 0.12, role: 'dim', fill: false, w: 0.8 })),
  moon: () => [C(0, 0, 0.75, 'ink'), C(-0.25, -0.2, 0.15, 'dim'), C(0.25, 0.22, 0.11, 'dim'), C(0.18, -0.35, 0.08, 'dim')],
  star: ({ role }) => [PG(star(0, 0, 0.4, 0.95, 5, -Math.PI / 2), role || 'accent')],
  blackhole: ({ f = 0 }) => {                                           // tâm đen lớn + vành photon mảnh + đĩa bồi tụ mỏng cắt ngang phía trước
    const band = (ro, ri, ry0, ry1) => [...Array.from({ length: 19 }, (_, i) => { const a = i / 18 * Math.PI; return [Math.cos(a) * ro, Math.sin(a) * ry0]; }),
                                        ...Array.from({ length: 19 }, (_, i) => { const a = Math.PI - i / 18 * Math.PI; return [Math.cos(a) * ri, Math.sin(a) * ry1]; })];
    return [{ k: 'circle', x: 0, y: 0, r: 1, rx: 0.98, ry: 0.2, role: 'hot' }, ARC(0, 0, 0.62, Math.PI + 0.25, 2 * Math.PI - 0.25, 'hot', { w: 1.3 }),
            C(0, 0, 0.5, 'bg'), C(0, 0, 0.53, 'accent', { fill: false, w: 0.45 }), PG(band(0.98, 0.56, 0.2, 0.08), 'hot'),
            ARC(0, 0, 0.8, f * 0.05, f * 0.05 + 0.5, 'accent', { w: 0.45, rx: 0.86, ry: 0.15 })];
  },
  galaxy: ({ f = 0 }) => [0, 1].map((k) => ({ k: 'line', role: k ? 'cold' : 'accent', w: 1,
    pts: Array.from({ length: 30 }, (_, i) => { const a = i * 0.32 + k * Math.PI + f * 0.01, r = 0.08 + i * 0.03; return [Math.cos(a) * r, Math.sin(a) * r * 0.7]; }) })).concat([C(0, 0, 0.14, 'ink')]),
  satellite: () => [R(-0.22, -0.22, 0.44, 0.44, 0.04, 'ink'), R(-0.95, -0.15, 0.6, 0.3, 0.02, 'cold'), R(0.35, -0.15, 0.6, 0.3, 0.02, 'cold'),
                    LN([[0, -0.22], [0, -0.55]], 'dim', { w: 0.6 }), C(0, -0.6, 0.08, 'accent')],
  heart: ({ role }) => [PG(Array.from({ length: 40 }, (_, i) => { const t = i / 40 * Math.PI * 2; return [0.055 * 16 * Math.sin(t) ** 3, -0.055 * (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) - 0.05]; }), role || 'hot')],
  brain: ({ role }) => [...[[-0.48, -0.32, 0.36], [-0.05, -0.48, 0.38], [0.42, -0.34, 0.36], [-0.6, 0.12, 0.34], [0.6, 0.1, 0.34], [-0.2, 0.18, 0.42], [0.22, 0.16, 0.42]]
                          .map(([x, y, r]) => C(x, y, r, role || 'hot')), R(0.02, 0.4, 0.2, 0.42, 0.08, role || 'hot'),
                        LN([[-0.02, -0.82], [0.02, -0.4], [-0.04, 0.0], [0.0, 0.42]], 'bg', { w: 0.8 }),
                        LN([[-0.62, -0.25], [-0.38, -0.12], [-0.5, 0.1], [-0.28, 0.25]], 'bg', { w: 0.6 }),
                        LN([[0.62, -0.28], [0.38, -0.1], [0.52, 0.12], [0.3, 0.26]], 'bg', { w: 0.6 })],
  bone: () => [R(-0.6, -0.12, 1.2, 0.24, 0.1, 'ink'), C(-0.65, -0.15, 0.17, 'ink'), C(-0.65, 0.15, 0.17, 'ink'), C(0.65, -0.15, 0.17, 'ink'), C(0.65, 0.15, 0.17, 'ink')],
  eye: ({ f = 0 }) => [{ k: 'circle', x: 0, y: 0, r: 1, rx: 0.92, ry: 0.5, role: 'ink' }, C(Math.sin(f * 0.05) * 0.15, 0, 0.36, 'cold'), C(Math.sin(f * 0.05) * 0.15, 0, 0.16, 'bg')],
  hand: ({ role }) => [R(-0.42, -0.1, 0.84, 0.85, 0.3, role || 'ink'), ...[-0.32, -0.1, 0.12, 0.34].map((x, i) => R(x - 0.08, -0.75 + (i % 3) * 0.06, 0.18, 0.75, 0.09, role || 'ink')),
                       R(-0.72, -0.05, 0.4, 0.18, 0.09, role || 'ink')],
  tooth: () => [PG([[-0.6, -0.42], [-0.48, -0.72], [-0.18, -0.74], [0, -0.62], [0.18, -0.74], [0.48, -0.72], [0.6, -0.42], [0.55, 0.08],
                      [0.42, 0.82], [0.24, 0.85], [0.12, 0.3], [-0.12, 0.3], [-0.24, 0.85], [-0.42, 0.82], [-0.55, 0.08]], 'ink'),
                  LN([[-0.32, -0.5], [-0.22, -0.58]], 'bg', { w: 0.6 })],
  cell: ({ f = 0 }) => [{ k: 'circle', x: 0, y: 0, r: 1, rx: 0.9, ry: 0.72 + Math.sin(f * 0.08) * 0.03, role: 'cold' }, C(0.15, -0.05, 0.28, 'accent'),
                        C(-0.45, 0.25, 0.08, 'dim'), C(-0.3, -0.35, 0.06, 'dim'), C(0.5, 0.35, 0.07, 'dim')],
  virus: ({ f = 0 }) => [C(0, 0, 0.5, 'hot'), ...Array.from({ length: 10 }, (_, i) => { const a = i / 10 * Math.PI * 2 + f * 0.01; return C(Math.cos(a) * 0.72, Math.sin(a) * 0.72, 0.1, 'hot'); }),
                         ...Array.from({ length: 10 }, (_, i) => { const a = i / 10 * Math.PI * 2 + f * 0.01; return LN([[Math.cos(a) * 0.5, Math.sin(a) * 0.5], [Math.cos(a) * 0.65, Math.sin(a) * 0.65]], 'hot', { w: 0.6 }); })],
  dna: ({ f = 0 }) => { const pts = (ph) => Array.from({ length: 24 }, (_, i) => [Math.sin(i * 0.5 + f * 0.08 + ph) * 0.45, -0.95 + i * 0.083]);
    const a = pts(0), b = pts(Math.PI); return [LN(a, 'cold', { w: 1 }), LN(b, 'hot', { w: 1 }), ...a.filter((_, i) => i % 3 === 0).map((p, i) => LN([p, b[i * 3]], 'dim', { w: 0.5 }))]; },
  pill: () => [R(-0.8, -0.28, 1.6, 0.56, 0.28, 'ink'), R(0, -0.28, 0.8, 0.56, 0.28, 'hot'), R(0, -0.28, 0.3, 0.56, 0, 'hot')],
  fish: ({ role }) => [{ k: 'circle', x: -0.1, y: 0, r: 1, rx: 0.65, ry: 0.4, role: role || 'cold' }, PG([[0.45, 0], [0.92, -0.38], [0.92, 0.38]], role || 'cold'), C(-0.45, -0.08, 0.07, 'bg')],
  bird: ({ f = 0, role }) => { const flap = Math.sin(f * 0.45) * 0.35;  // thân + đầu + mỏ + cánh vỗ + đuôi
    return [PG([[-0.55, 0.05], [-0.95, -0.2], [-0.88, 0.2]], 'dim'), { k: 'circle', x: -0.05, y: 0.1, r: 1, rx: 0.55, ry: 0.32, rot: -0.15, role: role || 'ink' },
            C(0.45, -0.2, 0.22, role || 'ink'), PG([[0.62, -0.24], [0.92, -0.14], [0.62, -0.08]], 'accent'), C(0.5, -0.26, 0.05, 'bg'),
            { k: 'circle', x: -0.12, y: -0.08, r: 1, rx: 0.42, ry: 0.16, rot: -0.45 - flap, role: 'dim' },
            LN([[-0.05, 0.4], [-0.1, 0.62]], 'dim', { w: 0.6 }), LN([[0.12, 0.4], [0.1, 0.62]], 'dim', { w: 0.6 })]; },
  animal: ({ role }) => [{ k: 'circle', x: 0, y: -0.05, r: 1, rx: 0.62, ry: 0.36, role: role || 'ink' }, C(0.62, -0.35, 0.24, role || 'ink'),
                         ...[-0.42, -0.18, 0.2, 0.42].map((x) => R(x - 0.07, 0.15, 0.14, 0.6, 0.06, role || 'ink')), LN([[-0.6, -0.1], [-0.88, -0.38]], role || 'ink', { w: 0.8 })],
  insect: () => [{ k: 'circle', x: 0, y: 0.1, r: 1, rx: 0.34, ry: 0.5, role: 'accent' }, C(0, -0.5, 0.18, 'ink'),
                 { k: 'circle', x: -0.42, y: -0.1, r: 1, rx: 0.36, ry: 0.22, role: 'cold', fill: false, w: 0.6 }, { k: 'circle', x: 0.42, y: -0.1, r: 1, rx: 0.36, ry: 0.22, role: 'cold', fill: false, w: 0.6 },
                 LN([[-0.3, 0.05], [0.3, 0.05]], 'ink', { w: 0.6 }), LN([[-0.3, 0.3], [0.3, 0.3]], 'ink', { w: 0.6 })],
  plant: ({ role }) => [PG([[-0.42, 0.32], [0.42, 0.32], [0.32, 0.9], [-0.32, 0.9]], 'hot'), R(-0.48, 0.24, 0.96, 0.14, 0.04, 'hot'),
                        LN([[0, 0.25], [0, -0.75]], 'dim', { w: 1 }),
                        { k: 'circle', x: -0.32, y: -0.1, r: 1, rx: 0.34, ry: 0.13, rot: -0.55, role: role || 'cold' },
                        { k: 'circle', x: 0.32, y: -0.42, r: 1, rx: 0.34, ry: 0.13, rot: 0.55, role: role || 'cold' },
                        { k: 'circle', x: -0.12, y: -0.78, r: 1, rx: 0.24, ry: 0.11, rot: -1.1, role: role || 'cold' }],
  food: () => [{ k: 'arc', x: 0, y: 0.15, r: 0.85, a0: 0, a1: Math.PI, role: 'ink', w: 1.2 }, LN([[-0.85, 0.15], [0.85, 0.15]], 'ink', { w: 1.2 }),
               C(-0.3, -0.05, 0.22, 'hot'), C(0.15, -0.12, 0.25, 'accent'), C(0.45, 0.0, 0.16, 'cold')],
  bottle: ({ p = 0.6 }) => [R(-0.15, -0.95, 0.3, 0.3, 0.04, 'dim'), PG([[-0.15, -0.65], [0.15, -0.65], [0.38, -0.3], [0.38, 0.9], [-0.38, 0.9], [-0.38, -0.3]], 'ink', { fill: false, w: 1 }),
                            R(-0.34, 0.86 - 1.1 * p, 0.68, 1.1 * p, 0.03, 'cold')],
  can: () => [R(-0.45, -0.75, 0.9, 1.5, 0.12, 'hot'), R(-0.45, -0.25, 0.9, 0.35, 0, 'ink'), LN([[-0.3, -0.85], [0.3, -0.85]], 'dim', { w: 0.8 })],
  gear: ({ f = 0 }) => [PG(Array.from({ length: 32 }, (_, i) => { const a = i / 32 * Math.PI * 2 + f * 0.03, r = i % 4 < 2 ? 0.92 : 0.7; return [Math.cos(a) * r, Math.sin(a) * r]; }), 'dim'), C(0, 0, 0.28, 'bg')],
  robot: () => [R(-0.45, -0.85, 0.9, 0.7, 0.12, 'ink'), C(-0.18, -0.52, 0.1, 'cold'), C(0.18, -0.52, 0.1, 'cold'), R(-0.55, -0.05, 1.1, 0.95, 0.1, 'dim'),
                LN([[0, -0.85], [0, -1.0]], 'ink', { w: 0.7 }), C(0, -1.0, 0.07, 'accent'), C(0, 0.4, 0.14, 'hot')],
  chip: () => [R(-0.55, -0.55, 1.1, 1.1, 0.08, 'ink'), R(-0.3, -0.3, 0.6, 0.6, 0.04, 'cold'),
               ...[-0.35, 0, 0.35].flatMap((v) => [LN([[v, -0.55], [v, -0.85]], 'dim', { w: 0.6 }), LN([[v, 0.55], [v, 0.85]], 'dim', { w: 0.6 }), LN([[-0.55, v], [-0.85, v]], 'dim', { w: 0.6 }), LN([[0.55, v], [0.85, v]], 'dim', { w: 0.6 })])],
  wifi: () => [C(0, 0.55, 0.12, 'accent'), ARC(0, 0.55, 0.45, -2.4, -0.74, 'ink', { w: 1 }), ARC(0, 0.55, 0.8, -2.4, -0.74, 'ink', { w: 1 }), ARC(0, 0.55, 1.15, -2.4, -0.74, 'dim', { w: 1 })],
  diamond: () => [PG([[-0.75, -0.25], [-0.4, -0.65], [0.4, -0.65], [0.75, -0.25], [0, 0.8]], 'cold'), LN([[-0.75, -0.25], [0.75, -0.25]], 'bg', { w: 0.6 }),
                  LN([[-0.4, -0.65], [0, 0.8], [0.4, -0.65]], 'bg', { w: 0.5 })],
  crystal: () => [PG([[0, -0.95], [0.32, -0.45], [0.32, 0.6], [0, 0.9], [-0.32, 0.6], [-0.32, -0.45]], 'cold'), PG([[0.45, -0.3], [0.65, -0.05], [0.65, 0.6], [0.45, 0.75], [0.36, 0.6], [0.36, -0.05]], 'dim')],
  hammer: () => [R(-0.08, -0.35, 0.16, 1.25, 0.05, 'dim'), R(-0.6, -0.75, 1.2, 0.42, 0.08, 'ink')],
  spring: () => [LN(Array.from({ length: 50 }, (_, i) => [Math.sin(i * 0.75) * 0.45, -0.9 + i * 0.037]), 'dim', { w: 1 })],
  wheel: ({ f = 0 }) => [C(0, 0, 0.85, 'ink', { fill: false, w: 1.6 }), C(0, 0, 0.14, 'ink'),
                         ...[0, 1, 2, 3, 4, 5].map((i) => { const a = i / 6 * Math.PI * 2 + f * 0.08; return LN([[0, 0], [Math.cos(a) * 0.8, Math.sin(a) * 0.8]], 'dim', { w: 0.6 }); })],
  shield: () => [PG([[0, -0.9], [0.75, -0.6], [0.65, 0.2], [0, 0.9], [-0.65, 0.2], [-0.75, -0.6]], 'cold'), PG([[0, -0.6], [0.45, -0.42], [0.38, 0.12], [0, 0.6]], 'bg')],
  warning: () => [PG([[0, -0.9], [0.95, 0.8], [-0.95, 0.8]], 'accent'), R(-0.07, -0.35, 0.14, 0.7, 0.07, 'bg'), C(0, 0.55, 0.09, 'bg')],
  // ---- vòng 7c: phòng thí nghiệm, đo lường, Trái Đất, đời sống — và nhân vật nhà khoa học của kênh
  scientist: ({ f = 0 }) => { const look = Math.sin(f * 0.05) * 0.03;  // brand: đầu tròn, kính bảo hộ to tròng xanh, áo blouse
    return [PG([[-0.44, -0.02], [0.44, -0.02], [0.58, 0.92], [-0.58, 0.92]], 'ink'), LN([[-0.14, -0.02], [0, 0.32], [0.14, -0.02]], 'bg', { w: 0.7 }),
            LN([[0, 0.32], [0, 0.88]], 'bg', { w: 0.5 }), LN([[-0.44, 0.05], [-0.78, 0.5]], 'ink', { w: 1.8 }), LN([[0.44, 0.05], [0.78, 0.5]], 'ink', { w: 1.8 }),
            C(0, -0.46, 0.38, 'ink'), LN([[-0.38, -0.52], [0.38, -0.52]], 'dim', { w: 1 }),
            C(-0.16, -0.52, 0.15, 'cold'), C(0.16, -0.52, 0.15, 'cold'), C(-0.16 + look, -0.52, 0.05, 'bg'), C(0.16 + look, -0.52, 0.05, 'bg'),
            ARC(0, -0.3, 0.1, 0.4, Math.PI - 0.4, 'bg', { w: 0.6 })]; },
  flask: ({ p = 0.55, f = 0, role }) => {                             // bình tam giác: p = mực dung dịch, bọt sủi
    const hw = (y) => (y <= -0.35 ? 0.15 : 0.15 + (y + 0.35) / 1.1 * 0.5), yl = Math.max(-0.33, 0.72 - 1.05 * p);
    return [PG([[-hw(yl) + 0.04, yl], [hw(yl) - 0.04, yl], [0.6, 0.72], [-0.6, 0.72]], role || 'cold'),
            ...[0, 1, 2].map((i) => C(-0.2 + i * 0.2, 0.62 - ((f * 0.02 + i * 0.33) % 1) * Math.max(0.05, 0.6 - yl + 0.1), 0.05, 'ink')),
            LN([[-0.15, -0.9], [-0.15, -0.35], [-0.65, 0.75], [0.65, 0.75], [0.15, -0.35], [0.15, -0.9]], 'ink', { w: 1.1 }),
            LN([[-0.24, -0.9], [0.24, -0.9]], 'ink', { w: 1.1 })];
  },
  testtube: ({ p = 0.5, role }) => {                                  // ống nghiệm: p = mực dung dịch
    const yl = 0.55 - 1.2 * p, bottom = Array.from({ length: 9 }, (_, i) => { const a = i / 8 * Math.PI; return [Math.cos(a) * 0.22, 0.55 + Math.sin(a) * 0.22]; });
    return [PG([[0.2, yl], ...bottom, [-0.2, yl]], role || 'hot'),
            LN([[-0.22, -0.9], [-0.22, 0.55], ...bottom.slice().reverse(), [0.22, 0.55], [0.22, -0.9]].filter((_, i) => i !== 2), 'ink', { w: 1 }),
            LN([[-0.32, -0.9], [0.32, -0.9]], 'ink', { w: 1 })];
  },
  microscope: () => [R(-0.62, 0.72, 1.24, 0.2, 0.06, 'ink'), PG([[0.2, 0.72], [0.38, 0.72], [0.42, -0.2], [0.24, -0.2]], 'dim'),
                     R(-0.5, 0.22, 0.8, 0.1, 0.03, 'ink'), PG([[-0.36, -0.88], [-0.14, -0.92], [0.12, -0.02], [-0.1, 0.04]], 'ink'),
                     R(-0.08, 0.02, 0.14, 0.18, 0.03, 'cold'), R(-0.42, -0.98, 0.3, 0.12, 0.04, 'dim'), C(0.32, -0.25, 0.1, 'dim')],
  telescope: () => [PG([[-0.85, -0.2], [0.55, -0.72], [0.68, -0.4], [-0.75, 0.08]], 'ink'), PG([[0.55, -0.72], [0.72, -0.78], [0.86, -0.44], [0.68, -0.4]], 'cold'),
                    LN([[-0.05, -0.15], [-0.45, 0.88]], 'dim', { w: 1 }), LN([[-0.05, -0.15], [0.3, 0.88]], 'dim', { w: 1 }), LN([[-0.05, -0.15], [-0.05, 0.88]], 'dim', { w: 1 })],
  magnifier: () => [C(-0.15, -0.15, 0.52, 'cold'), C(-0.15, -0.15, 0.56, 'ink', { fill: false, w: 1.5 }), LN([[0.25, 0.25], [0.78, 0.78]], 'ink', { w: 2.6 }),
                    ARC(-0.15, -0.15, 0.36, -2.6, -1.7, 'bg', { w: 0.7 })],
  balance: ({ p = 0.5 }) => { const t = (p - 0.5) * 0.5, ly = -0.45 - Math.sin(t) * 0.55, ry = -0.45 + Math.sin(t) * 0.55;   // cân đĩa: p lệch
    return [R(-0.06, -0.55, 0.12, 1.3, 0.04, 'dim'), R(-0.45, 0.72, 0.9, 0.16, 0.05, 'ink'), LN([[-0.62, ly], [0.62, ry]], 'ink', { w: 1.2 }), C(0, -0.5, 0.08, 'accent'),
            LN([[-0.62, ly], [-0.8, ly + 0.45]], 'dim', { w: 0.5 }), LN([[-0.62, ly], [-0.44, ly + 0.45]], 'dim', { w: 0.5 }),
            LN([[0.62, ry], [0.44, ry + 0.45]], 'dim', { w: 0.5 }), LN([[0.62, ry], [0.8, ry + 0.45]], 'dim', { w: 0.5 }),
            { k: 'arc', x: -0.62, y: ly + 0.45, r: 0.24, a0: 0, a1: Math.PI, role: 'ink', w: 1.2 }, { k: 'arc', x: 0.62, y: ry + 0.45, r: 0.24, a0: 0, a1: Math.PI, role: 'ink', w: 1.2 }]; },
  ruler: () => [R(-0.92, -0.22, 1.84, 0.44, 0.04, 'accent'), ...Array.from({ length: 13 }, (_, i) => LN([[-0.8 + i * 0.133, -0.22], [-0.8 + i * 0.133, i % 2 ? -0.08 : 0.02]], 'bg', { w: 0.5 }))],
  earth: ({ f = 0 }) => { const sh = (f * 0.004) % 0.2;                 // Trái Đất: đại dương + lục địa trôi rất chậm
    return [C(0, 0, 0.85, 'cold'), PG([[-0.5 + sh, -0.55], [-0.15 + sh, -0.65], [-0.05 + sh, -0.3], [-0.3 + sh, -0.05], [-0.25 + sh, 0.35], [-0.45 + sh, 0.2], [-0.62 + sh, -0.2]], 'ink'),
            PG([[0.15 + sh, -0.2], [0.55, -0.35], [0.7, 0.05], [0.45, 0.45], [0.2 + sh, 0.6], [0.1 + sh, 0.2]], 'ink'),
            C(0, 0, 0.85, 'ink', { fill: false, w: 0.6 })]; },
  bed: () => [R(-0.9, 0.0, 1.8, 0.32, 0.06, 'cold'), R(-0.9, -0.45, 0.16, 1.05, 0.04, 'ink'), R(0.74, -0.15, 0.16, 0.75, 0.04, 'ink'),
              R(-0.68, -0.2, 0.42, 0.2, 0.1, 'ink'), R(-0.24, -0.16, 0.96, 0.18, 0.08, 'hot')],
  cup: ({ p = 0.7, f = 0 }) => [R(-0.5, -0.35, 0.82, 1.05, 0.12, 'ink'), ARC(0.36, 0.12, 0.24, -1.4, 1.4, 'ink', { w: 1.3 }),
                                { k: 'circle', x: -0.09, y: -0.35 + (1 - p) * 0.3, r: 1, rx: 0.37, ry: 0.09, role: 'hot' },
                                ...[-0.25, 0.05].map((x, i) => LN(wave(-0.95, -0.5, 0, 0.06, 6, f * 0.2 + i * 2).map(([a, b]) => [x + b, a]), 'dim', { w: 0.6 }))],
  hourglass: ({ p = 0.5, f = 0 }) => { const top = 1 - p, bot = p;      // đồng hồ cát: p = phần cát đã rơi
    return [R(-0.62, -0.92, 1.24, 0.14, 0.05, 'dim'), R(-0.62, 0.78, 1.24, 0.14, 0.05, 'dim'),
            PG([[-0.42 * top, -0.05 - 0.7 * top], [0.42 * top, -0.05 - 0.7 * top], [0, -0.05]], 'accent'),
            PG([[-0.45, 0.76], [0.45, 0.76], [0.45 * (1 - bot) * 0.6, 0.76 - 0.6 * bot]], 'accent'),
            LN([[0, -0.05], [0, 0.76 - 0.5 * bot]], 'accent', { w: 0.4, dash: [1, 1] }),
            LN([[-0.5, -0.78], [-0.08, -0.05], [-0.5, 0.78]], 'ink', { w: 1 }), LN([[0.5, -0.78], [0.08, -0.05], [0.5, 0.78]], 'ink', { w: 1 })]; },
  speaker: ({ f = 0 }) => [R(-0.85, -0.22, 0.3, 0.44, 0.04, 'ink'), PG([[-0.55, -0.22], [-0.1, -0.62], [-0.1, 0.62], [-0.55, 0.22]], 'ink'),
                           ...[0, 1, 2].map((i) => ARC(-0.1, 0, 0.32 + i * 0.26 + ((f * 0.02) % 0.26), -0.8, 0.8, i ? 'dim' : 'accent', { w: 1 }))],
  radiation: ({ f = 0 }) => [C(0, 0, 0.92, 'accent'), C(0, 0, 0.14, 'bg'),
                             ...[0, 1, 2].map((k) => { const c = -Math.PI / 2 + k * 2 * Math.PI / 3 + f * 0.01, n = 10;
                               const out = Array.from({ length: n + 1 }, (_, i) => { const a = c - 0.52 + i / n * 1.04; return [Math.cos(a) * 0.78, Math.sin(a) * 0.78]; });
                               const inn = Array.from({ length: n + 1 }, (_, i) => { const a = c + 0.52 - i / n * 1.04; return [Math.cos(a) * 0.24, Math.sin(a) * 0.24]; });
                               return PG([...out, ...inn], 'bg'); })],
  umbrella: () => [PG([...Array.from({ length: 17 }, (_, i) => { const a = Math.PI + i / 16 * Math.PI; return [Math.cos(a) * 0.9, -0.05 + Math.sin(a) * 0.75]; }),
                       ...Array.from({ length: 9 }, (_, i) => [0.9 - i * 0.225, -0.05 + (i % 2 ? -0.12 : 0)])], 'hot'),
                   LN([[0, -0.8], [0, 0.65]], 'ink', { w: 1 }), ARC(-0.14, 0.65, 0.14, 0, Math.PI, 'ink', { w: 1 })],
  chart: () => [LN([[-0.82, -0.85], [-0.82, 0.78], [0.88, 0.78]], 'ink', { w: 1 }), R(-0.62, 0.22, 0.32, 0.56, 0.03, 'cold'),
                R(-0.16, -0.12, 0.32, 0.9, 0.03, 'accent'), R(0.3, -0.62, 0.32, 1.4, 0.03, 'hot')],
  syringe: ({ p = 0.6 }) => [R(-0.62, -0.18, 1.0, 0.36, 0.05, 'ink', { fill: false, w: 0.9 }), R(-0.62 + 1.0 * (1 - p), -0.14, 1.0 * p - 0.03, 0.28, 0.03, 'cold'),
                             LN([[-0.62, 0], [-0.9, 0]], 'ink', { w: 1.2 }), LN([[-0.9, -0.22], [-0.9, 0.22]], 'ink', { w: 1.2 }),
                             LN([[0.38, 0], [0.92, 0]], 'dim', { w: 0.5 }), LN([[-0.3, -0.18], [-0.3, -0.06]], 'bg', { w: 0.4 }), LN([[0.0, -0.18], [0.0, -0.06]], 'bg', { w: 0.4 })],
  candle: ({ f = 0 }) => { const w = Math.sin(f * 0.6) * 0.05;
    return [R(-0.28, -0.1, 0.56, 1.0, 0.06, 'ink'), PG([[-0.28, -0.1], [-0.12, -0.1], [-0.16, 0.12]], 'dim'), LN([[0, -0.1], [0, -0.25]], 'dim', { w: 0.6 }),
            PG(tear(w, -0.42, 0.16, 0.4), 'hot'), PG(tear(w * 0.6, -0.36, 0.08, 0.2), 'accent')]; },
};

Object.assign(ICONS, CHANNEL_ICONS);
export { GROUPS };

/** Icon tự ghép do storyboard viết: {"parts": [{"k": "circle"|"rect"|"poly"|"line"|"arc", …, "role": "hot"}]} — toạ độ trong
 *  [-1,1] (y xuống dưới). Dùng khi không có icon sẵn phù hợp chủ đề. */
export function partsIcon(spec) {
  const ok = ['circle', 'rect', 'poly', 'line', 'arc'], out = [];
  for (const p of spec.parts || []) {
    if (!p || !ok.includes(p.k)) continue;
    const { holes, ...q } = p;
    out.push(q);
    for (const h of holes || []) out.push({ k: 'poly', pts: h, role: q.role, hole: true });   // lỗ (SVG nhập: chữ O, bánh răng…)
  }
  return out;
}

// Từ khoá (tiếng Anh, vì storyboard của kênh viết tiếng Anh) → icon. Tên icon dùng trực tiếp cũng được.
// Bộ theo các mảng của kênh (A–D, lab, thiên nhiên…) nằm ở icons_channel.js và được gộp vào đây.
const ALIASES = [
  [['steel ball', 'iron ball', 'metal ball', 'ball', 'sphere', 'marble', 'bearing', 'cannonball'], 'ball'],
  [['ice water', 'water', 'glass', 'bucket', 'tank', 'pool', 'liquid', 'oil', 'acid'], 'glass'],
  [['ice', 'frozen'], 'ice'], [['fire', 'flame', 'lava', 'torch', 'burn', 'heat'], 'flame'],
  [['drop', 'droplet'], 'drop'], [['thermometer', 'temperature'], 'thermo'], [['steam', 'vapor', 'vapour', 'gas'], 'steam'],
  [['explosion', 'explode', 'impact', 'bang', 'boom'], 'burst'], [['crack', 'shatter', 'break'], 'crack'],
  [['lightning', 'electric', 'volt', 'spark'], 'bolt'], [['magnet'], 'magnet'], [['rocket', 'missile', 'launch'], 'rocket'],
  [['planet', 'saturn', 'mars', 'jupiter', 'neptune'], 'planet'], [['atom', 'molecule', 'nucleus'], 'atom'],
  [['person', 'human', 'man', 'woman', 'you', 'people', 'body'], 'person'], [['clock', 'time', 'second', 'minute', 'timer'], 'clock'],
  [['weight', 'kilogram', 'ton', 'heavy', 'mass'], 'weight'], [['cube', 'box', 'block', 'brick'], 'cube'], [['sun'], 'sun'],
  [['bulb', 'light', 'idea'], 'bulb'], [['battery', 'charge'], 'battery'], [['snow', 'cold', 'freeze'], 'snow'],
  [['bubble', 'boil'], 'bubble'], [['coin', 'money', 'gold'], 'coin'], [['egg'], 'egg'], [['balloon'], 'balloon'],
  [['phone', 'smartphone', 'iphone', 'mobile'], 'phone'], [['laptop', 'computer', 'pc'], 'laptop'], [['car', 'truck', 'vehicle'], 'car'],
  [['plane', 'airplane', 'jet', 'aircraft'], 'plane'], [['ship', 'boat', 'submarine', 'titanic'], 'ship'], [['train', 'subway', 'metro'], 'train'],
  [['bike', 'bicycle'], 'bike'], [['house', 'home'], 'house'], [['building', 'skyscraper', 'tower', 'city'], 'building'],
  [['tree', 'forest', 'wood'], 'tree'], [['mountain', 'everest', 'hill'], 'mountain'], [['volcano', 'eruption', 'magma'], 'volcano'],
  [['cloud', 'sky'], 'cloud'], [['wave', 'ocean', 'sea', 'tsunami'], 'wave'], [['tornado', 'hurricane', 'storm'], 'tornado'],
  [['moon'], 'moon'], [['black hole', 'blackhole', 'singularity'], 'blackhole'], [['galaxy', 'milky way', 'universe'], 'galaxy'],
  [['satellite', 'station', 'iss'], 'satellite'], [['heart', 'blood', 'pulse'], 'heart'], [['brain', 'mind', 'neuron', 'memory', 'think'], 'brain'],
  [['bone', 'skeleton'], 'bone'], [['eye', 'vision', 'see'], 'eye'], [['hand', 'finger', 'touch'], 'hand'], [['tooth', 'teeth'], 'tooth'],
  [['cell', 'bacteria', 'microbe'], 'cell'], [['virus', 'germ', 'infection'], 'virus'], [['dna', 'gene', 'genetic'], 'dna'],
  [['pill', 'medicine', 'drug', 'vitamin'], 'pill'], [['fish'], 'fish'], [['bird', 'chicken', 'eagle', 'pigeon'], 'bird'],
  [['animal', 'dog', 'cat', 'horse', 'cow', 'mammal'], 'animal'], [['insect', 'bee', 'ant', 'fly', 'mosquito'], 'insect'],
  [['plant', 'flower', 'seed', 'leaf'], 'plant'], [['food', 'meal', 'pizza', 'bread', 'burger'], 'food'],
  [['bottle', 'soda', 'vinegar', 'coke'], 'bottle'], [['can', 'tin'], 'can'], [['gear', 'machine', 'engine', 'motor'], 'gear'],
  [['robot', 'android'], 'robot'], [['chip', 'processor', 'cpu', 'circuit'], 'chip'], [['wifi', 'signal', 'radio', 'internet'], 'wifi'],
  [['diamond', 'gem', 'jewel'], 'diamond'], [['crystal', 'salt', 'sugar', 'quartz'], 'crystal'], [['hammer', 'tool'], 'hammer'],
  [['spring', 'coil'], 'spring'], [['wheel', 'tire', 'tyre'], 'wheel'], [['shield', 'armor', 'protect'], 'shield'],
  [['warning', 'danger', 'toxic', 'poison', 'caution'], 'warning'], [['star'], 'star'],
  [['scientist', 'professor', 'researcher', 'chemist', 'physicist', 'inventor', 'mascot'], 'scientist'],
  [['flask', 'lab', 'laboratory', 'chemical', 'reaction', 'potion', 'experiment'], 'flask'], [['test tube', 'testtube', 'sample', 'vial'], 'testtube'],
  [['microscope', 'microscopic'], 'microscope'], [['telescope', 'observatory'], 'telescope'],
  [['magnifying glass', 'magnifier', 'search', 'detective', 'inspect', 'zoom in'], 'magnifier'],
  [['balance', 'scale', 'weigh', 'weighing'], 'balance'], [['ruler', 'measure', 'length', 'millimeter', 'centimeter', 'inch'], 'ruler'],
  [['earth', 'planet earth', 'world', 'globe'], 'earth'], [['bed', 'sleep', 'nap', 'mattress', 'asleep'], 'bed'],
  [['cup', 'mug', 'coffee', 'tea', 'hot chocolate'], 'cup'], [['hourglass', 'sand', 'countdown'], 'hourglass'],
  [['speaker', 'sound', 'noise', 'music', 'loud', 'volume', 'audio', 'scream'], 'speaker'],
  [['radiation', 'radioactive', 'nuclear', 'uranium', 'reactor'], 'radiation'], [['umbrella'], 'umbrella'],
  [['chart', 'graph', 'data', 'statistics', 'percent', 'growth'], 'chart'], [['syringe', 'needle', 'vaccine', 'injection'], 'syringe'],
  [['candle', 'wax'], 'candle'],
];
// Phẳng hoá + xếp từ khoá dài trước (cùng thuật toán với engines/html/__init__.py → icon_for).
const FLAT = [...ALIASES, ...CHANNEL_ALIASES].flatMap(([keys, id]) => keys.map((k) => [k, id])).sort((a, b) => b[0].length - a[0].length);
export function iconFor(name) {
  const s = String(name || '').toLowerCase().trim();
  if (ICONS[s]) return s;
  const padded = ` ${s} `;
  for (const [k, id] of FLAT) if (padded.includes(` ${k} `) || padded.includes(` ${k}s `)) return id;   // cụm dài trước:
  for (const [k, id] of FLAT) if (k.length >= 4 && s.includes(k)) return id;                     // chuỗi con: chỉ từ khoá ≥ 4 ký tự ("nope" ≠ "no")
  return 'dot';
}
export const ICON_NAMES = Object.keys(ICONS);
