#!/usr/bin/env python3
"""Scaffold or validate a per-target audit spec.json (the state file the audit loop turns on).

Scaffold:  python new_target_spec.py --target nar.bet --chain Monad --chain-id 143 \
               --app https://nar.bet --out "C:/Users/me/Desktop/audit6/TARGETS/nar.bet/spec.json"
Validate:  python new_target_spec.py --validate "C:/Users/me/Desktop/audit6/TARGETS/nar.bet/spec.json"

Exit codes: 0 = clean, 1 = issues found (validation only), 2 = usage/IO error.
Pure stdlib, cross-platform. The template is templates/target-spec.json inside this skill, so there is
ONE source of truth for the schema.
"""
import argparse
import json
import pathlib
import sys
from datetime import date

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "templates" / "target-spec.json"
VALID_SECTION_STATUS = {"not_started", "in_progress", "closed"}


def load_template():
    if not TEMPLATE.exists():
        sys.exit(f"template not found: {TEMPLATE}")
    data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    data.pop("_README", None)
    return data


def scaffold(a):
    spec = load_template()
    spec["target"].update({"name": a.target, "app": a.app or "", "chain": a.chain or "",
                          "chain_id": a.chain_id, "opened": a.opened or date.today().isoformat()})
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"scaffolded {out}")
    print("next: fill target.contracts[] + integrations[], then sections[] (Phase 0 recon)")
    print("then Phase 0.5 TMAAR (actors/assumptions) BEFORE reading code.")
    return 0


def validate(path):
    p = pathlib.Path(path)
    if not p.exists():
        sys.exit(f"no such spec: {p}")
    spec = json.loads(p.read_text(encoding="utf-8"))
    issues, notes = [], []

    tgt = spec.get("target", {})
    if not tgt.get("name"):
        issues.append("target.name is empty")
    if not str(tgt.get("coverage_gap", "")).strip():
        issues.append("target.coverage_gap is empty (must name unmapped contracts, or say 'none')")
    if not tgt.get("contracts"):
        issues.append("target.contracts[] is empty (Phase 0 recon not started)")

    sections = spec.get("sections", [])
    if not sections:
        issues.append("sections[] is empty (the loop has nothing to work through)")
    for s in sections:
        sid, st = s.get("id", "?"), s.get("status", "")
        if st not in VALID_SECTION_STATUS:
            issues.append(f"section {sid}: invalid status {st!r}")
        if st == "closed" and not str(s.get("evidence", "")).strip():
            issues.append(f"section {sid}: CLOSED with empty evidence - it is OPEN")
        if st == "not_started":
            notes.append(f"section {sid} ({s.get('name','')}) not_started")

    invs = spec.get("invariants", [])
    for i in invs:
        iid = i.get("id", "?")
        if not str(i.get("check", "")).strip():
            issues.append(f"invariant {iid}: no check - an invariant with no test is a wish")
        if i.get("checked") and not str(i.get("evidence", "")).strip():
            issues.append(f"invariant {iid}: marked checked with empty evidence")
        if not i.get("checked"):
            notes.append(f"invariant {iid}: unchecked")

    for n in spec.get("never_should_happen", []):
        nid = n.get("id", "?")
        if not str(n.get("attempt", "")).strip():
            issues.append(f"never_should_happen {nid}: no fork ATTEMPT recorded")
        if not str(n.get("result", "")).strip():
            issues.append(f"never_should_happen {nid}: no result (blocked/partial/succeeded)")

    for k in ("actors", "assumptions", "value_movers", "main_functions"):
        if not spec.get(k):
            issues.append(f"{k}[] is empty")
    for a_ in spec.get("assumptions", []):
        if not str(a_.get("breaks_if", "")).strip():
            issues.append(f"assumption {a_.get('id','?')}: no breaks_if (what if it fails?)")

    st = spec.get("status", {})
    closed = sum(1 for s in sections if s.get("status") == "closed")
    print(f"spec: {tgt.get('name','<unnamed>')} | sections {closed}/{len(sections)} closed | "
          f"status.done={st.get('done')}")
    print(f"invariants {sum(1 for i in invs if i.get('checked'))}/{len(invs)} checked | "
          f"ns_h {len(spec.get('never_should_happen', []))} | passes {len(spec.get('passes', []))}")
    if notes:
        print(f"\nopen work ({len(notes)}):")
        for n in notes:
            print(f"  - {n}")
    if issues:
        print(f"\nISSUES ({len(issues)}):")
        for i in issues:
            print(f"  ! {i}")
        print("\nA target with any unreachable section or unmapped contract is a COVERAGE GAP, not clean.")
        return 1
    print("\nno issues: every closed section has evidence, every ns_h has an attempt.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validate", metavar="SPEC_JSON", help="validate an existing spec instead of scaffolding")
    ap.add_argument("--target"); ap.add_argument("--chain"); ap.add_argument("--app")
    ap.add_argument("--chain-id", type=int, default=None); ap.add_argument("--opened")
    ap.add_argument("--out", help="path to write spec.json")
    a = ap.parse_args()
    if a.validate:
        return validate(a.validate)
    if not (a.target and a.out):
        ap.error("--target and --out are required when scaffolding (or use --validate)")
    return scaffold(a)


if __name__ == "__main__":
    sys.exit(main())
