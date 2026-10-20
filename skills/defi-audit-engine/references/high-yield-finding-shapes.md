# High-yield finding shapes — imported from a peer's published corpus (2026-09-21)

**Provenance.** Extracted from `github.com/blessingblockchain/Audits-` (handle `demonhat`) at commit
`98947433a220eb37287dafe9ec5c3d870d77f398` — 16 contest write-ups, 3 self-published bounty write-ups
(`dogecoin-auxpow-finding`, `finding-6-is-refund-required-bug`, `olas-btc-bridge-audit`), and the
`intuition-rules` AI-audit harness. Track record: **30+ confirmed H/M** on Code4rena / Cantina /
Sherlock / CodeHawks, 20+ private audits at Octane Security, Pashov Group, BurraSec, Valsec.
Verticals overlap ours exactly (lending, vaults, AMMs, staking, synthetics, vesting, launchpads).

**This file is the technique half only.** His *selection* model (scope is handed to you; he has never
published a finding that began with a discovery door) is a campaign-strategy question and lives in
`defi-security-research`. What follows is what to DO on a target you have already chosen.

**Why this is worth importing at all:** it is an *independent second corpus* confirming the L1-L7
severity-density order — `reentrancy` appears in **none** of his published Criticals. And it adds
shapes the L-stack does not currently name (§1, S1 and S2).

**Naming, so nothing collides:** this file uses **S1-S6** for finding *shapes* (where to look) and
**A1-A5** for finding *anatomy* (how a finding is written up). The engine's **L1-L7** stays reserved
for the lens stack in `SKILL.md`, and **G0-G10** for gates. Do not reuse L-numbers here.

---

## 0. Anatomy — how one of his findings is written (A1-A5)

Take these wholesale; they cost nothing and they are why his reports read as proven rather than argued.

| # | Law | Effect |
|---|---|---|
| **A1** | **One line, named.** Every finding names the exact line: `skip_pow_verification = true` (dogecoin.rs:85), `PromiseResult::Failed => false` (deposit.rs:273), `Gas::from_tgas(20)` (burn.rs:7). | The line number *is* the finding. Removes all ambiguity about what is being claimed. |
| **A2** | **The diff is the report.** Write the fix as a unified diff against the real file at real line numbers. | Fastest proof the mechanism was understood rather than pattern-matched — and it hands the team remediation. |
| **A3** | **The PoC runs in the project's own harness.** *"uses the project's own `near-workspaces` sandbox infrastructure with real deployed contracts — no mocks or stubs"* | Matches G0 Reality. His Dogecoin PoC passing in **0.08 s** is itself the argument: no real mining work was needed. |
| **A4** | **Assert the economic consequence, not just the state change.** `assert_eq!(utxo_value, 50000)` — the bridge recorded a 50,000-sat UTXO with zero token liability. | Turns "a value is wrong" into "the user is short by this much". |
| **A5** | **Quantify in currency.** *"1 BTC ($60,000) … the entire 1 BTC is permanently stolen."* | A $911 vault is what a ledger looks like when this line is never written. |

---

## 1. The six shapes

Ordered by his own hit rate. **S1 and S2 are the two highest-yield moves in the corpus and are not
currently named in the L1-L7 pass stack.**

### S1 — MIRROR: find the sibling that does it differently *(highest yield)*

Two functions that do the same job, written inconsistently. His headline: `mint_callback` uses
`is_promise_success()`; `safe_mint_callback` uses `!is_refund_required()` — and `is_refund_required()`
maps `PromiseResult::Failed → false`, so a **completely failed** cross-contract call takes the *success*
path: the UTXO is recorded as deposited, no token is minted, and the user's deposit is absorbed
permanently. Medium–High, from one inverted boolean.

**Procedure.** Group functions by *purpose*, not by name. For each group, tabulate the columns that
must agree. Any cell that differs is a candidate; any cell that is absent is a stronger one.

His comparison table is the technique — the column headers force the divergence into view:

| Step | `mint_callback` | `safe_mint_callback` |
|---|---|---|
| Success check | `is_promise_success()` ✓ | `!is_refund_required()` **✗** |
| `PromiseResult::Failed` | `is_success = false` ✓ | `is_success = true` **✗** |
| On failure: record stored? | NO ✓ | **YES — nothing minted** ✗ |
| On failure: cleaned up? | YES ✓ | **NO — stuck** ✗ |

Same move found the Plume **C-01** (a wrong `DEFAULT_ADMIN_ROLE` letting token creators escape factory
upgrade controls) and IgniteLabs C-01 (transfer updates `_balances`, never `_userDebt` → recipients claim
historical fees).

**Mirror groups worth checking on every target:** deposit vs. safe-deposit · mint vs. burn · deposit vs.
withdraw · `transfer` vs. `transferFrom` · claim-vs-compound · per-user vs. global accumulate ·
main path vs. emergency path · two chain deployments of the same contract.

**Emit the missing sibling.** If the reference implementation of a path exists and the other path omits
it, that omission **is** the finding — and the reference implementation is free remediation code you can
hand the team. That is how his `skip_pow_verification` finding is framed: the check exists in the
non-AuxPoW path and is bypassed in the AuxPoW path.

### S2 — The bypass flag

A variable that disables a downstream check. `skip_pow_verification = true` set unconditionally after
`check_aux()` → `check_target()` never called → **any** difficulty target accepted → blocks forged at
minimum difficulty, fabricated deposits minted. **Critical, professional bounty, one line.** His second
such: `compoundLPFees()` bypasses the bin invariant that `addLiquidity()` enforces (`totalShares` never
updated), letting a user withdraw more than they own.

**Procedure.** Grep for every boolean/flag/enum that is *passed to* or *read by* a validation path:
`skip`, `ignore`, `force`, `trusted`, `verified`, `bypass`, `override`, `_UNCHECKED`, `assume`, `unsafe`.
For each: which check does it disable, and **who can set it**? A flag set `true` on a branch that an
unprivileged caller reaches is a Critical; a flag only the owner sets is an observation.

### S3 — Cycle the constant *(one procedure, five H/M in a single contest)*

Find a declared constant, find its consumers, check the arithmetic — *including child calls' allocations*.

His IgniteLabs sweep, all from this one move:

| Constant | Apparent value | Real requirement | Consequence |
|---|---|---|---|
| `GAS_FOR_WITHDRAW_BURN_CALL_BACK` | 20 TGas | children need 20 + 10 = **30** | refund promise cannot be created; burn commits on a separate receipt; **funds destroyed, state stuck forever** |
| `sqrt(1e18)` | 1e18 | returns **1e9** | IL calculator reports **−99.99%** for any price move |
| `_getAmountIn` fee | any hop count | **hardcoded 0.3% single-hop** | every multi-hop exact-output swap reverts |
| `binStep` | per-pair | **hardcoded 25** | wrong price/bin maths — found in **three** separate places (L-01, L-04, and the IL calculator) |

**Procedure.** For every literal in the codebase (grep `= [0-9_]+`, `1e[0-9]+`, `from_tgas`, `BASIS`,
`PRECISION`, `_FEE`, `MAX_`): list its consumers, and for each consumer ask *what does this value have to
satisfy here?* A constant that satisfies one consumer and starves another is the bug. **On a
resource-metered runtime (NEAR gas, Solana compute, gas-forwarding) the check is arithmetic and
unconditional: does the parent's allocation cover the sum of its children's static allocations?**

### S4 — Invariant broken through a bypass path

Write the protocol's stated invariant, then find the function that skips the check enforcing it.
`compoundLPFees()` breaks the bin rule; IgniteLabs C-02 mints shares without updating `totalShares`,
letting the user burn shares backed by *other* users' reserves. **This is the shape G5 exists to catch:
if you have not written `never_should_happen` down, you cannot see the path that violates it.**

### S5 — Arithmetic direction

Decimal/scale errors, rounding direction, `sqrt` halving precision. Dense but usually lower severity —
and it found `M-02` above at Medium. Ceiling is real but bounded; do not lead with it.

### S6 — Temporal

Checkpoint/epoch boundaries, staleness, snapshot-vs-live reads. His `POST-MORTEM.md` is the model: he
analysed a **live incident** (a VotingEscrow `_supply_at` unsigned underflow, `Panic(0x11)`) from the
breaking transaction outward — a checkpoint created *after* an epoch boundary made every historical
supply query underflow. The executable version of this law on a chosen target is
`references/onchain-invariant-forensics.md`: sample the invariant across history, bisect at a materiality
threshold, decompose the block where it broke.

---

## 2. `audit-variants` — the systematic form of the mirror

His harness runs a fixed pipeline (`audit-context` → `audit-entry-points` → `audit-static-analysis` →
**`audit-variants`** → `audit-spec-compliance`). The one worth stealing outright is `audit-variants`:
**after finding one real instance, re-scan the entire repo for that same pattern and classify every hit**
(confirmed / probable / false-positive).

Map it onto our fan-out:

1. When a child returns a confirmed finding, do **not** close the track — brief a follow-up pass whose
   only job is the pattern, not the bug: *"instances of `<pattern>` anywhere in scope, each classified
   confirmed / probable / FP, with the discriminating test stated."*
2. S1 (mirror) and S3 (constant cycle) are the two patterns that repay this most, because both scale
   linearly across a codebase — one instance implies N more.
3. Their `audit-entry-points` command is a cheap pre-pass we do not explicitly have: enumerate every
   state-changing entry point and **classify it public / role-gated / upgrade-admin** before hunting.
   That is the L6 access-control clamp, moved to the front where it costs less.

**Override on their static analysis:** their `audit-static-analysis` delegates trust to `semgrep`. Our
standing rule wins — **detectors need a planted positive control before any negative is recorded**
(see `defi-security-research` → Pitfalls). Their own corpus also shows a scanner-shaped zero being
mistaken for a result, three separate ways.

---

## 3. What this changes in the pass stack

Do **not** replace L1-L7; these are orthogonal. The concrete edits:

- **Add S1 (mirror) and S2 (bypass flag) to the front of the on-target procedure**, before the lens
  sweep. Both are cheap, both are grep-able, and both produced his highest-severity findings —
  including the only Critical he published for money.
- **S3 (constant cycle) is the arithmetic form of S1**: the "sibling" is the consuming call site rather
  than a second function, and the check is whether the declared value satisfies *every* consumer.
- **Run variant-analysis after every confirmed finding**, before declaring a section closed.
- **Severity tail vs. density, stated honestly:** the L-stack is ranked by *density* (reward/accrual
  first) and that ranking survives this corpus. But his two most valuable singles are a **bypass flag**
  and a **wrong role constant** — the *tail*. **Mine both; do not pick one.** A cheap S1/S2 pass over
  the whole surface costs little and is where the Criticals are.

---

## 4. Limits of this import — stated so it is not over-trusted

- **Sample:** ~19 published H/C findings across 10 contests and 3 bounties. Directional, not statistical.
  Much of the L1-L7 density order rests on a **different, larger corpus** (125 audits); this is
  corroboration, not a recount.
- **His harness is Claude-Code-shaped** (`.claude/commands`, `.claude/agents`). The pipeline shape
  transfers; the specific command files are not portable to our subagent fan-out without translation
  (§2 does that translation).
- **One genuine oddity, flagged not repeated:** `audit-context` invokes an `audit-context-building` skill
  that is **not present in that repo**, and the checks live inside `intuition-contracts-v2/.claude/`
  rather than at the repo root — so the harness ships partially. Do not assume the referenced skills
  exist when reading it.
- **Not verified:** whether any of these findings were *paid*. Severity labels are the platforms' and
  his own; there is no payout record in the repo. Treat his method as validated, his economics as
  unverified.
