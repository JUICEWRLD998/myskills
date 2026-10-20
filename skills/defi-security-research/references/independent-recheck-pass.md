# Post-audit independent re-check (V0 doc track / V1 falsification / V2 claims audit)

When to run: after the findings are consolidated and BEFORE anything is sent to the team or published. Also run it
on demand when the user asks "can a black hat actually drain this?" or "are these numbers right?" — that question is
the trigger, not a threat to the conclusion.

Validated 2026-09-12 on Sato (AUDIT 4): 3 tracks, ~27 claims indexed, 4 corrections applied, nothing falsified.
Deliverable: ONE file (`recon/verify/RECHECK.md`) = claims index + per-track detail + corrections + "what this did
NOT establish" + reproduce commands + raw logs in the same directory. That single file is what the user reads.

## The three tracks

- **V0 — third-party figures (orchestrator, cheap, do it yourself).** For any externally quoted number: pull the
  source that actually produces it (e.g. the aggregator adapter from a jsDelivr mirror when raw.githubusercontent
  is 503), reproduce the `eth_call` it makes at a pinned block, reconcile against the aggregator's own price feed
  at its snapshot timestamp, and quote the discrepancy as price-timing if it is <1%. Sato: published TVL = one
  `eth_call` to the wounded accumulator `curveReserveEth()`, reconciled to 0.11%.
- **V1 — falsification suite.** Tests whose GREEN means "the finding survived an attempt to break it". Each test
  must be able to destroy the claim. Sato's seven: state identity + storage-slot vs getter cross-check; the
  per-operation dynamics law (observed vs analytic delta); no-op that *reduces* the invariant (14 sizes + a
  29-size sweep); whole-supply redemption vs the claimed maximum; splitting a redemption beating it whole;
  absence of any admin/upgrade/withdraw path; and the invariant at the earliest possible block (is the defect a
  recent artefact or present from the first trade?).
- **V2 — claims audit.** Re-derive EVERY number the report quotes: your own interfaces, your own arithmetic, no
  snapshot/revert trickery (each measurement is a before/after pair around ONE live op), raw storage reads
  cross-checked against getters, and claim + measurement printed side by side. Re-verify the negative result too
  (best-case arbitrage at several sizes across every reachable venue) — that is the claim most likely to be
  challenged, and "capacity 0 ETH" is a finding in its own right.

Credibility details that mattered: separate test files that import nothing from the audit's own PoCs (the one
exception is re-compiling the protocol's own curve library — the comparison IS the test); exact wei integers
throughout; and the pre-fix failing log kept and committed as the reproduction of any harness defect.

## Harness-defect triage: a red test is a hypothesis, not a refutation

Classify every red before writing it down:

1. **Assertion bug** — expected value is wrong. Sato: `assertApproxEqAbs(ethOut, CLAIM, 1e4)` failed by exactly
   one 0.30% fee because `CLAIM` was the PRE-fee curve value while `ethOut` was post-fee. The fee-exact identity
   (`ethOut == CLAIM - CLAIM*fee/denom`) then held TO THE WEI. A reviewer who writes this up as "claim refuted"
   is wrong and will be corrected by the team.
2. **Harness/state assumption bug** — the environment is not what the test assumes (see the `vm.roll` trap below).
3. **Genuine falsification** — write it up immediately and prominently; this is the most valuable outcome.

Protocol: keep the PRE-fix log, label each item `H-n` with its mechanism and the fix, re-run to green, and state
plainly in the recheck file that no property changed. Also re-derive constants from the deployed contract rather
than trusting the report (`cast call <hook> 'COOLDOWN_BLOCKS()(uint256)'`) when a guard you did not expect fires.

## Foundry/fork gotchas that cost real time

- **`vm.roll(block.number + N)` on a forked test is a trap.** The test contract keeps reading `block.number` equal
  to the fork block, so repeated relative rolls all target the SAME absolute block (all three rolls in one Sato
  loop went to 25,963,311). Use ABSOLUTE roll targets (`forkBlock + 10*(i+1)`) and one fresh actor per round, so a
  caller-keyed cooldown/limit cannot bite.
- **Symptom of that bug:** `WrappedError(0x…hook, 0x575e24b4, 0xaa9a98df, 0xa9e35b2f)` = Uniswap v4
  `CustomRevert.WrappedError(address target, bytes4 selector, bytes reason, bytes details)` — target = the hook,
  selector = the hook function that reverted (`beforeSwap`), 3rd = the inner custom error (`CooldownActive()`),
  4th = context (`HookCallFailed()`). Decode each 4-byte selector with `cast 4byte 0x…` before theorising.
- **Do not point a failing-fork test at an unpinned state.** Pin `--fork-block-number`, and use
  `--compute-units-per-second 15 --fork-retries 5 --fork-retry-backoff 2000` on public archive endpoints.
- **Background runs need ABSOLUTE log paths.** `forge … > ../recon/verify/x.log` in a background shell failed with
  "No such file or directory" (cwd/redirect resolution differs); `> /c/Users/…/x.log` worked. Same for any helper
  script a native tool must read.
- On this host Python is `python` (no `python3`); write helper scripts to files and run them by forward-slash path.

## Corrections table (C-n) — what the pass should produce even when nothing is falsified

A re-check earns its keep by fixing the text of the report. On Sato it produced four, all applied in the same pass:

1. **Denominator/metric pairing.** "466.156 ETH (52.1% of the reserve)" — wrong: 466.156/1087.96 = 42.84%; 52.11%
   was the STRANDED TOTAL (drift + unreachable fees). Pair every percentage with the exact numerator and
denominator it came from, and say which quantity it describes.
2. **Numbers carried over from a DIFFERENT reference block.** The recovery round-trip mint figure (5,741.6 SATO)
   came from the 09-10 measurement while the payout in the same sentence (391,047,750,008,974,069 wei) was measured
   at the current block; at the current block that same 1 ETH buy mints 5,809.326 SATO. Any sentence mixing two
   reference states is a bug in the report even when each half is individually true.
3. **A correction that never propagated.** A wording fix landed in its own evidence file but not in the
   team-facing draft and the ranked report — grep the whole report set for the old phrasing after every correction.
4. **Exact-decimal vs contract-arithmetic rounding.** The PRBMath 18-dp `ln` makes the contract's own `ethAt`
   differ from exact decimal by a few thousand wei (Sato: `ethAt` Δ0, invariant gap Δ3,876, stranded Δ124).
   State explicitly that you quote the raw integer values AS THE DEPLOYED CONTRACT COMPUTES THEM, and give the
   exact-decimal value alongside.

Also record the direction of the error: the Sato re-check found the report UNDERSTATED the stranded balance
(568.58 ETH real vs 567.01 claimed, = claim + one burn fee). Say so — a conservative error still gets corrected.

## "What this did NOT establish" is mandatory

Close the recheck file with it: fork-only evidence (nothing broadcast to mainnet), provider-dependence, which
sub-claims are still estimates (Sato: the "share of capital ever committed" denominator), which surfaces were
probed and at what sizes (6 sizes on one venue, 4 on the curve, one cross-venue pair — not an exhaustive route
search), and any claim taken from the audit's own evidence rather than re-derived.

## Pitfalls

- **Verify your own tooling before writing its output into the report.** A selector-map script compared
  `0x`-prefixed disassembler output against bare `forge inspect` values and reported all 33 ABI selectors as
  "missing" — which proves nothing and would have become a phantom finding. On a suspicious all-negative result,
  suspect the comparator first; fix it, re-run, and only then quote the number. When a scan stays inconclusive,
  mark it inconclusive in the recheck file instead of crediting the audit's original claim to it.
- Do not credit a claim to a probe that did not actually test it ("immutability CONFIRMED" from a selector map
  that was broken); list the probes that did (the 8 admin/upgrade selectors that answer false/absent, the zero
  EIP-1967 slots) and name the on-chain check that resolves the residual (`SATO_TOKEN()` still answering on-chain
  though the optimiser inlined its dispatch branch).
