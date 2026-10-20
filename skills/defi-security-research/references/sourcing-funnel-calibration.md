# Sourcing-funnel calibration (measured 2026-09-24)

One full vertical sweep, run end to end as the parent's mechanical work before any subagent was dispatched.
Nothing here is estimated — every number is a result of this pull. Use it to skip the re-derivation and, more
importantly, to avoid two traps that silently produce a confident wrong list.

Source data: `GET https://api.llama.fi/protocols` on 2026-09-24 → **8,352 protocols / 8.9 MB**, saved to
`audit3/data/protocols_raw.json`. Re-pull before trusting any count here; the schema facts hold, the counts move.

---

## 1. THE FILTER CHAIN, with what each stage actually removed

```
8,352  all protocols
 →  448  in our target verticals AND tvl >= $250k          (19 low-coverage verticals, see §3)
 →  206  of those reporting audits == '0'
 →  140  EVM-compatible                                       (66 removed: Solana/TON/Bitcoin/Aptos/Sui/Algorand)
 →  129  after removing tokenised-fund / AUM-shaped listings  (11 removed)
 →   55  seeded to 4 recon batches + the exploit-backwards door
```

**Two of those stages are cheap, purely local, and removed 77 of 206 candidates (37%) before any subagent time
was spent.** Run both before the fan-out — they are the highest-leverage classification steps in the funnel.

### Stage 4 — the NON-EVM filter

Our audit skills are Solidity/EVM-only. A protocol with `chains = ['Solana']` (or TON, Bitcoin, Aptos, Sui,
Algorand, Starknet, Cosmos, Filecoin, XRPL, Hedera…) is **not a candidate**, it is out of scope, and it should be
recorded as such rather than left in the pool where a child will burn a pass discovering it.

Method: `any(c not in NON_EVM for c in chains)` — i.e. keep a protocol that has **at least one** EVM chain,
because a multi-chain protocol is auditable on its EVM deployment. Mind two edge cases: **Tron is EVM-compatible**
(Solidity applies — `JustLend sTRX` is a valid candidate), and a mixed listing like `KAIO` (Sei + Aptos) needs
its TVL decomposed per chain before you know which side the money is on. Measured split of the 206: **140 EVM,
66 non-EVM only**.

### Stage 5 — the TOKENISED-FUND filter, and why it is not optional for RWA

RWA is full of listings whose "TVL" is a **fund's assets under management or a tokenised T-bill balance**, not
value sitting in a contract anybody can drain. `Invesco USTB` ($550M) is a BlackRock-style money-market fund;
`Anemoy Capital`, `DigiFT`, `OpenTrade`, `RealT Tokens`, `Lofty` are the same shape. A pass spent on these
returns "no drainable contract", which is exactly the G8b/G8d family of false positives.

Heuristic applied here (name-based, so it **flags for review rather than deletes**): match the listing against
known tokenised-fund / RWA-issuer names (`Invesco, Anemoy, DigiFT, RealT, Lofty, OpenTrade, OnRe, Sky RWA,
Frax USD, R25, Valos, CIAN, Ethena, Superstate, WisdomTree, Franklin, Hashnote, Securitize, Sygnum`). Measured:
**11 of 140 removed.** The honest limit: a name filter cannot catch a fund with an unfamiliar name, so a
candidate that survives still needs its TVL decomposed by token in recon (G8d) — the filter only removes the
obvious ones cheaply.

---

## 2. FIELD SEMANTICS — the two traps

### 2.1 `audits` is a 2-value STRING FLAG, not a count

Measured value set across the corpus and the detail endpoint: **`'0'` and `'2'` only.** Present on 8,339/8,352
rows. It is a boolean-ish "has some audits recorded" flag.

**The trap that bit this campaign's own enrichment pass:** a field described in earlier doctrine as "a string
count" invites `int()` / `isinstance(x, int)` handling, and a `isinstance(x, int) else 0` conversion **silently
turns `'2'` into 0** — reporting an audited protocol as unaudited, with no error anywhere. If you build a
ranking off that number, the entire top of the list is wrong.

### 2.2 `audits == '0'` at high TVL is usually a DATA GAP, not a signal

Verified false zeros, all reporting `'0'` while holding public audits:

| Protocol | TVL | Reality |
|---|---|---|
| `ether.fi Stake` | $5,188M | multiple public audits |
| `mETH Protocol` | $631M | audited |
| `Coinbase Wrapped Staked ETH` | $512M | audited |
| `Hyperlane` | $86M | audited |
| `Polymarket International` | $337M | audited |

**Consequence for targeting:** `audits == '0'` is only weak evidence of low scrutiny, and it is *weakest exactly
where the TVL is highest* — the opposite of the "small unaudited protocol" thesis it is used to serve. Confirm
audit reality from the protocol's OWN docs/audit page and record firm + date + scope. Expect a large fraction of a
high-TVL zero-audit list to die on **crowding** (G11d) rather than on being unaudited, and say so in the
deliverable instead of implying the list found unwatched code.

### 2.3 `listedAt` — the constant-field defect is CONTEXTUAL; check before assuming either way

Earlier doctrine records a pull where `_ageDays`/`listedAt` carried only three distinct values (the 1970-01-01
epoch sentinel), making any recency filter select on a constant. **That defect was NOT present in this pull:**
6,481 distinct values, range 2021-10-12 → 2026-09-24, zero pre-2020 values. So the rule stands as *"print the
distinct count and the min/max before filtering, then decide"* — not as *"listedAt is broken"*. Assume neither.

---

## 3. VERTICAL COUNTS (in-vertical, tvl ≥ $250k, audits == '0')

Useful because it shows which verticals actually have funded, zero-audit candidates rather than which are
interesting in principle:

```
Liquid Staking   83   $15,915M      Cross Chain Bridge  6    $167M
RWA              39    $3,106M      Options Vault       3     $72M
Farm             17      $614M      Token Locker        7     $48M
Yield Aggregator 16      $447M      NFT Lending         1      $9M
Prediction Mkt   12      $357M      Yield Lottery       1      $5M
Restaking         6    $3,420M      Luck Games          3      $4M
Leveraged Farm    4      $179M      SoFi / Insurance    1+1   $3M
```

The doctrine's chosen low-coverage verticals (SoFi, Insurance, NFT Lending, Options Vault, Token Locker,
gambling) are **thin in this pull** — 1 to 7 funded zero-audit candidates each. The volume sits in Liquid
Staking / RWA / Farm / Yield Aggregator, which is where the specialist-crowd warning applies. Treat the thin
verticals as *low competition*, and the fat ones as *high volume, high scrutiny*, and pick deliberately rather
than by pool size.

---

## 4. FILTER OVERLAP: `audits == '0'` AND the fork thesis DO NOT OVERLAP

Measured: among funded in-vertical protocols, the intersection of `audits == '0'` with `forkedFromIds != []` is
**ZERO**. Running the fork query with the audit filter applied returns nothing.

That is a methodology error, not a finding: **a fork's *base* is audited and maximally crowded while its *diff* is
unread**, so demanding `audits == '0'` excludes precisely the targets the fork thesis exists to find. Run the fork
query over **all funded in-vertical protocols regardless of the audit field** — that surfaced 9 funded EVM forks
(Autofarm, Hop Protocol, Rari Capital, LOCKON, CHATEAU, Kleva Farm, Geode, YFII, Orchai LST).

Generalisable rule: **an aggregator field that is a proxy for scrutiny must not be ANDed with another
scrutiny-based thesis.** Each filter is answering "is this unwatched?"; stacking two of them does not sharpen the
answer, it returns an empty set and looks like a clean negative.

---

## 5. THE SELF-HOSTED PROGRAMME INDEX IS A STUB, NOT A DISCOVERY SOURCE

`raw.githubusercontent.com/solodit/solodit_content/main/bug_bounties/custom.md` measured **1,287 bytes / 9
programmes** (Frax, Uniswap, Aptos, 0x, Convex, Ethereum Foundation, Compound, PoolTogether). Cross-referenced
against 55 candidates it matched **exactly one** (`Frax Ether` → Frax Finance, $10M cap) — and that match is a
false-friend, since "Frax Ether" is Frax's LST, not Frax Finance's core.

So the index is an *extender target*, not a lookup table: it tells you the industry has self-hosted programmes,
not which of your candidates has one. **Channel discovery must be per-protocol and is the first gate run**, since
a candidate with no channel is not a target. Record it as a coverage gap when the index is your only source.

---

## 6. HANDING THE FUNNEL TO THE CATALOGUE — three guards, all found by fixture-testing

`scripts/build_findings_catalogue.py` expects a record shape that a recon brief rarely produces verbatim, so a
thin adapter is the right layer (never a second formatter — the file and the JSONs must not be able to drift).
**A thin adapter is still code that can silently return zero, so test it with planted fixtures for EVERY verdict
path before the real agents land.** Two real bugs surfaced that way in this pass, both invisible in a happy-path run:

1. **A hardcoded glob silently drops an agent's output.** `glob(recon/"B*"/*.json)` matched nothing when the
   fixture directory was named differently — and the failure mode is `adapted 0 protocol records`, which reads as
   "the agents found nothing" rather than "the adapter never looked". Fix: glob **every** subdirectory (excluding
   the output dir) and print the count of paths scanned in the zero case. Same family as the campaign's standing
   rule that an empty scan and a broken scanner are indistinguishable — so make the zero case *say what it scanned*.
2. **A cache file gets ingested as a protocol record.** Agents legitimately drop scratch responses (explorer JSON,
   `api.llama.fi` payloads) inside their batch directory, and those carry a `name` and often a `tvl` — so
   "requires `name` or `slug`" happily admits them and puts a junk row in the user's index. Fix: identify records
   **positively**, by requiring one of the four mandated `verdict` values, and **report** the skipped files rather
   than discarding them quietly.

A third, smaller guard that earns its keep: warn when a record's slug has **no matching metadata row**, because the
builder's index prints TVL looked up by slug — an unmatched slug shows a confident `$0` next to a real protocol.

---

## 7. WHERE CHILDREN PUT THEIR SCRATCH FILES

A child inherits the parent's working directory, not the campaign directory named in its brief. In this pass an
agent wrote `probe_explorers.py` into the **previous** campaign's folder (`Desktop/audit2/`, the shell's cwd)
while working on `Desktop/audit3/`. Harmless here, but it means:

- **Give every child an ABSOLUTE scratch path** in the brief (`$LOCALAPPDATA/Temp/<campaign>/`), never a relative
  one and never "the campaign dir" — and expect some strays anyway.
- **Sweep the previous campaign dir at the end of the pass** and delete files the children left behind, or the
  next session's recon reads another campaign's scratch as its own context.
- The brief's own output paths must be absolute too; a child that writes its JSON to a relative path may write it
  somewhere the adapter never globs.

---

## 8. THE OUTCOME — what the doors actually bought (endgame, 2026-09-24)

§1 ends at "55 seeded". Here is what the four recon batches plus the exploit door returned, because **payoff per
door** is the measurement that should steer the next pass.

```
55 seeded -> 53 distinct verified (2 slugs were seeded into two batches each)
          -> 16 survivors: 6 TARGET_CANDIDATE, 5 WEAK_CANDIDATE, 7 UNRESOLVED
          -> 37 KILLED, each with its killing gate recorded
```

**Every survivor had all three of: a live payment channel, at least ~400 lines of the protocol's OWN code, and
external value independently re-derived on-chain.** Nothing missing any one of the three survived. That is the
scrutiny-adjusted-value metric (`sourcing-brief-2026-09-reconciliation.md` §0) made concrete, and it is the
cheapest post-hoc test of a shortlist: **if a candidate misses one of the three, it is a note, not a target.**

### Door verdicts — measured, therefore not to be re-run

| Door | Result |
|---|---|
| **Vertical sweep + channel-first (G11)** | **Produced every single survivor.** 206 funded zero-flag -> 16. The ordering is what made it cheap: **20+ candidates holding $367k-$1.9M on-contract died purely on "no channel exists"** — real money, no buyer, no target. |
| **Fork thesis** | Produced genuine *determinations* but **no target**. `LOCKON` -> Controller/SetToken **sha256-match Set Protocol v2 byte-for-byte**, so the money is the upstream's (G8b, not a target). `Autofarm` -> a real diff: MasterChef fused with Yearn-v2 accounting, upstream `devaddr`/`bonusEndBlock` removed. `Hop` -> only the AMM is Saddle-derived; the bridges are original. `Rari` -> Compound V2, diff undetermined. `CHATEAU` -> source unreachable. Read as: the door works, its ceiling in this particular pool was low. |
| **Fresh deployments** | **Dead as a funds source for the third time**, and now for a NEW reason — the listing-artifact trap below. |
| **Exploit-backwards (D1)** | **Killed on evidence** — see `sourcing-brief-2026-09-reconciliation.md` §5-D1. |

### A third trap for the freshness thesis: `listedAt` measures the LISTING, not the DEPLOY

Even when the date field is healthy (§2.3), a fresh `listedAt` does **not** mean fresh code:

- `JustLend sTRX` showed **age 0 days** — it is the **JST token from 2020**, newly listed on the aggregator.
- `Theo Network thUSD` showed **13 days** — a **5-month-old, already-audited** protocol whose *listing* is new.

So a fresh-deployment thesis needs a **deploy-block fact** (contract creation block, first-seen verification
timestamp, or first git commit) — **never the aggregator's listing date.** This is the third independent way
freshness has failed to predict funds; keep it as a *scrutiny discount only*, and kill it on the spec next time
rather than re-running it.

### Two mechanical notes worth reusing

- **Seeding one candidate into two batches is useful, but the aggregator must dedupe by slug AND report the
duplicates.** `justlend-strx` and `levr-bet` were each seeded twice on purpose (independent second opinion), and
`levr-bet` came back **KILLED** from one agent and **UNRESOLVED** from the other. Silently keeping the first would
have hidden a real disagreement. Batch ordering happened to keep the more determinate verdict here — make that an
*explicit* rule (prefer the determinate verdict, log the conflict) rather than luck.
- **The kill ledger is the most reusable artifact of the pass.** 37 rejections, each with the gate that killed it,
is what stops the next pass re-researching them — the same reason this campaign stores rejected doors and
superseded strategy files instead of deleting them.
