# On-chain invariant forensics: proving how a protocol actually behaves

Use when the source is verified and readable, hypotheses exist, and the question is whether the LIVE
protocol behaves like the source. This is the loop that produced a proven Critical on Sato
(2026-09): two accumulators drifting apart, self-amplifying, stranding the reserve.

## Archive access — find it before you design the investigation

Public nodes commonly refuse pre-archive-window state: `eth_getCode`/`eth_call`/`eth_getLogs` at an
old block fail with "Archive requests require a personal token" (publicnode) or silently answer from
latest. RPCs that DID serve archive `getLogs` + historical `eth_call` on 2026-09: `https://0xrpc.io/eth`,
`https://eth-pokt.nodies.app`, `https://rpc.mevblocker.io` (candidates also: `eth.drpc.org`, `1rpc.io/eth`).
Probe one cheap historical call per candidate before building anything around it.

**PITFALL — never bisect for a deploy block with `eth_getCode` on a non-archive RPC.** The node
answers from latest state, so the bisection converges confidently to a WRONG "first block with code"
(Sato: reported 25,947,162, real genesis 25,015,094 — off by ~932k blocks, ~112 days). Get genesis
deploy facts from the contract's own immutables/getters or the explorer.

## The loop (in order; each step is cheap and each one gates the next)

1. **Write the invariant in closed form** from the verified source. Sato:
   `totalMintedFair == K*(1 - exp(-ethCum/S))`, i.e. the ETH-side accumulator and the token-side
   accumulator must sit on the same curve.
2. **Sample it across history** with archive `eth_call` — one call per block for each state variable,
   all storage reads, so ~10 blocks is a second's work. Print `gap = f(state)` per block.
3. **Bisect — but with a MATERIALITY threshold.** A 1e-9 threshold found integer-rounding noise at the
   first block and sent the investigation down a false trail. Scale the threshold to TVL (0.01-0.5 ETH
   for a single-digit-million protocol) and bisect only for jumps that matter.
4. **Compute the invariant in EXACT arithmetic.** Float64 cancels catastrophically when the invariant
   is a difference of two ~1e3-magnitude terms: float readings showed phantom 0.001-ETH "steps".
   Python `decimal.Decimal` at 50 digits (`.ln()`, `.exp()` are built in) gave stable values to 18
   decimals and confirmed the growth was real.
5. **Decompose one block whose delta is material** — see the recipe below. This localizes the leak to
   a trade type instead of a whole history.
6. **Derive the per-operation dynamics analytically.** Spot values are not enough: differentiate the
   invariant under each code path. Sato: buys change the gap by `e*(1 - exp(-g/S))` (amplifying), sells
   preserve it EXACTLY (`g' = g`).
7. **Measure impact on a fork** (see fork PoC patterns) and report the fork block number.

## Block decomposition recipe

* Read every relevant state variable at `block-1` and at `block` (archive `eth_call`).
* Pull the trade evidence for that block: token mints/burns = `Transfer` events with topic1 or topic2
  = `0x0`; pool swaps = the pool manager's `Swap` events filtered by poolId.
* Replay the trades in execution order using the VERIFIED source's math; compare predicted vs observed
  deltas for each state variable, and report the residual.
* A residual of 0 (to 9 decimals) proves the code path is faithful — Sato's buy-only block reproduced
  the full state exactly, which is what made the divergence attributable to the interaction between
  the two accumulators rather than to a misread of the buy path.

**PITFALL — `tx.value` is NOT the swap's ETH when the buyer is a smart contract.** A contract buyer
funds the swap from its own balance, so a mint event can sit in a tx with `value = 0` (Sato block
25,018,272: three mints totalling 8,804 SATO, only 0.7 ETH of `tx.value`, ~1.686 ETH implied). Derive
the implied ETH by INVERTING the forward curve on the observed mint instead of trusting `tx.value`.
Per-trade ETH attribution also needs internal transfers (traces), which public RPCs usually lack.

## The high-yield pattern: a one-way ratchet in two accumulators

Generalize this. Look for TWO state variables that are only mutually consistent when equal — curve
position vs fair supply, totalAssets vs shares, debt vs collateral, reserve vs liabilities. Then:

* Spot equality proves nothing; check the PER-OPERATION DELTA of the discrepancy.
* The exploitable signature is a RATCHET: one operation amplifies the discrepancy, another preserves
  it exactly, and nothing ever re-syncs them. Such a protocol cannot heal — any initial asymmetry
  (integer rounding, a launch bonus/discount window, a fee split) grows monotonically.
* Quantify the amplification law. Sato's gap grew as `dg/g ~ de/S` (exponential in cumulative buy
  volume): a rounding-scale seed of ~1e-11 ETH at block 25,017,000 had become
  `+466.155974625857930601 ETH`. Cross-check with an independent volume proxy — accrued fees were 0.3%
  of gross volume (100.84 ETH of fees -> ~33.6k ETH gross, ~half buys), which matched the arithmetic.
* The two sides then price the same asset differently. Sato's buy/sell spread was exactly `exp(g/S)`
  = 2.54x, i.e. a measured 60.89% loss on a 1 ETH round trip against a documented ~0.6% fee cost.

## Recovering a v4 pool key without docs

You need `(currency0, currency1, fee, tickSpacing, hooks)` to drive the real swap path; currency and
fee are usually pinned by the hook's own validation, leaving tickSpacing. Neither the DeFiLlama adapter
nor the project's dashboard JS carried it.

* Probe route: `poolId = keccak256(abi.encode(key))`, then `PoolManager.getSlot0(poolId)` for candidate
  spacings. A non-existent pool REVERTS WITH EMPTY DATA — "no return" from a CLI call IS the revert, and
  only one spacing will answer.
* Robust route: `eth_getLogs` for the manager's `Initialize` in a window after the hook's genesis block.
  Topics = `(sig, poolId, currency0, currency1)`; data = `(fee, tickSpacing, hooks, sqrtPriceX96, tick)`.
  Match the entry whose `hooks` equals your target. `scripts/find_v4_pool_key.py` decodes it.

## Fork PoC patterns for pricing / accounting bugs

* **Round trip through the protocol's own router**: `vm.deal` ETH to a trader, `buy`, then
  `vm.roll(block.number + 1)` (clear any same-block cooldown), approve and `sell`. Report the loss in
  bps. This is the single most convincing artifact for a pricing defect.
* **Prove stranding**: grant the test address the ENTIRE supply via `vm.store` on the token's balance
  slot (OZ ERC20: `_balances` is slot 0, so `keccak(abi.encode(addr, 0))`; check the layout — a token
  that declares variables after inheritance still has ERC20 storage first, and immutables consume no
  slots), then burn the whole supply in one `sell`. Assert what was paid out, what the contract still
  holds, and that no function can move the remainder. Sato: entire 13.68M supply paid 525.26 ETH while
  568.58 ETH stayed in the hook permanently.
* Compare the measured payout against the reserve the way the protocol prices it, not against the
  contract's raw balance — the difference IS the finding.

## Prove WHERE it started (don't blame the wrong mechanism)

Sampling today's value only tells you the invariant is broken. Measure it at deploy and at the END of
every special window (launch bonus, discount, migration, parameter change) before naming a cause:
Sato's seed was initially attributed to the 100-block entropy window, but the gap was EXACTLY
`0.000000000000 ETH` at block 25,015,195 (the block the window closed) — so the window was innocent
and the seed was integer rounding inside `mintFor`, visible as ~1.3e-11 ETH ~1,900 blocks later.
Cheap to check, and it stops a false root cause reaching the report.

Then make the amplification law FALSIFIABLE. The law predicts how a proxy quantity must behave; test
it on independent windows and report the spread. Sato's `d(ln g) = dV_buys/S` predicted that
fee-implied volume (0.3% per trade) would attribute ~50% of gross volume to buys; four independent
windows gave 44.8%, 53.4%, 51.2%, 44.4%. A prediction that lands where the mechanism says it should,
across windows you did not choose to make it fit, is worth more than any single spot value.

## Asserting the dynamics on a fork (tolerance discipline)

The strongest artifact is not the round trip alone but measuring the INVARIANT ITSELF before and after
each operation, against the live contract, via the protocol's own router:

* buy -> print `delta gap`; assert it is positive and within a relative BAND of the closed-form
  prediction, never equality. A first-order law ignores the second-order term: Sato measured
  0.604776 ETH against a first-order 0.604537 ETH (+0.04%), which failed an exact assertion and would
  have been "fixed" by loosening the wrong thing.
* sell -> assert the gap is NOT REDUCED (a one-sided bound) plus a dust tolerance. "Preserved
  exactly" is true to integer-rounding dust, not literally: 6,500 wei of drift on a 4.67e20 wei gap
  = 1.4e-17 relative. `assertApproxEqAbs(.., 1e9)` + `assertGe(after, before)` states the real claim;
  `assertEq` does not.
* Useful trick for reading the inverse curve without new math: for a curve whose inverse is
  `S*ln(K/(K-T))`, calling the BURN function with degenerate arguments — `burnFor(T, T)` — evaluates
  exactly `S*ln(K/(K-T))`, i.e. the curve position of `T`. That is how the gap can be computed inside
  a test with only the protocol's own library.

## Unrecoverability + public-figure checks (do all four; they are what turns a bug into a report)

1. Enumerate the contract's ENTIRE external surface from the verified source and list the functions
   that can move the asset. Sato: three views + v4 callbacks + `receive()`, no sweep/withdraw/admin, and
   no setter for any curve variable.
2. Check proxy slots on-chain — EIP-1967 implementation, admin and beacon — for zero (and remember a
   beacon proxy hides its impl one hop away). Non-proxy + no admin function = nobody can recover funds,
   including the team; say so explicitly.
3. Grep the verified source for `delegatecall|selfdestruct|assembly|\.call\{|\.transfer\(|\.send\(`
   rather than inferring from bytecode (see the opcode pitfall in SKILL.md).
4. Compare the PUBLIC figure against the redeemable one. Aggregators often read the protocol's own view
   of gross reserves: DeFiLlama reported Sato's TVL as $2,439,622 (= `curveReserveEth()` = `ethCum`,
   the reserve they advertise) while the redemption path could pay only 526.84 ETH — a 47%
   overstatement of redeemable backing. Quote the aggregator, the block and the date; it is independent
   corroboration that the discrepancy is real and being reported as if claimable.

Also quote the project's OWN documentation against the implementation where it contradicts (Sato's
docs define the reserve as `balance - feesAccrued` — precisely `ethCum` — and say it "moves out only
through burn/redemption execution", listing `admin reserve withdrawal` among the things the design
deliberately lacks). A source-verified implementation contradicting the protocol's own published model
is far harder to wave away than an auditor's opinion about intent.

## Framing discipline

State plainly whether the defect is attacker-profitable or value-destroying. A permanent stranding /
broken exit price is still High/Critical under a loss-of-funds mandate, but it must not be dressed as
an exploit, and the report should say which it is. Verify whether the contract is immutable: if there
is no repair path, the disclosure value is a holder warning and a migration, which changes the
recommended remediation.
