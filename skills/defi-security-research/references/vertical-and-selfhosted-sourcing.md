# Vertical sourcing: self-hosted targets, no platforms (2026-09-16)

**Why this file exists.** The campaign has now tried four sampling strategies and measured each:

| Strategy | Measured outcome | Verdict |
|---|---|---|
| TVL sweep of "small + unaudited" (audit2) | 8 targets, 0 findings, **$0**, no buyer existed | **Dead** — no program, no money on-contract |
| Fresh-contract firehose (Door 1) | 6,500 contracts → 36 funded → **0 own-code** | **Dead** — newly-verified = freshly deployed = empty |
| DefiLlama adapter additions (Door 2) | mechanism works, **4 hits → 0 survivors** | Low yield |
| Platform programs (Immunefi/HackenProof) | 54 no-KYC Solidity programs available | **Dropped by user decision** — duplicate race, someone else's queue |
| **Vertical + self-hosted program (this file)** | **309 → 30 → 18 candidates; 1 genuinely funded target measured** | **Current strategy** |

This file is the replacement for platform hunting. It is honest about the yield: the method works, the
first vertical tried is **thin**, and the bottleneck has moved from *finding* to **address resolution**.

---

## 1. The sampling change

**Sample from verticals, not from TVL rankings.** A TVL ranking surfaces the biggest protocol in every
category — which is the most-audited one. A vertical filter surfaces the set that generalist auditors
never specialised in.

```js
// D1 — from the corpus the campaign already pulls
const all = await (await fetch('https://api.llama.fi/protocols')).json();
const cands = all.filter(p =>
  VERTICAL.test(p.category) &&        // pick a low-coverage vertical
  (p.tvl || 0) >= 250_000 &&          // money must exist
  String(p.audits || '0') === '0'     // and reported unaudited
);
```

**Measured, gambling vertical:** 309 in vertical → 30 funded ≥$250k → **18 funded + zero-audit.**

### Low-coverage verticals worth working (protocol count / total TVL)

```
SoFi 86 · Insurance 31 · NFT Lending 32 · Options Vault 22 · Token Locker 21
Gambling cluster: Prediction Market 123 · Gaming 91 · Gamified Mining 42 · Luck Games 38 · Yield Lottery 15
```

Chosen because they are funded, unglamorous, and (unlike Lending/Dexes/Staking) have **no specialist
crowd** and barely appear in the `/hacks` incident corpus.

**`audits == "0"` is unreliable in BOTH directions** — the campaign already found a protocol reporting 0
with two real audits on GitHub. Treat 0 as "worth checking", and confirm against `audit_links` from the
per-protocol endpoint. Never score from the count.

---

## 2. Address resolution — the real bottleneck

> **SOLVED 2026-09-22 — see §2.0. The bottleneck below is real, and it has a one-fetch fix that this
> file missed for six days.** Everything after §2.0 stays as the record of *why* the manual methods
> were tried, and as the fallback when a protocol has no published scope.

### 2.0 THE FIX — the buyer publishes the map

**The wall: "there is no machine-readable map from protocol → the contract that holds its money."**
The map exists; it is on the **buyer's scope page**, and it carries more than addresses.

```
node .../defi-security-research/scripts/immunefi_targets.mjs --scope "<Program>"
```

One fetch returns: every in-scope **address** with chain + label, the **severity→price ladder**, the
**attack window**, the **payout token**, the **KYC flag**, and the **prior-audit count**.

Measured 2026-09-22 (`STRATEGY_v7.md`, `TARGET_RADAR_v7.md`):

| Program | addresses | buyer critical | priced at rest | control |
|---|---|---|---|---|
| **Flux Finance** | 9 | $550k (`10% of funds at risk`), KYC waived, `prior audits: 0` | **$43.51M** | Compound USDC `$832.64M` PASS |
| Stader for ETH | 21 | $1.0M | $5.09M | PASS |
| Ankr | 3 | $500k | $3.34M | PASS |

This is the first time the campaign has held **buyer money and on-contract money in one target**.

**Three scope shapes — do not conclude "no addresses" from one parse:**
1. **Address on a known explorer** (Flux → etherscan) → price directly.
2. **Address on a CUSTOM explorer** (Derive → `explorer.lyra.finance`) → add one map entry to
   `SWEEP/v7_scope_g8.mjs`; the addresses are there, the host is just not in the map.
3. **A pinned GitHub commit and NO addresses at all** (CoW Protocol →
   `cowprotocol/contracts@6ebbd810`) → the scope is *source at a commit*; clone it and **skip address
   resolution entirely**. Often the best shape for a fork-diff audit.
4. A scope listing contract **names** with no addresses (Nexus Mutual: "3 assets, 0 addresses") is
   **UNRESOLVED**, never "holds nothing".

**Money method (unchanged, and it is load-bearing):** Blockscout `/token-balances` enumerates ALL
tokens with the explorer's own price — the native-only gate returned a **false "0 of 10 funded"**
twice. Run a **positive control on the same code path** before writing any negative. Unpriced tokens
count as **ZERO**.

**Chain coverage gap, measured:** BSC and Avalanche have **no keyless Blockscout** —
`bsc.blockscout.com` / `avalanche.blockscout.com` → 404, Routescan → `"chain not supported"`,
Etherscan V2 free tier → `"Free API access is not supported for this chain"`. Lista's 55 BSC
addresses and BENQI's 35 Avalanche addresses are therefore **unpriced, not empty**. A paid Etherscan
key is the cheapest fix.

---

**D1 gives you a name and a TVL. It does not give you the contract to audit.**
*(The manual methods below remain the fallback when no scope is published.)*

**Source 1 (reliable):** the per-protocol detail endpoint carries a chain-prefixed address that the
*list* endpoint does **not**.

```
api.llama.fi/protocol/<slug>   ->   .address = "base:0x16ee7eca…"
```
Measured **4/18 resolved**. Reading the *list* endpoint and concluding "no addresses exposed" is a
wrong-endpoint error — it cost a cycle in this campaign.

**Source 2 (fallback): DefiLlama adapter source, EXACT names only.**
```
raw.githubusercontent.com/DefiLlama/DefiLlama-Adapters/main/projects/<slug>/index.js
```
- **Page the listing.** Measured 1,000 entries/page, **4,000 total** — an unpaged read sees a quarter of
  the corpus and silently reports a wrong denominator.
- **Slugs ≠ display names.** `EtherFlip`, `Ape Church`, `Ridotto`, `Trueo`, `Zethr`, `Fake World Assets`
  and `Polymarket International` have **no adapter dir at all**. Fuzzy matching then returns the **wrong
  protocol** — measured false pairs: `Fake World Assets → alienworlds`,
  `Liquidity House → amulet-liquidity-staking`. **A wrong address is worse than NOT FOUND**, because it
  scores someone else's contract and produces a confident wrong answer.

### The trap that matters most: the address you get is usually NOT the contract you want

Measured on the gambling vertical — three of four resolved addresses hold the protocol's **own token**:

| Target | Address holds | Is that the target? |
|---|---|---|
| Sport.fun | 91,281 **FUN** (own token) | No — peripheral pool |
| Limitless Exchange | 8,991 **LMTS** (own token) | No — peripheral pool |
| Trueo | nothing | No |
| **beta-finance** | **WETH + USDC + USDT + DAI** | **Yes — proxy fronting a real bankroll** |

**A protocol's own token is not value at risk** in the sense that matters: an attacker cannot convert it
into someone else's money. So a G8 result read off the wrong contract is worse than no result.

**Find the core contract a second time, from:**
1. the protocol's own docs — `/developers/addresses`, `/docs/contracts` (Pareto's scope page was exactly
   this, and it listed every vault + strategy + queue);
2. the token's large holders — the game/vault contract is often among them (`token-balances` on the token,
   or the explorer's holders tab);
3. the explorer's internal-transaction graph out from the known address;
4. `cast storage <known> 0x360894…bbbc` for a proxy impl, or an owner/controller slot.

**Budget real recon time here.** This is the step that decides whether a target exists, and it does not
collapse into one API call. Log a target whose core contract cannot be located as a **coverage gap**, not
as a negative.

---

## 3. G8 — the funds gate, and why it keeps lying

**G8 must enumerate ALL tokens with prices, and must run a positive control on the same code path.**

This session re-learned the campaign's own documented defect: a **native-only** check reported
**"0 of 10 funded"** on contracts that held value. The corrected gate uses the explorer's
`/addresses/<addr>/token-balances` (all tokens + explorer prices):

```
beta-finance   0x972a785b…  $25,311   WETH $13,060 | USDC $8,733 | USDT $3,185 | DAI $332
CONTROL (USDC)              $27,501   -> gate is LIVE
```

### The new trap this exposed: dust and airdrop spam

Ample's ten adapter addresses look busy — `ABTC`, `UXOR`, `DIOR`, `DOODLE`, `basenoun`, `T.ME/S/US_POOL`
— and hold **no real value**. One address showed `4,156,641 steakUSDC` and still priced to $0.

**Rank by PRICED USD, never by token count**, and count unpriced tokens as zero. A contract with 390
unpriced tokens is not a funded target.

### The permanent rule
**Never write down "0 of N funded" without a positive control on the same code path.** An empty scan and
a broken scanner are indistinguishable, and this campaign has now made that mistake twice.

---

## 4. Payment without a platform

**Self-hosted programs are the channel.** They are published in protocol docs, not on a platform, and a
compiled list already exists:

```
raw.githubusercontent.com/solodit/solodit_content/main/bug_bounties/custom.md
```

Measured on one fetch — these are programs offered **directly by protocols**:

| Protocol | Max bounty | Where the terms live |
|---|---|---|
| **Frax Finance** | **$10,000,000** | `docs.frax.finance/smart-contracts/bug-bounty` |
| Uniswap | $2,250,000 | `uniswap.org/bug-bounty` |
| Aptos Foundation | $2,250,000 | `github.com/aptos-labs/aptos-core/blob/main/SECURITY.md` |
| 0x Protocol | $1,000,000 | `docs.0xprotocol.org` |
| Convex Finance | $250,000 | `docs.convexfinance.com` |
| Ethereum Foundation | $250,000 | `ethereum.org/en/bug-bounty` |
| Compound | $250,000 | `docs.compound.finance` |
| PoolTogether | $25,000 | `docs.pooltogether.com` |

Solodit's schema is the right one — **Funds Reserved, Max Bounty, Total Paid, Turnaround (mins)** — and
is **mostly unfilled**, so it is a stub to extend, not a complete list.

**The door generalises:** every protocol's own `SECURITY.md`, `/security` page, or `/bug-bounty` docs is
a self-hosted program. **Grep for it on every D1 target before deciding who to tell.**

### The rule that follows from dropping platforms
> **Never audit a target whose payment channel you have not confirmed.**
> Order: D1 → D2 (address resolution) → G8 (funds) → **channel** → audit.

Auditing first and looking for a buyer afterwards is exactly what produced three weeks of $0. A target
failing the channel check is logged as an observation, never started. If no channel exists, the options
are direct disclosure to a security contact, or the advisory path (which pays in track record only).

---

## 5. Rejected doors, so they are not re-run

- **Explorer name-search** (`/search?q=casino|lottery|dice|…` across 6 chains): **2,304 contracts →
  ~5 holding >0.05 native, all dust.** It searches the **metadata layer**, not the funded protocol layer.
  It finds token contracts named "Casino", meme coins and dead projects. Closed as tested-negative.
- **Function-selector recurrence** (`4byte.directory` `?text_signature=placeBet|spin|cashOut`, then probe
  explorers for which contracts expose them): **RUN 2026-09-17 — mechanism works, yield zero with
  adapter addresses. See §7 for the verified recipe and the two traps that produced a false negative.**

---

## 7. D5 selector recurrence — RUN, and what it actually takes (2026-09-17)

**Verdict: the door is sound and now tested; it fails only on address supply, not on method.**
161 addresses → 10 contracts implementing vertical behaviour → **all holding $0**. Re-runnable the
moment a real address list exists. Do NOT record it as a negative.

**Recipe that works:**

1. **Compute the selectors LOCALLY with `cast keccak`, never from the 4byte API.**
   `cast keccak 'withdraw(uint256)' | cut -c1-10` → `0x2e1a7d4d`. Self-check against
   `deposit()` = `0xd0e30db0`, `transfer(address,uint256)` = `0xa9059cbb` before trusting it.
2. **TRAP 1 — `slice(0, N)` of 4byte results returns the OBSCURE registered variants.**
   `text_signature=stake(` returns `stake(uint256,uint8,bytes)` first; the canonical
   `stake(uint256)` is not in the first four. Indexing those yields a scanner that can never match a
   real dispatcher — a clean-looking **zero** from a dead matcher.
3. **TRAP 2 — the 4byte API has no exact-match guarantee.** `?text_signature=deposit()` returned
   "no exact row" for `deposit()` and `withdraw(uint256)` while those signatures certainly exist.
   A lookup-driven scanner silently loses its whole keyword list. Hence step 1.
4. **Match the PUSH4 bytes against runtime code.** The dispatcher embeds every selector, so
   `code.includes(sel)` is a valid membership test. Search with the selector, not the bare hash.
5. **CAVEAT, recorded:** a PUSH4 constant anywhere in the code (a stored interface id, a hardcoded
   call) also matches. **A hit is a LEAD, never a finding** — confirm by calling.
6. **Skip `codesize < 100 bytes`** (EIP-1167 clones carry no dispatcher) and log the count as a
   coverage gap, not a zero.

**Mandatory controls, both cheap:**
- **Positive, on a known contract:** WETH must match `d0e30db0` + `2e1a7d4d`. If it does not, the
  scanner is broken and NO negative may be written.
- **Positive, on the candidate stream's shape:** Convex Booster `0xF403C1…AE31` matches
  `claimRewards()`. If real staking contracts match nothing, the selector list is too narrow.

**The blocker this exposed is not selectors — it is addresses.** 71 of 161 adapter-supplied
addresses had no code at all: adapter lists carry the pools an adapter *counts*, not the protocol's
fund-holding core. Same wall as the `.address` field (6/30). **There is no machine-readable map from
"protocol" to "the contract that holds its money"** — resolve from the protocol's own docs/app, by
hand, and budget real time for it.

### The EIP-1167 warning restated
`363d3d373d3d3d363d73<impl>5af43d82…` is a clone, not an unverified contract, and it has no
dispatcher — resolve the embedded implementation before concluding anything about it.
- **Fresh-verification firehose** and **TVL sweep**: dead, see §1.

---

## 6. The pipeline, as a script

`SWEEP/sweep.mjs` implements D1 → D2 → G9 → G8 → G7 with a positive control:

```bash
node sweep.mjs --list-verticals
node sweep.mjs --vertical gambling --top 25
node sweep.mjs --vertical all
```

**Known defect in it, recorded rather than hidden:** its D2 uses the adapter-repo fuzzy match, which
produced the two false pairs in §2. **Replace that stage with the per-protocol `.address` read** before
trusting its address output. The D1 and G8 stages are sound.
