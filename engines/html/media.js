// Media actor cho beat `scene` của engine html: animation vẽ sẵn của người khác/của anh, chạy đúng theo frame.
//   Lottie (.json / .lottie) — dotLottie web (vendor/dotlottie, MIT; WASM ThorVG nạp từ máy, không CDN)
//   Rive (.riv)              — Rive canvas-advanced (vendor/rive, MIT; WASM nhúng)
// Tài sản nằm ở assets/user/lottie|rive/, storyboard gọi bằng tên (vidlib/userassets.py đổi thành *_url khi dựng job).
// Tất định: Lottie setFrame(n) vẽ đồng bộ đúng frame n; Rive chạy từ 0 theo lưới bước cố định 1/120 s (về sau một mốc
// thì dựng lại artboard) → worker nào render frame nào, theo thứ tự nào cũng ra cùng hình.
// Màu (chỉ Lottie JSON): colors "palette" (mặc định: đổi từng màu sang vai gần nhất của style) · "<vai>" (tô một màu,
// giữ sáng/tối) · "keep" (giữ nguyên). File .lottie (zip) và Rive giữ màu gốc.

const RGB = (h) => { const s = String(h).replace('#', ''); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) / 255); };
const roleOf = (r, g, b) => {                                // cùng luật với nhập SVG (svgimport.js)
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn;
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  if (s < 0.25 || d < 0.08) return l > 0.45 ? 'ink' : 'dim';
  let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  h = (h * 60 + 360) % 360;
  return h < 60 || h >= 330 ? 'hot' : h >= 150 && h < 260 ? 'cold' : 'accent';
};

/** Đổi màu toàn bộ file Lottie JSON (fill, stroke, gradient, solid layer; tĩnh và có keyframe). */
export function recolorLottie(json, mode, col, bg) {
  if (!mode || mode === 'keep') return json;
  const B = RGB(bg);
  const map = (r, g, b) => {
    const l = (Math.max(r, g, b) + Math.min(r, g, b)) / 2;
    const T = RGB(col(mode === 'palette' ? roleOf(r, g, b) : mode));
    const k = mode === 'palette' ? 1 : 0.35 + 0.65 * l;      // tô một màu: giữ độ sáng tương đối của bản gốc
    return T.map((v, i) => B[i] + (v - B[i]) * k);
  };
  const recolorArr = (a) => { if (Array.isArray(a) && a.length >= 3 && a.slice(0, 3).every((v) => typeof v === 'number')) { const m = map(a[0], a[1], a[2]); a[0] = m[0]; a[1] = m[1]; a[2] = m[2]; } };
  const recolorProp = (p) => {                                  // {a:0,k:[r,g,b,a]} | {a:1,k:[{s:[…],e:[…]}…]}
    if (!p || p.k === undefined) return;
    if (p.a) for (const kf of p.k || []) { recolorArr(kf.s); recolorArr(kf.e); } else recolorArr(p.k);
  };
  const recolorGrad = (gr) => {                                 // g: {p: số điểm, k: {a, k: [o,r,g,b, o,r,g,b, …, (o,a…)]}}
    if (!gr || !gr.k) return;
    const fix = (arr) => { for (let i = 0; i + 3 < gr.p * 4 + 1 && i + 3 < arr.length; i += 4) { const m = map(arr[i + 1], arr[i + 2], arr[i + 3]); arr[i + 1] = m[0]; arr[i + 2] = m[1]; arr[i + 3] = m[2]; } };
    if (gr.k.a) for (const kf of gr.k.k || []) { if (kf.s) fix(kf.s); if (kf.e) fix(kf.e); } else fix(gr.k.k);
  };
  const walk = (o) => {
    if (Array.isArray(o)) { o.forEach(walk); return; }
    if (!o || typeof o !== 'object') return;
    if ((o.ty === 'fl' || o.ty === 'st') && o.c) recolorProp(o.c);
    if ((o.ty === 'gf' || o.ty === 'gs') && o.g) recolorGrad(o.g);
    if (o.ty === 1 && typeof o.sc === 'string') { const m = map(...RGB(o.sc)); o.sc = '#' + m.map((v) => Math.round(v * 255).toString(16).padStart(2, '0')).join(''); }
    for (const v of Object.values(o)) if (v && typeof v === 'object') walk(v);
  };
  walk(json);
  return json;
}

const findMedia = (root) => {                                  // mọi actor có lottie_url / rive_url trong job (kể cả ô hàng xóm)
  const out = [];
  const walk = (o) => {
    if (Array.isArray(o)) { o.forEach(walk); return; }
    if (!o || typeof o !== 'object') return;
    if (o.lottie_url || o.rive_url) out.push(o);
    for (const v of Object.values(o)) if (v && typeof v === 'object') walk(v);
  };
  walk(root);
  return out;
};
const maxSize = (a) => Math.max(a.size ?? 170, ...((a.keys || []).map((k) => k.size || 0)));
const keyOf = (a) => `${a.lottie_url || a.rive_url}|${a.colors || ''}|${a.animation || ''}|${a.state_machine || ''}|${a.artboard || ''}`;

/** Nạp mọi media actor của job → {draw(actor, x, y, s, frameLocal, fps, alpha, rot), info}. */
export async function loadMedia(job, { g, col, bg }) {
  const acts = findMedia(job);
  const reg = new Map();
  if (!acts.length) return { draw: () => false, info: [] };
  let DL = null, RV = null;
  for (const a of acts) {
    const key = keyOf(a), px = Math.min(1600, Math.max(256, Math.ceil(maxSize(a) / 128) * 128));
    if (reg.has(key)) { const e = reg.get(key); if (px > e.px) e.px = px; continue; }
    reg.set(key, { a, px });
  }
  for (const e of reg.values()) {
    const a = e.a, cv = document.createElement('canvas');
    cv.width = cv.height = e.px;
    if (a.lottie_url) {
      if (!DL) {
        DL = (await import('../../vendor/dotlottie/dotlottie-web.js')).DotLottie;
        DL.setWasmUrl(new URL('../../vendor/dotlottie/dotlottie-player.wasm', import.meta.url).href);
      }
      const isJson = /\.json$/i.test(a.lottie_url);
      let data = await (await fetch(a.lottie_url, { cache: 'no-store' }))[isJson ? 'json' : 'arrayBuffer']();
      if (isJson) {
        e.fr = data.fr || 30; e.total = Math.max(1, (data.op ?? 60) - (data.ip ?? 0));
        data = JSON.stringify(recolorLottie(data, a.colors ?? 'palette', col, bg));
      }
      const pl = new DL({ canvas: cv, data, autoplay: false, loop: false, useFrameInterpolation: false,
        renderConfig: { devicePixelRatio: 1, autoResize: false, freezeOnOffscreen: false } });
      await new Promise((ok, bad) => { pl.addEventListener('load', ok); pl.addEventListener('loadError', (ev) => bad(new Error(`lottie ${a.lottie_url}: ${ev.error || 'không nạp được'}`))); });
      e.total = pl.totalFrames || e.total; e.fr = e.fr || (pl.totalFrames / Math.max(1e-6, pl.duration));
      e.kind = 'lottie'; e.cv = cv; e.pl = pl;
      e.render = (n) => { pl.setFrame(n); };
    } else {
      if (!RV) RV = await (await import('../../vendor/rive/canvas_advanced_single.mjs')).default();
      const bytes = new Uint8Array(await (await fetch(a.rive_url, { cache: 'no-store' })).arrayBuffer());
      const file = await RV.load(bytes);
      const rd = RV.makeRenderer(cv);
      // trạng thái Rive có thể phụ thuộc lịch sử (ràng buộc, state machine) → luôn chạy từ 0 theo lưới bước cố định
      // STEP giây; về sau một mốc = dựng lại artboard mới. Worker nào, thứ tự nào cũng đi đúng chuỗi bước đó.
      const STEP = 1 / 120;
      const mk = () => {
        const ab = a.artboard ? file.artboardByName(a.artboard) : file.defaultArtboard();
        let anim = null, sm = null;
        if (a.state_machine !== undefined && ab.stateMachineCount() > 0) {
          sm = new RV.StateMachineInstance(typeof a.state_machine === 'string' ? ab.stateMachineByName(a.state_machine) : ab.stateMachineByIndex(0), ab);
        } else if (ab.animationCount() > 0) {
          anim = new RV.LinearAnimationInstance(typeof a.animation === 'string' ? ab.animationByName(a.animation) : ab.animationByIndex(0), ab);
          anim.advance(0); anim.apply(1);
        }
        ab.advance(0);
        return { ab, anim, sm, n: 0 };
      };
      let st = mk();
      e.fr = (st.anim && st.anim.fps) || 60; e.dur = st.anim ? st.anim.duration / Math.max(1, st.anim.fps) : 0;
      e.kind = 'rive'; e.cv = cv;
      e.render = (t) => {                                       // t = giây tính từ lúc actor vào cảnh
        const n = Math.round(t / STEP);
        if (n < st.n) { st.anim?.delete?.(); st.sm?.delete?.(); st.ab.delete?.(); st = mk(); }
        for (; st.n < n; st.n++) {
          if (st.anim) { st.anim.advance(STEP); st.anim.apply(1); }
          if (st.sm) st.sm.advance(STEP);
          st.ab.advance(STEP);
        }
        const ab = st.ab;
        rd.clear(); rd.save();
        rd.align(RV.Fit.contain, RV.Alignment.center, { minX: 0, minY: 0, maxX: cv.width, maxY: cv.height }, ab.bounds);
        ab.draw(rd); rd.restore();
        if (rd.flush) rd.flush();
        if (RV.resolveAnimationFrame) RV.resolveAnimationFrame();
      };
    }
  }
  const info = [...reg.values()].map((e) => ({ url: e.a.lottie_url || e.a.rive_url, kind: e.kind, px: e.px, fr: e.fr, total: e.total || null }));
  /** Vẽ actor: frameLocal = số frame video kể từ lúc actor vào (u `in`). */
  const draw = (a, x, y, s, frameLocal, fps, alpha = 1, rot = 0) => {
    const e = reg.get(keyOf(a));
    if (!e) return false;
    const t = Math.max(0, frameLocal) / fps * (a.speed ?? 1) + (a.start ?? 0);
    if (e.kind === 'lottie') {
      let n = t * e.fr;
      n = a.loop === false ? Math.min(e.total - 1, n) : n % e.total;
      e.render(Math.max(0, n));
    } else {
      let tt = t;                                               // lặp: quay về đầu vòng (dựng lại), giữ: dừng ở cuối
      if (e.dur > 0) tt = a.loop === false ? Math.min(tt, e.dur) : tt % e.dur;
      e.render(tt);
    }
    g.save();
    g.globalAlpha *= alpha;
    g.translate(x, y); if (rot) g.rotate(rot);
    g.drawImage(e.cv, -s, -s, 2 * s, 2 * s);                    // cả hai thư viện đã canh "contain" trong ô vuông
    g.restore();
    return true;
  };
  return { draw, info };
}
