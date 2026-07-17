# PMO progress

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
