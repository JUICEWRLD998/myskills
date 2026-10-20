#!/usr/bin/env python
"""parity_check_immutables.py - prove a local build matches the DEPLOYED bytecode, accounting for
immutables and the CBOR metadata tail.

A naive compare fails on any contract with immutables: the Foundry artifact stores zeros where the
chain holds deploy-time values. This script reads the artifact's deployedBytecode.immutableReferences
and asserts that EVERY differing byte lies either inside an immutable range or inside the trailing
CBOR metadata block.

Usage:
    python parity_check_immutables.py <artifact.json> <address> <rpc_url>
Example:
    python parity_check_immutables.py out/SatoHook.sol/SatoHook.json 0x0000f07d... https://0xrpc.io/eth

Verdict semantics:
    "IDENTICAL"            - byte-for-byte, no differences at all
    "PARITY (immutables)"  - same length, differences confined to immutables + metadata tail
    "MISMATCH"             - anything else: the artifact is NOT the deployed code (or the wrong address)
"""
import json
import subprocess
import sys


def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
    return (r.stdout or "").strip()


def deployed_code(rpc, address):
    out = sh(["cast", "code", address, "--rpc-url", rpc])
    return out[2:] if out.startswith("0x") else out


CBOR_MARKERS = ("a2646970667358", "a264697066735822")  # a2 64 "ipfs" 58 22/20 ...


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    art_path, address, rpc = sys.argv[1], sys.argv[2], sys.argv[3]
    art = json.load(open(art_path, encoding="utf-8"))
    db = art.get("deployedBytecode") or art.get("runtimeBytecode") or {}
    local = (db.get("object") if isinstance(db, dict) else db) or ""
    local = local[2:] if local.startswith("0x") else local
    remote = deployed_code(rpc, address)

    print(f"local  runtime: {len(local)//2} bytes")
    print(f"deployed code: {len(remote)//2} bytes")
    if len(local) != len(remote):
        print("MISMATCH: lengths differ -> wrong compiler settings (viaIR? runs? evm version?) or wrong address")
        return 2
    if local.lower() == remote.lower():
        print("VERDICT: IDENTICAL")
        return 0

    ranges = []
    refs = (db.get("immutableReferences") if isinstance(db, dict) else {}) or {}
    for _, entries in refs.items():
        for e in entries:
            start = e.get("start", 0) * 2
            ranges.append((start, start + e.get("length", 32) * 2))

    total = len(local)
    # trailing CBOR metadata block: scan the last ~120 bytes for the ipfs/solc marker
    tail_start = total
    for marker in CBOR_MARKERS:
        idx = remote.lower().rfind(marker)
        if idx != -1:
            candidate = idx - 4  # the a2 64 ipfs head starts 4 hex chars (2 bytes) earlier
            tail_start = min(tail_start, max(0, candidate))
    d_imm, d_meta, d_other = 0, 0, []
    for i in range(total):
        if local[i].lower() == remote[i].lower():
            continue
        if any(a <= i < b for a, b in ranges):
            d_imm += 1
        elif i >= tail_start:
            d_meta += 1
        else:
            d_other.append(i // 2)

    print(f"differing hex chars: immutable={d_imm}  metadata-tail={d_meta}  unexplained={len(d_other)}")
    if ranges:
        print(f"immutable ranges: {len(ranges)} slots (byte offsets {ranges[0][0]//2}..{ranges[-1][1]//2})")
    if d_other:
        print(f"MISMATCH: first unexplained byte at offset {d_other[0]} -> NOT the deployed code")
        return 3
    print("VERDICT: PARITY (immutables) - executable code identical; differences are deploy-time "
          "immutable values and the metadata hash. Safe to audit this source as the live code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
