r"""The guard for the ledger fields nothing else can see.

Three guards already run over this repository and a class of defect is outside all of them **by
construction**:

* ``claims.verify_ledger`` resolves ``evidence`` paths and never opens one;
* the appendix byte-identity test compares generated output against ``render_surface``;
* ``check_paper_claims`` reads the paper.

``render_surface`` emits ``claim_id``, ``wording`` and ``limitations``. So a change to ``method``,
``scope`` or ``verified_by`` alters no rendered output, carries no path to resolve, and never
enters the paper. That is not a hypothetical: a correction to ``CX-CAPGAP-01`` was applied to
``method``, the generated appendix inherited the stale sentence byte-identically, and the guard
passed it green.

**The rendered-field set is derived, not declared.** Hardcoding ``{claim_id, wording, limitations}``
would go stale the first time somebody extended the renderer, and the guard would keep reporting on
a model of the world that had moved. Instead a probe claim is built with a unique sentinel in every
field, rendered, and the sentinels that survive *are* the rendered set. If the renderer changes,
this guard's map changes with it.

**The rule it enforces** (owner's ruling): *no UNBACKED numeral in a blind field.* A numeral is
permitted in ``method``, ``scope`` or ``verified_by`` if the same numeral appears in a **checked**
field of the same claim --- ``wording`` or ``limitations``, which the appendix guard holds
byte-identical --- or is **pinned in the paper manifest**, which ``check_paper_claims`` compares
against a committed artifact under a declared configuration.

**Backed, not exempted, and the distinction is the point.** Declared constants such as
:math:`\alpha`, :math:`\delta`, the acceptance floor and *n* pass automatically because they are
pinned, not because a list forgives them. So there is no exemption list to maintain, to mis-remember
or to quietly widen --- and this project has already had a hand-written exemption list rejected by
its own guard-the-guard for naming files that did not contain the phrase they exempted.

Structural exclusions remain for tokens that are **not numerals in the first place** --- an
identifier fragment, a date, a call signature, a formula operand, a list ordinal, a path. Those are
matched on **context, never on value**, because a rule keyed on the value is an exemption list
wearing a rule's clothes.

Restating a figure where nothing checks it is the mechanism behind ``12.9x`` and behind
``1.3-1.8%``.

Usage::

    uv run python scripts/check_ledger_prose.py            # exit 1 on any violation
    uv run python scripts/check_ledger_prose.py --map      # print the derived field map
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from conformalextract.claims import Claim, ClaimLedger, load_ledger, render_surface  # noqa: E402

LEDGER_PATH = ROOT / "evidence" / "plan4" / "claim_ledger.json"
MANIFEST_PATH = ROOT / "evidence" / "plan4" / "paper_claims.json"

#: Fields whose content is prose a reader could act on. ``evidence``/``surfaces``/``status`` are
#: structural and are checked by other means.
PROSE_FIELDS = ("wording", "scope", "method", "verified_by", "limitations")

_SENTINEL = "ZQXJ{field}ZQXJ"


def rendered_fields(surface: str = "report") -> set[str]:
    """Which prose fields ``render_surface`` actually emits, established by probe."""

    probe = Claim(
        claim_id="CX-PROBE-01",
        wording=_SENTINEL.format(field="WORDING"),
        status="verified",
        scope=_SENTINEL.format(field="SCOPE"),
        evidence=("README.md",),
        method=_SENTINEL.format(field="METHOD"),
        limitations=(_SENTINEL.format(field="LIMITATIONS"),),
        surfaces=(surface,),
        verified_by=_SENTINEL.format(field="VERIFIEDBY"),
    )
    ledger = ClaimLedger(ledger_id="probe", analysis_id="probe", claims=(probe,))
    output = render_surface(ledger, surface)
    return {
        field
        for field in PROSE_FIELDS
        if _SENTINEL.format(field=field.replace("_", "").upper()) in output
    }


#: Structural exemptions, each matched on the text AROUND the numeral.
_EXEMPT = (
    ("identifier fragment", re.compile(r"(?:CX-[A-Z0-9-]*|arXiv|ADR|sha256|[0-9a-f]{4,})[- ]?$")),
    ("date", re.compile(r"\d{4}-\d{2}-\d{2}")),
    ("call signature", re.compile(r"[A-Za-z_]\w*\s*\([^)]*$|[a-z_]+\s*=\s*$")),
    ("notation or formula", re.compile(r"[/(*+^-]\s*$|\balpha\b\s*\*?\s*$|\bdelta\b\s*/?\s*$")),
    ("enumerator", re.compile(r"\(\s*$")),
    ("ordinal in a list", re.compile(r"\b(?:Limitations?|elements?|items?|finding|R)\s*$")),
    # "Plan 4", "Gate 0", "Thm 1" name a thing; they assert no measurement.
    (
        "named phase or theorem",
        re.compile(r"\b(?:Plan|Gate|Thm|Theorem|Algorithm|Table|Figure|Section|step)\s*$"),
    ),
    ("path or filename", re.compile(r"[\w./-]*[/.][\w-]*$")),
)

_NUMERAL = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+\.\d+|\d+)")


@dataclass
class Violation:
    claim_id: str
    field: str
    numeral: str
    context: str

    def line(self) -> str:
        return f"{self.claim_id:<28} {self.field:<12} {self.numeral:<10} ...{self.context}"


def _exempt(before: str, numeral: str, after: str) -> str | None:
    if re.match(r"^[-/.]\d", after) or re.search(r"\d[-/.]$", before):
        return "part of a compound token"
    for reason, pattern in _EXEMPT:
        if pattern.search(before):
            return reason
    # "~16x" is an approximation marker on a ratio, not a stated measurement. ASCII x only:
    # the ledger uses it, and the multiplication sign would be an ambiguous-unicode trap.
    if re.match(r"^\s*x\b", after) and before.rstrip().endswith("~"):
        return "approximation marker"
    return None


def _normalise(numeral: str) -> str:
    """1,396 and 1396 are the same figure; 0.20 and 0.2 are not treated as the same token."""

    return numeral.replace(",", "")


def manifest_figures(path: Path = MANIFEST_PATH) -> set[str]:
    """Every figure the paper manifest pins, in normalised form.

    A numeral pinned there is compared against a committed artifact under a declared
    configuration on every run, which is a stronger check than anything this guard could apply.
    """

    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {_normalise(str(entry["figure"])) for entry in data.get("claims", [])}


def backing_for(claim: Claim, rendered: set[str]) -> set[str]:
    """Numerals this claim states in a CHECKED field.

    ``wording`` and ``limitations`` are held byte-identical against the generated appendix, so a
    figure appearing there is one a reader sees and a guard compares.
    """

    backed: set[str] = set()
    for field in sorted(rendered):
        value: Any = getattr(claim, field, None)
        texts = value if isinstance(value, tuple) else (value,)
        for text in texts:
            if isinstance(text, str):
                backed |= {_normalise(m.group(1)) for m in _NUMERAL.finditer(text)}
    return backed


def scan(ledger: ClaimLedger, blind: set[str], rendered: set[str]) -> list[Violation]:
    pinned = manifest_figures()
    violations: list[Violation] = []
    for claim in ledger.claims:
        backed = backing_for(claim, rendered) | pinned
        for field in sorted(blind):
            value: Any = getattr(claim, field)
            texts = value if isinstance(value, tuple) else (value,)
            for text in texts:
                if not isinstance(text, str):
                    continue
                for match in _NUMERAL.finditer(text):
                    numeral = match.group(1)
                    before = text[max(0, match.start() - 44) : match.start()]
                    after = text[match.end() : match.end() + 14]
                    if _exempt(before, numeral, after):
                        continue
                    if _normalise(numeral) in backed:
                        continue  # BACKED, not exempted
                    context = " ".join((before[-40:] + "[" + numeral + "]" + after).split())
                    violations.append(Violation(claim.claim_id, field, numeral, context))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", action="store_true", help="print the derived field map and exit")
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    args = parser.parse_args()

    # A checker with nothing to check passes vacuously. The model happens to reject an empty
    # claim list at load, so the vacuous case is unreachable -- but that is a property of the
    # model, not of this guard, and it is asserted here rather than relied on silently.
    try:
        ledger = load_ledger(args.ledger)
    except Exception as error:  # the message is the point, not the exception type
        print(f"FAIL: the ledger did not load, so nothing was checked: {error}")
        return 1
    if not ledger.claims:
        print("FAIL: the ledger defines no claims; this check would be vacuous")
        return 1

    emitted = rendered_fields()
    blind = {f for f in PROSE_FIELDS if f not in emitted}
    if not emitted:
        print("FAIL: the probe found no rendered field; render_surface may have changed shape")
        return 1
    if not blind:
        print("ok: every prose field is rendered; there is no blind class to guard")
        return 0

    if args.map:
        print("derived by probe, not declared:")
        for field in PROSE_FIELDS:
            mark = "RENDERED" if field in emitted else "blind"
            print(f"  {field:<14} {mark}")
        return 0

    violations = scan(ledger, blind, emitted)
    for violation in violations:
        print(violation.line())
    if violations:
        print(
            f"\nFAIL: {len(violations)} UNBACKED numerals in blind prose "
            f"({', '.join(sorted(blind))}). Each appears in no checked field of its own claim "
            "and is pinned in no manifest entry, so nothing compares it to anything. Back it "
            "or reference the claim that already does; do not restate it."
        )
        return 1
    print(
        f"ok: every numeral in the blind fields ({', '.join(sorted(blind))}) is backed by a "
        "checked field of its own claim or by a manifest pin."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
