// Look = "ngữ pháp phong cách" của engine html. Mỗi look gồm: token mặc định (palette, pen, type, motion, post — bị ghi đè bởi
// styles/<id>.json → html) và vài hàm vẽ đặc trưng (nền, tiêu đề, cột, nhãn, mũi tên, vòng nhấn, mặt đất).
// Beat (beats.js) chỉ gọi các hàm này qua c.K nên một beat chạy được với mọi look.
// Các look được viết lại cho nền đen 9:16 từ ngữ pháp của nguồn ghi trong docs/CREDITS.md (không chép mã/tài liệu nguồn).
const TAU = Math.PI * 2;
const D = {                                          // token mặc định chung
  palette: { bg: '#000000', ink: '#F2F2EE', a: '#FF5A36', b: '#5AC8FA' },
  roles: { hot: 'a', cold: 'b', accent: 'a' },
  pen: { fill: true, stroke: 0, line: 7, seg: 44, every: 2 },
  type: { weight: 800, upper: true, align: 'center', enter: 'mask', lh: 1.06, track: 0, monoUpper: true },
  motion: { ease: 'smooth', enter: 'pop', step: 1, creep: 0.025, stagger: 3 },
  post: { grain: 0.05, vignette: 0.25 },
};
const deep = (a, b) => { const o = { ...a }; for (const k of Object.keys(b || {})) o[k] = (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k])) ? deep(a[k] || {}, b[k]) : b[k]; return o; };

const base = {
  tokens: {},
  bg() {}, fg() {},
  /** Tiêu đề shot: h = {kicker, title, index:[i,n]} → trả về y đáy. */
  header(c, h, k) {
    let y = c.A.top + 46;
    if (h.kicker) { c.text(h.kicker, c.A.cx, y, { size: 34, font: 'mono', role: 'dim', k: c.clamp(k * 1.6), enter: 'type', weight: 600 }); y += 96; } else y += 60;
    if (h.title) { const b = c.text(h.title, c.A.cx, y + 50, { size: h.size || 112, k, maxW: 880 }); y = b.y1; }
    return y;
  },
  bar(c, x, y, w, h, role) { c.draw([{ k: 'rect', x: 0, y: -h, w, h, rad: 0, role }], { x, y, s: 1 }); },
  label(c, str, x, y, k, o = {}) { return c.text(str, x, y, { size: 50, k, maxW: 420, ...o }); },
  tag(c, str, x, y, k, role = 'accent') { return c.text(str, x, y, { size: 68, k, role, maxW: 820 }); },
  arrow(c, x0, y0, x1, y1, k, role = 'ink') {
    if (k <= 0) return;
    const e = c.EASE.out(k), xe = c.lerp(x0, x1, e), ye = c.lerp(y0, y1, e), a = Math.atan2(y1 - y0, x1 - x0), s = 22;
    c.draw([{ k: 'line', pts: [[x0, y0], [xe, ye]], role }, { k: 'poly', role, pts: [[xe + Math.cos(a) * s, ye + Math.sin(a) * s], [xe + Math.cos(a + 2.5) * s, ye + Math.sin(a + 2.5) * s], [xe + Math.cos(a - 2.5) * s, ye + Math.sin(a - 2.5) * s]] }], { s: 1 });
  },
  ring(c, x, y, r, k, role = 'accent') {             // vòng nhấn quanh vật
    if (k <= 0) return;
    c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0: -1.4, a1: -1.4 + TAU * 1.04 * c.EASE.out(k), role }], { x, y, s: r, seed: 5 });
  },
  ground(c, x, y, w) { c.draw([{ k: 'circle', x: 0, y: 0, r: 1, rx: w / 2, ry: w * 0.07, role: 'dim' }], { x, y, s: 1, alpha: 0.35, plain: true }); },
  halo() {},
};

// ---------- các look ----------
const shapesDrift = (c, n, roleA = 'dim') => {       // mảnh hình học trôi chậm ở nền
  for (let i = 0; i < n; i++) {
    const x = c.hash(i, 1) * c.W, y0 = c.hash(i, 2) * c.H, sp = 0.25 + c.hash(i, 3) * 0.5, y = ((y0 - c.f * sp) % c.H + c.H) % c.H;
    const s = 16 + c.hash(i, 4) * 44, kind = i % 4, rot = c.f * 0.004 * (i % 2 ? 1 : -1) + i;
    const pr = kind === 0 ? [{ k: 'circle', x: 0, y: 0, r: 1, role: roleA, fill: false }] : kind === 1 ? [{ k: 'line', pts: [[-1, 0], [1, 0]], role: roleA }, { k: 'line', pts: [[0, -1], [0, 1]], role: roleA }]
      : kind === 2 ? [{ k: 'rect', x: -1.4, y: -0.4, w: 2.8, h: 0.8, rad: 0.4, role: roleA }] : [{ k: 'poly', pts: [[0, -1], [0.9, 0.7], [-0.9, 0.7]], role: roleA }];
    c.draw(pr, { x, y, s, rot, alpha: 0.32, plain: true, lw: 0.6 });
  }
};

const flat = {
  tokens: { palette: { ink: '#FFF6E9', a: '#FF5A4E', b: '#4B5BFF', c: '#FFC62B' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            type: { weight: 800, upper: false, enter: 'pop' }, motion: { ease: 'bounce', enter: 'pop', stagger: 3 }, post: { grain: 0.03, vignette: 0.15 } },
  bg(c) { shapesDrift(c, 14); },
  tag(c, str, x, y, k, role = 'accent') {            // viên thuốc màu, chữ nền đen
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 64, k: 0, maxW: 800 }), w = b.x1 - b.x0 + 70, h = b.y1 - b.y0 + 34;
    c.enter(k, [x - w / 2, b.y0 - 17, w, h], () => c.draw([{ k: 'rect', x: -w / 2, y: b.y0 - 17 - y, w, h, rad: h / 2, role }], { x, y, s: 1 }));
    return c.text(str, x, y, { size: 64, k: c.clamp(k * 1.5 - 0.5), role: 'bg', maxW: 800, enter: 'pop' });
  },
};

const boil = {
  tokens: { palette: { ink: '#F3EAD7', a: '#FF4B33', b: '#FFD23F' }, roles: { hot: 'a', cold: 'ink', accent: 'b' },
            pen: { fill: false, stroke: 6, boil: 2.2, every: 2, tint: 0.9, wobLen: 40 }, type: { weight: 400, upper: true, enter: 'write', boil: 1.6, lh: 1.0 },
            motion: { ease: 'out', enter: 'draw', step: 2, creep: 0.03, lead: 14 }, post: { grain: 0.09, vignette: 0.3 } },
  bg(c) {                                            // dấu cel FX nhỏ "sôi" rải nền
    for (let i = 0; i < 16; i++) {
      const x = c.hash(i, 11) * c.W, y = c.hash(i, 12) * c.H, s = 10 + c.hash(i, 13) * 16;
      c.draw(i % 2 ? [{ k: 'line', pts: [[-1, 0], [1, 0]], role: 'dim' }, { k: 'line', pts: [[0, -1], [0, 1]], role: 'dim' }] : [{ k: 'arc', x: 0, y: 0, r: 1, a0: 0, a1: 4, role: 'dim' }], { x, y, s, seed: i, alpha: 0.5, lw: 0.5 });
    }
  },
  ground(c, x, y, w) { c.draw([{ k: 'line', pts: [[-w / 2, 0], [w / 2, 0]], role: 'ink' }], { x, y, s: 1, seed: 3 }); },
  tag(c, str, x, y, k, role = 'accent') {
    const b = c.text(str, x, y, { size: 64, k, role: 'ink', maxW: 800 });
    if (k >= 1) c.draw([{ k: 'line', pts: [[b.x0, b.y1 + 14], [b.x1, b.y1 + 8]], role, w: 1.3 }], { s: 1, seed: 9 });
    return b;
  },
};

const isoPt = (c, gx, gy, gz = 0) => [c.A.cx + (gx - gy) * 0.866, 1040 + (gx + gy) * 0.5 - gz];
const iso = {
  tokens: { palette: { ink: '#E9EDF5', a: '#FF8A65', b: '#5DE6B1', c: '#9B8CFF' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 0, slab: 14 }, type: { weight: 800, upper: true, enter: 'mask' },
            motion: { ease: 'bounce', enter: 'grow', creep: 0.0 }, post: { grain: 0.03, vignette: 0.3 } },
  bg(c) {                                            // sàn lưới đẳng trục, camera trượt song song (không xoay)
    const g = c.g, slide = c.f * 0.6;
    g.strokeStyle = c.col('dim'); g.globalAlpha = 0.55; g.lineWidth = 2; g.beginPath();
    for (let i = -14; i <= 14; i++) {
      const o = i * 120 + (slide % 120);
      let [x0, y0] = isoPt(c, o, -900), [x1, y1] = isoPt(c, o, 900); g.moveTo(x0, y0); g.lineTo(x1, y1);
      [x0, y0] = isoPt(c, -900, o); [x1, y1] = isoPt(c, 900, o); g.moveTo(x0, y0); g.lineTo(x1, y1);
    }
    g.stroke();
    const gr = g.createLinearGradient(0, 700, 0, 1500); gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.3, 'rgba(0,0,0,0)'); gr.addColorStop(0.8, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,1)');
    g.globalAlpha = 1; g.fillStyle = gr; g.fillRect(0, 0, c.W, c.H);
  },
  prism(c, x, y, w, h, role) {                       // lăng trụ đẳng trục: đáy tâm (x,y), cạnh w, cao h
    const a = w * 0.866, b = w * 0.5, top = c.col(role), g = c.g;
    const quad = (pts, colr) => { g.fillStyle = colr; g.beginPath(); pts.forEach((p, i) => (i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]))); g.closePath(); g.fill(); };
    quad([[x - a, y], [x, y + b], [x, y + b - h], [x - a, y - h]], c.shade(top, 0.38));
    quad([[x + a, y], [x, y + b], [x, y + b - h], [x + a, y - h]], c.shade(top, 0.62));
    quad([[x, y - b - h], [x + a, y - h], [x, y + b - h], [x - a, y - h]], top);
  },
  bar(c, x, y, w, h, role) { this.prism(c, x + w / 2, y - w * 0.25, w * 0.55, Math.max(2, h), role); },
  ground(c, x, y, w) { this.prism(c, x, y - 34, w * 0.44, 18, 'dim'); },
};

const hud = {
  tokens: { palette: { ink: '#00E5FF', a: '#FF6A00', b: '#B8FBFF' }, roles: { hot: 'a', cold: 'ink', accent: 'a' },
            pen: { fill: false, stroke: 3.5, glow: 14, tint: 0.16, cap: 'butt', join: 'miter' }, type: { weight: 700, upper: true, enter: 'type', glow: 12, track: 0.06 },
            motion: { ease: 'out', enter: 'lock', creep: 0.015 }, post: { grain: 0.06, scanlines: 0.22, vignette: 0.45 } },
  bg(c) {
    const g = c.g, cx = c.A.cx, cy = 880;
    g.strokeStyle = c.col('ink'); g.lineWidth = 1.5; g.globalAlpha = 0.13; g.beginPath();      // lưới lục giác
    const R = 46, hx = R * 1.732, hy = R * 1.5;
    for (let j = 0; j < 30; j++) for (let i = 0; i < 9; i++) {
      const x = i * hx + (j % 2 ? hx / 2 : 0), y = j * hy;
      for (let k = 0; k < 3; k++) { const a = Math.PI / 6 + k * Math.PI / 3; g.moveTo(x + Math.cos(a) * R, y + Math.sin(a) * R); g.lineTo(x + Math.cos(a + Math.PI / 3) * R, y + Math.sin(a + Math.PI / 3) * R); }
    }
    g.stroke();
    g.globalAlpha = 0.5;
    [[330, 0.004, 60], [396, -0.007, 24], [452, 0.002, 120]].forEach(([r, sp, n], ri) => {      // vòng xoay có vạch chia
      g.save(); g.translate(cx, cy); g.rotate(c.f * sp + ri); g.lineWidth = ri === 1 ? 3 : 1.5; g.beginPath(); g.arc(0, 0, r, 0.3, TAU - 0.9 - ri * 0.4); g.stroke();
      g.beginPath(); for (let i = 0; i < n; i++) { const a = i / n * TAU, l = i % 5 ? 8 : 18; g.moveTo(Math.cos(a) * (r + 8), Math.sin(a) * (r + 8)); g.lineTo(Math.cos(a) * (r + 8 + l), Math.sin(a) * (r + 8 + l)); }
      g.stroke(); g.restore();
    });
    const sw = c.f * 0.05;                                                                      // quét radar
    const cg = g.createConicGradient(sw, cx, cy); cg.addColorStop(0, 'rgba(0,229,255,0)'); cg.addColorStop(0.86, 'rgba(0,229,255,0)'); cg.addColorStop(1, 'rgba(0,229,255,0.16)');
    g.globalAlpha = 1; g.fillStyle = cg; g.beginPath(); g.arc(cx, cy, 452, 0, TAU); g.fill();
    g.font = '600 20px "StyleMono", monospace'; g.fillStyle = c.col('ink'); g.globalAlpha = 0.5; g.textAlign = 'left';   // cột số liệu nhảy
    for (let i = 0; i < 6; i++) {                     // nằm dưới vùng nhãn, sát đáy vùng an toàn
      const v = Math.floor(c.hash(i, Math.floor(c.f / 4)) * 9999).toString().padStart(4, '0');
      g.fillText(`${(i * 37 + 11).toString(16).toUpperCase().padStart(2, '0')}:${v}`, 70 + (i % 3) * 150, c.A.bottom - 30 + Math.floor(i / 3) * 26);
    }
  },
  fg(c) {                                            // 4 góc khung ngắm
    const g = c.g, m = 56, l = 70; g.strokeStyle = c.col('ink'); g.lineWidth = 3; g.globalAlpha = 0.8; g.beginPath();
    for (const [x, y, dx, dy] of [[m, c.A.top - 30, 1, 1], [c.W - m, c.A.top - 30, -1, 1], [m, c.A.bottom + 30, 1, -1], [c.W - m, c.A.bottom + 30, -1, -1]]) { g.moveTo(x + dx * l, y); g.lineTo(x, y); g.lineTo(x, y + dy * l); }
    g.stroke();
  },
  header(c, h, k) {
    let y = c.A.top + 50;
    if (h.kicker) { c.text('> ' + h.kicker, c.A.x0, y, { size: 32, font: 'mono', align: 'left', role: 'cold', k: c.clamp(k * 1.5), weight: 600 }); y += 40; }
    c.g.fillStyle = c.col('ink'); c.g.globalAlpha = 0.6; c.g.fillRect(c.A.x0, y, (c.A.x1 - c.A.x0) * c.EASE.out(k), 2); c.g.globalAlpha = 1; y += 96;
    if (h.title) { const b = c.text(h.title, c.A.cx, y + 10, { size: h.size || 84, k, maxW: 860 }); y = b.y1; }
    return y;
  },
  ring(c, x, y, r, k, role = 'accent') {             // ngoặc khoá mục tiêu co 1.4 → 1.0
    if (k <= 0) return;
    const s = c.lerp(1.4, 1, c.EASE.out(k)) * r, l = r * 0.36, pr = [];
    for (const [dx, dy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) pr.push({ k: 'line', role, pts: [[dx * s, dy * (s - l)], [dx * s, dy * s], [dx * (s - l), dy * s]] });
    c.draw(pr, { x, y, s: 1, alpha: c.clamp(k * 3) });
  },
  tag(c, str, x, y, k, role = 'accent') { return c.text(`[ ${str} ]`, x, y, { size: 54, k, role, maxW: 940, font: 'mono' }); },
  label(c, str, x, y, k, o = {}) { return c.text(str, x, y, { size: 36, k, maxW: 420, font: 'mono', weight: 600, ...o }); },
  ground() {},
};

const synth = {
  tokens: { palette: { ink: '#F6F0FF', a: '#FF2BD6', b: '#2BE8FF', c: '#FFC43D' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: false, stroke: 5, glow: 6, glow2: 30, tint: 0.2 }, type: { weight: 400, upper: true, enter: 'slam', chrome: true, glow: 10 },
            motion: { ease: 'out', enter: 'flicker', creep: 0.0 }, post: { grain: 0.07, scanlines: 0.2, vignette: 0.4 } },
  bg(c) {
    const g = c.g, hz = 1170, cx = c.A.cx;
    for (let i = 0; i < 70; i++) { g.fillStyle = c.col('ink'); g.globalAlpha = 0.25 + 0.5 * c.hash(i, Math.floor(c.f / 6)); g.fillRect(c.hash(i, 1) * c.W, c.hash(i, 2) * hz, 2, 2); }
    g.globalAlpha = 0.55;                              // mặt trời sọc, lặn dần sau chân trời
    const sr = 300, sy = hz - 150 + c.u * 30, gr = g.createLinearGradient(0, sy - sr, 0, sy + sr); gr.addColorStop(0, c.col('accent')); gr.addColorStop(1, c.col('hot'));
    g.save(); g.beginPath(); g.rect(0, 0, c.W, hz); g.clip(); g.fillStyle = gr; g.beginPath(); g.arc(cx, sy, sr, 0, TAU); g.fill();
    g.fillStyle = c.pal.bg; g.globalAlpha = 1; for (let i = 0; i < 7; i++) { const y = sy + 10 + i * 44 + (c.f * 0.4 % 44); g.fillRect(cx - sr, y, sr * 2, 6 + i * 4); }
    g.restore();
    g.strokeStyle = c.col('hot'); g.lineWidth = 2.5; g.shadowColor = c.col('hot'); g.shadowBlur = 12; g.globalAlpha = 0.85; g.beginPath();   // lưới phối cảnh lao về camera
    for (let i = -12; i <= 12; i++) { g.moveTo(cx + i * 40, hz); g.lineTo(cx + i * 420, c.H); }
    const ph = (c.f * 0.035) % 1;
    for (let j = 0; j < 12; j++) { const d = (j + ph) / 12, y = hz + (c.H - hz) * d * d; g.moveTo(0, y); g.lineTo(c.W, y); }
    g.moveTo(0, hz); g.lineTo(c.W, hz); g.stroke();
  },
  fg(c) {                                            // dải nhiễu tracking VHS chạy dọc
    const g = c.g, y = (c.f * 9) % (c.H + 300) - 150; g.globalAlpha = 0.07; g.fillStyle = '#ffffff'; g.fillRect(0, y, c.W, 46);
  },
  ground() {},
};

const sticker = {
  tokens: { palette: { ink: '#EEF2F5', a: '#FF5A36', b: '#7FB7D9' }, roles: { hot: 'a', cold: 'b', accent: 'a' },
            pen: { fill: true, stroke: 0, sticker: 9 }, type: { weight: 700, upper: false, enter: 'mask' },
            motion: { ease: 'smooth', enter: 'pop', creep: 0.05 }, post: { grain: 0.03, vignette: 0.3 } },
  bg(c) {                                            // canvas lớn chấm lưới, camera lia dài
    const g = c.g, ox = (c.f * 0.9) % 60, oy = (c.f * 0.5) % 60; g.fillStyle = c.col('dim'); g.globalAlpha = 0.45;
    for (let y = -60; y < c.H + 60; y += 60) for (let x = -60; x < c.W + 60; x += 60) g.fillRect(x - ox, y - oy, 3, 3);
  },
  label(c, str, x, y, k, o = {}) { return c.text(str, x, y, { size: 42, k, maxW: 420, weight: 700, ...o }); },
  tag(c, str, x, y, k, role = 'accent') {
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 54, k: 0, maxW: 780 }), w = b.x1 - b.x0 + 64, h = b.y1 - b.y0 + 30;
    c.enter(k, [x - w / 2, b.y0 - 15, w, h], () => c.draw([{ k: 'rect', x: -w / 2, y: b.y0 - 15 - y, w, h, rad: 14, role: 'ink' }], { x, y, s: 1, plain: true }));
    return c.text(str, x, y, { size: 54, k: c.clamp(k * 1.5 - 0.5), role: 'bg', maxW: 780 });
  },
};

const swiss = {
  tokens: { palette: { ink: '#F2F0EA', a: '#E30613' }, roles: { hot: 'a', cold: 'ink', accent: 'a' },
            pen: { fill: true, stroke: 0, line: 6, cap: 'butt', join: 'miter' }, type: { weight: 800, upper: false, align: 'left', enter: 'mask', track: -0.02, lh: 0.98 },
            motion: { ease: 'snap', enter: 'wipe', creep: 0.03 }, post: { grain: 0.025, vignette: 0 } },   // hạt rất nhẹ: quy tắc kênh 'không đứng hình' thắng 'không grain'
  bg(c) {                                            // lưới 4 cột + hàng chú thích mono có kẻ 1px
    const g = c.g, x0 = c.A.x0, x1 = c.A.x1, cw = (x1 - x0) / 4; g.strokeStyle = c.col('dim'); g.globalAlpha = 0.3; g.lineWidth = 1; g.beginPath();
    for (let i = 0; i <= 4; i++) { g.moveTo(x0 + i * cw, c.A.top - 40); g.lineTo(x0 + i * cw, c.A.bottom + 30); }
    g.stroke(); g.globalAlpha = 0.8; g.fillStyle = c.col('ink'); g.fillRect(x0, c.A.top - 40, x1 - x0, 2);
    g.font = '600 22px "StyleMono", monospace'; g.textAlign = 'left'; g.fillStyle = c.col('dim'); g.globalAlpha = 1;
    g.fillText(`f ${String(c.f).padStart(3, '0')} / ${c.N}`, x0 + cw * 3 + 8, c.A.bottom + 24);
    g.fillRect(x0 + cw * 3, c.A.bottom - 2, cw * c.u, 2);                                      // thanh đếm chạy tuyến tính
  },
  header(c, h, k) {
    let y = c.A.top + 6;
    if (h.kicker) c.text(h.kicker, c.A.x0 + 8, y, { size: 26, font: 'mono', role: 'dim', k: c.clamp(k * 2), weight: 600, enter: 'wipe', align: 'left' });
    if (h.index) c.text(String(h.index[0]).padStart(2, '0'), c.A.x0 - 6, y + 250, { size: 290, weight: 900, role: 'accent', k, track: -0.05, quiet: true });
    y += h.index ? 330 : 120;
    if (h.title) { const b = c.text(h.title, c.A.x0, y + 20, { size: h.size || 92, k, maxW: 820 }); y = b.y1; }
    return y;
  },
  tag(c, str, x, y, k, role = 'accent') {            // in chồng: chữ đen trên khối màu tín hiệu
    if (k <= 0) return null;
    const b = c.text(str, c.A.x0 + 26, y, { size: 60, k: 0, maxW: 760 }), w = (b.x1 - b.x0 + 52) * c.EASE.snap(k), h = b.y1 - b.y0 + 28;
    c.g.fillStyle = c.col(role); c.g.fillRect(c.A.x0, b.y0 - 14, w, h);
    return c.text(str, c.A.x0 + 26, y, { size: 60, k: c.clamp(k * 2 - 1), role: 'bg', maxW: 760 });
  },
  label(c, str, x, y, k, o = {}) { return c.text(str, x, y, { size: 38, k, maxW: 400, weight: 600, align: 'left', ...o }); },
  arrow(c, x0, y0, x1, y1, k, role = 'ink') { if (k > 0) { const e = c.EASE.linear(k); c.draw([{ k: 'line', pts: [[x0, y0], [c.lerp(x0, x1, e), c.lerp(y0, y1, e)]], role, w: 0.5 }], { s: 1 }); } },
  ring(c, x, y, r, k, role = 'accent') { if (k > 0) { c.g.fillStyle = c.col(role); c.g.beginPath(); c.g.arc(Math.min(c.A.xr(y) - 30, x + r * 1.25), y - 10, 26 * c.EASE.snap(k), 0, TAU); c.g.fill(); } },
  ground(c, x, y, w) { c.g.fillStyle = c.col('ink'); c.g.fillRect(x - w / 2, y, w, 2); },
};

const spy = {
  tokens: { palette: { ink: '#F1E6D0', a: '#E8432A', b: '#E8B32A' }, roles: { hot: 'a', cold: 'ink', accent: 'b' },
            pen: { fill: true, stroke: 0, jitter: 3.2, seg: 18, shadow: [9, 11], wobLen: 90, join: 'miter' }, type: { weight: 400, upper: true, enter: 'slide', jaunty: 3, lh: 1.02 },
            motion: { ease: 'dead', enter: 'slide', step: 2, creep: 0.02 }, post: { grain: 0.08, vignette: 0.25 } },
  bg(c) {                                            // dải giấy cắt chéo trượt (camera chạy "on ones")
    const g = c.g;
    for (let i = 0; i < 5; i++) {
      const w = 36 + c.hash(i, 5) * 90, x = ((c.hash(i, 6) * 1600 + c.f * (1.2 + i * 0.5)) % 1700) - 300;
      g.save(); g.translate(x, 0); g.rotate(0.28); g.fillStyle = c.col(i % 3 === 0 ? 'hot' : i % 3 === 1 ? 'accent' : 'dim'); g.globalAlpha = i % 3 === 2 ? 0.5 : 0.85;
      g.fillRect(0, -300, w, c.H + 900); g.restore();
    }
    g.fillStyle = c.pal.bg; g.globalAlpha = 0.72; g.fillRect(0, 0, c.W, c.H);
  },
  tag(c, str, x, y, k, role = 'accent') {            // chữ trên băng giấy mù tạt, nghiêng
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 62, k: 0, maxW: 780, rot: 0 }), w = b.x1 - b.x0 + 80, h = b.y1 - b.y0 + 36, g = c.g;
    g.save(); g.translate(x, y); g.rotate(-0.05); g.translate(-x, -y);
    c.enter(k, [x - w / 2, b.y0 - 18, w, h], () => c.draw([{ k: 'rect', x: -w / 2, y: b.y0 - 18 - y, w, h, rad: 0, role }], { x, y, s: 1, seed: 4 }), 'snap');
    const r = c.text(str, x, y, { size: 62, k: c.clamp(k * 2 - 1), role: 'bg', maxW: 780, rot: 0, enter: 'wipe' });
    g.restore(); return r;
  },
};

const picto = {
  tokens: { palette: { ink: '#FFFFFF', a: '#FFC400' }, roles: { hot: 'a', cold: 'ink', accent: 'a' },
            pen: { fill: true, stroke: 0, line: 16, cap: 'round' }, type: { weight: 900, upper: true, enter: 'mask', track: -0.01, lh: 0.96 },
            motion: { ease: 'expo', enter: 'snap', creep: 0.0 }, post: { grain: 0.05, vignette: 0.1 } },
  bg(c) {                                            // hoạ tiết đĩa/nửa đĩa 5 sắc độ một màu, cả hàng cắt và trượt ngang
    const g = c.g, cell = 180, hue = c.col('accent');
    for (let r = 0; r < 11; r++) {
      const beat = Math.floor(c.f / 15), sh = ((r % 2 ? 1 : -1) * (c.f * 0.5 + (beat % 2) * 0) + r * 47) % cell;
      for (let i = -1; i < 8; i++) {
        const v = c.hash(r, i, 3), x = i * cell + sh, y = r * cell - 30, tone = c.mix(c.pal.bg, hue, 0.05 + 0.05 * Math.floor(v * 5));
        g.fillStyle = tone; g.beginPath();
        if (v < 0.4) g.arc(x + cell / 2, y + cell / 2, cell * 0.46, 0, TAU); else if (v < 0.7) g.arc(x + cell / 2, y + cell / 2, cell * 0.46, Math.PI * (r % 2), Math.PI * (1 + (r % 2))); else g.rect(x + cell * 0.36, y + cell * 0.36, cell * 0.28, cell * 0.28);
        g.fill();
      }
    }
  },
  header(c, h, k) {
    let y = c.A.top + 40;
    const idx = h.index ? `${String(h.index[0]).padStart(2, '0')} / ${String(h.index[1]).padStart(2, '0')}` : '';
    if (idx) c.text(idx, c.A.x0, y, { size: 30, font: 'mono', align: 'left', role: 'accent', k: c.clamp(k * 2), weight: 700, enter: 'type' });
    if (h.kicker) c.text(h.kicker, c.A.x1, y, { size: 30, font: 'mono', align: 'right', role: 'dim', k: c.clamp(k * 2), weight: 700, enter: 'type' });
    y += 130;
    if (h.title) { const b = c.text(h.title, c.A.x0, y + 20, { size: h.size || 118, k, maxW: 880, align: 'left' }); y = b.y1; }
    return y;
  },
  ground(c, x, y, w) { c.g.fillStyle = c.mix(c.pal.bg, c.col('accent'), 0.32); c.g.beginPath(); c.g.arc(x, y - w * 0.36, w * 0.62, 0, TAU); c.g.fill(); },   // đĩa sân khấu sau pictogram
  tag(c, str, x, y, k, role = 'accent') { return c.text(str, c.A.x0, y, { size: 72, k, role, maxW: 860, align: 'left' }); },
};

const zoom = {
  tokens: { palette: { ink: '#F4F1E8', a: '#FFD23F', b: '#5AC8FA', c: '#FF6B4A' }, roles: { hot: 'c', cold: 'b', accent: 'a' },
            pen: { fill: true, stroke: 0 }, type: { weight: 800, upper: false, enter: 'mask' },
            motion: { ease: 'spring', enter: 'pop', creep: 0.04 }, post: { grain: 0.03, vignette: 0.2 } },
  bg(c) { for (let i = 0; i < 60; i++) { c.g.fillStyle = c.col(i % 9 ? 'dim' : 'ink'); const s = 2 + (i % 3) * 2; c.g.fillRect(c.hash(i, 1) * c.W, ((c.hash(i, 2) * c.H + c.f * (0.2 + (i % 4) * 0.15)) % c.H), s, s); } },
  fg(c) {                                            // dải thang log ở góc + số trường nhìn (đọc từ cùng một camera)
    const g = c.g, x = c.A.x0, y = c.A.bottom + 4, w = 300; g.fillStyle = c.col('dim'); g.fillRect(x, y, w, 3);
    for (let i = 0; i <= 6; i++) g.fillRect(x + i * w / 6, y - 8, 3, 14);
    g.fillStyle = c.col('accent'); g.beginPath(); g.arc(x + w * c.clamp(c.zoomU ?? c.u), y + 1, 9, 0, TAU); g.fill();
  },
  halo(c, x, y, r) { const g = c.g; g.fillStyle = c.mix(c.pal.bg, c.col('hot'), 0.16); g.beginPath(); g.arc(x, y, r * 1.55, 0, TAU); g.fill(); g.fillStyle = c.mix(c.pal.bg, c.col('hot'), 0.3); g.beginPath(); g.arc(x, y, r * 1.25, 0, TAU); g.fill(); },
  ring(c, x, y, r, k, role = 'accent') {             // vòng "điểm dừng kế tiếp": vòng vàng + vòng ngoài nét đứt, khoá bằng lò xo
    if (k <= 0) return;
    const s = c.EASE.spring(k) * r;
    c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role, fill: false, w: 0.9 }, { k: 'circle', x: 0, y: 0, r: 1.28, role, fill: false, w: 0.45, dash: [1.6, 1.6] }], { x, y, s, rot: c.f * 0.01 });
  },
  arrow(c, x0, y0, x1, y1, k, role = 'accent') {     // đường ngắm chấm: chấm bật ra từng cái
    const n = 9; for (let i = 0; i < n; i++) { const kk = c.clamp(k * n - i); if (kk <= 0) continue; const t = (i + 0.5) / n, s = 9 * (kk < 1 ? c.lerp(0, 1.3, kk) : 1); c.g.fillStyle = c.col(role); c.g.beginPath(); c.g.arc(c.lerp(x0, x1, t), c.lerp(y0, y1, t), s, 0, TAU); c.g.fill(); }
  },
};

const flow = {
  tokens: { palette: { ink: '#FCF9EC', a: '#FBBF2F', b: '#D41928' }, roles: { hot: 'b', cold: 'ink', accent: 'a' },
            pen: { fill: true, stroke: 0, shadow: [8, 8, '#3a2f12'] }, type: { weight: 900, upper: false, enter: 'mask' },
            motion: { ease: 'out', enter: 'pop', creep: 0.03 }, post: { grain: 0.03, vignette: 0.2 } },
  bg(c) {                                            // vành mặt đồng hồ 12 vạch, thị sai 0.5; kim chạy liên tục
    const g = c.g, cx = c.A.cx + 220 - c.f * 0.5, cy = 1020, r = 420; g.strokeStyle = c.col('dim'); g.globalAlpha = 0.3; g.lineWidth = 14; g.lineCap = 'round';
    g.beginPath(); g.arc(cx, cy, r, 0, TAU); g.stroke(); g.beginPath();
    for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; g.moveTo(cx + Math.cos(a) * (r - 44), cy + Math.sin(a) * (r - 44)); g.lineTo(cx + Math.cos(a) * (r - 76), cy + Math.sin(a) * (r - 76)); }
    const a = c.f * 0.06; g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a) * (r - 120), cy + Math.sin(a) * (r - 120)); g.stroke();
  },
  header(c, h, k) {                                  // băng tiêu đề hổ phách, chữ gần đen rất đậm
    const y0 = c.A.top - 6, hh = 150, g = c.g;
    g.fillStyle = c.col('accent'); g.fillRect(0, y0, c.W * c.EASE.out(k), hh);
    if (h.title) c.text(h.title, c.A.cx, y0 + 100, { size: h.size ? Math.min(h.size, 74) : 70, k: c.clamp(k * 1.6 - 0.6), role: 'bg', maxW: 900 });
    let y = y0 + hh + 60;
    if (h.kicker) { c.text(h.kicker, c.A.cx, y, { size: 32, font: 'mono', role: 'dim', k, weight: 700 }); y += 30; }
    return y;
  },
  badge(c, n, x, y, k) {                             // huy hiệu số có mũi nhọn bên phải
    c.enter(k, [x - 44, y - 44, 88, 88], () => c.draw([{ k: 'poly', pts: [[30, -20], [60, 0], [30, 20]], role: 'accent' }, { k: 'circle', x: 0, y: 0, r: 40, role: 'accent' }], { x, y, s: 1 }));
    c.text(String(n), x, y + 17, { size: 50, k: c.clamp(k * 2 - 1), role: 'bg', enter: 'pop', quiet: true });
  },
  arrow(c, x0, y0, x1, y1, k) {                      // mũi tên vòng cung: đuôi trong suốt → đầu hổ phách
    if (k <= 0) return;
    const g = c.g, mx = (x0 + x1) / 2 + (y1 - y0) * 0.3, my = (y0 + y1) / 2 - (x1 - x0) * 0.3, e = c.EASE.out(k), n = 22;
    g.lineCap = 'round';
    for (let i = 0; i < n * e; i++) { const t0 = i / n, t1 = (i + 1) / n, q = (t) => [(1 - t) * (1 - t) * x0 + 2 * (1 - t) * t * mx + t * t * x1, (1 - t) * (1 - t) * y0 + 2 * (1 - t) * t * my + t * t * y1], a = q(t0), b = q(t1);
      g.strokeStyle = c.col('accent'); g.globalAlpha = t1; g.lineWidth = 6 + 10 * t1; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
    g.globalAlpha = 1;
  },
  tag(c, str, x, y, k, role = 'accent') {            // hộp chú giải bo góc
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 54, k: 0, maxW: 760 }), w = b.x1 - b.x0 + 70, h = b.y1 - b.y0 + 40;
    c.enter(k, [x - w / 2, b.y0 - 20, w, h], () => c.draw([{ k: 'rect', x: -w / 2, y: b.y0 - 20 - y, w, h, rad: 22, role }], { x, y, s: 1 }));
    return c.text(str, x, y, { size: 54, k: c.clamp(k * 1.6 - 0.6), role: 'bg', maxW: 760 });
  },
};

const sketch = {
  tokens: { palette: { ink: '#E8E6DC', a: '#F8711C' }, roles: { hot: 'a', cold: 'ink', accent: 'a' },
            pen: { fill: false, stroke: 4.5, jitter: 1.6, hatch: 13, wobLen: 34, tint: 0.85 }, type: { weight: 400, upper: false, enter: 'write', lh: 1.0 },
            motion: { ease: 'out', enter: 'draw', creep: 0.0, lead: 14 }, post: { grain: 0.08, vignette: 0.3 } },
  bg(c) {                                            // trang sổ: dòng kẻ mờ trôi lên (camera "đọc" từ trên xuống) + lề
    const g = c.g, off = (c.f * 0.8) % 74; g.strokeStyle = c.col('dim'); g.globalAlpha = 0.22; g.lineWidth = 1.5; g.beginPath();
    for (let y = -off; y < c.H; y += 74) { g.moveTo(0, y); g.lineTo(c.W, y); }
    g.stroke(); g.strokeStyle = c.col('accent'); g.globalAlpha = 0.35; g.beginPath(); g.moveTo(70, 0); g.lineTo(70, c.H); g.stroke();
  },
  header(c, h, k) {                                  // khung tiêu đề nét đứt, góc vẽ lố
    const y0 = c.A.top, hh = 230, x0 = c.A.x0 + 10, x1 = c.A.x1 - 10, o = 18;
    c.enter(k, [x0, y0, x1 - x0, hh], () => c.draw([[x0 - o, y0, x1 + o, y0], [x1, y0 - o, x1, y0 + hh + o], [x1 + o, y0 + hh, x0 - o, y0 + hh], [x0, y0 + hh + o, x0, y0 - o]].map((q) => ({ k: 'line', pts: [[q[0], q[1]], [q[2], q[3]]], role: 'ink', dash: [2.2, 1.6], w: 0.7 })), { s: 1, seed: 2 }), 'draw');
    if (h.kicker) c.text(`※ ${h.kicker} ※`, c.A.cx, y0 + 14, { size: 30, role: 'accent', k: c.clamp(k * 2), quiet: true });
    if (h.title) c.text(h.title, c.A.cx, y0 + (String(h.title).length > 18 ? 100 : 140), { size: 112, k: c.clamp(k * 1.5 - 0.3), maxW: 820 });
    return y0 + hh + 30;
  },
  tag(c, str, x, y, k, role = 'accent') {            // "@nhãn:" khối đặc + chữ tay
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 56, k: 0, maxW: 760 }), w = b.x1 - b.x0 + 50, h = b.y1 - b.y0 + 26;
    c.enter(k, [x - w / 2, b.y0 - 13, w, h], () => { c.g.fillStyle = c.col(role); c.g.fillRect(x - w / 2, b.y0 - 13, w, h); }, 'wipe');
    return c.text(str, x, y, { size: 56, k: c.clamp(k * 1.6 - 0.6), role: 'bg', maxW: 760 });
  },
  ground(c, x, y, w) { c.draw([0, 1, 2].map((i) => ({ k: 'line', pts: [[-w / 2 + i * 26, i * 12], [w / 2 - i * 40, i * 12]], role: 'dim', w: 0.6 })), { x, y: y + 6, s: 1, seed: 6 }); },
  ring(c, x, y, r, k, role = 'accent') { if (k > 0) c.draw([{ k: 'arc', x: 0, y: 0, r: 1, rx: 1.08, ry: 0.94, a0: -1.2, a1: -1.2 + TAU * 1.12 * c.EASE.out(k), role, w: 0.9 }], { x, y, s: r, seed: 8 }); },
};

const gallery = {                                    // "tranh lồng khung": cảnh được vẽ lại bằng chấm màu trong một khung tranh treo trên tường đen
  tokens: { palette: { ink: '#F3EDE0', a: '#FF8A3C', b: '#4FA3E0', c: '#F2D15C' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 0 }, type: { weight: 700, upper: false, enter: 'mask', outline: 0.16 }, deferText: true,
            motion: { ease: 'smooth', enter: 'pop', step: 2, creep: 0.02 }, post: { grain: 0.06, vignette: 0.35 }, frame: [100, 480, 880, 900] },
  bg() {},
  paint(c) {                                         // gọi SAU khi beat vẽ xong: đọc vùng tranh rồi chấm lại (pointillism), sau đó đóng khung
    const g = c.g, [fx, fy, fw, fh] = c.L.frame, img = g.getImageData(fx, fy, fw, fh).data, step = 11, tick = Math.floor(c.f / 2);
    g.fillStyle = '#05070c'; g.fillRect(fx, fy, fw, fh);
    for (let y = 0; y < fh; y += step) for (let x = 0; x < fw; x += step) {
      const jx = x + (c.hash(x, y, 1) - 0.5) * step, jy = y + (c.hash(x, y, 2) - 0.5) * step, i = (Math.min(fh - 1, Math.max(0, Math.round(jy))) * fw + Math.min(fw - 1, Math.max(0, Math.round(jx)))) * 4;
      let r = img[i], gg = img[i + 1], b = img[i + 2]; const lum = (r + gg + b) / 3, v = c.hash(x, y, 3 + (tick % 3));
      if (lum < 24) { r = 6 + v * 16; gg = 9 + v * 18; b = 18 + v * 34; } else { const d = (v - 0.5) * 46; r += d; gg += d * 0.7; b -= d; }
      g.fillStyle = `rgb(${r | 0},${gg | 0},${b | 0})`; g.beginPath();
      const a = c.hash(x, y, 4) * 3.14; g.ellipse(fx + jx, fy + jy, step * 0.62, step * 0.38, a, 0, TAU); g.fill();
    }
    g.lineWidth = 26; g.strokeStyle = '#6b5a3a'; g.strokeRect(fx - 13, fy - 13, fw + 26, fh + 26);       // khung gỗ + viền trong + bóng
    g.lineWidth = 5; g.strokeStyle = '#c9b27a'; g.strokeRect(fx - 3, fy - 3, fw + 6, fh + 6); g.strokeStyle = '#2c2416'; g.strokeRect(fx - 27, fy - 27, fw + 54, fh + 54);
  },
};

// ================= vòng 10: look 2D theo bộ "10 style viral" (in tram, truyện tranh cũ, pixel 16/8-bit, rối bóng, cắt giấy,
// nét đơn). Hậu kỳ in/pixel là token post.* (core.js → post2d.js, WebGL một pass); chữ/nhãn hoãn vẽ SAU lớp đó (deferText)
// nên luôn sắc và OCR đọc được. Mọi thứ trên nền đen; giấy chỉ có trong khung tranh hoặc trong hình.
const INKK = '#120F0C';                              // mực đen in (khác #000 của sân khấu để không lẫn vào nền khi vẽ hoãn)
const regMark = (c, x, y, s) => {                    // dấu canh bản ⊕ của nhà in
  const g = c.g; g.strokeStyle = c.col('ink'); g.lineWidth = 2; g.globalAlpha = 0.55;
  g.beginPath(); g.arc(x, y, s * 0.55, 0, TAU); g.moveTo(x - s, y); g.lineTo(x + s, y); g.moveTo(x, y - s); g.lineTo(x, y + s); g.stroke(); g.globalAlpha = 1;
};
const halftone = {
  tokens: { palette: { ink: '#F6EEDD', a: '#E5432F', b: '#2A6FB5', c: '#F4B42E' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 5, strokeRole: 'bg', line: 7 }, type: { weight: 400, upper: true, enter: 'mask', lh: 1.0, track: 0.01 }, deferText: true,
            motion: { ease: 'out', enter: 'pop', creep: 0.03 },
            post: { grain: 0.02, vignette: 0.22, halftone: { mode: 'cmyk', cell: 9, angle: 0, gain: 1.12 }, misregister: { x: 3, y: 2 }, paper: { color: '#F4EBD7' } } },
  bg(c) {                                            // vầng màu lớn trôi chậm (thành dải chấm tram thưa dần) + dấu canh bản 4 góc
    const g = c.g, x = c.W * 0.5 + Math.sin(c.f * 0.011) * 70, y = 980 + Math.cos(c.f * 0.009) * 60, r = 470;
    const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, c.mix(c.pal.bg, c.col('hot'), 0.34)); gr.addColorStop(1, c.pal.bg);
    g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r);
    const m = 70; for (const [px, py] of [[m, c.A.top - 40], [c.W - m, c.A.top - 40], [m, c.A.bottom + 40], [c.W - m, c.A.bottom + 40]]) regMark(c, px, py, 22);
  },
  header(c, h, k) {                                  // kicker mono kẹp giữa hai vạch kẻ báo in, tiêu đề chữ khối lớn
    let y = c.A.top + 46;
    if (h.kicker) {
      const kk = c.clamp(k * 1.6), w = (c.A.x1 - c.A.x0 - 60) * c.EASE.out(kk);
      c.g.fillStyle = c.col('ink'); c.g.fillRect(c.A.cx - w / 2, y - 44, w, 3); c.g.fillRect(c.A.cx - w / 2, y + 18, w, 3);
      c.text(h.kicker, c.A.cx, y, { size: 34, font: 'mono', role: 'ink', k: kk, enter: 'type', weight: 600 }); y += 96;
    } else y += 60;
    if (h.title) { const b = c.text(h.title, c.A.cx, y + 50, { size: h.size || 118, k, maxW: 900 }); y = b.y1; }
    return y;
  },
  tag(c, str, x, y, k, role = 'accent') {            // tem vé xé: khối màu (in tram) góc khuyết, chữ mực đen sắc
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 62, k: 0, maxW: 800 }), w = b.x1 - b.x0 + 80, h = b.y1 - b.y0 + 38, n = 16;
    const pts = [[-w / 2 + n, 0], [w / 2 - n, 0], [w / 2, n], [w / 2, h - n], [w / 2 - n, h], [-w / 2 + n, h], [-w / 2, h - n], [-w / 2, n]];
    c.enter(k, [x - w / 2, b.y0 - 19, w, h], () => c.draw([{ k: 'poly', pts: pts.map(([px, py]) => [px, py + b.y0 - 19 - y]), role }], { x, y, s: 1 }));
    return c.text(str, x, y, { size: 62, k: c.clamp(k * 1.5 - 0.5), role: 'bg', maxW: 800, enter: 'pop', bare: true });
  },
  ground(c, x, y, w) { c.draw([{ k: 'rect', x: -w / 2, y: 0, w, h: 14, rad: 7, role: 'dim' }], { x, y, s: 1, plain: true }); },
};

const COMIC_PANEL = [90, 470, 900, 940];             // khung tranh mặc định (x, y, w, h) — style ghi đè bằng post.paper.rect
const caption = (c, str, x, y, k, o = {}) => {       // hộp chú thích vàng viền mực (kiểu "MEANWHILE…")
  if (k <= 0 || !str) return null;
  const size = o.size || 40, mw = o.maxW || 760, b = c.text(str, x, y, { size, k: 0, align: 'left', maxW: mw });
  const p = 18, bx = b.x0 - p, by = b.y0 - p, bw = b.x1 - b.x0 + p * 2, bh = b.y1 - b.y0 + p * 2;
  c.enter(k, [bx, by, bw, bh], () => c.later(() => {
    const g = c.g; g.fillStyle = INKK; g.fillRect(bx + 7, by + 8, bw, bh);
    g.fillStyle = c.col(o.role || 'accent'); g.fillRect(bx, by, bw, bh); g.lineWidth = 5; g.strokeStyle = INKK; g.strokeRect(bx, by, bw, bh);
  }), 'snap');
  return c.text(str, x, y, { size, k: c.clamp(k * 1.5 - 0.3), align: 'left', maxW: mw, role: 'bg', bare: true, enter: 'type' });
};
const balloon = (c, str, x, y, k, o = {}) => {       // bóng thoại trắng viền mực, đuôi chỉ lên vật phía trên
  if (k <= 0 || !str) return null;
  const size = o.size || 54, mw = o.maxW || 720, b = c.text(str, x, y, { size, k: 0, maxW: mw });
  const cx = (b.x0 + b.x1) / 2, cy = (b.y0 + b.y1) / 2, rx = (b.x1 - b.x0) / 2 + 52, ry = (b.y1 - b.y0) / 2 + 38, side = o.side ?? -1;
  const tail = [[cx + side * rx * 0.2, cy - ry * 0.7], [cx + side * rx * 0.62, cy - ry - 70], [cx + side * rx * 0.48, cy - ry * 0.55]];
  c.enter(k, [cx - rx, cy - ry, 2 * rx, 2 * ry], () => c.later(() => {
    const g = c.g, path = () => { g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, 0, TAU); g.moveTo(...tail[0]); g.lineTo(...tail[1]); g.lineTo(...tail[2]); g.closePath(); };
    path(); g.lineWidth = 11; g.strokeStyle = INKK; g.lineJoin = 'round'; g.stroke(); g.fillStyle = '#FFFDF4'; g.fill();
  }), 'pop');
  return c.text(str, x, y, { size, k: c.clamp(k * 1.5 - 0.4), role: 'bg', maxW: mw, bare: true, enter: 'pop' });
};
const comic = {
  tokens: { palette: { ink: '#FFF6E0', a: '#E62E2D', b: '#1F6FD0', c: '#FFD23A' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 6.5, strokeRole: 'ink', line: 8 }, type: { weight: 400, upper: true, enter: 'pop', outline: 0.14, shadow: [7, 8, 'bg'], track: 0.03, lh: 1.0 },
            deferText: true, motion: { ease: 'bounce', enter: 'pop', creep: 0.03 },
            post: { grain: 0.03, vignette: 0.15, halftone: { mode: 'benday', cell: 13, flat: 0.8, low: 0.15 }, misregister: { x: 3, y: -2 },
                    paper: { rect: COMIC_PANEL, color: '#F2E3BE', age: 0.75, fiber: 0.1, border: 9, gutter: 7 } } },
  header(c, h, k) {
    let y = c.A.top + 40;
    if (h.kicker) { caption(c, h.kicker, c.A.x0 + 6, y + 26, c.clamp(k * 1.6), { size: 38 }); y += 110; } else y += 50;
    if (h.title) { const b = c.text(h.title, c.A.cx, y + 64, { size: h.size || 118, k, maxW: 900, rot: -2.5 }); y = b.y1; }
    return y;
  },
  tag(c, str, x, y, k) { return balloon(c, str, x, y, k, { side: x > c.A.cx ? 1 : -1 }); },
  ring(c, x, y, r, k, role = 'accent') {             // tia "BAM!" răng cưa quanh vật thay cho vòng tròn
    if (k <= 0) return;
    const n = 14, e = c.EASE.bounce(k), pts = Array.from({ length: n * 2 }, (_, i) => { const a = i / (n * 2) * TAU + 0.2, rr = (i % 2 ? 0.86 : 1.12 + c.hash(i, 5) * 0.12) * r * e; return [x + Math.cos(a) * rr, y + Math.sin(a) * rr]; });
    c.draw([{ k: 'poly', pts, role, fill: false, w: 0.8 }], { s: 1, seed: 7 });
  },
  halo(c, x, y, r) {                                 // trường năng lượng kiểu Kirby: vầng màu + cụm chấm mực đen
    c.draw([{ k: 'circle', x: 0, y: 0, r: 1.5, role: 'accent' }], { x, y, s: r, plain: true, alpha: 0.9 });
    for (let i = 0; i < 16; i++) { const a = i / 16 * TAU + c.f * 0.01, d = r * (1.05 + 0.3 * c.hash(i, 2)); c.g.fillStyle = INKK; c.g.beginPath(); c.g.arc(x + Math.cos(a) * d, y + Math.sin(a) * d, r * (0.06 + 0.07 * c.hash(i, 3)), 0, TAU); c.g.fill(); }
  },
  fg(c) {                                            // tia tốc độ toả từ tâm khung tranh lúc va chạm (kick)
    const kk = Math.abs(c.kick || 0); if (kk < 0.05) return;
    const g = c.g, [px, py, pw, ph] = c.L.post.paper?.rect || COMIC_PANEL, cx = px + pw / 2, cy = py + ph / 2;
    g.save(); g.beginPath(); g.rect(px, py, pw, ph); g.clip(); g.strokeStyle = c.col('ink'); g.lineCap = 'butt';
    for (let i = 0; i < 36; i++) { const a = i / 36 * TAU + c.hash(i, 9) * 0.1, r0 = 300 + c.hash(i, 4) * 140; g.lineWidth = 3 + 7 * c.hash(i, 6) * kk; g.beginPath(); g.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); g.lineTo(cx + Math.cos(a) * 900, cy + Math.sin(a) * 900); g.stroke(); }
    g.restore();
  },
  arrow(c, x0, y0, x1, y1, k, role = 'accent') {     // mũi tên khối mập, viền mực
    if (k <= 0) return;
    const e = c.EASE.out(k), xe = c.lerp(x0, x1, e), ye = c.lerp(y0, y1, e), a = Math.atan2(y1 - y0, x1 - x0), w = 13, hs = 34;
    const nx = -Math.sin(a), ny = Math.cos(a), bx = xe - Math.cos(a) * hs, by = ye - Math.sin(a) * hs;
    c.draw([{ k: 'poly', role, pts: [[x0 + nx * w, y0 + ny * w], [bx + nx * w, by + ny * w], [bx + nx * w * 2.4, by + ny * w * 2.4], [xe, ye], [bx - nx * w * 2.4, by - ny * w * 2.4], [bx - nx * w, by - ny * w], [x0 - nx * w, y0 - ny * w]] }], { s: 1 });
  },
};

// pixel: cảnh vẽ đủ độ phân giải rồi post.pixel hạ về lưới div, lượng tử bảng màu + Bayer; nền có thị sai trôi liên tục để
// không khối pixel nào đứng yên ≥ 4 frame (chuyển động chậm dưới 1 khối sẽ bị lưới "nuốt").
const starfield = (c, n, cell, speeds, roleA = 'ink') => {
  const g = c.g;
  for (let i = 0; i < n; i++) {
    const sp = speeds[i % speeds.length], x = ((c.hash(i, 21) * (c.W + 200) - c.f * sp) % (c.W + 200) + c.W + 200) % (c.W + 200) - 100;
    const y = c.hash(i, 22) * c.H, tw = c.hash(i, Math.floor(c.f / 6), 23) > 0.82 ? 0.35 : 1;
    g.fillStyle = c.mix(c.pal.bg, c.col(i % 7 ? roleA : 'accent'), (0.35 + 0.45 * (i % speeds.length) / speeds.length) * tw);
    g.fillRect(Math.round(x / cell) * cell, Math.round(y / cell) * cell, cell * (i % 11 ? 1 : 2), cell * (i % 11 ? 1 : 2));
  }
};
const ridge = (c, y0, amp, speed, role, tone, seed) => {   // dải núi xa trôi ngang (thị sai), màu tối của một vai
  const g = c.g, off = c.f * speed; g.fillStyle = c.mix(c.pal.bg, c.col(role), tone); g.beginPath(); g.moveTo(0, c.H);
  for (let x = 0; x <= c.W + 40; x += 40) { const u = (x + off) / 260; g.lineTo(x, y0 - amp * (0.55 * Math.sin(u + seed) + 0.3 * Math.sin(u * 2.3 + seed * 2) + 0.15 * Math.sin(u * 5.1))); }
  g.lineTo(c.W, c.H); g.closePath(); g.fill();
};
const pixel16 = {
  tokens: { palette: { ink: '#F7F1E3', a: '#F2544B', b: '#3D8BEF', c: '#F9C846' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 5, strokeTone: 0.62, line: 6, cap: 'square', join: 'miter', seg: 28, cel: [10, 10, 0.34] },
            type: { weight: 600, upper: false, enter: 'type', drop: [5, 5, 'bg'], track: 0, lh: 1.08 }, deferText: true,
            motion: { ease: 'out', enter: 'pop', step: 2, creep: 0.02, shake_px: 5 },
            post: { grain: 0, vignette: 0, pixel: { div: 5, colors: 48, dither: 0.08 } } },
  bg(c) {
    starfield(c, 70, 5, [1.6, 3.1, 5.2]);
    ridge(c, c.A.bottom + 150, 60, 1.6, 'cold', 0.2, 1.3);
    ridge(c, c.A.bottom + 230, 40, 3.4, 'cold', 0.12, 4.1);
  },
  tag(c, str, x, y, k, role = 'accent') {            // hộp thoại RPG: khung đôi viền sáng, nền tối, chữ có bóng
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 56, k: 0, maxW: 820 }), w = b.x1 - b.x0 + 70, h = b.y1 - b.y0 + 44;
    c.enter(k, [x - w / 2, b.y0 - 22, w, h], () => c.draw([{ k: 'rect', x: -w / 2, y: b.y0 - 22 - y, w, h, rad: 10, role: 'cold' }, { k: 'rect', x: -w / 2 + 10, y: b.y0 - 12 - y, w: w - 20, h: h - 20, rad: 5, role: 'ink', fill: false, sw: 0.8 }], { x, y, s: 1 }), 'grow');
    return c.text(str, x, y, { size: 56, k: c.clamp(k * 1.5 - 0.4), role: 'ink', maxW: 820 });
  },
  ground(c, x, y, w) { c.draw([{ k: 'rect', x: -w / 2, y: 0, w, h: 20, rad: 0, role: 'dim' }, { k: 'rect', x: -w / 2, y: 20, w, h: 10, rad: 0, role: 'cold' }], { x, y, s: 1, plain: true }); },
};
const sprite8 = {
  tokens: { palette: { ink: '#FCFCFC', a: '#E83A3A', b: '#3CBCFC', c: '#F8B800' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 10, strokeRole: 'bg', line: 10, cap: 'square', join: 'miter', seg: 16, limit: 4, cel: [10, 10, 0.42] },
            type: { weight: 400, upper: true, enter: 'type', px: 5, drop: [5, 5, 'bg'], track: 0, lh: 1.35 }, deferText: true,
            motion: { ease: 'steps', enter: 'pop', step: 4, hold: 2, creep: 0, shake_px: 10 },
            post: { grain: 0, vignette: 0, pixel: { div: 10, colors: 16, ramp: [0.45, 1, 1.45], greys: 2, dither: 0 } } },
  bg(c) {                                            // sao 8-bit trôi bậc + vạch sàn ô bàn cờ chạy ngang (luôn có khối đổi chỗ mỗi 2 frame)
    starfield(c, 46, 10, [5, 10]);
    const g = c.g, y = c.A.bottom + 120, off = Math.floor(c.f / 2) * 10 % 80;
    for (let x = -80; x < c.W + 80; x += 80) { g.fillStyle = c.mix(c.pal.bg, c.col('cold'), 0.45); g.fillRect(x - off, y, 40, 20); g.fillStyle = c.mix(c.pal.bg, c.col('cold'), 0.25); g.fillRect(x - off + 40, y, 40, 20); }
  },
  tag(c, str, x, y, k, role = 'accent') { return pixel16.tag(c, str, x, y, k, role); },
  ring(c, x, y, r, k, role = 'accent') {             // 4 góc ngắm vuông kiểu con trỏ chọn menu
    if (k <= 0) return;
    const s = r * c.lerp(1.3, 1, c.EASE.steps(k)), l = r * 0.32, pr = [];
    for (const [dx, dy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) pr.push({ k: 'line', role, w: 1, pts: [[dx * s, dy * (s - l)], [dx * s, dy * s], [dx * (s - l), dy * s]] });
    c.draw(pr, { x, y, s: 1 });
  },
};

// rối bóng (ink silhouette): mọi vật là bóng đen đặc trước một nguồn sáng giới hạn (đĩa trăng/hoàng hôn + dải chân trời),
// viền sáng mảnh ở mép ngoài, đinh khớp kiểu rối; chữ sáng có viền đen đọc được cả trên vùng sáng lẫn vùng tối.
const silhouette = {
  tokens: { palette: { ink: '#FFE7C2', a: '#FF6B35', b: '#8FB3FF', c: '#FFC15E' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 0, line: 7, silhouette: { rim: 2.2, role: 'ink' }, pins: true }, type: { weight: 700, upper: false, enter: 'mask', outline: 0.16 },
            motion: { ease: 'smooth', enter: 'pop', creep: 0.02 }, post: { grain: 0.05, vignette: 0.3 },
            light: { x: 0.5, y: 0.5, r: 330, glow: 150, band: [1300, 200], rise: 46 } },
  bg(c) {
    const Lt = c.L.light, g = c.g, x = c.W * Lt.x, y = c.H * Lt.y - Lt.rise * c.u, R = Lt.r + Lt.glow;
    if (!c.L._moon) {                                // đĩa sáng + quầng dựng MỘT lần (chỉ trôi lên theo u) → rẻ mỗi frame
      const cv = document.createElement('canvas'); cv.width = cv.height = Math.ceil(2 * R); const m = cv.getContext('2d'), r = Lt.r;
      const gl = m.createRadialGradient(R, R, r * 0.9, R, R, R); gl.addColorStop(0, c.mix(c.pal.bg, c.col('hot'), 0.55)); gl.addColorStop(1, c.pal.bg);
      m.fillStyle = gl; m.beginPath(); m.arc(R, R, R, 0, TAU); m.fill();
      const dk = m.createRadialGradient(R - r * 0.25, R - r * 0.3, r * 0.1, R, R, r); dk.addColorStop(0, c.mix(c.col('accent'), c.col('ink'), 0.45)); dk.addColorStop(1, c.mix(c.col('accent'), c.col('hot'), 0.55));
      m.fillStyle = dk; m.beginPath(); m.arc(R, R, r, 0, TAU); m.fill();
      c.L._moon = cv;
    }
    g.drawImage(c.L._moon, x - R, y - R);
    if (Lt.band) {                                   // dải hoàng hôn mảnh ở chân trời (đặt dưới vùng nhãn)
      const [by, bh] = Lt.band, bd = g.createLinearGradient(0, by, 0, by + bh); bd.addColorStop(0, c.pal.bg); bd.addColorStop(0.55, c.mix(c.pal.bg, c.col('hot'), 0.62)); bd.addColorStop(1, c.pal.bg);
      g.fillStyle = bd; g.fillRect(0, by, c.W, bh);
    }
  },
  halo(c, x, y, r) {                                 // vật "nóng" tự có quầng sáng riêng để bóng của nó đọc được ở vùng tối
    const g = c.g, gr = g.createRadialGradient(x, y, r * 0.2, x, y, r * 1.6); gr.addColorStop(0, c.mix(c.col('accent'), c.col('ink'), 0.3)); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(x, y, r * 1.6, 0, TAU); g.fill();
  },
  ground(c, x, y, w) { c.draw([{ k: 'rect', x: -w / 2, y: -4, w, h: 22, rad: 6, role: 'ink' }], { x, y, s: 1, seed: 3 }); },
};

// cắt giấy 2D: mép xé răng cưa (rung tĩnh theo đỉnh), lõi giấy trắng ở mép, vân giấy nhân, bóng mềm theo độ sâu, chụp on 2s
// + mỗi lần chụp lệch nhẹ tất định. Nền là các lớp giấy rất tối (vẫn tính là đen) trôi thị sai.
const tornStrip = (c, y0, h, speed, tone, role, seed) => {
  const off = c.f * speed, pts = [];
  for (let x = -60; x <= c.W + 60; x += 30) pts.push([x, y0 + Math.sin((x + off) / 170 + seed) * 18 + (c.hash(Math.floor((x + off) / 30), seed) - 0.5) * 10]);
  for (let x = c.W + 60; x >= -60; x -= 30) pts.push([x, y0 + h + Math.sin((x + off) / 210 + seed * 2) * 14]);
  c.draw([{ k: 'poly', pts, role: c.mix(c.pal.bg, c.col(role), tone) }], { s: 1, seed: 17 + seed, plain: true });
};
const cutout = {
  tokens: { palette: { ink: '#F4EAD5', a: '#E2552D', b: '#2F86A6', c: '#F3C246' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 0, line: 7, jitter: 2.2, wobLen: 10, seg: 40, cut: { edge: 2.6, grain: 0.3, shadow: [6, 10, 8] }, nudge: [2.2, 0.012], pins: true },
            type: { weight: 400, upper: false, enter: 'mask', jaunty: 1.2, lh: 1.05 },
            motion: { ease: 'dead', enter: 'slide', step: 2, hold: 2, creep: 0.025 }, post: { grain: 0.05, vignette: 0.3 } },
  bg(c) {
    tornStrip(c, c.A.bottom + 110, 400, 0.6, 0.13, 'cold', 1);
    tornStrip(c, c.A.bottom + 190, 400, 1.3, 0.1, 'hot', 3);
    tornStrip(c, -330, 420, -0.5, 0.1, 'cold', 5);
  },
  tag(c, str, x, y, k, role = 'accent') {            // băng giấy xé, chữ in đen
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 60, k: 0, maxW: 800, rot: 0 }), w = b.x1 - b.x0 + 80, h = b.y1 - b.y0 + 40;
    c.enter(k, [x - w / 2, b.y0 - 20, w, h], () => c.draw([{ k: 'rect', x: -w / 2, y: b.y0 - 20 - y, w, h, rad: 0, role }], { x, y, s: 1, seed: 4, rot: -0.03 }), 'slide');
    return c.text(str, x, y, { size: 60, k: c.clamp(k * 2 - 1), role: 'bg', maxW: 800, rot: -1.7 });
  },
  ground(c, x, y, w) { c.draw([{ k: 'rect', x: -w / 2, y: -6, w, h: 30, rad: 0, role: 'dim' }], { x, y, s: 1, seed: 6 }); },
};

// nét đơn sạch (line art): một độ dày, không tô, không rung — khác boil (nét sôi) và sketch (nét chì + gạch bóng)
const lineart = {
  tokens: { palette: { ink: '#EEECE6', a: '#FF6A3D' }, roles: { hot: 'a', cold: 'ink', accent: 'a' },
            pen: { fill: false, stroke: 4, tint: 0, seg: 64 }, type: { weight: 600, upper: false, enter: 'wipe', lh: 1.04 },
            motion: { ease: 'smooth', enter: 'draw', creep: 0.02, lead: 12 }, post: { grain: 0.03, vignette: 0.2 } },
  ground(c, x, y, w) { c.draw([{ k: 'line', pts: [[-w / 2, 0], [w / 2, 0]], role: 'ink', w: 0.6 }], { x, y, s: 1 }); },
  tag(c, str, x, y, k, role = 'accent') {
    const b = c.text(str, x, y, { size: 62, k, role: 'ink', maxW: 820 });
    if (k > 0) c.draw([{ k: 'line', pts: [[b.x0, b.y1 + 14], [c.lerp(b.x0, b.x1, c.EASE.out(k)), b.y1 + 14]], role, w: 1 }], { s: 1 });
    return b;
  },
};

// Vox Editorial Dark-Mode: nền than chì báo chí (#0E1014), lưới cột mảnh, thẻ giấy tối/kem, bút dạ quang vàng Vox (#F5D547) quẹt mượt theo từ khoá
const vox = {
  tokens: { palette: { bg: '#0E1014', ink: '#F4EFE6', a: '#E5483B', b: '#4CA8D8', c: '#F5D547' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 2.5, strokeRole: '#0E1014', line: 5, cap: 'butt', join: 'miter', seg: 48, shadow: [6, 8, '#050608'] },
            type: { weight: 700, upper: false, align: 'left', enter: 'mask', lh: 1.08, track: -0.01 },
            motion: { ease: 'snap', enter: 'wipe', creep: 0.02, stagger: 3 }, post: { grain: 0.045, vignette: 0.22 } },
  bg(c) {
    const g = c.g, x0 = c.A.x0, x1 = c.A.x1, cw = (x1 - x0) / 3;
    // lưới cột báo chí mờ + dải chấm biên tập trôi rất nhẹ (đảm bảo luôn có chuyển động mịn)
    g.strokeStyle = c.col('dim'); g.globalAlpha = 0.16; g.lineWidth = 1.5; g.beginPath();
    for (let i = 0; i <= 3; i++) { g.moveTo(x0 + i * cw, c.A.top - 56); g.lineTo(x0 + i * cw, c.A.bottom + 36); }
    for (let y = c.A.top; y < c.A.bottom; y += 160) { g.moveTo(x0, y); g.lineTo(x1, y); }
    g.stroke();
    // thanh trên kiểu tiêu đề chuyên mục Vox (vạch vàng dạ quang + dateline)
    g.globalAlpha = 0.92; g.fillStyle = c.col('accent'); g.fillRect(x0, c.A.top - 58, 120 + 60 * c.u, 6);
    g.fillStyle = c.col('dim'); g.globalAlpha = 0.45; g.fillRect(x0, c.A.top - 44, x1 - x0, 1.5);
    g.fillRect(x0, c.A.bottom + 14, (x1 - x0) * c.u, 3);
  },
  header(c, h, k) {
    let y = c.A.top + 8;
    if (h.kicker) {
      const kb = c.text(h.kicker, c.A.x0 + 14, y, { size: 28, font: 'mono', role: 'bg', align: 'left', k: 0, weight: 700 });
      const kw = (kb.x1 - kb.x0 + 28) * c.EASE.snap(c.clamp(k * 1.8));
      c.g.fillStyle = c.col('accent'); c.g.fillRect(c.A.x0, kb.y0 - 8, kw, kb.y1 - kb.y0 + 16);
      c.text(h.kicker, c.A.x0 + 14, y, { size: 28, font: 'mono', role: 'bg', align: 'left', k: c.clamp(k * 1.8), weight: 700, enter: 'wipe' });
      y += 72;
    } else y += 24;
    if (h.title) { const b = c.text(h.title, c.A.x0, y + 28, { size: h.size || 96, k, maxW: 860, align: 'left' }); y = b.y1; }
    return y;
  },
  tag(c, str, x, y, k, role = 'accent') {            // bút dạ quang vàng Vox quẹt ngang từ trái sang phải, chữ đen đậm
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 58, k: 0, maxW: 820 }), w = b.x1 - b.x0 + 52, h = b.y1 - b.y0 + 24;
    const e = c.EASE.snap(k);
    c.g.save(); c.g.fillStyle = c.col(role);
    c.g.fillRect(b.x0 - 26, b.y0 - 12, w * e, h);
    c.g.restore();
    return c.text(str, x, y, { size: 58, k: c.clamp(k * 2 - 0.6), role: 'bg', maxW: 820, enter: 'wipe' });
  },
  label(c, str, x, y, k, o = {}) { return c.text(str, x, y, { size: 42, k, maxW: 400, weight: 700, ...o }); },
  arrow(c, x0, y0, x1, y1, k, role = 'accent') {
    if (k <= 0) return;
    const e = c.EASE.snap(k), xe = c.lerp(x0, x1, e), ye = c.lerp(y0, y1, e), a = Math.atan2(y1 - y0, x1 - x0), s = 18;
    c.draw([
      { k: 'circle', x: x0, y: y0, r: 7, role },
      { k: 'line', pts: [[x0, y0], [xe, ye]], role, w: 0.7 },
      { k: 'poly', role, pts: [[xe + Math.cos(a) * s, ye + Math.sin(a) * s], [xe + Math.cos(a + 2.5) * s, ye + Math.sin(a + 2.5) * s], [xe + Math.cos(a - 2.5) * s, ye + Math.sin(a - 2.5) * s]] },
    ], { s: 1 });
  },
  ring(c, x, y, r, k, role = 'accent') {
    if (k <= 0) return;
    c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0: -1.2, a1: -1.2 + TAU * 1.02 * c.EASE.snap(k), role, w: 1.1 }], { x, y, s: r, seed: 7 });
  },
  ground(c, x, y, w) {
    const g = c.g; g.save(); g.strokeStyle = c.col('dim'); g.lineWidth = 3; g.globalAlpha = 0.65;
    g.beginPath(); g.moveTo(x - w / 2, y); g.lineTo(x + w / 2, y);
    for (let t = -3; t <= 3; t++) { const tx = x + (t / 3) * (w * 0.45); g.moveTo(tx, y - 6); g.lineTo(tx, y + 6); }
    g.stroke(); g.restore();
  },
};

// Cartoon Story Dark-Mode (cảm hứng kênh ammedia9192): viền đen sắc 5px, mảng màu phẳng tươi trên nền tối, khung cảnh chân trời tối giản + hộp thoại đen bo tròn
const story = {
  tokens: { palette: { bg: '#0B0D12', ink: '#F8F5EE', a: '#E84D3D', b: '#2EBFA5', c: '#F9C74F' }, roles: { hot: 'a', cold: 'b', accent: 'c' },
            pen: { fill: true, stroke: 5.2, strokeRole: '#12151C', line: 6, cap: 'round', join: 'round', seg: 40, cel: [8, 8, 0.24] },
            type: { weight: 800, upper: false, align: 'center', enter: 'pop', lh: 1.08, outline: 0.14 },
            motion: { ease: 'bounce', enter: 'pop', creep: 0.018, stagger: 3 }, post: { grain: 0.025, vignette: 0.2 } },
  bg(c) {
    // sân khấu truyện tranh dark-mode: bầu trời chạng vạng tối + dải đất/cỏ đêm + vài đám mây/đồi trôi nhẹ
    const g = c.g, hz = c.A.bottom - 180;
    const sky = g.createLinearGradient(0, c.A.top - 120, 0, hz);
    sky.addColorStop(0, '#0B0D12'); sky.addColorStop(0.65, '#131A26'); sky.addColorStop(1, '#1C2838');
    g.fillStyle = sky; g.fillRect(0, 0, c.W, hz);
    // mây phẳng viền tối trôi chậm
    for (let i = 0; i < 4; i++) {
      const cx = ((c.hash(i, 31) * (c.W + 300) + c.f * (0.6 + i * 0.25)) % (c.W + 300)) - 150;
      const cy = c.A.top + 80 + c.hash(i, 32) * 340, r = 34 + c.hash(i, 33) * 26;
      g.save(); g.globalAlpha = 0.22; g.fillStyle = '#8FA8C8';
      g.beginPath(); g.arc(cx, cy, r, 0, TAU); g.arc(cx + r * 0.9, cy + 6, r * 0.78, 0, TAU); g.arc(cx - r * 0.85, cy + 8, r * 0.72, 0, TAU); g.fill();
      g.restore();
    }
    // dải mặt đất/cỏ đêm có đường chân trời đen sắc
    const grd = g.createLinearGradient(0, hz, 0, c.H);
    grd.addColorStop(0, '#1D332B'); grd.addColorStop(0.38, '#13221D'); grd.addColorStop(1, '#0B0D12');
    g.fillStyle = grd; g.fillRect(0, hz, c.W, c.H - hz);
    g.fillStyle = '#090B0E'; g.fillRect(0, hz - 3, c.W, 6);
  },
  tag(c, str, x, y, k, role = 'accent') {            // hộp đen bo tròn viền trắng + thanh nhấn vàng (đúng kiểu caption/banner ammedia9192)
    if (k <= 0) return null;
    const b = c.text(str, x, y, { size: 54, k: 0, maxW: 820 }), w = b.x1 - b.x0 + 68, h = b.y1 - b.y0 + 34;
    c.enter(k, [x - w / 2, b.y0 - 17, w, h], () => {
      c.draw([
        { k: 'rect', x: -w / 2, y: b.y0 - 17 - y, w, h, rad: 16, role: '#101319' },
        { k: 'rect', x: -w / 2 + 18, y: b.y0 - 17 - y + h - 8, w: w - 36, h: 6, rad: 3, role },
      ], { x, y, s: 1, plain: true });
    });
    return c.text(str, x, y - 2, { size: 54, k: c.clamp(k * 1.6 - 0.4), role: 'ink', maxW: 820, enter: 'pop' });
  },
  ground(c, x, y, w) {
    c.draw([{ k: 'circle', x: 0, y: 0, r: 1, rx: w * 0.48, ry: w * 0.08, role: '#090C10' }], { x, y, s: 1, alpha: 0.65, plain: true });
  },
};

const RAW = { flat, boil, iso, hud, synth, sticker, swiss, spy, picto, zoom, flow, sketch, gallery, halftone, comic, pixel16, sprite8, silhouette, cutout, lineart, vox, story };
export const LOOKS = Object.fromEntries(Object.entries(RAW).map(([k, v]) => [k, { ...base, ...v }]));
export const LOOK_NAMES = Object.keys(RAW);
/** token mặc định chung ← token của look ← styles/<id>.json → html */
export function mergeLook(cfg) {
  const kind = RAW[cfg.look] ? cfg.look : 'flat';
  return { ...deep(deep(D, RAW[kind].tokens), cfg), look: kind };
}
