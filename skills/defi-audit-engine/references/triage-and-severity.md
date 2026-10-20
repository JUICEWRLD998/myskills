# Triage and severity — the five gates

A candidate is not a finding until it passes all five, IN ORDER. Record the gate that killed or demoted
each candidate; the reject reasons are part of the deliverable.

## G0 — Reality (30 seconds)

Must be confirmed by a fork simulation or an on-chain call.

| Counts as evidence | Does NOT count |
|---|---|
| Foundry/script PoC demonstrating the path end-to-end | "the code looks like it could..." |
| `eth_call` at boundary conditions proving the behaviour | "this pattern is dangerous in general" |
| exact line numbers for the unguarded path | "I read it and it seems like..." |

**KILL:** not run · pattern-matching on contract type · tested only the happy path · ambiguous signal
("the response was different so there might be...").
**DEMOTE to observation:** real but requires unlikely conditions · real but no fund movement.

## G1 — Impact

Litmus test, in one sentence: **"An attacker can ______, resulting in ______."**
FAIL phrasings: "potentially access funds", "theoretically could", "could be used in a chain" (build the
chain first).

Then add the two questions the peer playbook does NOT ask and our mandate does:
- **Can they EXTRACT it?** A value-destroying bug with no drain is still Critical under loss-of-funds,
  but it is reported as value destruction — never dressed as an exploit.
- **What is the precondition COST?** Quantify it (capital, a role, a specific block, one upgrade).

**Severity tiers (7):**

| Tier | Criteria | Action |
|---|---|---|
| Critical | funds WILL be lost or permanently locked | must fix |
| High | very bad — funds/assets at serious risk (drain specific users, steal all fees, grief all withdrawals) | must fix |
| Medium | severe but not existential (dust, grief a specific user, temporary DoS) | should fix |
| Low | small risk / non-exploitable edge case | optional |
| Code Quality / Gas / Informational | no security risk | note |

**Impact x Likelihood (both axes, always):**

| Impact \ Likelihood | Low | Medium | High |
|---|---|---|---|
| Critical | High | Critical | Critical |
| High | Medium | High | Critical |
| Medium | Medium | Medium | High |
| Low | Low | Low | Medium |

Likelihood: **Low** = specific unlikely conditions / multiple assumptions / long horizon · **Medium** =
standard exploit conditions (public mempool, typical user behaviour) · **High** = trivially exploitable,
no prerequisites.

**Reject these inflations:** "owner can steal" (design choice, unless there is a trust-minimisation
angle) · "reentrancy" without a concrete fund-movement path · "centralization risk" without
exploitability.

## G2 — Dedup

Search before writing: **Solodit** (50K+ findings) · the target's changelog/release notes · GitHub issues
for the repo · their known-issues / out-of-scope page · Macro's audit library. Same bug + same root cause
= KILL. Same surface, different bug = continue. Same bug with a proven HIGHER impact = report with
escalation language. **An acknowledged-but-unfixed prior finding is not a dedup kill** — pivot to the
modules that audit never touched.

## G3 — Quality

Title `[Bug Class] in [Contract/Function] allows [attacker] to [action]`. Minimal copy-pasteable PoC
(the triager runs it and sees the same result). Evidence = tx hash or fork output. Shortest call sequence
that demonstrates impact. Use `templates/finding.md`.

## G4 — Reachability (ours; the peer playbook's hardest-won lesson)

Can an OUTSIDE party reach the path? Rate **external reachability, never usage frequency** — "the
backend calls it constantly" is not a capability handed to a user (7,329 on-chain calls proved nothing
about who could order them). On native-AA chains `tx.from` is the ACCOUNT, never the signer: session
keys, relayers and paymasters all produce the user's shape. The decisive check is whether the client can
RECEIVE the credential (response-body destructuring, `*_pending` pollers) — not a keyword grep.

---

## Demote vs kill — where demoted findings live

Demoted material is NOT deleted. It goes into `spec.json` as an observation plus an explicit
`coverage_gap` entry, because an upgrade, a config change or a re-deployment promotes it to a finding.
This is also how owner-reachable paths are handled: never silently dropped, never inflated.

## Closure rules (re-check before any "clean" verdict)

- Every closed section has a non-empty `evidence`.
- Every invariant has a CHECK (a sentence is a wish) and a recorded result.
- Every `never_should_happen` has a fork ATTEMPT with `blocked | partial | succeeded`.
- No section is `not_started`; no contract is unmapped. If either is true, the verdict is
  "coverage gap", not "clean".
- `scripts/new_target_spec.py --validate <spec.json>` is the mechanical check for all of the above.

## Related (do not duplicate)

- **Severe-density ordering + the 8-point vault gauntlet + the AA clamp**: `defi-security-research` →
  `references/severity-density-triage-and-tmaar.md`.
- **Our mandate (V2, 2026-09-13) — ATTACKER PROFITABILITY (G6) and the LIVE-FUNDS GATE (G8)**: same skill,
  `references/vulnerability-first-screening.md`. G6 is the reason G1 here asks "can they EXTRACT it"; G8
  (does the contract hold funds on-contract?) belongs at target-selection time, because a contract that
  holds nothing cannot lose funds. Note that V2's reporting cadence also supersedes the older
  "finish the audit before reporting" rule — see the engine's Procedure step 9.
- **R2 was superseded by V2** for finding-level decisions; keep `references/r2-fund-loss-rubric.md` only for
  the campaign-scoring history. Campaign gates filter TARGETS; these five gates filter FINDINGS.
- **Fork-attack technique bank**: same skill, `references/fork-attack-craft.md`.
