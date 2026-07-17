# Gate 0F Hugging Face Jobs smoke

Status: Gate 0E and corrected Gate 0F passed independently; Gate 0 decision is `go`.

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
finite gradients, saves safetensors, frees the first model, and launches a fresh process to reload and
greedily generate. It refuses repository creation, public evidence repositories, existing evidence
paths, and concurrent branch changes. Logs contain only hashes, counts, loss, revision, and a
base64-encoded text-free report—not credentials or generated text. Trackio is deliberately deferred
to Plan 2's R0/R1/R2 training pipeline; Gate 0F is a single synthetic compatibility step rather than
an experiment run.

Planned Gate 0F submission after focused review and immediately refreshed pricing:

The local-script transport cannot stage through this fine-grained token's private `jobs-artifacts`
bucket. Submission therefore uses the already-proven authenticated CLI path with the reviewed script
decoded to a temporary file inside the official `uv` Docker image, an L40S flavor, a 20-minute hard
timeout, and `HF_TOKEN` injected only through the Jobs secrets mechanism.

The first Gate 0F submission, job `6a5a7cfad216bd6f3a1fbf0b`, waited 8,069 seconds for L40S
capacity, ran for 96 seconds (about $0.05), and stopped after the fresh-process reload generated a
different four-token hash from the in-memory model. All preceding checks passed, including the
one-step update, adapter-only finite gradients, safetensors save, exact saved/reloaded adapter hashes,
and fresh-process generation. The failed run did not print or persist a success report. Review
identified an inference-state mismatch: the training base had passed through
`prepare_model_for_kbit_training`, which changes non-quantized parameter dtypes, while the reload base
had not. The corrected contract prepares both bases, explicitly disables gradient checkpointing and
enables cache for both inference paths, retains exact greedy token-hash equality as a hard gate, and
prints a text-free state/dtype/hash diagnostic before that gate so another mismatch remains
recoverable. Plan 2's parsed-output replay gate is unchanged.

At the last documented L40S price of $1.80/hour, the hard 20-minute timeout projects at most $0.60.
That figure is not approval evidence and must be rechecked immediately before submission. The job ID,
terminal status, logs, actual duration/cost, adapter hashes, and confirmation that no billable resource
remains will be frozen into Gate 0 evidence.

The independently approved retry, job `6a5aa15dd216bd6f3a1fc41f`, queued for 444 seconds and ran for
95 seconds (estimated $0.0475). It passed the one-step update, completion mask, adapter-only finite
gradients, safetensors save, fresh-process reload, identical state/dtype maps, identical adapter
hashes, and identical four-token greedy hash. It persisted `gate0/qlora_smoke.v1.json` to the private
Dataset at Hub revision `840fb41e72077daa9299661b1e3ec1db2ea192f7`. Independent exact-revision
downloads reproduce SHA-256 `adb61606692952b132e75dabcb8b089d4aa779d45931c8f9d05e91fd383e2205`.
The Reviewer issued `PASS`; all Jobs are terminal and no billable resource remains.
