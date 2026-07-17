# Gate 0F Hugging Face Jobs smoke

Status: blocked pending direct Dataset-write permission for the Job token.

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
still requires resolution. See
`evidence/gate0/hf_jobs_submission_attempts.json`.

The prepared job is `jobs/gate0_qlora_smoke.py`. It uses only synthetic text, pins the Qwen Hub
revision and runtime versions, loads NF4 4-bit weights, attaches rank-16/alpha-32/dropout-0.05
`all-linear` LoRA, performs one completion-only gradient step, verifies all trainable parameters have
gradients, saves safetensors, frees the first model, and launches a fresh process to reload and greedily
generate. Logs contain only hashes, counts, loss and revision—not credentials or generated text.

Planned submission after authentication and immediately refreshed pricing:

```console
hf jobs uv run jobs/gate0_qlora_smoke.py --flavor l40sx1 --timeout 20m --detach
```

At the last documented L40S price of $1.80/hour, the hard 20-minute timeout projects at most $0.60.
That figure is not approval evidence and must be rechecked immediately before submission. The job ID,
terminal status, logs, actual duration/cost, adapter hashes, and confirmation that no billable resource
remains will be frozen into Gate 0 evidence.
