# Prediction parsing under ADR 0006 — result (2026-07-21)

Reproduce with:

```bash
uv run conformalextract parse-predictions
```

Summary artifact (text-free, committed): `evidence/plan2/prediction_parse_summary.json`.
Source predictions: private evidence Dataset `plan2/predictions/{zs,fs,qa}.v1.jsonl`.
No gold label is read — grounding validates spans against **source document tokens**, so every
split including the sealed ones is safe to parse here.

## Result

All three arms, 9,124 frames each, under the uniform ADR 0006 first-object extraction policy:

| Arm | valid | valid % | content-bearing | empty | grounding failure | structural failure |
|---|---|---|---|---|---|---|
| ZS | 3,596 | 39.4% | 3,550 | 46 | **5,355** | 173 |
| FS | 6,217 | 68.1% | 3,330 | **2,887** | 2,875 | 32 |
| **QA** | **8,729** | **95.7%** | **8,277** | 452 | **340** | 55 |

Dominant failure mode is `ungrounded_span` in every arm: ZS 5,355, FS 2,875, QA 340.

## What this means

**The comparison reverses between stages, and grounding is the stage that discriminates.**

- *Structural* (post-extraction): FS 9,105 ≥ QA 9,085 > ZS 8,959 — near-saturated, no
  discrimination, exactly as ADR 0006's condition C6 predicted.
- *Grounded*: QA 8,729 ≫ FS 6,217 ≫ ZS 3,596 — a wide, consistent separation.

The baselines can produce well-formed JSON; what they cannot do is **point at the right tokens**.
They emit a `text` field that does not match the document tokens at the `start`/`end` indices they
chose — hallucinated or mis-indexed spans. The QLoRA adapter's principal learned behaviour is
therefore **grounding fidelity, not format compliance**.

**This vindicates the reviewer's ruling on its merits.** Under the pre-ADR-0006 strict parser both
baselines scored 0 structural validity, which would have conflated a missing stop sequence and an
instruction echo with an inability to extract. The uniform extraction policy separates the two
cleanly, and the result is a *more* informative finding, not a softer one: baselines are ~98–100%
well-formed but only 39%/68% grounded, against QA's 96%.

**Condition C3 matters exactly as anticipated.** FS's 6,217 "valid" frames include **2,887 empty
ones (46%)** — contentless predictions that are structurally valid and ground trivially. On
content-bearing frames FS (3,330) falls *below* ZS (3,550). Reporting FS acceptance as a single
number would credit it for saying nothing 46% of the time. It was C3, not the extraction policy
itself, that prevented a wrong conclusion here.

**The grounding separation is stark on the axis structural validity could not see:** ungrounded
spans are **QA 340 (3.7%) vs ZS 5,355 (58.7%)** — a ~16× difference.

### Stated result: few-shot prompting *harms* this task

On content-bearing frames the **zero-shot baseline beats the few-shot one** (ZS 3,550 vs FS 3,330),
and FS emits 63× more empty frames than ZS (2,887 vs 46). The two frozen demonstrations appear to
have taught the model two counterproductive behaviours: emit `{"arguments":[]}`, and continue
generating a fabricated next example. This is a genuine and slightly counterintuitive finding
about few-shot prompting for grounded event-argument extraction, and it is recorded here as a
claim in its own right rather than as an aside.

Boundaries on that claim: it holds for *these* two demonstrations, selected by the frozen
Ross-approved rule (one multi-argument plus one empty-gold frame, lowest example-id hash in each
category), under this template and this model. A different demonstration set — in particular one
without an empty-gold exemplar — might not reproduce it. The missing stop sequence contributed to
the continuation behaviour but not to the empty-frame rate, which survives extraction and is
genuine model output.

## What this is NOT

**"Valid" means parseable and grounded. It does not mean correct.** A prediction can point at real
document text and still assign the wrong role, or the wrong entity. Correctness is scored against
gold during certification; nothing here licenses a claim about extraction accuracy, and the
QA figure must not be quoted as "95.7% correct".

Nor is this certified acceptance. Certification applies the risk controller and the abstention
policy on top of these parses, against sealed labels not yet touched. H1/H2 remain open.

## Residual notes

- The 140 ZS `no_json_object` failures are the cap-truncated records disclosed under condition C5
  — a harness artifact, not a model failure.
- 18 `context_overflow` frames per arm are identical across arms and counted as explicit
  structural failures, never silently excluded.
- QA's 55 structural failures (14 `invalid_json`, 16 `invalid_span`, 6 `schema_violation`,
  1 `no_json_object`) are genuine model failures on a clean serving path.
