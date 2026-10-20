#!/usr/bin/env python
"""Pure-Python keccak-256 + 4-byte function selectors for eth_call when cast/foundry is unavailable.

Usage:
    python keccak_selectors.py "transfer(address,uint256)" "balanceOf(address)" "minter()"

Self-tests against known selectors before printing, so a wrong implementation cannot pass silently.
Note: hashlib.sha3_256 is NIST SHA3 (different padding) and OpenSSL CLI is sha3-256 too — neither
produces Ethereum keccak256. Use THIS implementation.
"""
import sys

RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
      0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
      0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
      0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
      0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
      0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
R = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56],
     [27, 20, 39, 8, 14]]
M = (1 << 64) - 1


def _rol(x, n):
    return ((x << n) | (x >> (64 - n))) & M


def _keccak_f(state):
    for rc in RC:
        C = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(0, 25, 5):
                state[x + y] ^= D[x]
        B = [0] * 25
        for x in range(5):
            for y in range(5):
                B[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(state[x + 5 * y], R[x][y])
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = B[x + 5 * y] ^ ((~B[(x + 1) % 5 + 5 * y]) & B[(x + 2) % 5 + 5 * y])
        state[0] ^= rc
    return state


def keccak256(data: bytes) -> bytes:
    rate = 136
    pad = bytearray(data)
    pad.append(0x01)
    while len(pad) % rate != rate - 1:
        pad.append(0)
    pad.append(0x80)
    st = [0] * 25
    for off in range(0, len(pad), rate):
        block = pad[off:off + rate]
        for i in range(rate // 8):
            st[i] ^= int.from_bytes(block[i * 8:(i + 1) * 8], "little")
        _keccak_f(st)
    return b"".join(x.to_bytes(8, "little") for x in st[:4])


def selector(sig: str) -> str:
    return "0x" + keccak256(sig.encode())[:4].hex()


if __name__ == "__main__":
    assert selector("transfer(address,uint256)") == "0xa9059cbb", "sel transfer"
    assert selector("balanceOf(address)") == "0x70a08231", "sel balanceOf"
    assert selector("transferFrom(address,address,uint256)") == "0x23b872dd", "sel transferFrom"
    sigs = sys.argv[1:] or ["minter()", "ve()", "governor()", "emergencyCouncil()"]
    for s in sigs:
        print(f"{s}  ->  {selector(s)}")
    print("keccak self-test OK")
