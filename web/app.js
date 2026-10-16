'use strict';

// ================================================================= transport
async function call(op, args, method) {
  const isPost = method === 'POST' || (args && method !== 'GET');
  let url = '/api/' + op, opts = { method: 'GET' };
  if (isPost) {
    opts = { method: 'POST', body: JSON.stringify(args || {}),
             headers: { 'Content-Type': 'application/json' } };
  } else if (args) {
    url += '?' + new URLSearchParams(args);
  }
  const res = await fetch(url, opts);
  let body = {};
  try { body = await res.json(); } catch (e) { /* not JSON */ }
  if (!res.ok || !body.ok) {
    const err = new Error(body.error || res.statusText || 'request failed');
    err.status = res.status;
    throw err;
  }
  return body.data;
}
const post = (op, args) => call(op, args || {}, 'POST');

// =================================================================== helpers
const el = (tag, attrs, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === 'class') n.className = v;
    else if (k === 'html') n.innerHTML = v;
    else if (k === 'style') n.setAttribute('style', v);
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return n;
};

const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// `code`, **bold**, *emphasis*.  Code spans are lifted out first, so `a * b` stays code.
function inline(text) {
  const spans = [];
  let out = esc(text).replace(/`([^`]+)`/g, (_, c) => '\u0000' + (spans.push(c) - 1) + '\u0000');
  out = out
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>')
    // textbook notation outside code: 10^9, 2^(n-1), a_i, a_(l+1)
    .replace(/([\w)|])\^(\((?:[^()]|\([^()]*\))*\)|\|[^|\s]+\||[-−]?[A-Za-z0-9]+)/g, (_, b, e) => b + '<sup>' + e.replace(/^\((.*)\)$/, '$1') + '</sup>')
    .replace(/\b([A-Za-z])_(\([^)]*\)|[A-Za-z0-9]{1,3}\b)/g, (_, b, e) => b + '<sub>' + e.replace(/^\((.*)\)$/, '$1') + '</sub>');
  return out.replace(/\u0000(\d+)\u0000/g, (_, i) => '<code>' + spans[i] + '</code>');
}

// ---- C++ highlighting, shared by prose code blocks and the editor
const CPP_KW = new Set(('alignas alignof and asm auto bitand bitor break case catch class compl const ' +
  'constexpr const_cast continue decltype default delete do dynamic_cast else enum explicit export ' +
  'extern false for friend goto if inline mutable namespace new noexcept not nullptr operator or ' +
  'private protected public register reinterpret_cast return sizeof static static_assert ' +
  'static_cast struct switch template this throw true try typedef typeid typename union using ' +
  'virtual volatile while xor').split(' '));
const CPP_TY = new Set(('int long short char bool double float void unsigned signed size_t string ' +
  'vector pair map set multiset multimap unordered_map unordered_set queue deque stack ' +
  'priority_queue array bitset tuple ll ull ld pii pll vi vll greater less int64_t uint64_t ' +
  'int32_t uint32_t __int128 stringstream istringstream ostringstream function optional list ' +
  'mt19937 mt19937_64 complex').split(' '));
const CPP_RE = /(\/\/[^\n]*|\/\*[\s\S]*?(?:\*\/|$))|("(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?)|(^[ \t]*#[^\n]*)|(\b\d[\w.']*)|([A-Za-z_]\w*)/gm;

function highlight(src) {
  let out = '', last = 0, m;
  CPP_RE.lastIndex = 0;
  while ((m = CPP_RE.exec(src))) {
    if (m[0] === '') { CPP_RE.lastIndex++; continue; }
    out += esc(src.slice(last, m.index));
    const t = m[0];
    const cls = m[1] ? 'com' : m[2] ? 'str' : m[3] ? 'pre' : m[4] ? 'num'
      : CPP_KW.has(t) ? 'kw' : CPP_TY.has(t) ? 'ty' : '';
    out += cls ? '<span class="tk-' + cls + '">' + esc(t) + '</span>' : esc(t);
    last = m.index + t.length;
  }
  return out + esc(src.slice(last));
}

function codeBlock(text, lang) {
  const code = el('code');
  if (!lang || lang === 'cpp' || lang === 'c++') code.innerHTML = highlight(text);
  else code.textContent = text;
  return el('pre', {}, code);
}

// Blocks from cptutor/markup.py: paragraph / heading / bullet / num / code / table.
function prose(blocks, cls) {
  const box = el('div', { class: 'prose' + (cls ? ' ' + cls : '') });
  let list = null, listType = '';
  for (const b of blocks || []) {
    const lt = b.type === 'bullet' ? 'ul' : b.type === 'num' ? 'ol' : '';
    if (lt !== listType) { list = null; listType = lt; }
    if (b.type === 'code') box.append(codeBlock(b.text, b.lang));
    else if (b.type === 'heading') box.append(el('h4', { html: inline(b.text) }));
    else if (lt) {
      if (!list) {
        list = el(lt, lt === 'ol' && b.n ? { start: b.n } : {});
        box.append(list);
      }
      list.append(el('li', { html: inline(b.text) }));
    } else if (b.type === 'table') {
      const t = el('table');
      b.rows.forEach((cells, i) => t.append(el('tr', {}, cells.map(c => el(i ? 'td' : 'th', { html: inline(c) })))));
      box.append(t);
    } else box.append(el('p', { html: inline(b.text) }));
  }
  return box;
}
const book = blocks => el('div', { class: 'book' }, prose(blocks));

const heading = (title, value, rule = true) => el('div', { class: 'heading' },
  el('div', { class: 'top' }, el('span', { class: 't' }, title),
     value != null && value !== '' ? el('span', { class: 'v' }, value) : null),
  rule ? el('div', { class: 'rule' }) : null);

const kbd = (key, on) => el('span', { class: 'kbd' + (on ? ' on' : '') }, key);
const figure = (n, k) => el('div', { class: 'figure' }, el('div', { class: 'n' }, n), el('div', { class: 'k' }, k));
const meter = (label, pct) => el('div', { class: 'meter' },
  el('span', { class: 'ellipsis' }, label), el('span', { class: 'grow' }),
  el('span', { class: 'track' }, el('span', {
    class: pct >= 80 ? 'hi' : pct >= 65 ? '' : 'lo', style: 'width:' + Math.max(0, Math.min(100, pct)) + '%' })),
  el('span', { class: 'pct' }, pct));

function forecastStrip(counts) {
  const peak = Math.max(1, ...counts.slice(1));
  return el('div', { class: 'forecast' }, counts.map((n, i) => el('span', {
    class: (n ? 'has' : '') + (i === 0 ? ' today' : ''),
    title: (i === 0 ? 'today' : 'in ' + i + ' day' + (i === 1 ? '' : 's')) + ': ' + n + ' due',
    style: n ? 'opacity:' + (0.35 + 0.65 * Math.min(1, n / peak)) : '',
  })));
}

const rowbtn = (href, cls, ...kids) => el(href ? 'a' : 'div', { class: 'rowbtn ' + (cls || ''), href }, ...kids);
const titleline = (title, note) => el('div', { class: 'titleline' },
  el('h1', {}, title), note ? el('span', { class: 'note' }, note) : null);

// A balloon per problem: outlined until solved, filled after, like the ones on the
// tables at a contest.
function balloonSvg(color, solved, size) {
  const s = el('span', { class: 'balloon', style: size ? `width:${size}px;height:${Math.round(size * 1.25)}px` : '' });
  s.innerHTML = `<svg viewBox="0 0 20 25" aria-hidden="true"><path d="M10 1.2C5.1 1.2 2 5 2 9.3c0 4.9 4.2 9.1 7 10.1l-1.1 1.6h4.2L11 19.4c2.8-1 7-5.2 7-10.1C18 5 14.9 1.2 10 1.2z" fill="${solved ? color : 'none'}" stroke="${color}" stroke-width="${solved ? 0 : 1.6}"/>${solved ? `<ellipse cx="7" cy="7" rx="1.6" ry="2.6" fill="#fff" opacity=".35"/>` : ''}</svg>`;
  s.title = solved ? 'solved' : 'not solved yet';
  return s;
}
const balloonRow = bs => el('span', { class: 'balloons' }, (bs || []).map(b => balloonSvg(b.color, b.solved)));

function floatBalloon(color) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const n = el('div', { class: 'float-balloon', style: 'left:' + (18 + Math.random() * 60) + 'vw' });
  n.innerHTML = `<svg viewBox="0 0 20 34"><path d="M10 1.2C5.1 1.2 2 5 2 9.3c0 4.9 4.2 9.1 7 10.1l-1.1 1.6h4.2L11 19.4c2.8-1 7-5.2 7-10.1C18 5 14.9 1.2 10 1.2z" fill="${color}"/><ellipse cx="7" cy="7" rx="1.6" ry="2.6" fill="#fff" opacity=".35"/><path d="M10 21c-1 3 1.5 5 0 8s1 4 0 5" stroke="${color}" stroke-width=".6" fill="none"/></svg>`;
  document.body.append(n);
  setTimeout(() => n.remove(), 3400);
}

function flash(msg) {
  const n = el('div', { class: 'flash', role: 'status' }, msg);
  document.body.append(n);
  setTimeout(() => n.remove(), 2800);
}

// replaceChildren, minus the nulls and falses that conditional children produce
function fill(node, ...kids) {
  node.replaceChildren(...kids.flat(Infinity).filter(k => k != null && k !== false));
  return node;
}

const view = () => document.getElementById('view');
function show(nodes, width) {
  const v = view();
  v.className = width || '';
  v.replaceChildren(...[].concat(nodes).flat(Infinity).filter(n => n != null && n !== false));
  window.scrollTo(0, 0);
}

// Two columns with a draggable rule between them.  The left width is a percentage kept
// in --split (so the narrow-screen media query can still stack the columns) and
// remembered under `key`; double-clicking the rule puts it back to `dflt`.
function splitCols(left, right, key, dflt = 44) {
  const rule = el('div', { class: 'rule', role: 'separator', 'aria-orientation': 'vertical',
                           'aria-label': 'resize columns', tabindex: '0', title: 'drag to resize · double-click to reset' });
  const cols = el('div', { class: 'problem-cols' }, left, rule, right);
  let pct = Math.min(80, Math.max(20, +stored(key, dflt) || dflt));
  const set = (p, save) => {
    const w = cols.getBoundingClientRect().width;
    const lo = w ? Math.max(20, 280 / w * 100) : 20, hi = w ? Math.min(80, 100 - 340 / w * 100) : 80;
    pct = Math.round(Math.min(hi, Math.max(lo, p)) * 10) / 10;
    cols.style.setProperty('--split', pct + '%');
    rule.setAttribute('aria-valuenow', Math.round(pct));
    if (save) store(key, pct);
  };
  cols.style.setProperty('--split', pct + '%');
  rule.setAttribute('aria-valuenow', Math.round(pct));
  requestAnimationFrame(() => set(pct));  // once on the page, clamp to this window's width
  rule.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    e.preventDefault();
    rule.setPointerCapture(e.pointerId);
    rule.classList.add('dragging');
    document.body.classList.add('resizing');
  });
  rule.addEventListener('pointermove', e => {
    if (!rule.hasPointerCapture(e.pointerId)) return;
    const r = cols.getBoundingClientRect();
    set((e.clientX - r.left) / r.width * 100);
  });
  const end = e => {
    if (!rule.classList.contains('dragging')) return;
    rule.classList.remove('dragging');
    document.body.classList.remove('resizing');
    if (rule.hasPointerCapture(e.pointerId)) rule.releasePointerCapture(e.pointerId);
    store(key, pct);
  };
  rule.addEventListener('pointerup', end);
  rule.addEventListener('pointercancel', end);
  rule.addEventListener('lostpointercapture', end);
  rule.addEventListener('dblclick', () => set(dflt, true));
  rule.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      set(pct + (e.key === 'ArrowLeft' ? -2 : 2), true);
    }
  });
  return cols;
}

const VERDICT_NAME = { AC: 'Accepted', WA: 'Wrong Answer', TLE: 'Time Limit Exceeded',
                       RE: 'Run-Time Error', OLE: 'Output Limit Exceeded', CE: 'Compilation Error' };
const plural = (n, w) => n + ' ' + w + (n === 1 ? '' : 's');
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function shortDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  return m ? MONTHS[+m[2] - 1] + ' ' + (+m[3]) : iso;
}
function whenAgo(iso) {
  const t = Date.parse(iso);
  if (!t) return '';
  const s = (Date.now() - t) / 1000;
  if (s < 60) return 'just now';
  if (s < 3600) return Math.round(s / 60) + ' min ago';
  if (s < 86400) return Math.round(s / 3600) + ' h ago';
  return shortDate(iso);
}
const isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
const MOD = isMac ? '⌘' : 'Ctrl+';

// ================================================================ keyboard
// Single-key shortcuts, rebound per screen; global ones fill in what a screen leaves free.
let KEYS = {};
const GLOBAL_KEYS = { t: '#/', b: '#/browse', o: '#/problems', r: '#/review', s: '#/stats',
                      g: '#/playground', c: '#/contest', n: '#/notebook', '?': '#/about' };
// ⌘/Ctrl shortcuts that work anywhere on a screen (the editor and other boxes that
// handle a combination themselves call preventDefault first, and win).
let MODKEYS = {};
document.addEventListener('keydown', e => {
  if (!(e.metaKey || e.ctrlKey) || e.altKey || e.defaultPrevented) return;
  const fn = MODKEYS[e.key];
  if (fn) { e.preventDefault(); fn(e); }
});
document.addEventListener('keydown', e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const tag = (e.target.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;
  const fn = KEYS[e.key];
  if (fn) { e.preventDefault(); fn(e); return; }
  if (GLOBAL_KEYS[e.key]) { e.preventDefault(); location.hash = GLOBAL_KEYS[e.key]; }
});

// Time on task: counted while a working screen is open, visible, and touched recently.
let lastActive = Date.now();
['keydown', 'mousedown', 'scroll', 'mousemove'].forEach(ev =>
  document.addEventListener(ev, () => { lastActive = Date.now(); }, { passive: true }));
setInterval(() => {
  const h = location.hash;
  if (document.visibilityState !== 'visible') return;
  if (Date.now() - lastActive > 150000) return;
  if (!/^#\/(lesson|problem|review|playground|contest)/.test(h)) return;
  post('heartbeat', { seconds: 60 }).catch(() => {});
}, 60000);

// ================================================================== editor
function makeEditor(code, opts = {}) {
  const gutter = el('div', { class: 'gutter', 'aria-hidden': 'true' });
  const hl = el('pre', { class: 'hl', 'aria-hidden': 'true' });
  const ta = el('textarea', { spellcheck: 'false', autocapitalize: 'off', autocomplete: 'off',
                              autocorrect: 'off', wrap: 'off', 'aria-label': 'C++ source' });
  ta.value = code || '';
  const node = el('div', { class: 'editor' + (opts.tall ? ' tall' : '') }, gutter,
                  el('div', { class: 'codewrap' }, hl, ta));
  let marks = new Set();

  function paint() {
    const v = ta.value;
    hl.innerHTML = highlight(v) + '\n\n';
    const n = v.split('\n').length;
    let g = '';
    for (let i = 1; i <= n; i++) g += (marks.has(i) ? '<span class="err">' + i + '</span>' : i) + '\n';
    gutter.innerHTML = g + '\n';
    sync();
  }
  function sync() {
    hl.scrollTop = ta.scrollTop;
    hl.scrollLeft = ta.scrollLeft;
    gutter.scrollTop = ta.scrollTop;
  }
  function insert(text) {
    ta.focus();
    // execCommand keeps the browser's undo stack; setRangeText is the fallback
    if (!document.execCommand || !document.execCommand('insertText', false, text)) {
      ta.setRangeText(text, ta.selectionStart, ta.selectionEnd, 'end');
      ta.dispatchEvent(new Event('input'));
    }
  }
  function lineBounds() {
    const v = ta.value;
    const s = v.lastIndexOf('\n', ta.selectionStart - 1) + 1;
    let e = ta.selectionEnd;
    if (e > ta.selectionStart && v[e - 1] === '\n') e--;
    const end = v.indexOf('\n', e);
    return [s, end === -1 ? v.length : end];
  }
  function mapLines(fn) {
    const [s, e] = lineBounds();
    const lines = ta.value.slice(s, e).split('\n');
    const out = fn(lines).join('\n');
    ta.setSelectionRange(s, e);
    insert(out);
    ta.setSelectionRange(s, s + out.length);
  }

  ta.addEventListener('input', () => { paint(); if (opts.onChange) opts.onChange(ta.value); });
  ta.addEventListener('scroll', sync);
  ta.addEventListener('keydown', e => {
    const mod = e.metaKey || e.ctrlKey;
    if (mod && e.key === 'Enter') { e.preventDefault(); (e.shiftKey ? opts.onRun : opts.onSubmit || opts.onRun)?.(); return; }
    if (mod && e.key === "'") { e.preventDefault(); opts.onRun?.(); return; }
    if (mod && (e.key === 's' || e.key === 'S')) { e.preventDefault(); opts.onSave?.(); return; }
    if (mod && e.key === '/') {
      e.preventDefault();
      mapLines(lines => {
        const all = lines.filter(l => l.trim()).every(l => /^\s*\/\//.test(l));
        return lines.map(l => !l.trim() ? l : all ? l.replace(/^(\s*)\/\/ ?/, '$1') : l.replace(/^(\s*)/, '$1// '));
      });
      return;
    }
    if (e.key === 'Tab') {
      e.preventDefault();
      const multi = ta.value.slice(ta.selectionStart, ta.selectionEnd).includes('\n');
      if (e.shiftKey) mapLines(lines => lines.map(l => l.replace(/^ {1,4}/, '')));
      else if (multi) mapLines(lines => lines.map(l => l ? '    ' + l : l));
      else insert('    ');
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey && !mod) {
      e.preventDefault();
      const v = ta.value, pos = ta.selectionStart;
      const ls = v.lastIndexOf('\n', pos - 1) + 1;
      const indent = /^[ \t]*/.exec(v.slice(ls, pos))[0];
      const before = v.slice(ls, pos).trimEnd();
      const after = v[ta.selectionEnd];
      if (before.endsWith('{') && after === '}') {
        insert('\n' + indent + '    \n' + indent);
        const p = ta.selectionStart - indent.length - 1;
        ta.setSelectionRange(p, p);
      } else {
        insert('\n' + indent + (before.endsWith('{') ? '    ' : ''));
      }
      return;
    }
    if (e.key === '}' && !mod) {
      const v = ta.value, pos = ta.selectionStart;
      const ls = v.lastIndexOf('\n', pos - 1) + 1;
      const head = v.slice(ls, pos);
      if (/^ {4,}$/.test(head) && ta.selectionStart === ta.selectionEnd) {
        e.preventDefault();
        ta.setSelectionRange(pos - 4, pos);
        insert('}');
      }
    }
  });
  paint();
  return {
    node, ta,
    get: () => ta.value,
    set: v => { ta.value = v; paint(); },
    focus: () => ta.focus(),
    mark: lines => { marks = new Set(lines); paint(); },
    goto(line) {
      const lines = ta.value.split('\n');
      let off = 0;
      for (let i = 0; i < Math.min(line - 1, lines.length); i++) off += lines[i].length + 1;
      ta.focus();
      ta.setSelectionRange(off, off + (lines[line - 1] || '').length);
      const lh = parseFloat(getComputedStyle(ta).lineHeight) || 19;
      ta.scrollTop = Math.max(0, (line - 6) * lh);
      sync();
    },
  };
}

// =================================================================== screens
const State = { env: null };

// ---------------------------------------------------------------- today
async function screenToday() {
  const t = await call('today');
  const plan = el('div', { class: 'rows', style: 'margin-top:10px' }, t.plan.map(r => {
    const done = r.state === 'done';
    const node = rowbtn(r.route, r.state === 'active' ? 'on' : '',
      kbd(r.key, r.state === 'active'),
      el('span', { class: (done ? 'done ' : '') + 'name', style: 'width:70px;flex:none' }, r.title),
      el('span', { class: 'label ellipsis ' + (done ? 'faint' : 'muted') }, r.detail),
      el('span', { class: 'grow' }),
      el('span', { class: 'cost' + (done ? ' pass' : '') }, done ? '✓' : '~' + r.minutes + ' min'));
    if (r.route) KEYS[r.key] = () => { location.hash = r.route; };
    return node;
  }));

  const bar = el('div', { class: 'row', style: 'gap:12px;margin:14px 0 4px' },
    el('div', { class: 'bar grow' }, el('span', { style: 'width:' + Math.min(100, 100 * t.minutes / Math.max(1, t.target)) + '%' })),
    el('span', { class: 'small muted nowrap' }, t.minutes + ' of ' + t.target + ' min today'));

  const upcoming = el('div', { class: 'rows' }, t.upcoming.map(u => rowbtn('#/lesson/' + u.id, '',
    el('span', { class: 'dot ' + (u.state === 'ahead' ? 'ahead' : u.state) }),
    el('span', { class: 'id' }, u.id),
    el('span', { class: 'name ellipsis' + (u.state === 'ahead' ? ' muted' : '') }, u.title),
    u.state === 'ahead' ? el('span', { class: 'small faint nowrap' }, 'after ' + u.missing.slice(0, 2).join(', ')) : null,
    el('span', { class: 'grow' }),
    balloonRow(u.balloons),
    el('span', { class: 'cost', style: 'width:92px;text-align:right' },
       u.state === 'started' ? u.answered + '/' + u.questions + ' asked' : '~' + u.minutes + ' min'))));

  const env = State.env;
  const warn = [];
  if (env && !env.compiler.ok) warn.push(el('div', { class: 'warnbox' }, 'No C++ compiler found: ' + env.compiler.error));
  t.warnings.forEach(w => warn.push(el('div', { class: 'warnbox' }, w)));

  const side = [
    heading('solved', t.solved + ' / ' + t.problems, false),
    el('div', { class: 'bar', style: 'margin-top:8px' },
       el('span', { style: 'width:' + (100 * t.solved / Math.max(1, t.problems)) + '%' })),
    heading('due · next 14 days', String(t.forecast.reduce((a, b) => a + b, 0)), false),
    el('div', { style: 'margin-top:8px' }, forecastStrip(t.forecast)),
    t.recent.length ? heading('recent submissions') : null,
    el('div', { class: 'rows subs' }, t.recent.map(s => rowbtn('#/problem/' + s.ref, '',
      el('span', { class: 'vd ' + s.verdict }, s.verdict),
      el('span', { class: 'label ellipsis' }, s.title), el('span', { class: 'grow' }),
      el('span', { class: 'cost' }, whenAgo(s.ts))))),
    t.retention.length ? heading('retention by lesson') : null,
    t.retention.map(r => meter(r.label, r.pct)),
  ];

  const d = new Date();
  const date = d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  show(el('div', { class: 'dense-cols' },
    el('div', { class: 'main' },
      titleline('today', [date, 'day ' + t.day, t.streak ? 'streak ' + t.streak + 'd' : ''].filter(Boolean).join(' · ')),
      warn, bar, plan,
      heading('next lessons', t.learned + ' of ' + t.lessons + ' learned'),
      upcoming,
      el('div', { class: 'row small faint', style: 'gap:18px;margin-top:28px' },
        ['b lessons', 'o problems', 'r review', 's stats', 'g playground', '? about'].map(x => el('span', {}, x)))),
    el('div', { class: 'rule' }),
    el('div', { class: 'side' }, side)), 'dense');
}

// --------------------------------------------------------------- browse
async function screenBrowse() {
  const { tracks } = await call('lessons');
  const out = [titleline('lessons', tracks.reduce((n, t) => n + t.lessons.length, 0) + ' lessons in ' + tracks.length + ' tracks')];
  for (const t of tracks) {
    const learned = t.lessons.filter(l => l.status === 'learned').length;
    out.push(heading(t.name, learned + ' of ' + t.lessons.length + ' learned'));
    out.push(el('p', { class: 'label muted', style: 'margin:8px 0 6px' }, t.blurb));
    out.push(el('div', { class: 'rows' }, t.lessons.map(l => {
      const ahead = l.status === 'new' && l.missing.length > 0;
      return rowbtn('#/lesson/' + l.id, '',
        el('span', { class: 'dot ' + (ahead ? 'ahead' : l.status) }),
        el('span', { class: 'id' }, l.id),
        el('span', { class: 'name ellipsis' + (ahead ? ' muted' : '') }, l.title),
        el('span', { class: 'grow' }),
        l.due ? el('span', { class: 'cost accent' }, l.due + ' due') : null,
        balloonRow(l.balloons),
        el('span', { class: 'cost', style: 'width:118px;text-align:right' },
          l.status === 'new' ? (ahead ? 'after ' + l.missing.slice(0, 2).join(', ') : '~' + l.minutes + ' min')
                             : l.answered + '/' + l.questions + ' · ' + l.solved + '/' + l.problems + ' solved'));
    })));
  }
  show(out);
}

// --------------------------------------------------------------- lesson
const KIND_LABEL = { mcq: 'choose', numeric: 'estimate', short: 'answer', reflect: 'think it through', try: 'now solve it' };

async function screenLesson(id) {
  const d = await call('lesson', { id });
  const L = d.lesson;
  const ctx = { id: L.id, reached: d.reached, total: d.total, nodes: new Map(), partShown: new Set(), d };
  const dlg = el('div', { class: 'dialogue book' });
  ctx.dlg = dlg;

  const outline = el('div', { class: 'outline' });
  ctx.outline = outline;
  const tail = el('div');
  ctx.tail = tail;

  for (const v of d.steps) appendStep(ctx, v, false);
  renderOutline(ctx);
  renderTail(ctx);

  const probList = el('div', { class: 'rows' }, d.problems.map(p => rowbtn('#/problem/' + p.ref, '',
    balloonSvg(p.color, p.solved),
    el('span', { class: 'label ellipsis' }, p.title), el('span', { class: 'grow' }),
    el('span', { class: 'cost' }, p.solved ? '✓' : p.difficulty))));

  const side = el('div', { class: 'side sticky' },
    heading('outline', d.parts.length + ' parts', false),
    el('div', { style: 'margin-top:6px' }, outline),
    heading('problems', d.problems.filter(p => p.solved).length + '/' + d.problems.length, false),
    el('div', { style: 'margin-top:4px' }, probList),
    d.prereqs.length ? heading('builds on', '', false) : null,
    d.prereqs.length ? el('div', { class: 'small', style: 'margin-top:4px' }, d.prereqs.map(p =>
      el('div', {}, el('a', { href: '#/lesson/' + p.id, class: p.done ? 'pass' : 'muted' },
        p.id + ' ' + p.title + (p.done ? ' ✓' : ''))))) : null,
    d.unlocks.length ? heading('opens up', '', false) : null,
    d.unlocks.length ? el('div', { class: 'small muted', style: 'margin-top:4px' },
      d.unlocks.map(u => el('div', {}, el('a', { href: '#/lesson/' + u.id }, u.id + ' ' + u.title)))) : null,
    el('div', { style: 'margin-top:26px' }, el('button', { class: 'bare small', onclick: async () => {
      if (!twice('lesson', 'Click again to clear your answers in this lesson (solved problems stay solved).')) return;
      await post('lesson_reset', { id: L.id });
      route();
    } }, 'restart this dialogue')));

  show(el('div', { class: 'dense-cols' },
    el('div', { class: 'main' },
      titleline(L.title, L.id + ' · ' + plural(L.parts, 'part') + ' · ' + plural(L.questions, 'question') +
                ' · ' + plural(L.problems, 'problem')),
      el('p', { class: 'label muted', style: 'margin:6px 0 0' }, L.summary),
      dlg, tail),
    el('div', { class: 'rule' }), side), 'dense');

  // resume where the learner left off
  const cur = ctx.nodes.get(Math.min(d.reached, d.total - 1));
  if (cur && d.reached > 0) setTimeout(() => cur.scrollIntoView({ block: 'center' }), 30);
  bindLessonKeys(ctx);
}

// Destructive buttons want a second click within 3 s instead of a modal dialog.
let armed = { what: '', at: 0 };
function twice(what, msg) {
  if (armed.what === what && Date.now() - armed.at < 3000) { armed = { what: '', at: 0 }; return true; }
  armed = { what, at: Date.now() };
  flash(msg);
  return false;
}

function renderOutline(ctx) {
  const d = ctx.d;
  const reachedPart = ctx.reached < ctx.total ? stepPart(ctx, ctx.reached) : -1;
  ctx.outline.replaceChildren(...d.parts.map((p, i) => el('a', {
    href: '#', class: (p.open ? '' : 'closed') + (i === reachedPart ? ' cur' : '') + (p.gates && p.done >= p.gates ? ' full' : ''),
    onclick: e => { e.preventDefault(); document.getElementById('part-' + i)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); },
  }, el('span', { class: 'n' }, i + 1), el('span', { class: 'ellipsis', html: inline(p.title) }),
     el('span', { class: 'c' }, p.done + '/' + p.gates))));
}
function stepPart(ctx, k) {
  const parts = ctx.d.parts;
  for (let i = parts.length - 1; i >= 0; i--) if (k >= parts[i].first) return i;
  return 0;
}

function appendStep(ctx, v, fresh) {
  if (!ctx.partShown.has(v.part)) {
    ctx.partShown.add(v.part);
    ctx.dlg.append(el('div', { class: 'part-title', id: 'part-' + v.part, style: 'scroll-margin-top:70px' },
      el('span', { class: 'n' }, String(v.part + 1).padStart(2, '0')),
      el('h2', { html: inline(ctx.d.parts[v.part].title) })));
  }
  const node = renderStep(ctx, v);
  if (fresh) node.classList.add('fresh');
  node.style.scrollMarginTop = '70px';
  const old = ctx.nodes.get(v.k);
  if (old) old.replaceWith(node); else ctx.dlg.append(node);
  ctx.nodes.set(v.k, node);
  return node;
}

// After an answer: re-render the step, append what unfolded, update outline and tail.
function applyAdvance(ctx, res) {
  appendStep(ctx, res.step, false);
  let first = null;
  for (const v of res.unfolded || []) {
    if (ctx.nodes.has(v.k) && v.k !== res.reached) { appendStep(ctx, v, false); continue; }
    const n = appendStep(ctx, v, true);
    if (!first) first = n;
  }
  const grew = res.reached !== ctx.reached;
  ctx.reached = res.reached;
  // refresh the outline counts cheaply from the lesson view
  if (grew) {
    call('lesson', { id: ctx.id }).then(d => { ctx.d.parts = d.parts; renderOutline(ctx); if (res.finished) { ctx.d = Object.assign(ctx.d, d); renderTail(ctx); } });
  }
  if (res.learned) flash('Lesson learned ✓');
  // keep the answer's explanation in view; what unfolded below is one scroll away
  const answered = ctx.nodes.get(res.step.k);
  const target = (answered && answered.querySelector('.feedback, .why:last-of-type')) || first;
  if (target) setTimeout(() => target.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 60);
  bindLessonKeys(ctx);
}

function bindLessonKeys(ctx) {
  KEYS = {};
  const cur = ctx.nodes.get(ctx.reached);
  if (!cur) return;
  const opts = cur.querySelectorAll('button.opt:not(:disabled)');
  opts.forEach((b, i) => {
    KEYS[String(i + 1)] = () => b.click();
    KEYS['abcdefgh'[i]] = () => b.click();
  });
  const input = cur.querySelector('input[type=text], textarea');
  if (input) KEYS['Enter'] = () => input.focus();
  const open = cur.querySelector('a.pill.prominent-link');
  if (open) KEYS['Enter'] = () => open.click();
}

function renderStep(ctx, v) {
  if (v.kind === 'say') return el('div', { class: 'say', 'data-k': v.k }, prose(v.blocks));
  if (v.kind === 'try') return renderTry(ctx, v);
  const box = el('div', { class: 'ask' + (v.done ? ' done' : ''), 'data-k': v.k });
  const tools = el('span', { class: 'tools' });
  if (!v.done && v.has_hint && !v.hint)
    tools.append(el('button', { class: 'bare small', onclick: async () => {
      const r = await post('hint_step', { lesson: ctx.id, k: v.k });
      appendStep(ctx, r.step, false);
      bindLessonKeys(ctx);
    } }, 'hint'));
  if (!v.done && v.kind !== 'reflect')
    tools.append(el('button', { class: 'bare small', title: 'Mark this one as shown and move on', onclick: async () => {
      const r = await post('reveal', { lesson: ctx.id, k: v.k });
      applyAdvance(ctx, r);
    } }, v.tries ? 'show me' : 'skip · show me'));
  box.append(el('div', { class: 'askhead' }, el('span', { class: 'kind' }, KIND_LABEL[v.kind] || v.kind), tools));
  box.append(el('div', { class: 'qtext' }, prose(v.q)));

  if (v.kind === 'mcq') box.append(renderMCQ(ctx, v));
  else if (v.kind === 'numeric' || v.kind === 'short') box.append(renderTyped(ctx, v));
  else if (v.kind === 'reflect') box.append(renderReflect(ctx, v));

  if (v.hint && !v.done) box.append(el('div', { class: 'hintbox' }, el('span', { class: 'small faint' }, 'hint'), prose(v.hint)));
  if (v.done && v.kind !== 'reflect') {
    const fb = el('div', { class: 'feedback' });
    const n = v.tries;
    fb.append(el('div', { class: 'verdictline ' + (v.revealed ? 'faint' : 'pass') },
      v.revealed ? 'shown' : n <= 1 ? '✓ first try' : '✓ after ' + n + ' tries'));
    if (v.answer && v.answer.length) fb.append(prose(v.answer));
    if (v.explain && v.explain.length) fb.append(prose(v.explain));
    if (fb.childNodes.length > 1 || v.revealed) box.append(fb);
  }
  return box;
}

function renderMCQ(ctx, v) {
  const list = el('div', { class: 'options' });
  const picked = new Map((v.picked || []).map(p => [p.i, p]));
  const right = new Set(v.right || []);
  v.options.forEach((text, i) => {
    const p = picked.get(i);
    let cls = 'opt';
    if (p && !p.correct) cls += ' wrong';
    if ((p && p.correct) || (v.done && right.has(i))) cls += ' right';
    if (v.done && !p && !right.has(i)) cls += ' dim';
    const b = el('button', { class: cls, disabled: v.done || (p && !p.correct), onclick: async () => {
      b.disabled = true;
      try {
        const r = await post('answer', { lesson: ctx.id, k: v.k, response: i });
        applyAdvance(ctx, r);
      } catch (e) { flash(e.message); b.disabled = false; }
    } }, el('span', { class: 'letter' }, 'ABCDEFGH'[i]), el('span', { html: inline(text) }));
    list.append(b);
    if (p && p.why && p.why.length) list.append(el('div', { class: 'why' + (p.correct ? ' ok' : '') }, prose(p.why)));
  });
  return list;
}

function renderTyped(ctx, v) {
  const wrap = el('div');
  const tries = el('div', { class: 'tries' }, (v.responses || []).map(r => el('div', { class: 'try-row' },
    el('span', { class: 'mark ' + (r.correct ? 'pass' : 'fail') }, r.correct ? '✓' : '✗'),
    el('span', { class: 'given' }, r.text),
    r.feedback && r.feedback.length ? el('span', { class: 'muted' }, prose(r.feedback)) : null)));
  if (!v.done) {
    const input = el('input', { type: 'text', placeholder: v.placeholder || (v.kind === 'numeric' ? 'a number: 2e5, 4*10^10, 2^20 ...' : 'your answer'),
                                autocomplete: 'off', spellcheck: 'false' });
    const msg = el('div', { class: 'small fail', style: 'margin-top:6px' });
    const go = async () => {
      if (!input.value.trim()) { input.focus(); return; }
      btn.disabled = true;
      try {
        const r = await post('answer', { lesson: ctx.id, k: v.k, response: input.value });
        if (r.result && r.result.invalid) {
          msg.replaceChildren(prose(r.result.feedback));
          btn.disabled = false;
          input.focus();
          return;
        }
        applyAdvance(ctx, r);
        if (!r.result.correct) {
          const node = ctx.nodes.get(v.k);
          const inp = node && node.querySelector('input[type=text]');
          if (inp) inp.focus();
        }
      } catch (e) { flash(e.message); btn.disabled = false; }
    };
    const btn = el('button', { class: 'prominent', onclick: go }, 'check');
    input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); go(); } });
    wrap.append(el('div', { class: 'answerline' }, input, v.unit ? el('span', { class: 'unit' }, v.unit) : null, btn), msg);
  }
  if ((v.responses || []).length) wrap.append(tries);
  return wrap;
}

function renderReflect(ctx, v) {
  const wrap = el('div', { class: 'reflect' });
  if (!v.done) {
    const ta = el('textarea', { class: 'plain', placeholder: 'Write your idea in a sentence or two, then compare with the tutor.' });
    const go = async text => {
      const r = await post('reflect', { lesson: ctx.id, k: v.k, text });
      applyAdvance(ctx, r);
    };
    ta.addEventListener('keydown', e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); go(ta.value); } });
    wrap.append(ta, el('div', { class: 'row', style: 'margin-top:8px' },
      el('button', { class: 'prominent', onclick: () => go(ta.value) }, 'compare with the tutor'),
      el('span', { class: 'small faint' }, MOD + '↵'),
      el('span', { class: 'grow' }),
      el('button', { class: 'bare small', onclick: () => go('') }, 'no idea yet · show me')));
    return wrap;
  }
  wrap.append(el('div', { class: 'small faint' }, 'you wrote'),
    el('div', { class: 'mine' }, v.mine || '(nothing: you asked to see it)'),
    el('div', { class: 'small faint' }, 'the tutor'),
    prose(v.answer));
  const rate = el('div', { class: 'selfrate' }, el('span', { class: 'small faint' }, 'your version:'),
    [['got', 'had it'], ['partly', 'partly'], ['missed', 'missed it']].map(([k, label]) =>
      el('button', { class: v.self === k ? 'on' : '', onclick: async () => {
        const r = await post('reflect_self', { lesson: ctx.id, k: v.k, self: k });
        appendStep(ctx, r.step, false);
      } }, label)));
  wrap.append(rate);
  return wrap;
}

function renderTry(ctx, v) {
  const box = el('div', { class: 'ask trystep' + (v.done ? ' done' : ''), 'data-k': v.k });
  box.append(el('div', { class: 'askhead' }, el('span', { class: 'kind' }, 'now solve it')));
  const status = v.solved ? el('span', { class: 'pass label' }, '✓ solved')
    : v.skipped ? el('span', { class: 'faint label' }, 'skipped for now: it waits in the problem list')
    : v.submits ? el('span', { class: 'muted label' }, plural(v.submits, 'submission') + ' so far') : null;
  box.append(el('div', { class: 'trycard' },
    balloonSvg(ctx.d.problems.find(p => p.ref === v.ref)?.color || '#888', v.solved, 16),
    el('a', { class: 'ptitle', href: '#/problem/' + v.ref }, v.title),
    el('span', { class: 'small faint' }, v.difficulty),
    el('span', { class: 'grow' }),
    status,
    el('a', { class: 'pill prominent-link', href: '#/problem/' + v.ref,
              style: v.done ? '' : 'background:var(--accent);color:var(--on-accent);border-color:var(--accent)' },
      v.solved ? 'open' : 'open problem →'),
    !v.done ? el('button', { onclick: async () => {
      const r = await post('try_skip', { lesson: ctx.id, k: v.k });
      applyAdvance(ctx, r);
    } }, 'later') : null));
  if (v.note && v.note.length) box.append(el('div', { style: 'margin-top:8px' }, prose(v.note)));
  return box;
}

function renderTail(ctx) {
  const d = ctx.d;
  if (ctx.reached < ctx.total) { ctx.tail.replaceChildren(); return; }
  const unsolved = d.problems.filter(p => !p.solved && !p.gave_up);
  const nodes = [el('div', { class: 'endcap' },
    el('div', { class: 'row' }, el('h2', { style: 'margin:0' }, 'End of the dialogue'), el('span', { class: 'grow' }),
      d.next ? el('a', { class: 'pill', href: '#/lesson/' + d.next.id }, 'next: ' + d.next.id + ' ' + d.next.title + ' →') : null),
    el('p', { class: 'label muted', style: 'margin:8px 0 0' },
      unsolved.length ? 'Still open: ' + unsolved.map(p => p.title).join(', ') + '. The lesson counts as learned when each is solved (or its editorial read).'
                      : 'Every problem here is solved or read. Rate the cards below; they come back in review.'))];
  if (d.cards.length) {
    nodes.push(heading('cards to remember', d.cards.filter(c => c.seen).length + ' of ' + d.cards.length + ' scheduled'));
    d.cards.forEach(c => nodes.push(cardNode(c)));
  }
  ctx.tail.replaceChildren(...nodes);
}

function cardNode(c) {
  const answer = el('div', { hidden: true, style: 'margin-top:8px' }, prose(c.a));
  const state = el('span', { class: 'cost' }, c.seen ? (c.is_due ? 'due' : 'next ' + shortDate(c.due)) : 'new');
  const labels = ['again', 'hard', 'good', 'easy'];
  const rate = el('div', { class: 'row', hidden: true, style: 'margin-top:10px' },
    el('span', { class: 'small faint', style: 'margin-right:4px' }, 'how well did you know it?'),
    labels.map((label, i) => el('button', { onclick: async () => {
      const res = await post('grade_card', { lesson: c.lesson, item: c.item, rating: i + 1 });
      flash('next review in ' + plural(res.interval, 'day'));
      state.textContent = 'next ' + shortDate(res.due);
      rate.hidden = true;
    } }, label, el('span', { class: 'shortcut' }, (c.intervals[i] || 0) + 'd'))));
  const reveal = el('button', { onclick: () => { answer.hidden = false; rate.hidden = false; reveal.hidden = true; } }, 'show answer');
  return el('section', { class: 'block cardq' }, prose(c.q),
    el('div', { class: 'row', style: 'margin-top:8px' }, reveal, el('span', { class: 'grow' }), state), answer, rate);
}

// -------------------------------------------------------------- problem
// The editor, the buttons, custom input and the verdicts: shared by practice and
// contest.  In a contest, hidden tests say only their verdict and custom input runs
// your program alone (the reference would be an oracle).
function judgePanel(d, ref, opts = {}) {
  let dirty = false, saveTimer = null, busy = false;
  const doSave = async quiet => {
    clearTimeout(saveTimer);
    if (!dirty) { if (!quiet) flash('saved'); return; }
    dirty = false;
    try { await post('code_save', { ref, code: ed.get() }); if (!quiet) flash('saved to ' + d.path); }
    catch (e) { flash('could not save: ' + e.message); }
  };
  const ed = makeEditor(d.code, {
    onChange: () => { dirty = true; clearTimeout(saveTimer); saveTimer = setTimeout(() => doSave(true), 1500); },
    onSubmit: () => submit('submit'), onRun: () => submit('samples'), onSave: () => doSave(false),
  });
  // unsaved edits are written when leaving the screen or closing the tab
  State.flush = () => { if (dirty) doSave(true); };
  window.onbeforeunload = () => {
    if (!dirty) return;
    fetch('/api/code_save', { method: 'POST', keepalive: true, headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ ref, code: ed.get() }) });
  };

  const results = el('div', { 'aria-live': 'polite' });
  const subBtn = el('button', { class: 'prominent', onclick: () => submit('submit') }, 'submit', el('span', { class: 'shortcut' }, MOD + '↵'));
  const runBtn = el('button', { onclick: () => submit('samples') }, 'run samples', el('span', { class: 'shortcut' }, MOD + "'"));

  async function submit(mode) {
    if (busy) return;
    busy = true;
    subBtn.disabled = runBtn.disabled = true;
    clearTimeout(saveTimer);
    dirty = false;
    const t0 = Date.now();
    const banner = el('div', { class: 'verdict running' }, el('span', { class: 'big' }, mode === 'submit' ? 'judging…' : 'running samples…'),
                      el('span', { class: 'sub' }, 'compiling'));
    const tick = setInterval(() => { banner.lastChild.textContent = ((Date.now() - t0) / 1000).toFixed(1) + ' s'; }, 100);
    results.replaceChildren(banner);
    try {
      const r = await post('run', { ref, code: ed.get(), mode, contest: !!opts.contest });
      clearInterval(tick);
      renderResult(r, mode);
    } catch (e) {
      clearInterval(tick);
      results.replaceChildren(el('p', { class: 'err' }, e.message));
    } finally {
      busy = false;
      subBtn.disabled = runBtn.disabled = false;
    }
  }

  function renderResult(r, mode) {
    const res = r.result;
    const nodes = [];
    const v = res.verdict;
    let title = VERDICT_NAME[v] || v;
    if (v !== 'AC' && v !== 'CE' && res.failed) title += ' on ' + res.failed;
    if (mode === 'samples' && v === 'AC') title = 'Samples pass';
    const sub = v === 'CE' ? 'fix the first error; the rest often follow from it'
      : res.passed + ' / ' + (mode === 'submit' && v !== 'AC' ? res.total + ' passed, stopped at the first failure' : res.total + ' passed') +
        ' · max ' + res.max_ms + ' ms of ' + (res.time_limit * 1000) + ' · ' + (res.max_kb / 1024).toFixed(1) + ' MB';
    nodes.push(el('div', { class: 'verdict ' + v }, el('span', { class: 'big' }, title), el('span', { class: 'sub' }, sub)));
    if (mode === 'samples' && v === 'AC') nodes.push(el('p', { class: 'small muted', style: 'margin:0 0 6px' }, 'Samples are only the start. Submit to run the hidden tests.'));

    if (v === 'CE') {
      const lines = new Set();
      const pre = el('pre', { class: 'compile' });
      pre.innerHTML = esc(res.compile).replace(/main\.cpp:(\d+):(\d+)/g, (m, ln) => { lines.add(+ln); return '<a data-line="' + ln + '">' + m + '</a>'; });
      pre.querySelectorAll('a').forEach(a => a.onclick = () => ed.goto(+a.dataset.line));
      ed.mark([...lines]);
      nodes.push(pre);
    } else {
      ed.mark([]);
      const detail = el('div');
      const chips = el('div', { class: 'chips' });
      const showCase = c => {
        chips.querySelectorAll('.chip').forEach(x => x.classList.toggle('sel', x.dataset.name === c.name));
        detail.replaceChildren(caseNode(c));
      };
      res.cases.forEach(c => chips.append(el('button', { class: 'chip ' + c.verdict, 'data-name': c.name,
        title: c.name + ': ' + c.verdict + ' · ' + c.ms + ' ms', onclick: () => showCase(c) })));
      for (let i = res.cases.length; i < res.total; i++) chips.append(el('span', { class: 'chip skip', title: 'not run: judging stops at the first failure' }));
      nodes.push(chips, detail);
      const firstBad = res.cases.find(c => c.verdict !== 'AC');
      if (firstBad) showCase(firstBad);
      else if (mode === 'samples' && res.cases.length) showCase(res.cases[0]);
    }
    if (res.warnings) nodes.push(el('details', { style: 'margin-top:10px' },
      el('summary', { class: 'small muted' }, 'compiler warnings'), el('pre', { class: 'compile' }, res.warnings)));
    if (mode === 'submit' && v === 'AC' && (r.first_ac || (r.contest && opts.contest))) floatBalloon(d.color);
    if (opts.onResult) nodes.push(...[].concat(opts.onResult(r, mode) || []));
    fill(results, nodes);
  }

  function caseNode(c) {
    const cls = c.verdict === 'AC' ? 'ok' : c.verdict === 'TLE' ? 'slow' : '';
    const n = el('div', { class: 'case ' + cls });
    n.append(el('div', { class: 'ch' }, el('span', { class: 'vd ' + c.verdict }, c.verdict),
      el('b', { style: 'font-weight:500' }, c.name), c.gen ? el('span', { class: 'faint small' }, c.gen) : null,
      el('span', { class: 'faint small' }, c.ms + ' ms'), el('span', { class: 'grow' })));
    if (c.hidden) {
      if (c.verdict !== 'AC') n.append(el('div', { class: 'small muted' }, 'A hidden test. In a contest that is all the judge says: find the case yourself (edge cases, the limits, overflow, a brute force to compare against).'));
      return n;
    }
    if (c.message) n.append(el('div', { class: 'msg ' + (c.verdict === 'TLE' ? 'slow' : 'fail') }, c.message));
    if (c.note && c.note.length && c.verdict !== 'AC') n.append(el('div', { class: 'small muted', style: 'margin-bottom:6px' }, prose(c.note)));
    if (c.input) {
      n.append(el('div', { class: 'grid three' },
        el('div', {}, el('div', { class: 'k' }, 'input'), el('pre', {}, c.input)),
        el('div', {}, el('div', { class: 'k' }, 'expected'), el('pre', {}, c.expected || '')),
        el('div', {}, el('div', { class: 'k' }, 'your output'), el('pre', {}, c.got || ''))));
    } else if (c.verdict !== 'AC') {
      n.append(el('div', { class: 'small muted' }, 'This hidden test is large (' + Math.round((c.input_size || 0) / 1024) + ' KB of input), so it is not shown. ' +
        (c.verdict === 'TLE' ? 'A time limit on a large test usually means the complexity, not a constant factor, is the problem.' : 'Test your program on big random inputs against a brute force.')));
      if (c.got) n.append(el('div', { style: 'margin-top:6px' }, el('div', { class: 'k small faint' }, 'start of your output'), el('pre', { class: 'box' }, c.got)));
    }
    if (c.stderr) n.append(el('div', { style: 'margin-top:8px' }, el('div', { class: 'k small faint' }, 'stderr'), el('pre', { class: 'box' }, c.stderr)));
    return n;
  }

  // ---- custom input
  const stdin = el('textarea', { class: 'plain mono', style: 'width:100%;min-height:90px;font-size:12.5px', spellcheck: 'false' });
  stdin.value = d.samples[0] ? d.samples[0].input : '';
  const customOut = el('div');
  const customRun = async () => {
    customOut.replaceChildren(el('p', { class: 'small faint' }, 'running…'));
    try {
      const r = await post('custom', { ref, code: ed.get(), input: stdin.value, contest: !!opts.contest });
      customOut.replaceChildren(customNode(r));
    } catch (e) { customOut.replaceChildren(el('p', { class: 'err' }, e.message)); }
  };
  stdin.addEventListener('keydown', e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); customRun(); } });
  const customBox = el('div', { hidden: true, style: 'margin-top:12px' },
    el('div', { class: 'row small faint', style: 'margin-bottom:4px' },
      opts.contest ? 'your input (in a contest there is no reference to compare with)' : 'your input (the reference solution runs on it too)'),
    stdin, el('div', { class: 'row', style: 'margin-top:6px' }, el('button', { onclick: customRun }, 'run on this input', el('span', { class: 'shortcut' }, MOD + '↵'))),
    customOut);

  function customNode(r) {
    if (r.verdict === 'CE') return el('pre', { class: 'compile' }, r.compile);
    const same = r.matches;
    const hasRef = r.reference != null || r.reference_error;
    return el('div', { class: 'case ' + (r.verdict !== 'AC' ? 'slow' : same === false ? '' : 'ok') },
      el('div', { class: 'ch' }, el('span', { class: 'vd ' + r.verdict }, r.verdict), el('span', { class: 'faint small' }, r.ms + ' ms'),
        same === true ? el('span', { class: 'pass small' }, 'matches the reference') :
        same === false ? el('span', { class: 'fail small' }, 'differs from the reference') : null),
      r.message ? el('div', { class: 'msg fail' }, r.message) : null,
      el('div', { class: hasRef ? 'grid' : '' },
        el('div', {}, el('div', { class: 'k' }, 'your output'), el('pre', {}, r.stdout || '')),
        hasRef ? el('div', {}, el('div', { class: 'k' }, 'reference output'), el('pre', {}, r.reference != null ? r.reference : r.reference_error)) : null),
      r.stderr ? el('div', { style: 'margin-top:6px' }, el('div', { class: 'k' }, 'stderr'), el('pre', {}, r.stderr)) : null);
  }

  const customToggle = el('button', { onclick: () => { customBox.hidden = !customBox.hidden; customToggle.classList.toggle('passbtn', !customBox.hidden); if (!customBox.hidden) stdin.focus(); } }, 'custom input');
  const node = el('div', { class: 'work' },
    ed.node,
    el('div', { class: 'toolbar' }, subBtn, runBtn, customToggle,
      el('button', { class: 'bare small', onclick: async () => {
        if (!twice('code', 'Click again to replace your code with the starter.')) return;
        const r = await post('code_reset', { ref }); ed.set(r.code); dirty = false;
      } }, 'reset'),
      el('span', { class: 'where ellipsis', title: d.path }, 'also at ' + d.path.replace(/^.*\/workspace\//, 'workspace/'))),
    customBox, results);

  KEYS = { e: () => ed.focus() };
  MODKEYS = { Enter: e => submit(e.shiftKey ? 'samples' : 'submit'), "'": () => submit('samples'),
              s: () => doSave(false) };
  return { node, ed, submit };
}

function sampleNodes(d) {
  return d.samples.map((s, i) => el('div', {},
    el('div', { class: 'sample' },
      el('div', { class: 'io' }, el('div', { class: 'k' }, 'sample input ' + (i + 1), el('button', { onclick: () => { navigator.clipboard?.writeText(s.input); flash('copied'); } }, 'copy')), el('pre', {}, s.input)),
      el('div', { class: 'io' }, el('div', { class: 'k' }, 'sample output ' + (i + 1)), el('pre', {}, s.output))),
    s.note && s.note.length ? el('div', { class: 'small muted', style: 'margin:-6px 0 12px' }, prose(s.note)) : null));
}

async function screenProblem(ref) {
  const d = await call('problem', { ref });

  const hintBox = el('div');
  const renderHints = hs => hintBox.replaceChildren(...hs.map((h, i) => el('div', { class: 'block' }, heading('hint ' + (i + 1), '', false), prose(h))));
  renderHints(d.hints);
  const hintBtn = el('button', { onclick: async () => {
    const r = await post('hint', { ref });
    renderHints(r.hints);
    hintBtn.textContent = r.hints.length < r.total ? 'hint ' + (r.hints.length + 1) + ' of ' + r.total : 'no more hints';
    hintBtn.disabled = r.hints.length >= r.total;
  } }, d.hints.length < d.hints_total ? 'hint ' + (d.hints.length + 1) + ' of ' + d.hints_total : 'no more hints');
  hintBtn.disabled = d.hints.length >= d.hints_total;

  const editorialBox = el('div', { class: 'editorial' });
  function renderEditorial(text, sol) {
    editorialBox.replaceChildren(heading('editorial'), prose(text),
      el('details', { style: 'margin-top:10px' }, el('summary', { class: 'small muted' }, 'reference solution'),
        el('div', { class: 'prose' }, codeBlock(sol, 'cpp'))));
  }
  async function loadEditorial(giveUp) {
    const r = giveUp ? await post('editorial', { ref }) : await call('problem', { ref });
    if (r.editorial) renderEditorial(r.editorial, r.solution);
    if (giveUpBtn) giveUpBtn.remove();
  }
  if (d.editorial) renderEditorial(d.editorial, d.solution);
  const giveUpBtn = d.editorial ? null : el('button', { class: 'bare small', onclick: async () => {
    if (!twice('editorial', 'Click again to read the editorial. The next review of this problem will treat it as not solved alone.')) return;
    await loadEditorial(true);
  } }, 'read the editorial (counts as giving up this time)');

  const subsHead = heading('your submissions');
  const subsBox = el('div', { class: 'rows subs' });
  const drawSubs = subs => {
    subsBox.replaceChildren(...subs.map(s => rowbtn(null, 'off',
      el('span', { class: 'vd ' + s.verdict }, s.verdict),
      el('span', { class: 'small muted' }, s.failed ? 'on ' + s.failed : s.passed + '/' + s.total),
      el('span', { class: 'grow' }), el('span', { class: 'cost' }, s.ms + ' ms · ' + whenAgo(s.ts)))));
    subsHead.hidden = !subs.length;
  };
  drawSubs(d.submissions);

  const headerBalloon = el('span');
  const statusLine = el('span', { class: 'small' });
  function updateHeader(st) {
    headerBalloon.replaceChildren(balloonSvg(d.color, st.solved, 18));
    statusLine.className = 'small ' + (st.solved ? 'pass' : 'faint');
    statusLine.textContent = st.solved ? 'solved' : st.submits ? plural(st.submits, 'submission') : '';
  }
  updateHeader(d);

  function gradeBox() {
    const box = el('div', { style: 'margin-top:16px' },
      heading('how did that solve feel?', 'schedules when you re-solve it from scratch'),
      el('div', { class: 'row', style: 'margin-top:8px' },
        [[1, 'hard'], [2, 'good'], [3, 'easy']].map(([feel, label]) => el('button', { onclick: async () => {
          const res = await post('grade_problem', { ref, feel });
          flash('re-solve in ' + plural(res.interval, 'day'));
          d.graded = true;
          box.replaceChildren(el('p', { class: 'small pass' }, 'Scheduled: re-solve on ' + shortDate(res.due) + '.'));
        } }, label))));
    return box;
  }

  const panel = judgePanel(d, ref, {
    onResult(r, mode) {
      if (r.state) updateHeader(r.state);
      if (mode !== 'submit') return [];
      call('problem', { ref }).then(p => drawSubs(p.submissions));
      if (r.result.verdict !== 'AC') return [];
      if (r.learned) flash('Lesson learned ✓');
      loadEditorial(false);
      if (!d.graded || (r.srs && r.srs.is_due)) return [gradeBox()];
      return [el('p', { class: 'small muted' }, 'Scheduled: the next re-solve is on ' + shortDate(r.srs.due) + '.')];
    },
  });

  const left = el('div', { class: 'statement' },
    el('div', { class: 'row small', style: 'gap:8px;margin-bottom:10px' },
      el('a', { class: 'muted', href: '#/lesson/' + d.lesson }, d.lesson + ' · ' + d.lesson_title),
      el('span', { class: 'grow' }),
      d.siblings.map(s => el('a', { href: '#/problem/' + s.ref, title: s.title, style: s.ref === ref ? 'outline:1px solid var(--hairline);outline-offset:3px;border-radius:3px' : '' }, balloonSvg(s.color, s.solved)))),
    el('div', { class: 'titleline' }, headerBalloon, el('h1', {}, d.title), statusLine),
    el('div', { class: 'limits' },
      el('span', {}, 'time limit ' + d.time_limit + ' s'), el('span', {}, d.difficulty),
      d.source ? el('span', {}, d.source) : null,
      d.solved && d.complexity ? el('span', {}, 'target ' + d.complexity) : null),
    el('div', { class: 'book' }, prose(d.statement)),
    heading('input'), el('div', { class: 'book' }, prose(d.input)),
    heading('output'), el('div', { class: 'book' }, prose(d.output)),
    heading('samples'), sampleNodes(d),
    el('div', { class: 'row', style: 'margin-top:16px' }, d.hints_total ? hintBtn : null, el('span', { class: 'grow' }), giveUpBtn),
    hintBox, editorialBox, subsHead, subsBox);

  show(splitCols(left, panel.node, 'cp.split'), 'wide');
}

// -------------------------------------------------------------- contest
const fmtClock = s => {
  s = Math.max(0, Math.round(s));
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), sec = s % 60;
  return h + ':' + String(m).padStart(2, '0') + ':' + String(sec).padStart(2, '0');
};

// A countdown that re-renders the screen when time runs out.
function contestClock(c, node) {
  const end = Date.now() + c.remaining * 1000;
  const draw = () => {
    const left = (end - Date.now()) / 1000;
    node.textContent = fmtClock(left);
    node.classList.toggle('fail', left < 600);
    if (left <= 0) { clearInterval(State.timer); State.timer = null; route(); }
  };
  draw();
  State.timer = setInterval(draw, 1000);
}

function scoreCell(r) {
  if (r.solved) return el('span', { class: 'pass mono' }, '+' + (r.wrong || '') + ' ', el('span', { class: 'faint' }, r.minute + '′'));
  if (r.wrong) return el('span', { class: 'fail mono' }, '−' + r.wrong);
  return el('span', { class: 'faint mono' }, '·');
}

function scoreboard(c, clickable) {
  return el('div', { class: 'rows' }, c.rows.map(r => rowbtn(clickable ? '#/contest/' + r.letter : (r.lesson ? '#/problem/' + r.ref : null), clickable ? '' : 'off',
    el('span', { class: 'mono', style: 'width:18px;font-weight:600' }, r.letter),
    balloonSvg(r.color, r.solved, 12),
    el('span', { class: 'name ellipsis' }, r.title),
    r.lesson ? el('span', { class: 'small faint ellipsis', style: 'max-width:280px' }, r.lesson + ' ' + r.lesson_title + ' · ' + r.difficulty) : null,
    el('span', { class: 'grow' }),
    r.last && !r.solved ? el('span', { class: 'vd ' + r.last, style: 'width:auto' }, r.last) : null,
    el('span', { style: 'width:70px;text-align:right' }, scoreCell(r)))));
}

async function screenContest() {
  const s = await call('contest');
  const c = s.active;
  if (c) {
    const clock = el('span', { class: 'mono', style: 'font-size:25px' });
    contestClock(c, clock);
    show([
      el('div', { class: 'titleline' }, el('h1', {}, 'contest #' + c.id), clock),
      el('div', { class: 'figures', style: 'margin-top:14px' }, figure(c.solved + ' / ' + c.rows.length, 'solved'),
        figure(c.penalty, 'penalty minutes'), figure(Math.floor(c.elapsed / 60) + '′', 'elapsed of ' + c.minutes + '′')),
      heading('problems', 'the order says nothing about difficulty'),
      scoreboard(c, true),
      el('p', { class: 'small muted', style: 'margin-top:18px' },
        'No hints, no editorials, no lesson names: recognising the technique is the skill. Hidden tests report only their verdict. ' +
        'Each rejected submission on a problem you later solve costs 20 minutes; compilation errors cost nothing.'),
      el('div', { class: 'row', style: 'margin-top:14px' }, el('button', { class: 'bare small', onclick: async () => {
        if (!twice('endcontest', 'Click again to end the contest now.')) return;
        await post('contest_end'); route();
      } }, 'end the contest now')),
    ]);
    c.rows.forEach(r => { KEYS[r.letter.toLowerCase()] = () => { location.hash = '#/contest/' + r.letter; }; });
    return;
  }

  const choice = { minutes: 120, count: 6, pool: 'studied' };
  const seg = (key, options) => el('div', { class: 'row', style: 'gap:6px' }, options.map(([v, label]) => {
    const b = el('button', { class: choice[key] === v ? 'passbtn' : '', onclick: () => {
      choice[key] = v;
      b.parentNode.querySelectorAll('button').forEach(x => x.classList.toggle('passbtn', x === b));
    } }, label);
    return b;
  }));
  const last = s.last;
  show([
    titleline('virtual contest', s.past.length ? plural(s.past.length, 'contest') + ' so far' : 'ICPC rules, against the clock'),
    el('div', { class: 'book' }, prose([{ type: 'paragraph', text: 'A set of problems in random order, labelled A, B, C..., a clock, and ICPC scoring: most problems solved wins; ties are broken by penalty, the sum over solved problems of the minute of acceptance plus 20 minutes for each rejected submission before it. The problems come from lessons you have started, unsolved ones first, and their lessons stay hidden until the end.' }])),
    el('div', { class: 'helpgrid', style: 'margin-top:18px;align-items:center;gap:12px 18px' },
      el('span', { class: 'label muted' }, 'length'), seg('minutes', [[60, '1 h'], [120, '2 h'], [180, '3 h'], [300, '5 h']]),
      el('span', { class: 'label muted' }, 'problems'), seg('count', [[4, '4'], [6, '6'], [8, '8'], [10, '10']]),
      el('span', { class: 'label muted' }, 'from'), seg('pool', [['studied', 'lessons I have started'], ['algo', 'the algorithms track'], ['all', 'everything']])),
    el('div', { class: 'row', style: 'margin-top:20px' }, el('button', { class: 'prominent', onclick: async () => {
      try { await post('contest_start', choice); route(); } catch (e) { flash(e.message); }
    } }, 'start the clock')),
    last ? [heading('last contest', last.solved + ' solved · ' + last.penalty + ' penalty'), scoreboard(last, false),
            el('p', { class: 'small muted', style: 'margin-top:8px' }, 'Now the lessons are shown: each problem links to its editorial.')] : null,
    s.past.length > 1 ? [heading('history'), el('div', { class: 'rows' }, s.past.map(p => rowbtn(null, 'off',
      el('span', { class: 'id' }, '#' + p.id), el('span', { class: 'label' }, shortDate(p.started) + ' · ' + p.minutes + ' min'),
      el('span', { class: 'grow' }), el('span', { class: 'cost' }, p.solved + '/' + p.problems + ' solved · ' + p.penalty + ' penalty'))))] : null,
  ]);
}

async function screenContestProblem(letter) {
  const s = await call('contest');
  const c = s.active;
  if (!c) { location.hash = '#/contest'; return; }
  const row = c.rows.find(r => r.letter === letter);
  if (!row) throw new Error('no problem ' + letter + ' in this contest');
  const d = await call('problem', { ref: row.ref, contest: 1 });
  const clock = el('span', { class: 'mono' });
  contestClock(c, clock);
  const subsBox = el('div', { class: 'rows subs' });
  const drawSubs = subs => subsBox.replaceChildren(...subs.map(x => rowbtn(null, 'off',
    el('span', { class: 'vd ' + x.verdict }, x.verdict), el('span', { class: 'grow' }), el('span', { class: 'cost' }, 'minute ' + x.minute))));
  drawSubs(d.subs);
  const status = el('span', {}, scoreCell(d.row));
  const panel = judgePanel(d, row.ref, {
    contest: true,
    onResult(r, mode) {
      if (mode !== 'submit' || !r.contest) return [];
      const me = r.contest.rows.find(x => x.ref === row.ref);
      status.replaceChildren(scoreCell(me));
      call('problem', { ref: row.ref, contest: 1 }).then(p => drawSubs(p.subs));
      return r.result.verdict === 'AC' ? [el('p', { class: 'small pass' }, 'Accepted at minute ' + me.minute + '. Back to the ', el('a', { href: '#/contest', style: 'text-decoration:underline' }, 'scoreboard'), '.')] : [];
    },
  });
  const left = el('div', { class: 'statement' },
    el('div', { class: 'row small', style: 'gap:10px;margin-bottom:10px' },
      el('a', { class: 'muted', href: '#/contest' }, 'contest #' + c.id + ' · scoreboard'), el('span', { class: 'grow' }),
      c.rows.map(r => el('a', { href: '#/contest/' + r.letter, class: 'mono small' + (r.letter === letter ? '' : ' faint'), title: r.title }, r.letter)),
      clock),
    el('div', { class: 'titleline' }, el('span', { class: 'mono', style: 'font-size:22px;color:' + d.color }, letter), el('h1', {}, d.title), status),
    el('div', { class: 'limits' }, el('span', {}, 'time limit ' + d.time_limit + ' s')),
    el('div', { class: 'book' }, prose(d.statement)),
    heading('input'), el('div', { class: 'book' }, prose(d.input)),
    heading('output'), el('div', { class: 'book' }, prose(d.output)),
    heading('samples'), sampleNodes(d),
    heading('submissions'), subsBox);
  show(splitCols(left, panel.node, 'cp.split'), 'wide');
}

// ------------------------------------------------------------- problems
async function screenProblems() {
  const { groups } = await call('problems');
  const all = groups.flatMap(g => g.lessons.flatMap(l => l.problems));
  const solved = all.filter(p => p.solved).length;
  const out = [titleline('problems', solved + ' of ' + all.length + ' solved')];
  const filter = { mode: 'all' };
  const box = el('div');
  const tabs = el('div', { class: 'tabs' }, [['all', 'all'], ['open', 'unsolved'], ['solved', 'solved'], ['due', 'due for re-solve']].map(([k, label]) =>
    el('button', { class: k === filter.mode ? 'on' : '', onclick: e => {
      filter.mode = k; tabs.querySelectorAll('button').forEach(b => b.classList.toggle('on', b === e.currentTarget)); draw();
    } }, label)));
  function draw() {
    const nodes = [];
    for (const g of groups) {
      const lessons = g.lessons.map(l => ({ ...l, problems: l.problems.filter(p =>
        filter.mode === 'all' || (filter.mode === 'open' && !p.solved) || (filter.mode === 'solved' && p.solved) || (filter.mode === 'due' && p.due)) }))
        .filter(l => l.problems.length);
      if (!lessons.length) continue;
      nodes.push(heading(g.name, lessons.reduce((n, l) => n + l.problems.length, 0) + ' problems'));
      for (const l of lessons) {
        nodes.push(el('div', { class: 'small faint', style: 'margin:12px 0 2px' }, el('a', { href: '#/lesson/' + l.id }, l.id + ' · ' + l.title)));
        nodes.push(el('div', { class: 'rows' }, l.problems.map(p => rowbtn('#/problem/' + p.ref, '',
          balloonSvg(p.color, p.solved),
          el('span', { class: 'name ellipsis' }, p.title),
          p.source ? el('span', { class: 'small faint ellipsis', style: 'max-width:260px' }, p.source) : null,
          el('span', { class: 'grow' }),
          p.due ? el('span', { class: 'cost accent' }, 're-solve due') : null,
          el('span', { class: 'cost', style: 'width:130px;text-align:right' },
            p.solved ? '✓ ' + p.difficulty : p.submits ? p.submits + (p.submits === 1 ? ' try' : ' tries') + ' · ' + p.difficulty : p.difficulty)))));
      }
    }
    box.replaceChildren(...(nodes.length ? nodes : [el('p', { class: 'empty' }, 'Nothing here.')]));
  }
  draw();
  show([out, tabs, box]);
}

// --------------------------------------------------------------- review
async function screenReview() {
  const { queue } = await call('due');
  if (!queue.length) {
    return show([titleline('review', 'nothing due'),
      el('p', { class: 'empty' }, 'The queue is empty. Cards you rate at the end of a lesson, and problems you rate after solving them, come back here when they are due.')]);
  }
  const cards = queue.filter(q => q.kind === 'card');
  const probs = queue.filter(q => q.kind === 'problem');
  const out = [titleline('review', queue.length + ' due')];
  if (probs.length) {
    out.push(heading('re-solve from scratch', String(probs.length)));
    out.push(el('p', { class: 'small muted', style: 'margin:6px 0' }, 'Clear the editor (reset) and solve it again without looking. Rate it after the AC.'));
    out.push(el('div', { class: 'rows' }, probs.map(q => rowbtn('#/problem/' + q.problem.ref, '',
      balloonSvg(q.problem.color, true), el('span', { class: 'name ellipsis' }, q.problem.title),
      el('span', { class: 'grow' }), el('span', { class: 'cost' }, q.lesson_title)))));
  }
  if (cards.length) {
    out.push(heading('cards', String(cards.length)));
    cards.forEach(q => out.push(cardNode(q.card)));
  }
  show(out);
}

// ---------------------------------------------------------------- stats
async function screenStats() {
  const s = await call('stats');
  const order = ['AC', 'WA', 'TLE', 'RE', 'CE', 'OLE'];
  const total = Object.values(s.verdicts).reduce((a, b) => a + b, 0);
  const vbar = el('div', { style: 'display:flex;height:10px;border-radius:3px;overflow:hidden;background:var(--hairline);margin:10px 0 6px' },
    order.filter(v => s.verdicts[v]).map(v => el('span', { title: v + ': ' + s.verdicts[v],
      style: 'flex:' + s.verdicts[v] + ';background:' + (v === 'AC' ? 'var(--pass)' : v === 'TLE' ? 'var(--slow)' : 'var(--fail)') + ';opacity:' + (v === 'AC' ? .8 : v === 'CE' ? .5 : .85) })));
  const vlegend = el('div', { class: 'row small muted', style: 'gap:16px' }, order.filter(v => s.verdicts[v]).map(v =>
    el('span', {}, el('span', { class: 'vd ' + v, style: 'width:auto;margin-right:4px' }, v), s.verdicts[v])));

  const progress = (label, done, tot) => el('div', { style: 'margin:14px 0' },
    el('div', { class: 'row label', style: 'margin-bottom:5px' }, el('span', {}, label), el('span', { class: 'grow' }),
      el('span', { class: 'small faint' }, done + ' / ' + tot)),
    el('div', { class: 'bar' }, el('span', { style: 'width:' + (tot ? 100 * done / tot : 0) + '%' })));

  const side = [
    heading('due · next 14 days', String(s.forecast.reduce((a, b) => a + b, 0)), false),
    el('div', { style: 'margin-top:8px' }, forecastStrip(s.forecast)),
    s.retention.length ? heading('retention by lesson') : null,
    s.retention.map(r => meter(r.label, r.pct)),
    s.hardest.length ? heading('hardest for you') : null,
    el('div', { class: 'rows' }, s.hardest.map(h => rowbtn(h.ref ? '#/problem/' + h.ref : '#/lesson/' + h.lesson, '',
      el('span', { class: 'dot' }), el('span', { class: 'label ellipsis' }, h.label), el('span', { class: 'grow' }),
      el('span', { class: 'cost mono' }, h.ease)))),
  ];
  show(el('div', { class: 'dense-cols' },
    el('div', { class: 'main' },
      titleline('stats', s.hours + ' h in sessions'),
      el('div', { class: 'figures', style: 'margin-top:18px' },
        figure(s.solved, 'problems solved'), figure(s.streak, 'day streak'),
        figure(s.first_try_pct + '%', 'questions right first try'), figure(s.submissions, 'submissions')),
      heading('verdicts', total ? Math.round(100 * (s.verdicts.AC || 0) / total) + '% accepted' : ''),
      total ? [vbar, vlegend] : el('p', { class: 'empty' }, 'No submissions yet.'),
      heading('progress'),
      s.tracks.map(t => [progress(t.name + ': lessons learned', t.learned, t.total),
                         progress(t.name + ': problems solved', t.solved, t.problems)]),
      progress('cards scheduled', s.cards_seen, s.cards_total),
      heading('activity', 'last ' + s.activity_weeks + ' weeks'),
      activityGrid(s.activity, s.activity_weeks)),
    el('div', { class: 'rule' }), el('div', { class: 'side' }, side)), 'dense');
}

function activityGrid(counts, weeks) {
  const peak = Math.max(1, ...counts);
  const grid = el('div', { style: 'display:grid;gap:3px;max-width:360px;margin-top:10px;grid-template-columns:repeat(' + weeks + ',1fr)' });
  for (const n of counts) grid.append(el('span', { title: plural(n, 'action'),
    style: 'height:10px;border-radius:2px;background:' + (n ? 'var(--accent)' : 'var(--hairline)') + ';opacity:' + (n ? 0.35 + 0.65 * Math.min(1, n / peak) : 1) }));
  return grid;
}

// ----------------------------------------------------------- playground
const PLAY_DEFAULT = `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;
    sort(a.begin(), a.end());
    for (auto x : a) cout << x << ' ';
    cout << '\\n';
    return 0;
}
`;
function stored(key, fallback) { try { return localStorage.getItem(key) ?? fallback; } catch (e) { return fallback; } }
function store(key, value) { try { localStorage.setItem(key, value); } catch (e) { /* private mode */ } }

async function screenPlayground() {
  const out = el('div');
  const stdin = el('textarea', { class: 'plain mono', style: 'width:100%;min-height:110px;font-size:12.5px', spellcheck: 'false' });
  stdin.value = stored('cp.play.in', '5\n3 1 4 1 5\n');
  stdin.addEventListener('input', () => store('cp.play.in', stdin.value));
  const run = async () => {
    out.replaceChildren(el('p', { class: 'small faint' }, 'compiling and running…'));
    try {
      const r = await post('playground', { code: ed.get(), input: stdin.value });
      if (r.verdict === 'CE') {
        const pre = el('pre', { class: 'compile' });
        const lines = new Set();
        pre.innerHTML = esc(r.compile).replace(/main\.cpp:(\d+):(\d+)/g, (m, ln) => { lines.add(+ln); return '<a data-line="' + ln + '">' + m + '</a>'; });
        pre.querySelectorAll('a').forEach(a => a.onclick = () => ed.goto(+a.dataset.line));
        ed.mark([...lines]);
        return out.replaceChildren(el('div', { class: 'verdict CE' }, el('span', { class: 'big' }, 'Compilation Error')), pre);
      }
      ed.mark([]);
      fill(out,
        el('div', { class: 'verdict ' + (r.verdict === 'AC' ? '' : r.verdict) }, el('span', { class: 'big' }, r.verdict === 'AC' ? 'ran' : VERDICT_NAME[r.verdict]),
          el('span', { class: 'sub' }, r.ms + ' ms · ' + (r.kb / 1024).toFixed(1) + ' MB' + (r.message ? ' · ' + r.message : ''))),
        el('div', { class: 'k small faint' }, 'stdout'), el('pre', { class: 'box' }, r.stdout || ''),
        r.stderr ? [el('div', { class: 'k small faint', style: 'margin-top:8px' }, 'stderr'), el('pre', { class: 'box' }, r.stderr)] : null,
        r.warnings ? el('details', { style: 'margin-top:8px' }, el('summary', { class: 'small muted' }, 'warnings'), el('pre', { class: 'compile' }, r.warnings)) : null);
    } catch (e) { out.replaceChildren(el('p', { class: 'err' }, e.message)); }
  };
  const ed = makeEditor(stored('cp.play.code', PLAY_DEFAULT), { tall: true, onChange: v => store('cp.play.code', v), onRun: run, onSubmit: run });
  stdin.addEventListener('keydown', e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); run(); } });
  show(splitCols(
    el('div', { class: 'statement' },
      titleline('playground', 'compile and run anything'), el('div', { class: 'spacer' }), ed.node,
      el('div', { class: 'toolbar' }, el('button', { class: 'prominent', onclick: run }, 'run', el('span', { class: 'shortcut' }, MOD + '↵')),
        el('button', { class: 'bare small', onclick: () => { if (twice('play', 'Click again to restore the example program.')) { ed.set(PLAY_DEFAULT); store('cp.play.code', PLAY_DEFAULT); } } }, 'reset'),
        el('span', { class: 'where' }, State.env && State.env.compiler.ok ? State.env.compiler.version : ''))),
    el('div', { class: 'work' }, heading('stdin', '', false), el('div', { style: 'margin-top:6px' }, stdin), el('div', { style: 'margin-top:14px' }, out)),
    'cp.split.play', 58), 'wide');
  KEYS = { e: () => ed.focus() };
  MODKEYS = { Enter: run };
}

// ------------------------------------------------------------- notebook
async function screenNotebook() {
  const { lessons } = await call('notebook');
  const pref = { which: stored('cp.nb.which', 'mine') };
  const box = el('div');
  function draw() {
    fill(box, lessons.length ? lessons.map(l => [
      el('h2', { class: 'nb-lesson', style: 'margin:30px 0 4px' }, l.id + ' · ' + l.title),
      l.problems.map(p => {
        const code = pref.which === 'mine' && p.mine ? p.mine : p.reference;
        return el('section', { class: 'nb-problem' },
          el('div', { class: 'row', style: 'margin:14px 0 6px' }, balloonSvg(p.color, true),
            el('a', { href: '#/problem/' + p.ref, class: 'label', style: 'font-weight:500' }, p.title),
            el('span', { class: 'small faint' }, [p.complexity, pref.which === 'mine' && !p.mine ? 'reference (no accepted copy saved)' : pref.which === 'mine' ? 'your accepted code' : 'reference'].filter(Boolean).join(' · '))),
          el('div', { class: 'prose' }, codeBlock(code, 'cpp')));
      })]) : el('p', { class: 'empty' }, 'Solve a problem and it lands here. At an ICPC contest you may bring a printed team reference document; this is the start of yours.'));
  }
  const tabs = el('div', { class: 'tabs noprint' }, [['mine', 'my accepted code'], ['ref', 'reference solutions']].map(([k, label]) =>
    el('button', { class: pref.which === k ? 'on' : '', onclick: e => {
      pref.which = k; store('cp.nb.which', k);
      tabs.querySelectorAll('button').forEach(b => b.classList.toggle('on', b === e.currentTarget)); draw();
    } }, label)));
  draw();
  const n = lessons.reduce((a, l) => a + l.problems.length, 0);
  show([el('div', { class: 'titleline' }, el('h1', {}, 'notebook'),
          el('span', { class: 'note noprint' }, plural(n, 'solved problem'), ' · ', el('button', { class: 'bare small', onclick: () => window.print() }, 'print'))),
        el('p', { class: 'label muted noprint', style: 'margin-top:8px' }, 'The code of everything you have solved, lesson by lesson: the seed of a team reference document.'),
        tabs, box]);
}

// ---------------------------------------------------------------- about
async function screenAbout() {
  const env = await call('env');
  State.env = env;
  const keys = [['t', 'today'], ['b', 'lessons'], ['o', 'problems'], ['r', 'review'], ['s', 'stats'], ['c', 'contest'], ['n', 'notebook'], ['g', 'playground'],
                ['1-4 / a-d', 'pick an option in the current question'], ['Enter', 'focus the current answer box'],
                [MOD + '↵', 'submit (in the editor)'], [MOD + "'", 'run the samples only'], [MOD + '/', 'comment lines'],
                [MOD + 'S', 'save now (it also autosaves)'], ['Tab / ⇧Tab', 'indent / dedent']];
  show([
    titleline('about', 'how this works'),
    el('div', { class: 'book' }, prose([
      { type: 'paragraph', text: 'Two tracks. **C++ for contests** teaches the language by contrast with Python: what C++ does differently and which differences cost points. **Algorithms, from the question up** rebuilds each technique from a concrete problem: the brute force, what it wastes, the insight, why it is correct, then the code.' },
      { type: 'paragraph', text: 'Lessons are dialogues. The page shows everything up to the next question and waits. Wrong options say *why* they are wrong; that is where most of the teaching is. `show me` is always there, and nothing is locked: every lesson opens, whatever order you choose.' },
      { type: 'paragraph', text: 'Problems are judged like an ICPC contest: your file is compiled with GCC, run on every test with a time limit, and the first failure is the verdict. Unlike a contest, small failing tests are shown to you, and custom input runs the reference solution next to yours.' },
      { type: 'paragraph', text: 'Cards at the end of a lesson, and problems after you solve them, are scheduled with SM-2 spaced repetition and come back in **review**.' },
    ])),
    heading('this machine'),
    el('div', { class: 'helpgrid', style: 'margin-top:10px' },
      el('span', { class: 'faint' }, 'compiler'), el('span', { class: env.compiler.ok ? '' : 'fail' }, env.compiler.ok ? env.compiler.version : env.compiler.error),
      env.compiler.ok ? [el('span', { class: 'faint' }, 'flags'), el('span', { class: 'mono small' }, env.compiler.flags.replace(/-idirafter \S+/, '-idirafter harness/include'))] : null,
      el('span', { class: 'faint' }, 'progress'), el('span', { class: 'mono small' }, env.progress),
      el('span', { class: 'faint' }, 'your code'), el('span', { class: 'mono small' }, env.workspace + '/<lesson>/<problem>.cpp')),
    Object.keys(env.load_errors).length ? el('div', { class: 'warnbox' }, Object.entries(env.load_errors).map(([m, e]) => el('div', {}, m + ': ' + e))) : null,
    heading('keys'),
    el('div', { class: 'helpgrid', style: 'margin-top:10px' }, keys.map(([k, v]) => [el('span', { class: 'mono small' }, k), el('span', { class: 'small' }, v)])),
  ]);
}

// ================================================================= routing
const ROUTES = [
  [/^#?\/?$/, screenToday],
  [/^#\/browse$/, screenBrowse],
  [/^#\/lesson\/([\w]+)$/, screenLesson],
  [/^#\/problem\/([\w.]+)$/, screenProblem],
  [/^#\/problems$/, screenProblems],
  [/^#\/review$/, screenReview],
  [/^#\/stats$/, screenStats],
  [/^#\/playground$/, screenPlayground],
  [/^#\/contest$/, screenContest],
  [/^#\/contest\/([A-Z])$/, screenContestProblem],
  [/^#\/about$/, screenAbout],
  [/^#\/notebook$/, screenNotebook],
];

async function route() {
  if (State.flush) { State.flush(); State.flush = null; }
  if (State.timer) { clearInterval(State.timer); State.timer = null; }
  window.onbeforeunload = null;
  const hash = location.hash || '#/';
  document.querySelectorAll('#bar nav a').forEach(a => {
    const h = a.getAttribute('href');
    a.classList.toggle('on', h === hash || (h !== '#/' && hash.startsWith(h)) ||
      (h === '#/browse' && hash.startsWith('#/lesson/')) || (h === '#/problems' && hash.startsWith('#/problem/')));
  });
  KEYS = {};
  MODKEYS = {};
  for (const [re, fn] of ROUTES) {
    const m = hash.match(re);
    if (!m) continue;
    try {
      return await fn(...m.slice(1));
    } catch (e) {
      console.error(e);
      return show([titleline('something went wrong'), el('p', { class: 'err', style: 'margin-top:12px' }, e.message),
                   el('p', {}, el('a', { href: '#/' }, 'back to today'))]);
    }
  }
  show([titleline('not found'), el('p', {}, el('a', { href: '#/' }, 'back to today'))]);
}

window.addEventListener('hashchange', route);
call('env').then(env => {
  State.env = env;
  document.getElementById('who').textContent = env.compiler.ok ? env.compiler.version.split(' ').slice(0, 1).join(' ') + ' ' + (env.compiler.version.match(/\d+\.\d+\.\d+/) || [''])[0] : 'no compiler';
}).catch(() => {}).finally(route);
