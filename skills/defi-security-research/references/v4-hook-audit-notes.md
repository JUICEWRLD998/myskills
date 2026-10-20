# v4-hook protocol audit notes (Fables campaign, 2026-09) — Phase 6-9

Class notes for auditing Uniswap v4 hook protocols on new L2s/appchains. Validated on Fables
(tokenized-stocks DEX, Robinhood Chain 4663, audit2 workspace at Desktop/audit2/).

## Architecture shapes seen (and what they mean for the audit)
- "Hook = the whole protocol": per-market hook instances are often full singleton contracts —
  fee schedule + liquidity ledger + access control in one IMMUTABLE deployment (no proxy, no patch
  path → findings need pre-event disclosure; config fixes only via storage levers or redeploy).
  Fables: 13 pools, each with its own hook address; two families:
  - FablesRWA = calendar model: per-pool FloorConfig (open/overnight/closed tiers + opening
    descent spike + closing ramp), fee = feeFloorAt(config, block.timestamp) — pure time math.
  - FablesRamp/FablesRampETH = flat fee + keeper poke (no on-chain vol model; a VolLib
    volatility-fee design was measured and REMOVED pre-launch — memecoins saturate, blue-chips
    need an oracle — worth quoting in disclosures as evidence the team iterated).
- Fee mechanics (v4): PoolKey.fee = 0x800000 DYNAMIC_FEE_FLAG; beforeSwap returns the per-swap
  fee as `fee | OVERRIDE_FEE_FLAG` (0x400000) and can otherwise be a pure `view` (no state write
  per swap = small attack surface; fees charged by PoolManager from the returned override).
  Poke pattern: restricted call setting fee + TTL expiry (≤72h), re-bounded at RESOLUTION time
  (floor = max(config floor, 50% of current autonomous fee)) so a hot key can't pin a low fee
  while the curve ramps.
- Ledger pattern (FablesLedger): ERC-6909 receipts 1:1 with uint128 liquidity units ("solvent by
  construction" — no share price → no inflation attack); fees accrue per (pool,tick-range) via
  Q128 accumulators checkpointed per holder on every balance change; v4 accrues fees LAZILY, so
  "sync" = zero-delta modifyLiquidity that materializes claims; fees settle as PoolManager
  ERC-6909 CLAIMS (mint/burn/take), NEVER token transfers on the fee path (blocklisted or
  fee-on-transfer tokens cannot wedge exits); principal pull happens inside the unlock callback
  with a transient reentrancy guard held. Claim-fee (≤20% cap) charged at sync time at
  min(live rate, rate-when-backlog-opened) via a bounded history walk — "min over window" is the
  defensible shape; attackers choose sync moments so rounding/remainder handling matters
  (mulmod remainder carried as Q128 fraction of one unit, never as raw numerator).
- Unpausable-exit doctrine: principal withdrawal + unstake are deliberately NOT pausable; pause
  is an expiry (≤7 days) not a flag; one-way `pause()` (guardian, cannot shorten/clear) separate
  from delayed `setPaused(0)` (admin lift). A combined setter once handed the unpause to the same
  zero-delay key — worth checking on any fork.
- Dormant ve(3,3)/emissions switches: ledger ships stake/ballotGate/distributor hooks referencing
  a Voter not yet deployed; verify live state (distributor/ballotGate unset ⇒ layer dormant) via
  eth_call before assuming the full design is live.
- Tokens: stock/asset tokens were OZ BeaconProxy v5.2 behind a CUSTOM beacon (2.3KB, no owner()
  getter — AccessManaged-style; check authority()). Beacon → implementation() hop = the real
  upgrade surface; the proxy itself is noise.

## Calendar audit method (reusable, found a real bug)
Market-hours fee models bake a holiday table (SessionLib.bakedClosed: y,mmdd lists). Audit it
DETERMINISTICALLY against market-observance rules, date-by-date, with a script
(scripts/verify_baked_calendar.py):
- every baked date must be a weekday;
- fixed holidays (NYD, Juneteenth, July 4, Christmas): Sat → observed prior Fri, Sun → next Mon;
- floating (MLK/Presidents 3rd/2nd Mon, Good Friday, Memorial last Mon, Labor 1st Mon,
  Thanksgiving 4th Thu).
Result: Fables tables 2026-2030 correct EXCEPT one dropped row — NYD 2028 (Sat Jan 1) observed
Fri 2027-12-31 missing from both 2027 and 2028 lists (2028 has 9 rows, every other year 10).
Severity Low: that Friday prices OPEN tier (~0.10%) instead of CLOSED (0.03%) — overcharges
swappers ~6.5h on a dead market, favors LPs; the toxic reopen (Mon Jan 3 spike) keys off the
preceding Sunday so it is unaffected. Fix on immutable hooks = ops dayOverride bitmap.
Also: baked tables END (2030 here) — later years rely on operator overrides; an ops-process note,
not a code finding.

## Live-state snapshot discipline
Probe getters in ONE batched POST per hook (≤14 calls/chunk, ~6s apart when the explorer fetch
job shares the IP): authority, session hours, dstMode, pausedUntil, claimFeeBps, distributor,
ballotGate, maxFee(poolId), pokeFloor(poolId), pokeOf(poolId), floorConfig(poolId),
currentFee(poolId,true/false). Sanity-check the snapshot against the CLOCK (Sunday 19:00 UTC ⇒
calendar markets must read their CLOSED tier — a live proof the calendar is wired).
Distinguish "getter absent" (eth_call returns 0x/empty → decode None) from "getter returns 0":
an FablesRWA-family ABI applied to an FablesRamp hook returns empty for calendar getters — that
mismatch is how a third hook revision (meme markets, ts=60, different bytecode sizes per market)
got detected. Per-market bytecode-size deltas among same-named contracts = constructor immutables
or revision drift — classify each deployment family from its own verified source, never assume
one contract = one codebase.

## Deployment forensics (constructor args, metadata, per-instance verification) — late-Phase-6 pass
- CONSTRUCTOR ARGS ARE FREE INTEL: the get-sourcecode payload carries a `ConstructorArguments`
  hex field — decode the words to recover immutables per deployment (Fables: poolManager,
  authority, ABSOLUTE_MAX_FEE = 20000 or 15000 pips per market, WETH as a 4th arg on native
  hooks). Watch hex misreads: 0x4e20 vs 0x4e2 (dropped zero) read as a 0.125% cap that
  contradicted on-chain state before the true 2% was seen — decode whole words and sanity-check
  against the maxFee() mapping values.
- solc metadata CBOR is often STRIPPED from runtimes on these chains (no `a2 64 ipfs…` tail on
  ANY hook) → metadata-hash compile-parity is IMPOSSIBLE on-chain. Fallback signal: runtime-SIZE
  variance among deployments that carry byte-identical verified mains (AAPL 34388 == TSLA 34388
  ≠ SPYGLD 35868 ≠ NVDA 33070, with constructor args that cannot change size) ⇒ deployed
  bytecode does not uniformly byte-compile from the verified source — either per-deploy
  optimizer settings or revision drift. Resolution = LOCAL recompile parity sweep (same solc
  version, sweep optimizer-runs) comparing modulo metadata-strip + immutables.
- "EVERY HOOK IS VERIFIED" DOCS CLAIMS ARE PER-INSTANCE, NOT CLASS: some deployments return
  empty SourceCode / repeated HTTP 500s on fetch while others verify instantly (Fables:
  AMC/CASHCAT meme hooks unverified across 2 rounds; AccessManager unverified). Enumerate every
  instance's verification status independently; unverifiable code that moves LP funds is a
  trust note for the report even when the docs claim full verification.
- ROLE DISCOVERY WITHOUT SOURCE/ABI (unverified AccessManager): pull RoleGranted logs
  (topic0 0x2f8788117e7eff1d82e926ec794901d17c78024a50270940304540aef656dbd) via
  eth_getLogs over the manager's lifetime → member addresses + roleIds per block. Label known
  roleIds by keccak of convention names (e.g. OZ MINTER_ROLE = 0x9f2df0fed2c77648de5860a4cc508
  cd0818c85b8b8a1ab4ceeef8d981c8956a6; a grant to 0x…dead = role burned). Pair with eth_call
  on AccessManager getters once selectors are known.

## Token-layer issuer powers (the defining external trust for RWA markets)
Asset tokens were Robinhood's OWN stack, not Fables': token proxies = OZ BeaconProxy v5.2 behind
AccessControlsRegistry 0xe10b6f6b… (AccessControl beacon: upgradeTo w/ BEACON_UPGRADER_ROLE,
blockAccounts w/ BLOCKER_ROLE, global paused w/ PAUSER_ROLE); implementation = `Stock`
(0xb35490d6…, upgradeable ERC20Permit): per-token pause, account blocklist on every
transfer/approve/permit, mint/burn (MINTER/BURNER), adminBurn (ADMIN_BURNER_ROLE — burns ANY
holder, no pause/blocklist checks), ui-multiplier (display scaling), oracle pause, uid/terms.
Consequences for the threat model: token pause OR blocklist bricks LP principal withdrawal
(PoolManager.take → token.transfer reverts) — the ledger's "unconditional withdrawal" guarantee
is token-layer-dependent (team docs concede issuer pause overrides); adminBurn can destroy LP
balances; an impl upgrade swaps all logic. Fables cannot mitigate; the audit must walk issuer
scenarios against each ledger invariant and report the boundary as centralization/external trust
(these powers are presumably Robinhood regulatory/security tooling — frame, don't editorialize).

## Fables campaign state (resume anchor 2026-09-06)
Workspace: Desktop/audit2/ (ARCHITECTURE_MAP.txt, PHASE6_RECON_CHECKPOINT.txt, HUNT_LOG.txt,
deployed_sources/, data/live_pools.json + hook_state_snapshot.json).
- Live map: 13 pools decoded from registry allPools() (struct = PoolKey + bytes32 poolId + bool
  active, 7 words/element). registry 0x159a113E…; AccessManager 0xA362D98B… = authority of every
  hook (source NOT verified on explorer → black-box; recover ABI from bytecode if roles needed);
  v4 PoolManager 0x8366a39C…; V4FeeAdapter (protocol fee controller) + StateView verified.
- Configs live: claim fee 0, distributor/ballotGate unset, no pokes; NVDA curve
  open 1000/overnight 800/closed 300 pips + spikeMult 5 (spike 4000) + closeFloor 2200/30min;
  AAPL/SPYGLD calm 500/350/300 no spikes; ETH flat 700 pips (cap 6000); AMC-family caps 2%.
- Confirmed finding F-C2-1 (Low): 2027-12-31 NYD-2028 observance missing from baked table
  (see above; HUNT_LOG.txt).
- Open leads RESOLVED (deep audit P6-11 COMPLETE 2026-09-07; 7 findings F-A1..A7 in
  Desktop/audit2/FINDINGS_MASTER.md; disclosure-bundle decision pending with user): C1
  (session-hours x ramp-window cross-config) CONFIRMED but Low/admin-gated (pairing needs
  role2 setSessionHours 1h-delayed + role0 setPoolConfig); C3 (midnight ramp wrap) DISPROVEN
  (hold needs sec>=closeS; exhaustive scan zero hits); meme hooks ALL VERIFIED (earlier
  'unverified' was transient Blockscout 500s — retry across rounds before concluding; AMC/
  42039B = newer FablesRWA w/ withdrawAndClaim, CASHCAT = FablesRamp, AMC-ETH = FablesRWAETH,
  PONS-ETH = FablesRampETH-v2 native).
- HEADLINE FINDING (top-tier class): AccessManager role0 = ONE EIP-7702-delegated EOA at
  execution delay 0 on EVERY config lever (setPoolConfig/setClaimFee/setDistributor/setPaused/
  registry/AM self-admin incl. setLock+grantRole) while code comments assume a delayed admin
  ('setPaused stays on the delayed ADMIN_ROLE'; 'the AccessManager execution delay on
  setClaimFee bounds history growth') — on-chain matrix via canCall/getTargetFunctionRole
  (tmp_work/am_matrix.json). Key compromise = fleet fee flattening to MIN_POOL_FEE + 20%
  claim fee + role grant; LP principal safe (withdraw reads no admin state). ALWAYS diff the
  on-chain role/delay matrix against code comments. Only delayed surface = role2 calendar ops
  (3600s); pokeFee role1 (keeper bot 0x1b6a88 + 2 dormant keys) delay 0; pause/clearPoke role4
  (0x5cda43, never used).
- Second external finding class: RH Stock-token issuer powers (registry-global pause/blocklist,
  adminBurn skipping pause+blocklist checks, one-beacon upgrade across ALL tokens) override the
  ledger's unconditional-withdrawal guarantee; blocklisting PoolManager 0x8366 DoSes all 9
  stock pools at once.
- Ledger core (FablesLedger/LedgerLib) survived 200k+ adversarial-window sims CLEAN (remainder
  carry, over-issuance, claim-walk min, solvency partition identity); poke bounds, registry,
  pause semantics clean; the three prior-bug classes (free-sync raid, snapshot/live drift,
  Q128 dust carry) verifiably fixed in this source.
- Docs gems: the team's own risk page pre-discloses keeper-band mispricing, immutable-hook
  defects, stale/missing reference prices — read it before writing findings so you cite the
  acknowledged classes correctly. Claim fee and v4 protocol fee both zero on these pools today.
