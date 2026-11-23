// Outro (mode code): nhà khoa học vẫy tay cạnh bảng "NEXT:" ghi teaser của video sau (chữ trong cảnh, đúng chính tả),
// biển CTA nhỏ bên dưới. Camera lướt nhẹ + creep; chữ bảng bật vào bằng back. Cảnh nối loop về frame đầu do hậu kỳ lo.
// params: teaser, next_prefix, follow, expr
export function build(ctx, params) {
  const { MO, PROPS, CAST } = ctx;
  const N = ctx.N;
  const P = { teaser: 'MORE EXPERIMENTS', next_prefix: 'NEXT:', follow: 'Follow for the next experiment', expr: 'excited', ...params };
  const board = PROPS.sign(ctx, { text: `${P.next_prefix}\n${P.teaser}`.toUpperCase(), x: 0, y: 1.92, w: 1.18, h: 0.74, px: 170, color: 'chalk' });
  const cta = PROPS.sign(ctx, { text: P.follow, x: 0, y: 1.4, w: 1.18, h: 0.17, px: 120, color: 'label' });
  const pal = ctx.job.cast_palette || {};
  const keys = [
    { f: 0, pos: [0.2, 1.3, 3.75], look: [0, 1.18, 0], fov: 38 },
    { f: N - 1, pos: [-0.1, 1.25, 3.45], look: [0, 1.16, 0], fov: 37, ease: 'smooth' },
  ];
  return {
    cues: [{ f: 2, name: 'pop' }],
    texts: [P.next_prefix, P.teaser.toUpperCase(), P.follow],
    frame(f) {
      const pop = MO.M.back(MO.clamp(f / 8));
      board.g.scale.setScalar(Math.max(0.01, pop));
      const cp = MO.M.back(MO.clamp((f - 6) / 8)); cta.g.scale.setScalar(Math.max(0.01, cp));
      const id = MO.idle(f, 2);
      const o = { expr: P.expr, armL: 'hip', armR: 'wave', wave: (f % 20) / 20, blink: MO.blinkAt(f, 4), bob: id.bob, tilt: id.tilt,
        headTilt: id.headTilt, look: [0.6, -0.2], pal, ol: CAST.olFor(3.4 / 0.62, 37, 9), rimW: CAST.olFor(3.4 / 0.62, 37, 4.5) };
      const actors = [{ key: CAST.keyOf(o), draw: (g) => CAST.scientist(g, o), x: -0.12, y: -0.05, z: 0.3, s: 0.62, ground: -0.05 }];
      PROPS.faceCamera(ctx);
      const cam = MO.camFromKeys(keys, f, { creep: 0.0015, kicks: [{ f: 8, a: 0.05 }] });
      return { cam, actors, dof: { focus: 3.4, cinf: 0 } };
    },
  };
}
