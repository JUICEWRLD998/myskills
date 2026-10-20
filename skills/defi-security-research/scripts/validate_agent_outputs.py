#!/usr/bin/env python
"""validate_agent_outputs.py <recon_dir> [--keys k1,k2,...]

Gate every subagent deliverable BEFORE aggregating/scoring. Checks each agents/G<N>.json in the
campaign dir: parses, is a JSON list, and carries the required keys per record. Exits 1 if any file
fails, so it can gate a pipeline. Also reports the total protocol count so you can compare against
what you dispatched ("all N accounted for") instead of assuming.

Why this exists: a child can report success while a write was refused (JSON syntax), and helper
files (G3_bs.json, *_pools.json) live in the same directory - a naive glob('agents/*.json') picks
them up and breaks the aggregation.

Usage: python validate_agent_outputs.py C:/Users/me/Desktop/audit3/recon
"""
import json, os, sys

DEFAULT_KEYS = ["slug", "name", "chain", "solidity_confirmed", "chain_is_evm_forkable",
                "source_verified_all_fund_contracts", "fund_facing_contracts", "audits",
                "audit_gap_note", "custody_of_funds", "custom_logic",
                "loss_of_funds_hypotheses", "verdict", "verdict_reason"]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    base = sys.argv[1].rstrip("/")
    keys = DEFAULT_KEYS
    if "--keys" in sys.argv:
        keys = sys.argv[sys.argv.index("--keys") + 1].split(",")
    agents = os.path.join(base, "agents")
    files = sorted(f for f in os.listdir(agents)
                   if f.endswith(".json") and f[0] == "G" and f[1:-5].isdigit())
    if not files:
        print(f"NO agent deliverables found in {agents}")
        return 1
    total, bad, verdicts = 0, 0, {}
    for f in files:
        p = os.path.join(agents, f)
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"  {f}: INVALID JSON -> {e}")
            bad += 1
            continue
        if not isinstance(d, list):
            print(f"  {f}: not a list ({type(d).__name__})")
            bad += 1
            continue
        total += len(d)
        issues = []
        for x in d:
            miss = [k for k in keys if k not in x]
            if miss:
                issues.append(f"{x.get('slug')}: missing {miss}")
            v = str(x.get("verdict", "?")).upper()
            verdicts[v] = verdicts.get(v, 0) + 1
        print(f"  {f}: OK, {len(d)} protocols, {os.path.getsize(p)}B"
              + (f" | SCHEMA GAPS: {issues}" if issues else " | schema complete"))
        if issues:
            bad += 1
    print(f"\ntotal protocols: {total} | verdicts: {verdicts} | files with problems: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
