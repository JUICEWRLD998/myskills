# Paying-program channels — invert the funnel (2026-09-16)

> ## ⛔ SUPERSEDED AND WITHDRAWN — DO NOT ADOPT THIS AS THE STRATEGY
> **The user withdrew Immunefi and HackenProof as the discovery channel on 2026-09-16** — for
> duplicate risk, and for being someone else's queue. The channel that replaced it is
> **`vertical-and-selfhosted-sourcing.md`** (same date). `STRATEGY_v5.md` §4 stated that the platform
> route *"is not re-proposed here."*
>
> **This banner exists because the file does not carry it, and that cost a full session on 2026-09-21:**
> a strategy pass read this file, took its thesis as current, and re-proposed the whole withdrawn
> Immunefi plan — even though the withdrawal was already recorded one line away in `SKILL.md`'s index.
> **A reference file gets read without its index. A superseded file must say so in its own first line,
> or it will be mistaken for the live position.**
>
> **Keep for the facts only** (and they are still good): the machine-readable program door
> `scripts/immunefi_targets.mjs` (useful for reading *one* program's scope + reward table), the
> per-program `isPayToSubmit` fee data, the duplicate economics in §2.3, the per-asset `addedAt`
> reasoning, and the RSC-payload extraction technique.
>
> **Do not re-propose the channel.** If it is ever reconsidered, that is the user's call.

**Why this file exists.** The audit2 campaign ran three weeks, read real protocol code, produced
reproduced findings across three targets — and earned **$0** and **zero feedback**. The post-mortem in
`HUNT_LOG.md` blamed the doors, the tooling, and the pass shape. All of those were contributing, but
none of them was the cause. The cause is at the END of the funnel, not the start:

> **Every target was selected from a TVL sweep of protocols that have no bounty program.**
> A perfect critical on `turbo-loop` pays nothing. There is no one at the other end to pay it or to
> reply. "No positive feedback" is not a signal that the findings were weak — it is the predictable
> result of hunting protocols that never had a buyer.

The v3 strategy's own disclosure plan is the tell: *"report → nudge → written deadline → published
advisory, never a drain."* That is the **volunteer-disclosure** playbook. It is the correct playbook
when you have deliberately chosen a target with no program. It is not a monetisation strategy.

---

## 1. The inversion

```
OLD (audit2, 3 weeks, $0):
  sweep DeFiLlama by TVL  ->  filter "small + unaudited"  ->  audit  ->  hope someone pays

NEW:
  sweep platforms that PAY  ->  gate on funds-in-scope + scope freshness  ->  audit  ->  submit  ->  paid
```

The population to sample from is **not** "protocols on DeFiLlama." It is "protocols with a live bounty
program or competition." Those are pre-qualified for payment, they publish a scope, and — critically —
they *want* to receive your report. Discovery gets **easier**, not harder: the platform hands you the
in-scope contracts, the impact taxonomy, and the payout table.

Corollary that matters more than anything else here: **the "less audited = more bugs" thesis optimises
for bug COUNT, not bug VALUE.** A small unaudited protocol has no program, so the bug you find is a
griefing/DoS bug — because there is no money in the contract for a juicy accounting bug to be worth
stealing. The audit2 severity profile is exactly what that funnel predicts: `turbo-loop` F-01
(medium DoS, fails G6), F-02 (latent low), F-03 (informational). **Real, reproduced, worth nothing.**

Audited protocols with programs pay *more*, because the bar becomes "what did the auditors miss" and
the bounty is denominated against real TVL. That is where the money is.

---

## 2. Channel inventory

Verified 2026-09-16 by fetching the pages. **Mark what you verified; do not trust a channel because it
is listed here.**

| Channel | What it is | Entry cost | Verified status |
|---|---|---|---|
| **Immunefi** | **175 programs** | **No submission fee. KYC is per-program** | Page fetched + **parsed** (see §2.1). **108 Solidity/Vyper · 74 no-KYC · 54 Solidity AND no-KYC.** Max bounty **$10M** |
| **HackenProof** | 324 programs + a separate contest tier | Programs: open registration. **Contests: fee + KYC** | Page fetched. Live web3 programs in §4 |
| **Sherlock** | Contests | — | **Client-side rendered — WebFetch cannot read it.** Needs a real browser |
| **Cantina** | Competitions | — | **Client-side rendered.** Site-wide: $65.1M payouts available, $54.1M paid, 22,911 researchers. Competitions tab read as empty at fetch time |
| **Code4rena** | Contests | — | Page 1 fetched: all entries `Completed`; no open contest visible |
| **Bugcrowd / HackerOne** | General + some web3 | Varies | Not fetched. `lance/references/platforms/` has intake guidance for both |

**The three client-side sites are the trap the campaign already documented** (`vulnerability-funnel.md`:
*"could not read Code4rena/Immunefi because they render client-side — do not re-run it and call it
negative"*). Use the headless-Chrome-over-CDP recipe in the global config; a fetch-and-parse pass over
these three is a wasted pass, not a negative result.

### 2.1 Immunefi IS machine-readable — the "client-side" conclusion was wrong for it

The old note lumped Immunefi in with Code4rena and called it unreadable. That is **incorrect**, and it
cost the campaign its best channel. WebFetch genuinely cannot read immunefi.com, but the data is in the
**first HTML response** inside the React Server Components stream:

```
self.__next_f.push([1,"<escaped json>"])   // unescape \n \" / and the payload is plain JSON
```

Each program object carries the schema below. Everything you need for G10 is here:

```json
{
  "slug": "layerzero", "project": "LayerZero",
  "kyc": true,
  "maxBounty": 15000000,
  "launchDate": "2023-05-17T17:00:00.000Z",
  "updatedDate": "2026-07-16T21:53:08.647Z",
  "immunefiStandard": true,
  "tags": { "language": ["Solidity"], "productType": ["Bridge"],
            "projectType": ["Infrastructure"], "ecosystem": ["Arbitrum", "..."] }
}
```

**Door script (built, tested, zero dependencies):**
`scripts/immunefi_targets.mjs` — fetches, unescapes the RSC payload, bracket-matches the `bounties`
array (never regex over JSON), and prints the actionable list.

```bash
node scripts/immunefi_targets.mjs                 # top 45 Solidity + no-KYC targets by max bounty
node scripts/immunefi_targets.mjs --all           # all 175 with kyc/bounty columns
node scripts/immunefi_targets.mjs --fresh 60      # only scopes updated in the last 60 days
node scripts/immunefi_targets.mjs --json out.json # write parsed rows
node scripts/immunefi_targets.mjs --url <program> # dump one program page's text (scope/severities)
```

**Environment note that decides the toolkit:** Python is **broken** on this host — `python`, `python3`
and `py` are WindowsApps store shims that all fail to execute, and there is no `pip`. So `lance`'s
Python scripts and `angus`'s `triage.sh` will not run as shipped. What *does* work: **Node 24**
(built-in `fetch`), **foundry 1.8.1** (`cast`, `anvil`, `forge`, `forge lint`), and
**Slither 0.11.6** as a standalone binary. Build new tooling in Node, not Python.

**`--scope` reads the whole G10 gate off one page.** A program page carries `kyc`, `kycLevel`,
`pausedAt`, `endDate`, `proofOfConceptType`, `rewardsToken`, `attackTimeInterval`,
`programRewards[]` (severity → `maxReward`), `assets[]` (every in-scope contract with its
`addedAt`), and `audits[]`. That is the payment gate, the severity table, and the exact list of
contracts you are permitted to audit — without opening a browser.

> `--fresh` is the single most useful filter for a hunter with no track record: a scope updated in the
> last 30-60 days is newly-added code that the crowd has not yet picked over. Better still is the
> **`addedAt` field per asset** — it tells you *which* contracts in the scope are new, which is a much
> sharper signal than a whole-program update date.

**Three traps hit while building the door (all recorded because they cost time):**

1. **Do not construct a program URL from a guessed slug.** Guessed slugs 404 — Pareto's is `pareto`,
   TermMax's is `termstructurelabs`, Extra Finance's is `extrafinance`. The payload already contains
   `"url":"/bug-bounty/<slug>/information/"` for every program: **read it**.
2. **Never `process.exit()` inside an async fetch path on Windows.** It asserts in libuv
   (`Assertion failed: !(handle->flags & UV_HANDLE_CLOSING), src\win\async.c, line 76`) because a
   socket handle is still closing. Set `process.exitCode` and `return` from `main()` instead.
3. **Bracket-match JSON arrays out of the payload; never regex over it.** The RSC stream is one giant
   escaped string, so a nested `assets:[...]` array needs depth counting with string/escape awareness,
   or the match terminates at the first inner `]`.

**`maxBounty` is the program ceiling, not the per-severity max.** Read `programRewards[]` for what each
severity actually pays, and note the common `rewardModel: "range"` with
`rewardCalculationPercentage: 10` — many programs cap a Critical at **10% of funds at risk**, so the
real payout depends on how much the in-scope contract actually holds. **Check the TVL of the in-scope
assets (G8) before assuming the headline number is reachable.**

---

## 2.2 G11 — VET THE IN-SCOPE ASSETS THEMSELVES (2026-09-16, caught in 2 calls what the scope read got wrong)

**A program page tells you which addresses are in scope. It does NOT tell you whether they are worth
auditing.** Two failure modes, both hit on the same program, both invisible from the scope read alone:

**Failure mode 1 — the in-scope code belongs to a THIRD PARTY.** Pareto Credit's scope looked ideal:
26 assets, all added **the day the board was built**, a repeating 7-family vault structure
(Fasanara / Bastion / FalconX / RockawayX / M1 / TwoPrime), $50k critical, no KYC. Resolving the
EIP-1967 slot (G9) on those "Pareto vaults" returned:

```
0xdd596250f838af8862d30e9c78a143356894a18d  IdleCDOEpochVariant   — Idle Finance's contract
0xf70e982682326ab6641d32058526b1b61aae8754  IdleCDOEpochVariant
0x55573cb84f02cb5dc4dd923bf5cd9c5b4b12a4a7  IdleCreditVault
```

The whole scope is **Pareto-owned proxies over Idle Finance's audited CDO**. Auditing it means auditing
Idle's base, not Pareto's delta. (Secondary signal worth knowing: Fasanara and RockawayX share one impl
while Bastion uses a *different* one — **version drift across families of the same product**, which is
itself a bug-class hunting ground.) This is the G8c trap in a new costume — after "the target is the
team's Gnosis Safe" and "the target is GMX v2, not Basalt", here it is "the target is Idle, not Pareto".

**Failure mode 2 — the in-scope contracts hold nothing.** The same program's vault proxies held
**$0** (dust only: Strategy $100.01, Queue $100.19). With `rewardCalculationPercentage: 10`, a Critical
pays 10% of funds at risk ⇒ **~$0**, and Immunefi triage rejects "theoretical only" impact.

**The gate:**

> **G11 — IN-SCOPE ASSET VETTING. A program's scope read is not a target. Before any pass, for each
> in-scope asset: (a) `cast storage <asset> 0x3608…bbbc` — resolve the impl slot, and if the impl is
> not the protocol's own code, it is a FORK-DELTA target, not a fresh-code target; (b) check what the
> asset actually holds — `balanceOf` for the relevant token — because 10% of $0 is $0; (c) check the
> impl is VERIFIED (Sourcify `exact_match`) or there is no source to audit.**

Two calls per asset. `cast storage` + `balanceOf`. On a 26-asset scope that is a loop, not a project.
Run G11 **after** G10 (the program exists and pays) and **before** G8 (which the board now folds in as
part of the same check).

**Sourcify is the fast verifier** and it also names the contract, which is how the third-party
impersonation was caught:

```bash
curl -s "https://sourcify.dev/server/v2/contract/1/<addr>?fields=compilation,proxyResolution"
# -> {"compilation":{"name":"IdleCDOEpochVariant","fullyQualifiedName":"...IdleCDOEpochVariant.sol:..."},
#     "match":"exact_match","proxyResolution":{"isProxy":false},"verifiedAt":"2026-06-24T13:57:37Z"}
```

When the returned `name` is **not** the protocol you are auditing, **stop and re-read the scope.** The
program may still be worth a pass — as a **delta** against the third party's audited base (D1) — but the
method changes completely, and `defi-audit-engine`'s fork-delta door is the one to run.

---

## 2.3 Duplicate economics — what is verified, and the sharpest mitigation (2026-09-16)

**The concern is legitimate: a duplicate pays nothing.** What is actually knowable:

**Verified from Immunefi's own rules page (`immunefi.com/rules/`, readable via the same RSC trick):**

- Whitehat prohibited behaviour includes *"Submitting duplicates of your original report to the same
  project to claim additional rewards"* — i.e. **re-submitting your own report for a second payout is
  banned.** Submitting to a *different* project is not addressed there.
- Project prohibited behaviour includes *"Claiming a bug report is a known or duplicate issue **without
  clear evidence**"* — **the project must prove the duplicate.** It cannot simply assert it.
- Also: *"Abusing the 'no fix, no pay' rule by stealth fixing the bug later without providing full
  payment to the whitehat"* — a project fixing silently to avoid paying is itself prohibited.
- Mediation exists, and *"negotiations outside of the Immunefi dashboard are considered invalid"*.

**NOT verified — do not assert it:** the exact first-to-report payout rule. The support site
(`immunefisupport.zendesk.com`) serves article HTML but blocks both its sitemap and its search API, so
the specific duplicate-payout article could not be read. **Do not tell the user "first reporter wins"**
as fact — it was not confirmed. Read it from the program page / support article before relying on it.

### The mechanism that makes duplicates cost money — and the programs that don't use it

`isPayToSubmit` and `payToSubmitFeeUsdc` are **per-program**, and they are the concrete duplicate
economics. Measured across the 54 Solidity + no-KYC programs (`--nofee`):

```
FREE to submit (46)   — a duplicate costs TIME only
CHARGES (5)           Sky $50 · GMX $25 · Beanstalk $50 · Alchemix $10 · TermMax $50
```

On a fee-charging program a duplicate is a **cash loss**. On a free program it costs only the hours
spent. **For a hunter with no track record, prefer the 46 free programs** — and note this reversed the
board's own top pick (see below).

### The sharpest duplicate mitigation: pick the NEWEST ASSET, not the newest program

Program age is the wrong signal. The per-asset **`addedAt`** field is the right one, because duplicate
risk attaches to *code*, not to *programs*: an old program that just added contracts this week has
**zero** existing reports on that code, while a young program with a year-old scope may be picked over.

Combine four filters and duplicate pressure drops hard:

| Filter | Why it lowers duplicate risk | Where to read it |
|---|---|---|
| **Asset `addedAt` is recent** | new code ⇒ nobody has reported on it yet | `--scope` output, per asset |
| **Scope is NARROW** | fewer contracts for the same crowd to cover | `assets.length` |
| **Submission is FREE** | a duplicate costs hours, not money | `--nofee` |
| **`high` tier pays real money** | a High is worth submitting even if a Critical is gone | `--scope` reward table |

> **The last row is a trap worth stating plainly: a `high` tier can pay `$0`.** dHEDGE shows
> `critical $50,000 range` and `high $0 fixed` — a High-severity finding there pays **nothing**. Always
> print the reward table; never assume the tiers pay.

**`analytics: "denied"` is returned on program pages, so pick-over level is NOT machine-readable.** You
cannot know how many hunters are on a program. That is a real limitation, not a negative result —
substitute the `addedAt` signal and read the program's disclosed-reports list in the UI.

### The strategic point: duplicate risk tracks how PATTERN-SHAPED the bug is

This is the part that matters more than any filter. **Pattern-shaped bugs get duplicated;
mechanism-shaped bugs do not.**

- A missing modifier, an unguarded function, a plain reentrancy, a `SafeMath`-era overflow — every
  hunter runs the same static analysis and reads the same playbooks, so these collide constantly.
- A protocol-specific accounting break, an invariant violated only across two interacting modules, a
  timer replayed through a state machine — these require having *understood the protocol*, which most
  submissions never do.

**The audit2 findings were the first kind** (a missing `checkMessageNotUsed`), which is a second,
independent reason they were worth nothing: even on a paying program that exact shape is the most
likely thing to be reported by someone else first.

So the duplicate concern and the "we need better findings" concern are **the same problem.** The answer
is not to find a quieter program; it is to find a **mechanism-shaped** bug — and the freshest asset in
the narrowest free scope is where those are still available.

**Practical pre-submission duplicate check, in order:** (1) the program's disclosed-reports list in the
Immunefi UI; (2) Solodit for the same contract/pattern; (3) the protocol's own audit PDFs (in
scope-relevant `audits[]`); (4) the repo's issues/PRs for a hint the team already knows. If a report
already covers your root cause, it is a duplicate regardless of how you phrase it.

---

## 3. Contests vs continuous bounties — for a hunter with no track record, bounties win

The rain-USDR contest is a clean worked example of why.

| | **Contest** (rain-USDR, Sept 2026) | **Continuous bounty** (Immunefi) |
|---|---|---|
| Pool | $14,000 total (Crit $5,600 / High $4,200 / Med $2,100 / Low $700) | ceiling **$15,000,000** (LayerZero); **54** Solidity no-KYC programs to choose from |
| Entry | **$5 per submission, explicitly non-refundable** | **no fee** |
| KYC | **required** | per-program; **74 of 175 need none** |
| Window | 14 Sep – 01 Oct (17 days) | **none** — work for weeks |
| Competition | 49 hackers, 152 submissions | first-to-report wins, but no clock |
| Cost of being wrong | **$5 burned** + public duplicate risk | nothing but time |
| Reputation | none; `Total rewards $0`, no leaderboard gate stated | builds a public track record |

Contests are a **negative-expected-value channel for a beginner**: you pay to submit, you cannot enter
without KYC, you compete against 49+ hunters on a small codebase, and duplicates split the pool. The
rain contest was the right *instinct* (a funded, scoped, Solidity protocol) reached through the wrong
*door*.

**Rule: skip contests until there is a track record. Take continuous bounties.**

---

## 4. Verified live web3 programs (HackenProof, fetched 2026-09-16)

Useful as a worked sample of *what the target profile looks like* — not as a finished list.

| Program | Max | Type | Signal |
|---|---|---|---|
| **Hinkal** | $10,000 | Solidity + ZK circuits, stablecoin | **NEW 03 Sep 2026, `$0 paid`, 71 submissions** — freshest scope, least picked over |
| **Arcadia Finance** | $25,000 | Non-custodial margin protocol, Base/Optimism/Unichain | 126 submissions, only $1,250 paid — hard, and live |
| **Snowbridge** | $75,000 | On-chain bridge code | **$35,100 paid** — pays, and pays well |
| **Starknet** (3 programs) | $250k / $250k / $100k | DLT, web+SC, staking | $11,000 paid; large scope |
| **ADI Predictstreet** | $10,000 | **Prediction market**, Solidity | 38 submissions, $0 paid — the rain-USDR archetype |
| **Cetus** | $300,000 | Smart contracts | $310 paid |
| **Turbos Finance** | $15,000 | Smart contracts | $0 paid |
| **FlowX CLMM** | $5,000 | Smart contracts | $0 paid |

**"$0 paid" is ambiguous and must be read both ways:** it can mean *nobody has cracked it yet* (Hinkal,
fresh — good) or *they do not pay* (a red flag). Distinguish by age and by whether the program is
`LIVE` with recent triage activity. `New + $0 paid + few submissions` is the sweet spot: fresh scope,
little competition, and a team that has not yet been burned into being hostile.

---

## 5. G10 — the gate that was missing (run it FIRST, before G8)

The campaign's gates are G0-G9. All of them test the *target*. None tested whether the target **pays**.

> **G10 — PAYMENT CHANNEL.** Before any code is read: does this protocol have a live bounty program or
> open competition that (a) pays for the severity class you expect to find, (b) is reachable by you
> without KYC you cannot pass or a fee you will not pay, and (c) lists the contract you are about to
> audit **inside** the published scope? **If no, it is not a target — it is a volunteer project.**

G10 runs **before** G8 (live-funds). G8 asks "can this contract lose funds"; G10 asks "will anyone pay
me when it does." A contract that can lose $17M and pays $0 scores worse than one that can lose
$500k and pays $100k.

This single gate would have redirected all three weeks of audit2 work at the start.

---

## 6. Selection criteria for a paying target (merged)

From `angus-bounty-hunter` (target-selection section) plus what the audit2 post-mortem adds:

| Criterion | Threshold | Why |
|---|---|---|
| **Live program exists** | mandatory | G10 |
| **Funds at risk IN SCOPE** | meaningful vs. bounty size | auditing an in-scope contract holding $0 pays $0 |
| **Past payouts** | **> $50k lifetime** | `$0 paid` + old + many submissions ⇒ likely never pays |
| **Scope freshness** | updated **< 30 days** | fresh code = unaudited paths = fewer duplicates |
| **Newly listed** | listing age < 30d | the beginner's edge: everyone is at the same starting line |
| **Source available** | GitHub repo or verified source | you cannot audit what you cannot read |
| **Language** | Solidity (unless the toolchain supports it) | Slither is Solidity-only |
| **Severity class matches your skill** | expect High/Critical, not DoS | a DoS-only bug class on a paid program pays little |

**Prefer: newly-listed + funded + pays-a-lot-elsewhere + Solidity + a repo you can clone.**

---

## 7. Tooling this maps onto

The two newly installed skills are built for exactly this inversion — use them as the spine:

- **`lance`** — the 7-gate workflow (scope → intake → detection → exploitability → economic →
  false-positive → triage/report). Opens with the principle the campaign needs: *"One accepted,
  reproducible high-signal Web3 finding is worth more than twenty theoretical findings."* Ships
  `references/platforms/{immunefi,hackenproof,hackerone-web3,bugcrowd-web3}.md` (per-platform triage
  focus and rejection reasons), 13 vulnerability playbooks, and
  `scripts/{parse_web3_scope,normalize_targets,scoring_engine,triage_simulator,generate_web3_report}.py`.
  Note its priority order differs from the campaign's severity-density order — lance is
  access-control → reentrancy → flashloan/oracle → signature-replay → upgradeability → bridge →
  accounting → governance. Both are defensible; reconcile rather than stacking both.
- **`angus-bounty-hunter`** — the volume play: `scripts/scan.sh <repo>` (Slither) → `triage.sh`
  (HIGH/MEDIUM filter) → `poc-template.sh`. Deep-dive only flagged code. This is how you cover many
  programs without reading every line.
- Not for this: `web-pentest`, `attacker`.

`lance`'s own intake guidance is the disclosure-side match: immunefi triage is *"exploitability and
impact first"*, and its frequent rejection reasons are **theoretical only / impact inflation / no
reproducible sequence / out-of-scope class** — which is precisely the shape the campaign's three
findings would be rejected for, and precisely why a DoS-only bug with no extractor is the wrong
product to be manufacturing.

---

## 8. The legal/scoping line (unchanged)

A payout obliges you to the program's rules: stay in scope, no public disclosure before resolution, and
follow their severity taxonomy rather than your own. `lance`'s G0 scope gate and its
`platforms/*.md` rejection lists are the operative documents. Never test against a contract you have
not confirmed is in scope.
