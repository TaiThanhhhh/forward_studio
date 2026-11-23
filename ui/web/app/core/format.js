// Định dạng hiển thị (tiếng Việt).
export const ENGINES = {
  flow: { label: 'Google Flow', short: 'Flow' },
  three: { label: '3D three.js', short: '3D' },
  html: { label: 'Motion 2D (html)', short: '2D' },
  manim: { label: 'Sơ đồ Manim', short: 'Manim' },
  board: { label: 'Evidence board', short: 'Board' },
};

export const STATUS = {
  done: { label: 'Hoàn tất', tone: 'success' },
  running: { label: 'Đang chạy', tone: 'info', live: true },
  queued: { label: 'Đang chờ', tone: 'info' },
  waiting_clips: { label: 'Chờ clip Flow', tone: 'warning' },
  look_check: { label: 'Chờ duyệt look', tone: 'warning' },
  need_storyboard: { label: 'Cần storyboard', tone: 'warning' },
  confirm_map: { label: 'Chờ xác nhận map', tone: 'warning' },
  storyboard_invalid: { label: 'Storyboard lỗi', tone: 'danger' },
  lint_failed: { label: 'Lint lỗi', tone: 'danger' },
  need_ideas: { label: 'Cần ideas.json', tone: 'warning' },
  pick_idea: { label: 'Chờ chọn ý tưởng', tone: 'warning' },
  failed: { label: 'Lỗi', tone: 'danger' },
  cancelled: { label: 'Đã huỷ', tone: '' },
  interrupted: { label: 'Bị ngắt', tone: 'danger' },
  finished: { label: 'Xong', tone: 'success' },
  draft: { label: 'Bản nháp', tone: '' },
  new: { label: 'Mới', tone: '' },
};

export const STAGE_LABEL = {
  idea: 'Ý tưởng', script: 'Kịch bản', storyboard: 'Storyboard', prompts: 'Prompt', page: 'Trang prompt', clips: 'Clip Flow',
  ingest: 'Nhập clip', trim: 'Cắt', voice: 'Giọng đọc', assemble: 'Dựng timeline', text: 'Chữ', outro: 'Outro', audio: 'Âm thanh',
  look: 'Look-check', code: 'Shot code', render: 'Render', thumbnails: 'Thumbnail', publish: 'Đăng tải', qa: 'QA',
};

export function ago(ts) {
  if (!ts) return '—';
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 60) return 'vừa xong';
  if (s < 3600) return `${Math.floor(s / 60)} phút trước`;
  if (s < 86400) return `${Math.floor(s / 3600)} giờ trước`;
  if (s < 86400 * 30) return `${Math.floor(s / 86400)} ngày trước`;
  return new Date(ts * 1000).toLocaleDateString('vi-VN');
}

export function dur(sec) {
  if (sec === null || sec === undefined) return '—';
  if (sec < 60) return `${(+sec).toFixed(1)}s`;
  return `${Math.floor(sec / 60)}:${String(Math.round(sec % 60)).padStart(2, '0')}`;
}

export function elapsed(a, b) {
  if (!a) return '—';
  return dur((b || Date.now() / 1000) - a);
}

export function bytes(n) {
  if (!n && n !== 0) return '—';
  const u = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
}

/** Timecode HH:MM:SS:FF ở 30 fps (mono). */
export function tc(sec, fps = 30) {
  if (sec === null || sec === undefined || Number.isNaN(sec)) return '--:--:--:--';
  const f = Math.round(sec * fps);
  const ff = f % fps, s = Math.floor(f / fps);
  const p = (n) => String(n).padStart(2, '0');
  return `${p(Math.floor(s / 3600))}:${p(Math.floor(s / 60) % 60)}:${p(s % 60)}:${p(ff)}`;
}

export function pct(x) { return x === null || x === undefined ? '—' : `${Math.round(x * 100)}%`; }

export function eta(sec) {
  if (!sec && sec !== 0) return '';
  if (sec < 60) return `còn ~${Math.max(1, Math.round(sec))}s`;
  return `còn ~${Math.round(sec / 60)} phút`;
}

export const LEVEL = { green: { cls: 'ok', label: 'Xanh' }, yellow: { cls: 'warn', label: 'Vàng' }, red: { cls: 'err', label: 'Đỏ' } };
