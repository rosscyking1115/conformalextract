# ACL style files — fetched, not vendored

- Date fetched: **2026-08-02**
- Authorised by the owner on 2026-08-02, with the condition that the licence be checked before
  anything was committed.
- Local (gitignored) destination: `docs/writeup/acl-template/`

## The licence finding, which decided this

**The upstream repository declares no licence.** `GET /repos/acl-org/acl-style-files` returns
`"license": null`, there is no `LICENSE` file in the tree, and the README contains no grant of
redistribution rights. What the README does contain is a restriction — *"Authors may not modify
these style files or use templates designed for other conferences."*

No declared licence means default copyright, which means **no right to redistribute**. The files are
therefore **not committed to this repository** and `docs/writeup/acl-template/` is gitignored. That
is the conservative reading and it is the one the owner's instruction asked for: vendor only if the
licence permits, otherwise document the fetch.

This costs nothing. Anyone typesetting the paper runs the command below and gets byte-identical
files.

## A correction to the instruction, for the record

There is no file named `acl_latex.sty`. The style file is **`acl.sty`**; `acl_latex.tex` is the
template *document* that loads it. Both are fetched below.

## Exact fetch, pinned

Upstream commit **`d5adc823ff0f80f98c80405ca0ab66c68e684409`** (committed 2026-06-29T15:47:20Z),
default branch `master`. Pinning the commit rather than tracking `master` means a later upstream
change cannot silently alter the formatting of an in-flight submission.

```bash
mkdir -p docs/writeup/acl-template
for f in acl.sty acl_latex.tex acl_natbib.bst custom.bib; do
  gh api "repos/acl-org/acl-style-files/contents/$f?ref=d5adc823ff0f80f98c80405ca0ab66c68e684409" --jq '.content' | base64 -d > "docs/writeup/acl-template/$f"
done
```

Verify against what was fetched on 2026-08-02:

| File | Bytes | SHA-256 |
|---|---|---|
| `acl.sty` | 11,615 | `19dfeddc2c0e448f3926a0bef048a9db3f3611b46265b760caabd7ada4f361de` |
| `acl_latex.tex` | 14,533 | `339c9ee9705c1767d44ef24b85365c0bb8619ecc3fcf66172bf1356292389614` |
| `acl_natbib.bst` | 45,442 | `6fbb306202290f4b68e74ac1460a8b27398500cb6dfeb4492e74c457eae7cd1e` |
| `custom.bib` | 2,071 | `d76ccb30ddceb70c9e1ad0be3f43dfe301ad5765aab2c960fc830ef67bf8232a` |

```bash
uv run conformalextract hash-file docs/writeup/acl-template/acl.sty
```

Every byte count matches the size the GitHub contents API reports for that blob at that commit.

## Not fetched, and why

- `acl_lualatex.tex` — only needed for a LuaLaTeX build; the pdfLaTeX template is `acl_latex.tex`.
- `anthology.bib.txt` — a pointer file, not the anthology itself.
- `formatting.md` — the human-facing formatting guide; read it upstream rather than copying it.

## What still has to happen

Nothing here typesets the paper. `uncertainlp-2026-short.md` is still Markdown, and converting it
is a separate step that has not been done. When it is:

- The style files **may not be modified** — the README forbids it and a modified template is a desk
  reject.
- **There is no LaTeX toolchain on this machine.** Checked 2026-08-02: no `pdflatex`, `latexmk` or
  `xelatex` on `PATH`. Typesetting needs a TeX distribution (MiKTeX or TeX Live, a multi-gigabyte
  install) or an external service such as Overleaf. Having the style files is therefore necessary
  and **not sufficient**, and this is the larger of the two remaining obstacles. It is the owner's
  call which route to take; note that pasting the paper into a hosted editor sends it off this
  machine, which is a decision about a private repository's contents rather than a technicality.
- Figure 1 is a PDF at 5.5 in wide, i.e. a full-width `figure*`. At single-column width its
  annotations need larger relative type; `scripts/plot_risk_coverage.py` takes `--out` and the
  figure size is one edit.
