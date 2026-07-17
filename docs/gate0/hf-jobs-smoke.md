# Gate 0F Hugging Face Jobs smoke

Status: Gate 0E passed independently; Gate 0F pending focused review and submission.

Authentication is confirmed as `rosscyking`. On 2026-07-17 the independently approved Gate 0E
submission was attempted only after a live L40S price check ($1.80/hour), but the Hub returned HTTP
402 before scheduling because the prepaid credit balance was insufficient. A later funded Gate 0E
attempt completed model generation but could not create the evidence Dataset with its Jobs token.
The hardened rerun prints text-free evidence to private job logs before upload and skips repository
creation by default; it still requires write permission to a Dataset created by Ross. Ross created
the private `rosscyking/conformalextract-evidence` Dataset, and a CPU Basic write preflight confirmed
that the Jobs token can read it. Direct upload still returned HTTP 403, with the Hub permitting only
pull-request creation. The frozen Gate 0 evidence contract requires direct immutable persistence;
the PR-only path is not treated as a passing substitute. After the Codex Hugging Face connector was
reconnected following fine-grained token creation, a second CPU Basic probe returned the same HTTP
403. Reconnecting did not establish direct Dataset-write
permission; the effective Job authorization remained PR-only, so its authentication source or scope
still required resolution. Ross then activated the fine-grained token in the local `hf` CLI. After
one command-transport failure that did not execute the probe, CPU Basic job
`6a5a72b9bee6ee1cf4ecdb93` completed a direct write. The exact private Dataset commit
`b42cefa8fefb9efcb5d1576312617aecea7d585c` was downloaded and its text-free artifact independently
matched SHA-256 `feb4234ff8752370a9c45f43c1d11b1f39feb4360f12a01cf259858e90cca061`. The
authenticated local CLI is therefore the approved submission path for the Gate 0E rerun. See
`evidence/gate0/hf_jobs_submission_attempts.json`.

The local-script CLI transport could not stage to the private `jobs-artifacts` bucket, so no Job was
created and no charge accrued. The reviewed script was then submitted inline without that staging
dependency. L40S job `6a5a74aabee6ee1cf4ecdbbd` completed in 97 seconds (92 running; estimated
$0.05), persisted `gate0/model_score_smoke.v3.json`, and left no running Job. The private Hub artifact
and Git evidence copy both hash to
`ac228abf40723a76f5871f30c764efea10db21258440f9f39dfa970992f9ba13`. The independent Reviewer
issued `PASS`. Twelve of 20 outputs were ungrounded-span structural failures and correctly received
loss 1/worst confidence; this is weak zero-shot quality, not a broken model/score path. The provisional
`mean` confidence winner is not frozen until full grouped development predictions exist.

The prepared job is `jobs/gate0_qlora_smoke.py`. It uses only synthetic text, pins the Qwen Hub
revision and runtime versions, loads NF4 4-bit weights, attaches rank-16/alpha-32/dropout-0.05
`all-linear` LoRA, performs one completion-only gradient step, verifies all trainable parameters have
gradients, saves safetensors, frees the first model, and launches a fresh process to reload and greedily
generate. Logs contain only hashes, counts, loss and revision—not credentials or generated text.

Planned Gate 0F submission after focused review and immediately refreshed pricing:

```console
hf jobs uv run jobs/gate0_qlora_smoke.py --flavor l40sx1 --timeout 20m --detach
```

At the last documented L40S price of $1.80/hour, the hard 20-minute timeout projects at most $0.60.
That figure is not approval evidence and must be rechecked immediately before submission. The job ID,
terminal status, logs, actual duration/cost, adapter hashes, and confirmation that no billable resource
remains will be frozen into Gate 0 evidence.
