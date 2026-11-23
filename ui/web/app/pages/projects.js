// 1 · Projects — bảng dự án (sắp xếp/lọc/chọn nhiều + nút Việc tiếp theo) + tạo video mới + lô 10 ý tưởng (dán ideas.json tại chỗ).
import { h, clear } from '../core/dom.js';
import { api } from '../core/api.js';
import * as keys from '../core/keys.js';
import * as store from '../core/store.js';
import { ago, dur } from '../core/format.js';
import { Btn, St, Table, Field, Seg, Empty, Callout, toast, copyText } from '../ui/kit.js';

const STAGE_TONE = { done: 'ok', running: 'proc', queued: 'proc', waiting_clips: 'warn', look_check: 'warn', confirm_map: 'warn',
  need_storyboard: 'warn', qa_failed: 'err', failed: 'err', storyboard_invalid: 'err', lint_failed: 'err' };

function nextActionForRow(ctx, r) {
  const st = r.status;
  if (st === 'need_storyboard') return Btn('Dán storyboard', { size: 'sm', ico: 'script', onClick: () => ctx.go('script', r.slug) });
  if (st === 'storyboard_invalid' || st === 'lint_failed') return Btn('Sửa lỗi JSON', { size: 'sm', ico: 'pen', onClick: () => ctx.go('script', r.slug) });
  if (st === 'waiting_clips' || st === 'confirm_map') return Btn('Nạp clip Flow', { size: 'sm', ico: 'sparkles', onClick: () => ctx.go('generate', r.slug) });
  if (st === 'look_check') return Btn('Duyệt look', { size: 'sm', ico: 'check', onClick: () => ctx.run('video', { target: r.slug, look_ok: true, yes: true, dry_run: !!r.dry_run }, `Duyệt look · ${r.slug}`) });
  if (st === 'qa_failed') return Btn('Xem QA', { size: 'sm', ico: 'eye', onClick: () => ctx.go('review', r.slug) });
  if (st === 'done') return Btn('Deliver', { size: 'sm', ico: 'package', onClick: () => ctx.go('deliver', r.slug) });
  return Btn('Mở', { size: 'sm', kind: 'ghost', onClick: () => ctx.setProject(r.slug) });
}

export async function render(ctx) {
  const [data, ideasData] = await Promise.all([
    api.projects(true).catch(() => ({ items: [] })),
    api.ideas().catch(() => ({ items: [] })),
  ]);
  let items = data.items;
  let batches = ideasData.items || [];
  const draft = store.autosave('draft.new', { idea: '', style: 'auto', narrative: 'auto', voice: '', flow: 'auto', dry: false, open: !items.length });
  let q = store.get('projects.q', '');
  let showDemo = store.get('projects.demo', false);

  // ---- tạo video
  const idea = h('textarea.textarea', { id: 'new-idea', rows: 2, placeholder: 'What happens if you drop a 1,000°C steel ball into ice water?',
    'aria-label': 'Ý tưởng video (tiếng Anh)', value: draft.state.idea });
  idea.value = draft.state.idea;
  const plan = h('div.row.wrap.muted', { 'aria-live': 'polite' });
  const styleSel = h('select.select', { 'aria-label': 'Style' }, h('option', { value: 'auto' }, 'Tự chọn theo chủ đề'));
  const narrSel = h('select.select', { 'aria-label': 'Dạng kịch bản' }, h('option', { value: 'auto' }, 'Tự xoay vòng'));
  const voice = h('input.input', { placeholder: 'auto (vd Brian)', value: draft.state.voice, 'aria-label': 'Giọng' });
  const dry = h('input', { type: 'checkbox', checked: draft.state.dry });
  Promise.all([api.styles(), api.narratives('')]).then(([st, nr]) => {
    for (const s of st.items || []) styleSel.append(h('option', { value: s.id }, `${s.name} · ${s.engine}${s.auto === false ? ' · chỉ chọn tay' : ''}`));
    for (const n of nr.items || []) narrSel.append(h('option', { value: n.id }, n.name));
    styleSel.value = draft.state.style; narrSel.value = draft.state.narrative;
  }).catch(() => {});
  let pt = null;
  const preview = () => {
    clearTimeout(pt);
    const t = idea.value.trim();
    if (t.length < 12) { clear(plan).append(h('span.dim', 'Gõ ý tưởng để xem kế hoạch: style · giọng · dạng kịch bản · có Flow hay toàn code.')); return; }
    pt = setTimeout(async () => {
      try {
        const p = await api.plan({ topic: t, style: styleSel.value, narrative: narrSel.value, ...(draft.state.flow !== 'auto' ? { flow: draft.state.flow === 'flow' ? 1 : 0 } : {}) });
        clear(plan).append(h('span', 'Style ', h('b', p.style)), h('span.dim', '·'), h('span', 'giọng ', h('b', (p.voice && p.voice.short) || 'auto')), h('span.dim', '·'),
          h('span', 'kịch bản ', h('b', p.narrative_name || p.narrative || '—')), h('span.dim', '·'), St(p.uses_flow ? 'có Flow' : 'toàn code', p.uses_flow ? 'warn' : 'ok'),
          p.reason ? h('span.dim.ellipsis', { title: p.reason }, p.reason) : null);
      } catch (e) { clear(plan).append(h('span.dim', e.message)); }
    }, 350);
  };
  idea.addEventListener('input', () => { draft.save({ idea: idea.value }); preview(); });
  styleSel.addEventListener('change', () => { draft.save({ style: styleSel.value }); preview(); });
  narrSel.addEventListener('change', () => { draft.save({ narrative: narrSel.value }); preview(); });
  voice.addEventListener('input', () => draft.save({ voice: voice.value }));
  dry.addEventListener('change', () => draft.save({ dry: dry.checked }));
  const create = async () => {
    const t = idea.value.trim();
    if (t.length < 12 || !t.includes(' ')) { toast('Ý tưởng cần là một câu (vd "What happens if…").', { kind: 'warn' }); idea.focus(); return; }
    const p = { target: t, style: styleSel.value, narrative: narrSel.value, voice: voice.value.trim() || 'auto', dry_run: dry.checked, yes: true };
    if (draft.state.flow !== 'auto') p.flow = draft.state.flow === 'flow';
    const j = await ctx.run('video', p, 'Đã bắt đầu: dựng video từ ý tưởng');
    if (j) { draft.clear(); idea.value = ''; preview(); setTimeout(() => ctx.setProject(j.slug), 800); }
  };
  idea.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); create(); } });

  // ---- Lô 10 ý tưởng (need_ideas / pick_idea) — không cần mở ideas/<batch>/ideas.json ----
  const ideasBox = h('div.col', { style: { marginTop: '8px', gap: '8px' } });
  let selBatch = batches[0] ? batches[0].batch : '';
  const drawIdeas = () => {
    clear(ideasBox);
    const themeIn = h('input.input', { placeholder: 'Chủ đề lô 10 ý tưởng (vd: human body extreme limits)…', 'aria-label': 'Chủ đề lô ý tưởng', style: { width: '280px' } });
    const newBatchBtn = Btn('Tạo lô 10 ý tưởng', { size: 'sm', ico: 'bulb', onClick: async () => {
      const th = themeIn.value.trim();
      if (!th) { toast('Nhập chủ đề trước.', { kind: 'warn' }); themeIn.focus(); return; }
      await ctx.run('ideas', { theme: th }, `Đang tạo brief 10 ý tưởng · ${th}`);
      setTimeout(async () => { batches = ((await api.ideas().catch(() => ({}))).items) || []; selBatch = batches[0]?.batch || ''; drawIdeas(); }, 1200);
    } });
    const bSel = batches.length ? h('select.select', { 'aria-label': 'Chọn lô ý tưởng', style: { width: '240px' }, on: { change: (e) => { selBatch = e.target.value; drawIdeas(); } } },
      batches.map((b) => h('option', { value: b.batch, selected: b.batch === selBatch }, `${b.theme || b.batch} (${b.ready ? `${b.ideas.length} ý tưởng` : 'cần dán JSON'})`))) : null;
    const cur = batches.find((b) => b.batch === selBatch) || batches[0];
    ideasBox.append(h('div.row.wrap', { style: { gap: '8px' } }, themeIn, newBatchBtn, bSel ? h('span.dim', '· Lô có sẵn:') : null, bSel));
    if (!cur) return;
    const idText = h('textarea.textarea.mono', { rows: 4, placeholder: `Dán JSON 10 ý tưởng cho lô "${cur.batch}" (hoặc kéo-thả file ideas.json vào đây)…`, 'aria-label': 'Dán ideas.json' });
    const idStatus = h('div');
    idText.addEventListener('dragover', (e) => { e.preventDefault(); });
    idText.addEventListener('drop', (e) => {
      e.preventDefault();
      const f = e.dataTransfer?.files?.[0];
      if (!f) return;
      const rd = new FileReader();
      rd.onload = () => { idText.value = String(rd.result || ''); };
      rd.readAsText(f, 'utf-8');
    });
    const saveIdeas = async () => {
      const txt = idText.value.trim();
      if (!txt) { toast('Dán nội dung ideas.json vào ô trước.', { kind: 'warn' }); idText.focus(); return; }
      const rep = await api.ideasImport(cur.batch, txt);
      clear(idStatus);
      if (!rep.ok) {
        idStatus.append(Callout('err', `ideas.json có ${(rep.errors || []).length} lỗi`, (rep.errors || []).map((e) => `${e.path || ''}${e.line ? ' (dòng ' + e.line + ')' : ''}: ${e.msg}`).join(' · ')));
        return;
      }
      toast(`Đã lưu ${rep.summary?.ideas || 10} ý tưởng vào ideas/${cur.batch}/ideas.json`, { kind: 'ok' });
      batches = ((await api.ideas().catch(() => ({}))).items) || [];
      drawIdeas();
    };
    const copyBrief = async () => {
      if (!cur.brief_md) { toast('Lô này chưa có brief.md.', { kind: 'warn' }); return; }
      await copyText(cur.brief_md);
      toast(`Đã chép brief ý tưởng (${cur.brief_md.length.toLocaleString('vi-VN')} ký tự)`, { kind: 'ok' });
    };
    if (!cur.ready) {
      ideasBox.append(
        Callout('warn', `Việc tiếp theo · Lô "${cur.batch}" đang chờ ideas.json (exit 5: need_ideas)`,
          'Bấm "Copy brief ý tưởng" gửi cho AI, sau đó dán JSON trả lời vào ô dưới và bấm Lưu 10 ý tưởng.',
          [Btn('Copy brief ý tưởng', { size: 'sm', ico: 'copy', onClick: copyBrief }),
            Btn('Lưu 10 ý tưởng', { kind: 'primary', size: 'sm', ico: 'check', onClick: saveIdeas })]),
        idText, idStatus);
    } else {
      const list = h('ul.list', { style: { maxHeight: '180px', overflow: 'auto', border: '1px solid var(--line)', borderRadius: 'var(--r2)' } },
        (cur.ideas || []).map((it, idx) => h('li',
          h('span.mono.dim', `#${idx + 1}`),
          h('span.grow.ellipsis', { title: it.hook || it.title }, it.title || it.hook || `Ý tưởng ${idx + 1}`),
          it.truth ? St(it.truth, it.truth === 'True' ? 'ok' : 'warn') : null,
          Btn('Điền vào ô tạo', { size: 'sm', kind: 'ghost', onClick: () => { idea.value = it.title || it.hook || ''; draft.save({ idea: idea.value }); preview(); idea.focus(); } }),
          Btn('Dựng video', { size: 'sm', ico: 'play', onClick: () => ctx.run('ideas', { theme: cur.batch, pick: String(idx + 1) }, `Chọn ý tưởng #${idx + 1} · ${cur.batch}`) }))));
      ideasBox.append(
        h('div.row.wrap', { style: { gap: '8px' } },
          St(`${cur.ideas.length} ý tưởng sẵn sàng (exit 6: pick_idea)`, 'ok'),
          Btn('Copy brief ý tưởng', { size: 'sm', ico: 'copy', onClick: copyBrief }),
          Btn('Tự chọn điểm cao nhất (--auto-pick)', { size: 'sm', ico: 'sparkles', onClick: () => ctx.run('ideas', { theme: cur.batch, auto_pick: true }, `Tự chọn ý tưởng · ${cur.batch}`) })),
        list,
        h('details', h('summary.muted', { style: { cursor: 'pointer' } }, 'Dán đè ideas.json mới cho lô này'),
          h('div.col', { style: { marginTop: '6px', gap: '6px' } }, idText, Btn('Lưu đè ideas.json', { size: 'sm', onClick: saveIdeas }), idStatus)));
    }
  };
  drawIdeas();

  const hasPendingIdeas = batches.some((b) => !b.ready);
  const ideasDetails = h('details', { open: hasPendingIdeas, style: { marginTop: '6px' } },
    h('summary.muted', { style: { cursor: 'pointer' } }, `Lô 10 ý tưởng (${batches.length} lô${hasPendingIdeas ? ' · có lô chờ dán JSON' : ''})`),
    ideasBox);

  const adv = h('details', { open: false }, h('summary.muted', { style: { cursor: 'pointer' } }, 'Nâng cao'),
    h('div.row.wrap', { style: { marginTop: '8px', gap: '12px', alignItems: 'flex-end' } },
      h('div', { style: { width: '260px' } }, Field('Style', styleSel)), h('div', { style: { width: '200px' } }, Field('Dạng kịch bản', narrSel)),
      h('div', { style: { width: '160px' } }, Field('Giọng', voice)),
      Field('Ngày', Seg([{ value: 'auto', label: 'Tự động' }, { value: 'flow', label: 'Có Flow' }, { value: 'code', label: 'Toàn code' }], draft.state.flow,
        (v) => { draft.save({ flow: v }); preview(); }, { label: 'Ngày có Flow hay toàn code' })),
      h('label.check', dry, 'Chạy thử (dữ liệu giả, không tốn credit)')));
  const form = h('section.section', { 'aria-label': 'Video mới' },
    h('div.row', h('h2', 'Video mới'), h('span.dim', 'tiếng Anh · 9:16 · nền đen'), h('span.grow'),
      Btn('Tạo video', { kind: 'primary', ico: 'play', kbd: `${keys.mod}↵`, onClick: create })),
    h('div.col', { style: { marginTop: '8px' } }, idea, plan, adv, ideasDetails));

  // ---- bảng
  const qInput = h('input.input', { type: 'search', placeholder: 'Lọc theo tên, slug, style…', value: q, 'aria-label': 'Lọc dự án', style: { width: '260px' } });
  const filter = (r) => (showDemo || !r.demo) && (!q || `${r.title} ${r.slug} ${r.style} ${r.idea}`.toLowerCase().includes(q.toLowerCase()));
  const cost = (r) => (r.cost ? (r.cost.usd_known ? `$${r.cost.usd_known.toFixed(2)}` : `${r.cost.tts_chars || 0} ký tự`) : '—');
  const table = Table({
    rowKey: (r) => r.slug, rows: items, filter, sortKey: 'updated', sortDir: -1, selectable: true,
    onOpen: (r) => ctx.setProject(r.slug),
    columns: [
      { key: 'title', label: 'Video', render: (r) => h('div.col', { style: { gap: 0 } }, h('span.ellipsis', r.title || r.idea || r.slug), h('span.mono.dim.ellipsis', r.slug)), width: '34%' },
      { key: 'status', label: 'Stage', render: (r) => St(r.status_label || r.status, STAGE_TONE[r.status] || '') },
      { key: 'next', label: 'Việc tiếp theo', sortable: false, render: (r) => nextActionForRow(ctx, r), width: '140px' },
      { key: 'qa', label: 'QA', render: (r) => (r.qa ? St(({ green: 'Xanh', yellow: 'Vàng', red: 'Đỏ' })[r.qa] || r.qa, r.qa) : h('span.dim', '—')) },
      { key: 'style', label: 'Style', render: (r) => h('span.ellipsis', r.style || '—') },
      { key: 'duration', label: 'Dài', num: true, render: (r) => (r.duration ? dur(r.duration) : '—') },
      { key: 'version', label: 'Ver', render: (r) => h('span.mono', r.version || '—') },
      { key: 'cost', label: 'Chi phí', num: true, render: cost, sort: (r) => (r.cost && r.cost.usd_known) || 0 },
      { key: 'updated', label: 'Cập nhật', render: (r) => ago(r.updated) },
    ],
    empty: Empty('Chưa có dự án', 'Gõ ý tưởng ở trên rồi bấm Tạo video. Hoặc mở Lô 10 ý tưởng để chọn.', []),
  });
  qInput.addEventListener('input', () => { q = qInput.value; store.set('projects.q', q); table.refresh(); });
  const demo = h('input', { type: 'checkbox', checked: showDemo, on: { change: (e) => { showDemo = e.target.checked; store.set('projects.demo', showDemo); table.refresh(); } } });
  keys.register('page', 'N', () => { idea.focus(); return true; }, 'Gõ ý tưởng video mới');
  keys.register('page', '/', () => { qInput.focus(); return true; }, 'Lọc dự án');
  preview();
  return h('div.page.fill',
    h('div.pagehead', h('h1', 'Projects'), h('span.sub', `${items.filter((r) => !r.demo).length} dự án`), h('span.grow'), qInput,
      h('label.check', demo, 'Hiện bản thử/so sánh'), Btn('Làm mới', { kind: 'ghost', ico: 'refresh', onClick: async () => { items = (await api.projects(true)).items; table.refresh(items); } })),
    form, h('div', { style: { flex: 1, minHeight: 0 } }, table));
}
