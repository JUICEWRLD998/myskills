# Benchmarking / adopting a third-party auditor's playbook repo

Class of work: the user points at someone else's audit operations repo (a peer auditor, a team,
a firm's public kit) and asks *is the whole method actually in there, is it detailed enough to
adopt, and should we switch tooling to theirs?* Validated 2026-09-14 on
`github.com/Savage27z/SAVAGEAUD` (1,169 files / 152 commits / 2026-07-22 → 2026-09-14).

Deliverable shape (this user): the full clone on disk + **ONE clean catalogue file**
(index + detail + reject reasons) + a ranked/verdict report in chat. He reads the catalogue, then
decides — never auto-start the audit or assume his pick.

## Procedure

1. **Clone with real history, into the workspace, not a temp dir.** `git clone` then
   `git fetch --unshallow` (or `--depth 50` first only if you know you want the tail). Why it
   matters: the commit SUBJECTS are themselves a lesson corpus ("an empty scan result and a broken
   scanner are indistinguishable from inside"), and the author prefix in history tells you which
   agent actually wrote it (`claude:` = Claude Code). Save the clone somewhere durable
   (`Desktop/audits/<NAME>_repo`) — the user may want to run it.
2. **Read the doctrine in the order the repo itself prescribes.** Any serious ops repo names its
   entry file (`CLAUDE.md` / `AGENTS.md` / `README.md` → "read this first"). Follow that chain
   completely before forming an opinion; the entry file usually points at a *canonical* workflow
   file and declares the rest "implementation detail underneath it".
3. **Read the per-target artifacts, not just the doctrine.** The doctrine says what should happen;
   one filled example (`TARGETS/<n>/spec.json`, a findings file, a fork harness, a draft
   disclosure email) shows what actually happens. Pull counts/status programmatically rather than
   eyeballing (`json.load` the spec: sections closed vs total, invariants checked/blocked,
   never-should-happen results).
4. **Then check what is NOT there.** Grep/ls for the layer that turns method into execution:
   `find . -iname '*SKILLS*' -o -iname '*prompt*' -o -iname 'AGENTS.md' -o -iname '.claude*'`.
   Typical result: the methodology text is rich but "run 6 independent agent perspectives" is a
   DIRECTIVE with no agent definitions, and the skills/tools it names live in external repos or a
   machine-local path (`/root/.hermes/workspace/evm-cortex/`). That gap is the single most
   important thing to report — it decides whether the playbook is adoptable as-is or needs us to
   supply the orchestration layer.
5. **Verify every external dependency actually exists** (one `web_search` each, batched). Name
   what you could NOT verify as unverified rather than repeating it as fact — a referenced triage
   framework repo returned zero search results and was reported as "treat these gates as prose,
   not as a tool".
6. **Read `.gitignore` as intent.** What is deliberately withheld (keys, PK-bearing scripts,
   browser profiles, scan results) tells you the boundary between the public playbook and the
   operator's private edge.
7. **Windows checkout caveat:** `TARGETS/<name>` entries that are symlinks to root-level dirs
   degrade to 8-byte text files. Nothing is lost (the real dirs sit at the root of the same name),
   but say so instead of reporting missing code.

## How to report the verdict honestly

- Lead with a two-line verdict table: *is the METHOD in there and well detailed* / *is the AGENT
  layer in there* / *is the money side (disclosure, negotiation, payout) in there*.
- Give discovery its own section with the filters, the DRIFT between documented and actual filters,
  and the per-target evidence ("found via the post-X sweep: 8,243 protocols → 130 candidates →
  decided by source readability").
- **Read the track record, don't inherit the reputation.** Count what the repo itself shows:
  how many targets ended clean vs findings, WHEN the first reportable findings landed, and whether
  any team response or payment is recorded anywhere. If there is no payment record, say "no payment
  record" plainly — a well-organised repo is not a proven earner, and the user's own success
  criterion is exploitable bugs in the team's code.
- **Separate ADOPT / ADAPT / SKIP** at the end, each item one line with the reason. The most
  useful ADAPT lines come from where their rubric and ours diverge (e.g. their owner-gated rule →
  keep for submissions, but keep owner-reachable paths in the spec as coverage gaps).
- Flag tooling honestly: the repo being Claude-native is a FILE-NAME fact (`CLAUDE.md` is Claude
  Code's auto-loaded context), not a content fact — the content is plain markdown and works with
  any agent. Do not recommend switching tools for cosmetics; recommend whichever tool gives the
  fan-out the method needs.

## Reusable finding from the worked example

The peer's own stated rule — **the filter that decides a candidate is SOURCE READABILITY, not TVL**
— independently matches our shortlist gate (a), full-fleet source verification. Treat a candidate
that cannot be source-verified as capped at black-box work and de-prioritise it, exactly as they
de-prioritised Monad for having no free verified-source route.
