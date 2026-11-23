// Chạy cảnh `stage` của engine three.js trong Node (không trình duyệt, không WebGL) cho test:
//   node tests/fixtures/stage_harness.mjs '<json {params, frames, fps}>'
// → JSON {cues, physics, pos: {propId: [[x,y,z] mỗi frame]}, cams: số frame có camera}
import * as THREE from '../../vendor/three/three.module.js';
import * as MO from '../../lib/motion/motion.js';
import * as PROPS from '../../engines/three/props.js';
import * as CAST from '../../engines/three/cast.js';
import { needsPhysics, loadRapier } from '../../engines/three/physics.js';
import { build } from '../../engines/three/scenes/stage.js';

const arg = JSON.parse(process.argv[2] || '{}');
const N = arg.frames || 60, fps = arg.fps || 30, params = arg.params || {};
const world = new THREE.Group();
const ctx = {
  THREE, MO, PROPS, CAST, world, N, fps, job: { font_family: 'sans-serif' },
  C: () => '#ffffff',
  toon: () => new THREE.MeshBasicMaterial(),
  flat: () => new THREE.MeshBasicMaterial(),
  glow: (c, size, p = world) => { const me = new THREE.Mesh(new THREE.PlaneGeometry(size || 1, size || 1), new THREE.MeshBasicMaterial()); me.userData.billboard = true; p.add(me); return me; },
  add: (geo, m, x = 0, y = 0, z = 0, p = world) => {
    const me = new THREE.Mesh(geo, typeof m === 'string' ? new THREE.MeshBasicMaterial() : m);
    me.position.set(x, y, z); p.add(me); return me;
  },
  group: (p = world, x = 0, y = 0, z = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); p.add(g); return g; },
  RAPIER: needsPhysics(params) ? await loadRapier() : null,
};
const s = build(ctx, params);
const ids = (params.props || []).map((p, i) => p.id || `${p.type}${i}`);
// vị trí thế giới của từng prop sau frame(f): lấy từ group của prop (thứ tự tạo = thứ tự trong world.children)
const pos = Object.fromEntries(ids.map((id) => [id, []]));
let cams = 0;
for (let f = 0; f < N; f++) {
  const st = s.frame(f);
  if (st.cam && st.cam.pos.every(Number.isFinite)) cams++;
  for (const id of ids) {
    const it = s.objectOf(id);
    if (it) pos[id].push([it.position.x, it.position.y, it.position.z].map((v) => +v.toFixed(5)));
  }
}
console.log(JSON.stringify({ cues: s.cues, physics: s.physics, pos, cams }));
