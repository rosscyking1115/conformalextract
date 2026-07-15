# Frozen given-trigger extraction contract

Input is one normalized document and one given event trigger. Output is a compact JSON object whose
`arguments` field is always an array; the empty output is `{"arguments": []}`. Each argument contains
exactly one ontology role and one source-grounded span.

Internally, spans are half-open token intervals after Unicode NFC and CRLF/CR-to-LF normalization.
Adapters must prove a round trip to each source's original indexing before use. No semantic repair,
role invention, or fuzzy grounding is permitted during evaluation.

Arguments match one-to-one by event type, role, normalized grounded text, and normalized span.
Document loss is `1 - argument micro-F1`. Empty-gold/empty-prediction has F1 1; unmatched non-empty
cases have F1 0. Invalid JSON/schema, ungrounded spans, token-alignment failures, and other structural
failures receive loss 1 and confidence negative infinity.

Whole-document acceptance requires every frame to be structurally valid and the minimum frame
confidence to meet the selected threshold.

## Failure taxonomy

- `invalid_json`
- `schema_violation`
- `unknown_role`
- `invalid_span`
- `ungrounded_span`
- `token_alignment_failure`
- `duplicate_contradiction`
- `generation_empty`
- `runtime_failure`

