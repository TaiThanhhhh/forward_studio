// Vật lý vật rắn cho cảnh `stage` (engine three.js) — Rapier 3D bản TẤT ĐỊNH đa nền tảng
// (@dimforge/rapier3d-deterministic-compat, vendor/rapier/, Apache-2.0).
// Mô phỏng MỘT LẦN lúc dựng cảnh (build) và ghi quỹ đạo từng frame; frame(f) chỉ đọc lại → cảnh vẫn là hàm thuần theo
// frame: mọi worker song song mô phỏng ra cùng một kết quả, RESUME an toàn. Va chạm tự sinh cue SFX + kick camera +
// hạt (bụi/tia) đúng frame chạm. Schema dữ liệu (storyboard): đầu engines/three/scenes/stage.js (dòng physics/body).

// vật liệu: khối lượng riêng (kg/m³), độ nảy, ma sát, cản không khí (drag = linear damping, vận tốc rơi tối đa ≈ 9.81/drag)
export const MATERIALS = {
  plastic: { density: 1000, bounce: 0.45, friction: 0.45 },
  rubber: { density: 1100, bounce: 0.8, friction: 0.9 },
  wood: { density: 600, bounce: 0.35, friction: 0.6 },
  metal: { density: 7800, bounce: 0.15, friction: 0.35 },
  stone: { density: 2500, bounce: 0.1, friction: 0.7 },
  glass: { density: 2500, bounce: 0.25, friction: 0.25 },
  ice: { density: 917, bounce: 0.1, friction: 0.02 },
  foam: { density: 60, bounce: 0.25, friction: 0.8, drag: 1.5, angular_drag: 1 },
  paper: { density: 300, bounce: 0.05, friction: 0.6, drag: 8, angular_drag: 3, flutter: 0.15 },
  feather: { density: 30, bounce: 0.05, friction: 0.6, drag: 18, angular_drag: 5, flutter: 0.3 },
};
export const KINDS = ['dynamic', 'fixed', 'kinematic'];
export const SHAPES = ['auto', 'ball', 'box', 'cylinder', 'capsule', 'hull', 'mesh'];
const ROUND = new Set(['ball', 'sphere', 'bowling', 'planet', 'earth']);
const SFX_OF = { metal: 'thunk', glass: 'ting', stone: 'impact', wood: 'thud', rubber: 'thud', plastic: 'thud', ice: 'tick' };

/** Cảnh có dùng vật lý không (main.js chỉ nạp Rapier ~4 MB khi cần). */
export const needsPhysics = (params) => Boolean(params && (params.physics || (params.props || []).some((p) => p && p.body)));

let RAPIER = null;
export async function loadRapier() {
  if (!RAPIER) {
    const m = await import('../../vendor/rapier/rapier.mjs');
    RAPIER = m.default || m;
    await RAPIER.init();
  }
  return RAPIER;
}

const deg = (v) => (v || 0) * Math.PI / 180;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const smooth = (t) => { const x = clamp(t, 0, 1); return x * x * (3 - 2 * x); };
const V = (a) => ({ x: a[0], y: a[1], z: a[2] });
const vec3 = (v, d = [0, 0, 0]) => (Array.isArray(v) && v.length === 3 ? v.map(Number) : typeof v === 'number' ? [0, v, 0] : d);

/** Đỉnh hình học của prop trong hệ toạ độ THÂN (đã nhân scale của prop, chưa xoay/dời). Bỏ chữ, billboard, hạt. */
function geometryOf(THREE, g, scale, wantIdx) {
  const pos0 = g.position.clone(), q0 = g.quaternion.clone(), s0 = g.scale.clone();
  g.position.set(0, 0, 0); g.quaternion.identity(); g.scale.set(scale[0], scale[1], scale[2]);
  if (g.parent) g.parent.updateMatrixWorld(true);
  g.updateMatrixWorld(true);
  const inv = new THREE.Matrix4();
  if (g.parent) inv.copy(g.parent.matrixWorld).invert();
  const pts = [], idx = [], v = new THREE.Vector3(), m = new THREE.Matrix4();
  g.traverse((o) => {
    if (!o.isMesh || !o.geometry || !o.geometry.attributes || !o.geometry.attributes.position) return;
    const ud = o.userData || {};
    if (ud.text !== undefined || ud.billboard || ud.ndSkip) return;
    for (let p = o; p && p !== g; p = p.parent) if (!p.visible) return;
    m.multiplyMatrices(inv, o.matrixWorld);
    const pa = o.geometry.attributes.position, base = pts.length / 3;
    for (let i = 0; i < pa.count; i++) { v.fromBufferAttribute(pa, i).applyMatrix4(m); pts.push(v.x, v.y, v.z); }
    if (wantIdx) {
      const ix = o.geometry.index;
      if (ix) for (let i = 0; i < ix.count; i++) idx.push(base + ix.getX(i));
      else for (let i = 0; i < pa.count; i++) idx.push(base + i);
    }
  });
  g.position.copy(pos0); g.quaternion.copy(q0); g.scale.copy(s0); g.updateMatrixWorld(true);
  return { pts, idx };
}

/** Prop → mô tả collider (độc lập với world, dựng lại mỗi lần chạy mô phỏng) + khối lượng ước tính (kg). */
function shapeSpec(THREE, it, b, scale) {
  const kind = b.shape || 'auto';
  const wantMesh = kind === 'mesh' && b.kind !== 'dynamic';
  const { pts, idx } = geometryOf(THREE, it.g, scale, wantMesh);
  if (!pts.length) throw new Error(`stage physics: prop '${it.id}' không có hình khối để làm collider`);
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < pts.length; i += 3) for (let k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], pts[i + k]); hi[k] = Math.max(hi[k], pts[i + k]); }
  const c = [0, 1, 2].map((k) => (lo[k] + hi[k]) / 2), h = [0, 1, 2].map((k) => Math.max(0.004, (hi[k] - lo[k]) / 2));
  const flat = Math.min(...h) < 0.006;
  let k = kind;
  if (k === 'auto') k = ROUND.has(it.p.type) ? 'ball' : it.p.type === 'box' ? 'box' : it.p.type === 'cylinder' ? 'cylinder' : 'hull';
  if (k === 'mesh' && !wantMesh) k = 'hull';                 // trimesh (lõm) chỉ cho vật đứng yên / kinematic
  if (k === 'hull' && flat) k = 'box';                       // lông vũ, tờ giấy: hình phẳng → hộp mỏng
  const vol = 8 * h[0] * h[1] * h[2];
  let spec, fill;
  if (k === 'ball') { const r = b.r ?? Math.max(...h); spec = { k, r, c }; fill = 0.524 * 8 * r * r * r / Math.max(1e-9, vol); }
  else if (k === 'box') { spec = { k, h, c }; fill = 1; }
  else if (k === 'cylinder') { spec = { k, hh: h[1], r: Math.max(h[0], h[2]), c }; fill = 0.785; }
  else if (k === 'capsule') { const r = Math.max(h[0], h[2]); spec = { k, hh: Math.max(0.001, h[1] - r), r, c }; fill = 0.7; }
  else if (k === 'mesh') { spec = { k, pts: new Float32Array(pts), idx: new Uint32Array(idx), h, c }; fill = 0.5; }
  else {
    let P = pts;
    if (P.length > 3 * 24000) { const s = Math.ceil(P.length / 3 / 24000), q = []; for (let i = 0; i < P.length; i += 3 * s) q.push(P[i], P[i + 1], P[i + 2]); P = q; }
    spec = { k: 'hull', pts: new Float32Array(P), h, c }; fill = 0.6;
  }
  const massEst = b.mass ?? (b.density ?? 1000) * vol * Math.min(1, fill);
  return { spec, massEst };
}

function colliderDesc(R, s) {
  let d = null;
  if (s.k === 'ball') d = R.ColliderDesc.ball(s.r);
  else if (s.k === 'box') d = R.ColliderDesc.cuboid(s.h[0], s.h[1], s.h[2]);
  else if (s.k === 'cylinder') d = R.ColliderDesc.cylinder(s.hh, s.r);
  else if (s.k === 'capsule') d = R.ColliderDesc.capsule(s.hh, s.r);
  else if (s.k === 'mesh') d = R.ColliderDesc.trimesh(s.pts, s.idx);
  else d = R.ColliderDesc.convexHull(s.pts);
  if (!d) d = R.ColliderDesc.cuboid(s.h[0], s.h[1], s.h[2]);  // bao lồi suy biến → hộp bao
  if (s.k !== 'hull' && s.k !== 'mesh') d.setTranslation(s.c[0], s.c[1], s.c[2]);
  return d;
}

/**
 * Mô phỏng cảnh. o = {N, fps, set, base, fOf(k), opts: params.physics, bodies: [{id, p, g, pose(f) → {at, rot, sc}}]}
 * → {tracks: {id: Float64Array(N·7) [x y z qx qy qz qw]}, cues: [{f, name}], kicks: [{f, a}], fx: [{kind, at, f0, f1, r, color}], info}
 */
export function simulate(R, THREE, o) {
  const { N, fps } = o;
  const PH = { gravity: -9.81, floor: true, floor_friction: 0.8, floor_bounce: 0, substeps: 4, iterations: 8, settle: 0,
    slowmo: [], sfx: true, kicks: true, min_hit: 1.2, max_hits: 6, kick_min: 2, fx: null, ...(o.opts || {}) };
  const grav = Array.isArray(PH.gravity) ? vec3(PH.gravity) : [0, Number(PH.gravity), 0];
  const fOf = o.fOf || ((k) => (k.u !== undefined ? k.u * (N - 1) : (k.t ?? 0) * fps));
  const fOfU = (u) => fOf(typeof u === 'object' && u !== null ? u : { u: Number(u) });
  const warn = [];

  // slow motion: [{u:[u0,u1], rate 0..1, ramp (frame)}] — tốc độ thời gian vật lý, vào/ra mượt
  const slow = (PH.slowmo || []).map((w) => {
    const [a, b] = w.u || [(w.t || [0, 0])[0] * fps / Math.max(1, N - 1), (w.t || [0, 0])[1] * fps / Math.max(1, N - 1)];
    return { f0: fOfU(a), f1: fOfU(b), rate: clamp(w.rate ?? 0.3, 0.02, 1), ramp: Math.max(1, w.ramp ?? 5) };
  });
  const rate = (f) => {
    let r = 1;
    for (const w of slow) {
      let k = 0;
      if (f > w.f0 - w.ramp && f < w.f1 + w.ramp) k = f < w.f0 ? smooth((f - (w.f0 - w.ramp)) / w.ramp) : f > w.f1 ? smooth((w.f1 + w.ramp - f) / w.ramp) : 1;
      r = Math.min(r, 1 + (w.rate - 1) * k);
    }
    return r;
  };

  // ---- thân vật lý: vật liệu + collider dựng từ chính hình của prop
  const quatOf = (rot) => new THREE.Quaternion().setFromEuler(new THREE.Euler(deg(rot[0]), deg(rot[1]), deg(rot[2])));
  const B = o.bodies.map((it, i) => {
    const b0 = it.p.body === true ? {} : { ...it.p.body };
    const mat = MATERIALS[b0.material] ? b0.material : 'plastic';
    if (b0.material && !MATERIALS[b0.material]) warn.push(`${it.id}: material '${b0.material}' không có → plastic`);
    const b = { kind: 'dynamic', shape: 'auto', ...MATERIALS[mat], ...b0, material: mat };
    if (!KINDS.includes(b.kind)) { warn.push(`${it.id}: kind '${b.kind}' không có → dynamic`); b.kind = 'dynamic'; }
    const p0 = it.pose(0);
    const { spec, massEst } = shapeSpec(THREE, it, b, p0.sc);
    const dyn = b.kind === 'dynamic';
    return {
      i, id: it.id, it, b, spec, mass: massEst,
      release: dyn ? (b.release !== undefined ? fOfU(b.release) : -Infinity) : Infinity,
      hitF: dyn && b.hit_u !== undefined ? Math.round(fOfU(b.hit_u)) : null,
      pushes: (b.push || []).map((k) => ({ f: Math.round(fOf(k)), v: vec3(k.v), spin: k.spin ? vec3(k.spin).map(deg) : null })),
    };
  });

  const poseW = (bd, f) => { const p = bd.it.pose(f); return { at: p.at, q: quatOf(p.rot) }; };
  const keyVel = (bd, f) => {
    const a = poseW(bd, f - 1), b = poseW(bd, f), k = fps / Math.max(0.02, rate(f - 1));
    const lin = [0, 1, 2].map((j) => (b.at[j] - a.at[j]) * k);
    const dq = b.q.clone().multiply(a.q.clone().invert());
    if (dq.w < 0) { dq.x = -dq.x; dq.y = -dq.y; dq.z = -dq.z; dq.w = -dq.w; }
    const ang = 2 * Math.acos(clamp(dq.w, -1, 1)), s = Math.sqrt(Math.max(1e-12, 1 - dq.w * dq.w));
    const w = ang < 1e-6 ? [0, 0, 0] : [dq.x / s * ang * k, dq.y / s * ang * k, dq.z / s * ang * k];
    return { lin, w };
  };

  const run = (rel) => {
    const preF = Math.round((PH.settle || 0) * fps);
    const fStart = Math.min(0, ...rel.filter(Number.isFinite).map((x) => Math.floor(x))) - preF;
    const world = new R.World(V(grav));
    world.numSolverIterations = PH.iterations;
    const owner = new Map();
    if (PH.floor !== false) {
      const c = world.createCollider(R.ColliderDesc.cuboid(60, 0.5, 60).setTranslation(0, -0.5, 0)
        .setFriction(PH.floor_friction).setRestitution(PH.floor_bounce));
      owner.set(c.handle, -1);
    }
    // mặt bàn: lab (PROPS.bench 3.4 × 1.2 m) hoặc set tabletop (o.table = {w, d, x, z}); mặt trên ở base
    const tb = o.table || (o.set === 'lab' ? { w: 3.4, d: 1.2, x: 0, z: 0 } : null);
    if (tb && PH.bench !== false) {
      const c = world.createCollider(R.ColliderDesc.cuboid(tb.w / 2, 0.04, tb.d / 2).setTranslation(tb.x || 0, o.base - 0.04, tb.z || 0)
        .setFriction(PH.floor_friction).setRestitution(PH.floor_bounce));
      owner.set(c.handle, -1);
    }
    const S = B.map((bd, i) => {
      const startDyn = bd.b.kind === 'dynamic' && !(rel[i] > fStart);
      const p = poseW(bd, fStart);
      const desc = bd.b.kind === 'fixed' ? R.RigidBodyDesc.fixed() : startDyn ? R.RigidBodyDesc.dynamic() : R.RigidBodyDesc.kinematicPositionBased();
      desc.setTranslation(p.at[0], p.at[1], p.at[2]).setRotation({ x: p.q.x, y: p.q.y, z: p.q.z, w: p.q.w });
      if (bd.b.kind === 'dynamic') desc.setCcdEnabled(true).setLinearDamping(bd.b.drag ?? 0).setAngularDamping(bd.b.angular_drag ?? 0.05);
      if (startDyn) {
        const v = vec3(bd.b.v), w = vec3(bd.b.spin).map(deg);
        desc.setLinvel(v[0], v[1], v[2]).setAngvel(V(w));
      }
      const rb = world.createRigidBody(desc);
      const cd = colliderDesc(R, bd.spec).setFriction(bd.b.friction ?? 0.5).setRestitution(bd.b.bounce ?? 0.3)
        .setRestitutionCombineRule(R.CoefficientCombineRule.Max).setActiveEvents(R.ActiveEvents.COLLISION_EVENTS);
      if (bd.b.mass) cd.setMass(bd.b.mass); else cd.setDensity(bd.b.density ?? 1000);
      const col = world.createCollider(cd, rb);
      owner.set(col.handle, i);
      return { rb, dyn: startDyn, relF: startDyn ? fStart : null };
    });
    const eq = new R.EventQueue(true);
    const tracks = B.map(() => new Float64Array(N * 7));
    const vPre = B.map(() => [0, 0, 0]), impacts = [];
    const k = Math.max(1, Math.round(PH.substeps));
    let tau = 0;
    for (let f = fStart; f < N; f++) {
      const r = rate(f), dt = r / fps / k;
      world.timestep = dt;
      S.forEach((s, i) => {                                   // thả (kinematic → dynamic) và cú đẩy ở đầu frame
        const bd = B[i];
        if (bd.b.kind === 'dynamic' && !s.dyn && f >= rel[i]) {
          const kv = keyVel(bd, f);
          const v = bd.b.v ? vec3(bd.b.v) : kv.lin, w = bd.b.spin ? vec3(bd.b.spin).map(deg) : kv.w;
          s.rb.setBodyType(R.RigidBodyType.Dynamic, true);
          s.rb.setLinvel(V(v), true); s.rb.setAngvel(V(w), true);
          s.dyn = true; s.relF = f;
        }
        if (s.dyn) for (const pu of bd.pushes) {
          if (pu.f !== f) continue;
          const lv = s.rb.linvel();
          s.rb.setLinvel({ x: lv.x + pu.v[0], y: lv.y + pu.v[1], z: lv.z + pu.v[2] }, true);
          if (pu.spin) { const av = s.rb.angvel(); s.rb.setAngvel({ x: av.x + pu.spin[0], y: av.y + pu.spin[1], z: av.z + pu.spin[2] }, true); }
        }
      });
      for (let st = 0; st < k; st++) {
        S.forEach((s, i) => {
          const bd = B[i];
          if (bd.b.kind === 'fixed') return;
          if (!s.dyn) {                                         // vật đang theo keyframe: đẩy được vật khác
            const p = poseW(bd, f - 1 + (st + 1) / k);
            s.rb.setNextKinematicTranslation(V(p.at)); s.rb.setNextKinematicRotation({ x: p.q.x, y: p.q.y, z: p.q.z, w: p.q.w });
          } else if (bd.b.flutter) {                            // lông vũ/giấy: lực ngang + mô-men dao động tất định (lả lướt)
            const m = s.rb.mass(), c = (bd.b.drag || 1) * bd.b.flutter * m, t = tau + dt * st;
            s.rb.resetForces(true); s.rb.resetTorques(true);
            s.rb.addForce({ x: c * Math.sin(t * 7.3 + i * 1.7), y: 0, z: 0.6 * c * Math.cos(t * 5.1 + i * 0.9) }, true);
            s.rb.addTorque({ x: 0.02 * c * Math.sin(t * 4.1 + i), y: 0, z: 0.02 * c * Math.cos(t * 3.3 + i * 2.3) }, true);
          }
          const lv = s.rb.linvel(); vPre[i] = [lv.x, lv.y, lv.z];
        });
        world.step(eq);
        eq.drainCollisionEvents((h1, h2, started) => {
          if (!started) return;
          const a = owner.get(h1) ?? -1, b = owner.get(h2) ?? -1;
          let pt = null, n = null;
          world.contactPair(world.getCollider(h1), world.getCollider(h2), (m) => {
            n = m.normal();
            if (m.numSolverContacts() > 0) { const q = m.solverContactPoint(0); if (q) pt = [q.x, q.y, q.z]; }
          });
          const va = a >= 0 ? vPre[a] : [0, 0, 0], vb = b >= 0 ? vPre[b] : [0, 0, 0];
          const d = [va[0] - vb[0], va[1] - vb[1], va[2] - vb[2]];
          const speed = n ? Math.abs(d[0] * n.x + d[1] * n.y + d[2] * n.z) : Math.hypot(...d);
          impacts.push({ f, a, b, speed, sa: Math.hypot(...va), sb: Math.hypot(...vb), pt });
        });
      }
      tau += r / fps;
      if (f >= 0) S.forEach((s, i) => {
        const t = s.rb.translation(), q = s.rb.rotation(), j = f * 7;
        tracks[i].set([t.x, t.y, t.z, q.x, q.y, q.z, q.w], j);
      });
    }
    eq.free(); world.free();
    const first = B.map((bd, i) => {
      const rf = S[i].relF ?? Infinity;
      const e = impacts.find((x) => (x.a === i || x.b === i) && x.f > rf && x.speed > 0.05);
      return e ? e.f : null;
    });
    return { tracks, impacts, first, fStart };
  };

  // ---- canh va chạm theo lời đọc: hit_u → dời thời điểm thả để lần chạm ĐẦU TIÊN rơi đúng frame đó
  //      frame chạm tăng đơn điệu theo frame thả → bước "dời đúng độ lệch" + chặn hai đầu (bisection khi slow-mo làm lệch)
  const rel = B.map((bd) => (bd.hitF !== null ? Math.round(Number.isFinite(bd.release) ? bd.release : bd.hitF - 12) : bd.release));
  let res = run(rel);
  const aligned = [];
  B.forEach((bd, i) => {
    if (bd.hitF === null) return;
    let lo = null, hi = null, best = null;
    for (let n = 0; n < 18; n++) {
      const got = res.first[i];
      let next;
      if (got === null) {                                      // chưa chạm trước hết shot → thả sớm hơn
        hi = rel[i];
        next = lo !== null ? Math.floor((lo + hi) / 2) : rel[i] - 15;
      } else {
        const err = Math.abs(bd.hitF - got);
        if (!best || err < best.err || (err === best.err && got < best.got)) best = { err, r: rel[i], got };   // hoà: chạm sớm (trước từ khoá)
        if (err === 0) break;
        if (got < bd.hitF) lo = rel[i]; else hi = rel[i];
        next = rel[i] + (bd.hitF - got);
        if (lo !== null && hi !== null && ((next <= lo) || (next >= hi))) next = Math.floor((lo + hi) / 2);
      }
      if ((lo !== null && hi !== null && hi - lo <= 1) || next === rel[i] || next < -20 * N) break;
      rel[i] = next;
      res = run(rel);
    }
    if (best) rel[i] = best.r;
    res = run(rel);
    if (res.first[i] === null) warn.push(`${bd.id}: hit_u — vật không chạm gì sau khi thả`);
    aligned.push({ id: bd.id, want: bd.hitF, got: res.first[i], release: rel[i] });
  });

  // ---- va chạm → cue SFX + kick camera + hạt, theo vật nhanh hơn trong cặp
  const last = {};
  let hits = res.impacts.filter((e) => e.f >= 0 && e.f < N && e.speed >= PH.min_hit).map((e) => {
    const who = e.a >= 0 && (e.b < 0 || e.sa >= e.sb) ? e.a : e.b;
    const bd = B[who];
    return { ...e, who, bd, mom: bd.mass * e.speed, at: e.pt || [...res.tracks[who].slice(e.f * 7, e.f * 7 + 3)] };
  }).filter((e) => {
    if (last[e.who] !== undefined && e.f - last[e.who] < 6) return false;
    last[e.who] = e.f; return true;
  });
  // nhiều vật va cùng lúc (tháp đổ) = MỘT cú: gộp các va chạm cách nhau ≤ 2 frame, giữ cú mạnh nhất
  hits = hits.sort((x, y) => y.mom - x.mom).filter((e, i, arr) => !arr.slice(0, i).some((x) => Math.abs(x.f - e.f) <= 2));
  hits = hits.slice(0, Math.max(0, PH.max_hits)).sort((x, y) => x.f - y.f);
  const cues = [], kicks = [], fx = [], fxCount = {};
  const momMax = Math.max(0, ...hits.map((h) => h.mom));
  for (const h of hits) {
    const b = h.bd.b;
    const silent = PH.sfx === false || b.sfx === false || ['paper', 'feather', 'foam'].includes(b.material) && b.sfx === undefined;
    if (!silent) {
      const name = typeof b.sfx === 'string' ? b.sfx : h.bd.mass < 0.25 ? 'tick' : h.speed >= 3 && h.mom > 15 ? 'impact' : SFX_OF[b.material] || 'thud';
      cues.push({ f: h.f, name });
    }
    // physics.fx (chung) chỉ cho cú mạnh (≥ một nửa cú mạnh nhất); body.fx (riêng) cho mọi cú của vật đó
    const kind = b.fx === undefined ? (h.mom >= PH.kick_min && h.mom >= 0.5 * momMax ? PH.fx : null) : b.fx;
    if (kind && (fxCount[h.who] || 0) < (b.fx_max ?? 2)) {
      const spec = typeof kind === 'string' ? { kind } : kind;
      fxCount[h.who] = (fxCount[h.who] || 0) + 1;
      fx.push({ kind: spec.kind || 'burst', at: h.at, f0: h.f, f1: h.f + Math.round((spec.sec ?? 0.6) * fps),
        r: spec.r ?? clamp(0.12 + 0.05 * Math.log1p(h.mom), 0.15, 0.45), color: spec.color });
    }
  }
  if (PH.kicks !== false) {
    hits.filter((h) => h.mom >= PH.kick_min).sort((x, y) => y.mom - x.mom).slice(0, 3)
      .forEach((h) => kicks.push({ f: h.f, a: clamp(0.025 + 0.015 * Math.log1p(h.mom), 0.025, 0.09) }));
  }
  const tracks = {};
  B.forEach((bd, i) => { tracks[bd.id] = res.tracks[i]; });
  return {
    tracks, cues, kicks, fx,
    info: {
      bodies: B.map((bd) => ({ id: bd.id, kind: bd.b.kind, shape: bd.spec.k, material: bd.b.material, mass: +bd.mass.toFixed(3) })),
      impacts: hits.map((h) => ({ f: h.f, id: h.bd.id, speed: +h.speed.toFixed(2) })),
      aligned, start: res.fStart, warn,
    },
  };
}
