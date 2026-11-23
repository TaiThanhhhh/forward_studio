// Lớp gọi API duy nhất của UI: JSON, lỗi tiếng Việt, header chống CSRF, URL file, luồng log (SSE).
const HEADERS = { 'X-Studio-Client': 'web' };

export class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

async function request(method, path, body) {
  const opt = { method, headers: { ...HEADERS } };
  if (body !== undefined) {
    opt.headers['Content-Type'] = 'application/json';
    opt.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, opt);
  } catch {
    throw new ApiError(0, 'Không kết nối được máy chủ Studio UI (python studio.py ui còn chạy không?).');
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data.error || `Lỗi ${res.status}`);
  return data;
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b = {}) => request('POST', p, b),
  overview: () => request('GET', '/api/overview'),
  projects: (demo = false) => request('GET', `/api/projects${demo ? '?demo=1' : ''}`),
  project: (slug) => request('GET', `/api/projects/${encodeURIComponent(slug)}`),
  styles: () => request('GET', '/api/styles'),
  voices: () => request('GET', '/api/voices'),
  narratives: (topic = '') => request('GET', `/api/narratives?topic=${encodeURIComponent(topic)}`),
  stages: () => request('GET', '/api/stages'),
  models: () => request('GET', '/api/models'),
  ideas: () => request('GET', '/api/ideas'),
  plan: (q) => request('GET', `/api/plan?${new URLSearchParams(q)}`),
  jobs: () => request('GET', '/api/jobs'),
  job: (id, from = 0) => request('GET', `/api/jobs/${id}?from=${from}`),
  startJob: (kind, params) => request('POST', '/api/jobs', { kind, params }),
  cancelJob: (id) => request('POST', `/api/jobs/${id}/cancel`),
  reveal: (slug) => request('POST', `/api/projects/${encodeURIComponent(slug)}/reveal`),
  system: () => request('GET', '/api/system'),
  // v2 — trang công đoạn
  workspace: (slug) => request('GET', `/api/v2/projects/${encodeURIComponent(slug)}/workspace`),
  review: (slug) => request('GET', `/api/v2/projects/${encodeURIComponent(slug)}/review`),
  reviewOp: (slug, body) => request('POST', `/api/v2/projects/${encodeURIComponent(slug)}/review`, body),
  delivery: () => request('GET', '/api/v2/delivery'),
  atlas: (n) => request('GET', `/api/v2/atlas/${n}`),
  assets: () => request('GET', '/api/v2/assets'),
  session: () => request('GET', '/api/v2/session'),
  // v2 — vòng 10 (sửa storyboard/ideas có kiểm, xem trước 1 frame, cài đặt key .env, schema catalog)
  sbCheck: (slug, text = '') => request('POST', `/api/v2/projects/${encodeURIComponent(slug)}/sb/check`, { text }),
  sbImport: (slug, text, { resume = false, dry_run = undefined } = {}) =>
    request('POST', `/api/v2/projects/${encodeURIComponent(slug)}/sb/import`, { text, resume, dry_run }),
  sbPatch: (slug, { shot = null, set = {}, unset = [] } = {}) =>
    request('POST', `/api/v2/projects/${encodeURIComponent(slug)}/sb/patch`, { shot, set, unset }),
  sbHistory: (slug) => request('GET', `/api/v2/projects/${encodeURIComponent(slug)}/sb/history`),
  sbRestore: (slug, id) => request('POST', `/api/v2/projects/${encodeURIComponent(slug)}/sb/restore`, { id }),
  sbPreview: (slug, shot, u = 0.5) => request('POST', `/api/v2/projects/${encodeURIComponent(slug)}/sb/preview`, { shot, u }),
  ideasImport: (batch, text) => request('POST', `/api/v2/ideas/${encodeURIComponent(batch)}/import`, { text }),
  saveEnv: (body) => request('POST', '/api/v2/env', body),
  schema: () => request('GET', '/api/v2/catalog/schema'),
};

/** Ảnh nhỏ có cache phía server (lưới shot/style). */
export function thumbUrl(root, path, w = 240, v) {
  const q = new URLSearchParams({ root, path, w: String(w) });
  if (v) q.set('v', v);
  return `/api/v2/thumb?${q}`;
}

/** URL đọc file qua API (projects/qa/styles/docs/ideas). v = phá cache khi file được dựng lại. */
export function fileUrl(root, path, v) {
  const q = new URLSearchParams({ root, path });
  if (v) q.set('v', v);
  return `/api/file?${q}`;
}
export const projectFile = (slug, rel, v) => fileUrl('projects', `${slug}/${rel}`, v);

/** Tải clip lên cho một shot, báo tiến độ 0..1. */
export function uploadClip(slug, sid, file, onProgress) {
  return new Promise((resolve, reject) => {
    const x = new XMLHttpRequest();
    x.open('POST', `/api/projects/${encodeURIComponent(slug)}/clips/${sid}`);
    x.setRequestHeader('X-Studio-Client', 'web');
    x.setRequestHeader('X-Filename', encodeURIComponent(file.name));
    x.upload.onprogress = (e) => e.lengthComputable && onProgress && onProgress(e.loaded / e.total);
    x.onload = () => {
      let d = {};
      try { d = JSON.parse(x.responseText); } catch { /* bỏ qua */ }
      if (x.status >= 200 && x.status < 300) resolve(d); else reject(new ApiError(x.status, d.error || 'Tải lên lỗi'));
    };
    x.onerror = () => reject(new ApiError(0, 'Mất kết nối khi tải lên'));
    x.send(file);
  });
}

/** Theo dõi log job: onLines(lines), onMeta(meta), onEnd(). Trả về hàm huỷ. */
export function followJob(id, { from = 0, onLines, onMeta, onEnd } = {}) {
  let es = null, next = from, closed = false;
  const open = () => {
    es = new EventSource(`/api/jobs/${id}/events?from=${next}`);
    es.addEventListener('lines', (e) => { const d = JSON.parse(e.data); next = d.next; onLines && onLines(d.lines); });
    es.addEventListener('meta', (e) => onMeta && onMeta(JSON.parse(e.data)));
    es.addEventListener('end', () => { closed = true; es.close(); onEnd && onEnd(); });
    es.onerror = () => {                        // mất kết nối (server khởi động lại…) → nối lại từ dòng đã có
      if (closed) return;
      es.close();
      setTimeout(() => { if (!closed) open(); }, 1500);
    };
  };
  open();
  return { close: () => { closed = true; if (es) es.close(); } };
}
