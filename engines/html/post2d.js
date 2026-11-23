// Hậu kỳ "in & pixel" của các look 2D (vòng 10) — MỘT pass WebGL2, thứ tự cố định, tất định:
//   paper  (giấy ngả màu CHỈ trong khung tranh: vân sợi + ố mép, viền mực + lề giấy)
//   → halftone (cmyk: 4 bản mực theo góc tram trên giấy, chấm chỉ trong hình · benday: màu phẳng + chấm Ben-Day cho tông giữa)
//     + misregister (bản màu lệch so với bản mực)
//   → pixel (hạ phân giải div, lượng tử về bảng ≤ 64 màu sinh từ palette style, Bayer 4×4, phóng nearest)
// Ảnh ra chỉ phụ thuộc ảnh nguồn + tham số + số frame (không random, không thời gian thực) → worker nào cũng ra y hệt.
// Module thuần (không đọc job, không đọc đĩa): engine html gọi từ core.js; engine khác (three) có thể nạp lại để shot 3D
// cùng look với shot 2D: makePost2D(opts, palette, W, H) → {apply(srcCanvas, dstCtx, f), info} | null.

const VS = `#version 300 es
in vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }`;

const FS = `#version 300 es
precision highp float;
uniform sampler2D src;
uniform vec2 res;
uniform int ht;                 // 0 tắt · 1 cmyk · 2 benday
uniform float cell, ang, gain, ucr, maskLo, maskHi;
uniform vec3 paperC;
uniform vec2 mis;               // lệch bản màu (px)
uniform int np;                 // benday: số màu bảng (0 = mực/ink)
uniform vec3 pal[8], pmap[8];   // màu nguồn → màu in trong khung (ink → mực đen)
uniform float flatHi, flatLo;
uniform int usePanel;
uniform vec4 panel;             // x0 y0 x1 y1 (px, gốc trên-trái)
uniform float border, gutter, fiber, age;
uniform vec3 borderC;
uniform int pix;
uniform float div, dith, blackT;
uniform int nc;
uniform vec3 cols[64];
out vec4 o;

float h21(vec2 q) { q = fract(q * vec2(123.34, 456.21)); q += dot(q, q + 45.32); return fract(q.x * q.y); }
float vnoise(vec2 q) {
  vec2 i = floor(q), f = fract(q); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
}
vec3 at(vec2 q) { ivec2 s = ivec2(clamp(floor(q), vec2(0.0), res - 1.0)); return texelFetch(src, s, 0).rgb; }
mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
bool inRect(vec2 P, vec4 r) { return P.x >= r.x && P.y >= r.y && P.x < r.z && P.y < r.w; }

vec3 paperAt(vec2 P) {          // giấy: vân sợi tĩnh (không đổi theo frame) + ố vàng dần ra mép khung
  float n = vnoise(P * vec2(0.9, 0.25)) * 0.55 + vnoise(P * 0.07) * 0.45;
  vec2 c = (panel.xy + panel.zw) * 0.5, hs = (panel.zw - panel.xy) * 0.5;
  vec2 d = abs(P - c) / max(hs, vec2(1.0));
  float e = smoothstep(0.55, 1.0, max(d.x, d.y));
  vec3 aged = mix(paperC, paperC * vec3(0.93, 0.86, 0.66), age * e);
  return aged * (1.0 - fiber * (n - 0.5));
}

// ---- cmyk: 4 bản mực (C 15°, M 75°, Y 0°, K 45° + ang), chấm chỉ trong hình, nền đen giữ đen ----
vec4 toCmyk(vec3 s) {
  vec3 r = clamp(s / max(paperC, vec3(0.05)), 0.0, 1.0);
  float k = (1.0 - max(r.r, max(r.g, r.b))) * ucr;
  vec3 cmy = (1.0 - r - k) / max(1.0 - k, 1e-3);
  return vec4(clamp(cmy, 0.0, 1.0), k);
}
// tram ngưỡng (AM screen): độ phủ lấy từ CHÍNH điểm ảnh (lệch theo bản) so với hàm khoảng cách tới tâm ô lưới xoay
// → vùng phẳng ra chấm tròn đúng góc tram, còn nét mảnh/mép vật không bị "ăn" như khi lấy mẫu ở tâm ô.
float plate(vec2 P, int i, vec2 off, float a) {
  vec2 Q = rot(a) * (P + off);
  vec2 cc = (floor(Q / cell) + 0.5) * cell;
  vec4 k = toCmyk(at(P - off));
  float cov = i == 0 ? k.x : i == 1 ? k.y : i == 2 ? k.z : k.w;
  float r = cell * 0.7071 * sqrt(clamp(cov * gain, 0.0, 1.0));
  float d = length(Q - cc);
  return smoothstep(r + 0.75, r - 0.75, d);
}
vec3 cmykAt(vec2 P) {
  vec3 s = at(P);
  float m = smoothstep(maskLo, maskHi, max(s.r, max(s.g, s.b)));
  if (m <= 0.0) return vec3(0.0);
  const float D = 0.0174533;
  float c = plate(P, 0, mis, (15.0 + ang) * D), mm = plate(P, 1, -mis * 0.7, (75.0 + ang) * D);
  float y = plate(P, 2, vec2(mis.y, -mis.x) * 0.6, ang * D), k = plate(P, 3, vec2(0.0), (45.0 + ang) * D);
  vec3 col = paperC;
  col *= mix(vec3(1.0), vec3(0.0, 0.62, 0.92), c);
  col *= mix(vec3(1.0), vec3(0.92, 0.04, 0.52), mm);
  col *= mix(vec3(1.0), vec3(1.0, 0.92, 0.0), y);
  col *= mix(vec3(1.0), vec3(0.07, 0.06, 0.07), k);
  return col * m;
}

// ---- benday: mỗi điểm = t·(một màu bảng) trên nền; t cao → màu phẳng, t giữa → chấm Ben-Day, t thấp → nền ----
void fit(vec3 s, out int bi, out float bt) {
  bi = 0; bt = 0.0; float be = 1e9;
  for (int i = 0; i < 8; i++) {
    if (i >= np) break;
    vec3 p = pal[i];
    float t = clamp(dot(s, p) / max(dot(p, p), 1e-4), 0.0, 1.0);
    vec3 e = s - p * t; float er = dot(e, e);
    if (er < be) { be = er; bi = i; bt = t; }
  }
}
float bdot(vec2 P, float t) {
  vec2 Q = rot(0.7854) * P; vec2 cc = (floor(Q / cell) + 0.5) * cell;
  float r = cell * 0.7071 * sqrt(clamp((t - flatLo) / max(flatHi - flatLo, 1e-3), 0.0, 1.0));
  return smoothstep(r + 0.75, r - 0.75, length(Q - cc));
}
vec3 bendayAt(vec2 P, bool inP) {
  vec3 bg = inP ? paperAt(P) : vec3(0.0);
  int ik; float tk; fit(at(P), ik, tk);                // bản mực (đường viền ink, tông xám) — không lệch
  int ic; float tc; fit(at(P + mis), ic, tc);           // bản màu — lệch bản
  vec3 col = bg;
  if (ic > 0 && tc > flatLo) {
    vec3 cc = inP ? pmap[ic] : pal[ic];
    col = tc >= flatHi ? cc : mix(bg, cc, bdot(P, tc));
  }
  if (ik == 0 && tk > flatLo) {
    vec3 kc = inP ? pmap[0] : pal[0];
    col = tk >= flatHi ? kc : mix(col, kc, bdot(P + vec2(cell * 0.5), tk));
  }
  return col;
}

vec3 stage1(vec2 P) {
  bool inP = usePanel == 1 && inRect(P, panel);
  if (usePanel == 1) {
    if (!inP) {
      vec4 outer = vec4(panel.xy - gutter - border, panel.zw + gutter + border);
      if (inRect(P, outer)) {
        vec4 inner = vec4(panel.xy - border, panel.zw + border);
        return inRect(P, inner) ? borderC : paperAt(P);
      }
    }
  }
  if (ht == 1) return cmykAt(P);
  if (ht == 2) return bendayAt(P, inP);
  vec3 s = at(P);
  if (inP && max(s.r, max(s.g, s.b)) < 0.06) return paperAt(P);
  return s;
}

const float BAYER[16] = float[16](0., 8., 2., 10., 12., 4., 14., 6., 3., 11., 1., 9., 15., 7., 13., 5.);
vec3 quant(vec3 c, vec2 cellI) {
  if (max(c.r, max(c.g, c.b)) < blackT) return vec3(0.0);
  int bi = int(mod(cellI.x, 4.0)) + int(mod(cellI.y, 4.0)) * 4;
  c += (BAYER[bi] / 16.0 - 0.47) * dith;
  vec3 best = cols[0]; float bd = 1e9;
  for (int i = 0; i < 64; i++) {
    if (i >= nc) break;
    vec3 d = c - cols[i]; float e = 2.0 * d.r * d.r + 4.0 * d.g * d.g + 3.0 * d.b * d.b;
    if (e < bd) { bd = e; best = cols[i]; }
  }
  return best;
}

void main() {
  vec2 P = vec2(gl_FragCoord.x, res.y - gl_FragCoord.y);
  vec3 c;
  if (pix == 1) {
    vec2 ci = floor(P / div), base = ci * div;
    c = vec3(0.0);
    for (int j = 0; j < 4; j++) for (int i = 0; i < 4; i++) c += stage1(base + (vec2(i, j) + 0.5) * div / 4.0);
    c = quant(c / 16.0, ci);
  } else c = stage1(P);
  o = vec4(c, 1.0);
}`;

const hex3 = (h) => { const s = String(h || '#000000').replace('#', ''); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) / 255); };
const mix3 = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);

/** Bảng màu pixel ≤ n màu sinh từ palette style: đen + mỗi màu gốc thành một dải sáng/tối (+ xám trung tính).
 *  ramp: các mức sáng (0..1 = trộn từ đen tới màu gốc, > 1 = trộn tiếp tới trắng). */
export function pixelPalette(bases, { colors = 48, ramp = [0.22, 0.42, 0.64, 0.84, 1, 1.32], greys = 4 } = {}) {
  const out = [[0, 0, 0]];
  const add = (c) => { if (out.length < Math.min(64, colors) && !out.some((q) => Math.abs(q[0] - c[0]) + Math.abs(q[1] - c[1]) + Math.abs(q[2] - c[2]) < 0.035)) out.push(c); };
  for (const b of bases) for (const l of ramp) add(l <= 1 ? b.map((v) => v * l) : mix3(b, [1, 1, 1], l - 1));
  for (let i = 1; i <= greys; i++) add([i / (greys + 1), i / (greys + 1), i / (greys + 1)].map((v) => v * 0.9));
  return out;
}

/** opts = L.post (pixel/halftone/misregister/paper); pal = {bg, ink, a, b, c, dim…} (hex); roles = {hot, cold, accent}.
 *  Trả về null khi look không cần pass nào (không tạo WebGL). */
export function makePost2D(opts, pal, W, H) {
  const px = opts.pixel, ht = opts.halftone, mr = opts.misregister, pp = opts.paper;
  if (!px && !ht && !mr && !pp) return null;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const gl = cv.getContext('webgl2', { preserveDrawingBuffer: true, premultipliedAlpha: false, antialias: false, alpha: false, depth: false, stencil: false });
  if (!gl) throw new Error('engine html: look cần WebGL2 cho hậu kỳ pixel/halftone nhưng trình duyệt không có');
  const sh = (type, srcTxt) => { const s = gl.createShader(type); gl.shaderSource(s, srcTxt); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error('post2d shader: ' + gl.getShaderInfoLog(s)); return s; };
  const prog = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error('post2d link: ' + gl.getProgramInfoLog(prog));
  gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  const U = (n) => gl.getUniformLocation(prog, n);
  const set1 = (n, v) => gl.uniform1f(U(n), v), seti = (n, v) => gl.uniform1i(U(n), v);
  gl.uniform1i(U('src'), 0); gl.uniform2f(U('res'), W, H);
  // ---- halftone / benday ----
  const mode = !ht ? 0 : ht.mode === 'benday' ? 2 : 1;
  seti('ht', mode);
  set1('cell', ht?.cell ?? 10); set1('ang', ht?.angle ?? 0); set1('gain', ht?.gain ?? 1.08); set1('ucr', ht?.ucr ?? 0.9);
  set1('maskLo', ht?.mask?.[0] ?? 0.035); set1('maskHi', ht?.mask?.[1] ?? 0.11);
  set1('flatHi', ht?.flat ?? 0.8); set1('flatLo', ht?.low ?? 0.14);
  const paperC = hex3(pp?.color || ht?.paper || '#F2E8D2');
  gl.uniform3f(U('paperC'), ...paperC);
  const m = mr ? (typeof mr === 'number' ? [mr, mr * 0.6] : [mr.x ?? mr.px ?? 3, mr.y ?? (mr.px ?? 3) * 0.6]) : [0, 0];
  gl.uniform2f(U('mis'), m[0], m[1]);
  // bảng benday: [ink, màu…] → trong khung ink thành mực đen, màu giữ (hoặc ink_map)
  const bases = ['ink', 'a', 'b', 'c', 'd'].filter((k) => pal[k]).map((k) => hex3(pal[k]));
  const bmap = bases.map((b, i) => (i === 0 ? hex3(ht?.ink_in_panel || '#14110F') : b));
  seti('np', Math.min(8, bases.length));
  gl.uniform3fv(U('pal'), new Float32Array([...bases.flat(), ...new Array((8 - bases.length) * 3).fill(0)].slice(0, 24)));
  gl.uniform3fv(U('pmap'), new Float32Array([...bmap.flat(), ...new Array((8 - bmap.length) * 3).fill(0)].slice(0, 24)));
  // ---- giấy trong khung tranh ----
  const rect = pp?.rect;
  seti('usePanel', rect ? 1 : 0);
  gl.uniform4f(U('panel'), ...(rect ? [rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]] : [0, 0, 0, 0]));
  set1('border', pp?.border ?? 10); set1('gutter', pp?.gutter ?? 8); set1('fiber', pp?.fiber ?? 0.08); set1('age', pp?.age ?? 0.6);
  gl.uniform3f(U('borderC'), ...hex3(pp?.border_color || '#0E0C0A'));
  // ---- pixel ----
  seti('pix', px ? 1 : 0);
  let cols = [[0, 0, 0]];
  if (px) {
    const pb = (px.bases || ['ink', 'a', 'b', 'c']).filter((k) => pal[k]).map((k) => hex3(pal[k]));
    cols = px.list ? px.list.map(hex3) : pixelPalette(pb, { colors: px.colors ?? 48, ramp: px.ramp, greys: px.greys ?? 4 });
    set1('div', Math.max(1, px.div ?? 6)); set1('dith', px.dither ?? 0.06); set1('blackT', px.black ?? 0.045);
  } else { set1('div', 1); set1('dith', 0); set1('blackT', 0); }
  seti('nc', cols.length);
  const flat = new Float32Array(64 * 3); cols.forEach((c, i) => flat.set(c, i * 3));
  gl.uniform3fv(U('cols'), flat);
  gl.viewport(0, 0, W, H);
  return {
    info: { mode: ['none', 'cmyk', 'benday'][mode], pixel: px ? { div: px.div ?? 6, colors: cols.length } : null, panel: rect || null },
    colors: cols,
    apply(srcCanvas, dst) {
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, srcCanvas);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      dst.save(); dst.setTransform(1, 0, 0, 1, 0, 0); dst.globalAlpha = 1; dst.globalCompositeOperation = 'copy';
      dst.drawImage(cv, 0, 0); dst.restore();
    },
  };
}
