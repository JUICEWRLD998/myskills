#!/usr/bin/env python
"""dl_adapter_addrs.py <slug> [...] -- pull a protocol's contract addresses out of its
DeFiLlama TVL adapter source (github.com/DefiLlama/DefiLlama-Adapters/projects/<slug>/index.{js,ts}).

The adapter almost always contains the deployed addresses AND describes the real architecture in
comments. Validated 2026-09-10: revealed Longbow is a Morpho Blue curator (not its own lender),
HertzFlow is GMX-v2-shaped (DataStore/Reader), STRATO uses chain-native system addresses, and both
RockSolid and Syntropia run Lagoon's shared ERC-7540 vault implementation.
"""
import re, sys, urllib.request

BASE = "https://raw.githubusercontent.com/DefiLlama/DefiLlama-Adapters/main/projects/{}/{}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CHAIN_HINT = re.compile(r"chain\s*:\s*['\"]([a-zA-Z0-9_ -]+)['\"]")
ROLE = re.compile(r"(owner|pool|vault|lending|market|core|factory|router|stake|gauge|escrow|"
                  r"comptroller|controller|manager|token|treasury)\s*:\s*['\"]0x[a-fA-F0-9]{40}", re.I)


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def main():
    for slug in sys.argv[1:]:
        print("=" * 70)
        print(slug)
        src = None
        for fn in ("index.js", "index.ts", "index.jsx"):
            try:
                src = get(BASE.format(slug, fn))
                print(f"  adapter: {fn} ({len(src)} bytes)")
                break
            except Exception as e:
                print(f"  {fn}: {e}")
        if not src:
            continue
        addrs = sorted(set(re.findall(r"0x[a-fA-F0-9]{40}", src)))
        print(f"  chains in adapter: {sorted(set(CHAIN_HINT.findall(src)))}")
        print(f"  addresses ({len(addrs)}):")
        for a in addrs:
            print("   ", a)
        for m in ROLE.finditer(src):
            print("   role:", m.group(0))
        for c in re.findall(r"^\s*//\s*(.{12,160})$", src, re.M)[:5]:
            print("   //", c)


if __name__ == "__main__":
    main()
