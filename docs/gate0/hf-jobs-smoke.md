# Gate 0F Hugging Face Jobs smoke

Status: blocked pending interactive Hugging Face authentication and live hardware/price check.

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

