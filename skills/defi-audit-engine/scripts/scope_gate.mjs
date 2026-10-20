#!/usr/bin/env node
// scope_gate.mjs — refuse to proceed unless a target is written into SCOPE.md's "In Scope" section.
// Idea taken from DevCop95/bugbounty-lab101: mandatory scope file, no override flag.
// usage:  node scope_gate.mjs <SCOPE.md> <address|url|path-fragment>     exit 0 = in scope, 2 = blocked
//         node scope_gate.mjs --selftest
import fs from 'node:fs';

export function checkScope(md, target) {
  const t = target.trim().toLowerCase();
  if (!t) return { ok: false, why: 'empty target' };
  let section = null; const inn = [], out = [];
  for (const line of md.split(/\r?\n/)) {
    const h = line.match(/^#{1,6}\s*(.+?)\s*$/);
    if (h) {
      const name = h[1].toLowerCase();
      section = /out[\s-]*of[\s-]*scope|excluded|known issues|prohibited/.test(name) ? 'out'
              : /in[\s-]*scope|assets? in scope|scope/.test(name) ? 'in' : null;
      continue;
    }
    if (section === 'in') inn.push(line.toLowerCase());
    if (section === 'out') out.push(line.toLowerCase());
  }
  if (!inn.length) return { ok: false, why: 'SCOPE.md has no "In Scope" section entries — write scope first' };
  const hit = a => a.some(l => l.includes(t));
  if (hit(out)) return { ok: false, why: 'target appears in an out-of-scope/excluded section' };
  if (!hit(inn)) return { ok: false, why: 'target not listed under In Scope' };
  return { ok: true, why: 'listed in scope' };
}

if (process.argv[2] === '--selftest') {
  const md = '# Scope\n## In Scope\n- Vault 0xAbC123 (Ethereum)\n- https://github.com/x/y/tree/main/src\n## Out of Scope\n- 0xDEAD00 oracle\n';
  const cases = [
    ['0xabc123', true],             // positive control: listed, case-insensitive
    ['github.com/x/y/tree/main/src', true],
    ['0xdead00', false],            // negative control: excluded
    ['0xffffff', false],            // negative control: never listed
    ['', false],
  ];
  let bad = 0;
  for (const [t, want] of cases) { const r = checkScope(md, t); if (r.ok !== want) { bad++; console.error('SELFTEST FAIL', JSON.stringify(t), r); } }
  if (checkScope('# Notes\nnothing here\n', '0xabc').ok) { bad++; console.error('SELFTEST FAIL: no scope section must block'); }
  console.log(bad ? `selftest FAILED (${bad})` : 'selftest ok (5 target cases + missing-section case)');
  process.exit(bad ? 1 : 0);
}

const [, , file, target] = process.argv;
if (!file || !target) { console.error('usage: scope_gate.mjs <SCOPE.md> <target> | --selftest'); process.exit(64); }
if (!fs.existsSync(file)) { console.error(`BLOCKED: ${file} does not exist. Write the scope from the program page first. There is no override.`); process.exit(2); }
const r = checkScope(fs.readFileSync(file, 'utf8'), target);
console.log((r.ok ? 'SCOPE OK: ' : 'BLOCKED: ') + r.why);
process.exit(r.ok ? 0 : 2);
