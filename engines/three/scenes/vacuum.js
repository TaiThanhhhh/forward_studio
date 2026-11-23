// Phòng thí nghiệm chân không (dùng cho style toon3d-lab, toàn bộ bằng code): bàn lab tối, buồng kính chân không,
// lông vũ + bóng bowling, đồng hồ áp suất, nhà khoa học card 2D; cảnh Mặt Trăng cho twist.
// params: beat = hook | air | pump | gauge | drop | moon ; vacuum (0..1, chỉ cho hook/drop), sign (chữ trên biển), year
export function build(ctx, params) {
  const { THREE, MO, PROPS, CAST } = ctx;
  const N = ctx.N;
  const P = { beat: 'hook', sign: 'VACUUM', year: '1971', ...params };
  const pal = ctx.job.cast_palette || {};
  const cues = [], texts = [];
  const rnd = (k) => { const x = Math.sin(k * 127.1 + 3.3) * 43758.5453; return x - Math.floor(x); };

  // ---- đạo cụ riêng của cảnh
  const feather = (parent) => {
    const s = new THREE.Shape(); s.moveTo(0, -0.17);
    s.bezierCurveTo(0.07, -0.08, 0.06, 0.1, 0, 0.17); s.bezierCurveTo(-0.05, 0.1, -0.07, -0.06, 0, -0.17);
    const g = ctx.group(parent);
    ctx.add(new THREE.ShapeGeometry(s, 16), ctx.toon('feather', { side: THREE.DoubleSide }), 0, 0, 0, g);
    ctx.add(new THREE.CylinderGeometry(0.004, 0.004, 0.36, 6), 'grey', 0, -0.02, 0.002, g);
    return g;
  };
  const bowling = (parent, r = 0.09) => {
    const g = ctx.group(parent);
    ctx.add(new THREE.SphereGeometry(r, 32, 20), 'iron', 0, 0, 0, g);
    for (const [a, b] of [[-0.25, 0.35], [0.05, 0.42], [-0.08, 0.15]]) {
      const h = ctx.add(new THREE.CircleGeometry(r * 0.12, 12), ctx.flat('#05070a'), Math.sin(a) * r * 1.002, Math.sin(b) * r, Math.cos(a) * Math.cos(b) * r * 1.002, g, { cast: false });
      h.lookAt(h.position.clone().multiplyScalar(3)); h.userData.ndSkip = true;
    }
    return g;
  };
  const moon = P.beat === 'moon';
  if (!moon) PROPS.bench(ctx, { w: 3.6, d: 1.2, top: 0.92 });
  const TOP = moon ? 0 : 0.92;

  let keys, frame;
  if (moon) {
    // Mặt Trăng: nền đen (bầu trời đen thật), mặt đất xám có hố, búa + lông rơi cùng lúc
    const ground = ctx.add(new THREE.CylinderGeometry(6, 6, 0.2, 64), 'grey', 0, -0.1, -1, ctx.world);
    for (let k = 0; k < 9; k++) {
      const c = ctx.add(new THREE.TorusGeometry(0.15 + rnd(k) * 0.35, 0.03, 8, 32), 'metal', (rnd(k + 1) - 0.5) * 5, 0.01, -1 - rnd(k + 2) * 4, ctx.world);
      c.rotation.x = Math.PI / 2; c.scale.set(1, 1, 0.4);
    }
    const earth = ctx.add(new THREE.SphereGeometry(0.5, 32, 20), 'water', 2.6, 3.6, -9, ctx.world, { cast: false });
    earth.userData.ndSkip = false;
    const hammer = ctx.group(ctx.world);
    ctx.add(new THREE.BoxGeometry(0.035, 0.32, 0.035), 'bench_leg', 0, 0, 0, hammer);
    ctx.add(new THREE.BoxGeometry(0.16, 0.06, 0.06), 'metal', 0, 0.16, 0, hammer);
    const fe = feather(ctx.world);
    const sg = PROPS.sign(ctx, { text: `APOLLO 15 · ${P.year}`, x: 0.05, y: 1.75, z: -0.6, w: 0.95, h: 0.24, px: 150, color: 'label' });
    texts.push(`APOLLO 15 · ${P.year}`);
    const t0 = Math.round(N * 0.2), t1 = Math.round(N * 0.68);
    cues.push({ f: t0, name: 'whoosh_soft' }, { f: t1, name: 'thunk' });
    keys = [{ f: 0, pos: [0.0, 1.0, 3.3], look: [0, 0.95, 0], fov: 40 },
      { f: N - 1, pos: [-0.1, 0.85, 2.9], look: [0.02, 0.8, 0], fov: 38, roll: 2.5, ease: 'smooth' }];
    frame = (f) => {
      const u = MO.clamp((f - t0) / (t1 - t0)), y = 1.45 - 1.29 * u * u;     // rơi đều gia tốc, cùng lúc
      hammer.position.set(-0.22, Math.max(0.16, y), 0.3); hammer.rotation.z = 0.3;
      fe.position.set(0.18, Math.max(0.17, y + 0.01), 0.3); fe.rotation.z = -0.4;
      return { kicks: [{ f: t1, a: 0.08 }] };
    };
  } else {
    const C = PROPS.chamber(ctx, { x: 0.1, y: TOP, r: 0.34, h: 1.2 });
    const g = PROPS.gauge(ctx, { x: 0.62, y: TOP + 1.05, z: 0.15, r: 0.17, labels: ['0', '50', '100'], unit: 'kPa' });
    texts.push('kPa');
    const sg = PROPS.sign(ctx, { text: P.sign, x: 0.1, y: TOP + 1.52, z: 0.05, w: 0.8, h: 0.2, px: 170, color: 'label' });
    texts.push(P.sign);
    const pump = ctx.group(ctx.world, 0.62, TOP, -0.15);
    ctx.add(ctx.tbox(0.34, 0.3, 0.3, 1), 'grey', 0, 0.15, 0, pump);
    ctx.add(new THREE.CylinderGeometry(0.05, 0.05, 0.12, 16), 'metal', 0, 0.36, 0, pump);
    const fe = feather(C.g), ba = bowling(C.g);
    const air = Array.from({ length: 40 }, (_, k) => {
      const me = ctx.add(new THREE.SphereGeometry(0.011, 8, 6), 'accent_hi', 0, 0, 0, C.g, { cast: false });
      return { me, x: (rnd(k) - 0.5) * 0.55, y: 0.15 + rnd(k + 9) * 1.05, z: (rnd(k + 4) - 0.5) * 0.4, ph: rnd(k + 2) };
    });
    const vacOf = (f) => ({ hook: 1, air: 0, pump: MO.M.smooth(f / N), gauge: MO.M.smooth(MO.clamp(f / (N * 0.8))), drop: 1 })[P.beat] ?? (P.vacuum ?? 0);
    const dropping = ['hook', 'air', 'drop'].includes(P.beat);
    const t0 = Math.round(N * (P.beat === 'hook' ? 0.12 : 0.18));
    const fall = Math.round(N * 0.42);                                     // số frame rơi tới đáy trong chân không
    const yTop = C.inner.top - 0.22, yBot = C.inner.bottom + 0.09;
    if (dropping) cues.push({ f: t0, name: 'click' }, { f: t0 + fall, name: 'thunk' });
    if (P.beat === 'pump') cues.push({ f: 2, name: 'riser' });
    if (P.beat === 'gauge') cues.push({ f: Math.round(N * 0.8), name: 'ting' });
    const sci = !['gauge'].includes(P.beat);
    keys = {
      hook: [{ f: 0, pos: [0.1, TOP + 0.95, 3.1], look: [0.1, TOP + 1.02, 0], fov: 38 },
        { f: N - 1, pos: [0.15, TOP + 0.88, 2.95], look: [0.1, TOP + 1.0, 0], fov: 37, ease: 'smooth' }],
      air: [{ f: 0, pos: [-0.2, TOP + 0.95, 3.9], look: [0.0, TOP + 0.92, 0], fov: 40 },
        { f: N - 1, pos: [-0.1, TOP + 0.9, 3.6], look: [0.02, TOP + 0.90, 0], fov: 39, ease: 'smooth' }],
      pump: [{ f: 0, pos: [0.45, TOP + 0.95, 3.9], look: [0.12, TOP + 0.92, 0], fov: 40 },
        { f: N - 1, pos: [0.35, TOP + 0.9, 3.5], look: [0.12, TOP + 0.92, 0], fov: 39, ease: 'smooth' }],
      gauge: [{ f: 0, pos: [0.7, TOP + 1.1, 1.45], look: [0.62, TOP + 1.05, 0.15], fov: 34 },
        { f: N - 1, pos: [0.66, TOP + 1.07, 1.0], look: [0.62, TOP + 1.05, 0.15], fov: 32, roll: -2, ease: 'smooth' }],
      drop: [{ f: 0, pos: [0.1, TOP + 0.85, 3.3], look: [0.1, TOP + 0.96, 0], fov: 37 },
        { f: N - 1, pos: [0.1, TOP + 0.6, 2.9], look: [0.1, TOP + 0.42, 0], fov: 35, roll: -2, ease: 'easeOut' }],
    }[P.beat];
    frame = (f) => {
      const vac = vacOf(f);
      g.setValue(1 - vac);
      air.forEach((a, k) => {
        const on = rnd(k + 20) > vac; a.me.visible = on;
        a.me.position.set(a.x + 0.02 * Math.sin(f * 0.2 + k), a.y + 0.03 * Math.sin(f * 0.13 + k * 2), a.z);
        if (P.beat === 'pump') { const pull = MO.clamp(vac * 1.4 - rnd(k + 20)); a.me.position.x += pull * (0.5 - a.x); }
      });
      // rơi: chân không → cả hai rơi cùng gia tốc; có khí → bóng rơi nhanh, lông bay lượn chậm
      const u = MO.clamp((f - t0) / fall);
      const yFall = (k) => Math.max(yBot, yTop - (yTop - yBot) * k * k);
      if (dropping && vac > 0.5) {
        ba.position.set(-0.11, yFall(u), 0.05); fe.position.set(0.12, Math.max(yBot + 0.08, yFall(u) + 0.08), 0.05);
        fe.rotation.set(0, 0, 0.2);
      } else if (dropping) {
        ba.position.set(-0.13, yFall(MO.clamp((f - t0) / (fall * 0.8))), 0.05);
        const ff = Math.max(0, f - t0) / 30;
        fe.position.set(0.15 + 0.12 * Math.sin(ff * 3.2), Math.max(yBot + 0.08, yTop + 0.08 - ff * 0.12), 0.05);
        fe.rotation.set(0, 0, 0.6 * Math.sin(ff * 3.2 + 0.5));
      } else {
        ba.position.set(-0.13, yTop, 0.05); fe.position.set(0.15, yTop + 0.08, 0.05); fe.rotation.set(0, 0, 0.2);
      }
      const id = MO.idle(f, 3);
      const expr = { hook: 'excited', air: 'neutral', pump: 'stern', drop: 'shock' }[P.beat] || 'neutral';
      const o = { expr, armL: P.beat === 'pump' ? 'point' : 'hip', armR: P.beat === 'drop' ? 'up' : P.beat === 'air' ? 'think' : 'present',
        wave: (f % 24) / 24, blink: MO.blinkAt(f, 5), bob: id.bob, tilt: id.tilt, headTilt: id.headTilt, look: [-0.7, 0.1], pal,
        ol: CAST.olFor(3.2 / 0.82, 39, 8), rimW: CAST.olFor(3.2 / 0.82, 39, 3) };
      const actors = sci ? [{ key: CAST.keyOf(o), draw: (gg) => CAST.scientist(gg, o), x: -0.52, y: 0, z: 0.6, s: 0.82, ground: 0 }] : [];
      return { actors, kicks: dropping ? [{ f: t0 + Math.round(fall * (vac > 0.5 ? 1 : 0.8)), a: 0.07 }] : [] };
    };
  }
  return {
    cues, texts,
    frame(f) {
      const st = frame(f) || {};
      PROPS.faceCamera(ctx);
      const cam = MO.camFromKeys(keys, f, { creep: 0.0015, kicks: st.kicks || [] });
      const dofF = { gauge: 1.1, moon: 2.7 }[P.beat] || 2.6;
      return { cam, actors: st.actors || [], dof: { focus: dofF, cinf: 7 }, shadowAt: [0, TOP + 0.4, 0], shadowExt: 3 };
    },
  };
}
