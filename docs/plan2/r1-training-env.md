# R1/R2 frozen training environment (gate G3f)

Pins the training stack for the paid R1/R2 QLoRA runs so a run is reproducible and NF4 numerics
don't drift across library versions (frontier check, cluster B). Baseline = the exact stack that
trained the Gate 0F QLoRA smoke successfully (`jobs/gate0_qlora_smoke.py`, independently PASSed),
so it is known-good on the HF Jobs GPU image.

## Verified-good base (from Gate 0F)
```
accelerate==1.14.0
bitsandbytes==0.49.2
huggingface-hub==0.36.2
numpy==2.5.1
peft==0.19.1
safetensors==0.8.0
torch==2.13.0
transformers==4.57.6
```

## Open decision before R1 (do not pick unilaterally)
The Gate 0F smoke used a **raw transformers + peft** training loop with manual completion-only
masking. The frontier check (cluster B) recommends **TRL `SFTTrainer`** with native
`completion_only_loss` instead (cleaner, first-party). If R1 uses TRL, add a pinned `trl==<ver>`
and re-verify the stack resolves on the L4 image — treat the version pin like R0's vLLM lesson
(verify against the live image; the first smoke doubles as the check). Either way, the G3
pre-flight (`validate_training_preflight`) enforces `max_length == context_tokens`, the learning
rate, the pad token, and the pinned tokenizer revision before the run.

## R0-derived HF-Jobs recipe carried into R1
- Token needs **Write** scope; confirm prepaid credit (else 402).
- Pin deps tightly but avoid over-constraining transitive deps (the R0 uv-resolution failure).
- The slim uv image lacks `nvcc`; training on transformers+peft doesn't need it, but if a
  library JIT-compiles a kernel, either disable that path or use a CUDA-devel/framework image.
- Submit `--detach` and poll with `PYTHONUTF8=1` (Windows console charmap-crashes on streamed logs).

## Still blocked before R1
1. **Real `prepare-data`** needs `example_profiles.jsonl` — the RAMS→profiles generator
   (parse trigger frames/args, build prompts from the frozen template, tokenize with the pinned
   Qwen tokenizer, emit text-free token/masking counts) does not exist yet. This is the next
   substantial CPU build; it reads restricted text and must output only metadata.
2. Re-run R0 with the real frozen prompt-length distribution (only improves the margin).
3. Decide the TRL-vs-raw training approach and draft the R1 job for approval.
