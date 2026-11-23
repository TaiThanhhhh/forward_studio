// Cảnh nhiệt kế trong cốc nước đá: nước sủi quanh viên bi dưới đáy, đá nổi, nhiệt kế đứng trong cốc — cột đỏ
// dao động nhẹ nhưng vẫn ở 0. Vạch chia + số là texture trên thân nhiệt kế (đúng chính tả, không lật gương),
// "0°C" tô accent. Camera đẩy vào vạch 0 rồi rack focus.
// params: value (°C, mặc định 0), lo, hi, step, bubbles (0..1), hot (0..1 bi đáy cốc), push (0..1 mức đẩy vào)
export function build(ctx, params) {
  const { THREE, MO, PROPS } = ctx;
  const N = ctx.N;
  const P = { value: 0, lo: -10, hi: 30, step: 10, bubbles: 1, hot: 0.55, push: 1, ...params };
  const G = PROPS.glass(ctx, { r: 0.3, h: 0.86, water: 0.7 });
  const TY = 0.26; const T = PROPS.thermometer(ctx, { x: 0.07, y: TY, z: 0.02, lo: P.lo, hi: P.hi, step: P.step, highlight: P.value, h: 1.25, w: 0.24 });
  T.g.rotation.z = -0.08;
  const ball = PROPS.ball(ctx, { r: 0.07, x: -0.12, y: 0.1, z: 0.05 }); ball.setHot(P.hot);
  const ice = [[-0.16, 0.05, 0.4], [0.17, -0.06, 1.1], [-0.02, -0.13, 2.0]].map(([x, z, ry]) => {
    const c = PROPS.iceCube(ctx, { s: 0.12, x, y: G.waterTop, z }); c.g.rotation.y = ry; return c;
  });
  const rnd = (k) => { const x = Math.sin(k * 127.1) * 43758.5453; return x - Math.floor(x); };
  const NB = 26, bub = Array.from({ length: NB }, (_, k) => {
    const me = ctx.add(new THREE.SphereGeometry(0.012 + rnd(k) * 0.016, 10, 8), 'white', 0, 0, 0, ctx.world, { cast: false });
    return { me, ph: rnd(k + 9), x: (rnd(k + 3) - 0.5) * 0.3, z: (rnd(k + 5) - 0.5) * 0.3, sp: 0.55 + rnd(k + 7) * 0.6 };
  });
  const y0 = T.yOf(P.value) + TY;   // toạ độ thế giới của vạch giá trị
  const keys = [
    { f: 0, pos: [0.25, 0.85, 2.7], look: [0.03, 0.62, 0], fov: 38 },
    { f: N - 1, pos: [0.14, y0 + 0.06, 1.25 + 1.0 * (1 - P.push)], look: [0.09, y0 + 0.02, 0], fov: 32, roll: 2, ease: 'smooth' },
  ];
  return {
    cues: [{ f: 0, name: 'bubbles' }, { f: Math.round(N * 0.6), name: 'tick' }],
    texts: [`${P.value}°C`],
    frame(f) {
      const t = f / 30;
      T.setValue(P.value + 0.6 * Math.sin(t * 9) * Math.exp(-t * 0.6));     // run nhẹ quanh 0, không lên
      bub.forEach((b) => {
        const u = ((t * b.sp + b.ph) % 1);
        b.me.visible = P.bubbles > 0;
        b.me.position.set(-0.12 + b.x * (0.4 + u), 0.12 + u * (G.waterTop - 0.14), 0.05 + b.z * (0.4 + u));
        b.me.scale.setScalar(0.5 + u);
      });
      ice.forEach((c, k) => { c.g.position.y = G.waterTop - 0.02 + 0.012 * Math.sin(t * 6 + k * 2); c.g.rotation.z = 0.06 * Math.sin(t * 4 + k); });
      PROPS.faceCamera(ctx);
      const cam = MO.camFromKeys(keys, f, { creep: 0.0015, kicks: [{ f: Math.round(N * 0.6), a: 0.05 }] });
      const k = MO.M.smooth(f / Math.max(1, N - 1));
      return { cam, dof: { focus: MO.lerp(2.6, 1.22 + 1.0 * (1 - P.push), k), cinf: 6 * k }, shadowAt: [0, 0.5, 0] };
    },
  };
}
