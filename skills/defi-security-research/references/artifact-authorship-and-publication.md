# Artifact authorship, reader-facing polish, and repo visibility

Trigger: the user says any of "make sure it looks like I was the one that made the findings and reported it",
"ensure the docs are cleaner and clearer so anyone who stumbles on it knows what I audited", "review it once more
so it does not look like slop if they read it", or "do I need to make the repo public?". Validated 2026-09-12 on
Sato (name supplied by the user: Mustapha Fadhlullah).

This pass turns a working audit repo into a signed, checkable artifact. It is adjacent to
`disclosure-bundle-polish.md` (which scrubs prose texture) — run that one for the writing, this one for identity,
reader orientation and visibility.

## 1. Byline discipline

| Artifact | Attribution |
|---|---|
| README, findings catalogue, ranked report, per-finding write-up, hunt log, team-facing technical report, re-check file | `Author: <Full Name> — independent security researcher` near the top, plus "unsolicited, no relationship with the protocol team" where a stranger would wonder |
| Holder advisory (drafted FOR the team to publish) | a DRAFTER note at the bottom only ("Draft prepared by <name> (independent review); the team is free to publish it as their own"). A byline here defeats the file's purpose |
| Submission / outreach files | the byline also goes in the text the team receives (last line of the paste block), not only in the local file |

Also replace machine-shop framing with the author's: `Campaign: C:\Users\<user>\Desktop\audit<N>\` →
`Repository: this review's repository`. Ask for the name explicitly if the user has not given one — never invent a
handle and never leave artifacts unsigned.

## 2. Voice: singular in the author's own voice, impersonal in the report body

The user wrote none of the "we". Sweep for `we / our / us` and convert ONLY where the author is speaking:
`we measured` → `I measured`, `our rebuild` → `the local rebuild`, `(or ask us to)` → `(or ask the team to)`.
Leave impersonal report prose impersonal ("the hook pays out X", not "I paid out X"). Never touch quoted text,
the target's own documentation, or test/version strings. Cheap scan: one Python pass with a per-file
`Counter` over `we|our|us|orchestrator|agents?|reviewer`, print counts first, then per-line context for the
files that matter — oversized grep-alternation one-liners get the shell parser blocked.

## 3. Internal-jargon scrub (anything an outsider will read)

| Internal term | Replacement |
|---|---|
| orchestrator | the author / `independently re-verified` |
| per-agent outputs, `agent S6`, "the agents" | per-track analysis outputs, `track S6`, the analysis tracks |
| "not a self-report from the agents" | "re-derived, not taken from the analysis outputs" |
| "Verified by orchestrator" (table column) | "Independently re-verified" |
| internal numbering/labels (`AUDIT 4`, phase numbers) in prose | drop them, or keep only inside files that are clearly internal catalogues |
| absolute local paths (`C:\Users\…`, `/c/Users/…`) in prose | remove (scripts may keep theirs — see §6) |

The directory name may itself carry jargon (`recon/agents/`). Check what a rename would break first: hardcoded
paths inside committed analysis scripts are re-runnable as-is, so weigh cosmetics against reproducibility before
renaming evidence directories.

## 4. README for an outsider (the "what did I audit" question)

Order that answers it in one screen: title → byline/date/reference block → method + read-only statement → status
(reported privately where; not published) → **What was reviewed** (component/address table) → headline numbers →
findings-at-a-glance table (rank, ID, one-line, severity, fund loss, attacker-reachable) → contents map, one line
per file → reproduction commands (audit suite AND re-check suites) → "How this review was produced" (parity
method, tracks, verification passes, corrections applied) → authorship/reuse line. The question to answer first
is *what was audited, by whom, and can I check it myself*.

## 5. Repo visibility — answer it as three decisions

1. **Not needed for the report.** GitHub advisories take no attachments and no repo link; the advisory thread
   carries the evidence and the reporter's name. Do not hand over a repo link as "the disclosure".
2. **Private through the coordinated-disclosure window.** The target's own policy asks for confidentiality on
   unresolved issues, and the repo holds the PoCs plus the advisory drafts — publishing early is the opposite of
   what you told them you would do. If they want evidence: read-only collaborator invite, or a zip.
3. **Public after the window (or after acknowledgment/fix).** That is the portfolio asset that fixes "the
   platforms ignored me". If the user wants something public sooner, publish a sanitized copy (README +
   technical report + verification suites) and hold the disclosure drafts and the holder advisory back.

## 6. Pre-publication hygiene scan (run before flipping anything public)

Over `git ls-files` (not the working tree — that is what a reader receives), in Python:

* **Secrets.** `api[_-]?key|secret|private[_-]?key|mnemonic|bearer [A-Za-z0-9_-]{16,}|0x[0-9a-fA-F]{64}`.
  FALSE POSITIVES ARE THE NORM on-chain: v4 pool ids, event topic0 signature hashes and EIP-1967 storage slots
  are all 32-byte hex. Report "no secrets — the only 64-hex strings are public by design" rather than a hit list.
* **Tracked junk.** `.env/.pem/.zip/.key` and committed `__pycache__/*.pyc`. Untrack with `git rm --cached` —
  `.gitignore` does NOT apply to already-tracked files (adding the rule and re-running `git status` changes
  nothing).
* **Absolute user paths** in scripts/JSONs: cosmetic leak; count them and offer one relativize pass before
  release. Do not rewrite audit evidence scripts speculatively.
* **Build artifacts** (`out/`, `cache/`, `broadcast/`) should be ignored, not shipped.

## 7. Order of operations (what actually shipped clean)

1. Byline blocks (§1), then the voice sweep (§2), then the jargon sweep (§3).
2. Rebuild the README to the §4 skeleton.
3. Reader-facing status lines: "NOT SENT, NOT PUBLISHED", the send state, and a pointer to the strategy file.
4. Recompute the sha256 of any file about to be sent and refresh the hash record — write the record LAST (an
   earlier pass recorded a hash that two later edits invalidated).
5. Commit the polish as its own commit, so the user can revert cosmetics without touching findings.
