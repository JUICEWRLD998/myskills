#!/usr/bin/env python
"""build_findings_catalogue.py <recon_dir> [--out FILE]

Emit the user-facing ONE-FILE catalogue for a verification pass, straight from the subagents'
agents/G*.json plus the campaign metadata. Never re-type findings by hand: rebuild the catalogue
after every correction so the file and the JSONs cannot drift apart.

Reads (all optional except the first):
  agents/G*.json      required - protocol records (see brief: slug..verdict_reason)
  candidates_*.json   optional - metadata: evm_tvl, category, age_days, listed_date, url, description
  dq_ledger.json      optional - per-slug killed_by + orchestrator_recheck/orchestrator_note stamps
  overrides.json      optional - orchestrator facts that beat an agent report
  scores_*.json       optional - rubric output ({'ranked':[{'slug','score'}], ...})

Structure: header/how-to-read -> INDEX (index order != ranking order; a TOP10 map adds the rank)
-> full detail on survivors -> rejections with reasons -> appendix (funnel, artefacts, caveats).

Usage: python build_findings_catalogue.py C:/Users/me/Desktop/audit3/recon \
         --out C:/Users/me/Desktop/audit3/ALL_FINDINGS_R2.md
"""
import json, os, sys, textwrap

ORDER = {"STRONG": 0, "MAYBE": 1, "REJECT": 2}


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def find(base, prefix, default):
    for f in sorted(os.listdir(base)):
        if f.startswith(prefix) and f.endswith(".json"):
            return load(os.path.join(base, f), default)
    return default


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    base = sys.argv[1].rstrip("/")
    out = (sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv
           else os.path.join(base, "ALL_FINDINGS.md"))

    meta = {r["slug"]: r for r in find(base, "candidates", []) if isinstance(r, dict) and r.get("slug")}
    ledger = load(os.path.join(base, "dq_ledger.json"), {})
    overrides = load(os.path.join(base, "overrides.json"), {})
    sc = find(base, "scores", {}) or {}
    score_by = {r["slug"]: r for r in (sc.get("ranked") or []) if r.get("slug")}

    agents = os.path.join(base, "agents")
    records = []
    for f in sorted(os.listdir(agents)):
        if not (f.endswith(".json") and f[0] == "G" and f[1:-5].isdigit()):
            continue
        for x in load(os.path.join(agents, f), []):
            x["_group"] = f[:-5]
            records.append(x)
    if not records:
        print("no protocol records found under agents/")
        return 1

    records.sort(key=lambda x: (ORDER.get(str(x.get("verdict", "MAYBE")).upper(), 1),
                                -(meta.get(x.get("slug"), {}).get("evm_tvl") or 0)))

    def g(x, *keys, default="UNKNOWN"):
        for k in keys:
            v = x.get(k)
            if v not in (None, "", [], "UNKNOWN", "unknown"):
                return v
        return default

    def wrap(s, ind=""):
        return "\n".join(textwrap.wrap(str(s), 112, subsequent_indent=ind)) if s else ""

    L = []
    A = L.append
    sur = [x for x in records if str(x.get("verdict", "")).upper() != "REJECT"]
    rej = [x for x in records if str(x.get("verdict", "")).upper() == "REJECT"]

    A(f"# VERIFICATION PASS - ALL PROTOCOL FINDINGS ({len(records)} protocols)")
    A("")
    A("HOW TO READ THIS FILE")
    A("  Structure: INDEX of every protocol, FULL DETAIL on the ones that passed the gates")
    A("             (STRONG first, then MAYBE, ordered by TVL), then the REJECTIONS with the gate")
    A("             that killed each, then method/provenance/caveats.")
    A("  Ranking:  the INDEX is grouped by verdict, NOT by preference. Index order != ranking order;")
    A("             the TOP10 column maps to the ranked report's order where applicable.")
    A("  PROVENANCE: entries carrying [ORCHESTRATOR-VERIFIED] were re-fetched by hand and confirmed")
    A("             (explorer/on-chain); everything else is the subagent's own report = a strong lead,")
    A("             not gospel. Loss-of-funds hypotheses are TEST PLANS, not findings.")
    A("")
    A("=" * 100)
    A("INDEX")
    A("=" * 100)
    A(f"{'#':>3}  {'KEY':<24} {'VERDICT':<7} {'RANK':>4} {'CHAIN':<22} {'EVM TVL':>13}  AUDITS")
    A("-" * 140)
    for n, x in enumerate(records, 1):
        slug = x.get("slug")
        m = meta.get(slug, {})
        auds = x.get("audits") or []
        astat = ("none found" if not auds else
                 f"{len(auds)}: " + ", ".join(str(a.get("firm"))[:24] for a in auds if isinstance(a, dict))[:60])
        rank = score_by.get(slug, {}).get("rank")
        A(f"{n:>3}  {str(slug)[:24]:<24} {str(x.get('verdict','?'))[:6]:<7} "
          f"{('#' + str(rank)) if rank else '-':>4} {str(g(x,'chain'))[:22]:<22} "
          f"${(m.get('evm_tvl') or 0):>12,}  {astat}")

    A("")
    A("=" * 100)
    A(f"SURVIVORS - FULL DETAIL ({len(sur)})")
    A("=" * 100)
    for x in sur:
        slug = x.get("slug")
        m = meta.get(slug, {})
        stamp = ledger.get(slug, {}).get("orchestrator_recheck")
        A("")
        A("-" * 100)
        A(f"## {x.get('name') or slug}   [{str(x.get('verdict')).upper()}]"
          + (f"   score {score_by[slug]['score']}" if slug in score_by else ""))
        A(f"  key     : {slug}   (agents/{x.get('_group')}.json)")
        A(f"  chain   : {g(x,'chain')}   category: {m.get('category') or g(x,'category')}")
        A(f"  EVM TVL : ${(m.get('evm_tvl') or 0):,}   (age {m.get('age_days')}d)")
        if m.get("url"):
            A(f"  website : {m['url']}")
        A(f"  SOLIDITY: {g(x,'solidity_confirmed')}   source verified: "
          f"{g(x,'source_verified_all_fund_contracts')}   impls verified: {g(x,'implementation_verified')}")
        for c in (x.get("fund_facing_contracts") or []):
            if isinstance(c, dict):
                A(f"     {'OK ' if c.get('verified') else 'UNV'} {c.get('address')}  "
                  f"{str(c.get('name'))[:32]:<32} {str(c.get('role'))[:100]}")
        for u in (x.get("unverified_fund_contracts") or []):
            A("  UNVERIFIED: " + wrap(u, "              "))
        A("  AUDITS  :" + ("" if x.get("audits") else " none found"))
        for a in (x.get("audits") or []):
            if isinstance(a, dict):
                A(f"     - {a.get('firm')} | {a.get('date')} | {str(a.get('scope'))[:140]}")
        A("  AUDIT GAP: " + wrap(str(x.get("audit_gap_note", ""))[:900], "             "))
        A("  CUSTODY  : " + wrap(g(x, "custody_of_funds")[:900], "             "))
        A("  OWN CODE : " + wrap(g(x, "custom_logic")[:900], "             "))
        for i, h in enumerate(x.get("loss_of_funds_hypotheses") or [], 1):
            A(f"  HYPOTHESIS {i}: " + wrap(h, "                "))
        A("  VERDICT  : " + wrap(str(x.get("verdict_reason"))[:1200], "             "))
        for u in [u for u in (x.get("evidence_urls") or []) if isinstance(u, str)][:10]:
            A("     " + u[:190])
        if stamp:
            A("  [ORCHESTRATOR-VERIFIED] " + wrap(stamp, "     "))

    A("")
    A("=" * 100)
    A(f"REJECTED / GATE-FAILED ({len(rej)}) - do not re-research")
    A("=" * 100)
    for x in rej:
        slug = x.get("slug")
        led = ledger.get(slug, {})
        A("-" * 100)
        A(f"## {x.get('name') or slug}   [REJECT]"
          + (f"   killed by: {led.get('killed_by')}" if led.get("killed_by") else ""))
        A(f"  key   : {slug}   (agents/{x.get('_group')}.json)")
        A(f"  chain : {g(x,'chain')}   TVL ${(meta.get(slug, {}).get('evm_tvl') or 0):,}")
        A("  REASON: " + wrap(str(x.get("verdict_reason"))[:1400], "          "))
        stamp = led.get("orchestrator_recheck") or led.get("orchestrator_note")
        if stamp:
            A("  [ORCHESTRATOR-VERIFIED] " + wrap(stamp, "     "))

    A("")
    A("=" * 100)
    A("APPENDIX - method, artefacts, caveats")
    A("=" * 100)
    A("  - 'UNKNOWN' means the agent could not establish it; it is not a soft 'no'.")
    A("  - Explorer 429/500 bodies look exactly like 'unverified'. Every claim that mattered was")
    A("    re-fetched with the noise gone; where a re-check changed the answer, it is noted inline.")
    A("  - PRIVATE/DRAFT reports, Drive-card entries and AI-assist reviews are attention, not coverage.")
    A("  - No exploit was attempted; all live interaction was read-only (eth_call/balanceOf/storage).")

    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"wrote {out}")
    print(f"protocols={len(records)} survivors={len(sur)} rejected={len(rej)} lines={len(L)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
