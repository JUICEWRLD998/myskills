# Fork-attack craft, oracle impersonation, and detector calibration

Technique bank imported/validated 2026-09-14 from a peer auditor's fork-attack phase. Use during the
mandatory fork-attack / red-team phase, and whenever a negative result is about to be written down.

## Forge outcomes by impersonating the ORACLE CONTRACT, not the player

You usually cannot fabricate the randomness provider's own reveal tx (commitment / hash-chain checks
reject it), but you CAN drive the CONSUMER's callback with `msg.sender == oracle`:
`anvil_impersonateAccount(<ORACLE_CONTRACT>)` + `anvil_setBalance`, then call the consumer's callback
(e.g. `_entropyCallback(uint64, address, bytes32)`) directly on the game proxy, with the request
sequence read out of the contract's own state getter. That makes the outcome yours to choose and
turns "player can't do this" into a testable invariant.

## Read state machines out of revert data (free spec)

Block-number / time guards leak their own constants. `RefundTooEarly(have, want)` ⇒
`want = requestBlock + 2001`; `RefundClaimPending(have, want)` ⇒ `want = commitBlock + 21` — which
decoded a TWO-step refund gated by TWO different constants, after reading the constants alone had
suggested one gate. Method: probe at increasing offsets until the error NAME changes, decode
`(uint256,uint256)` args with `eth_abi.decode`, then verify the boundary by landing exactly on it.
Corollary: **guard order hides the mechanism** — every early probe returned the timeout error, making
the other gate look irrelevant; walk one gate at a time.

## Fee-aware balance classification

Where a per-operation oracle/library fee exists (e.g. 1.4 MON per bet), a WINNING action nets
negative: `delta > 0` marks every action a loss and the harness "proves" the wrong thing. Recover
the payout as `delta + amount + fee` and classify against the stake, not against zero.

## The proxy selector-existence oracle (get the rule right or it lies)

No source, no ABI match — call the selector on the PROXY:

| Result | Meaning |
|---|---|
| a return value | IMPLEMENTED |
| revert carrying **≥4 bytes** of revert data (a custom-error selector) | IMPLEMENTED |
| revert with **EMPTY `"0x"` data** | ABSENT (what the fallback returns when the impl lacks it) |

Never test `"data" in error_json`: every revert payload has that key (usually empty string), so the
rule reports every selector as implemented on every proxy — it did, 10/10 contracts. Include a
known-absent selector as a control. An unmatched selector is a CANDIDATE, not proof of a hidden
function (14 "unidentified" BankRoll selectors were live; a `0x5614ffd9` "hidden selector" claim was
a regex false positive, retracted after an `eth_call` control against `deadbeef` / `12345678`).
Resolve derived contract ROLES by probing which selectors each proxy answers
(`getIsGame`/`tokenTotalShares` ⇒ bankroll; `edgeFactor`/`entropy`/`REFUND_*` ⇒ shared config base) —
not from the bundle's variable names, which were misleading.

## Detector calibration (the rule that decides whether a NEGATIVE is evidence)

"An empty scan result and a broken scanner are indistinguishable from inside." Before writing a
negative result:

1. **Enumerate every response SLOT/shape the parser covers** and state which it does NOT. A leak
   scanner that read `currentGame` + `history` but never `previousGame` reported `leaks: NONE` on a
   leak planted in exactly the `previousGame` shape it left open; v2 parsed all three and shipped a
   `--self-test` (3/3) — the OLD version must be re-run against the new fixtures and shown to FAIL.
2. **Plant a positive fixture per shape** and a secure fixture proving no false-positive. Implement
   detection as a PURE function over parsed payloads so the fixtures run offline, and ship
   `--self-test` with the tool.
3. **Read the detector's own source for self-matching patterns** — a scanner whose field-name regex
   included a key from its own log schema (`"note":`) fires on its own output and manufactures the
   escalation it was meant to prevent.
4. **Do hash/commitment/float reproduction in the TARGET's language.** Python
   `round(o*1e8)/1e8` + `json.dumps` disagrees with JS `Math.round(o*1e8)/1e8` + `JSON.stringify`
   on 55 of 706 records (different half-rounding, different float-to-string) — that produced both a
   bogus "651/706 reproduce" and a bogus set of "committed board ≠ board played" claims. A spread
   between two languages is itself a signal you are comparing the wrong things; a hash comparison is
   binary, so 92% is 92% WRONG.
5. **Print one RAW response** before believing any row of a table you generated.
6. **Calibrate verification status against the response FIELD, never the HTTP status.** A Blockscout
   `/api/v2/smart-contracts/<a>` returns a 36-key object (with `is_verified`, `name`, `abi`,
   `source_code`) when verified and a 6-key object (with `creation_bytecode`, no name) when not —
   and the same 500 `"Internal server error"` appeared intermittently for BOTH. Always fetch a
   known-verified control in the same batch and compare the JSON SHAPE. Same class of failure:
   an HTML `grep -i unverified` that called a nonexistent address "verified"; an API "404" that was
   actually a deprecation message telling you to use Etherscan V2 (read the body).

## Shell / cast / anvil traps that silently produce a confident false timeline

- **A shell helper that does not forward `"$@"` calls the function with NO arguments.**
  `c() { cast call "$1" "$2" ...; }` dropped every extra arg, so every parameterised call returned
  empty — and with stderr sent to `/dev/null`, a 28-market sweep produced a beautifully formatted
  table of blanks that the parser read as "no pool, no price". Forward explicitly
  (`local to=$1 sig=$2; shift 2; cast call "$to" "$sig" "$@"`) and never swallow stderr in a
  collector without ALSO asserting a known-good control returns non-empty in the same run.
- **`cast` prints an annotation that corrupts `awk` field indices** — `24073181425 [2.407e10]`, so
  `tr '\n' ' '` + `awk '{print $3}'` silently picks the COMMENT of field 2. Strip the annotation
  per line (`awk '{print $1}'`) before joining, or the value you read is the wrong variable.
- **`anvil_mine(count)` silently under-mines** (asked 2002, got 1058) → the test never reached the
  code under test. Mine in ~100-block chunks and verify `eth_blockNumber` actually reached target.
- **`python3 script.py | head -80` SIGPIPEs the script mid-run** and kills it before its `json.dump`,
  losing the artifact while the console looks complete. Redirect to a file, then read the file.
- **`cast codesize` a family of siblings before reading any of them.** Identical sizes ⇒ same source
  with different immutables; a deviating size is where the custom code is — but "different" ≠ "the
  protocol wrote it" (a 23 KB outlier attributed to the team turned out to be Chainlink's own
  contract, retracted).
- **Cloudflare `403 "Just a moment…"` is not "no source".** A spoofed browser User-Agent is not
  enough; real headless Chrome is (`google-chrome --headless=new --dump-dom` + strip the `<pre>`
  wrapper) and then the same explorer API returns full verified source. Note the complementary rule
  in scripts/fetch_explorer.py — some walls fall to plain `curl` where Python gets a TLS-fingerprint
  rejection; try curl first, escalate to headless Chrome.
- **zkSync-family L2s (Abstract, zkSync Era) do not run under stock Foundry** — they compile via
  zksolc to zkEVM bytecode. The working fix is `foundry-zksync` built from source (no official
  Windows release) with zksolc from `matter-labs/zksolc-bin` and the **ZKsync fork of solc** from
  `matter-labs/era-solidity` (NOT vanilla `ethereum/solidity`), passed via `--zk-solc-path`; a
  patched `ZKSOLC_PATH` env path and the Windows case in the OS-detection table are needed, and a
  toolchain auto-update mid-build corrupts the cache (`cargo clean`). If that is not worth it,
  fall back to read-only live verification and say which claim is therefore untested.

## Two meta-rules worth keeping

- **A contradiction between two of your OWN artifacts is a finding** — resolve it with primary data,
  never by picking the version you like (two internal notes had disagreed for two days on whether a
  create-response hash equalled the on-chain commitment; one fresh `eth_call` settled it, and the
  earlier note was wrong).
- **"The feature is used a lot" ≠ "an outside party can reach it".** On a native-AA chain `tx.from`
  is the ACCOUNT, never the signer (session keys, relayers and paymasters all look like the user), so
  7,329 "player" calls proved nothing about who ordered them; the decisive check was the client's
  response-body DESTRUCTURING (does it ever receive the signature?) plus the `*_pending` status
  poller. Rate EXTERNAL REACHABILITY, not usage frequency — conflating them flips Likelihood from
  Low to High wrongly.
