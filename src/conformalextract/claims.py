"""Plan 4 claim ledger (§3.4): every material public statement, gated by its evidence.

The honesty boundary is enforced here as code rather than discipline. A claim may only reach a
public surface if it has a status that permits prose, cites evidence that exists in the repo,
and carries the limitations that must travel with it. Wordings the independent reviewer
forbade — calling grounding validity "accuracy", asserting a certified margin that does not
exist, hinting a laxer target would certify — are rejected by pattern, so they cannot reach a
README, report, card or CV by inattention.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CLAIM_ID = re.compile(r"^CX-[A-Z0-9]+(-[A-Z0-9]+)*$")

#: A **regression tripwire, not a verification gate.** It catches the specific regression the
#: ADR 0011 reviewer found -- a claim reading "pending independent review" reaching a public
#: surface, because `publishable()` looked only at `surfaces` -- and very little else.
#:
#: Measured, not assumed: against 18 strings that genuinely describe pending verification it
#: misses 11, including "under review", "in progress", "unreviewed", "self-assessed by the
#: implementer" and "verification outstanding". Do not read the constant's name as evidence that
#: unverified claims cannot be published; they can (ADR 0011 section 6 records this).
#:
#: Anchored to the leading token deliberately. An unanchored version matched "independent review
#: complete; no items **pending**" and "review closed; nothing **awaiting** sign-off" -- i.e. it
#: penalised writing a detailed provenance record and rewarded writing "reviewed". A rule that
#: applies pressure toward vagueness in the field the honesty doctrine depends on is worse than
#: no rule. The anchored form has zero false positives across the same corpus.
PENDING_VERIFICATION_TRIPWIRE = re.compile(
    r"^\s*(pending|awaiting|unreviewed|provisional|tbd|tbc|not yet)\b",
    flags=re.IGNORECASE,
)


class ClaimStatus(StrEnum):
    VERIFIED = "verified"
    QUALIFIED = "qualified"
    NEGATIVE = "negative"
    INFEASIBLE = "infeasible"
    FAILED = "failed"
    PLANNED = "planned"


#: Only these may enter public prose (§3.4). `failed` and `planned` may not.
PROSE_PERMITTED: frozenset[ClaimStatus] = frozenset(
    {
        ClaimStatus.VERIFIED,
        ClaimStatus.QUALIFIED,
        ClaimStatus.NEGATIVE,
        ClaimStatus.INFEASIBLE,
    }
)

#: `repo_description` is deliberately distinct from `abstract`, not a synonym for it. An abstract
#: has room to carry a claim's limitations in the same passage; a repository description is one
#: line with no second passage, and the claim boundaries require the grounding gain and the null to
#: travel together. A claim written for `abstract` cannot be trimmed into a description without
#: dropping exactly the half the boundaries protect, so a description needs a wording authored for
#: that constraint (Plan 4 open decision 2, ruled 2026-07-29).
PUBLIC_SURFACES: frozenset[str] = frozenset(
    {
        "README",
        "report",
        "model_card",
        "dataset_card",
        "CV",
        "kaggle",
        "slide",
        "abstract",
        "repo_description",
    }
)

#: Wordings the reviewer forbade, in both directions (over- and under-claiming).
FORBIDDEN_WORDINGS: tuple[tuple[str, str], ...] = (
    (r"\bstate[- ]of[- ]the[- ]art\b", "SOTA claim without a comparable benchmark review (§8.2)"),
    (r"\bpeer[- ]reviewed\b", "a preprint must not be called peer reviewed (§8.2)"),
    (
        r"\bgrounding\s+accuracy\b|\baccuracy\s+of\s+95\.7|\b95\.7%\s+(correct|accurate)",
        "grounding validity is not accuracy (Plan 3 certification review)",
    ),
    (
        r"\bQLoRA\s+(does\s*n[o']t|doesn't)\s+work\b",
        "overclaims the null (Plan 3 certification review)",
    ),
    (
        # The risk symbol is matched via its escape (U+03B1) to keep this source ASCII-only.
        "\\b(lower|laxer|relax\\w*|softer)\\s+(alpha|\\u03b1|target|risk target)\\b",
        "must not hint a laxer target would certify (plan §6.3)",
    ),
    (
        r"\bcertified\s+(margin|advantage|gain)\b",
        "no certified margin exists; all systems are infeasible",
    ),
    (r"\bproduction[- ]grade\b", "the project is explicitly not production-grade (CLAUDE.md)"),
)


class Claim(BaseModel):
    """One material statement with everything required to publish or refuse it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: NonEmpty
    wording: NonEmpty
    status: ClaimStatus
    scope: NonEmpty
    evidence: tuple[NonEmpty, ...] = Field(min_length=1)
    method: NonEmpty
    limitations: tuple[NonEmpty, ...] = ()
    surfaces: tuple[NonEmpty, ...] = ()
    verified_by: NonEmpty

    @model_validator(mode="after")
    def validate_claim(self) -> Claim:
        if not CLAIM_ID.match(self.claim_id):
            raise ValueError(f"claim_id must look like CX-TOPIC-01: {self.claim_id!r}")

        unknown = set(self.surfaces) - PUBLIC_SURFACES
        if unknown:
            raise ValueError(f"{self.claim_id}: unknown surfaces {sorted(unknown)}")

        # §3.4: `planned` is never written as achieved; `failed` evidence is not a result.
        if self.surfaces and self.status not in PROSE_PERMITTED:
            raise ValueError(
                f"{self.claim_id}: status {self.status.value!r} may not appear on a public "
                f"surface; remove surfaces or change status"
            )

        # A claim that reaches the public without its conditions is a claim without its scope.
        if self.surfaces and not self.limitations:
            raise ValueError(
                f"{self.claim_id}: public claims must carry the limitations that travel with them"
            )

        # ... and a claim whose own verification record OPENS by saying it has not been verified
        # yet is not publishable, whatever its status says. Registering future work with a
        # `pending` verified_by stays legitimate; pairing it with a public surface does not.
        # This is a tripwire, not a gate -- see PENDING_VERIFICATION_TRIPWIRE for what it misses.
        if self.surfaces and PENDING_VERIFICATION_TRIPWIRE.search(self.verified_by):
            raise ValueError(
                f"{self.claim_id}: verified_by reports verification still pending "
                f"({self.verified_by!r}); remove surfaces or record the completed verification"
            )

        for pattern, reason in FORBIDDEN_WORDINGS:
            if re.search(pattern, self.wording, flags=re.IGNORECASE):
                raise ValueError(f"{self.claim_id}: forbidden wording — {reason}")
        return self


class ClaimLedger(BaseModel):
    """The full ledger. Public prose is only ever generated from this."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ledger_id: NonEmpty
    analysis_id: NonEmpty
    claims: tuple[Claim, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ledger(self) -> ClaimLedger:
        seen = [claim.claim_id for claim in self.claims]
        duplicates = {claim_id for claim_id in seen if seen.count(claim_id) > 1}
        if duplicates:
            raise ValueError(f"duplicate claim ids: {sorted(duplicates)}")
        return self

    def publishable(self) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if claim.surfaces)

    def for_surface(self, surface: str) -> tuple[Claim, ...]:
        return tuple(claim for claim in self.claims if surface in claim.surfaces)


def _reference_path(reference: str) -> str:
    """Strip the optional ``#anchor`` suffix naming a table or field."""

    return reference.split("#", maxsplit=1)[0]


def tracked_paths(root: Path) -> frozenset[str] | None:
    """Every git-tracked path under ``root``, or None if that cannot be determined.

    **Tracked, not committed.** ``git ls-files`` reads the index, so a staged-but-uncommitted
    file counts as tracked here. That is one step weaker than "a reader can fetch it" and the
    difference is worth keeping straight -- staging is a local act too. Tracked is the right
    check for this gate (an untracked file is certainly unpublishable), but it does not by itself
    establish that the evidence has been pushed anywhere.

    Returning None rather than an empty set matters: "no tracked files" and "cannot tell" must
    not look the same to the caller, or an export outside a git checkout would silently report
    every claim's evidence as untracked.
    """

    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    output = completed.stdout.decode("utf-8", errors="replace")
    return frozenset(entry for entry in output.split("\0") if entry)


def unresolved_evidence(ledger: ClaimLedger, *, root: Path) -> dict[str, list[str]]:
    """Every evidence path that does not exist, per claim.

    A claim whose evidence cannot be resolved is a claim without a basis, regardless of how
    confident its wording is. Paths may carry a ``#anchor`` suffix naming a table or field.
    """

    missing: dict[str, list[str]] = {}
    for claim in ledger.claims:
        absent = [
            reference
            for reference in claim.evidence
            if not (root / _reference_path(reference)).exists()
        ]
        if absent:
            missing[claim.claim_id] = absent
    return missing


def untracked_evidence(ledger: ClaimLedger, *, root: Path) -> dict[str, list[str]]:
    """Every evidence path that exists on disk but is not tracked by git, per claim.

    ``unresolved_evidence`` asks whether a file is *there*; this asks whether anyone else will
    ever see it. An untracked artifact resolves perfectly on the machine that produced it and
    not at all for a reader, so a claim resting on one is unsupported the moment it is published
    -- which the existence check alone cannot detect (ADR 0011 section 6). Tracked is a weaker
    condition than committed-and-pushed; see ``tracked_paths``.

    Returns an empty mapping when tracked status cannot be determined; ``verify_ledger`` reports
    that condition separately rather than reading it as "all clear".
    """

    tracked = tracked_paths(root)
    if tracked is None:
        return {}
    untracked: dict[str, list[str]] = {}
    for claim in ledger.claims:
        absent = [
            reference
            for reference in claim.evidence
            # git reports POSIX separators; normalise so this works on Windows too.
            if _reference_path(reference).replace("\\", "/") not in tracked
            and (root / _reference_path(reference)).exists()
        ]
        if absent:
            untracked[claim.claim_id] = absent
    return untracked


def load_ledger(path: Path) -> ClaimLedger:
    return ClaimLedger.model_validate_json(path.read_text(encoding="utf-8"))


def verify_ledger(
    ledger: ClaimLedger, *, root: Path, require_tracked: bool = True
) -> dict[str, object]:
    """Full ledger verification; ``ok`` is False if anything would block publication.

    ``require_tracked`` fails the check when git-tracked status cannot be determined at all.
    That is deliberately fail-closed: this is a publication gate, and "I could not tell whether
    the evidence is committed" is not a pass. Set it False only when verifying a ledger outside
    a git checkout on purpose.
    """

    missing = unresolved_evidence(ledger, root=root)
    untracked = untracked_evidence(ledger, root=root)
    tracking_known = tracked_paths(root) is not None
    by_status: dict[str, int] = {}
    for claim in ledger.claims:
        by_status[claim.status.value] = by_status.get(claim.status.value, 0) + 1
    ok = not missing and not untracked and (tracking_known or not require_tracked)
    return {
        "ledger_id": ledger.ledger_id,
        "analysis_id": ledger.analysis_id,
        "claims": len(ledger.claims),
        "publishable": len(ledger.publishable()),
        "by_status": dict(sorted(by_status.items())),
        "unresolved_evidence": missing,
        "untracked_evidence": untracked,
        "tracking_verifiable": tracking_known,
        "ok": ok,
    }


def render_surface(ledger: ClaimLedger, surface: str) -> str:
    """Render the approved sentences for one surface, each with its limitations attached.

    Deliberately mechanical: public prose is assembled from approved wordings rather than
    re-written, so a claim cannot drift from the sentence its evidence supports.
    """

    lines: list[str] = []
    for claim in ledger.for_surface(surface):
        lines.append(f"- [{claim.claim_id}] {claim.wording}")
        for limitation in claim.limitations:
            lines.append(f"  - _Limitation:_ {limitation}")
    return "\n".join(lines)


def write_ledger(ledger: ClaimLedger, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(ledger.model_dump_json())
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def claim_ids(claims: Sequence[Claim]) -> tuple[str, ...]:
    return tuple(claim.claim_id for claim in claims)
