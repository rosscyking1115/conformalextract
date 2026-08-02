# Plan 3 §12.1 certification-only scope addendum

Date: 2026-07-30  
Authority: Ross approved: `Approve certification-only §12.1 scope.`

## Amendment

This addendum amends only the population scope of the sentence in `docs/plan3/accepted-plan.md` §12.1:

> Assign every non-zero-loss prediction one or more deterministic categories

The sentence is to be read for this authorised analysis as: assign every non-zero-loss prediction **in the already-open `certification` role, across all three systems (`zs`, `fs`, and `qa`)**, one or more deterministic categories. No other part of §12.1 is amended.

The role map is the population definition. Its current distribution supplies 3,152 `certification` records per system, but that observed cardinality is not an eligibility threshold or a stale count guard: membership is determined by the role map itself.

## Unchanged taxonomy semantics

The category vocabulary and multi-label semantics are unchanged. A prediction may receive one or more of the following deterministic categories, exactly as written in §12.1:

- invalid JSON;
- schema-invalid key/type/role;
- hallucinated or ungrounded span;
- missing gold argument;
- extra grounded but incorrect argument;
- wrong role;
- boundary/normalization mismatch;
- duplicate argument;
- coreference/alias mismatch under policy;
- empty-output collapse;
- context-window evidence loss.

Where the available evidence cannot distinguish a category, the implementation must retain that uncertainty as unsupported/unclassified rather than forcing an attribution.

## Input identity and provenance

The execution must use these locally verified input identities from `C:\tmp\conformalextract-s12-1-implementer-report.md`:

| Input | SHA-256 |
| --- | --- |
| `data/private/plan2/predictions/zs.v1.jsonl` | `ac5f7c31549c33fa5dc0fb0530ebc1c8066f7bfd3aea7763460482c3464dc862` |
| `data/private/plan2/predictions/fs.v1.jsonl` | `07b886bc37e8fe484dbaad023964b4e1dd93da3409144ab2ba1346dd08c02225` |
| `data/private/plan2/predictions/qa.v1.jsonl` | `036f8f08dcbe7587c19def951f81e62e4be0a5de1485b406c64514d03bf721f3` |
| `data/private/splits/rams_roles.jsonl` | `17718598eb279e668cf56eb33b4936a09a6898367d79838e7107c0a83906aaf3` |
| `data/raw/rams/RAMS_1.0c.tar.gz` | `cbcbec6759d520afe565d065c8086925120a42609bd0ad8ed79f49f0ccd68b54` |

The three prediction files and the role map each contain 9,124 records. The role map records 3,152 `certification` assignments for each system's aligned prediction population; it contains no `shift` records. These figures identify the checked inputs; they do not replace role-map selection with a count check.

## Required fail-closed execution boundary

The future command must accept **only** the exact role `certification`. Its role guard must reject `final`, `shift`, `development`, an empty value, a comma-separated value, and every unknown value **before any RAMS gold or source/input opening**. It must not read and then merely disclose a disallowed role.

The emitted text-free result artifact must identify the checked input hashes and, for each of `zs`, `fs`, and `qa`, report:

- `examined` count;
- `non_zero_loss` count;
- `classified` count; and
- `unsupported_or_unclassified` count.

Any zero-capable check in the command or its verification must also report how many items it examined, so zero never means both “clean” and “nothing was scanned”. The role guard must be adversarially proven on the actual command path using disallowed values and non-existent input paths, demonstrating that rejection precedes all file access.

## Interpretation and retained boundaries

Finding O2 was reworded before this measurement. This certification-only analysis cannot be read as confirmation of the withdrawn wording. Any stronger statement is a new claim and needs independent review.

Plan 3 §12.2 remains moot/descoped and is not executed. Plan 3 §12.3 remains binding, including its limit on causal attribution from examples or a taxonomy.

This addendum does not close Plan 3, start or resume Plan 4, authorise public claims, or authorise execution by itself.

## Proposed future execution command

The repository has no taxonomy CLI command today. The following is a **target interface**, not an executable current command; it must be implemented and independently reviewed before it can be run.

```text
uv run conformalextract failure-taxonomy --roles certification --out evidence/plan3/failure_taxonomy.certification.json
```

## Preconditions for any future execution

Execution remains blocked until all of the following are true:

- this addendum has independently PASSed and has then been applied;
- the command implementation has independently PASSed;
- a fresh routing verdict permits the named action;
- required verification is clean;
- the repository is clean;
- the final/shift guard has been adversarially proven; and
- the action requires no paid, network, or model activity.
