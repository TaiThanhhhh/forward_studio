// GENERAL data-driven code scene — works for ANY new idea, no JavaScript needed.
// Storyboard: "code": {"scene": "stage", "params": {set, props[], fx[], camera[]?, kicks[], cues[], flash[], dof, frame}}
// Units: metres, y up, +z toward the camera. A character card is 2.25 m × s tall; a 3D mannequin is ~1.7 m × s tall.
// set:     "black" (empty black stage, default) | "lab" (dark lab bench, top at 0.92 m; prop y is measured from the top)
//          | "track" (miniature Atlas stadium running track diorama: tartan lanes, checkered finish, grass infield, stands, floodlights)
//          | "stadium" (wider stadium track diorama) | "diorama" (Futurepedia Tiny Diorama floating soil/grass slab + trail + trees)
//          | "meadow" (floating grass island: tufts, flowers, rocks, far hills — every edge fades into black)
//          | "tabletop" (wooden table + room corner, top at 0.76 m; prop y from the top)
//          | "street" (a low-poly street: road at y=0, sidewalk, buildings, lamp). Sets auto-size to the props.
//          set_opts: {r (meadow radius m), w, d, top, seed, grass, flowers, rocks, hills, buildings, wall, corner, lamp,
//          trees, colors: {grass, flower, dirt, hill, wood, wall, asphalt, brick…}} · blob: 0.5 = round contact shadow
//          under every prop (default on in the 90s looks retro90/psx, which have no shadow maps; false = off)
// props[]: {id, type, at:[x,y,z], rot:[x,y,z deg], scale (number|[x,y,z]), color, ...type params, keys:[...]}
//   3D actors: mannequin{pose: idle|run|sprint|walk|squat|lift|curl|press|point|cheer|fall, armL, armR, color, accent, hot, heat}
//              (aliases: human3d, runner3d, lifter3d, scientist3d) · character{s,expr,armL,armR,prop: tongs|clipboard,look:[x,y]} (2D card)
//   3D animals & people (procedural, face painted on texture, run in every 3D look):
//     creature{species: dog|dachshund|cat|fox|wolf|bear|rabbit|mouse|pig|cow|horse|sheep|chicken|bird|duck|penguin|fish|frog
//              |turtle|dino|kid|adult, gait: auto|idle|walk|trot|run|sniff|sit|jump|hop|wag|eat|sleep|fall|swim,
//              expr: neutral|happy|shock|sad|angry|sleepy|sniff|love|wink, look:[x,y,z] world point | "camera", heat: 0..1,
//              color: token/hex (body) or {body, belly, snout, ear, paw, shirt, pants, hair, skin…}, hair (kid/adult):
//              short|bob|pony|spiky|curly|bald, face: path|fixed}  — aliases: type = dog, puppy, dachshund, cat, kitten,
//              fox, wolf, bear, rabbit, bunny, rat, pig, cow, horse, sheep, chicken, hen, duck, penguin, fish, frog, turtle,
//              dino, dinosaur, kid, child, adult. Moving it with `at` keys = it walks there (gait auto picks walk/trot/run by
//              speed, legs match the distance, it turns to face the path); keys may switch gait/expr/look at any u
//              (gaits blend). jump/fall play once from their key; hop repeats. 1 m ≈ a big dog; scale to taste.
//   nature: flower{h,color,center} · tuft{h,color} (grass) · rock{r} · tree{h,color} · bush{r,color}
//   running & body (A): shoe{value} · bottle{r,h,water} · stopwatch{r,value} · heart{r,value} · lungs{r,value}
//                       brain{r,value} · cell{r,value} · medal{r} · trophy{h} · track{w,d}
//   strength & fitness (B): dumbbell{w,r} · barbell{w,r,value} · kettlebell{r} · weightplate{r} · shaker{r,h,water} · muscle{r,value}
//   AI visual & motion (C): camera{s} · clapper{w,h,value} · screen{w,h,text} · waveform{w,h,bars,value}
//   developer tech & AI (D): laptop{w,d,value} · server{w,h,d} · bug{r} · database{r,h} · phone{w,h} · battery{r,h,value}
//                            chip{w} · lock{r,value} · key{len}
//   lab & science: ball{r,hot 0..1 glow} · ice{s} · glass{r,h,water 0..1} · beaker{r,h,water} · flask{r,h,water}
//                  burner{r,h,value} · syringe{r,h,value} · scale{span,tilt deg, + = left side down}
//                  thermometer{value °C,lo,hi,step,h,w,highlight} · gauge{value 0..1,labels[],unit} · chamber{r,h}
//                  anvil{s} · pendulum{h,r,value} · flame{r,h,value} · drop{r} · magnet{r} · rocket{r,h} · planet{r}
//                  clock{r,value} · hourglass{r,h,value} · feather · hammer · bowling{r}
//   primitives & custom: box{size:[w,h,d]} · sphere{r} · cylinder{r,r2,h} · cone{r,h} · torus{r,tube}
//                        parts{parts:[{k: box|sphere|cylinder|cone|torus|rod, at:[x,y,z], rot:[x,y,z], size, r, h, color}]}
//                        sign{text,w,h,color,face} · text{text,w,h,color} · glow{color,size,opacity}
//                        fx{kind: steam|smoke|sparks|burst|splash|bubbles|shockwave|fire, r, color, value}
//                        OR ANY of the 189 channel icon names (auto-extruded into 3D geometry via icon3d!)
//                        OR "svg:<name>" = an SVG the owner imported (`studio.py svg`), extruded the same way (holes kept)
//                        OR "model:<name>" = a CC0 glTF model from the asset library (`studio.py assets search <word>`):
//                          {anim (clip name, e.g. walk|run|idle|cheer), anim_speed, anim_offset s, anim_blend s, anim_loop,
//                          h (height m, default = real size) | size (largest side m), colors: palette|keep|<color>, color}
//                          — keys may switch anim at any u ({u, anim}); 400+ models: food, furniture, kitchen, nature,
//                          buildings, street, vehicles, tech, space, people with 76 animations (knight, mage, rogue…)
//   hybrid 2D ↔ 3D:
//     card2d{draw: icon|"rig:<species>"|"text", text, look: flat|pixel16|sprite8|halftone|comic|cutout|silhouette,
//            w, h, thickness, cut_edge, billboard, two_sided, action, expr} (2D dynamic CanvasTexture in 3D space)
//     multiplane{layers:[{draw, z, x, y, w, h, thickness, look}]} (multi-layer paper cutout with real parallax & shadows)
//     overlay2d[]: [{text, icon, of:"propId", offset:[dx,dy], x, y, u0, u1, z:"front"|"back", color, bg, arrow}]
//     do[]: [{u|t|f, verb, dur, args, stagger}] on ANY prop — runs shared `lib/motion` verbs (pop, drop_bounce, squash,
//           heartbeat, breathe, float, wag, fly_off…) composed onto the prop's pose.
//   colors: white grey water accent accent_hi danger iron metal glass_line chalk board label dial orange (style palette)
//   expr:   neutral shock grin worried stern excited smug · arms: hang hip wave up point hold shrug cheer think present
//   keys:  [{t (s) | u (0..1 of the shot — preferred, shots are re-timed to the voice), at, rot, scale, value, hot, heat,
//            tilt, pose, text, visible, opacity, expr, armL, armR, ease: smooth|easeOut|easeIn|back|anticip|linear|spring
//            |bounceOut|elastic|expoOut|circOut|sine|backIn|steps}]
// fx[]:    [{kind: steam|smoke|sparks|burst|splash|bubbles|shockwave|fire, at:[x,y,z], of:"propId", u:[u0,u1], r, color}]
// camera[]: [{t|u, pos, look, fov, roll, ease, path}] — LEAVE EMPTY to auto-frame every prop for 9:16 (safe margin,
//           slow push-in + small orbit, never static). frame: {elev deg, azim deg, margin 1.15, push 0.08, orbit 6,
//           headroom 0.16, footroom 0.28 = bottom Zone C kept empty for auto-captions}. Backdrop props → "frame": false
// kicks[]: [{t|u, a≈0.07}] 7-frame impact shake · cues[]: [{t|u, sfx}] · flash[]: [{t|u, frames}] · dof: {focus, cinf}
// sfx: whoosh pop hit boom impact thud tick click riser ding thunk rumble crash scrape ting sting creak snap splash
//      sizzle bubbles glitch sparkle heartbeat
// PHYSICS (optional, real rigid bodies — Rapier, deterministic): drops, bounces, throws, collisions, toppling stacks look
//   real, and every impact auto-adds its SFX cue + camera kick (+ fx puff) on the exact contact frame. Add "body" to a prop:
//   body: {kind: dynamic (default) | fixed (static collider) | kinematic (follows its keys, shoves dynamic props),
//          material: plastic|rubber|wood|metal|stone|glass|ice|foam|paper|feather (sets density, bounce, friction, air drag),
//          shape: auto|ball|box|cylinder|capsule|hull|mesh (auto = from the prop's own 3D shape; mesh = concave, fixed only),
//          mass kg, bounce 0..1, friction, drag (terminal speed ≈ 9.81/drag m/s), v:[m/s] launch velocity, spin:[deg/s],
//          release: u (follows its keys until then, then flies on with the key velocity = throw/drop),
//          hit_u: u (auto-times the release so its FIRST impact lands exactly there — put it on the VO keyword),
//          push: [{u, v:[m/s]}], sfx: name|false, fx: burst|smoke|splash|sparks|shockwave (puff at its impacts)}
//   physics: {gravity -9.81 (moon -1.62, 0 = space), floor true, slowmo: [{u:[u0,u1], rate 0.25}], settle s, fx, sfx, kicks}
//   After release a dynamic prop ignores its at/rot keys (value/hot/visible/scale keys still apply). Origins: box/cylinder/
//   cone sit on y (bottom centre), ball/sphere/bowling are centred → a stack of 0.2 m boxes uses y = 0, 0.2, 0.4…
import { ICONS, iconFor } from '../../html/icons.js';
import { simulate } from '../physics.js';
import * as CR from '../creatures.js';
import * as MODELS from '../models.js';
import * as HYBRID from '../hybrid.js';

export function build(ctx, params) {
  const { THREE, MO, PROPS, CAST } = ctx;
  const N = ctx.N, FPS = ctx.fps || 30;
  const P = { set: 'black', props: [], fx: [], kicks: [], cues: [], flash: [], frame: {}, ...params };
  const pal = ctx.job.cast_palette || {};
  const fOf = (k) => (k.u !== undefined ? k.u * (N - 1) : (k.t ?? 0) * FPS);
  if (PROPS.SETS && !PROPS.SETS.includes(P.set)) throw new Error(`stage: set '${P.set}' không có (có: ${PROPS.SETS.join(', ')})`);
  const SO = P.set_opts || {};
  const BASE = PROPS.setBase ? PROPS.setBase(P.set, SO) : P.set === 'lab' ? 0.92 : 0;
  if (P.set === 'lab') PROPS.bench(ctx, { w: 3.4, d: 1.2, top: 0.92 });

  const deg = (v) => (v || 0) * Math.PI / 180;
  const mkMannequin = (defPose) => (p) => {
    const m = PROPS.mannequin(ctx, { color: p.color || 'white', accent: p.accent || 'accent', pose: p.pose || defPose });
    if (p.value !== undefined) m.setValue(p.value);
    if (p.hot !== undefined) m.setHot(p.hot);
    if (p.heat !== undefined && m.setHeat) m.setHeat(p.heat);
    if (p.armL) m.setArmL(p.armL);
    if (p.armR) m.setArmR(p.armR);
    return {
      g: m.g,
      tick: (f) => m.update(f),
      set: {
        pose: (v) => m.setPose(v),
        value: (v) => m.setValue(v),
        hot: (v) => m.setHot(v),
        heat: (v) => m.setHeat && m.setHeat(v),
        armL: (v) => m.setArmL(v),
        armR: (v) => m.setArmR(v),
      },
    };
  };
  const wrapVal = (fn) => (p) => {
    const o = fn(ctx, p);
    if (p.value !== undefined && o.setValue) o.setValue(p.value);
    return { g: o.g, set: { ...(o.set || {}), ...(o.setValue ? { value: (v) => o.setValue(v) } : {}), ...(o.setWater ? { water: (v) => o.setWater(v) } : {}), ...(o.setTilt ? { tilt: (v) => o.setTilt(v) } : {}) } };
  };

  const mk = {
    ball: (p) => { const b = PROPS.ball(ctx, { r: p.r ?? 0.08 }); b.setHot(p.hot ?? 0); return { g: b.g, set: { hot: (v) => b.setHot(v) } }; },
    ice: (p) => ({ g: PROPS.iceCube(ctx, { s: p.s ?? 0.1 }).g }),
    glass: (p) => ({ g: PROPS.glass(ctx, { r: p.r ?? 0.3, h: p.h ?? 0.8, water: p.water ?? 0.6 }).g }),
    scale: (p) => { const s = PROPS.scale(ctx, { span: p.span ?? 0.4 }); s.setTilt(p.tilt ?? 0); return { g: s.g, set: { tilt: (v) => s.setTilt(v) }, scaleObj: s }; },
    thermometer: (p) => {
      const t = PROPS.thermometer(ctx, { lo: p.lo ?? -10, hi: p.hi ?? 30, step: p.step ?? 10, highlight: p.highlight ?? p.value ?? 0, h: p.h ?? 1.2, w: p.w ?? 0.24 });
      t.setValue(p.value ?? 0); return { g: t.g, set: { value: (v) => t.setValue(v) } };
    },
    gauge: (p) => { const q = PROPS.gauge(ctx, { r: p.r ?? 0.2, labels: p.labels || ['0', '50', '100'], unit: p.unit || '' }); q.setValue(p.value ?? 0); return { g: q.g, set: { value: (v) => q.setValue(v) } }; },
    chamber: (p) => ({ g: PROPS.chamber(ctx, { r: p.r ?? 0.35, h: p.h ?? 1.2 }).g }),
    sign: (p) => { const s = PROPS.sign(ctx, { text: p.text || '', w: p.w ?? 1, h: p.h ?? 0.3, color: p.color || 'label', face: p.face || 'board', px: p.px ?? 160 }); return { g: s.g, set: { text: (v) => s.text.userData.setText(v) } }; },
    text: (p) => { const g = ctx.group(ctx.world); const m = ctx.textPlane({ text: p.text || '', px: p.px ?? 180, color: p.color || 'label', w: 1024, h: Math.round(1024 * (p.h ?? 0.25) / (p.w ?? 1)) }, p.w ?? 1, p.h ?? 0.25, g); return { g, set: { text: (v) => m.userData.setText(v) } }; },
    box: (p) => { const g = ctx.group(ctx.world); const [w, h, d] = p.size || [0.3, 0.3, 0.3]; ctx.add(new THREE.BoxGeometry(w, h, d), p.color || 'white', 0, h / 2, 0, g); return { g }; },
    sphere: (p) => { const g = ctx.group(ctx.world); ctx.add(new THREE.SphereGeometry(p.r ?? 0.15, 32, 20), p.color || 'white', 0, 0, 0, g); return { g }; },
    cylinder: (p) => { const g = ctx.group(ctx.world); ctx.add(new THREE.CylinderGeometry(p.r ?? 0.1, p.r2 ?? p.r ?? 0.1, p.h ?? 0.4, 32), p.color || 'white', 0, (p.h ?? 0.4) / 2, 0, g); return { g }; },
    cone: (p) => { const g = ctx.group(ctx.world); ctx.add(new THREE.ConeGeometry(p.r ?? 0.15, p.h ?? 0.4, 32), p.color || 'white', 0, (p.h ?? 0.4) / 2, 0, g); return { g }; },
    torus: (p) => { const g = ctx.group(ctx.world); const m = ctx.add(new THREE.TorusGeometry(p.r ?? 0.2, p.tube ?? 0.04, 12, 48), p.color || 'white', 0, 0, 0, g); m.rotation.x = Math.PI / 2; return { g }; },
    feather: (p) => {
      const g = ctx.group(ctx.world), s = new THREE.Shape(); s.moveTo(0, -0.17);
      s.bezierCurveTo(0.07, -0.08, 0.06, 0.1, 0, 0.17); s.bezierCurveTo(-0.05, 0.1, -0.07, -0.06, 0, -0.17);
      ctx.add(new THREE.ShapeGeometry(s, 16), ctx.toon(p.color || 'white', { side: THREE.DoubleSide }), 0, 0, 0, g);
      ctx.add(new THREE.CylinderGeometry(0.004, 0.004, 0.36, 6), 'grey', 0, -0.02, 0.002, g); return { g };
    },
    hammer: (p) => { const g = ctx.group(ctx.world); ctx.add(new THREE.BoxGeometry(0.035, 0.32, 0.035), p.color || 'grey', 0, 0, 0, g); ctx.add(new THREE.BoxGeometry(0.16, 0.06, 0.06), 'metal', 0, 0.16, 0, g); return { g }; },
    bowling: (p) => { const g = ctx.group(ctx.world); ctx.add(new THREE.SphereGeometry(p.r ?? 0.09, 32, 20), p.color || 'iron', 0, 0, 0, g); return { g }; },
    glow: (p) => { const g = ctx.group(ctx.world); const m = ctx.glow(p.color || 'danger', p.size ?? 0.4, g, 0, 0, 0, p.opacity ?? 0.8); return { g, set: { opacity: (v) => { m.material.opacity = v; } } }; },
    character: () => ({ g: null, card: true }),
    // Nhân vật 3D khớp nối
    mannequin: mkMannequin('idle'),
    human3d: mkMannequin('idle'),
    scientist3d: mkMannequin('idle'),
    runner3d: mkMannequin('run'),
    runner: mkMannequin('run'),
    lifter3d: mkMannequin('lift'),
    lifter: mkMannequin('lift'),
    // Vũ trụ A (Running & Body)
    shoe: wrapVal(PROPS.shoe),
    bottle: wrapVal(PROPS.bottle),
    stopwatch: wrapVal(PROPS.stopwatch),
    heart: wrapVal(PROPS.heart),
    lungs: wrapVal(PROPS.lungs),
    brain: wrapVal(PROPS.brain),
    cell: wrapVal(PROPS.cell),
    bloodcell: wrapVal(PROPS.cell),
    medal: wrapVal(PROPS.medal),
    trophy: wrapVal(PROPS.trophy),
    track: wrapVal(PROPS.track),
    // Vũ trụ B (Strength & Fitness)
    dumbbell: wrapVal(PROPS.dumbbell),
    barbell: wrapVal(PROPS.barbell),
    kettlebell: wrapVal(PROPS.kettlebell),
    weightplate: wrapVal(PROPS.weightplate),
    shaker: wrapVal(PROPS.shaker),
    muscle: wrapVal(PROPS.muscle),
    // Vũ trụ C (AI Visual & Motion)
    camera: wrapVal(PROPS.camera),
    clapper: wrapVal(PROPS.clapper),
    screen: wrapVal(PROPS.screen),
    frame: wrapVal(PROPS.screen),
    waveform: wrapVal(PROPS.waveform),
    // Vũ trụ D (Developer Tech & AI Tools)
    laptop: wrapVal(PROPS.laptop),
    terminal: wrapVal(PROPS.laptop),
    code: wrapVal(PROPS.laptop),
    server: wrapVal(PROPS.server),
    bug: wrapVal(PROPS.bug),
    database: wrapVal(PROPS.database),
    phone: wrapVal(PROPS.phone),
    battery: wrapVal(PROPS.battery),
    chip: wrapVal(PROPS.chip),
    cpu: wrapVal(PROPS.chip),
    lock: wrapVal(PROPS.lock),
    key: wrapVal(PROPS.key),
    // Phòng thí nghiệm & Khoa học / Tự nhiên / Vũ trụ
    beaker: wrapVal(PROPS.beaker),
    flask: wrapVal(PROPS.flask),
    burner: wrapVal(PROPS.burner),
    syringe: wrapVal(PROPS.syringe),
    anvil: wrapVal(PROPS.anvil),
    pendulum: wrapVal(PROPS.pendulum),
    flame: wrapVal(PROPS.flame),
    fire: wrapVal(PROPS.flame),
    drop: wrapVal(PROPS.drop),
    magnet: wrapVal(PROPS.magnet),
    rocket: wrapVal(PROPS.rocket),
    planet: wrapVal(PROPS.planet),
    earth: wrapVal(PROPS.planet),
    clock: wrapVal(PROPS.clock),
    hourglass: wrapVal(PROPS.hourglass),
    // Tổ hợp 3D & Hạt FX 3D
    parts: (p) => PROPS.partsProp(ctx, p),
    svgicon: (p) => wrapVal(PROPS.icon3d)({ ...p, icon: { parts: p.icon_parts || [] } }),   // "svg:<tên>" (tool đổi khi dựng job)
    fx: (p) => { const f = PROPS.fx3d(ctx, p); return { g: f.g, tick: (fr) => f.update(fr, p.value), set: { value: (v) => f.setValue(v) } }; },
    // Con vật + người 3D (engines/three/creatures.js) · thiên nhiên nhỏ
    creature: (p) => mkCreature(p, p.species),
    flower: (p) => ({ g: PROPS.flower(ctx, { h: p.h ?? 0.2, color: p.color, center: p.center }).g }),
    tuft: (p) => ({ g: PROPS.tuft(ctx, { h: p.h ?? 0.12, color: p.color, seed: p.seed ?? 1 }).g }),
    grass: (p) => ({ g: PROPS.tuft(ctx, { h: p.h ?? 0.12, color: p.color, seed: p.seed ?? 1 }).g }),
    rock: (p) => ({ g: PROPS.rock(ctx, { r: p.r ?? 0.12, color: p.color, seed: p.seed ?? 3 }).g }),
    tree: (p) => ({ g: PROPS.tree(ctx, { h: p.h ?? 1.4, color: p.color }).g }),
    bush: (p) => ({ g: PROPS.bush(ctx, { r: p.r ?? 0.22, color: p.color }).g }),
    // Hybrid 2D trong 3D (WP-X)
    card2d: (p) => HYBRID.makeCard2D(ctx, p),
    multiplane: (p) => HYBRID.makeMultiplane(ctx, p),
  };
  function mkCreature(p, species) {
    const c = CR.creature(ctx, { ...p, species });
    return { g: c.g, tick: (f, env) => c.update(f, { ...env, base: BASE }), bind: c.bind, set: c.set, creature: c };
  }
  for (const [alias, sp] of Object.entries(CR.ALIASES)) if (!mk[alias]) mk[alias] = (p) => mkCreature(p, p.species || sp);

  const resolveMake = (p) => {
    if (mk[p.type]) return mk[p.type];
    if (MODELS.isModelType(p.type)) return (q) => MODELS.makeModel(ctx, q);   // "model:<tên>" (kho glTF, WP-A)
    if (p.parts && Array.isArray(p.parts)) return mk.parts;
    if (ICONS[p.type]) return (q) => wrapVal(PROPS.icon3d)({ ...q, icon: p.type });
    const mapped = iconFor(p.type || '');
    if (mapped && mapped !== 'dot' && ICONS[mapped]) return (q) => wrapVal(PROPS.icon3d)({ ...q, icon: mapped });
    return null;
  };

  // ---- dựng prop + chuẩn hoá keyframe
  const items = P.props.map((p, i) => {
    const make = resolveMake(p);
    if (!make) throw new Error(`stage: prop type '${p.type}' không có (có: ${Object.keys(mk).join(', ')})`);
    const o = make(p);
    const base = { at: p.at || [0, 0, 0], rot: p.rot || [0, 0, 0], scale: p.scale ?? 1, value: p.value, hot: p.hot, heat: p.heat, tilt: p.tilt,
      pose: p.pose, text: p.text, visible: p.visible ?? true, opacity: p.opacity, expr: p.expr, armL: p.armL, armR: p.armR };
    const keys = [{ f: 0, ...base }, ...(p.keys || []).map((k) => ({ ...k, f: fOf(k) }))].sort((a, b) => a.f - b.f);
    return { p, o, keys, id: p.id || `${p.type}${i}` };
  });

  const lerpV = (a, b, t) => (Array.isArray(a) ? a.map((v, i) => MO.lerp(v, Array.isArray(b) ? b[i] : b, t)) : MO.lerp(a, b, t));
  // giá trị của thuộc tính tại frame f: nội suy giữa 2 key gần nhất CÓ thuộc tính đó (số/vector); chuỗi đổi bậc
  const valueAt = (keys, prop, f) => {
    const ks = keys.filter((k) => k[prop] !== undefined);
    if (!ks.length) return undefined;
    if (f <= ks[0].f) return ks[0][prop];
    for (let i = 0; i < ks.length - 1; i++) {
      const a = ks[i], b = ks[i + 1];
      if (f <= b.f) {
        if (typeof a[prop] === 'string' || typeof a[prop] === 'boolean') return f < b.f ? a[prop] : b[prop];
        const e = MO.M[b.ease || 'smooth'] || MO.M.smooth;
        const t = b.ease === 'spring' ? MO.M.spring((f - a.f) / FPS) : e((f - a.f) / Math.max(1e-6, b.f - a.f));
        const sa = typeof a[prop] === 'number' && Array.isArray(b[prop]) ? [a[prop], a[prop], a[prop]] : a[prop];
        return lerpV(sa, b[prop], t);
      }
    }
    return ks[ks.length - 1][prop];
  };
  const pose = (it, f) => {
    const at = valueAt(it.keys, 'at', f), rot = valueAt(it.keys, 'rot', f), sc = valueAt(it.keys, 'scale', f);
    const vis = valueAt(it.keys, 'visible', f);
    return { at: [at[0], at[1] + BASE, at[2]], rot, sc: Array.isArray(sc) ? sc : [sc, sc, sc], vis: vis !== false };
  };
  // nhân vật: bảng pha/tốc độ/hướng/dáng tính MỘT LẦN từ keyframe (hàm thuần theo frame, worker nào cũng như nhau)
  items.forEach((it) => { if (it.o.bind) it.o.bind(it.keys, (f) => pose(it, f)); });

  const _nb = new THREE.Box3();
  const boxNoFx = (root, out) => {
    out.makeEmpty();
    root.traverse((o) => {
      if (!o.visible || (o.userData && o.userData.noFrame)) return;
      if (o.isMesh && o.geometry) {
        if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
        _nb.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld);
        out.union(_nb);
      }
    });
    return out;
  };

  // ---- bối cảnh track/stadium/diorama/meadow/tabletop/street: tự vừa vùng đặt prop (đo theo keyframe, chưa tính vật lý)
  let SET = null;
  if (PROPS.setScene && ['track', 'stadium', 'diorama', 'meadow', 'tabletop', 'street'].includes(P.set)) {
    const eb = new THREE.Box3(), tb = new THREE.Box3();
    for (const u of [0, 0.5, 1]) {
      const f = Math.round(u * (N - 1));
      items.forEach((it) => {
        if (it.p.frame === false) return;
        const ps = pose(it, f);
        if (!it.o.g) { eb.expandByPoint(new THREE.Vector3(ps.at[0], ps.at[1], ps.at[2])); return; }
        it.o.g.position.set(...ps.at); it.o.g.scale.set(...ps.sc); it.o.g.updateMatrixWorld(true);
        boxNoFx(it.o.g, tb); if (!tb.isEmpty()) eb.union(tb);
      });
    }
    const ext = eb.isEmpty() ? { cx: 0, cz: 0, sx: 1, sz: 1 }
      : { cx: (eb.min.x + eb.max.x) / 2, cz: (eb.min.z + eb.max.z) / 2, sx: eb.max.x - eb.min.x, sz: eb.max.z - eb.min.z };
    SET = PROPS.setScene(ctx, P.set, SO, ext);
  }

  // ---- bóng tròn dưới vật (blob — máy thời 90 không có shadow map): look retro90/psx bật sẵn, params.blob ghi đè
  const blobK = P.blob === false ? 0 : (typeof P.blob === 'number' ? P.blob : (ctx.look3d && ctx.look3d.blob) || 0);
  const kdir = ((ctx.job.world || {}).lights || {}).key_dir || [-0.5, 1, 0.8];
  const kxz = [-kdir[0], -kdir[2]].map((v) => v / Math.max(1e-3, Math.hypot(kdir[0], kdir[2])));   // bóng lệch ra sau đèn key
  if (blobK > 0 && ctx.P && ctx.P.blob && typeof document !== 'undefined') {
    const bt = ctx.P.tex(ctx.P.blob(64));
    items.forEach((it) => {
      if (!it.o.g || it.p.frame === false || it.p.blob === false) return;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: bt, transparent: true, depthWrite: false, opacity: blobK,
        polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      m.rotation.x = -Math.PI / 2; m.renderOrder = 1; m.castShadow = false; m.receiveShadow = false; m.userData.ndSkip = true;
      ctx.world.add(m); it.blob = m;
    });
  }
  const blobBox = new THREE.Box3();
  const placeBlob = (it) => {
    const b = it.blob, g = it.o.g;
    if (!g.visible) { b.visible = false; return; }
    g.updateMatrixWorld(true); boxNoFx(g, blobBox);
    if (blobBox.isEmpty()) { b.visible = false; return; }
    const hgt = Math.max(0.05, blobBox.max.y - blobBox.min.y), lift = Math.max(0, blobBox.min.y - BASE);
    const k = Math.max(0, 1 - lift / (hgt * 1.5 + 0.3));
    b.visible = k > 0.02; b.material.opacity = blobK * k;
    const off = Math.min(hgt, 1.2) * 0.12 + lift * 0.3;
    b.position.set((blobBox.min.x + blobBox.max.x) / 2 + kxz[0] * off, BASE + 0.004, (blobBox.min.z + blobBox.max.z) / 2 + kxz[1] * off);
    const s = 1.45 * (0.6 + 0.4 * k);
    b.scale.set(Math.max(0.05, blobBox.max.x - blobBox.min.x) * s, Math.max(0.05, blobBox.max.z - blobBox.min.z) * s, 1);
  };

  // ---- vật lý (Rapier, engines/three/physics.js): mô phỏng MỘT LẦN ở đây → quỹ đạo từng frame; frame(f) chỉ đọc lại
  const physOn = Boolean(P.physics) || items.some((it) => it.p.body);
  let phys = null;
  if (physOn) {
    if (!ctx.RAPIER) throw new Error('stage: physics/body cần Rapier — main.js nạp vendor/rapier khi params có physics hoặc body');
    const cards = items.filter((it) => it.p.body && !it.o.g).map((it) => it.id);
    if (cards.length) throw new Error(`stage: body không dùng được cho nhân vật card 2D (${cards.join(', ')}) — dùng mannequin`);
    phys = simulate(ctx.RAPIER, THREE, { N, fps: FPS, set: P.set, base: BASE, fOf, opts: P.physics || {}, table: SET && SET.table,
      bodies: items.filter((it) => it.p.body).map((it) => ({ id: it.id, p: it.p, g: it.o.g, pose: (f) => pose(it, f) })) });
  }
  const tracks = phys ? phys.tracks : {};

  // ---- hệ hạt / FX 3D cấp cảnh (P.fx[]) + hạt lúc va chạm do vật lý sinh (toạ độ thế giới, một đợt)
  const fxItems = (P.fx || []).map((fx) => {
    const inst = PROPS.fx3d(ctx, { kind: fx.kind || fx.k || 'steam', r: fx.r ?? 0.45, color: fx.color, n: fx.n ?? 12 });
    const [u0, u1] = fx.u || [0, 1];
    return { fx, inst, f0: u0 * (N - 1), f1: Math.max(u0 * (N - 1) + 1, u1 * (N - 1)) };
  }).concat((phys ? phys.fx : []).map((h) => ({
    fx: { kind: h.kind, world: true, at: h.at },
    inst: PROPS.fx3d(ctx, { kind: h.kind, r: h.r, color: h.color, n: 14, once: true }), f0: h.f0, f1: h.f1,
  })));

  const apply = (f, env = {}) => {
    const actors = [], byId = {};
    items.forEach((it, i) => {
      const ps = pose(it, f);
      const tr = tracks[it.id];
      if (tr) { const j = Math.max(0, Math.min(N - 1, Math.round(f))) * 7; ps.at = [tr[j], tr[j + 1], tr[j + 2]]; ps.q = [tr[j + 3], tr[j + 4], tr[j + 5], tr[j + 6]]; }
      byId[it.id] = ps;
      if (it.o.card) {
        if (!ps.vis) return;
        const id = MO.idle(f, i + 2), s = ps.sc[0] * (it.p.s ?? 0.8);
        const o = { expr: valueAt(it.keys, 'expr', f) || 'neutral', armL: valueAt(it.keys, 'armL', f) || 'hang',
          armR: valueAt(it.keys, 'armR', f) || 'hang', prop: it.p.prop, look: it.p.look || [0, 0], wave: (f % 24) / 24,
          blink: MO.blinkAt(f, i + 3), bob: id.bob, tilt: id.tilt, headTilt: id.headTilt, pal,
          ol: CAST.olFor(Math.max(1.5, camDist) / s, camFov, 8), rimW: CAST.olFor(Math.max(1.5, camDist) / s, camFov, 3.5) };
        actors.push({ key: CAST.keyOf(o), draw: (g) => CAST.scientist(g, o), x: ps.at[0], y: ps.at[1], z: ps.at[2], s, ground: ps.at[1] });
        return;
      }
      const g = it.o.g; g.visible = ps.vis;
      g.position.set(...ps.at); g.scale.set(...ps.sc);
      if (ps.q) g.quaternion.set(...ps.q); else g.rotation.set(deg(ps.rot[0]), deg(ps.rot[1]), deg(ps.rot[2]));
      // WP-X: nối động từ chuyển động (`do: [{u|t|f, verb, dur, args}]`) từ lib/motion vào prop 3D
      if (Array.isArray(it.p.do) && it.p.do.length && typeof MO.play === 'function' && typeof MO.threeDelta === 'function') {
        const vd = MO.threeDelta(MO.play(it.p.do, f, N, FPS, i, items.length), it.p.h || 1);
        g.position.x += vd.dx; g.position.y += vd.dy; g.position.z += vd.dz;
        g.scale.x *= vd.sx; g.scale.y *= vd.sy; g.scale.z *= vd.sz;
        g.rotation.z += vd.rotZ;
        if (vd.alpha <= 0.01) g.visible = false;
      }
      for (const [k, fn] of Object.entries(it.o.set || {})) { const v = valueAt(it.keys, k, f); if (v !== undefined) fn(v); }
      if (it.o.tick) it.o.tick(f, env);
      if (it.blob) placeBlob(it);
    });
    fxItems.forEach(({ fx, inst, f0, f1 }) => {
      if (f < f0 || f > f1) { inst.g.visible = false; return; }
      inst.g.visible = true;
      const ref = fx.of && byId[fx.of] ? byId[fx.of].at : null;
      const at = fx.world ? fx.at : fx.at ? [fx.at[0], fx.at[1] + BASE, fx.at[2]] : (ref || [0, BASE, 0]);
      inst.g.position.set(...at);
      inst.update(f, (f - f0) / Math.max(1, f1 - f0));
    });
    return actors;
  };

  // ---- camera: khai báo, hoặc tự căn khung dọc quanh mọi prop (tránh cắt mép trên 9:16)
  let camDist = 3, camFov = 38;
  let keys;
  if (P.camera && P.camera.length) {
    keys = P.camera.map((k) => ({ ...k, f: fOf(k), pos: [k.pos[0], k.pos[1] + BASE, k.pos[2]], look: [k.look[0], k.look[1] + BASE, k.look[2]],
      fov: k.fov ?? 38, path: k.path && k.path.map((q) => [q[0], q[1] + BASE, q[2]]) })).sort((a, b) => a.f - b.f);
    camDist = Math.hypot(...keys[0].pos.map((v, i) => v - keys[0].look[i])); camFov = keys[0].fov;
  } else {
    const box = new THREE.Box3(), tmp = new THREE.Box3(), cards = [];
    const samples = physOn ? [0, 0.25, 0.5, 0.75, 1] : [0, 0.5, 1];      // vật lý: vật bay/nảy giữa shot cũng phải lọt khung
    for (const f of samples.map((s) => Math.round(s * (N - 1)))) {
      apply(f).forEach((a) => cards.push(a));
      ctx.world.updateMatrixWorld(true);
      items.forEach((it) => { if (it.p.frame !== false && it.o.g && it.o.g.visible) { boxNoFx(it.o.g, tmp); if (!tmp.isEmpty()) box.union(tmp); } });
    }
    for (const a of cards) box.union(new THREE.Box3(new THREE.Vector3(a.x - 0.45 * a.s * 2.25 / 2, a.y, a.z - 0.1), new THREE.Vector3(a.x + 0.45 * a.s * 2.25 / 2, a.y + a.s * 2.25, a.z + 0.1)));
    if (box.isEmpty()) box.set(new THREE.Vector3(-0.5, BASE, -0.5), new THREE.Vector3(0.5, BASE + 1, 0.5));
    const PRESETS = {
      three_quarter: { elev: 18, azim: 32, orbit: 6 },
      diorama: { elev: 25, azim: 34, orbit: 7 },
      side: { elev: 12, azim: 52, orbit: 4 },
      hero_low: { elev: 7, azim: -20, orbit: 5 },
      front: { elev: 10, azim: 0, orbit: 6 },
    };
    const pr = (P.frame && P.frame.preset && PRESETS[P.frame.preset]) || {};
    // Nếu nhân vật chạy dọc trục -Z (quay lưng khỏi máy) và chưa ép góc → tự xoay 3/4 để thấy dáng + mặt thay vì nhìn lưng
    let smartAz = {};
    if ((P.frame || {}).azim === undefined && !pr.azim && !((SET && SET.frame) || {}).azim) {
      const away = items.some((it) => {
        if (!it.o.creature || it.keys.length < 2) return false;
        const a = pose(it, 0).at, b = pose(it, N - 1).at;
        return (b[2] - a[2]) < -0.5 && Math.abs(b[0] - a[0]) < 0.6;
      });
      if (away) smartAz = { azim: 34, elev: 16 };
    }
    // Tôn trọng Grid 3 tầng (Zone C phụ đề ở đáy 9:16): tự tăng footroom khi captions bật để chân nhân vật/bệ diorama ở trên y = 1280
    const captionsOn = ctx.job.captions_on !== false;
    const gridStage = (ctx.job.layout_grid && ctx.job.layout_grid.stage) || [390, 1240];
    const Href = ctx.job.height || 1920;
    const defFoot = captionsOn ? Math.max(0.22, Math.min(0.32, (Href - (gridStage[1] || 1240)) / Href - 0.06)) : 0;
    const defHead = captionsOn ? 0.16 : 0.2;
    const F = { elev: 10, azim: 0, margin: 1.15, push: 0.08, orbit: 6, fov: 38, headroom: defHead, footroom: defFoot,
      ...((SET && SET.frame) || {}), ...smartAz, ...pr, ...P.frame };
    const hr = Math.max(0, Math.min(0.4, F.headroom || 0));
    const fr = Math.max(0, Math.min(0.4, F.footroom || 0));
    if (hr + fr > 0) {
      const hgt = box.max.y - box.min.y;
      const denom = Math.max(0.35, 1 - hr - fr);
      box.max.y += hgt * hr / denom;
      box.min.y -= hgt * fr / denom;
    }
    const c = box.getCenter(new THREE.Vector3()), sz = box.getSize(new THREE.Vector3());
    const vt = Math.tan(F.fov * Math.PI / 360), ht = vt * 9 / 16;
    const d = Math.max((sz.x / 2) / ht, (sz.y / 2) / vt) * F.margin + sz.z / 2;
    const followIt = F.follow ? items.find((it) => it.id === F.follow) : null;
    const c0 = followIt ? new THREE.Vector3(...pose(followIt, 0).at).setY(c.y) : c;
    const c1 = followIt ? new THREE.Vector3(...pose(followIt, N - 1).at).setY(c.y - sz.y * 0.02) : new THREE.Vector3(c.x, c.y - sz.y * 0.02, c.z);
    const at = (center, az, dd) => [center.x + dd * Math.sin(deg(az)) * Math.cos(deg(F.elev)), center.y + dd * Math.sin(deg(F.elev)), center.z + dd * Math.cos(deg(az)) * Math.cos(deg(F.elev))];
    keys = [{ f: 0, pos: at(c0, F.azim - F.orbit / 2, d), look: [c0.x, c0.y, c0.z], fov: F.fov },
      { f: N - 1, pos: at(c1, F.azim + F.orbit / 2, d * (1 - F.push)), look: [c1.x, c1.y, c1.z], fov: F.fov - 1, ease: 'smooth' }];
    camDist = d; camFov = F.fov;
  }
  const kicks = P.kicks.map((k) => ({ f: Math.round(fOf(k)), a: k.a ?? 0.07 })).concat(phys ? phys.kicks : []);
  const flashes = P.flash.map((k) => ({ f: Math.round(fOf(k)), n: k.frames ?? 2 }));
  const texts = P.props.filter((p) => p.type === 'sign' || p.type === 'text' || (p.type === 'card2d' && p.text))
    .map((p) => p.text).concat((P.overlay2d || []).map((o) => o.text)).filter(Boolean);
  return {
    cues: P.cues.map((k) => ({ f: Math.round(fOf(k)), name: k.sfx || k.name })).concat(phys ? phys.cues : []),
    physics: phys ? phys.info : null,
    objectOf: (id) => { const it = items.find((x) => x.id === id); return it && it.o.g; },   // test/công cụ: group 3D của prop
    overlay2d: P.overlay2d || null,
    texts,
    frame(f) {
      const cam = MO.camFromKeys(keys, f, { creep: 0.0015, kicks });   // camera trước → nhân vật "look: camera" đúng frame
      const actors = apply(f, { cam });
      let flash = 0;
      for (const k of flashes) { const d = f - k.f; if (d >= 0 && d < k.n) flash = 0.9; else if (d >= k.n && d < k.n + 3) flash = Math.max(flash, 0.6 * (1 - (d - k.n + 1) / 4)); }
      return { cam, actors, flash, dof: P.dof || { focus: camDist, cinf: 0 }, shadowAt: cam.look, shadowExt: Math.max(3, camDist) };
    },
  };
}
