// Character test sheet: nhà khoa học ở nhiều biểu cảm/dáng tay, đứng trên sân khấu đen — xem trước khi dùng nhân vật.
export function build(ctx, params) {
  const { CAST, MO } = ctx;
  const looks = params.looks || [
    { expr: 'neutral', armL: 'hang', armR: 'hold', prop: 'tongs' }, { expr: 'shock', armL: 'up', armR: 'up' },
    { expr: 'grin', armL: 'hip', armR: 'wave' }, { expr: 'worried', armL: 'think', armR: 'hang' },
    { expr: 'excited', armL: 'cheer', armR: 'point' }, { expr: 'stern', armL: 'hip', armR: 'present', prop: 'clipboard' },
  ];
  const pal = ctx.job.cast_palette || {};
  const cols = 2, gapX = 1.55, gapY = 2.6;
  const pos = looks.map((_, i) => [(i % cols - (cols - 1) / 2) * gapX, -Math.floor(i / cols) * gapY]);
  const labels = looks.map((l, i) => ctx.textPlane({ text: l.expr.toUpperCase(), px: 120, color: 'label', w: 1024, h: 200 }, 1.0, 0.2, ctx.world, pos[i][0], pos[i][1] - 0.18, 0.2));
  return {
    texts: labels.map((l) => l.userData.text),
    frame(f) {
      const actors = looks.map((l, i) => {
        const id = MO.idle(f, i + 1), o = { ...l, pal, ol: CAST.olFor(12.8, 36, 6), rimW: CAST.olFor(12.8, 36, 3), blink: MO.blinkAt(f, i + 3), wave: (f % 24) / 24, bob: id.bob, tilt: id.tilt, headTilt: id.headTilt };
        return { key: CAST.keyOf(o), draw: (g) => CAST.scientist(g, o), x: pos[i][0], y: pos[i][1], z: 0, s: 1, ground: pos[i][1] };
      });
      const cam = MO.camFromKeys([{ f: 0, pos: [0, -1.45, 12.8], look: [0, -1.45, 0], fov: 36 }], f, { creep: 0.0004 });
      return { cam, actors, dof: { focus: 9, cinf: 0 } };
    },
  };
}
