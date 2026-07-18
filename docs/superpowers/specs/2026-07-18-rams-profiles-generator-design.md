# Design — RAMS→profiles generator (`build-profiles`)

**Date:** 2026-07-18 · **Status:** approved (design), pending implementation plan · **Scope:** RAMS only.

## Purpose

Produce the text-free `example_profiles.jsonl` that the existing `prepare-data` command consumes,
so real context-window evidence can be frozen (unblocking a real-distribution R0 and R1). One
`ExampleProfile` per RAMS trigger instance, emitted for **`train`/`development` roles only**. This
is the data-pipeline step currently missing between raw RAMS and `freeze_preparation_manifests`.

## Non-goals

- WikiEvents (separate later slice; its role file and KAIROS ontology differ).
- Any GPU or paid job (tokenization is CPU, tokenizer-only).
- Building prompts/demonstrations for FS, or generating predictions (Plan 3).
- Changing the frozen prompt template, the `ExampleProfile` schema, or the context policy.

## Inputs (all local; raw text is git-ignored)

| Input | Source | Notes |
|---|---|---|
| Raw RAMS | `data/raw/rams/RAMS_1.0c.tar.gz` | `.jsonlines` per split; restricted text — extracted to a temp dir, read, then deleted |
| Ontology | `RAMS_1.0c/scorer/event_role_multiplicities.txt` (inside the archive) | `event_type role mult role mult …` → `event_type → allowed_roles` |
| Role assignment | `data/private/splits/rams_roles.jsonl` | 9,124 lines `{document_id, group_id, role, schema_version}`; `document_id` = per-trigger RAMS instance key, grouped by `group_id` (source doc) |
| Tokenizer | `data/private/qwen-metadata/` | Qwen3-4B tokenizer, loaded on CPU via `transformers`/`tokenizers` |

## Output

`data/private/plan2/example_profiles.jsonl` (git-ignored), one `ExampleProfile` per emitted
instance. `ExampleProfile` (frozen, `preparation.py`): `example_id_hash`, `document_id_hash`,
`group_id_hash`, `frame_id_hash`, `data_role`, `event_type`, `argument_roles`, `prompt_tokens`,
`completion_tokens`, `prompt_masked_tokens`, `completion_supervised_tokens`.

## Components (each independently testable)

1. **`parse_rams_instance(record)` → structured instance**: source-doc id, flattened document word
   tokens, `event_type`, trigger half-open span (via existing `rams_inclusive_to_half_open`),
   arguments as `(role, span)`. Empty-gold = no `gold_evt_links`; multi-role = multiple links.
2. **`load_event_ontology(text)` → dict[event_type, tuple[str, …]]**: parse the multiplicities file.
3. **`render_prompt(...)` / `render_completion(...)`**: render by filling the **existing frozen
   template file** `docs/gate0/prompt-template.md` (the one `PromptManifest.zero_shot_template_sha256`
   hashes) — never a new inline template string, so rendered prompts can't drift from the hashed
   template. The gold completion is `{"arguments":[…]}` (empty → `{"arguments":[]}`), with
   `argument_roles` and completion arguments emitted in a **deterministic order** (ontology role
   order, ties broken by span start) so the jsonl is byte-reproducible.
4. **`profile_counts(prompt, completion, tokenizer)`**: `prompt_tokens`, `completion_tokens`;
   completion-only masking ⇒ `prompt_masked_tokens = prompt_tokens`,
   `completion_supervised_tokens = completion_tokens` (satisfies the `MaskManifest` invariant).
5. **`instance_hashes(...)`**: deterministic SHA-256 over ids only (never content), with an explicit
   mapping (the `rams_roles.jsonl` naming is confusing so it is pinned here):
   - `rams_roles.document_id` = the **per-trigger RAMS instance key** (9,124 of them).
   - `rams_roles.group_id` = the **source-document group** — the **aggregation unit** (~3,988) that
     Plan 2's `aggregate_document_prediction` folds frames back into.
   - Therefore: `document_id_hash = sha256(instance_key)` (the RAMS instance is RAMS's "document",
     matching how `_split_summary` counts per-trigger lines as documents);
     `group_id_hash = sha256(group_id)` (the true source-doc aggregation unit);
     `frame_id_hash = sha256(f"{instance_key}#frame")` and
     `example_id_hash = sha256(f"{instance_key}#example")` — **disjoint by suffix** so the two fields
     stay semantically distinct across slices (WikiEvents may be non-1:1) and no downstream code can
     assume they are equal.
   - **⚠ Aggregation-key rule (closes the naming trap this section exists to fix):** the
     whole-document prediction/certification aggregation key is **`group_id_hash`**, NOT
     `document_id_hash`. `document_id_hash` is the frame-level per-trigger RAMS-instance id and must
     never be used as the aggregation key. Plan 2's `aggregate_document_prediction` and the split use
     "document" to mean the per-trigger instance, whereas the *aggregation unit* is the source-doc
     group — so wiring `FrameGeneration.document_id` from `document_id_hash` would fold 9,124
     singletons and silently defeat aggregation. Whoever wires Plan 3 generation must map the
     aggregation/binding key from `group_id_hash`.
6. **`build_profiles(...)`**: orchestrates — join instances to roles, drop sealed roles, emit
   train/development `ExampleProfile`s. CLI seam: `build-profiles` in `cli.py`.

## Data flow

extract archive (temp) → for each train/development instance: parse → render prompt+completion →
tokenize+count → hash ids → `ExampleProfile` → write jsonl → delete temp extraction.

## Privacy invariant (must not break)

The generator reads restricted RAMS text but the only persisted output is text-free profiles:
hashes + ontology labels (`event_type`, `argument_roles`) + integer counts. Grounded argument text
and document tokens are used only transiently for rendering/tokenization and never written. Enforced
by a test that scans the serialized output for source token strings and finds none. Sealed roles
(`certification`/`final`/`shift`) are dropped at generation, not merely later.

## Error handling (fail loud — a silent skip would bias a frozen evidence set)

- **Ontology-coverage preflight** *before* the main build: assert the ontology covers the full RAMS
  event-type set and every gold role, so a halt during the build means a genuine per-instance anomaly
  and not a systematic vocabulary mismatch. A missing event type or role here fails fast with the
  offending label(s).
- Per-instance errors raise with **the instance key AND a reason tag** — one of `bad_span`
  (trigger/argument span out of range), `unknown_event` (event type absent from the ontology),
  `unknown_role` (gold role not allowed for the event type), or `unknown_data_role` (role outside the
  five known roles).
- **Conservation assertion:** `emitted + sealed_dropped == total_instances` exactly (for this
  `rams_roles.jsonl`: 4,068 train + 933 development = **5,001 emitted**; 3,152 certification + 971
  final = 4,123 sealed-dropped; no `shift` present; 5,001 + 4,123 = 9,124). Catches join bugs for free.
- Refuse to overwrite an existing output file (mirror `freeze_preparation_manifests`).

## Testing (synthetic RAMS-shaped fixtures; no real restricted text)

- parser: triggers/args/spans extracted; inclusive→half-open correct.
- empty-gold → `argument_roles == ()` and completion `{"arguments":[]}`.
- multi-role → `argument_roles` = all roles for the trigger.
- masking invariant: `prompt_tokens == prompt_masked_tokens`, `completion_tokens == completion_supervised_tokens`.
- sealed roles excluded from output; only train/development emitted.
- hashes deterministic across runs; **output scanned for source token text → none present**.
- each emitted record validates as `ExampleProfile`.
- end-to-end: generated profiles are accepted by `freeze_preparation_manifests` (with the other
  synthetic manifest inputs), producing the seven manifests.
- **ontology-coverage preflight** fails fast on a fixture whose event type/role is absent from the
  ontology; per-instance errors carry the instance key + the correct reason tag.
- **conservation**: emitted + sealed-dropped == total instances on the fixture.
- **template drift guard**: `render_prompt` fills the frozen `docs/gate0/prompt-template.md`; a test
  asserts the rendered structure matches the frozen template (not a divergent inline string).
- **determinism**: two runs over the same fixture produce byte-identical jsonl (role/argument order).

## Review gate (2026-07-18) — PASS-WITH-NITS, resolved

Independent verification against the repo + data (not the narrative) confirmed every load-bearing
claim: id counts (9,124 / 3,988), the `rams_roles` fields, the `ExampleProfile` schema, the existing
`rams_inclusive_to_half_open` helper, the archive layout, and that the output path is exactly
`prepare-data`'s `profiles` default (feeds the existing consumer, same `rams_roles.jsonl` as
`split_assignment`). Resolutions folded in above: (1) the **`document_id_hash` aggregation-key trap**
— aggregation keys on `group_id_hash`, never `document_id_hash`; (2) example/frame hashes made
**disjoint-by-suffix**; (3) fail-loud kept, with an **ontology-coverage preflight**, reason-tagged
errors, and a **conservation assertion**; (4) render from the **frozen template file**; (5)
**deterministic** role/argument ordering.

## Acceptance

`build-profiles` turns real RAMS + the role assignment into a text-free `example_profiles.jsonl`
that `prepare-data` accepts; all tests green (ruff/mypy clean); no source text in the output; sealed
roles never emitted; no GPU/paid work.
