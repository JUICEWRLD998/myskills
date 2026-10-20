# Verification-pass orchestration (parallel fan-out -> validated verdict set)

Validated 2026-09-10 on the R2 pass: 287 filtered candidates -> 56 shortlisted -> **40 protocols
verified at depth by 10 parallel agents** (4 each) -> 14 survivors / 26 kills -> Top-10 + catalogue.
This file is the machinery. The rubric lives in `r2-fund-loss-rubric.md`; the domain signals live in
`defillama-recon-playbook.md`; the two nasty pitfalls are in SKILL.md (rate-limit false negatives,
orphaned child jobs).

## Division of labour
- ORCHESTRATOR (never delegated): the DeFiLlama pull, all filtering, the DeFiLlama-adapter probe,
the scoring script, the cross-checks, the deliverables, and every write to a shared file.
- CHILDREN: one group of 3-4 protocols each, deep verification only (no hunting), one JSON file each.
Children cannot ask questions - the brief must be complete before dispatch.

## 1. Brief as a FILE, not as context
Write `AGENT_BRIEF.md` once (`recon/AGENT_BRIEF.md`) and put "read this file first" in every task.
It must contain: who is asking + why (so the child optimises for the right thing), the hard gates
with the exact evidence each needs, the output JSON shape, the evidence/UNKNOWN discipline, and the
SHARED-resource budget (unauth GitHub API = 60 req/hr/IP for ALL children combined -> cap ~12 calls
per child and mandate the HTML fallback). Without the file you repeat ~2k chars of brief per task and
the children drift apart on what "verified" means.

## 2. Seed inline, group by affinity
Fetch the metadata yourself (list + per-slug detail + adapter signals) and inline a seed line per
protocol: slug, name, category, chain, EVM TVL, listed date, url, DL audit string/links, GitHub hint,
plus any orchestrator finding to beat ("Longbow is a Morpho curator - confirm or refute"). Group so
each child works ONE ecosystem/toolchain (all Robinhood-Chain, all Ethereum lending, all exotic
chains, all vaults) - they then reuse one explorer technique instead of learning 4 chains.
Keep a reserve list: if the wave-1 survivors are thin you can fan out wave 2 without re-filtering.

## 3. Output contract: file + one-line reply
Children write `agents/G<N>.json` (JSON ARRAY of protocol objects) AND reply with one line each
(`slug | VERDICT | solidity | verified | audits | why`). The FILE is the deliverable - treat the reply
as a summary. Steer with the exact output path in the task text; one pass lost time because a goal
line and its context named different files (G7 vs G8).

## 4. Steering mid-run (this is how you save a half-broken wave)
`delegate_task(action='steer')` text lands on the child's NEXT tool result, so it works while the
child is deep in a loop. What actually needed steering: a tooling fix discovered after dispatch
(broadcast the SAME message to all 10 - "helper fixed, re-check anything you recorded as 403"), a
shortcut discovered after dispatch (the DeFiLlama-adapter trick), and output-path corrections.
Never steer with new scope - that is what wave 2 is for.

## 5. VALIDATE before aggregating
Run `scripts/validate_agent_outputs.py <recon_dir>` first: every `agents/G*.json` must parse, be a
list, and carry the required keys. Real cases that made this non-optional: a child reported success
while one write had been refused for JSON syntax (the refusal was an intermediate attempt and the
final file was sound - only a validation pass can tell you which), and helper files (`G3_bs.json`,
`_kumba_pools.json`) sit in the same directory and will break a naive `glob('agents/*.json')`.

## 6. Score deterministically, then override
Implement the rubric in a script (`score_r2.py`) so no arithmetic happens in your head. Two
guarantees it must have: (a) an AGENT-VERDICT SHORT-CIRCUIT - a child's REJECT must not resurface as
a high-scoring survivor just because its structured fields looked fine; (b) an `overrides.json` path
for orchestrator-verified facts that beat the child's report (my Longbow curator finding, my Twofold
correction after the agent's deeper source read).

## 7. Cross-check the top names YOURSELF
Child self-reports are leads, not facts. Re-verify the top contenders by direct fetch: verified
status + implementation address, the custody balance (`cast call balanceOf` / `cast balance`), the
ERC-1967 slot actually being a proxy or not, and the reserve getter the protocol itself exposes.
On this pass that caught: a probe "proxy" whose impl slot read 0x0, a fee collector that was really
a 1-of-1 Gnosis Safe (slot0 = SafeL2 singleton, `getThreshold()`=1), and GIGA's ApexVault/ApexController
being reported as failures when they were clean.

## 8. Deliverables (user preference - do not improvise this)
TWO artefacts, in this order:
1. `TARGET_SELECTION_REPORT_R2.txt` - ranked Top-10 (qualitative order + a RE-RANK NOTE whenever the
   qualitative order departs from the raw scores), Top-3 analysis, ONE primary recommendation, and a
   kill ledger naming the gate that killed each rejection.
2. `ALL_FINDINGS_<PASS>.md` - ONE consolidated readable catalogue of EVERY verified protocol,
   generated from the JSONs by `scripts/build_findings_catalogue.py`: index table grouped by verdict
   (with a column mapping to the Top-10 rank, because index order != ranking order), full detail on
   the survivors (contracts with OK/UNV flags, every audit with firm/date/scope/url, the gap note,
   custody, own code, numbered loss-of-funds hypotheses, evidence URLs), then the rejections with
   their reasons, then method/provenance/caveats.
The user reads the catalogue and verifies the protocols himself BEFORE naming a target. Never assume
his pick, never pre-empt him into Phase 6, and label each claim `[ORCHESTRATOR-VERIFIED]` vs
agent-reported so he can weigh them differently.

## 9. Pitfall checklist for the next pass
- Rank from `audits[]`, never from verdict one-liners (SKILL.md: the Tangent/Monolith case).
- 429/500 bodies masquerade as "unverified" - re-fetch after the noise, and only then write REJECT.
- Kill/clear the children's orphaned background scans before you run your own verification.
- After re-ranking, MOVE THE BLOCKS - editing the `Rank N |` labels leaves the sections in their old
  physical order; a 10-line script that splits on `^Rank (\d+) \|`, sorts, and re-emits fixes it.
- Watch for a "meta" copy of the same protocol list: children report a protocol's fund-facing
  contracts WITH one role each, but only a source read reveals that part of the stack is third-party
  (Accountable/Lagoon/Upshift/Mellow vault frameworks) - split the own-code claim accordingly.
