# Audit-campaign methodology (user's standing spec, as dictated 2026-09)

The user runs DeFi security research as a staged campaign and does NOT want the audit to start before target selection is approved. Phase names below are theirs.

## Phase 1-5 — Target discovery (executed/validated 2026-09)
1. Discover candidates from https://defillama.com/recent (use the API — see defillama-recon-playbook). Research per protocol: website, category, chains, TVL + growth, volume/fees, launch age, GitHub + activity, deployments, audits, security history, funding, docs quality, architecture, upgradeability, oracles, integrations, cross-contract complexity, source verified, bug bounty, maintenance. Cross-check; mark UNKNOWN rather than guess.
2. Exclude: abandoned, inactive, closed-source, insignificant, token-only, simple forks without custom logic, already-mature/heavily-audited, unassessable. An audit does NOT auto-exclude — check deployed code vs audited revision.
3. Score serious candidates (rubric below). Score ≠ verdict; score only generates the shortlist, then reason qualitatively.
4. Deliver TOP 10 table — per candidate: rank, protocol, category, chain, TVL, launch/recency, audit status, GitHub activity, funding, main attack surfaces, security maturity, score, why interesting, major concerns.
5. Deliver TOP 3 — per target: WHY THIS TARGET / WHAT TO INVESTIGATE / WHAT MAKES IT DIFFERENT / EXPECTED ATTACK SURFACE / ESTIMATED AUDIT DIFFICULTY / POTENTIAL IMPACT. Then choose ONE PRIMARY (highest expected research value, not top score) and explain. STOP for user confirmation before Phase 6.

## Revision R1 (approved by the user 2026-09-07, after the Fables/audit2 outcome)
Amends Phases 1-5. Trigger: a strict "must have public GitHub repo" reading plus thin clean hook cores were starving the funnel (Arcus = private repo, Fables = no repo at all) and produced config/trust-only results instead of code exploits.
1. CODE-AVAILABILITY GATE — GitHub is NOT required for entry. Publicly readable = GitHub repo OR explorer-verified source covering 100% of fund-facing contracts (every principal- and fee-moving contract: hooks/ledgers/registries, the authority/AccessManager, fee sinks/distributors, token proxies that hold LP value). Full-fleet verification is checked at SHORTLIST time (before the primary is chosen), not discovered during deep recon. Any unverified fund-adjacent contract = drop or flag pre-selection. GitHub repo remains preferred when present (enables repo-vs-live diff + compile parity, which verified-only sources can't fully give when solc metadata is stripped).
2. OWN-CODE-DEPTH GATE — extends the existing "simple forks without custom logic" exclusion: thin wrapper / single-hook / minimal-own-logic cores are excluded even when unaudited and even with real TVL. A target must carry a substantial custom layer (custom accounting, ledger/ve/governance, non-standard AMM or hook machinery) — that is the single best predictor of finding quality (up v3's custom ve layer produced the proven M-01; Fables' small clean hook core produced config notes). Estimate own-logic complexity before committing the deep audit.
3. RECENCY WINDOW widened: pull listings up to 90 days old (was 45-60d); keep "recently deployed / significantly upgraded" +10 in the rubric.
4. SCOPE LABELING — CRIT/HIGH/MEDIUM findings = contract-code defects. External-trust items (issuer token powers), centralization/config-vs-code-comment mismatches, and off-chain economics go into a clearly-labeled separate section: reportable to the team, never counted or sold as code exploits. A clean core + config-only outcome is a legitimate Phase 14 close ("target not worth further contract research"), reported honestly — never padded to look like an exploit.
5. SPEED TO DISCLOSURE — pre-launch / pre-TGE timing is a first-class selection factor (immutable code + launch deadlines make findings time-sensitive). After Phase 11 adversarial review passes, notify the team as soon as possible; do not sit on verified findings.

## Revision R2 (user-directed 2026-09-10, after the Fables/audit2 "config-only" outcome)
R1 widened *what counts as readable code*; R2 changes *what we optimize for*. User's words: "the main goal is to audit and find bugs that lead to loss of funds, so our primary target now should be HIGH or CRITICAL", and "smaller protocols ... find more protocols that are small", "ensure that their smart contract is written in Solidity" (Foundry-only host). His read on why the up v3 team went quiet: we did not show a fund-loss bug.
1. OUTPUT FILTER — only High/Critical *loss-of-funds* candidate classes are worth selection now: liquidation/margin/bad-debt math, share<->asset & ERC4626 accounting, debt/CDP collateral accounting, custom AMM/curve math against a real reserve, oracle-priced value, cross-contract accounting ledgers, reward/emission payouts, withdrawal/cooldown queues. Config/centralization/trust items are never the goal.
2. SIZE INVERSION — bias to SMALL protocols (~$0.5M-$30M EVM TVL), where audits and reviewers have not been. >$60M is de-prioritized (crowded, usually audited). Small is not "less vulnerable" — it is *less scrutinized*, which is the actual edge.
3. AUDIT-GAP WEIGHTING — "no known audit" is now the single biggest scoring term (+20); an audit of an OLDER revision or narrower scope than deployed is a LEAD (+12), not coverage; broad recent tier-1 coverage is a heavy negative (-25).
4. SOLIDITY + EVM GATE — target must be Solidity on an EVM chain forkable locally with Foundry. Non-EVM (Solana/Stellar/Canton/Move/BTC-native), off-chain engines and chain-native/precompile system contracts are out.
5. FULL-VERIFIED-SOURCE GATE IS HARD — every fund-facing contract (incl. proxy implementations, routers, vaults, queues) must have readable verified source; unverified fund custody = instant REJECT (this is what killed FermiSwap and Metric in the R2 pass, and Arcus in R1).
6. FRONT-END/CURATOR REJECT — a protocol whose fund-holding code is someone else's shared audited implementation (Morpho Blue curators, Lagoon ERC-7540 curators, Aave/Uniswap front-ends) has no own attack surface: REJECT early. Cheap detector: read DeFiLlama's TVL adapter source (see playbook).
7. UNSUPPORTED-CHAIN AWKWARDNESS IS A COST, NOT A DISQUALIFIER — but "exotic chain with no reachable verified source" is a REJECT on G2, recorded as such.
Full rubric (point values) written up in Desktop/audit3/recon/R2_RUBRIC.md and implemented in Desktop/audit3/recon/score_r2.py.

## Scoring rubric (exact points)
- RECENCY: recently launched +10; recently deployed/significantly upgraded +10.
- CAPITAL AT RISK: $500k-5m +8; $5m-50m +12; >$50m +5 (TVL is not auto-positive — impact indicator only).
- CODE & DEV: active GitHub +10; recent contract changes +10; verified public source +5; meaningful tests +3.
- SECURITY MATURITY: no known audit +15; one weak/old audit +10; multiple strong recent audits -10; large mature security team -10.
- ECONOMIC COMPLEXITY: complex financial logic +10; oracle dependency +5; upgradeable +5; cross-contract +5; external integrations +5; complex accounting +8; liquidation mechanism +7; flash-loan-sensitive +5.
- REAL ACTIVITY: real users +5; meaningful volume +5; growing TVL +5.
- FUNDING: recently funded +8.
- PROJECT QUALITY: good docs +2; poor/incomplete docs +3 ONLY when it hints at undocumented assumptions with security-relevant ambiguity.

## Phase 6+ — Deep audit (EXECUTED 2026-09 on up v3: Phases 6-9 done, hunting in progress)
Execution notes, architecture semantics, invariant sets and the poke/reset lead class: see references/ve33-audit-notes.md.
- Phase 6 deep recon: docs/GitHub/contracts/deployments/verified source/deploy+upgrade history/audits/issues/disclosures/architecture/admin roles/governance/timelocks/oracles/tokens/integrations. Map: USER → ENTRY POINT → CORE CONTRACT → STATE CHANGES → EXTERNAL CALLS → ASSET MOVEMENT → FINAL RECIPIENT. Find every funds entry/exit.
- Phase 7 threat model: unprivileged external, flash-loan-funded, malicious user, malicious token, MEV, oracle manipulator, cross-protocol. No admin-power assumptions unless the vuln IS privilege escalation.
- Phase 8 invariants: what must ALWAYS hold for assets/shares/debt/collateral/reserves/fees/exchange rates/positions/liquidations/balances — then try to violate.
- Phase 9 vuln classes checklist: access control (init takeover, upgrade auth), reentrancy (direct/cross-function/read-only/callback), oracles (manipulation, spot, staleness, decimals/scaling, fallback), accounting (share inflation, donation, double-count, rounding, decimals, fee math), lending, vaults/ERC4626, DEX, derivatives, signatures (replay/nonces/domain/chainid/permit), upgradeability (storage collisions, dangerous paths), token assumptions (FoT, rebase, hooks, pausable), economic attacks.
- Phase 10 tooling: Foundry/forge/cast, Slither, Aderyn, Echidna, fuzz + invariant tests, local forks. Static analysis is NOT proof. Serious findings get a reproducible local PoC: preconditions, attacker capital, liquidity needed, state changes, protocol loss, attacker gain, repeatability. Never destructive interaction with real funds.
- Phase 11 adversarial review: for EVERY candidate vuln try to disprove it (reachability, other validations, state achievability, other contracts, intended behavior, known issue, deployed impl, privilege needs, economic impact). Insufficient evidence → UNCONFIRMED. Never upgrade an AI hypothesis to a finding without evidence.
- Phase 12 quality: CRITICAL/HIGH/MEDIUM only (Low/Info only if security-relevant). ONE proven high > twenty speculative findings.
- Phase 13 finding format: Title, Severity, Confidence, Summary, Root Cause, Affected Contract, Affected Function, Attack Preconditions, Attack Path, Technical Explanation, Proof of Concept, Impact, Exploitability, Recommended Fix, Why Existing Protections Do Not Prevent It, Evidence.
- Phase 14 stop conditions: no attack surface / extremely mature / inaccessible source / insufficient info / nothing after thorough analysis → say "TARGET NOT WORTH FURTHER RESEARCH" and why. On a potentially serious finding → stop expanding scope; switch to verification/PoC/adversarial review/evidence/responsible-disclosure prep.

## Core principles (user's, non-negotiable)
- Goal is REAL vulnerabilities that survive scrutiny — not an impressive-looking report. Never fabricate, never exaggerate, never dress code smells as exploits, never assume audits guarantee safety, never assume unaudited = vulnerable.
- Fan out parallel subagents for discovery (one agent per disjoint candidate set), then aggregate and cross-check before producing Top 10 / Top 3. Deep audit waits for target approval.
