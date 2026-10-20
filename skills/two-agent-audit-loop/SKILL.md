---
name: two-agent-audit-loop
description: "Run an authorized protocol audit with exactly two agents - audit-discovery (attack researcher) and audit-validator (adversarial disprover) - joined by a fixed evidence-package handoff and a five-state status vocabulary. Use after a target is chosen and its SCOPE.md passes the scope gate; composes defi-audit-engine gates and the attacker skill's independence rules."
version: 0.1.0
author: Mustapha Fadhlullah
metadata:
  status: UNTESTED - designed 2026-09-29 from public sources; first real run must record results in Measured below
  related_skills: [defi-audit-engine, attacker, defi-security-research, systematic-debugging]
---

# two-agent-audit-loop

> **Opt-in only (2026-10-01).** Runs two subagents, so use it only when he asks for it. Default audits run inline per `defi-audit-engine`.


Two agents, no swarm. `audit-discovery` (Agent 1) generates and packages hypotheses; `audit-validator` (Agent 2)
tries to kill them. Definitions: `~/.claude/agents/audit-discovery.md`, `audit-validator.md`. Neither may trust the
other, and only Agent 2 can say CONFIRMED. The user alone decides whether anything is sent.

## Why two and why this split

The `attacker` skill already documents the mechanism: a checker built from the same mental model as the thing it
checks produces correlated error and false positives. Agent 2 exists to be the uncorrelated check. It re-derives
reachability from source before reading Agent 1's reasoning, and defaults to REJECTED. Splitting *by role* rather
than by file keeps one agent's context from anchoring the other's.

## The loop

```
scope gate (scope_gate.mjs, no bypass)  ->  G8 funds-on-contract  ->  G10 payment channel
  -> Agent 1: TMAAR, funds flow, invariants, hypotheses (each with a falsifier)
  -> Agent 1: fork test -> findings/F-xx/EVIDENCE.md      (status <= LIKELY)
  -> Agent 2: independent reachability, then challenge list -> re-run PoC yourself
  -> VERDICT.md: CONFIRMED | LIKELY | POSSIBLE | UNCONFIRMED | REJECTED
  -> CONFIRMED only: report candidate -> user decides on disclosure
  -> REJECTED / UNCONFIRMED: kept, a lesson is written (below)
```
Disagreement is resolved with primary data (a test, a chain read), never by a third opinion or by seniority.
If neither can produce the observation that settles it, the status is UNCONFIRMED, not a coin flip.

## EVIDENCE.md schema (Agent 1 writes; every field required, `unknown` allowed, invention not)

```
id: F-xx            title: [Bug Class] in [Contract.function] allows [attacker] to [action]
target/commit/chain/block-pinned:      scope-entry (quote from SCOPE.md):
invariant violated (plain English):    coupled variables / assumption broken:
attacker: address type, privileges held (must be none for headline), starting capital
steps: numbered, each with file:line YOU opened
loss: who loses what, denominated, upper bound and how derived
extractor: does the attacker end with more value? yes/no + how (G6)
falsifier: the observation that would prove this wrong
PoC: path + exact command + fork block + observed output
already-known check: what was searched, where, when
status (self-assigned, max LIKELY): ...
```

## Fixed status vocabulary

| State | Means | Who may assign |
|---|---|---|
| CONFIRMED | green fork PoC run by Agent 2; G0-G6, G8, G11 pass | Agent 2 only |
| LIKELY | green PoC by Agent 1, not yet independently reproduced | either |
| POSSIBLE | mechanism plausible in code, state reachability unproven | either |
| UNCONFIRMED | cannot be tested yet (missing access, no fork) - say what is missing | either |
| REJECTED | disproved or fails a gate - state which and the evidence | Agent 2 |

## Agent 2's challenge list (answer every one, with file:line)

Scope · funds on-contract · reachable by an unprivileged caller · mitigating guard or invariant elsewhere ·
state reachable by a legal call sequence · extractable with own capital, protocol short by same amount ·
duplicate/known · PoC asserts the claimed loss (not just "call succeeds") · **PoC also fails on the patched
code** (a test that passes both before and after the fix proves nothing) · severity matches the program's own
table.

## Lessons (written for every CONFIRMED and every REJECTED)

`lesson: mechanism that generated the bug (not the bug) | protocol type | invariant | precondition |
detection heuristic (grep-able) | false-positive pattern | test that caught it`. REJECTED items are the
most valuable rows: they record which plausible-sounding shapes are noise. Promote grep-able patterns into
`defi-audit-engine/references/checklist-full.md`.

## Measured (fill in on every run — a system with no measurements is a belief)

| Run | Target | Time to first useful hypothesis | Hypotheses | Rejected by Agent 2 | Confirmed | Duplicates found late | Notes |
|---|---|---|---|---|---|---|---|
| (none yet) | | | | | | | |

## Failure modes to watch

- Agent 2 reads Agent 1's narrative first and inherits its framing -> re-derive before reading.
- Agent 2 becomes a rubber stamp because Agent 1's PoC is green -> the patched-code check is mandatory.
- Agent 1 writes falsifiers that cannot fail -> Agent 2 rewrites one and reports it.
- Same model in both seats -> blind spots are shared; the validator is set to a different model tier, which
  buys *different errors*, not more strength (the `attacker` skill's measured caveat).
- Detector negatives: an empty scan and a broken scanner look identical; plant a control before writing "clean".
