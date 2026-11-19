// Ridgeback site editing relay (Google Apps Script web app).
// Lets team members save edits from the website with a shared team passcode instead of their own GitHub token.
// It can only change data/parts.toml and data/inputs.toml in the one repository below; every save is a normal
// commit (with the editor's name in the message) and can be undone from the GitHub history.
// Setup: tools/relay/SETUP.md. Script properties: GITHUB_TOKEN (required), PASSCODE (team passcode; empty = anyone).

const REPO = 'guinterface/skyrunners-ridgeback';
const ALLOWED = ['data/parts.toml', 'data/inputs.toml'];
const MAX_BYTES = 400000;          // parts.toml is ~60 kB; refuses anything wildly larger
const MAX_SAVES_PER_HOUR = 60;
const MAX_WRONG_PASSCODES = 20;    // per 10 minutes, for everyone together; then the relay refuses all requests for 10 minutes

function doPost(e) {
  try {
    const q = JSON.parse(e.postData.contents);
    const props = PropertiesService.getScriptProperties();
    const pass = props.getProperty('PASSCODE') || secret('PASSCODE');
    const cache = CacheService.getScriptCache();
    const wrong = Number(cache.get('wrong') || 0);
    if (wrong >= MAX_WRONG_PASSCODES) return out({ error: 'Too many wrong passcodes; editing is paused for 10 minutes.', status: 429 });
    if (pass && q.pass !== pass) { cache.put('wrong', String(wrong + 1), 600); return out({ error: 'Wrong team passcode.', status: 401 }); }
    if (q.op === 'check') return out({ ok: true });
    if (q.op === 'read') { allowed(q.path); return out(readFile(q.path)); }
    if (q.op === 'status') return out(status(String(q.sha || '')));
    if (q.op === 'save') {
      allowed(q.path);
      // The commit message is built here from safe pieces only (never taken from the request).
      const name = String(q.name || '').replace(/[^\w .,'-]/g, '').slice(0, 40).trim() || 'someone';
      const what = String(q.what || '').replace(/[^\w ,-]/g, '').slice(0, 80).trim();
      if (typeof q.text !== 'string' || q.text.length > MAX_BYTES) throw err('The file is too large.', 413);
      rateLimit();
      const body = {
        message: (q.path === 'data/inputs.toml' ? 'Change design numbers' : 'Edit part') + (what ? ' ' + what : '') + ' (by ' + name + ', on the website)',
        content: Utilities.base64Encode(q.text, Utilities.Charset.UTF_8), sha: q.sha, branch: 'main',
      };
      const r = gh('put', '/contents/' + q.path, body);
      return out({ commit: r.commit.sha });
    }
    if (q.op === 'undo') {                       // put a file back as it was before one commit, if nobody changed it since
      const sha = String(q.sha || '');
      if (!/^[0-9a-f]{40}$/.test(sha)) throw err('Bad commit id.', 400);
      const name = String(q.name || '').replace(/[^\w .,'-]/g, '').slice(0, 40).trim() || 'someone';
      const c = gh('get', '/commits/' + sha);
      const files = (c.files || []).filter(function (f) { return ALLOWED.indexOf(f.filename) >= 0; });
      if (files.length !== 1) throw err('That change cannot be undone from the website.', 400);
      const path = files[0].filename, now = gh('get', '/contents/' + path + '?ref=main');
      if (now.sha !== files[0].sha) throw err('Someone changed this file after that edit; undo it by hand (see the history).', 409);
      const before = gh('get', '/contents/' + path + '?ref=' + c.parents[0].sha);
      rateLimit();
      const r = gh('put', '/contents/' + path, { message: 'Undo ' + sha.slice(0, 7) + ' (by ' + name + ', on the website)', content: before.content.replace(/\n/g, ''), sha: now.sha, branch: 'main' });
      return out({ commit: r.commit.sha });
    }
    throw err('Unknown request.', 400);
  } catch (x) {
    return out({ error: String(x.message || x), status: x.status || 500 });
  }
}

function doGet() { return out({ ok: true, what: 'Ridgeback site editing relay; use POST.' }); }

function readFile(path) {
  const f = gh('get', '/contents/' + path + '?ref=main&t=' + Date.now());
  return { sha: f.sha, text: Utilities.newBlob(Utilities.base64Decode(f.content.replace(/\n/g, ''))).getDataAsString('UTF-8') };
}

function status(sha) {
  if (!/^[0-9a-f]{40}$/.test(sha)) throw err('Bad commit id.', 400);
  const runs = gh('get', '/actions/runs?head_sha=' + sha).workflow_runs || [];
  const run = runs.find(function (r) { return r.name.indexOf('Rebuild') === 0; });
  let pages = null;
  try { pages = gh('get', '/pages/builds/latest'); } catch (x) { /* not visible: fine */ }
  return {
    run: run ? { status: run.status, conclusion: run.conclusion, html_url: run.html_url, updated_at: run.updated_at } : null,
    pages: pages ? { status: pages.status, updated_at: pages.updated_at } : null,
  };
}

function allowed(path) { if (ALLOWED.indexOf(path) < 0) throw err('This file cannot be edited from the website.', 403); }

function rateLimit() {
  const c = CacheService.getScriptCache();
  const n = Number(c.get('saves') || 0);
  if (n >= MAX_SAVES_PER_HOUR) throw err('Too many saves this hour; try again later.', 429);
  c.put('saves', String(n + 1), 3600);
}

function gh(method, path, body) {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN') || secret('GITHUB_TOKEN');
  if (!token) throw err('The relay has no GitHub token yet (see tools/relay/SETUP.md).', 500);
  const opt = { method: method, muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' } };
  if (body) { opt.contentType = 'application/json'; opt.payload = JSON.stringify(body); }
  const r = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + path, opt);
  const code = r.getResponseCode(), text = r.getContentText();
  if (code >= 300) throw err(code + ' ' + text.slice(0, 200), code);
  return JSON.parse(text);
}

// Values may also come from a private Secrets.gs in the Apps Script project (never in this repository):
//   const SECRETS = { GITHUB_TOKEN: 'github_pat_...', PASSCODE: '...' };
function secret(k) { return (typeof SECRETS !== 'undefined' && SECRETS[k]) || ''; }
function err(msg, status) { const e = new Error(msg); e.status = status; return e; }
function out(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
