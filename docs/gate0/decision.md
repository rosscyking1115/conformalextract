# Gate 0 decision

**Decision: revise**

Gates 0A–0E pass for private research. Gate 0F cannot start because the installed Hugging Face CLI
is not authenticated. The paid smoke is already restricted to synthetic text, the immutable Qwen
revision, L40S first, a hard 20-minute timeout, and a projected maximum below $1 at the last observed
price. Live price and hardware availability will be refreshed immediately before submission.

Plans 2–4 remain blocked. This is an evidence state, not a failure claim.

| Gate | Status | Required evidence |
|---|---|---|
| 0A licences | pass for private research | public text-bearing redistribution remains blocked |
| 0B grouping/sample feasibility | pass | 3,988 RAMS groups; 1,396 certification groups; nine-candidate theorem precondition 1,386 |
| 0C evaluator | pass | 32 automated tests plus 25 independent real-example adjudications and official scorer replay |
| 0D statistics | pass | preferred and conservative implementations; 2,000 grouped replicates pass |
| 0E model/score | pass | pinned revision/tokenizer/runtime, greedy decoding and completion-only transition scoring |
| 0F paid QLoRA smoke | blocked | interactive `hf auth login` required; no job has started |
