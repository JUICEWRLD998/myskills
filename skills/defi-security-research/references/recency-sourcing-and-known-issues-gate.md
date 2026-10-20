# Recency-first sourcing, and the KNOWN-ISSUES GATE

Measured 2026-09-26 on a full live pass (audit3 → v10). Two things here: (1) a recency-first sweep as an
axis in its own right, with the cohort trap it is uniquely exposed to, and (2) **the gate that should run
before you rank *any* hunt surface** — the target's own prior audit reports.

---

## 1. The recency axis, re-measured (and a stale doctrine line corrected)

`listedAt` was previously recorded as *contextually defect* / "a filter built on a constant is not a
filter". **Re-measured 2026-09-26 against a fresh pull and it carries a real time signal:**

| Field | Measured |
|---|---|
| pull | `api.llama.fi/protocols`, **http 200, 8,962,035 bytes, 2.55 s**, **8,382** protocols |
| `listedAt` present | **6,707 / 8,382** (80%) |
| distinct-value check (the anti-constant test) | **passes** — a real spread, not one sentinel |
| within 30d / 60d / 90d / 120d / 180d / 365d | 257 / 384 / 508 / 577 / **787** / 1,323 |

So: keep running the distinct-count test on every field filter (that rule stands and is cheap), but do not
treat `listedAt` as dead. **Also unchanged: `listedAt` measures the LISTING, not the DEPLOY** — a "fresh"
entry can be a 2020 token (recorded previously). Recency is a scoping axis, never a freshness proof.

**Funnel (recency-first), for calibration:**
```
8,382 all → 6,707 with listedAt → 787 listed <=180d → 107 TVL >=$3M
      → 88 with >=1 EVM chain → 24 in a fund-bearing vertical → 12 not a parentProtocol child
      47 rows if the category filter is dropped (the honest pool to write rejections from)
```

## 2. THE COHORT TRAP — "Risk Curators" is a G8b cohort BY CONSTRUCTION

This is what a recency-first sweep hits hardest, and it killed **20 of 88** rows before a line was read.

The largest category in the recent+funded+EVM set is **`Risk Curators`**: Armitage by Wintermute ($145.0M),
Galaxy Curation ($44.9M), Y10K Capital ($30.2M), Gamma Research ($25.0M), Waterline ($23.9M), Bitwise
($21.9M), Syntetika ($15.7M), Flowdesk ($15.6M), Nemo Trading ($15.2M), Pangolins ($13.8M), Monarq ($12.1M),
Anthias ($10.5M), Dialectic ($9.4M), Keyrock ($8.2M), August Digital ($7.4M), Sharpbyte ($6.6M), Damm ($6.5M),
Presto ($3.3M).

**Why every one is a kill:** a curator's DeFiLlama TVL is capital allocated *into* Morpho/Euler-style vaults.
The money sits in a verbatim upstream's code, so no bug in the curator's own code can move it. Same family as
LOCKON (a fork displayed, the value belongs to the base).

**Rule:** at sector-selection time, drop `Risk Curators` wholesale on a direct-to-team channel; only revisit
if the curator ships its OWN vault contracts holding its OWN money. Recency-first makes this trap *more*
likely to catch you, because curators list young and list big.

## 3. THE KNOWN-ISSUES GATE — run it BEFORE ranking hunt surfaces

**The failure this gate exists to prevent, from this session:** a sourcing pass named its hunt surface as
*"signed-order verification, per-block rate-limit accounting, and the overridden access-control path"*, then
downloaded the two prior audits and found the first two were **already reported** — Sherlock's single High
was on exactly the collateral-routing function, and a Medium was literally titled *"Bypassing TrUSD Rate
Limits via StakedTrUSD"*. Re-reporting either pays **$0**, because "already-known issues" is an explicit
out-of-scope bucket on essentially every bounty.

**Ordering rule: SCOPING PRECEDES HYPOTHESIS RANKING.** Reading the prior reports is the *first* work on a
target that has any, not a mid-audit sanity check. Praising your own hypothesis list before checking the
known set is how a week gets spent on an unclaimable class.

**Recipe (all keyless):**
1. Find the reports from the target's OWN docs — `/security/audits`, `/resources/risks`, often a link table.
2. Fetch them (GitHub raw works for NethermindEth/PublicAuditReports and sherlock-protocol/sherlock-reports).
   Verify a real payload: a 200 with a plausible size (measured: **258,770 B** and **977,048 B**).
3. Extract to text with `uv run --with pymupdf python -c "..."` (pymupdf is NOT preinstalled; `uv` is).
4. **These reports are 2-COLUMN.** Naive line-splitting truncates every title at the column break
   (`"H-1: tra"`, `"Blacklisted users ca"`). Read the **issue table / findings index** in the report's own
   text instead — for Nethermind that is the `6.0.x [Severity] Title` block; for Sherlock the `H-n/M-n/L-n`
   list. Titles that still truncate are transcribed from the table, and say so.
5. If the target is on a platform, the program's scope page is authoritative. On a **direct/disclosed-email
   channel** the reports ARE the definition of "already-known" — no program page exists to fall back on.

**Deliverable:** a `KNOWN_ISSUES.md` in the target dir listing every reported finding, marked unclaimable,
plus an explicit **"what is still open"** section. It is the boundary file the hunt works inside.

**Payoff is real:** with the known set in hand you can (a) avoid the one OOS bucket that silently voids good
work, and (b) spend the freed hours on surfaces neither firm touched. Here the open ground was the
**NAV/oracle valuation path** (the oracle contract was not even in the docs' address table), the EIP-1271
signature branch under upgradeable proxies, and **invariant fuzzing** — neither report described an
Echidna/Medusa run, so that ground was unexploited.

## 4. Recon recipe that worked (keyless, 10/10)

**Verified source, no API key: `https://eth.blockscout.com/api/v2/smart-contracts/<addr>`** — **http 200 on
all 10** addresses pulled, every one `is_verified: true`, full `source_code` + `additional_sources`.

- **Proxy implementations DID resolve from the explorer's own field here.** Both ERC1967 proxies returned
  `implementations[]` naming `TrUSD` and `StakedTrUSD`. This is a genuine data point against the older
  "Blockscout omits `implementations[]` for ERC1967/UUPS" note — but it is **explorer- and contract-dependent,
  so the G9 rule (read the impl slot from CHAIN STATE) remains the fallback, not something to skip.** Presence
  of the field is a convenience; its absence is not evidence, and a proxy whose impl you have not read is an
  audited-nothing target regardless of which method resolved it.
- **Mintlify docs (docs.<protocol>.finance) are JS shells to `curl`.** Get the real text by appending
  **`.md`** to the page path, or read **`/llms.txt`** for the index. Measured: `resources/contracts.md`,
  `security/audits.md`, `security/roles.md` all returned clean markdown; the plain HTML URL returned a
  script blob. **`/sitemap.xml`** enumerates the real page set when guessing paths fails.
- The protocol's own **contract-address table** in those docs is the address map — it named 6 Ethereum
  contracts plus the cross-chain deployments and the CCIP pools (which are third-party ⇒ out of scope).

## 5. Instrument defects logged this pass (all produced a confident wrong answer first)

1. **A `:` delimiter collision silently emptied every probe.** A probe loop written as
   `for rpc in "https://host:NAME"` with `url="${rpc%%:*}"` splits on the **scheme**, not the intended
   separator, so every URL became `https:` and **all 7 chain probes returned empty** — which reads exactly
   like "these chains are unreachable". Only the Ethereum **control** exposed it. Fixed with `|`.
   *This is the fourth "the instrument was wrong" case in this campaign.*
2. **Guessed RPC URLs are not probes.** After the fix: `rpc.risechain.com` → `0x1039` (live), `rpc.monad.xyz`
   → `0x8f` (live), `mainnet.base.org` → `0x2105` (live); guessed Strato/Robinhood/Fluent URLs did **not**
   answer, and `eth.llamarpc.com` returned **525**. Chain reachability is case-by-case, always re-probed.
3. **node's `fetch`/undici cannot reach `raw.githubusercontent.com` on this host while `curl` returns 200.**
   Already on record; re-confirmed. Drive all pulls from the shell.
4. **A bad API slug produces a non-JSON body** (`"Protocol not found"`), which a `.json` parse reports as a
   parse failure rather than a 404. Check for `message` before treating a body as a record — and note one
   inherited slug in the loop had a **non-ASCII character** that silently created a 0-byte file.

**Standing rule, reinforced: every empty result gets a positive control before it is believed.**
