# How findings were found, proved and resolved — 23,625-finding corpus, second pass (2026-10-05)

Source: `Zaevlad/audit-findings-dataset` (same file as `corpus-severity-density-23k.md`; that note measured
severity density only). This pass read the **PoC and fix columns** of the 1,479 High/Critical rows whose
`bug_poc` is >300 chars, plus 28 hand-read top-weight cases across 8 bug classes. Reload with
`uv run --with pandas --with pyarrow` (no system Python; set `PYTHONUTF8=1`, the cp1252 console crashes on U+2011).

**Limits.** Contest data. No fork receipts, no tx hashes. Resolution is NOT a column: it appears only as judge/
sponsor text inside `bug_rec`/`bug_desc` (~10% of rows). Regex stats below are coarse.

## 1. Anatomy of a High/Critical write-up that survived

1. **Title = who does what to whose funds.** Top Critical titles: "X is unrestricted leading to free purchases",
   "Anyone can ...", "... allows draining of ...", "User can steal vault funds by sequencing deposit, rebase,
   redeem". Mechanism names (reentrancy, rounding) rarely lead a Critical title; the consequence does.
2. **Description** = quote the exact function (file#line), then the one-line flaw, then the impact sentence
   with a number or a victim ("purchase all remaining tokens for free", "up to 26x the yield").
3. **PoC** = either a runnable test pasted into an existing suite (`test_<finding>()`, names the file to put it
   in, names the `forge test --mt` line) or a numbered attack flow when the bug is a missing check.
4. **Fix** = smallest diff that restores the invariant (AND to OR; `external` to `internal`; add the one
   `require(order.initPosId == initPosId)` copied from the sibling function; decrement the forgotten variable).

## 2. PoC craft — measured on the 1,479 real PoCs

| Trait | Share | Lesson |
|---|---|---|
| Foundry `function test*` | 44% | JS/Hardhat 12%. Foundry wins. |
| `vm.prank/startPrank` | 34% | Attacker is a pranked EOA unless a callback is the bug. |
| asserts / `expectRevert` | 32% / 12% | DoS or access bug is proved by `expectRevert` on the victim call. |
| before/after variables | 42% | Show victim delta AND attacker delta. |
| `console.log` | 22% | Prints the numbers the report quotes. |
| fork (`createSelectFork`) | 2% | Contest PoCs run on mocks. **A fork PoC is a real differentiator for bounty.** |
| dedicated attacker contract | 3% | Only for callback bugs: `onERC721Received` bad selector, malicious ERC4626 vault, malicious hook, malicious allowlist. |
| fuzz | <1% | Almost never. Do not wait for a fuzzer to give the proof. |
| shows `forge test` run + output | 13% / 9% | The `[FAIL. Reason: ...]` line with numbers is the cheap, convincing form. |

(One probe, "no vm" share, was a broken regex and is discarded.)

**PoC shapes by class (each seen in a High/Critical):**
- *Missing access control:* second EOA (Bob) calls the function on Alice's object; assert Alice's object changed
  (`updateOrder` on another user's order). Prove with state diff, not a revert.
- *Unrestricted setter on a trust anchor:* attacker deploys a contract that answers `true` (`MaliciousAllowlist.isSigner`),
  sets it, then forges the privileged signature. Trust-anchor setters (allowlist, oracle, signer, hook) are where Critical lives.
- *Callback / push-payment DoS:* attacker contract returns a wrong selector; test asserts the victim's liquidation
  or settlement reverts. Fix class is pull over push.
- *Rounding / first-depositor:* 1 wei mint, direct donation, victim deposit gets 0 shares; print shares. Fix:
  dead shares to `address(0)` plus `require(shares != 0)`.
- *Accounting desync:* balances written as `A`, `A + profit`, `A + profit - B`; the report walks the variables
  line by line and shows the branch (`profit <= B` treated as loss, no fee). No contract needed.
- *Wrong formula / scaling:* `assertEq` against the independently computed value; the failing line is the proof
  (`50000000000 != 20000000000000`). Direct vs indirect route comparison (USDC/USD vs USDC/ETH x ETH/USD) is a
  strong oracle-decimals PoC.
- *Time-dependent underflow:* `advanceTimes` past the auction window so interest exceeds the bid, then
  `vm.expectRevert(stdError.arithmeticError)` on the final settle call.
- *Signature gaps:* list the signed fields next to the fields the function consumes; the diff is the bug
  (`from_chain`, chain id, contract address, nonce, deadline missing). Accepted without a run.

## 3. How the bugs were found (discovery moves visible in the text)

1. **Sibling diff.** Same family, one omits the check (`cancelOrder` checks `initPosId`, `updateOrder` does not).
2. **Reuse of a global.** Two features share one guard/flag/slot (BunniHub transient reentrancy slot reused by
   `lockForRebalance`/`unlockForRebalance`): a hostile participant flips shared state of unrelated pools.
3. **Coupled variables.** One function updates A, forgets B (`undeploy` forgot `_deployedAmount`; `release()`
   forgot `userTotalStaked`; repay burns shares but borrow rate used burnt, not remaining, shares).
4. **Applied twice.** Factor/fee multiplied by caller and callee (`amount` twice; deleverage factor twice).
   Grep a fee or factor symbol across the whole call chain and count applications.
5. **Sign/operator typo.** `+` for `-` in capacity, `&&` for `||`, inverted Merkle `require(!verify())`.
6. **Spec promised it.** Tokens with token/ETH but no token/USD feed were in contest scope but mishandled
   decimals: read the README's supported-asset list, then run each asset through the math.
7. **Unit mismatch.** Positive and negative balances on different scales; health math ignores decimals.
8. **Chain-halting loops.** Unmetered iteration in begin/end-block hooks; attacker pays gas once, chain pays always.
9. **Standards edges.** ERC-6492 side effects, ERC-4626 inflation, EIP-712 domain with mutable token name,
   `safeTransferFrom` callbacks, `selfdestruct` in a sandbox, calls to non-existent token addresses succeeding.

## 4. How they were resolved — and why some were not

Fix shapes seen (template for the recommendation): add the sibling's check; flip the operator; make the setter
`internal` and expose it through an owner wrapper; decrement the forgotten variable; mint dead shares to
`address(0)`; per-pool not global guard, hooks constrained to the canonical implementation; pull-over-push for
NFT/ETH returns; include `chainid`, contract, nonce, deadline and every consumed parameter in the signed message;
scale through one helper and compare against a direct oracle.

**Judge/sponsor language that decided severity:**
- *Kept/upgraded High:* "Math is incorrect · based on intended usage · impact over an order of magnitude ·
  principal is impacted, not just yield." Principal loss plus wrong math is High.
- *Kept High on invariant:* broken accounting invariant (`userTotalStaked` below intended) causing user loss.
- *Downgraded or rejected:* "by design / we knew this flaw"; "rare, and if it happens we change config";
  "pool quality is filtered by our frontend"; "if Flan were meant to target 1:1 I'd accept it" (documented peg
  assumption defeated a flash-loan manipulation claim); "acknowledged, will not fix at contract level".
- *Scope death:* bug in older code fixed later is out of scope unless the fix is incomplete AND the sponsor
  intended the fix. Check whether HEAD already fixed it (G2 changelog).
- *"Provide a PoC showing a veritable exploit case":* sponsor reply to a rounding claim with no demonstrated
  extraction. Precision claim without profit is Low/Informational.
- *Admin-key "trust issue"* appears as High in some corpora; not reportable on bounty (G6).

## 5. What to change in our own passes

1. In every PoC for a missing-check or setter bug, name attacker and victim; print both balances/state fields
   before and after; attach the failing or passing line.
2. For every external function family, emit the **guard matrix** (rows = functions, columns = guards) before
   reading bodies. Flag the minority row.
3. For every shared guard/slot/flag/index, list every writer and ask whether a hostile external party can drive it.
4. For every fee/factor/scaling symbol, grep all uses along the call path and count applications.
5. For every setter on a trust anchor (allowlist, oracle, signer, hook, validator), check who can call it first.
6. Before writing a Critical, answer the judge test: principal lost? math wrong? outside documented intent?
   order of magnitude? If "outside intent" is no, expect a downgrade.
7. Write the recommendation as the smallest diff; sponsors merge those.
8. Bounty premium: a fork PoC against mainnet state beats the ~98% of contest PoCs that run only on mocks.
