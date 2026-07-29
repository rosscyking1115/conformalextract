"""Gate state is summarised in one file, and that file must match the records.

Three stale gate-state assertions surfaced in one repository in one week — the README saying
"Plan 1 is active" while Plan 3 was executing, `docs/plan4/accepted-plan.md` opening Plan 4 still
saying Plans 1-3 were "not implemented", and `docs/progress.md` frozen at 2026-07-17 asserting
that Plans 3-4 remained blocked. Each was found by a human reading prose. Nothing in the
repository could fail on any of them, because **gate state was asserted in prose across several
documents and derived in none.**

## What this test can do, and what it cannot

**It can** hold `evidence/gate_state.json` to what the reviewer records actually attest. That gives
one place to reconcile a document against, and that place cannot drift from its sources.

**It cannot** check a prose assertion against the records. Detecting that a sentence asserts a gate
state, and what state it asserts, is natural-language work — the pattern would have to recognise
"Plan 1 is active", the blocked-plans line and "accepted in direction but not
implemented" as the same kind of statement, and would still miss the fourth phrasing nobody has
written yet. **A test that appeared to do this would be worse than none**, for exactly the reason
ADR 0011 §6 records about the pending-verification tripwire: a substance-blind rule whose name
implies coverage teaches the next reader that the hole is closed.

So the division is deliberate. The derivation below is a **gate**. `SUPERSEDED_ASSERTIONS` is a
**regression tripwire** over phrasings known to be stale — it catches their reappearance and nothing
else. Reconciling a *new* document's prose remains a manual step, which is why `REVIEW.md` carries
it as a check rather than relying on this file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE_STATE = ROOT / "evidence" / "gate_state.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _reviewer_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(ROOT.glob("evidence/*/reviewer_record*.json")):
        if path.name == "reviewer_record.template.json":
            continue
        try:
            records.append(_load(path))
        except json.JSONDecodeError:  # pragma: no cover - a malformed record fails elsewhere
            continue
    return records


def _closed_plans_from_records() -> set[str]:
    """Plans with a close record. Mechanism two of the two this repository uses."""

    closed: set[str] = set()
    for record in _reviewer_records():
        if record.get("review_kind") != "plan_close":
            continue
        plan = record.get("plan")
        verdict = str(record.get("verdict", ""))
        if isinstance(plan, str) and verdict.upper().startswith("PASS"):
            closed.add(plan)
    return closed


def _plan_one_closed_from_gate_status() -> bool:
    """Mechanism one: Plan 1's close is attested in the Gate 0 status artifact, not a record."""

    status = _load(ROOT / "evidence" / "gate0" / "gate_status.v4.json")
    return status.get("decision") == "go" and status.get("independent_plan1_verdict") == "PASS"


def test_the_derivation_finds_something() -> None:
    """Guard the guard: a glob that matched nothing would make every assertion below vacuous."""

    assert len(_reviewer_records()) >= 10
    assert _plan_one_closed_from_gate_status() is True


def test_declared_gate_state_matches_the_records() -> None:
    declared = _load(GATE_STATE)
    plans = declared["plans"]
    assert isinstance(plans, dict)

    closed_by_record = _closed_plans_from_records()
    mismatches: list[str] = []

    for name, entry in plans.items():
        assert isinstance(entry, dict)
        declared_closed = entry["state"] == "closed"
        if name == "Plan 1":
            derived_closed = _plan_one_closed_from_gate_status()
        else:
            derived_closed = name in closed_by_record
        if declared_closed != derived_closed:
            mismatches.append(
                f"  {name}: gate_state.json says state={entry['state']!r} "
                f"(closed={declared_closed}), records say closed={derived_closed}"
            )

    if mismatches:
        detail = "\n".join(mismatches)
        raise AssertionError(
            "evidence/gate_state.json disagrees with the reviewer records:\n"
            f"{detail}\n"
            "The records are the authority. Update gate_state.json to match them — and if a plan "
            "has just been closed, update it in the same commit as the close record."
        )


def test_an_override_is_only_declarable_while_the_prior_plan_is_unclosed() -> None:
    """`open_by_owner_override` is a claim about the sequence, so it must stay true of it."""

    plans = _load(GATE_STATE)["plans"]
    assert isinstance(plans, dict)
    order = ["Plan 1", "Plan 2", "Plan 3", "Plan 4"]
    for index, name in enumerate(order[1:], start=1):
        entry = plans.get(name)
        if not isinstance(entry, dict) or entry.get("state") != "open_by_owner_override":
            continue
        previous = order[index - 1]
        prior = plans.get(previous)
        assert isinstance(prior, dict)
        assert prior["state"] != "closed", (
            f"{name} is declared open_by_owner_override, but {previous} is closed — there is "
            f"nothing left to override. Change {name} to 'open'."
        )


#: Phrasings that were true once and are false now. A **tripwire**, not a gate: it catches these
#: exact strings coming back, and cannot detect a gate-state error phrased any other way.
#:
#: `permitted_in` names files where the string may appear, each with the reason — the same
#: mention-not-use structure `tests/test_internal_paths.py` uses, and for the same reason: a
#: document reporting a stale assertion has to quote it, and a dated record preserves what was true
#: on its date. Two distinct grounds appear below and the distinction matters: *historical* (the
#: string is preserved as a record of what was once asserted) and *reporting* (the string is quoted
#: in order to say it is false). Neither is a standing assertion, which is the thing being caught.
SUPERSEDED_ASSERTIONS: dict[str, dict[str, object]] = {
    "Plan 1 is active": {
        "false_since": "2026-07-17, when Gate 0 closed with a consolidated Plan 1 reviewer PASS",
        "permitted_in": {
            "REVIEW.md": "reporting — the gate cites it as the first of three instances",
            "docs/plan3/HANDOFF-2026-07-22-reanalysis.md": (
                "reporting — the dated amendment records the correction that removed it"
            ),
        },
    },
    # The en dashes below are load-bearing: these keys must match the source documents byte for
    # byte, and those documents use en dashes. Replacing them with hyphens would silently stop the
    # tripwire matching — the same class of failure as the line-wrap miss recorded in `_flat`.
    "Plans 1–3 are accepted in direction but not implemented": {  # noqa: RUF001
        "false_since": "2026-07-21, when Plan 2 closed",
        "permitted_in": {
            "docs/plan4/accepted-plan.md": (
                "historical — the original line is preserved above its 2026-07-29 amendment, "
                "because an accepted plan is amended by appended note and never rewritten"
            ),
        },
    },
    "Plans 3–4 remain sequentially blocked": {  # noqa: RUF001
        "false_since": "2026-07-22, when Plan 3's certification executed",
        "permitted_in": {
            "docs/progress.md": "historical — a dated log entry that was accurate on 2026-07-17",
            "docs/plan4/proposed-visibility-change.md": (
                "reporting — quoted to show the log asserts a state the records contradict"
            ),
        },
    },
}


def _flat(text: str) -> str:
    """Collapse whitespace so a phrase still matches across a line wrap.

    The first version of this tripwire matched raw text and therefore **missed the instance it was
    written for**: `docs/progress.md` wraps "Plans 3-4 remain / sequentially blocked" across two
    lines, so the one file that provoked the check passed it. Measured, not reasoned about — the
    flaw was invisible from reading the pattern, which is the lesson ADR 0011 §6 records about the
    pending-verification tripwire, arriving again in a new place.
    """

    return " ".join(text.split())


def _scanned_markdown() -> list[str]:
    """The set the tripwire below actually reads. Extracted so a companion can bound IT.

    It was previously inline, and `test_the_derivation_finds_something` was credited with guarding
    it. That was false: the derivation guard bounds `_reviewer_records()` — 18 JSON files — and this
    walk covers 63 markdown files, **with zero overlap**. If this walk went empty the tripwire would
    pass silently and the companion would be untouched. Found by an independent reviewer measuring
    the two sets rather than reading the docstring that claimed one guarded the other.
    """

    files: list[str] = []
    for path in ROOT.rglob("*.md"):
        parts = path.relative_to(ROOT).parts[:-1]
        if any(p.startswith(".") or p in {"node_modules", "data"} for p in parts):
            continue
        files.append(path.relative_to(ROOT).as_posix())
    return files


def test_the_markdown_scan_reaches_files() -> None:
    """Guard the tripwire's own set — not the derivation's, which is a different set entirely."""

    scanned = _scanned_markdown()
    assert len(scanned) > 30, f"markdown scan reached only {len(scanned)} files"
    assert "README.md" in scanned


@pytest.mark.parametrize("phrase", sorted(SUPERSEDED_ASSERTIONS))
def test_a_superseded_gate_assertion_does_not_come_back(phrase: str) -> None:
    permitted = SUPERSEDED_ASSERTIONS[phrase]["permitted_in"]
    assert isinstance(permitted, dict)
    allowed = set(permitted)
    needle = _flat(phrase)
    offenders: list[str] = []
    for relative in _scanned_markdown():
        if relative in allowed:
            continue
        if needle in _flat((ROOT / relative).read_text(encoding="utf-8")):
            offenders.append(relative)
    assert not offenders, (
        f"superseded gate-state assertion {phrase!r} "
        f"({SUPERSEDED_ASSERTIONS[phrase]['false_since']}) appears in: {offenders}. "
        f"Reconcile against evidence/gate_state.json, or add the file to permitted_in with the "
        f"reason if the string is preserved as a dated record or quoted in order to report it."
    )


@pytest.mark.parametrize("phrase", sorted(SUPERSEDED_ASSERTIONS))
def test_every_permitted_exception_still_earns_its_place(phrase: str) -> None:
    """An exemption kept past its need is a blanket waiting to hide the next stale assertion."""

    permitted = SUPERSEDED_ASSERTIONS[phrase]["permitted_in"]
    assert isinstance(permitted, dict)
    for relative, reason in permitted.items():
        path = ROOT / relative
        assert path.exists(), f"permitted_in names a file that does not exist: {relative}"
        assert _flat(phrase) in _flat(path.read_text(encoding="utf-8")), (
            f"{relative} no longer contains {phrase!r} — remove the exemption. ({reason})"
        )
