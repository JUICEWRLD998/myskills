# Pass briefs — the lenses as dispatchable subagents

The peer playbook mandates "run 6 independent agent perspectives" and never defines them. This is the
definition. **Order = severity density** (measured over 125 published audits); dispatch in this order
so the highest-yield lens gets the freshest context.

## Fan-out rules

- **One lens per child, disjoint file sets.** The orchestrator preps the shared facts first (contract
  addresses, ABIs, source paths, pinned fork block, RPC, the spec's `sections[]`) so no child re-fetches.
- **Deliverable-first dispatch:** the child writes its JSON EARLY and updates it incrementally after each
  verified item, and repeats the key numbers in its final message. Children die on `max_iterations` and on
  provider billing walls; only the file and the final message survive.
- **"No finding" is a valid, expected result** — but it must be accompanied by what was checked. A child
  that returns silence has produced nothing usable.
- **Serialise the fork children.** Fork work on a shared RPC is heavy: `--compute-units-per-second 15`,
  `--fork-retries 5 --fork-retry-backoff 2000`, and PIN `--fork-block-number` for anything quotable.
- **The orchestrator re-derives every number that will enter a finding** — child self-reports are not
  verified facts. Machinery, resume-after-interruption and validation gate: see
  `references/verification-pass-orchestration.md` + `references/audit-sweep-resume.md` in
  `defi-security-research`.
- **Red-team pass (mandatory once a finding is proven):** one child whose only job is to DISPROVE it,
  forbidden from reusing your scripts, required to reproduce by a different method. A failure to
  disprove is itself the evidence.

## Common child output contract

```json
{
  "lens": "L1-reward-accrual",
  "sections_touched": ["S2", "S5"],
  "findings": [{
    "title": "[Bug Class] in [Contract/Function] allows [attacker] to [action]",
    "contract": "", "function": "", "lines": "L120-L160",
    "mechanism": "one paragraph, plain language",
    "precondition_cost": "what the attacker must have/do, quantified",
    "reachable_by": "anyone | holder | keeper | owner | unreachable-today",
    "can_extract": "yes/no + how much",
    "evidence": "file:line | tx hash | fork receipt path | on-chain read",
    "confidence": "proven | partial | hypothesis"
  }],
  "no_finding_checked": ["what was examined and came back negative"],
  "open_questions": ["what could not be settled and what would settle it"]
}
```

Rules for every child: `UNKNOWN` is a value — never guess. Every nonzero claim carries evidence.
Every untested idea is labelled a hypothesis, not a finding.

---

## L1 — Reward / accrual accounting (39% severe)
**Scope:** every path that credits, accrues, vests, distributes or forfeits value over time; staking,
multi-cycle vaults, emission schedules, dividend/refining indices, points systems.
**Run the 8-point gauntlet in order:** (1) is the `totalShares == 0` guard actually REACHABLE (a
permanent dead/minimum stake makes it unreachable — that is a bug, not a safety net)? (2) every `== 0`
used as "uninitialized" — can 0 be legitimate? (3) `x * PRECISION / y` under/overflow bounds.
(4) where does rounding dust go — is the pool zeroed anyway? (5) does the claim path filter by the
STAKE's duration/cycle eligibility or merely by availability? (6) catch-up loops advancing one cycle
per tx. (7) are "allocated" and "minted" tracked separately — can a claim fall between them?
(8) events derived from a pre-scan that can `break` early.
**Ignore:** gas, naming, docs-vs-code cosmetics, event emission style.
**Evidence bar:** the accrual identity written in closed form and evaluated at the boundaries.

## L2 — Withdrawal / exit / queue (29% severe)
**Scope:** deposit→withdraw symmetry, queues, cooldowns, two-step/async settlement, refunds, delays,
fulfilment math, "who may abort", and exit paths that depend on an operator or keeper.
**Look for:** a snapshot taken on one transition and re-read live on the reverse; a withdraw path that
uses a different price source than the deposit path; a queue whose fulfilment depends on a role that can
stop running; a user who can abort AFTER seeing the outcome; funds that sit between two stages.
**Ignore:** UX-level delay complaints; documented cooldowns that are enforced and symmetric.
**Evidence bar:** the full state machine decoded, incl. constants read from the contract itself.

## L3 — Rounding / precision / decimals (27% severe, 2.5% of volume)
**Scope:** every conversion, share/asset ratio, scaling between token decimals, fee arithmetic.
**Look for:** ERC-4626 `convertToShares` must round UP on withdrawal (a round-down there was a real
Critical); two branches computing the same kind of amount with different scaling/rounding; comparison or
summing of raw amounts of two different-decimal tokens; a formula whose precision behaviour changes at
the extremes (`x = SCALE/rate - 1` truncating to zero); `min`/`max` across different scales.
**Evidence bar:** exact numbers at the boundary, in exact arithmetic (not float).

## L4 — Fee / tax routing (25% severe)
**Scope:** every setter and branch that touches fees, taxes, referral rewards, protocol take.
**Look for:** fees charged to the protocol instead of returned to the user; fees paid when not due (or
not paid when due); config that can dodge a fee entirely; a recipient setter that reshapes pending/
in-flight accruals without checkpointing the old recipient; internal operations routed through a
user-facing taxed or hooked surface.
**Evidence bar:** the fee actually landing/not landing, measured as a balance delta.

## L5 — Funds locked / DoS / griefing (20% severe AND 9.6% of volume)
**Scope:** anything that can make funds unmoveable or a function uncallable — without theft.
**Look for:** a suspended/banned/blacklisted actor who can no longer exit; a griefable unbounded array
or loop; an unreachable terminal flag (`filled`/`settled` only implied by the UI); a required external
call that can revert (blacklistable token, external protocol min/max); a pull-payment that nobody can
pull; the "funds nobody can move" reading that everyone else dismisses as UX.
**Evidence bar:** a fork attempt that leaves the funds stuck, or a clear proof the path is revivable.

## L6 — Access control (+ the mandatory AA clamp) (20% severe; 8 of 34 Criticals)
**Scope:** every state-changing function's gate, initializers, role plumbing, proxy admin, upgrade path,
and any module/account-abstraction surface.
**Look for:** default-state authz — for every access predicate, test with a FRESH/empty account; the
predicate must be FALSE when the caller has done nothing (`0 == 0` self-admin; "holds 100% of supply"
where supply = 0). Stale or informational fields used in guards (any field not updated on all lifecycle
paths must never gate authz).**Mandatory clamp — AA / session-key / module authz (10 of 34 Criticals):**
key identity (unused AND not registered to another wallet), whose `validUntil`/`expiry`/`owner` is read
(subject's field vs caller's), `msg.sender` is not the caller in a module context (`sender` taken from
calldata), and proof CONSUMPTION (nonce/used-flag) vs bare verification = replay.
**Evidence bar:** the exact predicate evaluated, and the revert/allow result for the fresh-account control.

## L7 — Web2 / off-chain / frontend (22% severe, 9 Highs — do not skip)
**Scope:** only when an app surface exists (API, backend signer, relayer, webhooks, indexer).
**Look for:** decimals/format handling, parameter spoofing, missing server-side validation (PROBE the
endpoint — never infer absence from the client, and remember a custom serialiser like superjson can make
"field not received" look like "field not validated"), error handling that turns a failure into a silent
success, and off-chain trust anchors (one hot EOA signing everything).
**Evidence bar:** the actual request/response pair, with the envelope shape recorded.
**Note:** "the client is the only bound I can find" is not "there is no server-side bound" — mark OPEN.

---

## The three gap passes (cross-lens only)

Run only AFTER L1-L7, and report ONLY bugs that REQUIRE 2-3 lenses: a bug one lens can see belongs to
that lens. Full seam checklists live in `templates/gap-hunter-scan.md`.

- **G1 Flow gap** — execution x periphery x first-principles: value computed before an external call and
  used after; delta-checks (`received = after - before`) followed by `>= amount`; callbacks moving control
  mid-flow while post-callback code assumes pre-callback state; multi-step ops individually correct whose
  combined end-state contradicts the protocol's stated purpose.
- **G2 Trust gap** — access x economics x asymmetry: a correctly-gated actor who can systematically
  extract value (sandwich-able params, `amountOutMin = 0`); the same operation priced differently by
  entry path; an admin setter that changes the destination of in-flight value.
- **G3 Numerical gap** — precision x invariant x boundary: an invariant that holds in exact arithmetic
  but drifts under rounding over N operations; a boundary where precision behaviour flips; an invariant
  skipped on an early-return/zero-input fast path.

Each gap result must carry `seam / trace / violated_principle / proof` (proof = concrete numbers).

## Fork-attack brief (the gate, not a lens)

Attempt every `never_should_happen[]` entry on a pinned fork. Impersonate owner/admin/keeper/**oracle
provider** (drive the consumer's callback with `msg.sender == oracle`), send malformed calldata, replay
signatures, re-enter through callbacks, grief via loops, race refunds/withdrawals. Findings = attacks
that succeed or partially succeed. **Static reading alone never yields a clean verdict.** Technique bank
and the traps that fake a result: `references/fork-attack-craft.md` in `defi-security-research`.
