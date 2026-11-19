# Editing without a GitHub account: the relay (one-time setup, about 10 minutes)

The website's Edit button can save with a **team passcode** instead of each person's GitHub token. The page sends the
edit to a small Google Apps Script web app (`Code.gs` here), which holds one GitHub token and writes the change to
`data/parts.toml` or `data/inputs.toml`. Nothing else in the repository can be changed through it, saves are limited
to 60 an hour, and every save is a normal commit with the editor's name (the relay writes the commit message itself), so it can be undone from the history.

## 1. A GitHub token for the relay (repo admin)
1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token.
2. Resource owner: **guinterface** (your own account: no organization approval needed). Repository access: **Only select repositories → skyrunners-ridgeback**.
3. Repository permissions: **Contents: Read and write**, **Actions: Read-only**, **Pages: Read-only**. Expiry: up to a year.
4. Generate, copy the token (starts with `github_pat_`).
   The organisation may have to approve the token (Organization settings → Personal access tokens) before it works.
   Avoid a classic `public_repo` token: it can write to every public repository its owner can, not just this one.

## 2. The Apps Script web app (a club or personal Gmail account, not a Stanford one)
A Stanford Google account may not be allowed to publish a web app to "Anyone"; the page would then get a sign-in page
instead of an answer.
1. Go to https://script.google.com → **New project**. Name it "Ridgeback site relay".
2. Delete what is in `Code.gs` and paste the whole of `tools/relay/Code.gs` from this repository. Save.
3. Project Settings (gear) → **Script properties** → add `GITHUB_TOKEN` = the token from step 1, and
   `PASSCODE` = the team passcode: three or four random words, not a short word (share it in the club channel).
   Without a passcode anyone on the internet can edit. After 20 wrong passcodes in 10 minutes the relay pauses for 10 minutes.
4. **Deploy → New deployment** → type **Web app** → Execute as: **Me** → Who has access: **Anyone** → Deploy.
   Allow the permissions it asks for (it needs to "connect to an external service": that is GitHub).
5. Copy the **Web app URL** (`https://script.google.com/macros/s/…/exec`).

## 3. Turn it on
Paste the URL between the quotes of `const RELAY = '';` at the top of `docs/assets/edit.js` and push (or send the URL
to whoever maintains the site). From then on the Edit button asks only for a name and the passcode.

## Changing things later
- New passcode: edit the `PASSCODE` script property. No redeploy needed.
- After changing `Code.gs`: Deploy → Manage deployments → edit → Version: New version (the URL stays the same).
- Token expired: make a new one (step 1) and replace `GITHUB_TOKEN`.
- Check it is alive: open the Web app URL in a browser; it answers `{"ok":true,...}`.
