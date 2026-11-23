// 2 · Script — ý tưởng → thẻ "Việc tiếp theo" → dán/kiểm/lưu storyboard (không mở file) → lời đọc theo shot → take giọng.
import { h, clear } from '../core/dom.js';
import { api, projectFile } from '../core/api.js';
import * as keys from '../core/keys.js';
import { ago, bytes } from '../core/format.js';
import { Btn, St, Table, Split, Empty, Callout, confirm, toast, copyText } from '../ui/kit.js';
import { Waveform } from '../ui/media.js';

function renderCheckReport(box, rep) {
  clear(box);
  if (!rep) return;
  const errs = rep.errors || [];
  const warns = rep.warnings || [];
  const sum = rep.summary || {};
  const head = h('div.row.wrap', { style: { gap: '8px', marginBottom: (errs.length || warns.length) ? '6px' : '0' } },
    rep.ok ? St('Hợp lệ · sẵn sàng lưu', 'ok') : St(`${errs.length} lỗi cần sửa`, 'err'),
    warns.length ? St(`${warns.length} cảnh báo`, 'warn') : null,
    sum.shots ? h('span.mono.dim', `${sum.shots} shot · ${sum.words || 0} từ · ${sum.sec || 0}s · style ${sum.style || 'auto'}`) : null,
    (rep.notes || []).map((n) => h('span.dim', n)));
  box.append(head);
  if (errs.length || warns.length) {
    const ul = h('ul.list', { style: { maxHeight: '160px', overflow: 'auto', border: '1px solid var(--line)', borderRadius: 'var(--r2)', background: 'var(--s0)' } });
    for (const e of errs) {
      const loc = [e.shot, e.path, e.line ? `dòng ${e.line}` : null].filter(Boolean).join(' · ');
      ul.append(h('li', St('lỗi', 'err'), h('span.grow', e.msg), loc ? h('span.mono.dim', loc) : null));
    }
    for (const w of warns) {
      const loc = [w.shot, w.path, w.line ? `dòng ${w.line}` : null].filter(Boolean).join(' · ');
      ul.append(h('li', St('lưu ý', 'warn'), h('span.grow', w.msg), loc ? h('span.mono.dim', loc) : null));
    }
    box.append(ul);
  }
}

export function NextStepCard(ctx, w, { onOpenEditor } = {}) {
  const st = w.status;
  const run = (extra, msg) => ctx.run('video', { target: ctx.slug, yes: true, dry_run: !!w.dry_run, ...extra }, msg);
  const copyBrief = async () => {
    if (!w.brief_md) { toast('Chưa có brief.md — bấm Chạy tiếp để sinh brief.', { kind: 'warn' }); return; }
    await copyText(w.brief_md);
    toast(`Đã chép brief.md (${w.brief_md.length.toLocaleString('vi-VN')} ký tự) — dán cho AI rồi chép JSON trả lời vào ô dưới`, { kind: 'ok' });
  };
  const copyCmd = async () => {
    await copyText(`/video ${ctx.slug}`);
    toast(`Đã chép lệnh: /video ${ctx.slug}`, { kind: 'ok' });
  };
  if (st === 'need_storyboard' || !w.shots) {
    return Callout('warn', 'Việc tiếp theo · Viết storyboard (exit 2: need_storyboard)',
      'Bước 1: Bấm "Copy brief.md" đưa cho AI (hoặc chạy lệnh /video trong Claude Code, hoặc bấm AI viết giúp). Bước 2: Dán câu trả lời JSON vào khung bên dưới rồi bấm "Lưu & Chạy tiếp".',
      [Btn('Copy brief.md', { kind: 'primary', size: 'sm', ico: 'copy', onClick: copyBrief }),
        Btn('Copy /video', { size: 'sm', ico: 'terminal', onClick: copyCmd }),
        Btn('AI viết (Claude)', { size: 'sm', ico: 'sparkles', onClick: () => run({ ai: 'claude' }, 'Đang gọi Claude viết storyboard') }),
        Btn('AI viết (Gemini)', { size: 'sm', ico: 'sparkles', onClick: () => run({ ai: 'gemini' }, 'Đang gọi Gemini viết storyboard') })]);
  }
  if (st === 'storyboard_invalid' || st === 'lint_failed' || (w.sb_check && !w.sb_check.ok)) {
    const nErr = (w.sb_check && (w.sb_check.errors || []).length) || 0;
    return Callout('err', `Việc tiếp theo · Sửa ${nErr || ''} lỗi storyboard (exit 3: ${st})`,
      'Xem danh sách lỗi theo trường/dòng ở khung Storyboard bên dưới, sửa trực tiếp hoặc dán bản mới từ AI rồi bấm "Lưu & Chạy tiếp".',
      [onOpenEditor ? Btn('Nạp JSON hiện tại để sửa', { kind: 'primary', size: 'sm', ico: 'pen', onClick: onOpenEditor }) : null,
        Btn('Copy brief.md', { size: 'sm', ico: 'copy', onClick: copyBrief }),
        Btn('Sửa từng shot ở Board', { size: 'sm', ico: 'grid', onClick: () => ctx.go('board') })].filter(Boolean));
  }
  if (st === 'waiting_clips') {
    return Callout('warn', 'Việc tiếp theo · Tạo & thả clip Google Flow (exit 10: waiting_clips)',
      'Mở trang Generate để chép prompt theo thứ tự cây keyframe và kéo-thả clip Flow vào đúng shot.',
      [Btn('Mở Generate', { kind: 'primary', size: 'sm', ico: 'sparkles', onClick: () => ctx.go('generate') })]);
  }
  if (st === 'confirm_map') {
    return Callout('warn', 'Việc tiếp theo · Xác nhận bảng ghép clip (exit 4: confirm_map)',
      'Kiểm tra clip đã nạp ở Generate hoặc xác nhận chạy tiếp.',
      [Btn('Xác nhận & Chạy tiếp', { kind: 'primary', size: 'sm', ico: 'check', onClick: () => run({}, 'Đang chạy tiếp sau khi xác nhận map clip') }),
        Btn('Mở Generate', { size: 'sm', onClick: () => ctx.go('generate') })]);
  }
  if (st === 'look_check') {
    return Callout('warn', 'Việc tiếp theo · Duyệt contact sheet trước khi render đầy đủ (exit 11: look_check)',
      'Kiểm tra bảng màu/ánh sáng ở contact sheet, nếu ưng ý bấm Duyệt look để render toàn bộ frame.',
      [Btn('Duyệt look & Render đầy đủ', { kind: 'primary', size: 'sm', ico: 'check', onClick: () => run({ look_ok: true }, 'Đã duyệt look · đang render đầy đủ') }),
        Btn('Mở Board xem shot', { size: 'sm', ico: 'grid', onClick: () => ctx.go('board') })]);
  }
  if (st === 'qa_failed') {
    return Callout('err', 'Việc tiếp theo · Cổng QA báo đỏ (exit 12: qa_failed)',
      'Mở trang Review để xem chỉ số QA bị chặn, sửa shot lỗi ở Board/Edit hoặc duyệt tay nếu chấp nhận.',
      [Btn('Mở Review / QA', { kind: 'primary', size: 'sm', ico: 'eye', onClick: () => ctx.go('review') }),
        Btn('Duyệt tay QA (--accept-qa)', { size: 'sm', onClick: () => run({ accept_qa: true }, 'Đang duyệt tay QA') })]);
  }
  if (st === 'done') {
    return Callout('ok', 'Video đã hoàn tất', 'Xem bản dựng ở Review hoặc xuất gói đa nền tảng ở Deliver.',
      [Btn('Mở Review', { size: 'sm', ico: 'eye', onClick: () => ctx.go('review') }),
        Btn('Mở Deliver', { kind: 'primary', size: 'sm', ico: 'package', onClick: () => ctx.go('deliver') })]);
  }
  return Callout('info', `Trạng thái · ${w.status_label || st}`, 'Bấm Chạy tiếp để pipeline thực hiện công đoạn kế tiếp.',
    [Btn('Chạy tiếp pipeline', { kind: 'primary', size: 'sm', ico: 'play', onClick: () => run({}, 'Đang chạy tiếp pipeline') })]);
}

export async function render(ctx) {
  const w = ctx.ws;
  const shots = w.shots_detail || [];
  const vo = w.vo || { takes: [], words: [] };
  const cur = vo.takes.find((t) => t.current);
  const plan = w.plan || {};
  const needSb = !shots.length || ['need_storyboard', 'storyboard_invalid', 'lint_failed'].includes(w.status) || (w.sb_check && !w.sb_check.ok);

  // ---- Khung dán / kiểm / lưu Storyboard JSON (không mở file) ----
  const sbText = h('textarea.textarea.mono', {
    rows: needSb ? 10 : 6,
    placeholder: 'Dán trực tiếp câu trả lời của AI (có chữ giải thích hoặc ```json đều được) hoặc kéo-thả file storyboard.json vào đây…',
    'aria-label': 'Nội dung Storyboard JSON',
    value: (!shots.length || !w.sb_raw) ? '' : (w.sb_check && !w.sb_check.ok ? w.sb_raw : ''),
  });
  if (w.sb_check && !w.sb_check.ok && w.sb_raw) sbText.value = w.sb_raw;
  const repBox = h('div', { 'aria-live': 'polite' });
  renderCheckReport(repBox, w.sb_check);

  const loadFile = (file) => {
    const rd = new FileReader();
    rd.onload = async () => {
      sbText.value = String(rd.result || '');
      toast(`Đã nạp file ${file.name} — đang kiểm tra…`, { kind: 'ok', ms: 2000 });
      await doCheck();
    };
    rd.readAsText(file, 'utf-8');
  };
  sbText.addEventListener('dragover', (e) => { e.preventDefault(); sbText.style.borderColor = 'var(--accent-text)'; });
  sbText.addEventListener('dragleave', () => { sbText.style.borderColor = ''; });
  sbText.addEventListener('drop', (e) => {
    e.preventDefault(); sbText.style.borderColor = '';
    const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) loadFile(f);
  });
  const fileIn = h('input', { type: 'file', accept: '.json,.txt,.md', hidden: true, on: { change: () => fileIn.files[0] && loadFile(fileIn.files[0]) } });

  const doCheck = async () => {
    const txt = sbText.value.trim();
    if (!txt && !w.sb_raw) { toast('Dán JSON storyboard vào ô trước khi kiểm tra.', { kind: 'warn' }); sbText.focus(); return; }
    const rep = await api.sbCheck(ctx.slug, txt);
    renderCheckReport(repBox, rep);
    toast(rep.ok ? 'Storyboard hợp lệ!' : `Có ${(rep.errors || []).length} lỗi cần sửa`, { kind: rep.ok ? 'ok' : 'warn' });
  };
  const doSave = async (resume) => {
    const txt = sbText.value.trim();
    if (!txt) { toast('Chưa có nội dung JSON trong ô để lưu.', { kind: 'warn' }); sbText.focus(); return; }
    const rep = await api.sbImport(ctx.slug, txt, { resume, dry_run: !!w.dry_run });
    renderCheckReport(repBox, rep);
    if (!rep.ok && !rep.saved) {
      toast(`Chưa lưu được: ${(rep.errors || []).length} lỗi`, { kind: 'err' });
      return;
    }
    toast(resume ? 'Đã lưu storyboard.json & bắt đầu chạy tiếp pipeline!' : 'Đã lưu storyboard.json!', { kind: 'ok' });
    if (rep.resume_job && ctx.drawer) ctx.drawer.open();
    await ctx.reload();
  };
  const doRestore = async (bid) => {
    if (!await confirm(`Khôi phục bản lưu ${bid}?`, 'Storyboard hiện tại vẫn được lưu vào lịch sử để có thể hoàn tác.', { ok: 'Khôi phục' })) return;
    const rep = await api.sbRestore(ctx.slug, bid);
    if (!rep.ok && !rep.saved) { toast('Không khôi phục được.', { kind: 'err' }); return; }
    toast(`Đã khôi phục bản ${bid}`, { kind: 'ok' });
    await ctx.reload();
  };

  const hist = w.sb_history || [];
  const histEl = hist.length ? h('details', { style: { marginTop: '6px' } },
    h('summary.muted', { style: { cursor: 'pointer' } }, `Hoàn tác / Lịch sử (${hist.length} bản lưu)`),
    h('ul.list', { style: { maxHeight: '140px', overflow: 'auto', marginTop: '4px', border: '1px solid var(--line)', borderRadius: 'var(--r2)' } },
      hist.slice(0, 12).map((item) => h('li',
        h('span.mono', item.id.slice(0, 15)),
        h('span.dim', `${item.shots || 0} shot`),
        h('span.grow.ellipsis', item.note || ''),
        Btn('Khôi phục', { size: 'sm', ico: 'undo', onClick: () => doRestore(item.id) }))))) : null;

  const sbDetails = h('details', { open: needSb },
    h('summary', { style: { cursor: 'pointer', fontWeight: 600 } },
      needSb ? 'Dán / Sửa Storyboard JSON tại chỗ (không cần mở thư mục)' : 'Sửa / Dán lại Storyboard JSON & Lịch sử hoàn tác'),
    h('div.col', { style: { marginTop: '8px', gap: '8px' } },
      h('div.row.wrap', { style: { gap: '6px' } },
        Btn('Copy brief.md', { size: 'sm', ico: 'copy', onClick: async () => {
          if (!w.brief_md) { toast('Chưa có brief.md — bấm Chạy tiếp để tạo.', { kind: 'warn' }); return; }
          await copyText(w.brief_md);
          toast(`Đã chép brief.md (${w.brief_md.length.toLocaleString('vi-VN')} ký tự)`, { kind: 'ok' });
        } }),
        Btn('Copy lệnh /video', { size: 'sm', ico: 'terminal', onClick: async () => { await copyText(`/video ${ctx.slug}`); toast(`Đã chép: /video ${ctx.slug}`, { kind: 'ok' }); } }),
        w.sb_raw ? Btn('Nạp JSON hiện có', { size: 'sm', ico: 'script', onClick: () => { sbText.value = w.sb_raw; sbText.focus(); } }) : null,
        Btn('Chọn file .json…', { size: 'sm', ico: 'upload', onClick: () => fileIn.click() }), fileIn,
        h('span.grow'),
        Btn('Kiểm tra ngay', { size: 'sm', ico: 'check', onClick: doCheck }),
        Btn('Lưu JSON', { size: 'sm', onClick: () => doSave(false) }),
        Btn('Lưu & Chạy tiếp', { kind: 'primary', size: 'sm', ico: 'play', onClick: () => doSave(true) })),
      sbText,
      repBox,
      histEl));

  const nextCard = NextStepCard(ctx, w, { onOpenEditor: () => { sbDetails.open = true; sbText.value = w.sb_raw || ''; sbText.focus(); } });

  const info = h('div',
    h('section.section', h('h2', 'Ý tưởng'), h('dl.gridform.stack',
      h('dt', 'Ý tưởng'), h('dd', w.idea || w.topic || '—'),
      h('dt', 'Tiêu đề'), h('dd', w.title || '—'),
      h('dt', 'Hook'), h('dd', w.hook || '—'),
      h('dt', 'Nhãn sự thật'), h('dd', w.truth ? St(w.truth, w.truth === 'True' ? 'ok' : 'warn') : '—'))),
    h('section.section', h('h2', 'Kế hoạch'), h('dl.gridform.stack',
      h('dt', 'Style'), h('dd', h('span.mono', w.style || '—'), w.style_name ? h('span.dim', ` · ${w.style_name}`) : null),
      h('dt', 'Giọng'), h('dd', w.voice || vo.voice || '—'),
      h('dt', 'Dạng kịch bản'), h('dd', w.narrative || plan.narrative || '—'),
      h('dt', 'Ngày'), h('dd', w.uses_flow === null || w.uses_flow === undefined ? '—' : St(w.uses_flow ? 'có Flow' : 'toàn code', w.uses_flow ? 'warn' : 'ok')),
      plan.reason ? [h('dt', 'Vì sao'), h('dd.muted', plan.reason)] : null)));

  const words = (t) => (t || '').split(/\s+/).filter(Boolean).length;
  const table = Table({
    rowKey: (r) => r.id, rows: shots.filter((s) => s.vo),
    onOpen: (r) => { ctx.go('board'); },
    columns: [
      { key: 'id', label: 'Shot', render: (r) => h('span.mono', r.id), width: '64px' },
      { key: 'beat', label: 'Beat', width: '84px' },
      { key: 'vo', label: 'Lời đọc (tiếng Anh)', render: (r) => h('span', { title: r.vo }, r.vo) },
      { key: 'dur', label: 'Dài', num: true, render: (r) => (r.dur ? `${(+r.dur).toFixed(1)}s` : '—'), width: '64px' },
      { key: 'wps', label: 'Từ/s', num: true, sort: (r) => (r.dur ? words(r.vo) / r.dur : 0), render: (r) => (r.dur ? (words(r.vo) / r.dur).toFixed(1) : '—'), width: '64px' },
    ],
    empty: Empty('Chưa có kịch bản', 'Copy brief.md ở trên đưa cho AI rồi dán JSON vào ô Storyboard, hoặc bấm AI viết giúp.', []),
  });

  const takes = h('ul.list');
  const audio = cur ? h('audio', { src: projectFile(ctx.slug, cur.file), controls: true, preload: 'metadata', style: { width: '100%' }, 'aria-label': 'Take hiện tại' }) : null;
  const seek = (t) => { if (audio) { audio.currentTime = t; audio.play(); } };
  for (const t of vo.takes) {
    takes.append(h(`li${t.current ? '.sel' : ''}`, h('div.col.grow', { style: { gap: '2px' } },
      h('div.row', h('span.mono', t.file.split('/').pop()), t.current ? St('đang dùng', 'ok') : St('take cũ', '')),
      h('span.dim', `${ago(t.mtime)} · ${bytes(t.size)}`)),
    t.current ? null : h('audio', { src: projectFile(ctx.slug, t.file), controls: true, preload: 'none', style: { width: '220px', height: '28px' }, 'aria-label': 'Nghe take cũ' })));
  }
  const voPane = h('div',
    h('section.section', h('div.row', h('h2', 'Take giọng'), h('span.grow'), vo.wps ? h('span.mono.dim', `${vo.wps} từ/giây`) : null),
      cur ? h('div.col', { style: { marginTop: '8px' } }, audio, Waveform(projectFile(ctx.slug, cur.file), { words: vo.words, onSeek: seek })) :
        Empty('Chưa có giọng đọc', 'Giọng được tạo ở stage voice (ElevenLabs) sau khi có storyboard hợp lệ.', [])),
    vo.takes.length ? takes : null,
    h('section.section.dim', 'Take cũ được giữ để so sánh (vo.prev-*.mp3). Mốc từng từ lấy từ ElevenLabs — bấm một từ để nghe từ đó.'));

  const redo = async () => {
    if (!await confirm('Tạo lại giọng đọc?', 'Gọi ElevenLabs (tốn credit) để tạo take mới cho toàn bộ lời đọc, rồi dựng lại video. Take hiện tại được giữ lại để so sánh.', { ok: 'Tạo take mới' })) return;
    ctx.run('redo_voice', { target: ctx.slug }, 'Đang tạo take giọng mới');
  };
  const primary = cur ? Btn('Tạo lại giọng', { kind: 'primary', ico: 'mic', onClick: redo })
    : Btn('Chạy tiếp', { kind: 'primary', ico: 'play', onClick: () => ctx.run('video', { target: ctx.slug, yes: true, dry_run: !!ctx.ws.dry_run }) });
  keys.register('page', 'P', () => { if (audio) audio.paused ? audio.play() : audio.pause(); }, 'Nghe / dừng take hiện tại');

  const centerCol = h('div', { style: { display: 'flex', flexDirection: 'column', height: '100%' } },
    h('section.section', { style: { display: 'flex', flexDirection: 'column', gap: '8px' } }, nextCard, sbDetails),
    h('div', { style: { flex: 1, minHeight: 0 } }, table));

  return h('div.page.fill',
    h('div.pagehead', h('h1', 'Script'), h('span.sub.ellipsis', w.title || ctx.slug), h('span.grow'),
      h('details', h('summary.muted', { style: { cursor: 'pointer' } }, 'Nâng cao'), h('div.row', { style: { position: 'absolute', right: '16px', marginTop: '6px', background: 'var(--s1)', padding: '6px', border: '1px solid var(--line)', zIndex: 5 } },
        Btn('Chạy thử giọng (dữ liệu giả)', { size: 'sm', onClick: () => ctx.run('video', { target: ctx.slug, from: 'voice', dry_run: true, yes: true }) }))),
      primary),
    Split([h('div', info), centerCol, h('div', voPane)],
      { id: 'script', sizes: [300, null, 360] }));
}
