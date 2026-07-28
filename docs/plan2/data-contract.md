# Plan 2 data and manifest contract

`prepare-data` accepts a private JSONL of text-free trigger-frame profiles. Each profile carries
SHA-256 identities for its example, source document, duplicate group and trigger frame; a research
role; the event type; zero or more argument roles; and token/masking counts. Empty-gold frames use an
empty role tuple. Multi-role frames remain one training example and contribute to every applicable
event-role context slice. Training is per given trigger; prediction and certification aggregate all
frames back into one whole-document record.

Only `train` and `development` profiles are legal inputs. `certification`, `final` and `shift` are
sealed and cause preparation to fail. The split assignment may contain only document ID, group ID,
role and schema metadata; any text-bearing or label-bearing field is rejected. Duplicate groups may
not cross roles.

The context policy starts at 2,048 input tokens with at most 512 output tokens. It selects the lowest
rung of the ladder 2,048 / 2,560 / 3,072 / 3,584 / 4,096 / 4,608 / 5,120 / 6,144 for which exclusions
are at most 5% overall and 10% in every event-role slice. Empty-gold frames form an explicit `<EMPTY>`
slice. A changed rung requires a new R0 smoke. *(Ladder extended past 4,096 on 2026-07-19, Ross-approved
— ADR 0003: measured RAMS token counts made the per-slice limit unsatisfiable at 4,096 via tiny slices
with a single long example; at 6,144 the policy passes with 7/5,001 excluded.)*
This pre-training/R0 decision is separate from R1 changes, which are allowed only for a demonstrated
compatibility problem.

The command freezes exactly seven compact manifests: source, split, trainer, prompt, mask,
context-window and lineage. They share one immutable analysis ID and are never overwritten. Prompt,
demonstration, source-document and label content is represented only by SHA-256 hashes and aggregate
counts. The source manifest directs remote jobs to ephemeral downloads from the official URLs,
requires checksum verification before use, and forbids upload or persistence of local raw sources.

