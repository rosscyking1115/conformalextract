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
3. **`render_prompt(...)` / `render_completion(...)`**: the frozen template string and the gold
   completion JSON (`{"arguments":[…]}`; empty → `{"arguments":[]}`). Deterministic serialization.
4. **`profile_counts(prompt, completion, tokenizer)`**: `prompt_tokens`, `completion_tokens`;
   completion-only masking ⇒ `prompt_masked_tokens = prompt_tokens`,
   `completion_supervised_tokens = completion_tokens` (satisfies the `MaskManifest` invariant).
5. **`instance_hashes(...)`**: deterministic SHA-256 over ids only (never content), with an explicit
   mapping (the `rams_roles.jsonl` naming is confusing so it is pinned here):
   - `rams_roles.document_id` = the **per-trigger RAMS instance key** (9,124 of them).
   - `rams_roles.group_id` = the **source-document group** — the **aggregation unit** (~3,988) that
     Plan 2's `aggregate_document_prediction` folds frames back into.
   - Therefore: `frame_id_hash = sha256(instance_key)`; `example_id_hash = sha256(instance_key)` (one
     training example per given trigger, so example ≡ frame at 1:1);
     `document_id_hash = sha256(instance_key)` (the RAMS instance is RAMS's "document");
     `group_id_hash = sha256(group_id)` (the true source-doc aggregation unit).
   - If the implementation needs example and frame hashes to differ, derive them from disjoint
     canonical strings (e.g. `f"{instance_key}#example"` vs `f"{instance_key}#frame"`) — decided in
     the plan; either way they are deterministic and content-free.
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

## Error handling

- A record whose trigger/argument spans are out of range, or an event type absent from the ontology,
  raises with the instance key (fail loud; no silent skip that would bias the profile set).
- A role in `rams_roles.jsonl` outside the five known roles → error.
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

## Acceptance

`build-profiles` turns real RAMS + the role assignment into a text-free `example_profiles.jsonl`
that `prepare-data` accepts; all tests green (ruff/mypy clean); no source text in the output; sealed
roles never emitted; no GPU/paid work.
