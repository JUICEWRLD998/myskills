# Pre-send submission gate (added 2026-10-11)

The last gate before a finding leaves. Modelled on `mdpsec/should-i-submit`. It runs AFTER the V2 finding
gates (G0 Reality → G1 Impact → G6 extractability → G2 Dedup → G3 Quality → G4 Reachability) and AFTER the
report is drafted, and BEFORE his send decision. It does not hunt for new bugs, broaden scope, invent impact,
or rescue a weak report with a different issue. It judges the report you already have against the program's
own brief.

## Inputs
- `report.md` — the exact, final report you intend to submit (not recon notes, not a lead).
- `brief.md` — the program's complete, current scope and rules, in the platform's own format. Do not
  summarise or reformat it. Fields the brief does not publish are recorded as `NOT STATED`, never invented.
- One finding per review. A report bundling unrelated findings is split, one folder each.

## The four verdicts
- **YES** — the report reproduces under a safe, read-only (or explicitly authorised) check, the impact is
  concrete and in scope, and no required field is missing. Send-ready.
- **NO** — do not submit. A scope miss, an unprovable claim, a duplicate, or an impact that does not hold.
- **NOT-YET** — one specific proof or repair is still needed; name it exactly and pause. Do not submit until
  that proof exists. (e.g. "PoC does not reproduce at the pinned block", "severity field required by brief is
  absent".)
- **CAN'T-DECIDE-SAFELY** — scope, access, or safety prevents an honest verdict; say so plainly.

## What it checks (distilled)
1. **Reproduces.** Run the exact supplied reproduction when safe and authorised. If the supplied proof does
   not reproduce, that is a report defect → NOT-YET or NO. The author's asserted severity is never treated as
   evidence — an untested claim is `NOT TESTED`.
2. **One root cause / one necessary chain.** Not a grab-bag. Provisional / hypothesis / "potential impact if
   confirmed" language, or impact that depends on *discovering* whether another system trusts the state, is a
   lead, not a submission.
3. **Concrete impact, in scope.** A verbose error or framework disclosure with no material impact fails.
   Impact must map to a real asset / fund movement / trust-boundary break. Confirm against `brief.md` scope.
4. **Dedup.** Already covered by the target's own prior audits, known-issues, Solodit, or the contest's
   known-issues list ⇒ NO. (This is the step that most often turns a "find" into a rejection — run it hard.)
5. **Required fields present.** Severity / CVSS / VRT / classification / title when the brief requires them —
   absent ⇒ report defect. Do not infer them from the impact description.
6. **Safety.** Only read-only or explicitly-authorised actions. Never run destructive, DoS/availability, or
   unknown-owner actions to "prove" impact. An impact provable only by a destructive action under an
   availability policy ⇒ DO NOT SUBMIT.
7. **Evidence hygiene.** No unresolved screenshot/attachment placeholders; no secrets, `.env`, credential
   exports, or researcher infrastructure in the package; no symlink / absolute-path / `..` traversal / archive
   tricks in the report folder.

## Why this is in the kit
Most rejections are triage failures, not find failures: a duplicate, an unprovable lead, or a missing field.
This gate externalises the V2 bar so a weak report never reaches the team and never costs reputation. A
NOT-YET is a cheap save; a NO is cheaper than a rejected submission. He still makes the send decision — the
gate only refuses to let an un-ready report through.
