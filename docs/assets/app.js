// Drone explorer. Airframe = the CAD meshes. Bought parts = shapes built at each part's CAD position and size.
const safeUrl = u => /^https?:\/\//i.test(String(u)) ? u : '#';   // only web links are ever rendered as links
// Click a part (or a table row): it turns purple, the camera moves to it, lines show what it connects to.
// Flight modes: Hover spins the lift propellers; Cruise parks them along the booms and spins the pusher.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const data = await (await fetch('assets/parts.json')).json();
const parts = Object.fromEntries(data.parts.map(p => [p.id, p]));
const exact = {}, prefixes = [];
data.parts.forEach(p => p.nodes.forEach(n => n.endsWith('*') ? prefixes.push([n.slice(0, -1), p.id]) : (exact[n] = p.id)));
const lookup = n => exact[n] || (prefixes.find(([pre]) => n.startsWith(pre)) || [])[1];
const css = getComputedStyle(document.documentElement);
const PURPLE = new THREE.Color(css.getPropertyValue('--purple').trim() || '#7b3fa0');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

const el = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
el.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, 1, 0.02, 60);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8678, 2.0));
const sun = new THREE.DirectionalLight(0xffffff, 1.8); sun.position.set(-3, 6, 2); scene.add(sun);
const root = new THREE.Group(); root.rotation.x = -Math.PI / 2; scene.add(root);   // CAD: x aft, y right, z up

const meshesByPart = {}, pickables = [], base = new Map(), sizeOf = {};
function register(mesh, pid, sys, opacity = 1) {
  const col = new THREE.Color(data.systems[sys].color);
  mesh.material = new THREE.MeshStandardMaterial({ color: col, roughness: 0.75, metalness: sys === 'airframe' ? 0 : 0.15, transparent: true, opacity });
  base.set(mesh, { color: col.clone(), opacity });
  mesh.userData.sys = sys;
  if (pid) { mesh.userData.pid = pid; (meshesByPart[pid] ||= []).push(mesh); pickables.push(mesh); }
}

// ---------- shapes for bought parts, built inside a box (centre c, size s, metres, CAD axes)
const M = (g) => new THREE.Mesh(g);
const cylZ = (r, h) => { const g = new THREE.CylinderGeometry(r, r, h, 40); g.rotateX(Math.PI / 2); return g; };
const cylX = (r, h) => { const g = new THREE.CylinderGeometry(r, r, h, 40); g.rotateZ(Math.PI / 2); return g; };
function blade(len, chord, thick) {
  const sh = new THREE.Shape();
  sh.moveTo(0, -chord * 0.35); sh.quadraticCurveTo(len * 0.25, -chord * 0.6, len * 0.92, -chord * 0.22);
  sh.quadraticCurveTo(len, 0, len * 0.92, chord * 0.18); sh.quadraticCurveTo(len * 0.3, chord * 0.5, 0, chord * 0.3); sh.closePath();
  return new THREE.ExtrudeGeometry(sh, { depth: thick, bevelEnabled: false });
}
const builders = {
  motor(c, s) {                       // vertical outrunner: stator base, spinning bell, shaft
    const g = new THREE.Group(), r = Math.min(s.x, s.y) / 2, h = s.z;
    const b = M(cylZ(r * 0.92, h * 0.28)); b.position.z = -h * 0.36; g.add(b);
    const bell = M(cylZ(r, h * 0.62)); bell.position.z = 0.05 * h; g.add(bell);
    const cap = M(cylZ(r * 0.55, h * 0.1)); cap.position.z = h * 0.41; g.add(cap);
    const sh = M(cylZ(r * 0.12, h * 0.35)); sh.position.z = h * 0.6; g.add(sh);
    return g;
  },
  pusherMotor(c, s) {                 // horizontal outrunner along x
    const g = new THREE.Group(), r = Math.min(s.y, s.z) / 2, L = s.x;
    const b = M(cylX(r * 0.95, L * 0.3)); b.position.x = -L * 0.33; g.add(b);
    const bell = M(cylX(r, L * 0.6)); bell.position.x = L * 0.12; g.add(bell);
    const sh = M(cylX(r * 0.12, L * 0.5)); sh.position.x = L * 0.55; g.add(sh);
    return g;
  },
  prop(c, s, axis) {                  // two-blade propeller; spins about z (lift) or x (pusher)
    const g = new THREE.Group(), D = axis === 'x' ? Math.max(s.y, s.z) : Math.max(s.x, s.y), R = D / 2;
    for (const k of [0, 1]) {
      const m = M(blade(R, D * 0.085, 0.004)); m.rotation.z = k * Math.PI; g.add(m);
    }
    const hub = M(cylZ(D * 0.03, 0.012)); g.add(hub);
    if (axis === 'x') g.rotation.y = Math.PI / 2;
    g.userData.spin = axis;
    return g;
  },
  esc(c, s) {                         // speed controller with heatsink fins
    const g = new THREE.Group();
    g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z * 0.55)));
    const n = 7;
    for (let i = 0; i < n; i++) {
      const f = M(new THREE.BoxGeometry(s.x * 0.9, s.y * 0.06, s.z * 0.45));
      f.position.set(0, -s.y / 2 + s.y * (i + 0.5) / n, s.z * 0.5); g.add(f);
    }
    return g;
  },
  battery(c, s) {                     // 6 x 6 cells, standing
    const g = new THREE.Group(), n = 6, dx = s.x / n, dy = s.y / n, r = Math.min(dx, dy) * 0.47;
    const geo = cylZ(r, s.z * 0.95);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const m = M(geo); m.position.set(-s.x / 2 + dx * (i + 0.5), -s.y / 2 + dy * (j + 0.5), 0); g.add(m);
    }
    return g;
  },
  board(c, s) {                       // flight controller or power module: body, top plate, connectors
    const g = new THREE.Group();
    g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z * 0.8)));
    const top = M(new THREE.BoxGeometry(s.x * 0.8, s.y * 0.7, s.z * 0.2)); top.position.z = s.z * 0.45; g.add(top);
    for (let i = 0; i < 4; i++) { const k = M(new THREE.BoxGeometry(s.x * 0.08, s.y * 0.12, s.z * 0.3)); k.position.set(-s.x / 2 - s.x * 0.03, -s.y * 0.3 + i * s.y * 0.2, 0); g.add(k); }
    return g;
  },
  gps(c, s) { const g = new THREE.Group(), r = Math.min(s.x, s.y) / 2; g.add(M(cylZ(r, s.z * 0.7))); const d = M(new THREE.SphereGeometry(r * 0.8, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2)); d.rotation.x = Math.PI / 2; d.scale.z = 0.35; d.position.z = s.z * 0.3; g.add(d); return g; },
  radio(c, s) { const g = new THREE.Group(); g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z))); const a = M(cylZ(0.003, 0.09)); a.position.set(s.x * 0.35, 0, s.z / 2 + 0.045); g.add(a); return g; },
  pitot(c, s) { const g = new THREE.Group(); g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z))); const t = M(cylX(0.003, 0.16)); t.position.set(-s.x / 2 - 0.08, 0, 0); g.add(t); return g; },
  servo(c, s) { const g = new THREE.Group(); g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z))); const h = M(new THREE.BoxGeometry(s.x * 0.15, s.y * 0.55, s.z * 0.25)); h.position.set(s.x * 0.3, s.y * 0.3, s.z * 0.55); g.add(h); return g; },
  box(c, s) { return M(new THREE.BoxGeometry(s.x, s.y, s.z)); },
  camera(c, s) {                      // body with a lens looking down
    const g = new THREE.Group(); g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z * 0.6)));
    const l = M(cylZ(Math.min(s.x, s.y) * 0.3, s.z * 0.45)); l.position.z = -s.z * 0.5; g.add(l); return g;
  },
  thermal(c, s) {                     // board + small core with a dark window looking down
    const g = new THREE.Group(); g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z * 0.5)));
    const core = M(new THREE.BoxGeometry(s.x * 0.35, s.y * 0.45, s.z * 0.4)); core.position.z = -s.z * 0.42; g.add(core);
    const win = M(cylZ(s.x * 0.12, s.z * 0.12)); win.position.z = -s.z * 0.66; g.add(win); return g;
  },
  spot(c, s) {                        // sensor head: view tube down, diffuser dome up
    const g = new THREE.Group(); g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z * 0.5)));
    const tube = M(cylZ(s.y * 0.18, s.z * 0.5)); tube.position.z = -s.z * 0.45; g.add(tube);
    const d = M(new THREE.SphereGeometry(s.y * 0.2, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2)); d.rotation.x = Math.PI / 2; d.position.z = s.z * 0.25; g.add(d); return g;
  },
  computer(c, s) {                    // board on a heatsink with a fan
    const g = new THREE.Group(); g.add(M(new THREE.BoxGeometry(s.x, s.y, s.z * 0.25)));
    const hs = M(new THREE.BoxGeometry(s.x * 0.55, s.y * 0.6, s.z * 0.55)); hs.position.z = s.z * 0.38; g.add(hs);
    const fan = M(cylZ(s.y * 0.25, s.z * 0.12)); fan.position.z = s.z * 0.7; g.add(fan); return g;
  },
};
function builderFor(node) {
  if (node.startsWith('motor_MN5008')) return ['motor'];
  if (node.startsWith('motor_pusher')) return ['pusherMotor'];
  if (node.startsWith('prop_P18')) return ['prop', 'z'];
  if (node.startsWith('prop_pusher')) return ['prop', 'x'];
  if (node.startsWith('esc_')) return ['esc'];
  if (node.startsWith('battery')) return ['battery'];
  if (node.startsWith('pixhawk') || node.startsWith('power_module')) return ['board'];
  if (node.startsWith('gnss')) return ['gps'];
  if (node.startsWith('telemetry') || node.startsWith('rc_receiver')) return ['radio'];
  if (node.startsWith('airspeed')) return ['pitot'];
  if (node.startsWith('servo_aileron') || node.startsWith('servo_rudder')) return ['servo'];
  return null;
}

// ---------- load the CAD model and swap placeholders for shapes
const gltf = await new GLTFLoader().loadAsync('assets/ridgeback.glb');
root.add(gltf.scene);
const spinning = [];
const swaps = [];
gltf.scene.traverse(o => {
  if (!o.isMesh) return;
  const raw = o.name || o.parent?.name || '';            // the loader strips ':' from node names
  const isAir = /^airframe/.test(raw);
  const node = raw.replace(/^(part|airframe)[_:]?/, '');
  if (isAir && node === 'prop') { o.visible = false; return; }
  const pid = lookup(isAir ? 'airframe:' + node : node);
  const sys = pid ? parts[pid].system : 'airframe';
  const bf = !isAir && builderFor(node);
  if (bf) swaps.push([o, node, pid, sys, bf]);
  else { if (!o.geometry.attributes.normal) o.geometry.computeVertexNormals(); register(o, pid, sys, sys === 'airframe' ? 0.9 : 1); }
});
for (const [o, node, pid, sys, [kind, axis]] of swaps) {
  o.geometry.computeBoundingBox();
  const bb = o.geometry.boundingBox, c = bb.getCenter(new THREE.Vector3()), s = bb.getSize(new THREE.Vector3());
  const obj = builders[kind](c, s, axis);
  obj.position.copy(c); obj.userData.node = node;
  if (pid && !sizeOf[pid]) sizeOf[pid] = s.clone();
  root.add(obj); o.visible = false;
  obj.traverse(m => { if (m.isMesh) register(m, pid, sys, kind === 'prop' ? 0.85 : 1); });
  if (obj.userData.spin) spinning.push(obj);
}

const SHAPE = { thermal_cam: 'thermal', rgb_cam: 'camera', spot_sensor: 'spot', payload_computer: 'computer' };
for (const p of data.parts) {
  if (!p.box || meshesByPart[p.id]) continue;
  const c = new THREE.Vector3(...p.box.c).multiplyScalar(0.001), s = new THREE.Vector3(...p.box.dims).multiplyScalar(0.001);
  const obj = builders[SHAPE[p.id] || 'box'](c, s); obj.position.copy(c);
  root.add(obj); obj.traverse(m => { if (m.isMesh) register(m, p.id, p.system, 1); });
  sizeOf[p.id] = s;
}

// ---------- camera framing and fly-to
const all = new THREE.Box3().setFromObject(root), home = all.getCenter(new THREE.Vector3());
const homePos = home.clone().add(new THREE.Vector3(-1.75, 2.35, -1.55));
controls.target.copy(home); camera.position.copy(homePos);
let fly = null;
function flyTo(target, dist) {
  const dir = camera.position.clone().sub(controls.target).normalize();
  const to = { t: target.clone(), p: target.clone().add(dir.multiplyScalar(dist)) };
  if (reduce) { controls.target.copy(to.t); camera.position.copy(to.p); return; }
  fly = { from: { t: controls.target.clone(), p: camera.position.clone() }, to, k: 0 };
}

// ---------- selection
const boxOf = pid => { const b = new THREE.Box3(); (meshesByPart[pid] || []).forEach(m => b.expandByObject(m)); return b; };
let lines = null, selected = null, sizeBox = null;
function select(pid, fromHash = false) {
  selected = pid || null;
  base.forEach((b, m) => {
    m.material.color.copy(b.color); m.material.emissive.set(0x000000); m.material.depthTest = true; m.renderOrder = 0;
    m.material.opacity = !pid ? b.opacity : (m.userData.sys === 'airframe' && m.userData.pid !== pid ? 0.14 : Math.min(b.opacity, 0.3));
  });
  if (lines) { scene.remove(lines); lines.geometry.dispose(); lines = null; }
  if (sizeBox) { scene.remove(sizeBox); sizeBox = null; }
  document.querySelectorAll('tr[data-id]').forEach(r => r.classList.toggle('sel', r.dataset.id === pid));
  if (!pid) { flyTo(home, homePos.distanceTo(home)); return; }
  const p = parts[pid], pts = [];
  const ctr = m => new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3());
  const groupsOf = id => { const seen = new Map(); (meshesByPart[id] || []).forEach(m => { let g = m; while (g.parent && g.parent !== root && g.parent !== gltf.scene) g = g.parent; seen.set(g, true); }); return [...seen.keys()]; };
  p.connects.forEach(([to]) => {
    (meshesByPart[to] || []).forEach(m => { m.material.opacity = base.get(m).opacity; });
    const targets = groupsOf(to).map(ctr);
    groupsOf(pid).forEach(g => {                        // one line from each copy of this part to its nearest connected part
      const a = ctr(g); let best = null, d = Infinity;
      targets.forEach(t => { const dd = a.distanceTo(t); if (dd < d) { d = dd; best = t; } });
      if (best && d > 1e-4) pts.push(a, best);
    });
  });
  (meshesByPart[pid] || []).forEach(m => { m.material.color.copy(PURPLE); m.material.opacity = 1; m.material.depthTest = false; m.renderOrder = 10; });
  if (pts.length) { lines = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: PURPLE, depthTest: false })); lines.renderOrder = 11; scene.add(lines); }
  const b = boxOf(pid), size = b.getSize(new THREE.Vector3()).length();
  if (p.system !== 'airframe' && (meshesByPart[pid] || []).length) { sizeBox = new THREE.Box3Helper(b, PURPLE); sizeBox.material.depthTest = false; sizeBox.renderOrder = 12; scene.add(sizeBox); }
  flyTo(b.getCenter(new THREE.Vector3()), Math.max(0.7, Math.min(3.4, size * 3.4)));
  showDetail(p);
  if (!fromHash) history.replaceState(null, '', '#' + pid);
}
function tex(t) { try { return window.katex ? katex.renderToString(t, { throwOnError: false }) : esc(t); } catch { return esc(t); } }
function calcBlock(p) {
  if (!p.calc) return '';
  const lines = p.calc.map(([t, why]) => `<div class="line">${tex(t)}</div><p class="why">${esc(why)}</p>`).join('');
  const links = [p.calcStep ? `<a href="calculations.html#${p.calcStep}">step ${p.calcStep.split('-')[1]} on the calculations page</a>` : '',
                 p.calcSheet ? `<a href="${esc(p.calcSheet)}" target="_blank" rel="noopener">${esc(p.calcSheetName)}</a>` : esc(p.calcSheetName || '')].filter(Boolean).join(' and ');
  return `<h3>The numbers behind it</h3><div class="calcbox">${lines}<p class="small">Worked out in ${links}.</p></div>`;
}
function esc(s) { return String(s).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch])); }
function showDetail(p) {
  if (window.RB?.partForm?.(p, document.getElementById('detail'))) return;
  const ed = !!window.RB?.isEditing?.();
  const price = p.status.startsWith('reuse') ? 'owned' : (p.price ? `$${p.price.toFixed(2)} each` : '');
  const conn = p.connects.length ? '<ul>' + p.connects.map(([to, how]) => `<li><button class="link" data-go="${to}">${esc(parts[to]?.name || to)}</button>: ${esc(how)}</li>`).join('') + '</ul>' : '<p>Nothing wired; it runs on its own.</p>';
  const buy = p.buy.length ? '<ul>' + p.buy.map(([s, u, pr], i) => `<li data-buy="${i}"><a href="${esc(safeUrl(u))}" target="_blank" rel="noopener">${esc(s)}</a>, ${esc(pr)}</li>`).join('') + '</ul>' : '<p>Not bought.</p>';
  document.getElementById('detail').innerHTML = `<h2><span data-f="name">${esc(p.name)}</span></h2>
   <dl class="meta"><div><dt>System</dt><dd><span class="key" style="--c:${p.color}"></span>${esc(p.systemName)}</dd></div><div><dt>Status</dt><dd><span data-f="status">${esc(p.status.charAt(0).toUpperCase() + p.status.slice(1))}</span></dd></div>${p.order ? `<div><dt>Bought?</dt><dd><span class="ostate s-${p.order.state.replace(' ', '-')}" data-order="${p.order.key}" data-state="${p.order.state}">${p.order.label}</span>${p.order.date ? `<span class="small"> ${esc(p.order.date)}${p.order.by ? ' by ' + esc(p.order.by) : ''}</span>` : ''}</dd></div>` : ''}<div><dt>Quantity</dt><dd><span data-f="qty">${p.qty}</span></dd></div>${price || ed ? `<div><dt>Price</dt><dd><span data-f="price">${price || '$0 (bundled or printed)'}</span></dd></div>` : ''}<div><dt>Mass</dt><dd><span data-f="mass">${p.mass}</span> g each</dd></div>${p.power_w ? `<div><dt>Power</dt><dd><span data-f="power_w">${p.power_w}</span> W</dd></div>` : ''}</dl>
   ${p.size || sizeOf[p.id] ? `<p class="size"><b>Size</b> <span data-f="size">${esc(p.size || '')}</span>${sizeOf[p.id] ? `${p.size ? '. ' : ''}Drawn at its CAD size: ${[sizeOf[p.id].x, sizeOf[p.id].y, sizeOf[p.id].z].map(v => Math.round(v * 1000)).join(' × ')} mm (outlined).` : ''}</p>` : ''}
   <h3>What it does</h3><p data-f="job">${esc(p.job)}</p><h3>Why we chose it</h3><p data-f="why">${esc(p.why)}</p>${p.without || ed ? `<h3>Without it</h3><p data-f="without">${esc(p.without || '')}</p>` : ''}${p.refs?.length || ed ? '<h3>Evidence</h3><ul class="refs">' + (p.refs || []).map((r, i) => `<li data-ref="${i}"><a href="${esc(safeUrl(r.link))}" target="_blank" rel="noopener">${esc(r.cite)}</a>: ${esc(r.says || '')}</li>`).join('') + '</ul>' + (ed ? '<p data-add="ref"></p>' : '') : ''}${calcBlock(p)}
   <h3>Connects to</h3>${conn}<h3>Where to buy</h3>${buy}${ed ? '<p data-add="buy"></p>' : ''}
   ${p.instead || ed ? `<h3>Considered instead</h3><p data-f="instead">${esc(p.instead || '')}</p>` : ''}${p.source || ed ? `<p class="small">Numbers from: <span data-f="source">${esc(p.source || '')}</span></p>` : ''}
   <p class="small"><a href="#row-${p.id}">Show in the parts table</a> · <a href="${esc(p.edit)}" target="_blank" rel="noopener">Edit this part</a> (data/parts.toml, line ${p.editLine})</p>`;
  document.querySelectorAll('#detail [data-go]').forEach(b => b.addEventListener('click', () => select(b.dataset.go)));
  window.RB?.decorate?.(document.getElementById('detail'));
}
document.querySelectorAll('tr[data-id]').forEach(r => {
  const go = () => { select(r.dataset.id); el.scrollIntoView({ block: 'nearest', behavior: reduce ? 'auto' : 'smooth' }); };
  r.addEventListener('click', go); r.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
});

// ---------- picking and hover label
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2(), tip = document.getElementById('tip');
let down = null;
const pick = e => {
  const r = renderer.domElement.getBoundingClientRect();
  ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const hit = ray.intersectObjects(pickables, false).find(h => h.object.visible);
  return hit ? hit.object.userData.pid : null;
};
renderer.domElement.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => { if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 5) select(pick(e)); });
renderer.domElement.addEventListener('pointermove', e => {
  if (e.buttons) { tip.hidden = true; return; }
  const pid = pick(e); const r = el.getBoundingClientRect();
  if (pid) { tip.textContent = parts[pid].name; tip.style.left = (e.clientX - r.left + 14) + 'px'; tip.style.top = (e.clientY - r.top + 10) + 'px'; tip.hidden = false; renderer.domElement.style.cursor = 'pointer'; }
  else { tip.hidden = true; renderer.domElement.style.cursor = ''; }
});
renderer.domElement.addEventListener('pointerleave', () => { tip.hidden = true; });

// ---------- flight modes
let mode = reduce ? 'still' : 'hover';
document.querySelectorAll('[data-mode]').forEach(b => {
  b.setAttribute('aria-pressed', b.dataset.mode === mode);
  b.addEventListener('click', () => { mode = b.dataset.mode; document.querySelectorAll('[data-mode]').forEach(x => x.setAttribute('aria-pressed', x === b)); });
});
document.getElementById('reset')?.addEventListener('click', () => select(null));
document.querySelectorAll('[data-pick]').forEach(b => b.addEventListener('click', () => select(b.dataset.pick)));

function size() { const w = el.clientWidth, h = el.clientHeight; renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); }
new ResizeObserver(size).observe(el); size();
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05), t = clock.elapsedTime;
  for (const p of spinning) {
    if (p.userData.spin === 'z') {
      if (mode === 'hover') p.rotation.z += dt * 9;
      else if (mode === 'cruise') p.rotation.z += (Math.round(p.rotation.z / Math.PI) * Math.PI - p.rotation.z) * Math.min(1, dt * 4); // park along the boom
    } else if (mode === 'cruise') p.rotateOnAxis(new THREE.Vector3(0, 0, 1), dt * 12);
  }
  if (selected) { const k = 0.35 + 0.25 * Math.sin(t * 3); (meshesByPart[selected] || []).forEach(m => m.material.emissive.copy(PURPLE).multiplyScalar(k)); }
  if (fly) {
    fly.k = Math.min(1, fly.k + dt / 0.9); const e = fly.k < 0.5 ? 2 * fly.k * fly.k : 1 - Math.pow(-2 * fly.k + 2, 2) / 2;
    controls.target.lerpVectors(fly.from.t, fly.to.t, e); camera.position.lerpVectors(fly.from.p, fly.to.p, e);
    if (fly.k >= 1) fly = null;
  }
  controls.update(); renderer.render(scene, camera);
});
const fromHash = () => { const id = location.hash.slice(1); if (parts[id]) select(id, true); };
addEventListener('hashchange', fromHash); fromHash();
window.RB = Object.assign(window.RB || {}, { rerender: () => { if (selected) showDetail(parts[selected]); }, part: id => parts[id], current: () => parts[selected] });
