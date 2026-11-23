// Lớp phủ toàn cục: command palette (Ctrl+K), bảng phím tắt (?), Jobs drawer.
import { h, clear } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { api, followJob } from '../core/api.js';
import * as keys from '../core/keys.js';
import { ago, eta, STAGE_LABEL } from '../core/format.js';
import { Btn, St, Progress, Modal, toast, Empty } from './kit.js';

// ---------- command palette ----------
export function palette(commands) {
  const input = h('input.input', { placeholder: 'Gõ để tìm trang, dự án, lệnh…', 'aria-label': 'Lệnh', autocomplete: 'off' });
  const ul = h('ul', { role: 'listbox' });
  let items = [], idx = 0;
  const score = (q, s) => {
    if (!q) return 1;
    s = s.toLowerCase(); q = q.toLowerCase();
    if (s.includes(q)) return 2 + (s.startsWith(q) ? 1 : 0);
    let i = 0;
    for (const ch of s) if (ch === q[i]) i++;
    return i === q.length ? 1 : 0;
  };
  const draw = () => {
    const q = input.value.trim();
    items = commands().map((c) => ({ ...c, s: score(q, `${c.label} ${c.group || ''} ${c.hint || ''}`) })).filter((c) => c.s > 0)
      .sort((a, b) => b.s - a.s).slice(0, 40);
    idx = Math.min(idx, Math.max(0, items.length - 1));
    clear(ul);
    items.forEach((c, i) => ul.append(h('li', { role: 'option', 'aria-selected': String(i === idx), on: { mousedown: (e) => { e.preventDefault(); run(i); }, mousemove: () => { if (idx !== i) { idx = i; draw(); } } } },
      icon(c.ico || 'chevron'), h('span', c.label), c.kbd ? h('kbd', c.kbd) : null, h('span.grp', c.group || ''))));
    if (!items.length) ul.append(h('li', h('span.dim', 'Không có lệnh khớp.')));
  };
  const m = Modal('', h('div.cmdk', input, ul), [], { cls: 'cmdk' });
  const run = (i) => { const c = items[i]; if (!c) return; m.close(); setTimeout(() => c.run(), 0); };
  input.addEventListener('input', () => { idx = 0; draw(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { idx = Math.min(items.length - 1, idx + 1); draw(); e.preventDefault(); }
    if (e.key === 'ArrowUp') { idx = Math.max(0, idx - 1); draw(); e.preventDefault(); }
    if (e.key === 'Enter') { run(idx); e.preventDefault(); }
  });
  draw();
  input.focus();
}

// ---------- bảng phím tắt ----------
export function helpOverlay() {
  const groups = {};
  for (const k of keys.list()) (groups[k.group] = groups[k.group] || []).push(k);
  const combo = (k) => h('span', k.combo.split('+').map((p) => h('kbd', p.replace('Ctrl', keys.mod))));
  const row = (k) => h('div', h('span.muted', k.label), combo(k));
  const body = h('div.col', Object.entries(groups).map(([g, ks]) => h('div.col', h('div.label', g), h('div.keys', ks.map(row)))));
  Modal('Phím tắt', body);
}

// ---------- Jobs drawer ----------
export function JobsDrawer({ onCount }) {
  const list = h('ul.list', { role: 'listbox', 'aria-label': 'Job' });
  const log = h('pre.log', { 'aria-live': 'off' });
  const head = h('div.row.grow');
  const el = h('aside.drawer', { 'aria-label': 'Hàng đợi job', inert: '' },
    h('header', icon('terminal'), h('h3', 'Job'), head, Btn('', { kind: 'ghost', ico: 'x', title: 'Đóng (Esc)', onClick: () => close() })),
    h('div.split', h('div.pane.side', { style: { width: '300px' } }, list), h('div.pane.grow', log)));
  let jobs = [], sel = null, follow = null, timer = null, opened = false;
  const close = () => { opened = false; el.classList.remove('open'); el.setAttribute('inert', ''); };
  const open = (id) => { opened = true; el.classList.add('open'); el.removeAttribute('inert'); refresh().then(() => select(id || sel || (jobs[0] && jobs[0].id))); };
  const tone = (j) => j.status === 'running' ? 'running' : j.status === 'queued' ? 'queued' : j.exit_code === 12 ? 'qa_failed' : j.status;
  const label = (j) => ({ running: 'Đang chạy', queued: 'Chờ', finished: j.stage === 'done' ? 'Xong' : (j.stage || 'Xong'), failed: 'Lỗi', cancelled: 'Đã huỷ', interrupted: 'Bị ngắt' }[j.status] || j.status);
  const draw = () => {
    clear(list);
    if (!jobs.length) list.append(h('li', Empty('Chưa có job', 'Job xuất hiện ở đây khi anh tạo video, xuất gói hay render lại một shot.')));
    for (const j of jobs) {
      list.append(h(`li.clickable${j.id === sel ? '.sel' : ''}`, { tabindex: 0, role: 'option', 'aria-selected': String(j.id === sel), on: { click: () => select(j.id), keydown: (e) => e.key === 'Enter' && select(j.id) } },
        h('div.col.grow', { style: { gap: '4px' } },
          h('div.row', h('span.ellipsis.grow', j.title), St(label(j), tone(j))),
          j.status === 'running' ? h('div.row', Progress(j.progress || 0), h('span.dim.mono', [j.current && (STAGE_LABEL[j.current] || j.current), j.frames && `${j.frames[0]}/${j.frames[1]} frame`, eta(j.eta)].filter(Boolean).join(' · '))) :
            h('span.dim', ago(j.ended || j.created)))));
    }
    const running = jobs.filter((j) => j.status === 'running' || j.status === 'queued');
    onCount && onCount(running, jobs);
  };
  const select = (id) => {
    sel = id; draw();
    const j = jobs.find((x) => x.id === id);
    clear(head);
    if (follow) { follow.close(); follow = null; }
    clear(log);
    if (!j) return;
    head.append(h('span.mono.dim.ellipsis', `$ python ${j.argv.join(' ')}`), h('span.grow'),
      j.status === 'running' || j.status === 'queued' ? Btn('Huỷ', { size: 'sm', kind: 'danger', ico: 'stop', onClick: async () => { await api.cancelJob(j.id); toast('Đã gửi lệnh huỷ — dừng cả tiến trình con.'); refresh(); } }) :
        Btn('Chạy lại', { size: 'sm', ico: 'refresh', disabled: !j.params || !Object.keys(j.params).length, onClick: async () => { const n = (await api.startJob(j.kind, j.params)).job; toast(`Đã xếp hàng: ${n.title || j.title}`, { kind: 'ok' }); refresh().then(() => select(n.id)); } }));
    follow = followJob(id, { onLines: (lines) => {
      const atEnd = log.scrollTop + log.clientHeight >= log.scrollHeight - 30;
      for (const ln of lines) log.append(h(`span${/^▶/.test(ln) ? '.stage' : /✖|⛔|Lỗi|Error|Traceback/.test(ln) ? '.bad' : /⚠/.test(ln) ? '.warn' : ''}`, ln + '\n'));
      if (atEnd) log.scrollTop = log.scrollHeight;
    }, onEnd: () => refresh() });
  };
  const refresh = async () => {
    try { jobs = (await api.jobs()).items; } catch (e) { toast(e.message, { kind: 'err' }); }
    draw();
  };
  const tick = async () => { await refresh(); clearTimeout(timer); timer = setTimeout(tick, jobs.some((j) => j.status === 'running' || j.status === 'queued') ? 1500 : 6000); };
  tick();
  el.addEventListener('keydown', (e) => { if (e.key === 'Escape') { close(); e.stopPropagation(); } });
  return { el, open, close, toggle: () => (opened ? close() : open()), refresh, isOpen: () => opened };
}

/** Gửi job + mở drawer + toast lỗi dễ hiểu. Trả về job hoặc null. */
export async function runJob(drawer, kind, params, okText) {
  try {
    const j = (await api.startJob(kind, params)).job;
    toast(okText || `Đã xếp hàng: ${j.title}`, { kind: 'ok' });
    drawer.open(j.id);
    return j;
  } catch (e) {
    toast(`Không chạy được: ${e.message}`, { kind: 'err' });
    return null;
  }
}
