# Open release-policy decisions for Plan 4

Decisions that must be made **before** anything is published, recorded here so Plan 4 finds them
rather than rediscovering them. Each item needs the owner's approval, and any item that changes a
public claim needs an independent review as well.

> **Amended 2026-07-29.** This paragraph read "Nothing here is decided. Plan 4 has not opened" —
> false at this commit on both counts. Four decisions were ruled on 2026-07-29 and Plan 4 was opened
> the same day. The standing of each ruling is stated per item: decisions 1, 3 and 4 are the owner's
> calls on questions of policy and carry no separate review record; decision 2 changes a public
> claim and its wording was independently reviewed (**BLOCK**, then re-worded — see
> `evidence/plan4/reviewer_record.visibility-and-description.json`). Recorded rather than silently
> corrected: a live list whose header contradicts its own table is the defect this repository has
> spent two days removing from other documents.

This file is a live list: items are added when found and struck when decided. It is deliberately not
a dated record — see `docs/release-check-2026-07-28.md` for the check that surfaced the first item.

> ## Plan 4 is PAUSED as of 2026-07-29 — not cancelled
>
> The owner's override kept Plan 4 open on the hypothesis that only Plan 3's paperwork was missing.
> The independent close review **refuted** that hypothesis
> ([`../../evidence/plan3/reviewer_record.plan3-close.json`](../../evidence/plan3/reviewer_record.plan3-close.json)).
> Plan 4 is the release plan, and finding **O2** was a live overclaim on README, report and abstract
> surfaces — so continuing would have built release artifacts on a claim that was about to change.
>
> **Resumes when O1, O2 and O3 are discharged and Plan 3 closes on its merits.** Nothing below is
> withdrawn, and the Plan 4 work already done stands: the gate-state derivation, the privacy review,
> the link audit, decisions 1–4, and the rejection of the staged-release amendment.

> ### Known exposure, recorded and deliberately not addressed: unnamed conventions
>
> Several conventions in this repository exist **only in their implementations**, with no rule
> naming them: the reviewer-record shape (`schema_version`, `review_kind`, `verdict`, per-question
> sections), the dated-amendment form used to correct an accepted plan or ADR without rewriting it,
> and the `permitted_in`/`ALLOWED`-with-reasons pattern for mention-not-use exemptions.
>
> **This is the exact mechanism that produced B2.** The guard-the-guard convention was real,
> consistent across four modules, and unnamed — so the fifth scanning check shipped without it and
> nothing noticed until it hid a red suite. **A convention that lives in N implementations and no
> rule is one new file away from being broken**, and each of the three above is currently in that
> state.
>
> **A fourth, measured and still latent:** the three filesystem walks in the test suite carry
> **three different skip lists**, and the newest carries the narrowest. Divergence from `.gitignore`
> is currently zero — 203 files against 202, differing only by a reviewer's probe — so nothing is
> wrong today.
>
> **The live consequence, in one line: the suite's scope now depends on what happens to be on the
> machine, and one of the three walks is guarded against that while two are not.**
> `test_the_markdown_scan_matches_the_index` closes it for the markdown walk by asserting nothing
> gitignored is included; `test_internal_paths.py` and `test_withdrawn_assertions.py` are unguarded.
>
> **Two of the three walks still carry a floor, and it is worse than the one that was replaced.**
> `test_internal_paths.py` and `test_withdrawn_assertions.py` bound at `> 50` against **202** files —
> **75% headroom**, against the 51% the floor rule was derived from. Each of the three walks now has
> exactly one of the two guards; **none has both.**
>
> **The deferral rule, stated because "Plan 4 is paused" does not distinguish these from what has
> been changed.** Three commits of test changes have landed during the pause, so the pause alone is
> not the criterion. The criterion actually being applied: **blocking findings are fixed in the round
> that raises them; non-blocking findings are recorded and deferred.** That fits every commit in this
> sequence, and it is why the Q1 kind-probe was added immediately and these two floors were not.
> Recorded here so it is a known exposure rather than a discovery waiting to happen, and so whoever
> resumes Plan 4 finds it already enumerated.

> ### Known exposure, recorded 2026-08-03 and deliberately not closed: the claims guard never opens the file
>
> `claims.verify_ledger` checks three things about a claim's cited evidence: that the **paths
> exist**, that they are **git-tracked**, and that tracking is determinable. It never opens a file,
> never compares a number against one, and never sees the configuration — the δ allocation, the
> candidate count, the sample size — that produced either the number in the file or the number in
> the prose. **A claim quoting a figure that appears nowhere in its own evidence passes unchanged,
> because the metric is satisfied by absence.**
>
> **`verify-claims ok` therefore means the paths resolve.** It was reported as a green signal in
> every status line of the 2026-08-03 session, and reading it as "the claims check out" — as that
> seat did — is reading information that is not there. That reading is the exposure; the tool is
> doing what it says, under a name that suggests more.
>
> **This is the mechanism behind the five quoting errors** recorded in the write-up's limitations,
> not five separate lapses of attention. It also explains their direction: nothing was ever pushing
> back, so the only filter on a wrong number was whether it looked plausible, and a number that
> flatters the result looks plausible to the person who wants it. Contrast
> `test_doc_references.py::test_every_test_named_in_the_docs_exists`, which *does* open the file and
> compare — it caught a stale test name in the very commit that renamed it.
>
> **Attestation is not checking.** `evidence/plan3/certification_sensitivity.json` now stamps each
> quoted quantity with its δ, allocation, candidate count and n. That narrows the four quantities it
> covers and closes nothing: **nothing compares the prose against it.** The stamp is a place to look
> up the right answer, not a gate that notices the wrong one.
>
> **The instance list. The paper carries five; this repository carries six.** The paper's five are
> scoped to the claims it reports, and it now says so in the sentence rather than leaving the scope
> implied. The sixth is not a reported claim and does not belong in an ACL Limitations section,
> where it would dilute the five that bear on the result.
>
> | # | The quantity | Where it was quoted | Caught by |
> |---|---|---|---|
> | i | $\alpha$-frontier point 0.406, as a threshold | claim wording | claim-wording audit |
> | ii | empirical oracle 0.2357, as clearing the floor | write-up | independent review |
> | iii | 11.4%, as "certified" without naming the construction | write-up | pre-submission audit |
> | iv | a narrowing applied to a derived doc, not the ledger | ledger → appendix | review |
> | v | acceptance LCB 0.2017, at an allocation not used | write-up | review |
> | **vi** | **"content ends 82% down page 4, within the limit"** | **every status line** | **a rebuild** |
>
> **Four more of the same class, and the reason they are listed separately is their ROUTE.**
> Instances (i)–(vi) were generated by the author. These four arrived **through an instruction**
> and were carried into the work because they came from the owner rather than from the seat:
>
> | # | The quantity or framing | Caught by |
> |---|---|---|
> | vii | the 0.1075 counter-example endorsed on the risk constraint alone, one turn after writing that both constraints bind | independent review |
> | viii | "at δ/3 … the largest this benchmark can support" — qualified and then unqualified inside one sentence | independent review |
> | ~~ix~~ | ~~the validity guard's first scope defined as "the four stamped quantities"~~ **WITHDRAWN — misclassified; the scope was proposed by this seat, not supplied** | — |
> | x | the 0.0925 framing endorsed without asking which construction produced it | independent review |
>
> **Instance ix is withdrawn from this table.** *(Corrected 2026-08-04 on an independent review
> finding.)* It recorded the validity guard's "four stamped quantities" first scope as having
> arrived through an instruction. This document's own earlier text contradicts that: the scope was
> proposed here by the seat, with the owner deciding **whether** to build the guard, not **what**
> it should cover. Three instances, written as four. The row is struck rather than deleted, because
> a table that quietly loses an entry is worse than one that shows its own correction.
>
> **Provenance caveat, and it applies to all of them.** `REVIEW.md` already carries exactly this
> caveat for this class and this table lacked it: each attribution rests on conversation that
> leaves no trace in the repository, and **the sole source for the attribution is the seat the
> attribution favours** — this one. A reader should treat the *mechanisms* as the durable content
> and the *routing* as unverified. Having the caveat in one file and not the other was itself the
> twin-surface defect, on a passage about attribution.
>
> **A defect arriving through an instruction is a different path from one the author generates, and
> nothing here distinguished them until now.** The seat's failure in each is the same and it is not
> that the instruction was wrong: it is that a figure or framing supplied by a trusted source was
> passed through without the check it would have received had the seat written it. That is exactly
> the gap recorded for instance vi — **"confirmed by a reader" is not "verified"** — running in the
> opposite direction. **"Supplied by an instruction" is not "verified" either.** All four are
> recorded here at the owner's direction, and the owner's own framing is the source of three of
> them, which is the point rather than an embarrassment: a route that nothing checks will carry
> whatever is put into it.
>
> **A second defect class, recorded separately so it does not dilute the six above: a search that
> ends in a conclusion must state what it searched.** Three occurrences, all ending in a verdict:
>
> | # | The search | Population it used | What it missed | The verdict it produced |
> |---|---|---|---|---|
> | S1 | surfaces carrying "each forbid the target" | the write-up | source, generated strings, committed artifacts | "corrected on all five surfaces" — it was eight |
> | S2 | surfaces carrying the capability attribution | prose, source, artifacts, tests | required companion records | "the ten-surface map is complete" — the withdrawn-assertions registry was not in it |
> | S3 | artifacts backing six programme figures | `evidence/*.json` | committed **Markdown** | "six figures are untraceable" — all six were recoverable |
>
> **The rule: "I found none" is not a finding until "I looked in X, Y, Z" is stated beside it.** In
> all three the query was correct and the population was wrong, which is why re-running the search
> never helps — the error is invisible from inside it. This is the same shape as the claims gate
> one level up: a metric satisfied by absence, where absence was never measured against a stated
> universe.
>
> **A fourth class, and the second to cross a repository boundary: the status you read is not the
> status of the thing you ran, and it fails toward "fine".**
>
> | # | The wrapper | What it reported | What had happened | Repository |
> |---|---|---|---|---|
> | P1 | `pytest \| tail -2 && git commit` | success, so the commit proceeded | the suite was red; `&&` reads `tail`'s status, not pytest's | conformalextract |
> | P2 | a run wrapper | exit 0 | the process took a SIGSEGV | redteam-foundry |
> | P3 | the same wrapper | exit 0 | a CUDA out-of-memory | redteam-foundry |
>
> All three fail **toward "fine"**, which is the direction that ships. And all three are the
> session's own defect one level down: a check reported as passing because *the thing being read
> was not the thing being measured* — a status from the last element of a pipe, not from the
> command that mattered. **Verify by exit status or `PIPESTATUS`; never through a pipe.** With the
> population rule, this is the second class to recur across different repositories, which is the
> signal that it is a property of the practice rather than of one codebase.
>
> **A shape, not two incidents: a test that requires a defect to exist becomes an obstacle to
> fixing it.** Twice in `tests/test_paper_claims_guard.py` — one asserting an unbacked figure
> existed, one asserting a declared disagreement existed. Both were true when written and both
> turned red the moment the last instance was repaired, so the suite punished the repair it was
> written to encourage. The correct form asserts the *property* against a synthesised case:
> remove an entry from a copy and assert absence fails; declare a disagreement on a copy and
> assert it is not muted. Neither needs a live defect, and neither goes red when the paper is
> clean.
>
> **A third class, distinct from both and from anything a value check can reach: the form is wrong
> while every value is right.** The write-up printed the abstain/extract flip rate as
> "1.3--1.8\%", which reads as a confidence interval. It is not. 1.33% is the flip rate at full
> acceptance and 1.78% is the same four flips over the top-75% denominator — two measurements of
> different things, dash-joined into an apparent claim about sampling uncertainty that neither
> figure supports. **Both numbers are correct, so no value check and no configuration check can
> see this.** Its sibling is `12.9×`, where a presentational choice ran the other way and
> manufactured a quantity that was never correct anywhere. Corrected in the paper; the guard now
> backs each rate separately with its own denominator pinned, which is what makes the distinction
> visible in the manifest rather than only in prose.
>
> **Instance vi is the purest example in the set.** It cites an artifact that exists — the built
> PDF — states a number that artifact does not contain, flatters compliance, and sits in the one
> line whose entire job is to assert compliance. No guard could have caught it, and none did.
>
> **And it propagated further than any of the others.** It was repeated in every status report,
> including to the owner, who read it and repeated it back. **A wrong number that its reader
> confirms is a different failure from one that goes unnoticed**: the confirmation is evidence to
> the author that the number was checked, so the error acquires a second source and becomes harder
> to find than it was when only one person held it. None of instances (i)–(v) had that property.
> Nothing in this repository currently distinguishes "confirmed by a reader" from "verified".
>
> **Open item — a validity guard that reads its evidence.** First scope, deliberately small: the
> four quantities in `certification_sensitivity.json` (the acceptance lower bound by allocation, the
> empirical-Bernstein probe, the AUROC bootstrap interval, and grid capacity), asserted against the
> surfaces that quote them. **Not built.** Building it before the overdue review round would repeat
> the bundling problem the round exists to catch, and naming the gap is the disclosure the paper
> carries. Whether to build it at all is the owner's call.
>
> **BUILT 2026-08-03, and the deferral was the wrong call.** The guard below was deferred twice so
> a review round would not be delayed. Review then found the class it would have caught, three
> rounds running, *inside the corrections* — so deferring it was producing the instances. It is
> `scripts/check_paper_claims.py`, backed by `evidence/plan4/paper_claims.json`, proved by mutation
> in `tests/test_paper_claims_guard.py`, and its first run is reported below. **Its output has not
> been acted on**: an instrument's correctness is checked before its results are trusted, and
> building-and-acting in one motion is the shape that produced three of the instances.
>
> Its scope is **the paper, not the artifacts** — the "four stamped quantities" scope recorded here
> earlier was wrong for the reason the finding itself gives: a scope defined by what an artifact
> already contains cannot see a figure that was never written into it.
>
> **What it does not do**, stated here rather than left to be discovered. It cannot read prose, so
> it cannot catch a correctly-valued figure attached to the wrong claim — the 0.2017 error would
> have survived it unless the manifest author declared the allocation honestly. It reads only the
> paper, so nothing in `certification-result.md`, the ledger or the README is in its population. It
> binds one entry per rendered token, so where two different quantities round to the same string
> (`0.589` is both the 3-trigger stratum and the fully-grounded stratum) only one binding is
> checked. And the manifest is authored, so a human step remains — though the build-time verifier
> caught two of this author's own pointer errors before either reached a run.
>
> ### The gate is green: all 118 figures backed. What changed, and what was refused
>
> **`scripts/check_paper_claims.py` now exits 0.** Every figure the paper asserts resolves to a
> committed artifact carrying its value and its configuration, and
> `test_every_figure_in_the_paper_is_backed` holds it there. A permanently red gate stops being
> read, which is its own quiet failure mode; the fix was **better extraction plus more backing**,
> never an exemption.
>
> **The distinction, held precisely.** An exemption says "this is a claim, do not check it" — 
> refused, always. Better extraction says "this was never a claim". `Table 5`, the `2507` in
> `Qwen3-4B-Instruct-2507`, a `(2)` row label, `6+`, `mechanism-3` and the `1` in $(1-\alpha)$ were
> never claims. Every rule is stated over **context** — position, LaTeX environment, surrounding
> tokens — and none is a list of values to skip, because a rule keyed on the value is an exemption
> wearing a rule's clothes.
>
> **The rules apply per OCCURRENCE, not per figure**, which narrows the token-collision limit
> recorded above but **does not close it, and an earlier version of this line said it did.**
> Per-occurrence logic decides only whether a *figure is dropped* as structural; it does not change
> how a surviving figure **binds**. `check_paper_claims` still keys the manifest on the normalised
> value and iterates one entry per value, so `0.20` is written eight times and bound once — three
> of those eight are the acceptance floor and one is the coverage multiplier in
> $0.20 \times 1{,}396$, all satisfied by a single entry pointing at `alpha`. Closing it needs
> per-occurrence *binding*, which is the same work as the inline-declaration design and belongs
> with it. *(Corrected 2026-08-04 on an independent review finding: a premature closure claim in a
> document whose subject is premature closure claims.)* A figure is dropped only when *every* place it is written is structural, so
> `3` survives — it is a row label, an allocation divisor in $\delta/3$, **and** the number of
> non-failing groups the ZS AUROC rests on. The test
> `tests/test_paper_claims_guard.py::test_a_claim_is_not_hidden_behind_a_label_that_renders_the_same`
> pins that.
>
> **The rules were tested against the case that would prove them wrong.** `top-75\%` is a
> hyphenated alphanumeric run structurally identical to `4-bit`, and it is a real threshold. The
> identifier rule therefore requires two letter-bearing segments, so a `word-number` compound
> survives. Which meant **`4-bit` had to be backed rather than excluded** — it is derived in
> `programme_facts.json` from the gate-0 smoke artifact's `load_in_4bit` and `quant_type: nf4`,
> because the artifact records the mode and not the numeral.
>
> **Four figures were backed rather than excluded, and this is the part worth arguing with.**
> "Normalized AURC is 0 for a perfect ranking, 1 for chance" and "an invalid output scores 1.0"
> *are* claims — assertions about the implementation, checkable against it. So they are computed:
> the AURC endpoints from the committed values, and the structural-failure loss through the frozen
> scorer itself. Excluding them would have been the exemption the whole apparatus refuses.
>
> **Two extractor bugs surfaced on the way.** `\setlength{\tabcolsep}{4pt}` leaked `4pt` because
> the strip pattern took only the first brace group, and `\multicolumn{4}{@{}l}` leaked its span
> count because the column spec nests braces. Both were reporting typesetting as asserted figures.
>
> ### The audit, stated as a result
>
> **An instrument scoped by the paper found 53 of the paper's own 120 figures unbacked — including
> the headline 21.6-point ranking gap and the 8.4% family-wide certified acceptance — six that
> traced to no artifact at all, and three that disagreed with a freshly computed value because one
> paragraph used two prefix definitions and named neither.** Every one of those figures had passed
> every gate this project had. `verify-claims` returned `ok` throughout.
>
> That is this paper's own thesis demonstrated on itself, one level up. The paper argues that
> ranking a population well is not the same as certifying anything about it; the repository's gate
> certified *agreement between documents* and was silent on whether the documents were right. A
> synchronisation guard cannot find an unbacked figure, because absence satisfies it. A validity
> guard finds it on the first run — and did.
>
> **The three disagreements share one cause, and it is not arithmetic.** 0.20 × 1,396 = 279.2, so
> the acceptance floor is met at k = 280 and missed at 279. The paper used both prefixes in a single
> paragraph and named neither, so 0.0925 was a k = 280 figure sitting beside an 18,000-group
> extrapolation that only reconciles at k = 279. **An undefined term, not a miscalculation.**
> The paper now states the definition where it is first used.
>
> **Fairy's view on whether any of this belongs in the paper** — the owner's call, not hers. The
> Limitations section already carries the mechanism and the five instances, and it earns its space
> because the failure it describes is the paper's subject. The audit is a *result about this
> repository*, not about selective prediction, and a short paper that spent a paragraph on its own
> tooling would be spending it on the wrong thesis. **One sentence is defensible**: that every
> figure in the paper resolves to an artifact carrying its value and its configuration, checked
> mechanically, with the exceptions named. That is a reproducibility claim, it belongs in the
> Reproducibility section where a version of it already sits, and it is worth more than the
> narrative would be. The rest stays here.
>
> ### Second run: 101 of 120 backed. What remains, and why each one remains
>
> Buckets B, C, D and E are now backed — ratios stored beside their counts
> (`evidence/plan3/derived_ratios.json`), quoted values in a citation record with source,
> identifier and access date (`evidence/plan4/external_citations.json`), and two renderer ops for
> the order-of-magnitude p-values. **101 pass, 19 fail: the 3 declared disagreements and 16
> unbacked.** No prose was touched.
>
> ### Recoverability of the six, established before deciding anything. NOT YET ACTED ON.
>
> The earlier entry below called these six "untraceable". That was a search result, not a verdict,
> and checking changed the answer for **all six**: none is genuinely unrecoverable, and the reason
> the first search missed them is that it looked only in `evidence/*.json` while their sources are
> committed **Markdown**.
>
> | Figure | Status | Where its inputs are |
> |---|---|---|
> | `86.3` | **(a)** inputs exist | `docs/plan2/serving-equivalence-probe-result.md`: **259/300**, 95% Wilson CI [81.98%, 89.76%] |
> | `1.3` | **(a)** inputs exist | same document: **4/300** abstain/extract flips at 100% acceptance |
> | `1.8` | **(a)** inputs exist | same document: the flip rate rises to 1.78% under tightening — *and note this is a different denominator from 1.3, not the same measurement twice* |
> | `18.7`–`18.9` | **(a)** inputs exist | `docs/adr/0012`: a full per-job table, Plan 2 subtotal $18.33 + Gate 0 $0.2008 = $18.53, plus one job never recorded per-job and recovered by differencing four running totals |
> | `637` | **(b)** re-runnable at $0 | `evaluation.py` emits `false_positives` and `false_negatives`; recomputable over the already-open certification split |
> | — | **(c)** genuinely untraceable | **none** |
>
> **Held, per instruction: classification reported, nothing built.** Two observations that bear on
> how they should be backed. First, `1.3` and `1.8` are *not* a range of one measurement — 1.33% is
> the flip rate at full acceptance and 1.78% is the rate under tightening, and the write-up prints
> them as a dash-joined band, which reads as a confidence interval. That is a presentation defect
> hiding inside an unbacked figure, and it would not have surfaced without going to the source.
> Second, the cost band's reason for *being* a band — no single ledger, one job differenced — is
> recorded in the README and in ADR 0012 but **not in the paper beside the figure**. A paper about
> backing quantities cannot carry an unbacked quantity silently; whatever the resolution, it is
> visible.
>
> ### Superseded by the table above: the "six untraceable" finding
>
> **Six figures have no computation-bearing artifact anywhere in the repository**, and this is the
> new finding. `86.3` (serving-stack parity), `637` (false positives less false negatives),
> `1.3`–`1.8` (the abstain/extract flip band) and `18.7`–`18.9` (the cost band) appear **only in
> reviewer records, the claim ledger and prose**. A search of every committed `evidence/*.json`
> finds no computed source for any of them; the one apparent hit on `86.3` is a coincidental
> coordinate on an unrelated curve. They are not wrong — they are untraceable, which is the state
> the whole apparatus exists to detect, and they were not invented an artifact to hide in. The cost
> band is a special case the README already records: there is no single spend ledger, the total is
> assembled by a reader, and one job is recovered by differencing running totals, which is what
> makes it a band. Recording *that* is honest; manufacturing a ledger would not be.
>
> **Nine are extractor false positives** — table row labels `1`/`2`/`3`, the citation locator
> `Table 5`, the stratum label `6+`, `Qwen3-4B`, `-2507`, and the definitional `0` and `1.0` of the
> loss range. They get no pointer and **no exemption**. A guard loud about what it cannot parse is
> honest; one that exempts it is the defect.
>
> ### Stated limit: one entry per rendered token, and it already hides a real claim
>
> The guard keys on the rendered token, so where two different quantities render the same string
> only one binding is checked. **`3` is both a table row label and "3 non-failing groups"** — a
> real claim about why the ZS AUROC is unstable, sitting behind a piece of typesetting. `0.589` is
> both the 3-trigger stratum and the fully-grounded stratum. This is no longer hypothetical.
>
> Not fixed. Disambiguating by context is the same work as the inline declaration below and belongs
> with it — both need the guard to know *where* in the paper a token sits, not just that it occurs.
>
> ### Ruling: remove the number 80, do not back it and do not exempt it
>
> "Roughly 80% of what we measured is a replication" is an author's estimate wearing a
> measurement's clothes, in a paper about backing quantities. An `author_estimate` pointer kind
> would be an exemption with better manners. The replacement says more and needs no artifact:
>
> > Most of what we measure replicates prior work. What is new is X, Y and Z.
>
> Checkable, more informative, no number. **This is a prose edit and has not been made.** Recorded
> here so the ruling survives to the repair round.
>
> ### For the instance table, when the repair round comes
>
> **`12.9×` is not a measurement.** It is `18000/1396` — the already-rounded group count divided by
> n. It reproduces at neither prefix (13.4 at the floor, 12.8 below it). **A rounding was fed back
> in as an input.** That is a distinct sub-species and deserves its own name: every prior instance
> was a correct number attached to a wrong configuration, while this one was never correct
> anywhere, produced by a presentational choice being read back as data.
>
> **The cause of all three disagreements is one thing, recorded once.** 0.20 × 1396 = 279.2, so the
> acceptance floor is met at k = 280 and missed at k = 279. One paragraph uses both prefixes and
> names neither: `0.0925` is the k = 280 figure, `18,000` and `12.9×` reconcile at k = 279.
>
> ### The residual hole, and the design that closes it. RECORDED, NOT BUILT.
>
> The guard checks the **manifest's** declared configuration against the **artifact**. It never
> checks either against **what the prose claims**, because it cannot read prose. So instance (v)
> survives it in the general case: a figure pointed at a block honestly stamped "three candidates,
> full δ" passes, while the sentence two words away says "at the frozen δ/3 allocation". The guard
> would have caught (v) *only if the manifest author had pointed the entry at the allocation the
> sentence names* — which converts "did anyone check?" into "did the author declare truthfully?",
> a weaker property and the same human step that produced the error.
>
> **The closing design: declare the configuration inline in the paper, adjacent to the figure**, in
> a macro that both typesets the number and states the allocation it belongs to. The manifest is
> then **derived from the paper** rather than written alongside it, so a declaration cannot diverge
> from the sentence it sits in — the two are the same token. That restores "did anyone check?",
> which is the property the current guard cannot have at any level of author diligence.
>
> Not built. Whether to build it is the owner's call.
>
> ### Stated hit rate: one conditional catch in six, and the five it misses
>
> An instrument whose limits are unstated is worth less than one with a modest, published hit rate.
> Against this project's own six recorded instances:
>
> | # | Instance | Would the guard have caught it? |
> |---|---|---|
> | i | 0.406 reported as a threshold | **No** — the value is right; "threshold" is a wording claim |
> | ii | 0.2357 reported as clearing the floor | **No** — the value is right; the inference is wrong |
> | iii | 11.4% called "certified" without its construction | **No** — `calibration_diagnostics.json` records no `construction` field to pin |
> | iv | correction applied to a derived doc, not the ledger | **No** — neither file is in its population; it reads only the paper |
> | v | acceptance LCB quoted at an allocation not used | **Conditionally** — caught iff the entry is pointed at the allocation the sentence names |
> | vi | "content ends 82% down page 4" | **No** — not in the paper, and not a computed quantity |
>
> **Five missed, one conditional.** Every miss is of the same two kinds: a correct number attached
> to a wrong claim, or a document outside the paper. The guard closes absence and drift. It does
> not close attribution, and no version of it that cannot read prose will.
>
> **Reference implementation: `redteam-foundry` built the equivalent.** Two properties of it are
> the requirement, not decoration. Its checker **opens both the artifact and the document** and
> compares — the thing `verify_ledger` does not do. And it **refuses to pass on an empty claim
> list**, because a checker with nothing to check passes vacuously, which is the same failure shape
> as a metric satisfied by absence. Any guard built here inherits both or it reproduces the gap it
> was written to close.

> ### First run: the paper's figures are not wrong, they are backed by nothing
>
> **Zero value mismatches and zero configuration mismatches** on the first paper-scoped run.
> Everything that resolved, resolved correctly under the configuration it declared. The failure was
> entirely **absence**: 53 of 120 figures resolved to no artifact at all — and the set included
> **21.6, the paper's headline ranking gap**, and **8.4%, its family-wide certified acceptance**.
> Both had been derived in a shell and written into prose, and had been in that state since they
> were written. That is a finding about the paper, not a to-do list: the central quantity of a
> results paper was traceable to nothing, and every gate the project had passed it.
>
> **Then the eleven were computed into `evidence/plan3/derived_quantities.json`** by
> `scripts/derived_quantities.py`, each stamped with its construction, δ, allocation, n and prefix
> length. Eight now resolve. **Three disagree with the paper**, reported by the guard rather than
> asserted:
>
> | Paper | Artifact at the floor-meeting prefix (k = 280) |
> |---|---|
> | empirical risk 0.174 at the floor | **0.1747**, which renders 0.175 |
> | "about 18,000 groups" | **18,740** |
> | "12.9× this split" | **13.4×** — and 12.8× one group below the floor, so 12.9 reproduces at neither |
>
> The cause is a definition the paper never states. 0.20 × 1396 = 279.2, so the floor is *met* at
> k = 280 and *missed* at k = 279. The paper's 0.0925 is the k = 280 figure; its 18,000 and 12.9×
> reconcile at k = 279. **One paragraph uses both prefixes without naming either.** And 12.9 is not
> a computation at all — it is 18000/1396, the already-rounded group count divided by n, so a
> rounding was fed back in as an input.
>
> The manifest entries point at **k = 280 deliberately**, so the guard fails. Pointing them at
> k = 279, where two of the three match, would be choosing the configuration that makes the paper
> right — the defect this apparatus exists to refuse. **The prose is not corrected here**: the
> figures were discovered in the session that built the instrument, and correcting a number in the
> session that found it is the shape that produced three of the six instances.
>
> ### Reconciled 2026-08-04: two committed records give different Hoeffding radii, and both are right
>
> `evidence/plan4/reviewer_record.writeup-draft.json` records a radius of **0.0856** where the
> paper and the code publish **0.0925**, for what is described as the same quantity. Nothing
> reconciled them, and a reader finding both would have no way to tell which was wrong.
>
> **Neither is.** The reviewer computed `sqrt(ln(1/δ)/(2n))` — the tight **one-sided** constant,
> which is the right form for an upper bound. `certification.hoeffding_upper` implements
> `sqrt(ln(2/δ)/(2n))` — the **two-sided** constant, which is larger. The function's docstring said
> "one-sided" while using the two-sided constant, which is how the two records diverged without
> either being in error.
>
> **The implementation is unchanged and stays unchanged.** A wider radius yields a valid bound, so
> every conclusion drawn from it holds a fortiori; recomputing would move published numbers to make
> a null result *less* stark. The docstring now states the constant it actually uses and discloses
> the size of the conservatism — about 8%, in the direction that makes the benchmark look more
> forbidding and therefore flatters this paper's thesis. **The reviewer record is not touched**: it
> is a verdict, it was correct on its own terms, and mutating a reviewer record to agree with a
> later number would be the worst available fix.
>
> ### Carried forward from the 2026-08-03 review round, recorded and deliberately not fixed
>
> Both come from the independent reviews of packets 1 and 2. Neither is actioned, and the second
> is worth more as a documented finding than as a quiet fix.
>
> **`certification_sensitivity.json` has no test and no label-access attestation.** Every other
> re-analysis artifact is registered in `tests/test_reanalysis_artifacts.py` under ruling R3, and
> every other artifact that opens gold carries a `certification_access` block with its chain head
> and `final_reads: 0` / `shift_reads: 0`. This one has neither, while being cited as evidence by
> the ledger and passed by `verify-claims` — by the path-existence check it was written to work
> around. The structural guard is intact (`assert_reanalysis_role` is fail-closed and the role is
> hardcoded), so this is a missing attestation, not a leak. An independent verifier of that
> artifact currently has nothing to check.
>
> **The withdrawn-assertions gate cannot see `.tex`, and exempts a `.tex` file anyway.**
> `PROSE_SUFFIXES` is `{.md, .json, .txt, .py, .toml}`, so the typeset paper — the most public
> surface here — has never been scanned. Meanwhile `permitted_in` for
> `grounding-orthogonal-entity-naming` lists `docs/writeup/uncertainlp-2026-short.tex`, and the
> guard-the-gate test reads that path directly, so the exemption passes and **reads as coverage
> that does not exist**. That is this repository's own defect class occurring inside its
> governance layer: a metric satisfied by absence, and an affirmative signal generated by it.
> Left standing deliberately — the finding is the point.
>
> Also carried: two further live phrasings of the withdrawn capability attribution, both inside
> immutable reviewer records, are unregistered; and the convention that a surface map must state
> the population it searched exists only in a routing packet, not in `REVIEW.md`.

## Live list

| # | Decision | Status |
|---|---|---|
| 1 | Reviewer records in the public bundle | ~~open~~ **DECIDED 2026-07-29 — publish as-is** |
| 2 | Repository description | ~~open~~ **DECIDED 2026-07-29 — gets its own ledger claim; sentence still to be drafted and reviewed** |
| 3 | Repository topics | ~~open~~ **DECIDED 2026-07-29 — three approved; more may be proposed** |
| 4 | §1 versus §17 on the minimum contribution | **DEFERRED 2026-07-29** — §1's seven stand; not on the path to the actual goal |
| 5 | Repository visibility | **OPEN** — routed separately, see [`proposed-visibility-change.md`](proposed-visibility-change.md) |
| 6 | An operator path inside a byte-frozen document | **OPEN** — added 2026-08-02; see §6 below |

Decisions 1–4 were ruled by Ross on 2026-07-29. Their reasoning is preserved below rather than
deleted: a struck decision is a record of *why*, and the next person to ask the same question should
find the argument, not just the answer.

---

## 1. ~~Do reviewer records ship in the public evidence bundle?~~ **DECIDED: publish as-is**

**Raised:** 2026-07-28, by the release-hygiene check.
**Decided:** 2026-07-29 by Ross — **option (a), publish as-is.**

> **The reasoning below is adopted as the basis of the decision.**
>
> **The cost is larger than every document describing it has said, this one included.** It was
> framed as "a directory name from one machine". Measured at this commit: the operator's Windows
> **account name** appears in 19 tracked lines across two files — including two full user-home
> paths — and the private-planning-directory name in 31 occurrences across three files. Decision 1
> as first written named the directory only; `publishable-and-sealed.md` §4 named one file; the
> `ALLOWED` list in `tests/test_internal_paths.py` names three. **Each description was narrower than
> the thing it described**, which is this week's recurring defect appearing in the artifacts written
> to prevent it.
>
> The decision is unchanged — an account name and a directory name disclose nothing exploitable, and
> the attestations they sit inside are worth more than their removal. But it is accepted knowingly
> now rather than on an undercount. **Note also that no gate covers the bare account name:**
> `test_internal_paths.py` deliberately hardcodes no username, which is sound design and leaves that
> class uncovered.
>
> **One addition that changes when this binds, and it was not said when the options were framed:**
> **flipping repository visibility publishes those records whether or not a bundle is ever
> assembled.** Every reviewer record is a tracked file. There is no assembly step between "the repo
> is public" and "the records are public".
>
> **This decision is therefore a precondition for any visibility change, not merely for bundle
> assembly.** It is now satisfied — but the general shape is worth keeping: a decision framed as
> being about *what we publish* can be forced by an act that publishes *everything tracked*, and
> the framing hides that.

`evidence/plan3/reviewer_record.reanalysis.json` contains four references to the private planning
directory the accepted plans were held in, including its absolute path. Two sibling occurrences
elsewhere in the repository were reworded; this one was **held**, and the reasoning should survive
whatever is decided:

- Reviewer records are immutable evidence artifacts. Other documents cite them, and the honesty
  doctrine treats them as fixed.
- The paths sit inside first-person prose recording *what was hashed against what*
  ("I hashed all four in-repo copies from git and all four sources in …"). Redacting them does not
  tidy a citation; it breaks the attestation the sentence exists to make.
- Doing it inside the record of a review whose subject was partly whether artifacts say what they
  claim would be a poor place to start editing artifacts.

The two available decisions:

**(a) Publish as-is.** The paths name a directory on one machine, disclose nothing sensitive about
its contents, and are part of the historical record. Cost: a public artifact contains an internal
filesystem path.

**(b) Exclude reviewer records from the public bundle.** Cost is much higher than it looks. The
records are the evidence that the independent-review discipline happened at all; the write-up cites
them by name as the basis for "reproduced by someone who did not compute it". Publishing the claims
while withholding the reviews that tested them inverts the project's own argument.

**Recommendation on the record, for the reviewer of this decision to test:** (a). But it is not
this seat's call, and it is not urgent until a public bundle is actually assembled.

**Do not resolve it by editing the record.** That is the one option ruled out already.

---

## 2. ~~What does the repository description say?~~ **DECIDED: its own ledger claim**

**Raised:** 2026-07-28, by the release-hygiene check.
**Decided:** 2026-07-29 by Ross — **the description gets its own ledger claim, not a compression of
an existing one.** The sentence itself is still to be drafted and routed like any other public
sentence. Currently **empty** (`gh repo view` → `"description":""`).

> **Why its own claim, and the analysis below is the specification:** the claim boundaries require
> the ~16× grounding gain and the null to travel in the **same passage**, and a description has no
> second passage. `CX-H1-PRIMARY`, `CX-CAPGAP-01` and `CX-GROUNDING-ORTHOGONAL-01` all carry the
> `abstract` surface and none is short enough as written. **So the sentence must be written for the
> constraint, not trimmed into it** — trimming an existing claim is how the null gets dropped.
>
> `"95.7% grounded event-argument extraction"` remains forbidden by name.

A description is a claim about what the repository is, rendered on every search result, every
listing, and every link preview — and it is the one public surface with no room for a caveat. This
project does not let claims land without review, and a one-line summary of a **negative** result is
harder to write honestly than a paragraph, because there is no space to attach the null.

The trap to avoid is stating the grounding result without it. "95.7% grounded event-argument
extraction" would be true, catastrophic, and forbidden by name in
[`../plan3/certification-result.md`](../plan3/certification-result.md) — the claim boundaries
require the 16× grounding gain and the null to travel in the same passage, and a description has no
second passage.

Whatever is chosen must trace to a ledger claim like any other public sentence. `CX-H1-PRIMARY`,
`CX-CAPGAP-01` and `CX-GROUNDING-ORTHOGONAL-01` all carry the `abstract` surface, which is the
closest existing analogue to a description; none of them is short enough as written, so the
decision includes whether a description needs its own ledger entry rather than a compression of an
existing one. **Not filled in now**, deliberately.

## 3. ~~What topics does the repository carry?~~ **DECIDED: three approved**

**Raised:** 2026-07-28, by the release-hygiene check.
**Decided:** 2026-07-29 by Ross — **`conformal-prediction`, `selective-prediction`,
`event-extraction`** are approved as accurate. Further topics may be proposed if they trace
honestly. Currently **none** set.

> `certified` and `production` stay **banned**. `certified` in particular is reserved by the honesty
> boundary for something this project did not achieve, and a topic is not exempt from that because
> it is metadata rather than prose.
>
> **Candidates for the "propose more" allowance, not applied:** `rams`, `qlora`, `negative-results`,
> `reproducibility`, `llm-evaluation`. Each traces to something the repository actually contains.
> `negative-results` is the one worth arguing for — it is the most accurate single word for what
> this project produced, and it is the opposite of the direction a topic list usually drifts.

Lower stakes than the description — topics are discovery metadata, not prose — but they are still a
public surface and still a claim of a kind. `conformal-prediction`, `selective-prediction` and
`event-extraction` describe the subject matter accurately. Anything implying a working system
(`certified`, `production`) does not, and `certified` in particular is reserved by the honesty
boundary for something this project did not achieve.

Both items are gated behind Plan 4 opening, and Plan 4 has not opened.

---

## 4. ~~§1 and §17 disagree on the minimum contribution~~ **DEFERRED**

**Raised:** 2026-07-29, by the independent review that rejected the staged-release amendment.
**Deferred:** 2026-07-29 by Ross. **§1's seven stand.** Deferred rather than answered, because it is
**not on the path to the thing actually wanted** — visibility is decision 5, and §1 governs the
public *contribution*, which is a different question. Resolving §1-versus-§17 would not move a
visibility change one step closer.

**Neither party had found it** — not the implementer proposing to cut §1, and not the reviewer
refusing the cut, until it read §17 in the primary text.

`accepted-plan.md` §1 names **seven** items as "the minimum useful public contribution". §17's
evidence-acceptance checklist contains a ticked line reading *"The evaluator/certifier, evidence
bundle and CPU replay are the minimum contribution"* — **three** items.

This is a genuine internal contradiction in an accepted plan, and it is the strongest argument the
rejected amendment could have made and did not. It does not rescue that proposal: §17's three are a
*different set* (they omit item 4, the versioned GitHub release, which Stage A kept), and treating a
checklist gloss as though it overrode the section it summarises is the exact trap `CLAUDE.md`
already records from the §6.3 episode — *"the repo's gloss on §6.3 was stricter than §6.3 actually
is, and an ADR was written against the gloss."*

**Not resolved here, and deliberately not resolved by a release commit.** An accepted plan is
amended by dated note and its hash pin moved in the same commit; which of the two readings governs
is a scope question for Ross, and it changes what the release must contain. Until it is answered,
**§1's seven stand**, because that is the section and §17 is the summary of it.

Both readings should be tested against the same question: which one did the plan's author intend to
bind — and if the answer is not recoverable, which one this project would rather be held to.

---

## 6. An operator path inside a byte-frozen document **OPEN**

`docs/plan3/section-12-1-certification-only-scope-addendum-2026-07-30.md` cites, at its line 36, an
operator-local implementer report held under a machine temp directory, as the source of the five
input hashes it then reproduces inline. The file is admitted **byte-for-byte** — its authority is
hash equality with the artifact independently reviewed on 2026-07-30 — so the string cannot be
edited without destroying the evidentiary value the document exists to carry.

**What was done, and what was not.** `tests/test_internal_paths.py` previously enumerated three
known roots by name and matched none of this, so the suite would have stayed green while the path
shipped. A `windows-drive-path` pattern matching the *shape* of a drive-letter path now catches it,
and the file is named in `ALLOWED` with byte-fidelity as the stated reason. **The gate now sees the
string; nothing has removed it.** That is the open decision.

**This section was rewritten by its own gate, which is the point.** The first draft quoted the paths
verbatim — the natural way to be specific — and the newly widened pattern failed the suite on nine
hits in this file. That is the 2026-07-28 defect recorded in `REVIEW.md` recurring exactly: a
disclosure that introduces the strings it exists to disclose. The difference is that this time a
mechanism caught it instead of a reviewer, in the same change that built the mechanism. The paths are
therefore described here rather than quoted; the one document that may quote one is the frozen
addendum, because it may not be edited at all.

**The choice, stated plainly.** Either (a) this repository publishes a document containing an
operator-local path, disclosed here and defensible as mention-not-use — the same ground three
reviewer records already stand on; or (b) the addendum does not ship in the public bundle, which
means the §12.1 amendment's own text is absent from what a reader can check. Interacts with decision
1: reviewer records were ruled publishable as-is on the same reasoning, so (a) is the consistent
answer, and consistency is not by itself a reason.

**Not to be confused with the packet-location finding.** That the *routing packets* for this work
also lived under the same temp directory, outside any enumerable location, is a governance defect
recorded in the PMO learning log as entry `2026-08-01-003` — it is about where packets are kept, not
about what a shipped document contains, and it is not this decision.
