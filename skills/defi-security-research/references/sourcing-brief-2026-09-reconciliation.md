# Sourcing brief 2026-09-24 — reconciled against this campaign's own measurements

**Status: ACTIVE for the doors that are still UN-RUN (§5 D2, D4, D5). §5-D1 IS NOW MEASURED AND DEAD — read its verdict before proposing it again.** Every line marked MEASURED below is a
result this campaign already produced; a door that has a measurement is **not** re-run, and a door that
carries a retraction is **not** re-proposed. This file exists because on 2026-09-24 the user supplied a
10-point hunting-ground brief that is mostly *already doctrine*, partly *already measured false*, and
has three genuinely new doors in it. Sorting those three categories is the work; running the brief end
to end would re-burn budget on doors this campaign already killed.

Read this with `vertical-and-selfhosted-sourcing.md` (still START HERE for the primary sweep) and
`vulnerability-funnel.md` (the measured corpus + the seven address doors).

---

## 0. The brief's ranking metric is correct — adopt it, and name it

> *"You're not looking for the protocol with the most money. You're looking for the largest amount of
> money relative to the amount of security scrutiny."*

That is the metric. Write it down as **SCRUTINY-ADJUSTED VALUE** and use it as the sort key everywhere
a headline TVL currently is:

```
rank  =  external_drainable_value  ÷  scrutiny
scrutiny = (verified-audit coverage of the DEPLOYED version)
         + crowd size (platform program age, contest history, TVL-rank visibility, hours since listing)
         + code-maturity of the base (unmodified-fork base ⇒ near-infinite scrutiny on the base, ~0 on the diff)
```

This is not a new gate — it is the existing one stated as one number. It is exactly what these already
enforce, and the brief's sentence is the plain-language version of the same insight:

- **G8 / G8b / G8c / G8d** — external value, *not* third-party-core value, *not* team-Safe value, *not*
  the protocol's own governance token priced by its own market quote.
- **G10 payoff** — "a contract that can lose $17M and pays $0 scores **worse** than one that can lose
  $500k and pays $100k."
- **G11d crowding** — prior-audit count *verified, never quoted*.
- **own-code-depth** — a thin hook/wrapper core has a ceiling of config notes however unwatched it is.

**Consequence for the brief's Protocol A vs Protocol B example.** The brief says B ($3M TVL, 3 weeks old,
solo dev, no public audit) can beat A ($150M, 5 audits, 3 years). By the *metric* that is right. By our
*gates* it is only right when B also clears G10 (a live program, or a team that answers) and G8 (funds
on-contract in B's own code). Severity-adjusted: **an unwatched protocol with no buyer and no on-contract
funds is a volunteer project** — the measured audit2 profile (one medium DoS failing G6, one latent low,
one informational: all real, all reproduced, worth nothing). Optimise scrutiny-adjusted value, not bug
count.

---

## 1. Verdict table — the brief, point by point

| § | Brief point | Verdict | Basis |
|---|---|---|---|
| 1 | Keep DeFiLlama, use **Recently Listed** as the discovery feed | **PARTIAL** — read `/recent` as a cheap feed; do **not** revert to DeFiLlama-as-primary | §3.1, §3.2 |
| 2 | Hunt NEW deployments (launched/upgraded 1–8 weeks ago) | **PARTIAL** — freshness is a *scrutiny* signal, not a funds signal | §3.3 |
| 3 | Hunt CONTRACT TYPES, not protocols (lending + bridges first) | **ADOPT** — confirmed by our own dollar ladder | §5 D3 |
| 4 | Hunt unverified contracts (decompile → reconstruct → fork PoC) | **ADOPT as a door** — now unblocked tooling-wise | §5 D4 |
| 5 | Follow EXPLOITS backwards (root cause → pattern → GitHub → fresh deployments) | **ADOPT — highest-priority new door**, converges with our highest-yield door | §5 D1 |
| 6 | Use GitHub as the protocol-discovery engine | **ADOPT** — a door we have never run | §5 D2 |
| 7 | Look at audit contests — as intelligence, not as entry | **ADOPT (corpus only)** — as a *channel* it is measured closed | §3.5, §5 D6 |
| 8 | Automated AI triage pipeline, refuse to let it produce generic findings | **ALREADY DOCTRINE** + one real addition | §6 |
| 9 | Investigate RWA / stablecoin / yield / restaking / perps / prediction | **ADOPT** — extends the vertical sweep | §5 D5 |
| 10 | Don't require huge TVL; optimise value ÷ scrutiny | **ADOPT** — it is the metric in §0 | §0 |

---

## 2. Verified external facts (checked 2026-09-24, sources in-line)

Carry these numbers, not the brief's paraphrase of them.

- **Unverified contracts — the headline is real but the sample is 4.** Chainalysis, "The Hidden Code
  Problem" (published ~2026-06-09): *"In the last six months, at least $36.7 million has been stolen
  from protocols whose source code was never publicly verified — meaning attackers had to decompile raw
  bytecode"*, and the report attributes an accelerating role to **AI-assisted exploit development**.
  Independent coverage puts the population at **four exploits since January**. So: a genuine and rising
  surface, **not** a volume channel — 4 incidents is too small an n to calibrate a week around. The
  honest read is "a door worth opening, with an unknown ceiling", which is exactly what D4's
  falsification test is for.
- **Symbiosis BTC bridge, 2026-09-11 — and the number to learn from is not 46.1B.** Two bugs let a
  **330-satoshi ($0.25) deposit mint ~46,100,000,000 unbacked syBTC**; the protocol's own loss estimate
  was **9.97 BTC (~$770k)** and the attacker's *realised* proceeds were **4.39 WBTC (~$336k)** sold on
  Uniswap. **Minted ≠ extractable.** Every cross-chain mint finding must compute the extractable fraction
  and the exit liquidity before the impact sentence is written (G1/G6) — a number like 46.1B in a report
  is a credibility loss, not a severity gain.
- **Notional Finance, 2026-09-03/04 — the month's biggest lending loss was an arithmetic cast.** ~$1.73M
  in DAI+USDC left the V1 Escrow contract in a **single transaction**; root cause an **unchecked uint128
  downcast** in the free-collateral check (taking `abs(debt)` and casting, so a fabricated 2^128-scale
  debt read as **zero** and the whole solvency check was bypassed). **No flash loan, no oracle
  manipulation.** This is the strongest available argument that L3 (rounding/precision/decimals) is not
  a low-severity lens, and it belongs next to Maakai's ROUNDING-ISSUES heuristics as a worked case.
- **Extra Finance (Immunefi program page) — read this as a dedup lesson, not a hint sheet.** Its
  documented known issues include *"Debt Repayment Failure Due to Rounding Errors. Accumulated rounding
  differences between pool-level and individual position debt calculations can cause
  `reserve.totalBorrows` to fall below `debtPosition.borrowed`. This can prevent full repayment of the
  affected position."* (entry dated **15 September**). Two readings: (a) it is a textbook specimen of the
  **pool-aggregate vs per-position accounting split** — file it in the heuristic bank; (b) it is
  *published as a programme known issue*, so on **that** program the class is a **G11b zero**. Study it
  here, never file it there. The brief cites this page as a target hint; it is the opposite.

---

## 3. Where the brief collides with our own measurements — do not revert

**3.1 DeFiLlama-as-primary was superseded for a measured reason (2026-09-16).** The seven-address-door
funnel started *and ended* on `api.llama.fi/protocols`: 8,256 protocols → 152 fresh+small → 1,267
addresses → 1,161 on-chain probes → 36 holding ≥$10k → **0 findings**. Anything with meaningful TVL has
already been looked at, and a funded contract that is *not* on a leaderboard is invisible to that
funnel. Model **ATTENTION** as a first-class variable; it is manufactured by new code, unlisted code,
forked code and new chains — none of which the ranked list can give you. `/recent` is worth *reading*
(cheap, human-curated-ish, and it is a *feed* not a filter) — it is not worth reverting the primary
strategy to.

**3.2 `listedAt` is not a usable time field — print its DISTINCT count before any filter on it.**
MEASURED: all 6,580 rows carrying the field held the same three day-values (20691–20693 = the
1970-01-01 epoch sentinel), so a "≤180d fresh" filter was 152 rows **selected on a constant** and the
campaign's premise that it had found *fresh* protocols was never true. A filter built on a constant is
not a filter. If `/recent` is to be a feed, read its rendered rows; do not re-derive "newness" from
`listedAt`.

**3.3 "New deployment + real money" is the exception, not the rule — the firehose is empty BY
CONSTRUCTION.** MEASURED (2026-09-16, retracting the day-before recommendation to lead with it): 4,500
newly-verified contracts across 3 chains → 36 of 220 funded (16%) → **zero** after removing third-party
custodians; a 30-per-bucket experiment gave **0/60 funded across every verification-age bucket**; and
the API pages head-only, reaching **2.1 days of depth**. Mechanism: **newly verified = freshly deployed
= empty**, because money arrives months after deployment. The leftovers were generic Uniswap V2 pairs at
$6–84k. Keep freshness as a *scrutiny* discount and a *fork-discovery* input; never as a funds source.

**3.4 Contests are a measured-closed CHANNEL (2026-09-15).** Sherlock returned **0 live contests** (last
ended 2026-07-27); Code4rena and Immunefi serve HTTP 200 but render client-side, so open-program state
is **not confirmable from a fetched page** — never assert "platform has nothing open" from a `curl`.
Contests are a bonus door; never schedule a week around one. (As a *corpus*, see D6.)

**3.5 The brief's bridge question list is CONFIRMED by our own dollar ladder — bridges/Go too low in
your intuition, not too high.** MEASURED over 708 Solidity+DeFi incidents / $5.44B, by *average payout*:
**cross-chain message spoofing $99.0M/3** is the single highest dollars-per-incident shape in the
corpus, ahead of flashloan governance ($90.7M/2). By *frequency × total* it is access control
($1.09B/149) and oracle ($633M/87). So the brief's instinct to put bridges high is right for the right
reason, and the correct framing is: bridges are where a *small number of enormous* outcomes live.

---

## 4. Doctrine defects this reconciliation exposed — fix or flag, never paper over

These were found by cross-reading doctrine while writing this file. Both are real; the first is open.

**(a) The donation-attack ranking is internally contradictory — RESOLVE WITH PRIMARY DATA.**
`SKILL.md` line ~117 says donation attack *"is the highest dollars-per-incident shape at ~$26.6M (14
incidents)"*. Line ~125 lists the same family as *"donation/skim **$26.6M/14**"* — i.e. $26.6M is a
**total over 14 incidents (≈$1.9M each)**, which is *not* the highest per-incident figure, since
cross-chain message spoofing is $99.0M/3 (≈$33M each) and flashloan governance $90.7M/2 (≈$45M each).
The two lines cannot both be right; the "$26.6M/14" phrasing on line ~125 is consistent with the
corpus and the "highest dollars-per-incident" claim on line ~117 is not. **Do not decide this by
picking the nicer number** — `curl` the `/hacks` corpus, re-derive both columns (total and per-incident)
for every family, and write the winner with its arithmetic shown. Until then, treat "donation is the
highest dollars-per-incident" as **UNVERIFIED**.

**(b) The Python outage is over — `python` EXECUTES as of 2026-09-24.** MEASURED this session by
RUNNING it: `python -c "print('python OK', 2**10)"` → `python OK 1024`, exit 0; `python --version` →
`Python 3.11.16`. `python3` is still the WindowsApps Store alias and `py` still points at a missing
`Python313`, so use the literal name `python` and **keep testing tools by running them** (`command -v`
lies here — it printed a path for a `python` that did not execute). **`pip` is still missing but `uv`
0.12.7 IS present** → `uv pip install` / `uv run`. `node` v24.14.1 and `$HOME/.foundry/bin`
(`forge`/`cast`/`anvil`/`chisel`/`solar`) are present; **`medusa` and `echidna` are still MISSING**, so
`fizz`'s Step 1 remains a hard halt; **no Solidity decompiler is installed** (`heimdall` absent) — which
is the one blocker on D4.

---

## 5. New doors — the actual work

Each door: why we believe it, the **cheap falsification that kills it on the spec** (our rule: kill a
door on its measured ceiling rather than executing it and post-morteming the result), and the first move.

### D1 — EXPLOIT-BACKWARDS *pattern* hunting  ← **RUN 2026-09-24: KILLED AS A DISCOVERY DOOR.** Keep the corpus as a pattern source only; the measured verdict is at the end of this section. Do not re-propose it.
**What.** Don't hunt bugs from code outward; hunt *repeated mistakes*. Recent exploit → root cause →
the **design pattern** that made it possible → find every other implementation of that pattern → filter
to recently-deployed ones → check which hold funds → read only those.

**Why we believe it.** It converges with the door we have already measured as **highest-yield**:
fork-hunting. MEASURED 2026-09-15 — two forks found in one run (Basalt → unmodified GMX V2 Synthetics;
SwingHook `BrokerV2` → dYdX Solo Broker at 0.5.12); and the doctrine line is *"the base is maximally
crowded, the **diff is unread**"*. Fork-hunting takes the **base** as the pattern; exploit-backwards
takes a **recent root cause** as the pattern. Same insight, second pattern source — and the second
source is fresher, which is a scrutiny discount by construction.

**Falsification (run before a campaign, cheap).** Take the 3 most recent root causes with a clean public
post-mortem (start: Notional uint128 downcast 2026-09-04; Symbiosis dual-bug BTC mint 2026-09-11; one
oracle/access-control case). For each, express the pattern as a *code signature*, count its hits in
GitHub code search (D2), and fund-check the top 10 hits. **If 0 of 30 hits hold external drainable value,
the door is dead — record the number and stop.**

**First move.** Build a `recent-exploits.md` corpus: date, protocol, chain, root cause in one sentence,
the **code signature** (the grep/code-search query that finds it), the affected-value number, the
realised number. Notional's signature is concrete and searchable today: a signed→unsigned or wide→narrow
cast (`uint128(`, `int128(`, `uint96(`, `int256(`) applied to a balance/debt before a solvency or
collateral comparison, with no bound check on the input.

**MEASURED 2026-09-24 — THE DOOR IS KILLED, AND NOT FOR THE EXPECTED REASON. Record it; never re-propose it.**
The falsification above was run and came back negative:

- **The signature is not searchable at all.** Notional's `uint128(balance.abs())` returns **0 Solidity
  hits**; the 48 regex hits are all C/C++ (e.g. `TemporalRoundingMode.h`). The shape occurs **once in the
  world, in a private deployment**, so "find every other implementation of this pattern" has no population
  to find. That is the door's general failure mode: a root cause is only a *pattern* if the mechanism is
  idiomatic enough to recur, and the high-profile 2026 losses are dominated by **one-off logic errors**,
  not repeated idioms.
- **The corpus was still worth building — keep it as a hypothesis source.** 14 incidents from 2026 with
  signatures **S1-S10** are at `Desktop/audit3/data/recent-exploits.md`: date, protocol, chain, value at
  risk, value **realised**, root cause, the searchable signature, the post-mortem URL, and whether the
  class clears the **G6** unprivileged bar — **12 of 14 do**; **KelpDAO is CONDITIONAL** (a deploy-time DVN
  configuration, not a code defect). Use it to generate hypotheses about a chosen target, never to find
  targets.
- **Rate calibration, with its own caveat** (`Desktop/audit3/data/exploit-rate-check.md`):
  `GET api.llama.fi/hacks` -> **1,284 rows**; filter `year == 2026` -> **277 rows /
  $1,840,310,747.17** (8 null amounts deliberately left unimputed; raw slice kept as
  `data/llama_2026_rows.tsv`). **The series is NON-MONOTONIC** (2025 = 148 rows < 2024 = 217), so any
  "2.6x jump this year" reading is an **upper bound, not doctrine** — same discipline as every other
  number in this campaign.
- **DeFiLlama's `classification` field is unusable for root cause** — wrong **twice in one pass**
  (`dTRINITY`, `Tectonic`) against the published post-mortems. Use that corpus for **counting** incidents,
  never for classifying them.
- **Where sources disagree, keep both and resolve neither by preference:** Tectonic is **$124.47M** on
  DeFiLlama against ~$75M controlled / $119.5M withdrawn / **~$6M realised** in the post-mortem coverage.
  A nominal or minted figure must never be written as a loss.

**What D1 actually teaches, for the next door of this shape.** The convergence argument in "Why we believe
it" was right about *mechanism* and wrong about *scale*: fork-diffing works because a base is a real
population with a real diff, whereas exploit-backwards needs a **recurring idiom**. So before spending on
any signature, count its population first — **a pattern with a single known instance is not a pattern.**

### D2 — GitHub CODE-SEARCH as a discovery engine
**What.** Search the *code*, not the protocol list, for the shapes that concentrate severity; then map
each hit to a deployment and a funds check. The brief's query set is a good seed —
`"deposit" "withdraw" "liquidate" Solidity`, `"vault" "oracle" "upgradeable"`, `"crosschain" "mint"`,
`"delegatecall" "upgradeTo"`, `"ERC4626" "oracle"` — plus ours: the **cast-before-comparison** signature
from D1, `unchecked` blocks, and the sibling-asymmetry family.

**Filters (from the brief, all usable):** recent commits, few contributors, new contracts, no audit
folder, evidence of a mainnet deployment, a real user base, complex financial logic.

**Constraint — budget it or it burns like Door 2 did.** The unauthenticated **GitHub API is 60 req/hr
per IP and all parallel children share that IP** (MEASURED: it hit `403 remaining: 0`). So: use the
**HTML search UI via `curl`** with a desktop UA, or `grep.app` / Sourcegraph / `codeload` tarballs, and
give any child a hard API cap. Code search is the one place the HTML route is *worse* than the API —
which is the reason this door is normally run with a token or not at all. Decide that up front.

**Falsification.** Pick one query, run it, take the top 20 repos, apply the brief's own filters, and
fund-check what survives. If the filter chain yields <3 funded own-code protocols, the door costs more
than it returns.

### D3 — CONTRACT-CLASS-FIRST hunting (lending + bridges)
**What.** Stop asking "which protocol", ask **"which class of contract is disproportionately capable of
losing money"**, and run that class's question list as the entry point. The brief's lists are good; here
they are mapped to our existing lenses so they are *executed*, not admired:

| Brief question | Our lens | Note |
|---|---|---|
| share-price manipulation, first-depositor, donation | L1 / L3 | **donation/skim** is a named class in the corpus; MEASURED high total ($26.6M/14) |
| bad debt accounting, interest-index errors, catch-up | L1 | the 8-point vault gauntlet in the engine |
| liquidation calculations, liquidation incentive, small positions | L2 | Maakai's LIQUIDATION-ISSUES tree is now the heuristic bank here |
| collateral valuation, stale oracle handling | L5 / oracle | oracle is $633M/87 — 2nd by total |
| debt/share rounding, decimals, casts | **L3** | Notional 2026-09-04 is the proof this lens has teeth |
| isolation-mode mistakes, borrow caps, role self-grant | L6 | access control is $1.09B/149 — **#1 by both count and dollars** |
| **bridges:** who can mint / who can release / who validates | L6 + cross-chain | cross-chain message spoofing $99.0M/3 — highest per-incident |
| **bridges:** replay, signature reuse, nonce/order bypass, double representation | signature-verification class | $12.1M/7; and Symbiosis 2026-09-11 was **two** bugs, not one |

**First move.** Fold the class→lens table into target *scoring*: a candidate that can host L1+L3+L6
(a real accrual engine **and** conversion math **and** privileged paths) outranks a bigger-VL candidate
that can host none. This is the quantitative form of the own-code-depth gate.

### D4 — UNVERIFIED-CONTRACT PIPELINE (now unblocked)
**What.** `unverified + meaningful funds ≠ skip`. Find deployment → identify contracts holding funds →
confirm no verified source → **decompile** → reconstruct architecture → find privileged ops → build a
local fork → prove locally → disclose.

**Status.** Legitimate and interesting (Chainalysis: ≥$36.7M / 4 exploits, AI-assisted decompilation
rising). **Blocker: no decompiler is installed** (`heimdall` absent; `panoramix` is a Python package).
`python` now runs and `uv` is present, so **`uv pip install panoramix` is the first move** — note it
handles only Solidity ≤0.6-era bytecode patterns well; for modern bytecode prefer **`heimdall-rs`**
(install from its release binary; it also does `heimdall decompile --include-solidity`). `cast` cannot
decompile.

**Approval discipline.** Reading mainnet bytecode and building a **local fork** is authorized research;
a mainnet drain is a crime and is never the plan (standing rule: non-response ladder, PoC green ⇒ report
in 24h ⇒ nudges ⇒ publish the advisory). `defaultProhibitedActivities` bans live testing market-wide;
fork-only is not merely safer, it is the contract.

**Falsification.** Take the top 10 unverified contracts holding ≥$100k own-code funds, decompile all 10,
and count how many yield a *reconstructible* privileged money-mover. If the reconstruction rate is
near-zero, the door is a research project, not a campaign.

### D5 — The verticals the brief adds
**What.** The existing sweep covers SoFi, Insurance, NFT Lending, Options Vault, Token Locker,
gambling/prediction. The brief adds **RWA vaults, stablecoins, yield aggregators, points→token, restaking,
liquid staking, leveraged vaults, perps, cross-chain yield, institutional DeFi** — with the sharpest
sub-signal being *"recently introduced a new asset + oracle + vault + withdrawal mechanism"* (four
mechanisms at once = four seams, and seam bugs are what our gap passes hunt).

**Why we believe it.** Money is substantial while codebases are younger than the blue-chip primitives,
and the **RWA/NAV** vertical has its own domain maths that generic lenses miss: NAV staleness and
update authority, redemption gating/queues, attestation and custody assumptions, allow-listed
counterparties, and the *"is the asset real"* trust break. That is the same treatment
`gambling-vertical-bug-classes.md` got.

**First move.** Add **RWA / stablecoin-NAV** as a vertical with its own bug-class file before running it;
do not run it on L1–L7 alone, or it will return generic findings (the measured failure mode).

### D6 — Audit and contest reports as a LEARNING CORPUS
**What the brief gets right.** Even without entering, the published findings of contests and private
audits teach: recurring classes, where auditors *missed*, which functions repeatedly break, what new
architectures look like. **What to change:** this is an *input to the heuristic bank*, not a channel.
MEASURED: as a channel, contests are closed (§3.4). The best evidence that the corpus route works is the
artifact this session imported — a researcher's hand-accumulated bug library, organised as
`writeup.md` + `Heuristics.md` pairs (see `defi-audit-engine` → the losing/lending heuristic bank).
Accumulate the same way: every confirmed finding we produce, and every public post-mortem we read, gets
one generalised rule appended.

**Falsification-free, but timebox it.** Reading is cheap; make it a fixed budget (e.g. one post-mortem
per confirmed finding), never a substitute for a pass.

---

## 6. The AI-triage funnel (brief §8) — mostly already doctrine, one real addition

The brief's 14 steps map almost exactly onto what `spec.json` already carries, so the honest answer is
"we have this, run it in this order":

| Brief step | Where it already lives |
|---|---|
| 1–2 find deployments / identify contracts | Phase 0 recon → `target.contracts[]` |
| 3 map relationships | Phase 0 contract-graph walk (`target-recon-playbook.md`) |
| 4–6 external/public, privileged, money-moving fns | `main_functions[]`, `value_movers[]` (with `bounded_by`), L6 |
| 7 oracle dependencies | `integrations[]` + TMAAR trust levels |
| 8 upgrade mechanisms | G9 proxy-impl slot read; `proxy_kind` |
| 9 accounting variables | L1 accrual gauntlet |
| 10 token/share conversion formulas | L3 |
| 11 generate hypotheses | `never_should_happen[]` |
| 12 reject hypotheses with no economic impact | **G1 + G6** |
| 13 Foundry PoCs for survivors | the fork-attack gate |
| 14 rank only by concrete exploitability | the five-gate triage + the ranked report |

**The addition worth taking: make the REJECT step counted and auditable.** Today kills are recorded per
candidate, but the funnel's *shape* is invisible — which is how "500 generic possible vulnerabilities"
gets produced by pipelines that look like ours. So: keep a **hypotheses ledger** per target —
`hypothesis → gate that killed it → one-line reason` — and enforce the output contract:

> **N hypotheses raised → M survived G1/G6 → K reached a PoC → the report contains exactly K.**
> Anything less than K is a kill with a reason, not a section.

This is also the honest defense against the brief's own warning ("that's AI slop"): slop is *prose that
never entered the ledger*. A finding with no gate row and no reproduction is not a finding.

---

## 7. Seven days, in gate order

1. **Day 0 (spec, no code):** run §5-D1 and §5-D2 falsifications. Both are cheap and both can kill a
   door before it costs a pass. Record the numbers either way — a killed door with a measured ceiling is
   an asset (it stops the next session re-proposing it).
2. **Day 0, same session:** install the decompiler (`uv pip install panoramix`, or the `heimdall-rs`
   release binary) and re-validate that `python` still executes — the whole `scripts/*.py` surface and
   D4 depend on it.
3. **Days 1–2:** build `recent-exploits.md` (D1) with code signatures; add the **RWA/NAV** vertical file
   (D5) before touching that vertical.
4. **Days 3–5:** run the primary sweep (verticals + self-hosted programs) with §0 as the sort key, and
   the D1/D2 pattern searches as a **parallel refill**, not as the main line.
5. **Days 6–7:** for anything that survived, the engine's loop applies — spec → passes → fork gate →
   five gates → PoC ⇒ report within 24h. Remember the entry bar did not move: **G10 (a buyer) and G11
   (may I enter, is it taken) run before any code is read.**

**One sentence to carry forward:** the brief is a good statement of *what* to hunt; the value of this
file is that it stops us re-running three doors that already have measurements against them, and points
the new effort at the doors that do not — **GitHub code search (D2), the unverified/decompile door (D4),
and the RWA/NAV vertical (D5)**. (D1 was measured on 2026-09-24 and killed; see §5-D1.)
