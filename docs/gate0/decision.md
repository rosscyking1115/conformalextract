# Gate 0 decision

**Decision: revise**

Gates 0A–0D pass for private research. Independent preflight review blocked Gate 0F because Gate 0E
had only metadata and synthetic-logit evidence. A real local run downloaded the pinned model, but
Windows NF4 loading exited natively and BF16 loading failed with paging-file error 1455 before the
first shard completed. No generation evidence was produced. Gate 0E therefore remains blocked, and
the installed Hugging Face CLI is also not authenticated.

Plans 2–4 remain blocked. This is an evidence state, not a failure claim.

| Gate | Status | Required evidence |
|---|---|---|
| 0A licences | pass for private research | public text-bearing redistribution remains blocked |
| 0B grouping/sample feasibility | pass | 3,988 RAMS groups; 1,396 certification groups; nine-candidate theorem precondition 1,386 |
| 0C evaluator | pass | 32 automated tests plus 25 independent real-example adjudications and official scorer replay |
| 0D statistics | pass | nine-candidate adaptive/global suite; 2,000 replicates across non-monotone, boundary, unsafe and low-acceptance regimes |
| 0E model/score | blocked | real 20-example development generation requires authenticated remote Linux GPU execution |
| 0F paid QLoRA smoke | blocked | 0E must pass, then interactive `hf auth login` and live price check are required |
