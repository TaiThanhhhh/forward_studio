// WP-X — Hybrid 2D ↔ 3D cho engine three.js (Vòng 10).
// 1. 2D trong 3D (`card2d`): vẽ icon / rig2d (`rig:<loài>`) / chữ bằng bút Canvas 2D + hậu kỳ look 2D (pixel/halftone/
//    cutout/…) vào CanvasTexture cập nhật mỗi frame, đặt trên mặt phẳng/tấm giấy có độ dày (`thickness`) trong không gian
//    3D (nhận ánh sáng, bóng, DOF, billboard tuỳ chọn). Hỗ trợ multiplane cắt giấy (`layers`) & HD-2D (sprite pixel trong
//    thế giới 3D).
// 2. 2D bám 3D (`overlay2d`): lớp Canvas 2D trong suốt ghép trước/sau khung 3D trong CÙNG trang; nhãn/mũi tên có `of` bám
//    vị trí chiếu màn hình của prop 3D từng frame; ghi `textBoxes()` cho QA OCR.
// 3. Hậu kỳ 3D theo look 2D (`world.look3d.post`: `pixel`, `halftone`, `misregister`, `paper`, `silhouette`, `posterize`)
//    tái dùng `makePost2D` của `engines/html/post2d.js`.
// Mọi thứ tất định theo frame f — không Math.random, không thời gian thực.

import { ICONS, iconFor, partsIcon } from '../html/icons.js';
import { rigPrims, isRig } from '../html/rig2d.js';
import { makePost2D } from '../html/post2d.js';

const hexRgb = (h) => {
  const s = String(h || '#ffffff').replace('#', '');
  if (s.length === 3) return [0, 1, 2].map((i) => parseInt(s[i] + s[i], 16));
  return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) || 0);
};
const mixHex = (a, b, t) => {
  const A = hexRgb(a), B = hexRgb(b);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('');
};
const hash = (a, b = 0) => {
  let h = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
};
const strSeed = (s) => {
  let h = 2166136261;
  for (const ch of String(s || '')) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return h | 0;
};

/** Bảng màu 2D từ world của job three.js để card2d/overlay2d cùng tông với cảnh 3D. */
export function paletteFromWorld(world = {}) {
  const c = world.colors || {};
  return {
    bg: '#000000',
    ink: c.white || c.label || '#F4F1EA',
    a: c.danger || '#FF4D3D',
    b: c.water || '#3CA4F0',
    c: c.accent || '#FFD23F',
    d: c.orange || '#FF9A3D',
    dim: c.grey || '#8E8E93',
  };
}

function drawPrims2d(g, prims, { x, y, s, pal, look = 'flat', cutEdge = false, seed = 1 }) {
  const col = (role) => {
    if (!role) return pal.ink;
    if (String(role)[0] === '#') return role;
    const map = { hot: pal.a, cold: pal.b, accent: pal.c, ink: pal.ink, dim: pal.dim, bg: pal.bg, skin: pal.skin || '#c98d66', hair: pal.hair || '#3a2a22' };
    return map[role] || pal.ink;
  };
  g.save();
  g.lineJoin = 'round'; g.lineCap = 'round';
  const isSil = look === 'silhouette';
  const isCut = look === 'cutout' || cutEdge;
  const strokeW = look === 'comic' ? 7 : look === 'halftone' ? 5 : look === 'lineart' ? 4 : 3.5;

  const trace = (p) => {
    const path = new Path2D();
    if (p.k === 'circle') {
      path.ellipse(x + (p.x || 0) * s, y + (p.y || 0) * s, Math.abs((p.rx ?? p.r ?? 0.5) * s),
        Math.abs((p.ry ?? p.r ?? 0.5) * s), p.rot || 0, 0, Math.PI * 2);
    } else if (p.k === 'rect') {
      const rx = x + (p.x || 0) * s, ry = y + (p.y || 0) * s, rw = (p.w || 1) * s, rh = (p.h || 1) * s;
      path.rect(rx, ry, rw, rh);
    } else if (p.k === 'arc') {
      path.arc(x + (p.x || 0) * s, y + (p.y || 0) * s, Math.abs((p.r ?? 0.5) * s), p.a0 || 0, p.a1 || Math.PI);
    } else if (Array.isArray(p.pts) && p.pts.length) {
      p.pts.forEach((q, i) => {
        const px = x + q[0] * s, py = y + q[1] * s;
        if (i === 0) path.moveTo(px, py); else path.lineTo(px, py);
      });
      if (p.k === 'poly') path.closePath();
    }
    return path;
  };

  if (isCut) {
    g.save();
    g.strokeStyle = mixHex(pal.ink, '#ffffff', 0.7);
    g.lineWidth = Math.max(8, s * 0.06);
    for (const p of prims) if (!p.fine && p.k !== 'line') g.stroke(trace(p));
    g.restore();
  }
  for (const p of prims) {
    const pa = trace(p);
    const fill = p.k !== 'line' && p.k !== 'arc' && p.fill !== false;
    const baseCol = p.tone ? mixHex(col(p.role), '#000000', p.tone) : col(p.role);
    g.save();
    if (p.alpha !== undefined) g.globalAlpha *= p.alpha;
    if (isSil) {
      if (!p.fine) {
        g.strokeStyle = pal.ink; g.lineWidth = strokeW + 3; g.stroke(pa);
        if (fill) { g.fillStyle = '#050505'; g.fill(pa); }
      } else if (p.role === 'ink') {
        g.fillStyle = pal.ink; g.fill(pa);
      }
    } else {
      if (fill) {
        g.fillStyle = p.hole ? 'rgba(0,0,0,0)' : (look === 'lineart' ? '#000000' : baseCol);
        g.fill(pa);
      }
      if (!p.fine && (strokeW > 0 || !fill)) {
        g.strokeStyle = look === 'comic' || look === 'halftone' ? '#0e0c0a' : (fill ? mixHex(baseCol, '#000000', 0.35) : baseCol);
        g.lineWidth = (p.w || 1) * strokeW;
        g.stroke(pa);
      }
    }
    g.restore();
  }
  g.restore();
}

/**
 * Prop `card2d`: vẽ 2D động (icon | `rig:<loài>` | text | parts) vào CanvasTexture cập nhật mỗi frame.
 * Hỗ trợ: `billboard`, `two_sided`, `thickness` (tạo viền dày cắt giấy), `cut_edge`, `look` (pixel16/sprite8/cutout/halftone/comic/silhouette/flat).
 */
export function makeCard2D(ctx, p) {
  const { THREE } = ctx;
  const w = p.w ?? 0.9, h = p.h ?? (p.draw === 'text' || p.text ? 0.45 : 0.9);
  const look = p.look || (ctx.job.html && ctx.job.html.look) || 'flat';
  const isPx = look === 'pixel16' || look === 'sprite8';
  const res = p.res || (isPx ? (look === 'sprite8' ? 96 : 160) : 512);
  const cw = Math.max(32, Math.round(res * (w / Math.max(w, h))));
  const ch = Math.max(32, Math.round(res * (h / Math.max(w, h))));
  const pal = { ...paletteFromWorld(ctx.job.world), ...(p.palette || {}) };
  const seed = strSeed(p.id || p.draw || p.icon || p.text || 'card');

  const g = ctx.group(ctx.world);
  if (typeof document === 'undefined') {
    // Môi trường Node (unit test không có DOM): vẫn dựng mesh phẳng đúng kích thước
    const geo = new THREE.PlaneGeometry(w, h);
    geo.translate(0, h / 2, 0);
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
    g.add(m);
    return { g, tick: () => {}, set: {} };
  }

  const cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
  const c2 = cv.getContext('2d');
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  if (isPx) { tex.minFilter = tex.magFilter = THREE.NearestFilter; tex.generateMipmaps = false; }

  const side = p.two_sided === false ? THREE.FrontSide : THREE.DoubleSide;
  const mat = p.lit === false
    ? new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.05, side })
    : ctx.toon('#ffffff', { map: tex, transparent: true, alphaTest: 0.05, side });
  const thick = Number(p.thickness || 0);
  let mesh;
  if (thick > 0.002) {
    const geo = new THREE.BoxGeometry(w, h, thick);
    geo.translate(0, h / 2, 0);
    const edgeMat = ctx.toon(p.edge_color || pal.ink);
    mesh = new THREE.Mesh(geo, [edgeMat, edgeMat, edgeMat, edgeMat, mat, mat]);
  } else {
    const geo = new THREE.PlaneGeometry(w, h);
    geo.translate(0, h / 2, 0);
    mesh = new THREE.Mesh(geo, mat);
  }
  mesh.castShadow = p.cast !== false;
  mesh.receiveShadow = p.receive !== false;
  if (p.billboard) g.userData.billboard = true;
  g.add(mesh);

  let curText = p.text || '';
  let curAction = p.action, curExpr = p.expr;
  const drawFrame = (f) => {
    const step = look === 'sprite8' || look === 'cutout' ? 2 : 1;
    const fs = Math.floor(f / step) * step;
    c2.clearRect(0, 0, cw, ch);
    if (p.bg) { c2.fillStyle = p.bg; c2.fillRect(0, 0, cw, ch); }
    const spec = p.draw || p.icon || (curText ? 'text' : 'dot');
    const size = Math.min(cw, ch) * 0.38;
    if (spec === 'text' || (curText && !p.icon && !p.draw)) {
      const px = Math.max(14, Math.round(ch * 0.42));
      c2.font = `700 ${px}px "${ctx.job.font_family || 'sans-serif'}", sans-serif`;
      c2.textAlign = 'center'; c2.textBaseline = 'middle';
      c2.fillStyle = p.color || pal.ink;
      c2.fillText(String(curText), cw / 2, ch / 2, cw * 0.92);
    } else if (typeof spec === 'object' && spec.parts) {
      drawPrims2d(c2, partsIcon(spec), { x: cw / 2, y: ch / 2, s: size, pal, look, cutEdge: p.cut_edge, seed });
    } else if (isRig(spec)) {
      const pr = rigPrims(spec, { f: fs, fps: ctx.fps || 30, seed, role: p.role, args: { action: curAction, expr: curExpr, face: p.face, hair: p.hair, colors: p.colors } });
      drawPrims2d(c2, pr, { x: cw / 2, y: ch * 0.54, s: size * 1.05, pal, look, cutEdge: p.cut_edge, seed });
    } else {
      const fn = ICONS[iconFor(String(spec))] || ICONS.dot;
      const pr = fn({ f: fs, p: p.p ?? 0.6, role: p.role, hash });
      drawPrims2d(c2, pr, { x: cw / 2, y: ch / 2, s: size, pal, look, cutEdge: p.cut_edge, seed });
    }
    tex.needsUpdate = true;
  };
  drawFrame(0);
  return {
    g,
    tick: (f) => drawFrame(f),
    set: {
      text: (v) => { curText = String(v ?? ''); },
      action: (v) => { curAction = v; },
      expr: (v) => { curExpr = v; },
    },
  };
}

/**
 * Prop `multiplane`: nhiều lớp cắt giấy 2D ở các z khác nhau trong không gian 3D (parallax thật + bóng thật).
 * `layers: [{draw|icon|text, z, x, y, w, h, thickness, look, cut_edge}]`
 */
export function makeMultiplane(ctx, p) {
  const g = ctx.group(ctx.world);
  const subs = (p.layers || []).map((ly, i) => {
    const card = makeCard2D(ctx, { look: 'cutout', thickness: 0.02, cut_edge: true, ...ly, id: `${p.id || 'mp'}_${i}` });
    card.g.position.set(ly.x || 0, ly.y || 0, ly.z ?? (-i * 0.35));
    ctx.world.remove(card.g);
    g.add(card.g);
    return card;
  });
  return { g, tick: (f) => subs.forEach((s) => s.tick(f)), set: {} };
}

/**
 * Overlay 2D bám vật 3D (`overlay2d: [{kind|type, text, of, offset, x, y, u0, u1, z: "front"|"back", color, bg, arrow}]`).
 * Ghép lớp Canvas 2D trong suốt lên trên/dưới canvas WebGL trong CÙNG trang; xuất khung OCR qua `textBoxes()`.
 */
export function makeOverlay2D(ctx, items, W, H) {
  if (!Array.isArray(items) || !items.length || typeof document === 'undefined') return null;
  const pal = paletteFromWorld(ctx.job.world);
  const grid = ctx.job.layout_grid || { header: [250, 370], stage: [390, 1240] };
  const captionsOn = ctx.job.captions_on !== false;
  const minY = (grid.header && grid.header[0]) || 250;
  const maxY = captionsOn ? Math.min(H - 220, ((grid.stage && grid.stage[1]) || 1240) - 36) : H - 220;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const g = cv.getContext('2d');
  let lastBoxes = [];

  function project(obj, camera, THREE) {
    if (!obj) return null;
    obj.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(obj);
    const pt = box.isEmpty() ? obj.getWorldPosition(new THREE.Vector3()) : new THREE.Vector3(
      (box.min.x + box.max.x) / 2, box.max.y, (box.min.z + box.max.z) / 2,
    );
    const p = pt.clone().project(camera);
    if (p.z > 1) return null;
    return [(p.x + 1) / 2 * W, (1 - p.y) / 2 * H];
  }

  return {
    canvas: cv,
    draw(f, N, objectOf, camera, THREE, layer = 'front') {
      const u = f / Math.max(1, N - 1);
      g.clearRect(0, 0, W, H);
      if (layer === 'front') lastBoxes = [];
      const placed = [];
      for (const it of items) {
        if ((it.z || 'front') !== layer) continue;
        if (u < (it.u0 ?? 0) || u > (it.u1 ?? 1)) continue;
        const anchor = it.of ? project(objectOf(it.of), camera, THREE) : null;
        const off = it.offset || [0, -100];
        const x = anchor ? anchor[0] + (off[0] || 0) : (it.x ?? 0.5) * W;
        const y = anchor ? anchor[1] + (off[1] || 0) : (it.y ?? 0.24) * H;
        const clampedX = Math.max(120, Math.min(W - 120, x));
        let clampedY = Math.max(minY, Math.min(maxY, y));
        for (const pb of placed) {
          if (Math.abs(clampedX - pb.x) < 280 && Math.abs(clampedY - pb.y) < 76) {
            clampedY = Math.max(minY, Math.min(maxY, clampedY >= pb.y ? pb.y + 78 : pb.y - 78));
          }
        }
        placed.push({ x: clampedX, y: clampedY });
        const u0 = it.u0 ?? 0, u1 = it.u1 ?? 1;
        const fadeIn = Math.min(1, Math.max(0, (u - u0) / 0.07));
        const fadeOut = Math.min(1, Math.max(0, (u1 - u) / 0.06));
        const alpha = Math.min(fadeIn, fadeOut);
        if (alpha <= 0.01) continue;
        const accent = (it.color && pal[it.color]) || (it.color && String(it.color)[0] === '#' ? it.color : null) || pal.c;
        const textCol = it.color === 'danger' ? pal.a : it.color === 'accent' ? pal.c : it.color === 'water' ? pal.b : (it.color && String(it.color)[0] === '#' ? it.color : pal.ink);

        g.save();
        g.globalAlpha = alpha;
        if (anchor && it.arrow !== false) {
          g.save();
          g.strokeStyle = accent;
          g.lineWidth = 2.0;
          g.globalAlpha = alpha * 0.82;
          g.beginPath(); g.moveTo(clampedX, clampedY + 22); g.lineTo(anchor[0], anchor[1]); g.stroke();
          g.fillStyle = accent;
          g.beginPath(); g.arc(anchor[0], anchor[1], 5, 0, Math.PI * 2); g.fill();
          g.restore();
        }
        if (it.icon) {
          const fn = ICONS[iconFor(it.icon)] || ICONS.dot;
          drawPrims2d(g, fn({ f, p: 0.6, hash }), { x: clampedX, y: clampedY, s: it.size || 56, pal, look: it.look || 'flat' });
        }
        if (it.text) {
          const px = it.px || 36;
          const fam = ctx.job.font_family || 'StyleFont';
          const font = `600 ${px}px "${fam}", sans-serif`;
          g.save();
          g.font = font; g.textAlign = 'center'; g.textBaseline = 'middle';
          const hasPin = it.pin !== undefined && it.pin !== null && it.pin !== '';
          const pinW = hasPin ? px * 1.1 + 12 : 0;
          const tw = g.measureText(String(it.text)).width, padX = 20, padY = 12;
          const bw = tw + pinW + padX * 2, bh = px + padY * 2;
          const bx0 = Math.max(40, Math.min(W - 40 - bw, clampedX - bw / 2));
          const by0 = clampedY - bh / 2;
          g.shadowColor = 'rgba(0,0,0,0.48)'; g.shadowBlur = 14; g.shadowOffsetY = 4;
          g.fillStyle = it.bg || 'rgba(12,15,20,0.82)';
          g.strokeStyle = it.border || accent;
          g.lineWidth = 1.8;
          g.beginPath(); g.roundRect(bx0, by0, bw, bh, 10); g.fill();
          g.shadowBlur = 0; g.shadowOffsetY = 0; g.stroke();
          if (hasPin) {
            const pcx = bx0 + padX + px * 0.48, pcy = by0 + bh / 2;
            g.fillStyle = accent;
            g.beginPath(); g.arc(pcx, pcy, px * 0.48, 0, Math.PI * 2); g.fill();
            g.fillStyle = '#0B0C10';
            g.font = `800 ${Math.round(px * 0.68)}px "${fam}", sans-serif`;
            g.fillText(String(it.pin), pcx, pcy + 1);
            g.font = font;
          }
          g.fillStyle = textCol;
          g.fillText(String(it.text), bx0 + padX + pinW + tw / 2, by0 + bh / 2 + 1);
          g.restore();
          if (layer === 'front' && alpha > 0.7) {
            lastBoxes.push({ text: String(it.text), box: [bx0, by0, bx0 + bw, by0 + bh], tex: null });
          }
        }
        g.restore();
      }
      return cv;
    },
    textBoxes: () => lastBoxes,
  };
}

/**
 * Hậu kỳ 3D theo look 2D (`world.look3d.post`: `pixel`, `halftone`, `misregister`, `paper`, `silhouette`, `posterize`).
 * Tái dùng WebGL2 pass `makePost2D` của `engines/html/post2d.js` → shot 3D cùng chất với shot 2D.
 */
export function make3DPost2D(look3d, world, W, H) {
  const po = look3d && typeof look3d.post === 'object' ? look3d.post : null;
  if (!po || (!po.pixel && !po.halftone && !po.misregister && !po.paper)) return null;
  const pal = paletteFromWorld(world);
  const p2 = makePost2D(po, pal, W, H);
  if (!p2) return null;
  const out = document.createElement('canvas'); out.width = W; out.height = H;
  const ctx2d = out.getContext('2d');
  return {
    canvas: out,
    info: p2.info,
    apply(webglCanvas) {
      p2.apply(webglCanvas, ctx2d);
      return out;
    },
  };
}
