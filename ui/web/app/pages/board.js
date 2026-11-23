// 3 · Board — lưới shot + kéo-thả đổi thứ tự + Bảng thuộc tính Shot (Properties Panel) + Xem trước 1 frame (sb/preview).
import { h, clear } from '../core/dom.js';
import { api, thumbUrl } from '../core/api.js';
import * as keys from '../core/keys.js';
import * as undo from '../core/undo.js';
import * as store from '../core/store.js';
import { Btn, St, Field, Split, Empty, Callout, confirm, toast, copyText } from '../ui/kit.js';

const ENG = { flow: 'Flow', three: '3D', html: '2D', manim: 'Manim', board: 'Board' };
const MODES = [['code', 'code (3D / 2D / Manim / Board)'], ['frames_start', 'Flow · ảnh đầu'],
  ['frames_start_end', 'Flow · ảnh đầu + cuối'], ['ingredients', 'Flow · Ingredients'], ['auto', 'auto']];

export function shotState(s) {
  if (s.engine === 'flow') return s.clip ? ['clip ✓', 'ok'] : ['thiếu clip', 'warn'];
  if (s.still) return ['đã dựng', 'ok'];
  if (s.preview) return ['có preview', 'proc'];
  return ['chưa dựng', ''];
}

function frameImg(slug, rel, alt, v) {
  return rel ? h('img', { src: thumbUrl('projects', `${slug}/${rel}`, 200, v), alt, loading: 'lazy' }) : h('span', '—');
}

/** Các trường tham số nhanh (Essential Graphics) cho từng beat để sửa không cần đụng JSON. */
function quickParamSpecs(scene) {
  const base = [{ k: 'kicker', label: 'Kicker (nhãn trên)', type: 'text' }, { k: 'title', label: 'Title (tiêu đề cảnh)', type: 'text' }];
  if (scene === 'counter') {
    return [...base, { k: 'to', label: 'Giá trị đích (to)', type: 'number' }, { k: 'from', label: 'Giá trị đầu (from)', type: 'number' },
      { k: 'unit', label: 'Đơn vị (unit)', type: 'text' }, { k: 'label', label: 'Nhãn (label)', type: 'text' }, { k: 'icon', label: 'Icon / rig:<loài>', type: 'text' }];
  }
  if (scene === 'fact') {
    return [{ k: 'kicker', label: 'Kicker', type: 'text' }, { k: 'text', label: 'Câu chốt (text)', type: 'text' },
      { k: 'em', label: 'Cụm nhấn (em)', type: 'text' }, { k: 'icon', label: 'Icon / rig:<loài>', type: 'text' }];
  }
  if (scene === 'meter') {
    return [...base, { k: 'kind', label: 'Loại đồng hồ (ecg|battery|tank|thermo|dial)', type: 'text' },
      { k: 'value', label: 'Giá trị (value / bpm)', type: 'number' }, { k: 'unit', label: 'Đơn vị (unit)', type: 'text' }, { k: 'label', label: 'Nhãn', type: 'text' }];
  }
  if (scene === 'title') {
    return [...base, { k: 'sub', label: 'Phụ đề (sub)', type: 'text' }, { k: 'icon', label: 'Icon / rig:<loài>', type: 'text' }];
  }
  if (scene === 'callout') {
    return [...base, { k: 'icon', label: 'Icon / rig:<loài>', type: 'text' }];
  }
  if (scene === 'stage') {
    return [{ k: 'set', label: 'Bối cảnh 3D (black|lab|track|meadow|tabletop|street)', type: 'text' }, { k: 'title', label: 'Chữ trong cảnh (title)', type: 'text' }];
  }
  return base;
}

export async function render(ctx) {
  const w = ctx.ws;
  const schema = await api.schema().catch(() => ({ beats: {}, layouts: {}, three_scenes: ['stage'] }));
  const base = (w.shots_detail || []).map((s) => s.id);
  let order = store.get(`board.order.${ctx.slug}`) || base;
  if (order.length !== base.length || order.some((x) => !base.includes(x))) order = base;
  const by = Object.fromEntries((w.shots_detail || []).map((s) => [s.id, s]));
  let sel = store.get(`board.sel.${ctx.slug}`) || order[0];
  const grid = h('div.shotgrid', { role: 'listbox', 'aria-label': 'Shot', 'aria-multiselectable': 'false' });
  const insp = h('div', { style: { overflow: 'auto' } });
  const saveBtn = Btn('Lưu thứ tự', { kind: 'primary', ico: 'check', onClick: () => saveOrder() });
  const dirty = () => order.join() !== base.join();
  const qaRows = (w.qa && w.qa.rows) || [];

  const draw = () => {
    clear(grid);
    order.forEach((id, i) => {
      const s = by[id];
      const [stTxt, stTone] = shotState(s);
      const warns = qaRows.filter((r) => r.level !== 'green' && r.label.includes(id));
      const mainStill = s.preview || s.still;
      const card = h('div.shot', { role: 'option', tabindex: 0, draggable: true, 'aria-selected': String(id === sel), dataset: { id }, 'aria-label': `${id} ${s.beat || ''}` },
        h('div.frames', h('div', s.engine === 'flow' ? frameImg(ctx.slug, s.frames && s.frames.start, `${id} khung đầu`) : frameImg(ctx.slug, mainStill, `${id} frame`, s.preview_mtime)),
          h('div', frameImg(ctx.slug, s.frames && s.frames.end, `${id} khung cuối`))),
        h('div.meta', h('div.top', h('span.mono', id), h('span.dim', `#${i + 1}`), h('span.grow'), h(`span.chip.eng.${s.engine}`, ENG[s.engine] || s.engine)),
          h('div.vo', s.vo || h('span.dim', s.subject || '—')),
          h('div.row.wrap', St(stTxt, stTone), s.scene ? h('span.chip.mono', s.scene) : (s.beat ? h('span.chip', s.beat) : null),
            (s.refs || []).length ? h('span.chip', `ref ${s.refs.join(',')}`) : null,
            s.dur ? h('span.mono.dim', `${(+s.dur).toFixed(1)}s`) : null, warns.length ? St(`${warns.length} cảnh báo`, 'warn') : null)));
      card.addEventListener('click', () => select(id));
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') select(id);
        if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) { move(id, e.key === 'ArrowRight' ? 1 : -1); e.preventDefault(); }
      });
      card.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/plain', id); card.classList.add('dragging'); });
      card.addEventListener('dragend', () => card.classList.remove('dragging'));
      card.addEventListener('dragover', (e) => { e.preventDefault(); card.classList.add('drop-before'); });
      card.addEventListener('dragleave', () => card.classList.remove('drop-before'));
      card.addEventListener('drop', (e) => {
        e.preventDefault(); card.classList.remove('drop-before');
        const from = e.dataTransfer.getData('text/plain');
        if (from && from !== id) reorder(order.filter((x) => x !== from).flatMap((x) => (x === id ? [from, x] : [x])), `Kéo ${from} lên trước ${id}`);
      });
      grid.append(card);
    });
    saveBtn.disabled = !dirty();
    drawInsp();
  };
  const reorder = (next, label) => {
    const prev = order;
    order = next; store.set(`board.order.${ctx.slug}`, order); draw();
    undo.push({ label, undo: () => { order = prev; store.set(`board.order.${ctx.slug}`, order); draw(); }, redo: () => { order = next; store.set(`board.order.${ctx.slug}`, order); draw(); } });
    toast(`${label} — chưa lưu vào storyboard`, { action: () => undo.undo(), actionLabel: 'Hoàn tác' });
  };
  const move = (id, d) => {
    const i = order.indexOf(id), j = i + d;
    if (j < 0 || j >= order.length) return;
    const next = order.slice(); [next[i], next[j]] = [next[j], next[i]];
    reorder(next, `Dời ${id} ${d > 0 ? 'sau' : 'trước'}`);
    setTimeout(() => grid.querySelector(`[data-id="${id}"]`)?.focus(), 0);
  };
  const select = (id) => {
    sel = id; store.set(`board.sel.${ctx.slug}`, id);
    grid.querySelectorAll('.shot').forEach((c) => c.setAttribute('aria-selected', String(c.dataset.id === id)));
    drawInsp();
  };
  const saveOrder = async () => {
    if (!await confirm('Lưu thứ tự shot mới?', `Ghi thứ tự ${order.join(' → ')} vào storyboard.json (nguồn sự thật). Video sẽ dựng theo thứ tự này ở lần chạy sau.`, { ok: 'Lưu' })) return;
    const j = await ctx.run('reorder', { target: ctx.slug, order: order.join(',') }, 'Đang ghi thứ tự shot');
    if (j) { store.del(`board.order.${ctx.slug}`); undo.reset(); }
  };
  const rerender = async (id) => {
    if (!await confirm(`Render lại ${id}?`, 'Chỉ dựng lại frame/clip của shot này (shot khác giữ nguyên nhờ RESUME), rồi ghép video, QA, gói và version mới.', { ok: 'Render lại' })) return;
    ctx.run('rerender_shot', { target: ctx.slug, shot: id }, `Đang render lại ${id}`);
  };

  const drawInsp = () => {
    clear(insp);
    const s = by[sel];
    if (!s) { insp.append(Empty('Chọn một shot', 'Bấm vào thẻ shot để xem và sửa thuộc tính.')); return; }
    const [stTxt, stTone] = shotState(s);
    const code = s.code || {};
    let curParams = JSON.parse(JSON.stringify(code.params || {}));
    const canPreview = ['three', 'html', 'manim'].includes(s.engine) || (code && code.scene);

    // ---- Khung xem trước 1 frame (sb/preview) ----
    const prevImgBox = h('div', { style: { background: '#000', borderRadius: 'var(--r2)', border: '1px solid var(--line)', minHeight: '160px', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' } });
    const prevMeta = h('span.mono.dim', '');
    let uVal = 0.5;
    const drawPrevImg = (rel, ver, note = '') => {
      clear(prevImgBox);
      if (rel) {
        prevImgBox.append(h('img', { src: thumbUrl('projects', `${ctx.slug}/${rel}`, 360, ver || Date.now()), alt: `Xem trước ${s.id}`, style: { maxHeight: '240px', width: 'auto', display: 'block' } }));
      } else {
        prevImgBox.append(h('span.dim', canPreview ? 'Bấm "Xem trước 1 frame" để dựng thử trong ~1–2s' : 'Shot Flow / Board không dùng preview 1 frame'));
      }
      prevMeta.textContent = note;
    };
    drawPrevImg(s.preview || s.still, s.preview_mtime, s.preview ? `work/preview/${s.id}.jpg` : (s.still ? 'frame đã render' : ''));

    const doPreview = async () => {
      if (!canPreview) { toast('Chỉ shot code (three/html/manim) mới dựng preview 1 frame.', { kind: 'warn' }); return; }
      prevMeta.textContent = `Đang dựng frame u=${uVal}…`;
      const res = await api.sbPreview(ctx.slug, s.id, uVal);
      if (!res.ok) {
        const msg = (res.errors && res.errors[0] && res.errors[0].msg) || 'Không dựng được preview.';
        prevMeta.textContent = msg;
        toast(msg, { kind: 'err' });
        return;
      }
      s.preview = res.file;
      s.preview_mtime = Date.now();
      drawPrevImg(res.file, s.preview_mtime, `frame ${res.frame}/${res.frames - 1} · ${res.engine}:${res.scene} · ${res.sec}s`);
      toast(`Đã dựng preview ${s.id} (${res.sec}s)`, { kind: 'ok', ms: 2200 });
    };

    const uInput = h('input.input.mono', { type: 'number', min: '0', max: '1', step: '0.1', value: '0.5', 'aria-label': 'Vị trí thời gian u (0..1)', style: { width: '68px' },
      on: { change: (e) => { uVal = Math.max(0, Math.min(1, parseFloat(e.target.value) || 0.5)); e.target.value = String(uVal); } } });

    // ---- Bảng thuộc tính Shot (Properties Panel) ----
    const voIn = h('textarea.textarea', { rows: 2, value: s.vo || '', 'aria-label': 'Lời đọc (vo)' });
    voIn.value = s.vo || '';
    const secIn = h('input.input.mono', { type: 'number', min: '0.5', max: '20', step: '0.1', value: s.target_sec ?? s.dur ?? '', 'aria-label': 'Thời lượng (target_sec)' });
    const holdIn = h('input', { type: 'checkbox', checked: !!s.hold });
    const modeSel = h('select.select', { 'aria-label': 'Mode' },
      MODES.map(([v, l]) => h('option', { value: v, selected: (s.mode || 'code') === v }, l)));

    const beatNames = Object.keys(schema.beats || {});
    const threeNames = schema.three_scenes || ['stage'];
    const allScenes = [...new Set(['', ...beatNames, ...threeNames, code.scene || ''])];
    const sceneSel = h('select.select', { 'aria-label': 'Beat / Cảnh code (code.scene)' },
      allScenes.map((sc) => h('option', { value: sc, selected: (code.scene || '') === sc },
        sc ? `${sc}${beatNames.includes(sc) ? ' (2D html)' : threeNames.includes(sc) ? ' (3D three)' : ''}` : '— (không dùng code.scene)')));

    const layoutBox = h('div');
    const quickBox = h('div.col', { style: { gap: '6px' } });
    const paramsText = h('textarea.textarea.mono', { rows: 6, 'aria-label': 'JSON code.params', value: JSON.stringify(curParams, null, 2) });
    paramsText.value = JSON.stringify(curParams, null, 2);
    const errBox = h('div');

    const syncJsonText = () => { paramsText.value = JSON.stringify(curParams, null, 2); };

    const rebuildSceneFields = () => {
      const sc = sceneSel.value;
      clear(layoutBox);
      clear(quickBox);
      const bInfo = (schema.beats || {})[sc];
      const lays = (schema.layouts || {})[sc] || (bInfo && bInfo.layouts) || [];
      if (lays.length) {
        const lHelp = (bInfo && bInfo.layout_help) || {};
        const lSel = h('select.select', { 'aria-label': 'Bố cục (code.params.layout)', on: { change: (e) => {
          if (e.target.value) curParams.layout = e.target.value; else delete curParams.layout;
          syncJsonText();
        } } },
        h('option', { value: '', selected: !curParams.layout }, 'Tự chọn (xoay vòng chống lặp)'),
        lays.map((l) => h('option', { value: l, selected: curParams.layout === l }, lHelp[l] ? `${l} — ${lHelp[l]}` : l)));
        layoutBox.append(Field('Bố cục (layout)', lSel, bInfo && bInfo.doc ? bInfo.doc.slice(0, 120) : null));
      }
      for (const sp of quickParamSpecs(sc)) {
        const inp = h(`input.input${sp.type === 'number' ? '.mono' : ''}`, {
          type: sp.type,
          value: curParams[sp.k] !== undefined && curParams[sp.k] !== null ? String(curParams[sp.k]) : '',
          placeholder: sp.k,
          'aria-label': sp.label,
          on: { input: (e) => {
            const raw = e.target.value;
            if (raw === '') delete curParams[sp.k];
            else if (sp.type === 'number') curParams[sp.k] = Number.isNaN(Number(raw)) ? raw : Number(raw);
            else curParams[sp.k] = raw;
            syncJsonText();
          } },
        });
        quickBox.append(Field(sp.label, inp));
      }
    };
    sceneSel.addEventListener('change', () => rebuildSceneFields());
    paramsText.addEventListener('input', () => {
      try {
        const parsed = JSON.parse(paramsText.value || '{}');
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          curParams = parsed;
          paramsText.style.borderColor = '';
        }
      } catch {
        paramsText.style.borderColor = 'var(--err)';
      }
    });
    rebuildSceneFields();

    const saveShot = async (andPreview = false) => {
      clear(errBox);
      let parsedParams = {};
      try {
        parsedParams = JSON.parse(paramsText.value || '{}');
        if (!parsedParams || typeof parsedParams !== 'object' || Array.isArray(parsedParams)) throw new Error('code.params phải là object { … }');
      } catch (e) {
        errBox.append(Callout('err', 'JSON code.params không hợp lệ', e.message));
        return;
      }
      const set = {
        vo: voIn.value,
        hold: holdIn.checked,
        mode: modeSel.value,
      };
      const secNum = parseFloat(secIn.value);
      if (!Number.isNaN(secNum) && secNum > 0) set.target_sec = secNum;
      if (sceneSel.value) {
        set['code.scene'] = sceneSel.value;
        set['code.params'] = parsedParams;
      }
      const rep = await api.sbPatch(ctx.slug, { shot: s.id, set });
      if (!rep.ok && !rep.saved) {
        errBox.append(Callout('err', `Không lưu được (${(rep.errors || []).length} lỗi)`,
          (rep.errors || []).map((e) => `${e.path || ''}: ${e.msg}`).join(' · ')));
        return;
      }
      toast(`Đã lưu thuộc tính ${s.id}`, { kind: 'ok', ms: 2200 });
      if (andPreview && canPreview) await doPreview();
      await ctx.reload();
    };

    const doUndoSb = async () => {
      const h0 = (w.sb_history || [])[0];
      if (!h0) { toast('Chưa có bản lưu trước để hoàn tác.', { kind: 'warn' }); return; }
      const rep = await api.sbRestore(ctx.slug, h0.id);
      if (rep.ok || rep.saved) {
        toast(`Đã hoàn tác về bản ${h0.id}`, { kind: 'ok' });
        await ctx.reload();
      }
    };

    insp.append(
      h('section.section',
        h('div.row', h('h2.mono', s.id), St(stTxt, stTone), h('span.grow'), h(`span.chip.eng.${s.engine}`, ENG[s.engine] || s.engine)),
        canPreview ? h('div.col', { style: { marginTop: '8px', gap: '6px' } },
          prevImgBox,
          h('div.row.wrap', { style: { gap: '6px', alignItems: 'center' } },
            h('span.dim', 'u='), uInput,
            Btn('Xem trước 1 frame', { size: 'sm', ico: 'eye', kbd: 'P', onClick: doPreview }),
            prevMeta)) : null),
      h('section.section',
        h('div.row', h('h3', 'Bảng thuộc tính Shot'), h('span.grow'),
          (w.sb_history || []).length ? Btn('Hoàn tác', { size: 'sm', kind: 'ghost', ico: 'undo', title: `Khôi phục ${(w.sb_history[0] || {}).id}`, onClick: doUndoSb }) : null),
        h('div.col', { style: { marginTop: '8px', gap: '8px' } },
          Field('Lời đọc (VO tiếng Anh)', voIn),
          h('div.row', { style: { gap: '8px', alignItems: 'flex-end' } },
            h('div', { style: { width: '110px' } }, Field('Thời lượng (s)', secIn)),
            h('div.grow', Field('Mode', modeSel)),
            h('label.check', { style: { paddingBottom: '4px' } }, holdIn, 'Hold')),
          Field('Beat 2D / Cảnh 3D (code.scene)', sceneSel),
          layoutBox,
          quickBox,
          h('details', h('summary.muted', { style: { cursor: 'pointer' } }, 'JSON code.params đầy đủ (nâng cao)'),
            h('div', { style: { marginTop: '6px' } }, paramsText)),
          errBox,
          h('div.row.wrap', { style: { gap: '6px', marginTop: '4px' } },
            Btn('Lưu thay đổi', { kind: 'primary', size: 'sm', ico: 'check', onClick: () => saveShot(false) }),
            canPreview ? Btn('Lưu & Xem trước', { size: 'sm', ico: 'eye', onClick: () => saveShot(true) }) : null,
            Btn('Render lại shot', { size: 'sm', ico: 'refresh', kbd: 'R', onClick: () => rerender(s.id) })))),
      Object.values(s.prompts || {}).some((v) => v && String(v).trim()) ? h('section.section', h('div.label', 'Prompt Flow'),
        Object.entries(s.prompts).filter(([, v]) => v && String(v).trim()).map(([k, v]) => h('div.col', { style: { marginTop: '6px' } }, h('div.row', h('span.mono.dim', k), h('span.grow'),
          Btn('Chép', { size: 'sm', ico: 'copy', onClick: async () => { await copyText(v); toast(`Đã chép prompt ${k} của ${s.id}`, { kind: 'ok' }); } })), h('div.prompt', { tabindex: 0, role: 'region', 'aria-label': `Prompt ${k}` }, v)))) : null,
      h('section.section.row.wrap',
        s.engine === 'flow' ? Btn('Mở trong Generate', { size: 'sm', ico: 'sparkles', onClick: () => ctx.go('generate') }) : null,
        Btn('Xem ở Edit', { size: 'sm', ico: 'timeline', onClick: () => { store.set(`edit.sel.${ctx.slug}`, s.id); ctx.go('edit'); } })));
  };
  keys.register('page', 'R', () => sel && rerender(sel), 'Render lại shot đang chọn');
  keys.register('page', 'P', async () => {
    const s = by[sel];
    if (!s) return;
    const res = await api.sbPreview(ctx.slug, s.id, 0.5);
    if (res.ok) { s.preview = res.file; s.preview_mtime = Date.now(); draw(); toast(`Đã dựng preview ${s.id} (${res.sec}s)`, { kind: 'ok' }); }
  }, 'Xem trước 1 frame shot đang chọn');
  keys.register('page', 'Alt+ArrowRight', () => sel && move(sel, 1), 'Dời shot đang chọn ra sau');
  keys.register('page', 'Alt+ArrowLeft', () => sel && move(sel, -1), 'Dời shot đang chọn lên trước');
  keys.register('page', 'ArrowRight', () => { const i = order.indexOf(sel); if (i < order.length - 1) { select(order[i + 1]); grid.querySelector(`[data-id="${order[i + 1]}"]`)?.focus(); } }, 'Shot kế');
  keys.register('page', 'ArrowLeft', () => { const i = order.indexOf(sel); if (i > 0) { select(order[i - 1]); grid.querySelector(`[data-id="${order[i - 1]}"]`)?.focus(); } }, 'Shot trước');
  draw();
  if (!order.length) grid.append(Empty('Chưa có shot', 'Storyboard chưa có shot nào — dán hoặc viết kịch bản ở trang Script.', [Btn('Mở Script', { kind: 'primary', onClick: () => ctx.go('script') })]));
  const counts = (w.shots_detail || []).reduce((a, s) => { const k = shotState(s)[1] || 'none'; a[k] = (a[k] || 0) + 1; return a; }, {});
  return h('div.page.fill',
    h('div.pagehead', h('h1', 'Board'), h('span.sub', `${order.length} shot · ${counts.ok || 0} sẵn sàng · ${counts.warn || 0} thiếu clip`), h('span.grow'),
      h('span.dim', 'Chọn shot để sửa thuộc tính / xem trước 1 frame (P) · Kéo thẻ để đổi thứ tự'), saveBtn),
    Split([h('div', grid), insp], { id: 'board', sizes: [null, 400] }));
}
