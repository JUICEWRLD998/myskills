# Severity-density triage order, TMAAR, and the spec.json evidence discipline

Imported 2026-09-14 from a peer auditor's operations repo (SAVAGEAUD). Three things here are
orthogonal to our own 14-phase campaign methodology and worth running ALONGSIDE it.

## 1. Rank bug classes by SEVERE DENSITY, not by frequency

Measured over **125 published audits / 1,022 findings** (Shieldify corpus). The most COMMON family
is the least dangerous; count-based triage points you at the cheapest bugs.

| Priority | Family | Severe share |
|---|---|---|
| 1 | reward / accrual accounting | **39%** |
| 2 | withdrawal / exit / queue | 29% |
| 3 | rounding / precision / decimals | 27% (on only 2.5% of volume) |
| 4 | fee / tax routing | 25% |
| 5 | funds locked / DoS / griefing | 20% — AND 9.6% of volume (only family in both top-3s) |
| 6 | access control | 20% (8 of the corpus's 34 Criticals) |
| 7 | web2 / off-chain / frontend | 22% severe, 0 Criticals but 9 Highs — do not skip it |

**Deprioritise to "mention, don't deepen":** docs/spec (38 findings), events/returns (31),
pause/emergency polish (21), auction polish (6) = **96 findings, ZERO Criticals or Highs across
125 audits**. `gas_optimization` = 88 findings, 1 severe.
**`reentrancy` = 12 findings, 1 severe — the lowest-yield famous class in the corpus.** *[CORRECTED 2026-09-29: n=12 was too small. On a 23,625-finding corpus reentrancy is 821 findings at 25.5% High/Critical, slightly ABOVE the 21.8% baseline; the lowest classes there are input-validation / token-integration / initialization. Still not a first-spend class, but not the bottom — see `defi-audit-engine/references/corpus-severity-density-23k.md`.]* Spend the
seasoned-auditor time on reward accounting and exits instead.

Reusable check for #1 — the 8-point vault reward-accrual gauntlet: is the `totalShares == 0` guard
actually REACHABLE (a permanent dead/minimum stake makes it unreachable — bug, not safety net)?
is any `== 0` used as "uninitialized" where 0 is legitimate? `x * PRECISION / y` bounds? where does
rounding dust go, is the pool zeroed anyway? does the claim path filter by the stake's duration/
cycle eligibility or just by availability? catch-up loops advancing one step per tx? are
"allocated" and "minted" tracked separately (can a claim fall between them)? events derived from a
pre-scan that can `break` early?

## 2. The mandatory AA / session-key / module-authz clamp

ERC-4337 modular wallets and session-key modules produced **10 of 34 Criticals** in that corpus
(one vendor's CAM module alone: 8). Grep every session-key/module path for:

- **Key identity** — does `enableSessionKey`/`addKey` check the key is unused AND not registered to
  another wallet? Missing either = session-key hijack (a key's identity is not its value).
- **Whose state is being read** — any `validUntil`/`expiry`/`owner` check reading the CALLER's field
  instead of the SUBJECT's turns into `0 >= now` → always false → skipped.
- **`msg.sender` isn't the caller in a module context** — install/uninstall/execute paths taking
  `sender` from calldata and treating it as the real sender ⇒ anyone can act on any wallet.
- **Proof consumption** — does the validator CONSUME the signature (nonce/used flag) or merely
  verify it? Verify-without-consume = replay. (Same family as the signed-message function that
  binds `msg.value`/deadline but tracks no used-signature set.)

## 3. TMAAR (trust model, assumptions & accepted risks) — before reading code

Merge this into our Phase 0.5/recon as an explicit artifact, not prose:

- **Actors & trust level** — protocol owner/admin, users, vault manager, oracle/resolver,
  relayer/keeper/bot, bridge; for each: what they can do, and the failure mode if compromised.
- **Key assumptions** — every "we assume X" must carry a "what if X fails?" answer.
- **Accepted risks** — what the protocol SAYS is out of scope (stated, not assumed) — this is also
  what makes a later disclosure defensible (see references/disclosure-framing-and-intake.md).
- **Attack-surface summary** — primary assumption to attack, most powerful attacker, can the
  protocol survive if X fails.

Quality bar they enforce: every external dependency has a trust level; every assumption has a
failure mode; owner power is ENUMERATED (not just "can upgrade"); accepted risks are explicit.

## 4. The per-target spec.json evidence discipline

Our campaign produces reports and JSONs; this adds a per-target MACHINE-READABLE state file that
makes "one section at a time" enforceable. Fields worth copying: `sections[]` (one contract or one
flow each, `status: not_started → in_progress → closed`), `invariants[]` (statement, where, HOW IT
IS CHECKED, checked, result, evidence), `never_should_happen[]` (statement, concrete fork ATTEMPT,
result blocked/partial/succeeded, evidence), `actors[]`, `assumptions[]`, `value_movers[]`
(function, direction, caller_can_be, guards, **bounded_by**), `main_functions[]`, `coverage_gap`,
`passes[]`, `status` (sections_closed/total, open_questions, blocked_on).

Four rules that make it more than paperwork:

- Every invariant needs a CHECK, not a sentence — "an invariant with no test is a wish".
- Every `never_should_happen` needs an ATTEMPT on a fork.
- **A section with an empty evidence field is OPEN**, however convincing it reads.
- **A target is never "clean" while any section is `not_started` or any contract is unmapped** —
  record that as an explicit COVERAGE GAP (their worked example records "9 of 19 game contracts
  never mapped" instead of a clean verdict). This is the honest version of our own
  "what this did NOT establish" section.

## 5. The owner-gated school difference (read before quoting anyone's clean rate)

Their rule: *"only flag things a non-owner / arbitrary caller can exploit — owner can steal is a
DESIGN CHOICE, not a finding"*, combined with *"never report anything not proven on a fork"* and
*"don't manufacture findings"*. Those three rules are why ~30 consecutive targets read clean. It is
a coherent rubric — and it is NOT ours (R2 hunts attacker-profitable High/Critical AND
value-destruction, and values own-code depth). When benchmarking another auditor's numbers:
name their rubric first, never import their severity bar, and keep owner-reachable paths in the
spec as observations + coverage gaps so an upgrade or config change promotes them later.
