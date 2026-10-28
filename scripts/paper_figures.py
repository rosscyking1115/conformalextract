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
    r"\\(?:citet|citep|cite|label|ref|autoref|eqref|bibliography|includegraphics)"
    r"\s*(?:\[[^\]]*\])?\{[^{}]*\}",
    # setlength takes TWO brace groups and the length lives in the second; stripping only the
    # first leaks "4pt" into the figure list as though the paper asserted it.
    r"\\setlength\s*\{[^{}]*\}\s*\{[^{}]*\}",
    r"\\begin\{tabular\}\{[^{}]*\}",
    # multicolumn's column spec nests braces (``{@{}l}``), so a flat [^{}]* misses it and the
    # span count leaks through as if it were a figure.
    r"\\multicolumn\{\d+\}\{(?:[^{}]|\{[^{}]*\})*\}",
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
    excluded: list[tuple[str, str]] = field(default_factory=list)


#: Structural rules that decide **this occurrence is not a quantity the paper asserts**.
#:
#: The distinction these encode is the one that matters, and it is easy to lose. An EXEMPTION says
#: "this is a claim, do not check it" and is refused here always. BETTER EXTRACTION says "this was
#: never a claim" -- and ``Table 5``, the ``2507`` in a model name and a ``(2)`` row label were
#: never claims. So every rule below is stated over **context** -- position, LaTeX environment,
#: surrounding tokens -- and none is a list of values to skip. A rule keyed on the value would be
#: an exemption wearing a rule's clothes.
#:
#: They apply **per occurrence**, not per figure. A figure is dropped only when *every* place it
#: is written is structural, so a real claim can never be hidden behind a piece of typesetting
#: that happens to render the same token. That was a stated limitation of the first version: ``3``
#: is both a table row label and "3 non-failing groups", and the row label came first.
_IDENTIFIER_RUN = re.compile(r"[A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)+")
#: A name-with-an-ordinal, not a measurement: "Table 5", "Appendix A", "Mechanism 3". The paper
#: names its three mechanisms by number throughout, and those ordinals are labels for arguments,
#: not quantities the paper asserts about the world.
_LOCATOR = re.compile(r"(?:Table|Figure|Section|Appendix|Eq\.?|\\S|[Mm]echanism)[~\s-]*$")
_MATH_SYMBOL = re.compile(r"\\(?:mu|alpha|delta|rho|times|leq|geq|approx|frac)")


def _classify(text: str, start: int, end: int) -> str | None:
    """Why this occurrence is not an asserted quantity, or ``None`` if it is one."""

    token = text[start:end]
    before = text[max(0, start - 24) : start]
    after = text[end : end + 12]

    # A cross-reference locator: "Table 5", "Figure 2", "Appendix A". Never a measurement.
    if _LOCATOR.search(before):
        return "cross-reference locator"

    # Part of an alphanumeric identifier: Qwen3-4B-Instruct-2507, and only when the surrounding
    # run has at least two letter-bearing segments. "top-75" has one, so it survives -- a
    # threshold written that way is a real parameter and must not be swallowed.
    left = start
    while left > 0 and (text[left - 1].isalnum() or text[left - 1] in "-."):
        left -= 1
    right = end
    while right < len(text) and (text[right].isalnum() or text[right] in "-."):
        right += 1
    run = text[left:right]
    if _IDENTIFIER_RUN.fullmatch(run):
        segments = re.split(r"[-.]", run)
        if sum(1 for s in segments if any(c.isalpha() for c in s)) >= 2:
            return "identifier fragment"

    # An enumerated row label: parentheses containing the integer and nothing else.
    if token.isdigit() and before.endswith("(") and after.startswith(")"):
        return "enumerated row label"

    # A bin label: "6+".
    if token.isdigit() and after.startswith("+"):
        return "stratum bin label"

    # A bare single digit inside symbolic math is a formula operand, not a measurement:
    # the 1 in (1-\alpha). Decimals and thousands-separated numbers are never treated this way,
    # so $\alpha = 0.20$ and $n = 1{,}396$ both survive.
    if len(token) == 1 and token.isdigit():
        opening = text.rfind("$", 0, start)
        closing = text.find("$", end)
        if opening != -1 and closing != -1 and _MATH_SYMBOL.search(text[opening:closing]):
            return "symbolic formula operand"

    return None


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
        window = max(0, match.start() - 75)
        context = " ".join(body[window : match.end() + 45].split())
        figure = figures.setdefault(value, Figure(token=token, value=value))
        reason = _classify(scrubbed, match.start(), match.end())
        if reason is not None:
            figure.excluded.append((reason, context))
            continue
        figure.occurrences.append(context)
        figure.lines.append(offset + scrubbed[: match.start()].count("\n") + 1)

    # A figure survives if ANY occurrence is an asserted quantity. One written entirely as
    # typesetting is not a claim and is not checked; one written anywhere as a claim is.
    return [f for f in figures.values() if f.occurrences]


def excluded_occurrences(paper: Path = PAPER) -> list[tuple[str, str, str]]:
    """(token, rule, context) for every occurrence the structural rules removed.

    Exposed so the exclusions can be read and argued with. A rule nobody can inspect is an
    exemption list with extra steps.
    """

    raw = paper.read_text(encoding="utf-8")
    text = _strip_comments(raw)
    body = _body(text)
    scrubbed = body
    for pattern in _STRIP:
        scrubbed = re.sub(pattern, lambda m: " " * len(m.group(0)), scrubbed)

    out: list[tuple[str, str, str]] = []
    for match in _TOKEN.finditer(scrubbed):
        reason = _classify(scrubbed, match.start(), match.end())
        if reason is None:
            continue
        window = max(0, match.start() - 60)
        out.append(
            (match.group(1), reason, " ".join(body[window : match.end() + 30].split()))
        )
    return out
