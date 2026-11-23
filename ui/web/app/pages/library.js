// 8 · Library — Style (lọc nhóm Atlas / tier / brand_fit / engine, style frame do tool render, prompt gốc ↔ preset),
// Giọng, Dạng kịch bản, SFX, Font, Quyền (sổ rights/ledger.json). Hành động chính: Dùng style này cho video mới.
import { h, clear } from '../core/dom.js';
import { api, fileUrl, thumbUrl } from '../core/api.js';
import * as keys from '../core/keys.js';
import * as store from '../core/store.js';
import { bytes } from '../core/format.js';
import { Btn, St, Split, Empty, Table, Modal, Seg, toast, copyText } from '../ui/kit.js';

const TABS = [['styles', 'Style'], ['round10', 'Kho Vòng 10'], ['voices', 'Giọng'], ['narratives', 'Dạng kịch bản'], ['sfx', 'SFX'], ['fonts', 'Font'], ['rights', 'Quyền'], ['keys', 'API Keys']];
const CATS = [['', 'Mọi nhóm'], ['flat-physical', 'Phẳng → vật thật'], ['machines', 'Cỗ máy'], ['material', 'Chất liệu'], ['products', 'Sản phẩm'],
  ['diagrams', 'Sơ đồ chiều sâu'], ['spaces', 'Không gian'], ['filters', 'Bộ lọc 3D'], ['tool', 'Style của tool']];

export async function render(ctx) {
  const tab = ctx.sub || store.get('lib.tab', 'styles');
  store.set('lib.tab', tab);
  const body = h('div', { style: { flex: 1, minHeight: 0, display: 'flex' } });
  const tabs = h('div.seg-ctl', { role: 'tablist', 'aria-label': 'Thư viện' }, TABS.map(([id, label]) =>
    h('button', { type: 'button', role: 'tab', 'aria-selected': String(id === tab), on: { click: () => ctx.go('library', null, id) } }, label)));
  const view = await ({ styles: stylesTab, round10: round10Tab, voices: voicesTab, narratives: narrTab, sfx: sfxTab, fonts: fontsTab, rights: rightsTab, keys: keysTab }[tab] || stylesTab)(ctx);
  body.append(view);
  return h('div.page.fill', h('div.pagehead', h('h1', 'Library'), tabs, h('span.grow')), body);
}

async function stylesTab(ctx) {
  const items = (await api.styles()).items;
  const f = store.get('lib.styleFilter', { cat: '', tier: '', fit: '', eng: '', q: '' });
  let sel = store.get('lib.styleSel', items[0] && items[0].id);
  const grid = h('div.stylegrid', { role: 'listbox', 'aria-label': 'Style' });
  const insp = h('div');
  const match = (s) => (!f.cat || (f.cat === 'tool' ? !s.atlas : s.category === f.cat)) && (!f.tier || String(s.tier) === f.tier)
    && (!f.fit || (s.brand_fit || 'ok') === f.fit) && (!f.eng || s.engine === f.eng)
    && (!f.q || `${s.id} ${s.name} ${(s.tags || []).join(' ')}`.toLowerCase().includes(f.q.toLowerCase()));
  const sel_ = (k, opts) => h('select.select', { style: { width: 'auto' }, 'aria-label': k, on: { change: (e) => { f[k] = e.target.value; store.set('lib.styleFilter', f); draw(); } } },
    opts.map(([v, l]) => h('option', { value: v, selected: f[k] === v }, l)));
  const q = h('input.input', { type: 'search', placeholder: 'Tìm style, nhãn chủ đề…', value: f.q, 'aria-label': 'Tìm style', style: { width: '200px' }, on: { input: (e) => { f.q = e.target.value; store.set('lib.styleFilter', f); draw(); } } });
  const count = h('span.dim');
  const draw = () => {
    clear(grid);
    const list = items.filter(match);
    count.textContent = `${list.length}/${items.length}`;
    for (const s of list) {
      const card = h('div.stylecard', { role: 'option', tabindex: 0, 'aria-selected': String(s.id === sel), on: { click: () => pick(s.id), keydown: (e) => e.key === 'Enter' && pick(s.id) } },
        s.frame ? h('img', { src: thumbUrl('qa', s.frame, 200), alt: '', loading: 'lazy' }) : h('div', { style: { aspectRatio: '9/16', background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' } }, h('span.dim', s.engine)),
        h('div.meta', h('span.ellipsis', { title: s.name }, s.name), h('div.row.wrap', h(`span.chip.eng.${s.engine}`, s.engine),
          s.atlas ? h('span.chip', `#${String(s.atlas).padStart(2, '0')} t${s.tier}`) : null,
          s.brand_fit && s.brand_fit !== 'ok' ? St(s.brand_fit, s.brand_fit === 'off-brand' ? 'err' : 'warn') : null)));
      grid.append(card);
    }
    if (!list.length) grid.append(Empty('Không có style khớp bộ lọc', 'Bỏ bớt bộ lọc ở trên.'));
    drawInsp();
  };
  const pick = (id) => { sel = id; store.set('lib.styleSel', id); grid.querySelectorAll('.stylecard').forEach((c, i) => c.setAttribute('aria-selected', String(items.filter(match)[i]?.id === id))); drawInsp(); };
  const drawInsp = () => {
    clear(insp);
    const s = items.find((x) => x.id === sel);
    if (!s) { insp.append(Empty('Chọn một style', '')); return; }
    const showPreset = async () => {
      const txt = await (await fetch(fileUrl('styles', `${s.id}.json`))).text();
      Modal(`Preset đã chuyển · ${s.id}`, h('pre.prompt', { style: { maxHeight: '60vh' } }, txt), [Btn('Chép JSON', { onClick: async () => { await copyText(txt); toast('Đã chép', { kind: 'ok' }); } })]);
    };
    const showRaw = async () => {
      try {
        const r = await api.atlas(s.atlas);
        Modal(`Prompt gốc · #${String(s.atlas).padStart(2, '0')} ${r.name}`, h('div.col',
          h('p.dim', `${r.category} · ${r.tag} · ${(r.prompt_full || '').length.toLocaleString('vi-VN')} ký tự · lấy ${String(r.captured_at || '').slice(0, 10)} · chỉ lưu trên máy này (điều khoản: cá nhân, phi thương mại)`),
          h('dl.gridform', h('dt', 'Mô tả'), h('dd', r.description), h('dt', 'Shown here'), h('dd', r.shown_here), h('dt', 'Good for'), h('dd', r.good_for)),
          h('pre.prompt', { style: { maxHeight: '44vh' } }, (r.prompt_full || '').slice(0, 20000) + ((r.prompt_full || '').length > 20000 ? '\n…(còn nữa — Chép để lấy đủ)' : ''))),
        [Btn('Chép toàn văn', { onClick: async () => { await copyText(r.prompt_full || ''); toast('Đã chép prompt gốc', { kind: 'ok' }); } })]);
      } catch (e) { toast(e.message, { kind: 'err' }); }
    };
    insp.append(
      s.frame ? h('div', { style: { background: '#000', display: 'flex', justifyContent: 'center' } }, h('img', { src: thumbUrl('qa', s.frame, 360), alt: `Style frame ${s.name}`, style: { height: '320px' } })) : null,
      h('section.section', h('div.row', h('h2', s.name), h('span.grow'), s.auto === false ? St('chỉ chọn tay', 'warn') : St('vòng tự động', 'ok')),
        h('p.muted', { style: { marginTop: '6px' } }, s.description),
        h('dl.gridform', { style: { marginTop: '8px' } }, h('dt', 'Id'), h('dd.mono', s.id), h('dt', 'Engine'), h('dd', s.engine_label || s.engine),
          s.look3d ? [h('dt', 'Look 3D'), h('dd.mono', s.look3d)] : null,
          s.atlas ? [h('dt', 'Atlas'), h('dd', `#${String(s.atlas).padStart(2, '0')} · ${s.category_name} · tier ${s.tier} · ${s.brand_fit}`)] : null,
          s.duplicate_of ? [h('dt', 'Gần với'), h('dd.mono', s.duplicate_of)] : null,
          h('dt', 'Bảng màu'), h('dd', Object.entries(s.palette || {}).map(([k, v]) => h('span', { title: `${k} ${v}`, style: { marginRight: '4px' } }, h('span.swatch', { style: { background: v } })))),
          h('dt', 'Hợp chủ đề'), h('dd.muted', (s.tags || []).join(', ')), h('dt', 'Dùng gần nhất'), h('dd.mono', s.last_used || '—'))),
      h('section.section.row.wrap',
        Btn('Dùng cho video mới', { kind: 'primary', size: 'sm', onClick: () => { store.set('draft.new', { ...(store.get('draft.new') || {}), style: s.id, open: true }); ctx.go('projects'); } }),
        Btn('Preset đã chuyển', { size: 'sm', ico: 'layers', onClick: showPreset }),
        s.atlas ? Btn('Prompt gốc', { size: 'sm', ico: 'book', onClick: showRaw }) : null));
  };
  keys.register('page', '/', () => { q.focus(); return true; }, 'Tìm style');
  draw();
  const toolbar = h('div.row.wrap', { style: { padding: '8px 12px', borderBottom: '1px solid var(--line)' } }, q,
    sel_('cat', CATS), sel_('tier', [['', 'Mọi tier'], ['1', 'Tier 1'], ['2', 'Tier 2']]), sel_('fit', [['', 'Mọi brand_fit'], ['ok', 'ok'], ['adapted', 'adapted'], ['off-brand', 'off-brand']]),
    sel_('eng', [['', 'Mọi engine'], ['three', '3D three.js'], ['flow', 'Flow'], ['html', '2D html'], ['manim', 'Manim'], ['board', 'Board']]), count);
  return Split([h('div', { style: { display: 'flex', flexDirection: 'column' } }, toolbar, h('div', { style: { flex: 1, overflow: 'auto' } }, grid)), insp], { id: 'lib-styles', sizes: [null, 380] });
}

async function voicesTab() {
  const v = (await api.voices()).items;
  return h('div', { style: { flex: 1 } }, Table({ rowKey: (r) => r.id, rows: v, columns: [
    { key: 'short', label: 'Giọng', width: '120px' }, { key: 'gender', label: 'Giới', width: '80px' }, { key: 'accent', label: 'Giọng vùng', width: '120px' },
    { key: 'tags', label: 'Hợp với', render: (r) => (r.tags || []).join(', ') }, { key: 'auto', label: 'Vòng tự động', render: (r) => (r.auto ? St('có', 'ok') : St('chỉ chọn tay', '')) },
    { key: 'last_used', label: 'Dùng gần nhất', render: (r) => h('span.mono', r.last_used || '—') }] }));
}

async function narrTab() {
  const n = (await api.narratives('')).items;
  return h('div', { style: { flex: 1 } }, Table({ rowKey: (r) => r.id, rows: n, columns: [
    { key: 'id', label: 'Id', render: (r) => h('span.mono', r.id), width: '140px' }, { key: 'name', label: 'Dạng kịch bản', width: '260px' },
    { key: 'shape', label: 'Khung kể', render: (r) => r.shape }, { key: 'last_used', label: 'Dùng gần nhất', render: (r) => h('span.mono', r.last_used || '—'), width: '200px' }] }));
}

async function sfxTab() {
  const a = await api.assets();
  return h('div', { style: { flex: 1 } }, Table({ rowKey: (r) => r.file, rows: a.sfx, columns: [
    { key: 'name', label: 'SFX', render: (r) => h('span.mono', r.name), width: '200px' }, { key: 'builtin', label: 'Nguồn', render: (r) => (r.builtin ? St('tổng hợp bằng code', 'ok') : St('người dùng — cần license', 'warn')), width: '220px' },
    { key: 'play', label: 'Nghe', sortable: false, render: (r) => h('audio', { src: `/api/file?root=sfx&path=${encodeURIComponent(r.file)}`, controls: true, preload: 'none', style: { height: '24px' }, 'aria-label': `Nghe ${r.name}` }) }],
    empty: Empty('Chưa có SFX trong assets/sfx', 'SFX tổng hợp được sinh khi chạy pipeline lần đầu.') }));
}

async function fontsTab() {
  const a = await api.assets();
  return h('div', { style: { flex: 1 } }, Table({ rowKey: (r) => r.file, rows: a.fonts, columns: [
    { key: 'file', label: 'Font', render: (r) => h('span.mono', r.file) }, { key: 'license', label: 'License', render: (r) => r.license || '—', width: '240px' },
    { key: 'commercial', label: 'Thương mại', render: (r) => St(r.commercial === 'yes' ? 'được' : r.commercial === 'no' ? 'không' : 'chưa rõ', r.commercial === 'yes' ? 'ok' : r.commercial === 'no' ? 'err' : 'warn'), width: '120px' },
    { key: 'size', label: 'Cỡ', num: true, render: (r) => bytes(r.size), width: '90px' }] }));
}

async function rightsTab() {
  const a = await api.assets();
  const led = a.ledger || {};
  const dec = Object.entries(led.decisions || {}).filter(([k]) => !k.startsWith('_'));
  return h('div', { style: { flex: 1, overflow: 'auto' } },
    h('section.section', h('h2', 'Chờ chủ kênh quyết định'), h('p.dim', 'Sửa rights/ledger.json → decisions. unknown/pending làm cổng QA báo vàng cho video dùng thứ đó.'),
      h('dl.gridform', { style: { marginTop: '8px' } }, dec.flatMap(([k, v]) => [h('dt.mono', k), h('dd', St(String(v), ['unknown', 'pending', '?'].includes(String(v)) ? 'warn' : 'ok'))]))),
    h('div', { style: { height: '60vh' } }, Table({ rowKey: (r) => r.id, rows: led.assets || [], columns: [
      { key: 'id', label: 'Asset', render: (r) => h('span.mono', r.id), width: '200px' }, { key: 'license', label: 'License', width: '220px' },
      { key: 'commercial', label: 'Thương mại', render: (r) => St(r.commercial, r.commercial === 'yes' ? 'ok' : r.commercial === 'no' ? 'err' : 'warn'), width: '200px' },
      { key: 'source', label: 'Nguồn' }, { key: 'note', label: 'Ghi chú', render: (r) => h('span.dim', r.note || '') }] })));
}

async function round10Tab(ctx) {
  const sc = await api.schema();
  const c3 = sc.creatures3d || {}, r2 = sc.rig2d || {}, a3 = sc.assets3d || {};
  const verbs = Object.entries(sc.verbs || {}).map(([name, meta]) => ({ name, group: meta.g, dur: meta.dur ?? '∞', doc: (sc.verb_doc || {})[name] || '' }));
  const mets = sc.metaphors || [];
  let q = '';
  const listHost = h('div', { style: { flex: 1, minHeight: 0, overflow: 'auto', padding: '12px' } });
  const drawMets = () => {
    clear(listHost);
    const ql = q.trim().toLowerCase();
    const filtered = mets.filter((m) => !ql || `${m.id} ${(m.keywords || []).join(' ')} ${m.mechanism || ''}`.toLowerCase().includes(ql));
    listHost.append(
      h('section.section',
        h('h2', `7 Style mới Vòng 10 (${(sc.round10_styles || []).length})`),
        h('div.row.wrap', { style: { gap: '8px', marginTop: '8px' } }, (sc.round10_styles || []).map((s) =>
          Btn(`${s.name} (${s.id})`, { size: 'sm', onClick: () => { store.set('draft.new', { ...(store.get('draft.new') || {}), style: s.id, open: true }); ctx.go('projects'); } })))),
      h('section.section',
        h('h2', `Nhân vật 3D (${(c3.species || []).length} loài) & Nhân vật 2D (${(r2.species || []).length} loài)`),
        h('p.muted', { style: { marginTop: '4px' } }, `3D creatures (stage): ${(c3.species || []).join(', ')}`),
        h('p.dim', { style: { marginTop: '4px' } }, `Bối cảnh 3D (set): ${(c3.sets || []).join(', ')} · Dáng: ${(c3.gaits || []).join(', ')}`),
        h('p.muted', { style: { marginTop: '6px' } }, `2D rig (rig:<loài>): ${(r2.species || []).join(', ')}`)),
      h('section.section',
        h('h2', `Kho tài sản CC0 / MIT (${a3.summary?.models || 0} mô hình 3D · ${a3.summary?.svg || 0} icon SVG)`),
        h('p.dim', { style: { marginTop: '4px' } }, `Gọi trong storyboard: "type": "model:<tên>" (3D) hoặc "icon": "svg:<tên>" (2D/3D). Có ${a3.summary?.animated || 0} mô hình 3D có animation.`),
        h('div.row.wrap', { style: { gap: '6px', marginTop: '6px' } }, (a3.models || []).slice(0, 30).map((m) =>
          h('span.chip', { title: `${m.pack} · ${m.anims?.length ? 'anim: ' + m.anims.slice(0, 5).join(', ') : 'tĩnh'}` }, `model:${m.name}`)))),
      h('section.section',
        h('h2', `Động từ chuyển động (${verbs.length} verbs · ${(sc.staggers || []).length} stagger)`),
        h('div', { style: { height: '240px', marginTop: '8px', border: '1px solid var(--line)' } },
          Table({ rowKey: (r) => r.name, rows: verbs, columns: [
            { key: 'name', label: 'Verb', render: (r) => h('span.mono', r.name), width: '160px' },
            { key: 'group', label: 'Nhóm', width: '90px' },
            { key: 'dur', label: 'Mặc định (s)', width: '100px' },
            { key: 'doc', label: 'Mô tả' }] }))),
      h('section.section',
        h('h2', `Kho cơ chế hình ảnh (${filtered.length}/${mets.length})`),
        h('div', { style: { height: '320px', marginTop: '8px', border: '1px solid var(--line)' } },
          Table({ rowKey: (r) => r.id, rows: filtered, columns: [
            { key: 'id', label: 'Id', render: (r) => h('span.mono', r.id), width: '190px' },
            { key: 'mechanism', label: 'Cơ chế' },
            { key: 'verbs', label: 'Verbs', render: (r) => (r.verbs || []).join(', '), width: '180px' }] }))));
  };
  const search = h('input.input', { type: 'search', placeholder: 'Lọc cơ chế theo từ khoá (heart, dog, battery…)', style: { width: '320px' },
    on: { input: (e) => { q = e.target.value; drawMets(); } } });
  drawMets();
  return h('div', { style: { flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 } },
    h('div.row', { style: { padding: '8px 12px', borderBottom: '1px solid var(--line)' } }, search,
      h('span.dim', `15 beat · ${Object.values(sc.layouts || {}).reduce((a, b) => a + b.length, 0)} biến thể bố cục · ${(sc.html_looks || []).length} look 2D`)),
    listHost);
}

async function keysTab() {
  const host = h('div', { style: { flex: 1, overflow: 'auto', padding: '12px', maxWidth: '680px' } });
  const KEYS = [
    ['ELEVENLABS_API_KEY', 'ElevenLabs API Key', 'Bắt buộc cho giọng đọc thật (TTS + timestamp từ).'],
    ['ANTHROPIC_API_KEY', 'Anthropic API Key', 'Cho nút "AI viết giúp (--ai claude)" ngay trong UI.'],
    ['GEMINI_API_KEY', 'Gemini API Key', 'Cho nút "AI viết giúp (--ai gemini)" ngay trong UI.'],
  ];
  const renderForm = async () => {
    const sys = await api.system();
    const by = Object.fromEntries((sys.checks || []).map((c) => [c.key, c]));
    clear(host);
    const inputs = {};
    const rows = KEYS.map(([k, label, desc]) => {
      const ok = !!(by[k] && by[k].ok);
      const inp = h('input.input', { type: 'password', autocomplete: 'off', placeholder: ok ? '•••••••• (để trống = giữ nguyên key hiện tại)' : 'Dán API key vào đây…' });
      inputs[k] = inp;
      return h('div.col', { style: { gap: '4px', padding: '10px 0', borderBottom: '1px solid var(--line)' } },
        h('div.row', h('strong', label), h('span.mono.dim', k), h('span.grow'), St(ok ? 'Đã đặt' : 'Chưa đặt', ok ? 'ok' : 'warn'),
          ok ? Btn('Xoá', { size: 'sm', kind: 'ghost', onClick: async () => {
            try { await api.saveEnv({ clear: [k] }); toast(`Đã xoá ${k}`, { kind: 'ok' }); renderForm(); } catch (e) { toast(e.message, { kind: 'err' }); }
          } }) : null),
        h('span.dim', desc), inp);
    });
    host.append(
      h('section.section',
        h('h2', 'Cài đặt API Key (.env cục bộ)'),
        h('p.muted', { style: { marginTop: '4px' } }, 'Key chỉ được lưu vào file .env trên máy này (gitignored) và không bao giờ hiển thị lại giá trị.'),
        ...rows,
        h('div.row', { style: { marginTop: '12px' } },
          Btn('Lưu API Key', { kind: 'primary', onClick: async () => {
            const payload = {};
            for (const [k, inp] of Object.entries(inputs)) if (inp.value.trim()) payload[k] = inp.value.trim();
            if (!Object.keys(payload).length) { toast('Chưa nhập key mới nào.', { kind: 'warn' }); return; }
            try {
              const r = await api.saveEnv({ keys: payload });
              toast(`Đã lưu ${r.updated.join(', ')} vào .env`, { kind: 'ok' });
              renderForm();
            } catch (e) { toast(e.message, { kind: 'err' }); }
          } }))));
  };
  await renderForm();
  return host;
}
