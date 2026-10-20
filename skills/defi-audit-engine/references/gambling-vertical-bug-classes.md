# Gambling / prediction-market bug classes (2026-09-16)

Written for the v4 vertical strategy. **These are not the generic L1-L7 lenses.** They are the bug
classes that only exist in a wagering protocol, and that generalist playbooks do not cover — which is
why they are both higher-severity and less likely to be duplicated than "a guard is missing".

Pair with `defi-audit-engine` for the pass machinery and the five gates.

---

## 0. What makes this vertical worth specialist attention

- **The bankroll is the product.** Funds sit in-contract and must stay liquid, so a "small" accounting
  error is directly withdrawable.
- **The protocol is an adversary of its own users in spec terms.** Every payout direction is a decision,
  and a wrong direction is theft, not a rounding nit.
- **There is a public, adversarial, well-funded opponent who already wants the bug** — the player. This is
  unlike a lending protocol, where the threat model is a sophisticated outsider.

**The single most productive question in any wagering protocol:**

> **"Can a player construct a bet or a settlement whose EV is positive against the house, funded only by
> their own capital?"** That is the vertical's G6.

---

## 1. House-edge and payout direction (highest severity density)

The house edge is an integer/fixed-point computation, and its **direction** is the whole business model.

- **Which way does the rounding go, and who does it favour?** A payout that rounds **up** on both sides
  of a multi-leg settlement drains the bankroll one wei at a time, and the loop is cheap.
- **Is the edge applied before or after the payout cap?** `min(cap, stake*odds)` vs `min(cap, stake*odds)*0.98`
  changes solvency.
- **A "fee" that is charged to the house instead of the stake** — the L4 lens in generic form, but here it
  is usually a sign error on a multiplication.
- **Odds/price scaling across decimals.** A price with 6 decimals multiplied by a stake with 18 is the
  classic site of a 10^12 error, and it only shows up at scale.
- **Can the player choose the leg that rounds in their favour** and repeat it? A rounding bug that is
  unprofitable at one bet size is often profitable at another — fuzz the size, do not reason about one.

**Invariant to actually check:** `sum(all payouts) + house_edge == sum(all stakes)` across a closed round,
for both outcomes of every game, including the cap path.

## 2. RNG and entropy (the vertical's signature bug)

- **What seeds the randomness?** `block.prevrandao`, `blockhash`, `block.timestamp`, or a "random" value
  the caller supplies. Anything a player can influence or predict is the whole game.
- **Commit–reveal done properly?** If commit and reveal land in the **same transaction** (or the commit is
  front-runnable), the house can see the outcome before settling.
- **The reveal window.** Can the player simply **not reveal** a losing outcome and get a refund, while
  revealing winners? That is a free option against the house and is a critical, not a nit. Check the
  timeout path and who can trigger it.
- **Sequential draws.** If a game draws several numbers from one seed, can a player re-roll cheaply?
- **Operator/relayer influence.** Most of these protocols settle off-chain with a signed outcome — so the
  real question is §4, not the on-chain RNG.

## 3. Bet lifecycle: settlement ordering and races

- **Order of state updates vs. the payout transfer.** Non-reentrant alone is not enough — is the bet marked
  settled **before** value moves, and is the mark idempotent?
- **Can a bet be settled twice?** Look for a settlement flag that is set in a path that can `return` early.
  (This is `checkMessageNotUsed`'s family — and note that **the generic version of this bug is the one most
  likely to be duplicated**; the vertical-specific version is settlement racing a cash-out.)
- **Cash-out / early-exit.** The signature bug of this vertical: cash out at a favourable price **and**
  still collect the settlement. Two paths, one bet, one guard between them — or none.
- **Can a player exit after the outcome is knowable** but before settlement? That is a free option.
- **Front-running the settlement** from the mempool when the outcome is derivable from the pending tx.
- **Odds drift.** If the price is read at cash-out rather than locked at bet time, the player picks the
  better of the two.

## 4. Signature-gated settlement (where the money actually is)

Most production wagering protocols settle with an **off-chain signed outcome**, so the trust anchor is the
signature, not the RNG. Check, in this order:

- **What exactly is signed?** If the outcome hash omits the bet id, market id, or the amount, a valid
  signature for one bet settles a different one.
- **Domain separation and replay.** Is the signature bound to `address(this)` and `chainid`? Is a used
  signature **consumed** (nonce/`usedMessages`), or merely verified? — *Verified-not-consumed is the
  highest-value shape in the vertical.*
- **Who chooses the outcome, and can they equivocate?** A single signer that can publish two outcomes is a
  trust question to document, not a bug.
- **Settlement deadline.** A signed outcome with no expiry is a perpetual option against the house.

## 5. Bankroll, caps, and solvency

- **Max-payout cap vs. actual bankroll.** If the cap is a constant and the bankroll drops, a winning bet
  can exceed the balance — the payout then reverts and the bet is unpayable. **Is there a solvency path at
  all?** This is the vertical's version of insolvency and it is frequently missing.
- **Concurrent large bets.** Cap is per bet; is it also enforced on the total exposure of correlated legs?
- **Withdrawal queue vs. open exposure.** Can a bettor withdraw their stake while the bet is still live,
  or does the queue let them exit after the outcome is known?
- **First-depositor / share inflation** if the bankroll is share-tokenised (the generic L1 gauntlet
  applies — run it, it is cheap here).

## 6. Free options against the house — the classes to look for first

The vertical's characteristic exploit is **not** a drain. It is an asymmetry where the player decides
after seeing the outcome:

| Free option | Where it lives |
|---|---|
| Don't reveal a loser, take the refund | commit–reveal timeout path |
| Cash out the winner, also claim settlement | cash-out + settlement paths, one missing flag |
| Bet after the outcome is derivable | settlement derivable from pending tx / oracle |
| Re-roll until favourable | sequential draws from one seed, cheap re-entry |
| Refund on abort **and** keep the position | abort/refund path vs. state reset |
| Repeat a rounding-favourable leg | §1, at a size the audit did not try |

**Each of these is a positive-EV loop for a player funded by their own capital.** That is the bar: prove
the loop, on a fork, with real numbers, and it is a report.

---

## 7. The finding bar for this vertical

| Reject | Accept |
|---|---|
| "Rounding favours the user" | "A player repeats bet size X N times and nets $Y, house short $Y" |
| "The signature is not bound to the bet id" | "Signature for bet A settles bet B; PoC moves B's payout to the attacker" |
| "Missing nonReentrant" | "Settlement can be entered twice via cash-out; second entry pays again" |
| "RNG uses block.timestamp" | "Player predicts and wins K consecutive games in a pinned fork; house short $Y" |
| DoS, griefing, dust | **Only as a hardening note.** The headline must be theft, insolvency, or permanent freezing |

**The shape that wins:** a player-funded loop with a number attached, proved on a pinned fork of the live
protocol. That is a mechanism-shaped finding: it requires understanding the product, and no checklist
produces it.
