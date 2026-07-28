# Plan 2 focused reviewer brief — output-extraction policy for ZS/FS baselines

Purpose: give a reviewer who did **not** implement Plan 2 a self-contained basis to rule on a
proposed **evaluation change** discovered after the prediction-generation run. Per `CLAUDE.md`,
"changes to evaluation, label access, certification, or release policy require an independent
review." The implementer has **not** applied the change; the parser is untouched pending this
ruling.

This is a focused review. It does **not** re-open the Plan 2 PASS recorded at `8e5a2c8`
(`evidence/plan2/reviewer_record.v2.json`).

## What happened

Job `6a5e5724d09dc1f57c6bd938` (l4x1, ~14h, ~$11.2) generated ZS/FS/QA × 9,124 RAMS trigger
frames. All three arms persisted to the private evidence Dataset before the job crashed:

| Arm | Path (`rosscyking/conformalextract-evidence`) | Records | sha256 |
|---|---|---|---|
| ZS | `plan2/predictions/zs.v1.jsonl` | 9,124 | `ac5f7c31549c33fa5dc0fb0530ebc1c8066f7bfd3aea7763460482c3464dc862` |
| FS | `plan2/predictions/fs.v1.jsonl` | 9,124 | `07b886bc37e8fe484dbaad023964b4e1dd93da3409144ab2ba1346dd08c02225` |
| QA | `plan2/predictions/qa.v1.jsonl` | 9,124 | `036f8f08dcbe7587c19def951f81e62e4be0a5de1485b406c64514d03bf721f3` |

Each arm: 9,106 generated + 18 `context_overflow` (identical frame sets across arms, per the
job's design). Decoding: greedy (`temperature=0`), `max_new_tokens=256`, `logprobs=1`.

**The crash** (implementer error, disclosed): after the QA arm persisted, the fresh-process
serving-equivalence probe subprocess exited 1 — it loads a second 4-bit model while the parent
vLLM engine still holds `gpu_memory_utilization=0.90` on a 24GB L4, so the child OOMs. The
engine was never torn down first. Consequence: the aggregate report was never uploaded
(recomputable locally at $0) and the serving-equivalence probe never ran. The job then hung
`RUNNING` on the orphaned engine subprocess and was cancelled to stop billing.

## The finding under review

Under the **frozen** parser (`src/conformalextract/parsing.py::parse_generated_frame`, strict
`json.loads` of the entire `raw_output`), structural validity is:

| Arm | Bare `json.loads` succeeds |
|---|---|
| ZS | **0 / 9,106** |
| FS | **0 / 9,106** |
| QA | 9,091 / 9,106 (99.8%) |

The cause is **not** that the base model failed the task. Verbatim samples:

- **ZS** prepends an instruction echo, then emits correct JSON, and stops cleanly
  (`finish_reason=stop`):
  `'Only return the JSON object, nothing else.\n\n{"arguments":[{"role":"victim","start":42,...}]}'`
- **FS** emits a correct JSON object **first**, then `\n\n`, then continues generating a
  *fabricated next example* until it hits the 256 cap (`finish_reason=length`, all 9,106):
  `'{"arguments":[{"role":"victim",...}]}\n\nYou extract grounded event arguments for one given trigger.\n\nEvent type: ...'`
  The two frozen demonstrations taught the model that `completion\n\n` is followed by another
  prompt. **The job set no stop sequence — an implementer bug, not a model failure.**
- **QA** emits bare JSON and stops. Unaffected.

## Proposed change (NOT applied)

Freeze a **first balanced top-level `{…}` object** extraction step, applied **identically to all
three arms**, before the existing strict parse. Brace-matching ignores string contents and
escapes. Measured recovery from the already-saved outputs:

| Arm | First object closed | Schema-valid (`{"arguments":[...]}`) | No closed object (stays a failure) |
|---|---|---|---|
| ZS | 8,966 (98.5%) | **8,965 (98.5%)** | 140 (1.5%) |
| FS | 9,106 (100%) | **9,105 (100.0%)** | 0 |
| QA | 9,105 (100%) | 9,091 (99.8%) | 1 |

Note this fixes only the **structural** stage. The parser still validates every span against the
source document tokens; grounding failures are unaffected, and final accepted rates will be lower.

### The case for

- Under greedy decoding the tokens forming the first JSON object are **identical** whether or not
  a stop sequence halts generation afterward. So extraction from saved output is mathematically
  equivalent to regenerating the baselines with a correct stop sequence — at $0 instead of ~$3–4
  from the ~$6.6 remaining.
- It is model-agnostic and uniform; it corrects harness artifacts, not model errors.
- Genuine failures are preserved: the 140 ZS records that never close an object remain
  structural failures.
- Certifying on the current outputs would report FS at ~0% structural success when the model
  actually produced the correct answer and the harness discarded it — an indefensible baseline.

### The case against (argue this seriously)

- **The policy was chosen post-hoc, after seeing that it helps.** The pre-registered artifact was
  the strict parser. Freezing a new rule once outcomes are visible is exactly the degree of
  freedom pre-registration exists to remove — even when applied uniformly.
- One could hold that **format adherence is part of the task**: "an untrained base model cannot
  reliably emit parseable grounded output; QLoRA fixes it" is itself a legitimate, publishable
  finding, and lenient extraction erases it.
- The change is not symmetric in effect: it rescues ~98–100% of the baselines and ~0% of QA, so
  it materially narrows the very gap the Plan 3 hypotheses (H1/H2) test.
- A reviewer may reasonably prefer **regeneration with corrected decoding** so no post-hoc
  transformation sits between the model and the evidence, accepting the cost.

## Reproduce independently (do not take the implementer's word)

Requires read access to the private evidence Dataset. This measures only; it applies nothing.

```bash
uv run python - <<'EOF'
import hashlib, json
from pathlib import Path
from huggingface_hub import hf_hub_download

def first_balanced_object(s):
    start = s.find("{")
    if start < 0: return None
    depth = 0; in_str = False; esc = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': in_str = False
        else:
            if c == '"': in_str = True
            elif c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0: return s[start:i+1]
    return None

for sysid in ("zs", "fs", "qa"):
    p = hf_hub_download("rosscyking/conformalextract-evidence",
                        f"plan2/predictions/{sysid}.v1.jsonl", repo_type="dataset")
    data = Path(p).read_bytes()
    print(sysid, "sha256", hashlib.sha256(data).hexdigest())
    rows = [json.loads(l) for l in data.decode("utf-8").splitlines()]
    gen = [r for r in rows if r["status_hint"] == "generated"]

    def schema_valid(text):
        if text is None: return False
        try: d = json.loads(text)
        except json.JSONDecodeError: return False
        return isinstance(d, dict) and isinstance(d.get("arguments"), list)

    strict = sum(1 for r in gen if schema_valid(r["raw_output"]))
    extracted = sum(1 for r in gen if schema_valid(first_balanced_object(r["raw_output"])))
    print(f"  n={len(gen)} strict_json={strict} first_object_schema_valid={extracted}")
EOF
```
Expected: ZS `strict=0 extracted=8965`, FS `strict=0 extracted=9105`, QA `strict=9091
extracted=9091`. Better still, write your own extractor — the point is not to reuse implementer
code, and a bug in the matcher above is precisely one of the things worth catching.

Also verify yourself:
- The three sha256 values above match what you download.
- `git log` shows **no** commit applying an extraction step to `parsing.py` before this ruling.
- No sealed label (`certification`/`final`/`shift` gold) has been read: prompts are rendered from
  `evt_triggers` + `sentences` only, and the string `gold_evt_links` does not appear in
  `jobs/plan2_prediction_generation.py`. Confirm the policy is being frozen **before** any
  sealed-label access.

## Reviewer challenge list

- Can you construct a `raw_output` where first-object extraction accepts something the model did
  **not** intend as its answer (e.g. a JSON object appearing inside the ZS preamble, or a
  demonstration echoed before the answer)? Sample the ZS records with the longest preambles.
- Is the brace matcher correct under escaped quotes, nested objects, and unicode? Find a
  counterexample.
- Does extraction ever change a **grounding** outcome, or only a structural one?
- Are the 18 `context_overflow` frames genuinely identical across the three arms? (Verify by
  `instance_key` set equality — the comparison's validity depends on it.)
- Quantify the asymmetry: what does the QA-minus-baseline gap look like under strict parsing vs
  under extraction? If the ruling changes the sign or significance of H1/H2, say so explicitly.
- Is 256 the right cap given FS ran to it every time? Does the 1.5% ZS non-closure indicate the
  cap, or degenerate rambling?

## Decision requested

1. **Extraction policy** — one of:
   - `adopt` — freeze first-balanced-object extraction, uniform across arms, recorded in an ADR
     that discloses the post-hoc discovery. Certification proceeds from the saved predictions.
   - `regenerate` — reject post-hoc transformation; require ZS+FS re-generation with corrected
     decoding (~$3–4 of the ~$6.6 remaining, needs separate Ross approval to spend).
   - `strict` — keep the frozen parser; report ZS/FS near-zero structural success with the cause
     documented.
   - `revise` — the framing or evidence above is insufficient; state what is missing.
2. **Serving-equivalence probe** — `require` a fixed standalone probe run (~$0.30) before the
   Plan 2 close, or `descope` it with written justification (R2 already proved fresh-process
   *reload* equivalence via greedy-hash match at `evidence` — vLLM-vs-transformers *parsed-output*
   parity would remain an untested residual).

Record the verdict in `evidence/plan2/reviewer_record.extraction-policy.json` with your identity,
the reviewed commit, and the evidence you gathered yourself. A ruling against the implementer's
recommendation is an expected, safe outcome — do not adopt to unblock the schedule.
