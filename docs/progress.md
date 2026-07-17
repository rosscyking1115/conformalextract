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
