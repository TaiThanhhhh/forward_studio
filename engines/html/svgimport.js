// SVG → `parts` của tool (circle/rect/poly/line… toạ độ -1..1, y xuống, có vai màu) — chạy trong Edge headless lúc NHẬP
// (`python studio.py svg <file.svg>`), không chạy lúc render. Nhờ ra `parts`, icon SVG được vẽ bằng bút của từng look
// (boil, sketch, iso…) như đạo cụ có sẵn, và engine three.js ép khối được (icon3d).
// 1. SVGO (vendor/svgo, MIT) dọn file: style → thuộc tính, hình cơ bản → path, mọi lệnh path tuyệt đối.
// 2. Trình duyệt đo hình học: mỗi subpath lấy mẫu bằng getPointAtLength, nhân ma trận getCTM (mọi transform lồng nhau).
// 3. Màu fill/stroke tính sẵn (getComputedStyle, có kế thừa) → vai: xám/đen/trắng = ink, đỏ–vàng = hot,
//    xanh lá–lam = cold, còn lại = accent. Subpath nằm trong subpath khác của cùng hình = lỗ (holes).
import { optimize } from '../../vendor/svgo/svgo.browser.js';

const ROLE_OF = (css) => {
  const m = String(css || '').match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const [r, g, b, a = 1] = m[1].split(',').map((v) => parseFloat(v));
  if (a === 0) return null;
  const mx = Math.max(r, g, b) / 255, mn = Math.min(r, g, b) / 255, l = (mx + mn) / 2, d = mx - mn;
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  if (s < 0.25 || d < 0.08) return 'ink';
  let h = mx === r / 255 ? ((g - b) / 255 / d) % 6 : mx === g / 255 ? (b - r) / 255 / d + 2 : (r - g) / 255 / d + 4;
  h = (h * 60 + 360) % 360;
  if (h < 60 || h >= 330) return 'hot';
  if (h >= 150 && h < 260) return 'cold';
  return 'accent';
};

const inside = (pt, poly) => {                       // điểm trong đa giác (ray casting)
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
};
const area = (P) => { let a = 0; for (let i = 0, j = P.length - 1; i < P.length; j = i++) a += (P[j][0] + P[i][0]) * (P[j][1] - P[i][1]); return Math.abs(a / 2); };

/** text SVG → {parts, stats}. opts: {role: 'auto'|vai cố định, budget: tổng số điểm tối đa} */
window.svgToParts = async (text, opts = {}) => {
  const role0 = opts.role && opts.role !== 'auto' ? opts.role : null, budget = opts.budget || 1800;
  const svgo = optimize(text, {
    multipass: true,
    plugins: [
      { name: 'preset-default', params: { overrides: {
        convertPathData: { forceAbsolutePath: true, applyTransforms: false },
        convertShapeToPath: { convertArcs: true },
        cleanupIds: false, mergePaths: false,
      } } },
      'convertStyleToAttrs',
    ],
  }).data;
  const host = document.createElement('div');
  host.style.cssText = 'position:absolute;left:-99999px;top:0;width:1000px;height:1000px';
  host.innerHTML = svgo;
  document.body.appendChild(host);
  const root = host.querySelector('svg');
  if (!root) throw new Error('không phải file SVG');
  if (!root.getAttribute('width')) { root.setAttribute('width', '1000'); root.setAttribute('height', '1000'); }
  const NS = root.namespaceURI;                     // không ghi URL trong trang engine (test chặn mạng)
  const els = [...root.querySelectorAll('path, circle, ellipse, rect, line, polyline, polygon')]
    .filter((e) => !e.closest('defs, clipPath, mask, symbol, pattern, marker'));
  // subpath: path đã tuyệt đối hoá → tách trước mỗi lệnh M
  const pieces = [];
  for (const el of els) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const fill = cs.fill && cs.fill !== 'none' ? ROLE_OF(cs.fill) : null;
    const stroke = cs.stroke && cs.stroke !== 'none' ? ROLE_OF(cs.stroke) : null;
    if (!fill && !stroke) continue;
    const sw = parseFloat(cs.strokeWidth) || 1;
    const ds = el.tagName.toLowerCase() === 'path' ? (el.getAttribute('d') || '').split(/(?=M)/).filter((s) => s.trim()) : [null];
    for (const d of ds) {
      let geo = el;
      if (d !== null && ds.length > 1) {
        geo = document.createElementNS(NS, 'path'); geo.setAttribute('d', d);
        if (el.getAttribute('transform')) geo.setAttribute('transform', el.getAttribute('transform'));
        el.parentNode.insertBefore(geo, el);
      }
      const len = geo.getTotalLength ? geo.getTotalLength() : 0;
      if (!(len > 0)) continue;
      const closed = d === null ? !/^(line|polyline)$/i.test(el.tagName) : /z\s*$/i.test(d.trim());
      pieces.push({ el, geo, len, closed, fill, stroke, sw, M: geo.getCTM() });
    }
  }
  const total = pieces.reduce((a, p) => a + p.len, 0) || 1;
  for (const p of pieces) {
    const n = Math.max(p.closed ? 6 : 2, Math.min(420, Math.round(budget * p.len / total)));
    const pts = [];
    for (let i = 0; i <= n; i++) {
      if (p.closed && i === n) break;
      const q = p.geo.getPointAtLength(p.len * i / n), m = p.M;
      pts.push([m.a * q.x + m.c * q.y + m.e, m.b * q.x + m.d * q.y + m.f]);
    }
    p.pts = pts;
    p.scale = Math.sqrt(Math.abs(p.M.a * p.M.d - p.M.b * p.M.c)) || 1;
  }
  // chuẩn hoá về -1..1 (giữ tỉ lệ, căn giữa)
  const all = pieces.flatMap((p) => p.pts);
  if (!all.length) throw new Error('SVG không có hình vẽ được');
  const xs = all.map((q) => q[0]), ys = all.map((q) => q[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, k = 2 / Math.max(1e-9, x1 - x0, y1 - y0);
  const N = (q) => [+((q[0] - cx) * k).toFixed(4), +((q[1] - cy) * k).toFixed(4)];
  pieces.forEach((p) => { p.n = p.pts.map(N); });
  // lỗ: subpath tô kín nằm trong subpath tô kín khác (lớn hơn) của CÙNG phần tử. Đếm độ lồng: lẻ = lỗ của vỏ nhỏ
  // nhất chứa nó, chẵn = hình tô (mắt nằm trong khoảng khoét của mặt — kiểu icon "fill" — vẫn được vẽ).
  const parts = [];
  const byEl = new Map();
  pieces.forEach((p) => { if (!byEl.has(p.el)) byEl.set(p.el, []); byEl.get(p.el).push(p); });
  for (const group of byEl.values()) {
    const filled = group.filter((p) => p.fill && p.n.length >= 3);
    filled.forEach((p) => { p.area = area(p.n); });
    for (const p of filled) {
      const hosts = filled.filter((o) => o !== p && o.area > p.area && inside(p.n[0], o.n) && inside(p.n[Math.floor(p.n.length / 2)], o.n))
        .sort((a, b) => a.area - b.area);
      p.depth = hosts.length; p.host = hosts[0];
    }
    for (const p of filled) {
      if (p.depth % 2 === 1 && p.host) { (p.host.holes = p.host.holes || []).push(p.n); p.isHole = true; }
    }
    for (const p of group) {
      if (p.fill && !p.isHole && p.n.length >= 3) {
        const part = { k: 'poly', pts: p.n, role: role0 || p.fill };
        if (p.holes) part.holes = p.holes;
        parts.push(part);
      }
      if (p.stroke) {
        const w = Math.max(0.5, Math.min(2.5, (p.sw * p.scale * k) / 0.12));
        parts.push(p.closed ? { k: 'poly', pts: p.n, role: role0 || p.stroke, fill: false, w: +w.toFixed(2) }
          : { k: 'line', pts: p.n, role: role0 || p.stroke, w: +w.toFixed(2) });
      }
    }
  }
  host.remove();
  return { parts, stats: { elements: els.length, subpaths: pieces.length, points: all.length, bytes_in: text.length, bytes_svgo: svgo.length } };
};
window.glInfo = 'svgimport';
window.ready = true;
