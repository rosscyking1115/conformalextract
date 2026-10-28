"""The ledger-prose guard runs on every suite, reports its count, and may only shrink.

**Not a gate, deliberately.** There are unbacked numerals left in the blind fields and a
permanently red gate stops being read --- this project has already named that failure mode. So the
guard runs as a **ratchet**: the count is recorded here, the suite fails if it goes UP, and the
number lives in a diff where it is visible rather than in one report that scrolls away.

**It becomes a gate when the count reaches zero.** At that point ``EXPECTED_DEBT`` is 0, the
assertion below is exactly "no unbacked numeral in a blind field", and
``test_the_debt_is_zero_and_this_is_now_a_gate`` starts enforcing it. Nothing needs rewriting for
that to happen; the ratchet turns into the gate by arithmetic.

The rule, per the owner's ruling: **no UNBACKED numeral in a blind field.** A numeral is permitted
in ``method``/``scope``/``verified_by`` if it appears in a checked field of the same claim, or is
pinned in the paper manifest. Declared constants pass because they are pinned --- *backed*, not
exempted --- so there is no exemption list to maintain or mis-remember.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_ledger_prose import (  # noqa: E402
    PROSE_FIELDS,
    load_ledger,
    rendered_fields,
    scan,
)

LEDGER = ROOT / "evidence" / "plan4" / "claim_ledger.json"

#: Unbacked numerals remaining in the blind fields. **This number may only go down.**
#:
#: 46 when the rule was first implemented; 43 after the self-refuting CX-REPO-DESCRIPTION-01
#: passage was rewritten; 21 once "backed by a checked field or a manifest pin" replaced the
#: proposed exemption tiers. The remainder is dominated by CX-COST-01's per-job reconciliation,
#: whose migration to a pinned artifact is deferred.
EXPECTED_DEBT = 21


def _violations():
    ledger = load_ledger(LEDGER)
    emitted = rendered_fields()
    blind = {field for field in PROSE_FIELDS if field not in emitted}
    return scan(ledger, blind, emitted), blind


def test_the_scan_reaches_the_ledger_and_a_blind_class_exists() -> None:
    """Guard the guard: an empty ledger or an empty blind set would pass everything below."""

    violations, blind = _violations()
    assert blind, "no blind field found; render_surface may now emit everything"
    assert load_ledger(LEDGER).claims, "no claims; the count below would be vacuous"
    assert isinstance(violations, list)


def test_unbacked_numerals_in_blind_prose_do_not_increase() -> None:
    """The ratchet. Going up fails; going down is a passing state that must be recorded."""

    violations, blind = _violations()
    count = len(violations)
    detail = "\n".join(v.line() for v in violations)

    assert count <= EXPECTED_DEBT, (
        f"unbacked numerals in blind prose rose from {EXPECTED_DEBT} to {count}. A figure in "
        f"{sorted(blind)} is compared to nothing. Back it, or reference the claim that already "
        f"does.\n{detail}"
    )
    assert count == EXPECTED_DEBT, (
        f"unbacked numerals fell from {EXPECTED_DEBT} to {count} — good. Lower EXPECTED_DEBT to "
        f"{count} so the ratchet holds the gain; leaving it high lets the debt grow back silently."
    )


@pytest.mark.skipif(EXPECTED_DEBT > 0, reason="debt outstanding; the ratchet is still climbing")
def test_the_debt_is_zero_and_this_is_now_a_gate() -> None:
    """Once the count reaches zero this stops being a ratchet and starts being a gate."""

    violations, _ = _violations()
    assert not violations, "\n".join(v.line() for v in violations)
