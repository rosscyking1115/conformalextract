# Security and restricted-data policy

Report security issues privately to the repository owner. Do not open a public issue containing a
credential, restricted source text, sealed label, signed URL, or private tracking output.

- Secrets enter only through environment variables or interactive provider login.
- `data/raw`, `data/sealed`, checkpoints, adapters, and Trackio state are ignored by Git.
- Label-bearing commands require a declared role and append to a hash-linked access log.
- Artifact writers refuse overwrite by default.
- Raw RAMS and WikiEvents text is research-only and is not redistributed by this repository.

