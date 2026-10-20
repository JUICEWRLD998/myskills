# Resuming an interrupted multi-agent audit sweep

Validated on the Sato audit: dispatched 2026-09-10 15:04 (6 children). At 15:27 the provider's
billing wall (`Billing or credits exhausted: HTTP 402`) plus `max_iterations` killed three of them;
the user resumed two days later and the sweep was reconstructed from cache + workspace.

## 1. What actually happened (the failure mode to expect)

Each child's log ends with one of:

- `final | status=completed duration=… summary: Billing or credits exhausted: HTTP 402: Insufficient
  Balance …` — the child was cut off by the provider, then reported as "completed".
- `final | end status=completed exit_reason=max_iterations (iteration budget exhausted)` — the child
  ran out of iterations mid-investigation.

In BOTH cases the child was mid-write-up, so its deliverable JSON was never created — while the
real work (test files, dumped JSON, analysis scripts) was already on disk. Recovery is therefore an
archaeology job, not a re-run job.

## 2. Delegation cache layout (read this FIRST, before re-dispatching anything)

```
~/.hermes/cache/delegation/
  live/deleg_<delegation_id>/
    manifest.json                 # per task: goal, log path, status, exit_reason
    task-0.log … task-<n>.log     # full human-readable transcript of each child
  subagent-summary-<task_idx>-<YYYYmmdd_HHMMSS>.txt   # per-task consolidated summary (may exist
                                                      # only for the tasks that got that far)
```

Order of operations:

1. `manifest.json` — one line gives you WHO failed: `exit_reason` is `completed` for the clean
   children and `max_iterations` for the ones that died mid-work. Do not guess from file presence.
2. The surviving children's JSONs in the workspace (`recon/agents/S*.json`) — read the structure, not
   the prose: `scope`, `verdict_per_item[]`, `findings[]`, `checked_and_clean[]`, `unknowns[]`.
3. `task-<i>.log` for each dead child — the transcript contains its measurements, the test names it
   wrote, the paths it produced, and often most of its conclusion, even though the JSON is absent.
   Extract the tail first (the last ~6 KB usually holds the findings-bearing tool output) and only
   page back if a number needs its provenance.
4. The workspace artefacts the dead child left: its test file, its `recon/agents/<child>/` scratch
   directory, dumped JSON, disassembly text. These are reusable — the re-dispatched agent should be
   told about them explicitly so it does not re-derive from zero.

Re-dispatch ONLY the tracks that failed, and hand each new child the predecessor's thread ("what it
was investigating when it stopped, where its artefacts are, what it had already measured").

## 3. The predecessor's failing test file is NOT a finding

Dead children leave half-finished harnesses that fail for harness reasons. On Sato the red
`test_S5_D_crossMarketExecuted` failure was a missing `approve`/`transferFrom` allowance in the
agent's own mocker, not a protocol defect. So: before trusting, fixing, or reporting any number from
a predecessor's test file, run it, read the failure REASON, and separate "the protocol said no" from
"my mocker is wrong". Some failures are the RPC (see references/fork-test-rpc-reliability.md) and
some are the harness; neither belongs in the findings list.

## 4. Dispatch-time discipline that makes the next interruption survivable

Put these lines in every audit child's brief:

- "Write your deliverable JSON at PATH FIRST (skeleton + keys), then update it after EACH verified
  item. Do not wait until the end." — this is the single change that decides whether an interrupted
  sweep has to be redone or merely consolidated.
- "Your final message must carry the key numbers and verdicts (<=25 lines): the orchestrator sees
  ONLY that message, not your transcript."
- "If neither the deliverable nor your final message can be completed, write what you have into the
  deliverable and stop" — partial-but-on-disk beats complete-but-lost.
- "Run your own test file only (`--match-path`); add `--skip test/<sibling>.t.sol>` if a sibling
  breaks compilation; never edit a sibling's file."
- "Every quoted number needs the command, the pinned fork block and the endpoint that produced it."
- "An RPC-caused failure (429 / Max retries / database error) is not a finding: re-run on another
  endpoint, else record UNKNOWN with the reason."

## 5. Reconstruction order for the orchestrator (state first, then findings)

1. Re-establish the live facts BEFORE reading anyone's conclusions: current block number and the
   protocol's key state (for Sato: `ethCum`, `totalMintedFair`, `totalSupply`, hook balance) read
   fresh, plus the gap re-computed in exact decimal. Two days of history can move the numbers
   substantially — and a fix or an upgrade can invalidate the whole sweep.
2. Re-run the proven finding's PoC suite yourself (not the child's self-report). On Sato the S-01
   suite was re-run green at a new block, which also produced genuinely NEW evidence: the protocol
   had been net-redeeming for two days and the gap had stayed pinned, i.e. an independent
   confirmation of the sell-preservation law over a period the original write-up never covered.
3. Only then fold children's results into the catalogue, marking each claim
   `[ORCHESTRATOR-VERIFIED]` vs agent-reported, and re-checking anything a child asserts about a
   number you can read cheaply yourself.
4. Reconcile finding IDs before publishing: dead-and-re-dispatched children renumber, and children
   label their own findings inconsistently (`S-02` in one file, `S2-01` in another, a third child
   reusing an ID for a different issue). The catalogue's index is the only numbering that counts.
5. Note which deliverables already exist and were untouched by the interruption (on Sato:
   `FINDINGS_MASTER.md`, `FINDING_S01_*.md`, `HUNT_LOG.md`, `DISCLOSURE/`) so the resume updates
   them instead of creating parallel files.

## 6. The OTHER kill mode: instant fleet death on HTTP 429 (2026-09-26)

Different in kind from §1, and it needs a different response. Measured on the Tori audit: **6 audit
children dispatched in one batch; 3 died at ~10s on their FIRST API call** with
`API call failed after 3 retries: HTTP 429: Fair-use limit` — before reading a single file. The other
3 proceeded normally.

What changes:

- **§2's archaeology does not apply.** A 429-dead child leaves exactly one transcript line
  (`final | status=completed duration=8.69s summary: API call failed after 3 retries: HTTP 429`) and
  nothing else — no deliverable, no scratch dir, no partial measurement. Do not spend a recovery pass
  hunting for work that was never done; that is the §1 failure mode being misapplied.
- **A child that dies at 10s leaves an EMPTY SURFACE, so the orchestrator owns it.** Read those
  contracts yourself. Re-dispatching immediately burns the same budget that just refused, and can
  strand the children that are still running.
- **Size the fleet to the limit, not to the lens count.** "One subagent per lens" is the doctrine, and
  it is correct until the provider rate-limits a burst. Then launch in WAVES (3, then 3) rather than
  6–10 at once, and prefer FEWER, LARGER children while the limit is tight.
- **A 429 is infrastructure, never evidence about the target** — same classification rule as the RPC
  failures in `references/fork-test-rpc-reliability.md`. A lens that never ran is a documented
  `coverage_gap` in the spec; it is not a `no_finding`, and it must never be counted as one.
- Corollary for the orchestrator's own time: with 3 of 6 surfaces unowned, the correct move is to keep
  working (read, measure on-chain, write kills) and let the survivors land — not to idle waiting for a
  consolidated result that is already known to be incomplete.
