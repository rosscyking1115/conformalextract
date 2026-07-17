# Gate 0 decision

**Decision: revise**

Gates 0A–0D pass for private research. Independent preflight review blocked Gate 0F because Gate 0E
had only metadata and synthetic-logit evidence. A real local run downloaded the pinned model, but
Windows NF4 loading exited natively and BF16 loading failed with paging-file error 1455 before the
first shard completed. Authentication is now confirmed as `rosscyking`, and the leakage-safe remote
Gate 0E contract received an independent submission `PASS`. The explicitly approved L40S submission
was initially not scheduled because the prepaid Jobs credit balance was insufficient. After credit
was added, job `6a59943c85d9643ce16d7011` loaded the pinned model and reached evidence persistence,
which proves the generation stage completed, but the job token lacked permission to create the
private evidence Dataset. The 90-second job ended `ERROR` with HTTP 403; its report had not yet been
printed and was lost. Ross then created the private Dataset. CPU Basic job
`6a5a6307bee6ee1cf4ecda9a` verified that the Jobs token can read the repository but cannot commit to
its main branch: upload returned HTTP 403 and offered only a pull-request path. Gate 0E therefore
remains blocked pending direct Dataset-write permission for the Job token, then one short rerun.
After the Codex connector was reconnected following creation of a new fine-grained token, a second
CPU Basic probe returned the same PR-only HTTP 403. Effective direct-write authorization was not
established; whether the cause is the authentication source or its scope remains unresolved.

Plans 2–4 remain blocked. This is an evidence state, not a failure claim.

| Gate | Status | Required evidence |
|---|---|---|
| 0A licences | pass for private research | public text-bearing redistribution remains blocked |
| 0B grouping/sample feasibility | pass | 3,988 RAMS groups; 1,396 certification groups; nine-candidate theorem precondition 1,386 |
| 0C evaluator | pass | 32 automated tests plus 25 independent real-example adjudications and official scorer replay |
| 0D statistics | pass | nine-candidate adaptive/global suite; 2,000 replicates across non-monotone, boundary, unsafe and low-acceptance regimes |
| 0E model/score | blocked | grant the Job token direct Dataset-write permission, then rerun the hardened L40S smoke |
| 0F paid QLoRA smoke | blocked | 0E must pass; a new live price check and independent Gate 0F review remain required |
