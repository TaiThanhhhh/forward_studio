// Cảnh cân đĩa: bi thép (khối lượng ball_g) ở đĩa trái, viên đá rơi từng viên vào đĩa phải; đòn cân nghiêng theo
// chênh lệch khối lượng (spring), qua mức cân bằng rồi lệch hẳn sang phía đá. Chữ trong cảnh (đúng chính tả 100%):
// tấm biển dưới mỗi đĩa — "100 g STEEL" và bộ đếm "0 g → 175 g ICE" khắc trên biển (texture phẳng, không lật gương).
// params: ball_g, cube_g, cubes, unit, ball_label, ice_label, hot (0..1 độ đỏ của bi), start_f, every
export function build(ctx, params) {
  const { THREE, MO, PROPS } = ctx;
  const N = ctx.N;
  const P = { ball_g: 100, cube_g: 25, cubes: 7, unit: 'g', ball_word: 'STEEL', ice_word: 'ICE', hot: 0.25,
    start_f: 8, every: 0, tilt_per_g: 0.16, max_tilt: 15, ...params };
  const every = P.every || Math.max(8, Math.floor((N - P.start_f - 30) / P.cubes));
  const S = PROPS.scale(ctx, { y: 0 });
  S.g.rotation.y = P.yaw ?? -1.1;   // đòn cân chạy vào chiều sâu → vừa khung dọc, đĩa gần to hơn
  const ball = PROPS.ball(ctx, { r: 0.065, parent: S.g }); ball.setHot(P.hot);
  const cubes = Array.from({ length: P.cubes }, (_, k) => PROPS.iceCube(ctx, { s: 0.075, parent: S.g }));
  const slot = (k) => { const row = k < 4 ? 0 : 1, i = row ? k - 4 : k; return [(i - (row ? 1 : 1.5)) * 0.068, row * 0.07, ((k * 37) % 5 - 2) * 0.01]; };
  const tag = (txt) => ctx.textPlane({ text: txt, px: 190, color: 'ink_text', bg: 'white', w: 1024, h: 300 }, 0.36, 0.105, S.g, 0, 0, 0);
  const tagL = tag(`${P.ball_g} ${P.unit} ${P.ball_word}`), tagR = tag(`0 ${P.unit} ${P.ice_word}`);
  const landF = (k) => P.start_f + k * every + 9;                    // frame viên k chạm đĩa
  const cues = [];
  for (let k = 0; k < P.cubes; k++) cues.push({ f: landF(k), name: k % 2 ? 'thunk' : 'tick' });
  const levelK = Math.ceil(P.ball_g / P.cube_g) - 1;                 // viên làm cân thăng bằng
  cues.push({ f: landF(levelK) + 2, name: 'ting' });
  const kicks = Array.from({ length: P.cubes }, (_, k) => ({ f: landF(k), a: k === levelK ? 0.11 : 0.06 }));
  const massAt = (f) => { let m = 0; for (let k = 0; k < P.cubes; k++) if (f >= landF(k)) m += P.cube_g; return m; };
  // góc đòn cân: lò xo tắt dần về mục tiêu mỗi khi khối lượng đổi
  const tiltAt = (f) => {
    const target = (m) => Math.max(-P.max_tilt, Math.min(P.max_tilt, (P.ball_g - m) * P.tilt_per_g));
    let ang = target(0);
    for (let k = 0; k < P.cubes; k++) {
      const f0 = landF(k); if (f < f0) break;
      const a0 = target(k * P.cube_g), a1 = target((k + 1) * P.cube_g);
      ang = a0 + (a1 - a0) * MO.M.spring((f - f0) / 30, 2.2, 4.5);
    }
    return ang;
  };
  const keys = [
    { f: 0, pos: [0.25, 0.95, 2.55], look: [0.04, 0.5, 0], fov: 38 },
    { f: Math.round(N * 0.55), pos: [0.2, 0.88, 2.46], look: [0.04, 0.48, 0], fov: 37, ease: 'smooth' },
    { f: N - 1, pos: [0.14, 0.84, 2.4], look: [0.02, 0.46, 0], fov: 36, roll: -1.0, ease: 'smooth' },
  ];
  return {
    cues, texts: [`${P.ball_g} ${P.unit} ${P.ball_word}`, `${P.cubes * P.cube_g} ${P.unit} ${P.ice_word}`],
    frame(f) {
      const cam = MO.camFromKeys(keys, f, { creep: 0.0012, kicks });
      ctx.camera.position.set(...cam.pos);
      S.setTilt(tiltAt(f));
      const L = S.panTop(0), R = S.panTop(1);
      ball.g.position.set(L[0], L[1] + 0.06, L[2]);
      cubes.forEach((c, k) => {
        const lf = landF(k), sl = slot(k);
        if (f < lf - 9) { c.g.visible = false; return; }
        c.g.visible = true;
        const fall = MO.M.easeIn(MO.clamp((f - (lf - 9)) / 9));
        const y = R[1] + 0.036 + sl[1] + (1 - fall) * 0.7;
        c.g.position.set(R[0] + sl[0], y, R[2] + sl[2]);
        const d = f - lf; const sq = d >= 0 && d < 2 ? 0.72 : d >= 2 ? 1 - 0.28 * (1 - MO.M.spring((d - 2) / 30, 3, 6)) : 1.08;
        c.g.scale.set(1 / Math.sqrt(sq), sq, 1 / Math.sqrt(sq)); c.g.rotation.y = 0.4 + k * 0.7;
      });
      // dịch biển theo trục THẾ GIỚI (dx sang ngang, dz về phía người xem) → đổi sang toạ độ cục bộ của cây cân đã xoay;
      // biển trái lệch ra ngoài để trụ cân không che chữ
      const th = S.g.rotation.y, w2l = (dx, dz) => [dx * Math.cos(th) - dz * Math.sin(th), dx * Math.sin(th) + dz * Math.cos(th)];
      const oL = w2l(-0.1, 0.17), oR = w2l(0.03, 0.17);
      tagL.position.set(L[0] + oL[0], L[1] - 0.1, L[2] + oL[1]);
      tagR.position.set(R[0] + oR[0], R[1] - 0.1, R[2] + oR[1]);
      const cp = ctx.camera.position, wp = new THREE.Vector3();  // biển quay mặt về camera (đọc đúng chiều, không lật gương)
      S.g.updateMatrixWorld(true);
      for (const tg of [tagL, tagR]) { tg.getWorldPosition(wp); tg.rotation.y = Math.atan2(cp.x - wp.x, cp.z - wp.z) - S.g.rotation.y; }
      tagR.userData.setText(`${massAt(f)} ${P.unit} ${P.ice_word}`);
      PROPS.faceCamera(ctx);
      return { cam, dof: { focus: 2.3, cinf: 0 }, shadowAt: [0, 0.4, 0] };
    },
  };
}
