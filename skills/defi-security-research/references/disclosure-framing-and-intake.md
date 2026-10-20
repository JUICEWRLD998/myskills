# Framing + channel for a finding nobody can exploit (disclosure strategy)

Trigger: the finding is proven but NOT attacker-drainable, and the user asks the honest version of "will they take
me seriously?" / "what is the point of reporting this?". Do not answer with reassurance. Answer with the evidence
that decides it: (a) does the finding contradict the target's OWN published spec, and (b) submit through THEIR
intake form. Validated 2026-09-12 on Sato (immutable hook, 466.156 ETH permanently destroyed, no drain path).

## 1. Classify first, concede the concession in paragraph one

Say plainly which of the two the finding is: attacker-profitable, or value-destroying. Never dress the second as
an exploit — but do not let the team's "it is not exploitable" reply be a surprise either: put the concession in
the first paragraph yourself ("no path extracts this ETH, every venue/size is a net loss, capacity 0"). That
concession is what buys the rest of the report its credibility, and it is also the honest answer to the user.

## 2. Mine the target's own docs — the strongest non-exploitable claim is a spec contradiction

Read their published material (for Sato: the docs repo captured under `recon/sato-docs/`) and hunt four things:

- **Published equations that must hold.** Sato's formal-reasoning page documents forward `q(e) = K(1 - e^(-e/S))`
  and inverse `ethOutRaw = S*ln((K - q + b)/(K - q))` as THE implemented formulas. Those two are exact mutual
  inverses, so "cumulative ETH committed to the fair curve" must equal "ETH the curve owes for the whole fair
  supply" — measured on-chain they are 466.156 ETH apart. Their own equations no longer invert each other.
- **Their definition of the reserve/NAV.** Sato's Reserve Model: "curveReserveEth = balance - feesAccrued …
  represents the ETH available to back inverse-curve redemptions". Measured: the whole supply redeems at most
  520.945884 ETH, so the documented redemption backing is 1.9x the truth.
- **The public figure derived from it, and their own instruction to read it.** Their data page tells the world to
  read `curveReserveEth()` for "the reserve view used for protocol reporting", and the TVL aggregator publishes
  exactly that `eth_call` (verified in the V0 track). A wrong private number is a nit; a wrong PUBLISHED number,
  published on their instruction, is a claim they must correct.
- **Their Non-Guarantees list — check the claim is not disclaimed.** Sato disclaims market price, stable price,
  secondary liquidity, profitable minting, profitable burning, successful arbitrage, MEV, third-party routers,
  frontends, formal verification and "absence of all contract bugs" — but NOT that the reserve backs redemption.
  A claim that sits inside their guarantees and outside their disclaimers cannot be closed with "by design".

Also read their False-Positive-Analysis page so the report does not restate something they pre-rebutted, and quote
their own review checklist where it asks for exactly the class of test you ran (Sato's developer page asks
reviewers to "confirm that forward curve, inverse curve, fee accounting, reserve accounting, and supply conversion
agree under rounding and boundary cases" — we did; they do not agree by 466 ETH, not rounding).

## 3. Find their intake channel before drafting, and use their fields

Their own security policy is the highest-probability channel — it is their process, not an unsolicited DM. Sato's
`SECURITY.md` names GitHub Private Vulnerability Reporting on the docs repo and asks for: description, affected
component, reproduction steps, EXPECTED behaviour, observed behaviour, impact, suggested mitigation. "Expected"
is where the documented invariant above goes. Reformat the technical report into exactly those fields (this is a
change of shape, not of content). Submitting through a bug-bounty platform or an unsolicited DM when a documented
private-report path exists is a self-inflicted reason to be ignored.

## 4. What to ask for

Acknowledgment; a fix in the NEXT deployment (an immutable target cannot be patched — ask for the invariant test
that would have caught it, e.g. `|ethCum - ethAt(totalMintedFair)| <= 1e12 wei`); and correction of the published
figure/adapter/methodology. Do NOT open with a payout request. If they do have a program, the write-up is the
application — send it the same way either way.

## 5. Honest odds, and the fallback

State the odds plainly instead of selling: acknowledge them within a week is likely; a bounty for a non-drainable
finding is unlikely (often no program exists); a real fix means a redeploy plus a corrected public figure. If they
go quiet for 2-4 weeks, the fallback for an IMMUTABLE target is the holder advisory — plain language, verifiable
numbers, no accusation, and it says the one thing holders need (this balance can never be redeemed, and every new
buy is still destroying ~60% at entry). Keep the advisory drafted and unsent until the user decides.

## 6. Why it is worth sending even at $0

- **A timestamped, good-faith private report is protection.** If the team ever ships a migration, resync or
  withdrawal path, the stranded balance becomes a live theft target overnight; being the researcher who reported
  it first is a very different position from being one who knew and stayed quiet.
- **The artifact is the asset.** An acknowledged, reproducible, non-overclaiming write-up is what fixes "the
  platforms ignored me for months" — it is the only evidence a stranger can check. Ten unreviewed severity claims
  are worth less than one acknowledged CRITICAL with wei-exact reproduction.
- Say the counter-case too when it applies: if the user's only metric is a payout, the expected value here is near
  zero and the hours are better spent on the next target. And a small anonymous team may simply not reply — the
  cost of finding out is one form submission.

## 7. Turn the strategy into a SEND PACK (two files, not one)

When the user says "help me write it up and send it", produce two files in `DISCLOSURE/`:

- **`03_SUBMISSION.md` — paste-ready, no commentary.** A `Title field` line, then everything after a `---`
  marker is the body to paste. Body = the target's own field order (summary, affected component, steps to
  reproduce, EXPECTED, observed, impact, suggested mitigation, what I am asking for, disclosure stance,
  attachments). First screen carries the exact integers and the spec contradiction; the concession (no drain
  path, capacity 0, nothing urgent) sits in paragraph one; the ask is three cheap yes/no items; state the
  private window (e.g. 45 days) and that a plain-language holder note follows if unanswered. Include the
  read-only reproduction command that THEY can run against their own verified source in one minute.
- **`04_OUTREACH_STRATEGY.md` — the plan around it.** Verified channel (with the evidence you checked it),
  the step-by-step sending sequence, the nudge ladder (§10) with ready-to-send wording, framing do/don'ts
  (§9), the response playbook (§11), evidence hygiene (§12), honest expectations, and a hash record block
  the user fills in at send time.

Also update the bundle README index/status in the same pass — the team reads that first — and put the
numerator/denominator distinction there explicitly ("466.16 ETH = 42.84% of the balance; the 52.11% figure is
the stranded total incl. unreachable fees") so a mixed-up ratio cannot reach them.
Lead the submission with ONE finding. The rest of the report is the second message — an engagement asset and a
reason for a second conversation, not a reason to look like a scanner dump.

## 8. Verify the intake door is actually open before promising it

Do not tell the user "submit here" from the SECURITY.md text alone. Check, in this order:

1. **Account type.** `curl -s https://api.github.com/users/<account> | grep -E '"type"|"public_repos"'`.
   TRAP: if the account is `User` (not `Organization`), then `/orgs/<account>/repos` returns an EMPTY body —
   which reads exactly like "no repositories". Use `/users/<account>/repos?per_page=20` instead. On Sato the
   account was a User with 4 repos (docs, assets, and their own forks of the aggregator adapters).
2. **Is Private Vulnerability Reporting enabled?** `curl -sL https://github.com/<owner>/<repo>/security |
   grep -oiE 'report a vulnerability|security advisories|security policy'` — the literal "Report a vulnerability"
   string means an advisory can be opened. (Opening one requires being logged in; that is expected, not a block.)
3. **Scope covers the CONTRACT, not just the repo.** Read the SECURITY.md component table: Sato's listed
   SatoToken/SatoHook/SatoSwapRouter by address, which is what makes a contract finding in-scope there.
4. **Where the seven fields go** — the advisory's title + description fields, exactly as the policy asks.

Reusable probe: `scripts/check_github_intake_channel.py <owner>/<repo>` (does 1 and 2).

## 8b. The GitHub advisory form, field by field (validated 2026-09-12)

The PVR form is not a blank page: it pre-fills the description with `### Summary` / `### Details` / `### PoC` /
`### Impact`, so the paste block must be ordered to THOSE headings (the policy's seven fields map onto them:
summary→Summary; affected component + expected/observed→Details; repro→PoC; impact, mitigation and the ask after
Impact).

| UI field | What goes in it |
|---|---|
| Title | the finding as a ratio/contradiction, never a severity adjective ("…the documented curve equations no longer invert — getter reports 1.90x the ETH that can be redeemed") |
| Description | the paste block, kept between explicit `▼ PASTE FROM HERE ▼` / `▲ PASTE TO HERE ▲` markers in the local file so the user cannot mis-paste half of it |
| Ecosystem | `Other` — there is no smart-contract ecosystem. If the dropdown lacks it, leave blank; the description carries everything |
| Package name | `<Component> — <chain> contract 0x…` (e.g. `SatoHook — Ethereum mainnet contract 0x0000f07d…`) |
| Affected versions | all deployed versions + deploy block + the report's reference block + "immutable — no upgrade path" |
| Patched versions | "None on the deployed contract. A fix requires a new deployment." |
| Severity / Vector / CWE | see below |

**Severity for a non-drainable finding — pick the honest one and say why.** CVSS scores attacker impact; a
value-destruction bug has no attacker, so a maximal score reads as inflation and a strictly-scored one reads as
"not a bug". Recommended: **High** with `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:H` (= 7.4) — I:H is the
accounting state violating its own documented invariant, A:H is the reserve being permanently unavailable for its
documented purpose, AC:H is that no exploitation step exists for anyone; deliberately short of Critical. State
the alternative in the same place: the strict attacker-model vector
`CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N` = 0.0, and that leaving the selector at "Pending" for the
maintainers is also acceptable. Handing the user the reasoning (not just a value) is what makes the choice
defensible if the team disputes it. Paste the vector into the form's Calculator link to confirm the score before
submitting. CWE: `CWE-682: Incorrect Calculation` primary, `CWE-1339` optional.

**No attachment field exists.** Do not hunt for one and do not promise "attachments included". Say the pack is
available on request (zip or read-only repo invite) and that the `forge` commands in the PoC section are
everything they need to reproduce it themselves.

**Local file shape that survived contact:** section A = a paste-ready table of the simple fields (title,
ecosystem, package, affected/patched versions, severity, vector, CWE) with the severity reasoning beneath it;
section B = the description block between the markers; section C = what to do if they ask for a repo/link. Keep
the sha256 record in the STRATEGY file and recompute it after every edit to the submission file — two edits
invalidated a recorded hash in one session before it was refreshed.

## 9. Channels in order, and the no-detail rule on all of them

| Order | Channel | What may go in it |
|---|---|---|
| 1 | Their documented private intake (PVR advisory) | EVERYTHING — full report, attachments, all follow-ups in the same thread |
| 2 | A MINIMAL public issue on their repo (only if the private door is unavailable/ignored) | "I have a private security report for <component>; the policy points at advisories but I cannot open one — could you enable it or give me a contact?" No numbers, no mechanism |
| 3 | Their own socials — find them by scraping the project's own dashboard/docs HTML (`curl -sL <site> \| grep -oiE 'href="[^"]*(x\.com\|t\.me\|discord\|github)[^"]*"'`); Sato's docs repo listed none, its live dashboard served the Telegram/X/GitHub links | One line pointing at the advisory ("filed privately, could someone from the contract side pick it up?"). Never technical detail — public channels are read by other people |
| 4 | Aggregator/listing methodology (only for a wrong PUBLISHED figure, only after the private window) | "Please review this listing's methodology" — a lever, not a disclosure channel |

## 10. Nudge ladder (dates matter; keep every message in the advisory thread)

Day 0 send (pick a weekday) → +7 nudge → +14 nudge + walkthrough offer → +30 final notice naming the
publication date → +45 publish the holder advisory if there has been no substantive reply. Working wording
(keep it this short):

- **+7:** "Checking this reached the right people. Four-line version: at block N the hook reports X while the
  whole supply redeems at most Y, and your own curve equations imply those must be equal. Reproduction is one
  forge command against your verified source with a public RPC. Is this in scope for you?"
- **+14:** offer the cheapest path to engagement — walk an engineer through the two suites, or "answer any
  counter-argument with a test rather than an argument"; ask for the specific objection in writing.
- **+30 final notice:** no reply received; unless told otherwise you will publish on <date>, 45 days from
  submission; the note states the published reserve figure is 1.9x what the whole supply can redeem, contains
  no exploitation detail and no accusations, and says the report was filed privately through the policy in
  SECURITY.md; the technical pack goes to anyone who asks.

## 11. Response playbook

| Their reply | Move |
|---|---|
| "Received, reviewing" | Acknowledge briefly, then silence until the next rung. Do not chase. |
| "By design / not in scope" | Quote their own two definitions and ask the single yes/no they cannot dodge: "Do you intend to update the reserve definition (and the published figure) to reflect that this getter is not redemption backing?" That question IS the fix. |
| Disputes the math | Ask for the objection in writing; answer with the one command that settles it. Never argue prose against prose. |
| Wants the pack / wants a call | Send everything; offer to review their fix; verify identity before sending to a third party. |
| Asks for indefinite silence | Decline politely, keep the date, extend only for a concrete reason with a date. |
| Hostile or threatening | Stop private engagement, publish only the plain-language holder note, keep the record. |

## 12. Evidence hygiene

`sha256sum` the submission file BEFORE sending and record the hash + UTC time + the advisory URL in the
strategy file's hash block — that is what proves later that the version you sent is the version you hold.
No mainnet transaction was ever broadcast (say so if asked); never hand over keys, RPC endpoints or
credentials; keep the report copy immutable once sent.

## Pitfall

Do not answer the "what's the point" question from feeling. The whole answer above is checkable in the target's
captured docs in a few greps, and that is exactly why it beats reassurance: the user can read the same quotes you
are quoting.
