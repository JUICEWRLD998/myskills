# Compile parity: prove the source you are auditing IS the deployed code

Before any finding is claimed, prove the reviewed source compiles to the deployed bytecode.
"Verified on the explorer" is a claim about a UI; parity is evidence. Validated 2026-09 on Sato
(Ethereum, immutable v4 hook) where this was the difference between "maybe the source is stale"
and a clean proof that the reading was the live code.

## 1. Get the source WITH its compilation settings (Sourcify first)

    https://sourcify.dev/server/v2/contract/{chainId}/{address}?fields=sources,metadata,compilation

Keyless, and it returns the per-file sources AND the compiler settings AND the match verdict
(`match: exact_match` / `match: partial_match`). Prefer it over Etherscan HTML (no key needed, no
scraping). Etherscan-family HTML is the fallback; Blockscout `/api/v2/smart-contracts/<addr>` for L2s.

**PITFALL — preserve the ORIGINAL paths when dumping.** `sources` is a dict keyed by the project's
own path (e.g. `lib/prb-math/src/ud60x18/Math.sol`). Flattening to basenames silently COLLIDES and
LOSES files: PRBMath ships both `sd59x18/Math.sol` and `ud60x18/Math.sol`. On the first Sato dump only
34 of 57 files survived, and the lost one was `ud60x18/Math.sol` — exactly where the `exp`/`ln` used by
the curve live. Write each source at its declared path (see `scripts/sourcify_pull_sources.py`).

## 2. Rebuild with the EXACT original settings

Take every value from `compilation.compilerSettings`, do not infer:

    [profile.default]
    src = "src"
    libs = ["lib"]
    solc_version = "0.8.26"      # exact version from settings
    evm_version = "cancun"
    via_ir = true                 # viaIR changes everything; a miss here breaks parity
    optimizer = true
    optimizer_runs = 200
    bytecode_hash = "ipfs"
    cbor_metadata = true
    remappings = [ ... ]          # ALL of them, verbatim (see below)

Remappings are part of the METADATA, so a missing one changes the metadata hash even when the code
matches. The Sato build declared 13; shipping 9 produced identical executable code but a different
trailing hash, which cost a round of debugging.

## 3. Compare against the deployed code — immutables are the trap

A naive compare of local `deployedBytecode` vs `cast code <addr>` FAILS on any contract with
immutables (the artifact holds zeros where the chain holds real values). Do it properly:

1. Read the artifact's `deployedBytecode.immutableReferences` (map of immutable -> byte ranges).
2. Assert the two codes are the SAME LENGTH.
3. Assert every differing byte offset falls either inside an immutable range or inside the trailing
   CBOR metadata block (last ~52 bytes: `a2 64 ipfs 58 22 <32B hash> 64 solc 43 <3B ver> 00 33`).
4. Everything else must be byte-identical, including any bytes before the first immutable.

`scripts/parity_check_immutables.py` does exactly this. Sato result: 8576-byte runtime, 322 differing
bytes — 290 inside 19 immutable ranges, 32 the IPFS metadata hash, executable code identical.

## 4. Corroborate the immutables against chain truth

Decoding immutable slots from runtime code is only as good as the artifact, so cross-check them with
the contract's OWN getters and canonical addresses:

* `GENESIS_BLOCK()` / `GENESIS_HASH()` must describe a real block (the hash of `block-1`), and a
  contract's own genesis immutables are the deploy-block ground truth when the RPC cannot serve old
  state (see references/onchain-invariant-forensics.md).
* Infrastructure addresses must match the canonical deployments (v4 `POOL_MANAGER` =
  `0x000000000004444c5dc75cB358380D2e3dE08A90`; a token address must equal the token you think it is).
* A mismatched token/PoolManager address here means you are reading the wrong artifact — catch it
  before building anything on top.

## 5. What parity does and does not buy you

* Buys: the reviewed source's math is the deployed math, so a behavioural surprise is a BUG, not a
  stale-source artifact. This is what let the Sato curve divergence be reported as a code defect
  instead of an unverified suspicion.
* Does NOT buy: agreement on the metadata hash (expected to differ whenever your input file set or
  remappings differ), nor compile parity for contracts whose implementations were left unverified
  (proxy shells) — those need the impl address checked separately.
