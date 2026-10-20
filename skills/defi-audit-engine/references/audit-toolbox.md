# Audit toolbox: which skill, at which stage

Two spines, then specialists. Pick by stage. If a skill is missing, say so; never rebuild its rules from memory.

**No subagents unless he says so in this session (2026-10-01).** Wherever a skill below says "dispatch one
subagent per lens", "fan out recon", or "two agents", do the same work inline and in sequence instead: one
lens at a time in the severity-density order, each lens writing its findings file before the next starts, each
brief still read from `references/pass-briefs.md`. When he says "fan out" or "run the two-agent loop", use the
original machinery and name each agent's job first.

## By stage

| Stage | Job | Use | Notes |
|---|---|---|---|
| 1 Discovery | Find, score and shortlist targets; pick ONE | `defi-security-research` | Discovery only. Never auto-start a deep audit; he picks the target |
| 1b Dead-page recovery | Explorer, docs or dashboard behind Cloudflare or a paywall | `blocked-page-recovery`; firecrawl `firecrawl_scrape` | |
| 2 Pre-audit recon | Threat model, protocol-type profile, git-weighted attack surface, temporal risk, before reading code | `x-ray` (writes `x-ray.md`); the `TMAAR.md` rule in `defi-audit-engine` still holds: trust model first | G8 live-funds gate comes before code |
| 3 Spec and passes | One target: `spec.json`, section-by-section evidence-gated passes, 6 severity-density lenses, 5 finding gates, fork-attack gate | `defi-audit-engine` | The execution spine. Inline, one lens at a time |
| 3b Quick pass while coding | Fast Solidity review of a repo or one file, loop mode for repeated passes | `solidity-auditor` (pashov v4; 9 single-lens agents + 3 gap-hunters flow/numerical/trust already bundled) | A second opinion on a lens, never a replacement for the engine's gates |
| 3d Deep logic + state loop | Iterative Feynman (question every line) ↔ State-Inconsistency (coupled-state desync) until convergence | `nemesis-auditor` (orchestrator), or `feynman-auditor` / `state-inconsistency-auditor` standalone | Imported 2026-10-11 from `0xiehnnkta/nemesis-auditor`. Feeds the L8 state-desync lens and the per-function Feynman discipline. Inline, no subagent fan-out unless he says so |
| 3c Checklists | Bug-class greps and ecosystem patterns | `defi-audit-engine/references/checklist-full.md` (live document, add new patterns there); `ecc:defi-amm-security` for AMM and pool code; `ecc:evm-token-decimals` for decimals bugs; `ecc:nodejs-keccak256` for hashing mistakes; `lance` as a reference corpus of exploit classes (Solidity, EVM bytecode, Sui Move) | Checklists generate leads. A lead is not a finding |
| 4 Fuzz | Echidna and Medusa suites from a Foundry or Hardhat repo | `fizz` | Run when invariants exist in `spec.json` |
| 5 Reproduce | Fork PoC, pinned `--fork-block-number`, receipts | `defi-audit-engine` fork-attack gate; `test-driven-development` for the harness (RED first, then GREEN); `systematic-debugging` when the PoC misbehaves; `diagnosing-bugs` for a hard or slow one | No finding without a reproduction |
| 6 Attack the finding | Try to disprove it: reachability, preconditions, duplicates, scope, extractability | `attacker` run inline, lens by lens | Same session means SEMI-INDEPENDENT. Label it. A truly independent attacker is a subagent: only if he says so |
| 6b Two-agent loop | Discovery agent plus adversarial validator joined by an evidence package | `two-agent-audit-loop` (agents in `~/.claude/agents/`) | Opt-in only. He must ask for it |
| 7 Report | One-page report within 24h of a green PoC, then the campaign report | `defi-security-research` disclosure references; `humanizer` on the prose | He decides the send. Never send a disclosure without his explicit go |
| 7b Pre-send gate | Review the finished report against the program brief: YES / NO / NOT-YET / CAN'T-DECIDE, naming the one missing proof | `defi-security-research` pre-send gate (modelled on `mdpsec/should-i-submit`); run AFTER the V2 finding gates, BEFORE his send decision | Catches dups and unprovable leads. A NOT-YET pauses; do not submit until the named proof exists |
| Web2 side | Authorized web application pentest | `web-pentest` | Not a DeFi stage; only for a web target in scope |

## Gates that every stage inherits (do not skip, do not soften)

G0 Reality, G1 Impact and extractability (G6: an unprivileged address ends with more value than it started,
funded only by its own capital), G2 Dedup, G3 Quality (title, minimal PoC, tx hash), G4 Reachability. G8 live-funds
before reading code. Owner-gated paths are `coverage_gap` entries, never findings. A detector needs a planted
positive control before any negative result is written down.

## Archived on 2026-10-01 (`~/.claude/skills-archive/`, restore by moving back)

`angus-bounty-hunter` (Slither plus local-LLM triage, generates PoC templates without reproducing anything; it
cuts against the "no finding without a reproduction" rule), `web3-audit` (a generic ten-class checklist with
paid-example anecdotes; `defi-audit-engine/references/checklist-full.md` and the engine's gates cover it).
