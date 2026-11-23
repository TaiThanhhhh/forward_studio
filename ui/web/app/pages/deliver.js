// 7 · Deliver — preset nền tảng, cổng QA (đỏ chặn xuất), sổ quyền, gói publish (tiêu đề, mô tả, hashtag, .srt, bìa A/B).
// Hành động chính: Xuất gói (tắt khi cổng QA đỏ — duyệt tay nằm trong Nâng cao).
import { h, clear } from '../core/dom.js';
import { api, projectFile, thumbUrl } from '../core/api.js';
import * as store from '../core/store.js';
import { bytes } from '../core/format.js';
import { Btn, St, Split, Empty, Callout, confirm, toast, copyText, Panel } from '../ui/kit.js';

const LV = { green: ['Xanh', 'ok'], yellow: ['Vàng', 'warn'], red: ['Đỏ', 'err'] };

function fixFor(label) {
  if (/^loudness|^true peak|^LRA/.test(label)) return ['Edit', 'edit'];
  if (/^nguồn Flow/.test(label)) return ['Generate', 'generate'];
  if (/^chữ|^OCR/.test(label)) return ['Edit', 'edit'];
  if (/^quyền/.test(label)) return ['Library · Quyền', 'library'];
  if (/^safe zone/.test(label)) return ['Edit', 'edit'];
  if (/freeze|black frame|chuyển động/.test(label)) return ['Board', 'board'];
  return null;
}

export function parsePublish(md) {
  const sec = (name) => { const m = (md || '').match(new RegExp(`## ${name}[^\\n]*\\n([\\s\\S]*?)(?=\\n## |$)`)); return m ? m[1].trim() : ''; };
  const titles = sec('Titles').split('\n').map((l) => l.replace(/^\d+\.\s*/, '').replace(/\s*_\(\d+ chars\)_\s*$/, '').trim()).filter(Boolean);
  return { titles, description: sec('Description'), hashtags: sec('Hashtags'), ai: sec('Nhãn AI'), checklist: sec('Checklist trước khi đăng') };
}

export async function render(ctx) {
  const w = ctx.ws;
  const cfg = await api.delivery().catch(() => ({ presets: {}, default: [] }));
  const chosen = new Set(store.get(`deliver.presets.${ctx.slug}`) || cfg.default || []);
  const qa = w.qa || {};
  const rows = qa.rows || [];
  const red = rows.filter((r) => r.level === 'red');
  const verdict = qa.verdict;

  // ---- preset
  const presetList = h('ul.list');
  for (const [id, p] of Object.entries(cfg.presets || {})) {
    const res = (w.deliver || {})[id];
    const cb = h('input', { type: 'checkbox', checked: chosen.has(id), 'aria-label': p.label, on: { change: (e) => { e.target.checked ? chosen.add(id) : chosen.delete(id); store.set(`deliver.presets.${ctx.slug}`, [...chosen]); } } });
    presetList.append(h('li', h('label.check.grow', cb, h('span', h('b', p.label), h('span.dim', ` · ${p.size.join('×')} · ${p.fps} fps${p.max_sec ? ` · ≤ ${p.max_sec}s` : ''}${p.max_mb ? ` · ≤ ${p.max_mb} MB` : ''}`))),
      res ? St(LV[res.verdict][0], LV[res.verdict][1]) : h('span.dim', 'chưa xuất')));
  }

  // ---- cổng QA
  const order = { red: 0, yellow: 1, green: 2 };
  const gate = h('table.table', h('thead', h('tr', h('th', { style: { width: '64px' } }, 'Mức'), h('th', 'Kiểm tra'), h('th', 'Giá trị'), h('th', { style: { width: '128px' } }, h('span.sr-only', 'Sửa')))),
    h('tbody', rows.slice().sort((a, b) => order[a.level] - order[b.level]).map((r) => {
      const fx = r.level !== 'green' ? fixFor(r.label) : null;
      return h('tr', h('td', St(LV[r.level][0], LV[r.level][1])), h('td', { title: r.label }, r.label), h('td.mono', { title: r.value }, r.value),
        h('td', { style: { textAlign: 'right' } }, fx ? Btn(`Sửa ở ${fx[0].split(' · ')[0]}`, { size: 'sm', kind: 'ghost', title: `Mở ${fx[0]}`, onClick: () => ctx.go(fx[1]) }) : null));
    })));

  // ---- quyền
  const rights = w.rights || {};
  const rRows = (rights.rows || []);
  const rightsEl = rRows.length ? h('table.table', h('tbody', rRows.map((r) => h('tr', h('td', { style: { width: '64px' } }, St(r.ok === true ? 'OK' : r.ok === false ? 'CẤM' : 'Chờ', r.ok === true ? 'ok' : r.ok === false ? 'err' : 'warn')),
    h('td', { title: r.label }, r.label.replace(/^quyền( thương mại BỊ CẤM)?: /, '')), h('td.dim', { title: r.value }, r.value))))) :
    h('p.dim', 'Chưa có — sổ quyền được ghi khi chạy QA (out/rights.json).');
  const ai = rights.ai || {};

  // ---- gói publish
  const pub = parsePublish(w.publish_md);
  const copyBtn = (label, text) => Btn('Chép', { size: 'sm', ico: 'copy', onClick: async () => { await copyText(text); toast(`Đã chép ${label}`, { kind: 'ok', ms: 1600 }); } });
  const thumbs = (w.thumbnails || []);
  const pubEl = h('div.col',
    h('div.label', 'Tiêu đề (≤ 60 ký tự)'),
    pub.titles.length ? pub.titles.map((t, i) => h('div.row', h('span.mono.dim', `${i + 1}`), h('span.grow', t), h('span.mono.dim', `${t.length}`), copyBtn('tiêu đề', t))) : h('p.dim', 'Chưa có publish.md (sinh sau khi qua cổng QA).'),
    pub.description ? [h('div.label', 'Mô tả'), h('div.row', h('p.grow', pub.description), copyBtn('mô tả', pub.description + (ai.description_line ? `\n\n${ai.description_line}` : '')))] : null,
    pub.hashtags ? [h('div.label', 'Hashtag'), h('div.row', h('span.grow.mono', pub.hashtags), copyBtn('hashtag', pub.hashtags))] : null,
    h('div.label', 'Phụ đề'), w.outputs && w.outputs.find((o) => o.path.endsWith('.srt')) ? h('a', { href: projectFile(ctx.slug, 'out/captions.srt'), download: 'captions.srt' }, 'captions.srt') : h('span.dim', '—'),
    h('div.label', `Bìa A/B (${thumbs.length})`),
    h('div.row.wrap', thumbs.map((t) => h('a', { href: projectFile(ctx.slug, t), target: '_blank', rel: 'noopener', title: t }, h('img.thumb', { src: thumbUrl('projects', `${ctx.slug}/${t}`, 120), alt: t, width: 68, height: 120 })))));

  // ---- kết quả xuất
  const outEl = h('ul.list');
  for (const [id, r] of Object.entries(w.deliver || {})) {
    outEl.append(h('li', h('b', r.label), St(LV[r.verdict][0], LV[r.verdict][1]), h('span.grow'),
      h('a', { href: projectFile(ctx.slug, r.video), download: `${ctx.slug}-${id}.mp4` }, 'video.mp4'),
      r.cover ? h('a', { href: projectFile(ctx.slug, r.cover), download: `${ctx.slug}-${id}-cover.jpg` }, 'cover.jpg') : null));
  }

  const go = async (accept = false) => {
    if (!chosen.size) { toast('Chọn ít nhất một nền tảng.', { kind: 'warn' }); return; }
    if (accept) {
      if (!await confirm('Duyệt tay video bị cổng QA chặn?', `Bỏ qua ${red.length} mục đỏ (${red.map((r) => r.label).join('; ')}). Ghi "accepted_by_hand" vào manifest và dựng lại từ render.`, { ok: 'Duyệt tay + xuất', danger: true })) return;
      ctx.run('video', { target: ctx.slug, from: 'render', accept_qa: true, yes: true, platforms: [...chosen].join(',') }, 'Đang dựng lại + xuất (duyệt tay)');
      return;
    }
    ctx.run('deliver', { target: ctx.slug, platforms: [...chosen].join(',') }, `Đang xuất ${chosen.size} gói nền tảng`);
  };
  const blocked = verdict === 'red';
  const primary = Btn('Xuất gói', { kind: 'primary', ico: 'package', disabled: blocked || !w.has_final, onClick: () => go(false) });
  if (blocked) primary.title = `Cổng QA đỏ: ${red.length} mục chặn xuất`;
  const head = h('div.pagehead', h('h1', 'Deliver'), verdict ? St(`Cổng QA ${LV[verdict][0].toLowerCase()}`, LV[verdict][1]) : St(qa.legacy_ok === undefined || qa.legacy_ok === null ? 'Chưa QA' : 'QA cũ (trước vòng 9)', ''),
    rows.length ? h('span.sub', `${rows.length} mục · ${red.length} đỏ · ${rows.filter((r) => r.level === 'yellow').length} vàng`) : null, h('span.grow'),
    h('details', h('summary.muted', { style: { cursor: 'pointer' } }, 'Nâng cao'), h('div', { style: { position: 'absolute', right: '16px', marginTop: '6px', background: 'var(--s1)', padding: '8px', border: '1px solid var(--line)', zIndex: 5 } },
      Btn('Duyệt tay & xuất (--accept-qa)', { size: 'sm', kind: 'danger', disabled: !blocked, onClick: () => go(true) }))),
    primary);
  if (!w.has_final) {
    return h('div.page', head, Empty('Chưa có video để xuất', 'Deliver cần out/final.mp4 đã qua cổng QA.', [Btn('Chạy tiếp', { kind: 'primary', onClick: () => ctx.run('video', { target: ctx.slug, yes: true, dry_run: !!ctx.ws.dry_run }) })]));
  }
  const left = h('div',
    blocked ? h('div', { style: { padding: '12px 16px 0' } }, Callout('err', `Cổng QA đỏ — chặn xuất (${red.length} mục)`, red.map((r) => `${r.label}: ${r.value}`).join(' · '),
      [Btn('Chạy lại QA', { size: 'sm', ico: 'refresh', onClick: () => ctx.run('video', { target: ctx.slug, from: 'render', yes: true }) })])) : null,
    h('section.section', h('h2', 'Nền tảng'), presetList),
    h('section.section', h('h2', 'Cổng QA'), rows.length ? gate : h('p.dim', 'Chưa có kết quả QA vòng 9 — chạy lại từ render để có cổng đỏ/vàng/xanh.')),
    Object.keys(w.deliver || {}).length ? h('section.section', h('h2', 'Đã xuất'), outEl) : null);
  const right = h('div',
    h('section.section', h('h2', 'Nhãn AI'), ai.need ? h('dl.gridform', { style: { marginTop: '6px' } },
      h('dt', 'YouTube'), h('dd', ai.need.youtube), h('dt', 'TikTok'), h('dd', ai.need.tiktok), h('dt', 'Instagram'), h('dd', ai.need.instagram)) : h('p.dim', '—')),
    h('section.section', h('h2', 'Quyền sử dụng'), rightsEl),
    h('section.section', h('h2', 'Gói publish'), pubEl));
  return h('div.page.fill', head, Split([left, right], { id: 'deliver', sizes: [null, 440] }));
}
