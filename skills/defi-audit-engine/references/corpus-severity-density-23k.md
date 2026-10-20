# Bug-class severity density — 23,625-finding corpus (measured 2026-09-29)

Source: `Zaevlad/audit-findings-dataset` (Hugging Face, `data/train-00000-of-00001.parquet`, all 23,625 rows
loaded, 10 columns). Public audit-contest findings; severity labels normalised by the dataset author from
inconsistent originals. Analysis script + planted controls: `Desktop/research-system/data/analyze.py`.

**Read this before using it.** (1) The class labels are a *keyword classifier over title+description*, checked
with 5 planted positive controls — it is a coarse lens, not ground truth; `logic-flow` and `unclassified`
(28% of rows) are catch-all buckets and carry no signal. (2) These are *contest* severities. A contest
"High" is not a bounty "Critical", and contest findings are what auditors already found — they say where
bugs cluster, not what is unfound. (3) Baselines: P(High|Critical) = 21.8% overall, P(Critical) = 3.3%.

## P(High or Critical) by class (n >= 100) — the useful table

| Class | n | P(H/C) | P(Crit) | vs baseline (H/C) |
|---|---|---|---|---|
| access-control | 572 | **38.1%** | **9.6%** | 1.75x / 2.9x |
| accounting-desync (not updated / stale index / reward debt / double-count) | 732 | **36.7%** | 6.4% | 1.68x |
| liquidation-debt | 2,073 | 30.4% | 4.5% | 1.39x |
| reentrancy | 821 | 25.5% | 3.4% | 1.17x |
| signature-replay | 692 | 23.3% | 4.2% | 1.07x |
| slippage-mev | 1,032 | 22.9% | 2.3% | 1.05x |
| dos-griefing | 2,315 | 22.8% | 3.9% | 1.04x |
| rounding-precision | 1,156 | 21.5% | 3.5% | 0.98x |
| cross-chain-async | 1,057 | 20.3% | 2.4% | 0.93x |
| oracle-price | 1,210 | 18.7% | 2.7% | 0.86x |
| initialization-upgrade | 1,215 | 17.0% | 3.5% | 0.78x |
| token-integration (fee-on-transfer, weird ERC20) | 1,763 | 15.8% | 1.7% | 0.72x |
| input-validation | 1,637 | 14.4% | 2.7% | 0.67x |

## What it says, and what it does not

- **Two classes carry the severity: access-control and accounting-desync.** This matches the 1,022-finding
  Shieldify table in `defi-security-research/references/severity-density-triage-and-tmaar.md`
  (reward accounting 39%, access control 20% severe) — two independent corpora, same top of the ranking.
  Treat "state variable A updated, coupled variable B not" as the first thing to hunt.
- **CORRECTION to the Shieldify-derived claim "reentrancy = lowest-yield famous class".** That claim rested on
  n = 12 (1 severe). At n = 821 reentrancy is *slightly above* baseline (25.5% vs 21.8%), not the bottom. The
  bottom of the ranking here is input-validation / token-integration / initialization. Reentrancy is still not
  where to spend *first* (it is fully covered by the standard detectors), but "skip it" is not supported.
  Retraction marked in place in the source file.
- **The Critical titles are extractor sentences, not vulnerability names.** Top Critical title bigrams:
  "anyone can" (21), "attacker can" (17), "can steal" (16), "users can" (12), "can drain" (8), "steal all" (8),
  "wrong token" (6), "not updated" (4), "arbitrary calls" (4). A Critical is written as *who can do what to whose
  funds* — the same shape as our G1 sentence. Title yours that way.
- **PoC presence rises with severity but is still a minority: Critical 22.9%, High 36.4%, Medium 29.8%, Low
  5.1%** (a "PoC" = >40 chars and not a placeholder). ~64–77% of contest High/Critical findings carry no
  working reproduction. For a bounty submission where a PoC decides payout, a fork PoC is a real
  differentiator, not table stakes.
- **Exact-title duplicates among High/Critical: 74 of 5,153 (1.4%).** This only measures identical titles, so
  it is a *floor* on duplication; semantic duplication (same root cause, different words) is unmeasured here.
- **Median description length: High 1,129 chars, Medium 938, Critical 884, Low 694.** Critical findings are
  *shorter* than High — obvious-and-devastating bugs need fewer words; subtle ones need explaining. Length is
  a weak proxy for subtlety and is not evidence on its own.

## How to use it in a pass

1. In `spec.json`, order the invariants so every `accounting-desync` and `access-control` candidate is
   examined before any `input-validation` / `token-integration` one.
2. For each state-changing external function, list the *coupled variables* it touches and mark which it
   updates. Any function that updates A but not B is an `accounting-desync` candidate — run G0 on it.
3. Do not read this table as a probability that your target has the bug. It ranks *where to look first*.

## Not inspected

The raw CSV (`raw/bug_list_202608311315.csv`) was not opened; no per-source (Code4rena vs Sherlock vs other)
split is possible because `file_name` is just `<n>.json`. Protocol type per finding is not a column.
