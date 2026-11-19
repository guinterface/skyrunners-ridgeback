// Edit the site in place. Changes are saved to the GitHub repository (data/parts.toml, data/inputs.toml); GitHub then
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
  say(`<b>Editing.</b> ${document.getElementById('detail') ? 'Pick a part; its panel turns into a form.' : ''} ${document.getElementById('inputs') ? 'Change any value in the design numbers table, then press Save.' : ''}
    Saving writes data/parts.toml or data/inputs.toml on GitHub with your name; the sheets and pages rebuild in about two minutes. Every save is a commit in <a href="https://github.com/${REPO}/commits/main" target="_blank" rel="noopener">the history</a>, so it can be undone. <button type="button" id="forget" class="plainbtn">${viaRelay() ? 'Sign out' : 'Forget my token'}</button>`);
  document.getElementById('forget').onclick = () => { store.set('rb-token', null); store.set('rb-pass', null); try { sessionStorage.removeItem('rb-token'); } catch { } token = null; pass = null; stop(); };
  window.RB?.rerender?.();
  inputsMode(true); showUndo(true);
}
function stop() {
  editing = false; btn.setAttribute('aria-pressed', 'false'); btn.textContent = 'Edit';
  document.body.classList.remove('editing'); bar.hidden = true;
  window.RB?.rerender?.();
  inputsMode(false); showUndo(false);
}
btn?.addEventListener('click', () => {
  if (editing) return stop();
  if (token) return start();
  if (!RELAY) return askToken();
  if (pass == null) return askPass();
  relay({ op: 'check' }).then(start, askPass);              // stored passcode: make sure it still works
});

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
  if (!editing) return false;
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
  form.querySelector('.cancel').onclick = () => stop();
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

// ---------- design numbers (calculations page)
function inputsMode(on) {
  const sec = document.getElementById('inputs'); if (!sec) return;
  sec.querySelectorAll('tr[data-key]').forEach(tr => {
    const td = tr.querySelector('.val');
    if (on && !td.querySelector('input')) { const v = td.textContent; td.dataset.orig = v; td.innerHTML = `<input value="${esc(v)}" size="8" aria-label="${esc(tr.cells[0].textContent)}">`; }
    if (!on && td.querySelector('input')) td.textContent = td.dataset.orig;
  });
  let save = document.getElementById('saveInputs');
  if (on && !save) {
    sec.insertAdjacentHTML('beforeend', '<p class="actions" id="saveInputs"><button type="button">Save changed numbers to GitHub</button> <span class="err" hidden></span></p>');
    save = document.getElementById('saveInputs');
    save.querySelector('button').onclick = saveInputs;
  }
  if (!on && save) save.remove();
}
async function saveInputs() {
  const err = document.querySelector('#saveInputs .err'); err.hidden = true;
  const changes = [];
  for (const tr of document.querySelectorAll('#inputs tr[data-key]')) {
    const td = tr.querySelector('.val'), inp = td.querySelector('input'); if (!inp) continue;
    const v = inp.value.trim(); if (v === td.dataset.orig) continue;
    const isNum = /^-?\d+(\.\d+)?([eE]-?\d+)?$/.test(v), wasNum = /^-?\d/.test(td.dataset.orig);
    if (wasNum && !isNum) { err.textContent = `“${tr.cells[0].textContent}” must be a number.`; err.hidden = false; return; }
    changes.push([tr.dataset.key, isNum ? v : JSON.stringify(v.replace(/^"|"$/g, ''))]);
  }
  if (!changes.length) { say('Nothing changed.', 'ok'); return; }
  try {
    const sha = await saveFile('data/inputs.toml', t => changes.reduce((s, [k, v]) => s.replace(new RegExp(`^(${k} = )(.+?)(\\s+#.*)?$`, 'm'), (m, a, b, c) => a + v + (c || '')), t),
      `Change ${changes.map(c => c[0]).join(', ')}`);
    if (sha) follow(sha, changes.map(c => c[0]).join(', '));
  } catch (x) { err.textContent = 'Could not save: ' + x.message.slice(0, 160); err.hidden = false; }
}

// ---------- recent edits (files page): public GitHub history of the two data files, with Undo through the relay
async function recentEdits() {
  const list = document.getElementById('editlist'); if (!list) return;
  try {
    const get = path => fetch(`${API}/commits?path=${path}&per_page=10`).then(r => r.ok ? r.json() : []);
    const seen = new Set();
    const all = [...await get('data/parts.toml'), ...await get('data/inputs.toml')].filter(c => !seen.has(c.sha) && seen.add(c.sha))
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
