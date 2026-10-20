---
name: defi-audit-engine
description: "Use when auditing one DeFi target: spec, passes, gates."
version: 0.1.0
metadata:
  hermes:
    tags: [audit, defi, smart-contracts, methodology, fork-attack, evidence-gates]
    related_skills: [defi-security-research, systematic-debugging]
---

# DeFi Audit Engine

> **Routing and no-subagent rule (2026-10-01):** `defi-audit-engine/references/audit-toolbox.md` maps every installed audit skill to its stage. No subagents unless he says so this session: where this file says dispatch or fan out, run the same work inline and in sequence.


Executes ONE already-chosen target: spec -> section-by-section evidence-gated passes -> fork attacks ->
gated findings. Doctrine merged from the peer playbook `github.com/Savage27z/SAVAGEAUD` (benchmarked
2026-09-14), Macro TMAAR, BountyForge 4-gate triage, Pashov attack-framing, and our own R2
loss-of-funds mandate.

It is the EXECUTION half only. Target discovery, campaign scoring, disclosure framing and
submission mechanics live in `defi-security-research` (research/defi-security-research) — load both
when starting a campaign, load this one when the target is named.

## When to Use
- The user named a target and the audit phase begins ("we are auditing X now").
- Resuming a target whose spec still has open sections.
- A "clean" verdict is about to be written — the closure rules and the fork-attack gate decide it.
- Don't use for: discovery/shortlisting candidates, or writing the disclosure pack (both are in `defi-security-research`).

## Prerequisites
- Workspace `Desktop/audit<N>/TARGETS/<slug>/` scaffolded by `scripts/new_target_spec.py` (spec.json is the state file).
- Verified source for 100% of fund-facing contracts, or an explicit black-box statement in `target.source.note`.
- `anvil`/`cast` on PATH (Windows: `export PATH="$PATH:$HOME/.foundry/bin"`), and a fork RPC you can PIN by block number.
- Read `references/triage-and-severity.md` before scoring anything; read `references/checklist-full.md` before the first pass. Corpus lessons on PoC craft, discovery moves and resolution language: `references/corpus-poc-and-resolution-patterns.md`.

## The loop (canonical order — do not reorder)

**Before**
1. Gather all code + integrations into the target dir.
2. Push it into context (repo documents are the agent's context).
3. Split the target into SECTIONS in `spec.json` — one contract or one flow per section.
4. Extract invariants, actors, assumptions into `spec.json` (+ narrative `TMAAR.md`).
5. Every entry carries `evidence`. Nothing enters the spec as a sentence alone.
6. Work ONE section at a time; move `status` `not_started -> in_progress -> closed`.
7. Check every answer against the code — file:line, fork receipt, tx hash, or on-chain read.

**During**
1. Find where the value moves (`value_movers[]`: function, direction, caller_can_be, guards, **bounded_by**).
2. Find the main functions everything depends on (`main_functions[]`).
3. Pick ONE flow and hunt it MANUALLY — not a grep sweep.
4. Walk it end to end (only reading never reaches state-machine branches that exist mid-execution).
5. Ask "what must never happen here?" -> each answer becomes a `never_should_happen[]` entry with a fork attempt.

**After**
1. You are not done.
2. Complex integration? One extra pass per external dependency (oracle, relayer, bridge, proxy, upgrade path).
3. Heavy math? Fuzz around the math, not around the contracts in general.
4. New mechanism discovered mid-audit? Redo step 4 on the new mechanism's own invariants.
5. Grind to the end — the last section and the last never_should_happen is where the finding usually is.

**Four closure rules (a section that violates these is OPEN):**
- Every invariant needs a CHECK, not a sentence. "An invariant with no test is a wish."
- Every `never_should_happen` needs an actual fork ATTEMPT, with result `blocked | partial | succeeded`.
- A section with an empty `evidence` field is open, however convincing it reads.
- A target is NEVER "clean" while any section is `not_started` or any contract is unmapped — record it in
  `target.coverage_gap` instead (this is the honest version of "what this did NOT establish").

## The pass stack

Six hunt lenses in **severity-density order**, then three cross-lens gap passes, then the fork gate.
The order is the point: it is measured over 125 published audits, and it is why `reentrancy` — the
loudest famous class — sits LAST in yield (12 findings, 1 severe) while reward accrual sits first
(39% severe). Rationale and the deprioritise-list: `references/triage-and-severity.md` section 1.

| # | Lens | Hunt for |
|---|---|---|
| L1 | **Reward / accrual accounting** (39% severe) | the 8-point vault gauntlet: reachable `totalShares == 0` guard, `== 0` used as "uninitialized", `x*PRECISION/y` bounds, where rounding dust goes, claim filtered by stake duration/cycle vs mere availability, catch-up loops, allocated-vs-minted gap, events from an early-`break` pre-scan |
| L2 | **Withdrawal / exit / queue** (29%) | queues, cooldowns, two-step or async settlement, fulfilment math, refund paths, who can abort after seeing the outcome |
| L3 | **Rounding / precision / decimals** (27% on 2.5% volume) | ERC-4626 must round UP on withdrawal; conversion direction; cross-decimals comparisons; per-segment constraints that break the monolithic invariant |
| L4 | **Fee / tax routing** (25%) | fees charged to the protocol instead of returned, fees paid when not due, config that dodges fees, recipient setters that reshape pending accruals |
| L5 | **Funds locked / DoS / griefing** (20% severe AND 9.6% of volume) | "funds nobody can move" — a banned/blocked user who cannot exit, a griefable array, an unreachable terminal flag |
| L6 | **Access control** (20%; 8 of 34 Criticals) | every state-changing fn's modifier, open initializers, proxy admin, upgrade path, role self-granting. **Mandatory clamp: AA / session-key / module authz — 10 of 34 Criticals** (key identity, whose `validUntil` is read, `sender` from calldata, proof consumed vs merely verified) |
| L7 | **Web2 / off-chain / frontend** (22% severe, 9 Highs) | only when an app surface exists: decimals handling, parameter spoofing, server-side validation (probe the endpoint, never infer absence from the client), error handling |
| L8 | **State desync / coupled-state** (added 2026-10-11) | every coupled state PAIR where an operation mutates one side without the other — `balance`/`totalSupply`, `shares`/`assets`, `debt`/`collateral`, a mapping and its length/index, a flag and the state it guards, an accumulator and its checkpoint. One side updated, the mirror stale ⇒ silent corruption or a later revert. Run `state-inconsistency-auditor`; for the whole logic+state loop run `nemesis-auditor` (Feynman ↔ State until convergence). This is where Notional-class unchecked-downcast and reward-accrual desyncs live |

**Per-function discipline on every lens (Feynman, added 2026-10-11).** When you hunt a flow manually
(the "During" step 3), question each line the way `feynman-auditor` does: Q1 why does this line exist /
what breaks if deleted; Q2 what if it runs before/after its neighbour, or the fn aborts halfway; Q3 if fn A
has a check and sibling fn B doesn't, WHY; Q4 what does it implicitly trust about caller / external data /
state / time / price / amount; Q5 first call, last call, called twice, system-as-param; Q7 external-call
reordering and multi-tx state corruption. The full bank is the `feynman-auditor` skill — load it for a deep
logic pass, or `nemesis-auditor` to run it in a loop with L8.

**Then the three gap passes** (flow gap / trust gap / numerical gap) hunting only bugs that REQUIRE
2-3 lenses at once — a bug one lens can see belongs in L1-L8. Full seam checklists:
`templates/gap-hunter-scan.md`. The richest seam definitions (with code-shape catalogues) are now also in
the bundled `solidity-auditor` skill: `references/hacking-agents/{flow,numerical,trust}-gap-agent.md`.

**Then the FORK-ATTACK gate:** run an anvil fork and ATTEMPT the attacks — impersonate owner/admin/
keeper/oracle-provider, malformed calldata, replay, reentrancy, grief/DoS loops, refund/withdraw
races. `never_should_happen[]` entries are the attack list. Static reading alone never yields a clean
verdict. Craft + traps: `references/fork-attack-craft.md` in `defi-security-research`.

Per-lens subagent briefs, fan-out rules and the child output contract: `references/pass-briefs.md`.

**Then wrap the whole sweep in a PRIMER and mind the error budget: `references/primer-layer-and-agent-framing.md`**
(both imported 2026-09-24). A *primer* is not a checklist — it is a one-page context-load written per target
from `TMAAR.md` + `spec.json` and pasted at the top of EVERY child brief, so N children reason from one loaded
threat model instead of re-deriving and diverging; keep a longer-lived **class** primer for target types you
repeat. That file also carries the assertion-form seed prompt (hypothesis briefs only — never a verification
brief), the **business-flow detection unit** (emit call chains in `spec.json` and hand each child the chains it
owns, not a file list), and the **error-accumulation budget**: at 99% per action a 30-step chain lands near
73%, and at 60-70% per action five steps land near 16% — which is the quantitative case for keeping children
SHORT and splitting anything implying more than ~ten reasoning steps.

**Before the lens sweep, run the two cheap high-yield passes** — both are grep-able, both produced a
peer's highest-severity published findings, and neither is in L1-L7: **S1-mirror** (two functions that
do the same job written inconsistently — tabulate by purpose and find the cell that differs or is
missing) and **S2-bypass-flag** (any flag that disables a downstream check, and *who can set it*).
Then **variant-analysis after every confirmed finding** — re-scan the repo for that pattern and classify
each hit, because one instance implies N. Shapes (S1-S6), write-up anatomy (A1-A5), and the
constant-cycle arithmetic check (gas/compute allocation vs. children's requirements):
`references/high-yield-finding-shapes.md`. **S-numbers are shapes; L1-L7 stays reserved for the lens
stack above — do not mix them.**

**Then run the HEURISTIC BANK (imported 2026-09-24 — 137 entries across 5 files).** Every entry is in
`Trigger · Test · Impact · FP guard` form and every file ends with its own `## Sequence` (the order to run
it), `## Kernels covered` and `## Not covered here`:

- `references/heuristics-lending-liquidation.md` (44) — lending, collateralised debt, leveraged positions,
  auction/refinance/liquidation engines. **Start with its Sequence step 1, which is an economics computation,
  not a code read:** `liquidatorProfit = seizedCollateral × bonus − protocolFee − gas` evaluated at the
  protocol's OWN minimum position size. If that is ≤ 0 the entire dust / liquidation-incentive family (its
  entries 1, 10–14, 42) is live and becomes the highest-yield thread — that family is the single
  most-repeated kernel in the source library and the one our older checklists did not cover at all.
- `references/heuristics-core-solidity.md` (38) — the general pass: rounding truncating to zero, slippage
  parameter hygiene (`amountOutMinimum: 0`, `deadline: block.timestamp`, hardcoded fee tiers), stuck funds,
  unsafe/quirky ERC20s, ownership transfer, MEV, gas-as-a-bug, pool balance.
- `references/heuristics-state-lifecycle.md` (18) — use-after-`delete`, mapping default accepted as valid,
  hand-maintained counters decremented on unvalidated input, `type(uint256).max` sentinels, and
  existence-check-where-authorisation-is-needed.
- `references/heuristics-asymmetric-gating.md` (19) — sibling gating asymmetry, and "pause / frozen token /
  stale price blocks the user's escape hatch but not the liquidator". This is the **from-the-findings side of
  our own S1-mirror**, so run the two together and reconcile the tables.
- `references/heuristics-uniswap-v3-fork.md` (18) — V3-fork, concentrated-liquidity and pool-integration
  targets.

**Read `## Not covered here` before writing any clean verdict for a class these files touch.** The bank is
deep on lending/liquidation economics and **empty** on bridges and cross-chain messaging, signature / permit /
nonce replay, upgradeability and proxy storage layout, initialiser front-running, ERC-4626 donation /
first-depositor / share inflation, reentrancy as a first-class class, perps and funding mechanics,
AA / EIP-7702, and every non-EVM target. Those remain covered only by `checklist-full.md` and the lens stack
above — **a clean verdict justified by citing this bank alone is a COVERAGE GAP, not a result.**

**One structural rule borrowed from that library, because it is the part worth copying:** when a pass teaches
a new anti-pattern, add it to the matching bank file *with its instance* — a `Source:` clause naming the
target, the date, and a `file:line` or finding id. That library's rules read concretely instead of generically
because each was distilled from one real finding; ours may not become assertions without instances.


### Vertical overrides — when the target is in a specialised vertical, the L1-L7 lens stack is NOT the pass

The generic lenses find generic bugs, and generic bugs are both low-severity and the ones most likely to
be reported by someone else first. When the target is in a vertical with its own domain logic, run its own
bug classes **first** and use L1-L7 as the sweep afterwards.

- **Gambling / prediction markets / lotteries** → `references/gambling-vertical-bug-classes.md`.
  House-edge and payout direction, RNG/entropy, commit-reveal reveal-window free options, bet-settlement
  races and double-settlement, signed-outcome replay (**verified-but-not-consumed is the highest-value
  shape**), bankroll caps vs. solvency, and the vertical's signature exploit — a **free option against the
  house** where the player decides after seeing the outcome. §6 is a checklist of those free options;
  §7 is the finding bar (a player-funded positive-EV loop with a number, on a pinned fork — a DoS is a
  hardening note, never the headline).
- The same treatment applies to any vertical with domain maths (options vaults, insurance claims, RWA
  NAVs). Derive the lens from the product's own invariant, not from a checklist.

**The bar this raises, stated once:** the audit2 findings were pattern-shaped (a missing guard on one of
eight siblings, a latent unreachable low, a documentation defect). All were real, reproduced, and worth
nothing. A vertical-specific mechanism — "a player repeats bet size X and nets $Y, the house is short $Y"
— requires understanding the product, which is exactly why it is both higher-severity and harder to
duplicate. **Prefer one such finding to five guard-shaped observations.**

## Gates — a finding is not a finding until it passes all five

| Gate | Question | KILL condition |
|---|---|---|
| **G0 Reality** | Is it real? | not run; pattern-matching ("this type is often vulnerable"); happy-path only; ambiguous signal |
| **G1 Impact** | "An attacker can ____, resulting in ____." + Impact x Likelihood + **G6: can an UNPRIVILEGED address EXTRACT it** — ends with more value than it started, funded only by its own capital, protocol short by the same amount? | "potentially", "theoretically could", "could be used in a chain"; value destruction with no extractor (still filed — as a hardening note, never the headline) |
| **G2 Dedup** | Solodit / changelog / GitHub issues / known-issues / Macro library | same bug, same root cause, already known |
| **G3 Quality** | `[Bug Class] in [Contract/Function] allows [attacker] to [action]`; minimal copy-pasteable PoC; tx hash or fork output | prose without a reproduction |
| **G4 Reachability** | Can an OUTSIDE party reach it? | usage frequency mistaken for reachability ("the backend calls it a lot" is not a capability handed to a user) |

Demote (do not delete) anything that is real but unreachable today: it goes in the spec as an
observation + `coverage_gap`, because an upgrade or config change re-opens it.
Owner-reachable paths are kept that way too — never silently dropped.

## Workspace layout (match the existing campaign dirs)

```
Desktop/audit<N>/
  PLAN.md  HUNT_LOG.md  FINDINGS_MASTER.md  RANKED_REPORT.md  DISCLOSURE/
  TARGETS/<slug>/
    spec.json        # the state file - sections, invariants, ns_h, value_movers, passes, coverage_gap
    TMAAR.md         # trust model, BEFORE any code is read
    recon/           # source, ABI, bytecode, proxy map, scripts, dumps
    findings/        # F-xx-*.md, one file per finding (TEMPLATES/finding.md)
    fork/            # anvil drivers, forge tests, receipts (pin --fork-block-number)
```
One section belongs to one pass; findings never go straight to the report — they go through the five gates.

## Procedure

1. **Scaffold** — `terminal(command="python <skill>/scripts/new_target_spec.py --target <name> --chain <chain> --chain-id <id> --out <workspace>/TARGETS/<slug>/spec.json")`. Done when spec.json exists with `target`, `sections` empty and `status.done=false`.
2. **Phase 0 recon** — fill `target.contracts[]` (address, role, impl, proxy_kind, code_size, known), `integrations[]`, then `sections[]`. Done when every fund-facing contract is either `known: true` or listed in `coverage_gap`.
3. **Phase 0.5 TMAAR** — fill `actors[]`, `assumptions[]` (each with `breaks_if`) from `templates/TMAAR.md`. Done when every external dependency has a trust level and every assumption has a failure mode.
4. **Phase 1 read** — per section, Feynman it in plain English (emit `[Feynman: ...]`, `[Socratic: file:line]`, `[Inversion: fn]` markers) and fill `value_movers[]` + `main_functions[]`. Done when every section has `in_progress` + at least one evidence string.
5. **Phases L1-L7** — run one lens at a time inline (one subagent per lens only if he says fan out) (disjoint file sets, brief per `references/pass-briefs.md`), severity-density order. Each child writes its deliverable EARLY and updates it incrementally. Done when every lens returns `findings[] | no_finding + what_it_checked` and unresolved items are in `status.open_questions`.
6. **Gap passes** — 3 passes, cross-lens only. Done when each pass reports `seam / trace / violated_principle / proof` or an explicit negative.
7. **Fork gate** — attempt every `never_should_happen[]` on a pinned fork; record `blocked | partial | succeeded` + receipt. Done when no `never_should_happen` is unattempted.
8. **Triaging** — run the five gates in order (`references/triage-and-severity.md`); write survivors to `findings/`. Done when every candidate is either a finding file or a recorded demotion/kill with its gate. Screen the intake channel (G7) at the SAME time as the code — a perfect finding with no door is a blog post.
9. **Report on PROOF, not on completion (V2 cadence — supersedes "finish the audit before reporting")** — PoC green ⇒ a one-page report within 24h ⇒ a 48h urgency nudge naming the funds at risk and that the bug is live ⇒ the full campaign report later, separately. Never hold a drainable bug for a bundle. Draft it yourself and surface it for the send decision: the user owns disclosure and the send.
10. **Close** — `python scripts/new_target_spec.py --validate <spec>`: zero empty-evidence closed sections, zero unattempted ns_h. Done when `status.done=true` and the count is reconciled — then REPORT to the user and STOP (never auto-advance to disclosure; he names the next step and verifies the protocol himself).

## Pitfalls
- **Do not import the peer playbook's rubric.** Its "owner can steal is a design choice" + "never report unproven" + "don't manufacture findings" rules are why ~30 consecutive targets read clean. Their MACHINERY is excellent; their severity bar is not ours. Ours is V2's G6: a fork PoC where an UNPRIVILEGED address ends with more value than it started, funded only by its own capital — no admin key, no insider role, no oracle luck — with the protocol short by the same amount. Value destruction with no extractor is still reported, but as a hardening note, never the headline. Keep owner-reachable paths as observations + coverage gaps so an upgrade promotes them later.
- **Check the target holds funds ON-CONTRACT before spending a pass (V2 G8).** Of the top 45 pattern-scoring contracts in one pass, 43 held ~nothing — a contract that holds nothing cannot lose funds, however bad its code is. TVL inside a third-party pool it merely fronts is not drainable from its own code.
- **G11 — THE PLATFORM GATE PASS. RUNS ABOVE G10, ABOVE G8, BEFORE ANY CODE IS READ (2026-09-22).** G10 asks "will anyone
  pay me"; G8 asks "can this contract lose funds"; **G11 asks "may I enter at all, and is the bug already taken."** It is the
  gate whose absence caused the platform channel to be withdrawn on 2026-09-16, and it is cheapest thing in the pipeline — a
  kill here costs minutes, a kill at G2 costs a full pass. Four sub-gates, in order: **G11a PLATFORM** (KYC you cannot pass ⇒
  KILL; pay-to-submit fee weighed against *probability*, not the bounty headline; geography/sanctions; account standing;
  payout token on a chain you can receive; **is a PoC required** — required ⇒ the report must carry a runnable repro or it is
  invalid; **an attack-window restriction means a submission outside it is INVALID, not late** — Ankr's 24h window is a G11a
  constraint). **G11b SCOPE** (the address or pinned commit you will audit is inside the published scope, right chain, as a
  `smart_contract` asset — and **read the out-of-scope list before the code**: programs routinely exclude the exact class you
  are best at — "admin risk", "oracle manipulation", "known issues", "centralisation" — and a finding in an excluded class is
  a zero however good). **G11c DUPLICATE** (below). **G11d CROWDING** (prior-audit count **verified, never quoted** — the
  program's `prior audits: 0` field is the *buyer's own claim*; contest history; program age; TVL).
  **G11b-B — READ THE OUT-OF-SCOPE LIST *AND* THE FORK-BASE DECLARATION BEFORE PRICING, NOT AFTER (2026-09-22, Flux Finance — cost a whole ranking).** The PROGRAM PAGE carries two fields that decide payability and are invisible to every money gate: (1) an explicit **out-of-scope / known-issues list**, and (2) for a fork, the **exact upstream commits it was forked from**. Both take minutes and both can invalidate a target that passes G8, G10 and G11a cleanly. Measured on Flux: **$43.51M at rest, $550k cap, KYC waived, no attack window** — top of the radar for a day. Then the page declared *"The fToken contracts are forked from commit `3affca87…`; all other contracts (Comptroller, CErc20Delegator, InterestRateModel, …) from commit `a3214f67…`"* plus **"any known issues in CompoundV2 up to these commits are considered out of scope"** — which converts the entire inherited fToken/Comptroller codebase into known-and-excluded, and names the **first-deposit market-init bug**, **KYC/sanctions effects on borrower liquidation**, **blacklist effects**, **non-standard/transfer-tax tokens**, and **misuse of admin rights** ("malicious admin multi-sig") as excluded. The **prohibited-activities list closes more** — and **CORRECTION (same session): that list is the IMMUNEFI PLATFORM DEFAULT, not a Flux-specific term.** The page payload carries it under the keys `defaultOutOfScopeWebAndApplications` / `defaultProhibitedActivities`, and re-running the extractor across seven other programs (Origin, Aevo, deBridge, BENQI, Lista, Threshold, Yearn) returned the **identical text** in all of them, each prefixed *"Default prohibited activities"*. So two rules follow, and the second is the strategic one: **(1) read the word "Default" — platform boilerplate is not a programme-specific exclusion, and never cite it as one**; **(2) on Immunefi, *"any testing with pricing oracles or third-party smart contracts"* and *"testing only on local forks, never mainnet/testnet"* are banned MARKET-WIDE** — so an oracle-manipulation finding is off the table as a submission class on this platform entirely, for every target, not just the RWA-collateralised ones. That materially de-ranks every oracle-rich protocol on the list and should be applied at sector-selection time, not discovered per target. (What *was* Flux-custom, and is the model for what to look for: the two pinned fork-base commits, the named known-issues list — first-deposit market-init, KYC/sanctions on liquidation, blacklist effects, non-standard tokens, admin-rights misuse — and the CompoundV2-up-to-these-commits clause.) **Two consequences.** (a) **The payable surface of a declared fork is the DIFF, and only the diff** — a *gift* for G11c: "is this novel?" becomes mechanically answerable, every line inside the diff defensibly novel and every line outside it defensibly known. But diff against the **DECLARED commit, never current `master`**: diffing Flux's Comptroller against master produced pages of noise purely because Flux is an **older vintage** (`GovernorBravoDelegateStorageV2`, solidity 0.5.16, no `proposeBySig`), while the token-level diff against the declared commit gave **four real changes**. A wrong diff baseline manufactures a false delta — the stale-probe rule one level up. (b) **Rank a narrow-surface target DOWN at selection time**, however much money it holds: expected value = (money at risk) × (fraction of the codebase you may lawfully report on). So `--scope` gives addresses and prices, but **the program page tells you what you are ALLOWED to find** — fetch and read it before the pricing pass, and record the excluded-class list in the target's `spec/SCOPE.md` so no later pass re-derives it.
  **G11c is the load-bearing one, and it has one honest limit: on a platform like Immunefi there is NO public list of
  already-submitted findings, so novelty can never be PROVEN.** What you can do instead is (1) front-load every *checkable*
  source — program Known-Issues/out-of-scope, prior audit reports (**check they cover the DEPLOYED version**), **Solodit**,
  changelog/closed-issues/fix-commits (a fix commit for the same bug is a clean kill, and a *recent* fix means someone is
  reporting in this area now), Rekt/exploit history, and for a fork the upstream's own issue tracker — and (2) **target
  surfaces where a duplicate is structurally unlikely**. Crowded: generic reentrancy, spot-price oracle, generic access
  control, ERC-4626 rounding, standard proxy issues — Slither finds the shape, so a crowd finds it. Under-crowded, and this
  is the targeting rule: **degenerate-input guards** (see the checklist family added 2026-09-22), **asymmetric state
  transitions** (a flag set on one path, never reset on the inverse — this is our S1-mirror tabulation job), **variable
  mixups in multi-recipient fee paths**, **fork diffs** (the base is maximally crowded, the *diff is unread* — which is why
  fork-hunting is simultaneously our highest-yield door and our best dedup posture), and **vertical-specific mechanisms**
  (already our doctrine: "requires understanding the product, which is exactly why it is higher-severity and harder to
  duplicate"). Three dupe-resistance tests on any candidate before it is written up: **could a linter have found this?**
  (yes ⇒ assume a crowd got there first) → **is it in a prior audit's acknowledged list or the program's Known Issues?**
  (yes ⇒ KILL, do not file) → **does the report depend on the diff, the vertical mechanism, or a state-reset asymmetry?**
  (yes ⇒ strongest posture; a generic guard on one of eight siblings ⇒ weakest). **Never submit one root cause as two
  adjacent submissions on a platform channel** — splitting is rational on Code4rena (auto-dedup, no validity penalty) and
  actively harmful on Immunefi, where duplicates are rejected outright and repeat offenders lose standing. **If G11c cannot
  be cleared because the local dedup source is a stub, that is a COVERAGE GAP that blocks the pass — not a green light.**
- **PLATFORM ENTRY ECONOMICS — VERIFIED 2026-09-22, AND THEY RAISE THE BAR RATHER THAN LOWER IT.** Read these as G11a input; do not reason about a platform from memory (both platforms render client-side, so `curl` returns an SPA shell — the docs live at `docs.immunefi.foundation` and `docs.hackenproof.com`). **Immunefi:** the **Hunt Points** program (live since **2025-10-23**, airdrop-linked) pays points only for **valid *and PAID* reports**, weighted by severity, payout size, program type and cumulative-earnings milestones — and **attackathon / audit-competition reports are explicitly discounted "to account for duplicates."** The operative line for us is the ban rule, verbatim: *"Only valid reports earn reports. Spamming invalid reports in an attempt to earn points will result in an immediate and permanent ban."* So the points economy **punishes spraying** — a track record is built by one paid finding, not by volume, and an invalid submission costs standing rather than just time. **HackenProof:** there is an **explicit newbie gate** — its *crowdsourced audits* require **"qualified auditor"** status, met by at least one of: submitted valid **High/Critical** issues on HackenProof, or completing the **Smart Contract Hacking Course by JohnyTime** (list not fully enumerated on the page — treat as ≥2 criteria, re-check before relying on it). Its **bug-bounty programs are open** (that is where the published program list lives), alongside VDP and DualDefense-audit variants. **Neither platform's policy is a blanket KYC rule** — on Immunefi the KYC flag is **per-program** and is already returned by our own `immunefi_targets.mjs --scope` fetch, so treat KYC as a **mechanical per-target field**, not a platform-level question. Term-of-use sanction clause on Immunefi: citizenship/access from OFAC-sanctioned countries is out.
- **G10 — PAYMENT CHANNEL. RUN THIS BEFORE G8, BEFORE ANY CODE IS READ (2026-09-16, the actual cause of a $0 campaign).** Three weeks produced reproduced findings across three targets and earned **$0 and zero feedback** — not because the findings were weak, but because every target came from a **TVL sweep of protocols with no bounty program**. A perfect critical on a protocol that never had a buyer pays nothing and answers nothing. The gate: **does this protocol have a live bounty program or open competition that (a) pays for the severity class you expect, (b) is reachable without KYC you cannot pass or a fee you will not pay, and (c) lists the contract you are about to audit INSIDE the published scope?** If no, it is not a target — it is a volunteer project. G8 asks "can this contract lose funds"; G10 asks "will anyone pay me when it does." A contract that can lose $17M and pays $0 scores **worse** than one that can lose $500k and pays $100k. Corollary that inverts the old targeting thesis: "less audited = more bugs" optimises bug **count**, not bug **value** — an unaudited small protocol has no program and no money on-contract, so the bug you find is a griefing/DoS bug (the measured audit2 profile: one medium DoS failing G6, one latent low, one informational — real, reproduced, worth nothing). Prefer newly-listed **funded programs that already pay elsewhere**. Channel inventory, per-platform entry costs, and why continuous bounties beat contests without a track record: `defi-security-research/references/paying-program-channels.md`.
- **G8d — A CONTRACT HOLDING ITS OWN GOVERNANCE TOKEN IS NOT A FUNDED TARGET, AND "DOLLARS AT REST" IS THE WRONG SORT KEY (2026-09-22, measured twice in one pass).** G8 asks "does it hold funds"; G8b asks "whose code is it"; **G8d asks "is the money real, or is it the protocol's own token priced by its own market quote?"** Measured: Olympus's scope priced **$110.28M** and it ranked #1 on the whole filtered Immunefi shortlist — but **$109.56M of that (99.3%) was a single module holding 20,263.59 GOHM of a 49,875.93 total supply, i.e. 40.6% of the protocol's OWN governance token** (`0xD3204Ae00d6599Ba6e182c6D640A79d76CdAad74`; `cast code` = 10,471 bytes, EIP-1967 impl slot **zero**, so not even a proxy). Strip the own token out and Olympus's external money is **~$716k (sUSDS + USDS)** — mid-table at a $3.33M headline bounty. The same pattern shows up in Origin Protocol's number: its `xOGN` entry is **$12.72M of Origin's own OGN**, and `WOETH`/`wsuperOETHb` are its own LSTs. **Why it matters:** an own governance token has no redemption path — you cannot drain 40% of a supply without exit liquidity, and its "price" is a market quote that moves with the very bug you might find. It is the same family as G8b (third-party core) and G8c (team Safe): **value that is visible, prices high, and cannot leave.** **How to apply:** before ranking any priced target, decompose its at-rest total by token and ask per asset — *is this external collateral/stables, or the protocol's own token / its own LST / a third-party core?* Rank by **external drainable value**, and state the own-token share explicitly rather than letting it inflate the headline. A target whose total is mostly own-token scores on its residual, not its total.
- **DEDUP THE SCOPE'S ADDRESS LIST BEFORE PRICING IT, OR THE TOTAL INFLATES ~1.8x (2026-09-22, a bug in our OWN pipeline, caught by a self-check).** The buyer's scope page lists **one address once per ASSET entry**, so Arm/AMO/vault contracts appear **2–3×** in any naive extraction (Origin Protocol: the Ethena ARM appeared 3×). The v7 pipeline summed the list as-is, so the per-explorer total was inflated — measured on Origin, the etherscan host reported **$82.83M against a $45.02M distinct-address truth (1.84×)**, before the on-chain read even began. **How to apply:** dedup by `0x` address before summing (`v7_scope_g8.mjs` now does), and treat "addresses found" as a *raw* count with a separate distinct count — a scope claiming 108 addresses may be 60 contracts. The general rule is the same one that governs every extractor here: **an extractor that cannot reproduce a known count is not evidence** — cross-check the summed total against a distinct-address recomputation before quoting either.
- **G9 — RESOLVE THE PROXY IMPLEMENTATION SLOT BEFORE SCORING A TARGET (2026-09-16, hid ~$56M of coverage).** Recon that stages a proxy address has audited nothing. The specific failure: `pull.mjs:56` resolved the impl ONLY from the explorer's `implementations[]` field, which Blockscout omits for ERC1967/UUPS — so the proxy was staged, own-code scored `0`, and three real targets read as empty. **Read the slot from chain state, never from an explorer field:** impl = `cast storage <addr> 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`, beacon fallback = `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50` → `implementation()`. A target with zero own code is a **recon failure**, not a clean target, until the slot has been read. Recovery in that pass: 3/3 proxy-fronted targets had unread verified impls, 4,326 lines (874 / 1,673 / 1,779).
- **A filter built on a constant is not a filter (2026-09-16).** `analyze.mjs:71` selected an entire campaign's candidate pool on `p._ageDays <= 180`, derived from DefiLlama's `listedAt`. All **6,580** rows carrying that field held the same three day-values (20691–20693 = the 1970-01-01 epoch sentinel) — the field carried no time signal at all, so the "≤180d fresh" pool was 152 rows selected on a constant, and the plan's premise that it had found *fresh* protocols was never true. **Before trusting any field filter, print the DISTINCT count of that field.** One distinct value ⇒ dead field ⇒ the filter selects nothing but ordering. Same family: values above ~1,000% in `change_7d`/`change_1d` are division-by-near-zero base effects on new listings (one protocol read `+4,328,704%`), not growth — read the 15–150% band.
- **A pass that ends with neither a PoC nor a written kill has failed, however many addresses it gated.** Measured root cause of a week at 0 findings: 8 targets with verified source staged on disk, **not one `spec.json`, `TMAAR.md` or `findings/` dir among them** — every folder held only `recon/`. Discovery is not progress. A door that returns addresses has produced a lead, not a pass; close it with a PoC or a written reason, and treat discovery as a refill activity with a hard time box. Corollary: a door whose measured ceiling is zero (the 2026-09-15 firehose returned 36 funded → 0 own-code, exactly as its own spec predicted before it ran) should be killed on the spec, not executed and post-mortemed.
- **THE HEURISTIC BANK IS A HYPOTHESIS SOURCE, NOT EVIDENCE (2026-09-24).** Its 135 source files contain no
  PoC, no fuzz harness and no invariant — verification there is hand arithmetic, and at least one of its own
  worked examples is internally inconsistent. Cite a bank entry as the reason to *look*, never as the reason
  to *believe*: G0 still requires the reproduction.
- **A negative is only evidence if the detector could have fired.** Enumerate the shapes your parser covers, plant a positive fixture per shape, keep a secure fixture proving no false-positive, and re-run an old detector against new fixtures to show it FAILS. Print one RAW response before believing a table you generated.
- **`cast call` RETURNING `0x` WITH rc=0 IS NOT SUCCESS — IT IS AMBIGUOUS (2026-09-15, cost a false Critical).** A call that executed and returned nothing produces exactly the same output as a call whose selector is never dispatched: `0x`, exit code 0, no error. On 2026-09-15 this read as "an unprivileged address can call an unguarded `transferTokensOut` on a contract holding ~$2.7M" — it was an artifact. THE MANDATORY DISAMBIGUATOR: every reachability claim needs a call that MUST revert if the body runs (an impossible input — 1000x the balance, a non-contract asset address, a zero-address receiver) AND a known-reverting control on the same endpoint. Here `USDT.transfer` over-balance reverted (rc=1) while `transferTokensOut` at 1000x did not — proving the detector worked and the function simply was not being dispatched. Corollary that is stronger than bytecode grep: the selector CAN be present in the runtime code and still not dispatch (flattened bundles, data tables, or a source ≠ deployed contract), so bytecode presence is not proof either — run the reverting-input test.
- **A `0x`-returning call needs its rc checked, never eyeballed.** `cast call ... | head -1` prints `0x` for both "succeeded, empty return" and "reverted with empty data"; always capture `$?` and always run a control on the same RPC endpoint first. An endpoint that is itself failing returns `0x` too.
- **Never infer a missing check from the client's absence of handling.** Probe the endpoint; a schema-driven 400 enumerates the real validation in one call.
- **Watch the load-bearing nulls**: `== 0` used as "uninitialized" where 0 is legitimate; `totalShares == 0` guards that are unreachable; terminal flags only implied by the UI.
- **Two of your own artifacts disagreeing is a scheduled re-verification**, not a judgement call — resolve with primary data, never by picking the version you like. Corrections get a marked correction note in the finding file (kept, never silently rewritten).
- **Write the finding the moment it is proven** — fan-out children die on iteration limits or billing walls; a deliverable written early survives the death of its author.
- **SIBLING ASYMMETRY IS THE DETECTOR (2026-09-16, turbo-loop F-01).** When a contract has a family of similar functions, tabulate which guards each one carries; the single one omitting a guard its siblings all apply is the bug. Measured: **7 of 8** mutating externals on `Bridge2` call `checkMessageNotUsed` and **7** take a `nonce` — `updateValidatorSet` does neither, giving any third party an unprivileged DoS that resets the dispute timer forever. Grep the family, diff the guards, prefer the minority row. Full detectors: `references/checklist-full.md`.
- **A POSITIONAL QUORUM LOOP NEEDS A SIGNER-DEDUP CHECK (2026-09-16, turbo-loop F-02).** `for i { if (signer == validators[i]) cumulativePower += powers[i] }` credits a repeated address once per slot, so `[A,A,A,D]` + one key's signature ×3 = a 2/3 quorum alone. Measure the bound too: the repeated slots must clear the threshold (2 of 4 = 50% must NOT trigger), which is what proves the mechanism rather than pattern-matching it. And treat any "no functionality breaks if X" comment as an attack hypothesis — `Bridge2.sol:146-148` makes exactly that claim and F-02 disproves it.
- **DISTINGUISH REVERTS BY REASON STRING, NOT BY `ok == false` (2026-09-16).** A test "passed" because the call reverted on a role check (`checkFinalizer`) instead of the condition under test — the same trap class as `cast call → 0x`. `vm.prank` the correct role, then assert the decoded revert string equals the expected message. Related: read struct-getter tuple indices off the struct definition — index 4 of `pendingValidatorSetUpdate()` is `nValidators` (= 4), a plausible-looking number that silently asserted nothing.
- **VERIFY A BOARD ENTRY'S FILE ACTUALLY BELONGS TO THAT TARGET (2026-09-16).** The v3 worklist routed a `BrokerV2` dispatch question to turbo-loop `Bridge2`, but `BrokerV2.sol` is a **swinghook** file; the Wormhole note on turbo-loop belongs to `hibachi-bridge`. Grep the `proto` field for the symbol before spending a pass, or the pass is aimed at a file the target does not contain.
- Windows: run filter/parse scripts from FILES (`python C:/path/x.py`), never `python -c` with quotes; helper scripts that don't forward `"$@"`, `anvil_mine` under-mining, and `cast`'s `[2.4e10]` annotation corrupting `awk` fields all produce a confident false timeline (full list: `references/fork-attack-craft.md`).

## Verification
- `python scripts/new_target_spec.py --validate <spec>` returns 0 issues: it checks section evidence, invariant checks, ns_h attempts, and reports `coverage_gap` status.
- Every finding file passes G0-G4 with the gate recorded, and its numbers re-derive from the artifact (not from a summary).
- The chat deliverable is ONE catalogue file (index + detail + reject reasons) + a ranked report — never a replay of the process.
