# R2 rubric — fund-loss-oriented target selection (2026-09-10, user-directed)

Supersedes the R1 rubric for scoring. R1's Phase-1..5 procedure and the CODE-AVAILABILITY /
OWN-CODE-DEPTH gates remain in force; R2 changes WHAT we optimize for.

## The change in one line
R1 ranked "interesting research surface" (novelty, recency, TVL). R2 ranks
"probability that an unprivileged attacker can move user principal out of a contract we can
compile locally". Selection now optimizes for High/Critical loss-of-funds bugs, not for
finding *a* finding.

## Hard gates (fail one = out, before scoring)
G1. EVM + Solidity. Non-EVM (Solana/Stellar/Canton/Move/Bitcoin-native) is out — the operator's
    tooling is Foundry. Pure-Rust/Go cores (off-chain engines) are out unless the on-chain
    Solidity holds the funds. Chain-native/precompile system contracts (e.g. STRATO 0x...1005/1007/100a)
    are out unless they are ordinary verified Solidity.
G2. Source available AND verified for 100% of fund-facing contracts (explorer-verified or a
    public Solidity repo at the deployed revision). Unverified fund-adjacent contract = out.
G3. Own-code depth: custom accounting / ledger / AMM math / liquidation engine. Wrapper, single
    hook, thin fork with no added logic = out. Fund code that is someone else's shared audited
    implementation (Morpho Blue curators, Lagoon ERC-7540 curators, Aave/Uniswap front-ends) = out.
G4. Contract custody of principal: the contract must hold or route user funds (vault, pool,
    collateral, LP, escrow, bridge-lock, queue). Read-only aggregators, RFQ rails that never hold
    funds, points programs and curator/off-chain-managed products = out.
G5. Audit reality check: the *deployed revision* must NOT be covered by a broad, recent audit.
    An audit of an older revision, a narrow scope, or an acknowledged-and-unfixed list is NOT
    coverage — it is a lead.

## Scoring (fund-loss weighted)
LOSS-OF-FUNDS SURFACE
  +10 liquidation / leverage / margin math (bad debt is the classic Critical)
  +9  share<->asset accounting, ERC4626 vaults, redeem/accrue rounding, donation
  +8  debt/interest accounting, CDP stablecoin mint+burn, collateral accounting
  +8  custom AMM/curve math or swap accounting that touches a real reserve
  +7  oracle-priced collateral or NAV, external price ingestion, decimals/scaling
  +6  cross-contract state accounting (registries, ledgers, shares of shares)
  +5  reward/emission/bribe ledger paying out from a funded contract
  +5  withdrawal / cooldown / unstake queue with an escrow or claim step
  +4  upgradeable proxy or admin lever reachable without timelock
AUDIT GAP (this is the R2 point of the whole exercise)
  +20 no known audit anywhere
  +12 audit exists but covers an older revision / narrower scope than deployed
  +10 one weak, old, or short (<=1 week) audit
  -25 multiple recent broad audits by tier-1 firms  (de-prioritize: the bug is probably gone)
CODE & ACTIVITY
  +10 own-logic core >= ~1500 LOC of non-fork Solidity
  +6  active GitHub in the last 90 days, recent contract changes
  +5  deployed within the last 12 months
  +4  meaningful tests present
SIZE (needs funds to lose, but small enough to be under-touched)
  +12 EVM TVL $5M-30M
  +10 EVM TVL $1M-5M
  +6  EVM TVL $30M-60M
  +4  EVM TVL < $1M (real bugs, thin payout)
  -10 EVM TVL > $60M (crowded, usually audited, MEV-bot-covered)
ECONOMIC COMPLEXITY
  +8  complex accounting (multi-asset, multi-pool, indexer/accrual-driven)
  +5  flash-loan-sensitive or single-block-exploitable state
  +4  real users / real volume

Score generates the shortlist ONLY. A 90 that fails a gate is out; an 80 is not automatically
worse than a 95 (user's standing rule: decide qualitatively after the code is read).
Implemented in Desktop/audit3/recon/score_r2.py (with overrides.json for orchestrator-verified
corrections that beat an agent's report).

## What each top candidate must carry into the report
- Solidity + verified-source evidence (explorer URL, contract count, whether implementations are
  verified — proxy shells alone do NOT count).
- Audit reality: what was audited, when, which revision, and why it does not cover deployed code.
- ONE concrete loss-of-funds hypothesis to test in Phase 6.
- Kill reason if it fails a gate, so the next pass doesn't re-derive it.
