"""Enumerate every numeric leaf in the paper.

This is the *input* to `check_paper_claims.py`, and it is deliberately a separate
module so the enumeration can be inspected on its own. The scope decision it
encodes is the one that matters:

**The paper is the population, not the artifacts.** A guard scoped by what an
artifact already contains cannot see a figure that was never written into it,
which is how ``certification_sensitivity.json`` came to stamp four quantities
while the write-up quoted several it had never heard of. So the enumeration
starts from the ``.tex`` and every number it finds must be accounted for. A
figure that resolves to nothing **fails**; it is not exempted by being absent
from a list.

What is excluded, stated because a check reported wider than it runs is this
repository's recurring defect:

* everything before ``\\begin{document}`` (preamble, package options);
* LaTeX comments, and the arguments of ``\\label``/``\\ref``/``\\cite*``/
  ``\\includegraphics``/``\\bibliography``/``\\setlength``, and column
  specifications --- these are typesetting, not claims;
* ``\\appendix`` onward is **included**, because an appendix figure is still a
  figure a reader can check.

Nothing else is filtered. Model names carrying digits (``Qwen3-4B-Instruct-2507``)
and the ISO date this study read a paper on are picked up and must be declared
in the manifest like anything else --- classifying them away here would put the
decision somewhere no reviewer looks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "writeup" / "uncertainlp-2026-short.tex"

#: Arguments that are typesetting rather than claims.
_STRIP = (
    r"\\(?:citet|citep|cite|label|ref|autoref|eqref|bibliography|includegraphics|setlength)"
    r"\s*(?:\[[^\]]*\])?\{[^{}]*\}",
    r"\\begin\{tabular\}\{[^{}]*\}",
    r"\\multicolumn\{\d+\}\{[^{}]*\}",
    r"\\(?:begin|end)\{[^{}]*\}",
)

#: One token, most specific first. ISO dates and powers stay whole; thousands
#: separators are matched in both the plain and the LaTeX-escaped form.
_TOKEN = re.compile(
    r"""
    (?<![\w.])
    (
        \d{4}-\d{2}-\d{2}                      # ISO date
      | 10\^\{-\d+\}                           # power of ten, e.g. 10^{-55}
      | \d+(?:\.\d+)?\\times10\^\{-?\d+\}      # 8\times10^{-15}
      | \d{1,3}(?:(?:\{,\}|,)\d{3})+           # 1{,}396 or 1,396
      | \d+\.\d+                               # decimal
      | \d+                                    # integer
    )
    """,
    re.VERBOSE,
)


@dataclass
class Figure:
    """One numeric leaf, with every place it is written."""

    token: str
    value: str
    occurrences: list[str] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)


def _strip_comments(text: str) -> str:
    out_lines = []
    for line in text.splitlines():
        out, escaped = [], False
        for ch in line:
            if escaped:
                out.append(ch)
                escaped = False
            elif ch == "\\":
                out.append(ch)
                escaped = True
            elif ch == "%":
                break
            else:
                out.append(ch)
        out_lines.append("".join(out))
    return "\n".join(out_lines)


def normalise(token: str) -> str:
    """Canonical form of a written figure: 1{,}396 and 1,396 both become 1396."""

    return token.replace("{,}", "").replace(",", "")


def _body(text: str) -> str:
    marker = r"\begin{document}"
    index = text.find(marker)
    return text[index:] if index >= 0 else text


def extract_figures(paper: Path = PAPER) -> list[Figure]:
    """Every numeric leaf in the paper body, with context and line numbers."""

    raw = paper.read_text(encoding="utf-8")
    text = _strip_comments(raw)
    body = _body(text)
    marker = r"\begin{document}"
    offset = text[: text.find(marker) + 1].count("\n") if marker in text else 0

    scrubbed = body
    for pattern in _STRIP:
        scrubbed = re.sub(pattern, lambda m: " " * len(m.group(0)), scrubbed)

    figures: dict[str, Figure] = {}
    for match in _TOKEN.finditer(scrubbed):
        token = match.group(1)
        value = normalise(token)
        start = max(0, match.start() - 75)
        context = " ".join(body[start : match.end() + 45].split())
        figure = figures.setdefault(value, Figure(token=token, value=value))
        figure.occurrences.append(context)
        figure.lines.append(offset + scrubbed[: match.start()].count("\n") + 1)
    return list(figures.values())
