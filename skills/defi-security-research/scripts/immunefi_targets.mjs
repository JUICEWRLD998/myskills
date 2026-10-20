#!/usr/bin/env node
// Immunefi bounty-program door: fetch -> extract -> filter -> read scope (G10).
//
// Why Node and not Python: Python is BROKEN on this host (WindowsApps store shims; `python`,
// `python3` and `py` all fail to execute). Slither 0.11.6 is a standalone binary and works.
// Node 24 has fetch built in, so this needs zero dependencies.
//
// Why it works: immunefi.com renders client-side, so a plain fetch-and-parse sees nothing and the
// campaign previously recorded that as "cannot read Immunefi". The data IS in the first HTML
// response, inside the React Server Components stream as `self.__next_f.push([1,"<escaped json>"])`.
// Unescape it and the full program list is there, including the two fields that decide whether a
// program is worth a pass: `kyc` and `maxBounty`.
//
// Usage:
//   node immunefi_targets.mjs                        # top Solidity/no-KYC targets by max bounty
//   node immunefi_targets.mjs --all                  # all 175 with kyc + bounty columns
//   node immunefi_targets.mjs --fresh 60             # only scopes updated within N days
//   node immunefi_targets.mjs --json out.json        # also write the parsed rows
//   node immunefi_targets.mjs --scope "Pareto Credit" # G10: scope, reward table, in-scope assets
//   node immunefi_targets.mjs --url <page>           # dump one page's raw RSC payload

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

function extractArray(text, key) {
  const at = text.indexOf('"' + key + '":[');
  if (at < 0) throw new Error(`array key not found: "${key}" — page shape changed, re-inspect the RSC payload`);
  const start = text.indexOf('[', at);
  let depth = 0, inStr = false, esc = false;
  for (let i = start; i < text.length; i++) {
    const c = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === '\\') esc = true;
      else if (c === '"') inStr = false;
      continue;
    }
    if (c === '"') inStr = true;
    else if (c === '[' || c === '{') depth++;
    else if (c === ']' || c === '}') { depth--; if (depth === 0) return text.slice(start, i + 1); }
  }
  throw new Error('unterminated array for key: ' + key);
}

function parseRscPayload(html) {
  const chunks = [];
  const re = /self\.__next_f\.push\(\[1,\s*"([\s\S]*?)"\]\)/g;
  let m;
  while ((m = re.exec(html))) chunks.push(m[1]);
  if (!chunks.length) throw new Error('no RSC chunks found — page may have changed or been blocked');
  return chunks.join('').replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\u002F/g, '/');
}

// These keys occur once per program page, so a targeted match is safe.
function scalar(payload, key) {
  const m = payload.match(new RegExp('"' + key + '":("(?:[^"\\\\]|\\\\.)*"|null|true|false|-?[\\d.]+)'));
  if (!m) return undefined;
  const v = m[1];
  if (v === 'null') return null;
  if (v === 'true') return true;
  if (v === 'false') return false;
  if (v.startsWith('"')) return v.slice(1, -1);
  return Number(v);
}

function fmtUsd(n) { return n == null ? 'n/a' : '$' + Number(n).toLocaleString(); }
function day(v) { return v ? String(v).slice(0, 10) : '?'; }
function stripTags(s) { return String(s).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim(); }

async function get(url) {
  const r = await fetch(url, { headers: { 'user-agent': UA, accept: 'text/html' } });
  if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
  return r.text();
}

async function loadList() {
  const payload = parseRscPayload(await get('https://immunefi.com/bug-bounty/'));
  const programs = JSON.parse(extractArray(payload, 'bounties'));
  return programs.map((p) => ({
    project: p.project,
    slug: p.slug,
    // p.url is present for every program ("/bug-bounty/<slug>/information/"). Use it rather than
    // constructing a URL — guessed slugs 404 (Pareto is "pareto", TermMax "termstructurelabs").
    url: 'https://immunefi.com' + (p.url || `/bug-bounty/${p.slug}/information/`),
    kyc: p.kyc === true,
    maxBounty: Number(p.maxBounty) || 0,
    launched: day(p.launchDate),
    updated: day(p.updatedDate),
    languages: (p.tags && p.tags.language) || [],
    productType: (p.tags && p.tags.productType) || [],
    projectType: (p.tags && p.tags.projectType) || [],
    ecosystems: (p.tags && p.tags.ecosystem) || [],
    immunefiStandard: p.immunefiStandard === true,
  }));
}

// Resolve a project name / slug / URL to a program page. A fuzzy hit SELECTS rather than erroring.
async function resolveTarget(target) {
  if (/^https?:/.test(target)) return target;
  const list = await loadList();
  const want = String(target).toLowerCase();
  const hit =
    list.find((p) => p.slug === want) ||
    list.find((p) => p.project.toLowerCase() === want) ||
    list.find((p) => p.project.toLowerCase().includes(want)) ||
    list.find((p) => p.slug.includes(want));
  if (!hit) {
    const near = list.filter((p) => p.project.toLowerCase().includes(want));
    const msg = near.length
      ? `did you mean: ${near.map((p) => `${p.project} (${p.slug})`).join(', ')}`
      : 'no match — run without --scope to list all programs';
    throw new Error(`no program match for "${target}" — ${msg}`);
  }
  return hit.url;
}

async function scopeRead(target) {
  const url = await resolveTarget(target);
  const payload = parseRscPayload(await get(url));

  console.log('=== G10 SCOPE READ ===');
  console.log('url:', url);

  const m = {
    kyc: scalar(payload, 'kyc'),
    kycLevel: scalar(payload, 'kycLevel'),
    maxBounty: scalar(payload, 'maxBounty'),
    pausedAt: scalar(payload, 'pausedAt'),
    pausedMessage: scalar(payload, 'pausedMessage'),
    endDate: scalar(payload, 'endDate'),
    launchDate: scalar(payload, 'launchDate'),
    updatedDate: scalar(payload, 'updatedDate'),
    rewardsToken: scalar(payload, 'rewardsToken'),
    rewardsTokenNetwork: scalar(payload, 'rewardsTokenNetwork'),
    proofOfConcept: scalar(payload, 'proofOfConceptType'),
    attackTimeInterval: scalar(payload, 'attackTimeInterval'),
    reductionPercentage: scalar(payload, 'reductionPercentage'),
  };

  const open = !m.pausedAt && !m.endDate;
  console.log('\n--- gate ---');
  console.log('  status            :', open ? 'OPEN' : `CLOSED (pausedAt=${m.pausedAt} endDate=${m.endDate})`);
  if (!open && m.pausedMessage) console.log('  paused message    :', stripTags(m.pausedMessage).slice(0, 200));
  console.log('  KYC               :', m.kyc ? `REQUIRED${m.kycLevel ? ' (level ' + m.kycLevel + ')' : ''}` : 'NOT required');
  console.log('  PoC               :', m.proofOfConcept || 'n/a');
  console.log('  max bounty        :', fmtUsd(m.maxBounty));
  console.log('  payout token      :', m.rewardsToken || 'n/a', m.rewardsTokenNetwork ? '(' + m.rewardsTokenNetwork + ')' : '');
  console.log('  attack window     :', m.attackTimeInterval != null ? m.attackTimeInterval + 'h' : 'n/a');
  if (m.reductionPercentage != null) console.log('  reward reduction  :', m.reductionPercentage + '%');
  console.log('  launched / updated:', day(m.launchDate), '/', day(m.updatedDate));

  // Severity -> payout. This decides whether the bug class you can actually find is worth finding.
  const rw = JSON.parse(extractArray(payload, 'programRewards'));
  const order = { critical: 0, high: 1, medium: 2, low: 3, none: 4 };
  console.log('\n--- pays for (severity -> max) ---');
  for (const r of rw.slice().sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9))) {
    const pct = r.rewardCalculationPercentage ? `  (${r.rewardCalculationPercentage}% of funds at risk)` : '';
    console.log('  ' + String(r.severity).padEnd(9), String(r.assetType || '').padEnd(15),
      fmtUsd(r.maxReward).padStart(12), ' ' + (r.rewardModel || ''), pct);
  }
  const sev = new Set(rw.map((r) => r.severity));
  if (!sev.has('critical') && !sev.has('high')) {
    console.log('\n  !! NO critical/high tier — cannot pay for a serious bug. G10 FAILS.');
  }

  // The in-scope assets: the actual list of contracts you are permitted to audit.
  const assets = JSON.parse(extractArray(payload, 'assets'));
  console.log(`\n--- in-scope assets (${assets.length}) ---`);
  const byType = {};
  for (const a of assets) (byType[a.type] = byType[a.type] || []).push(a);
  for (const [t, list] of Object.entries(byType)) {
    console.log(`\n  [${t}] ${list.length}`);
    for (const a of list.slice(0, 60)) {
      const flags = [a.isSafeHarbor && 'SafeHarbor', a.isPrimacyOfImpact && 'PrimacyOfImpact'].filter(Boolean).join(',');
      console.log('    ' + day(a.addedAt), (a.url || '') + (a.description ? ' — ' + a.description : '') + (flags ? '  [' + flags + ']' : ''));
    }
    if (list.length > 60) console.log(`    ... ${list.length - 60} more`);
  }

  // Scope additions are the hunter's edge — everyone is at the same starting line on new code.
  const recent = assets.filter((a) => a.addedAt && a.addedAt >= new Date(Date.now() - 30 * 864e5).toISOString());
  if (recent.length) {
    console.log(`\n--- added to scope in the last 30d (${recent.length}) — freshest code ---`);
    for (const a of recent) console.log('  ' + day(a.addedAt), a.url, a.description ? '— ' + a.description : '');
  }

  const audits = JSON.parse(extractArray(payload, 'audits'));
  console.log('\n--- prior audits listed:', audits.length, '---');
  for (const a of audits.slice(0, 15)) console.log('  ', a.auditUrl || a.url || JSON.stringify(a).slice(0, 120));

  const oos = scalar(payload, 'customOutOfScopeInformation');
  if (oos && typeof oos === 'string') {
    console.log('\n--- out of scope (custom) ---');
    console.log('  ' + stripTags(oos).slice(0, 900));
  }
}

async function listPrograms() {
  const args = process.argv.slice(2);
  const flag = (n) => args.includes('--' + n);
  const val = (n) => { const i = args.indexOf('--' + n); return i >= 0 ? args[i + 1] : null; };

  const rows = await loadList();

  const jsonOut = val('json');
  if (jsonOut) { const fs = await import('fs'); fs.writeFileSync(jsonOut, JSON.stringify(rows, null, 2)); }

  const solidity = rows.filter((r) => r.languages.some((l) => /solidity|vyper/i.test(l)));
  const noKyc = rows.filter((r) => !r.kyc);
  const freshDays = val('fresh') ? Number(val('fresh')) : null;
  const cutoff = freshDays ? new Date(Date.now() - freshDays * 864e5).toISOString().slice(0, 10) : null;

  let actionable = solidity.filter((r) => !r.kyc);
  if (cutoff) actionable = actionable.filter((r) => r.updated >= cutoff);
  actionable.sort((a, b) => b.maxBounty - a.maxBounty);

  console.log('=== IMMUNEFI DOOR (fetched live) ===');
  console.log('  programs total        :', rows.length);
  console.log('  Solidity / Vyper      :', solidity.length);
  console.log('  KYC NOT required      :', noKyc.length);
  console.log('  Solidity AND no-KYC   :', solidity.filter((r) => !r.kyc).length,
    cutoff ? `(updated >= ${cutoff}: ${actionable.length})` : '');
  console.log('');

  const show = flag('all') ? rows.slice().sort((a, b) => b.maxBounty - a.maxBounty) : actionable;
  console.log('  ' + 'maxBounty'.padStart(13), 'kyc'.padEnd(9), 'launched'.padEnd(11), 'updated'.padEnd(11), 'project');
  for (const r of show.slice(0, 60)) {
    console.log('  ' + fmtUsd(r.maxBounty).padStart(13), (r.kyc ? 'REQUIRED' : 'no').padEnd(9),
      r.launched.padEnd(11), r.updated.padEnd(11),
      r.project + (r.productType.length ? '  [' + r.productType.join('/') + ']' : ''));
  }

  console.log('\nNext: G10 the payment-channel gate. Read a program\'s scope + reward table with:');
  console.log('  node immunefi_targets.mjs --scope "<project name>"');
  console.log('Duplicate cost matters too — scan submission fees with:');
  console.log('  node immunefi_targets.mjs --nofee');
}

// Duplicate-pressure scan: which programs charge per submission?
//
// isPayToSubmit / payToSubmitFeeUsdc are per-program. A program that charges a fee per submission
// makes a duplicate cost MONEY; a free program makes it cost only time. Since duplicate risk rises
// with program age and scope size, the useful board is: no KYC + no submission fee + fresh + narrow.
async function noFeeScan() {
  const rows = (await loadList()).filter((r) => r.languages.some((l) => /solidity|vyper/i.test(l)) && !r.kyc);
  rows.sort((a, b) => b.maxBounty - a.maxBounty);

  console.log(`=== SUBMISSION-FEE SCAN (${rows.length} Solidity + no-KYC programs) ===`);
  console.log('Fetching each program page for isPayToSubmit / payToSubmitFeeUsdc...\n');

  const out = [];
  for (const r of rows) {
    try {
      const p = parseRscPayload(await get(r.url));
      const pay = scalar(p, 'isPayToSubmit');
      const fee = scalar(p, 'payToSubmitFeeUsdc');
      const paused = scalar(p, 'pausedAt');
      out.push({ ...r, payToSubmit: pay === true, fee: typeof fee === 'number' ? fee : null, paused: !!paused });
    } catch (e) {
      out.push({ ...r, payToSubmit: null, fee: null, paused: null, err: e.message });
    }
    await new Promise((k) => setTimeout(k, 120));
  }

  const fmt = (r) => [
    fmtUsd(r.maxBounty).padStart(13),
    (r.payToSubmit === null ? 'ERR' : r.payToSubmit ? 'FEE $' + (r.fee ?? '?') : 'free').padEnd(11),
    r.updated.padEnd(11),
    r.project + (r.productType.length ? '  [' + r.productType.join('/') + ']' : ''),
  ].join(' ');

  const free = out.filter((r) => r.payToSubmit === false && !r.paused).sort((a, b) => b.maxBounty - a.maxBounty);
  const paid = out.filter((r) => r.payToSubmit === true && !r.paused).sort((a, b) => b.maxBounty - a.maxBounty);
  const errs = out.filter((r) => r.payToSubmit === null);
  const dead = out.filter((r) => r.paused);

  console.log(`### FREE TO SUBMIT (${free.length}) — a duplicate costs TIME, not money. Prefer these.`);
  console.log('  ' + 'maxBounty'.padStart(13), 'fee'.padEnd(11), 'updated'.padEnd(11), 'project');
  for (const r of free) console.log('  ' + fmt(r));

  console.log(`\n### CHARGES PER SUBMISSION (${paid.length}) — a duplicate costs money. Deprioritise unless scope is very fresh.`);
  console.log('  ' + 'maxBounty'.padStart(13), 'fee'.padEnd(11), 'updated'.padEnd(11), 'project');
  for (const r of paid) console.log('  ' + fmt(r));

  if (dead.length) { console.log(`\n### PAUSED (${dead.length})`); for (const r of dead) console.log('  ' + fmt(r)); }
  if (errs.length) { console.log(`\n### FETCH ERRORS (${errs.length}) — NOT negative results`); for (const r of errs) console.log('  ' + fmt(r), r.err || ''); }

  console.log('\nNote: fee status is read from the live program page and can change. Re-run before relying on it.');
  console.log('Cross-check with duplicate mitigations: a scope whose assets are PrimacyOfImpact, and a');
  console.log('scope updated recently, both reduce duplicate pressure (see --scope output).');
}

async function main() {
  const args = process.argv.slice(2);
  const val = (n) => { const i = args.indexOf('--' + n); return i >= 0 ? args[i + 1] : null; };

  // Return from main() rather than process.exit(): exiting while a fetch handle is still closing
  // trips a libuv assertion on Windows ("UV_HANDLE_CLOSING ... async.c").
  if (args.includes('--scope')) {
    const t = val('scope');
    if (!t) throw new Error('usage: --scope <project name | slug | full url>');
    await scopeRead(t);
    return;
  }
  if (args.includes('--url')) {
    const u = val('url');
    if (!u) throw new Error('usage: --url <page url>');
    console.log(parseRscPayload(await get(u)).slice(0, 6000));
    return;
  }
  if (args.includes('--nofee')) { await noFeeScan(); return; }
  await listPrograms();
}

await main().catch((e) => {
  console.error('ERROR:', e.message);
  process.exitCode = 1;
});
