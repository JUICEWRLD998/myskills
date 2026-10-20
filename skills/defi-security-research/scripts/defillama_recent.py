#!/usr/bin/env python
"""Pull DeFiLlama recently-listed protocols, filter, enrich top-N via detail endpoint.

Stdlib only. Usage:
    python defillama_recent.py [--window-days 60] [--min-tvl 150000] [--enrich 45]
                              [--cache <dir>] [--out <dir>]

Prints a summary table sorted by TVL; writes candidates_enriched.json + candidates.tsv.
Notes: list endpoint has NO github/audit_links (use detail endpoint); tvl is nullable;
audits is a STRING count and unreliable -- verify independently.
"""
import argparse, datetime, json, os, sys, time, urllib.request

API_LIST = "https://api.llama.fi/protocols"
EXCL_CATS = {"Chain", "CEX", "Bridge", "Cross Chain", "Reserve Currency",
             "Liquid Staking", "Launchpad", "Gamified Mining", "Luck Games"}


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-days", type=int, default=60)
    ap.add_argument("--min-tvl", type=float, default=150_000)
    ap.add_argument("--enrich", type=int, default=45, help="top-N by TVL to enrich via detail endpoint")
    ap.add_argument("--cache", default=".", help="dir for the cached /protocols dump")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.cache, exist_ok=True)

    cache = os.path.join(a.cache, "dl_protocols.json")
    if os.path.exists(cache):
        data = json.load(open(cache, encoding="utf-8"))
        print(f"using cached list ({len(data)} protocols)", file=sys.stderr)
    else:
        print("downloading full protocol list ...", file=sys.stderr)
        data = fetch(API_LIST, timeout=240)
        json.dump(data, open(cache, "w", encoding="utf-8"))

    cutoff = time.time() - a.window_days * 86400
    recent = [p for p in data if (p.get("listedAt") or 0) >= cutoff]
    print(f"listed in last {a.window_days}d: {len(recent)}")

    cands = [p for p in recent
             if (p.get("tvl") or 0) >= a.min_tvl
             and (p.get("category") or "") not in EXCL_CATS]
    cands.sort(key=lambda p: p.get("tvl") or 0, reverse=True)
    print(f"candidates (tvl>={a.min_tvl:,.0f}): {len(cands)}")

    rows = []
    for p in cands[: a.enrich]:
        try:
            det = fetch(f"https://api.llama.fi/protocol/{p['slug']}")
        except Exception as e:
            det = {"slug": p["slug"], "error": str(e)}
        rows.append({
            "name": p["name"], "slug": p["slug"], "category": p["category"],
            "chains": p.get("chains"), "tvl": round(p.get("tvl") or 0),
            "change_7d": p.get("change_7d"),
            "listed_date": datetime.datetime.utcfromtimestamp(p.get("listedAt") or 0).strftime("%Y-%m-%d"),
            "url": p.get("url"), "description": (p.get("description") or "")[:200],
            "audits_dl_string": p.get("audits"), "audit_links": det.get("audit_links"),
            "github": det.get("github"), "forkedFrom": det.get("forkedFrom"),
            "detail_error": det.get("error"),
        })
        time.sleep(0.3)

    out_json = os.path.join(a.out, "candidates_enriched.json")
    json.dump(rows, open(out_json, "w", encoding="utf-8"), indent=1)
    with open(os.path.join(a.out, "candidates.tsv"), "w", encoding="utf-8") as f:
        f.write("listed_date\tname\tslug\tcategory\tchains\ttvl\tchange_7d\turl\n")
        for r in rows:
            f.write("\t".join(str(r[k]) for k in
                    ("listed_date", "name", "slug", "category", "chains", "tvl", "change_7d", "url")) + "\n")

    print("\n=== TOP CANDIDATES (by tvl) ===")
    for r in rows:
        gh = ",".join(r["github"]) if isinstance(r["github"], list) else (r["github"] or "-")
        al = ",".join(r["audit_links"]) if isinstance(r["audit_links"], list) else (r["audit_links"] or "-")
        print(f"{r['listed_date']} | {r['name'][:28]:28} | {str(r['category'])[:18]:18} "
              f"| ${r['tvl']:>12,} | 7d {str(r['change_7d'])} | audits={r['audits_dl_string']} "
              f"| fork={str(r['forkedFrom'] or '-')[:36]:36} | gh={gh[:44]:44} | aud={al[:40]}")
    print(f"\nenriched -> {out_json}")


if __name__ == "__main__":
    main()
