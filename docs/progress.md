# PMO progress

> **This log was frozen at 2026-07-17 for eleven days** while Plans 2 and 3 executed. Its last entry
> closes on "Plans 3–4 remain sequentially blocked", which was accurate on its date and has not been
> true since 2026-07-22. It was the **third** stale gate-state assertion found in this repository in
> one week, after the README and `docs/plan4/accepted-plan.md`.
>
> Entries are appended and never rewritten, so the 2026-07-17 line stays as written. **For current
> gate state read [`../evidence/gate_state.json`](../evidence/gate_state.json)**, which is derived
> from the reviewer records and held to them by `tests/test_gate_state.py`. This log is a narrative
> of what happened, not an authority on where the project stands.

- 2026-07-17 — Gate 0E remote preflight hardened and independently approved: the selection lock
  contains 20 project-development records from 20 frozen groups, the job scans all nominal RAMS
  splits without opening certification/final roles, and evidence remains text-free/private. The
  explicitly approved L40S submission was not scheduled because Hugging Face returned HTTP 402 for
  insufficient prepaid Jobs credit. No running or billable job remained. Plans 2–4 stay blocked.
  — Manager (Codex)

- 2026-07-17 — After prepaid credit was added, Gate 0E job `6a59943c85d9643ce16d7011`
  completed model generation but failed at private Dataset creation with HTTP 403 because the Jobs
  token lacks repository-create scope. Runtime was 90 seconds (about $0.05); no job remains running.
  The rerun contract now prints its text-free, hashed report to private logs before upload so this
  persistence failure cannot erase evidence again. Gate 0 remains `revise`. — Manager (Codex)

- 2026-07-17 — Ross created the private evidence Dataset. CPU Basic write preflight
  `6a5a6307bee6ee1cf4ecda9a` confirmed the Jobs token can read it but cannot commit to its main branch;
  the Hub returned HTTP 403 and allowed only pull-request creation. The four-second job stopped and
  no billable resource remains. Gate 0E stays blocked pending direct Dataset-write permission.
  — Manager (Codex)

- 2026-07-17 — After a fine-grained token was created and the Codex Hugging Face connector was
  reconnected, CPU Basic probe `6a5a6cffbee6ee1cf4ecdb23` still received the same PR-only HTTP 403.
  Reconnecting did not establish direct Dataset-write permission; whether the effective Job
  authorization came from the wrong source or insufficient scope remains unresolved. The four-second
  job stopped and no billable resource remains. — Manager (Codex)

- 2026-07-17 — Ross activated the fine-grained token in the local `hf` CLI. One CPU Basic submission
  failed before the probe because the CLI consumed the remote shell option; the corrected job
  `6a5a72b9bee6ee1cf4ecdb93` completed in eight seconds and directly committed the text-free probe to
  the private evidence Dataset. Exact-commit download reproduced SHA-256
  `feb4234ff8752370a9c45f43c1d11b1f39feb4360f12a01cf259858e90cca061`; no job remains running.
  Gate 0E persistence is unblocked and its hardened L40S rerun is next. — Manager (Codex)

- 2026-07-17 — Gate 0E L40S job `6a5a74aabee6ee1cf4ecdbbd` completed in 97 seconds and persisted
  the exact text-free report to private Hub revision `3fb7d819398bc95ebdeb1a430523905476b77d9b`.
  The Hub artifact and Git evidence copy share SHA-256
  `ac228abf40723a76f5871f30c764efea10db21258440f9f39dfa970992f9ba13`. All frozen pinning,
  grouping, alignment, determinism, malformed-output, privacy and finite-AUC checks passed; the
  independent Reviewer issued `PASS`. Twelve structural failures demonstrate weak zero-shot quality,
  while the tested model/score path is valid. Gate 0E passes; Gate 0F is next. — Manager (Codex)

- 2026-07-17 — Gate 0F L40S job `6a5a7cfad216bd6f3a1fbf0b` queued for 8,069 seconds, then ran for
  96 seconds (about $0.05). Its synthetic one-step NF4 QLoRA update, adapter-only finite gradients,
  safetensors save, adapter-hash replay, and fresh-process generation succeeded. The job stopped on
  a bit-exact generated-token mismatch across two independently quantized base-model loads, so the
  independent Reviewer issued `BLOCK` and no success report was accepted. The correction aligns the
  k-bit preparation, gradient-checkpointing, cache and generation state on both inference paths,
  retains exact equality as a hard gate, and emits a recoverable text-free diagnostic before it.
  Plan 2's parsed-output replay gate is unchanged. — Manager (Codex)

- 2026-07-17 — Corrected Gate 0F L40S job `6a5aa15dd216bd6f3a1fc41f` completed after 444 seconds
  scheduling and 95 seconds running (about $0.05). Exact adapter hashes, aligned dtype/cache/state,
  and the four-token greedy hash reproduced in a fresh process. The private Hub artifact at revision
  `840fb41e72077daa9299661b1e3ec1db2ea192f7` and the Git evidence copy share SHA-256
  `adb61606692952b132e75dabcb8b089d4aa779d45931c8f9d05e91fd383e2205`. The independent Reviewer
  issued `PASS`; no Job remains active. Gates 0A–0F pass and Gate 0 is `go`. The consolidated Plan 1
  Reviewer also issued `PASS`, completing Plan 1 and authorizing Plan 2 while Plans 3–4 remain
  sequentially blocked. — Manager (Codex)

- 2026-07-21 — **Plan 2 closed.** An independent reviewer who did not implement Plan 2 reproduced
  its evidence base from the committed commands, confirmed the two outstanding rulings (extraction
  policy C1–C7 discharged; the serving-equivalence probe PASS-with-conditions at 86.33% parity), and
  verified no token, restricted-data or sealed-label leakage. Verdict `PASS` — Plan 2 CLOSED, Plan 3
  may open. Headline: grounding, not structure, is what discriminates — QA 95.7% parseable-and-
  grounded against FS 68.1% and ZS 39.4%, on an axis structural validity could not see.
  `evidence/plan2/reviewer_record.plan2-close.json`. — Manager (Claude)

- 2026-07-22 — **Plan 3 certification executed, and returned a negative result.** The sealed
  certification split was opened exactly once, over 3,152 documents in 1,396 groups, with
  `final_reads: 0` and `shift_reads: 0`. Cost $0. **All three systems are Infeasible** at α = 0.20,
  δ = 0.05, acceptance floor 0.20; H1 and H2 both return `both_infeasible`. Under an oracle with no
  finite-sample penalty the best system accepts 2.0% of documents at 20% error against a required
  20%. *(This entry read "the failure is a capability gap, not a methodological artifact" —
  narrowed 2026-08-03, `CX-CAPGAP-01`: the penalty-free diagnostic rules out the grid and the
  bounds, not the finite-sample penalty, which is a second barrier on the method side and forbids a
  certificate the empirical curve permits.)* Independent
  post-execution review `PASS`, four corrections incorporated.
  `evidence/plan3/certification_result.json`. — Manager (Claude)

- 2026-07-22 — **ADR 0011 $0 re-analysis.** An α-frontier (the 20% floor first becomes
  oracle-reachable at α ≈ 0.406 for QA) and a loss-channel decomposition establishing that
  **a large grounding gain moved certifiability almost not at all** — a ~16× reduction in ungrounded
  spans moved the certifiable frontier by +0.017 for QA and 0.000 for both baselines. (This entry
  read "grounding and certifiability are orthogonal" until 2026-08-02, when the claim was narrowed
  to a dissociation; independence was never tested.) The WikiEvents second arm was
  **withdrawn, not deferred**: the method needs 1,386 groups and the corpus has 246 documents.
  Independent review over four passes, opening at `BLOCK` — it found a `--roles` hole by which the
  analysis commands could have opened the sealed `final` split while the artifact attested
  `final_reads: 0` — and closing with the publication condition lifted. — Manager (Claude)

- 2026-07-28 — **Gate-state and release-hygiene sweep.** The README was corrected: it asserted a
  Plan 1 gate state while the records said Plan 1 complete, Plan 2 closed, Plan 3 executed.
  `CX-COST-01` was re-evidenced after review found it cited a forecast rather than a spend record. A
  first draft of the write-up was produced and independently reviewed (`BLOCK`, then
  PASS-WITH-NITS). `main` was merged, having sat eleven days behind the branch that corrected all of
  it. Three independent `BLOCK` verdicts across the day, all on implementer error, none on the
  science. — Manager (Claude)

- 2026-07-29 — **Plan 4 opened by owner authorisation**, while Plan 3 still had no close record — an
  override of the gated sequence rather than a satisfied gate, recorded as G1. The Plan 4 accepted
  plan's inherited-status line was reconciled by dated amendment with its hash pin moved in the same
  commit. A proposed staged-release amendment was **REJECTED**; the seven-item minimum stands.
  Decisions on reviewer records, description and topics were ruled; visibility was routed as its own
  question. This log was brought current, and `evidence/gate_state.json` was created so gate state
  has one derived home instead of being asserted in prose across four documents. Plan 3's close is
  under independent review as of this entry. — Manager (Claude)
