// Khung app công đoạn: 1 Projects · 2 Script · 3 Board · 4 Generate · 5 Edit · 6 Review · 7 Deliver · 8 Library.
// Dùng chung: thanh trên (trang + dự án), Jobs drawer, command palette (Ctrl+K), thanh trạng thái, phím tắt (?).
import { h, clear } from './core/dom.js';
import { icon } from './core/icons.js';
import { api } from './core/api.js';
import * as keys from './core/keys.js';
import * as store from './core/store.js';
import * as undo from './core/undo.js';
import { pct, eta } from './core/format.js';
import { Btn, Empty, toast, St } from './ui/kit.js';
import { JobsDrawer, palette, helpOverlay, runJob } from './ui/overlays.js';

const PAGES = [
  { id: 'projects', n: 1, label: 'Projects', ico: 'list', load: () => import('./pages/projects.js'), project: false },
  { id: 'script', n: 2, label: 'Script', ico: 'script', load: () => import('./pages/script.js'), project: true },
  { id: 'board', n: 3, label: 'Board', ico: 'grid', load: () => import('./pages/board.js'), project: true },
  { id: 'generate', n: 4, label: 'Generate', ico: 'sparkles', load: () => import('./pages/generate.js'), project: true },
  { id: 'edit', n: 5, label: 'Edit', ico: 'timeline', load: () => import('./pages/edit.js'), project: true },
  { id: 'review', n: 6, label: 'Review', ico: 'eye', load: () => import('./pages/review.js'), project: true },
  { id: 'deliver', n: 7, label: 'Deliver', ico: 'package', load: () => import('./pages/deliver.js'), project: true },
  { id: 'library', n: 8, label: 'Library', ico: 'book', load: () => import('./pages/library.js'), project: false },
];
const DESIGN = { id: '_design', label: 'Design system', load: () => import('./pages/design.js'), project: false };

const state = { page: 'projects', slug: store.get('project'), sub: null, projects: [], ws: null };

// ---------- mật độ ----------
const density = () => store.get('density', 'compact');
const applyDensity = () => { document.documentElement.dataset.density = density(); };
applyDensity();

// ---------- khung ----------
const projBtn = h('button.proj-switch', { type: 'button', title: 'Chọn dự án (Ctrl+P)', on: { click: () => pickProject() } }, icon('folder'), h('span', '—'));
const nav = h('nav.pages', { 'aria-label': 'Trang công đoạn' });
const jobsBtnLabel = h('span', 'Job');
const jobsBtn = Btn('', { kind: 'ghost', ico: 'terminal', title: 'Hàng đợi job (Ctrl+J)', onClick: () => drawer.toggle() });
jobsBtn.append(jobsBtnLabel);
const top = h('header.topbar',
  h('div.brand', 'forward', h('b', '.'), h('span.dim', 'studio')), projBtn, nav, h('div.grow'),
  Btn('', { kind: 'ghost', ico: 'cmd', title: `Command palette (${keys.mod}+K)`, onClick: () => openPalette() }),
  jobsBtn,
  Btn('', { kind: 'ghost', ico: 'layers', title: 'Mật độ: gọn / thoáng', onClick: () => { store.set('density', density() === 'compact' ? 'comfortable' : 'compact'); applyDensity(); } }),
  Btn('', { kind: 'ghost', ico: 'help', title: 'Phím tắt (?)', onClick: () => helpOverlay() }));
const mainEl = h('main.main', { id: 'content', tabindex: -1 });
const sbJob = h('button', { type: 'button', on: { click: () => drawer.open() } }, icon('terminal'), h('span', 'Không có job'));
const sbCost = h('span.seg', icon('chart'), h('span', '—'));
const sbProj = h('span.seg');
const sbUndo = h('span.seg.dim');
const status = h('footer.statusbar', { role: 'status' }, h('span.seg', sbJob), sbProj, h('span.grow'), sbUndo, sbCost,
  h('span.seg.dim', h('kbd', '?'), ' phím tắt'));
const drawer = JobsDrawer({ onCount: (running) => {
  jobsBtnLabel.textContent = running.length ? `Job · ${running.length}` : 'Job';
  const j = running[0];
  clear(sbJob).append(icon('terminal'), h('span', j ? `${j.title} · ${pct(j.progress)}${j.eta ? ' · ' + eta(j.eta) : ''}` : 'Không có job đang chạy'));
  if (j && j.slug === state.slug) scheduleReload();
  if (!j && wasRunning && state.slug) { reloadWs(); }
  wasRunning = !!j;
} });
let wasRunning = false;
mainEl.append(drawer.el);
const pageHost = h('div', { style: { height: '100%' } });
mainEl.prepend(pageHost);
document.getElementById('app').append(h('div.app', top, mainEl, status));

undo.watch(() => { sbUndo.textContent = undo.canUndo() ? `${keys.mod}Z hoàn tác` : ''; });

// ---------- điều hướng ----------
function hrefFor(page, slug = state.slug, sub = null) {
  if (page === 'projects') return '#/projects';
  if (page === 'library') return `#/library${sub ? '/' + sub : ''}`;
  if (page === '_design') return '#/_design';
  return slug ? `#/p/${encodeURIComponent(slug)}/${page}` : `#/p/_/${page}`;
}
export function go(page, slug = state.slug, sub = null) { location.hash = hrefFor(page, slug, sub); }

function parse() {
  const raw = location.hash.replace(/^#\/?/, '');
  const [path] = raw.split('?');
  const parts = path.split('/').filter(Boolean).map(decodeURIComponent);
  if (parts[0] === 'p' && parts[2]) return { page: parts[2], slug: parts[1] === '_' ? null : parts[1] };
  if (parts[0] === 'library') return { page: 'library', sub: parts[1] || null };
  if (parts[0] === '_design') return { page: '_design' };
  return { page: parts[0] && PAGES.some((p) => p.id === parts[0]) ? parts[0] : 'projects' };
}

function drawNav() {
  clear(nav);
  for (const p of PAGES) {
    const off = p.project && !state.slug;
    nav.append(h(`a${off ? '.off' : ''}`, { href: hrefFor(p.id), 'aria-current': state.page === p.id ? 'page' : null, title: `${p.label} (${p.n})` },
      icon(p.ico), p.label, h('kbd', String(p.n))));
  }
  const pr = state.projects.find((x) => x.slug === state.slug);
  clear(projBtn).append(icon('folder'), h('span', pr ? (pr.title || pr.slug) : state.slug || 'Chọn dự án'));
  clear(sbProj);
  if (state.slug && state.ws) {
    const v = state.ws.qa && state.ws.qa.verdict;
    sbProj.append(h('span.mono.dim', state.slug), v ? St(`QA ${({ green: 'xanh', yellow: 'vàng', red: 'đỏ' })[v]}`, v) : null);
  }
}

let renderToken = 0;
async function route() {
  const r = parse();
  state.page = r.page;
  state.sub = r.sub || null;
  if (r.slug && r.slug !== state.slug) { state.slug = r.slug; store.set('project', r.slug); state.ws = store.cache.get(r.slug) || null; undo.reset(); }
  keys.clearPage();
  drawNav();
  const def = r.page === '_design' ? DESIGN : PAGES.find((p) => p.id === r.page) || PAGES[0];
  const tok = ++renderToken;
  if (def.project && !state.slug) {
    pageHost.replaceChildren(h('div.page', Empty('Chưa chọn dự án', 'Trang này làm việc trên một dự án. Chọn dự án hoặc tạo video mới ở Projects.', [
      Btn('Chọn dự án', { kind: 'primary', ico: 'folder', onClick: () => pickProject() }), Btn('Mở Projects', { onClick: () => go('projects') })])));
    return;
  }
  if (def.project && !state.ws) await reloadWs(false);
  if (tok !== renderToken) return;
  if (def.project && !state.ws) {
    pageHost.replaceChildren(h('div.page', Empty('Không mở được dự án', state.wsError || `Không đọc được dữ liệu của '${state.slug}'.`, [
      Btn('Thử lại', { kind: 'primary', ico: 'refresh', onClick: () => { state.wsError = null; route(); } }), Btn('Chọn dự án khác', { onClick: () => pickProject() })])));
    return;
  }
  const mod = await def.load();
  if (tok !== renderToken) return;
  try {
    const el = await mod.render(ctx());
    if (tok !== renderToken) return;
    pageHost.replaceChildren(el);
  } catch (e) {
    pageHost.replaceChildren(h('div.page', Empty('Không mở được trang', e.message, [Btn('Thử lại', { kind: 'primary', ico: 'refresh', onClick: () => route() })])));
  }
}

let reloadTimer = null;
function scheduleReload() { clearTimeout(reloadTimer); reloadTimer = setTimeout(() => reloadWs(), 4000); }

/** Tải lại workspace của dự án; rerender trang khi dữ liệu đổi (ẩn chớp nháy khi không đổi). */
async function reloadWs(rerender = true) {
  if (!state.slug) return;
  try {
    const ws = await api.workspace(state.slug);
    state.wsError = null;
    const changed = JSON.stringify(ws) !== JSON.stringify(state.ws);
    state.ws = ws;
    store.cache.set(state.slug, ws);
    drawNav();
    if (rerender && changed && PAGES.find((p) => p.id === state.page)?.project) route();
  } catch (e) {
    const first = state.wsError !== e.message;
    state.wsError = e.message;
    if (e.status === 404) { state.ws = null; store.del('project'); }
    if (first) toast(e.status === 404 ? `Không có dự án '${state.slug}'.` : e.message, { kind: 'err' });
    drawNav();
  }
}

function ctx() {
  return {
    slug: state.slug, ws: state.ws, sub: state.sub, drawer, go, reload: () => reloadWs(),
    run: (kind, params, okText) => {
      const p = { ...params };
      // dự án chạy thử: mọi job dựng lại giữ dữ liệu giả (không gọi ElevenLabs) — trừ "tạo lại giọng" là chủ ý
      if (p.target === state.slug && state.ws && state.ws.dry_run && p.dry_run === undefined && kind !== 'redo_voice') p.dry_run = true;
      // nhả trình phát: Windows khoá file đang stream → pipeline không ghi đè được final.mp4
      if (p.target === state.slug) document.querySelectorAll('video, audio').forEach((m) => { try { m.pause(); m.removeAttribute('src'); m.load(); } catch { /* bỏ qua */ } });
      return runJob(drawer, kind, p, okText);
    },
    projects: state.projects, setProject: (slug) => { go(state.page === 'projects' || state.page === 'library' ? 'script' : state.page, slug); },
  };
}

// ---------- chọn dự án / palette ----------
async function loadProjects() {
  try { state.projects = (await api.projects()).items; } catch { state.projects = []; }
  drawNav();
}

function pickProject() {
  palette(() => state.projects.map((p) => ({ label: p.title || p.slug, hint: p.slug, group: 'Dự án', ico: 'folder',
    run: () => go(PAGES.find((x) => x.id === state.page)?.project ? state.page : 'script', p.slug) })));
}

function openPalette() {
  palette(() => [
    ...PAGES.map((p) => ({ label: `Đi tới ${p.label}`, group: 'Trang', ico: p.ico, kbd: String(p.n), run: () => go(p.id) })),
    { label: 'Video mới…', group: 'Lệnh', ico: 'plus', run: () => { go('projects'); setTimeout(() => document.getElementById('new-idea')?.focus(), 200); } },
    { label: 'Mở hàng đợi job', group: 'Lệnh', ico: 'terminal', kbd: `${keys.mod}J`, run: () => drawer.open() },
    { label: 'Kiểm môi trường (doctor)', group: 'Lệnh', ico: 'shield', run: () => runJob(drawer, 'tool', { name: 'doctor' }) },
    ...(state.slug ? [
      { label: 'Chạy tiếp pipeline dự án này', group: 'Lệnh', ico: 'play', run: () => ctx().run('video', { target: state.slug, yes: true }) },
      { label: 'Xuất gói nền tảng (Deliver)', group: 'Lệnh', ico: 'package', run: () => go('deliver') },
    ] : []),
    { label: 'Design system', group: 'Trang', ico: 'palette', run: () => go('_design') },
    { label: 'Bảng phím tắt', group: 'Trợ giúp', ico: 'help', kbd: '?', run: () => helpOverlay() },
    ...state.projects.map((p) => ({ label: p.title || p.slug, hint: p.slug, group: 'Dự án', ico: 'folder', run: () => go(PAGES.find((x) => x.id === state.page)?.project ? state.page : 'script', p.slug) })),
  ]);
}

// ---------- phím tắt toàn cục ----------
for (const p of PAGES) keys.register('global', String(p.n), () => go(p.id), `Trang ${p.label}`, { group: 'Điều hướng' });
keys.register('global', 'Ctrl+K', () => openPalette(), 'Command palette', { inInput: true, group: 'Điều hướng' });
keys.register('global', 'Ctrl+P', () => pickProject(), 'Chọn dự án', { inInput: true, group: 'Điều hướng' });
keys.register('global', 'Ctrl+J', () => drawer.toggle(), 'Mở/đóng hàng đợi job', { inInput: true, group: 'Điều hướng' });
keys.register('global', '?', () => helpOverlay(), 'Bảng phím tắt', { group: 'Trợ giúp' });
keys.register('global', 'Escape', () => (drawer.isOpen() ? drawer.close() : false), 'Đóng drawer / hộp thoại', { group: 'Chung' });
keys.register('global', 'Ctrl+Z', async () => { const l = await undo.undo(); toast(l ? `Đã hoàn tác: ${l}` : 'Không còn gì để hoàn tác'); }, 'Hoàn tác', { group: 'Chung' });
keys.register('global', 'Ctrl+Shift+Z', async () => { const l = await undo.redo(); toast(l ? `Làm lại: ${l}` : 'Không còn gì để làm lại'); }, 'Làm lại', { group: 'Chung' });

async function tickSession() {
  try {
    const s = await api.session();
    const c = s.cost || {};
    clear(sbCost).append(icon('chart'), h('span', `24h: ${c.tts_chars || 0} ký tự TTS · ${c.usd_known ? '$' + c.usd_known.toFixed(2) : '$—'}${(c.usd_unknown || []).length ? ' + chưa rõ giá' : ''}`));
  } catch { /* server tắt: drawer báo lỗi */ }
  setTimeout(tickSession, 30000);
}

window.addEventListener('hashchange', route);
loadProjects().then(() => { if (!location.hash) location.hash = '#/projects'; route(); });
tickSession();
