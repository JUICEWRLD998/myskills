# Phase 9-10 verification toolkit (validated 2026-09, up v3 campaign)

Execution-tested techniques for turning hypotheses into verified findings when the target is on a
new L2 with keyless-only tooling. All items below were actually run to completion.

## 1. Compile-parity: is the public repo the deployed code?
When a repo's function list diverges from the explorer-verified ABI (sanitized-repo trap), quantify
how much of the repo is still trustworthy instead of discarding it all:
1. Get the EXACT compiler of the live contracts (explorer "CompilerVersion" field, e.g.
   v0.8.19+commit.7dd6d404) and download that exact solc (binaries.soliditylang.org/windows-amd64/
   list.json). OZ dependency version comes from the repo package.json (4.9.x) — extract the zip,
   remap @openzeppelin/contracts -> extracted dir via standard-json remappings.
2. Compile each repo entrypoint via solc --standard-json, optimizer {enabled:false} AND
   {enabled:true, runs:200}; outputSelection evm.deployedBytecode.object.
3. Compare against eth_getCode of the LIVE address on three signals: runtime bytecode LENGTH
   (=(len(hex)-2)/2), and dispatcher-equivalent count (PUSH4 0x63 immediately followed by EQ 0x14,
   from an instruction-aware walk — a naive regex over hex mis-slices when solc emits unprefixed
   hex, a real bug hit this campaign). Verdict: MATCH-likely = sizes within ~5% AND selector counts
   equal.
4. Exact equality is impossible without constructor args (immutables embed into runtime code), but
   a byte-level diff of repo-vs-live code shows the differences are exactly the immutable address
   slots (20-byte runs of zeros in the uncompiled artifact vs live addresses) + the 53-byte
   metadata tail. Mask those and you get byte-identity. Caveat: don't compare the v2 Gauge contract
   against a CLGauge implementation — both exist behind 45-byte EIP-1167 proxies (impl address at
   hex offset 22..62 of the proxy code, pattern 363d3d373d3d3d363d73).
Result this campaign: ve/Minter/FeesVotingReward/BribeVotingReward/RewardsDistributor/Router were
byte-identical (repo analysis valid); Voter diverged (use explorer source); the "Gauge" mismatch
was a CLGauge-vs-v2 miscomparison.

## 2. Prior-audit calibration: OCR image-only audit PDFs + line-ref match
Audit reports are frequently image-only scans (read_file returns NeedsOcrError). OCR pipeline that
worked on Windows with no admin:
- `python -m venv venv-ocr && venv-ocr/Scripts/python -m pip install pymupdf winsdk`
- Render each page with pymupdf at 200 dpi, then OCR via winsdk (Windows.Media.Ocr):
  StorageFile.get_file_from_path_async -> BitmapDecoder -> get_software_bitmap_async ->
  OcrEngine.try_create_from_language(Language("en-US")) -> recognize_async -> join line texts.
  Needs the en-US OCR language pack (present on stock Win11); engine is None otherwise.
- The OCR text's file/line references ("contracts/Voter.sol#L338-L343") matched the explorer-
  verified flattened source line-for-line -> proves the audit covered the DEPLOYED code, and that
  its ACKNOWLEDGED findings are still live. Calibrate your own hypotheses against that list before
  claiming novelty: label overlaps KNOWN-ADJACENT and hunt where the report was silent.

## 3. Forge-less PoC: pure-Python state simulation
When forge/cast can't be installed (asset URLs 404, no MSVC toolchain), prove accounting claims
with a faithful Python re-implementation of the on-chain math (see
../templates/reward_checkpoint_sim.py — validated: control, three attack timings, prior-epoch
preservation, redistribution conservation, managed-exit variant all assert). Rules that kept it
trustworthy: model the EXACT function semantics (same-epoch checkpoint OVERWRITE, earned() iterating
completed epochs from lastEarn, supply-checkpoint overwrite), assert the control case equals the
closed-form expectation (b/S*R_E) before trusting any attack output, and never hand-decode hex
state (order-of-magnitude slips poison invariant checks — decode in Python).

## 4. Proof-design subagents (Phase 9 fan-out)
Send one subagent per lead with a strict JSON deliverable: {attack_X: {valid, constraints, steps,
victim_loss, attacker_gain}, novelty_vs_prior_findings, economic_impact_usd_estimate,
poc_plan, refutations, confidence} and instruct it to reason with line numbers against the saved
verified-source files. Notes: batch results are held until ALL children finish — read the live
`task-N.log` transcripts (tail) for early finals; subagent summary files can be one giant JSON line
(total_lines 0) — parse with json.load, never read_file line-wise. Orphans that run 90+ minutes
are usually doing extra on-chain discovery — let them finish, their corrections are valuable.

## 5. On-chain structure corrections that prevent wrong analysis
- Subgraph "gauge" entities are often 45-byte EIP-1167 proxies: fetch proxy code, extract impl at
  hex offset 22..62, compare real impl sizes, not proxy sizes.
- `isPool` in ve(3,3) gauge factories is a one-bit FEE-CLAIM gate, NOT a CL-vs-v2 discriminator
  (all 81 registered gauges returned true on the live chain).
- Emission accounting for CL gauges lives in the CL POOL (rewardReserve / rewardGrowthGlobalX128 /
  stakedLiquidity), not the gauge; claims are per NFT position; swap fees on staked liquidity go
  pool.gaugeFees -> gauge._claimFees -> FeesVotingReward for veNFT voters (stakers do NOT earn them).
