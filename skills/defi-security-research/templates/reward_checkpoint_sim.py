#!/usr/bin/env python
"""
Epoch-checkpointed Reward.sol state simulator (ve(3,3)/Solidly-family audits).

Validated 2026-09 against a live campaign: reproduces the mid-epoch zero-checkpoint
forfeiture family (permissionless poke/reset, same-block transfer guard, managed-exit)
with all assertions passing. Model the REAL semantics and assert the control case
before trusting attack output:
  - _writeCheckpoint OVERWRITES the slot when the last checkpoint is in the same epoch
  - earned() sums COMPLETED epochs since epochStart(lastEarn), each epoch using the LAST
    checkpoint at/before epoch end (so a mid-epoch zero checkpoint wipes the whole bucket)
  - supply checkpoints overwrite the same-epoch slot too
  - _withdraw leaves lastEarn and prior-epoch history intact
Tune b/S/R_E to the target's live anchors (voting weight, reward-contract supply, per-epoch
fee+bribe bucket).
"""

WEEK = 7 * 86400
HOUR = 3600


def epoch_start(t):
    return t - (t % WEEK)


class Reward:
    """Per-epoch buckets + checkpointed balances (Velodrome/Aerodrome Reward.sol)."""

    def __init__(self):
        self.totalSupply = 0
        self.balanceOf = {}
        self.cps = {}                # tokenId -> [(ts, balance)]
        self.supply_cps = []         # [(ts, totalSupply)]
        self.tokenRewardsPerEpoch = {}  # epochStart -> amount
        self.lastEarn = {}           # tokenId -> ts

    def _write_checkpoint(self, token_id, balance, now):
        cps = self.cps.setdefault(token_id, [])
        if cps and epoch_start(cps[-1][0]) == epoch_start(now):
            cps[-1] = (now, balance)      # same epoch: OVERWRITE
        else:
            cps.append((now, balance))

    def _write_supply_checkpoint(self, now):
        if self.supply_cps and epoch_start(self.supply_cps[-1][0]) == epoch_start(now):
            self.supply_cps[-1] = (now, self.totalSupply)
        else:
            self.supply_cps.append((now, self.totalSupply))

    def prior_balance_index(self, token_id, ts):
        cps = self.cps.get(token_id, [])
        if not cps:
            return 0
        if cps[-1][0] <= ts:
            return len(cps) - 1
        if cps[0][0] > ts:
            return 0
        lo, hi = 0, len(cps) - 1
        while hi > lo:
            mid = hi - (hi - lo) // 2
            if cps[mid][0] == ts:
                return mid
            if cps[mid][0] < ts:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def prior_supply_index(self, ts):
        if not self.supply_cps:
            return 0
        if self.supply_cps[-1][0] <= ts:
            return len(self.supply_cps) - 1
        lo, hi = 0, len(self.supply_cps) - 1
        while hi > lo:
            mid = hi - (hi - lo) // 2
            if self.supply_cps[mid][0] == ts:
                return mid
            if self.supply_cps[mid][0] < ts:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def deposit(self, amount, token_id, now):
        self.totalSupply += amount
        self.balanceOf[token_id] = self.balanceOf.get(token_id, 0) + amount
        self._write_checkpoint(token_id, self.balanceOf[token_id], now)
        self._write_supply_checkpoint(now)

    def withdraw(self, amount, token_id, now):
        self.totalSupply -= amount
        self.balanceOf[token_id] -= amount
        self._write_checkpoint(token_id, self.balanceOf[token_id], now)
        self._write_supply_checkpoint(now)

    def notify(self, amount, now):
        e = epoch_start(now)
        self.tokenRewardsPerEpoch[e] = self.tokenRewardsPerEpoch.get(e, 0) + amount

    def earned(self, token_id, now):
        if token_id not in self.cps or not self.cps[token_id]:
            return 0
        reward = 0
        supply = 1
        curr_ts = epoch_start(self.lastEarn.get(token_id, 0))
        idx = self.prior_balance_index(token_id, curr_ts)
        cp0 = self.cps[token_id][idx]
        curr_ts = max(curr_ts, epoch_start(cp0[0]))
        num_epochs = (epoch_start(now) - curr_ts) // WEEK
        for _ in range(num_epochs):
            idx = self.prior_balance_index(token_id, curr_ts + WEEK - 1)
            cp0 = self.cps[token_id][idx]
            sidx = self.prior_supply_index(curr_ts + WEEK - 1)
            supply = max(self.supply_cps[sidx][1], 1)
            reward += (cp0[1] * self.tokenRewardsPerEpoch.get(curr_ts, 0)) // supply
            curr_ts += WEEK
        return reward

    def claim(self, token_id, now):
        r = self.earned(token_id, now)
        self.lastEarn[token_id] = now
        return r


def build(b, S, R_E):
    """Victim holds votes b since E-1 (standing, never re-votes); other voter holds S-b from
    epoch-E start (epoch-E supply checkpoint = S); E-1 and E buckets each = R_E."""
    t0 = 1_788_393_600  # arbitrary epoch boundary
    R = Reward()
    R.notify(R_E, t0 - WEEK + 60)
    R.deposit(b, 7, t0 - WEEK + 2 * HOUR)   # victim voted E-1
    R.deposit(S - b, 8, t0 + HOUR)          # other voter (supply in E = S)
    R.notify(R_E, t0 + 3 * HOUR)            # epoch-E bucket fixed
    return R, t0


if __name__ == "__main__":
    b, S, R_E = 2_000_000, 10_000_000, 30_000
    expected = b * R_E // S

    R, t0 = build(b, S, R_E)
    R.claim(7, t0 + 4 * HOUR)               # victim claims E-1 cleanly
    got = R.earned(7, t0 + WEEK + 1)
    assert got == expected, f"control mismatch: {got} != {expected}"
    print(f"control (no poke): victim earns {got} for epoch E (expect {expected})")

    for day in (1, 3, 6.99):                # mid-epoch zero-balance poke / reset / managed exit
        R, t0 = build(b, S, R_E)
        R.claim(7, t0 + 4 * HOUR)
        R.withdraw(b, 7, t0 + int(day * 86400))  # Voter._reset -> Reward._withdraw
        lost = R.earned(7, t0 + WEEK + 1)
        print(f"zero-checkpoint at day {day}: victim E-bucket = {lost} (forfeited {expected})")
        assert lost == 0

    R, t0 = build(b, S, R_E)
    prev = R.claim(7, t0 + 4 * HOUR)        # prior-epoch claim BEFORE the poke
    R.withdraw(b, 7, t0 + 3 * 86400)
    assert R.earned(7, t0 + WEEK + 1) == 0
    print(f"preservation: E-1 claim before poke = {prev} (retained); post-poke E = 0 (wiped)")

    R, t0 = build(b, S, R_E)
    R.claim(7, t0 + 4 * HOUR)
    R.withdraw(b, 7, t0 + 3 * 86400)
    other = R.claim(8, t0 + WEEK + 1)       # redistribution is exactly conservative
    assert other == R_E
    print(f"redistribution: remaining holder claims {other} == notified {R_E} (conserved)")
    print("ALL ASSERTIONS PASSED")
