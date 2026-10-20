# Target deep-recon playbook — new-chain EVM (validated 2026-09 on up v3 / Robinhood Chain)

Phase 6 recipes for the chosen primary target once discovery is done.

## CRITICAL: public repo may be SANITIZED — verify repo == live before trusting it
- Real case: github.com/up-exchange published "open source" repos whose Voter.sol had 35 functions and
  ZERO custom machinery; the LIVE explorer-verified Voter had 83 functions incl. the whole custom
  cap/epoch layer. History was rewritten to a sanitized snapshot + one "adjustments" commit.
- Detection (cheap, static): pull the verified ABI from the explorer (get-sourcecode) and diff the
  function-name set against `grep -oE "function [a-zA-Z0-9_]+" contracts/<File>.sol`. Mismatch ⇒ repo is
  not the deployed code. Also grep the repo for the project's own edit markers (e.g. "Modified by <X>")
  and check `git log --date=short` for a single squash commit on top of upstream fork history.
- Consequence: audit target source = EXPLORER-VERIFIED flattened sources (explorer attestation ties
  source to runtime bytecode), NOT the repo. Keep the repo for upstream-lineage diffing.
- Bonus framing for disclosure: "deployed code is under-audited and diverges from the public repo" is
  a stronger justification than any pre-audit claim.

## Address discovery when docs/deploy scripts carry none
- Deploy scripts often read config JSONs of which only `*.example.json` placeholders (zero addresses)
  are committed — don't waste time grepping them for real addresses.
- App-bundle mining: fetch site HTML (`curl -sL -A <browser UA>`), grep the `<script src>` asset path,
  download the JS bundle, `grep -oE '0x[0-9a-fA-F]{40}'`. TRAP: frontend configs mix TESTNET and
  mainnet addresses (found a "CL factory" with zero code on mainnet). Always confirm code presence:
  batch JSON-RPC `eth_getCode` against the mainnet RPC (one batched POST works on most L1/L2 RPCs).
- Keyword-context scoring: for each address, count keyword hits (voter|minter|gauge|factory|escrow|...)
  in a ±120 char window around each occurrence; probe the top scorers for code.
- Goldsky public subgraphs (many dApps use them): GraphQL POST with `{ __schema { types { name } } }`
  introspection to learn entity names, then query factories/pools/gauges. Entities mirror the schema
  family (Uniswap-v3-style vs ve(3,3)-style subgraphs are separate deployments).
- Governance walk over RPC: eth_call the Voter's address getters (`minter()`, `ve()`, `governor()`,
  `epochGovernor()`, `emergencyCouncil()`, `factoryRegistry()`, ...) to map the contract graph.
  Note centralization: all three roles collapsing to ONE small contract (e.g. 171-byte multisig-shaped)
  is a finding-class observation for the threat model.

## Selectors without cast/foundry: pure-Python keccak-256
- hashlib has NO keccak256 (only NIST SHA3 — different padding, wrong). OpenSSL CLI is sha3-256, also
  wrong. Foundry zip download may 404 (asset names/redirects vary).
- Working fallback: self-tested pure-Python keccak-256 implementation + 4-byte selector. Validate before
  use: keccak("transfer(address,uint256)")[:4] == a9059cbb, balanceOf(address) == 70a08231,
  transferFrom == 23b872dd. See scripts/keccak_selectors.py.
- Then: `eth_call` with selector, decode last 40 hex chars for addresses.

## Blockscout keyless source API (Blockscout = most new L2s/appchains)
- GET https://<explorer>/api?module=contract&action=getsourcecode&address=0x... returns
  {result:[{ContractName, CompilerVersion, SourceCode, ABI, Implementation, Proxy}]}.
- RATE LIMIT ≈ 5 req/min per IP → HTTP 429. Pace at ~7-8s between calls, back off 20-30s×(attempt)
  on 429, or run the fetch as a background job with notify and let it churn. HTTP 500s happen too —
  retry with small sleep.
- SourceCode is EITHER a flattened single file OR JSON {"sources":{path:{"content":...}}}; handle both.
- SourceCode can come back TRUNCATED mid-function for some contracts — treat the ABI as authoritative
  for interface mapping and re-fetch or use the repo for the body.
- v2 REST: /api/v2/addresses/{addr} gives is_contract/tx_count/coin_balance (also rate-limited).
- Explorer "verified" badge ≠ repo match: verification ties to the submitter's source, so the
  repo-vs-verified diff is still required.

## RPC quirks
- Some RPCs (rpc.mainnet.chain.robinhood.com) return HTTP 403 when the request has NO browser-like
  User-Agent — always send `User-Agent: Mozilla/5.0` on RPC POSTs (and on any HTTP fetch).
- eth_getCode result "0x" or len-2 = no contract. Batch ~40 addresses per JSON-RPC POST comfortably.
- The RPC GATEWAY also 429s (not just Blockscout): keep eth_call batches ≤ ~14 and sleep ~6s
  between chunks whenever any background fetch job shares the IP; exponential backoff on 429.

## eth_call response decode (three traps that each cost a re-run)
- Dynamic-array return is [offset word][length word][data…]: read the LENGTH at word 2 — the
  first word is 0x20 (offset), so allPools() misread as "32" once. Slice hex from 128, not 64.
- Struct-array element stride = the STRUCT's word count, not a guess: registry entries were
  PoolKey (5 words) + bytes32 id + bool = 7 words/element. Decode from the ABI-declared struct
  (or the verified source) BEFORE slicing; a wrong stride silently misaligns every later element.
- Build calldata by CONCATENATION of hex without 0x prefixes on args: `sel + "0x…"` embeds a
  mid-string 0x and every such eth_call returns null/empty with NO error — strip arg prefixes
  (`sel + pid[2:]`).
- Fee/value units: v4 fees are pips (1e-6). Percent = pips/10000 (5100 pips ≈ 51 bps); dividing
  by 100 prints 100x-inflated percentages. Write the conversion once, label it, sanity-check.
- Distinguish "getter absent" from "getter returns 0": eth_call to a selector the contract lacks
  returns "0x" (empty → None after decode), a real zero comes back as a full 32-byte word.
  Applying one family's ABI to another deployment's address is a cheap structural probe — it is
  how a third hook revision (different bytecode sizes per market, same registry) was detected.
- Proxy-family check: an EMPTY EIP-1967 impl slot does NOT mean "not a proxy" — BeaconProxy
  stores its beacon at slot 0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50
  and the implementation is one hop away via beacon.implementation(). Query both slots + the
  beacon's implementation()/authority() before concluding a small-code contract is a plain EOA
  or an immutable token.

## Fork-diff methodology (ve(3,3)/Solidly-family and similar)
- `git log --date=short` — upstream-fork repos often keep the fork's history then add ONE squashed
  "adjustments" commit: `git show --stat HEAD` then IS the whole custom delta. Diff it file-by-file;
  renames (Aero.sol→Up.sol) and license-header edits hide real logic changes — read the actual hunks.
- Compare repo file vs live verified file line counts/function sets to quantify the true delta.
- Inherited weirdness (e.g. comparing token amounts to time constants) is usually upstream code
  (Aerodrome distribute dust-guards) — check the upstream baseline BEFORE flagging anything.

## Audit-PDF handling
- Scanned reports come back image-only: read_file raises NeedsOcrError (all pages need OCR). If a recon
  subagent already summarized the PDF (firm/date/scope/findings), that dossier may be the only text
  source available until OCR tooling exists — cite it as such, and verify key claims independently
  (commit hashes, severity counts) when the project publishes them elsewhere.

## Workspace hygiene
- Save per-contract verified sources to disk as you fetch (deployed_sources/<Name>_<0x8>.json) so later
  phases diff/re-read offline. Write a PHASE6_RECON_CHECKPOINT.txt with the live contract map, live
  state (roles, mode flags, reserves), and open items — future sessions resume from it.
