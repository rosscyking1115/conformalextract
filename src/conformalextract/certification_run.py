"""Certification execution (Plan 3 §7): group aggregation, per-system certificates, H1/H2.

This is the only module that reads **certification** gold. It deliberately does **not** reuse
``training.build_label_access_log``: that chain hard-rejects every sealed role, which is a Plan 2
training-time invariant (``sealed_reads: 0``) that must stay intact. Instead this module keeps a
parallel chain with its own genesis that permits ``certification`` and **only** ``certification`` --
``final`` and ``shift`` remain unreachable from here, so opening the certification split cannot
become a foothold for opening the others.

Within-group aggregation follows ADR 0009 (min score, all-members-valid, mean loss), reusing
``selection.accept_whole_document`` one level up rather than reimplementing it.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from conformalextract.certification import (
    HypothesisDecision,
    certified_acceptance,
    compare_certified_acceptance,
    conservative_certificate,
    scorc_certificate,
)
from conformalextract.contracts import CertificationResult
from conformalextract.selection import accept_whole_document

CERTIFICATION_ACCESS_GENESIS = hashlib.sha256(
    b"conformalextract/certification-access/v1"
).hexdigest()
CERTIFICATION_ONLY_ROLE = "certification"
FORBIDDEN_ROLES = frozenset({"final", "shift", "train", "development"})


class SealedRoleError(ValueError):
    """Raised when anything other than the certification split is reached from here."""


@dataclass(frozen=True)
class CertificationAccessLog:
    """Tamper-evident, text-free chain over certification gold reads."""

    entries: tuple[str, ...]
    head_hash: str
    document_count: int

    def verify(self) -> bool:
        previous = CERTIFICATION_ACCESS_GENESIS
        for entry in self.entries:
            previous = hashlib.sha256(
                json.dumps(
                    {"previous": previous, "document_id_hash": entry},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
        return previous == self.head_hash


def build_certification_access_log(
    document_ids: Sequence[str], *, data_role: str = CERTIFICATION_ONLY_ROLE
) -> CertificationAccessLog:
    """Authorize and chain every certification gold read; refuse any other role."""

    if data_role != CERTIFICATION_ONLY_ROLE:
        raise SealedRoleError(
            f"role {data_role!r} is unreachable from certification; this command opens "
            "the certification split only"
        )
    previous = CERTIFICATION_ACCESS_GENESIS
    entries: list[str] = []
    for document_id in document_ids:
        digest = hashlib.sha256(document_id.encode()).hexdigest()
        entries.append(digest)
        previous = hashlib.sha256(
            json.dumps(
                {"previous": previous, "document_id_hash": digest},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    return CertificationAccessLog(
        entries=tuple(entries), head_hash=previous, document_count=len(entries)
    )


@dataclass(frozen=True)
class GroupRow:
    """One independent certification unit (ADR 0009)."""

    group_id: str
    score: float
    all_valid: bool
    loss: float
    document_count: int


def aggregate_to_groups(
    *,
    document_ids: Sequence[str],
    group_by_document: Mapping[str, str],
    score_by_document: Mapping[str, float],
    valid_by_document: Mapping[str, bool],
    loss_by_document: Mapping[str, float],
) -> list[GroupRow]:
    """Fold documents into one row per source-document group, per ADR 0009.

    Group score is the **minimum** member confidence, a group is valid only if **every**
    member is, and group loss is the **mean** member loss (bounded in [0,1], as the certifier
    requires). Rows are returned in deterministic group-id order.
    """

    members: dict[str, list[str]] = {}
    for document_id in document_ids:
        group_id = group_by_document.get(document_id)
        if group_id is None:
            raise ValueError(f"no group assignment for {document_id}")
        members.setdefault(group_id, []).append(document_id)

    rows: list[GroupRow] = []
    for group_id in sorted(members):
        documents = members[group_id]
        losses = [loss_by_document[d] for d in documents]
        if any(loss < 0.0 or loss > 1.0 for loss in losses):
            raise ValueError(f"group {group_id} has an out-of-range document loss")
        rows.append(
            GroupRow(
                group_id=group_id,
                score=min(score_by_document[d] for d in documents),
                all_valid=all(valid_by_document[d] for d in documents),
                loss=sum(losses) / len(losses),
                document_count=len(documents),
            )
        )
    return rows


def group_accepted(row: GroupRow, threshold: float) -> bool:
    """Accept a group only if every member is valid and its worst score clears the threshold.

    Delegates to the tested ``accept_whole_document`` rather than restating the rule.
    """

    return accept_whole_document(
        frame_confidences=[row.score],
        structurally_valid=[row.all_valid],
        threshold=threshold,
    )


def _matrices(
    rows: Sequence[GroupRow], thresholds: Sequence[float]
) -> tuple[list[list[float]], list[list[bool]]]:
    losses = [[row.loss for _ in thresholds] for row in rows]  # loss is threshold-independent
    accepted = [[group_accepted(row, threshold) for threshold in thresholds] for row in rows]
    return losses, accepted


def certify_system(
    system_id: str,
    rows: Sequence[GroupRow],
    thresholds: Sequence[float],
    *,
    alpha: float,
    delta_s: float,
    acceptance_floor: float,
) -> CertificationResult:
    """Construction A: this system's SCoRC certificate at its allocated ``delta_s``."""

    if not thresholds:
        raise ValueError(f"{system_id}: threshold grid must be non-empty")
    losses, accepted = _matrices(rows, thresholds)
    candidate_ids = [f"{system_id}@{threshold}" for threshold in thresholds]
    return scorc_certificate(
        losses=losses,
        accepted=accepted,
        candidate_ids=candidate_ids,
        alpha=alpha,
        acceptance_floor=acceptance_floor,
        delta=delta_s,
    )


def conservative_system_view(
    system_id: str,
    rows: Sequence[GroupRow],
    thresholds: Sequence[float],
    *,
    alpha: float,
    delta: float,
    acceptance_floor: float,
    family_size: int,
    min_accepted: int = 1,
) -> CertificationResult:
    """Construction B: global-Bonferroni audit, best feasible candidate by acceptance LCB.

    Reported as a descriptive robustness view only; it never supports a claim Construction A
    does not (theorem-to-code note §7, condition 3).
    """

    best: CertificationResult | None = None
    for threshold in thresholds:
        accepted = [group_accepted(row, threshold) for row in rows]
        result = conservative_certificate(
            losses=[row.loss for row in rows],
            accepted=accepted,
            alpha=alpha,
            acceptance_floor=acceptance_floor,
            delta=delta,
            family_size=family_size,
            min_accepted=min_accepted,
        )
        if result.feasible and (best is None or result.acceptance_lower > best.acceptance_lower):
            best = result
    if best is not None:
        return best
    # No feasible candidate: report the last computed infeasible result shape, not a zero-risk one.
    return conservative_certificate(
        losses=[row.loss for row in rows],
        accepted=[group_accepted(row, thresholds[-1]) for row in rows],
        alpha=alpha,
        acceptance_floor=acceptance_floor,
        delta=delta,
        family_size=family_size,
        min_accepted=min_accepted,
    )


def _size_bucket(size: int) -> str:
    if size == 1:
        return "1"
    if size <= 3:
        return "2-3"
    if size <= 6:
        return "4-6"
    return "7+"


def size_distribution(rows: Sequence[GroupRow]) -> dict[str, int]:
    """Group-size histogram, so a size-skewed accepted set is visible not inferred (A3)."""

    counts: dict[str, int] = {"1": 0, "2-3": 0, "4-6": 0, "7+": 0}
    for row in rows:
        counts[_size_bucket(row.document_count)] += 1
    return counts


def loss_summaries(rows: Sequence[GroupRow]) -> dict[str, float]:
    """Unweighted mean-of-group-means and its size-weighted (document-level) counterpart.

    The certificate bounds the **unweighted** quantity; a reader naturally hears the
    size-weighted one. Emitting both lets the gap be observed on the certification split
    rather than assumed from development (reviewer amendment A2).
    """

    if not rows:
        return {"unweighted_mean_loss": 0.0, "size_weighted_mean_loss": 0.0, "gap": 0.0}
    losses = np.asarray([row.loss for row in rows], dtype=np.float64)
    weights = np.asarray([row.document_count for row in rows], dtype=np.float64)
    unweighted = float(np.mean(losses))
    weighted = float(np.average(losses, weights=weights))
    return {
        "unweighted_mean_loss": unweighted,
        "size_weighted_mean_loss": weighted,
        "gap": unweighted - weighted,
    }


@dataclass(frozen=True)
class RiskCoverageFrontier:
    """Oracle risk-coverage frontier: what ANY threshold could achieve, before any bound.

    This is the diagnostic that rules out the GRID AND THE BOUNDS as the cause. It applies no
    finite-sample penalty, no grid, and no multiplicity correction -- it sorts by score and reads
    the empirical risk of the best-scoring prefix. If the acceptance floor is unreachable *here*,
    no grid refinement, delta reallocation or tighter bound can rescue it.

    It does NOT establish that the whole infeasibility is a capability gap, and reading it that way
    was corrected on 2026-08-03 (``CX-CAPGAP-01``). Being penalty-free is what makes it clean
    evidence about the score, and it is also what blinds it to the finite-sample penalty -- a
    second, method-side barrier that can forbid a certificate the empirical curve permits. Here it
    does: the loss-optimal ranking reaches 0.2357 empirically and certifies 0.1139 at delta/3.

    It is a DIAGNOSTIC only: it selects no threshold and certifies nothing (plan §7.2 forbids
    picking the empirically best point and calling it certified).
    """

    eligible_groups: int
    total_groups: int
    risk_at_floor_acceptance: float | None
    max_acceptance_within_alpha: float
    alpha: float
    acceptance_floor: float

    @property
    def floor_reachable(self) -> bool:
        return self.max_acceptance_within_alpha >= self.acceptance_floor


def _curve_arrays(rows: Sequence[GroupRow]) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Shared oracle sweep: sort eligible rows best-score-first, return coverage and risk.

    Both ``risk_coverage_frontier`` and ``risk_coverage_curve`` read the same arrays from
    here, so the single-alpha frontier and the alpha-free curve cannot drift apart -- the
    frontier is definitionally the curve read at one height (ADR 0011).
    """

    eligible = sorted(
        (row for row in rows if row.all_valid and np.isfinite(row.score)),
        key=lambda row: -row.score,
    )
    total = len(rows)
    if not eligible or total == 0:
        empty = np.asarray([], dtype=np.float64)
        return empty, empty, len(eligible), total
    losses = np.asarray([row.loss for row in eligible], dtype=np.float64)
    running_risk = np.cumsum(losses) / np.arange(1, len(losses) + 1)
    # Acceptance is over ALL groups, so ineligible groups correctly dilute achievable coverage.
    coverage = np.arange(1, len(losses) + 1) / total
    return coverage, running_risk, len(eligible), total


def risk_coverage_frontier(
    rows: Sequence[GroupRow], *, alpha: float, acceptance_floor: float
) -> RiskCoverageFrontier:
    """Compute the oracle frontier over group rows (accept best-scoring first)."""

    coverage, running_risk, eligible_groups, total = _curve_arrays(rows)
    if coverage.size == 0:
        return RiskCoverageFrontier(
            eligible_groups=eligible_groups,
            total_groups=total,
            risk_at_floor_acceptance=None,
            max_acceptance_within_alpha=0.0,
            alpha=alpha,
            acceptance_floor=acceptance_floor,
        )
    within = np.flatnonzero(running_risk <= alpha)
    at_floor = (
        float(running_risk[int(np.argmin(np.abs(coverage - acceptance_floor)))])
        if coverage.max() >= acceptance_floor
        else None
    )
    return RiskCoverageFrontier(
        eligible_groups=eligible_groups,
        total_groups=total,
        risk_at_floor_acceptance=at_floor,
        max_acceptance_within_alpha=float(coverage[within[-1]]) if within.size else 0.0,
        alpha=alpha,
        acceptance_floor=acceptance_floor,
    )


@dataclass(frozen=True)
class RiskCoverageCurve:
    """The whole oracle risk-coverage curve -- the object the frontier reads at one alpha.

    The curve carries **no** alpha: sorting by score and taking the running mean loss of the
    best-scoring prefix produces one fixed object, and ``max_acceptance_within(alpha)`` is
    simply that object read at height alpha. A sweep over alpha therefore introduces no new
    statistic, no new selection and no new multiplicity -- which is exactly why it can be
    reported without relaxing the frozen target or issuing a certificate anywhere.

    It is a DIAGNOSTIC, on the same terms as ``RiskCoverageFrontier``: it applies no
    finite-sample penalty, no grid and no multiplicity correction, selects no threshold and
    certifies nothing. Because it is an oracle *upper bound* on what any threshold rule could
    achieve, an acceptance floor that is unreachable on this curve at some alpha is unreachable
    by any certificate at that alpha -- the direction that lets it rule alpha values out.
    """

    coverage: tuple[float, ...]
    running_risk: tuple[float, ...]
    eligible_groups: int
    total_groups: int

    def max_acceptance_within(self, alpha: float) -> float:
        """Largest oracle-reachable coverage whose running risk stays within ``alpha``."""

        if not self.running_risk:
            return 0.0
        risk = np.asarray(self.running_risk, dtype=np.float64)
        within = np.flatnonzero(risk <= alpha)
        return float(self.coverage[int(within[-1])]) if within.size else 0.0

    def alpha_star(self, coverage_target: float) -> float | None:
        """Smallest alpha at which ``coverage_target`` is oracle-reachable; None if never.

        This is ``min{running_risk[i] : coverage[i] >= coverage_target}``, which inverts
        ``max_acceptance_within`` exactly and stays correct where the curve is non-monotone
        (a later, cheaper prefix can beat an earlier one).
        """

        if not self.coverage:
            return None
        coverage = np.asarray(self.coverage, dtype=np.float64)
        risk = np.asarray(self.running_risk, dtype=np.float64)
        reachable = np.flatnonzero(coverage >= coverage_target)
        return float(np.min(risk[reachable])) if reachable.size else None


def risk_coverage_curve(rows: Sequence[GroupRow]) -> RiskCoverageCurve:
    """Compute the alpha-free oracle risk-coverage curve over group rows."""

    coverage, running_risk, eligible_groups, total = _curve_arrays(rows)
    return RiskCoverageCurve(
        coverage=tuple(float(c) for c in coverage),
        running_risk=tuple(float(r) for r in running_risk),
        eligible_groups=eligible_groups,
        total_groups=total,
    )


@dataclass(frozen=True)
class SystemCertification:
    system_id: str
    confidence_candidate: str
    thresholds: tuple[float, ...]
    delta_s: float
    primary: CertificationResult
    conservative: CertificationResult
    certified_acceptance: float | None
    group_count: int
    loss_summary: dict[str, float]
    group_size_distribution: dict[str, int]
    accepted_size_distribution: dict[str, int] | None
    never_acceptable_groups: int


@dataclass(frozen=True)
class CertificationRun:
    systems: dict[str, SystemCertification]
    h1: HypothesisDecision
    h2: HypothesisDecision
    hypotheses_collapsed: bool
    access_log: CertificationAccessLog


def run_certification(
    *,
    rows_by_system: Mapping[str, Sequence[GroupRow]],
    thresholds_by_system: Mapping[str, Sequence[float]],
    candidates_by_system: Mapping[str, str],
    delta_allocation: Mapping[str, float],
    access_log: CertificationAccessLog,
    alpha: float,
    delta: float,
    acceptance_floor: float,
    material_gain: float,
) -> CertificationRun:
    """Certify all three systems and decide H1/H2 (plan §7-§8)."""

    if set(rows_by_system) != {"zs", "fs", "qa"}:
        raise ValueError("certification requires exactly zs/fs/qa")
    total = sum(delta_allocation.values())
    if abs(total - delta) > 1e-12:
        raise ValueError(f"delta allocation sums to {total}, not delta {delta}")

    family_size = sum(len(thresholds_by_system[s]) for s in rows_by_system)
    systems: dict[str, SystemCertification] = {}
    for system_id in sorted(rows_by_system):
        rows = rows_by_system[system_id]
        thresholds = thresholds_by_system[system_id]
        primary = certify_system(
            system_id,
            rows,
            thresholds,
            alpha=alpha,
            delta_s=delta_allocation[system_id],
            acceptance_floor=acceptance_floor,
        )
        conservative = conservative_system_view(
            system_id,
            rows,
            thresholds,
            alpha=alpha,
            delta=delta,
            acceptance_floor=acceptance_floor,
            family_size=family_size,
        )
        accepted_sizes: dict[str, int] | None = None
        if primary.feasible and primary.selected_candidate is not None:
            selected_threshold = float(primary.selected_candidate.rsplit("@", maxsplit=1)[1])
            accepted_sizes = size_distribution(
                [row for row in rows if group_accepted(row, selected_threshold)]
            )
        systems[system_id] = SystemCertification(
            system_id=system_id,
            confidence_candidate=candidates_by_system[system_id],
            thresholds=tuple(thresholds),
            delta_s=delta_allocation[system_id],
            primary=primary,
            conservative=conservative,
            certified_acceptance=certified_acceptance(primary),
            group_count=len(rows),
            loss_summary=loss_summaries(rows),
            group_size_distribution=size_distribution(rows),
            accepted_size_distribution=accepted_sizes,
            # Groups with an invalid member can never be accepted at ANY threshold: a hard
            # ceiling on achievable acceptance before thresholding (reviewer amendment A4).
            never_acceptable_groups=sum(1 for row in rows if not row.all_valid),
        )

    h1, h2 = compare_certified_acceptance(
        qa=systems["qa"].certified_acceptance,
        zs=systems["zs"].certified_acceptance,
        fs=systems["fs"].certified_acceptance,
        material_gain=material_gain,
    )
    # Pre-registered in the §5.5 note §7a: when both baselines are infeasible, H1 and H2 are one
    # single-system test stated twice and must not be presented as two confirmatory comparisons.
    collapsed = (
        systems["zs"].certified_acceptance is None and systems["fs"].certified_acceptance is None
    )
    return CertificationRun(
        systems=systems, h1=h1, h2=h2, hypotheses_collapsed=collapsed, access_log=access_log
    )


def certification_artifact(
    run: CertificationRun,
    *,
    provenance: Mapping[str, object],
    gold_reads_by_role: Mapping[str, int],
) -> dict[str, object]:
    """Assemble the immutable §7.4 certification artifact (text-free).

    ``gold_reads_by_role`` is the count, per split role, of documents whose gold the caller
    actually used. ``final_reads`` and ``shift_reads`` are taken from it, so a nonzero read is
    reported rather than masked. The 2026-07-22 artifact predates this and wrote both as the
    constant 0 (independent review 2026-10-27, finding B2).
    """

    def result_dict(result: CertificationResult) -> dict[str, object]:
        parsed: dict[str, object] = json.loads(result.model_dump_json())
        return parsed

    return {
        "schema_version": "1",
        "method": (
            "scorc-joint-finite-grid (primary) + "
            "hoeffding-clopper-pearson-bonferroni (audit)"
        ),
        "theorem_reference": "arXiv 2606.08517 Theorem 1 / Algorithm 1; see "
        "docs/plan3/theorem-to-code-scorc.md and theorem-to-code-global-multiplicity.md",
        "systems": {
            system_id: {
                "confidence_candidate": certification.confidence_candidate,
                "thresholds": [
                    "-inf" if np.isneginf(t) else ("+inf" if np.isposinf(t) else t)
                    for t in certification.thresholds
                ],
                "delta_s": certification.delta_s,
                "group_count": certification.group_count,
                "primary": result_dict(certification.primary),
                "conservative_audit": result_dict(certification.conservative),
                "certified_acceptance": certification.certified_acceptance,
                # A2: the certificate bounds the UNWEIGHTED quantity; a reader hears the
                # size-weighted one. Both are emitted so the gap is observed, not assumed.
                "loss_summary": certification.loss_summary,
                # A3: the accepted set skews small-group (min over more draws is lower).
                "group_size_distribution": certification.group_size_distribution,
                "accepted_size_distribution": certification.accepted_size_distribution,
                # A4: groups with an invalid member cap acceptance before any threshold.
                "never_acceptable_groups": certification.never_acceptable_groups,
                "acceptance_ceiling": (
                    (certification.group_count - certification.never_acceptable_groups)
                    / certification.group_count
                    if certification.group_count
                    else 0.0
                ),
            }
            for system_id, certification in run.systems.items()
        },
        "hypotheses": {
            "h1": {
                "outcome": run.h1.outcome,
                "detail": run.h1.detail,
                "qa": run.h1.qa_acceptance,
                "baseline": run.h1.baseline_acceptance,
            },
            "h2": {
                "outcome": run.h2.outcome,
                "detail": run.h2.detail,
                "qa": run.h2.qa_acceptance,
                "baseline": run.h2.baseline_acceptance,
            },
            "collapsed_to_single_test": run.hypotheses_collapsed,
            "collapse_note": (
                "Both baselines infeasible: H1 and H2 reduce to CA_QA >= material_gain and are "
                "ONE test stated twice. Must not be reported as two confirmatory comparisons "
                "(pre-registered, theorem-to-code-global-multiplicity.md section 7a)."
                if run.hypotheses_collapsed
                else None
            ),
        },
        "certification_access": {
            "head_hash": run.access_log.head_hash,
            "documents_read": run.access_log.document_count,
            "verified": run.access_log.verify(),
            "final_reads": int(gold_reads_by_role.get("final", 0)),
            "shift_reads": int(gold_reads_by_role.get("shift", 0)),
            "gold_reads_by_role": dict(sorted(gold_reads_by_role.items())),
        },
        **dict(provenance),
    }
