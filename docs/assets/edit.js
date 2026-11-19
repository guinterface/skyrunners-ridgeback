// Edit the site in place. Changes are saved to the GitHub repository (data/parts.toml, data/inputs.toml, data/orders.toml); GitHub then
// rebuilds the sheets and the pages (.github/workflows/rebuild.yml). Two ways to save:
//  - team passcode: through the relay (tools/relay/Code.gs, a Google Apps Script web app that holds one team token);
//  - own GitHub token: for people with write access, or while no relay is set up.
// RELAY: paste the relay's web app URL (https://script.google.com/macros/s/.../exec) between the quotes.
const RELAY = 'https://script.google.com/macros/s/AKfycbyk8_AVZHNF-hboeR7PNGiZm2r85k1m4cnDSoK09AfEZN6TVsxQWjAzT_WjPRDIP_FAPw/exec';
const REPO = 'guinterface/skyrunners-ridgeback';
const API = `https://api.github.com/repos/${REPO}`;
const TOKEN_URL = 'https://github.com/settings/tokens/new?scopes=public_repo&description=Ridgeback%20site%20editing';
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch { /* private window */ } },
};
let token = store.get('rb-token') || sessionToken();
let pass = store.get('rb-pass'), editor = store.get('rb-name');
const viaRelay = () => RELAY && !token;
function sessionToken() { try { return sessionStorage.getItem('rb-token'); } catch { return null; } }

const btn = document.getElementById('editToggle');
const bar = document.getElementById('editbar');
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
let editing = false;

// ---------- GitHub
async function gh(path, opts = {}) {
  const r = await fetch(API + path, { ...opts, headers: { Accept: 'application/vnd.github+json', Authorization: `Bearer ${token}`, ...(opts.headers || {}) } });
  if (!r.ok) { const t = await r.text(); const e = new Error(`${r.status} ${t.slice(0, 200)}`); e.status = r.status; throw e; }
  return r.json();
}
const b64dec = s => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\n/g, '')), c => c.charCodeAt(0)));
const b64enc = s => { const b = new TextEncoder().encode(s); let x = ''; b.forEach(c => { x += String.fromCharCode(c); }); return btoa(x); };
async function relay(body) {                              // the relay answers JSON; plain-text POST avoids a CORS preflight
  const r = await fetch(RELAY, { method: 'POST', body: JSON.stringify({ ...body, pass, name: editor }) });
  let j;
  try { j = await r.json(); } catch { throw new Error('The editing relay did not answer properly; try again in a minute or tell a lead.'); }
  if (j.error) {
    if (j.status === 401) { store.set('rb-pass', null); pass = null; }      // passcode changed: ask again next time
    const e = new Error(j.error); e.status = j.status; throw e;
  }
  return j;
}
async function getFile(path) {
  if (viaRelay()) return relay({ op: 'read', path });
  const f = await gh(`/contents/${path}?ref=main&t=${Date.now()}`); return { sha: f.sha, text: b64dec(f.content) };
}
async function putFile(path, text, sha, message) {
  if (viaRelay()) return (await relay({ op: 'save', path, text, sha, what: message.replace(/^(Edit|Change) /, '') })).commit;
  return (await gh(`/contents/${path}`, { method: 'PUT', body: JSON.stringify({ message: message + ' on the website', content: b64enc(text), sha, branch: 'main' }) })).commit.sha;
}
async function buildStatus(sha) {                         // -> { run: {status, conclusion, html_url, updated_at} | null, pages: {status, updated_at} | null }
  if (viaRelay()) return relay({ op: 'status', sha });
  const runs = await gh(`/actions/runs?head_sha=${sha}&t=${Date.now()}`);
  const pages = await gh(`/pages/builds/latest?t=${Date.now()}`).catch(() => null);
  return { run: runs.workflow_runs.find(r => r.name.startsWith('Rebuild')) || null, pages };
}
async function saveFile(path, change, message) {          // change(text) -> new text; retries once if someone saved in between
  for (let i = 0; i < 2; i++) {
    const f = await getFile(path);
    const text = change(f.text);
    if (text === f.text) return null;
    try { return await putFile(path, text, f.sha, message); } catch (e) { if (e.status !== 409 || i) throw e; }
  }
}

// ---------- TOML for one part (same layout as the file)
const tv = v => Array.isArray(v) ? '[' + v.map(tv).join(', ') + ']'
  : (v && typeof v === 'object') ? '{ ' + Object.entries(v).map(([k, x]) => `${k} = ${tv(x)}`).join(', ') + ' }'
  : typeof v === 'number' ? String(v) : JSON.stringify(String(v));
function partBlock(raw) {
  const out = ['[[part]]'];
  for (const [k, v] of Object.entries(raw)) {
    if (k === 'buy' || k === 'refs') out.push(v.length ? `${k} = [\n` + v.map(b => '  ' + tv(b) + ',').join('\n') + '\n]' : `${k} = []`);
    else out.push(`${k} = ${tv(v)}`);
  }
  return out.join('\n') + '\n';
}
function replacePart(text, raw) {
  const blocks = text.split(/^(?=\[\[part\]\]\s*$)/m);
  const i = blocks.findIndex(b => new RegExp(`^id = "${raw.id}"\\s*$`, 'm').test(b));
  if (i < 0) throw new Error(`part "${raw.id}" not found in data/parts.toml`);
  const tail = blocks[i].match(/\n*$/)[0];
  blocks[i] = partBlock(raw).replace(/\n$/, '') + (tail.length > 1 ? tail : '\n\n');
  if (i === blocks.length - 1) blocks[i] = blocks[i].replace(/\n+$/, '\n');
  return blocks.join('');
}

// ---------- status bar and token
function say(html, kind = '') { bar.hidden = false; bar.className = 'editbar ' + kind; bar.innerHTML = html; }
function askPass() {                                      // the easy way: name + team passcode, no GitHub account needed
  say(`<b>Edit the site.</b> Saves go to the team's GitHub repository and rebuild the pages in about two minutes; every save can be undone.
    <span class="row"><label>Your name <input id="edName" autocomplete="name" size="14" value="${esc(editor || '')}"></label>
    <label>Team passcode <input id="edPass" type="password" autocomplete="off" size="12"></label>
    <button type="button" id="passOk">Start editing</button> <button type="button" id="passNo" class="plainbtn">Cancel</button></span>
    <span class="small">No account or token needed: ask in the club channel for the passcode. <a href="#" id="useToken">I have a GitHub token instead</a></span>`);
  document.getElementById('useToken').onclick = e => { e.preventDefault(); askToken(); };
  document.getElementById('passNo').onclick = stop;
  document.getElementById('passOk').onclick = async () => {
    const n = document.getElementById('edName').value.trim(), v = document.getElementById('edPass').value;
    if (!n) { document.getElementById('edName').focus(); return; }
    editor = n; pass = v;
    try { await relay({ op: 'check' }); } catch (e) { say(`${esc(e.message.slice(0, 100))} <button type="button" id="again" class="plainbtn">Try again</button>`, 'bad'); document.getElementById('again').onclick = askPass; return; }
    store.set('rb-name', editor); store.set('rb-pass', pass);
    start();
  };
}
function askToken() {
  say(`<b>Editing saves straight to the team's GitHub repository.</b> It needs your GitHub token once (with write access to the repo; ask a lead if you have none).
    <a href="${TOKEN_URL}" target="_blank" rel="noopener">Make a token</a> (tick <i>public_repo</i>, then copy it) and paste it here:
    <input id="tok" type="password" autocomplete="off" placeholder="ghp_… or github_pat_…" size="28"> <label><input id="tokKeep" type="checkbox" checked> remember in this browser</label>
    <button type="button" id="tokOk">Start editing</button> <button type="button" id="tokNo" class="plainbtn">Cancel</button>`);
  document.getElementById('tokOk').onclick = async () => {
    const v = document.getElementById('tok').value.trim(); if (!v) return;
    token = v;
    try {
      const repo = await gh('');
      if (!repo.permissions?.push) { say('This token works, but its GitHub account cannot save to the repository. Ask a lead to add you, or propose the change on GitHub.', 'bad'); token = null; return; }
    } catch (e) { say(`GitHub did not accept the token (${esc(e.message.slice(0, 60))}).`, 'bad'); token = null; return; }
    if (document.getElementById('tokKeep').checked) store.set('rb-token', token); else { try { sessionStorage.setItem('rb-token', token); } catch { } }
    start();
  };
  document.getElementById('tokNo').onclick = stop;
}
function start() {
  editing = true; btn.setAttribute('aria-pressed', 'true'); btn.textContent = 'Done editing';
  document.body.classList.add('editing');
  say(`<b>Editing.</b> Click the ✎ next to any number, text or link (or double-click it) to change it, then press Save.
    Saving writes data/parts.toml, data/inputs.toml or data/orders.toml on GitHub with your name; the sheets and pages rebuild in about two minutes. Every save is a commit in <a href="https://github.com/${REPO}/commits/main" target="_blank" rel="noopener">the history</a>, so it can be undone. <button type="button" id="forget" class="plainbtn">${viaRelay() ? 'Sign out' : 'Forget my token'}</button>`);
  document.getElementById('forget').onclick = () => { store.set('rb-token', null); store.set('rb-pass', null); try { sessionStorage.removeItem('rb-token'); } catch { } token = null; pass = null; stop(); };
  window.RB?.rerender?.();
  inputsMode(true); showUndo(true); decorate(document.body);
  if (pending) { const el = document.querySelector(pending); pending = null; const t = el && target(el); if (t) { el.scrollIntoView({ block: 'center' }); openEditor(t); } }
}
function stop() {
  editing = false; fullFor = null; document.querySelectorAll('form.qedit').forEach(q => q.cancel()); document.querySelectorAll('.qhint, .addbtn, .loginpop').forEach(b => b.remove());
  btn.setAttribute('aria-pressed', 'false'); btn.textContent = 'Edit';
  document.body.classList.remove('editing'); bar.hidden = true;
  window.RB?.rerender?.();
  inputsMode(false); showUndo(false);
}
function login() {
  if (token) return start();
  if (!RELAY) return askToken();
  if (pass == null) return askPass();
  relay({ op: 'check' }).then(start, askPass);              // stored passcode: make sure it still works
}
btn?.addEventListener('click', () => { if (editing) return stop(); pending = null; login(); });

// ---------- after a save: follow the rebuild, then reload
async function follow(sha, what) {
  say(`Saved ${esc(what)} (<a href="https://github.com/${REPO}/commit/${sha}" target="_blank" rel="noopener">${sha.slice(0, 7)}</a>). Rebuilding the sheets and pages…`, 'busy');
  const t0 = Date.now();
  while (Date.now() - t0 < 6 * 60e3) {
    await new Promise(r => setTimeout(r, 8000));
    try {
      const { run } = await buildStatus(sha);
      if (!run) continue;
      if (run.status !== 'completed') { say(`Saved ${esc(what)}. Rebuilding… (<a href="${run.html_url}" target="_blank" rel="noopener">progress</a>)`, 'busy'); continue; }
      if (run.conclusion !== 'success') { say(`The rebuild failed, so the site keeps the previous version. <a href="${run.html_url}" target="_blank" rel="noopener">See why</a>; fix the value and save again.`, 'bad'); return; }
      say(`Rebuilt. The page reloads when GitHub has published it (about a minute)…`, 'busy');
      for (let k = 0; k < 30; k++) {
        await new Promise(r => setTimeout(r, 6000));
        const b = (await buildStatus(sha).catch(() => ({}))).pages;
        if (b && b.status === 'built' && new Date(b.updated_at) > new Date(run.updated_at)) { location.reload(); return; }
      }
      say('Rebuilt and saved. Reload the page in a minute to see it everywhere.', 'ok'); return;
    } catch (e) { /* keep waiting */ }
  }
  say('Saved. The rebuild is taking longer than usual; check the Actions tab on GitHub.', 'ok');
}

// ---------- the part form (drone page)
const FIELDS = [['name', 'Name', 'text'], ['status', 'Status', 'text'], ['qty', 'Quantity', 'num'], ['price', 'Price each (US$)', 'num'],
  ['mass', 'Mass each (g)', 'num'], ['size', 'Size', 'text'], ['power_w', 'Power (W)', 'num'],
  ['job', 'What it does', 'area'], ['why', 'Why we chose it', 'area'], ['without', 'Without it (what we would lose)', 'area'], ['instead', 'Considered instead', 'area'], ['source', 'Numbers from', 'text']];
function partForm(p, el) {
  if (!editing || fullFor !== p.id) return false;
  const raw = structuredClone(p.raw);
  const f = FIELDS.filter(([k]) => k in raw || ['size', 'instead', 'source'].includes(k)).map(([k, label, kind]) => {
    const v = raw[k] ?? '';
    const input = kind === 'area' ? `<textarea name="${k}" rows="${k === 'why' ? 6 : 3}">${esc(v)}</textarea>`
      : `<input name="${k}" ${kind === 'num' ? 'inputmode="decimal"' : ''} value="${esc(v)}">`;
    return `<label class="fld"><span>${label}</span>${input}</label>`;
  }).join('');
  const refRow = (r = { cite: '', link: '', says: '' }) => `<div class="buyrow refrow"><input name="cite" placeholder="Author et al., Journal 1:2 (2020)" value="${esc(r.cite)}"><input name="rlink" placeholder="https://doi.org/…" value="${esc(r.link)}"><input name="says" placeholder="what it shows, in a few words" value="${esc(r.says)}"><button type="button" class="plainbtn rm" aria-label="Remove reference">remove</button></div>`;
  const buyRow = (b = { store: '', link: '', price: '' }) => `<div class="buyrow"><input name="store" placeholder="Shop" value="${esc(b.store)}"><input name="link" placeholder="https://…" value="${esc(b.link)}"><input name="bprice" placeholder="$0.00" value="${esc(b.price)}"><button type="button" class="plainbtn rm" aria-label="Remove shop">remove</button></div>`;
  el.innerHTML = `<form class="pform"><h2>Edit: ${esc(p.name)}</h2>${f}
    <div class="fld"><span>Where to buy</span><div class="buys">${(raw.buy || []).map(buyRow).join('')}</div><button type="button" class="plainbtn addbuy">+ add a shop</button></div>
    <div class="fld"><span>Evidence (papers, datasheets)</span><div class="refs">${(raw.refs || []).map(refRow).join('')}</div><button type="button" class="plainbtn addref">+ add a reference</button></div>
    <p class="small">Words in {curly braces} are numbers filled in from the sheets (for example {TW_hot}); keep the braces.</p>
    <p class="err" hidden></p><div class="actions"><button type="submit">Save to GitHub</button> <button type="button" class="plainbtn cancel">Cancel</button></div></form>`;
  const form = el.querySelector('form');
  form.querySelector('.addbuy').onclick = () => form.querySelector('.buys').insertAdjacentHTML('beforeend', buyRow());
  form.querySelector('.addref').onclick = () => form.querySelector('.refs').insertAdjacentHTML('beforeend', refRow());
  form.addEventListener('click', e => { if (e.target.classList.contains('rm')) e.target.closest('.buyrow').remove(); });
  form.querySelector('.cancel').onclick = () => { fullFor = null; window.RB?.rerender?.(); };
  form.onsubmit = async e => {
    e.preventDefault();
    const err = form.querySelector('.err'); err.hidden = true;
    for (const [k, , kind] of FIELDS) {
      const inp = form.elements[k]; if (!inp) continue;
      const s = inp.value.trim();
      if (kind === 'num') {
        if (s === '' && !(k in p.raw)) continue;
        const n = Number(s.replace(/[$,]/g, ''));
        if (!Number.isFinite(n) || n < 0) { err.textContent = `“${FIELDS.find(x => x[0] === k)[1]}” must be a number.`; err.hidden = false; return; }
        raw[k] = n;
      } else if (s !== '' || k in p.raw) raw[k] = s;
    }
    const refs = [...form.querySelectorAll('.refrow')].map(r => ({ cite: r.querySelector('[name=cite]').value.trim(), link: r.querySelector('[name=rlink]').value.trim(), says: r.querySelector('[name=says]').value.trim() }))
      .filter(r => r.cite || r.link);
    const badRef = refs.find(r => !r.cite || !/^https:\/\/\S+$/.test(r.link));
    if (badRef) { err.textContent = `Each reference needs a name and a link starting with https:// (${badRef.cite || 'a reference'})`; err.hidden = false; return; }
    if (refs.length || 'refs' in p.raw) raw.refs = refs;
    raw.buy = [...form.querySelectorAll('.buys .buyrow')].map(r => ({ store: r.querySelector('[name=store]').value.trim(), link: r.querySelector('[name=link]').value.trim(), price: r.querySelector('[name=bprice]').value.trim() }))
      .filter(b => b.store || b.link);
    const bad = raw.buy.find(b => !/^https?:\/\/\S+$/.test(b.link));
    if (bad) { err.textContent = `The link for “${bad.store || 'a shop'}” must start with https://`; err.hidden = false; return; }
    const sub = form.querySelector('[type=submit]'); sub.disabled = true; sub.textContent = 'Saving…';
    try {
      const sha = await saveFile('data/parts.toml', t => replacePart(t, raw), `Edit ${raw.id}`);
      if (!sha) { say('Nothing changed.', 'ok'); sub.disabled = false; sub.textContent = 'Save to GitHub'; return; }
      p.raw = raw; follow(sha, raw.name);
    } catch (x) { err.textContent = 'Could not save: ' + x.message.slice(0, 160); err.hidden = false; sub.disabled = false; sub.textContent = 'Save to GitHub'; }
  };
  return true;
}
window.RB = Object.assign(window.RB || {}, { partForm, isEditing: () => editing });

// ---------- design numbers (calculations page): each value gets a pencil (see quick edits)
function inputsMode(on) {
  document.querySelectorAll('#inputs tr[data-key] .val').forEach(td => { if (on && td.dataset.orig == null) td.dataset.orig = td.textContent.trim(); });
}
async function saveInputChanges(changes) {
  const sha = await saveFile('data/inputs.toml', t => changes.reduce((s, [k, v]) => s.replace(new RegExp(`^(${k} = )(.+?)(\\s+#.*)?$`, 'm'), (m, a, b, c) => a + v + (c || '')), t),
    `Change ${changes.map(c => c[0]).join(', ')}`);
  if (!sha) { say('Nothing changed.', 'ok'); return false; }
  follow(sha, changes.map(c => c[0]).join(', ')); return true;
}

// ---------- quick edits: a pencil next to each value, or double-click it; each one saves on its own
const NUM = new Set(['qty', 'price', 'mass', 'power_w']), LONG = new Set(['job', 'why', 'without', 'instead']);
const LABEL = Object.fromEntries(FIELDS.map(([k, l]) => [k, l]));
const EDITABLE = '[data-f], [data-buy], [data-ref], [data-order], #inputs tr[data-key] .val';
let pending = null;                                      // selector of the value someone tried to edit before logging in
let fullFor = null;
const PEN = '<button type="button" class="pen" title="Change this" aria-label="Change this">✎</button>';
function decorate(root) {
  if (!root) return;
  if (editing && root.id === 'detail' && !root.querySelector('.qhint') && !root.querySelector('form.pform') && window.RB?.current?.()) {
    root.insertAdjacentHTML('afterbegin', '<p class="qhint">Click ✎ or double-click a value to change it. <button type="button" class="plainbtn" data-full>Edit all fields at once</button></p>');
    root.querySelector('[data-full]').onclick = () => { fullFor = window.RB.current().id; window.RB.rerender(); };
  }
  root.querySelectorAll(EDITABLE).forEach(e => { if (!e.closest('form') && !e.querySelector(':scope > .pen')) e.insertAdjacentHTML('beforeend', PEN); });
  if (editing) root.querySelectorAll('[data-add]').forEach(p => {
    if (p.querySelector('.addbtn')) return;
    const kind = p.dataset.add;
    p.innerHTML = `<button type="button" class="plainbtn addbtn">+ add ${kind === 'buy' ? 'a shop' : 'a reference'}</button>`;
    p.querySelector('button').onclick = () => {
      let ul = p.previousElementSibling;
      if (!ul || ul.tagName !== 'UL') { ul = document.createElement('ul'); if (kind === 'ref') ul.className = 'refs'; const prev = p.previousElementSibling; if (prev && prev.tagName === 'P' && kind === 'buy') prev.replaceWith(ul); else p.before(ul); }
      const li = document.createElement('li'); li.dataset[kind] = String(ul.children.length); ul.append(li);
      const t = target(li); if (t) openEditor(t, true);
    };
  });
}
function target(el) {
  const f = el.closest(EDITABLE); if (!f) return null;
  const key = f.closest('#inputs tr[data-key]');
  if (key) return { kind: 'input', el: f, key: key.dataset.key, label: key.cells[0].textContent.trim() };
  if (f.dataset.order != null) return { kind: 'order', el: f, key: f.dataset.order, state: f.dataset.state || 'to order' };
  const row = f.closest('tr[data-id]');
  const p = row ? window.RB?.part?.(row.dataset.id) : (f.closest('#detail') ? window.RB?.current?.() : null);
  if (!p || !p.raw) return null;
  if (f.dataset.buy != null) return { kind: 'buy', el: f, p, i: +f.dataset.buy };
  if (f.dataset.ref != null) return { kind: 'ref', el: f, p, i: +f.dataset.ref };
  return { kind: 'field', el: f, p, k: f.dataset.f };
}
document.addEventListener('click', e => {
  if (!editing) {
    const b = e.target.closest('.pen'); if (!b) return;
    e.preventDefault(); e.stopPropagation(); loginPrompt(b); return;
  }
  const b = e.target.closest('.pen'), a = e.target.closest('[data-buy] a, [data-ref] a');
  if (!b && !a) return;
  e.preventDefault(); e.stopPropagation();                 // while editing, a click on a shop or paper link edits it instead of opening it
  const t = target((b || a).parentElement); if (t) openEditor(t);
}, true);
document.addEventListener('dblclick', e => {
  if (!editing || e.target.closest('form')) return;
  const t = target(e.target); if (!t) return;
  e.preventDefault(); getSelection()?.removeAllRanges(); openEditor(t);
});
function openEditor(t, isNew = false) {
  document.querySelectorAll('form.qedit').forEach(q => q.cancel());
  const el = t.el, keep = el.innerHTML;
  let fields;
  if (t.kind === 'order') {
    el.innerHTML = `<form class="qedit"><select name="v" aria-label="Order status">${Object.entries(OSTATE).map(([k, l]) => `<option value="${k}"${k === t.state ? ' selected' : ''}>${l}</option>`).join('')}</select><span class="qbtns"><button type="submit" class="ok">Save</button> <button type="button" class="plainbtn no">Cancel</button></span><span class="err" hidden></span></form>`;
    const form = el.querySelector('form'), err = form.querySelector('.err');
    form.cancel = () => { el.innerHTML = keep; };
    form.querySelector('.no').onclick = () => form.cancel();
    form.addEventListener('keydown', e => { if (e.key === 'Escape') form.cancel(); });
    form.addEventListener('click', e => e.stopPropagation());
    form.elements.v.focus();
    form.onsubmit = async e => {
      e.preventDefault(); const st = form.elements.v.value;
      if (st === t.state) return form.cancel();
      form.querySelectorAll('button, select').forEach(b => { b.disabled = true; }); form.querySelector('.ok').textContent = 'Saving…';
      try {
        if (await saveOrder(t.key, st)) { el.dataset.state = st; el.className = 'ostate s-' + st.replace(' ', '-'); el.innerHTML = `${OSTATE[st]} <span class="saving">saving…</span>`; }
        else form.cancel();
      } catch (x) { form.querySelectorAll('button, select').forEach(b => { b.disabled = false; }); form.querySelector('.ok').textContent = 'Save'; err.textContent = 'Could not save: ' + x.message.slice(0, 160); err.hidden = false; }
    };
    return;
  }
  if (t.kind === 'input') fields = [['v', t.label, el.dataset.orig ?? '']];
  else if (t.kind === 'field') fields = [['v', LABEL[t.k] || t.k, t.p.raw[t.k] ?? '', LONG.has(t.k)]];
  else if (t.kind === 'buy') { const b = t.p.raw.buy?.[t.i] || { store: '', link: '', price: '' }; fields = [['store', 'Shop', b.store], ['link', 'https://… link', b.link], ['price', 'Price, e.g. $24.99', b.price]]; }
  else { const r = t.p.raw.refs?.[t.i] || { cite: '', link: '', says: '' }; fields = [['cite', 'Author et al., Journal (year)', r.cite], ['link', 'https://doi.org/… link', r.link], ['says', 'What it shows, in a few words', r.says]]; }
  const one = fields.length === 1;
  const inp = ([n, l, v, long]) => long ? `<textarea name="${n}" rows="5" aria-label="${esc(l)}">${esc(v)}</textarea>`
    : `<input name="${n}" value="${esc(v)}" placeholder="${esc(l)}" aria-label="${esc(l)}"${t.k === 'status' ? ' list="statusIdeas"' : ''}${one ? ` size="${Math.min(40, Math.max(6, String(v).length + 2))}"` : ''}>`;
  if (t.k === 'status' && !document.getElementById('statusIdeas')) document.body.insertAdjacentHTML('beforeend', '<datalist id="statusIdeas"><option value="buy"><option value="print"><option value="build"><option value="print + buy tubes"><option value="reuse (we own it)"><option value="borrow"></datalist>');
  el.innerHTML = `<form class="qedit${one ? '' : ' multi'}">${fields.map(inp).join('')}<span class="qbtns"><button type="submit" class="ok">Save</button> <button type="button" class="plainbtn no">Cancel</button>${(t.kind === 'buy' || t.kind === 'ref') && !isNew ? ' <button type="button" class="plainbtn del">Remove</button>' : ''}</span><span class="err" hidden></span></form>`;
  const form = el.querySelector('form');
  form.cancel = () => { if (isNew) el.remove(); else el.innerHTML = keep; };
  form.querySelector('.no').onclick = () => form.cancel();
  form.addEventListener('keydown', e => { if (e.key === 'Escape') form.cancel(); });
  form.addEventListener('click', e => e.stopPropagation());   // do not re-select the table row underneath
  const first = form.querySelector('input, textarea'); first.focus(); first.select?.();
  const err = form.querySelector('.err'), val = n => form.elements[n].value.trim();
  const fail = m => { err.textContent = m; err.hidden = false; return false; };
  const busy = on => { form.querySelectorAll('button').forEach(b => { b.disabled = on; }); form.querySelector('.ok').textContent = on ? 'Saving…' : 'Save'; };
  const run = async (save, shown) => {
    busy(true);
    try { const ok = await save(); if (ok) el.innerHTML = `${esc(shown)} <span class="small saving">saved, updating the site…</span>`; else form.cancel(); }
    catch (x) { busy(false); fail('Could not save: ' + x.message.slice(0, 160)); }
  };
  form.querySelector('.del')?.addEventListener('click', () => {
    const raw = structuredClone(t.p.raw); raw[t.kind === 'buy' ? 'buy' : 'refs'].splice(t.i, 1);
    run(() => savePart(t.p, raw), '(removed)');
  });
  form.onsubmit = e => {
    e.preventDefault(); err.hidden = true;
    if (t.kind === 'input') {
      const v = val('v'), orig = el.dataset.orig ?? '';
      if (v === orig) return form.cancel();
      const isNum = /^-?\d+(\.\d+)?([eE]-?\d+)?$/.test(v), wasNum = /^-?\d/.test(orig);
      if (wasNum && !isNum) return fail('This must be a number.');
      return run(() => saveInputChanges([[t.key, isNum ? v : JSON.stringify(v.replace(/^"|"$/g, ''))]]), v);
    }
    const raw = structuredClone(t.p.raw); let shown;
    if (t.kind === 'field') {
      let v = val('v');
      if (NUM.has(t.k)) { const n = Number(v.replace(/[$,]/g, '')); if (v === '' || !Number.isFinite(n) || n < 0) return fail('This must be a number.'); v = n; }
      if (v === '' && !(t.k in raw)) return form.cancel();
      raw[t.k] = v; shown = String(v);
    } else if (t.kind === 'buy') {
      const b = { store: val('store'), link: val('link'), price: val('price') };
      if (!b.store || !/^https:\/\/\S+$/.test(b.link)) return fail('A shop name and a link starting with https:// are needed.');
      raw.buy = [...(raw.buy || [])]; raw.buy[t.i] = b; shown = `${b.store}, ${b.price}`;
    } else {
      const r = { cite: val('cite'), link: val('link'), says: val('says') };
      if (!r.cite || !/^https:\/\/\S+$/.test(r.link)) return fail('A name and a link starting with https:// are needed.');
      raw.refs = [...(raw.refs || [])]; raw.refs[t.i] = r; shown = `${r.cite}: ${r.says}`;
    }
    run(() => savePart(t.p, raw), shown);
  };
}
async function savePart(p, raw) {
  const sha = await saveFile('data/parts.toml', t => replacePart(t, raw), `Edit ${raw.id}`);
  if (!sha) { say('Nothing changed.', 'ok'); return false; }
  p.raw = raw; follow(sha, raw.name); return true;
}
// ---------- orders (data/orders.toml): what we have ordered and what has arrived
const OSTATE = { 'to order': 'To order', ordered: 'Ordered', arrived: 'Arrived', 'have it': 'Have it' };
async function saveOrder(key, st) {
  if (!/^[a-z0-9_]+$/.test(key)) throw new Error('bad item id');
  const by = String(editor || '').replace(/[^\w .,'-]/g, '').slice(0, 40), date = new Date().toISOString().slice(0, 10);
  const line = st === 'to order' ? '' : `${key} = { state = "${st}", date = "${date}", by = "${by}" }`;
  const sha = await saveFile('data/orders.toml', t => {
    const re = new RegExp(`^${key} = .*\n?`, 'm');
    if (re.test(t)) return t.replace(re, line ? line + '\n' : '');
    return line ? t.replace(/\n*$/, '\n') + line + '\n' : t;
  }, `Mark ${key} ${st}`);
  if (!sha) { say('Nothing changed.', 'ok'); return false; }
  follow(sha, `${key.replace(/_/g, ' ')}: ${OSTATE[st].toLowerCase()}`); return true;
}
// buy page: show only some states
document.querySelectorAll('.ofilter [data-show]').forEach(b => b.addEventListener('click', () => {
  const v = b.dataset.show;
  document.querySelectorAll('.ofilter [data-show]').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
  document.querySelectorAll('table.buy tbody tr').forEach(tr => {
    const s = tr.querySelector('[data-order]')?.dataset.state.replace(' ', '-') || null;
    tr.hidden = v !== 'all' && !(s === v || (v === 'arrived' && s === 'have-it'));
  });
}));

// ---------- the pencil before logging in: say so, with a button to log in
function selOf(f) {
  const q = (a, v) => `[${a}="${CSS.escape(v)}"]`;
  const key = f.closest('#inputs tr[data-key]'); if (key) return `#inputs tr${q('data-key', key.dataset.key)} .val`;
  const scope = f.closest('#detail') ? '#detail ' : (f.closest('tr[data-id]') ? `tr${q('data-id', f.closest('tr[data-id]').dataset.id)} ` : '');
  for (const a of ['order', 'f', 'buy', 'ref']) if (f.dataset[a] != null) return scope + q('data-' + a, f.dataset[a]);
  return null;
}
function loginPrompt(pen) {
  document.querySelectorAll('.loginpop').forEach(x => x.remove());
  const f = pen.closest(EDITABLE); if (!f) return;
  pen.insertAdjacentHTML('afterend', '<span class="loginpop" role="status">Log in to edit. <button type="button" class="go">Log in</button> <button type="button" class="plainbtn no">Not now</button></span>');
  const pop = pen.nextElementSibling;
  pop.addEventListener('click', e => e.stopPropagation());
  pop.querySelector('.no').onclick = () => pop.remove();
  pop.querySelector('.go').onclick = () => {
    pending = selOf(f); pop.remove(); login();
    if (!editing) { bar.scrollIntoView({ block: 'center', behavior: 'smooth' }); setTimeout(() => document.getElementById('edName')?.focus({ preventScroll: true }), 400); }
  };
  pop.querySelector('.go').focus();
}
decorate(document.body);                                    // pencils show for everyone; editing needs a login
window.RB = Object.assign(window.RB || {}, { decorate });

async function recentEdits() {
  const list = document.getElementById('editlist'); if (!list) return;
  try {
    const get = path => fetch(`${API}/commits?path=${path}&per_page=10`).then(r => r.ok ? r.json() : []);
    const seen = new Set();
    const all = [...await get('data/parts.toml'), ...await get('data/inputs.toml'), ...await get('data/orders.toml')].filter(c => !seen.has(c.sha) && seen.add(c.sha))
      .sort((a, b) => new Date(b.commit.author.date) - new Date(a.commit.author.date)).slice(0, 12);
    if (!all.length) { list.innerHTML = '<li class="quiet">No edits yet.</li>'; return; }
    list.innerHTML = all.map(c => {
      const msg = c.commit.message.split('\n')[0], who = (msg.match(/\(by ([^,]+), on the website\)/) || [])[1] || c.commit.author.name;
      const when = new Date(c.commit.author.date).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      return `<li><span class="when">${esc(when)}</span> <b>${esc(who)}</b>: ${esc(msg.replace(/ \(by [^)]*\)$/, '').replace(/ on the website$/, ''))}
        <a href="${c.html_url}" target="_blank" rel="noopener">what changed</a> <button type="button" class="plainbtn undo" data-sha="${c.sha}" hidden>Undo</button></li>`;
    }).join('');
    showUndo(editing);
    list.addEventListener('click', async e => {
      const b = e.target.closest('.undo'); if (!b) return;
      if (!confirm('Put the file back as it was before this change?')) return;
      b.disabled = true; b.textContent = 'Undoing…';
      try { const r = await relay({ op: 'undo', sha: b.dataset.sha }); follow(r.commit, 'the undo'); }
      catch (x) { b.textContent = 'Could not undo'; say(esc(x.message.slice(0, 160)), 'bad'); }
    });
  } catch { list.innerHTML = '<li class="quiet">Could not load the history; see it on GitHub.</li>'; }
}
function showUndo(on) { document.querySelectorAll('#editlist .undo').forEach(b => { b.hidden = !(on && viaRelay()); }); }
recentEdits();
