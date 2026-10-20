# ve(3,3) / Solidly-family deep-audit execution notes (validated 2026-09 on up v3 / UP33)

Execution knowledge from running Phases 7-9 on a Velodrome/Aerodrome-lineage fork with a custom layer (UP33: gauge-cap machinery, epoch reserve/burn, permanent locks). Generalizes to any Solidly-family audit.

## Architecture semantics that matter (stock, per project)
- Minter: `updatePeriod()` is anyone-callable but advances ONCE per epoch (activePeriod guard) -> exactly ONE `Voter.notifyRewardAmount` per epoch. This single-notify structure makes index fixed per epoch and KILLS most ordering/front-run double-accrual hypotheses — check it BEFORE theorizing, then state the refutation in the hunting log (proves coverage). Mint = emission + growth + team only, mint-balanced; initialize() = genesis airdrops (liquid + PERMANENT ve locks).
- Voter: allocation is index-based (index += amount/max(totalWeight,1) at notify); per-gauge supplyIndex deltas -> claimable; epoch-boundary gating (onlyNewEpoch, vote window at epoch edges); expiredIndexFloor prevents stale gauges double-accruing across an epoch settle.
- VotingEscrow: checkpointed decaying bias; managed NFTs (depositManaged/withdrawManaged voter-only); delegation ONLY for permanent locks; split gated by team-set canSplit; voted[] blocks withdraw/merge/split/unlockPermanent.
- Reward (fee/bribe) contracts: PER-EPOCH buckets + checkpointed balances; earned() sums epochs since lastEarn using each epoch's LAST checkpoint -> a mid-epoch zero-balance checkpoint forfeits the ENTIRE current-epoch bucket; earlier epochs stay claimable forever. Bribe notify = any caller + whitelisted token; fee notify = the pool's gauge only. `_withdraw` leaves lastEarn/history intact.
- Gauge: SNX-style rewardRate, periodFinish aligned to epoch end; `left()` returns remaining reward AMOUNT (time x rate), NOT time — amount-vs-left comparisons are sane, not type errors. notifyRewardAmount sweeps pool fees first (dust threshold compares amount to DURATION seconds ~= 604800 wei dust).
- Custom-layer hideouts (UP33 example): an epoch-time library (EPOCH_DURATION/EPOCH_OFFSET/VOTE_WINDOW) replacing WEEK constants — trace EVERY use; gauge-cap machinery bolted onto Voter (queued CapMode switches, governance/emergency/default/global-fallback caps, epoch reserve/burn/settle via burnFrom, external GaugeCapController: staticcall quote + state-changing markReportUsed call — unverified = black-box trust boundary); governor-set rebase knob on Minter scaling a growth formula; "cleanup" tweaks in vote paths.

## Invariant sets to write BEFORE hunting (violation = candidate bug)
- Money conservation per epoch: notified == released + open-claimable + aged-out + burned (reserve-backed 1:1).
- liveAccountedReserve == sum of unsettled epochReserve; burnFrom never underflows; killGauge refunds consistent.
- Allocation: sum(weights)==totalWeight; usedWeights[t]==sum(votes); per-gauge cumulative release <= policy ceiling (governance cap / controller report / fallback ladder incl. FAIL-OPEN nominal).
- Epoch gating: cap-mode changes cannot hit an already-notified epoch; settle idempotent.
- ve: supply == sum locked; permanentLockBalance <= supply; poke preserves the pool set, only rescales to balanceOfNFT, never increases votes beyond balance.

## Strongest lead class found (generalize, don't copy)
- Asymmetric auth on vote paths: `poke()` is permissionless and NOT gated by onlyNewEpoch (reset() has both owner check AND epoch gate). A custom `_weight == 0 -> _reset` branch turns poke into an unauthorized reset. Effects: force-unvote writes a ZERO checkpoint into the current epoch of fee/bribe contracts -> victim forfeits the whole current-epoch bucket (per-epoch semantics); same-block-after-transfer tokens report balanceOfNFT == 0 (ownershipChange guard) so a same-block back-run resets a LIVE lock. Verify each variant against the prior audit's acknowledged findings (Shieldify M-01 covered the expired-lock variant) before claiming novelty — label KNOWN-ADJACENT otherwise.

## Methodology lessons
- Label every hypothesis CANDIDATE / UNCONFIRMED / REFUTED / KNOWN-ADJACENT in a PHASE9_HUNTING_LOG with line references and why each invariant holds/breaks. Refutations are valuable output (prove coverage, kill dead ends for the next session).
- Query live state early: weekly/teamRate/rebaseRateBps/activePeriod/epochCount + ve.team/distributor/allowedManager. One Gnosis Safe (171B proxy, slot0=singleton) holding governor+epochGovernor+emergencyCouncil+team+allowedManager = near-total centralization — record it, don't model it as attacker.
- Decode hex state in Python — never by hand (order-of-magnitude slips are easy and poison invariant checks).
- Permissions per path: vote/reset/poke/updateFor/distribute are permissionless by design; verify each claim path's checkpoint interaction rather than assuming claim-loss.
