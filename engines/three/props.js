// Đạo cụ 3D dựng từ primitive (đơn vị mét). Mỗi hàm trả về { g: THREE.Group, ...tay cầm để animate }.
// Màu là token palette của style (white/grey/accent/danger/iron/...) → shot code khớp palette shot Flow cạnh nó.
// Kính trong suốt KHÔNG che nét của vật bên trong: thành kính ndSkip, đường viền kính dựng bằng ống (giống nét vẽ).
import { ICONS, iconFor } from '../html/icons.js';

const ring = (ctx, r, tube, parent, y, m = 'white') => {
  const me = ctx.add(new ctx.THREE.TorusGeometry(r, tube, 10, 64), m, 0, y, 0, parent); me.rotation.x = Math.PI / 2; return me;
};
const rod = (ctx, a, b, r, m, parent) => {
  const { THREE } = ctx, A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), L = A.distanceTo(B);
  const me = ctx.add(new THREE.CylinderGeometry(r, r, L, 12), m, 0, 0, 0, parent);
  me.position.copy(A).add(B).multiplyScalar(0.5); me.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), B.clone().sub(A).normalize());
  return me;
};

/** Cốc thuỷ tinh kiểu nét vẽ: vành + đáy là vòng, hai cạnh bên là ống quay theo camera, nước xám bên trong. */
export function glass(ctx, { r = 0.32, h = 0.9, water = 0.62, parent = ctx.world, x = 0, y = 0, z = 0, line = 0.022 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ring(ctx, r, line, g, h); ring(ctx, r * 0.9, line, g, 0.02);
  const sides = ctx.group(g); sides.userData.facing = true;
  for (const s of [-1, 1]) rod(ctx, [s * r, h, 0], [s * r * 0.9, 0.02, 0], line, 'white', sides);
  const wall = ctx.add(new THREE.CylinderGeometry(r, r * 0.9, h, 48, 1, true), new THREE.MeshBasicMaterial({ color: ctx.C('white'), transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false }), 0, h / 2, 0, g, { cast: false });
  wall.userData.ndSkip = true;
  const wh = h * water;
  const waterM = ctx.add(new THREE.CylinderGeometry(r * (0.9 + 0.1 * water) - line, r * 0.9 - line, wh, 48), 'water', 0, wh / 2 + 0.02, 0, g, { cast: false });
  return { g, sides, water: waterM, waterTop: wh + 0.02, r, h };
}

export function iceCube(ctx, { s = 0.18, parent = ctx.world, x = 0, y = 0, z = 0, m = 'accent' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const cube = ctx.add(new THREE.BoxGeometry(s, s, s, 1, 1, 1), m, 0, 0, 0, g);
  const hi = ctx.add(new THREE.BoxGeometry(s * 0.5, s * 0.08, s * 0.02), ctx.flat('accent_hi'), -s * 0.12, s * 0.28, s * 0.51, g, { cast: false });
  hi.userData.ndSkip = true;
  return { g, cube };
}

/** Bi sắt: lạnh = xám đậm; hot 0..1 → đỏ phát sáng + quầng glow (giống bi 1,000°C trong clip Flow). */
export function ball(ctx, { r = 0.11, parent = ctx.world, x = 0, y = 0, z = 0 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const m = ctx.toon('iron'); const me = ctx.add(new THREE.SphereGeometry(r, 32, 20), m, 0, 0, 0, g);
  const hi = ctx.add(new THREE.SphereGeometry(r * 0.22, 12, 8), ctx.flat('#ffffff'), -r * 0.35, r * 0.4, r * 0.75, g, { cast: false }); hi.userData.ndSkip = true;
  const gl = ctx.glow('danger', r * 4.2, g, 0, 0, 0, 0);
  const cold = new THREE.Color(ctx.C('iron')), hotC = new THREE.Color(ctx.C('danger'));
  const setHot = (k) => { m.color.copy(cold).lerp(hotC, k); if (m.emissive) m.emissive.copy(hotC).multiplyScalar(k * 0.55); /* holo/wire: không có emissive → chỉ đổi màu */ gl.material.opacity = k * 0.85; };
  return { g, mesh: me, setHot };
}

/** Cân đĩa: đế, trụ, đòn cân quay quanh đỉnh, 2 đĩa treo bằng 3 dây; tilt(độ) dương = bên trái xuống. */
export function scale(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, span = 0.4, post = 0.62, panR = 0.16, drop = 0.34 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(0.22, 0.26, 0.05, 48), 'white', 0, 0.025, 0, g);
  ctx.add(new THREE.CylinderGeometry(0.14, 0.17, 0.05, 48), 'white', 0, 0.075, 0, g);
  ctx.add(new THREE.CylinderGeometry(0.025, 0.035, post, 16), 'white', 0, 0.1 + post / 2, 0, g);
  const pivot = ctx.group(g, 0, 0.12 + post, 0);
  ctx.add(new THREE.SphereGeometry(0.045, 16, 12), 'white', 0, 0, 0, pivot);
  ctx.add(new THREE.BoxGeometry(span * 2 + 0.06, 0.036, 0.045), 'white', 0, 0, 0, pivot);
  ctx.add(new THREE.ConeGeometry(0.025, 0.12, 12), 'accent', 0, -0.085, 0.03, pivot).rotation.x = Math.PI;
  const pans = [];
  for (const s of [-1, 1]) {
    const hang = ctx.group(pivot, s * span, 0, 0);          // điểm treo trên đòn
    const pan = ctx.group(g);                                 // đĩa luôn thẳng đứng (treo)
    ctx.add(new THREE.CylinderGeometry(panR, panR * 0.72, 0.035, 40), 'white', 0, -drop + 0.0175, 0, pan);          // đĩa nông: vật đặt lên thấy rõ
    ring(ctx, panR, 0.008, pan, -drop + 0.036);
    const strings = [];
    for (let k = 0; k < 3; k++) { const a = k / 3 * Math.PI * 2 + 0.3; strings.push([Math.cos(a) * panR * 0.85, Math.sin(a) * panR * 0.85]); }
    const lines = strings.map(() => rod(ctx, [0, 0, 0], [0, -0.1, 0], 0.006, 'white', g));
    pans.push({ s, hang, pan, drop, strings, lines });
  }
  const setTilt = (deg) => {
    pivot.rotation.z = -deg * Math.PI / 180;
    pivot.updateMatrixWorld(true); g.updateMatrixWorld(true);
    for (const P of pans) {
      const wp = new THREE.Vector3(); P.hang.getWorldPosition(wp); const lp = g.worldToLocal(wp.clone());
      P.pan.position.set(lp.x, lp.y, lp.z);
      P.strings.forEach(([sx, sz], k) => {
        const a = new THREE.Vector3(lp.x, lp.y, lp.z), b = new THREE.Vector3(lp.x + sx, lp.y - P.drop + 0.03, lp.z + sz);
        const L = a.distanceTo(b), me = P.lines[k]; me.scale.set(1, L / 0.1, 1);
        me.position.copy(a).add(b).multiplyScalar(0.5); me.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
      });
    }
  };
  setTilt(0);
  /** toạ độ (local của g) mặt đĩa trái/phải để đặt vật lên */
  const panTop = (i) => { const P = pans[i]; return [P.pan.position.x, P.pan.position.y - P.drop + 0.036, P.pan.position.z]; };
  return { g, pivot, pans, setTilt, panTop };
}

/** Nhiệt kế: thân trắng có vạch chia + số (texture, đọc đúng chiều), ống mao dẫn, bầu + cột chất lỏng theo value (°C). */
export function thermometer(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, lo = -10, hi = 30, step = 10, highlight = 0,
  h = 1.6, w = 0.34, font, unit = '°C' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const body = ctx.add(new THREE.BoxGeometry(w, h, 0.06), 'white', 0, h / 2 + 0.16, 0, g);
  ctx.add(new THREE.CylinderGeometry(w / 2, w / 2, 0.06, 32, 1, false, 0, Math.PI), 'white', 0, h + 0.16, 0, g).rotation.set(Math.PI / 2, 0, Math.PI / 2);
  const scaleCanvas = ctx.P.thermoScale({ lo, hi, step, minor: step / 5, unit, font: font || ctx.job.font_family, ink: ctx.C('ink_text'), highlight, hiColor: ctx.C('accent') });
  const t = new THREE.CanvasTexture(scaleCanvas); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  const plate = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.62, h * 0.96), new THREE.MeshBasicMaterial({ map: t, transparent: true, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
  plate.position.set(w * 0.16, h / 2 + 0.16, 0.0305); plate.userData.text = `${highlight}${unit}`; plate.castShadow = false; g.add(plate);
  const tubeX = -w * 0.27, y0 = 0.16 + h * 0.06, yTop = 0.16 + h * 0.94;
  ctx.add(new THREE.CylinderGeometry(0.026, 0.026, yTop - y0, 16), 'white', tubeX, (y0 + yTop) / 2, 0.035, g);
  const bulb = ctx.add(new THREE.SphereGeometry(0.075, 24, 16), 'danger', tubeX, 0.12, 0.04, g);
  const col = ctx.add(new THREE.CylinderGeometry(0.017, 0.017, 1, 12), 'danger', tubeX, 0, 0.07, g, { cast: false });
  // vạch v trên texture (thermoScale: y_canvas = 0.94 − 0.88·r, mặt chữ cao 0.96h) → toạ độ y cục bộ của nhiệt kế
  const yOf = (v) => 0.16 + h * (0.0776 + 0.8448 * (v - lo) / (hi - lo));
  const setValue = (v) => { const top = yOf(v); const b = 0.12; col.scale.y = Math.max(0.01, top - b); col.position.y = (top + b) / 2; };
  setValue(highlight);
  return { g, body, bulb, setValue, yOf };
}

/** Biển/bảng có chữ (diegetic): khung trắng, mặt tối, chữ texture. */
export function sign(ctx, { text, parent = ctx.world, x = 0, y = 0, z = 0, w = 1.2, h = 0.5, face = 'board', color = 'chalk', px = 150, font } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(w + 0.08, h + 0.08, 0.05), 'white', 0, 0, -0.03, g);
  ctx.add(new THREE.BoxGeometry(w, h, 0.02), face, 0, 0, 0.002, g);
  const tp = ctx.textPlane({ text, px, color, font: font || ctx.job.font_family, w: 1536, h: Math.round(1536 * h / w) }, w * 0.94, h * 0.9, g, 0, 0, 0.014);
  return { g, text: tp };
}

export function bench(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 3.2, d = 1.1, top = 0.92 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const tt = ctx.P.tex(ctx.P.benchTop(1, ctx.C('bench'), ctx.C('bench_seam')), 2, 1);
  ctx.add(ctx.tbox(w, 0.08, d, 1), ctx.toon('#ffffff', { map: tt }), 0, top - 0.04, 0, g);
  for (const sx of [-1, 1]) ctx.add(ctx.tbox(0.08, top - 0.08, d * 0.9, 1), 'bench_leg', sx * (w / 2 - 0.12), (top - 0.08) / 2, 0, g);
  return { g, top };
}

/** Buồng chân không: ống kính trụ (viền vẽ bằng ống) + nắp & đế kim loại + ống hút. */
export function chamber(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.42, h = 1.5 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r + 0.06, r + 0.08, 0.1, 48), 'metal', 0, 0.05, 0, g);
  ctx.add(new THREE.CylinderGeometry(r + 0.06, r + 0.06, 0.1, 48), 'metal', 0, h + 0.15, 0, g);
  ring(ctx, r, 0.018, g, 0.1, 'glass_line'); ring(ctx, r, 0.018, g, h + 0.1, 'glass_line');
  const sides = ctx.group(g); sides.userData.facing = true;
  for (const s of [-1, 1]) rod(ctx, [s * r, 0.1, 0], [s * r, h + 0.1, 0], 0.018, 'glass_line', sides);
  const wall = ctx.add(new THREE.CylinderGeometry(r, r, h, 48, 1, true), new THREE.MeshBasicMaterial({ color: ctx.C('glass_line'), transparent: true, opacity: 0.06, side: THREE.DoubleSide, depthWrite: false }), 0, h / 2 + 0.1, 0, g, { cast: false });
  wall.userData.ndSkip = true;
  rod(ctx, [r + 0.06, 0.05, 0], [r + 0.5, 0.05, 0], 0.03, 'metal', g);
  return { g, sides, inner: { bottom: 0.1, top: h + 0.1, r } };
}

/** Đồng hồ áp suất: mặt số (texture có số), kim quay theo value 0..1. */
export function gauge(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.22, labels = ['0', '50', '100'], unit = 'kPa', font } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r + 0.03, r + 0.03, 0.06, 48), 'metal', 0, 0, 0, g).rotation.x = Math.PI / 2;
  const c = document.createElement('canvas'); c.width = c.height = 512; const q = c.getContext('2d');
  q.fillStyle = ctx.C('dial'); q.beginPath(); q.arc(256, 256, 250, 0, 7); q.fill();
  q.strokeStyle = ctx.C('ink_text'); q.fillStyle = ctx.C('ink_text'); q.lineCap = 'round';
  for (let i = 0; i <= 10; i++) { const a = Math.PI * (0.75 + 1.5 * i / 10); q.lineWidth = i % 5 ? 6 : 12; q.beginPath(); q.moveTo(256 + Math.cos(a) * 200, 256 + Math.sin(a) * 200); q.lineTo(256 + Math.cos(a) * (i % 5 ? 175 : 160), 256 + Math.sin(a) * (i % 5 ? 175 : 160)); q.stroke(); }
  q.font = `64px "${font || ctx.job.font_family}"`; q.textAlign = 'center'; q.textBaseline = 'middle';
  labels.forEach((t, i) => { const a = Math.PI * (0.75 + 1.5 * i / (labels.length - 1)); q.fillText(t, 256 + Math.cos(a) * 112, 256 + Math.sin(a) * 112); });
  q.font = `56px "${font || ctx.job.font_family}"`; q.fillText(unit, 256, 380);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const face = new THREE.Mesh(new THREE.CircleGeometry(r, 48), new THREE.MeshBasicMaterial({ map: t })); face.position.z = 0.032; face.userData.text = unit; g.add(face);
  const needle = ctx.group(g, 0, 0, 0.04);
  ctx.add(new THREE.BoxGeometry(0.012, r * 0.8, 0.01), 'danger', 0, r * 0.38, 0, needle, { cast: false });
  ctx.add(new THREE.CylinderGeometry(0.025, 0.025, 0.02, 16), 'danger', 0, 0, 0, needle, { cast: false }).rotation.x = Math.PI / 2;
  const setValue = (k) => { needle.rotation.z = -(Math.PI * (0.75 + 1.5 * k) + Math.PI / 2); };
  setValue(0);
  return { g, setValue };
}

/** Mỗi frame: các nhóm "facing" xoay quanh trục Y về phía camera (cạnh bên của kính luôn là đường viền). */
export function faceCamera(ctx, root = ctx.world) {
  const cam = ctx.camera.position, v = new ctx.THREE.Vector3();
  root.traverse((o) => { if (o.userData.facing) { o.getWorldPosition(v); o.rotation.y = Math.atan2(cam.x - v.x, cam.z - v.z); } });
}

// ===========================================================================
// NHÂN VẬT 3D KHỚP NỐI (mannequin / human3d / runner3d / lifter3d)
// ===========================================================================

const ARM_3D = {
  hang: [0.08, 0, 0.08, 0.12],
  hip: [0.35, 0, 0.55, 0.9],
  wave: [-2.4, 0, -0.45, 0.6],
  up: [-2.85, 0, -0.15, 0.1],
  point: [-1.45, 0, 0, 0.05],
  hold: [-0.95, 0, 0.15, 1.1],
  shrug: [0.25, 0, 0.45, 1.65],
  cheer: [-2.55, 0, -0.38, 0.35],
  think: [-0.85, -0.25, 0.15, 1.85],
  present: [-1.05, 0.2, -0.25, 0.55],
};

/** Nhân vật 3D khớp nối thật (đứng trên mặt y=0, cao ~1.7m khi s=1), hỗ trợ pose động (idle/run/walk/squat/lift/curl/press/point/cheer/fall) + armL/armR. */
export function mannequin(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, color = 'white', accent = 'accent', pose = 'idle' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const root = ctx.group(g, 0, 0.88, 0); // hông tại y=0.88m
  const bodyM = ctx.toon(color), accM = ctx.toon(accent), darkM = ctx.toon('iron');

  // Hông + thân trên + đầu
  ctx.add(new THREE.CylinderGeometry(0.14, 0.13, 0.14, 20), darkM, 0, 0, 0, root);
  const torso = ctx.group(root, 0, 0.06, 0);
  ctx.add(new THREE.CylinderGeometry(0.18, 0.14, 0.44, 24), bodyM, 0, 0.22, 0, torso);
  ctx.add(new THREE.BoxGeometry(0.24, 0.09, 0.22), accM, 0, 0.3, 0.02, torso); // đai/sọc ngực accent
  const head = ctx.group(torso, 0, 0.5, 0);
  ctx.add(new THREE.CylinderGeometry(0.055, 0.065, 0.09, 16), bodyM, 0, 0.03, 0, head);
  ctx.add(new THREE.SphereGeometry(0.155, 28, 20), bodyM, 0, 0.17, 0, head);
  // Kính bảo hộ / visor 3D
  ctx.add(new THREE.BoxGeometry(0.23, 0.075, 0.12), accM, 0, 0.18, 0.11, head);
  ctx.add(new THREE.BoxGeometry(0.25, 0.03, 0.22), darkM, 0, 0.18, 0.01, head);

  // Tay trái / phải (vai → khuỷu → bàn tay)
  const makeArm = (side) => {
    const sh = ctx.group(torso, side * 0.22, 0.4, 0);
    ctx.add(new THREE.SphereGeometry(0.056, 16, 12), bodyM, 0, 0, 0, sh);
    ctx.add(new THREE.CylinderGeometry(0.046, 0.04, 0.26, 16), bodyM, 0, -0.13, 0, sh);
    const el = ctx.group(sh, 0, -0.26, 0);
    ctx.add(new THREE.SphereGeometry(0.044, 14, 10), bodyM, 0, 0, 0, el);
    ctx.add(new THREE.CylinderGeometry(0.04, 0.035, 0.24, 16), bodyM, 0, -0.12, 0, el);
    ctx.add(new THREE.SphereGeometry(0.048, 16, 12), bodyM, 0, -0.25, 0, el);
    return { sh, el, side };
  };
  const armL = makeArm(-1), armR = makeArm(1);

  // Chân trái / phải (hông → gối → bàn chân/giày)
  const makeLeg = (side) => {
    const hip = ctx.group(root, side * 0.1, -0.04, 0);
    ctx.add(new THREE.SphereGeometry(0.062, 16, 12), darkM, 0, 0, 0, hip);
    ctx.add(new THREE.CylinderGeometry(0.062, 0.05, 0.4, 16), bodyM, 0, -0.2, 0, hip);
    const knee = ctx.group(hip, 0, -0.4, 0);
    ctx.add(new THREE.SphereGeometry(0.052, 14, 10), bodyM, 0, 0, 0, knee);
    ctx.add(new THREE.CylinderGeometry(0.05, 0.042, 0.38, 16), bodyM, 0, -0.19, 0, knee);
    const foot = ctx.group(knee, 0, -0.39, 0.04);
    ctx.add(new THREE.BoxGeometry(0.11, 0.07, 0.22), accM, 0, -0.02, 0, foot);
    ctx.add(new THREE.BoxGeometry(0.115, 0.025, 0.23), 'white', 0, -0.055, 0, foot);
    return { hip, knee, foot, side };
  };
  const legL = makeLeg(-1), legR = makeLeg(1);

  const coldC = new THREE.Color(ctx.C(color)), hotC = new THREE.Color(ctx.C('danger'));
  let curPose = pose, curVal = 0, curHot = 0, curArmL = null, curArmR = null;

  const applyArmPreset = (arm, name, f) => {
    const p = ARM_3D[name];
    if (!p) return false;
    const s = arm.side;
    const w = name === 'wave' ? Math.sin(f * 0.35) * 0.35 : 0;
    arm.sh.rotation.set(p[0], p[1] * s, p[2] * s);
    arm.el.rotation.set(-p[3] + w, 0, 0);
    return true;
  };

  const update = (f = 0) => {
    const p = curPose || 'idle', u = curVal || 0;
    root.position.set(0, 0.88, 0); root.rotation.set(0, 0, 0);
    torso.rotation.set(0, 0, 0); head.rotation.set(0, 0, 0);
    legL.hip.rotation.set(0, 0, 0); legL.knee.rotation.set(0, 0, 0);
    legR.hip.rotation.set(0, 0, 0); legR.knee.rotation.set(0, 0, 0);
    armL.sh.rotation.set(0.06, 0, -0.08); armL.el.rotation.set(-0.15, 0, 0);
    armR.sh.rotation.set(0.06, 0, 0.08); armR.el.rotation.set(-0.15, 0, 0);

    if (p === 'run' || p === 'sprint') {
      const ph = f * (p === 'sprint' ? 0.38 : 0.26) + u * Math.PI * 2;
      const s = Math.sin(ph), c = Math.cos(ph);
      root.position.y = 0.86 + Math.abs(s) * 0.08;
      torso.rotation.x = 0.24; torso.rotation.y = -s * 0.18;
      head.rotation.x = -0.14;
      legL.hip.rotation.x = -s * 0.85; legL.knee.rotation.x = Math.max(0.1, c * 0.95 + 0.45);
      legR.hip.rotation.x = s * 0.85; legR.knee.rotation.x = Math.max(0.1, -c * 0.95 + 0.45);
      armL.sh.rotation.x = s * 0.75 - 0.2; armL.el.rotation.x = -1.35;
      armR.sh.rotation.x = -s * 0.75 - 0.2; armR.el.rotation.x = -1.35;
    } else if (p === 'walk') {
      const ph = f * 0.16 + u * Math.PI * 2, s = Math.sin(ph), c = Math.cos(ph);
      root.position.y = 0.88 + Math.abs(s) * 0.03;
      legL.hip.rotation.x = -s * 0.45; legL.knee.rotation.x = Math.max(0, c * 0.4 + 0.15);
      legR.hip.rotation.x = s * 0.45; legR.knee.rotation.x = Math.max(0, -c * 0.4 + 0.15);
      armL.sh.rotation.x = s * 0.35; armL.el.rotation.x = -0.3;
      armR.sh.rotation.x = -s * 0.35; armR.el.rotation.x = -0.3;
    } else if (p === 'squat' || p === 'lift') {
      const d = u > 0 ? u : (0.5 - 0.5 * Math.cos(f * 0.15));
      root.position.y = 0.88 - d * 0.32;
      torso.rotation.x = d * 0.38;
      legL.hip.rotation.x = -d * 1.15; legL.knee.rotation.x = d * 1.85;
      legR.hip.rotation.x = -d * 1.15; legR.knee.rotation.x = d * 1.85;
      if (p === 'lift') {
        armL.sh.rotation.x = -1.2 - (1 - d) * 1.5; armL.el.rotation.x = -0.25;
        armR.sh.rotation.x = -1.2 - (1 - d) * 1.5; armR.el.rotation.x = -0.25;
      } else {
        armL.sh.rotation.x = -1.35; armR.sh.rotation.x = -1.35;
      }
    } else if (p === 'curl' || p === 'press') {
      const d = u > 0 ? u : (0.5 - 0.5 * Math.cos(f * 0.18));
      if (p === 'curl') {
        armL.sh.rotation.x = -0.15; armL.el.rotation.x = -0.3 - d * 1.85;
        armR.sh.rotation.x = -0.15; armR.el.rotation.x = -0.3 - d * 1.85;
      } else {
        armL.sh.rotation.set(-1.5 - d * 1.35, 0, -0.35); armL.el.rotation.x = -1.4 * (1 - d);
        armR.sh.rotation.set(-1.5 - d * 1.35, 0, 0.35); armR.el.rotation.x = -1.4 * (1 - d);
      }
    } else if (p === 'cheer' || p === 'jump') {
      const b = Math.abs(Math.sin(f * 0.22));
      root.position.y = 0.88 + b * 0.12;
      applyArmPreset(armL, 'cheer', f); applyArmPreset(armR, 'cheer', f);
    } else if (p === 'point' || p === 'present') {
      applyArmPreset(armR, p, f);
    } else if (p === 'fall') {
      const d = Math.min(1, u > 0 ? u : f / 35);
      root.rotation.z = d * 1.35; root.position.y = 0.88 * (1 - d * 0.75);
      armL.sh.rotation.set(-1.8, 0, -0.6); armR.sh.rotation.set(-2.1, 0, 0.6);
    } else {
      const br = Math.sin(f * 0.1);
      root.position.y = 0.88 + br * 0.012;
      head.rotation.z = Math.sin(f * 0.06) * 0.04;
    }

    if (curArmL) applyArmPreset(armL, curArmL, f);
    if (curArmR) applyArmPreset(armR, curArmR, f);
    bodyM.color.copy(coldC).lerp(hotC, curHot);
  };
  update(0);
  return {
    g,
    update,
    setPose: (v) => { curPose = v; },
    setValue: (v) => { curVal = v; },
    setHot: (v) => { curHot = v; },
    setArmL: (v) => { curArmL = v; },
    setArmR: (v) => { curArmR = v; },
  };
}

// ===========================================================================
// ĐẠO CỤ 3D THEO 4 VŨ TRỤ KÊNH (A–D) + KHOA HỌC / ĐỜI SỐNG / VŨ TRỤ
// ===========================================================================

/** A1. Giày chạy bộ 3D: đế đệm dày, thân nghiêng, cổ giày, dây giày; value làm cong/nén đế. */
export function shoe(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, color = 'accent', sole = 'white' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const soleG = ctx.group(g, 0, 0.045, 0);
  ctx.add(new THREE.BoxGeometry(0.64, 0.08, 0.26), sole, 0, 0, 0, soleG);
  ctx.add(new THREE.BoxGeometry(0.66, 0.025, 0.27), 'iron', 0, -0.045, 0, soleG);
  const upper = ctx.group(g, -0.03, 0.15, 0);
  ctx.add(new THREE.BoxGeometry(0.5, 0.16, 0.23), color, 0, 0, 0, upper);
  ctx.add(new THREE.CylinderGeometry(0.11, 0.12, 0.16, 20), 'iron', -0.14, 0.06, 0, upper);
  for (let i = 0; i < 3; i++) ctx.add(new THREE.BoxGeometry(0.025, 0.03, 0.24), sole, 0.04 + i * 0.065, 0.08, 0, upper);
  const setValue = (v = 0) => { soleG.scale.y = Math.max(0.45, 1 - v * 0.35); upper.position.y = 0.15 - v * 0.025; };
  return { g, setValue };
}

/** A2. Bình nước thể thao 3D: vỏ trong, mực nước động theo water/value, nắp vòi accent. */
export function bottle(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.2, h = 0.72, water = 0.65, color = 'water' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ring(ctx, r, 0.016, g, 0.02); ring(ctx, r, 0.016, g, h * 0.78);
  const sides = ctx.group(g); sides.userData.facing = true;
  for (const s of [-1, 1]) rod(ctx, [s * r, 0.02, 0], [s * r, h * 0.78, 0], 0.016, 'white', sides);
  const wall = ctx.add(new THREE.CylinderGeometry(r, r, h * 0.76, 36, 1, true), new THREE.MeshBasicMaterial({ color: ctx.C('white'), transparent: true, opacity: 0.08, side: THREE.DoubleSide, depthWrite: false }), 0, h * 0.4, 0, g, { cast: false });
  wall.userData.ndSkip = true;
  ctx.add(new THREE.CylinderGeometry(r * 0.55, r * 0.95, h * 0.12, 32), 'accent', 0, h * 0.84, 0, g);
  ctx.add(new THREE.CylinderGeometry(r * 0.22, r * 0.26, h * 0.1, 20), 'white', 0, h * 0.94, 0, g);
  const liq = ctx.add(new THREE.CylinderGeometry(r * 0.9, r * 0.9, 1, 32), color, 0, 0, 0, g, { cast: false });
  const setWater = (w = 0.65) => {
    const wh = Math.max(0.02, Math.min(1, w)) * h * 0.72;
    liq.scale.y = wh; liq.position.y = wh / 2 + 0.03;
  };
  setWater(water);
  return { g, setWater, setValue: setWater };
}

/** A3. Đồng hồ bấm giờ (stopwatch) 3D: vỏ kim loại, nút bấm đỉnh, kim giây quay theo value. */
export function stopwatch(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.36 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r + 0.04, r + 0.04, 0.1, 48), 'metal', 0, r + 0.04, 0, g).rotation.x = Math.PI / 2;
  ctx.add(new THREE.CylinderGeometry(r, r, 0.11, 48), 'dial', 0, r + 0.04, 0, g).rotation.x = Math.PI / 2;
  ctx.add(new THREE.CylinderGeometry(0.05, 0.05, 0.12, 20), 'accent', 0, r * 2 + 0.1, 0, g);
  ctx.add(new THREE.BoxGeometry(0.14, 0.04, 0.06), 'accent', 0, r * 2 + 0.16, 0, g);
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI * 2;
    const tk = ctx.add(new THREE.BoxGeometry(0.02, r * 0.14, 0.02), 'ink_text', Math.sin(a) * r * 0.8, r + 0.04 + Math.cos(a) * r * 0.8, 0.06, g);
    tk.rotation.z = -a;
  }
  const hand = ctx.group(g, 0, r + 0.04, 0.07);
  ctx.add(new THREE.BoxGeometry(0.024, r * 0.76, 0.02), 'danger', 0, r * 0.32, 0, hand);
  ctx.add(new THREE.CylinderGeometry(0.04, 0.04, 0.03, 16), 'danger', 0, 0, 0, hand).rotation.x = Math.PI / 2;
  const setValue = (v = 0) => { hand.rotation.z = -v * Math.PI * 2; };
  return { g, setValue };
}

/** A4. Trái tim 3D: 2 thuỳ tròn + đỉnh nhọn mượt + cung động mạch chủ gọn gàng, nhịp đập theo value. */
export function heart(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.34, color = 'danger' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const body = ctx.group(g, 0, r * 1.1, 0);
  for (const s of [-1, 1]) {
    const lobe = ctx.add(new THREE.SphereGeometry(r * 0.56, 24, 18), color, s * r * 0.4, r * 0.24, 0, body);
    lobe.scale.set(1.0, 1.05, 0.78);
  }
  const cone = ctx.add(new THREE.ConeGeometry(r * 0.85, r * 1.22, 28), color, 0, -r * 0.34, 0, body);
  cone.rotation.x = Math.PI;
  cone.scale.set(1.05, 1.0, 0.72);
  const arch = ctx.add(new THREE.TorusGeometry(r * 0.2, r * 0.075, 10, 20, Math.PI * 0.9), color, -r * 0.04, r * 0.62, 0, body);
  arch.rotation.z = 0.2;
  const setValue = (v = 0) => { const s = 1 + Math.sin(v * Math.PI * 2) * 0.14; body.scale.set(s, s, s); };
  return { g, setValue };
}

/** A5. Phổi 3D: khí quản + 2 lá phổi phồng/xẹp theo value. */
export function lungs(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.42, color = 'accent_hi' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r * 0.12, r * 0.12, r * 0.9, 16), 'white', 0, r * 1.45, 0, g);
  const lobes = [];
  for (const s of [-1, 1]) {
    const lb = ctx.group(g, s * r * 0.55, r * 0.85, 0);
    const m = ctx.add(new THREE.SphereGeometry(r * 0.48, 24, 18), color, 0, 0, 0, lb);
    m.scale.set(0.85, 1.45, 0.75);
    lobes.push(lb);
  }
  const setValue = (v = 0) => {
    const k = 1 + 0.18 * Math.sin(v * Math.PI * 2);
    lobes.forEach((lb) => lb.scale.set(k, k, k));
  };
  return { g, setValue };
}

/** A6. Bộ não 3D: 2 bán cầu đại não + các nếp gấp cuộn não nổi rõ bên ngoài + tiểu não + cuống não. */
export function brain(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.38, color = 'white' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const core = ctx.group(g, 0, r * 0.95, 0);
  for (const s of [-1, 1]) {
    const h = ctx.add(new THREE.SphereGeometry(r * 0.56, 28, 20), color, s * r * 0.33, r * 0.05, 0, core);
    h.scale.set(0.76, 0.84, 1.15);
    // Nếp gấp hồi não (gyri) nổi rõ trên bề mặt ngoài để shader mực vẽ đường cuộn não thật
    const gyri = [
      [s * r * 0.42, r * 0.28, r * 0.18, 0.35, 0.2, 0.45 * s],
      [s * r * 0.48, r * 0.05, r * 0.34, -0.25, 0.4 * s, -0.3 * s],
      [s * r * 0.45, -r * 0.08, -r * 0.12, 0.4, -0.3 * s, 0.5 * s],
      [s * r * 0.34, r * 0.36, -r * 0.22, -0.35, 0.15, -0.35 * s],
    ];
    for (const [gx, gy, gz, rx, ry, rz] of gyri) {
      const cap = ctx.add(new THREE.CapsuleGeometry(r * 0.11, r * 0.28, 6, 12), color, gx, gy, gz, core);
      cap.rotation.set(rx, ry, rz);
    }
    // Tiểu não (cerebellum) ở phía sau dưới
    const cb = ctx.add(new THREE.SphereGeometry(r * 0.26, 20, 14), color, s * r * 0.24, -r * 0.36, -r * 0.32, core);
    cb.scale.set(0.95, 0.72, 0.88);
  }
  // Cuống não (brain stem)
  const stem = ctx.add(new THREE.CylinderGeometry(r * 0.12, r * 0.09, r * 0.38, 16), color, 0, -r * 0.56, -r * 0.2, core);
  stem.rotation.x = 0.22;
  const gl = ctx.glow('accent', r * 2.1, core, 0, 0, 0, 0.18);
  const setValue = (v = 0) => { gl.material.opacity = 0.15 + 0.45 * Math.abs(Math.sin(v * Math.PI * 2)); };
  return { g, setValue };
}

/** A7. Tế bào / hồng cầu 3D: đĩa lõm 2 mặt, phồng/teo theo value. */
export function cell(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.34, color = 'danger' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const body = ctx.group(g, 0, r * 0.5, 0);
  const tr = ctx.add(new THREE.TorusGeometry(r * 0.68, r * 0.28, 18, 40), color, 0, 0, 0, body);
  tr.rotation.x = Math.PI / 2;
  ctx.add(new THREE.CylinderGeometry(r * 0.58, r * 0.58, r * 0.22, 32), color, 0, 0, 0, body);
  const setValue = (v = 0) => { body.scale.set(1 + v * 0.25, 1 + v * 0.45, 1 + v * 0.25); };
  return { g, setValue };
}

/** A8. Huy chương 3D + Cúp 3D + Đường chạy 3D. */
export function medal(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.28 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  for (const s of [-1, 1]) {
    const rb = ctx.add(new THREE.BoxGeometry(r * 0.36, r * 1.1, 0.03), 'accent', s * r * 0.26, r * 1.45, -0.02, g);
    rb.rotation.z = s * 0.24;
  }
  ctx.add(new THREE.CylinderGeometry(r, r, 0.07, 40), 'orange', 0, r * 0.85, 0, g).rotation.x = Math.PI / 2;
  ctx.add(new THREE.CylinderGeometry(r * 0.76, r * 0.76, 0.08, 6), 'white', 0, r * 0.85, 0, g).rotation.x = Math.PI / 2;
  return { g };
}

export function trophy(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, h = 0.78 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(h * 0.44, h * 0.16, h * 0.44), 'iron', 0, h * 0.08, 0, g);
  ctx.add(new THREE.CylinderGeometry(h * 0.07, h * 0.11, h * 0.28, 20), 'orange', 0, h * 0.3, 0, g);
  ctx.add(new THREE.CylinderGeometry(h * 0.28, h * 0.14, h * 0.44, 32), 'orange', 0, h * 0.64, 0, g);
  for (const s of [-1, 1]) {
    const hd = ctx.add(new THREE.TorusGeometry(h * 0.13, h * 0.03, 12, 24), 'orange', s * h * 0.24, h * 0.64, 0, g);
    hd.rotation.z = Math.PI / 2;
  }
  return { g };
}

export function track(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 4.2, d = 1.8 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const tTex = HAS_DOM && ctx.P && ctx.P.tartanTrack ? ctx.P.tex(ctx.P.tartanTrack(21, '#B44530', '#F4F1EA', 256, 4), Math.max(1, Math.round(w / 1.8)), 1) : null;
  ctx.add(new THREE.BoxGeometry(w, 0.08, d), tTex ? ctx.toon('#ffffff', { map: tTex }) : '#B44530', 0, 0.04, 0, g);
  ctx.add(new THREE.BoxGeometry(w, 0.11, 0.06), 'white', 0, 0.055, -d / 2 - 0.03, g);
  ctx.add(new THREE.BoxGeometry(w, 0.11, 0.06), 'white', 0, 0.055, d / 2 + 0.03, g);
  return { g };
}

/** B1–B6. Đạo cụ Strength & Fitness: dumbbell, barbell (uốn cong theo value), kettlebell, weightplate, shaker, muscle. */
export function dumbbell(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 0.72, r = 0.22 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const bar = ctx.add(new THREE.CylinderGeometry(0.032, 0.032, w, 16), 'metal', 0, r, 0, g);
  bar.rotation.z = Math.PI / 2;
  for (const s of [-1, 1]) {
    for (const [dx, pr, col] of [[0.22, r, 'iron'], [0.3, r * 0.84, 'accent']]) {
      const p = ctx.add(new THREE.CylinderGeometry(pr, pr, 0.065, 8), col, s * dx, r, 0, g);
      p.rotation.z = Math.PI / 2;
    }
  }
  return { g };
}

export function barbell(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 1.9, r = 0.34 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const bar = ctx.add(new THREE.CylinderGeometry(0.028, 0.028, w, 20), 'metal', 0, r, 0, g);
  bar.rotation.z = Math.PI / 2;
  const ends = [];
  for (const s of [-1, 1]) {
    const eg = ctx.group(g, s * w * 0.38, r, 0);
    for (const [dx, pr, col] of [[0, r, 'iron'], [s * 0.075, r * 0.88, 'accent'], [s * 0.14, r * 0.74, 'danger']]) {
      const p = ctx.add(new THREE.CylinderGeometry(pr, pr, 0.06, 32), col, dx, 0, 0, eg);
      p.rotation.z = Math.PI / 2;
    }
    ends.push({ eg, s });
  }
  const setValue = (v = 0) => { ends.forEach(({ eg, s }) => { eg.position.y = r - v * 0.12; eg.rotation.z = -s * v * 0.18; }); };
  return { g, setValue };
}

export function kettlebell(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.28 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.SphereGeometry(r, 28, 20), 'iron', 0, r * 0.92, 0, g);
  ctx.add(new THREE.CylinderGeometry(r * 0.72, r * 0.72, 0.05, 24), 'accent', 0, r * 1.45, 0, g);
  ctx.add(new THREE.TorusGeometry(r * 0.58, r * 0.13, 14, 32, Math.PI), 'metal', 0, r * 1.72, 0, g);
  return { g };
}

export function weightplate(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.36 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r, r, 0.08, 36), 'iron', 0, r, 0, g).rotation.x = Math.PI / 2;
  ctx.add(new THREE.TorusGeometry(r * 0.72, 0.022, 12, 36), 'accent', 0, r, 0.04, g);
  ctx.add(new THREE.CylinderGeometry(r * 0.24, r * 0.24, 0.09, 24), 'metal', 0, r, 0, g).rotation.x = Math.PI / 2;
  return { g };
}

export function shaker(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.2, h = 0.66, water = 0.65 } = {}) {
  return bottle(ctx, { parent, x, y, z, r, h, water, color: 'accent' });
}

export function muscle(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.34 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r * 0.34, r * 0.38, r * 1.2, 20), 'white', -r * 0.3, r * 0.45, 0, g).rotation.z = Math.PI / 2;
  const bi = ctx.add(new THREE.SphereGeometry(r * 0.52, 24, 18), 'danger', -r * 0.25, r * 0.78, 0, g);
  const fa = ctx.group(g, r * 0.25, r * 0.45, 0);
  ctx.add(new THREE.CylinderGeometry(r * 0.3, r * 0.34, r * 1.1, 20), 'white', 0, r * 0.45, 0, fa);
  ctx.add(new THREE.SphereGeometry(r * 0.38, 18, 14), 'accent', 0, r * 1.05, 0, fa);
  const setValue = (v = 0) => {
    const s = 1 + v * 0.38; bi.scale.set(s, s, s); fa.rotation.z = v * 0.45;
  };
  setValue(0.3);
  return { g, setValue };
}

/** C1–C4. Đạo cụ AI Visual & Motion: camera, clapper, screen, waveform. */
export function camera(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, s = 1 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(0.54 * s, 0.38 * s, 0.42 * s), 'iron', 0, 0.24 * s, 0, g);
  const lens = ctx.add(new THREE.CylinderGeometry(0.16 * s, 0.14 * s, 0.26 * s, 32), 'metal', 0, 0.24 * s, 0.28 * s, g);
  lens.rotation.x = Math.PI / 2;
  ctx.add(new THREE.TorusGeometry(0.15 * s, 0.02 * s, 12, 32), 'accent', 0, 0.24 * s, 0.4 * s, g);
  for (const dx of [-0.14, 0.14]) {
    ctx.add(new THREE.CylinderGeometry(0.13 * s, 0.13 * s, 0.08 * s, 28), 'white', dx * s, 0.54 * s, 0, g).rotation.z = Math.PI / 2;
  }
  ctx.add(new THREE.SphereGeometry(0.035 * s, 12, 10), 'danger', 0.2 * s, 0.38 * s, 0.22 * s, g);
  return { g };
}

export function clapper(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 0.72, h = 0.54 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(w, h, 0.05), 'board', 0, h / 2, 0, g);
  ctx.add(new THREE.BoxGeometry(w, 0.09, 0.06), 'white', 0, h + 0.045, 0, g);
  const top = ctx.group(g, -w / 2, h + 0.09, 0);
  ctx.add(new THREE.BoxGeometry(w, 0.09, 0.06), 'accent', w / 2, 0.045, 0, top);
  const setValue = (v = 0) => { top.rotation.z = Math.max(0, (1 - v) * 0.52); };
  setValue(0.3);
  return { g, setValue };
}

export function screen(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 1.15, h = 0.76, text = '' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(0.36, 0.05, 0.26), 'metal', 0, 0.025, 0, g);
  ctx.add(new THREE.BoxGeometry(0.08, 0.2, 0.06), 'metal', 0, 0.12, -0.02, g);
  ctx.add(new THREE.BoxGeometry(w + 0.08, h + 0.08, 0.06), 'iron', 0, 0.22 + h / 2, 0, g);
  ctx.add(new THREE.BoxGeometry(w, h, 0.02), 'board', 0, 0.22 + h / 2, 0.025, g);
  for (let i = 0; i < 3; i++) {
    ctx.add(new THREE.BoxGeometry(w * (0.7 - i * 0.15), 0.045, 0.02), i === 0 ? 'accent' : 'white', -w * 0.08, 0.22 + h * (0.72 - i * 0.2), 0.04, g);
  }
  const tp = text ? ctx.textPlane({ text, px: 140, color: 'chalk', font: ctx.job?.font_family || 'sans-serif', w: 1024, h: 512 }, w * 0.88, h * 0.45, g, 0, 0.22 + h * 0.35, 0.045) : null;
  return { g, set: tp ? { text: (v) => tp.userData.setText(v) } : {} };
}

export function waveform(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 1.2, h = 0.58, bars = 9 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const list = [];
  for (let i = 0; i < bars; i++) {
    const bx = (i / (bars - 1) - 0.5) * w;
    const m = ctx.add(new THREE.CylinderGeometry(0.032, 0.032, h, 16), i % 2 ? 'white' : 'accent', bx, h / 2, 0, g);
    list.push(m);
  }
  const setValue = (v = 0) => {
    list.forEach((m, i) => {
      const k = 0.25 + 0.75 * Math.abs(Math.sin(v * Math.PI * 2 + i * 0.7));
      m.scale.y = k; m.position.y = (h * k) / 2;
    });
  };
  setValue(0.2);
  return { g, setValue };
}

/** D1–D9. Đạo cụ Developer Tech & AI Tools: laptop, server, bug, database, phone, battery, chip, lock, key. */
export function laptop(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 0.88, d = 0.58 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(w, 0.04, d), 'metal', 0, 0.02, 0, g);
  ctx.add(new THREE.BoxGeometry(w * 0.88, 0.015, d * 0.58), 'iron', 0, 0.042, -0.04, g);
  const lid = ctx.group(g, 0, 0.04, -d / 2 + 0.02);
  ctx.add(new THREE.BoxGeometry(w, d * 0.92, 0.03), 'metal', 0, d * 0.46, 0, lid);
  ctx.add(new THREE.BoxGeometry(w * 0.92, d * 0.82, 0.02), 'board', 0, d * 0.46, 0.012, lid);
  for (let i = 0; i < 3; i++) ctx.add(new THREE.BoxGeometry(w * (0.6 - i * 0.12), 0.03, 0.015), i === 0 ? 'accent' : 'white', -w * 0.12, d * (0.66 - i * 0.16), 0.025, lid);
  const setValue = (v = 1) => { lid.rotation.x = -(1 - Math.max(0, Math.min(1, v))) * 1.45 - 0.18; };
  setValue(1);
  return { g, setValue };
}

export function server(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 0.62, h = 0.96, d = 0.52 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(w, h, d), 'iron', 0, h / 2, 0, g);
  for (let i = 0; i < 4; i++) {
    const by = 0.14 + i * (h * 0.21);
    ctx.add(new THREE.BoxGeometry(w * 0.9, h * 0.16, 0.03), 'metal', 0, by, d / 2 + 0.005, g);
    ctx.add(new THREE.SphereGeometry(0.024, 12, 10), i === 0 ? 'danger' : 'accent', w * 0.34, by, d / 2 + 0.025, g);
  }
  return { g };
}

export function bug(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.28 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const body = ctx.add(new THREE.SphereGeometry(r, 24, 18), 'danger', 0, r * 0.85, 0, g);
  body.scale.set(0.85, 0.7, 1.15);
  ctx.add(new THREE.BoxGeometry(0.025, r * 0.8, r * 2.1), 'iron', 0, r * 1.1, 0, g);
  ctx.add(new THREE.SphereGeometry(r * 0.45, 20, 16), 'iron', 0, r * 0.82, r * 0.95, g);
  for (const s of [-1, 1]) {
    for (const zOff of [-0.5, 0, 0.5]) {
      const lg = ctx.add(new THREE.CylinderGeometry(0.02, 0.016, r * 1.1, 10), 'white', s * r * 0.95, r * 0.45, zOff * r, g);
      lg.rotation.z = s * 0.85;
    }
  }
  return { g };
}

export function database(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.34, h = 0.78 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  for (let i = 0; i < 3; i++) {
    const cy = 0.14 + i * (h * 0.33);
    ctx.add(new THREE.CylinderGeometry(r, r, h * 0.26, 36), 'metal', 0, cy, 0, g);
    ring(ctx, r + 0.008, 0.016, g, cy, 'accent');
  }
  return { g };
}

export function phone(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 0.44, h = 0.88 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(w, h, 0.06), 'metal', 0, h / 2, 0, g);
  ctx.add(new THREE.BoxGeometry(w * 0.9, h * 0.9, 0.02), 'board', 0, h / 2, 0.025, g);
  ctx.add(new THREE.BoxGeometry(w * 0.32, 0.025, 0.025), 'accent', 0, h * 0.88, 0.03, g);
  return { g };
}

export function battery(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.24, h = 0.72, value = 0.75 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r, r, 0.06, 32), 'metal', 0, 0.03, 0, g);
  ctx.add(new THREE.CylinderGeometry(r, r, 0.06, 32), 'metal', 0, h - 0.03, 0, g);
  ctx.add(new THREE.CylinderGeometry(r * 0.38, r * 0.38, 0.06, 20), 'metal', 0, h + 0.03, 0, g);
  const sides = ctx.group(g); sides.userData.facing = true;
  for (const s of [-1, 1]) rod(ctx, [s * r, 0.05, 0], [s * r, h - 0.05, 0], 0.016, 'white', sides);
  const coreM = ctx.toon('accent');
  const core = ctx.add(new THREE.CylinderGeometry(r * 0.86, r * 0.86, 1, 32), coreM, 0, 0, 0, g);
  const lowC = new THREE.Color(ctx.C('danger')), hiC = new THREE.Color(ctx.C('accent'));
  const setValue = (v = 0.75) => {
    const k = Math.max(0.05, Math.min(1, v)), ch = (h - 0.14) * k;
    core.scale.y = ch; core.position.y = 0.07 + ch / 2;
    coreM.color.copy(lowC).lerp(hiC, k);
  };
  setValue(value);
  return { g, setValue };
}

export function chip(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, w = 0.64 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(w, 0.08, w), 'iron', 0, 0.06, 0, g);
  ctx.add(new THREE.BoxGeometry(w * 0.62, 0.04, w * 0.62), 'accent', 0, 0.11, 0, g);
  for (let i = -2; i <= 2; i++) {
    const o = i * w * 0.18;
    ctx.add(new THREE.BoxGeometry(w * 1.18, 0.025, 0.04), 'metal', 0, 0.04, o, g);
    ctx.add(new THREE.BoxGeometry(0.04, 0.025, w * 1.18), 'metal', o, 0.04, 0, g);
  }
  return { g };
}

export function lock(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.28 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(r * 1.7, r * 1.4, r * 0.7), 'accent', 0, r * 0.7, 0, g);
  ctx.add(new THREE.CylinderGeometry(r * 0.16, r * 0.16, r * 0.75, 16), 'iron', 0, r * 0.75, 0, g).rotation.x = Math.PI / 2;
  const shackle = ctx.group(g, r * 0.45, r * 1.4, 0);
  ctx.add(new THREE.TorusGeometry(r * 0.45, r * 0.12, 14, 32, Math.PI), 'metal', -r * 0.45, 0, 0, shackle);
  const setValue = (v = 0) => { shackle.position.y = r * (1.4 + v * 0.25); shackle.rotation.y = v * 0.6; };
  return { g, setValue };
}

export function key(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, len = 0.68 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.TorusGeometry(len * 0.22, 0.04, 14, 32), 'accent', -len * 0.3, len * 0.25, 0, g);
  ctx.add(new THREE.CylinderGeometry(0.032, 0.032, len * 0.65, 16), 'accent', len * 0.12, len * 0.25, 0, g).rotation.z = Math.PI / 2;
  ctx.add(new THREE.BoxGeometry(0.06, 0.12, 0.04), 'accent', len * 0.28, len * 0.17, 0, g);
  ctx.add(new THREE.BoxGeometry(0.06, 0.09, 0.04), 'accent', len * 0.39, len * 0.19, 0, g);
  return { g };
}

/** Phòng thí nghiệm & Khoa học / Tự nhiên / Vũ trụ: beaker, flask, burner, syringe, anvil, pendulum, flame, drop, magnet, rocket, planet, clock, hourglass. */
export function beaker(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.32, h = 0.72, water = 0.58 } = {}) {
  return glass(ctx, { parent, x, y, z, r, h, water });
}

export function flask(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.38, h = 0.78, water = 0.52, color = 'accent' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const bodyH = h * 0.65, neckR = r * 0.34;
  ring(ctx, r, 0.018, g, 0.02); ring(ctx, neckR, 0.018, g, bodyH); ring(ctx, neckR * 1.15, 0.02, g, h);
  const sides = ctx.group(g); sides.userData.facing = true;
  for (const s of [-1, 1]) {
    rod(ctx, [s * r, 0.02, 0], [s * neckR, bodyH, 0], 0.018, 'white', sides);
    rod(ctx, [s * neckR, bodyH, 0], [s * neckR, h, 0], 0.018, 'white', sides);
  }
  const liqH = bodyH * Math.max(0.08, Math.min(0.95, water));
  const topR = r + (neckR - r) * (liqH / bodyH);
  ctx.add(new THREE.CylinderGeometry(topR * 0.92, r * 0.92, liqH, 36), color, 0, liqH / 2 + 0.02, 0, g, { cast: false });
  return { g, sides };
}

export function flame(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.28, h = 0.68 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const outer = ctx.group(g, 0, 0, 0);
  // Ngọn lửa 3 lưỡi bốc lên: thân chính + 2 lưỡi phụ nghiêng + lõi sáng bên trong (không dùng cầu tròn ở đáy giống giọt nước)
  const base = ctx.add(new THREE.SphereGeometry(r * 0.78, 20, 14), 'danger', 0, r * 0.55, 0, outer);
  base.scale.set(1.0, 0.72, 0.85);
  const mainT = ctx.add(new THREE.ConeGeometry(r * 0.78, h, 20), 'danger', 0, r * 0.48 + h * 0.45, 0, outer);
  mainT.rotation.z = -0.06;
  const sideL = ctx.add(new THREE.ConeGeometry(r * 0.46, h * 0.72, 16), 'danger', -r * 0.44, r * 0.38 + h * 0.3, 0.02, outer);
  sideL.rotation.z = 0.32;
  const sideR = ctx.add(new THREE.ConeGeometry(r * 0.42, h * 0.64, 16), 'danger', r * 0.42, r * 0.35 + h * 0.26, -0.02, outer);
  sideR.rotation.z = -0.36;
  const core = ctx.add(new THREE.ConeGeometry(r * 0.44, h * 0.62, 16), 'accent', 0, r * 0.42 + h * 0.28, r * 0.14, outer);
  core.rotation.z = 0.04;
  ctx.glow('danger', r * 3.2, g, 0, r * 0.6 + h * 0.3, 0, 0.45);
  const setValue = (v = 1) => {
    const s = Math.max(0.1, v);
    outer.scale.set(s, s * (1 + 0.12 * Math.sin(v * 18)), s);
  };
  return { g, setValue };
}

export function burner(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.24, h = 0.52 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r * 0.6, r, 0.08, 28), 'iron', 0, 0.04, 0, g);
  ctx.add(new THREE.CylinderGeometry(0.045, 0.055, h, 20), 'metal', 0, h / 2 + 0.04, 0, g);
  const fl = flame(ctx, { parent: g, x: 0, y: h + 0.04, z: 0, r: 0.14, h: 0.36 });
  return { g, setValue: fl.setValue };
}

export function syringe(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.12, h = 0.72, value = 0.65 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(0.01, 0.01, 0.22, 10), 'metal', 0, 0.11, 0, g);
  ctx.add(new THREE.CylinderGeometry(r, r, h, 24), 'white', 0, 0.22 + h / 2, 0, g);
  const liq = ctx.add(new THREE.CylinderGeometry(r * 0.82, r * 0.82, 1, 20), 'accent', 0, 0, 0, g);
  const pl = ctx.group(g, 0, 0.22 + h, 0);
  ctx.add(new THREE.CylinderGeometry(0.025, 0.025, h * 0.65, 12), 'metal', 0, h * 0.3, 0, pl);
  ctx.add(new THREE.CylinderGeometry(r * 1.15, r * 1.15, 0.04, 20), 'accent', 0, h * 0.62, 0, pl);
  const setValue = (v = 0.65) => {
    const k = Math.max(0.05, Math.min(1, v)), lh = h * 0.85 * k;
    liq.scale.y = lh; liq.position.y = 0.24 + lh / 2;
    pl.position.y = 0.24 + lh;
  };
  setValue(value);
  return { g, setValue };
}

export function anvil(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, s = 1 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(0.62 * s, 0.12 * s, 0.34 * s), 'iron', 0, 0.06 * s, 0, g);
  ctx.add(new THREE.BoxGeometry(0.38 * s, 0.2 * s, 0.26 * s), 'iron', 0, 0.2 * s, 0, g);
  ctx.add(new THREE.BoxGeometry(0.68 * s, 0.16 * s, 0.32 * s), 'iron', 0.06 * s, 0.36 * s, 0, g);
  const horn = ctx.add(new THREE.ConeGeometry(0.14 * s, 0.36 * s, 20), 'iron', -0.42 * s, 0.36 * s, 0, g);
  horn.rotation.z = Math.PI / 2;
  return { g };
}

export function pendulum(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, h = 1.15, r = 0.18 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.BoxGeometry(0.6, 0.06, 0.16), 'metal', 0, h, 0, g);
  const piv = ctx.group(g, 0, h, 0);
  rod(ctx, [0, 0, 0], [0, -h + r + 0.08, 0], 0.014, 'white', piv);
  ctx.add(new THREE.SphereGeometry(r, 28, 20), 'accent', 0, -h + r + 0.08, 0, piv);
  const setValue = (v = 0) => { piv.rotation.z = (Math.abs(v) <= 1.5 ? Math.sin(v * Math.PI * 2) * 35 : v) * Math.PI / 180; };
  return { g, setValue, setTilt: setValue };
}

export function drop(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.24, color = 'water' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.SphereGeometry(r, 24, 18), color, 0, r, 0, g);
  ctx.add(new THREE.ConeGeometry(r * 0.92, r * 1.4, 24), color, 0, r * 1.85, 0, g);
  return { g };
}

export function magnet(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.32 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const tr = ctx.add(new THREE.TorusGeometry(r, r * 0.28, 16, 32, Math.PI), 'danger', 0, r * 1.1, 0, g);
  tr.rotation.z = Math.PI;
  for (const s of [-1, 1]) {
    ctx.add(new THREE.CylinderGeometry(r * 0.28, r * 0.28, r * 0.55, 20), 'danger', s * r, r * 1.35, 0, g);
    ctx.add(new THREE.CylinderGeometry(r * 0.285, r * 0.285, r * 0.28, 20), 'white', s * r, r * 1.72, 0, g);
  }
  return { g };
}

export function rocket(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.24, h = 0.92 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r * 0.85, r, h * 0.62, 28), 'white', 0, h * 0.42, 0, g);
  ctx.add(new THREE.ConeGeometry(r * 0.85, h * 0.32, 28), 'danger', 0, h * 0.89, 0, g);
  ctx.add(new THREE.CylinderGeometry(r * 0.38, r * 0.38, 0.06, 20), 'accent', 0, h * 0.52, r * 0.85, g).rotation.x = Math.PI / 2;
  for (let i = 0; i < 3; i++) {
    const a = i / 3 * Math.PI * 2;
    const fin = ctx.add(new THREE.BoxGeometry(0.04, h * 0.28, r * 0.85), 'danger', Math.sin(a) * r, h * 0.18, Math.cos(a) * r, g);
    fin.rotation.y = a;
  }
  return { g };
}

export function planet(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.42, color = 'accent' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.SphereGeometry(r, 32, 24), color, 0, r * 1.15, 0, g);
  const rg = ctx.add(new THREE.TorusGeometry(r * 1.55, r * 0.12, 12, 48), 'white', 0, r * 1.15, 0, g);
  rg.rotation.set(1.25, 0.35, 0);
  return { g };
}

export function clock(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.4 } = {}) {
  return stopwatch(ctx, { parent, x, y, z, r });
}

export function hourglass(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.28, h = 0.78, value = 0.5 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  ctx.add(new THREE.CylinderGeometry(r * 1.1, r * 1.1, 0.06, 32), 'metal', 0, 0.03, 0, g);
  ctx.add(new THREE.CylinderGeometry(r * 1.1, r * 1.1, 0.06, 32), 'metal', 0, h - 0.03, 0, g);
  for (let i = 0; i < 3; i++) {
    const a = i / 3 * Math.PI * 2;
    rod(ctx, [Math.cos(a) * r, 0.04, Math.sin(a) * r], [Math.cos(a) * r, h - 0.04, Math.sin(a) * r], 0.016, 'metal', g);
  }
  const topC = ctx.add(new THREE.ConeGeometry(r * 0.78, h * 0.4, 28), 'orange', 0, h * 0.7, 0, g);
  topC.rotation.x = Math.PI;
  const botC = ctx.add(new THREE.ConeGeometry(r * 0.78, h * 0.4, 28), 'orange', 0, h * 0.24, 0, g);
  const setValue = (v = 0.5) => {
    const k = Math.max(0.05, Math.min(0.95, v));
    topC.scale.set(1 - k * 0.6, 1 - k * 0.75, 1 - k * 0.6);
    botC.scale.set(0.3 + k * 0.7, 0.25 + k * 0.75, 0.3 + k * 0.7);
  };
  setValue(value);
  return { g, setValue };
}

// ===========================================================================
// ĐẠO CỤ TỔ HỢP 3D (`parts`) & CHUYỂN ĐỔI 189 ICON KÊNH SANG KHỐI 3D (`icon3d`)
// ===========================================================================

const ROLE_COLOR = { ink: 'white', dim: 'metal', hot: 'danger', cold: 'water', accent: 'accent', bg: 'iron' };

/** Dựng prop 3D từ mảng `parts: [{k: 'box'|'sphere'|'cylinder'|'cone'|'torus'|'rod', at, rot, size, r, h, color}]`. */
export function partsProp(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, parts = [], color = 'white' } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z), deg = (v) => (v || 0) * Math.PI / 180;
  for (const q of parts) {
    const col = ROLE_COLOR[q.role] || q.color || color || 'white';
    const [px, py, pz] = q.at || [q.x || 0, q.y || 0, q.z || 0];
    let m = null;
    if (q.k === 'box' || q.k === 'rect') {
      const [w, h, d] = q.size || [q.w ?? 0.3, q.h ?? 0.3, q.d ?? 0.14];
      m = ctx.add(new THREE.BoxGeometry(w, h, d), col, px, py, pz, g);
    } else if (q.k === 'sphere' || q.k === 'circle') {
      m = ctx.add(new THREE.SphereGeometry(q.r ?? 0.16, 24, 18), col, px, py, pz, g);
    } else if (q.k === 'cylinder') {
      m = ctx.add(new THREE.CylinderGeometry(q.r ?? 0.12, q.r2 ?? q.r ?? 0.12, q.h ?? 0.36, 24), col, px, py, pz, g);
    } else if (q.k === 'cone') {
      m = ctx.add(new THREE.ConeGeometry(q.r ?? 0.15, q.h ?? 0.38, 24), col, px, py, pz, g);
    } else if (q.k === 'torus' || q.k === 'arc') {
      m = ctx.add(new THREE.TorusGeometry(q.r ?? 0.2, q.tube ?? 0.035, 12, 36), col, px, py, pz, g);
    } else if (q.k === 'rod' && q.a && q.b) {
      m = rod(ctx, q.a, q.b, q.r ?? 0.02, col, g);
    }
    if (m && q.rot) m.rotation.set(deg(q.rot[0]), deg(q.rot[1]), deg(q.rot[2]));
  }
  return { g };
}

/** Chuyển bất kỳ icon nào trong 189 icon của `engines/html/icons.js` sang khối 3D nổi (Extrude/Cylinder/Box/Torus/Rod). */
export function icon3d(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, icon = 'dot', s = 0.42, value = 0.5 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  // icon = tên trong thư viện html, hoặc {parts:[…]} (icon tự ghép / SVG nhập bằng `studio.py svg`, có thể có holes)
  const fn = icon && typeof icon === 'object' ? () => icon.parts || [] : ICONS[icon] || ICONS[iconFor(icon)] || ICONS.dot;
  const tube = (pts, closed, w, col, zOff) => {        // nét nhiều điểm (SVG) → MỘT ống liền thay vì hàng trăm thanh
    const v = pts.map(([px, py]) => new THREE.Vector3(px * s, -py * s, zOff));
    if (v.length < 2) return;
    const curve = new THREE.CatmullRomCurve3(v, closed, 'catmullrom', 0);
    ctx.add(new THREE.TubeGeometry(curve, Math.min(600, v.length * 3), 0.026 * s * (w || 1), 8, closed), col, 0, 0, 0, center);
  };
  const center = ctx.group(g, 0, s, 0);
  const buildAt = (pVal = 0.5, f = 0) => {
    while (center.children.length) center.remove(center.children[0]);
    const prims = fn({ f, p: pVal }) || [];
    prims.forEach((q, idx) => {
      const col = ROLE_COLOR[q.role] || 'white';
      const zOff = idx * 0.014, depth = 0.09;
      if (q.k === 'circle') {
        const r = Math.max(0.02, (q.r || 0.2) * s);
        if (q.fill === false) {
          ctx.add(new THREE.TorusGeometry(r, 0.022 * s, 10, 32), col, (q.x || 0) * s, -(q.y || 0) * s, zOff, center);
        } else {
          const m = ctx.add(new THREE.CylinderGeometry(r, r, depth, 28), col, (q.x || 0) * s, -(q.y || 0) * s, zOff, center);
          m.rotation.x = Math.PI / 2;
        }
      } else if (q.k === 'rect') {
        const w = Math.max(0.02, (q.w || 0.2) * s), h = Math.max(0.02, (q.h || 0.2) * s);
        const cx = ((q.x || 0) + (q.w || 0) / 2) * s, cy = -((q.y || 0) + (q.h || 0) / 2) * s;
        ctx.add(new THREE.BoxGeometry(w, h, depth), col, cx, cy, zOff, center);
      } else if (q.k === 'poly' && q.pts && q.pts.length >= 3 && q.fill === false) {
        tube(q.pts, true, q.w, col, zOff);
      } else if (q.k === 'poly' && q.pts && q.pts.length >= 3) {
        const sh = new THREE.Shape();
        q.pts.forEach(([px, py], i) => { if (i === 0) sh.moveTo(px * s, -py * s); else sh.lineTo(px * s, -py * s); });
        sh.closePath();
        for (const h of q.holes || []) {                // lỗ thật khi ép khối (chữ O, bánh răng…)
          const hp = new THREE.Path();
          h.forEach(([px, py], i) => { if (i === 0) hp.moveTo(px * s, -py * s); else hp.lineTo(px * s, -py * s); });
          hp.closePath(); sh.holes.push(hp);
        }
        const geo = new THREE.ExtrudeGeometry(sh, { depth, bevelEnabled: false });
        geo.translate(0, 0, -depth / 2);
        ctx.add(geo, col, 0, 0, zOff, center);
      } else if (q.k === 'line' && q.pts && q.pts.length > 6) {
        tube(q.pts, false, q.w, col, zOff);
      } else if (q.k === 'line' && q.pts && q.pts.length >= 2) {
        for (let i = 0; i < q.pts.length - 1; i++) {
          const [x0, y0] = q.pts[i], [x1, y1] = q.pts[i + 1];
          if (Math.hypot(x1 - x0, y1 - y0) > 1e-3) {
            rod(ctx, [x0 * s, -y0 * s, zOff], [x1 * s, -y1 * s, zOff], 0.028 * s, col, center);
          }
        }
      } else if (q.k === 'arc') {
        const r = Math.max(0.02, (q.r || 0.2) * s), arc = Math.abs((q.a1 ?? Math.PI) - (q.a0 ?? 0));
        const m = ctx.add(new THREE.TorusGeometry(r, 0.024 * s, 10, 28, arc), col, (q.x || 0) * s, -(q.y || 0) * s, zOff, center);
        m.rotation.z = -(q.a0 || 0);
      }
    });
  };
  buildAt(value, 0);
  return { g, setValue: (v) => buildAt(v, 0) };
}

// ===========================================================================
// HỆ HẠT / HIỆU ỨNG VẬT LÝ 3D (fx3d: steam, smoke, sparks, burst, splash, bubbles, shockwave, fire)
// ===========================================================================

// once = một đợt duy nhất (bụi/tia lúc va chạm của vật lý): mọi hạt xuất phát cùng lúc từ tâm, u 0→1 bay ra rồi tắt;
// mặc định là nguồn phát liên tục (pha hạt lệch nhau, lặp theo u).
export function fx3d(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, kind = 'steam', color = null, r = 0.45, n = 12, once = false } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const col = color || (kind === 'sparks' || kind === 'burst' || kind === 'fire' ? 'danger' : kind === 'splash' || kind === 'bubbles' ? 'water' : kind === 'shockwave' ? 'accent' : 'white');
  const meshes = [];
  if (kind === 'shockwave' || kind === 'ring') {
    const tr = ctx.add(new THREE.TorusGeometry(r, 0.026, 12, 48), col, 0, 0.04, 0, g, { cast: false });
    tr.rotation.x = Math.PI / 2;
    meshes.push(tr);
  } else {
    const geo = kind === 'sparks' || kind === 'burst' ? new THREE.ConeGeometry(0.035, 0.14, 8) : new THREE.SphereGeometry(0.055, 14, 10);
    for (let i = 0; i < n; i++) meshes.push(ctx.add(geo, col, 0, 0, 0, g, { cast: false }));
  }
  const update = (f = 0, u = null) => {
    const t = u !== null && u !== undefined ? u : (f % 36) / 36;
    if (kind === 'shockwave' || kind === 'ring') {
      const m = meshes[0], sc = 0.2 + t * 2.4;
      m.scale.set(sc, sc, Math.max(0.1, 1 - t * 0.8));
      m.visible = t > 0.01 && t < 0.99;
      return;
    }
    meshes.forEach((m, i) => {
      const ph = once ? Math.min(1, t * (0.8 + 0.4 * ((i * 0.618) % 1))) : (t + i / meshes.length) % 1;
      m.visible = !once || (t > 0 && ph < 0.98);
      const a = i * 2.39996;
      if (once && (kind === 'steam' || kind === 'smoke')) {    // bụi va chạm: vòng bụi loang sát sàn rồi tan
        const e = 1 - (1 - ph) * (1 - ph), rad = (0.15 + 0.85 * e) * r * 1.6;
        m.position.set(Math.cos(a) * rad, (0.15 + ((i * 0.37) % 1) * 0.5) * e * r, Math.sin(a) * rad);
        const sc = (0.6 + 0.9 * e) * (1 - ph) * 1.4;
        m.scale.set(sc, sc * 0.8, sc);
        return;
      }
      if (kind === 'steam' || kind === 'smoke') {
        const rad = (0.06 + ph * 0.28) * r * 2;
        m.position.set(Math.cos(a + f * 0.05) * rad, ph * r * 2.2, Math.sin(a + f * 0.05) * rad);
        const sc = Math.sin(ph * Math.PI) * (kind === 'smoke' ? 1.6 : 1.1);
        m.scale.set(sc, sc, sc);
      } else if (kind === 'sparks' || kind === 'burst') {
        const d = ph * r * 2.2;
        m.position.set(Math.cos(a) * d, Math.sin(ph * Math.PI) * r * 1.4 - ph * ph * 0.35, Math.sin(a) * d);
        const sc = Math.max(0.05, 1 - ph);
        m.scale.set(sc, sc, sc);
      } else if (kind === 'splash' || kind === 'drops') {
        const d = (0.15 + ph * 0.85) * r * 1.8;
        m.position.set(Math.cos(a) * d, 4 * ph * (1 - ph) * r * 1.6, Math.sin(a) * d);
        const sc = Math.max(0.1, 1 - ph * 0.6);
        m.scale.set(sc, sc, sc);
      } else if (kind === 'bubbles') {
        const rad = 0.18 * r;
        m.position.set(Math.cos(a + ph * 6) * rad, ph * r * 1.8, Math.sin(a + ph * 6) * rad);
        const sc = 0.4 + 0.6 * Math.sin(ph * Math.PI);
        m.scale.set(sc, sc, sc);
      } else {
        m.position.set(Math.cos(a) * 0.18 * r, ph * r * 1.5, Math.sin(a) * 0.18 * r);
        const sc = Math.max(0.1, 1 - ph);
        m.scale.set(sc, sc * 1.6, sc);
      }
    });
  };
  update(0, 0);
  return { g, update, setValue: (v) => update(0, v) };
}

// ===========================================================================
// THIÊN NHIÊN NHỎ (flower · tuft · rock · tree · bush) + BỐI CẢNH (set) meadow · tabletop · street
// Mọi mép bối cảnh tan vào ĐEN (màu đỉnh giảm dần → sân khấu đen của kênh). Màu: world.colors.<token> của style, nếu
// không có thì SET_COL; set_opts.colors ghi đè từng token. Texture vẽ bằng code (paint.js) qua ctx.lookTex (lọc theo look).
// ===========================================================================
export const SETS = ['black', 'lab', 'track', 'stadium', 'diorama', 'meadow', 'tabletop', 'street'];
/** Mặt đứng của set (prop y đo từ đây, như mặt bàn lab). */
export const setBase = (name, o = {}) => (name === 'lab' ? 0.92 : name === 'tabletop' ? (o.top ?? 0.76) : 0);
const SET_COL = { grass: '#4FA83A', tuft: '#62BE3C', dirt: '#6B4A2E', flower: '#FFD23F', flower_center: '#F08A24', stem: '#3E8E2E',
  rock: '#8E8C88', hill: '#2F7A55', wood: '#A0683A', wood_dark: '#5E3A22', wall: '#3E4A6A', asphalt: '#3A3D44',
  road_line: '#F2D24A', curb: '#9A9893', brick: '#B9785A', window: '#2A3448', window_lit: '#FFD27A', lamp: '#FFE7A0',
  leaf: '#4FA83A', trunk: '#6B4A2E', tartan: '#B84530', track_line: '#F4F1EA', infield: '#2F7D3E', stand: '#232833',
  stadium_base: '#181B22', cone: '#FF7A2F', trail: '#B99264' };
const HAS_DOM = typeof document !== 'undefined';
const setCol = (ctx, o, k) => {
  const own = o && o.colors && o.colors[k];
  const v = own || k, c = ctx.C ? ctx.C(v) : v;
  if (typeof c === 'string' && c[0] === '#' && (c !== v || own)) return c;
  return SET_COL[k] || '#888888';
};
const stex = (ctx, canvas, rx = 1, ry = 1) => (!canvas ? null : ctx.lookTex ? ctx.lookTex(canvas, rx, ry) : ctx.P.tex(canvas, rx, ry));
const hsh = (i, s = 1) => { const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return x - Math.floor(x); };
const sstep = (a, b, x) => { const t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
/** màu đỉnh (xám k 0..1, nhân với màu vật) — bối cảnh mờ dần vào đen */
const fadeGeo = (ctx, geo, fn) => {
  const p = geo.attributes.position, a = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { const k = Math.max(0, Math.min(1, fn(p.getX(i), p.getY(i), p.getZ(i)))); a[i * 3] = a[i * 3 + 1] = a[i * 3 + 2] = k; }
  geo.setAttribute('color', new ctx.THREE.BufferAttribute(a, 3)); return geo;
};
const setMesh = (ctx, geo, m, parent, x = 0, y = 0, z = 0, nd = false) => {
  const me = ctx.add(geo, m, x, y, z, parent); me.castShadow = false; me.receiveShadow = true; if (!nd) me.userData.ndSkip = true; return me;
};
const shadeHexP = (hex, dl) => {
  const n = parseInt(hex.slice(1, 7), 16), k = 1 + dl / 100, ch = (v) => Math.max(0, Math.min(255, Math.round(v * k))).toString(16).padStart(2, '0');
  return `#${ch((n >> 16) & 255)}${ch((n >> 8) & 255)}${ch(n & 255)}`;
};

/** Bông hoa low-poly: thân + lá + 5 cánh dẹt + nhuỵ; mặt hoa nghiêng về phía trước (+Z) cho camera thấy. */
export function flower(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, h = 0.2, color = null, center = null, petals = 5, s = 1, tilt = 0.45 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z), H = h * s;
  const pc = color ? (ctx.C ? ctx.C(color) : color) : setCol(ctx, null, 'flower'), cc = center ? (ctx.C ? ctx.C(center) : center) : setCol(ctx, null, 'flower_center');
  const stem = setCol(ctx, null, 'stem');
  ctx.add(new THREE.CylinderGeometry(0.006 * s, 0.008 * s, H, 5), stem, 0, H / 2, 0, g);
  const leaf = ctx.add(new THREE.SphereGeometry(0.03 * s, 6, 4), stem, 0.02 * s, H * 0.35, 0, g); leaf.scale.set(1, 0.25, 0.5); leaf.rotation.z = 0.5;
  const head = ctx.group(g, 0, H, 0); head.rotation.x = tilt;
  ctx.add(new THREE.SphereGeometry(0.018 * s, 8, 6), cc, 0, 0.006 * s, 0, head).scale.set(1, 0.6, 1);
  for (let i = 0; i < petals; i++) {
    const a = i / petals * Math.PI * 2, pm = ctx.add(new THREE.SphereGeometry(0.022 * s, 8, 5), pc, Math.cos(a) * 0.03 * s, 0, Math.sin(a) * 0.03 * s, head);
    pm.scale.set(1.3, 0.3, 0.75); pm.rotation.y = -a;
  }
  return { g, head, top: H };
}
/** Cụm cỏ: 2 mặt phẳng chéo dán texture cỏ (nền trong suốt) — sprite/mesh đơn giản kiểu thời 90. */
export function tuft(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, h = 0.12, color = null, seed = 1, yaw = 0 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z), col = color ? (ctx.C ? ctx.C(color) : color) : setCol(ctx, null, 'tuft');
  const t = HAS_DOM && ctx.P && ctx.P.tuft ? stex(ctx, ctx.P.tuft(seed % 4 + 1, col, Math.min(64, ctx.texPx || 64))) : null;
  if (!t) { const c = ctx.add(new THREE.ConeGeometry(h * 0.3, h, 5), col, 0, h / 2, 0, g); c.userData.ndSkip = true; return { g }; }
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  const m = ctx.toon('#ffffff', { map: t, alphaTest: 0.5, side: THREE.DoubleSide });
  for (const a of [0, Math.PI / 2]) {
    const me = ctx.add(new THREE.PlaneGeometry(h * 1.2, h), m, 0, h / 2, 0, g); me.rotation.y = yaw + a; me.castShadow = false; me.userData.ndSkip = true;
  }
  return { g };
}
/** Hòn đá low-poly: cầu ít đỉnh, đỉnh lệch tất định theo vị trí (pháp tuyến mượt cho Gouraud). */
export function rock(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.12, color = null, seed = 3 } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z);
  const geo = new THREE.SphereGeometry(r, 7, 5), p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const vx = p.getX(i), vy = p.getY(i), vz = p.getZ(i), k = 0.78 + 0.4 * hsh(Math.round(vx * 997) + Math.round(vy * 557) * 3 + Math.round(vz * 331) * 7, seed);
    p.setXYZ(i, vx * k, vy * k * 0.7, vz * k);
  }
  geo.computeVertexNormals();
  ctx.add(geo, color || setCol(ctx, null, 'rock'), 0, r * 0.35, 0, g);
  return { g };
}
/** Cây low-poly: thân + 3 tầng tán tròn. */
export function tree(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, h = 1.4, color = null } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z), lc = color ? (ctx.C ? ctx.C(color) : color) : setCol(ctx, null, 'leaf');
  ctx.add(new THREE.CylinderGeometry(h * 0.035, h * 0.05, h * 0.5, 6), setCol(ctx, null, 'trunk'), 0, h * 0.25, 0, g);
  [[0.24, 0.5, 0], [0.19, 0.72, 0.03], [0.13, 0.9, -0.02]].forEach(([r, yy, dx]) => { ctx.add(new THREE.SphereGeometry(h * r, 8, 6), lc, dx * h, yy * h, 0, g).scale.set(1, 0.85, 1); });
  return { g };
}
export function bush(ctx, { parent = ctx.world, x = 0, y = 0, z = 0, r = 0.22, color = null } = {}) {
  const { THREE } = ctx, g = ctx.group(parent, x, y, z), lc = color ? (ctx.C ? ctx.C(color) : color) : setCol(ctx, null, 'leaf');
  [[0, 0.6, 0, 1], [-0.7, 0.45, 0.1, 0.75], [0.65, 0.42, -0.1, 0.8]].forEach(([dx, yy, dz, k]) => { ctx.add(new THREE.SphereGeometry(r * k, 8, 6), lc, dx * r, yy * r, dz * r, g); });
  return { g };
}

/** Đĩa mặt đất toạ độ cực (vành lệch tất định) — UV phẳng theo x,z; trả về điểm vành để nối vách. */
function polarDisc(THREE, r, rings, segs, seed, rep) {
  const pos = [], uv = [], idx = [], rim = [];
  pos.push(0, 0, 0); uv.push(0.5 * rep, 0.5 * rep);
  for (let j = 1; j <= rings; j++) for (let i = 0; i < segs; i++) {
    const a = i / segs * Math.PI * 2, jit = 1 + (j === rings ? 0.16 : 0.08 * j / rings) * (hsh(i, seed) - 0.5), rr = r * j / rings * jit;
    const x = Math.cos(a) * rr, z = Math.sin(a) * rr, y = -0.06 * r * sstep(0.62, 1, j / rings);
    pos.push(x, y, z); uv.push((x / (2 * r) + 0.5) * rep, (0.5 - z / (2 * r)) * rep);
    if (j === rings) rim.push([x, y, z]);
  }
  for (let i = 0; i < segs; i++) idx.push(0, 1 + ((i + 1) % segs), 1 + i);
  for (let j = 1; j < rings; j++) for (let i = 0; i < segs; i++) {
    const a = 1 + (j - 1) * segs + i, b = 1 + (j - 1) * segs + (i + 1) % segs, c = 1 + j * segs + i, d = 1 + j * segs + (i + 1) % segs;
    idx.push(a, b, c, b, d, c);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx); geo.computeVertexNormals();
  return { geo, rim };
}
/** Vách đảo: từ vành đĩa xuống đáy (đá/đất), tối dần xuống dưới. */
function cliff(THREE, rim, depth, seed) {
  const pos = [], uv = [], idx = [], n = rim.length, rows = 4;
  for (let k = 0; k <= rows; k++) {
    const t = k / rows;
    rim.forEach(([x, y, z], i) => {
      const s = 1 - 0.62 * Math.pow(t, 0.85) * (0.85 + 0.3 * hsh(i + k * 31, seed)), yy = y - t * depth * (0.8 + 0.4 * hsh(i * 3 + k, seed + 1));
      pos.push(x * s, yy, z * s); uv.push(i / n * 6, t * 1.5);
    });
  }
  for (let k = 0; k < rows; k++) for (let i = 0; i < n; i++) {
    const a = k * n + i, b = k * n + (i + 1) % n, c = (k + 1) * n + i, d = (k + 1) * n + (i + 1) % n;
    idx.push(a, c, b, b, c, d);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx); geo.computeVertexNormals();
  return geo;
}

/**
 * Dựng bối cảnh. name: meadow | tabletop | street (black/lab/track dựng ở stage như cũ).
 * ext = {cx, cz, sx, sz}: tâm + cỡ vùng đặt prop (stage đo) để bối cảnh tự vừa. o = set_opts.
 * → {root, base, frame (gợi ý góc máy), table?}
 */
export function setScene(ctx, name, o = {}, ext = { cx: 0, cz: 0, sx: 1, sz: 1 }) {
  const { THREE } = ctx, root = ctx.group(ctx.world), seed = o.seed ?? 11;
  const tx = (painter, ...a) => (HAS_DOM && ctx.P && ctx.P[painter] ? ctx.P[painter](...a) : null);
  const px = Math.min(128, ctx.texPx || 128);
  const mapMat = (t, k, extra = {}) => ctx.toon(t ? '#ffffff' : setCol(ctx, o, k), { vertexColors: true, ...(t ? { map: t } : {}), ...extra });
  if (name === 'meadow') {
    const span = Math.max(ext.sx, ext.sz);
    const full = o.full === true || (ctx.job && ctx.job.world && ctx.job.world.darkmode_env === true);
    const r = o.r ?? (full ? Math.max(4.5, span * 1.2 + 2.5) : Math.max(0.8, Math.min(5, span * 0.5 + 0.4)));
    root.position.set(o.at ? o.at[0] : ext.cx, 0, o.at ? o.at[1] : ext.cz);
    const { geo, rim } = polarDisc(THREE, r, full ? 12 : 8, 36, seed, Math.max(1, Math.round(r / 0.55)));
    fadeGeo(ctx, geo, full
      ? (x, y, z) => 1 - 0.68 * sstep(0.55 * r, 1.0 * r, Math.hypot(x, z))
      : (x, y, z) => 1 - 0.93 * sstep(0.34 * r, 1.0 * r, Math.hypot(x, z)));
    setMesh(ctx, geo, mapMat(stex(ctx, tx('grass', seed, setCol(ctx, o, 'grass'), px)), 'grass'), root);
    if (!full) {
      const cg = fadeGeo(ctx, cliff(THREE, rim, r * 0.55, seed), (x, y) => 0.16 * Math.pow(Math.max(0, 1 + y / (r * 0.5)), 1.6));
      setMesh(ctx, cg, mapMat(stex(ctx, tx('dirt', seed + 1, setCol(ctx, o, 'dirt'), 64)), 'dirt'), root);
    }
    // rải cụm cỏ / hoa / đá (tất định), né vùng giữa nơi đặt prop
    const keep = Math.max(0.35, Math.min(r * 0.45, span * 0.42));
    const place = (i, s, rmin, rmax) => {
      const a = hsh(i, s) * Math.PI * 2, d = Math.sqrt(rmin * rmin + hsh(i, s + 1) * (rmax * rmax - rmin * rmin));
      return [Math.cos(a) * d, Math.sin(a) * d, d];
    };
    const nT = Math.round(o.grass ?? Math.min(full ? 95 : 70, 9 * r * r)), nF = Math.round(o.flowers ?? Math.min(36, 4 + 3 * r)), nR = Math.round(o.rocks ?? 4);
    for (let i = 0; i < nT; i++) { const [x, z, d] = place(i, seed + 2, keep * 0.6, r * 0.93); tuft(ctx, { parent: root, x, y: -0.06 * r * sstep(0.62 * r, r, d), z, h: 0.07 + 0.08 * hsh(i, seed + 3), seed: i, yaw: hsh(i, 9) * 3 }); }
    for (let i = 0; i < nF; i++) { const [x, z] = place(i, seed + 4, keep, r * 0.85); flower(ctx, { parent: root, x, z, h: 0.1 + 0.1 * hsh(i, seed + 5), color: o.colors && o.colors.flower ? o.colors.flower : null }); }
    for (let i = 0; i < nR; i++) { const [x, z] = place(i, seed + 6, keep * 1.2, r * 0.85); rock(ctx, { parent: root, x, z, r: 0.06 + 0.08 * hsh(i, seed + 7), seed: i }); }
    // đồi xa mờ dần: full (darkmode) thì đồi rõ hơn một chút và nối dài ra chân trời sương tối
    const nH = Math.round(o.hills ?? (full ? 5 : 3)), hc = setCol(ctx, o, 'hill');
    for (let i = 0; i < nH; i++) {
      const hw = 0.8 + r * (0.45 + 0.35 * hsh(i, seed + 8)), hh = 0.18 + r * (full ? 0.22 + 0.18 * hsh(i, seed + 9) : 0.14 + 0.16 * hsh(i, seed + 9));
      const hg = fadeGeo(ctx, new THREE.SphereGeometry(1, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), (x, y) => sstep(0.15, 1, y) * (full ? 0.68 : 0.42));
      const hx = (i - (nH - 1) / 2) * (hw * 1.15) + (hsh(i, seed) - 0.5) * r * 0.4;
      const hm = setMesh(ctx, hg, ctx.toon(hc, { vertexColors: true }), root, hx, -hh * 0.4, -(r * 0.9 + 2.2 + 1.8 * hsh(i, seed + 10)));
      hm.scale.set(hw, hh, hw * 0.5);
    }
    return { root, base: 0, frame: { elev: full ? 10 : 9, margin: full ? 1.2 : 1.3 }, r };
  }
  if (name === 'tabletop') {
    const top = setBase('tabletop', o), w = o.w ?? Math.max(1.8, ext.sx + 1.0), d = o.d ?? Math.max(1.0, ext.sz + 0.7);
    root.position.set(o.at ? o.at[0] : ext.cx, 0, o.at ? o.at[1] : ext.cz);
    const kx = (x) => 1 - 0.8 * sstep(0.3 * w, 0.52 * w, Math.abs(x));
    const topG = new THREE.PlaneGeometry(w, d, 12, 6); topG.rotateX(-Math.PI / 2);
    fadeGeo(ctx, topG, (x, y, z) => kx(x) * (1 - 0.75 * sstep(0.05 * d, 0.5 * d, -z)));
    setMesh(ctx, topG, mapMat(stex(ctx, tx('planks', seed, setCol(ctx, o, 'wood'), px), Math.max(1, Math.round(w / 0.8)), Math.max(1, Math.round(d / 0.8))), 'wood'), root, 0, top, 0);
    const lip = fadeGeo(ctx, new THREE.BoxGeometry(w, 0.05, 0.05, 12, 1, 1), (x) => kx(x) * 0.8);
    setMesh(ctx, lip, ctx.toon(setCol(ctx, o, 'wood_dark'), { vertexColors: true }), root, 0, top - 0.025, d / 2 - 0.02);
    for (const s of [-1, 1]) {
      const lg = fadeGeo(ctx, new THREE.CylinderGeometry(0.035, 0.03, top, 6, 3), (x, y) => 0.55 * sstep(-top / 2, top / 2, y) * kx(s * (w / 2 - 0.12)));
      setMesh(ctx, lg, ctx.toon(setCol(ctx, o, 'wood_dark'), { vertexColors: true }), root, s * (w / 2 - 0.12), top / 2, d / 2 - 0.12);
    }
    if (o.wall !== false) {
      const full = o.full === true || (ctx.job && ctx.job.world && ctx.job.world.darkmode_env === true);
      const wh = full ? 2.4 : 1.9, wc = setCol(ctx, o, 'wall'), wallT = stex(ctx, tx('tilesFlat', seed, wc, shadeHexP(wc, -25), 64, 4), 3, 2);
      const wg = new THREE.PlaneGeometry(w * (full ? 1.9 : 1.5), wh, 12, 6);
      fadeGeo(ctx, wg, (x, y) => (1 - (full ? 0.55 : 1.0) * sstep(-0.1, wh / 2, y)) * (1 - (full ? 0.65 : 1.0) * sstep(0.25 * w, 0.75 * w, Math.abs(x))) * (full ? 0.88 : 0.75));
      setMesh(ctx, wg, mapMat(wallT, 'wall'), root, 0, top + wh / 2 - 0.45, -d / 2 - 0.25);
      if (o.corner !== false) {
        const cg = new THREE.PlaneGeometry(d * 1.6, wh, 6, 6);
        fadeGeo(ctx, cg, (x, y) => (1 - (full ? 0.55 : 1.0) * sstep(-0.1, wh / 2, y)) * (1 - (full ? 0.65 : 1.0) * sstep(-0.1 * d, 0.7 * d, -x)) * (full ? 0.72 : 0.55));
        setMesh(ctx, cg, mapMat(wallT, 'wall'), root, -w * 0.62, top + wh / 2 - 0.45, -d * 0.25).rotation.y = Math.PI / 2;
      }
    }
    return { root, base: top, frame: { elev: 16 }, table: { w, d, x: root.position.x, z: root.position.z } };
  }
  if (name === 'street') {
    const W = o.w ?? Math.max(4, ext.sx + 3), D = o.d ?? Math.max(2.2, ext.sz + 1.6);
    root.position.set(o.at ? o.at[0] : ext.cx, 0, o.at ? o.at[1] : ext.cz);
    const kx = (x) => 1 - 0.85 * sstep(0.28 * W, 0.5 * W, Math.abs(x));
    const rg = new THREE.PlaneGeometry(W, D, 14, 6); rg.rotateX(-Math.PI / 2);
    fadeGeo(ctx, rg, (x, y, z) => kx(x) * (1 - 0.6 * sstep(0.1 * D, 0.5 * D, z)));
    setMesh(ctx, rg, mapMat(stex(ctx, tx('asphalt', seed, setCol(ctx, o, 'asphalt'), setCol(ctx, o, 'road_line'), px), Math.max(1, Math.round(W / 1.6)), 1), 'asphalt'), root);
    const sw = 1.1, cc = setCol(ctx, o, 'curb'), tt = stex(ctx, tx('tilesFlat', seed + 1, cc, shadeHexP(cc, -30), 64, 4), Math.round(W / 0.6), 2);
    const sg = fadeGeo(ctx, new THREE.BoxGeometry(W, 0.12, sw, 14, 1, 2), (x) => kx(x) * 0.85);
    setMesh(ctx, sg, mapMat(tt, 'curb'), root, 0, 0.06, -D / 2 - sw / 2);
    const nB = Math.round(o.buildings ?? 4);
    let bx = -W / 2 + 0.1;
    for (let i = 0; i < nB && bx < W / 2 - 0.3; i++) {
      const bw = Math.min(W / 2 - bx, 1.2 + 0.9 * hsh(i, seed)), bh = 2.2 + 2.2 * hsh(i, seed + 1), bd = 1.2, cx = bx + bw / 2;
      const ft = stex(ctx, tx('facade', seed + i, setCol(ctx, o, i % 2 ? 'brick' : 'wall'), setCol(ctx, o, 'window'), setCol(ctx, o, 'window_lit'), 64), Math.max(1, Math.round(bw / 0.9)), Math.max(1, Math.round(bh / 1.0)));
      const bg = fadeGeo(ctx, new THREE.BoxGeometry(bw, bh, bd, 4, 6, 1), (x, y) => (1 - sstep(-0.1 * bh, 0.5 * bh, y)) * kx(cx + x) * 0.8);
      setMesh(ctx, bg, mapMat(ft, 'brick'), root, cx, bh / 2 + 0.12, -D / 2 - sw - bd / 2 - 0.02);
      bx += bw + 0.06;
    }
    if (o.lamp !== false) {
      const lx = (o.lamp_x ?? 0.32) * W;
      const pole = fadeGeo(ctx, new THREE.CylinderGeometry(0.03, 0.04, 2.4, 6, 3), (x, y) => 0.5 + 0.35 * sstep(-1.2, 1.2, y));
      setMesh(ctx, pole, ctx.toon('#5A6070', { vertexColors: true }), root, lx, 1.32, -D / 2 - 0.25, true);
      const bulb = ctx.add(new THREE.SphereGeometry(0.09, 8, 6), ctx.flat(setCol(ctx, o, 'lamp')), lx, 2.56, -D / 2 - 0.25, root); bulb.castShadow = false;
      ctx.glow(setCol(ctx, o, 'lamp'), 0.9, root, lx, 2.56, -D / 2 - 0.2, 0.55);
    }
    if (o.trees !== false) tree(ctx, { parent: root, x: -(o.tree_x ?? 0.3) * W, y: 0.12, z: -D / 2 - 0.55, h: 1.6 });
    return { root, base: 0, frame: { elev: 12 } };
  }
  if (name === 'track' || name === 'stadium') {
    const isStad = name === 'stadium';
    const W = o.w ?? Math.max(isStad ? 7.2 : 5.8, ext.sx + 3.4);
    const D = o.d ?? Math.max(isStad ? 2.6 : 2.1, ext.sz + 1.1);
    const inD = isStad ? 3.2 : 2.2;
    const totalD = D + inD + 0.9;
    root.position.set(o.at ? o.at[0] : ext.cx, 0, o.at ? o.at[1] : ext.cz);
    const kx = (x) => 1 - 0.65 * sstep(0.36 * W, 0.52 * W, Math.abs(x));
    // bệ diorama dày (cạnh cắt đá/bê tông tối — đúng chất mô hình thu nhỏ Futurepedia 3D Style Atlas)
    const slabH = 0.28;
    const baseG = fadeGeo(ctx, new THREE.BoxGeometry(W + 0.2, slabH, totalD, 14, 2, 6), (x, y) => kx(x) * (0.45 + 0.55 * sstep(-slabH / 2, slabH / 2, y)));
    setMesh(ctx, baseG, ctx.toon(setCol(ctx, o, 'stadium_base'), { vertexColors: true }), root, 0, -slabH / 2 - 0.002, -inD / 2 + 0.15);
    // mặt đường chạy tartan cao su terracotta (4 làn + vạch trắng)
    const lanes = Math.max(2, Math.round(o.lanes ?? 4));
    const tTex = stex(ctx, tx('tartanTrack', seed, setCol(ctx, o, 'tartan'), setCol(ctx, o, 'track_line'), 256, lanes), Math.max(1, Math.round(W / 2.2)), 1);
    const trackG = new THREE.PlaneGeometry(W, D, 18, 6); trackG.rotateX(-Math.PI / 2);
    fadeGeo(ctx, trackG, (x) => kx(x));
    setMesh(ctx, trackG, mapMat(tTex, 'tartan'), root, 0, 0.003, 0);
    // vạch xuất phát / về đích ô cờ (checkered finish line)
    if (o.finish !== false) {
      const fx = o.finish_x ?? (W * 0.22);
      const cTex = stex(ctx, tx('checkeredStrip', 128, 8), 1, 2);
      const fg = new THREE.PlaneGeometry(0.26, D * 0.98); fg.rotateX(-Math.PI / 2);
      setMesh(ctx, fg, ctx.toon('#ffffff', { map: cTex }), root, fx, 0.007, 0);
    }
    // gờ trắng phân cách sân cỏ (inner raised curb) + mép ngoài
    for (const cz of [-D / 2 - 0.04, D / 2 + 0.04]) {
      const cg = fadeGeo(ctx, new THREE.BoxGeometry(W, 0.075, 0.08, 12, 1, 1), (x) => kx(x) * 0.92);
      setMesh(ctx, cg, ctx.toon(setCol(ctx, o, 'track_line'), { vertexColors: true }), root, 0, 0.037, cz);
    }
    // sân cỏ infield cắt sọc xanh đậm phía sau đường chạy
    const infTex = stex(ctx, tx('stadiumGrass', seed + 1, setCol(ctx, o, 'infield'), 256, 6), Math.max(2, Math.round(W / 2.0)), 1);
    const infG = new THREE.PlaneGeometry(W, inD, 14, 6); infG.rotateX(-Math.PI / 2);
    fadeGeo(ctx, infG, (x, y, z) => kx(x) * (1 - 0.55 * sstep(0.1 * inD, 0.5 * inD, -z)));
    setMesh(ctx, infG, mapMat(infTex, 'infield'), root, 0, 0.002, -D / 2 - 0.08 - inD / 2);
    // cọc tiêu / cột mốc khoảng cách (marker cones) dọc mép đường chạy
    if (o.cones !== false) {
      const cc = setCol(ctx, o, 'cone');
      for (const cx of [-W * 0.3, 0, W * 0.3]) {
        const cone = ctx.add(new THREE.ConeGeometry(0.055, 0.16, 8), cc, cx, 0.08, -D / 2 - 0.18, root);
        cone.castShadow = true;
        ctx.add(new THREE.BoxGeometry(0.13, 0.02, 0.13), '#222630', cx, 0.01, -D / 2 - 0.18, root);
      }
    }
    // khán đài bậc thang tối giản (stadium bleachers) phía xa mờ dần vào tối
    if (o.stands !== false) {
      const sc = setCol(ctx, o, 'stand'), z0 = -D / 2 - inD + 0.15;
      for (let t = 0; t < 4; t++) {
        const tw = W * (0.94 - t * 0.03), th = 0.22 + t * 0.2, tz = z0 - t * 0.36;
        const sg = fadeGeo(ctx, new THREE.BoxGeometry(tw, th, 0.34, 10, 1, 1), (x) => kx(x) * (0.78 - t * 0.14));
        setMesh(ctx, sg, ctx.toon(sc, { vertexColors: true }), root, 0, th / 2, tz);
        // dải ghế mảnh nổi khối
        const rg = fadeGeo(ctx, new THREE.BoxGeometry(tw * 0.96, 0.03, 0.08, 8, 1, 1), (x) => kx(x) * (0.65 - t * 0.1));
        setMesh(ctx, rg, ctx.toon(t === 1 ? 'accent' : '#4E586C', { vertexColors: true }), root, 0, th + 0.015, tz + 0.08);
      }
    }
    // 2 trụ đèn pha sân vận động (floodlight towers) tạo ánh sáng chiều sâu sân khấu đêm
    if (o.lights !== false) {
      const zL = -D / 2 - inD - 0.6;
      for (const sx of [-1, 1]) {
        const lx = sx * W * 0.34;
        const pole = fadeGeo(ctx, new THREE.CylinderGeometry(0.04, 0.06, 3.0, 6, 4), (x, y) => 0.35 + 0.5 * sstep(-1.5, 1.5, y));
        setMesh(ctx, pole, ctx.toon('#4C5566', { vertexColors: true }), root, lx, 1.5, zL);
        const head = ctx.add(new THREE.BoxGeometry(0.56, 0.24, 0.12), '#2C323E', lx, 3.05, zL + 0.05, root);
        head.rotation.x = 0.35; head.castShadow = false;
        const bulb = ctx.add(new THREE.PlaneGeometry(0.48, 0.18), ctx.flat(setCol(ctx, o, 'lamp')), lx, 3.03, zL + 0.12, root);
        bulb.rotation.x = 0.35; bulb.castShadow = false;
        ctx.glow(setCol(ctx, o, 'lamp'), 1.35, root, lx, 3.0, zL + 0.16, 0.42);
      }
    }
    return { root, base: 0, frame: { elev: 17, azim: 26, margin: 1.14, push: 0.06, orbit: 5, headroom: 0.2 } };
  }
  if (name === 'diorama') {
    // Futurepedia "Tiny Diorama": đảo đất cắt vát nổi trên sân khấu tối, đường mòn uốn nhẹ, cây kẹo mút, bụi, đá
    const W = o.w ?? Math.max(4.4, ext.sx + 2.4), D = o.d ?? Math.max(3.2, ext.sz + 1.8), H = 0.48;
    root.position.set(o.at ? o.at[0] : ext.cx, 0, o.at ? o.at[1] : ext.cz);
    // khối đất cắt vát (cut soil-and-rock bevel slab)
    const soilT = stex(ctx, tx('dirt', seed + 1, setCol(ctx, o, 'dirt'), 64), 3, 1);
    const slabG = fadeGeo(ctx, new THREE.BoxGeometry(W, H, D, 8, 3, 6), (x, y) => 0.42 + 0.58 * sstep(-H / 2, H / 2, y));
    setMesh(ctx, slabG, mapMat(soilT, 'dirt'), root, 0, -H / 2 - 0.02, 0, true);
    // lớp cỏ xanh phủ trên mặt (bo dày kiểu mô hình đất nặn/diorama)
    const grT = stex(ctx, tx('grass', seed, setCol(ctx, o, 'grass'), px), Math.max(2, Math.round(W / 1.5)), Math.max(2, Math.round(D / 1.5)));
    const topG = new THREE.BoxGeometry(W + 0.06, 0.09, D + 0.06, 10, 1, 8);
    fadeGeo(ctx, topG, () => 0.96);
    setMesh(ctx, topG, mapMat(grT, 'grass'), root, 0, -0.02, 0, true);
    // lối chạy đất nén băng ngang qua giữa đảo (trail)
    if (o.trail !== false) {
      const trG = new THREE.PlaneGeometry(W * 0.98, Math.min(1.1, D * 0.36), 12, 2); trG.rotateX(-Math.PI / 2);
      const trT = stex(ctx, tx('dirt', seed + 3, setCol(ctx, o, 'trail'), 64), 4, 1);
      fadeGeo(ctx, trG, () => 0.94);
      setMesh(ctx, trG, mapMat(trT, 'trail'), root, 0, 0.028, 0.15);
    }
    // rải cây + bụi + đá xung quanh mép đảo (tránh vùng chạy giữa)
    const nTr = Math.round(o.trees ?? 4);
    for (let i = 0; i < nTr; i++) {
      const tx0 = (-0.4 + 0.8 * (i / Math.max(1, nTr - 1))) * W + (hsh(i, seed) - 0.5) * 0.35;
      const tz0 = -D * 0.34 - hsh(i, seed + 2) * 0.12 * D;
      tree(ctx, { parent: root, x: tx0, y: 0.02, z: tz0, h: 0.95 + 0.45 * hsh(i, seed + 4) });
    }
    for (let i = 0; i < 6; i++) {
      const bx = (hsh(i, seed + 10) - 0.5) * W * 0.85, bz = (i % 2 ? -1 : 1) * (D * 0.35 + hsh(i, seed + 11) * 0.08 * D);
      bush(ctx, { parent: root, x: bx, y: 0.02, z: bz, r: 0.16 + 0.08 * hsh(i, seed + 12) });
    }
    for (let i = 0; i < 5; i++) {
      const rx = (hsh(i, seed + 20) - 0.5) * W * 0.8, rz = (i % 2 ? 0.36 : -0.3) * D;
      rock(ctx, { parent: root, x: rx, y: 0.02, z: rz, r: 0.09 + 0.06 * hsh(i, seed + 21), seed: i + 1 });
    }
    return { root, base: 0.025, frame: { elev: 24, azim: 32, margin: 1.15, push: 0.07, orbit: 7, headroom: 0.2 } };
  }
  return { root, base: 0 };
}

