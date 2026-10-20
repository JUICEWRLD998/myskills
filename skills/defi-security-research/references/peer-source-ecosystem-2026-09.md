# Peer researcher source-ecosystem triage (2026-09-24)

**What this is.** On 2026-09-24 the user asked us to review a peer researcher's bug repository and learn his
audit method. This file records what that account actually contains, what we imported, what we deliberately did
not, the upstreams worth following, and — first — a correction to the premise we were given.

Subject: `github.com/Maakai123` — 158 public repos indexed, **32 inspected** (all named repos plus two, minus
duplicates). Fork-vs-original was established from each repo's "forked from" link, and "he authored commits
here" from per-branch commit Atom feeds, not from guesswork.

## 0. THE PREMISE IS NOT SUPPORTED — and the correction is the first finding

We were told he **"got paid from Bugcrowd for a bug recently."** Measured, independently:

- **No payout, ranking, CVE, or named-program bounty attributable to him could be found anywhere.** A web
  search for his handles returns nothing; a Code4rena profile page 404s; no leaderboard entry, no payout
  mention, no disclosure write-up.
- **The platform in the claim is also probably wrong:** the account's own README lists **Cantina, Sherlock,
  Code4rena, HackenProof and Immunefi** — Bugcrowd appears nowhere. The two report IDs linked in his corpus
  (`SUIDEXCA-47`, `DEXLYNCA-59`) are **HackenProof** IDs, which is the strongest *submission* evidence present.
- What IS verifiable: **19 self-written finding reports** naming real protocols with the contest URL attached
  (see §2.5), so *participation* is checkable from public contest pages. Placements are stated nowhere.
- **Do not repeat the "$60,000+ bug bounties" badge** that appears in one of the repos he forked — that badge
  belongs to the upstream project's authors (finite-monkey), not to him. A misattributed payout is exactly the
  kind of unverified number that, once in doctrine, is indistinguishable from a measured one.

**So the method is importable and the payout claim is not.** That split is the whole point of this file: what
he demonstrably does (a hand-built pattern library, a findings corpus, a Solana→Move→ZK synthesis, and a
curated fork list) is real and visible in the code; the commercial claim attached to it is not, and calibrating
our strategy to it would repeat the 2026-09-22 lesson where a peer's platform claim was measured and collapsed.

## 1. Verdict counts (32 inspected)

| Verdict | n | Meaning |
|---|---|---|
| **IMPORT** | 6 | worth mining into our skills or vendoring under licence |
| **CITATION** | 20 | link/summarise only — reference corpus, report dumps, scope repos |
| **SKIP** | 1 | `Rarecode` — nothing of use |
| **DEAD** | 5 | empty or near-empty: `move-security`, `Perpetual-protocol`, `Decentralizedstablecoin` (no branch at all); `solana-security`, `smart-contract-sec-notes` (one-commit stubs) |

**Populated vs empty:** 27 of 32 populated. Note for anyone re-running this: **the GitHub API's `size=0KB` is
unreliable on this account** — most "0KB" forks are populated (one reports 0KB and holds a full XRPL C++ repo).
Only the no-default-branch check is decisive.

**He authored commits in exactly 7 repos** (`audits` 20, `Solana-primer` 15, `ai-auditor-primers` 2, plus
first-commit-only repos). **Every other fork is an unmodified sync** — for those, the upstream is the thing
worth studying, which is why §3 is a follow-list rather than a file list.

## 2. The IMPORT set

2.1 **`audits`** (fork of `x15-eth/audits`, 20 own commits) — **the best artifact on the account.**
`contests/` holds 19 self-written reports (~100 KB) in a consistent shape —
`## Protocol` + `### [Severity-NN] Title` + Description / Attack path / Recommendation, tied to the public
contest page. Spanning Move, Solana and Solidity: `Aave-Aptos` (stale-oracle Medium), `Suidex` (2 Criticals,
including a `token0/token1` parameter error in a swap), `Dexlyn` (token-identity bypass in a flash-swap
repayment = direct theft), `Gte` (CLOB bitwise-logic), `LiquityV2`, `mezo` (interest double-counted in
borrowing capacity), `Solaxy` (Solana account-owner index desync), `Telcoin` (base-fee validation bypass),
plus 11 more. **Use as a worked-example corpus** — every entry is independently verifiable against a public
contest — and as a shape convention for our own report templates.

2.2 **`ai-auditor-primers`** (fork of `devdacian/ai-auditor-primers`, MIT, he added 2 commits) — the
**primer-vs-checklist** distinction and a 278 KB v12 ERC-4626 specialist primer. Imported in detail into
`defi-audit-engine/references/primer-layer-and-agent-framing.md` §1.

2.3 **`Check-list-2`** (fork of `BradMoonUESTC/finite-monkey-engine`, Apache-2.0) — actually an LLM
vulnerability-mining *engine*, not a checklist. Its design write-up contributed the assertion-form seed prompt,
the business-flow detection unit, and the **error-accumulation budget** — the strongest single import in this
whole review, now in the same file, §2.

2.4 **`Blockchain-Attack-Vectors`** (fork of `ImmuneBytes-Security-Audit/Blockchain-Attack-Vectors`, **no
LICENSE**) — a single-axis *stack-layer* taxonomy (10 buckets, GitBook TOC in `SUMMARY.md`) whose best part is
an 11-file Solana vector set in a consistent vulnerable-code → scenario → mitigation template. **Not vendored**
(no licence) — the taxonomy *shape* was mined into our own text; see the note at the end of
`primer-layer-and-agent-framing.md`.

2.5 **`Solana-primer`** (his own repo, 15 commits, ~350 KB, no licence) — the account's only **original
knowledge synthesis**: a Solana vector set, a Rust/Solana code-smell catalogue with raw snippets, Token-2022
extension research, an annotated Raydium-CPMM/bonding-curve findings file (87 KB), Move/Aptos `#[view]`
semantics, plus SP1-ZKVM and ETH-Prysm notes. Raw and unpolished; it maps the owner's own learning path
(Solana → Move/Aptos → ZK). Summarise/link — no licence to copy under.

2.6 **`awesome-audits-checklists`** (fork of `TradMod/...`, no licence) — an 18 KB / ~200-link index in 11
sections, and its real value is as a **follow-list generator**: Cyfrin/Solodit, SCSVS, Beirao, Nascent's
simple-security-toolkit, QuillAudits' anti-hack list, the SEAL crisis handbook, Immunefi's report-writing
checklist. It opens (correctly) by warning that checklists must not be relied on alone. Do not copy the file.

## 3. Upstream follow-list (what the fork list reveals he learns from), ranked by signal

1. **`devdacian`** — `ai-auditor-primers` (MIT) + writes at dacian.me. Highest architectural relevance to us.
2. **`ImmuneBytes-Security-Audit`** (`shubhisaran`) — `Blockchain-Attack-Vectors`; the layered taxonomy.
3. **`x15-eth`** — `audits`. The solo-researcher "Web3 Security Research Portfolio" pattern (README table →
   per-contest markdown). A direct peer benchmark.
4. **`Frankcastleauditor`** — `public-audits`: Rust/Solana private-audit portfolio (Lido, GMX Solana, Pump,
   LayerZero, Synthetix, Hydration, Perena, BIO) with 24 public PDFs and a findings-severity ledger.
5. **`BradMoonUESTC`** — `finite-monkey-engine` (Apache-2.0), the mining engine + its design philosophy.
6. **`TradMod`** — `awesome-audits-checklists`, a maintained index of every other checklist worth having.
7. **`nullity00`** — `zk-security-reviews`: a 72-protocol ZK audit PDF corpus (Aleo, Celestia, Gnark, Risc0,
   Linea, Polygon Hermez, Penumbra, Renegade, Mina…).
8. **`immunefi-team`** — attackathon scope repos (XRPL lending, Plume, Nucleus Boring-Vault): what a programme
   looks like from the inside, useful for reading scopes.
9. **Contest-framing orgs** — `code-423n4`, `Cyfrin`, and the LayerZero-on-Sui scope repos: they publish the
   scope.txt / out_of_scope.txt / 4naly3er report / specification-PDF conventions.
10. **Protocols he keeps as reference implementations, whose own audit PDFs ship inside the forks** —
    `naviprotocol` (8 Move audit PDFs), ZKsync (10 ZK-stack audit PDFs), Meteora, notional-finance,
    mento-protocol, babylonlabs-io, OpenEdenHQ, Lendvest, bounce-tech, LumiaChain, aera-finance.

## 4. Licence handling — applied, and the rule to keep applying

Only licence-clear material was copied. Vendored to **`Desktop/audits/_vendor/`** (durable, outside any
campaign dir): `base.primer.md` (MIT), `amy.vault.erc4626.primer.md` (MIT), `Orderbook.md` (MIT),
`LICENSE-ai-auditor-primers-MIT.txt`, and `finite-monkey/philosophy_of_monkey_en.md` (**Apache-2.0 →
attribution required**). Everything under a repo with **no LICENSE** was summarised or linked, never copied —
`Blockchain-Attack-Vectors`, `awesome-audits-checklists`, `Solana-primer` and `audits` all fall on that side.

**Rule for the next peer review:** read the licence *before* deciding what to import, and record the upstream
URL + licence next to anything copied. "No LICENSE file" means all-rights-reserved, not "free to take".

## 5. Scope line — Solana / Move / Rust

The account's genuine value-add over our existing library is **non-EVM**: 19 findings spanning Move and
Solana, plus the only original synthesis in the account. **Our two audit skills are Solidity/EVM-only, and
every new heuristic bank file says so explicitly in its `Not covered here` block.** This is a deliberate scope
decision, not an oversight: importing a Solana/Move path means importing its own toolchain, runtime model
(account ownership, PDAs, signer privileges) and gate stack, and it should be a project the user chooses, not
a side effect of a repo review. If and when it is chosen, the starting material is §2.5 plus the
`Solana Attack Vectors` set in §2.4 and the upstreams in §3 items 3-4.

## 6. Where the artifacts live

- Method report + the 20 strongest kernels: `Desktop/audit2/research/A-maakai-findings-method.md`
- This triage's full per-repo table + deep notes: `Desktop/audit2/research/B-maakai-source-ecosystem.md`
- Heuristic bank (137 entries, 5 files) → `defi-audit-engine/references/heuristics-*.md`
- Primer/framing imports → `defi-audit-engine/references/primer-layer-and-agent-framing.md`
- Vendored third-party primers → `Desktop/audits/_vendor/`
