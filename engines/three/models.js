// Mô hình glTF/GLB của KHO THƯ VIỆN (assets/lib/3d, index config/assets3d.json — vidlib/assets3d.py) cho cảnh `stage`:
//   prop {type: "model:<tên>", anim, anim_speed, anim_offset, anim_blend, anim_loop, h | size, colors, color, mix, keys}
// Python đổi tên → model_url + model{h, anims, hide, colors…} lúc dựng job (engine không quét đĩa).
// - Nạp MỘT lần trước `ready` (top-level await khi module được import: đọc job, nạp mọi model_url) → build() vẫn đồng bộ.
// - Clone đúng cách: có xương → SkeletonUtils.clone (mỗi bản một bộ xương); không → clone(true).
// - Chuẩn hoá: cao h (m, mặc định theo index) hoặc size = cạnh lớn nhất; đáy ở y = 0, tâm x/z ở gốc.
// - Chất liệu theo look 3D hiện tại: mọi vật liệu gốc → ctx.toon(màu, {map…}) (toon/clay/…/retro90/psx tự áp);
//   màu: "palette" = mỗi màu gốc (cả từng điểm ảnh texture atlas) kéo về màu style gần nhất (OKLab, mix/mix_l) ·
//   "keep" · tên vai/hex = tô một màu giữ sáng tối. Texture thu về tex_px của look (retro: 128/64) + lọc theo look.
// - Animation tất định: mỗi frame đặt action.time = hàm thuần của f rồi mixer.update(0) (không cộng dồn delta);
//   đổi anim bằng keys [{u, anim}] — trộn chéo anim_blend giây, cũng là hàm thuần của f.
// - Shader tự viết (gouraud của retro90/psx, nd của nét ink) được vá thêm khối skinning của three → nhân vật có xương
//   không bị kẹt ở tư thế T.

const CACHE = new Map();           // url → gltf
let SKU = null;                    // SkeletonUtils (nạp khi có mô hình có xương)

/** Chuẩn hoá tên clip — GIỐNG vidlib/assets3d.anim_norm (test đối chiếu). */
export const animNorm = (s) => String(s ?? '').toLowerCase().split('|').pop().replace(/[^a-z0-9]/g, '');
/** Chọn clip: đúng tên → chuẩn hoá bằng → bắt đầu bằng → chứa (GIỐNG assets3d.anim_match). */
export function pickName(names, q) {
  if (q === undefined || q === null || q === '' || q === true) return names[0] ?? null;
  const q0 = String(q), qn = animNorm(q);
  const tests = [(n) => n === q0, (n) => animNorm(n) === qn, (n) => animNorm(n).startsWith(qn), (n) => animNorm(n).includes(qn)];
  for (const t of tests) for (const n of names) if (qn && t(n)) return n;
  return null;
}

const urlsIn = (o, out = []) => {
  if (Array.isArray(o)) { o.forEach((v) => urlsIn(v, out)); return out; }
  if (!o || typeof o !== 'object') return out;
  if (typeof o.model_url === 'string') out.push(o.model_url);
  for (const v of Object.values(o)) if (v && typeof v === 'object') urlsIn(v, out);
  return out;
};

/** Nạp mọi mô hình mà job cần (trình duyệt). Node (test harness) / job không có mô hình: không làm gì. */
export async function preload(job) {
  const urls = [...new Set(urlsIn(job && job.params))].filter((u) => !CACHE.has(u));
  if (!urls.length) return 0;
  const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
  if (!SKU) SKU = await import('three/addons/utils/SkeletonUtils.js');
  const loader = new GLTFLoader();
  for (const u of urls) {                          // tuần tự: thứ tự nạp cố định (texture/uuid không phụ thuộc mạng)
    try { CACHE.set(u, await loader.loadAsync(u)); } catch (e) { throw new Error(`model ${u}: ${e && e.message ? e.message : e}`); }
  }
  return urls.length;
}
if (typeof window !== 'undefined' && typeof location !== 'undefined') {
  const jq = new URLSearchParams(location.search).get('job');
  if (jq) {
    const st0 = window.stage;
    const job = await (await fetch(jq, { cache: 'no-store' })).json();
    if (urlsIn(job.params).length) { window.stage = 'models'; await preload(job); window.stage = st0; }
  }
}

// ------------------------------------------------------------------------------------------------- màu (OKLab)
const s2l = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const l2s = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);
const toLab = (r, g, b) => {
  r = s2l(r); g = s2l(g); b = s2l(b);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s, 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s];
};
const fromLab = (L, a, b) => {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const c = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s];
  return c.map((v) => Math.min(1, Math.max(0, l2s(Math.min(1, Math.max(0, v))))));
};
const hexRgb = (h) => { const s = String(h).replace('#', ''); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) / 255); };
const rgbHex = (c) => '#' + c.map((v) => Math.round(v * 255).toString(16).padStart(2, '0')).join('');

/** (r,g,b 0..1 sRGB) → (r,g,b) theo chế độ màu. pal = [{lab}] màu style; tint = lab của một màu. */
function mapper(mode, pal, tint, mix, mixL) {
  if (mode === 'keep' || (!tint && !pal.length)) return null;
  const f = (r, g, b) => {
    const [L, A, B] = toLab(r, g, b);
    let t = tint;
    if (!t) {
      let best = 1e9;
      for (const p of pal) {               // khoảng cách OKLab, nhẹ tay với độ sáng → giữ đúng sắc (xanh lá → màu lá)
        const d = 0.35 * (L - p[0]) ** 2 + (A - p[1]) ** 2 + (B - p[2]) ** 2;
        if (d < best) { best = d; t = p; }
      }
    }
    return fromLab(L + (t[0] - L) * mixL, A + (t[1] - A) * mix, B + (t[2] - B) * mix);
  };
  f.key = JSON.stringify([tint, pal, mix, mixL]);
  return f;
}

const TEX = new Map();               // texture đã đổi màu, dùng chung giữa các mô hình cùng atlas (cùng nội dung + cùng màu)
/** Texture → CanvasTexture đã đổi màu + thu nhỏ về texPx (hộp lọc tự viết → tất định, không phụ thuộc bộ resample). */
function lookTexture(ctx, tex, map, cache) {
  if (cache.has(tex.uuid)) return cache.get(tex.uuid);
  const THREE = ctx.THREE, LK = ctx.look3d || {}, img = tex.image;
  if (!img || typeof document === 'undefined') return tex;
  const w0 = img.width, h0 = img.height;
  const cv = document.createElement('canvas'); cv.width = w0; cv.height = h0;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.drawImage(img, 0, 0);
  let src = g.getImageData(0, 0, w0, h0);
  let hsh = 2166136261;                               // vân tay nội dung (FNV trên mẫu điểm ảnh) → khoá dùng chung
  for (let i = 0; i < src.data.length; i += 4093) hsh = Math.imul(hsh ^ src.data[i], 16777619) >>> 0;
  const key = `${w0}x${h0}:${hsh}:${map ? map.key : 'keep'}:${tex.flipY}:${tex.wrapS}:${tex.wrapT}`;
  if (TEX.has(key)) { cache.set(tex.uuid, TEX.get(key)); return TEX.get(key); }
  const lim = LK.tex_px || 1024, k = Math.max(1, 2 ** Math.ceil(Math.log2(Math.max(w0, h0) / lim)));
  let w = w0, h = h0;
  if (k > 1) {                                       // hộp k×k
    w = Math.max(1, Math.floor(w0 / k)); h = Math.max(1, Math.floor(h0 / k));
    const out = new ImageData(w, h), s = src.data, o = out.data;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let r = 0, gg = 0, b = 0, a = 0;
      for (let j = 0; j < k; j++) for (let i = 0; i < k; i++) { const q = ((y * k + j) * w0 + x * k + i) * 4; r += s[q]; gg += s[q + 1]; b += s[q + 2]; a += s[q + 3]; }
      const p = (y * w + x) * 4, n = k * k; o[p] = r / n; o[p + 1] = gg / n; o[p + 2] = b / n; o[p + 3] = a / n;
    }
    src = out;
  }
  if (map) {                                         // đổi màu từng điểm ảnh (cache theo màu lượng tử 6 bit/kênh)
    const d = src.data, memo = new Map();
    for (let i = 0; i < d.length; i += 4) {
      const kk = ((d[i] >> 2) << 12) | ((d[i + 1] >> 2) << 6) | (d[i + 2] >> 2);
      let c = memo.get(kk);
      if (!c) { c = map(d[i] / 255, d[i + 1] / 255, d[i + 2] / 255).map((v) => Math.round(v * 255)); memo.set(kk, c); }
      d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2];
    }
  }
  const oc = document.createElement('canvas'); oc.width = w; oc.height = h;
  oc.getContext('2d').putImageData(src, 0, 0);
  const t = new THREE.CanvasTexture(oc);
  t.flipY = tex.flipY; t.wrapS = tex.wrapS; t.wrapT = tex.wrapT; t.colorSpace = THREE.SRGBColorSpace;
  t.offset.copy(tex.offset); t.repeat.copy(tex.repeat); t.rotation = tex.rotation; t.center.copy(tex.center);
  if (LK.filter === 'nearest' || LK.filter === 'bilinear') {
    t.magFilter = t.minFilter = LK.filter === 'nearest' ? THREE.NearestFilter : THREE.LinearFilter; t.generateMipmaps = false;
  } else { t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.anisotropy = 4; }
  t.needsUpdate = true;
  cache.set(tex.uuid, t); TEX.set(key, t);
  return t;
}

// ------------------------------------------------------------------------- vá skinning cho ShaderMaterial tự viết
const SKIN_PARS = '#include <common>\n#include <skinning_pars_vertex>\n#include <morphtarget_pars_vertex>\n';
const SKIN_BODY = '#include <skinbase_vertex>\n#include <begin_vertex>\n#include <morphtarget_vertex>\n#include <skinning_vertex>\n'
  + '#include <beginnormal_vertex>\n#include <morphnormal_vertex>\n#include <skinnormal_vertex>\n';
/** vertexShader dùng position/normal thô → bản đọc `transformed`/`objectNormal` sau skinning + morph (khối chuẩn của three). */
export function skinPatchVS(vs) {
  if (vs.includes('skinning_vertex')) return vs;
  const i = vs.indexOf('void main()');
  if (i < 0) return vs;
  const open = vs.indexOf('{', i) + 1;
  const body = vs.slice(open).replace(/vec4\(\s*position\s*,/g, 'vec4(transformed,').replace(/\bnormal\b(?!Matrix)/g, 'objectNormal');
  return SKIN_PARS + vs.slice(0, open) + '\n' + SKIN_BODY + body;
}
function skinSafe(ctx, m, cache) {
  if (!m || !m.isShaderMaterial || m.vertexShader.includes('skinning_vertex')) return m;
  if (cache.has(m)) return cache.get(m);
  const THREE = ctx.THREE;
  const n = new THREE.ShaderMaterial({ uniforms: m.uniforms, defines: { ...(m.defines || {}) }, vertexShader: skinPatchVS(m.vertexShader),
    fragmentShader: m.fragmentShader, side: m.side, transparent: m.transparent, depthWrite: m.depthWrite, vertexColors: m.vertexColors,
    blending: m.blending });
  if (m.color) n.color = m.color;                       // uniform dùng chung → đổi màu/độ nóng vẫn tác dụng
  if (m.emissive) n.emissive = m.emissive;
  if (m.uniforms && m.uniforms.uOpacity) Object.defineProperty(n, 'opacity', { get: () => m.uniforms.uOpacity.value, set: (v) => { m.uniforms.uOpacity.value = v; } });
  cache.set(m, n);
  return n;
}
let ND_SKIN = null;
const ndSkin = (THREE) => ND_SKIN || (ND_SKIN = new THREE.ShaderMaterial({   // cùng hợp đồng normal/depth với ndMat của main.js
  vertexShader: skinPatchVS('varying vec3 vN; varying float vD; void main(){ vN = normalize(normalMatrix*normal); vec4 mv = modelViewMatrix*vec4(position,1.); vD = -mv.z; gl_Position = projectionMatrix*mv; }'),
  fragmentShader: 'varying vec3 vN; varying float vD; void main(){ vec3 n = normalize(vN); if(!gl_FrontFacing) n = -n; gl_FragColor = vec4(n*.5+.5, vD); }',
  side: THREE.DoubleSide,
}));

// ------------------------------------------------------------------------------------------------------- dựng prop
const fOf = (ctx, k) => (k.u !== undefined ? k.u * (ctx.N - 1) : (k.t ?? 0) * (ctx.fps || 30));

/** prop {type: "model:<tên>", model_url, model, …} → {g, tick(f), set} cho stage.js. */
export function makeModel(ctx, p) {
  const THREE = ctx.THREE, M = p.model || {}, name = M.name || String(p.type).slice(6);
  const gl = CACHE.get(p.model_url);
  if (!gl) throw new Error(`stage: mô hình '${name}' chưa nạp (thiếu model_url — chạy \`python studio.py assets search ${name}\`)`);
  const skinned = gl.scene.getObjectByProperty('type', 'SkinnedMesh') !== undefined;
  const root = skinned ? SKU.clone(gl.scene) : gl.scene.clone(true);
  // tháo vũ khí/khiên… gắn sẵn trên nhân vật (index: hide)
  const hide = (M.hide || []).map((h) => String(h).toLowerCase());
  if (hide.length) {
    const kill = [];
    root.traverse((o) => { if (o.isMesh && hide.some((h) => String(o.name).toLowerCase().includes(h))) kill.push(o); });
    kill.forEach((o) => o.removeFromParent());
  }
  // ---- chất liệu theo look + màu theo palette style
  const LK = ctx.look3d || {};
  const mode = p.colors ?? (p.color ? 'tint' : M.colors ?? 'palette');
  const keys = M.palette_keys || ['white', 'grey', 'metal', 'iron', 'danger', 'orange', 'accent', 'water'];
  const pal = [...new Set(keys.map((k) => ctx.C(k)).filter((c) => /^#[0-9a-f]{6}$/i.test(String(c))))].map((h) => toLab(...hexRgb(h)));
  const tintHex = mode === 'tint' ? ctx.C(p.color) : (mode !== 'palette' && mode !== 'keep' ? ctx.C(mode) : null);
  const tint = tintHex && /^#[0-9a-f]{6}$/i.test(String(tintHex)) ? toLab(...hexRgb(tintHex)) : null;
  const map = mapper(tint ? 'tint' : mode, pal, tint, tint ? 1 : (p.mix ?? M.mix ?? 0.7), tint ? (p.mix_l ?? 0.25) : (p.mix_l ?? M.mix_l ?? 0.3));
  const texCache = new Map(), matCache = new Map(), skinCache = new Map();
  const noMap = LK.mat === 'xray' || LK.mat === 'wire';
  const conv = (m0) => {
    if (matCache.has(m0)) return matCache.get(m0);
    const c0 = m0.color ? [m0.color.r, m0.color.g, m0.color.b].map(l2s) : [1, 1, 1];
    const o = { side: m0.side, transparent: !!m0.transparent, opacity: m0.opacity ?? 1, vertexColors: !!m0.vertexColors };
    if (m0.alphaTest) o.alphaTest = m0.alphaTest;
    if (m0.map && !noMap) o.map = lookTexture(ctx, m0.map, map, texCache);
    // có texture: màu đã đổi trong ảnh → hệ số màu giữ nguyên (không áp 2 lần); không texture: đổi hệ số màu
    const col = rgbHex(map && (!m0.map || noMap) ? map(...c0) : c0);
    const m = ctx.toon(col, o);
    matCache.set(m0, m);
    return m;
  };
  root.traverse((o) => {
    if (!o.isMesh) return;
    const deform = o.isSkinnedMesh || (o.geometry && o.geometry.morphAttributes && Object.keys(o.geometry.morphAttributes).length);
    const fix = (m0) => { const m = conv(m0); return deform ? skinSafe(ctx, m, skinCache) : m; };
    o.material = Array.isArray(o.material) ? o.material.map(fix) : fix(o.material);
    o.castShadow = true; o.receiveShadow = true;
    if (deform) { o.userData.nd = ndSkin(THREE); o.frustumCulled = false; }
  });
  // ---- chuẩn hoá cỡ: bbox ở tư thế nghỉ, chỉ mesh còn lại
  root.updateMatrixWorld(true);
  const box = new THREE.Box3(), tmp = new THREE.Box3();
  root.traverse((o) => {
    if (!o.isMesh) return;
    if (o.isSkinnedMesh) { o.computeBoundingBox(); tmp.copy(o.boundingBox).applyMatrix4(o.matrixWorld); } else {
      if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
      tmp.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld);
    }
    box.union(tmp);
  });
  const sz = box.isEmpty() ? new THREE.Vector3(1, 1, 1) : box.getSize(new THREE.Vector3());
  const k = p.size ? p.size / Math.max(sz.x, sz.y, sz.z, 1e-6) : (p.h ?? M.h ?? sz.y) / Math.max(sz.y, 1e-6);
  const g = ctx.group(ctx.world), inner = new THREE.Group();
  inner.scale.setScalar(k);
  if (!box.isEmpty()) inner.position.set(-(box.min.x + box.max.x) / 2 * k, -box.min.y * k, -(box.min.z + box.max.z) / 2 * k);
  inner.add(root); g.add(inner);
  g.userData.model = name;
  // ---- animation: dòng thời gian từ anim + keys[{u|t, anim, anim_speed, anim_offset, anim_loop}]
  const clips = gl.animations || [], names = clips.map((c) => c.name);
  const FPS = ctx.fps || 30;
  let tick = null;
  const want = p.anim ?? M.anim_default;
  if (clips.length && want !== false && want !== 'none') {
    const mixer = new THREE.AnimationMixer(root), acts = new Map();
    const clipOf = (q) => {
      const n = pickName(names, q);
      if (n === null) throw new Error(`stage: mô hình '${name}' không có anim '${q}' (có: ${names.slice(0, 30).join(', ')})`);
      return clips[names.indexOf(n)];
    };
    const segs = [{ f0: 0, clip: clipOf(want), speed: p.anim_speed ?? 1, off: p.anim_offset ?? 0, loop: p.anim_loop ?? true }];
    for (const kf of (p.keys || []).filter((x) => x && x.anim !== undefined).map((x) => ({ ...x, f: fOf(ctx, x) })).sort((a, b) => a.f - b.f)) {
      segs.push({ f0: kf.f, clip: clipOf(kf.anim), speed: kf.anim_speed ?? p.anim_speed ?? 1, off: kf.anim_offset ?? 0, loop: kf.anim_loop ?? p.anim_loop ?? true });
    }
    const blendF = Math.max(0, (p.anim_blend ?? 0.25) * FPS);
    const act = (clip) => {
      let a = acts.get(clip.name);
      if (!a) { a = mixer.clipAction(clip); a.play(); acts.set(clip.name, a); }
      return a;
    };
    const timeOf = (s, f) => {
      const d = Math.max(1e-4, s.clip.duration), t = s.off + (f - s.f0) / FPS * s.speed;
      return s.loop ? ((t % d) + d) % d : Math.min(Math.max(t, 0), d - 1e-4);
    };
    tick = (f) => {
      let i = 0;
      while (i + 1 < segs.length && segs[i + 1].f0 <= f) i++;
      for (const a of acts.values()) { a.enabled = true; a.setEffectiveWeight(0); }
      const cur = segs[i], w = i > 0 && blendF > 0 ? Math.min(1, (f - cur.f0) / blendF) : 1;
      if (w < 1) { const pa = act(segs[i - 1].clip); pa.time = timeOf(segs[i - 1], f); pa.setEffectiveWeight(1 - w); }
      const ca = act(cur.clip); ca.time = timeOf(cur, f); ca.setEffectiveWeight(w < 1 && segs[i - 1].clip === cur.clip ? 1 : w);
      mixer.update(0);                                   // đánh giá đúng action.time vừa đặt — không cộng dồn thời gian
    };
    tick(0);
  }
  return { g, tick, set: {}, model: { name, clips: names, scale: k } };
}

export const isModelType = (t) => typeof t === 'string' && t.startsWith('model:');
