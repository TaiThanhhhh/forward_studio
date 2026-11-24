// Engine code-shot cho kênh "forward." — port engine/main.js của cartoon-short-kit (toon material, ink pass theo
// normal/depth, DOF, grade, flash) sang SÂN KHẤU ĐEN: không sky/hills, nền #000, fog đen, màu ink + viền rim theo
// style (styles/*.json → world), palette lấy từ style. Cảnh (engines/three/scenes/*.js) là hàm thuần theo frame.
// Hợp đồng với vidlib/coderender.py: ?job=<url job.json> → window.ready, window.renderFrame(f), window.meta.
import * as THREE from '../../vendor/three/three.module.js';
import * as MO from '../../lib/motion/motion.js';
import * as P from './paint.js';
import * as CAST from './cast.js';
import * as PROPS from './props.js';
import { needsPhysics, loadRapier } from './physics.js';
import { makeOverlay2D, make3DPost2D } from './hybrid.js';

window.stage = 'job';
const qs = new URLSearchParams(location.search);
const JOB = await (await fetch(qs.get('job'), { cache: 'no-store' })).json();
window.stage = 'fonts';
const ST = JOB.world;
const W = JOB.width || 1080, H = JOB.height || 1920;
await Promise.all((JOB.fonts || []).map(async (f) => {
  const ff = new FontFace(f.family, `url(${f.url})`); await ff.load(); document.fonts.add(ff);
}));

window.stage = 'gl';
const canvas = document.getElementById('c');
canvas.width = W; canvas.height = H;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.shadowMap.enabled = ST.shadows !== false; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, W / H, 0.05, 400);
const rx = (a) => a * Math.PI / 180;
const C = (k) => (ST.colors && ST.colors[k]) || k;

// ---------- look 3D (styles/<id>.json → world.look3d): chất liệu + hậu kỳ cho CẢ cảnh ----------
// Chuỗi ("clay") hoặc object ({"kind": "clay", "rough": 0.8, "bloom": 0.3, …}) ghi đè từng tham số của preset.
// mat: toon | standard | physical | lambert | wire | xray · env: cường độ env map studio (0 = tắt) · facet: số cạnh tối đa
// của khối tròn (low-poly) · tm: tone map ACES · bloom/bloom_th · grain · ink_px: ghi đè độ dày nét (0 = không nét).
const LOOK3D = {
  toon: { mat: 'toon' },
  clay: { mat: 'standard', rough: 0.82, metal: 0.04, env: 0.72, bump: 0.012, tm: 1, exposure: 1.06, bloom: 0.14, bloom_th: 0.72, grain: 0.03 },
  plastic: { mat: 'physical', rough: 0.3, metal: 0, clearcoat: 1, coat_rough: 0.08, env: 1.0, tm: 1, exposure: 1.0, bloom: 0.18 },
  glass: { mat: 'physical', rough: 0.06, metal: 0, transmission: 0.5, thickness: 0.6, ior: 1.5, env: 2.4, glow: 0.14, clearcoat: 1,
    coat_rough: 0.04, tm: 1, exposure: 1.15, bloom: 0.3, bloom_th: 0.45, ink_px: 1.2 },
  chrome: { mat: 'standard', rough: 0.24, metal: 1, env: 2.6, env_wide: 1.9, glow: 0.04, tm: 1, exposure: 1.2, bloom: 0.25, ink_px: 0 },
  lowpoly: { mat: 'standard', rough: 0.78, metal: 0, env: 0.35, facet: 7, tm: 1, ink_px: 1.6 },
  paper: { mat: 'lambert', facet: 6, tm: 1, grain: 0.05, ink_px: 1.2 },
  holo: { mat: 'wire', facet: 10, opacity: 0.9, shadows: false, bloom: 0.55, bloom_th: 0.15, grain: 0.04, ink_px: 0 },
  xray: { mat: 'xray', power: 2.2, base: 0.06, shadows: false, bloom: 0.45, bloom_th: 0.1, grain: 0.03, ink_px: 0 },
  // thời 90 — retro90 (kiểu N64) · psx (kiểu PS1): mat 'gouraud' = ánh sáng tính ở ĐỈNH rồi nội suy màu (khối ít đỉnh,
  // pháp tuyến mượt), không viền, không shadow map (blob = bóng tròn dưới vật). Texture vẽ bằng code tex_px px, lọc
  // filter: bilinear | nearest. Hậu kỳ: render nội bộ 1/res_div → lượng tử color_bits bit/kênh + Bayer 4×4 dither →
  // phóng lại upscale: bilinear (+ vi_blur) | nearest. wobble = snap đỉnh theo lưới màn hình thấp (px), affine 0..1 = méo
  // texture không phối cảnh, wrap = sáng quấn mềm, spec/shine = bóng theo đỉnh, ambient = nhân đèn hemi, fog_near/fog_far
  // = sương theo đỉnh tan vào ĐEN, text_hd = chữ trong cảnh vẽ ở độ phân giải đầy đủ (OCR đọc được).
  retro90: { mat: 'gouraud', facet: 10, ink_px: 0, shadows: false, post: false, blob: 0.6, spec: 0.2, shine: 14, wrap: 0.35,
    ambient: 1, res_div: 3, upscale: 'bilinear', vi_blur: 0.5, aa: true, filter: 'bilinear', tex_px: 128, color_bits: 5,
    dither: 1, wobble: 0, affine: 0, text_hd: true, grain: 0.01 },
  psx: { mat: 'gouraud', facet: 8, ink_px: 0, shadows: false, post: false, blob: 0.55, spec: 0, wrap: 0.15, ambient: 1,
    res_div: 4, upscale: 'nearest', aa: false, filter: 'nearest', tex_px: 64, color_bits: 5, dither: 1, wobble: 1,
    affine: 0.85, text_hd: true },
};
const LK = (() => {
  const raw = ST.look3d || 'toon', o = typeof raw === 'string' ? { kind: raw } : { kind: 'toon', ...raw };
  return { ...(LOOK3D[o.kind] || LOOK3D.toon), ...o };
})();
const steps = ST.toon_steps || [150, 255];
const grad = (() => {
  const d = new Uint8Array(steps.length * 4); steps.forEach((v, i) => d.set([v, v, v, 255], i * 4));
  const t = new THREE.DataTexture(d, steps.length, 1); t.minFilter = t.magFilter = THREE.NearestFilter; t.needsUpdate = true; return t;
})();
// vân tay đất sét: nhiễu tất định (không Math.random) → frame nào cũng giống nhau, render song song an toàn
const noiseTex = (() => {
  if (!LK.bump) return null;
  const n = 256, d = new Uint8Array(n * n * 4); let s = 1234567;
  for (let i = 0; i < n * n; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; const v = 110 + (s % 36); d.set([v, v, v, 255], i * 4); }
  const t = new THREE.DataTexture(d, n, n); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 3);
  t.magFilter = THREE.LinearFilter; t.needsUpdate = true; return t;
})();
const xrayMat = (color, o = {}) => {
  const col = new THREE.Color(C(color));
  const m = new THREE.ShaderMaterial({
    uniforms: { color: { value: col }, power: { value: LK.power ?? 2.2 }, base: { value: LK.base ?? 0.06 } },
    vertexShader: `varying vec3 vN; varying vec3 vV; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 color; uniform float power, base; varying vec3 vN; varying vec3 vV;
      void main(){ float f = pow(1. - abs(dot(normalize(vN), normalize(vV))), power); gl_FragColor = vec4(color*(base + f*1.5), 1.); }`,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: o.side ?? THREE.DoubleSide,
  });
  m.color = col;                 // đạo cụ đổi màu bằng m.color.copy/lerp (bi nóng đỏ, pin…) → trỏ thẳng vào uniform
  return m;
};
// ---------- Gouraud theo đỉnh (mat 'gouraud' — retro90/psx). r160 MeshLambertMaterial đã tính sáng theo fragment nên tự
// viết ShaderMaterial: hemi (ambient) + đèn key + đèn rim/fill + bóng Blinn nhẹ, TẤT CẢ ở vertex shader; fragment chỉ
// nhân màu nội suy với texture. Uniform đèn là MỘT object dùng chung cho mọi vật liệu → renderFrame cập nhật 1 lần/frame
// (hướng đèn trong hệ camera của frame đó → tất định). SNAP = rung đỉnh (snap toạ độ màn hình theo lưới res thấp).
const GU = LK.mat === 'gouraud' ? {
  uKeyDir: { value: new THREE.Vector3(0, 1, 0) }, uKeyCol: { value: new THREE.Color(1, 1, 1) },
  uRimDir: { value: new THREE.Vector3(0, 0, -1) }, uRimCol: { value: new THREE.Color(0, 0, 0) },
  uUp: { value: new THREE.Vector3(0, 1, 0) }, uSky: { value: new THREE.Color() }, uGround: { value: new THREE.Color() },
  uSpec: { value: LK.spec ?? 0 }, uShine: { value: LK.shine ?? 16 }, uWrap: { value: LK.wrap ?? 0 }, uAffine: { value: LK.affine ?? 0 },
  uFogCol: { value: new THREE.Color(C(ST.fog || '#000000')) }, uFogNear: { value: LK.fog_near ?? ST.fog_near ?? 30 },
  uFogFar: { value: LK.fog_far ?? ST.fog_far ?? 120 }, uSnapRes: { value: new THREE.Vector2(W, H) },
} : null;
const GOURAUD_VS = `uniform vec3 uKeyDir, uKeyCol, uRimDir, uRimCol, uUp, uSky, uGround; uniform float uSpec, uShine, uWrap, uFogNear, uFogFar; uniform vec2 uSnapRes;
varying vec3 vLit; varying vec3 vSpec; varying float vFog;
#ifdef USE_COLOR
varying vec3 vCol;
#endif
#ifdef USE_MAP
varying vec2 vUv; varying vec3 vUvA;
#endif
void main(){
  vec4 mv = modelViewMatrix * vec4(position, 1.);
  vec3 n = normalize(normalMatrix * normal), v = normalize(-mv.xyz);
  float nk = dot(n, uKeyDir);
  vec3 lit = mix(uGround, uSky, .5 + .5 * dot(n, uUp)) + uKeyCol * max((nk + uWrap) / (1. + uWrap), 0.) + uRimCol * max(dot(n, uRimDir), 0.);
  vLit = lit * .3183099;                                   // 1/π như BRDF_Lambert của three → cùng cường độ đèn với look khác
  vSpec = nk > 0. ? uKeyCol * (uSpec * .3183099 * pow(max(dot(n, normalize(uKeyDir + v)), 0.), uShine)) : vec3(0.);
  vFog = clamp((-mv.z - uFogNear) / max(1e-3, uFogFar - uFogNear), 0., 1.);
  vec4 cp = projectionMatrix * mv;
#ifdef SNAP
  vec2 gr = uSnapRes * .5; cp.xy = floor(cp.xy / cp.w * gr + .5) / gr * cp.w;
#endif
#ifdef USE_COLOR
  vCol = color;
#endif
#ifdef USE_MAP
  vUv = uv; vUvA = vec3(uv * cp.w, cp.w);                  // vUvA: nội suy affine kiểu PS1 (chia lại ở fragment)
#endif
  gl_Position = cp;
}`;
const GOURAUD_FS = `uniform vec3 uColor, uEmissive, uFogCol; uniform float uOpacity, uAlphaTest, uAffine; uniform sampler2D uMap;
varying vec3 vLit; varying vec3 vSpec; varying float vFog;
#ifdef USE_COLOR
varying vec3 vCol;
#endif
#ifdef USE_MAP
varying vec2 vUv; varying vec3 vUvA;
#endif
void main(){
  vec4 b = vec4(uColor, uOpacity);
#ifdef USE_MAP
  b *= texture2D(uMap, mix(vUv, vUvA.xy / vUvA.z, uAffine));
#endif
  vec3 sp = vSpec;
#ifdef USE_COLOR
  b.rgb *= vCol; sp *= vCol;                               // mép bối cảnh tan vào đen: cả bóng sáng cũng tắt
#endif
  if (b.a < uAlphaTest) discard;
  gl_FragColor = vec4(mix(b.rgb * vLit + sp + uEmissive, uFogCol, vFog), b.a);
}`;
const gouraudMat = (color, o = {}) => {
  const map = o.map || null;
  const m = new THREE.ShaderMaterial({
    uniforms: { ...GU, uColor: { value: new THREE.Color(C(color)) }, uEmissive: { value: new THREE.Color(o.emissive ?? 0x000000) },
      uMap: { value: map }, uOpacity: { value: o.opacity ?? 1 }, uAlphaTest: { value: o.alphaTest ?? (map ? 0.02 : 0) } },
    defines: { ...(map ? { USE_MAP: '' } : {}), ...(LK.wobble ? { SNAP: '' } : {}) },
    vertexColors: !!o.vertexColors, vertexShader: GOURAUD_VS, fragmentShader: GOURAUD_FS,
    side: o.side ?? THREE.FrontSide, transparent: !!o.transparent, depthWrite: o.depthWrite ?? true,
  });
  m.color = m.uniforms.uColor.value; m.emissive = m.uniforms.uEmissive.value;   // đạo cụ đổi màu/độ nóng như vật liệu thường
  Object.defineProperty(m, 'opacity', { get: () => m.uniforms.uOpacity.value, set: (v) => { m.uniforms.uOpacity.value = v; } });
  return m;
};
// glow: tự phát sáng nhẹ theo màu vật (kính/kim loại trên nền đen vẫn đọc được hình khối)
const glowOf = (c) => (LK.glow ? { emissive: new THREE.Color(c).multiplyScalar(LK.glow) } : {});
const surf = (color, o = {}) => {
  const c = C(color);
  switch (LK.mat) {
    case 'standard':
      return new THREE.MeshStandardMaterial({ color: c, roughness: LK.rough ?? 0.6, metalness: LK.metal ?? 0,
        envMapIntensity: LK.env ?? 0, flatShading: !!LK.facet, ...glowOf(c), ...(noiseTex ? { bumpMap: noiseTex, bumpScale: LK.bump } : {}), ...o });
    case 'physical':
      return new THREE.MeshPhysicalMaterial({ color: c, roughness: LK.rough ?? 0.3, metalness: LK.metal ?? 0,
        clearcoat: LK.clearcoat ?? 0, clearcoatRoughness: LK.coat_rough ?? 0.1, transmission: LK.transmission ?? 0,
        thickness: LK.thickness ?? 0, ior: LK.ior ?? 1.5, envMapIntensity: LK.env ?? 0, flatShading: !!LK.facet,
        ...(LK.transmission ? { attenuationColor: new THREE.Color(c), attenuationDistance: 0.6 } : {}), ...glowOf(c), ...o });
    case 'lambert': return new THREE.MeshLambertMaterial({ color: c, flatShading: !!LK.facet, ...o });
    case 'wire': return new THREE.MeshBasicMaterial({ color: c, wireframe: !o.map, transparent: true, opacity: LK.opacity ?? 0.9, ...o });
    case 'xray': return o.map ? new THREE.MeshBasicMaterial({ color: c, ...o }) : xrayMat(color, o);
    case 'gouraud': return gouraudMat(color, o);
    default: return new THREE.MeshToonMaterial({ gradientMap: grad, color: c, ...o });
  }
};
const toon = surf;   // tên cũ: đạo cụ/cảnh gọi ctx.toon(...) → chất liệu theo look 3D của style
// low-poly: khối tròn ít cạnh (đạo cụ dựng hình qua ctx.THREE → bản THREE có lớp hình học "ít cạnh")
const T3 = (() => {
  if (!LK.facet) return THREE;
  const k = LK.facet, kh = Math.max(3, Math.round(k * 0.7));
  return {
    ...THREE,
    SphereGeometry: class extends THREE.SphereGeometry { constructor(r, w = 32, h = 16, ...a) { super(r, Math.min(w, k), Math.min(h, kh), ...a); } },
    CylinderGeometry: class extends THREE.CylinderGeometry { constructor(rt, rb, h, rs = 32, ...a) { super(rt, rb, h, Math.min(rs, k), ...a); } },
    ConeGeometry: class extends THREE.ConeGeometry { constructor(r, h, rs = 32, ...a) { super(r, h, Math.min(rs, k), ...a); } },
    TorusGeometry: class extends THREE.TorusGeometry { constructor(r, t, rs = 12, ts = 48, ...a) { super(r, t, Math.min(rs, kh), Math.min(ts, k * 2), ...a); } },
    CapsuleGeometry: class extends THREE.CapsuleGeometry { constructor(r, l, cs = 4, rs = 8) { super(r, l, Math.min(cs, 2), Math.min(rs, k)); } },
    CircleGeometry: class extends THREE.CircleGeometry { constructor(r, sg = 32, ...a) { super(r, Math.min(sg, k), ...a); } },
  };
})();
const flat = (color, o = {}) => new THREE.MeshBasicMaterial({ color: C(color), ...o });
// texture vẽ bằng code theo look: retro → lọc filter (bilinear | nearest), không mipmap (máy thời 90 lọc thô)
const lookTex = (canvas, rx = 1, ry = 1) => {
  const t = P.tex(canvas, rx, ry);
  if (LK.filter === 'nearest' || LK.filter === 'bilinear') {
    t.magFilter = t.minFilter = LK.filter === 'nearest' ? THREE.NearestFilter : THREE.LinearFilter;
    t.generateMipmaps = false; t.anisotropy = 1;
  }
  return t;
};
const glowTex = P.tex(P.radial('255,255,255', 1.0), 1, 1);
const MATS = {};
const mat = (k, o) => { const key = k + JSON.stringify(o || {}); return MATS[key] || (MATS[key] = toon(k, o)); };

// ---------- ink / normal-depth contract (giữ nguyên hợp đồng của kit) ----------
const ndMat = new THREE.ShaderMaterial({
  vertexShader: `varying vec3 vN; varying float vD; void main(){ vN = normalize(normalMatrix*normal); vec4 mv = modelViewMatrix*vec4(position,1.); vD = -mv.z; gl_Position = projectionMatrix*mv; }`,
  fragmentShader: `varying vec3 vN; varying float vD; void main(){ vec3 n = normalize(vN); if(!gl_FrontFacing) n = -n; gl_FragColor = vec4(n*.5+.5, vD); }`,
  side: THREE.DoubleSide,
});
const cardNd = (map) => new THREE.ShaderMaterial({
  uniforms: { map: { value: map } },
  vertexShader: `varying vec2 vUv; varying float vD; void main(){ vUv=uv; vec4 mv = modelViewMatrix*vec4(position,1.); vD=-mv.z; gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform sampler2D map; varying vec2 vUv; varying float vD; void main(){ if(texture2D(map,vUv).a<.5) discard; gl_FragColor=vec4(0.,0.,0.,vD); }`,
  side: THREE.DoubleSide,
});

// ---------- helpers ----------
const world = new THREE.Group(); scene.add(world);
const add = (geo, m, x = 0, y = 0, z = 0, parent = world, opts = {}) => {
  const me = new THREE.Mesh(geo, typeof m === 'string' ? mat(m) : m);
  me.position.set(x, y, z); me.castShadow = opts.cast ?? true; me.receiveShadow = opts.receive ?? true; parent.add(me); return me;
};
const group = (parent = world, x = 0, y = 0, z = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); return g; };
const tbox = (w, h, d, t = 1) => {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv;
  const dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) { const i = f * 4 + k; uv.setXY(i, uv.getX(i) * dims[f][0] / t, uv.getY(i) * dims[f][1] / t); }
  return g;
};
/** Chữ trong cảnh (diegetic): canvas → texture trên mặt phẳng, UV phẳng, đọc đúng chiều khi nhìn từ +Z cục bộ. */
const textTexture = (spec) => {
  const s = { text: '', font: JOB.font_family || 'sans-serif', weight: '', px: 160, color: C('ink_text') || '#000', bg: null,
    w: 1024, h: 256, align: 'center', outline: null, outlineW: 0, letter: 0, ...spec };
  const c = document.createElement('canvas'); c.width = s.w; c.height = s.h; const g = c.getContext('2d');
  if (s.bg) { g.fillStyle = C(s.bg); g.fillRect(0, 0, s.w, s.h); }
  // vừa khung: tự xuống dòng theo bề rộng rồi thu cỡ chữ tới khi tất cả dòng lọt (chữ trong cảnh không bao giờ bị cắt)
  let px = s.px, lines;
  const wrap = () => {
    const out = [];
    for (const para of String(s.text).split('\n')) {
      let cur = '';
      for (const w of para.split(' ')) {
        const tt = cur ? cur + ' ' + w : w;
        if (cur && g.measureText(tt).width > s.w * 0.92) { out.push(cur); cur = w; } else cur = tt;
      }
      out.push(cur);
    }
    return out;
  };
  for (;;) {
    g.font = `${s.weight} ${px}px "${s.font}"`; lines = wrap();
    const wide = Math.max(...lines.map((l) => g.measureText(l).width));
    if ((wide <= s.w * 0.94 && lines.length * px * 1.05 <= s.h * 0.92) || px < 24) break;
    px = Math.floor(px * 0.93);
  }
  g.textAlign = s.align; g.textBaseline = 'middle';
  const lh = px * 1.05, y0 = s.h / 2 - (lines.length - 1) * lh / 2;
  const x = s.align === 'center' ? s.w / 2 : s.align === 'left' ? px * 0.2 : s.w - px * 0.2;
  lines.forEach((ln, i) => {
    if (s.outline) { g.lineJoin = 'round'; g.strokeStyle = C(s.outline); g.lineWidth = s.outlineW; g.strokeText(ln, x, y0 + i * lh); }
    g.fillStyle = C(s.color); g.fillText(ln, x, y0 + i * lh);
  });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
};
const textPlane = (spec, w, h, parent = world, x = 0, y = 0, z = 0) => {
  const t = textTexture(spec);
  const m = new THREE.MeshBasicMaterial({ map: t, transparent: true, alphaTest: 0.05, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const me = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); me.position.set(x, y, z); me.castShadow = false; me.receiveShadow = false;
  me.userData.text = spec.text;
  me.userData.setText = (txt) => {           // chữ đổi theo frame (bộ đếm): chỉ vẽ lại khi chuỗi đổi
    if (txt === me.userData.text) return; me.userData.text = txt;
    const nt = textTexture({ ...spec, text: txt }); m.map.dispose(); m.map = nt; m.needsUpdate = true;
  };
  parent.add(me); return me;
};
const glow = (color, size, parent = world, x = 0, y = 0, z = 0, opacity = 1) => {
  const m = new THREE.MeshBasicMaterial({ map: glowTex, color: C(color), transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
  const me = new THREE.Mesh(new THREE.PlaneGeometry(size, size), m); me.position.set(x, y, z);
  me.userData.ndSkip = true; me.userData.billboard = true; me.renderOrder = 5; me.castShadow = false; parent.add(me); return me;
};

// ---------- lights: sân khấu tối — key + rim (accent) + hemi thấp ----------
const L = ST.lights || {};
const hemi = new THREE.HemisphereLight(C(L.hemi_sky || '#ffffff'), C(L.hemi_ground || '#ffffff'), L.hemi ?? 1.2); scene.add(hemi);
const key = new THREE.DirectionalLight(C(L.key_color || '#ffffff'), L.key ?? 2.2); key.castShadow = ST.shadows !== false;
key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0006; key.shadow.normalBias = 0.02; key.shadow.radius = 3;
scene.add(key); scene.add(key.target);
const rim = new THREE.DirectionalLight(C(L.rim_color || 'accent'), L.rim ?? 0.0); scene.add(rim); scene.add(rim.target);
// bầu trời darkmode (tuỳ chọn theo style: world.sky = {top, horizon, bottom}) → dome chuyển sắc màu tối
// giữ phong cách darkmode của kênh nhưng không bắt buộc đen tuyền #000 mọi pixel.
const SKY = ST.sky || null;
if (SKY && typeof SKY === 'object') {
  const skyMat = new THREE.ShaderMaterial({
    uniforms: {
      uTop: { value: new THREE.Color(C(SKY.top || '#070B16')) },
      uHor: { value: new THREE.Color(C(SKY.horizon || '#193052')) },
      uBot: { value: new THREE.Color(C(SKY.bottom || '#080D14')) },
    },
    vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
    fragmentShader: 'uniform vec3 uTop, uHor, uBot; varying vec3 vP; void main(){ float h = vP.y; vec3 c = h >= 0. ? mix(uHor, uTop, pow(clamp(h, 0., 1.), 0.65)) : mix(uHor, uBot, clamp(-h * 2.5, 0., 1.)); gl_FragColor = vec4(c, 1.); }',
    side: THREE.BackSide, depthWrite: false, fog: false,
  });
  const skyDome = new THREE.Mesh(new THREE.SphereGeometry(180, 20, 12), skyMat);
  skyDome.userData.ndSkip = true; skyDome.renderOrder = -10;
  scene.add(skyDome);
}
scene.fog = new THREE.Fog(C(ST.fog || ST.bg || '#000000'), LK.fog_near ?? ST.fog_near ?? 30, LK.fog_far ?? ST.fog_far ?? 120);
if (LK.shadows === false) { renderer.shadowMap.enabled = false; key.castShadow = false; }
// env map "studio" dựng bằng code (softbox trắng + dải rim màu accent): kim loại/nhựa/kính cần thứ để phản chiếu
// trên sân khấu đen. Nền vẫn đen (scene.background = null).
if ((LK.env ?? 0) > 0 && (LK.mat === 'standard' || LK.mat === 'physical')) {
  const es = new THREE.Scene();
  es.add(new THREE.Mesh(new THREE.BoxGeometry(12, 12, 12), new THREE.MeshBasicMaterial({ color: 0x030303, side: THREE.BackSide })));
  const ew = LK.env_wide ?? 1;          // kim loại: softbox to hơn → phản chiếu rộng, vật không chìm vào nền
  const panel = (w, h, col, k, pos) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w * ew, h * ew), new THREE.MeshBasicMaterial({ color: new THREE.Color(col).multiplyScalar(k), side: THREE.DoubleSide }));
    m.position.set(...pos); m.lookAt(0, 0, 0); es.add(m);
  };
  panel(4.8, 3.2, '#fff6eb', 2.8, [-3.6, 3.4, 3.4]);                // softbox chính ấm (trước-trái-trên kiểu Fern/Blender)
  panel(6.4, 1.4, '#eef4ff', 1.25, [0, 5.6, 0.4]);                  // đèn trần studio rộng
  panel(1.2, 7.2, C(L.rim_color || 'accent'), 3.2, [4.2, 1.2, -3.5]); // dải rim màu accent phía sau
  panel(3.2, 2.2, '#d8e6ff', 0.65, [3.2, 0.7, 4.0]);                // fill lạnh bên phải tạo tương phản ấm/lạnh
  panel(5.0, 5.0, '#18202c', 0.45, [0, -4.5, 0]);                   // phản xạ sàn mềm giữ chi tiết gầm khối 3D
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(es, 0.025).texture; pm.dispose();
}

// ---------- cards (nhân vật 2D trong không gian 3D — cơ chế của kit) ----------
const DW = 800, CW = 1600, CH = 2000, CM = 2.25; // thiết kế 800×1000 (rộng hơn kit 600 để tay duỗi không bị cắt)
const cardGeo = new THREE.PlaneGeometry(CM * DW / 1000, CM); cardGeo.translate(0, CM / 2 - CM * 0.025, 0);
const blobTex = P.tex(P.radial('0,0,0', 0.7));
class Card {
  constructor() {
    this.c = document.createElement('canvas'); this.c.width = CW; this.c.height = CH; this.g = this.c.getContext('2d');
    this.t = new THREE.CanvasTexture(this.c); this.t.colorSpace = THREE.SRGBColorSpace; this.t.anisotropy = 4;
    this.mat = new THREE.MeshBasicMaterial({ map: this.t, transparent: true, alphaTest: 0.02, side: THREE.DoubleSide, fog: false });
    this.mesh = new THREE.Mesh(cardGeo, this.mat); this.mesh.userData.nd = cardNd(this.t); this.mesh.castShadow = true;
    this.mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: this.t, alphaTest: 0.5 });
    this.blob = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false, opacity: 0.6 }));
    this.blob.rotation.x = -Math.PI / 2; this.blob.userData.ndSkip = true; this.blob.renderOrder = 1;
    scene.add(this.mesh); scene.add(this.blob); this.key = ''; this.mesh.visible = this.blob.visible = false;
  }
  draw(key, fn) {
    if (key === this.key) return; this.key = key;
    const g = this.g; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, CW, CH); g.setTransform(CW / DW, 0, 0, CH / 1000, 0, 0);
    fn(g); this.t.needsUpdate = true;
  }
}
const cards = []; const getCard = (i) => cards[i] || (cards[i] = new Card());
function drawActors(list) {
  cards.forEach((c) => { c.mesh.visible = c.blob.visible = false; });
  list.forEach((a, i) => {
    const c = getCard(i); c.draw(a.key, a.draw);
    c.mesh.visible = true; c.mesh.position.set(a.x, a.y, a.z);
    const s = a.s || 1; c.mesh.scale.set(s * (a.flip ? -1 : 1), s * (a.sy || 1), s);
    c.mesh.rotation.set(0, Math.atan2(camera.position.x - a.x, camera.position.z - a.z) + (a.yaw || 0), a.roll || 0);
    c.mat.opacity = a.alpha ?? 1; c.mesh.renderOrder = a.order || 2;
    if (a.blob !== false && a.ground !== undefined) { c.blob.visible = true; c.blob.position.set(a.x, a.ground + 0.004, a.z); c.blob.scale.set(0.9 * s, 0.35 * s, 1); }
  });
}

// ---------- render targets & post ----------
// retro: ảnh màu đầy đủ chỉ nhận ảnh phóng + chữ (nhiều lượt vẽ) → không MSAA (three huỷ nội dung bộ đệm MSAA sau mỗi lượt)
const RETRO_ON = (LK.res_div || 1) > 1 || Boolean(LK.color_bits);
const rtColor = new THREE.WebGLRenderTarget(W, H, { samples: RETRO_ON ? 0 : 4, type: THREE.HalfFloatType });
const rtNd = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
const rtInk = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
const fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), fsGeo = new THREE.PlaneGeometry(2, 2);
const fs = (m) => { const s = new THREE.Scene(); s.add(new THREE.Mesh(fsGeo, m)); return s; };
const INK = ST.ink || {};
const inkU = {
  col: { value: rtColor.texture }, nd: { value: rtNd.texture }, res: { value: new THREE.Vector2(W, H) }, px: { value: INK.px ?? 3.2 },
  inkCol: { value: new THREE.Color(C(INK.color || '#000000')) }, rimCol: { value: new THREE.Color(C(INK.rim || '#ffffff')) },
  rimPx: { value: INK.rim_px ?? 0 }, sat: { value: ST.grade?.sat ?? 1.0 }, vig: { value: ST.grade?.vig ?? 0.0 }, flash: { value: 0 },
  creaseK: { value: INK.crease ?? 0.9 },
  tm: { value: LK.tm ? 1 : 0 }, expo: { value: LK.exposure ?? 1 }, bloom: { value: LK.bloom ?? 0 },
  bloomTh: { value: LK.bloom_th ?? 0.6 }, grain: { value: LK.grain ?? 0 }, seed: { value: 0 },
  grainRes: { value: new THREE.Vector2(W, H) }, grainQ: { value: 0 },   // retro: hạt theo lưới pixel thấp (grainQ = 1)
};
if (LK.ink_px !== undefined) inkU.px.value = LK.ink_px;
if (inkU.bloom.value > 0) {             // bloom = trung bình các mức mip của ảnh màu → cần mipmap của rtColor
  rtColor.texture.generateMipmaps = true; rtColor.texture.minFilter = THREE.LinearMipmapLinearFilter;
}
const inkScene = fs(new THREE.ShaderMaterial({ uniforms: inkU, vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }`,
  fragmentShader: `uniform sampler2D col, nd; uniform vec2 res, grainRes; uniform float px, sat, vig, flash, rimPx, creaseK, tm, expo, bloom, bloomTh, grain, seed, grainQ; uniform vec3 inkCol, rimCol; varying vec2 vUv;
  vec3 aces(vec3 x){ x *= expo; return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14), 0., 1.); }
  vec3 glowAt(vec2 uv){ vec3 b = vec3(0.); float w = 0.;
    for (int i=3;i<7;i++){ float l = float(i); vec3 s = textureLod(col, uv, l).rgb; float k = 1./(l-1.5);
      b += max(s - vec3(bloomTh), 0.)*k; w += k; }
    return b/w; }
  float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + seed*1.618) * 43758.5453); }
  float edgeAt(vec2 uv, float r){
    vec4 c = texture2D(nd, uv); if (c.a <= 0.) return 0.; if (dot(c.rgb,c.rgb) < .01) return 0.; float d = c.a; vec3 n = c.rgb*2.-1.;
    float e = 0.; float rr = r * clamp(4./d, .62, 1.35);
    for (int i=0;i<16;i++){ float a = float(i)*.785398 + (i>7 ? .39 : 0.); float k = i>7 ? .5 : 1.;
      vec2 o = vec2(cos(a), sin(a))*rr*k/res; vec4 s = texture2D(nd, uv+o);
      float ds = s.a; bool card = dot(s.rgb,s.rgb) < .01;
      if (card && ds > 0.) continue;                 // card nhân vật: tự có nét, world ink bỏ qua
      if (card) ds = 1e4;                             // nền đen = rất xa → viền ngoài
      vec3 ns = s.rgb*2.-1.;
      e = max(e, smoothstep(.006, .02, (ds - d)/d));
      if (!card && abs(ds-d)/d < .06) e = max(e, smoothstep(.88, .72, dot(n, ns)) * creaseK);
    }
    return e;
  }
  float rimAt(vec2 uv, float r){                      // viền sáng NGOÀI vật (kiểu sticker như clip Flow)
    if (r < .5) return 0.; vec4 c = texture2D(nd, uv); if (c.a > 0.) return 0.;
    float h = 0.;
    for (int i=0;i<16;i++){ float a = float(i)*.392699; vec2 o = vec2(cos(a), sin(a))*r/res; vec4 s = texture2D(nd, uv+o);
      if (s.a > 0. && dot(s.rgb,s.rgb) >= .01) h = 1.; }
    return h;
  }
  void main(){
    vec3 c = texture2D(col, vUv).rgb;
    if (bloom > 0.) c += glowAt(vUv)*bloom*2.5;
    if (tm > .5) c = aces(c);
    float e = px > .05 ? edgeAt(vUv, px) : 0.;
    c = mix(c, inkCol, e);
    c = mix(c, rimCol, rimAt(vUv, rimPx));
    if (flash < -0.5) c = vec3(e);
    float l = dot(c, vec3(.299,.587,.114)); c = mix(vec3(l), c, sat);
    vec2 q = vUv-.5; c *= 1. - vig*dot(q*vec2(1.,.75), q*vec2(1.,.75))*2.2;
    c = mix(c, vec3(1.), max(flash, 0.));
    if (grain > 0.) c *= 1. + (hash(grainQ > .5 ? floor(vUv*grainRes) + .5 : vUv*res) - .5)*grain*5.;   // hạt nhân theo độ sáng: nền đen vẫn đen tuyền
    gl_FragColor = vec4(c,1.); }` }));
const dofU = { src: { value: rtInk.texture }, nd: { value: rtNd.texture }, res: { value: new THREE.Vector2(W, H) }, focus: { value: 5 }, cinf: { value: 0 }, near: { value: 1 } };
const dofScene = fs(new THREE.ShaderMaterial({ uniforms: dofU, vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }`,
  fragmentShader: `uniform sampler2D src, nd; uniform vec2 res; uniform float focus, cinf, near; varying vec2 vUv;
  float coc(vec2 uv){ float d = texture2D(nd, uv).a; if (d <= 0.) d = 400.; float k = 1. - focus/d; return k > 0. ? cinf*k : min(-k*cinf*near, cinf*1.4); }
  void main(){
    float c0 = coc(vUv);
    if (cinf < .5 || c0 < .6) { gl_FragColor = linearToOutputTexel(vec4(texture2D(src, vUv).rgb, 1.)); return; }
    vec3 acc = vec3(0.); float wsum = 0.;
    for (int i=0;i<48;i++){ float fi = float(i); float r = sqrt((fi+.5)/48.); float a = fi*2.39996;
      vec2 o = vec2(cos(a), sin(a))*r*c0/res; float cs = coc(vUv+o);
      float w = smoothstep(r*c0-1.5, r*c0+.5, cs + .5);
      acc += texture2D(src, vUv+o).rgb*w; wsum += w; }
    gl_FragColor = linearToOutputTexel(vec4(acc/max(wsum,1e-3), 1.)); }` }));

// ---------- hậu kỳ retro (look có res_div > 1 hoặc color_bits — retro90/psx) ----------
// cảnh → rtLow (1/res_div) → lượng tử: mã hoá sRGB, color_bits bit/kênh + Bayer 4×4 theo pixel THẤP (đen tuyền không dither
// → nền vẫn #000) → rtQ (lọc bilinear | nearest) → phóng lên rtColor (+ vi_blur kiểu bộ lọc VI của N64) → chữ trong cảnh
// vẽ lại ở độ phân giải đầy đủ (text_hd: vật khác chỉ ghi depth để che đúng) → ink/grade/DOF như mọi look.
const RETRO = RETRO_ON ? (() => {
  const div = Math.max(1, LK.res_div || 1), lw = Math.max(16, Math.round(W / div)), lh = Math.max(16, Math.round(H / div));
  const near = LK.upscale === 'nearest', filt = near ? THREE.NearestFilter : THREE.LinearFilter;
  const low = new THREE.WebGLRenderTarget(lw, lh, { samples: LK.aa ? 4 : 0, type: THREE.HalfFloatType });
  const q = new THREE.WebGLRenderTarget(lw, lh, { type: THREE.HalfFloatType, depthBuffer: false, minFilter: filt, magFilter: filt });
  const vs = `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }`;
  const qScene = fs(new THREE.ShaderMaterial({ uniforms: { src: { value: low.texture }, bits: { value: LK.color_bits || 8 }, dither: { value: LK.dither ?? 0 } },
    vertexShader: vs, depthTest: false, depthWrite: false,
    fragmentShader: `uniform sampler2D src; uniform float bits, dither; varying vec2 vUv;
    const float BY[16] = float[16](0.,8.,2.,10.,12.,4.,14.,6.,3.,11.,1.,9.,15.,7.,13.,5.);
    vec3 enc(vec3 c){ return mix(pow(c, vec3(.41666))*1.055 - .055, c*12.92, vec3(lessThanEqual(c, vec3(.0031308)))); }
    vec3 dec(vec3 c){ return mix(pow((c + .055)/1.055, vec3(2.4)), c/12.92, vec3(lessThanEqual(c, vec3(.04045)))); }
    void main(){
      vec3 c = clamp(enc(max(texture2D(src, vUv).rgb, 0.)), 0., 1.);
      float lv = exp2(bits) - 1.; ivec2 p = ivec2(mod(gl_FragCoord.xy, 4.));
      float d = (BY[p.x + p.y*4] + .5)/16. - .5, amt = dither * smoothstep(0., 2./lv, max(c.r, max(c.g, c.b)));
      gl_FragColor = vec4(dec(clamp(floor(c*lv + .5 + d*amt)/lv, 0., 1.)), 1.); }` }));
  const upScene = fs(new THREE.ShaderMaterial({ uniforms: { src: { value: q.texture }, texel: { value: new THREE.Vector2(1 / lw, 1 / lh) },
    blur: { value: near ? 0 : (LK.vi_blur ?? 0) } }, vertexShader: vs, depthTest: false, depthWrite: false,
    fragmentShader: `uniform sampler2D src; uniform vec2 texel; uniform float blur; varying vec2 vUv;
    void main(){ vec3 c = texture2D(src, vUv).rgb;
      if (blur > 0.) { vec2 o = texel*.5; vec3 s = texture2D(src, vUv+o).rgb + texture2D(src, vUv-o).rgb
        + texture2D(src, vUv+vec2(o.x,-o.y)).rgb + texture2D(src, vUv+vec2(-o.x,o.y)).rgb; c = mix(c, s*.25, blur); }
      gl_FragColor = vec4(c, 1.); }` }));
  if (GU) GU.uSnapRes.value.set(lw / Math.max(0.25, LK.wobble || 1), lh / Math.max(0.25, LK.wobble || 1));
  inkU.grainRes.value.set(lw, lh); inkU.grainQ.value = 1;
  return { lw, lh, low, q, qScene, upScene, textHd: LK.text_hd !== false, depthOnly: new THREE.MeshBasicMaterial({ colorWrite: false }) };
})() : null;
const isText = (o) => o.userData.text !== undefined;
/** text_hd: chữ trong cảnh (mesh có userData.text) vẽ đè ở độ phân giải đầy đủ; vật đục khác chỉ ghi depth (che đúng). */
const textHdPass = () => {
  let n = 0; scene.traverse((o) => { if (o.isMesh && o.visible && isText(o)) n++; });
  if (!n) return;
  const swap = [];
  scene.traverse((o) => {
    if (!o.isMesh || isText(o)) return;
    swap.push([o, o.material, o.visible]);
    if (o.material.transparent || o.userData.billboard || o.userData.ndSkip) o.visible = false; else o.material = RETRO.depthOnly;
  });
  const sm = renderer.shadowMap.autoUpdate; renderer.shadowMap.autoUpdate = false; renderer.autoClear = false;
  renderer.clearDepth(); renderer.render(scene, camera);
  renderer.autoClear = true; renderer.shadowMap.autoUpdate = sm;
  for (const [o, m, v] of swap) { o.material = m; o.visible = v; }
};

// ---------- hậu kỳ thêm bằng pmndrs/postprocessing (vendor/postprocessing, Zlib) — TUỲ CHỌN theo style ----------
// world.look3d.post: {smaa: true | "ultra" (khử răng cưa nét ink), ca: 0.0015 (lệch màu ống kính, mép khung),
//                     bloom: {intensity, threshold, radius} (bloom mipmap mềm hơn bloom theo mip của ink pass)}
// Mọi hiệu ứng ở đây tất định (không nhiễu theo thời gian).
// Mặc định {smaa: true} cho MỌI look (mép nét ink mượt hơn, nền không đổi); style tắt bằng "post": false.
const POST = LK.post === false ? null : { smaa: true, ...(typeof LK.post === 'object' ? LK.post : {}) };
let PPC = null;
if (POST) {
  window.stage = 'post';
  const PP = await import('../../vendor/postprocessing/postprocessing.js');
  PPC = new PP.EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType, depthBuffer: false });
  if (POST.smaa) {
    const smaa = new PP.SMAAEffect({ preset: POST.smaa === 'ultra' ? PP.SMAAPreset.ULTRA : PP.SMAAPreset.HIGH,
      edgeDetectionMode: PP.EdgeDetectionMode.COLOR });
    PPC.addPass(new PP.EffectPass(camera, smaa));
    // ảnh tra cứu SMAA nạp bất đồng bộ → chờ xong rồi mới "ready", nếu không frame đầu mỗi worker sẽ khác frame sau
    for (let i = 0; i < 200 && !(smaa.weightsMaterial.searchTexture && smaa.weightsMaterial.areaTexture); i++) await new Promise((r) => setTimeout(r, 10));
  }
  const fx = [];
  if (POST.bloom) fx.push(new PP.BloomEffect({ mipmapBlur: true, intensity: POST.bloom.intensity ?? 0.6,
    luminanceThreshold: POST.bloom.threshold ?? 0.8, luminanceSmoothing: 0.15, radius: POST.bloom.radius ?? 0.4 }));
  if (POST.ca) fx.push(new PP.ChromaticAberrationEffect({ offset: new THREE.Vector2(POST.ca, POST.ca * 0.6),
    radialModulation: true, modulationOffset: 0.3 }));
  if (fx.length) PPC.addPass(new PP.EffectPass(camera, ...fx));
  PPC.setSize(W, H, false);
}

const swapForNd = (on) => {
  scene.traverse((o) => {
    if (!o.isMesh) return;
    if (on) {
      o.userData.mat0 = o.material;
      if (o.userData.ndSkip || !o.visible) { o.userData.vis0 = o.visible; o.visible = false; return; }
      o.material = o.userData.nd || ndMat;
    } else {
      o.material = o.userData.mat0; if (o.userData.vis0 !== undefined) { o.visible = o.userData.vis0; delete o.userData.vis0; }
    }
  });
};

// ---------- cảnh ----------
const ctx = { THREE: T3, MO, P, CAST, PROPS, scene, world, camera, add, group, tbox, mat, toon, flat, C, glow, textPlane, textTexture,
  job: JOB, params: JOB.params || {}, N: JOB.frames, fps: JOB.fps || 30, rx, key, rim, hemi, look3d: LK, RAPIER: null,
  lookTex, texPx: LK.tex_px ?? 256 };
if (needsPhysics(JOB.params)) { window.stage = 'physics'; ctx.RAPIER = await loadRapier(); }   // Rapier chỉ nạp khi cảnh cần
window.stage = 'scene';
const mod = await import(`./scenes/${JOB.scene}.js`);
const S = await mod.build(ctx, JOB.params || {});
// WP-X: hậu kỳ 3D theo look 2D (pixel/halftone/misregister/paper) + lớp overlay 2D bám prop 3D trong CÙNG trang
const POST2D = make3DPost2D(LK, ST, W, H);
const OVERLAY2D = S.overlay2d ? makeOverlay2D(ctx, S.overlay2d, W, H) : null;
let compCanvas = null, compCtx = null;
if (POST2D || OVERLAY2D) {
  compCanvas = document.createElement('canvas'); compCanvas.width = W; compCanvas.height = H;
  compCanvas.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:2;';
  document.body.appendChild(compCanvas);
  compCtx = compCanvas.getContext('2d');
}
window.outCanvas = compCanvas || canvas;

window.meta = { cues: S.cues || [], texts: S.texts || [], frames: JOB.frames, scene: JOB.scene, physics: S.physics || null,
  hybrid: { post2d: POST2D ? POST2D.info : null, overlay2d: Boolean(OVERLAY2D) } };
window.renderFrame = (f) => {
  const st = S.frame(f) || {};
  const c = st.cam;
  camera.position.set(...c.pos); camera.up.set(0, 1, 0); camera.lookAt(...c.look); camera.rotateZ(rx(c.roll || 0));
  camera.fov = c.fov; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  const focus = new THREE.Vector3(...(st.shadowAt || c.look));
  const kd = st.keyDir || L.key_dir || [-0.5, 1.0, 0.8], rd = st.rimDir || L.rim_dir || [0.3, 0.6, -1.0];
  key.position.copy(focus).add(new THREE.Vector3(...kd).normalize().multiplyScalar(20)); key.target.position.copy(focus);
  rim.position.copy(focus).add(new THREE.Vector3(...rd).normalize().multiplyScalar(20)); rim.target.position.copy(focus);
  const sc = key.shadow.camera, ext = st.shadowExt || 4; sc.left = -ext; sc.right = ext; sc.top = ext; sc.bottom = -ext; sc.near = 1; sc.far = 60; sc.updateProjectionMatrix();
  // sau khi đặt camera CỦA FRAME NÀY: billboard + nhóm "facing" (cạnh kính vẽ bằng ống) quay về camera.
  // (Gọi trong scene.frame() thì dùng camera của frame trước → frame đầu mỗi worker sai.)
  const wp = new THREE.Vector3();
  scene.traverse((o) => {
    if (o.userData.billboard) o.quaternion.copy(camera.quaternion);
    if (o.userData.facing) {
      o.rotation.y = 0; o.updateMatrixWorld(true); o.getWorldPosition(wp);
      const pq = new THREE.Quaternion(); if (o.parent) o.parent.getWorldQuaternion(pq);
      const yawParent = new THREE.Euler().setFromQuaternion(pq, 'YXZ').y;
      o.rotation.y = Math.atan2(camera.position.x - wp.x, camera.position.z - wp.z) - yawParent;
    }
  });
  drawActors(st.actors || []);
  if (GU) {                                   // đèn của vật liệu Gouraud: hướng trong hệ camera CỦA FRAME NÀY
    const vm = camera.matrixWorldInverse, amb = LK.ambient ?? 1;
    GU.uKeyDir.value.set(...kd).normalize().transformDirection(vm);
    GU.uRimDir.value.set(...rd).normalize().transformDirection(vm);
    GU.uUp.value.set(0, 1, 0).transformDirection(vm);
    GU.uKeyCol.value.copy(key.color).multiplyScalar(key.intensity); GU.uRimCol.value.copy(rim.color).multiplyScalar(rim.intensity);
    GU.uSky.value.copy(hemi.color).multiplyScalar(hemi.intensity * amb); GU.uGround.value.copy(hemi.groundColor).multiplyScalar(hemi.intensity * amb);
  }
  const bgCol = C(ST.bg || '#000000');
  if (RETRO) {
    const hid = [];
    if (RETRO.textHd) scene.traverse((o) => { if (o.isMesh && o.visible && isText(o)) { hid.push(o); o.visible = false; } });
    // đặt renderTarget TRƯỚC setClearColor để Three.js (r160) xoá buffer HalfFloat ở không gian tuyến tính, không bị nhân sRGB 2 lần khi EffectComposer tắt autoClear
    renderer.setRenderTarget(RETRO.low); renderer.setClearColor(bgCol, 1); renderer.clear(); renderer.render(scene, camera);
    hid.forEach((o) => { o.visible = true; });
    renderer.setRenderTarget(RETRO.q); renderer.render(RETRO.qScene, fsCam);
    renderer.setRenderTarget(rtColor); renderer.setClearColor(0x000000, 1); renderer.clear(); renderer.render(RETRO.upScene, fsCam);
    if (RETRO.textHd && hid.length) textHdPass();
  } else {
    renderer.setRenderTarget(rtColor); renderer.setClearColor(bgCol, 1); renderer.clear(); renderer.render(scene, camera);
  }
  const D = st.dof || { focus: 5, cinf: 0 };
  // pass normal/depth chỉ khi có người đọc (nét ink, viền rim, DOF) — look không viền (retro, chrome…) bỏ qua, ảnh y hệt
  if (inkU.px.value > 0.05 || inkU.rimPx.value >= 0.5 || (D.cinf ?? 0) >= 0.5 || window.DEBUG_E) {
    const fog = scene.fog; scene.fog = null; const sm = renderer.shadowMap.enabled; renderer.shadowMap.enabled = false; renderer.shadowMap.autoUpdate = false;
    swapForNd(true); renderer.setRenderTarget(rtNd); renderer.setClearColor(0x000000, 0); renderer.clear(); renderer.render(scene, camera); swapForNd(false);
    scene.fog = fog; renderer.shadowMap.enabled = sm; renderer.shadowMap.autoUpdate = true;
  }
  inkU.flash.value = window.DEBUG_E ? -1 : (st.flash || 0); inkU.seed.value = (f % 97) + 1;
  renderer.setRenderTarget(rtInk); renderer.render(inkScene, fsCam);
  dofU.focus.value = D.focus; dofU.cinf.value = D.cinf; dofU.near.value = D.near ?? 1;
  if (PPC) { renderer.setRenderTarget(PPC.inputBuffer); renderer.render(dofScene, fsCam); PPC.render(1 / (JOB.fps || 30)); }
  else { renderer.setRenderTarget(null); renderer.render(dofScene, fsCam); }
  if (compCtx) {
    compCtx.setTransform(1, 0, 0, 1, 0, 0);
    compCtx.clearRect(0, 0, W, H);
    if (OVERLAY2D) {
      const back = OVERLAY2D.draw(f, JOB.frames, S.objectOf || (() => null), camera, THREE, 'back');
      compCtx.drawImage(back, 0, 0);
    }
    const src = POST2D ? POST2D.apply(canvas) : canvas;
    compCtx.drawImage(src, 0, 0);
    if (OVERLAY2D) {
      const front = OVERLAY2D.draw(f, JOB.frames, S.objectOf || (() => null), camera, THREE, 'front');
      compCtx.drawImage(front, 0, 0);
    }
  }
  return true;
};
/** Khung bao trên màn hình của mọi chữ trong cảnh (mesh có userData.text + overlay2d) sau renderFrame — cho QA OCR. */
window.textBoxes = () => {
  const out = OVERLAY2D ? [...OVERLAY2D.textBoxes()] : [], v = new THREE.Vector3();
  scene.traverse((o) => {
    if (!o.isMesh || o.userData.text === undefined) return;
    let vis = true; for (let p = o; p; p = p.parent) if (!p.visible) vis = false;
    if (!vis) return;
    o.geometry.computeBoundingBox(); const b = o.geometry.boundingBox; let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) {
      v.set(x, y, z).applyMatrix4(o.matrixWorld).project(camera);
      const px = (v.x + 1) / 2 * W, py = (1 - v.y) / 2 * H; x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py);
    }
    const img = o.material && o.material.map && o.material.map.image;          // texture phẳng (canvas) của chữ
    const tex = img && img.toDataURL ? img.toDataURL('image/png') : null;
    if (x1 > 0 && y1 > 0 && x0 < W && y0 < H) out.push({ text: String(o.userData.text), box: [x0, y0, x1, y1], tex });
  });
  return out;
};
window.glInfo = (() => { const gl = renderer.getContext(); const d = gl.getExtension('WEBGL_debug_renderer_info'); return d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); })();
window.ready = true;
