# Fork-test RPC reliability (keep a fork audit green under RPC pressure)

Validated on the Sato audit (Ethereum mainnet, 2026-09-10 → 09-12) with four parallel agents plus
the orchestrator forking against public archive nodes. Unpinned, unthrottled, endpoint-single
fork testing produces false failures that will be misread as code bugs — the failure text even
says "EVM error; database error", which is the opposite of what it is.

## 1. Symptom table — what an RPC failure looks like in forge output

| forge output | what it actually is |
|---|---|
| `[FAIL: EVM error; database error: failed to get storage for 0x<token> at 2: Max retries exceeded HTTP error 429 with body: <!doctype html> … error 1015]` | endpoint rate-limited you; the test never ran |
| `[FAIL: EVM error; database error: failed to get account for 0x…636F6e736F6c652e6c6f67: Max retries exceeded HTTP error 429 …]` | same; note the 0x…console.log address is the cheatcode → the failure is in setUp/fork bootstrap, not the test logic |
| `ERROR sharedbackend: Failed to send/recv `basic|storage` … HTTP error 429 with body: <!doctype html>` | first symptom, one line above the eventual FAIL |
| `[PASS]` on 3 of 5 tests with the other 2 dying on the above | endpoints are flaky mid-run, not "2 real failures" |
| test passes locally, fails in a batch | shared-node contention (see §4) |

Also watch for a whole-block HTML body in the middle of a forge log (`Cloudflare error 1015 /
Access denied`, `cf-ray:` headers) — the endpoint served a challenge page instead of JSON-RPC.

## 2. Classification rule (apply before writing ANY severity)

If the failure reason contains `Max retries exceeded`, `HTTP error 429`, `HTTP error 5xx`,
`database error: failed to get storage/account`, or an HTML/Cloudflare body → INFRASTRUCTURE.

- Never record it as PROVEN, CLEAN, or a finding.
- Re-run on a different endpoint (below). Only if it reproduces on two independent endpoints does
  it become a candidate finding.
- If it cannot be reproduced at all, record `UNKNOWN` with the raw reason string as evidence.
- State the same rule to every delegated child: children record RPC-caused failures as findings
  more often than you would expect.

## 2b. Endpoint reality table (re-tested 2026-09-12, mainnet, historical `eth_call` at block 25,039,900)

| endpoint | status | note |
|---|---|---|
| `https://eth.drpc.org` | WORKS (archive) | carried the whole final verification pass |
| `https://eth-mainnet.public.blastapi.io` | WORKS (archive) | good rotation partner |
| `https://eth.blockscout.com/api/eth-rpc` | WORKS (archive) | independent operator, handy third leg |
| `https://eth-pokt.nodies.app` | 429 under load | serves archive until the shared IP saturates; then `Rate limit exceeded on Nodies public endpoints` |
| `https://rpc.mevblocker.io` | 429 / Cloudflare 1015 | served archive on 09-10, blocked on 09-12 |
| `https://0xrpc.io/eth` | latest-state only | answers `historical state … is not available` for old blocks |
| `https://1rpc.io/eth`, `https://rpc.flashbots.net/fast` | do not use | no historical state / HTTP 403 on the RPC method |
| `https://ethereum-rpc.publicnode.com` | latest only | "Archive requests require a personal token" |

Endpoint list decays within days — re-test with one cheap `cast call <addr> '<getter>()' --block <old>` before
trusting any of it.

## 2c. CLI trap: throttling flags need an explicit `--rpc-url`

In forge 1.8.1 the RPC-load flags are only accepted together with `--rpc-url` on the command line. With just
`ETH_RPC=<url>` exported (which the test file reads via `vm.envString`), forge aborts before compiling:

```
error: the following required arguments were not provided:
  --rpc-url <URL>
Usage: forge.exe test --rpc-url <URL> --match-path <GLOB> … --compute-units-per-second <CUPS> --fork-retries <RETRIES>
```

Exit code 2, no test output — easy to misread as a harness failure. Pass BOTH: keep `ETH_RPC` set for the test,
and add `--rpc-url <same url>` for the flags. Also remember forge keeps a per-chain fork cache under
`~/.foundry/cache/rpc/<chain>/` (a `mainnet` dir exists on this host): reusing ONE pinned block across reruns
means later runs are largely served from cache, which is the cheapest way to stop throttling yourself.

## 3. Make numbers reproducible: pin the block, throttle the node

```bash
# every measurement that will be quoted in a report:
ETH_RPC=https://eth-pokt.nodies.app \
  forge test --match-path test/<yours>.t.sol \
  --fork-block-number 25963320 \
  --compute-units-per-second 15 \
  --fork-retries 5 --fork-retry-backoff 2000 -vv
```

- `--fork-block-number` is NOT optional for quoted numbers: unpinned/latest forks drift between
  runs — the same suite logged `fork block: 25963320` on one run and `base block: 25947519` on
  the next, so "sell 1 SATO → 6.83e-5 ETH" was measured against two different states.
- `--compute-units-per-second 15` throttles request rate; `--fork-retries` + `--fork-retry-backoff`
  ride out transient 429s. Add a `sleep 20-30` between separate forge invocations.
- Cache: a genuinely-failing compile will not be hidden by caching, but "No files changed,
  compilation skipped" means you are looking at stale artefacts — re-check before concluding.

## 4. Contention: several agents forking at once

Public endpoints rate-limit per IP, and all your children share one IP (the orchestrator included).

1. Serialise the heavy fork work — one forking child at a time, or stagger them; do not let four
   children each run `forge test` on 5 fork tests simultaneously.
2. The orchestrator's own verification run goes LAST (or against a pinned block already validated),
   and is repeated if it 429s.
3. Rotate on any 429: `eth.drpc.org` → `eth-mainnet.public.blastapi.io` → `eth.blockscout.com/api/eth-rpc` →
   `eth-pokt.nodies.app` (see §2b for live/dead status); pause ~30 s between attempts rather than retrying hard.
   `ethereum-rpc.publicnode.com` answers latest state
   happily but refuses historical calls ("Archive requests require a personal token"), so it is a
   last resort for current-state-only assertions, never for historical ones.
4. Endpoint character changes over time (mevblocker.io sat behind Cloudflare and started returning
   error 1015 under parallel load on 2026-09-12 after serving archive calls fine on 2026-09-10) —
   so hard-coding one "known good" RPC into a test file is a slow-motion failure. Take the endpoint
   from `ETH_RPC` and keep a fallback list.

## 5. Fan-out hygiene that prevents the problem (see also references/audit-sweep-resume.md)

- One uniquely-named test file per child (`<scope>_<agent>.t.sol`); each child runs
  `--match-path test/<its file>` and adds `--skip test/<sibling>.t.sol` only if a sibling breaks
  compilation. Never edit a sibling's in-flight file.
- Keep an isolated orchestrator copy of the project (agents' test files excluded) for the
  verification gate, so no child's compile error or RPC wedging can block your run.
- Ask children to dump their raw forge output into the JSON evidence; a number without the command
  that produced it, the endpoint and the pinned block is not reproducible and should not be quoted.
