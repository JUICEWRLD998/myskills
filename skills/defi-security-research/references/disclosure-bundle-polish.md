# Disclosure-bundle polish — scrub AI slop so the report reads human (validated 2026-09 on UP33)

Final gate before sending an audit bundle (report + PoC + flattened verified sources + verification guide) to the target team. The user's bar: it must read like the researcher wrote it — dry, concrete, zero AI tells — while every fact, address, and line citation stays intact. This is a scrub-and-verify pass, NOT a rewrite. Content was already ~90% human; the slop was texture, not substance.

## What reads as AI slop in audit prose (word-list scans MISS most of it)
Buzzword scans (delve / landscape / leverage / robust / seamless…) come back clean on good content. The tells are texture:

- Mid-sentence em-dash appositions: "…destroy the claim — regardless of when the poke lands", "rather than appending — `Reward.sol` lines 123–137". KEEP em-dashes in headings ("## 3. Finding X — …") and "label — description" bullets (normal report typography). KILL the prose ones with commas / semicolons / periods.
- Polite filler: "for the team's convenience", "the team may wish to", "may wish to publish and verify". Replace with concrete statements ("Publishing and source-verifying it would bring it within reach of outside review.").
- Parenthetical noise in headings: "### 2.2 Source-verification basis (important)", "## 5. Other observations (no action required, for completeness)" → plain headings, qualifier moves into the body.
- Pseudo-precision: "**High** (≈0.95)". Keep the qualitative label + the evidence sentence, drop the fake-looking decimal.
- Template phrase repetition: "Practical economic materiality at current scale" ×3-4 → vary ("Economic materiality today", "at current pot scale").
- Arrow-chain sentences: "Reconnaissance → threat model → invariant analysis → … → census" → plain prose (commas + full stop). (Fine to KEEP compact → inside tracking lists like prior-audit item notes.)
- Echo/doubled phrasing: "…without trusting the researcher. Nothing below requires trusting this bundle…" — same idea twice in adjacent sentences.
- Sentence-adverb / bullet-prefix filler: "additionally", "more importantly,", "thereby", "Overall:" → "also", "above all" or drop, "That destroys", "Net:".
- Mid-sentence emphasis bolds on function words (not, both, none, only, entire) and on numbers ("**651 deposits / 298 withdrawals**"). Bold count dropped 52 → 31 spans on the UP33 report. KEEP structural bolds: severity ratings, finding IDs, "Vector (a)" lead-ins, list labels ("Loss type:", "Scale:", "Attack-enabling property:", "Cap-controller opacity:"), table field labels, guide step labels ("**Census:**").
- Register drift: "custom delta" → "custom addition"; italic *true*/*last*/*next* emphasis → plain; "structurally excluded" → "excluded by construction" when the word repeats.

## Keep — this reads human, do NOT touch
Census numbers, USD estimates, chain IDs, addresses, line-range cites, code fences, honest qualitative confidence with its reasoning, one deliberate italic for rhetorical contrast (e.g. "the flaw is *who* can trigger it, and *when*").

## Workflow
1. Inventory: unzip -l the deliverable; confirm zip contents == source folder (folder is authoritative; the zip gets rebuilt at the end anyway).
2. Scan in Python (execute_code), NOT giant terminal grep -E alternation one-liners — the Hermes shell parser blocks oversized inline payloads (BLOCKED hardline). Two pattern lists: (A) buzzwords, (B) texture markers incl. em/en dash counts, bold-span dump with line + context to classify structural-vs-emphasis. Regex gotcha: count bold spans with re.escape('**') + r'[^*\n]+' + re.escape('**'); a raw '**' in the pattern raises "nothing to repeat".
3. Edit with exact fixed-string replacements in Python; assert text.count(old) == 1 per edit and report (label, count) misses — wrap-guess mismatches happen on multi-line strings, so re-read the exact lines and retry just those few. Do replacements across several lines freely (wraps are cosmetic in markdown).
4. Verify after editing: re-run residual scan (must be clean except deliberately kept items); cite/address integrity check — every line-range cite, address, finding ID, headline number must still be present; artifact scan (stray '** **', doubled spaces, odd backtick counts per line — expected inside ``` fences and table cells); read the edited regions for flow.
5. Re-run any PoC the report quotes — its output must still match the report's abridged block.
6. Rebuild the zip from the folder (delete stale archive first; flat arcname = basename only, ZIP_DEFLATED), then verify: namelist == folder listing, SHA256 of each entry == disk file, testzip() clean.

Discipline: prose-only edits; never touch code fences, addresses, line cites, or numbers. Report the deliverable path and list the judgment calls you made (dropped confidence decimals, renamed headings) so the user can veto cheaply — this user decides next steps himself.

## Tooling notes
- Big text-pattern scans: Python in execute_code beats terminal grep. Output per line (L# + [pattern] + snippet) so hits are auditable.
- Residual scans double as regression tests: keep the pattern list from step 2, re-run after edits, expect zero non-deliberate hits.
- Zip rebuild via python zipfile is portable on this Windows host (no `zip` binary needed).
