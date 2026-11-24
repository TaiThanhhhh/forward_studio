// Beat = "ngữ pháp giải thích" của engine html: mỗi beat nhận params (dữ liệu từ storyboard) và trả về {cues, texts, draw(c)}.
// Beat không biết look: mọi nét đặc trưng (tiêu đề, cột, nhãn, mũi tên, vòng nhấn, mặt đất) gọi qua c.K (looks.js).
// Mốc thời gian tính theo số frame của shot (N, do timeline theo VO quyết định) — không có mốc tuyệt đối nào trong mã;
// params.hit (0..1) cho phép storyboard đặt khoảnh khắc chính đúng vào từ khoá trong lời đọc.
const hd = (P) => ({ kicker: P.kicker, title: P.title, index: P.index, size: P.title_size });
const names = (...xs) => xs.filter((x) => x !== undefined && x !== null && x !== '').map(String);
const bob = (c, seed = 0, a = 8) => Math.sin((c.f + seed * 17) * 0.09) * a;      // trôi nhẹ liên tục (không frame nào đứng yên)
const hasHdr = (P) => !!(P.title || P.kicker || P.index);
function drawHeader(c, P, k, minimal = false) {
  if (!hasHdr(P)) return c.A.top;
  if (minimal && !P.title && !P.index && P.kicker) {
    c.g.save(); c.g.globalAlpha *= 0.55;
    const kb = c.text(P.kicker, c.A.cx, c.A.top + 28, { size: 24, font: 'mono', role: 'dim', k, enter: 'type', weight: 600 });
    c.g.restore();
    return kb.y1 + 16;
  }
  return c.K.header(c, hd(P), k);
}
function fitText(c, str, x, sizes, o = {}) {
  let pick = null;
  for (const size of sizes) {
    const b = c.text(str, x, 0, { ...o, size, k: 0 });
    pick = { size, b, h: b.y1 - b.y0 };
    if (!o.maxH || pick.h <= o.maxH) return pick;
  }
  return pick;
}
const tagY = (c, y) => Math.min(c.A.bottom - 36, y);

// ================= BIẾN THỂ BỐ CỤC (P.layout; Python chọn và xoay vòng theo video — engines/html/__init__.py LAYOUTS) =================
function titleLeft(c0, P) {                           // chữ lớn căn trái, vật khổng lồ tràn mép phải-dưới
  return {
    cues: [{ f: 1, name: 'whoosh_soft' }, { f: 9, name: 'pop' }], texts: names(P.kicker, P.title, P.sub),
    draw(c) {
      const x0 = c.A.x0 + 10, spanH = c.A.bottom - c.A.top;
      const s = Math.min(280, spanH * 0.27), ix = c.W - 195, iy = Math.min(c.A.bottom - s * 0.65, 1120) + bob(c, 1, 10);
      if (P.icon) {
        if (P.icon_role === 'hot') c.K.halo(c, ix, iy, s * 0.8);
        c.enter(c.k(5, 12), [ix - s, iy - s, 2 * s, 2 * s], () => c.icon(P.icon, { x: ix, y: iy, s, role: P.icon_role, p: P.icon_p ?? 0.6, rot: Math.sin(c.f * 0.02) * 0.06 }));
      }
      if (P.kicker) c.text(P.kicker, x0, c.A.top + 42, { size: 32, font: 'mono', role: 'dim', align: 'left', k: c.k(1, 8), enter: 'type', weight: 600 });
      const topY = c.A.top + (P.kicker ? 96 : 36), subMaxW = P.icon ? 500 : 760;
      const sf = P.sub ? fitText(c, P.sub, x0, [54, 46, 40], { align: 'left', maxW: subMaxW, maxH: 180 }) : null;
      const maxTitleH = Math.max(200, c.A.bottom - 36 - topY - (sf ? sf.h + 56 : 20));
      const tf = fitText(c, P.title, x0, [124, 106, 90, 76, 64], { align: 'left', maxW: 760, lh: 1.02, maxH: maxTitleH });
      const ty = topY + 24 - tf.b.y0;
      const b = c.text(P.title, x0, ty, { size: tf.size, align: 'left', k: c.k(2, 12), maxW: 760, lh: 1.02 });
      if (P.sub && sf) c.text(P.sub, x0, Math.min(c.A.bottom - 36 - sf.b.y1, b.y1 + 48 - sf.b.y0), { size: sf.size, align: 'left', role: 'accent', k: c.k(12, 10), maxW: subMaxW });
    },
  };
}
function titleHero(c0, P) {                           // vật chiếm gần hết khung làm nền, chữ đè lên ở phần ba dưới
  return {
    cues: [{ f: 1, name: 'whoosh' }, { f: 12, name: 'hit', kick: 0.5 }], texts: names(P.kicker, P.title, P.sub),
    draw(c) {
      const topY = c.A.top + (P.kicker ? 76 : 24), spanH = c.A.bottom - topY;
      const s = Math.min(340, spanH * 0.34) * (1 + 0.04 * Math.sin(c.f * 0.06)), cy = topY + spanH * 0.42;
      if (P.icon) c.enter(c.k(1, 14), [c.A.cx - s, cy - s, 2 * s, 2 * s], () => c.icon(P.icon, { x: c.A.cx, y: cy, s, role: P.icon_role, p: P.icon_p ?? 0.6, alpha: 0.9 }), 'pop');
      if (P.kicker) c.text(P.kicker, c.A.cx, c.A.top + 32, { size: 32, font: 'mono', role: 'dim', k: c.k(1, 8), enter: 'type', weight: 600 });
      const subRes = P.sub ? 112 : 24, maxTH = Math.max(160, spanH * 0.48);
      const tf = fitText(c, P.title, c.A.cx, [112, 96, 82, 70], { maxW: 900, lh: 1.04, maxH: maxTH });
      const baseY = c.A.bottom - 36 - subRes - tf.b.y1;
      const ty = Math.max(topY + 20 - tf.b.y0, baseY);
      const b = c.text(P.title, c.A.cx, ty, { size: tf.size, maxW: 900, lh: 1.04, enter: 'slam', k: c.k(10, 12) });
      if (P.sub) c.K.tag(c, P.sub, c.A.cx, tagY(c, b.y1 + 88), c.k(16, 10));
    },
  };
}
function counterGiant(c0, P) {                        // một con số khổng lồ + thanh tiến độ mảnh chạy theo
  const N = c0.N, f0 = 4, f1 = Math.max(f0 + 10, Math.round((P.land ?? 0.6) * N)), from = Number(P.from ?? 0), to = Number(P.to ?? P.value ?? 0), dec = P.decimals ?? 0;
  const final = `${P.prefix || ''}${c0.fmtNum(to, dec)}${P.suffix || ''}`;
  return {
    cues: [...Array.from({ length: Math.min(10, Math.floor((f1 - f0) / 3)) }, (_, i) => ({ f: f0 + i * 3, name: 'tick' })), { f: f1, name: 'hit', kick: 0.8 }],
    texts: names(P.title, final, P.unit, P.label),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), k = c.clamp((c.f - f0) / (f1 - f0)), e = c.EASE.out(k), landed = c.f >= f1;
      const txt = landed ? final : `${P.prefix || ''}${c.fmtNum(c.lerp(from, to, e), dec)}${P.suffix || ''}`;
      const botNeed = 68 + (P.unit ? 92 : 0) + (P.label ? 104 : 0) + 36;
      const avail = Math.max(160, c.A.bottom - botNeed - yb - 24);
      const numSize = Math.min(final.length > 5 ? 210 : 280, Math.max(116, avail * 0.78));
      const cy = yb + 24 + numSize * 0.84 + Math.max(0, (avail - numSize * 1.06) * 0.48);
      const sc = landed ? 1 + Math.max(0, 1 - (c.f - f1) / 8) * 0.16 : 0.92 + 0.08 * e;
      c.g.save(); c.g.translate(c.A.cx, cy - numSize * 0.3); c.g.scale(sc, sc); c.g.rotate(landed ? 0 : (1 - e) * -0.05); c.g.translate(-c.A.cx, -(cy - numSize * 0.3));
      const nb = c.text(txt, c.A.cx, cy, { size: numSize, quiet: !landed, enter: 'none', maxW: 940, track: -0.02, weight: 900 });
      c.g.restore();
      const bw = 760, bx = c.A.cx - bw / 2, barY = nb.y1 + 26;
      c.g.fillStyle = c.col('dim'); c.g.fillRect(bx, barY, bw, 10);
      c.g.fillStyle = c.col(P.role || 'hot'); c.g.fillRect(bx, barY, bw * Math.max(0.01, e), 10);
      if (P.icon) c.icon(P.icon, { x: bx + bw * e, y: barY + 5, s: 40, role: P.icon_role || 'accent', p: e });
      let curY = barY + 24;
      if (P.unit) { const ub = c.text(P.unit, c.A.cx, curY + 58, { size: 58, role: 'accent', k: c.k(6, 8), maxW: 820 }); curY = ub.y1; }
      if (P.label) c.K.tag(c, P.label, c.A.cx, tagY(c, curY + 82), c.k(f1 + 4, 9));
    },
  };
}
function counterBar(c0, P) {                          // cột dâng như mực nước, con số cưỡi trên mặt cột
  const N = c0.N, f0 = 6, f1 = Math.max(f0 + 12, Math.round((P.land ?? 0.6) * N)), from = Number(P.from ?? 0), to = Number(P.to ?? P.value ?? 0), dec = P.decimals ?? 0;
  const final = `${P.prefix || ''}${c0.fmtNum(to, dec)}${P.suffix || ''}`, top = Math.max(Math.abs(to), Math.abs(from), 1e-9);
  return {
    cues: [{ f: f0, name: 'riser' }, { f: f1, name: 'ding', kick: 0.6 }], texts: names(P.title, final, P.unit, P.label),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), botNeed = (P.icon ? 96 : 16) + (P.unit ? 74 : 0) + (P.label ? 96 : 0) + 36;
      const base = Math.min(c.A.bottom - botNeed, 1160), Hmax = Math.max(170, Math.min(480, base - yb - 150));
      const k = c.clamp((c.f - f0) / (f1 - f0)), e = c.EASE.out(k);
      const v = c.lerp(from, to, e), h = Hmax * Math.abs(v) / top * (0.25 + 0.75) + 6, x = c.A.cx - 115, w = 230, landed = c.f >= f1;
      c.g.fillStyle = c.col('dim'); c.g.globalAlpha = 0.35; c.g.fillRect(x, base - Hmax, w, Hmax); c.g.globalAlpha = 1;
      const wav = (i) => Math.sin(c.f * 0.25 + i * 0.9) * 8 * (1 - (landed ? Math.min(1, (c.f - f1) / 20) : 0));
      c.draw([{ k: 'poly', pts: [[x, base], [x, base - h + wav(0)], [x + w * 0.33, base - h + wav(1)], [x + w * 0.66, base - h + wav(2)], [x + w, base - h + wav(3)], [x + w, base]], role: P.role || 'cold' }], { s: 1, plain: true });
      c.text(landed ? final : `${P.prefix || ''}${c.fmtNum(v, dec)}${P.suffix || ''}`, c.A.cx, Math.max(yb + 108, base - h - 32), { size: 108, quiet: !landed, enter: 'none', maxW: 820 });
      let y = base;
      if (P.icon) { c.icon(P.icon, { x: c.A.cx, y: y + 54, s: 44, role: P.icon_role, p: e }); y += 96; }
      if (P.unit) { const ub = c.text(P.unit, c.A.cx, y + 60, { size: 52, role: 'accent', k: c.k(6, 8), maxW: 760 }); y = ub.y1; }
      if (P.label) c.K.tag(c, P.label, c.A.cx, tagY(c, y + 78), c.k(f1 + 4, 9));
    },
  };
}
// số chữ số thập phân của một giá trị: riêng của mục → chung của beat → tự đếm từ chính giá trị (tối đa 2),
// để 1.33 không bao giờ hiện thành "1" khi người viết quên `decimals`
const decOf = (o, P, key = 'value') => o.decimals ?? P.decimals ?? Math.min(2, (String(o[key] ?? '').split('.')[1] || '').length);

function compareSplit(c0, P) {                        // màn hình chia đôi: hai vật khổng lồ đối mặt, đường chia trượt vào
  const l = P.left || {}, r = P.right || {};
  const lab = (o) => (o.value !== undefined ? `${c0.fmtNum(o.value, decOf(o, P))}${o.unit ? ' ' + o.unit : ''}` : '');
  const win = (Number(l.value) || 0) >= (Number(r.value) || 0) ? 'l' : 'r';
  return {
    cues: [{ f: 3, name: 'whoosh' }, { f: 12, name: 'pop' }, { f: 20, name: 'pop' }, { f: 32, name: 'hit', kick: 0.6 }],
    texts: names(P.title, l.label, r.label, lab(l), lab(r), P.result),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), kd = c.EASE.out(c.k(3, 12)), mx = c.A.cx;
      const y0 = Math.max(yb + 26, c.A.top + 36), y1 = c.A.bottom - (P.result ? 102 : 24);
      const availH = Math.max(190, y1 - y0 - 155), sBase = Math.min(148, availH * 0.42), cy = y0 + availH * 0.5;
      c.g.save(); c.g.strokeStyle = c.col('ink'); c.g.lineWidth = 4; c.g.beginPath(); c.g.moveTo(mx + 50, y0 + (y1 - y0) * (1 - kd)); c.g.lineTo(mx - 50, y1); c.g.stroke(); c.g.restore();
      [[l, mx - 245, 'l', 12], [r, mx + 245, 'r', 20]].forEach(([o, x, side, f0]) => {
        const k = c.k(f0, 12), s = sBase * (side === win ? 1.1 : 0.94), y = cy + bob(c, f0, 8);
        c.enter(k, [x - s, y - s, 2 * s, 2 * s], () => c.icon(o.icon || 'dot', { x, y, s, role: o.role || (side === win ? 'hot' : 'cold'), p: o.p ?? 0.6 }), 'pop');
        let ty = cy + sBase * 1.1 + 66;
        if (lab(o)) { const vb = c.text(lab(o), x, Math.min(y1 - (o.label ? 68 : 16), ty), { size: 58, k: c.k(f0 + 6, 8), role: side === win ? 'accent' : 'ink', maxW: 410 }); ty = vb.y1 + 54; }
        if (o.label) c.K.label(c, o.label, x, Math.min(y1 - 12, ty), c.k(f0 + 8, 8), { align: 'center', maxW: 390, size: 42 });
      });
      if (P.vs) { const k = c.k(26, 6); c.enter(k, [mx - 70, cy - 70, 140, 140], () => c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'bg' }, { k: 'circle', x: 0, y: 0, r: 1, role: 'ink', fill: false }], { x: mx, y: cy, s: 62 }), 'pop');
        c.text(P.vs, mx, cy + 18, { size: 46, k, enter: 'none', font: 'mono', quiet: true }); }
      if (P.result) c.K.tag(c, P.result, mx, tagY(c, y1 + 64), c.k(32, 9));
    },
  };
}
function compareBalance(c0, P) {                      // cân đòn: hai vật trên hai đĩa, cân nghiêng về bên nặng hơn
  const l = P.left || {}, r = P.right || {}, lv = Number(l.value) || 0, rv = Number(r.value) || 0;
  const lab = (o) => (o.value !== undefined ? `${c0.fmtNum(o.value, decOf(o, P))}${o.unit ? ' ' + o.unit : ''}` : '');
  const tilt = Math.max(-0.28, Math.min(0.28, (rv - lv) / Math.max(lv, rv, 1e-9) * 0.36));
  return {
    cues: [{ f: 8, name: 'thunk' }, { f: 16, name: 'thunk' }, { f: 26, name: 'creak', kick: 0.4 }], texts: names(P.title, l.label, r.label, lab(l), lab(r), P.result),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10));
      const kt = c.k(22, 22, false), wob = Math.sin(c.f * 0.35) * 0.05 * Math.max(0, 1 - (c.f - 22) / 30) * (c.f > 22 ? 1 : 0);
      const baseY = c.A.bottom - (P.result ? 114 : 30), availH = Math.max(240, baseY - yb - 40);
      const a = tilt * c.EASE.spring(kt) + wob, px = c.A.cx, py = yb + 40 + availH * 0.28, arm = 305, panDrop = Math.min(125, availH * 0.24);
      c.draw([{ k: 'line', pts: [[px, py], [px, baseY - 12]], role: 'dim', w: 1.2 }, { k: 'poly', pts: [[px - 24, py + 4], [px + 24, py + 4], [px, py - 30]], role: 'accent' },
              { k: 'rect', x: px - 120, y: baseY - 22, w: 240, h: 22, rad: 8, role: 'dim' }], { s: 1, plain: true });
      c.draw([{ k: 'line', pts: [[px - arm * Math.cos(a), py - arm * Math.sin(a)], [px + arm * Math.cos(a), py + arm * Math.sin(a)]], role: 'ink', w: 1.6 }], { s: 1 });
      [[l, -1, 8], [r, 1, 16]].forEach(([o, sd, f0]) => {
        const ex = px + sd * arm * Math.cos(a), ey = py + sd * arm * Math.sin(a), panY = ey + panDrop, panR = Math.min(96, availH * 0.19);
        c.draw([{ k: 'line', pts: [[ex, ey], [ex - panR * 0.82, panY]], role: 'dim', w: 0.5 }, { k: 'line', pts: [[ex, ey], [ex + panR * 0.82, panY]], role: 'dim', w: 0.5 },
                { k: 'arc', x: ex, y: panY, r: panR, a0: 0, a1: Math.PI, role: 'ink', w: 1.2 }], { s: 1, plain: true });
        c.enter(c.k(f0, 10), [ex - 80, panY - 150, 160, 150], () => c.icon(o.icon || 'dot', { x: ex, y: panY - 68, s: 68, role: o.role, p: o.p ?? 0.6 }), 'slide');
        let ty = panY + panR + 46;
        if (lab(o)) { const vb = c.text(lab(o), ex, Math.min(baseY - (o.label ? 66 : 16), ty), { size: 48, k: c.k(f0 + 6, 8), role: 'accent', maxW: 380 }); ty = vb.y1 + 48; }
        if (o.label) c.K.label(c, o.label, ex, Math.min(baseY - 12, ty), c.k(f0 + 8, 8), { align: 'center', maxW: 360, size: 38 });
      });
      if (P.result) c.K.tag(c, P.result, px, tagY(c, c.A.bottom - 36), c.k(30, 9));
    },
  };
}
function factStamp(c0, P) {                           // câu chốt + cụm nhấn đóng như con dấu (đập xuống, rung)
  const fs0 = Math.round(c0.N * 0.42);
  return {
    cues: [{ f: 2, name: 'whoosh_soft' }, { f: fs0, name: 'stamp', kick: 1 }], texts: names(P.kicker, P.text, P.em),
    draw(c) {
      if (P.kicker) c.text(P.kicker, c.A.cx, c.A.top + 38, { size: 32, font: 'mono', role: 'dim', k: c.k(1, 8), weight: 600, enter: 'type' });
      const topY = c.A.top + (P.kicker ? 86 : 26), botY = c.A.bottom - 44, iconH = P.icon ? 170 : 0;
      const ef = P.em ? fitText(c, P.em.toUpperCase(), 0, [74, 62, 52], { maxW: 720, weight: 900, maxH: 130 }) : null;
      const emReserve = ef ? ef.h + 108 : 0;
      const tf = fitText(c, P.text, c.A.cx, [96, 82, 70, 58, 48], { maxW: 860, lh: 1.08, maxH: Math.max(150, botY - topY - iconH - emReserve - 20) });
      const totalH = iconH + tf.h + emReserve, startY = topY + Math.max(0, (botY - topY - totalH) / 2);
      if (P.icon) c.icon(P.icon, { x: c.A.cx, y: startY + 78 + bob(c), s: 82, role: P.icon_role, alpha: c.k(3, 9) });
      const b = c.text(P.text, c.A.cx, startY + iconH - tf.b.y0, { size: tf.size, k: c.k(4, 12), maxW: 860, lh: 1.08 });
      if (P.em && ef) {
        const k = c.k(fs0, 5, false), sc = c.lerp(2.4, 1, c.EASE.out(k)), y = Math.min(botY - ef.h / 2 - 22, b.y1 + 54 + ef.h / 2);
        if (k > 0) {
          c.g.save(); c.g.translate(c.A.cx, y); c.g.rotate(-0.1); c.g.scale(sc, sc); c.g.globalAlpha *= Math.min(1, k * 2);
          const t = c.text(P.em.toUpperCase(), 0, -(ef.b.y0 + ef.b.y1) / 2, { size: ef.size, role: 'hot', enter: 'none', quiet: k < 1, maxW: 720, weight: 900 });
          c.g.strokeStyle = c.col('hot'); c.g.lineWidth = 9; c.g.strokeRect(t.x0 - 32, t.y0 - 22, t.x1 - t.x0 + 64, t.y1 - t.y0 + 42);
          c.g.restore();
        }
      }
    },
  };
}
function factLeft(c0, P) {                            // gõ chữ căn trái, vạch màu bên lề, cụm nhấn đổi màu
  const fe = Math.round(c0.N * 0.45);
  return {
    cues: [{ f: 2, name: 'typing:1.0' }, { f: fe, name: 'pop', kick: 0.4 }], texts: names(P.kicker, P.text, P.em),
    draw(c) {
      const x = c.A.x0 + 56, topY = c.A.top + 32, botY = c.A.bottom - 36, maxW = 820, emW = P.icon ? 620 : 820;
      const kickH = P.kicker ? 64 : 0;
      const ef = P.em ? fitText(c, P.em, x, [82, 68, 56, 48], { align: 'left', maxW: emW, maxH: 200 }) : null;
      const emReserve = ef ? ef.h + 54 : 0;
      const tf = fitText(c, P.text, x, [92, 80, 68, 56, 48], { align: 'left', maxW, lh: 1.08, maxH: Math.max(160, botY - topY - kickH - emReserve) });
      const totalH = kickH + tf.h + emReserve, startY = topY + Math.max(0, (botY - topY - totalH) / 2);
      c.g.fillStyle = c.col('accent'); c.g.fillRect(c.A.x0 + 10, startY - 12, 12, Math.min(botY - startY + 12, totalH + 24) * c.EASE.out(c.k(1, 14)));
      if (P.kicker) c.text(P.kicker, x, startY + 28, { size: 30, font: 'mono', role: 'dim', align: 'left', k: c.k(1, 6), weight: 600, enter: 'type' });
      const b = c.text(P.text, x, startY + kickH - tf.b.y0, { size: tf.size, align: 'left', k: c.k(3, Math.max(14, Math.round(c.N * 0.3))), enter: 'type', maxW, lh: 1.08 });
      if (P.em && ef) c.text(P.em, x, Math.min(botY - ef.b.y1, b.y1 + 48 - ef.b.y0), { size: ef.size, align: 'left', role: 'hot', k: c.k(fe, 8), enter: 'slide', maxW: emW });
      if (P.icon) c.icon(P.icon, { x: c.W - 205, y: Math.min(c.A.bottom - 95, startY + totalH - 35) + bob(c, 3, 10), s: 90, role: P.icon_role, alpha: c.k(6, 10) });
    },
  };
}
function processPath(c0, P) {                         // các bước nằm trên một đường cong, chấm sáng chạy dọc đường
  const steps = (P.steps || []).slice(0, 4), N = c0.N, n = Math.max(1, steps.length), stride = Math.max(8, Math.floor(0.72 * N / n));
  return {
    cues: steps.map((_, i) => ({ f: 6 + i * stride, name: i === steps.length - 1 ? 'ding' : 'pop' })), texts: names(P.title, ...steps.map((s) => s.label)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), y0 = Math.max(c.A.top + 110, (Number(yb) || 0) + 96), y1 = Math.max(y0 + 200, c.A.bottom - 80);
      const pts = steps.map((_, i) => [i % 2 ? 750 : 330, y0 + i * ((y1 - y0) / Math.max(1, n - 1 || 1))]);
      const iconS = Math.min(72, Math.max(46, (y1 - y0) / Math.max(1, n - 1) * 0.34));
      const prog = c.clamp((c.f - 6) / Math.max(1, stride * (n - 1))), seg = [];
      for (let i = 0; i < pts.length - 1; i++) for (let j = 0; j <= 12; j++) { const t = j / 12, a = pts[i], b = pts[i + 1]; seg.push([c.lerp(a[0], b[0], t * t * (3 - 2 * t)), c.lerp(a[1], b[1], t)]); }
      if (seg.length) c.draw([{ k: 'line', pts: seg, role: 'dim', w: 0.5, dash: [2, 2] }], { s: 1, plain: true });
      if (seg.length > 1) { const q = seg[Math.min(seg.length - 1, Math.floor(prog * (seg.length - 1)))]; c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'accent' }], { x: q[0], y: q[1], s: 16 + Math.sin(c.f * 0.4) * 4, plain: true }); }
      steps.forEach((s, i) => {
        const [x, y] = pts[i], f0 = 6 + i * stride, k = c.k(f0, 9), on = c.fs >= f0, left = x < c.A.cx;
        c.enter(k, [x - iconS, y - iconS, iconS * 2, iconS * 2], () => c.icon(s.icon || 'dot', { x, y: y + (on ? bob(c, i, 5) : 0), s: iconS, role: s.role, p: s.p ?? 0.6 }));
        if (on && k >= 1) c.K.ring(c, x, y, iconS * 1.35, c.k(f0 + 4, 8));
        c.K.label(c, s.label, left ? x + 175 : x - 135, y + 14, c.k(f0 + 3, 8), { align: left ? 'left' : 'right', maxW: 370, size: 42 });
      });
    },
  };
}

// ================= VÒNG 10 — bố cục/beat mà DỮ LIỆU lái chuyển động (số thật → số biểu tượng, nhịp tim, quãng chạy…) =================
const num = (v, d = 0) => { const x = Number(v); return Number.isFinite(x) ? x : d; };
const fmtV = (c0, v, dec, P) => `${P.prefix || ''}${c0.fmtNum(v, dec)}${P.suffix || ''}`;
const decN = (x) => (Number.isInteger(x) ? 0 : Math.min(2, (String(x).split('.')[1] || '').length));
const nice = (x) => {                                 // bội số "đẹp" ≥ x: 1 · 2 · 2.5 · 5 × 10^k
  if (!(x > 0)) return 1;
  const p = 10 ** Math.floor(Math.log10(x));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * p >= x * 0.9999) return +(m * p).toPrecision(6);
  return 10 * p;
};
// isotype: mỗi biểu tượng = `per` đơn vị THẬT. Số nguyên ≤ cap → đếm từng cái; lớn hơn → per là bội số đẹp (10, 50…);
// giá trị nhỏ có phần lẻ (1.33) → per 0.1 để khác biệt vẫn thấy được
const perUnit = (vals, cap = 100, given = 0) => {
  if (given > 0) return given;
  const vmax = Math.max(1e-9, ...vals.map((v) => Math.abs(v)));
  if (vmax > cap) return nice(vmax / cap);
  return vals.every((v) => Number.isInteger(v)) || vmax >= 8 ? 1 : nice(vmax / 16);
};
/** lưới isotype: khối 10 (5 × 2), các khối xếp lưới vừa khung. o: {maxS, anchor:'center'|'bottom', up} → {s, pos(i)} */
function unitGrid(n, box, o = {}) {
  const cnt = Math.max(1, Math.ceil(n - 1e-9)), nb = Math.ceil(cnt / 10), gap = 0.55, cols = cnt <= 5 ? cnt : 5, rows = cnt <= 5 ? 1 : 2;
  let best = null;
  for (let bc = 1; bc <= Math.min(nb, 8); bc++) {
    const br = Math.ceil(nb / bc), wu = bc * cols + (bc - 1) * gap, hu = br * rows + (br - 1) * gap;
    const s = Math.min(o.maxS || 130, box.w / wu, box.h / hu);
    if (!best || s > best.s + 1e-6) best = { bc, br, s, wu, hu };
  }
  const { bc, br, s, wu, hu } = best, x0 = box.x + (box.w - wu * s) / 2;
  const y0 = o.anchor === 'bottom' ? box.y + box.h - hu * s : box.y + (box.h - hu * s) / 2;
  return { s, x0, y0, w: wu * s, h: hu * s, pos: (i) => {
    const b = Math.floor(i / 10), j = i % 10, bx = b % bc, byr = Math.floor(b / bc), by = o.up ? br - 1 - byr : byr, jr = Math.floor(j / cols);
    return [x0 + (bx * (cols + gap) + (j % cols) + 0.5) * s, y0 + (by * (rows + gap) + (o.up ? rows - 1 - jr : jr) + 0.5) * s];
  } };
}
// vẽ n biểu tượng (n lẻ → biểu tượng cuối bị cắt theo phần lẻ — quy ước isotype); biểu tượng i rơi vào ô ở frame fOf(i)
function drawUnits(c, grid, n, o) {
  const cnt = Math.ceil(n - 1e-9), s = grid.s * 0.43;
  let shown = 0;
  for (let i = 0; i < cnt; i++) {
    const t = c.f - o.fOf(i); if (t < 0) break;
    shown = Math.min(n, i + 1);
    const [x, y] = grid.pos(i), k = c.clamp(t / 7), dy = (1 - c.EASE.bounce(k)) * -grid.s * 0.8, frac = i === cnt - 1 ? n - (cnt - 1) : 1;
    c.g.save();
    if (frac < 0.999) { c.g.beginPath(); c.g.rect(x - grid.s / 2, y - grid.s, grid.s * frac, grid.s * 2); c.g.clip(); }
    c.icon(o.icon || 'dot', { x, y: y + dy, s, role: o.role, alpha: c.clamp(k * 3), seed: (o.seed || 1) + i, plain: cnt > 150,
                              rot: (c.hash(i, o.seed || 1) - 0.5) * 0.5 * (1 - k) });
    c.g.restore();
  }
  return shown;
}
const legendOf = (c0, per, P, unit) => P.per_label || `${c0.fmtNum(per, decN(per))}${unit ? ' ' + unit : ''}`;
function drawLegend(c, icon, role, txt, x, y, k) {    // "● = 10 people": một biểu tượng nhỏ + giá trị của nó
  if (k <= 0 || !txt) return;
  const b = c.text(`= ${txt}`, 0, 0, { size: 44, k: 0, maxW: 700 }), w = b.x1 - b.x0, x0 = x - (w + 70) / 2;
  c.icon(icon || 'dot', { x: x0 + 24, y: y - 16, s: 24, role, alpha: c.clamp(k * 2) });
  c.text(`= ${txt}`, x0 + 70, y, { size: 44, k, align: 'left', role: 'dim', maxW: 700 });
}

function counterUnits(c0, P) {                        // isotype: đúng số đơn vị rơi vào lưới (khối 10), số đếm chạy theo số biểu tượng
  const N = c0.N, f0 = 6, f1 = Math.max(f0 + 14, Math.round((P.land ?? 0.66) * N)), to = num(P.to ?? P.value), dec = P.decimals ?? decN(to);
  const per = perUnit([to], num(P.max_units, 100), num(P.per)), n = Math.abs(to) / per, cnt = Math.ceil(n - 1e-9);
  const final = fmtV(c0, to, dec, P), legend = per !== 1 || P.per_label ? legendOf(c0, per, P, P.per_unit || P.unit) : '';
  const fOf = (i) => f0 + (f1 - f0) * (cnt > 1 ? i / (cnt - 1) : 0);
  return {
    cues: [...Array.from({ length: Math.min(10, Math.floor(cnt / 10)) }, (_, b) => ({ f: Math.round(fOf(b * 10 + 9)), name: 'tick' })), { f: f1, name: 'ding', kick: 0.5 }],
    texts: names(P.title, final, P.unit, P.label, legend && `= ${legend}`),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), ny = Math.max(yb + 126, c.A.top + 150), landed = c.f >= f1;
      let gy = ny + 48;
      if (P.unit) { const ub = c.text(P.unit, c.A.cx, ny + 76, { size: 50, role: 'accent', k: c.k(4, 8), maxW: 800 }); gy = ub.y1 + 24; }
      const botNeed = (legend ? 62 : 0) + (P.label ? 92 : 0) + 38;
      const grid = unitGrid(n, { x: c.A.x0, y: gy, w: c.A.x1 - c.A.x0, h: Math.max(150, c.A.bottom - botNeed - gy) }, { maxS: 120 });
      const shown = drawUnits(c, grid, n, { icon: P.icon, role: P.icon_role || P.role, fOf, seed: 7 });
      const v = Math.sign(to) * Math.min(Math.abs(to), shown * per), pop = landed ? 1 + Math.max(0, 1 - (c.f - f1) / 7) * 0.1 : 1;
      c.g.save(); c.g.translate(c.A.cx, ny - 44); c.g.scale(pop, pop); c.g.translate(-c.A.cx, -(ny - 44));
      c.text(landed ? final : fmtV(c, v, dec, P), c.A.cx, ny, { size: 132, quiet: !landed, enter: 'none', maxW: 900, weight: 900 });
      c.g.restore();
      let ly = grid.y0 + grid.h + 52;
      if (legend) { drawLegend(c, P.icon, P.icon_role || P.role, legend, c.A.cx, Math.min(c.A.bottom - (P.label ? 102 : 34), ly), c.k(f0 + 6, 8)); ly += 78; }
      if (P.label) c.K.tag(c, P.label, c.A.cx, tagY(c, ly + (legend ? 14 : 26)), c.k(f1 + 4, 9));
    },
  };
}

// bánh xe số kiểu đồng hồ km: chữ số hàng p chỉ quay khi các hàng thấp hơn đang qua 9 → 0 (nhớ cơ khí)
const wheel = (V, p) => {
  const base = 10 ** p, d = Math.floor(V / base) % 10;
  if (p === 0) return ((V % 10) + 10) % 10;
  const r = (V % base) / base;
  return d + (r > 0.9 ? (r - 0.9) * 10 : 0);
};
/** ô chữ số mono của một chuỗi số: [{ch, digit, p}] (p = hàng của chữ số, 0 = hàng đơn vị nhỏ nhất) */
const cellsOf = (str) => {
  let p = 0; const out = [];
  for (let i = str.length - 1; i >= 0; i--) { const ch = str[i], dg = ch >= '0' && ch <= '9'; out.unshift({ ch, digit: dg, p: dg ? p++ : -1 }); }
  return out;
};
function counterOdometer(c0, P) {                     // đồng hồ cơ: từng bánh xe chữ số lăn, hàng cao chỉ nhích khi hàng thấp qua 9
  const N = c0.N, f0 = 5, f1 = Math.max(f0 + 14, Math.round((P.land ?? 0.62) * N)), from = num(P.from), to = num(P.to ?? P.value), dec = P.decimals ?? decN(to);
  const body = c0.fmtNum(Math.abs(to), dec), cells = cellsOf(body), sc = 10 ** dec, final = fmtV(c0, to, dec, P);
  return {
    cues: [{ f: f0, name: 'riser' }, ...Array.from({ length: Math.min(8, Math.floor((f1 - f0) / 4)) }, (_, i) => ({ f: f0 + 2 + i * 4, name: 'click' })), { f: f1, name: 'ding', kick: 0.6 }],
    texts: names(P.title, final, P.unit, P.label),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), landed = c.f >= f1;
      const topNeed = P.icon ? 136 : 44, botNeed = (P.unit ? 90 : 0) + (P.label ? 104 : 0) + 52;
      const avail = Math.max(130, c.A.bottom - botNeed - (yb + topNeed));
      const e = c.EASE.out(c.clamp((c.f - f0) / (f1 - f0))), V = Math.round(Math.abs(c.lerp(from, to, e)) * sc * 1000) / 1000;
      const Vp = Math.abs(c.lerp(from, to, c.EASE.out(c.clamp((c.f - 1 - f0) / (f1 - f0))))) * sc;
      const size = Math.min(200, 880 / Math.max(3, cells.length) * 1.5, Math.max(92, avail * 0.72)), m = c.text('0', 0, 0, { size, font: 'mono', k: 0, track: 0 });
      const cw = m.x1 - m.x0, ch = size * 1.18, x0 = c.A.cx - cw * cells.length / 2;
      const top = yb + topNeed + Math.max(0, (avail - ch) * 0.45), cy = top + size * 0.86;
      c.g.save(); c.g.fillStyle = c.mix(c.pal.bg, c.col('ink'), 0.1); c.g.fillRect(x0 - 26, top - 22, cw * cells.length + 52, ch + 44); c.g.restore();
      c.draw([{ k: 'rect', x: x0 - 26, y: top - 22, w: cw * cells.length + 52, h: ch + 44, rad: 18, role: 'dim', fill: false }], { s: 1, plain: true });
      cells.forEach((cl, i) => {
        const x = x0 + cw * (i + 0.5);
        if (!cl.digit || landed) return;
        const w = wheel(V, cl.p), d0 = Math.floor(w), fr = w - d0, speed = Math.abs(V - Vp) / 10 ** cl.p;   // tốc độ bánh xe (số/frame)
        const lead = V < 10 ** cl.p && cl.p > 0;                                 // chữ số đầu chưa tới: bánh xe tối (số 0 mờ)
        c.g.save(); c.g.beginPath(); c.g.rect(x - cw / 2 + 3, top, cw - 6, ch); c.g.clip();
        for (const [dg, off] of [[d0, -fr], [(d0 + 1) % 10, 1 - fr], [(d0 + 9) % 10, -1 - fr]]) {
          const y = cy + off * ch, al = speed > 0.6 ? 0.55 : 1;
          if (Math.abs(off) > 1.05) continue;
          c.g.globalAlpha = al * (lead ? 0.3 : 1);
          c.text(String(dg), x, y, { size, font: 'mono', quiet: true, enter: 'none', track: 0, role: 'ink' });
        }
        c.g.restore();
      });
      if (landed) {                                     // đứng: cả dãy số là MỘT dòng chữ mono trùng khít các ô (OCR đọc được)
        c.g.save(); c.g.beginPath(); c.g.rect(x0, top, cw * cells.length, ch); c.g.clip();
        c.text(body, c.A.cx, cy, { size, font: 'mono', enter: 'none', track: 0, maxW: 2000 });
        c.g.restore();
      } else cells.forEach((cl, i) => { if (!cl.digit) c.text(cl.ch, x0 + cw * (i + 0.5), cy, { size, font: 'mono', quiet: true, enter: 'none', track: 0 }); });
      c.g.save(); c.g.globalAlpha *= 0.35; c.g.fillStyle = c.pal.bg; c.g.fillRect(x0 - 20, cy - size * 0.36 - 2, cw * cells.length + 40, 4); c.g.restore();   // khe giữa bánh xe
      const sgn = to < 0 ? '-' : '';
      if (P.prefix || sgn) c.text(`${sgn}${P.prefix || ''}`, x0 - 40, cy, { size: size * 0.6, align: 'right', role: 'accent', k: c.k(3, 8) });
      if (P.suffix) c.text(P.suffix, x0 + cw * cells.length + 40, cy, { size: size * 0.6, align: 'left', role: 'accent', k: c.k(3, 8) });
      let y = top + ch + 28;
      if (P.unit) { const ub = c.text(P.unit, c.A.cx, y + 60, { size: 58, role: 'accent', k: c.k(4, 8), maxW: 840 }); y = ub.y1; }
      if (P.icon) c.icon(P.icon, { x: c.A.cx, y: Math.max(yb + 62, top - 82) + bob(c, 2, 6), s: 56, role: P.icon_role, p: e });
      if (P.label) c.K.tag(c, P.label, c.A.cx, tagY(c, y + 82), c.k(f1 + 4, 9));
    },
  };
}

function counterFlap(c0, P) {                         // bảng lật (split-flap): mỗi ô lật qua từng chữ số tới đích, ô sau trễ hơn ô trước
  const N = c0.N, f0 = 4, f1 = Math.max(f0 + 16, Math.round((P.land ?? 0.66) * N)), to = num(P.to ?? P.value), dec = P.decimals ?? decN(to);
  const body = fmtV(c0, to, dec, P), cells = cellsOf(body), FL = 3;          // một lần lật = 3 frame (lá trên gập · lá dưới mở)
  const fromV = Math.round(Math.abs(num(P.from)) * 10 ** dec);
  const plan = cells.map((cl, i) => {
    if (!cl.digit) return null;
    const st = f0 + i * 2, tgt = +cl.ch, a = Math.floor(fromV / 10 ** cl.p) % 10;     // chữ số xuất phát cùng hàng của `from`
    const base = (tgt - a + 10) % 10, avail = Math.max(0, Math.floor((f1 - st) / FL)), laps = Math.max(0, Math.floor((avail - base) / 10));
    return { st, a, n: base + laps * 10 };
  });
  const last = Math.max(f0 + 1, ...plan.filter(Boolean).map((q) => q.st + q.n * FL));
  return {
    cues: [{ f: f0, name: `typing:${Math.max(0.3, (last - f0) / c0.FPS).toFixed(2)}` }, { f: last, name: 'click' }, { f: last + 2, name: 'ding', kick: 0.5 }],
    texts: names(P.title, body, P.unit, P.label),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), landed = c.f >= last;
      const topNeed = P.icon ? 132 : 42, botNeed = (P.unit ? 90 : 0) + (P.label ? 104 : 0) + 50;
      const avail = Math.max(130, c.A.bottom - botNeed - (yb + topNeed));
      const size = Math.min(185, 860 / Math.max(3, cells.length) * 1.45, Math.max(88, avail * 0.72)), m = c.text('0', 0, 0, { size, font: 'mono', k: 0, track: 0 });
      const cw = m.x1 - m.x0, gap = cw * 0.08, ch = size * 1.22, x0 = c.A.cx - cw * cells.length / 2;
      const top = yb + topNeed + Math.max(0, (avail - ch) * 0.45), cy = top + size * 0.84, hinge = top + ch / 2;
      const plate = c.mix(c.pal.bg, c.col('ink'), 0.13), plate2 = c.mix(c.pal.bg, c.col('ink'), 0.2);
      cells.forEach((cl, i) => {
        const x = x0 + cw * (i + 0.5), q = plan[i], g = c.g;
        g.save(); g.fillStyle = plate; g.fillRect(x - cw / 2 + gap, top, cw - 2 * gap, ch); g.restore();
        if (!q) { c.text(cl.ch, x, cy, { size, font: 'mono', quiet: true, enter: 'none', track: 0 }); return; }
        const done = c.clamp(Math.floor((c.f - q.st) / FL), 0, q.n), cur = (q.a + done) % 10, nxt = (cur + 1) % 10;
        const ph = done < q.n && c.f >= q.st ? ((c.f - q.st) % FL + 0.5) / FL : 0;
        const half = (dg, upper, sy = 1, shadeK = 0) => {                       // nửa trên/dưới của một chữ số (gập quanh bản lề)
          g.save(); g.beginPath(); g.rect(x - cw / 2 + gap, upper ? top : hinge, cw - 2 * gap, ch / 2); g.clip();
          g.translate(0, hinge); g.scale(1, sy); g.translate(0, -hinge);
          if (shadeK) { g.fillStyle = plate2; g.fillRect(x - cw / 2 + gap, upper ? top : hinge, cw - 2 * gap, ch / 2); }
          c.text(String(dg), x, cy, { size, font: 'mono', quiet: true, enter: 'none', track: 0, role: 'ink' });
          if (shadeK) { g.fillStyle = `rgba(0,0,0,${0.55 * shadeK})`; g.fillRect(x - cw / 2, top, cw, ch); }
          g.restore();
        };
        if (landed) return;
        if (ph <= 0) { half(cur, true); half(cur, false); return; }
        half(nxt, true); half(cur, false);                                       // phía sau: nửa trên số mới, nửa dưới số cũ
        if (ph < 0.5) half(cur, true, Math.cos(ph * Math.PI), ph * 2);           // lá trên (số cũ) gập xuống
        else half(nxt, false, -Math.cos(ph * Math.PI), (1 - ph) * 2);            // lá dưới (số mới) mở ra
      });
      if (landed) c.text(body, c.A.cx, cy, { size, font: 'mono', enter: 'none', track: 0, maxW: 2000 });
      c.g.save(); c.g.fillStyle = c.pal.bg; c.g.fillRect(x0, hinge - 2, cw * cells.length, 4); c.g.restore();      // bản lề
      if (P.icon) c.icon(P.icon, { x: c.A.cx, y: Math.max(yb + 62, top - 82) + bob(c, 2, 6), s: 56, role: P.icon_role });
      let y = top + ch + 26;
      if (P.unit) { const ub = c.text(P.unit, c.A.cx, y + 60, { size: 58, role: 'accent', k: c.k(4, 8), maxW: 840 }); y = ub.y1; }
      if (P.label) c.K.tag(c, P.label, c.A.cx, tagY(c, y + 82), c.k(last + 4, 9));
    },
  };
}

// đồng hồ kim: thang tự chọn từ dữ liệu (min..max bội số đẹp), vùng đỏ từ `danger`, kim vượt rồi rung như cảm biến thật
function drawDial(c, o) {
  const { x, y, R, lo, hi, v, k, danger, dec } = o, a0 = Math.PI * 0.8, a1 = Math.PI * 2.2, A = (val) => c.lerp(a0, a1, c.clamp((val - lo) / Math.max(1e-9, hi - lo)));
  c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0, a1, role: 'dim', w: 0.7 }], { x, y, s: R, plain: true, k });
  if (danger !== undefined && danger < hi) c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0: A(danger), a1, role: 'hot', w: 1.6 }], { x, y, s: R * 0.94, plain: true, k });
  const step = nice((hi - lo) / 5), g = c.g;
  for (let t = Math.ceil(lo / step) * step, i = 0; t <= hi + 1e-9 && i < 12; t += step, i++) {
    const a = A(t), ca = Math.cos(a), sa = Math.sin(a);
    c.draw([{ k: 'line', pts: [[x + ca * R * 0.84, y + sa * R * 0.84], [x + ca * R * 0.98, y + sa * R * 0.98]], role: 'ink', w: 0.6 }], { s: 1, plain: true, alpha: k });
    c.text(c.fmtNum(t, decN(step)), x + ca * R * 0.68, y + sa * R * 0.68 + 14, { size: 36, font: 'mono', role: 'dim', quiet: true, enter: 'none', k });
    for (let j = 1; j < 5 && t + step * j / 5 <= hi; j++) {
      const b = A(t + step * j / 5);
      g.save(); g.globalAlpha *= 0.5 * k; c.draw([{ k: 'line', pts: [[x + Math.cos(b) * R * 0.91, y + Math.sin(b) * R * 0.91], [x + Math.cos(b) * R * 0.98, y + Math.sin(b) * R * 0.98]], role: 'dim', w: 0.4 }], { s: 1, plain: true }); g.restore();
    }
  }
  const a = A(v), hot = danger !== undefined && v >= danger;
  c.draw([{ k: 'poly', pts: [[x + Math.cos(a) * R * 0.9, y + Math.sin(a) * R * 0.9], [x + Math.cos(a + 1.57) * 14, y + Math.sin(a + 1.57) * 14], [x - Math.cos(a) * 40, y - Math.sin(a) * 40], [x + Math.cos(a - 1.57) * 14, y + Math.sin(a - 1.57) * 14]], role: hot ? 'hot' : 'accent' },
          { k: 'circle', x, y, r: 26, role: 'ink' }], { s: 1, plain: true, alpha: k });
  return { dec };
}
function dialRange(vals, P) {
  const top = Math.max(...vals, num(P.danger, -Infinity));
  const lo = P.min !== undefined ? num(P.min) : Math.min(0, ...vals), hi = P.max !== undefined ? num(P.max) : lo + nice((top - lo) * 1.18 || 1) ;
  return [lo, Math.max(hi, lo + 1e-6)];
}
function counterGauge(c0, P) {                        // đồng hồ kim: kim quét theo giá trị, vượt nhẹ rồi rung (cảm biến sống)
  const N = c0.N, f0 = 6, f1 = Math.max(f0 + 12, Math.round((P.land ?? 0.6) * N)), from = num(P.from), to = num(P.to ?? P.value), dec = P.decimals ?? decN(to);
  const [lo, hi] = dialRange([from, to], P), final = fmtV(c0, to, dec, P);
  return {
    cues: [{ f: f0, name: 'whoosh_soft' }, { f: f1, name: P.danger !== undefined && to >= num(P.danger) ? 'warn' : 'ding', kick: 0.6 }],
    texts: names(P.title, final, P.unit, P.label),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), landed = c.f >= f1;
      const botNeed = 122 + (P.unit ? 68 : 0) + (P.label ? 92 : 0) + 36;
      const availDial = Math.max(220, c.A.bottom - botNeed - yb - 20);
      const R = Math.min(280, availDial / 1.62), cy = yb + 20 + R + Math.max(0, (availDial - R * 1.62) * 0.4);
      const t = c.clamp((c.f - f0) / (f1 - f0)), e = c.EASE.back(t, 1.4), live = landed ? (c.noise(c.f, 3) * 0.6 + Math.sin(c.f * 0.9) * 0.4) * (hi - lo) * 0.006 : 0;
      const v = c.lerp(from, to, e) + live;
      drawDial(c, { x: c.A.cx, y: cy, R, lo, hi, v, k: c.k(1, 10), danger: P.danger !== undefined ? num(P.danger) : undefined, dec });
      const ry = cy + R * 0.7 + 56, rSize = Math.min(118, Math.max(76, R * 0.44));
      const rb = c.text(landed ? final : fmtV(c, c.lerp(from, to, Math.min(1, e)), dec, P), c.A.cx, ry, { size: rSize, quiet: !landed, enter: 'none', maxW: 820, weight: 900 });
      let y = rb.y1;
      if (P.unit) { const ub = c.text(P.unit, c.A.cx, y + 54, { size: 50, role: 'accent', k: c.k(4, 8), maxW: 800 }); y = ub.y1; }
      if (P.icon) c.icon(P.icon, { x: c.A.cx, y: cy - R * 0.46, s: Math.min(54, R * 0.2), role: P.icon_role, p: t });
      if (P.label) c.K.tag(c, P.label, c.A.cx, tagY(c, y + 78), c.k(f1 + 4, 9));
    },
  };
}

const labOf = (c0, o, P) => (o.value !== undefined ? `${c0.fmtNum(o.value, decOf(o, P))}${o.unit ? ' ' + o.unit : ''}` : '');
function compareRace(c0, P) {                         // đua về phía camera: tốc độ ∝ giá trị (faster: higher|lower) → bên thắng chạm đích đúng lúc land
  const l = P.left || {}, r = P.right || {}, lower = P.faster === 'lower';
  const sp = [l, r].map((o) => { const v = Math.abs(num(o.value)); return lower ? (v > 0 ? 1 / v : 0) : v; }), smax = Math.max(...sp, 1e-9), dist = sp.map((s) => s / smax);
  const N = c0.N, f0 = 4, f1 = Math.max(f0 + 16, Math.round((P.land ?? 0.68) * N)), Z0 = 1.45, acc = 0.16;
  const prog = (f, d) => { const t = c0.clamp((f - f0) / (f1 - f0)), g = t < acc ? t * t / (2 * acc) : t - acc / 2; return d * g / (1 - acc / 2); };
  const win = dist[0] >= dist[1] ? 0 : 1;
  return {
    cues: [{ f: f0, name: 'whoosh' }, ...Array.from({ length: Math.min(6, Math.floor((f1 - f0) / 6)) }, (_, i) => ({ f: f0 + 4 + i * 6, name: 'thud' })), { f: f1, name: 'hit', kick: 0.7 }],
    texts: names(P.title, l.label, r.label, labOf(c0, l, P), labOf(c0, r, P), P.result),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10), true), vy = yb + 84, near = c.A.bottom - (P.result ? 132 : 56), cx = c.A.cx;
      const pj = (lx, z) => { const s = 1 / (1 + Math.max(-0.35, z)); return [cx + lx * s, vy + (near - vy) * s / 1, s]; };
      const zAt = (d) => Z0 * (1 - d), g = c.g, k0 = c.k(1, 10), Sbase = Math.min(185, Math.max(105, (near - vy) * 0.31));
      // mặt đường chạy phối cảnh (terracotta / nhấn mờ) để khung không bị trống đen
      {
        const tl = pj(-420, Z0 + 0.18), tr = pj(420, Z0 + 0.18), bl = pj(-420, -0.1), br = pj(420, -0.1);
        g.save(); g.globalAlpha *= 0.18 * k0; g.fillStyle = c.col('hot');
        g.beginPath(); g.moveTo(tl[0], tl[1]); g.lineTo(tr[0], tr[1]); g.lineTo(br[0], br[1]); g.lineTo(bl[0], bl[1]); g.closePath(); g.fill();
        g.restore();
      }
      for (const lx of [-420, 0, 420]) { const a = pj(lx, Z0 + 0.18), b = pj(lx, -0.1); c.draw([{ k: 'line', pts: [[a[0], a[1]], [b[0], b[1]]], role: lx ? 'ink' : 'dim', w: lx ? 0.55 : 0.35 }], { s: 1, plain: true, k: k0, alpha: lx ? 0.7 : 0.45 }); }
      [0.25, 0.5, 0.75].forEach((d) => { const a = pj(-420, zAt(d)), b = pj(420, zAt(d)); g.save(); g.globalAlpha *= 0.35; c.draw([{ k: 'line', pts: [[a[0], a[1]], [b[0], b[1]]], role: 'dim', w: 0.3, dash: [1, 2] }], { s: 1, plain: true, k: k0 }); g.restore(); });
      { const a = pj(-420, Z0), b = pj(420, Z0); c.draw([{ k: 'line', pts: [[a[0], a[1]], [b[0], b[1]]], role: 'ink', w: 0.5 }], { s: 1, plain: true, k: k0 }); }
      const fa = pj(-420, 0), fb = pj(420, 0), flash = c.f >= f1 ? Math.max(0, 1 - (c.f - f1) / 10) : 0;          // vạch đích (ô cờ)
      for (let i = 0; i < 16; i++) for (let j = 0; j < 2; j++) if ((i + j) % 2 === 0) { g.save(); g.fillStyle = c.col(flash > 0 ? 'hot' : 'ink'); g.globalAlpha *= 0.8 * k0; g.fillRect(c.lerp(fa[0], fb[0], i / 16), fa[1] - 8 + j * 9, (fb[0] - fa[0]) / 16, 9); g.restore(); }
      const items = [[l, -210, 0], [r, 210, 1]].map(([o, lx, i]) => ({ o, lx, i, d: prog(c.f, dist[i]) })).sort((a, b) => a.d - b.d);   // xa vẽ trước
      for (const it of items) {
        const z = zAt(it.d), [x, y, s] = pj(it.lx, z), run = c.f < f1 && it.d < dist[it.i] - 1e-4, ph = it.d * 46;
        const hop = run ? Math.abs(Math.sin(ph)) * 18 * s : Math.sin(c.f * 0.1 + it.i) * 3, S = Sbase * s;
        c.draw([{ k: 'circle', x: 0, y: 0, r: 1, rx: 1, ry: 0.16, role: 'dim' }], { x, y: y + 6, s: S * 0.8, plain: true, alpha: 0.5 });
        if (run) for (let q = 1; q <= 4; q++) {                                  // bụi sau chân: phun theo nhịp bước
          const fq = c.f - q * 3, dq = prog(fq, dist[it.i]), [px, py, ps] = pj(it.lx + (c.hash(q, it.i, Math.floor(fq / 3)) - 0.5) * 60, zAt(dq) + 0.05);
          c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'dim' }], { x: px, y: py - 6, s: (8 + q * 6) * ps, plain: true, alpha: 0.4 * (1 - q / 5) });
        }
        g.save(); if (z > 0.3) g.filter = `brightness(${(1 - Math.min(0.45, z * 0.2)).toFixed(3)})`;
        c.icon(it.o.icon || 'runner', { x, y: y - S - hop, s: S, role: it.o.role || (it.i === win ? 'hot' : 'cold'), rot: run ? 0.08 : 0, seed: 3 + it.i });
        g.restore();
        const lSize = Math.max(32, 48 * Math.sqrt(s)), vSize = Math.max(36, 56 * Math.sqrt(s)), hasVal = !!labOf(c, it.o, P);
        const minLabelY = yb + 44 + (hasVal ? vSize + 30 : 0);
        const ty = Math.max(minLabelY, y - 2 * S - 28 * s - hop);
        if (it.o.label) c.K.label(c, it.o.label, x, ty, c.k(6 + it.i * 4, 8), { align: 'center', maxW: 380, size: lSize });
        if (hasVal) c.text(labOf(c, it.o, P), x, Math.max(yb + vSize + 12, ty - (it.o.label ? lSize + 24 : 0)), { size: vSize, k: c.k(f1 - 2, 8), role: it.i === win ? 'accent' : 'ink', maxW: 400 });
      }
      if (P.result) c.K.tag(c, P.result, cx, tagY(c, c.A.bottom - 36), c.k(f1 + 5, 9));
    },
  };
}

function compareUnits(c0, P) {                        // hai nhóm isotype cùng tỉ giá, rơi CÙNG nhịp → nhóm lớn rơi lâu hơn, chênh lệch hiện bằng thời gian
  const l = P.left || {}, r = P.right || {}, vals = [num(l.value), num(r.value)], per = perUnit(vals, num(P.max_units, 100), num(P.per));
  const ns = vals.map((v) => Math.abs(v) / per), cmax = Math.max(1, ...ns.map((n) => Math.ceil(n - 1e-9))), N = c0.N;
  const f0 = 8, f1 = Math.max(f0 + 14, Math.round((P.land ?? 0.66) * N)), fOf = (i) => f0 + (f1 - f0) * (cmax > 1 ? i / (cmax - 1) : 0);
  const ends = ns.map((n) => Math.round(fOf(Math.max(0, Math.ceil(n - 1e-9) - 1)))), legend = legendOf(c0, per, P, P.per_unit || l.unit);
  return {
    cues: [{ f: f0, name: 'whoosh_soft' }, ...ends.map((f) => ({ f, name: 'tick' })), { f: f1 + 3, name: 'hit', kick: 0.5 }],
    texts: names(P.title, l.label, r.label, labOf(c0, l, P), labOf(c0, r, P), P.result, `= ${legend}`),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), resY = P.result ? yb + 70 : yb;
      const top = resY + (P.result ? 112 : 82), base = c.A.bottom - 172, half = (c.A.x1 - c.A.x0 - 60) / 2;
      const boxes = [{ x: c.A.x0, y: top, w: half, h: Math.max(160, base - top) }, { x: c.A.x0 + half + 60, y: top, w: half, h: Math.max(160, base - top) }];
      const s = Math.min(...ns.map((n, i) => unitGrid(n, boxes[i], { maxS: 105 }).s));
      [l, r].forEach((o, i) => {
        const grid = unitGrid(ns[i], boxes[i], { maxS: s, anchor: 'bottom', up: true }), shown = drawUnits(c, grid, ns[i], { icon: o.icon, role: o.role || (i ? 'cold' : 'hot'), fOf, seed: 11 + i * 5 });
        const cx = boxes[i].x + half / 2, done = c.f >= ends[i], v = Math.min(Math.abs(vals[i]), shown * per);
        c.text(done ? labOf(c, o, P) : `${c.fmtNum(v, decOf(o, P))}${o.unit ? ' ' + o.unit : ''}`, cx, Math.max(resY + (P.result ? 64 : 26), grid.y0 - 28), { size: 52, quiet: !done, enter: 'none', role: done ? 'accent' : 'ink', maxW: half });
        if (o.label) c.K.label(c, o.label, cx, base + 60, c.k(f0 + 2 + i * 4, 8), { align: 'center', maxW: half - 10, size: 42 });
      });
      c.draw([{ k: 'line', pts: [[c.A.x0, base + 12], [c.A.x1, base + 12]], role: 'dim', w: 0.4 }], { s: 1, plain: true });
      drawLegend(c, l.icon, l.role || 'hot', legend, c.A.cx, Math.min(c.A.bottom - 32, base + 130), c.k(f0 + 8, 8));
      if (P.result) c.K.tag(c, P.result, c.A.cx, resY, c.k(f1 + 3, 9));
    },
  };
}

function compareStack(c0, P) {                        // chồng vật: mỗi vật = per đơn vị, rơi từng cái (cùng nhịp hai bên), tháp cao = giá trị lớn
  const l = P.left || {}, r = P.right || {}, vals = [num(l.value), num(r.value)], per = perUnit(vals, num(P.max_units, 12), num(P.per));
  const ns = vals.map((v) => Math.abs(v) / per), cnt = ns.map((n) => Math.ceil(n - 1e-9)), cmax = Math.max(1, ...cnt), N = c0.N;
  const f0 = 6, f1 = Math.max(f0 + 14, Math.round((P.land ?? 0.66) * N)), fOf = (j) => f0 + (f1 - f0) * (cmax > 1 ? j / (cmax - 1) : 0), DR = 7;
  const legend = per !== 1 ? legendOf(c0, per, P, P.per_unit || l.unit) : '';
  return {
    cues: [...Array.from({ length: Math.min(10, cmax) }, (_, j) => ({ f: Math.round(fOf(Math.floor(j * cmax / Math.min(10, cmax))) + DR), name: 'thunk' })), { f: f1 + DR + 2, name: 'hit', kick: 0.5 }],
    texts: names(P.title, l.label, r.label, labOf(c0, l, P), labOf(c0, r, P), P.result, legend && `= ${legend}`),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), resY = P.result ? yb + 70 : yb;
      const base = c.A.bottom - (legend ? 172 : 104), topY = resY + (P.result ? 116 : 82), sz = Math.min(148, Math.max(32, (base - topY) / cmax));
      c.K.ground(c, c.A.cx, base + 4, 860);
      [[l, c.A.cx - 210, 0], [r, c.A.cx + 210, 1]].forEach(([o, x, i]) => {
        let topNow = base;
        const sway = Math.sin(c.f * 0.08 + i * 2) * 0.0035 * cnt[i];
        for (let j = 0; j < cnt[i]; j++) {
          const t = c.f - fOf(j); if (t < 0) break;
          const yT = base - (j + 0.5) * sz, kd = c.clamp(t / DR), y = kd < 1 ? c.lerp(Math.min(yT - 3 * sz, topY), yT, c.EASE.in(kd)) : yT;
          const sq = kd >= 1 ? Math.max(0, 1 - (t - DR) / 5) * 0.16 : 0, frac = j === cnt[i] - 1 ? ns[i] - j : 1, xs = x + Math.sin(sway) * (base - yT);
          c.g.save();
          if (frac < 0.999) { c.g.beginPath(); c.g.rect(xs - sz, yT + sz / 2 - sz * frac, sz * 2, sz * frac + 2); c.g.clip(); }
          c.icon(o.icon || 'cube', { x: xs, y: y + sz * sq * 0.4, s: sz * 0.48, sx: 1 + sq, sy: 1 - sq, role: o.role || (i ? 'cold' : 'hot'), rot: sway, seed: 20 + j, alpha: c.clamp(kd * 3) });
          c.g.restore();
          topNow = base - (j + frac) * sz;
        }
        const done = c.f >= fOf(cnt[i] - 1) + DR;
        if (labOf(c, o, P)) c.text(labOf(c, o, P), x, Math.max(resY + (P.result ? 64 : 26), topNow - 28), { size: 52, k: done ? 1 : 0, enter: 'none', role: 'accent', maxW: 380 });
        if (o.label) c.K.label(c, o.label, x, base + 64, c.k(f0 + i * 4, 8), { align: 'center', maxW: 380, size: 42 });
      });
      drawLegend(c, l.icon || 'cube', l.role || 'hot', legend, c.A.cx, Math.min(c.A.bottom - 32, base + 132), c.k(f0 + 8, 8));
      if (P.result) c.K.tag(c, P.result, c.A.cx, resY, c.k(f1 + DR + 2, 9));
    },
  };
}

function compareOverlay(c0, P) {                      // chồng hình đúng tỉ lệ: vật nhỏ trượt vào lồng trong vật lớn, hiện "×tỉ số"
  const l = P.left || {}, r = P.right || {}, lv = Math.abs(num(l.value)), rv = Math.abs(num(r.value)), bigL = lv >= rv;
  const B = bigL ? l : r, S = bigL ? r : l, vb = Math.max(lv, rv, 1e-9), vs = Math.min(lv, rv), area = P.by === 'area';
  const ratio = vb / Math.max(vs, 1e-9), rs = area ? Math.sqrt(vs / vb) : vs / vb, rtxt = `${c0.fmtNum(ratio, ratio < 10 ? 1 : 0)}×`;
  const N = c0.N, fs = Math.round(N * 0.28), fr = Math.round(N * 0.5);
  return {
    cues: [{ f: 3, name: 'pop' }, { f: fs, name: 'whoosh' }, { f: fs + 12, name: 'thunk' }, { f: fr, name: 'hit', kick: 0.6 }],
    texts: names(P.title, l.label, r.label, labOf(c0, l, P), labOf(c0, r, P), rtxt, P.result),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), base = c.A.bottom - (P.result ? 228 : 138), R = Math.max(80, Math.min(310, (base - yb - 130) / 2)), cx = c.A.cx;
      const Rs = Math.max(8, R * rs), kb = c.k(3, 12), ksl = c.EASE.back(c.clamp((c.f - fs) / 12), 1.2);
      c.K.ground(c, cx, base, R * 2.6);
      c.enter(kb, [cx - R, base - 2 * R, 2 * R, 2 * R], () => c.icon(B.icon || 'dot', { x: cx, y: base - R, s: R, role: B.role || 'cold', alpha: 0.9, p: B.p ?? 0.6 }), 'grow');
      const sx = c.lerp(c.A.x1 + Rs + 40, cx, ksl), sy = base - Rs + bob(c, 4, 4) * (ksl < 1 ? 1 : 0.3);
      if (c.f >= fs - 2) c.icon(S.icon || 'dot', { x: sx, y: sy, s: Rs, role: S.role || 'hot', p: S.p ?? 0.6, seed: 9 });
      const lead = (o, x, y, side, k) => { if (k <= 0) return; const tx = side < 0 ? c.A.x0 + 10 : c.A.xr(y) - 10;
        const cyL = c.clamp(y, yb + 76, base - 64);
        c.K.arrow(c, tx + side * -20, cyL, x, y, k, 'dim');
        if (o.label) c.K.label(c, o.label, tx, cyL - 44, k, { align: side < 0 ? 'left' : 'right', maxW: 360, size: 40 });
        if (labOf(c, o, P)) c.text(labOf(c, o, P), tx, cyL + 54, { size: 48, k, align: side < 0 ? 'left' : 'right', role: 'accent', maxW: 360 }); };
      lead(B, cx - R * 0.7, base - 2 * R + 30, -1, c.k(10, 8));
      lead(S, cx + Rs * 0.7, base - 2 * Rs, 1, c.k(fs + 12, 8));
      let rY1 = base + 108;
      if (c.f >= fr - 8) { const kr = c.k(fr, 8); c.enter(kr, [cx - 200, base + 12, 400, 140], () => { const rb = c.text(rtxt, cx, base + 106, { size: 112, role: 'hot', enter: 'none', maxW: 700, weight: 900 }); rY1 = rb.y1; }, 'pop'); }
      if (P.result) c.K.tag(c, P.result, cx, tagY(c, Math.max(base + 190, rY1 + 78)), c.k(fr + 8, 9));
    },
  };
}

function titleKinetic(c0, P) {                       // chữ động từng từ: mỗi từ một cú vào riêng, khối chữ dồn lên như camera bám theo
  const words = String(P.title || '').split(/\s+/).filter(Boolean).slice(0, 9), N = c0.N, nw = Math.max(1, words.length);
  const fe = Math.max(8, Math.round((P.hit ?? 0.5) * N)), step = Math.max(3, Math.floor((fe - 2) / nw)), fw = words.map((_, i) => 2 + i * step);
  const bare = (w) => w.toLowerCase().replace(/[^\p{L}\p{N}']/gu, '');
  const em = String(P.em || '').toLowerCase().split(/\s+/).map(bare).filter(Boolean);
  let hot = em.length ? words.findIndex((w) => em.includes(bare(w))) : -1;
  if (hot < 0) hot = words.reduce((b, w, i) => (bare(w).length > bare(words[b] || '').length ? i : b), 0);
  const FX = ['slam', 'pop', 'slide', 'mask'], sd = c0.strSeed(P.title || '') >>> 0;
  let lay = null;
  const layout = (c) => {                             // dòng: ≤ 2 từ (ngắn) mỗi dòng, cỡ chữ từng dòng vừa bề ngang + vừa chiều cao vùng sân khấu
    const lines = []; let cur = [];
    words.forEach((w, i) => { const len = cur.reduce((a, j) => a + words[j].length + 1, 0) + w.length; if (cur.length && (cur.length >= 2 || len > 11)) { lines.push(cur); cur = []; } cur.push(i); });
    if (cur.length) lines.push(cur);
    const topMin = c.A.top + (P.kicker ? 96 : 32), botMax = c.A.bottom - (P.sub ? 132 : 36), maxH = Math.max(240, botMax - topMin);
    const build = (sc = 1) => {
      let y = 0;
      const out = lines.map((ids) => {
        const m = c.text(ids.map((i) => words[i]).join(' '), 0, 0, { size: 100, k: 0, weight: 900 });
        const size = Math.max(54, Math.min(200, 100 * 880 / Math.max(1, m.x1 - m.x0)) * sc);
        const ws = ids.map((i) => { const b = c.text(words[i], 0, 0, { size, k: 0, weight: 900 }); return b.x1 - b.x0; }), sp = size * 0.28, tot = ws.reduce((a, b) => a + b, 0) + sp * (ids.length - 1);
        let x = c.A.cx - tot / 2; const xs = ws.map((w) => { const cxw = x + w / 2; x += w + sp; return cxw; });
        y += size * 0.92; const ln = { ids, size, xs, y }; y += size * 0.28; return ln;
      });
      return { lines: out, H: y, topMin, botMax };
    };
    const raw = build(1);
    return raw.H > maxH ? build(maxH / raw.H) : raw;
  };
  return {
    cues: [...fw.map((f, i) => ({ f, name: i === hot ? 'hit' : 'pop', kick: i === hot ? 0.6 : 0.15 })), ...(P.sub ? [{ f: fe + 4, name: 'whoosh_soft' }] : [])],
    texts: names(P.kicker, ...words, P.sub),
    draw(c) {
      lay = lay || layout(c);
      if (P.kicker) c.text(P.kicker, c.A.cx, c.A.top + 38, { size: 32, font: 'mono', role: 'dim', k: c.k(1, 8), enter: 'type', weight: 600 });
      // khối chữ canh giữa theo số dòng ĐÃ hiện → dồn lên mượt khi có dòng mới (máy quay đi theo chữ)
      const nShown = (f) => lay.lines.filter((ln) => f + 4 >= fw[ln.ids[0]]).length || 1;
      const hOf = (n) => lay.lines[n - 1].y + lay.lines[n - 1].size * 0.24, mid = (lay.topMin + lay.botMax) / 2, ns = nShown(c.f), np = nShown(c.f - 6);
      const rawOff = mid - c.lerp(hOf(np), hOf(ns), c.EASE.out(c.clamp((c.f - fw[lay.lines[ns - 1].ids[0]] + 4) / 6))) / 2;
      const off = Math.max(lay.topMin, Math.min(lay.botMax - lay.H, rawOff));
      lay.lines.forEach((ln) => ln.ids.forEach((i, j) => {
        const k = c.k(fw[i], 7), role = i === hot ? 'hot' : 'ink';
        c.text(words[i], ln.xs[j], off + ln.y, { size: ln.size, k, enter: FX[(i + sd) % FX.length], role, weight: 900, maxW: 2000 });
        if (i === hot && k >= 1) {                    // vạch nhấn quét dưới từ chính
          const b = c.text(words[i], ln.xs[j], off + ln.y, { size: ln.size, k: 0, weight: 900 }), kb = c.EASE.out(c.k(fw[i] + 6, 8));
          c.g.save(); c.g.fillStyle = c.col('accent'); c.g.fillRect(b.x0, b.y1 + 8, (b.x1 - b.x0) * kb, Math.max(7, ln.size * 0.06)); c.g.restore();
        }
      }));
      if (P.sub) c.K.tag(c, P.sub, c.A.cx, tagY(c, off + lay.H + 82), c.k(fe + 4, 10));
    },
  };
}
function titleReveal(c0, P) {                         // lộ qua chiều sâu: iris mở trên vật (nét) → "rack focus" kéo nét sang chữ, vật lùi xa, mờ
  const N = c0.N, fr = Math.round(N * 0.24), fd = Math.max(fr + 8, Math.round(N * 0.46));
  return {
    cues: [{ f: 1, name: 'whoosh_soft' }, { f: fr, name: 'riser' }, { f: fd, name: 'hit', kick: 0.4 }],
    texts: names(P.kicker, P.title, P.sub),
    draw(c) {
      const rk = c.EASE.smooth(c.clamp((c.f - fr) / (fd - fr))), g = c.g;
      const topY = c.A.top + (P.kicker ? 84 : 26), spanH = c.A.bottom - topY, cy = topY + spanH * 0.42;
      if (P.icon) {
        const ki = c.EASE.out(c.k(1, 16)), Ri = ki * 720, s = Math.min(310, spanH * 0.34) * (1 - 0.2 * rk) * (1 + 0.025 * Math.sin(c.f * 0.05));
        g.save(); g.beginPath(); g.arc(c.A.cx, cy, Math.max(1, Ri), 0, c.TAU); g.clip();
        if (rk > 0.02) g.filter = `blur(${(rk * 9).toFixed(1)}px) brightness(${(1 - 0.5 * rk).toFixed(3)})`;
        if (P.icon_role === 'hot') c.K.halo(c, c.A.cx - rk * 40, cy, s * 0.8);
        c.icon(P.icon, { x: c.A.cx - rk * 40, y: cy + bob(c, 1, 6), s, role: P.icon_role, p: P.icon_p ?? 0.6 });
        g.restore();
        if (ki < 1) c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'accent', fill: false, w: 0.8 }], { x: c.A.cx, y: cy, s: Math.max(1, Ri), plain: true, alpha: 1 - ki });
      }
      if (P.kicker) c.text(P.kicker, c.A.cx, c.A.top + 38, { size: 32, font: 'mono', role: 'dim', k: c.k(1, 8), enter: 'type', weight: 600 });
      const subRes = P.sub ? 114 : 24, tbBlur = (1 - rk) * 14;
      const tf = fitText(c, P.title, c.A.cx, [118, 102, 88, 74, 64], { maxW: 900, lh: 1.02, maxH: Math.max(160, spanH - subRes - 40) });
      const wantY = P.icon ? topY + spanH * 0.72 : topY + spanH * 0.48;
      const maxTy = c.A.bottom - 36 - subRes - tf.b.y1, minTy = topY + 24 - tf.b.y0;
      const ty = Math.max(minTy, Math.min(maxTy, wantY));
      g.save(); if (tbBlur > 0.3) g.filter = `blur(${tbBlur.toFixed(1)}px)`;
      const b = c.text(P.title, c.A.cx + (1 - rk) * 30, ty, { size: tf.size, k: c.k(fr - 8, 12), maxW: 900, quiet: tbBlur > 0.5, lh: 1.02 });
      g.restore();
      if (P.sub) c.K.tag(c, P.sub, c.A.cx, tagY(c, b.y1 + 88), c.k(fd + 4, 10));
    },
  };
}

function factFlip(c0, P) {                            // thẻ lật: mặt trước (front: lời đồn/câu hỏi) → lật 3D → mặt sau là sự thật
  const N = c0.N, fh = Math.max(10, Math.round((P.hit ?? 0.36) * N)), FL = 10, front = P.front || '?';
  return {
    cues: [{ f: 2, name: 'whoosh_soft' }, { f: fh, name: 'whoosh' }, { f: fh + FL / 2, name: 'pop' }, ...(P.em ? [{ f: fh + FL + 8, name: 'hit', kick: 0.5 }] : [])],
    texts: names(P.front, P.kicker, P.text, P.em),
    draw(c) {
      const g = c.g, cx = c.A.cx, chh = Math.min(780, c.A.bottom - c.A.top - 80), cy = (c.A.top + c.A.bottom) / 2, cw = 860;
      const ph = c.clamp((c.f - fh) / FL), back = ph >= 0.5;
      const pre = c.f < fh ? c.clamp(1 - (fh - c.f) / 8) : 0, sx = Math.max(0.02, Math.abs(Math.cos(Math.PI * ph))), sk = Math.sin(Math.PI * ph) * 0.09 * (back ? -1 : 1);
      const kin = c.EASE.out(c.k(1, 12)), lift = pre * -18 + (1 - kin) * 220, rot = pre * Math.sin(c.f * 1.3) * 0.012;
      c.draw([{ k: 'circle', x: 0, y: 0, r: 1, rx: 1, ry: 0.06, role: 'dim' }], { x: cx, y: cy + chh / 2 + 34, s: cw * 0.48 * sx, plain: true, alpha: 0.35 * kin });
      g.save(); g.translate(cx, cy + lift); g.rotate(rot); g.transform(sx, sk, 0, 1, 0, 0); g.translate(-cx, -cy);
      if (ph > 0 && ph < 1) g.filter = `brightness(${(1 - 0.45 * Math.sin(Math.PI * ph)).toFixed(3)})`;
      g.globalAlpha *= c.clamp(kin * 2);
      g.fillStyle = c.mix(c.pal.bg, c.col(back ? 'accent' : 'ink'), back ? 0.1 : 0.12); g.fillRect(cx - cw / 2, cy - chh / 2, cw, chh);
      c.draw([{ k: 'rect', x: cx - cw / 2, y: cy - chh / 2, w: cw, h: chh, rad: 28, role: back ? 'accent' : 'dim', fill: false }], { s: 1, plain: true });
      const q = ph > 0 && ph < 1, maxW = cw - 120;
      if (!back) {
        if (P.kicker) c.text(P.kicker, cx, cy - chh / 2 + 78, { size: 30, font: 'mono', role: 'dim', k: c.k(2, 8), weight: 600, quiet: q });
        const topIn = cy - chh / 2 + (P.kicker ? 124 : 56), botIn = cy + chh / 2 - 56;
        if (P.icon) {
          c.icon(P.icon, { x: cx, y: topIn + 110, s: 96, role: P.icon_role, p: 0.6 });
          const ff = fitText(c, front, cx, front.length <= 2 ? [240, 180] : [86, 72, 60, 50], { maxW, lh: 1.08, maxH: Math.max(120, botIn - (topIn + 230)) });
          c.text(front, cx, topIn + 230 + Math.max(0, (botIn - (topIn + 230) - ff.h) / 2) - ff.b.y0, { size: ff.size, k: c.k(3, 10), maxW, lh: 1.08, quiet: q, role: front.length <= 2 ? 'accent' : 'ink' });
        } else {
          const ff = fitText(c, front, cx, front.length <= 2 ? [300, 220] : [92, 78, 66, 54], { maxW, lh: 1.08, maxH: botIn - topIn });
          c.text(front, cx, topIn + Math.max(0, (botIn - topIn - ff.h) / 2) - ff.b.y0, { size: ff.size, k: c.k(3, 10), maxW, lh: 1.08, quiet: q, role: front.length <= 2 ? 'accent' : 'ink' });
        }
      } else {
        // Tự đo P.text + P.em với k=0, thu nhỏ size động để tổng chiều cao luôn vừa chh - 140, căn giữa thẻ và đặt P.em strictly dưới tb.y1
        const ef = P.em ? fitText(c, P.em, cx, [74, 64, 56, 48], { maxW, lh: 1.08, weight: 900, maxH: chh * 0.34 }) : null;
        const emGap = 52, emH = ef ? ef.h : 0, availH = Math.max(220, chh - 140);
        let tSize = 54, tb0 = null;
        for (const sz of [84, 72, 62, 54, 46, 38]) {
          const m = c.text(P.text, cx, 0, { size: sz, k: 0, maxW, lh: 1.1 });
          tSize = sz; tb0 = m;
          if ((m.y1 - m.y0) + (ef ? emH + emGap : 0) <= availH) break;
        }
        const textH = tb0.y1 - tb0.y0, gap = ef && (textH + emH + emGap > chh - 90) ? 34 : emGap;
        const totalH = textH + (ef ? gap + emH : 0), stackTop = cy - totalH / 2, textY = stackTop - tb0.y0;
        const tb = c.text(P.text, cx, textY, { size: tSize, k: c.clamp((ph - 0.5) * 2), enter: 'none', maxW, lh: 1.1, quiet: q });
        if (P.em && ef) {
          const ke = c.k(fh + FL + 8, 6);
          c.text(P.em, cx, tb.y1 + gap - ef.b.y0, { size: ef.size, role: 'hot', k: ke, enter: 'slam', maxW, lh: 1.08, weight: 900 });
        }
      }
      g.restore();
    },
  };
}
function factQuote(c0, P) {                           // trích dẫn: ngoặc kép lớn rơi xuống, câu gõ ra từng chữ, dòng nguồn (by)
  const N = c0.N, ft = Math.max(14, Math.round(N * 0.34)), fe = Math.round(N * 0.52);
  const mark = (dx) => [{ k: 'circle', x: dx, y: 0, r: 0.42, role: 'accent' }, { k: 'poly', pts: [[dx + 0.36, 0.16], [dx + 0.12, 1.0], [dx - 0.2, 0.92], [dx - 0.02, 0.3]], role: 'accent' }];
  return {
    cues: [{ f: 2, name: 'thunk', kick: 0.3 }, { f: 4, name: `typing:${(ft / c0.FPS).toFixed(2)}` }, ...(P.em ? [{ f: fe, name: 'pop', kick: 0.4 }] : [])],
    texts: names(P.kicker, P.text, P.em, P.by && `— ${P.by}`),
    draw(c) {
      const x = c.A.x0 + 40, kq = c.k(1, 9), maxW = c.A.x1 - x - 20;
      if (P.kicker) c.text(P.kicker, x, c.A.top + 38, { size: 32, font: 'mono', role: 'dim', align: 'left', k: c.k(1, 6), weight: 600, enter: 'type' });
      const topY = c.A.top + (P.kicker ? 86 : 24), botY = c.A.bottom - 36, markH = 104;
      const ef = P.em ? fitText(c, P.em, x, [78, 66, 56, 48], { align: 'left', maxW, weight: 900, maxH: 180 }) : null;
      const bf = P.by ? fitText(c, `— ${P.by}`, x, [38, 32], { align: 'left', font: 'mono', maxW, weight: 600, maxH: 80 }) : null;
      const extraH = (ef ? ef.h + 44 : 0) + (bf ? bf.h + 38 : 0);
      const tf = fitText(c, P.text, x, [P.size || 92, 80, 68, 58, 48], { align: 'left', maxW, lh: 1.12, maxH: Math.max(150, botY - topY - markH - extraH) });
      const totalH = markH + tf.h + extraH, startY = topY + Math.max(0, (botY - topY - totalH) / 2), y0 = startY + markH - tf.b.y0;
      c.enter(kq, [x - 20, startY - 10, 220, 120], () => c.draw([...mark(0), ...mark(1.15)], { x: x + 62, y: startY + 24 + bob(c, 2, 4), s: 66, rot: Math.PI }), 'pop');
      const b = c.text(P.text, x, y0, { size: tf.size, align: 'left', k: c.k(4, ft), enter: 'type', maxW, lh: 1.12 });
      let lastY1 = b.y1;
      if (P.em && ef) { const eb = c.text(P.em, x, Math.min(botY - (bf ? bf.h + 36 : 0) - ef.b.y1, lastY1 + 42 - ef.b.y0), { size: ef.size, align: 'left', role: 'hot', k: c.k(fe, 8), enter: 'slide', maxW, weight: 900 }); lastY1 = eb.y1; }
      if (P.by && bf) { const bb = c.text(`— ${P.by}`, x, Math.min(botY - bf.b.y1, lastY1 + 36 - bf.b.y0), { size: bf.size, font: 'mono', role: 'dim', align: 'left', k: c.k(fe + 6, 10), weight: 600, enter: 'type', maxW }); lastY1 = bb.y1; }
      if (c.f >= ft) c.draw([...mark(0), ...mark(1.15)], { x: c.A.x1 - 150, y: Math.min(c.A.bottom - 48, lastY1 + 28), s: 42, alpha: c.k(ft, 8) });
    },
  };
}

function processLoop(c0, P) {                         // vòng tuần hoàn: các bước trên vòng tròn, một hạt chạy vòng `cycles` lần, bước sáng khi hạt đi qua
  const steps = (P.steps || []).slice(0, 6), n = Math.max(1, steps.length), N = c0.N, f0 = 6, f1 = Math.max(f0 + 10, N - 4), cyc = Math.max(1, Math.round(num(P.cycles, 1)));
  const arr = (i, lap = 0) => Math.round(f0 + (f1 - f0) * ((lap + i / n) / cyc));
  return {
    cues: [...steps.map((_, i) => ({ f: arr(i), name: 'pop' })), ...Array.from({ length: cyc }, (_, lap) => ({ f: arr(0, lap + 1) - 1, name: 'ding', kick: 0.3 }))],
    texts: names(P.title, P.center, ...steps.map((s) => s.label)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), availH = Math.max(300, c.A.bottom - yb - 130);
      const R = Math.min(n > 4 ? 235 : 215, availH * 0.36), cx = c.A.cx, cy = yb + 92 + R + Math.max(0, (availH - 2 * R - 30) * 0.45);
      const tk = c.clamp((c.f - f0) / (f1 - f0)), a = -Math.PI / 2 + 2 * Math.PI * cyc * tk, A = (i) => -Math.PI / 2 + 2 * Math.PI * i / n;
      c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'dim', fill: false, w: 0.4, dash: [1.5, 2] }], { x: cx, y: cy, s: R, plain: true, alpha: c.k(1, 10) });
      const sweep = Math.min(2 * Math.PI, 2 * Math.PI * cyc * tk);                   // vòng đầu: cung có mũi tên vẽ theo hạt
      for (let i = 0; i < n; i++) {
        const s0 = A(i) + 0.32, s1 = A(i + 1) - 0.32, e = Math.min(s1, -Math.PI / 2 + sweep);
        if (e <= s0) continue;
        c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0: s0, a1: e, role: 'accent', w: 0.7 }], { x: cx, y: cy, s: R, seed: 4 + i });
        if (e >= s1 - 1e-3) { const hx = cx + Math.cos(s1) * R, hy = cy + Math.sin(s1) * R, d = s1 + Math.PI / 2;
          c.draw([{ k: 'poly', role: 'accent', pts: [[hx + Math.cos(d) * 20, hy + Math.sin(d) * 20], [hx + Math.cos(d + 2.5) * 20, hy + Math.sin(d + 2.5) * 20], [hx + Math.cos(d - 2.5) * 20, hy + Math.sin(d - 2.5) * 20]] }], { s: 1 }); }
      }
      for (let j = 5; j >= 0; j--) { const aj = a - j * 0.07; c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'hot' }], { x: cx + Math.cos(aj) * R, y: cy + Math.sin(aj) * R, s: 18 - j * 2.2, plain: true, alpha: 1 - j / 6 }); }
      steps.forEach((s, i) => {
        const ai = A(i), x = cx + Math.cos(ai) * R, y = cy + Math.sin(ai) * R, k = c.k(arr(i) - 6, 8);
        const dA = Math.abs(((a - ai) % (2 * Math.PI) + 3 * Math.PI) % (2 * Math.PI) - Math.PI), on = c.f >= arr(i) - 2 && dA < Math.PI / n;
        c.enter(k, [x - 70, y - 70, 140, 140], () => c.icon(s.icon || 'dot', { x, y: y + (on ? bob(c, i, 5) : 0), s: on ? 70 : 58, role: s.role, p: s.p ?? 0.6 }));
        if (on) c.K.ring(c, x, y, 92, c.clamp((Math.PI / n - dA) / (Math.PI / n) * 3));
        const up = Math.sin(ai) < -0.5, ly = up ? Math.max(yb + 46, y - 92) : Math.min(c.A.bottom - 30, y + 104);
        const lx = Math.min(c.A.xr(ly) - 160, Math.max(c.A.x0 + 160, x));
        c.K.label(c, s.label, lx, ly, k, { align: 'center', maxW: 300, size: 38, role: on || c.f > f1 ? 'ink' : 'dim' });
      });
      if (P.center) c.text(P.center, cx, cy + 16, { size: 46, role: 'accent', k: c.k(4, 8), maxW: R * 1.15 });
      else c.text(`×${Math.min(cyc, 1 + Math.floor(cyc * tk))}`, cx, cy + 26, { size: 78, font: 'mono', role: 'dim', quiet: true, enter: 'none' });
    },
  };
}
function processNest(c0, P) {                         // zoom lồng: vĩ mô → vi mô, mỗi bước nằm TRONG bước trước; camera lao vào theo thang log
  const steps = (P.steps || []).slice(0, 5), M = Math.max(1, steps.length), Z = Math.max(3, num(P.ratio, 7)), N = c0.N, R0 = 260;
  const off = steps.map((_, i) => (i ? [(c0.hash(i, 31) - 0.5) * 0.7, (c0.hash(i, 37) - 0.5) * 0.5 + 0.05] : [0, 0]));
  const W = [[0, 0]]; for (let i = 1; i < M; i++) W.push([W[i - 1][0] + off[i][0] * R0 / Z ** (i - 1), W[i - 1][1] + off[i][1] * R0 / Z ** (i - 1)]);
  const pos = (u) => { const x = c0.clamp(u) * Math.max(1, M - 1), i = Math.min(M - 2, Math.floor(x)), t = x - i; return M < 2 ? [0, 0] : [i, c0.MO.M.smooth(c0.clamp((t - 0.35) / 0.65))]; };
  return {
    cues: steps.slice(1).map((_, i) => ({ f: Math.round((i + 0.35) / Math.max(1, M - 1) * N * 0.9), name: 'whoosh' })),
    texts: names(P.title, ...steps.map((s) => s.label)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), botNeed = 152, availH = Math.max(240, c.A.bottom - botNeed - yb - 20);
      const cx = c.A.cx, cy = yb + 20 + availH * 0.5, u = c.clamp(c.f / (c.N * 0.9)), [i, t] = pos(u);
      const L = i + t, zoom = Z ** L, w = (1 - Z ** -t) / (1 - 1 / Z), cam = M < 2 ? W[0] : [c.lerp(W[i][0], W[i + 1][0], w), c.lerp(W[i][1], W[i + 1][1], w)];
      c.zoomU = M < 2 ? 0 : L / (M - 1);
      steps.forEach((s, j) => {
        const r = R0 / Z ** j * zoom; if (r < 3 || r > 2600) return;
        const x = cx + (W[j][0] - cam[0]) * zoom, y = cy + (W[j][1] - cam[1]) * zoom, al = r > 520 ? c.clamp(1 - (r - 520) / 900) : 1;
        c.icon(s.icon || 'cell', { x, y: y + bob(c, j, 3), s: r, role: s.role || (j === Math.round(L) ? 'accent' : 'ink'), alpha: al, plain: r > 500, seed: 40 + j });
        if (j === i + 1 && t < 0.3) c.K.ring(c, x, y, Math.max(26, Math.min(500, r * 1.5)), c.clamp((u * (M - 1) - i) / 0.3));
      });
      const cur = t > 0.55 ? i + 1 : i, st = steps[cur]; if (!st) return;
      const settle = t <= 0.02 || t >= 0.98 || M < 2, kk = settle ? 1 : c.clamp(Math.abs(t - 0.55) * 5);
      const numY = Math.min(c.A.bottom - 102, cy + availH * 0.5 + 34);
      c.text(String(cur + 1).padStart(2, '0'), cx, numY, { size: 40, font: 'mono', role: 'accent', k: kk, quiet: true, enter: 'none', weight: 700 });
      c.text(st.label, cx, Math.min(c.A.bottom - 32, numY + 68), { size: 58, k: kk, quiet: !settle, maxW: 820 });
    },
  };
}
function processDomino(c0, P) {                       // chuỗi domino: mỗi bước một quân, quân trước đổ làm quân sau đổ (nhân → quả), xa dần theo chiều sâu
  const steps = (P.steps || []).slice(0, 6), n = Math.max(1, steps.length), N = c0.N, f0 = 8, st = Math.max(6, Math.min(22, Math.floor((0.74 * N - f0) / n)));
  const fi = (i) => f0 + i * st;
  return {
    cues: steps.map((_, i) => ({ f: fi(i) + st, name: i === n - 1 ? 'thunk' : 'click', kick: i === n - 1 ? 0.6 : 0.15 })),
    texts: names(P.title, ...steps.map((s) => s.label)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), q = (i) => (n > 1 ? i / (n - 1) : 0);
      const lh = Math.min(60, Math.max(46, (c.A.bottom - yb - 240) / (n + 1.5))), listH = n * lh + 26;
      const b0 = Math.max(yb + 190, c.A.bottom - listH - 46);
      const domH = Math.min(230, Math.max(120, b0 - yb - 44)), domW = domH * 0.31;
      const T = steps.map((_, i) => { const s = c.lerp(1, 0.64, q(i)); return { x: c.lerp(c.A.x0 + 70, c.A.x1 - 150, q(i)), b: b0 - q(i) * Math.min(140, domH * 0.55), s, w: domW * s, h: domH * s }; });
      const fallK = (i) => c.clamp((c.f - fi(i)) / st);
      T.forEach((d, i) => {                            // góc chạm quân sau (nghiêng tựa) → quân cuối nằm hẳn
        const nx = T[i + 1], lean = nx ? Math.asin(c.clamp((nx.x - d.w * 0.5 - (d.x + d.w / 2)) / d.h, 0.05, 0.98)) : Math.PI / 2;
        const k = fallK(i), rest = nx ? lean + (Math.min(1.25, lean + 0.35) - lean) * c.EASE.out(fallK(i + 1)) : lean;
        d.th = k < 1 ? lean * k * k : (nx ? rest : lean * (1 + Math.max(0, 1 - (c.f - fi(i) - st) / 6) * Math.sin((c.f - fi(i) - st) * 1.4) * -0.06));
      });
      for (let i = n - 1; i >= 0; i--) {               // xa vẽ trước
        const d = T[i], s = steps[i], px = d.x + d.w / 2, py = d.b, kin = c.k(2 + i * 2, 8);
        if (kin <= 0) continue;
        c.draw([{ k: 'circle', x: 0, y: 0, r: 1, rx: 1, ry: 0.12, role: 'dim' }], { x: d.x + Math.sin(d.th) * d.h * 0.5, y: py + 4, s: d.w * 0.9 + Math.sin(d.th) * d.h * 0.5, plain: true, alpha: 0.4 });
        c.g.save(); if (i > 0) c.g.filter = `brightness(${(1 - 0.35 * q(i)).toFixed(3)})`;
        c.enter(kin, [d.x - d.w / 2, py - d.h, d.w, d.h], () => {
          c.draw([{ k: 'rect', x: -d.w, y: -d.h, w: d.w, h: d.h, rad: 10 * d.s, role: c.f >= fi(i) ? 'accent' : 'ink' }], { x: px, y: py, s: 1, rot: d.th, seed: 50 + i });
          const ca = Math.cos(d.th), sa = Math.sin(d.th), lx = -d.w / 2, ly = -d.h * 0.62;
          c.icon(s.icon || 'dot', { x: px + lx * ca - ly * sa, y: py + lx * sa + ly * ca, s: d.w * 0.42, rot: d.th, role: c.L.pen.fill ? 'bg' : 'ink', plain: true, seed: 60 + i });
        }, 'grow');
        c.g.restore();
      }
      const ly0 = b0 + 56, lblSize = Math.min(38, Math.max(28, Math.floor(lh * 0.68)));
      steps.forEach((s, i) => {
        const y = ly0 + i * lh, k = c.k(fi(i), 7), on = c.f >= fi(i) && (i === n - 1 || c.f < fi(i + 1) + 4);
        c.text(String(i + 1).padStart(2, '0'), c.A.x0 + 10, y, { size: lblSize - 2, font: 'mono', role: 'accent', align: 'left', k, quiet: true, weight: 700 });
        c.K.label(c, s.label, c.A.x0 + 84, y, k, { align: 'left', size: lblSize, maxW: c.A.xr(y) - c.A.x0 - 94, role: on ? 'ink' : 'dim' });
      });
    },
  };
}

// bố cục vòng 10: [hàm, dữ liệu có hợp không]. Không hợp (vd overlay mà một bên = 0) → bố cục gốc, không bao giờ vỡ hình.
// Python (engines/html/__init__.py → layout_fits) dùng cùng điều kiện để không tự chọn bố cục không hợp dữ liệu.
const wordsOf = (s) => String(s || '').split(/\s+/).filter(Boolean);
const vpos = (o) => Number.isFinite(Number(o && o.value)) && Number(o.value) >= 0;
const LAYOUT10 = {
  title: { kinetic: [titleKinetic, (P) => wordsOf(P.title).length >= 2 && wordsOf(P.title).length <= 9], reveal: [titleReveal, (P) => !!P.title] },
  counter: { odometer: [counterOdometer, (P) => Math.abs(num(P.to ?? P.value)) < 1e9], flap: [counterFlap, (P) => Math.abs(num(P.to ?? P.value)) < 1e9],
             units: [counterUnits, (P) => Math.abs(num(P.to ?? P.value)) > 0], gauge: [counterGauge, () => true] },
  compare: { race: [compareRace, (P) => vpos(P.left) && vpos(P.right) && Math.max(num(P.left.value), num(P.right.value)) > 0],
             units: [compareUnits, (P) => vpos(P.left) && vpos(P.right) && Math.max(num(P.left.value), num(P.right.value)) > 0],
             stack: [compareStack, (P) => vpos(P.left) && vpos(P.right) && Math.max(num(P.left.value), num(P.right.value)) > 0],
             overlay: [compareOverlay, (P) => vpos(P.left) && vpos(P.right) && Math.min(num(P.left.value), num(P.right.value)) > 0] },
  fact: { flip: [factFlip, (P) => !!P.text], quote: [factQuote, (P) => !!P.text && String(P.text).length <= 180] },
  process: { loop: [processLoop, (P) => (P.steps || []).length >= 3], nest: [processNest, (P) => (P.steps || []).length >= 2],
             domino: [processDomino, (P) => (P.steps || []).length >= 2] },
};
const alt10 = (beat, c0, P) => { const e = (LAYOUT10[beat] || {})[P.layout]; return e && e[1](P) ? e[0](c0, P) : null; };

function title(c0, P) {
  const a10 = alt10('title', c0, P); if (a10) return a10;
  if (P.layout === 'left') return titleLeft(c0, P);
  if (P.layout === 'hero') return titleHero(c0, P);
  return {
    cues: [{ f: 1, name: 'whoosh_soft' }, { f: 9, name: 'pop' }], texts: names(P.kicker, P.title, P.sub),
    draw(c) {
      const yb = drawHeader(c, P, c.k(2, 12));
      const subH = P.sub ? 112 : 28, availTop = yb + 34, availBot = c.A.bottom - subH;
      const availH = Math.max(180, availBot - availTop), s = Math.min(195, availH * 0.38), cy = availTop + availH * 0.5;
      if (P.icon) {
        const k = c.k(7, 10);
        c.K.ground(c, c.A.cx, cy + s * 0.95, s * 2.2);
        if (P.icon_role === 'hot') c.K.halo(c, c.A.cx, cy + bob(c), s * 0.8);
        c.enter(k, [c.A.cx - s, cy - s, s * 2, s * 2], () => c.icon(P.icon, { x: c.A.cx, y: cy + bob(c), s, role: P.icon_role, p: P.icon_p ?? 0.6 }));
      }
      if (P.sub) c.K.tag(c, P.sub, c.A.cx, tagY(c, Math.max(yb + 86, P.icon ? cy + s + 90 : availTop + availH * 0.5)), c.k(16, 10));
    },
  };
}

function drop(c0, P) {                                // A rơi/đi vào B → va chạm → kết quả
  const N = c0.N, fh = Math.round((P.hit ?? 0.45) * N), a = P.a || {}, b = P.b || {};
  const hot = (a.role || '') === 'hot';
  return {
    cues: [{ f: Math.max(0, fh - 8), name: 'whoosh' }, { f: fh, name: P.sfx || 'splash', kick: 1 }, ...(hot ? [{ f: fh + 3, name: 'sizzle' }] : [])],
    texts: names(P.title, a.label, b.label, P.result),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), cx = c.A.cx;
      const botNeed = (b.label ? 74 : 14) + (P.result ? 92 : 16) + 36;
      const availH = Math.max(260, c.A.bottom - botNeed - yb - 20);
      const bs = Math.min(165, availH * 0.27), as = Math.round(bs * 0.48), by = c.A.bottom - botNeed - bs;
      const ay0 = Math.max(yb + as + 32, by - bs * 2.0);
      const fall = c.clamp((c.fs - (fh - 8)) / 8), ay = fall <= 0 ? ay0 + bob(c) - c.EASE.out(c.k(fh - 16, 8)) * 22 : c.lerp(ay0 - 22, by + 10, c.EASE.in(fall));
      const after = c.fs - fh, shake = after >= 0 && after < 10 ? Math.sin(after * 2.4) * (10 - after) * 1.6 : 0;
      c.K.ground(c, cx, by + bs * 0.98, bs * 2.3);
      if (after > 2) c.icon('steam', { x: cx, y: by - bs - 110 - Math.min(50, after * 1.4), s: 80 + Math.min(40, after), alpha: c.clamp(after / 8) * (hot ? 1 : 0.5), k: c.clamp(after / 10) });
      c.enter(c.k(4, 10), [cx - bs, by - bs, bs * 2, bs * 2], () => c.icon(b.icon || 'glass', { x: cx + shake, y: by, s: bs, p: b.p ?? 0.62, role: b.role }));
      if (after < 0 || hot) {                         // vật nóng vẫn thấy được sau khi chìm (nằm dưới đáy)
        const sunk = after >= 0;
        if (hot && !sunk) c.K.halo(c, cx, ay, as);
        c.enter(c.k(8, 8), [cx - as, ay - as, as * 2, as * 2], () => c.icon(a.icon || 'ball', { x: cx + (sunk ? shake : 0), y: sunk ? by + bs * 0.42 : ay, s: sunk ? as * 0.82 : as, role: a.role, sy: fall > 0 && !sunk ? 1.18 : 1 }), 'pop');
      }
      if (after >= 0 && after < 9) c.icon('burst', { x: cx, y: by - bs * 0.6, s: 55 + after * 30, alpha: 1 - after / 9, role: hot ? 'hot' : 'accent', plain: true });
      if (a.label && after < 0) { const k = c.k(12, 8); c.K.arrow(c, cx + 310, ay0, cx + as + 24, ay0, k, 'dim'); c.K.label(c, a.label, cx + 190, Math.max(yb + 46, ay0 - 36), k, { align: 'center', maxW: 320, size: 42 }); }
      let y = by + bs + 12;
      if (b.label) { const blb = c.K.label(c, b.label, cx, y + 50, c.k(8, 8), { role: 'dim', align: 'center', size: 42 }); y = blb.y1; }
      if (P.result) c.K.tag(c, P.result, cx, tagY(c, y + 76), c.k(fh + 8, 9));
    },
  };
}

function counter(c0, P) {
  const a10 = alt10('counter', c0, P); if (a10) return a10;
  if (P.layout === 'giant') return counterGiant(c0, P);
  if (P.layout === 'bar') return counterBar(c0, P);
  const N = c0.N, f0 = 6, f1 = Math.max(f0 + 10, Math.round((P.land ?? 0.6) * N)), from = Number(P.from ?? 0), to = Number(P.to ?? P.value ?? 0), dec = P.decimals ?? 0;
  const final = `${P.prefix || ''}${c0.fmtNum(to, dec)}${P.suffix || ''}`;
  const ticks = Array.from({ length: Math.min(8, Math.floor((f1 - f0) / 4)) }, (_, i) => ({ f: f0 + i * 4, name: 'tick' }));
  return {
    cues: [...ticks, { f: f1, name: 'ding', kick: 0.6 }], texts: names(P.title, final, P.unit, P.label),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), k = c.clamp((c.f - f0) / (f1 - f0)), e = c.EASE.out(k), landed = c.f >= f1;
      const v = landed ? to : c.lerp(from, to, e), txt = landed ? final : `${P.prefix || ''}${c.fmtNum(v, dec)}${P.suffix || ''}`;
      const botNeed = P.label ? 112 : 30, availH = Math.max(280, c.A.bottom - botNeed - yb - 24);
      const R = Math.min(305, availH * 0.48), cy = yb + 24 + availH * 0.5;
      c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0: -Math.PI * 1.25, a1: Math.PI * 0.25, role: 'dim', w: 0.6 }], { x: c.A.cx, y: cy, s: R, plain: true, alpha: 0.6 });
      c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0: -Math.PI * 1.25, a1: -Math.PI * 1.25 + Math.PI * 1.5 * Math.max(0.01, e), role: P.role || 'hot', w: 1.5 }], { x: c.A.cx, y: cy, s: R, seed: 3 });
      if (P.icon) c.icon(P.icon, { x: c.A.cx, y: cy - R * 0.56 + bob(c, 2, 5), s: Math.min(62, R * 0.21), role: P.icon_role, p: e });
      const pulse = landed ? 1 + Math.max(0, 1 - (c.f - f1) / 6) * 0.08 : 1;
      const numSize = Math.min(final.length > 6 ? 150 : 190, R * 0.62);
      c.g.save(); c.g.translate(c.A.cx, cy); c.g.scale(pulse, pulse); c.g.translate(-c.A.cx, -cy);
      const nb = c.text(txt, c.A.cx, cy + R * 0.18, { size: numSize, quiet: !landed, enter: 'none', align: 'center', maxW: R * 1.85, track: 0 });
      c.g.restore();
      let lastY = nb.y1;
      if (P.unit) { const ub = c.text(P.unit, c.A.cx, nb.y1 + Math.min(72, R * 0.24), { size: Math.min(64, R * 0.22), role: 'accent', k: c.k(4, 8), align: 'center', maxW: R * 1.8 }); lastY = ub.y1; }
      if (P.label) c.K.tag(c, P.label, c.A.cx, tagY(c, Math.max(cy + R * 0.85 + 62, lastY + 78)), c.k(f1 + 4, 9));
    },
  };
}

function compare(c0, P) {
  const a10 = alt10('compare', c0, P); if (a10) return a10;
  if (P.layout === 'split') return compareSplit(c0, P);
  if (P.layout === 'balance') return compareBalance(c0, P);
  const l = P.left || {}, r = P.right || {}, vmax = Math.max(Number(l.value) || 0, Number(r.value) || 0, 1e-9);
  const lab = (o) => (o.value !== undefined ? `${c0.fmtNum(o.value, decOf(o, P))}${o.unit ? ' ' + o.unit : ''}` : '');
  return {
    cues: [{ f: 8, name: 'pop' }, { f: 16, name: 'pop' }, { f: 30, name: 'hit', kick: 0.5 }], texts: names(P.title, l.label, r.label, lab(l), lab(r)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), botNeed = 76 + (P.result ? 104 : 18) + 36;
      const base = c.A.bottom - botNeed, topNeed = (l.icon || r.icon) ? 215 : 88;
      const maxH = Math.max(130, Math.min(280, base - yb - topNeed)), cols = [[l, c.A.cx - 215, 8], [r, c.A.cx + 195, 16]];
      c.g.fillStyle = c.col('dim'); c.g.fillRect(c.A.x0 + 20, base, c.A.xr(base) - c.A.x0 - 40, 3);
      for (const [o, x, f0] of cols) {
        const k = c.k(f0, 14), e = c.EASE.out(k), h = Math.max(8, maxH * (Number(o.value) || 0) / vmax) * e, win = (Number(o.value) || 0) >= vmax, w = 148;
        c.K.bar(c, x - w / 2, base, w, h, o.role || (win ? 'hot' : 'ink'));
        if (o.icon) c.enter(c.k(f0 + 2, 9), [x - 62, base - h - 160, 124, 124], () => c.icon(o.icon, { x, y: base - h - 92 + bob(c, f0, 5), s: 58, role: o.icon_role, p: o.p ?? 0.6 }));
        if (lab(o)) c.text(k >= 1 ? lab(o) : `${c.fmtNum((Number(o.value) || 0) * e, decOf(o, P))}${o.unit ? ' ' + o.unit : ''}`, x, Math.max(yb + 62, base - h - (o.icon ? 180 : 32)), { size: 52, quiet: k < 1, enter: 'none', align: 'center', role: win ? 'accent' : 'ink', maxW: 390 });
        if (o.label) c.K.label(c, o.label, x, base + 60, c.k(f0 + 4, 8), { align: 'center', maxW: 380, size: 42 });
      }
      if (P.vs) c.text(P.vs, c.A.cx - 10, base - maxH * 0.5, { size: 50, role: 'dim', k: c.k(22, 6), enter: 'pop', align: 'center', font: 'mono' });
      if (P.result) c.K.tag(c, P.result, c.A.cx, tagY(c, base + 150), c.k(30, 9));
    },
  };
}

function graph(c0, P) {
  const pts = (P.points || [[0, 0], [1, 1]]).map((q) => [Number(q[0]), Number(q[1])]);
  const xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys, P.y_min ?? Infinity), y1 = Math.max(...ys, P.y_max ?? -Infinity);
  const N = c0.N, fa = 8, fb = Math.round((P.end ?? 0.8) * N), last = pts[pts.length - 1], dec = P.decimals ?? 0;
  const fin = `${c0.fmtNum(last[1], dec)}${P.y_unit || ''}`;
  const marks = (P.marks || []).map((m) => ({ ...m, f: Math.round(fa + (fb - fa) * (m.x - x0) / Math.max(1e-9, x1 - x0)) }));
  return {
    cues: [{ f: fa, name: 'whoosh_soft' }, ...marks.map((m) => ({ f: m.f, name: 'pop' })), { f: fb, name: 'ding', kick: 0.4 }],
    texts: names(P.title, P.x_label, P.y_label, fin, ...marks.map((m) => m.label)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), L = c.A.x0 + 70, R = c.A.xr(1000) - 40;
      const T = yb + (P.y_label ? 84 : 44), botNeed = (marks.length ? 112 : 0) + (P.x_label ? 52 : 16) + 28;
      const B = Math.max(T + 180, Math.min(T + 480, c.A.bottom - botNeed));
      const X = (v) => c.lerp(L, R, (v - x0) / Math.max(1e-9, x1 - x0)), Y = (v) => c.lerp(B, T, (v - y0) / Math.max(1e-9, y1 - y0));
      c.draw([{ k: 'line', pts: [[L, T - 24], [L, B], [R + 20, B]], role: 'ink', w: 0.7 }], { s: 1, k: c.k(2, 10), seed: 1 });
      for (let i = 1; i <= 4; i++) c.draw([{ k: 'line', pts: [[L, c.lerp(B, T, i / 4)], [R, c.lerp(B, T, i / 4)]], role: 'dim', w: 0.25, dash: [1, 2] }], { s: 1, alpha: 0.5 * c.k(4, 8), plain: true });
      const k = c.clamp((c.f - fa) / (fb - fa)), dense = [];
      for (let i = 0; i < pts.length - 1; i++) for (let j = 0; j < 12; j++) { const t = j / 12, s = t * t * (3 - 2 * t); dense.push([X(c.lerp(pts[i][0], pts[i + 1][0], t)), Y(c.lerp(pts[i][1], pts[i + 1][1], P.smooth === false ? t : s))]); }
      dense.push([X(last[0]), Y(last[1])]);
      if (k > 0) {
        c.draw([{ k: 'line', pts: dense, role: P.role || 'hot', w: 1.4 }], { s: 1, k: Math.max(0.002, k), seed: 2 });
        const idx = Math.min(dense.length - 1, Math.floor(k * (dense.length - 1))), d = dense[idx], val = c.lerp(y1, y0, (d[1] - T) / (B - T));
        c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: P.role || 'hot' }], { x: d[0], y: d[1], s: 15 + Math.sin(c.f * 0.5) * 3, plain: true });
        const tx = Math.min(R - 110, Math.max(L + 130, d[0])), ty = Math.max(T + 14, d[1] - 42);
        c.text(k >= 1 ? fin : `${c.fmtNum(val, dec)}${P.y_unit || ''}`, tx, ty, { size: 56, quiet: k < 1, enter: 'none', align: 'center', role: 'accent' });
      }
      if (P.y_label) c.text(P.y_label, L - 20, T - 46, { size: 32, font: 'mono', role: 'dim', k: c.k(4, 8), align: 'left', weight: 600 });
      if (P.x_label) c.text(P.x_label, R + 10, B + 46, { size: 32, font: 'mono', role: 'dim', k: c.k(4, 8), align: 'right', weight: 600 });
      for (const m of marks) {
        const mk = c.k(m.f, 8, false); if (mk <= 0) continue;
        c.draw([{ k: 'line', pts: [[X(m.x), B], [X(m.x), c.lerp(B, T + 40, c.EASE.out(mk))]], role: 'dim', w: 0.4, dash: [2, 2] }], { s: 1, plain: true });
        c.K.label(c, m.label, Math.min(R - 120, Math.max(L + 120, X(m.x))), Math.min(c.A.bottom - 26, B + (P.x_label ? 104 : 62)), mk, { align: 'center', maxW: 300, size: 36 });
      }
    },
  };
}

function process(c0, P) {
  const a10 = alt10('process', c0, P); if (a10) return a10;
  if (P.layout === 'path') return processPath(c0, P);
  const steps = (P.steps || []).slice(0, 4), N = c0.N, stride = Math.max(8, Math.floor(0.72 * N / Math.max(1, steps.length)));
  return {
    cues: steps.map((_, i) => ({ f: 6 + i * stride, name: i === steps.length - 1 ? 'ding' : 'pop' })), texts: names(P.title, ...steps.map((s) => s.label)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), top = Math.max(yb + 92, c.A.top + 120);
      const gap = Math.min(200, Math.max(105, (c.A.bottom - 76 - top) / Math.max(1, steps.length - 1 || 1))), ix = c.A.x0 + 210;
      const iconS = Math.min(68, Math.max(46, gap * 0.38)), lblS = Math.min(46, Math.max(34, gap * 0.28));
      steps.forEach((s, i) => {
        const y = top + i * gap, f0 = 6 + i * stride, k = c.k(f0, 9), active = c.fs >= f0 && (i === steps.length - 1 || c.fs < f0 + stride);
        if (i > 0) c.K.arrow(c, ix, y - gap + iconS + 10, ix, y - iconS - 14, c.k(f0 - 6, 7), 'dim');
        if (c.K.badge) c.K.badge(c, i + 1, c.A.x0 + 50, y, k); else c.text(String(i + 1).padStart(2, '0'), c.A.x0 + 6, y + 14, { size: 38, font: 'mono', role: 'accent', k, align: 'left', quiet: true, weight: 700 });
        c.enter(k, [ix - iconS, y - iconS, iconS * 2, iconS * 2], () => c.icon(s.icon || 'dot', { x: ix, y: y + (active ? bob(c, i, 5) : 0), s: iconS, role: s.role, p: s.p ?? 0.6 }));
        if (active && k >= 1) c.K.ring(c, ix, y, iconS * 1.38, c.k(f0 + 6, 8));
        c.K.label(c, s.label, ix + 140, y + 14, c.k(f0 + 3, 8), { align: 'left', maxW: c.A.xr(y) - ix - 150, size: lblS, role: active ? 'ink' : 'dim' });
      });
    },
  };
}

function scale(c0, P) {                               // thang kích thước: camera đi qua các bậc theo thang log, vật vẽ đúng tỉ lệ trong khung
  const items = (P.items || []).filter((it) => Number(it.size) > 0), M = items.length, logs = items.map((it) => Math.log(Number(it.size)));
  const pos = (u) => { const x = c0.clamp(u) * Math.max(1, M - 1), i = Math.min(M - 2, Math.floor(x)), t = x - i; return M < 2 ? [0, 0] : [i, c0.MO.M.smooth(c0.clamp((t - 0.3) / 0.7))]; };
  const tx = (it) => `${c0.fmtNum(it.size, decOf(it, P, 'size'))}${it.unit ? ' ' + it.unit : ''}`;
  return {
    cues: items.slice(1).map((_, i) => ({ f: Math.round((i + 0.3) / Math.max(1, M - 1) * c0.N * 0.92), name: 'whoosh' })), texts: names(P.title, ...items.map((it) => it.label), ...items.map(tx)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), botNeed = 166, availH = Math.max(240, c.A.bottom - botNeed - yb - 20);
      const cx = c.A.cx, cy = yb + 20 + availH * 0.48, u = c.clamp(c.f / (c.N * 0.92)), [i, t] = pos(u);
      const ls = M < 2 ? logs[0] || 0 : c.lerp(logs[i], logs[i + 1], t), base = 128, curI = t > 0.55 ? i + 1 : i;
      c.zoomU = M < 2 ? 0 : (ls - logs[0]) / Math.max(1e-9, logs[M - 1] - logs[0]);
      items.forEach((it, j) => {
        const r = base * Math.exp(logs[j] - ls); if (r < 2.5 || r > 2600) return;
        const al = r > 420 ? c.clamp(1 - (r - 420) / 900) : 1, ox = j === 0 ? 0 : (j % 2 ? 1 : -1) * 0, y = cy + bob(c, j, 4);
        if (it.role === 'hot' && r < 500) c.K.halo(c, cx + ox, y, r);
        c.icon(it.icon || 'dot', { x: cx + ox, y, s: r, role: it.role || (j === curI ? 'accent' : 'ink'), alpha: al, plain: r > 500 });
      });
      if (M > 1 && i + 1 < M && t < 0.3) { const k = c.clamp((u * (M - 1) - i) / 0.3), rn = Math.max(26, base * Math.exp(logs[i + 1] - ls) * 1.4); c.K.ring(c, cx, cy, Math.min(rn, 500), k); }
      const it = items[curI]; if (!it) return;
      const settle = t <= 0.02 || t >= 0.98 || M < 2, kk = settle ? 1 : c.clamp(Math.abs(t - 0.55) * 5);
      const lb = c.text(it.label, cx, Math.min(c.A.bottom - 104, cy + availH * 0.52 + 42), { size: 60, k: kk, quiet: !settle, maxW: 800, align: 'center' });
      c.text(tx(it), cx, Math.min(c.A.bottom - 30, lb.y1 + 64), { size: 52, role: 'accent', k: kk, quiet: !settle, align: 'center', font: 'mono', weight: 700 });
    },
  };
}

function callout(c0, P) {
  const labs = (P.labels || []).slice(0, 4), N = c0.N, stride = Math.max(6, Math.floor(0.6 * N / Math.max(1, labs.length)));
  return {
    cues: [{ f: 4, name: 'pop' }, ...labs.map((_, i) => ({ f: 12 + i * stride, name: 'tick' }))], texts: names(P.title, ...labs.map((l) => l.text)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10)), availTop = yb + 64, availBot = c.A.bottom - 36, availH = Math.max(260, availBot - availTop);
      const cx = c.A.cx, cy = availTop + availH * 0.5, s = Math.min(180, availH * 0.33), span = Math.min(250, availH * 0.42);
      c.K.ground(c, cx, cy + s, s * 2.2);
      if (P.icon_role === 'hot') c.K.halo(c, cx, cy, s * 0.8);
      c.enter(c.k(4, 10), [cx - s, cy - s, s * 2, s * 2], () => c.icon(P.icon || 'dot', { x: cx, y: cy + bob(c, 1, 5), s, role: P.icon_role, p: P.icon_p ?? 0.6 }));
      const normY = labs.length > 0 && labs.every((l) => typeof l.y === 'number' && l.y >= 0 && l.y <= 1);
      const placed = { l: [], r: [] };
      labs.forEach((l, i) => {
        const left = String(l.side || (i % 2 ? 'r' : 'l')).toLowerCase().startsWith('l'), sideKey = left ? 'l' : 'r';
        const rawY = typeof l.y === 'number' ? (normY ? (l.y - 0.5) * 2.4 : l.y) : (i < 2 ? -0.85 : 0.85);
        const yOff = c.clamp(rawY, -1.0, 1.0);
        let ly = c.clamp(cy + yOff * span, availTop + 56, availBot);
        for (const py of placed[sideKey]) if (Math.abs(ly - py) < 92) ly = c.clamp(ly >= py ? py + 94 : py - 94, availTop + 56, availBot);
        placed[sideKey].push(ly);
        const lx = left ? c.A.x0 + 10 : c.A.xr(ly) - 10, k = c.k(12 + i * stride, 9);
        const ax = cx + (left ? -1 : 1) * s * 0.78, ay = cy + yOff * s * 0.48;
        const lb = c.K.label(c, l.text, lx, ly - 44, k, { align: left ? 'left' : 'right', maxW: 270, size: 38, role: l.role || 'ink' });
        const xStart = left ? Math.min(ax - 24, lb ? lb.x1 + 18 : lx + 210) : Math.max(ax + 24, lb ? lb.x0 - 18 : lx - 210);
        c.K.arrow(c, xStart, ly - 24, ax, ay, k, 'dim');
      });
    },
  };
}

function fact(c0, P) {
  const a10 = alt10('fact', c0, P); if (a10) return a10;
  if (P.layout === 'stamp') return factStamp(c0, P);
  if (P.layout === 'left') return factLeft(c0, P);
  return {
    cues: [{ f: 2, name: 'whoosh_soft' }, { f: Math.round(c0.N * 0.4), name: 'hit', kick: 0.6 }], texts: names(P.kicker, P.text, P.em),
    draw(c) {
      const left = c.L.type.align === 'left', x = left ? c.A.x0 : c.A.cx;
      if (P.kicker) c.text(P.kicker, x, c.A.top + 38, { size: 32, font: 'mono', role: 'dim', k: c.k(1, 8), weight: 600, enter: 'type' });
      const topY = c.A.top + (P.kicker ? 88 : 28), botY = c.A.bottom - 36, iconH = P.icon ? 185 : 0, emRes = P.em ? 126 : 16;
      const tf = fitText(c, P.text, x, [P.size || 96, 84, 72, 62, 52], { maxW: 860, lh: 1.1, maxH: Math.max(150, botY - topY - iconH - emRes) });
      const totalH = iconH + tf.h + (P.em ? 116 : 0), startY = topY + Math.max(0, (botY - topY - totalH) / 2);
      if (P.icon) c.enter(c.k(3, 9), [c.A.cx - 95, startY, 190, 190], () => c.icon(P.icon, { x: c.A.cx, y: startY + 86 + bob(c), s: 94, role: P.icon_role, p: 0.6 }));
      const b = c.text(P.text, x, startY + iconH - tf.b.y0, { size: tf.size, k: c.k(4, 12), maxW: 860, lh: 1.1 });
      if (P.em) { const f0 = Math.round(c.N * 0.4), bb = c.K.tag(c, P.em, c.A.cx, tagY(c, b.y1 + 102), c.k(f0, 9)); if (bb) c.K.ring(c, (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2, Math.min(160, Math.max(100, (bb.x1 - bb.x0) * 0.55)), c.k(f0 + 8, 10)); }
    },
  };
}

function outro(c0, P) {
  return {
    cues: [{ f: 2, name: 'pop' }], texts: names(P.next_prefix, P.teaser, P.follow),
    draw(c) {
      const yb = c.K.header(c, { kicker: P.next_prefix, title: P.teaser, size: 92 }, c.k(1, 12));
      const botNeed = P.follow ? 120 : 36, availH = Math.max(200, c.A.bottom - botNeed - yb - 24);
      const s = Math.min(124, availH * 0.36), cy = yb + 24 + availH * 0.48;
      const a = c.f * 0.05;                            // vòng lặp: mũi tên chạy vòng (video nối về đầu)
      c.draw([{ k: 'arc', x: 0, y: 0, r: 1, a0: a, a1: a + 4.6, role: 'accent', w: 1.3 }, { k: 'poly', role: 'accent', pts: [[Math.cos(a + 4.6) * 1.0 - Math.sin(a + 4.6) * 0.22, Math.sin(a + 4.6) + Math.cos(a + 4.6) * 0.22], [Math.cos(a + 4.6) * 1.22, Math.sin(a + 4.6) * 1.22], [Math.cos(a + 4.6) * 0.78, Math.sin(a + 4.6) * 0.78]] }],
             { x: c.A.cx, y: cy, s: s * c.EASE.out(c.k(4, 10)) + 0.01, seed: 4 });
      if (P.follow) c.K.tag(c, P.follow, c.A.cx, tagY(c, cy + s + 98), c.k(12, 9));
    },
  };
}

// ---- scene: cảnh ghép tự do — nhiều đạo cụ/nhân vật di chuyển theo keyframe, nhãn, mũi tên nối vật, hiệu ứng ----
// params: {kicker?, title?, actors:[{id, icon | lottie (tên trong assets/user/lottie, colors palette|<vai>|keep) | rive (tên
//          .riv, animation | state_machine, artboard), speed, loop, start (giây), x, y (0..1 của khung), size (px, mặc định 170), role, rot (độ), p,
//          z (chiều sâu: 0 = mặt phẳng nét, > 0 xa dần, < 0 sát ống kính), action/expr/face (nhân vật "rig:<loài>"),
//          verb + args (động từ chạy suốt đời diễn viên), in (u xuất hiện, mặc định 0), out (u biến mất),
//          keys:[{u, x, y, size, rot, p, alpha, z, ease, action, expr, verb, dur (u), args}]}],
//          labels:[{text, x, y, z, u, size, role, of (id actor: nhãn đi theo vật)}], arrows:[{from, to, u}],
//          fx:[{kind: burst|shockwave|smoke|splash|sparkle, x, y, z | at (id actor), u}],
//          camera:[{u, x, y (điểm nhìn 0..1), z (dolly: + là tiến vào), rot (độ, máy nghiêng), focus (độ sâu nét), ease}],
//          depth: false | true | {layers, fg, dof, fog}, seed}
// Thời gian dùng u (0..1 của shot) — shot được co giãn theo giọng đọc, nên dàn cảnh không phụ thuộc số giây.
// Chiều sâu 2D (vòng 10): điểm (x, y, z) chiếu qua camera → cỡ × 1/(1 + (z − cam.z)/2) (phối cảnh), trôi theo camera với thị
// sai đúng theo z, DOF = mờ theo |z − focus|, không khí = tối dần về nền đen theo z; lớp bụi xa + vật lướt sát ống kính tự
// sinh theo look (hạt giống theo nội dung). Không có z/camera/depth → vẽ y hệt cảnh cũ (tương thích ngược).
// động từ chuyển động: lib/motion (WP-M) có play()/canvasDelta() → dùng (58 verb, t = giây, cùng kết quả với Python);
// bản lib/motion cũ chưa có → bộ dự phòng nhỏ cùng quy ước (x/y theo cỡ vật, y hướng LÊN, rot độ ngược kim; dur = giây)
const VERB_FALLBACK = {
  pulse: (k) => { const w = Math.sin(Math.PI * k) * 0.14; return { sx: 1 + w, sy: 1 + w }; },
  heartbeat: (k, a, t) => { const per = 60 / Math.max(20, a.bpm ?? 72), w = lubdub(((t % per) + per) % per) * 0.18; return { sx: 1 + w, sy: 1 + w }; },
  shake: (k) => ({ x: Math.sin(k * 95) * 0.08 * (1 - k) }),
  wobble: (k) => ({ rot: Math.sin(k * Math.PI * 6) * 12 * (1 - k) }),
  squash: (k) => { const w = Math.sin(Math.PI * k) * 0.25; return { sx: 1 + w, sy: 1 - w }; },
  hop: (k) => ({ y: Math.sin(Math.PI * k) * 0.5 }),
  spin: (k) => ({ rot: -360 * k }),
  flash: (k) => ({ glow: 1 - k }),
  pop: (k) => { const e = Math.min(1, k * 1.6), sc = Math.max(0.001, e + Math.sin(e * Math.PI) * 0.18); return { sx: sc, sy: sc, alpha: Math.min(1, k * 5) }; },
  dissolve: (k) => ({ alpha: 1 - k }),
  float: (k, a, t) => ({ y: Math.sin(t * 2.2) * 0.06 }),
  breathe: (k, a, t) => { const b = Math.sin(t * 2 * Math.PI * (a.rate ?? 15) / 60) * 0.04; return { sx: 1 + b, sy: 1 - b * 0.6 }; },
  sway: (k, a, t) => ({ rot: Math.sin(t * 1.8) * 6 }),
};
const VERB_IDLE = new Set(['heartbeat', 'float', 'breathe', 'sway']);
/** Delta động từ của một diễn viên ở frame hiện tại → toạ độ canvas: {x, y (px), z (cỡ vật, về camera), sx, sy, rot (rad), alpha, glow, blur, reveal} */
function verbDelta(c, items, i, n, size) {
  const MO = c.MO;
  if (!items.length) return null;
  if (MO && typeof MO.play === 'function' && typeof MO.canvasDelta === 'function') {
    const d = MO.play(items, c.f, c.N, c.FPS, i, n), cd = MO.canvasDelta(d, size);
    return { x: cd.dx, y: cd.dy, z: d.z || 0, sx: cd.sx, sy: cd.sy, rot: cd.rot, alpha: cd.alpha, glow: cd.glow, blur: cd.blur, reveal: cd.reveal };
  }
  const m = { x: 0, y: 0, z: 0, sx: 1, sy: 1, rot: 0, alpha: 1, glow: 0, blur: 0, reveal: 1 };
  for (const it of items) {
    const name = String(it.verb || '').replace(/-/g, '_'), fb = VERB_FALLBACK[name]; if (!fb) continue;
    const t0 = it.t ?? (it.f !== undefined ? it.f / c.FPS : (it.u ?? 0) * Math.max(0, c.N - 1) / c.FPS), t = c.f / c.FPS - t0;
    const dur = it.dur ?? (it.args || {}).dur ?? (VERB_IDLE.has(name) ? null : 0.6);
    if (t < 0 || (dur !== null && t > dur)) continue;
    const o = fb(dur ? c.clamp(t / dur) : 0, it.args || {}, t);
    m.x += (o.x || 0) * size; m.y -= (o.y || 0) * size; m.rot -= (o.rot || 0) * Math.PI / 180;
    m.sx *= o.sx ?? 1; m.sy *= o.sy ?? 1; m.alpha *= o.alpha ?? 1; m.glow = Math.max(m.glow, o.glow || 0);
  }
  return m;
}
const VID = { x: 0, y: 0, z: 0, sx: 1, sy: 1, rot: 0, alpha: 1, glow: 0, blur: 0, reveal: 1 };
function scene(c0, P) {
  const N = c0.N, acts = P.actors || [], labs = P.labels || [], arrs = P.arrows || [], fxs = P.fx || [];
  const uf = (u) => Math.round(c0.clamp(u ?? 0) * (N - 1));
  const FXSFX = { burst: 'hit', shockwave: 'boom', smoke: 'whoosh_soft', splash: 'splash', sparkle: 'sparkle' };
  const DK = ['x', 'y', 'size', 'rot', 'p', 'alpha', 'z', 'heat'];
  const keysOf = (a) => {                              // keyframe đã sắp theo u, thuộc tính thiếu lấy từ key trước
    const ks = [{ u: a.in ?? 0, x: a.x ?? 0.5, y: a.y ?? 0.55, size: a.size ?? 170, rot: a.rot ?? 0, p: a.p ?? 0.6, alpha: 1, z: a.z ?? 0, heat: a.heat ?? 0 },
      ...(a.keys || []).map((k) => ({ ...k }))].sort((p, q) => (p.u ?? 0) - (q.u ?? 0));
    for (let i = 1; i < ks.length; i++) for (const key of DK) if (ks[i][key] === undefined) ks[i][key] = ks[i - 1][key];
    return ks;
  };
  const KS = Object.fromEntries(acts.map((a, i) => [a.id || `a${i}`, keysOf(a)]));
  const pose = (id, u, c) => {                         // nội suy keyframe (thuộc tính thiếu → giữ giá trị trước)
    const ks = KS[id];
    let cur = { ...ks[0] };
    for (let i = 1; i < ks.length; i++) {
      const k = ks[i], prev = { ...ks[i - 1] };
      const u0 = ks[i - 1].u ?? 0, u1 = k.u ?? 0;
      if (u <= u0) break;
      const t = u1 > u0 ? c.clamp((u - u0) / (u1 - u0)) : 1, e = (c.EASE[k.ease] || c.E)(t);
      for (const key of DK) cur[key] = c.lerp(prev[key], k[key], e);
      if (u < u1) break;
    }
    return cur;
  };
  const discrete = (a, id, u, key) => { let v = a[key]; for (const k of KS[id]) if ((k.u ?? 0) <= u && k[key] !== undefined) v = k[key]; return v; };
  // động từ của diễn viên: do:[{u|t|f, verb, dur (giây), args, stagger}] + key có verb + verb của cả diễn viên (cú pháp lib/motion)
  const VI = Object.fromEntries(acts.map((a, i) => [a.id || `a${i}`, [...(a.do || []), ...(a.keys || []).filter((k) => k.verb),
    ...(a.verb ? [{ u: a.in ?? 0, verb: a.verb, args: a.args || {} }] : [])]]));
  // ---- camera + chiều sâu ----
  const CK = [{ u: 0, x: 0.5, y: 0.5, z: 0, rot: 0, focus: 0 }, ...(P.camera || []).map((k) => ({ ...k }))].sort((p, q) => (p.u ?? 0) - (q.u ?? 0));
  for (let i = 1; i < CK.length; i++) for (const key of ['x', 'y', 'z', 'rot', 'focus']) if (CK[i][key] === undefined) CK[i][key] = CK[i - 1][key];
  if (CK.length > 1 && (CK[1].u ?? 0) <= 0) CK.shift();           // key của người viết ở u=0 thay cho mặc định
  const camAt = (u, c) => {
    let cur = { ...CK[0] };
    for (let i = 1; i < CK.length; i++) {
      const u0 = CK[i - 1].u ?? 0, u1 = CK[i].u ?? 0;
      if (u <= u0) break;
      const t = u1 > u0 ? c.clamp((u - u0) / (u1 - u0)) : 1, e = (c.EASE[CK[i].ease] || c.EASE.smooth)(t);
      for (const key of ['x', 'y', 'z', 'rot', 'focus']) cur[key] = c.lerp(CK[i - 1][key], CK[i][key], e);
      if (u < u1) break;
    }
    return cur;
  };
  const usesZ = acts.some((a) => a.z !== undefined || (a.keys || []).some((k) => k.z !== undefined)) || labs.some((l) => l.z !== undefined) || fxs.some((x) => x.z !== undefined);
  const depthOn = P.depth !== false && (P.depth === true || (P.depth && typeof P.depth === 'object') || usesZ || (P.camera || []).length > 0);
  const DO = { layers: true, fg: true, dof: 1, fog: 0.25, ...(P.depth && typeof P.depth === 'object' ? P.depth : {}) };
  const seed = P.seed !== undefined ? (num(P.seed) | 0) : (c0.strSeed(JSON.stringify([P.title, P.kicker, acts.map((a) => a.id || a.icon)])) >>> 0);
  const proj = (c, cam, x, y, z) => {                  // điểm thế giới (0..1 khung, z) → [x px, y px, tỉ lệ phối cảnh, độ sâu so với camera]
    const d = (z || 0) - cam.z, s = 1 / Math.max(0.12, 1 + d / 2);   // tiêu cự 2: z = 2 → nhỏ một nửa
    let sx = c.W / 2 + (x - cam.x) * c.W * s, sy = c.H / 2 + (y - cam.y) * c.H * s;
    if (cam.rot) { const r = -cam.rot * Math.PI / 180, dx = sx - c.W / 2, dy = sy - c.H / 2; sx = c.W / 2 + dx * Math.cos(r) - dy * Math.sin(r); sy = c.H / 2 + dx * Math.sin(r) + dy * Math.cos(r); }
    return [sx, sy, s, d];
  };
  const lens = (cam, z, d, extraBlur = 0) => {         // DOF + không khí → chuỗi ctx.filter
    const b = Math.min(10, DO.dof * 4 * Math.abs((z || 0) - cam.focus) + extraBlur), br = Math.max(0.4, Math.exp(-DO.fog * Math.max(0, d)));
    return `${b > 0.6 ? `blur(${b.toFixed(1)}px) ` : ''}${br < 0.985 ? `brightness(${br.toFixed(3)})` : ''}`.trim() || 'none';
  };
  const DUST = Array.from({ length: 26 }, (_, i) => ({ x: -1.2 + c0.hash(i, seed, 1) * 3.4, y: -0.3 + c0.hash(i, seed, 2) * 1.6, z: 1.6 + c0.hash(i, seed, 3) * 4.4, r: 5 + c0.hash(i, seed, 4) * 12, k: i % 3 }));
  const fgU = c0.hash(seed, 7, 1) < 0.5 ? 0.06 + c0.hash(seed, 7, 2) * 0.22 : 0.56 + c0.hash(seed, 7, 3) * 0.12;   // né u≈0.5 và cuối shot (frame OCR)
  const cues = [...fxs.map((x) => ({ f: uf(x.u), name: FXSFX[x.kind] || 'pop', kick: x.kind === 'burst' || x.kind === 'shockwave' ? 0.7 : 0 })),
                ...acts.filter((a) => (a.in ?? 0) > 0.02).map((a) => ({ f: uf(a.in), name: 'pop' })),
                ...(depthOn && DO.fg && N >= 45 ? [{ f: uf(fgU + 0.1), name: 'whoosh_soft' }] : [])];
  return {
    cues, texts: names(P.kicker, P.title, ...labs.map((l) => l.text)),
    draw(c) {
      const yb = (P.title || P.kicker) ? drawHeader(c, P, c.k(1, 10), true) : c.A.top;
      const u = c.clamp(c.f / Math.max(1, N - 1)), at = {}, g = c.g, cam = camAt(u, c);
      if (depthOn && DO.layers) {                      // hậu cảnh: bụi/mảnh xa, thị sai + DOF theo đúng camera của cảnh
        const kind = { hud: 'spark', synth: 'spark', sketch: 'cross', boil: 'cross', swiss: 'tick', picto: 'disc', spy: 'strip' }[c.L.look] || 'mote';
        for (const p of DUST) {
          const [x, y, s, d] = proj(c, cam, p.x, p.y + Math.sin((c.f + p.r * 7) * 0.015) * 0.01, p.z); if (x < -40 || x > c.W + 40 || y < -40 || y > c.H + 40) continue;
          const pr = kind === 'spark' ? [{ k: 'circle', x: 0, y: 0, r: 0.4, role: 'ink' }] : kind === 'cross' ? [{ k: 'line', pts: [[-1, 0], [1, 0]], role: 'dim' }, { k: 'line', pts: [[0, -1], [0, 1]], role: 'dim' }]
            : kind === 'tick' ? [{ k: 'line', pts: [[0, -1], [0, 1]], role: 'dim' }] : kind === 'disc' ? [{ k: 'circle', x: 0, y: 0, r: 1, role: 'dim' }]
            : kind === 'strip' ? [{ k: 'rect', x: -1.6, y: -0.3, w: 3.2, h: 0.6, rad: 0, role: 'dim' }] : [{ k: 'circle', x: 0, y: 0, r: 1, role: 'dim', fill: p.k !== 0 }];
          g.save(); g.filter = lens(cam, p.z, d);
          c.draw(pr, { x, y, s: p.r * Math.min(1.2, s * 2.2), rot: c.f * 0.004 + p.r, plain: true, alpha: 0.5, lw: 0.6 });
          g.restore();
        }
      }
      const order = acts.map((a, i) => {
        const id = a.id || `a${i}`, q = pose(id, u, c), vm = verbDelta(c, VI[id], i, acts.length, q.size) || VID;
        const z = q.z - vm.z * q.size / c.H, [x0, y0, s, d] = proj(c, cam, q.x, q.y, z);
        const r = q.size / 2 * s, x = x0 + vm.x * s, y = y0 + vm.y * s;
        at[id] = [x, y, r];
        return { a, i, id, q, vm, z, d, x, y, r };
      });
      if (depthOn) order.sort((p, q) => q.d - p.d || p.i - q.i);   // xa vẽ trước (painter)
      for (const o of order) {
        const { a, i, id, q, vm, x, y, r } = o, s = r;
        const kin = c.k(uf(a.in ?? 0), 8, false), kout = a.out !== undefined ? 1 - c.k(uf(a.out), 6, false) : 1;
        if (kin <= 0 || kout <= 0 || o.d < -1.76) continue;
        g.save();
        if (depthOn) g.filter = lens(cam, o.z, o.d, vm.blur);
        else if (vm.blur > 0.6) g.filter = `blur(${vm.blur.toFixed(1)}px)`;
        if ((a.role === 'hot' && s < 400) || vm.glow > 0.05) c.K.halo(c, x, y, s * (1 + 0.3 * vm.glow));
        const rot = (q.rot - (depthOn ? cam.rot : 0)) * Math.PI / 180 + vm.rot, alpha = q.alpha * kout * vm.alpha;
        if (a.lottie_url || a.rive_url) {                   // media actor: Lottie/Rive chạy theo frame (engines/html/media.js)
          c.enter(kin, [x - s, y - s, 2 * s, 2 * s], () => c.media.draw(a, x, y, s, c.f - uf(a.in ?? 0), c.FPS, alpha, rot));
        } else {
          // nhân vật rig:<loài> (rig2d.js): hành động/biểu cảm đổi theo key, đồng hồ riêng từ lúc vào, tự quay mặt theo hướng đi
          const rig = typeof a.icon === 'string' && a.icon.startsWith('rig:'), dx = rig ? q.x - pose(id, Math.max(0, u - 0.02), c).x : 0;
          const face = a.face || (rig && !/:(left|right)\b/.test(a.icon) && dx < -1e-4 ? 'left' : undefined);
          const args = { action: discrete(a, id, u, 'action'), expr: discrete(a, id, u, 'expr'), face, hair: a.hair, colors: a.colors, heat: q.heat, t0: uf(a.in ?? 0) / c.FPS };
          c.enter(kin, [x - s, y - s, 2 * s, 2 * s], () => c.icon(a.icon || 'dot', { x, y, s, sx: vm.sx, sy: vm.sy, role: a.role, p: q.p, rot, alpha, heat: q.heat, seed: i + 3, args, k: vm.reveal, z: o.z }));
        }
        g.restore();
      }
      for (const ar of arrs) {
        const A = at[ar.from], B = at[ar.to]; if (!A || !B) continue;
        const k = c.k(uf(ar.u ?? 0.3), 9, false), d = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1, ux = (B[0] - A[0]) / d, uy = (B[1] - A[1]) / d;
        c.K.arrow(c, A[0] + ux * A[2] * 1.15, A[1] + uy * A[2] * 1.15, B[0] - ux * B[2] * 1.2, B[1] - uy * B[2] * 1.2, k, 'dim');
      }
      for (const x of fxs) {
        const f0 = uf(x.u), t = c.f - f0; if (t < 0 || t > 22) continue;
        const A = x.at && at[x.at], pp = A ? null : depthOn ? proj(c, cam, x.x ?? 0.5, x.y ?? 0.5, x.z ?? 0) : [(x.x ?? 0.5) * c.W, (x.y ?? 0.5) * c.H, 1];
        const px = A ? A[0] : pp[0], py = A ? A[1] : pp[1], sc = A ? Math.max(0.3, A[2] / 85) : pp[2];
        if (x.kind === 'splash') {                     // các giọt nhỏ bắn toả ra
          for (let i = 0; i < 7; i++) { const ang = -Math.PI * (0.1 + 0.8 * i / 6), rr = (30 + t * 14) * (depthOn ? sc : 1), gy = t * t * 0.9;
            c.icon('drop', { x: px + Math.cos(ang) * rr, y: py + Math.sin(ang) * rr + gy, s: 18, alpha: 1 - t / 22, role: x.role || 'cold', plain: true }); }
        } else c.icon(x.kind, { x: px, y: py, s: (60 + t * 16) * (depthOn ? Math.min(2, sc) : 1), alpha: 1 - t / 22, role: x.role || 'accent', plain: true });
      }
      if (depthOn && DO.fg && N >= 45) {               // tiền cảnh: một vật mờ lướt sát ống kính (z≈−0.5), che khuất thoáng qua
        const t = (u - fgU) / 0.26;
        if (t > 0 && t < 1) {
          const wx = cam.x + c.lerp(-0.75, 0.75, t), wy = 0.25 + c.hash(seed, 9) * 0.5, [x, y, s] = proj(c, cam, wx, wy, cam.z - 0.5);
          g.save(); g.filter = 'blur(18px) brightness(0.35)';
          c.draw(c.hash(seed, 11) < 0.5 ? [{ k: 'circle', x: 0, y: 0, r: 1, role: 'dim' }] : [{ k: 'rect', x: -0.6, y: -1.2, w: 1.2, h: 2.4, rad: 0.5, role: 'dim' }],
                 { x, y, s: 150 * s, plain: true, alpha: 0.65 });
          g.restore();
        }
      }
      for (const l of labs) {
        const A = l.of && at[l.of], k = c.k(uf(l.u ?? 0.2), 8, false);
        // nhãn bám vật: kẹp trong vùng an toàn theo bề rộng chữ (đo bằng k=0, không vẽ). Viên nhãn mỗi look một kiểu
        // (mono IN HOA + ngoặc ở hud…) → đo bản rộng nhất (mono, in hoa, có ngoặc) cho chắc, thừa thì nhãn chỉ lùi vào trong.
        const b = !A ? null : l.tag ? c.text(`[ ${l.text} ]`, 0, 0, { size: 62, font: 'mono', upper: true, k: 0, maxW: 820 })
          : c.text(l.text, 0, 0, { size: l.size || 54, k: 0, maxW: 760 });
        const hw = b ? Math.min((c.A.x1 - c.A.x0) / 2, (b.x1 - b.x0) / 2 + (l.tag ? 40 : 20)) : 0;
        const Lp = !A && depthOn && l.z !== undefined ? proj(c, cam, l.x ?? 0.5, l.y ?? 0.8, l.z) : null;
        const x = A ? Math.min(c.A.x1 - hw, Math.max(c.A.x0 + hw, A[0])) : Lp ? Lp[0] : (l.x ?? 0.5) * c.W;
        const rawY = A ? A[1] + A[2] + 70 : Lp ? Lp[1] : (l.y ?? 0.8) * c.H;
        const minLabY = Math.max(c.A.top + 70, yb + (l.tag ? 76 : 48));
        const y = Math.min(c.A.bottom - 26, Math.max(minLabY, rawY));
        if (l.tag) c.K.tag(c, l.text, x, y, k, l.role || 'accent'); else c.K.label(c, l.text, x, y, k, { align: 'center', size: l.size || 54, role: l.role, maxW: 760 });
      }
    },
  };
}

// ================= VÒNG 10 — beat mới =================
function units(c0, P) {                               // biểu đồ đơn vị (isotype) 1–3 nhóm: mỗi biểu tượng = per đơn vị THẬT, rơi cùng nhịp
  const gs = (P.groups || []).slice(0, 3), vals = gs.map((g) => num(g.value)), per = perUnit(vals, num(P.max_units, 120), num(P.per));
  const ns = vals.map((v) => Math.abs(v) / per), cmax = Math.max(1, ...ns.map((n) => Math.ceil(n - 1e-9))), N = c0.N;
  const f0 = 6, f1 = Math.max(f0 + 14, Math.round((P.land ?? 0.68) * N)), fOf = (i) => f0 + (f1 - f0) * (cmax > 1 ? i / (cmax - 1) : 0);
  const ends = ns.map((n) => Math.round(fOf(Math.max(0, Math.ceil(n - 1e-9) - 1)))), legend = legendOf(c0, per, P, P.per_unit || P.unit);
  const vt = (g) => `${c0.fmtNum(num(g.value), g.decimals ?? P.decimals ?? decN(num(g.value)))}${(g.unit || P.unit) ? ' ' + (g.unit || P.unit) : ''}`;
  return {
    cues: [{ f: f0, name: 'whoosh_soft' }, ...ends.map((f) => ({ f, name: 'tick' })), { f: f1 + 2, name: 'ding', kick: 0.4 }],
    texts: names(P.title, ...gs.map((g) => g.label), ...gs.map(vt), `= ${legend}`, P.result),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10), true), top = Math.max(yb + (P.result ? 108 : 54), c.A.stageTop + 30), bot = c.A.bottom - 134, n = gs.length || 1, W0 = c.A.x1 - c.A.x0;
      const rows = n === 3, boxes = gs.map((_, i) => (rows
        ? { x: c.A.x0, y: top + i * (bot - top) / 3 + 56, w: W0, h: Math.max(64, (bot - top) / 3 - 76) }
        : { x: c.A.x0 + i * (W0 + 50) / n, y: top + 68, w: (W0 - 50 * (n - 1)) / n, h: Math.max(120, bot - top - 120) }));
      const s = Math.min(...ns.map((v, i) => unitGrid(v, boxes[i], { maxS: 108 }).s));
      gs.forEach((g, i) => {
        const bx = boxes[i], grid = unitGrid(ns[i], bx, { maxS: s, anchor: rows ? 'center' : 'bottom', up: !rows });
        const shown = drawUnits(c, grid, ns[i], { icon: g.icon || P.icon, role: g.role || ['hot', 'cold', 'accent'][i], fOf, seed: 70 + i * 9 });
        const done = c.f >= ends[i], v = Math.min(Math.abs(vals[i]), shown * per), cx = bx.x + bx.w / 2;
        const ty = rows ? bx.y - 16 : Math.max(top + 38, grid.y0 - 30), tx = rows ? bx.x : cx, al = rows ? 'left' : 'center';
        if (g.label) c.K.label(c, g.label, tx, rows ? ty - 42 : bot + 14, c.k(f0 + i * 3, 8), { align: al, maxW: rows ? 580 : bx.w, size: 40 });
        c.text(done ? vt(g) : `${c.fmtNum(v, decN(per))}${(g.unit || P.unit) ? ' ' + (g.unit || P.unit) : ''}`, rows ? bx.x + bx.w : tx, ty, { size: rows ? 44 : 52, quiet: !done, enter: 'none', role: done ? 'accent' : 'ink', align: rows ? 'right' : 'center', maxW: rows ? 360 : bx.w });
      });
      drawLegend(c, gs[0] && (gs[0].icon || P.icon), gs[0] && (gs[0].role || 'hot'), legend, c.A.cx, tagY(c, c.A.bottom - 38), c.k(f0 + 6, 8));
      if (P.result) c.K.tag(c, P.result, c.A.cx, Math.max(yb + 46, top - 34), c.k(f1 + 4, 9));
    },
  };
}

// lớp thị sai dùng chung (timeline, scene): vật xa trôi chậm hơn camera → thấy chiều sâu; hạt giống theo nội dung video
function parallaxDust(c, camX, camY, seed, o = {}) {
  const look = c.L.look, kind = { hud: 'spark', synth: 'spark', sketch: 'cross', boil: 'cross', swiss: 'tick', picto: 'disc', spy: 'strip' }[look] || 'mote';
  const n = o.n ?? 26, g = c.g;
  for (let i = 0; i < n; i++) {
    const z = 1.6 + c.hash(i, seed, 1) * 4.5, par = 1 / (1 + z), span = c.W * 3;
    const wx = c.hash(i, seed, 2) * span, wy = c.hash(i, seed, 3) * c.H;
    const x = (((wx - camX * par) % span) + span) % span - c.W, y = (((wy - camY * par + Math.sin((c.f + i * 13) * 0.02) * 12) % c.H) + c.H) % c.H;
    if (x < -60 || x > c.W + 60) continue;
    const s = (5 + c.hash(i, seed, 4) * 12) * (1.4 - par), rot = c.f * 0.004 * (i % 2 ? 1 : -1) + i;
    const pr = kind === 'spark' ? [{ k: 'circle', x: 0, y: 0, r: 0.35, role: 'ink' }] : kind === 'cross' ? [{ k: 'line', pts: [[-1, 0], [1, 0]], role: 'dim' }, { k: 'line', pts: [[0, -1], [0, 1]], role: 'dim' }]
      : kind === 'tick' ? [{ k: 'line', pts: [[0, -1], [0, 1]], role: 'dim' }] : kind === 'disc' ? [{ k: 'circle', x: 0, y: 0, r: 1, role: 'dim' }]
      : kind === 'strip' ? [{ k: 'rect', x: -1.6, y: -0.3, w: 3.2, h: 0.6, rad: 0, role: 'dim' }] : [{ k: 'circle', x: 0, y: 0, r: 1, role: 'dim', fill: i % 3 !== 0 }];
    g.save(); if (o.dof !== false && z > 2.5) g.filter = `blur(${Math.min(5, (z - 2.5) * 1.4).toFixed(1)}px)`;
    c.draw(pr, { x, y, s, rot, plain: true, alpha: (o.alpha ?? 0.45) * (1.15 - par), lw: 0.6 });
    g.restore();
  }
}

function timeline(c0, P) {                            // trục thời gian: khoảng cách ∝ thời gian thật (giãn tối thiểu để đọc), camera đi dọc sự kiện
  const ev = (P.events || []).map((e, i) => ({ ...e, t: num(e.t, i), i })).sort((a, b) => a.t - b.t).slice(0, 8), n = Math.max(1, ev.length), N = c0.N;
  const year = P.format === 'year' || (P.format !== 'number' && ev.length && ev.every((e) => Number.isInteger(e.t) && e.t >= 1000 && e.t <= 2999));
  const tl = (e) => e.t_label ?? (year ? String(e.t) : `${c0.fmtNum(e.t, decN(e.t))}${P.unit ? ' ' + P.unit : ''}`);
  const logT = P.scale === 'log' && ev.every((e) => e.t > 0), T = (t) => (logT ? Math.log(t) : t), t0 = T(ev[0] ? ev[0].t : 0), t1 = T(ev[n - 1] ? ev[n - 1].t : 1);
  const GAP = 430, Lw = Math.max(GAP * (n - 1), 1500), xs = [];
  ev.forEach((e, i) => { const raw = (T(e.t) - t0) / Math.max(1e-9, t1 - t0) * Lw; xs.push(i ? Math.max(raw, xs[i - 1] + GAP) : 0); });
  const f0 = 6, f1 = Math.max(f0 + 10, N - 8), seed = c0.strSeed(ev.map((e) => e.label).join('|')) >>> 0;
  const pos = (f) => { const x = c0.clamp((f - f0) / (f1 - f0)) * Math.max(1, n - 1), i = Math.min(n - 2, Math.floor(x)), t = x - i;
    return n < 2 ? [0, 0] : [i, c0.MO.M.smooth(c0.clamp((t - 0.25) / 0.75))]; };
  const arrive = ev.map((_, i) => Math.round(f0 + (f1 - f0) * (i === 0 ? 0 : (i - 1 + 1) / Math.max(1, n - 1))));
  return {
    cues: [...ev.map((_, i) => ({ f: arrive[i], name: 'pop' })), ...ev.slice(1).map((_, i) => ({ f: Math.round(f0 + (f1 - f0) * (i + 0.3) / Math.max(1, n - 1)), name: 'whoosh_soft' }))],
    texts: names(P.title, ...ev.map(tl), ...ev.map((e) => e.label)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10), true), availTop = yb + 34, availBot = c.A.bottom - 30, spanH = Math.max(320, availBot - availTop);
      const ay = availTop + spanH * 0.52, stem = Math.min(126, spanH * 0.16), [i, t] = pos(c.f);
      const camX = n < 2 ? 0 : c.lerp(xs[i], xs[i + 1], t), dz = 1 - 0.1 * Math.sin(Math.PI * t), cx = c.A.cx, X = (x) => cx + (x - camX) * dz, g = c.g;
      parallaxDust(c, camX, 0, seed, { n: 22 });
      // năm/mốc lớn mờ ở hậu cảnh (thị sai 0.35): camera đi qua như qua các lớp
      // chỉ mốc đang tới/đang rời (đan chéo), lớp này trôi 0.35 lần tốc độ camera → thấy hai tầng sâu
      [[i, 1 - t], [Math.min(n - 1, i + 1), t]].forEach(([j, w]) => { const e = ev[j]; if (!e || w < 0.02) return;
        g.save(); g.globalAlpha *= 0.12 * w; g.filter = 'blur(2px)';
        c.text(tl(e), cx + (xs[j] - camX) * 0.35, Math.min(c.A.bottom - 40, ay + 180), { size: 220, font: 'mono', quiet: true, enter: 'none', weight: 800, maxW: 2000 }); g.restore(); });
      const xA = X(xs[0]) - 200, xB = X(xs[n - 1]) + 200;
      c.draw([{ k: 'line', pts: [[Math.max(-50, xA), ay], [Math.min(c.W + 50, xB), ay]], role: 'dim', w: 0.6 }], { s: 1, plain: true, alpha: c.k(1, 10) });
      c.draw([{ k: 'line', pts: [[Math.max(-50, X(xs[0])), ay], [Math.min(c.W + 50, cx), ay]], role: 'accent', w: 1.1 }], { s: 1, plain: true });
      c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'hot' }], { x: cx, y: ay, s: 16 + Math.sin(c.f * 0.4) * 3, plain: true });
      ev.forEach((e, j) => {
        const x = X(xs[j]); if (x < -500 || x > c.W + 500) return;
        const up = j % 2 === 0, k = c.k(arrive[j] - 6, 9), here = j === (t > 0.5 ? i + 1 : i), sy = up ? ay - stem : ay + stem;
        c.draw([{ k: 'line', pts: [[x, ay], [x, c.lerp(ay, sy, c.EASE.out(k))]], role: here ? 'accent' : 'dim', w: 0.5 }], { s: 1, plain: true });
        c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: here ? 'hot' : 'ink' }], { x, y: ay, s: here ? 13 : 9, plain: true, alpha: c.clamp(k * 2) });
        if (e.icon) c.enter(k, [x - 56, sy - 56, 112, 112], () => c.icon(e.icon, { x, y: sy + (up ? -34 : 34) + (here ? bob(c, j, 4) : 0), s: here ? 58 : 48, role: e.role, p: e.p ?? 0.6, seed: 80 + j }));
        const rawTy = up ? sy - (e.icon ? 116 : 32) : sy + (e.icon ? 132 : 56);
        const ty = c.clamp(rawTy, availTop + 82, availBot - 76), lx = Math.min(c.A.xr(ty) - 200, Math.max(c.A.x0 + 200, x));
        const lblY = c.clamp(up ? ty - 68 : ty + 68, availTop + 26, availBot - 10);
        c.text(tl(e), here ? lx : x, ty, { size: here ? 68 : 52, font: 'mono', role: here ? 'accent' : 'dim', k, weight: 700, quiet: !here });
        c.K.label(c, e.label, here ? lx : x, lblY, k, { align: 'center', maxW: 420, size: here ? 44 : 36, role: here ? 'ink' : 'dim', quiet: !here });
      });
    },
  };
}

// điện tim tổng hợp: cộng phức bộ P-QRS-T quanh mỗi nhịp; QRS cố định (~0.09 s), khoảng QT co theo nhịp (√RR) như tim thật
const G = (x, w) => Math.exp(-0.5 * (x / w) * (x / w));
function beatTimes(c0, bpmAt, f0, f1) {               // tích phân nhịp theo frame → thời điểm đỉnh R (giây) — tất định, hàm của dữ liệu
  const out = []; let ph = 0.62;
  for (let f = f0; f < f1; f++) { const d = bpmAt(f) / 60 / c0.FPS; if (Math.floor(ph + d) > Math.floor(ph)) out.push((f + (Math.floor(ph + d) - ph) / d) / c0.FPS); ph += d; }
  return out;
}
function ecgAt(ts, beats) {
  let lo = 0, hi = beats.length - 1, y = 0;
  while (lo < hi) { const m = (lo + hi) >> 1; if (beats[m] < ts) lo = m + 1; else hi = m; }
  for (let j = Math.max(0, lo - 2); j <= Math.min(beats.length - 1, lo + 1); j++) {
    const b = beats[j], rr = Math.max(0.25, (beats[j + 1] ?? b + 0.8) - b), q = Math.sqrt(rr), d = ts - b;
    y += 0.13 * G(d + 0.17 * q, 0.028) - 0.12 * G(d + 0.028, 0.009) + G(d, 0.011) - 0.26 * G(d - 0.03, 0.011) + 0.3 * G(d - 0.27 * q, 0.05);
  }
  return y;
}
/** vết điện tim kiểu monitor: con trỏ quét trái → phải (sweep s), trước con trỏ là vết lượt trước, có khe xoá */
function ecgTrace(c, box, beats, sweep, role = 'hot') {
  const t = c.f / c.FPS, cur = ((t % sweep) + sweep) % sweep / sweep, n = 150, a = [], b = [], gap = 0.045;
  for (let i = 0; i <= n; i++) {
    const xf = i / n, back = xf <= cur ? cur - xf : cur - xf + 1;
    if (back < gap * 0.2 && xf > cur) continue;
    if (xf > cur && xf < cur + gap) continue;
    const p = [box.x + xf * box.w, box.y + box.h * 0.62 - ecgAt(t - back * sweep, beats) * box.h * 0.5];
    (xf <= cur ? a : b).push(p);
  }
  if (b.length > 1) c.draw([{ k: 'line', pts: b, role, w: 0.7 }], { s: 1, plain: true, alpha: 0.55 });
  if (a.length > 1) c.draw([{ k: 'line', pts: a, role, w: 0.9 }], { s: 1, seed: 5 });
  if (a.length) { const h = a[a.length - 1]; c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'ink' }], { x: h[0], y: h[1], s: 9, plain: true }); }
}
const lubdub = (dt) => (dt < 0 ? 0 : Math.exp(-dt * 16) + (dt > 0.2 ? 0.55 * Math.exp(-(dt - 0.2) * 20) : 0));   // tim co: "lub" + "dub"
const sinceBeat = (beats, t) => { let last = -1e9; for (const b of beats) { if (b > t) break; last = b; } return t - last; };

const SPLIT_ACTS = ['pulse', 'spin', 'run', 'fill', 'bounce', 'drip', 'count', 'grow'];
function split(c0, P) {                               // chia đôi màn hình (trên/dưới): hai hành động trên CÙNG một đồng hồ, nhịp = dữ liệu thật
  const S = [P.a || {}, P.b || {}], N = c0.N, FPS = c0.FPS, T = N / FPS, vmax = Math.max(1e-9, ...S.map((o) => Math.abs(num(o.value))));
  const act = (o) => (SPLIT_ACTS.includes(o.action) ? o.action : o.rate ? 'pulse' : 'grow');
  const B = S.map((o) => (num(o.rate) > 0 ? beatTimes(c0, () => num(o.rate), -2 * FPS, N + FPS) : []));
  const evName = { pulse: 'heartbeat', bounce: 'thud', drip: 'tick', count: 'tick' };
  const cues = [];
  S.forEach((o, i) => { const nm = evName[act(o)]; if (!nm) return; B[i].filter((b) => b >= 0 && b * FPS < N).slice(0, 12).forEach((b) => cues.push({ f: Math.round(b * FPS), name: nm, kick: i === 0 && act(o) === 'pulse' ? 0.12 : 0 })); });
  const vtxt = (o) => (o.value !== undefined ? `${c0.fmtNum(num(o.value), decOf(o, P))}${o.unit ? ' ' + o.unit : ''}` : o.rate ? `${c0.fmtNum(num(o.rate), decN(num(o.rate)))}${o.unit ? ' ' + o.unit : ''}` : '');
  return {
    cues, texts: names(P.title, ...S.map((o) => o.label), ...S.map(vtxt)),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10), true), top = yb + 24, mid = (top + c.A.bottom) / 2, t = c.f / FPS, g = c.g;
      const kd = c.EASE.out(c.k(1, 12));
      c.draw([{ k: 'line', pts: [[c.A.cx - 470 * kd, mid], [c.A.cx + 470 * kd, mid]], role: 'dim', w: 0.6 }], { s: 1, plain: true });
      const clk = `${c.fmtNum(Math.max(0, Math.min(T, t)), 1)} s`, cb = c.text(clk, 0, 0, { size: 34, font: 'mono', k: 0 });
      g.save(); g.fillStyle = c.pal.bg; g.fillRect(c.A.cx - (cb.x1 - cb.x0) / 2 - 22, mid - 26, cb.x1 - cb.x0 + 44, 52); g.restore();
      c.text(clk, c.A.cx, mid + 12, { size: 34, font: 'mono', role: 'accent', quiet: true, enter: 'none', weight: 700 });
      S.forEach((o, i) => {
        const y0 = i ? mid + 34 : top, y1 = i ? c.A.bottom - 14 : mid - 34, paneH = Math.max(180, y1 - y0);
        const cy = y0 + Math.min(paneH * 0.62, paneH - 76), ax = c.A.x0 + 170, a = act(o), k = c.k(2 + i * 4, 9);
        const role = o.role || (i ? 'cold' : 'hot'), ic = o.icon || (a === 'pulse' ? 'heart' : a === 'drip' ? 'drop' : a === 'run' ? 'runner' : 'dot');
        const icS = Math.min(92, paneH * 0.30);
        if (o.label) c.K.label(c, o.label, c.A.x0 + 10, y0 + 44, k, { align: 'left', maxW: 520, size: 42 });
        if (vtxt(o)) c.text(vtxt(o), c.A.xr(y0 + 44) - 10, y0 + 48, { size: 50, align: 'right', role: 'accent', k: c.k(6 + i * 4, 8), maxW: 420, weight: 800 });
        const dt = sinceBeat(B[i], t), env = lubdub(dt);
        if (a === 'pulse') {
          for (const b of B[i]) { const q = t - b; if (q < 0 || q > 0.6) continue; c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role, fill: false, w: 0.5 }], { x: ax, y: cy, s: icS + q * 220, plain: true, alpha: 0.5 * (1 - q / 0.6) }); }
          c.enter(k, [ax - icS, cy - icS, icS * 2, icS * 2], () => c.icon(ic, { x: ax, y: cy, s: icS * (1 + 0.2 * env), role, seed: 90 + i }));
          const eh = Math.min(165, paneH * 0.54);
          ecgTrace(c, { x: ax + 145, y: cy - eh / 2, w: c.A.xr(cy) - ax - 165, h: eh }, B[i], 2.2, role);
        } else if (a === 'spin') {
          c.enter(k, [ax - icS, cy - icS, icS * 2, icS * 2], () => c.icon(ic, { x: c.A.cx, y: cy, s: icS * 1.15, role, rot: 2 * Math.PI * num(o.rate) / 60 * t, seed: 90 + i }));
        } else if (a === 'bounce') {
          const ph = dt * num(o.rate) / 60, h = Math.sin(Math.PI * c.clamp(ph)) * Math.min(130, paneH * 0.4), sq = dt < 0.08 ? 0.18 * (1 - dt / 0.08) : 0;
          c.K.ground(c, c.A.cx, Math.min(y1 - 12, cy + icS * 0.9), 340);
          c.icon(ic, { x: c.A.cx, y: cy + 20 - h, s: icS * 0.78, sx: 1 + sq, sy: 1 - sq, role, seed: 90 + i });
        } else if (a === 'drip') {
          for (const b of B[i]) { const q = t - b; if (q < 0 || q > 1.2) continue; const fy = y0 + 84 + 0.5 * 2200 * q * q;
            if (fy < y1 - 30) c.icon(ic, { x: c.A.cx, y: fy, s: 30, role, seed: 90 + i, plain: true }); else c.icon('burst', { x: c.A.cx, y: y1 - 30, s: 36 + (q - Math.sqrt(Math.max(10, y1 - y0 - 114) / 1100)) * 260, role, plain: true, alpha: 0.6 }); }
          c.draw([{ k: 'line', pts: [[c.A.cx - 200, y1 - 22], [c.A.cx + 200, y1 - 22]], role: 'dim', w: 0.6 }], { s: 1, plain: true });
        } else if (a === 'count') {
          const n = B[i].filter((b) => b >= 0 && b <= t).length, pop = 1 + 0.15 * Math.exp(-dt * 12);
          g.save(); g.translate(c.A.cx, cy); g.scale(pop, pop); g.translate(-c.A.cx, -cy);
          c.text(c.fmtNum(n, 0), c.A.cx, cy + 48, { size: Math.min(156, paneH * 0.52), font: 'mono', quiet: true, enter: 'none', role, weight: 800 }); g.restore();
          c.icon(ic, { x: ax - 50, y: cy, s: 52 * (1 + 0.2 * env), role, seed: 90 + i });
        } else {                                       // run · fill · grow: quãng/mức/cỡ ∝ value (cùng thời gian → khác biệt là dữ liệu)
          const p = Math.abs(num(o.value)) / vmax * c.EASE.smooth(c.clamp((c.f - 4) / Math.max(1, N * 0.75 - 4)));
          if (a === 'run') {
            const x = c.lerp(c.A.x0 + 70, c.A.xr(cy) - 70, p);
            c.draw([{ k: 'line', pts: [[c.A.x0 + 20, Math.min(y1 - 14, cy + 74)], [c.A.xr(cy) - 20, Math.min(y1 - 14, cy + 74)]], role: 'dim', w: 0.5, dash: [1, 2] }], { s: 1, plain: true });
            c.icon(ic, { x, y: cy + 4 - Math.abs(Math.sin(p * 40)) * 12, s: icS * 0.85, role, seed: 90 + i });
          } else if (a === 'fill') {
            const bw = 540, bh = Math.min(104, paneH * 0.36), bx = c.A.cx - bw / 2 + 56;
            c.draw([{ k: 'rect', x: bx, y: cy - bh / 2, w: bw, h: bh, rad: 20, role: 'dim', fill: false }], { s: 1, plain: true });
            g.save(); g.fillStyle = c.col(role); g.fillRect(bx + 10, cy - bh / 2 + 10, Math.max(0, (bw - 20) * p), bh - 20); g.restore();
            c.icon(ic, { x: ax - 60, y: cy, s: 54, role, seed: 90 + i });
          } else c.icon(ic, { x: c.A.cx, y: cy, s: 26 + Math.min(110, paneH * 0.36) * Math.sqrt(p), role, seed: 90 + i });
        }
      });
    },
  };
}

const METER_KINDS = ['ecg', 'battery', 'tank', 'thermo', 'dial'];
function meter(c0, P) {                               // đồng hồ vật lý: chuyển động CHÍNH LÀ dữ liệu (điện tim đúng bpm, pin %, mực bể, thuỷ ngân, kim)
  const kind = METER_KINDS.includes(P.kind) ? P.kind : 'dial', N = c0.N, f0 = 6, f1 = Math.max(f0 + 12, Math.round((P.land ?? 0.62) * N));
  const to = num(P.value ?? P.bpm ?? P.to), from = P.from !== undefined ? num(P.from) : (kind === 'ecg' ? to : (P.min !== undefined ? num(P.min) : 0));
  const dec = P.decimals ?? decN(to), unit = P.unit ?? (kind === 'ecg' ? 'BPM' : kind === 'battery' ? '%' : '');
  const [lo, hi] = kind === 'battery' ? [num(P.min, 0), num(P.max, 100)] : dialRange([from, to], P);
  const vAt = (f) => c0.lerp(from, to, c0.EASE.out(c0.clamp((f - f0) / (f1 - f0))));
  const B = kind === 'ecg' ? beatTimes(c0, (f) => Math.max(20, vAt(f)), -3 * c0.FPS, N + c0.FPS) : [];
  const final = `${P.prefix || ''}${c0.fmtNum(to, dec)}${P.suffix || ''}`;
  const cues = kind === 'ecg' ? B.filter((b) => b >= 0 && b * c0.FPS < N).slice(0, 16).map((b) => ({ f: Math.round(b * c0.FPS), name: P.sfx || 'heartbeat', kick: 0.1 }))
    : [{ f: f0, name: kind === 'tank' ? 'bubbles' : 'riser' }, { f: f1, name: P.danger !== undefined && to >= num(P.danger) ? 'warn' : 'ding', kick: 0.5 }];
  return {
    cues, texts: names(P.title, final, unit, P.label),
    draw(c) {
      const yb = drawHeader(c, P, c.k(1, 10), true), cx = c.A.cx, landed = kind === 'ecg' ? from === to || c.f >= f1 : c.f >= f1, g = c.g, v = vAt(c.f);
      const fr = c.clamp((v - lo) / Math.max(1e-9, hi - lo)), hotNow = P.danger !== undefined && v >= num(P.danger);
      const readout = (x, y, size = 136, al = 'center') => {
        const nb = c.text(landed ? final : `${P.prefix || ''}${c.fmtNum(v, dec)}${P.suffix || ''}`, x, y, { size, quiet: !landed, enter: 'none', maxW: 700, weight: 900, align: al, role: hotNow ? 'hot' : 'ink' });
        if (unit) c.text(unit, x, Math.min(c.A.bottom - 26, nb.y1 + Math.max(46, size * 0.42)), { size: Math.max(38, size * 0.34), role: 'accent', k: c.k(4, 8), align: al, maxW: 600 });
        return nb;
      };
      if (kind === 'ecg') {
        const by = Math.max(yb + 44, c.A.stageTop + 16), eh = Math.min(280, Math.max(170, c.A.bottom - by - (P.label ? 300 : 210)));
        const box = { x: c.A.x0 + 10, y: by, w: c.A.x1 - c.A.x0 - 20, h: eh }, t = c.f / c.FPS;
        g.save(); g.strokeStyle = c.col('dim'); g.globalAlpha = 0.22; g.lineWidth = 1.5; g.beginPath();
        for (let x = box.x; x <= box.x + box.w; x += 40) { g.moveTo(x, box.y); g.lineTo(x, box.y + box.h); }
        for (let y = box.y; y <= box.y + box.h; y += 40) { g.moveTo(box.x, y); g.lineTo(box.x + box.w, y); }
        g.stroke(); g.restore();
        c.draw([{ k: 'rect', x: box.x - 10, y: box.y - 10, w: box.w + 20, h: box.h + 20, rad: 20, role: 'dim', fill: false }], { s: 1, plain: true, k: c.k(1, 10) });
        ecgTrace(c, box, B, num(P.sweep, 2.6), P.role || 'hot');
        const env = lubdub(sinceBeat(B, t)), hy = Math.min(c.A.bottom - (P.label ? 150 : 90), box.y + box.h + 114);
        c.icon(P.icon || 'heart', { x: cx - 220, y: hy, s: 94 * (1 + 0.22 * env), role: P.icon_role || 'hot' });
        readout(cx + 115, hy + 24, 132);
        if (P.label) c.K.tag(c, P.label, cx, tagY(c, c.A.bottom - 36), c.k(f1 + 4, 9));
        return;
      }
      if (kind === 'dial') {
        const botNeed = P.label ? 124 : 36, availH = Math.max(280, c.A.bottom - botNeed - yb - 24);
        const R = Math.min(265, availH * 0.42), cy = yb + 24 + R + 12;
        const live = landed ? (c.noise(c.f, 3) * 0.6 + Math.sin(c.f * 0.9) * 0.4) * (hi - lo) * 0.006 : 0;
        drawDial(c, { x: cx, y: cy, R, lo, hi, v: c.lerp(from, to, c.EASE.back(c.clamp((c.f - f0) / (f1 - f0)), 1.4)) + live, k: c.k(1, 10), danger: P.danger !== undefined ? num(P.danger) : undefined, dec });
        readout(cx, Math.min(c.A.bottom - (P.label ? 150 : 72), cy + Math.min(210, R * 0.78)), Math.min(118, R * 0.44));
        if (P.label) c.K.tag(c, P.label, cx, tagY(c, c.A.bottom - 36), c.k(f1 + 4, 9));
        return;
      }
      const top = Math.max(yb + 52, c.A.stageTop + 20), bot = c.A.bottom - (P.label ? 132 : 52), hgt = Math.max(200, bot - top);
      if (kind === 'battery') {
        const w = 300, x = cx - 220, low = fr < 0.2, segs = 5, charging = to > from && !landed;
        c.draw([{ k: 'rect', x: x - w / 2, y: top + 40, w, h: hgt - 40, rad: 34, role: 'ink', fill: false, sw: 1.2 }, { k: 'rect', x: x - 55, y: top, w: 110, h: 44, rad: 12, role: 'ink' }], { s: 1, plain: true, k: c.k(1, 10) });
        const ih = hgt - 80, sh = ih / segs;
        for (let i = 0; i < segs; i++) {
          const fill = c.clamp(fr * segs - i); if (fill <= 0) continue;
          const yb2 = top + 60 + ih - i * sh, hh = (sh - 14) * fill;
          g.save(); g.fillStyle = c.col(P.role || (low ? 'hot' : 'accent')); g.globalAlpha *= low ? 0.55 + 0.45 * Math.abs(Math.sin(c.f * 0.25)) : 1; g.fillRect(x - w / 2 + 22, yb2 - hh, w - 44, hh); g.restore();
        }
        if (charging) c.icon('bolt', { x, y: top + 40 + hgt / 2, s: 90 * (1 + 0.1 * Math.sin(c.f * 0.5)), role: 'ink', plain: true });
        readout(cx + 190, top + hgt / 2, 150);
      } else if (kind === 'tank') {
        const w = 460, x = cx - w / 2 - 70, lvl = top + hgt - hgt * fr;
        g.save(); g.beginPath(); g.rect(x, top, w, hgt); g.clip();
        const pts = [[x, top + hgt]];
        for (let i = 0; i <= 24; i++) pts.push([x + w * i / 24, lvl + Math.sin(c.f * 0.18 + i * 0.7) * 9 * (landed ? 0.5 : 1)]);
        pts.push([x + w, top + hgt]);
        c.draw([{ k: 'poly', pts, role: P.role || 'cold' }], { s: 1, plain: true });
        for (let i = 0; i < 12; i++) { const ph = ((c.f * (0.6 + c.hash(i, 2) * 0.8) + c.hash(i, 3) * 400) % 400) / 400, by = top + hgt - ph * (top + hgt - lvl);
          if (by > lvl + 12) c.draw([{ k: 'circle', x: 0, y: 0, r: 1, role: 'ink', fill: false }], { x: x + 40 + c.hash(i, 1) * (w - 80), y: by, s: 6 + c.hash(i, 4) * 8, plain: true, alpha: 0.5 }); }
        g.restore();
        c.draw([{ k: 'rect', x, y: top, w, h: hgt, rad: 28, role: 'ink', fill: false, sw: 1.1 }], { s: 1, plain: true, k: c.k(1, 10) });
        for (let i = 0; i <= 4; i++) { const yy = top + hgt * (1 - i / 4); c.draw([{ k: 'line', pts: [[x - 4, yy], [x + 26, yy]], role: 'dim', w: 0.5 }], { s: 1, plain: true });
          c.text(c.fmtNum(lo + (hi - lo) * i / 4, decN(nice((hi - lo) / 4))), x - 18, yy + 12, { size: 32, font: 'mono', role: 'dim', align: 'right', quiet: true, enter: 'none' }); }
        readout(x + w + 36, top + hgt * 0.45, 120, 'left');
      } else {                                         // thermo: cột thuỷ ngân + bầu, vạch chia từ min..max
        const x = cx - 180, tw = 64, bulbR = 78, tTop = top + 20, tBot = bot - bulbR, mh = (tBot - tTop) * fr;
        c.draw([{ k: 'rect', x: x - tw / 2, y: tTop - 20, w: tw, h: tBot - tTop + 40, rad: tw / 2, role: 'ink', fill: false, sw: 1.1 }, { k: 'circle', x, y: bot, r: bulbR, role: 'ink', fill: false, w: 1.1 }], { s: 1, plain: true, k: c.k(1, 10) });
        g.save(); g.fillStyle = c.col(P.role || (hotNow ? 'hot' : 'hot')); g.fillRect(x - tw / 2 + 14, tBot - mh, tw - 28, mh + 30); g.beginPath(); g.arc(x, bot, bulbR - 16, 0, c.TAU); g.fill(); g.restore();
        const step = nice((hi - lo) / 6);
        for (let tv = Math.ceil(lo / step) * step, i = 0; tv <= hi + 1e-9 && i < 10; tv += step, i++) { const yy = tBot - (tBot - tTop) * (tv - lo) / Math.max(1e-9, hi - lo);
          c.draw([{ k: 'line', pts: [[x - tw / 2 - 40, yy], [x - tw / 2 - 10, yy]], role: P.danger !== undefined && tv >= num(P.danger) ? 'hot' : 'dim', w: 0.5 }], { s: 1, plain: true });
          c.text(c.fmtNum(tv, decN(step)), x - tw / 2 - 56, yy + 12, { size: 32, font: 'mono', role: 'dim', align: 'right', quiet: true, enter: 'none' }); }
        readout(cx + 170, top + hgt * 0.45, 140);
      }
      if (P.icon && kind !== 'battery') c.icon(P.icon, { x: cx + 170, y: top + 40 + bob(c, 3, 5), s: 60, role: P.icon_role });
      if (P.label) c.K.tag(c, P.label, cx, tagY(c, c.A.bottom - 36), c.k(f1 + 4, 9));
    },
  };
}

// ================= VÒNG 13 — 3 beat điện ảnh cao cấp (dossier · xray_cutaway · hero_stat) =================
function wrapLinesPx(c, str, size, maxW, o = {}) {
  const g = c.g, T = c.L.type;
  const s = (o.upper ?? (o.font === 'mono' ? T.monoUpper : T.upper)) ? String(str).toUpperCase() : String(str);
  g.save();
  g.font = `${o.weight || T.weight || 700} ${Math.round(size)}px "${o.font === 'mono' ? 'StyleMono' : 'StyleFont'}", sans-serif`;
  if ('letterSpacing' in g) g.letterSpacing = `${(o.track ?? (o.font === 'mono' ? 0.04 : T.track || 0)) * size}px`;
  const mw = (txt) => {
    const m = g.measureText ? g.measureText(txt) : null;
    return (m && typeof m.width === 'number') ? m.width : String(txt).length * size * 0.56;
  };
  const out = [];
  for (const para of s.split('\n')) {
    let line = '';
    for (const w of para.split(/\s+/).filter(Boolean)) {
      const t = line ? `${line} ${w}` : w;
      if (line && maxW && mw(t) > maxW) { out.push(line); line = w; } else line = t;
    }
    out.push(line);
  }
  const widths = out.map(mw);
  const meas = (txt) => mw(txt);
  g.restore();
  return { lines: out, widths, meas, s };
}

function dossier(c0, P) {                              // thẻ hồ sơ lưu trữ (LEMMiNO · Johnny Harris · Fern)
  const N = c0.N, headline = String(P.headline || P.title || ''), ev = (P.evidence || []).slice(0, 4);
  const tag = String(P.tag || P.kicker || 'CASE FILE'), stamp = P.stamp ? String(P.stamp) : '';
  const hiRaw = P.highlight ? String(P.highlight).trim() : '';
  const hiInHead = hiRaw && headline.toLowerCase().includes(hiRaw.toLowerCase());
  const fHi = Math.max(8, Math.round((P.hit ?? 0.28) * N));
  const fStamp = Math.max(fHi + 8, Math.round(N * 0.56));
  const seed = c0.strSeed(`${tag}|${headline}|${stamp}`) >>> 0;
  const cues = [{ f: 2, name: 'whoosh_soft' }, ...ev.map((_, i) => ({ f: 12 + i * 7, name: 'tick' })),
                ...(stamp ? [{ f: fStamp, name: 'stamp', kick: 0.55 }] : [])];
  const texts = names(P.kicker !== tag ? P.kicker : '', P.title !== headline ? P.title : '', tag, headline,
                      !hiInHead ? hiRaw : '', ...ev.flatMap((r) => [r.k, r.v]), stamp, P.cite);
  return {
    cues, texts,
    draw(c) {
      const g = c.g;
      const showTopHdr = (P.title && P.title !== headline) || (P.kicker && P.kicker !== tag);
      const yb = showTopHdr ? drawHeader(c, { kicker: P.kicker !== tag ? P.kicker : '', title: P.title !== headline ? P.title : '' }, c.k(1, 10), true) : c.A.top;
      const kCard = c.EASE.out(c.k(1, 10)), slideY = (1 - kCard) * 26;
      const cardX = c.A.x0 + 6, cardW = c.A.x1 - c.A.x0 - 12;
      const cardY = Math.max(c.A.top + 8, yb + (showTopHdr ? 18 : 10)) + slideY;
      const cardBot = c.A.bottom - 16, cardH = Math.max(380, cardBot - (cardY - slideY));
      const padX = 34, hdrH = 54, footH = (P.cite || stamp) ? 78 : 22;

      // nền thẻ hồ sơ tối phân cấp + thanh đầu mục + viền 1.5px + dấu chữ thập 4 góc
      g.save();
      g.globalAlpha *= c.clamp(kCard * 1.4);
      const cardFill = c.mix(c.pal.bg, '#141820', 0.92), hdrFill = c.mix(c.pal.bg, '#1D2330', 0.92);
      g.fillStyle = cardFill;
      g.beginPath(); g.roundRect(cardX, cardY, cardW, cardH, 12); g.fill();
      g.fillStyle = hdrFill;
      g.beginPath(); g.roundRect(cardX, cardY, cardW, hdrH, [12, 12, 0, 0]); g.fill();
      g.strokeStyle = c.col('dim'); g.globalAlpha *= 0.58; g.lineWidth = 1.5;
      g.beginPath(); g.roundRect(cardX, cardY, cardW, cardH, 12); g.stroke();
      g.beginPath(); g.moveTo(cardX, cardY + hdrH); g.lineTo(cardX + cardW, cardY + hdrH); g.stroke();
      g.restore();

      // vạch nhấn trên cùng chạy từ trái sang phải + 4 chữ thập kỹ thuật ở 4 góc thẻ
      g.save();
      g.fillStyle = c.col(P.role || 'accent'); g.globalAlpha *= 0.92;
      g.fillRect(cardX + 12, cardY, (cardW - 24) * kCard, 3);
      g.strokeStyle = c.col(P.role || 'accent'); g.lineWidth = 1.5; g.globalAlpha = 0.65 * kCard;
      const arm = 12;
      g.beginPath();
      for (const [cx, cy] of [[cardX, cardY], [cardX + cardW, cardY], [cardX, cardY + cardH], [cardX + cardW, cardY + cardH]]) {
        g.moveTo(cx - arm, cy); g.lineTo(cx + arm, cy);
        g.moveTo(cx, cy - arm); g.lineTo(cx, cy + arm);
      }
      g.stroke();
      g.restore();

      // dòng tiêu đề mono góc trên trái (tag) + mã hồ sơ mờ góc trên phải
      c.text(tag, cardX + padX, cardY + 35, { size: 24, font: 'mono', role: P.role || 'accent', align: 'left', k: c.k(2, 8), enter: 'type', weight: 700, maxW: cardW * 0.62 });
      const pulse = 0.55 + 0.45 * Math.sin(c.f * 0.22);
      g.save(); g.fillStyle = c.col(P.role || 'accent'); g.globalAlpha = pulse * kCard;
      g.beginPath(); g.arc(cardX + cardW - padX - 102, cardY + 27, 4.5, 0, c.TAU); g.fill(); g.restore();
      c.text(`REF-${String((seed % 899) + 100)}`, cardX + cardW - padX, cardY + 34, { size: 20, font: 'mono', role: 'dim', align: 'right', quiet: true, enter: 'none', weight: 600, k: kCard });

      // khối tiêu đề chính + tùy chọn visual_icon ở góc phải
      const hasIcon = !!P.visual_icon, iconBox = 132;
      const headX = cardX + padX, headTop = cardY + hdrH + 26;
      const headMaxW = cardW - padX * 2 - (hasIcon ? iconBox + 24 : 0);
      const maxHeadH = Math.min(185, Math.max(96, (cardH - hdrH - footH) * 0.34));
      const hf = fitText(c, headline, headX, [54, 46, 40, 34], { align: 'left', maxW: headMaxW, lh: 1.12, maxH: maxHeadH, weight: 800 });
      const headY = headTop - hf.b.y0;

      if (hasIcon) {
        const ix = cardX + cardW - padX - iconBox, iy = headTop;
        g.save(); g.fillStyle = c.mix(c.pal.bg, '#0B0E14', 0.9);
        g.strokeStyle = c.col('dim'); g.lineWidth = 1.2; g.globalAlpha = 0.85 * kCard;
        g.beginPath(); g.roundRect(ix, iy, iconBox, iconBox, 10); g.fill();
        g.globalAlpha = 0.42 * kCard; g.stroke(); g.restore();
        c.enter(c.k(6, 10), [ix, iy, iconBox, iconBox], () => c.icon(P.visual_icon, { x: ix + iconBox / 2, y: iy + iconBox / 2 + bob(c, 2, 3), s: 46, role: P.icon_role || P.role || 'accent', p: 0.65 }), 'pop');
      }

      // vệt bút dạ quang quét ngang từ khóa highlight đồng bộ nhịp u / fHi
      const kHi = c.EASE.snap(c.k(fHi, 14, false));
      if (hiRaw && hiInHead && kHi > 0) {
        const wInfo = wrapLinesPx(c, headline, hf.b.size || hf.size, headMaxW, { weight: 800 });
        const sz = hf.b.size || hf.size, lh = sz * 1.12, target = (c.L.type.upper ? hiRaw.toUpperCase() : hiRaw);
        let drewHi = false;
        wInfo.lines.forEach((ln, li) => {
          const idx = ln.toLowerCase().indexOf(target.toLowerCase());
          if (idx < 0) return;
          drewHi = true;
          const preW = wInfo.meas(ln.slice(0, idx)), segW = wInfo.meas(ln.slice(idx, idx + target.length));
          const ly = headY + li * lh;
          g.save(); g.fillStyle = c.col(P.role || 'accent'); g.globalAlpha = 0.34;
          g.beginPath(); g.roundRect(headX + preW - 6, ly - sz * 0.84, (segW + 12) * kHi, sz * 1.06, 5); g.fill();
          g.globalAlpha = 0.85; g.fillRect(headX + preW - 4, ly + sz * 0.16, (segW + 8) * kHi, 3);
          g.restore();
        });
        if (!drewHi) {
          const words = target.split(/\s+/).filter((w) => w.length >= 2);
          wInfo.lines.forEach((ln, li) => {
            for (const w of words) {
              const idx = ln.toLowerCase().indexOf(w.toLowerCase());
              if (idx < 0) continue;
              const preW = wInfo.meas(ln.slice(0, idx)), segW = wInfo.meas(ln.slice(idx, idx + w.length));
              const ly = headY + li * lh;
              g.save(); g.fillStyle = c.col(P.role || 'accent'); g.globalAlpha = 0.32;
              g.beginPath(); g.roundRect(headX + preW - 5, ly - sz * 0.84, (segW + 10) * kHi, sz * 1.04, 5); g.fill();
              g.restore();
            }
          });
        }
      }
      const hb = c.text(headline, headX, headY, { size: hf.b.size || hf.size, align: 'left', maxW: headMaxW, lh: 1.12, weight: 800, k: c.k(4, 10) });
      let curY = Math.max(hb.y1, hasIcon ? headTop + iconBox : hb.y1) + 22;

      // nếu highlight là cụm riêng không nằm trong headline → vẽ 1 dải bút dạ quang ngay dưới headline
      if (hiRaw && !hiInHead) {
        const hiBox = c.text(hiRaw, headX + 14, curY + 34, { size: 30, align: 'left', maxW: cardW - padX * 2 - 28, weight: 800, k: 0 });
        if (kHi > 0) {
          g.save(); g.fillStyle = c.col(P.role || 'accent'); g.globalAlpha = 0.92;
          g.beginPath(); g.roundRect(headX, hiBox.y0 - 8, (hiBox.x1 - hiBox.x0 + 28) * kHi, hiBox.y1 - hiBox.y0 + 16, 6); g.fill();
          g.restore();
        }
        const h2 = c.text(hiRaw, headX + 14, curY + 34, { size: 30, align: 'left', maxW: cardW - padX * 2 - 28, weight: 800, role: 'bg', k: c.k(fHi + 3, 8), enter: 'wipe', bare: true });
        curY = h2.y1 + 22;
      }

      // các dòng bằng chứng (key-value) chia lưới sắc nét bằng hairline dividers
      const footTop = cardY + cardH - footH;
      if (ev.length) {
        const evAvail = Math.max(72, footTop - curY - 12);
        const rowH = Math.min(84, Math.floor(evAvail / ev.length));
        const kSz = Math.min(23, Math.max(18, Math.floor(rowH * 0.32)));
        const vSz = Math.min(32, Math.max(22, Math.floor(rowH * 0.44)));
        const kMaxW = (cardW - padX * 2) * 0.36, vMaxW = (cardW - padX * 2) * 0.56;
        ev.forEach((row, i) => {
          const ry = curY + i * rowH, kr = c.EASE.out(c.k(10 + i * 7, 9));
          g.save(); g.strokeStyle = c.col('dim'); g.globalAlpha = 0.34 * kr; g.lineWidth = 1;
          g.beginPath(); g.moveTo(cardX + padX, ry); g.lineTo(cardX + padX + (cardW - padX * 2) * kr, ry); g.stroke(); g.restore();
          const ty = ry + rowH * 0.62;
          const kf = fitText(c, String(row.k || ''), cardX + padX, [kSz, Math.max(16, kSz - 4)], { align: 'left', font: 'mono', maxW: kMaxW, maxH: rowH - 12, weight: 700 });
          const vf = fitText(c, String(row.v || ''), cardX + cardW - padX, [vSz, Math.max(18, vSz - 5), 18], { align: 'right', maxW: vMaxW, maxH: rowH - 12, weight: 700 });
          c.text(String(row.k || ''), cardX + padX, Math.min(ry + rowH - 12, ty), { size: kf.b.size || kf.size, font: 'mono', role: 'dim', align: 'left', maxW: kMaxW, k: kr, weight: 700 });
          c.text(String(row.v || ''), cardX + cardW - padX, Math.min(ry + rowH - 12, ty), { size: vf.b.size || vf.size, role: i === ev.length - 1 ? (P.role || 'accent') : 'ink', align: 'right', maxW: vMaxW, k: c.k(13 + i * 7, 9), weight: 700 });
        });
      }

      // chân thẻ: cite góc trái dưới + con dấu stamp góc phải dưới (tách ngang 100%, không bao giờ chồng)
      if (P.cite) {
        const citeW = stamp ? (cardW - padX * 2) * 0.54 : (cardW - padX * 2);
        c.text(String(P.cite), cardX + padX, cardY + cardH - 28, { size: 22, font: 'mono', role: 'dim', align: 'left', maxW: citeW, k: c.k(18, 9), weight: 600 });
      }
      if (stamp) {
        const ks = c.k(fStamp, 6, false);
        if (ks > 0) {
          const isNeg = /busted|false|myth|debunk|warning|fail|danger/i.test(stamp);
          const sRole = isNeg ? 'hot' : (P.role || 'accent'), stTxt = stamp.toUpperCase();
          const stMaxW = (cardW - padX * 2) * 0.36;
          const sf = fitText(c, stTxt, 0, [30, 25, 21], { font: 'mono', weight: 900, maxW: stMaxW, maxH: 46 });
          const sw = (sf.b.x1 - sf.b.x0) + 34, sh = (sf.b.y1 - sf.b.y0) + 18;
          const sx = cardX + cardW - padX - sw / 2, sy = cardY + cardH - 36;
          const sc = c.lerp(2.05, 1, c.EASE.out(ks));
          g.save();
          g.translate(sx, sy); g.rotate(-0.07); g.scale(sc, sc); g.globalAlpha *= c.clamp(ks * 2.2);
          g.fillStyle = c.mix(c.pal.bg, c.col(sRole), 0.14);
          g.strokeStyle = c.col(sRole); g.lineWidth = 3.2;
          g.beginPath(); g.roundRect(-sw / 2, -sh / 2, sw, sh, 6); g.fill(); g.stroke();
          g.lineWidth = 1; g.globalAlpha *= 0.65;
          g.beginPath(); g.roundRect(-sw / 2 + 4, -sh / 2 + 4, sw - 8, sh - 8, 3); g.stroke();
          g.restore();
          g.save();
          g.translate(sx, sy); g.rotate(-0.07); g.scale(sc, sc); g.globalAlpha *= c.clamp(ks * 2.2);
          c.text(stTxt, 0, -(sf.b.y0 + sf.b.y1) / 2, { size: sf.b.size || sf.size, font: 'mono', role: sRole, weight: 900, enter: 'none', quiet: ks < 1, maxW: stMaxW });
          g.restore();
        }
      }
    },
  };
}

function xray_cutaway(c0, P) {                         // mặt cắt X-ray 2 lớp + dòng hạt Bézier (Zack D. Films · Fern)
  const N = c0.N, bpm = P.pulse_rate !== undefined ? c0.clamp(num(P.pulse_rate, 72), 20, 240) : 0;
  const rawFlows = Array.isArray(P.flow) ? P.flow : [
    { from: [-0.82, -0.35], via: [-0.32, -0.52], to: [-0.04, -0.02], count: 8, role: 'cold', speed: 0.6 },
    { from: [0.04, 0.02], via: [0.38, 0.28], to: [0.82, 0.48], count: 8, role: 'hot', speed: 0.72 },
  ];
  const cues = [{ f: 2, name: 'whoosh_soft' }, { f: 8, name: 'pop' }];
  if (bpm > 0) {
    const bs = beatTimes(c0, () => bpm, 0, N);
    bs.slice(0, 10).forEach((b) => cues.push({ f: Math.round(b * c0.FPS), name: 'heartbeat', kick: 0.08 }));
  }
  return {
    cues, texts: names(P.kicker, P.title, P.callout_num, P.callout_label),
    draw(c) {
      const g = c.g, yb = hasHdr(P) ? drawHeader(c, P, c.k(1, 10), true) : c.A.top;
      const hasTel = !!(P.callout_num || P.callout_label), telH = hasTel ? 104 : 0;
      const stageTop = yb + 18, stageBot = c.A.bottom - (hasTel ? telH + 26 : 20);
      const stageW = c.A.x1 - c.A.x0, stageH = Math.max(260, stageBot - stageTop);
      const cx = c.A.cx, cy = stageTop + stageH * 0.5, R = Math.min(stageW * 0.44, stageH * 0.45);
      const kIn = c.EASE.out(c.k(1, 12));

      // trường X-ray blueprint + vòng quét đồng tâm + trục chữ thập + tia scan dọc
      g.save();
      const bgGlow = g.createRadialGradient ? g.createRadialGradient(cx, cy, R * 0.08, cx, cy, R * 1.25) : null;
      if (bgGlow) {
        bgGlow.addColorStop(0, c.mix(c.pal.bg, c.col('cold'), 0.22));
        bgGlow.addColorStop(0.6, c.mix(c.pal.bg, c.col('cold'), 0.07));
        bgGlow.addColorStop(1, 'rgba(0,0,0,0)');
        g.globalAlpha = 0.85 * kIn; g.fillStyle = bgGlow;
        g.beginPath(); g.arc(cx, cy, R * 1.25, 0, c.TAU); g.fill();
      }

      g.strokeStyle = c.col('cold'); g.lineWidth = 1.4;
      [0.56, 0.86, 1.06].forEach((fr, ri) => {
        g.save(); g.translate(cx, cy); g.rotate(c.f * (ri % 2 ? -0.005 : 0.004) + ri);
        g.globalAlpha = (ri === 0 ? 0.34 : 0.18) * kIn;
        if (ri === 1) g.setLineDash([8, 10]);
        g.beginPath(); g.arc(0, 0, R * fr, 0, c.TAU); g.stroke();
        g.restore();
      });
      g.globalAlpha = 0.14 * kIn; g.setLineDash([]);
      g.beginPath();
      g.moveTo(cx - R * 1.12, cy); g.lineTo(cx + R * 1.12, cy);
      g.moveTo(cx, cy - R * 1.12); g.lineTo(cx, cy + R * 1.12);
      g.stroke();

      // tia quét X-ray chạy mượt trong vùng cutaway
      const scanY = stageTop + ((c.u * 1.55) % 1) * stageH;
      const sg = g.createLinearGradient ? g.createLinearGradient(0, scanY - 46, 0, scanY + 4) : null;
      if (sg) {
        sg.addColorStop(0, 'rgba(0,0,0,0)'); sg.addColorStop(1, c.col('cold'));
        g.globalAlpha = 0.12 * kIn; g.fillStyle = sg; g.fillRect(c.A.x0 + 16, scanY - 46, stageW - 32, 46);
      }
      g.globalAlpha = 0.36 * kIn; g.fillStyle = c.col('cold'); g.fillRect(c.A.x0 + 16, scanY, stageW - 32, 1.5);
      g.restore();

      // lớp vỏ ngoài X-ray (shell_icon mờ + khung ống kính cutaway)
      if (P.shell_icon) {
        c.enter(c.k(2, 10), [cx - R, cy - R, R * 2, R * 2], () => {
          c.icon(P.shell_icon, { x: cx, y: cy + bob(c, 1, 4), s: R * 0.94, role: P.shell_role || 'cold', alpha: 0.24, plain: true });
        }, 'pop');
        g.save(); g.strokeStyle = c.col('cold'); g.globalAlpha = 0.42 * kIn; g.lineWidth = 2; g.setLineDash([12, 8]);
        g.beginPath(); g.arc(cx, cy, R * 0.56, 0, c.TAU); g.stroke(); g.restore();
      }

      // nhịp đập của lõi (pulse_rate BPM hoặc nhịp thở mềm tất định)
      const env = bpm > 0 ? lubdub((((c.t % (60 / bpm)) + (60 / bpm)) % (60 / bpm))) : (0.5 + 0.5 * Math.sin(c.f * 0.15)) * 0.65;
      const coreRole = P.role || 'hot', coreS = R * (P.shell_icon ? 0.44 : 0.54);

      // quầng phát sáng lõi + sóng nhịp lan tỏa
      g.save();
      const cg = g.createRadialGradient ? g.createRadialGradient(cx, cy, coreS * 0.15, cx, cy, coreS * (1.45 + 0.35 * env)) : null;
      if (cg) {
        cg.addColorStop(0, c.col(coreRole)); cg.addColorStop(0.5, c.mix(c.pal.bg, c.col(coreRole), 0.35)); cg.addColorStop(1, 'rgba(0,0,0,0)');
        g.globalAlpha = (0.32 + 0.2 * env) * kIn; g.fillStyle = cg;
        g.beginPath(); g.arc(cx, cy, coreS * (1.45 + 0.35 * env), 0, c.TAU); g.fill();
      }
      if (env > 0.15) {
        g.strokeStyle = c.col(coreRole); g.lineWidth = 2.2; g.globalAlpha = 0.42 * (1 - env * 0.5) * kIn;
        g.beginPath(); g.arc(cx, cy, coreS * (1.05 + (1 - env) * 0.48), 0, c.TAU); g.stroke();
      }
      g.restore();

      // lõi chính (core_icon)
      c.enter(c.k(4, 10), [cx - coreS, cy - coreS, coreS * 2, coreS * 2], () => {
        c.icon(P.core_icon || 'heart', { x: cx, y: cy, s: coreS * (1 + 0.11 * env), role: coreRole, p: 0.6 + 0.25 * env });
      }, 'pop');

      // dòng chảy hạt tất định theo đường cong Bézier bậc 2 (flow_particles)
      const mapPt = (pt) => {
        const px = num(pt && pt[0]), py = num(pt && pt[1]);
        if (Math.abs(px) <= 1.25 && Math.abs(py) <= 1.25) {
          if (px < 0 || py < 0) return [cx + px * R, cy + py * R];
          return [c.A.x0 + px * stageW, stageTop + py * stageH];
        }
        return [c.clamp(px, c.A.x0, c.A.x1), c.clamp(py, stageTop, stageBot)];
      };
      const quadAt = (p0, p1, p2, t) => {
        const mt = 1 - t;
        return [mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0], mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]];
      };
      rawFlows.forEach((fl, fi) => {
        if (!fl || !fl.from || !fl.to) return;
        const p0 = mapPt(fl.from), p2 = mapPt(fl.to);
        let p1;
        if (fl.via) p1 = mapPt(fl.via);
        else {
          const mx = (p0[0] + p2[0]) * 0.5, my = (p0[1] + p2[1]) * 0.5;
          const dx = p2[0] - p0[0], dy = p2[1] - p0[1], sgn = fi % 2 ? -1 : 1;
          p1 = [mx - dy * 0.2 * sgn, my + dx * 0.2 * sgn];
        }
        const fRole = fl.role || fl.color_role || 'accent', fCol = c.col(fRole);
        const count = Math.max(2, Math.min(24, Math.round(num(fl.count, 8))));
        const speed = Math.max(0.1, num(fl.speed, 0.6));
        const kf = c.EASE.out(c.k(6 + fi * 4, 10));

        // ống dẫn Bézier nét đứt mờ
        g.save(); g.strokeStyle = fCol; g.lineWidth = 2.2; g.globalAlpha = 0.26 * kf; g.setLineDash([6, 8]);
        g.beginPath(); g.moveTo(p0[0], p0[1]); g.quadraticCurveTo(p1[0], p1[1], p2[0], p2[1]); g.stroke();
        g.restore();

        // các hạt năng lượng/máu/xung chạy mượt kèm vệt sáng đuôi
        g.save();
        for (let i = 0; i < count; i++) {
          const s = ((c.t * speed + i / count + fi * 0.17) % 1 + 1) % 1;
          const edgeFade = Math.min(1, s * 6) * Math.min(1, (1 - s) * 6) * kf;
          if (edgeFade <= 0.02) continue;
          for (let tr = 4; tr >= 1; tr--) {
            const ts = s - tr * 0.024; if (ts <= 0) continue;
            const [tx, ty] = quadAt(p0, p1, p2, ts);
            g.fillStyle = fCol; g.globalAlpha = edgeFade * (0.36 - tr * 0.07);
            g.beginPath(); g.arc(tx, ty, 6.2 - tr * 0.9, 0, c.TAU); g.fill();
          }
          const [hx, hy] = quadAt(p0, p1, p2, s);
          g.fillStyle = fCol; g.globalAlpha = edgeFade * 0.26;
          g.beginPath(); g.arc(hx, hy, 15, 0, c.TAU); g.fill();
          g.globalAlpha = edgeFade * 0.96;
          g.beginPath(); g.arc(hx, hy, 6.4, 0, c.TAU); g.fill();
          g.fillStyle = c.col('ink'); g.globalAlpha = edgeFade * 0.85;
          g.beginPath(); g.arc(hx, hy, 2.6, 0, c.TAU); g.fill();
        }
        g.restore();
      });

      // cụm số liệu telemetry tối giản ở mép dưới Zone B (cách ly hoàn toàn khỏi Zone C)
      if (hasTel) {
        const tx = c.A.x0 + 8, tw = stageW - 16, ty = c.A.bottom - telH - 12, kt = c.EASE.out(c.k(10, 10));
        g.save(); g.globalAlpha = 0.9 * kt;
        g.fillStyle = c.mix(c.pal.bg, '#121620', 0.92);
        g.beginPath(); g.roundRect(tx, ty, tw, telH, 12); g.fill();
        g.strokeStyle = c.col('dim'); g.globalAlpha = 0.45 * kt; g.lineWidth = 1.5; g.stroke();
        g.fillStyle = c.col(coreRole); g.globalAlpha = 0.95 * kt;
        g.fillRect(tx + 1, ty + 14, 5, telH - 28);
        g.restore();
        const midY = ty + telH * 0.5;
        if (P.callout_num && P.callout_label) {
          const numMaxW = tw * 0.40, lblMaxW = tw * 0.50;
          const nf = fitText(c, String(P.callout_num), tx + 28, [50, 42, 34], { font: 'mono', align: 'left', weight: 800, maxW: numMaxW, maxH: telH - 22 });
          const lf = fitText(c, String(P.callout_label), tx + tw - 24, [34, 28, 24], { align: 'right', weight: 700, maxW: lblMaxW, maxH: telH - 22 });
          c.text(String(P.callout_num), tx + 28, midY - (nf.b.y0 + nf.b.y1) / 2, { size: nf.b.size || nf.size, font: 'mono', role: coreRole, align: 'left', weight: 800, maxW: numMaxW, k: kt });
          c.text(String(P.callout_label), tx + tw - 24, midY - (lf.b.y0 + lf.b.y1) / 2, { size: lf.b.size || lf.size, role: 'ink', align: 'right', weight: 700, maxW: lblMaxW, k: c.k(14, 9) });
        } else {
          const single = String(P.callout_num || P.callout_label);
          const sf = fitText(c, single, c.A.cx, [46, 38, 30], { font: P.callout_num ? 'mono' : undefined, weight: 800, maxW: tw - 48, maxH: telH - 22 });
          c.text(single, c.A.cx, midY - (sf.b.y0 + sf.b.y1) / 2, { size: sf.b.size || sf.size, font: P.callout_num ? 'mono' : undefined, role: P.callout_num ? coreRole : 'ink', weight: 800, maxW: tw - 48, k: kt });
        }
      }
    },
  };
}

const HERO_MOTIFS = ['rings', 'bars', 'grid', 'wave'];
function parseHeroNumber(P, c0) {
  const raw = P.number;
  if (typeof raw === 'number' && Number.isFinite(raw)) {
    const dec = P.decimals ?? decN(raw);
    return { numeric: true, val: raw, from: num(P.from, 0), dec, pre: P.prefix || '', suf: P.suffix || '', final: `${P.prefix || ''}${c0.fmtNum(raw, dec)}${P.suffix || ''}` };
  }
  const s = String(raw ?? '0').trim();
  const m = s.match(/^([^0-9.-]*)(-?\d[\d,]*(?:\.\d+)?)(.*)$/);
  if (m) {
    const cleaned = m[2].replace(/,/g, ''), val = Number(cleaned);
    if (Number.isFinite(val)) {
      const dec = P.decimals ?? ((cleaned.split('.')[1] || '').length);
      const pre = P.prefix || m[1] || '', suf = P.suffix || m[3] || '';
      return { numeric: true, val, from: num(P.from, 0), dec, pre, suf, final: `${pre}${c0.fmtNum(val, dec)}${suf}` };
    }
  }
  const final = `${P.prefix || ''}${s}${P.suffix || ''}`;
  return { numeric: false, val: 0, from: 0, dec: 0, pre: P.prefix || '', suf: P.suffix || '', final };
}

function hero_stat(c0, P) {                            // typography kiến trúc cỡ đại tràn khung + đồ họa nền phản ứng (Cleo Abram · Vox · Ordinary Folk)
  const N = c0.N, f0 = 3, f1 = Math.max(f0 + 12, Math.round((P.land ?? 0.54) * N));
  const spec = parseHeroNumber(P, c0), motif = HERO_MOTIFS.includes(P.bg_motif) ? P.bg_motif : 'rings';
  const role = P.role || 'accent';
  const cues = [{ f: f0, name: 'riser' }, { f: f1, name: 'hit', kick: 0.7 }];
  return {
    cues, texts: names(P.kicker, P.title, spec.final, P.unit, P.label),
    draw(c) {
      const g = c.g, yb = hasHdr(P) ? drawHeader(c, P, c.k(1, 10), true) : c.A.top + 8;
      const k = c.clamp((c.f - f0) / (f1 - f0)), e = c.EASE.out(k), landed = c.f >= f1;
      const stageW = c.A.x1 - c.A.x0, cx = c.A.cx;
      const hasBar = !!(P.sub_bar && typeof P.sub_bar === 'object');
      const barAreaH = hasBar ? 92 : 0, availTop = yb + 18, availBot = c.A.bottom - 18 - barAreaH;
      const midY = availTop + (availBot - availTop) * 0.44;

      // 1. Đồ họa nền phản ứng toàn khung theo motif & tiến độ e (tất định 100%)
      g.save();
      const ac = c.col(role), dm = c.col('dim');
      if (motif === 'rings') {
        const rg = g.createRadialGradient ? g.createRadialGradient(cx, midY, 30, cx, midY, 540) : null;
        if (rg) {
          rg.addColorStop(0, c.mix(c.pal.bg, ac, 0.16 * (0.4 + 0.6 * e))); rg.addColorStop(1, 'rgba(0,0,0,0)');
          g.fillStyle = rg; g.fillRect(0, availTop - 60, c.W, c.A.bottom - availTop + 120);
        }
        for (let i = 0; i < 6; i++) {
          const r = (90 + i * 86) * (0.72 + 0.28 * e) + Math.sin(c.f * 0.06 - i * 0.7) * 8;
          g.strokeStyle = i % 2 === 0 ? ac : dm; g.lineWidth = i === 1 ? 2.5 : 1.4;
          g.globalAlpha = (0.24 - i * 0.028) * (0.35 + 0.65 * e);
          g.beginPath(); g.arc(cx, midY, r, 0, c.TAU); g.stroke();
        }
        g.save(); g.translate(cx, midY); g.rotate(c.f * 0.008);
        g.strokeStyle = ac; g.lineWidth = 3; g.globalAlpha = 0.28 * e; g.setLineDash([16, 22]);
        g.beginPath(); g.arc(0, 0, 320, 0, c.TAU * (0.25 + 0.65 * e)); g.stroke(); g.restore();
      } else if (motif === 'bars') {
        const cols = 18, bw = (c.W - 120) / cols, baseY = c.A.bottom - 8;
        for (let i = 0; i < cols; i++) {
          const dist = Math.abs(i - (cols - 1) / 2) / (cols / 2);
          const env = (1 - dist * 0.55) * (0.5 + 0.5 * c.hash(i, 41));
          const wave = 0.85 + 0.15 * Math.sin(c.f * 0.09 + i * 0.55);
          const bh = Math.max(24, (c.A.bottom - availTop) * 0.72 * env * wave * (0.2 + 0.8 * e));
          g.fillStyle = i % 3 === 1 ? ac : dm;
          g.globalAlpha = i % 3 === 1 ? 0.16 : 0.11;
          g.fillRect(60 + i * bw + 6, baseY - bh, bw - 12, bh);
        }
      } else if (motif === 'grid') {
        const step = 68, shift = (c.f * 0.6) % step;
        g.strokeStyle = dm; g.lineWidth = 1.2; g.globalAlpha = 0.16;
        g.beginPath();
        for (let x = 40; x <= c.W - 40; x += step) { g.moveTo(x, availTop); g.lineTo(x, c.A.bottom); }
        for (let y = availTop + shift; y <= c.A.bottom; y += step) { g.moveTo(40, y); g.lineTo(c.W - 40, y); }
        g.stroke();
        g.fillStyle = ac; g.globalAlpha = 0.26 * e;
        const scanX = c.lerp(c.A.x0, c.A.x1, e);
        g.fillRect(scanX - 1.5, availTop, 3, c.A.bottom - availTop);
        for (let i = 0; i < 10; i++) {
          const nx = 40 + Math.floor(c.hash(i, 71) * 14) * step, ny = availTop + Math.floor(c.hash(i, 72) * 10) * step;
          g.beginPath(); g.arc(nx, ny, 4 + 2 * Math.sin(c.f * 0.12 + i), 0, c.TAU); g.fill();
        }
      } else {                                         // wave
        for (let w = 0; w < 4; w++) {
          g.strokeStyle = w === 0 ? ac : dm; g.lineWidth = w === 0 ? 3.5 : 1.6;
          g.globalAlpha = (w === 0 ? 0.3 : 0.16) * (0.3 + 0.7 * e);
          g.beginPath();
          for (let x = 0; x <= c.W; x += 24) {
            const amp = (42 + w * 22) * (0.35 + 0.65 * e);
            const y = midY + (w - 1.5) * 44 + Math.sin(x * (0.007 + w * 0.002) + c.f * (0.06 + w * 0.015) + w) * amp;
            if (x === 0) g.moveTo(x, y); else g.lineTo(x, y);
          }
          g.stroke();
        }
      }
      g.restore();

      // 2. Dynamic Flow Layout cho số kiến trúc cỡ đại + unit + label
      const numMaxW = stageW - 16;
      const uFit = P.unit ? fitText(c, String(P.unit), cx, [52, 44, 36], { maxW: stageW - 40, maxH: 110, weight: 800 }) : null;
      const lFit = P.label ? fitText(c, String(P.label), cx, [44, 38, 32], { maxW: stageW - 40, maxH: 120, weight: 700 }) : null;
      const subReserve = (uFit ? uFit.h + 24 : 0) + (lFit ? lFit.h + 28 : 0);
      const maxNumH = Math.max(130, availBot - availTop - subReserve - 24);

      let nPick = null;
      for (const sz of [230, 214, 198, 182, 166, 150, 134, 118, 102, 86]) {
        const b = c.text(spec.final, cx, 0, { size: sz, k: 0, maxW: numMaxW, track: -0.03, weight: 900 });
        nPick = { size: b.size || sz, b, h: b.y1 - b.y0 };
        if (b.lines === 1 && nPick.h <= maxNumH) break;
      }
      const stackH = nPick.h + subReserve;
      const startY = availTop + Math.max(0, (availBot - availTop - stackH) * 0.44);
      const numY = startY - nPick.b.y0;
      const dispTxt = (landed || !spec.numeric)
        ? spec.final
        : `${spec.pre}${c.fmtNum(c.lerp(spec.from, spec.val, e), spec.dec)}${spec.suf}`;
      const sc = landed ? 1 + Math.max(0, 1 - (c.f - f1) / 8) * 0.12 : (spec.numeric ? 0.94 + 0.06 * e : c.lerp(1.45, 1, e));

      g.save();
      g.translate(cx, numY - nPick.size * 0.32); g.scale(sc, sc); g.translate(-cx, -(numY - nPick.size * 0.32));
      const nb = c.text(dispTxt, cx, numY, { size: nPick.size, quiet: !landed, enter: 'none', maxW: numMaxW, track: -0.03, weight: 900, role: P.role ? role : 'ink' });
      g.restore();

      let curY = nb.y1;
      if (P.unit && uFit) {
        const ub = c.text(String(P.unit), cx, Math.min(availBot - (lFit ? lFit.h + 28 : 0) - uFit.b.y1, curY + 24 - uFit.b.y0), { size: uFit.b.size || uFit.size, role, k: c.k(6, 9), maxW: stageW - 40, weight: 800 });
        curY = ub.y1;
      }
      if (P.label && lFit) {
        c.text(String(P.label), cx, Math.min(availBot - lFit.b.y1, curY + 28 - lFit.b.y0), { size: lFit.b.size || lFit.size, role: 'ink', k: c.k(f1 + 2, 10), maxW: stageW - 40, weight: 700 });
      }

      // 3. Thanh so sánh mảnh phía dưới (sub_bar: {from, to, max?}) tách biệt hoàn toàn trên c.A.bottom
      if (hasBar) {
        const bFrom = num(P.sub_bar.from, 0), bTo = num(P.sub_bar.to, spec.val);
        const bMax = num(P.sub_bar.max) || Math.max(Math.abs(bFrom), Math.abs(bTo), 1) * 1.15;
        const bw = stageW - 40, bx = cx - bw / 2, barY = c.A.bottom - 58, bh = 12;
        const fFrac = c.clamp(bFrom / Math.max(1e-9, bMax)), curFrac = c.clamp(c.lerp(bFrom, bTo, e) / Math.max(1e-9, bMax));
        g.save();
        g.fillStyle = dm; g.globalAlpha = 0.28;
        g.beginPath(); g.roundRect(bx, barY, bw, bh, 6); g.fill();
        g.fillStyle = dm; g.globalAlpha = 0.65;
        g.beginPath(); g.roundRect(bx, barY, Math.max(4, bw * fFrac), bh, 6); g.fill();
        g.fillStyle = ac; g.globalAlpha = 0.94;
        g.beginPath(); g.roundRect(bx, barY, Math.max(6, bw * curFrac), bh, 6); g.fill();
        g.fillStyle = c.col('ink'); g.globalAlpha = 0.95;
        g.fillRect(bx + bw * fFrac - 1.5, barY - 6, 3, bh + 12);
        g.beginPath(); g.arc(bx + bw * curFrac, barY + bh / 2, 7.5, 0, c.TAU); g.fill();
        g.restore();
        const bDec = Math.max(decN(bFrom), decN(bTo));
        c.text(P.sub_bar.label_from || c.fmtNum(bFrom, bDec), bx, barY + 38, { size: 22, font: 'mono', role: 'dim', align: 'left', quiet: true, enter: 'none', weight: 600 });
        c.text(P.sub_bar.label_to || c.fmtNum(bTo, bDec), bx + bw, barY + 38, { size: 22, font: 'mono', role, align: 'right', quiet: true, enter: 'none', weight: 700 });
      }
    },
  };
}

// ================= VÒNG 16 — 2 BEAT TRỰC QUAN CHO TECH/AI (Fireship / ByteByteGo — 0 icon trừu tượng) =================
function code_terminal(c0, P) {
  const N = c0.N;
  const rawLines = (P.lines || []).slice(0, 6);
  const lines = rawLines.map((ln) => (typeof ln === 'string' ? { text: ln } : ln || { text: '' }));
  const tokens = (P.tokens || []).slice(0, 5);
  const hitF = Math.round((P.hit ?? 0.55) * N);
  const cues = [{ f: 2, name: 'click' }, ...lines.map((_, i) => ({ f: Math.min(N - 6, 4 + i * 7), name: 'typing' }))];
  if (P.status || lines.some((l) => l.bug)) cues.push({ f: hitF, name: 'hit', kick: 0.7 });
  const texts = names(P.kicker, P.title, P.filename, P.status, ...lines.map((l) => l.text),
    ...tokens.flatMap((t) => [t.text, t.id !== undefined ? String(t.id) : '']));
  return {
    cues, texts,
    draw(c) {
      const g = c.g, cx = c.A.cx;
      const yb = drawHeader(c, P, c.k(1, 9), true);
      const cardW = Math.min(920, c.A.x1 - c.A.x0 - 16), x0 = cx - cardW / 2;
      const hasTok = tokens.length > 0;
      const tokH = hasTok ? 156 : 0;
      const statH = P.status ? 72 : 0;
      const maxTermH = Math.max(260, c.A.bottom - yb - tokH - statH - 54);
      const termH = Math.min(maxTermH, 86 + Math.max(2, lines.length) * 66);
      const y0 = yb + 18 + Math.max(0, (c.A.bottom - yb - termH - tokH - statH - 36) * 0.35);
      const ke = c.k(1, 10);

      // Khung terminal tối có thanh tiêu đề 3 chấm
      g.save();
      g.globalAlpha = ke;
      g.fillStyle = '#0B0E14';
      g.strokeStyle = c.col('dim'); g.lineWidth = 2;
      g.beginPath(); if (g.roundRect) g.roundRect(x0, y0, cardW, termH, 18); else g.rect(x0, y0, cardW, termH);
      g.fill(); g.stroke();
      g.fillStyle = '#151A24';
      g.beginPath(); if (g.roundRect) g.roundRect(x0 + 1, y0 + 1, cardW - 2, 52, [17, 17, 0, 0]); else g.rect(x0 + 1, y0 + 1, cardW - 2, 52);
      g.fill();
      ['#FF5F56', '#FFBD2E', '#27C93F'].forEach((col, i) => {
        g.fillStyle = col; g.beginPath(); g.arc(x0 + 30 + i * 26, y0 + 26, 7.5, 0, c.TAU); g.fill();
      });
      g.restore();
      if (P.filename) {
        c.text(String(P.filename), cx, y0 + 34, { size: 24, font: 'mono', role: 'dim', k: ke, enter: 'none', weight: 600 });
      }

      // Từng dòng code gõ lần lượt + highlight đỏ dòng lỗi
      const rowH = Math.min(64, (termH - 74) / Math.max(1, lines.length));
      lines.forEach((ln, i) => {
        const ly = y0 + 68 + i * rowH + rowH * 0.56;
        const lk = c.k(4 + i * 7, 10);
        if (ln.bug && c.f >= hitF - 4) {
          const bk = c.clamp((c.f - (hitF - 4)) / 8);
          g.save();
          g.fillStyle = c.col('hot'); g.globalAlpha = 0.22 * bk;
          g.fillRect(x0 + 10, ly - rowH * 0.52, cardW - 20, rowH * 0.84);
          g.globalAlpha = 0.95 * bk;
          g.fillRect(x0 + 10, ly - rowH * 0.52, 6, rowH * 0.84);
          g.restore();
        }
        c.text(String(i + 1).padStart(2, '0'), x0 + 38, ly, { size: 26, font: 'mono', role: 'dim', align: 'left', k: lk, enter: 'none', quiet: true });
        c.text(String(ln.text || ''), x0 + 96, ly, {
          size: 32, font: 'mono', role: ln.bug ? 'hot' : (ln.role || 'ink'), align: 'left',
          k: lk, enter: 'type', maxW: cardW - 124, weight: ln.bug ? 700 : 600,
        });
      });

      // Dải thẻ token chips ([STR] -> 496) phía dưới terminal
      let curY = y0 + termH + 24;
      if (hasTok) {
        const gap = 18, chipW = Math.min(260, (cardW - gap * (tokens.length - 1)) / tokens.length);
        const startX = cx - (chipW * tokens.length + gap * (tokens.length - 1)) / 2;
        tokens.forEach((tk, i) => {
          const kChip = c.k(Math.max(hitF - 6, 12) + i * 5, 10);
          const bx = startX + i * (chipW + gap);
          const rCol = c.col(tk.role || (i === tokens.length - 1 ? 'hot' : 'accent'));
          g.save();
          g.globalAlpha = kChip;
          g.fillStyle = '#10151F'; g.strokeStyle = rCol; g.lineWidth = 3;
          g.beginPath(); if (g.roundRect) g.roundRect(bx, curY, chipW, 126, 14); else g.rect(bx, curY, chipW, 126);
          g.fill(); g.stroke();
          g.restore();
          c.text(String(tk.text || ''), bx + chipW / 2, curY + 48, { size: 32, font: 'mono', role: 'ink', k: kChip, enter: 'none', maxW: chipW - 20, weight: 700 });
          if (tk.id !== undefined && tk.id !== null) {
            c.text(String(tk.id), bx + chipW / 2, curY + 100, { size: 36, font: 'mono', role: tk.role || 'accent', k: kChip, enter: 'none', maxW: chipW - 20, weight: 800 });
          }
        });
        curY += 146;
      }

      if (P.status) {
        const ks = c.k(hitF, 8);
        c.K.tag(c, String(P.status), cx, Math.min(c.A.bottom - 34, curY + 34), ks);
      }
    },
  };
}

function chat_prompt(c0, P) {
  const N = c0.N, aiF = Math.round(N * 0.28), stampF = Math.round((P.hit ?? 0.62) * N);
  const cues = [{ f: 2, name: 'pop' }, { f: aiF, name: 'typing' }];
  if (P.verdict) cues.push({ f: stampF, name: 'stamp', kick: 0.85 });
  const texts = names(P.kicker, P.title, P.user, P.ai, P.verdict, P.note);
  return {
    cues, texts,
    draw(c) {
      const g = c.g, cx = c.A.cx;
      const yb = drawHeader(c, P, c.k(1, 9), true);
      const stageW = Math.min(900, c.A.x1 - c.A.x0 - 20), x0 = cx - stageW / 2;
      const bxW = stageW * 0.82;
      let curY = yb + 34;

      // 1. Bong bóng Prompt người dùng (căn phải, viền accent)
      const ku = c.k(2, 10);
      const uFit = fitText(c, String(P.user || ''), x0 + stageW - bxW + 28, [40, 34, 30], { align: 'left', maxW: bxW - 56, maxH: 150 });
      const uH = Math.max(96, uFit.h + 52);
      const ux = x0 + stageW - bxW;
      g.save();
      g.globalAlpha = ku;
      g.fillStyle = '#141B29'; g.strokeStyle = c.col('accent'); g.lineWidth = 3;
      g.beginPath(); if (g.roundRect) g.roundRect(ux, curY, bxW, uH, 22); else g.rect(ux, curY, bxW, uH);
      g.fill(); g.stroke();
      g.restore();
      c.text('USER PROMPT', ux + 28, curY + 28, { size: 20, font: 'mono', role: 'accent', align: 'left', k: ku, enter: 'none', quiet: true, weight: 700 });
      c.text(String(P.user || ''), ux + 28, curY + 52 - uFit.b.y0, { size: uFit.size, align: 'left', role: 'ink', k: ku, enter: 'none', maxW: bxW - 56, weight: 700 });
      curY += uH + 34;

      // 2. Bong bóng phản hồi AI (căn trái)
      const ka = c.k(aiF, 12);
      const aFit = fitText(c, String(P.ai || ''), x0 + 28, [42, 36, 32], { align: 'left', maxW: bxW - 56, maxH: 160 });
      const aH = Math.max(106, aFit.h + 56);
      g.save();
      g.globalAlpha = ka;
      g.fillStyle = '#18141A'; g.strokeStyle = c.col(P.verdict ? 'hot' : 'dim'); g.lineWidth = 3;
      g.beginPath(); if (g.roundRect) g.roundRect(x0, curY, bxW, aH, 22); else g.rect(x0, curY, bxW, aH);
      g.fill(); g.stroke();
      g.restore();
      c.text('AI MODEL', x0 + 28, curY + 28, { size: 20, font: 'mono', role: 'dim', align: 'left', k: ka, enter: 'none', quiet: true, weight: 700 });
      c.text(String(P.ai || ''), x0 + 28, curY + 54 - aFit.b.y0, { size: aFit.size, align: 'left', role: 'ink', k: ka, enter: 'type', maxW: bxW - 56, weight: 700 });
      curY += aH + 44;

      // 3. Con dấu kiểm chứng (VERIFIED / WRONG) đóng mạnh
      if (P.verdict && c.f >= stampF) {
        const ks = c.k(stampF, 7), sc = c.lerp(1.45, 1, c.EASE.back(ks));
        const vCol = c.col(P.verdict_role || 'hot');
        const vy = Math.min(c.A.bottom - (P.note ? 115 : 54), curY + 34);
        g.save();
        g.translate(cx, vy); g.scale(sc, sc); g.rotate(-0.06);
        g.strokeStyle = vCol; g.lineWidth = 6; g.fillStyle = '#0A0B0E';
        g.beginPath(); if (g.roundRect) g.roundRect(-240, -40, 480, 80, 12); else g.rect(-240, -40, 480, 80);
        g.fill(); g.stroke();
        g.restore();
        c.text(String(P.verdict).toUpperCase(), cx, vy + 16, { size: 46, font: 'mono', role: P.verdict_role || 'hot', k: ks, enter: 'none', weight: 900, maxW: 440 });
        curY = vy + 66;
      }

      if (P.note) {
        c.text(String(P.note), cx, Math.min(c.A.bottom - 28, curY + 36), { size: 32, font: 'mono', role: 'dim', k: c.k(stampF + 6, 10), maxW: stageW - 24, weight: 600 });
      }
    },
  };
}

export const BEATS = { title, drop, counter, compare, graph, process, scale, callout, fact, scene, outro, units, timeline, split, meter, dossier, xray_cutaway, hero_stat, code_terminal, chat_prompt };

// ---- công cụ nội bộ (KHÔNG cho storyboard dùng): bảng xem đạo cụ theo look — scripts/icon_sheet.py
function catalog(c0, P) {
  const names = P.names || [], cols = P.cols || 5;
  return {
    cues: [], texts: [],
    draw(c) {
      const cw = (c.W - 80) / cols, ch = 214;
      if (P.title) c.text(P.title, c.W / 2, 92, { size: 40, font: 'mono', quiet: true, enter: 'none', role: 'dim', weight: 700 });
      names.forEach((n, i) => {
        const x = 40 + (i % cols + 0.5) * cw, y = 140 + Math.floor(i / cols) * ch + 80;
        c.icon(n, { x, y, s: 66, p: 0.6, role: undefined });
        c.text(typeof n === 'string' ? n : 'parts', x, y + 108, { size: 24, font: 'mono', quiet: true, enter: 'none', role: 'dim', weight: 600 });
      });
    },
  };
}
export const TOOLS = { catalog };
