#!/usr/bin/env python
"""find_v4_pool_key.py - recover a Uniswap-v4 pool key (fee, tickSpacing, poolId) without docs.

Needed to drive the real swap path on a fork. currency0/currency1/fee are usually pinned by the hook's
own validation, so the unknown is tickSpacing.

Two modes:
  log     - decode the PoolManager's Initialize log (authoritative). Requires an ARCHIVE-capable RPC.
  probe   - brute force candidate tickSpacings against getSlot0 (no archive needed; a non-existent
            pool REVERTS WITH EMPTY DATA, so "no return" IS the negative signal).

Usage:
    python find_v4_pool_key.py log   <rpc> <block_from> <block_to> <currency0> <currency1> <hook>
    python find_v4_pool_key.py probe <rpc> <currency0> <currency1> <fee> <hook> [spacings...]
Example:
    python find_v4_pool_key.py log https://0xrpc.io/eth 25015094 25015120 \
        0x0000000000000000000000000000000000000000 0x829f4b62eebe12af653b4dd4ffc480966f7d7f09 \
        0x0000f07d2b5f1ddf3244b8780f972f306efd2888
"""
import subprocess
import sys

POOL_MANAGER = "0x000000000004444c5dc75cB358380D2e3dE08A90"
# Swap/Initialize signatures (topic0 precomputed to avoid needing keccak here)
TOPIC_INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3300374fcb9bd3d3fbb19f1"


def rpc_call(url, method, params):
    import json
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    r = subprocess.run(["curl", "-sS", "--max-time", "60", "-H", "Content-Type: application/json",
                        "-d", body, url], capture_output=True, text=True)
    try:
        return json.loads(r.stdout or "{}").get("result")
    except Exception:
        return None


def word(hexdata, i):
    return hexdata[2 + i * 64: 2 + (i + 1) * 64]


def int24(word_hex):
    v = int(word_hex, 16)
    return v - (1 << 256) if v >= (1 << 255) else v


def addr(word_hex):
    return "0x" + word_hex[-40:]


def mode_log(rpc, lo, hi, c0, c1, hook):
    logs = rpc_call(rpc, "eth_getLogs", [{
        "address": POOL_MANAGER, "fromBlock": hex(int(lo)), "toBlock": hex(int(hi)),
        "topics": [TOPIC_INITIALIZE],
    }]) or []
    print(f"{len(logs)} Initialize logs in {lo}..{hi}")
    for lg in logs:
        data = lg["data"]
        fee = int(word(data, 0), 16)
        spacing = int24(word(data, 1))
        hooks = addr(word(data, 2))
        sqrt_p = int(word(data, 3), 16)
        tick = int24(word(data, 4))
        pool_id = lg["topics"][1]
        mark = "  <== TARGET" if hooks.lower() == hook.lower() else ""
        print(f"  {pool_id}")
        print(f"     currency0={addr(lg['topics'][2])} currency1={addr(lg['topics'][3])}")
        print(f"     fee={fee} tickSpacing={spacing} hooks={hooks} sqrtPriceX96={sqrt_p} tick={tick}"
              f"  block={int(lg['blockNumber'], 16)}{mark}")
        if hooks.lower() == hook.lower():
            print("\n  USE THIS KEY:")
            print(f"    PoolKey(currency0={c0}, currency1={c1}, fee={fee}, tickSpacing={spacing}, hooks={hook})")
            print(f"    poolId = {pool_id}")
    return 0


def mode_probe(rpc, c0, c1, fee, hook, spacings):
    for sp in spacings:
        key = ("0" * 24 + c0[2:].lower()) + ("0" * 24 + c1[2:].lower()) \
              + f"{int(fee):064x}" + f"{int(sp) & (2**256 - 1):064x}" + ("0" * 24 + hook[2:].lower())
        pool_id = subprocess.run(["cast", "keccak", "0x" + key], capture_output=True, text=True).stdout.strip()
        out = subprocess.run(["cast", "call", POOL_MANAGER,
                              "getSlot0(bytes32)(uint160,int24,uint24,uint24)", pool_id,
                              "--rpc-url", rpc], capture_output=True, text=True)
        blob = (out.stdout or "") + (out.stderr or "")
        if "revert" in blob.lower() or not blob.strip() or blob.strip().startswith("0"):
            continue
        print(f"*** pool EXISTS: tickSpacing={sp} poolId={pool_id}")
        print(blob.strip())
    return 0


def main():
    if len(sys.argv) < 6:
        print(__doc__)
        return 1
    mode = sys.argv[1]
    if mode == "log":
        rpc, lo, hi, c0, c1, hook = sys.argv[2:8]
        return mode_log(rpc, lo, hi, c0, c1, hook)
    if mode == "probe":
        rpc, c0, c1, fee, hook = sys.argv[2:7]
        spacings = [int(x) for x in sys.argv[7:]] or [1, 5, 10, 30, 50, 60, 100, 200, 500, 1000, 3000]
        return mode_probe(rpc, c0, c1, fee, hook, spacings)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
