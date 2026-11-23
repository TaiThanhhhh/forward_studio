// Component dùng chung (headless tối giản, chỉ dùng token CSS). Không framework: mỗi hàm trả về Node.
import { h, clear } from '../core/dom.js';
import { icon } from '../core/icons.js';
import * as store from '../core/store.js';

export function Btn(label, { kind = '', size = '', ico = null, kbd = null, title = null, onClick = null, disabled = false, type = 'button', aria = {} } = {}) {
  const b = h(`button.btn${kind ? '.' + kind : ''}${size ? '.' + size : ''}${!label && ico ? '.icon' : ''}`,
    { type, title: title || (typeof label === 'string' ? null : null), disabled, 'aria-label': !label ? title : null, ...aria });
  if (ico) b.append(icon(ico));
  if (label) b.append(h('span', label));
  if (kbd) b.append(h('kbd', kbd));
  if (onClick) {
    b.addEventListener('click', async (e) => {
      if (b.dataset.busy) return;
      b.dataset.busy = '1';
      try { await onClick(e); } catch (err) { toast(err.message || String(err), { kind: 'err' }); } finally { delete b.dataset.busy; }
    });
  }
  return b;
}

const LV = { ok: 'ok', green: 'ok', success: 'ok', done: 'ok', finished: 'ok', approved: 'ok', warn: 'warn', yellow: 'warn',
  warning: 'warn', changes: 'warn', waiting_clips: 'warn', look_check: 'warn', err: 'err', red: 'err', danger: 'err', failed: 'err',
  qa_failed: 'err', interrupted: 'err', proc: 'proc', running: 'proc', queued: 'proc', info: 'proc' };

export function St(text, tone) { return h(`span.st${LV[tone] ? '.' + LV[tone] : ''}`, text); }

export function Progress(frac, { label = true, done = false } = {}) {
  const v = Math.max(0, Math.min(1, frac || 0));
  const bar = h(`div.prog${done ? '.ok' : ''}`, { role: 'progressbar', 'aria-label': 'Tiến độ', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': Math.round(v * 100) },
    h('i', { style: { width: `${v * 100}%` } }));
  return label ? h('div.row', bar, h('span.mono.dim', `${Math.round(v * 100)}%`)) : bar;
}

export function Empty(title, text, actions = []) {
  return h('div.empty', h('h2', title), text ? h('p', text) : null, actions.length ? h('div.row', actions) : null);
}

export function Callout(kind, title, text, actions = []) {
  return h(`div.callout.${kind}`, h('div.grow', h('b', title), text ? h('div.muted', text) : null), actions.length ? h('div.row', actions) : null);
}

export function Field(label, control, hint) {
  const id = control.id || (control.id = 'f' + Math.random().toString(36).slice(2, 8));
  return h('div.field', h('label', { for: id }, label), control, hint ? h('div.hint', hint) : null);
}

export function Seg(options, value, onChange, { label = '' } = {}) {
  const wrap = h('div.seg-ctl', { role: 'group', 'aria-label': label });
  const draw = (v) => {
    clear(wrap);
    for (const o of options) {
      wrap.append(h('button', { type: 'button', 'aria-pressed': String(o.value === v), on: { click: () => { draw(o.value); onChange(o.value); } } }, o.label));
    }
  };
  draw(value);
  return wrap;
}

export function Panel(title, body, actions = []) {
  return h('section.panel', h('header', h('h3', title), h('div.right.row', actions)), h('div.body', body));
}

/** Bảng: cột {key, label, render?, sort?(row)→giá trị, num?, width?}; sắp xếp bằng tiêu đề, lọc qua filter(row),
 *  chọn nhiều bằng ô check / Shift+click, ảo hoá khi > 200 hàng (chỉ dựng hàng trong khung nhìn). */
export function Table({ columns, rows, rowKey, onOpen, onSelect, selectable = false, filter = null, sortKey = null, sortDir = 1, empty = null }) {
  const st = { sortKey, sortDir, sel: new Set(), last: null };
  const root = h('div', { style: { height: '100%', overflow: 'auto', position: 'relative' } });
  const table = h('table.table', { role: 'grid' });
  const thead = h('thead');
  const tbody = h('tbody');
  table.append(thead, tbody);
  root.append(table);
  const ROW = 30;
  const view = () => {
    let r = filter ? rows.filter(filter) : rows.slice();
    const col = columns.find((c) => c.key === st.sortKey);
    if (col) {
      const f = col.sort || ((x) => x[col.key]);
      r.sort((a, b) => { const x = f(a), y = f(b); return (x > y ? 1 : x < y ? -1 : 0) * st.sortDir; });
    }
    return r;
  };
  let current = [];
  const head = () => {
    clear(thead);
    const tr = h('tr');
    if (selectable) {
      const all = h('input', { type: 'checkbox', 'aria-label': 'Chọn tất cả', on: { change: (e) => {
        st.sel = e.target.checked ? new Set(current.map(rowKey)) : new Set();
        body(); onSelect && onSelect([...st.sel]);
      } } });
      tr.append(h('th.cbx', all));
    }
    for (const c of columns) {
      const sorted = st.sortKey === c.key;
      tr.append(h(`th${c.num ? '.num' : ''}`, { style: c.width ? { width: c.width } : null, 'aria-sort': sorted ? (st.sortDir > 0 ? 'ascending' : 'descending') : null },
        c.sortable === false ? c.label : h('button', { type: 'button', on: { click: () => {
          st.sortDir = st.sortKey === c.key ? -st.sortDir : 1; st.sortKey = c.key; head(); body();
        } } }, c.label, sorted ? icon(st.sortDir > 0 ? 'down' : 'chevron') : null)));
    }
    thead.append(tr);
  };
  const rowEl = (r, i) => {
    const k = rowKey(r);
    const tr = h('tr', { 'aria-selected': String(st.sel.has(k)), tabindex: 0, dataset: { key: k },
      on: { click: (e) => {
        if (e.target.closest('button,a,input')) return;
        if (e.shiftKey && st.last !== null && selectable) {
          const [a, b] = [st.last, i].sort((x, y) => x - y);
          for (let j = a; j <= b; j++) st.sel.add(rowKey(current[j]));
        } else if ((e.ctrlKey || e.metaKey) && selectable) {
          st.sel.has(k) ? st.sel.delete(k) : st.sel.add(k);
        } else {
          st.sel = new Set([k]);
        }
        st.last = i; body(); onSelect && onSelect([...st.sel]);
      }, dblclick: () => onOpen && onOpen(r), keydown: (e) => { if (e.key === 'Enter' && onOpen) onOpen(r); } } });
    if (selectable) tr.append(h('td.cbx', h('input', { type: 'checkbox', checked: st.sel.has(k), 'aria-label': 'Chọn hàng', on: { change: (e) => {
      e.target.checked ? st.sel.add(k) : st.sel.delete(k); onSelect && onSelect([...st.sel]); tr.setAttribute('aria-selected', String(e.target.checked));
    } } })));
    for (const c of columns) {
      const v = c.render ? c.render(r) : r[c.key];
      tr.append(h(`td${c.num ? '.num' : ''}`, { title: typeof v === 'string' ? v : null }, v ?? '—'));
    }
    return tr;
  };
  const body = () => {
    current = view();
    clear(tbody);
    if (!current.length) {
      tbody.append(h('tr', h('td', { colspan: columns.length + (selectable ? 1 : 0), style: { maxWidth: 'none', height: 'auto' } }, empty || h('div.empty', h('p', 'Không có hàng nào.')))));
      return;
    }
    if (current.length <= 200) { current.forEach((r, i) => tbody.append(rowEl(r, i))); return; }
    const top = root.scrollTop, hgt = root.clientHeight || 800;
    const a = Math.max(0, Math.floor(top / ROW) - 10), b = Math.min(current.length, Math.ceil((top + hgt) / ROW) + 10);
    tbody.append(h('tr', { style: { height: `${a * ROW}px` } }));
    for (let i = a; i < b; i++) tbody.append(rowEl(current[i], i));
    tbody.append(h('tr', { style: { height: `${(current.length - b) * ROW}px` } }));
  };
  root.addEventListener('scroll', () => { if (current.length > 200) body(); });
  head(); body();
  return Object.assign(root, { refresh: (newRows) => { if (newRows) rows = newRows; body(); }, selected: () => [...st.sel] });
}

/** Panel chia đôi kéo được, nhớ độ rộng: Split([left, main, right], {id, sizes:[260, null, 320]}). null = co giãn. */
export function Split(parts, { id, sizes }) {
  const saved = store.get(`split.${id}`) || sizes;
  const wrap = h('div.split');
  parts.forEach((p, i) => {
    if (!p) return;
    const w = saved[i];
    p.classList.add('pane');
    if (!p.hasAttribute('tabindex')) p.setAttribute('tabindex', '0');
    if (w === null || w === undefined) p.classList.add('grow'); else p.style.width = `${w}px`;
    wrap.append(p);
    const next = parts[i + 1];
    if (next !== undefined && next !== null && (w !== null || saved[i + 1] !== null)) {
      const target = w !== null && w !== undefined ? p : next;
      const sign = target === p ? 1 : -1;
      const r = h('div.resizer', { role: 'separator', 'aria-orientation': 'vertical', tabindex: 0, 'aria-label': 'Kéo để đổi kích thước (←/→)', 'aria-valuemin': 160, 'aria-valuemax': 720, 'aria-valuenow': Math.round(w || saved[i + 1] || 320) });
      r.addEventListener('keydown', (e) => { if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return; e.preventDefault(); e.stopPropagation(); const tw = target.getBoundingClientRect().width + (e.key === 'ArrowRight' ? 16 : -16) * sign; target.style.width = `${Math.max(160, Math.min(720, tw))}px`; r.setAttribute('aria-valuenow', Math.round(tw)); });
      r.addEventListener('pointerdown', (e) => {
        const x0 = e.clientX, w0 = target.getBoundingClientRect().width;
        r.classList.add('drag'); r.setPointerCapture(e.pointerId);
        const mv = (ev) => { target.style.width = `${Math.max(160, Math.min(720, w0 + sign * (ev.clientX - x0)))}px`; };
        const up = () => {
          r.classList.remove('drag'); r.removeEventListener('pointermove', mv);
          const cur = parts.map((q) => (q && !q.classList.contains('grow') ? Math.round(q.getBoundingClientRect().width) : null));
          store.set(`split.${id}`, cur);
        };
        r.addEventListener('pointermove', mv); r.addEventListener('pointerup', up, { once: true });
      });
      wrap.append(r);
    }
  });
  return wrap;
}

// ---------- toast (có Undo / hành động) ----------
let tray = null;
export function toast(text, { kind = '', action = null, actionLabel = 'Hoàn tác', ms = 5000 } = {}) {
  if (!tray) { tray = h('div.toasts', { role: 'status', 'aria-live': 'polite' }); document.body.append(tray); }
  const el = h(`div.toast${kind ? '.' + kind : ''}`, h('div.grow', text));
  if (action) el.append(Btn(actionLabel, { size: 'sm', onClick: async () => { el.remove(); await action(); } }));
  el.append(Btn('', { kind: 'ghost', size: 'sm', ico: 'x', title: 'Đóng', onClick: () => el.remove() }));
  tray.append(el);
  setTimeout(() => el.remove(), kind === 'err' ? ms * 2 : ms);
  return el;
}

// ---------- modal ----------
export function Modal(title, body, footer = [], { onClose, cls = '' } = {}) {
  const prev = document.activeElement;
  const close = () => { scrim.remove(); document.removeEventListener('keydown', esc, true); onClose && onClose(); prev && prev.focus && prev.focus(); };
  const esc = (e) => { if (e.key === 'Escape') { e.stopPropagation(); close(); } };
  const box = h(`div.modal${cls ? '.' + cls : ''}`, { role: 'dialog', 'aria-modal': 'true', 'aria-label': title },
    title ? h('header', h('h2.grow', title), Btn('', { kind: 'ghost', ico: 'x', title: 'Đóng (Esc)', onClick: () => close() })) : null,
    h('div.body', body), footer.length ? h('footer', footer) : null);
  const scrim = h('div.scrim', { on: { mousedown: (e) => { if (e.target === scrim) close(); } } }, box);
  document.addEventListener('keydown', esc, true);
  document.body.append(scrim);
  setTimeout(() => (box.querySelector('input,textarea,button.primary,select') || box).focus(), 0);
  return { close, box };
}

/** Xác nhận thao tác phá huỷ / tốn thời gian. Trả về Promise<boolean>. */
export function confirm(title, text, { ok = 'Đồng ý', danger = false } = {}) {
  return new Promise((resolve) => {
    let done = false;
    const m = Modal(title, h('p.muted', text), [
      Btn('Huỷ', { onClick: () => { done = true; m.close(); resolve(false); } }),
      Btn(ok, { kind: danger ? 'danger' : 'primary', onClick: () => { done = true; m.close(); resolve(true); } }),
    ], { onClose: () => { if (!done) resolve(false); } });
  });
}

export function copyText(text) {
  if (navigator.clipboard && window.isSecureContext !== false) return navigator.clipboard.writeText(text);
  const t = h('textarea', { style: { position: 'fixed', opacity: 0 } }, text);
  document.body.append(t); t.select(); document.execCommand('copy'); t.remove();
  return Promise.resolve();
}
