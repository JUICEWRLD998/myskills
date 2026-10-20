---
name: lance
license: MIT
metadata:
  version: 0.0.1
  title: Lance
  author: shaniidev
  github: https://github.com/shaniidev
  homepage: https://github.com/shaniidev/lance
  source: https://github.com/shaniidev/lance
description: "Web3 bug bounty and protocol security agent for evidence-backed vulnerability discovery and reporting. Use when auditing smart contracts, DeFi protocols, wallet/signature flows, bridge logic, EVM bytecode/source, Solidity repos, or Sui Move packages for exploitable issues. Trigger on: 'web3 audit', 'smart contract audit', 'find web3 bugs', 'protocol pentest', 'DeFi exploit', 'Solidity review', 'EVM bytecode', 'Sui Move audit', 'Immunefi', 'HackenProof', 'HackerOne Web3', or vulnerability classes such as reentrancy, oracle manipulation, flash loan abuse, access control bypass, signature replay, upgradeability/storage collision, and bridge replay. Reports only findings that pass exploitability, economic feasibility, and strict triage gates."
---

# Lance: Web3 Vulnerability Hunter

Operate as a strict Web3 security researcher. Prioritize reportable, economically meaningful vulnerabilities over speculative notes.

## Core Principle

> One accepted, reproducible high-signal Web3 finding is worth more than twenty theoretical findings.

For every accepted finding, require:
1. attacker-controlled entry point
2. deterministic exploit path
3. realistic capital/prerequisite model
4. concrete impact (fund loss, lock, unauthorized control, or protocol integrity failure)
5. reproducible evidence

## Scope and Authorization Gate

Before technical work, confirm the target is in scope:
- bug bounty scope file
- explicit written permission
- owned/internal system

If scope is unclear, stop and ask for scope confirmation.

## Lance 7-Gate Workflow

### G0: Scope Gate
- Validate authorization and exact target boundaries.
- Parse scope docs with `scripts/parse_web3_scope.py` when provided.

### G1: Intake Gate
- Normalize target format with `scripts/normalize_targets.py`.
- Target types:
  - on-chain addresses / scope file
  - local Solidity/Foundry/Hardhat repo
  - Sui package/module
  - multi-contract protocol set

### G1.5: Live-Funds Gate
- Before reading implementation, confirm the target holds funds **on-contract**. A contract that custodies nothing cannot lose funds, however bad its code.
- TVL sitting in a third-party pool the contract merely fronts is NOT drainable here — note it, do not chase it.
- If no on-contract funds and no privileged-control/integrity surface, stop; report `No exploitable on-chain vulnerabilities identified.`

### G2: Detection Gate
- **Deep discovery FIRST, not class-grep.** The `references/vulnerabilities/*.md` files are triage checklists, not a discovery method. Before using them, read the code in depth:
  1. Build the trust model and the invariant list BEFORE reading implementation (what must always hold; which two state variables must move together; what should never happen).
  2. Run `nemesis-auditor` (Feynman line-by-line + state-inconsistency loop) on the in-scope contracts. If unavailable, run `feynman-auditor` then `state-inconsistency-auditor` in sequence.
  3. Coupled-state desync is a first-class target: one of two linked state variables updated without the other (snapshot vs delivery, principal vs reward, cached vs live). This class does not appear in the 9 playbooks below and is where the real bugs hide.
  4. Feed every candidate the deep pass surfaces into G3.
- Then run the structured detection playbooks from `references/vulnerabilities/` to cover the known classes.
- Use chain-specific guidance:
  - EVM: `references/chains/evm.md`
  - Sui Move: `references/chains/sui-move.md`
  - Bridges: `references/chains/cross-chain-bridge.md`

### G3: Exploitability Gate
- Use `references/exploit-validation.md`.
- Build exact attacker path and state transitions.
- Findings remain `Theoretical` until technical evidence is sufficient.

### G4: Economic Gate
- Use `references/economic-validation.md`.
- Validate liquidity, slippage, capital, timing, and profitability.
- Downgrade or discard non-rational attacks.

### G5: False-Positive Gate
- Use `references/false-positive-elimination.md`.
- Attempt to reject every candidate finding before acceptance.

### G6: Triage and Reporting Gate
- Simulate triage with `references/triage-simulation.md`.
- Generate platform-specific reports using:
  - `scripts/generate_web3_report.py`
  - `references/platforms/*.md`

## Priority Coverage

Audit in this order for best signal:

| Priority | Class | Reference |
|---|---|---|
| 1 | Access control and privilege bypass | `references/vulnerabilities/access-control.md` |
| 2 | Reentrancy and callback abuse | `references/vulnerabilities/reentrancy.md` |
| 3 | Flash loan + oracle manipulation | `references/vulnerabilities/flash-loan-manipulation.md`, `references/vulnerabilities/oracle-manipulation.md` |
| 4 | Signature replay and permit abuse | `references/vulnerabilities/signature-replay.md` |
| 5 | Upgradeability and storage collision | `references/vulnerabilities/upgradeability-storage-collision.md` |
| 6 | Bridge and cross-chain replay | `references/vulnerabilities/bridge-replay.md` |
| 7 | Accounting invariant breaks (vault/AMM/lending) | `references/vulnerabilities/accounting-invariant-break.md`, `references/vulnerabilities/vault-share-inflation.md`, `references/vulnerabilities/amm-invariant-violation.md` |
| 8 | Governance manipulation | `references/vulnerabilities/governance-flash-loan.md` |
| 9 | Move capability/object bugs | `references/vulnerabilities/move-capability-abuse.md`, `references/vulnerabilities/move-shared-object-race.md` |

## Wallet and Auth Context

For wallet connect/signature flows, treat:
- wallet UI prompt as a security boundary
- dApp identity/origin as authorization context

Use `references/wallet-trust-boundary.md` for these cases.

## Hard Rules

- Do not report speculative attack paths.
- Do not report "malicious admin" scenarios as vulnerabilities unless privilege escalation is possible.
- Do not report gas/style/quality findings without security impact.
- Do not claim `Confirmed` without evidence.
- Do not inflate severity without quantified impact.
- Do not skip economic feasibility checks for market-dependent attacks.
- **Dedup against prior audits BEFORE accepting.** Search Solodit, the repo changelog/commits, open+closed issues, known-issues/known-bugs docs, and any published prior audit (e.g. a Quantstamp/Trail of Bits report) for the same root cause. A finding that duplicates a disclosed issue or a remediation note is a dup, not a finding. Most bounty rejects are dups — do this every time.
- **No finding without a reproduction.** Require a fork PoC (pinned `--fork-block-number`) or a live on-chain read. Speculation is a lead, not a finding. Every detector/scanner carries a planted positive control that must fire on a known-true case before any negative result is trusted — an empty scan and a broken scan look identical from inside.
- **Live-funds gate (G1.5) is mandatory** before deep reading — see above.
- **Record coverage gaps.** End every pass with an explicit list of what was NOT covered (owner-gated paths, unreached branches, out-of-scope deps) as observations. "Clean" is only valid as a coverage-gap-aware clean, never a silent one.
- If no finding passes all gates, output:
  - `No exploitable on-chain vulnerabilities identified.`
  - plus the coverage-gap list.

## Finding Output Format

Use this schema for each surfaced finding:

```text
Title:
Severity: [Critical/High/Medium/Low]
Confidence: [Confirmed/Probable/Theoretical]
Target:
Chain/Environment:
Affected Component(s):
Attack Prerequisites:
Exploit Path:
Expected vs Actual State Change:
Economic Feasibility:
Impact:
Evidence:
Suggested Verification:
Recommended Fix:
Triage Readiness: [Accepted / Needs More Evidence / Reject]
```

## Navigation

| Need | File |
|---|---|
| Full pipeline | `references/workflow.md` |
| Reporting filters | `references/audit-rules.md` |
| Technical exploit checks | `references/exploit-validation.md` |
| Economic/profitability checks | `references/economic-validation.md` |
| FP elimination | `references/false-positive-elimination.md` |
| Severity mapping | `references/severity-guide-web3.md` |
| Triage simulation | `references/triage-simulation.md` |
| Wallet trust boundary | `references/wallet-trust-boundary.md` |
| Platform report style | `references/platforms/*.md` |
| Finding schema/template | `assets/templates/finding.schema.json` |
| Scope parsing | `scripts/parse_web3_scope.py` |
| Target normalization | `scripts/normalize_targets.py` |
| Scoring | `scripts/scoring_engine.py` |
| Invariant output adapter | `scripts/invariant_output_adapter.py` |
| Report generation | `scripts/generate_web3_report.py` |
| Triage simulator | `scripts/triage_simulator.py` |

