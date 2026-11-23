// 4 · Generate — bảng sản xuất cho Google Flow (thay scripts.html): thứ tự theo cây keyframe (ảnh làm nguồn trước),
// chép prompt một phím (C), checklist tự lưu, thả nhiều clip vào trang → tự map vào đúng shot, tiến độ x/y.
// Hành động chính: Chạy tiếp (bật khi đủ clip).
import { h, clear } from '../core/dom.js';
import { uploadClip, thumbUrl, projectFile } from '../core/api.js';
import * as keys from '../core/keys.js';
import * as store from '../core/store.js';
import * as undo from '../core/undo.js';
import { Btn, St, Progress, Empty, Modal, toast, copyText, Callout } from '../ui/kit.js';

const MODE = { frames_start: 'Frames · ảnh đầu', frames_start_end: 'Frames · ảnh đầu + cuối', ingredients: 'Ingredients', auto: 'tự chọn' };

/** Map file → shot: tên có C\d\d → shot đó; còn lại → theo thứ tự các shot còn thiếu clip. */
export function mapFiles(files, shots) {
  const want = shots.filter((s) => s.engine === 'flow');
  const missing = want.filter((s) => !s.clip).map((s) => s.id);
  const out = [];
  const used = new Set();
  for (const f of files) {
    const m = f.name.toUpperCase().match(/\bC(\d{2})\b|C(\d{2})[^0-9]/);
    const sid = m ? `C${m[1] || m[2]}` : null;
    if (sid && want.some((s) => s.id === sid)) { out.push({ file: f, sid, how: 'theo tên file' }); used.add(sid); }
  }
  const rest = missing.filter((s) => !used.has(s));
  for (const f of files) {
    if (out.some((o) => o.file === f)) continue;
    const sid = rest.shift();
    out.push({ file: f, sid: sid || null, how: sid ? 'theo thứ tự shot còn thiếu' : 'không còn shot trống' });
  }
  return out;
}

export async function render(ctx) {
  const w = ctx.ws;
  const shots = w.shots_detail || [];
  const flow = shots.filter((s) => s.engine === 'flow');
  const level = Object.fromEntries((w.keyframes || []).map((k) => [k.id, k]));
  const ordered = flow.slice().sort((a, b) => ((level[a.id] || {}).level || 0) - ((level[b.id] || {}).level || 0) || shots.indexOf(a) - shots.indexOf(b));
  const ckKey = `gen.check.${ctx.slug}`;
  const checks = store.get(ckKey, {});
  const have = () => flow.filter((s) => s.clip).length;
  const prog = h('div.row');
  const drawProg = () => clear(prog).append(h('span.mono', `${have()}/${flow.length} clip`), Progress(flow.length ? have() / flow.length : 1, { done: have() === flow.length }));
  const runBtn = Btn('Chạy tiếp', { kind: 'primary', ico: 'play', onClick: () => ctx.run('video', { target: ctx.slug, yes: true, dry_run: !!ctx.ws.dry_run }, 'Đang ingest clip + dựng video') });
  const items = [];          // [{el, prompts:[{key, text, el}]}] để điều hướng bằng phím
  let cur = { i: 0, p: 0 };

  const setCheck = (k, v, label) => {
    const prev = !!checks[k];
    checks[k] = v; store.set(ckKey, checks);
    undo.push({ label, undo: () => { checks[k] = prev; store.set(ckKey, checks); refresh(); }, redo: () => { checks[k] = v; store.set(ckKey, checks); refresh(); } });
  };
  const list = h('div.col', { style: { padding: '12px 16px', gap: '8px' } });
  const card = (id, title, sub, prompts, extra = []) => {
    const pEls = prompts.map((p) => {
      const ck = `${id}:${p.key}`;
      const box = h('input', { type: 'checkbox', checked: !!checks[ck], 'aria-label': `Đã tạo ${p.label} cho ${id}`, on: { change: (e) => setCheck(ck, e.target.checked, `${e.target.checked ? 'Đánh dấu' : 'Bỏ đánh dấu'} ${id} ${p.label}`) } });
      const pre = h('div.prompt', { tabindex: 0, role: 'region', 'aria-label': `Prompt ${p.label} của ${id}` }, p.text);
      const copy = async () => {
        await copyText(p.text);
        if (!checks[`${ck}:copied`]) { checks[`${ck}:copied`] = true; store.set(ckKey, checks); }
        toast(`Đã chép: ${id} · ${p.label}`, { kind: 'ok', ms: 1800 });
      };
      return { key: p.key, text: p.text, copy, el: h('div.col', { style: { gap: '4px' } },
        h('div.row', h('label.check', box, p.label), h('span.grow'), checks[`${ck}:copied`] ? h('span.dim', 'đã chép') : null,
          Btn('Chép', { size: 'sm', ico: 'copy', kbd: 'C', onClick: copy })), pre), pre };
    });
    const el = h('section.panel', { tabindex: 0, 'aria-label': `${id} ${title}` },
      h('header', h('span.mono', id), h('h3', title), h('span.grow'), ...extra),
      h('div.body.col', sub ? h('div.muted', sub) : null, pEls.map((p) => p.el)));
    items.push({ el, prompts: pEls, id });
    el.addEventListener('focus', () => { cur.i = items.findIndex((x) => x.el === el); highlight(); });
    return el;
  };
  const refresh = () => ctx.reload();

  const build = () => {
    clear(list); items.length = 0;
    if (!flow.length) { list.append(Empty('Hôm nay không cần Flow', 'Mọi shot dựng bằng code — chuyển qua Edit / Review sau khi render.', [Btn('Mở Edit', { onClick: () => ctx.go('edit') })])); return; }
    for (const ing of w.ingredients || []) {
      if (ing.prompt) list.append(card(ing.id, 'Ingredient (ảnh tham chiếu)', ing.desc, [{ key: 'img', label: 'Ảnh ingredient', text: ing.prompt }]));
    }
    let lastLevel = -1;
    for (const s of ordered) {
      const lv = (level[s.id] || {}).level || 0;
      if (lv !== lastLevel) { list.append(h('div.label', { style: { marginTop: '8px' } }, lv === 0 ? 'Bước 1 · shot độc lập (tạo trước)' : `Bước ${lv + 1} · cần ảnh của shot trước`)); lastLevel = lv; }
      const pr = s.prompts || {};
      const ps = [];
      if (pr.start) ps.push({ key: 'start', label: 'Ảnh đầu (Nano Banana)', text: pr.start });
      if (pr.end) ps.push({ key: 'end', label: 'Ảnh cuối', text: pr.end });
      if (pr.video) ps.push({ key: 'video', label: 'Video (Flow)', text: pr.video });
      const dep = (level[s.id] || {}).depends || [];
      const shotIn = h('input', { type: 'file', accept: '.mp4,.mov,.webm,.mkv', hidden: true,
        on: { change: () => shotIn.files[0] && upload([{ file: shotIn.files[0], sid: s.id, how: 'chọn trên thẻ shot' }]) } });
      const cardEl = card(s.id, `${s.beat || ''} · ${MODE[s.mode] || s.mode || ''}`, [dep.length ? `Dùng ảnh của ${dep.join(', ')} làm khung` : null, s.vo].filter(Boolean).join(' — '), ps,
        [s.frames && s.frames.start ? h('a', { href: projectFile(ctx.slug, s.frames.start), download: `${s.id}_start.png`, title: `Tải ảnh đầu ${s.id}` },
          h('img.thumb', { src: thumbUrl('projects', `${ctx.slug}/${s.frames.start}`, 64), alt: `Ảnh đầu ${s.id}`, width: 27, height: 48 })) : null,
        s.frames && s.frames.end ? h('a', { href: projectFile(ctx.slug, s.frames.end), download: `${s.id}_end.png`, title: `Tải ảnh cuối ${s.id}` },
          h('img.thumb', { src: thumbUrl('projects', `${ctx.slug}/${s.frames.end}`, 64), alt: `Ảnh cuối ${s.id}`, width: 27, height: 48 })) : null,
        s.clip ? St(`đủ clip · ${s.clip}`, 'ok') : St('thiếu clip', 'warn'),
        Btn(s.clip ? 'Đổi clip…' : 'Nạp clip…', { size: 'sm', ico: 'upload', onClick: () => shotIn.click() }), shotIn]);
      cardEl.addEventListener('dragover', (e) => { e.preventDefault(); });
      cardEl.addEventListener('drop', (e) => {
        const f = [...(e.dataTransfer?.files || [])].find((x) => /\.(mp4|mov|webm|mkv)$/i.test(x.name));
        if (f) { e.preventDefault(); e.stopPropagation(); dragDepth = 0; zone.classList.remove('on'); upload([{ file: f, sid: s.id, how: `thả trực tiếp lên ${s.id}` }]); }
      });
      list.append(cardEl);
    }
    highlight();
  };
  const highlight = () => {
    items.forEach((it, i) => it.prompts.forEach((p, j) => p.pre.classList.toggle('focus', i === cur.i && j === cur.p)));
  };
  const currentPrompt = () => { const it = items[cur.i]; return it && it.prompts[Math.min(cur.p, it.prompts.length - 1)]; };

  // ---- thả clip
  const zone = h('div.dropzone', 'Thả clip Flow vào đây — tự map theo tên (C03…) hoặc theo shot còn thiếu');
  let dragDepth = 0;
  const onEnter = (e) => { if ([...(e.dataTransfer.types || [])].includes('Files')) { dragDepth++; zone.classList.add('on'); e.preventDefault(); } };
  const onLeave = () => { dragDepth = Math.max(0, dragDepth - 1); if (!dragDepth) zone.classList.remove('on'); };
  const onDrop = (e) => {
    e.preventDefault(); dragDepth = 0; zone.classList.remove('on');
    const files = [...e.dataTransfer.files].filter((f) => /\.(mp4|mov|webm|mkv)$/i.test(f.name));
    if (!files.length) { toast('Chỉ nhận .mp4 / .mov / .webm / .mkv', { kind: 'warn' }); return; }
    confirmMap(mapFiles(files, shots));
  };
  const confirmMap = (rows) => {
    const body = h('table.table', h('thead', h('tr', h('th', 'File'), h('th', 'Shot'), h('th', 'Cách map'))),
      h('tbody', rows.map((r) => h('tr', h('td', r.file.name), h('td.mono', r.sid || '—'), h('td.dim', r.how)))));
    const m = Modal(`Tải ${rows.filter((r) => r.sid).length} clip`, body, [Btn('Huỷ', { onClick: () => m.close() }),
      Btn('Tải lên', { kind: 'primary', ico: 'upload', onClick: async () => { m.close(); await upload(rows.filter((r) => r.sid)); } })]);
  };
  const upload = async (rows) => {
    let ok = 0;
    for (const r of rows) {
      const t = toast(`${r.sid}: đang tải ${r.file.name}…`, { ms: 60000 });
      try {
        await uploadClip(ctx.slug, r.sid, r.file, (f) => { t.querySelector('.grow').textContent = `${r.sid}: ${Math.round(f * 100)}% · ${r.file.name}`; });
        ok++; t.remove();
      } catch (e) { t.remove(); toast(`${r.sid}: ${e.message}`, { kind: 'err', action: () => upload([r]), actionLabel: 'Thử lại' }); }
    }
    if (ok) { toast(`Đã tải ${ok} clip`, { kind: 'ok' }); refresh(); }
  };
  const fileInput = h('input', { type: 'file', accept: '.mp4,.mov,.webm,.mkv', multiple: true, hidden: true, on: { change: () => { if (fileInput.files.length) confirmMap(mapFiles([...fileInput.files], shots)); } } });
  const page = h('div.page.fill', { on: { dragenter: onEnter, dragleave: onLeave, dragover: (e) => e.preventDefault(), drop: onDrop } },
    h('div.pagehead', h('h1', 'Generate'), h('span.sub', 'Google Flow · tạo theo thứ tự dưới đây'), prog, h('span.grow'),
      Btn('Chọn clip…', { ico: 'upload', onClick: () => fileInput.click() }), fileInput, runBtn),
    flow.length && have() < flow.length ? h('div', { style: { padding: '8px 16px 0' } }, Callout('info', 'Cách làm',
      'Tạo ảnh/clip trong Flow theo thứ tự từ trên xuống (ảnh nguồn trước). Phím: ↑/↓ chọn thẻ · Tab đổi prompt · C chép · X đánh dấu xong. Kéo thả cả loạt clip vào trang — tool tự map đúng shot.')) : null,
    h('div', { style: { flex: 1, overflow: 'auto' } }, list), zone);
  keys.register('page', 'C', () => { const p = currentPrompt(); if (p) p.copy(); }, 'Chép prompt đang chọn');
  keys.register('page', 'ArrowDown', () => { cur = { i: Math.min(items.length - 1, cur.i + 1), p: 0 }; highlight(); items[cur.i]?.el.scrollIntoView({ block: 'nearest' }); }, 'Thẻ kế');
  keys.register('page', 'ArrowUp', () => { cur = { i: Math.max(0, cur.i - 1), p: 0 }; highlight(); items[cur.i]?.el.scrollIntoView({ block: 'nearest' }); }, 'Thẻ trước');
  keys.register('page', 'Tab', () => { const it = items[cur.i]; if (!it) return false; cur.p = (cur.p + 1) % it.prompts.length; highlight(); }, 'Prompt kế trong thẻ');
  keys.register('page', 'X', () => { const it = items[cur.i], p = currentPrompt(); if (!p) return; const k = `${it.id}:${p.key}`; setCheck(k, !checks[k], `Đánh dấu ${it.id} ${p.key}`); build(); }, 'Đánh dấu prompt đang chọn đã tạo');
  build(); drawProg();
  runBtn.disabled = flow.length > 0 && have() < flow.length;
  runBtn.title = runBtn.disabled ? `Còn thiếu ${flow.length - have()} clip` : '';
  return page;
}
