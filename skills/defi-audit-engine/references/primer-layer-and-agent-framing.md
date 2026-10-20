# The primer layer, and how to frame a hunting agent

Two peer-sourced ideas that change **how a pass is framed** rather than what it looks for. Both were
triaged and licensed on 2026-09-24; provenance and the vendored copies are at the bottom.

## 1. A PRIMER is not a checklist — load it before the pass, not during it

From `devdacian/ai-auditor-primers` (MIT), the structural distinction, in the author's own framing:

- A **checklist** is a flat list of things to verify. It is consulted *while* working.
- A **primer** is a **context-loading document for an LLM auditor**, written to be **ingested before** the
  audit so the model reasons *from* a loaded threat model instead of recalling one. It is consulted *once*,
  up front.

The primer's structure (from `base.primer.md`, v0.4, 598 lines, vendored):

```
Overview
Critical Vulnerability Patterns     ← named one-liners grouped into ~8 themed families
   state validation · signatures · precision/maths · lending/borrowing
   liquidation (incentives, DoS, calculations, fairness) · reentrancy
   slippage · oracle · concentrated liquidity · staking/rewards · auctions
Common Attack Vectors
Integration Hazards                 ← token / oracle / AMM / lending / staking / multi-chain
Audit Checklist                     ← ONE section DERIVED FROM the pattern taxonomy
Invariant Analysis                  ← the invariants + the patterns that break them
Code Analysis Approach
<personified working-relationship section>
```

**The load-bearing detail:** the checklist is a *derived artifact* at the bottom, not the document. Our
`checklist-full.md` is the inverse — a big list with the threat model implied. Both are useful and they are
not substitutes.

**How to apply it here — this is the actual change:**

1. **Write ONE primer per target, before the lens sweep.** Source it from the target's own `TMAAR.md`,
   `spec.json` (`integrations[]`, `value_movers[]`, `actors[]`) and the vertical override file. It is short —
   the base primer is 34 KB, and a target primer should be one page: the protocol's own threat model,
   the invariants, the integration hazards, and the 10-15 patterns that are *live for this codebase*.
2. **Paste the primer at the TOP of every child brief**, above the lens instructions. The point is that N
   children reason from the **same loaded model** instead of each re-deriving context and diverging. Today
   `references/pass-briefs.md` briefs a *lens*; this adds the *shared frame* over all of them.
3. **Keep class primers for repeated target types.** The source ships `amy.vault.erc4626.primer.md`
   (278 KB, v12.0 — an ERC-4626/vault specialist that has clearly been revised twelve times). That is a
   long-lived artifact for a *recurring* class, distinct from the per-target primer. If we audit a second
   and third vault, the class primer accumulates; the per-target primer does not.
4. **Specialist framing is a prompt technique, not evidence.** The source ends its primer with a personified
   working-relationship section (its own author calls this "evolve your own specialist auditor"). Using a
   persona in a child brief is legitimate prompt engineering — but it changes nothing about the gate stack,
   and a persona is never a reason to believe a claim. Keep it in the brief, keep it out of the finding.

## 2. Framing rules from a vulnerability-mining engine (Apache-2.0)

From `BradMoonUESTC/finite-monkey-engine` (the author's own design write-up, `philosophy_of_monkey_en.md`,
vendored). Four claims, each with a direct consequence for our fan-out:

**(a) Seed with an ASSERTION, not a question.** *"There is a vulnerability in this code, please find it"*
measurably outperforms *"is there a vulnerability?"* — the assertion form triggers *search*, the question
form triggers *recall of memorised classes*.
→ Use the assertion form in **hypothesis-generating** briefs. **Never in a verification or re-check brief**,
where presupposing the answer is exactly the bias the pass exists to remove (`independent-recheck-pass.md`).

**(b) The detection unit is a BUSINESS FLOW, not a function.** They parse the project to
*function* granularity (ANTLR4; they tried and rejected Slither's variable read-write extraction), then have
an LLM extract **business flows** — JSON chains of in-project function calls starting from a seed function —
and hand *those* to the detector. The stated reason: it restores the context a human has when reading a whole
contract, which function-granularity destroys.
→ This is a better `main_functions[]`/`value_movers[]` than a flat list. For an audit, emit the flow chains
explicitly in `spec.json` and give each child the chains it owns, not a file list.

**(c) The error-accumulation budget — the strongest import in this file.** At 99% accuracy per action, a
30-action chain ends at ~73%; at a realistic 60-70% per action, five actions end at ~16%. Their explicit
design goal is to *dodge* long agent chains rather than to make them reliable.
→ **Keep children short.** This is the quantitative case for our fan-out over a long single-agent pass, and
the reason to split any child whose brief implies more than roughly ten reasoning steps. It also explains a
failure mode we have hit: a child that "was working on it" for a long time and returned nothing usable.

**(d) The hypothesis cloud is finite (the "finite monkey" claim).** Their observation: ten iterations yield
about five *distinct* classes, so mining converges rather than expanding without bound.
→ Caution: this is an unverified design claim, not a measurement, and it contradicts the intuition that more
iterations always help. Treat it as a hypothesis worth testing on our own data (how many genuinely distinct
classes did successive passes actually produce?) rather than as a reason to cap passes. **Do not write it into
doctrine as a number.**

## Provenance and licences

| Artifact | Upstream | Licence | Local copy |
|---|---|---|---|
| `base.primer.md` (34 KB, v0.4) | `devdacian/ai-auditor-primers` | MIT (© 2025 Dacian) | `Desktop/audits/_vendor/` |
| `amy.vault.erc4626.primer.md` (278 KB, v12.0) | `devdacian/ai-auditor-primers` | MIT | `Desktop/audits/_vendor/` |
| `Orderbook.md` (17 KB — a real CLOB finding written up as a primer) | `devdacian/ai-auditor-primers`, authored by the peer researcher | MIT | `Desktop/audits/_vendor/` |
| `philosophy_of_monkey_en.md` (12 KB) | `BradMoonUESTC/finite-monkey-engine` | **Apache-2.0 — attribution required** | `Desktop/audits/_vendor/finite-monkey/` |

Do **not** vendor material from `ImmuneBytes-Security-Audit/Blockchain-Attack-Vectors` or
`TradMod/awesome-audits-checklists` — neither upstream ships a LICENSE file, so both are treated as
all-rights-reserved: mine the *shape* (their category axes, their follow-lists) into our own text, link the
repos, and copy nothing.

Their taxonomy does carry one design lesson worth stealing, and it is free: **bucket attack vectors by
STACK LAYER**, so chain-specific runtime vectors (Solana's account/PDA/owner-check family) get sibling buckets
instead of being mixed in under "Smart Contract Security", and **application/economics vectors**
(front-running, governance, social-engineering, phish) sit beside code-level ones in the same map. It is a
"full kill chain including the social layer" choice, and it is why that fork's Solana set is the best-organised
part of it.
