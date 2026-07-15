# Frozen zero-shot prompt template

```text
You extract grounded event arguments for one given trigger.

Event type: {event_type}
Trigger token span [start, end): {trigger_start}, {trigger_end}
Allowed roles: {allowed_roles_json}
Document tokens: {numbered_tokens_json}

Return one JSON object only:
{"arguments":[{"role":"<allowed role>","start":0,"end":1,"text":"<exact token text>"}]}

Use half-open token spans. Copy grounded text exactly. Do not infer an ungrounded argument.
When no argument is present return {"arguments":[]}.
```

Two-shot demonstrations are not part of this template; Plan 2 freezes them separately from the
development split and hashes their serialized form.

