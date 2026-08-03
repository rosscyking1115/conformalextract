"""Plan 3 §11.3 calibration diagnostics at the GROUP level — DIAGNOSTIC, certifies nothing.

The certification artifact answers "was the frozen target reachable" (no, for all three systems).
It does not answer **why**, and the two candidate answers have very different consequences:

* the population is too hard — base risk alone forbids the acceptance floor; or
* the population is reachable but the *score* does not rank the reachable part to the top.

Answering that needs THREE upper bounds, not one, and confusing them is the error this module was
corrected for. In increasing order of strictness, for QA on the certification split:

1. **Arithmetic** (0.4911) -- ``1 - (mu - alpha)/(1 - alpha)`` (:func:`minimum_abstention`).
   Assumes the population's goodness can be concentrated arbitrarily, which no real population
   allows. It OVERSTATES what was available and must not be quoted as a shortfall.
2. **Empirical oracle** (0.2357) -- rank this exact population by its actual loss and read the
   same height (``acceptance_under_loss_optimal_ranking``). Holds the population fixed and varies
   only the ranking, so the distance from the measured 0.0201 is attributable to the score. This
   is the like-for-like comparison and the only one a SCORE-DISCRIMINATION claim may use.
3. **Certified oracle** (0.1139 at delta/3) -- the same perfect ranking, but required to keep its
   Hoeffding UPPER bound within alpha (``acceptance_certified_loss_optimal``). This is the only
   one that licenses the word "certified".

The gap between (2) and (3) is not a detail. **An independent review on 2026-08-02 refuted the
claim that a perfect ranking "would clear the 20% floor"**: it clears the floor at (2) and misses
it at (3), because 0.1139 < 0.20. The measured score certifies 0.0000. So infeasibility here is
OVERDETERMINED -- three separate barriers, no one of which could be removed to rescue the result.
They are NOT all active on every system, and saying they each forbid the target is false: base risk
alone settles ZS and FS and PERMITS QA 0.4911, so QA is settled by the other two. No statement of
the form "it was reachable" is supportable either way. Reading (2) as if it
were (3) is the same category error as reading the alpha-frontier point 0.406 as a threshold,
which this repository already forbids by name.

**Governance, stated plainly rather than buried.** ``docs/plan3/sections-11-and-12-disposition.md``
(2026-07-29, Ross's ruling, itself still pending independent review) DESCOPES three of the four
§11.3 sub-items computed here — score-loss Spearman, AUROC/AUPRC, and binned confidence/risk
readouts — on the ground that the committed oracle risk-coverage curve answers the same question
more conservatively. That ground is sound as far as it goes and nothing here contradicts it: every
number below is descriptive, selects no threshold, issues no certificate, and is bounded above by
the curve that was already published. What it adds is *comparability* — AUROC and normalized AURC
are the units the selective-prediction literature reports, and a null that cannot be placed
against published scores cannot be assessed by a reader. Running these therefore REVERSES three
rows of that disposition and requires an independent review of the reversal before any number
here reaches a public surface. It is recorded as a proposal, not as a discharged item.

Everything runs at $0 on splits that are **already open**. ``final`` and ``shift`` stay sealed:
the loader is the re-analysis loader, so :func:`reanalysis.assert_reanalysis_role` guards the only
door to gold and refuses a sealed role before a file is opened.
"""

from __future__ import annotations

import itertools
import json
import tarfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
import numpy.typing as npt
from scipy.stats import rankdata, spearmanr

from conformalextract.certification import FROZEN_DELTA, hoeffding_upper
from conformalextract.certification_run import GroupRow
from conformalextract.profiles import RamsInstance
from conformalextract.reanalysis import CONTENT_CHANNEL, SplitSystemData

#: Coverage heights the risk readout is taken at. Coverage is measured over ALL groups, matching
#: ``certification_run._curve_arrays`` -- ineligible groups dilute achievable coverage there and
#: must dilute it here too, or the two artifacts would disagree about what 20% acceptance means.
COVERAGE_GRID: tuple[float, ...] = (0.05, 0.10, 0.20, 0.30, 0.50)

#: Group-level binary indicators the discrimination statistics are computed against. §11.3 asks
#: for "the predeclared strict-failure indicator", but Plan 1 §237 froze only that such a loss
#: *would* be frozen -- the exact definition never was, and inventing one now and calling it
#: predeclared would be the overclaim this repository exists to avoid. So three indicators are
#: reported, each named for what it is, and none is described as predeclared:
#:
#: ``above_alpha``    -- group loss exceeds the frozen alpha. The operationally decisive one: a
#:                       certificate at alpha=0.20 must rank these below the acceptance cut.
#: ``any_error``      -- group loss > 0. The closest analogue to the error-detection AUROC the
#:                       hallucination-detection literature reports, and the one that makes the
#:                       measured value comparable with published numbers.
#: ``not_all_valid``  -- the group contains a structural or grounding failure, so it can never be
#:                       accepted at all. This is the ``ni_groups`` indicator the certifier emits.
INDICATORS: tuple[str, ...] = ("above_alpha", "any_error", "not_all_valid")


def minimum_abstention(mean_loss: float, alpha: float) -> float:
    """Smallest abstention rate compatible with selective risk ``alpha`` at base risk ``mean_loss``.

    With losses bounded in [0,1], the accepted set of size ``c`` can at best carry all of the
    population's "goodness", so ``mu <= alpha * c + (1 - c)`` must hold; rearranged, abstention
    ``a = 1 - c`` is at least ``(mu - alpha)/(1 - alpha)``. This is the same arithmetic as
    ``reanalysis.mean_loss_ceiling`` read for the other unknown, and it is a property of the
    population alone -- no score, no threshold and no model enters it.

    Returns 0.0 when base risk is already within ``alpha`` (abstention is not forced at all).
    """

    if not 0.0 <= alpha < 1.0:
        raise ValueError(f"alpha must lie in [0,1): {alpha}")
    return max(0.0, (mean_loss - alpha) / (1.0 - alpha))


def auroc(scores: npt.ArrayLike, failure: npt.ArrayLike) -> float | None:
    """P(a non-failing group outscores a failing one), ties counted as half.

    Oriented so that 0.5 is chance and higher is better, matching the convention the
    hallucination-detection literature reports confidence AUROC under. Returns ``None`` when
    either class is empty, which is a real outcome here rather than a defensive branch: a system
    whose groups all fail has no AUROC, and reporting 0.5 for it would invent a measurement.
    """

    labels = np.asarray(failure, dtype=bool)
    values = np.asarray(scores, dtype=np.float64)
    if labels.size != values.size:
        raise ValueError("scores and failure must be the same length")
    positives = int((~labels).sum())
    negatives = int(labels.sum())
    if positives == 0 or negatives == 0:
        return None
    # Average ranks so that tied scores contribute exactly 0.5 rather than an arbitrary order.
    ranks = rankdata(values)
    rank_sum = float(ranks[~labels].sum())
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def average_precision(scores: npt.ArrayLike, failure: npt.ArrayLike) -> float | None:
    """Average precision for retrieving failing groups by ascending confidence.

    The abstention-shaped reading of the same ranking: sweep the low-confidence end and ask how
    densely failures are found there. Its no-skill baseline is the failure prevalence, not 0.5,
    so :func:`calibration_artifact` reports the prevalence alongside it -- an AUPRC quoted
    without its baseline is uninterpretable.
    """

    labels = np.asarray(failure, dtype=bool)
    values = np.asarray(scores, dtype=np.float64)
    if labels.size != values.size:
        raise ValueError("scores and failure must be the same length")
    total = int(labels.sum())
    if total == 0 or labels.size == 0:
        return None
    order = np.argsort(values, kind="stable")
    hits = labels[order]
    cumulative = np.cumsum(hits)
    precision = cumulative / np.arange(1, hits.size + 1)
    return float((precision * hits).sum() / total)


@dataclass(frozen=True)
class SelectiveRisk:
    """Risk-coverage summary for one score over one population.

    ``aurc`` is the mean of the running risk over every eligible prefix -- the standard
    selective-prediction area. On its own it confounds two things a null must keep apart: how
    hard the population is, and how well the score ranks it. ``aurc_optimal`` (the same area
    under a loss-sorted ranking) is the part attributable to the population, ``aurc_random``
    (the base risk) is what an uninformative score gives, and ``normalized_aurc`` places the
    measured score on the line between them: 0.0 is a perfect ranking, 1.0 is no better than
    chance, above 1.0 is worse than chance. That single number is the score-discrimination
    reading; the raw AURC is not, and must not be quoted as one.
    """

    eligible_groups: int
    total_groups: int
    base_risk_all_groups: float
    base_risk_eligible: float
    aurc: float | None
    aurc_optimal: float | None
    aurc_random: float | None
    normalized_aurc: float | None
    risk_at_coverage: dict[str, float | None]
    max_acceptance_within_alpha: float
    minimum_abstention_at_alpha: float
    acceptance_permitted_by_base_risk: float
    acceptance_under_loss_optimal_ranking: float
    acceptance_certified_score_ranked: float
    acceptance_certified_loss_optimal: float
    certified_delta: float

    @property
    def acceptance_shortfall_vs_base_risk(self) -> float:
        """Acceptance the base-risk arithmetic permitted, minus what the score delivered.

        The LOOSE reading of the gap. ``acceptance_permitted_by_base_risk`` assumes the
        population's goodness can be concentrated arbitrarily, which no real population allows,
        so this overstates what was lost. Reported because it is the bound Kotte states and a
        reader will want it, but :attr:`acceptance_shortfall_vs_oracle` is the honest number.
        """

        return self.acceptance_permitted_by_base_risk - self.max_acceptance_within_alpha

    @property
    def acceptance_shortfall_vs_oracle(self) -> float:
        """Acceptance a PERFECT ranking of this exact population would have reached, minus what
        the score delivered -- **both measured empirically, with no finite-sample penalty**.

        The like-for-like reading, and the one a claim about score DISCRIMINATION should use: it
        holds the population fixed and varies only the ranking, so what it leaves unexplained is
        attributable to the score.

        It says nothing whatever about certifiability, and reading it that way is the error this
        module was corrected for on 2026-08-02. An independent review refuted the claim that a
        perfect ranking "would clear the floor": the empirical oracle reaches 0.2357 for QA, but
        under the certifier's own bound the same perfect ranking certifies only 0.1139, below the
        0.20 floor. Use :attr:`acceptance_certified_loss_optimal` for any statement about what
        could have been certified -- never this.
        """

        return self.acceptance_under_loss_optimal_ranking - self.max_acceptance_within_alpha


def _running_risk(losses: np.ndarray) -> np.ndarray:
    return np.cumsum(losses) / np.arange(1, losses.size + 1)


#: Per-system confidence allocation used for the CERTIFIED readings. The certification run splits
#: the frozen delta three ways, one share per system, so delta/3 is the allocation a single
#: system's certificate actually gets. The family-wide Bonferroni allocation delta/(2*9) is
#: tighter still and is quoted in the write-up where the more conservative figure is wanted.
CERTIFIED_DELTA: float = FROZEN_DELTA / 3.0


def _certified_acceptance(
    sorted_losses: np.ndarray, total: int, alpha: float, delta: float
) -> float:
    """Largest coverage whose accepted prefix keeps its Hoeffding UPPER bound within ``alpha``.

    The empirical curve asks whether the accepted set's mean loss is within alpha. A certificate
    asks whether its upper confidence bound is, which is a strictly harder question and the only
    one that licenses the word "certified". Accepting more groups lowers the empirical mean but
    also shrinks the radius, so the two curves cross at very different coverages: on QA the
    empirical oracle reaches 0.2357 and the certified oracle 0.1139.

    Uses ``certification.hoeffding_upper`` rather than reimplementing it, so this cannot drift
    from the bound the certifier itself applied.
    """

    if sorted_losses.size == 0 or total == 0:
        return 0.0
    bounds = np.array(
        [hoeffding_upper(list(sorted_losses[:k]), delta) for k in range(1, sorted_losses.size + 1)]
    )
    within = np.flatnonzero(bounds <= alpha)
    return float((int(within[-1]) + 1) / total) if within.size else 0.0


def selective_risk(
    rows: Sequence[GroupRow],
    *,
    alpha: float,
    coverage_grid: Sequence[float] = COVERAGE_GRID,
    delta: float = CERTIFIED_DELTA,
) -> SelectiveRisk:
    """Summarise one system-and-score's whole risk-coverage behaviour.

    Eligibility, sort order and the coverage denominator are taken from the certifier's own
    sweep (``certification_run._curve_arrays``): only all-valid groups with a finite score can
    ever be accepted, they are accepted best-score-first, and coverage is a share of ALL groups.
    Reproducing that here rather than re-deriving it is what keeps this artifact and
    ``alpha_frontier.json`` from disagreeing about the same numbers.
    """

    total = len(rows)
    all_losses = np.asarray([row.loss for row in rows], dtype=np.float64)
    eligible = sorted(
        (row for row in rows if row.all_valid and np.isfinite(row.score)), key=lambda r: -r.score
    )
    base_all = float(all_losses.mean()) if total else float("nan")
    permitted = 1.0 - minimum_abstention(base_all, alpha) if total else 0.0

    if not eligible or total == 0:
        return SelectiveRisk(
            eligible_groups=len(eligible),
            total_groups=total,
            base_risk_all_groups=base_all,
            base_risk_eligible=float("nan"),
            aurc=None,
            aurc_optimal=None,
            aurc_random=None,
            normalized_aurc=None,
            risk_at_coverage={f"{c:.2f}": None for c in coverage_grid},
            max_acceptance_within_alpha=0.0,
            minimum_abstention_at_alpha=minimum_abstention(base_all, alpha) if total else 0.0,
            acceptance_permitted_by_base_risk=permitted,
            acceptance_under_loss_optimal_ranking=0.0,
            acceptance_certified_score_ranked=0.0,
            acceptance_certified_loss_optimal=0.0,
            certified_delta=delta,
        )

    losses = np.asarray([row.loss for row in eligible], dtype=np.float64)
    running = _running_risk(losses)
    coverage = np.arange(1, losses.size + 1) / total

    area = float(running.mean())
    optimal = float(_running_risk(np.sort(losses)).mean())
    random_area = float(losses.mean())
    spread = random_area - optimal
    # Guard the degenerate population where every group carries the same loss: there the score
    # has nothing to rank, so "how well did it rank" has no answer and None is the honest one.
    normalized = (area - optimal) / spread if spread > 1e-12 else None

    within = np.flatnonzero(running <= alpha)
    # The tight oracle: rank this exact population by loss instead of by score and read the same
    # height. It varies only the ranking, so the distance from it to the measured acceptance is
    # attributable to the score alone -- unlike the base-risk bound, which also absorbs whatever
    # the population's loss distribution makes impossible.
    optimal_losses = np.sort(losses)
    optimal_running = _running_risk(optimal_losses)
    optimal_within = np.flatnonzero(optimal_running <= alpha)
    readout: dict[str, float | None] = {}
    for target in coverage_grid:
        reachable = np.flatnonzero(coverage <= target + 1e-12)
        readout[f"{target:.2f}"] = float(running[int(reachable[-1])]) if reachable.size else None

    return SelectiveRisk(
        eligible_groups=len(eligible),
        total_groups=total,
        base_risk_all_groups=base_all,
        base_risk_eligible=random_area,
        aurc=area,
        aurc_optimal=optimal,
        aurc_random=random_area,
        normalized_aurc=normalized,
        risk_at_coverage=readout,
        max_acceptance_within_alpha=float(coverage[int(within[-1])]) if within.size else 0.0,
        minimum_abstention_at_alpha=minimum_abstention(base_all, alpha),
        acceptance_permitted_by_base_risk=permitted,
        acceptance_under_loss_optimal_ranking=(
            float(coverage[int(optimal_within[-1])]) if optimal_within.size else 0.0
        ),
        acceptance_certified_score_ranked=_certified_acceptance(losses, total, alpha, delta),
        acceptance_certified_loss_optimal=_certified_acceptance(
            optimal_losses, total, alpha, delta
        ),
        certified_delta=delta,
    )


def read_sentence_offsets(archive: Path) -> dict[str, tuple[int, ...]]:
    """Token index at which each RAMS sentence starts, per instance.

    ``profiles.parse_rams_instance`` flattens ``sentences`` into one token tuple and drops the
    boundaries, so cross-sentence distance -- which §11.2 asks to stratify on and which is the
    defining difficulty of the RAMS task -- is not recoverable from ``RamsInstance``. This reads
    the boundaries back out of the archive **separately**, and deliberately returns integer
    offsets only: no token text crosses this function, and nothing on the loss or score path
    touches it, so it cannot make this artifact disagree with the certifier about a loss.
    """

    offsets: dict[str, tuple[int, ...]] = {}
    with tarfile.open(archive, "r:gz") as tar:
        for split in ("train", "dev", "test"):
            member = tar.extractfile(f"RAMS_1.0c/data/{split}.jsonlines")
            if member is None:
                continue
            for line in member.read().decode("utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                starts: list[int] = []
                cursor = 0
                for sentence in record["sentences"]:
                    starts.append(cursor)
                    cursor += len(sentence)
                offsets[f"rams:{record['doc_key']}"] = tuple(starts)
    return offsets


def _sentence_of(token_index: int, starts: Sequence[int]) -> int:
    return int(np.searchsorted(np.asarray(starts, dtype=np.int64), token_index, side="right")) - 1


def cross_sentence_arguments(instance: RamsInstance, starts: Sequence[int]) -> int:
    """Gold arguments whose span begins in a different sentence from the trigger."""

    if not starts:
        return 0
    trigger = _sentence_of(instance.trigger_start, starts)
    return sum(1 for arg in instance.arguments if _sentence_of(arg.start, starts) != trigger)


@dataclass(frozen=True)
class GroupFeature:
    """Everything one group is stratified by, alongside its score and loss."""

    group_id: str
    score: float
    loss: float
    all_valid: bool
    triggers: int
    gold_arguments: int
    cross_sentence: int
    valid_members: int
    content_members: int

    @property
    def grounded_fraction(self) -> float:
        """Share of member documents that parsed AND stayed inside the source text.

        The group-level form of the Plan 2 grounding measurement (QA 95.7% vs ZS 39.4% /
        FS 68.1%), which was reported as an aggregate percentage over documents. §3.2 of the
        publication plan turns on whether that gain shows up per group against loss, which an
        aggregate percentage cannot say either way.
        """

        return self.valid_members / self.triggers if self.triggers else 0.0


def build_group_features(
    data: SplitSystemData,
    *,
    instances: Mapping[str, RamsInstance],
    sentence_offsets: Mapping[str, Sequence[int]],
) -> list[GroupFeature]:
    """Attach gold-side and channel-side features to each group row, in group-id order."""

    members: dict[str, list[str]] = {}
    for document_id, group_id in data.group_by_document.items():
        members.setdefault(group_id, []).append(document_id)

    features: list[GroupFeature] = []
    for row in data.rows:
        documents = sorted(members.get(row.group_id, ()))
        gold = 0
        cross = 0
        for document_id in documents:
            instance = instances[document_id]
            gold += len(instance.arguments)
            cross += cross_sentence_arguments(instance, sentence_offsets.get(document_id, ()))
        features.append(
            GroupFeature(
                group_id=row.group_id,
                score=row.score,
                loss=row.loss,
                all_valid=row.all_valid,
                triggers=len(documents),
                gold_arguments=gold,
                cross_sentence=cross,
                valid_members=sum(1 for d in documents if data.valid_by_document[d]),
                content_members=sum(
                    1 for d in documents if data.channel_by_document[d] == CONTENT_CHANNEL
                ),
            )
        )
    return features


def _bucket(value: int, edges: Sequence[int]) -> str:
    """Label ``value`` by the half-open bucket it falls in; the last edge opens upward."""

    for lower, upper in itertools.pairwise(edges):
        if lower <= value < upper:
            return f"{lower}" if upper == lower + 1 else f"{lower}-{upper - 1}"
    return f"{edges[-1]}+"


#: Strata reported for every system, as (name, accessor, bucket edges). Edges are fixed here
#: rather than chosen from the data, so the same cuts apply to all three systems and both splits
#: and no stratum is drawn around an interesting number after the fact. Accessors are explicit
#: rather than ``getattr`` so a renamed field is a type error instead of a silent empty stratum.
STRATA: tuple[tuple[str, Callable[[GroupFeature], int], tuple[int, ...]], ...] = (
    ("triggers", lambda f: f.triggers, (1, 2, 3, 4, 6)),
    ("gold_arguments", lambda f: f.gold_arguments, (0, 1, 2, 3, 4, 6)),
    ("cross_sentence", lambda f: f.cross_sentence, (0, 1, 2, 3)),
)


def stratify(
    features: Sequence[GroupFeature], *, alpha: float, accepted: frozenset[str]
) -> dict[str, object]:
    """Risk and acceptance by stratum, plus the never-acceptable groups as their own stratum.

    ``accepted`` is the oracle best-scoring prefix within ``alpha`` -- the only "accepted set"
    that exists, since certification returned infeasible for every system and no policy was ever
    selected. It is a diagnostic set, not a certified one, and ``acceptance_lift`` compares each
    stratum's share of it against that stratum's share of the population: 1.0 means the score's
    few acceptances fall where chance would put them.
    """

    def summarise(members: Sequence[GroupFeature]) -> dict[str, object]:
        if not members:
            return {"groups": 0}
        losses = np.asarray([f.loss for f in members], dtype=np.float64)
        in_accepted = sum(1 for f in members if f.group_id in accepted)
        share = len(members) / len(features)
        return {
            "groups": len(members),
            "population_share": share,
            "mean_loss": float(losses.mean()),
            "share_loss_within_alpha": float((losses <= alpha).mean()),
            "mean_score": float(np.mean([f.score for f in members if np.isfinite(f.score)]))
            if any(np.isfinite(f.score) for f in members)
            else None,
            "accepted_groups": in_accepted,
            "acceptance_lift": (
                (in_accepted / len(accepted)) / share if accepted and share > 0 else None
            ),
        }

    out: dict[str, object] = {}
    for name, accessor, edges in STRATA:
        buckets: dict[str, list[GroupFeature]] = {}
        for feature in features:
            buckets.setdefault(_bucket(accessor(feature), edges), []).append(feature)
        out[name] = {label: summarise(buckets[label]) for label in sorted(buckets)}
    out["never_acceptable"] = {
        "not_all_valid": summarise([f for f in features if not f.all_valid]),
        "all_valid": summarise([f for f in features if f.all_valid]),
    }
    return out


def grounding_association(features: Sequence[GroupFeature]) -> dict[str, object]:
    """Group-level relationship between grounding and loss (publication plan §3.2, §4.3).

    The committed grounding claim rests on aggregate percentages over documents. Those are
    consistent with grounding and loss being tightly coupled *and* with their being nearly
    unrelated, so they cannot support either wording. This measures the coupling directly:
    the rank correlation between a group's grounded share and its loss, and mean loss
    conditional on that share. A group with every member grounded is the interesting cell --
    if its mean loss is still far above alpha, grounding was necessary and nowhere near
    sufficient, which is what §3.2's replacement sentence says.
    """

    if not features:
        return {"groups": 0}
    grounded = np.asarray([f.grounded_fraction for f in features], dtype=np.float64)
    losses = np.asarray([f.loss for f in features], dtype=np.float64)
    conditional: dict[str, object] = {}
    bands = (("0.00", 0.0, 0.0), ("(0,0.5)", 0.0, 0.5), ("[0.5,1)", 0.5, 1.0), ("1.00", 1.0, 1.0))
    for label, low, high in bands:
        if low == high:
            mask = np.isclose(grounded, low)
        else:
            mask = (grounded >= low) & (grounded < high) & ~np.isclose(grounded, low)
        conditional[label] = (
            {"groups": int(mask.sum()), "mean_loss": float(losses[mask].mean())}
            if mask.any()
            else {"groups": 0}
        )
    return {
        "groups": len(features),
        "mean_grounded_fraction": float(grounded.mean()),
        "spearman_grounded_vs_loss": _spearman(grounded, losses),
        "conditional_mean_loss_by_grounded_fraction": conditional,
    }


def _spearman(left: np.ndarray, right: np.ndarray) -> dict[str, float] | None:
    """Rank correlation, or ``None`` where one side is constant and rho is undefined."""

    if left.size < 3 or np.ptp(left) == 0 or np.ptp(right) == 0:
        return None
    result = spearmanr(left, right)
    return {"rho": float(result.statistic), "p_value": float(result.pvalue)}


def system_readout(
    data: SplitSystemData,
    features: Sequence[GroupFeature],
    *,
    alpha: float,
) -> dict[str, object]:
    """Every §11.3 statistic for one system under one confidence candidate."""

    risk = selective_risk(data.rows, alpha=alpha)
    scores = np.asarray([f.score for f in features], dtype=np.float64)
    losses = np.asarray([f.loss for f in features], dtype=np.float64)
    finite = np.isfinite(scores)

    indicators = {
        "above_alpha": losses > alpha,
        "any_error": losses > 0.0,
        "not_all_valid": np.asarray([not f.all_valid for f in features], dtype=bool),
    }
    discrimination: dict[str, object] = {}
    for name in INDICATORS:
        failure = indicators[name][finite]
        subset = scores[finite]
        discrimination[name] = {
            "auroc": auroc(subset, failure),
            "auprc": average_precision(subset, failure),
            "failure_prevalence": float(failure.mean()) if failure.size else None,
            "scored_groups": int(finite.sum()),
        }

    eligible = [f for f in features if f.all_valid and np.isfinite(f.score)]
    return {
        "confidence_candidate": data.confidence_candidate,
        "selective_risk": {
            "eligible_groups": risk.eligible_groups,
            "total_groups": risk.total_groups,
            "base_risk_all_groups": risk.base_risk_all_groups,
            "base_risk_eligible_groups": risk.base_risk_eligible,
            "aurc": risk.aurc,
            "aurc_optimal_ranking": risk.aurc_optimal,
            "aurc_random_ranking": risk.aurc_random,
            "normalized_aurc": risk.normalized_aurc,
            "risk_at_coverage": risk.risk_at_coverage,
            "max_acceptance_within_alpha": risk.max_acceptance_within_alpha,
            "minimum_abstention_at_alpha": risk.minimum_abstention_at_alpha,
            "acceptance_permitted_by_base_risk": risk.acceptance_permitted_by_base_risk,
            "acceptance_under_loss_optimal_ranking": risk.acceptance_under_loss_optimal_ranking,
            "acceptance_certified_score_ranked": risk.acceptance_certified_score_ranked,
            "acceptance_certified_loss_optimal": risk.acceptance_certified_loss_optimal,
            "certified_delta": risk.certified_delta,
            "acceptance_shortfall_vs_base_risk": risk.acceptance_shortfall_vs_base_risk,
            "acceptance_shortfall_vs_oracle": risk.acceptance_shortfall_vs_oracle,
        },
        "discrimination": discrimination,
        "spearman_score_vs_loss": {
            "all_scored_groups": _spearman(scores[finite], losses[finite]),
            "eligible_groups_only": _spearman(
                np.asarray([f.score for f in eligible], dtype=np.float64),
                np.asarray([f.loss for f in eligible], dtype=np.float64),
            ),
        },
        "stratified": stratify(
            features, alpha=alpha, accepted=_oracle_accepted(data.rows, alpha=alpha)
        ),
        "grounding": grounding_association(features),
    }


def _oracle_accepted(rows: Sequence[GroupRow], *, alpha: float) -> frozenset[str]:
    """Group ids in the best-scoring prefix whose running risk stays within ``alpha``.

    Diagnostic only. No certificate selected this set, no finite-sample penalty was applied to
    it, and it is not a policy -- it is the largest set the measured ranking could have
    supported if the threshold had been chosen with the labels in hand.
    """

    eligible = sorted(
        (row for row in rows if row.all_valid and np.isfinite(row.score)), key=lambda r: -r.score
    )
    if not eligible:
        return frozenset()
    running = _running_risk(np.asarray([row.loss for row in eligible], dtype=np.float64))
    within = np.flatnonzero(running <= alpha)
    if not within.size:
        return frozenset()
    return frozenset(row.group_id for row in eligible[: int(within[-1]) + 1])


def headline(readout: Mapping[str, object]) -> dict[str, object]:
    """The four numbers the CLI echoes, pulled out of one system readout.

    The readout is a plain nested mapping because it is written straight to JSON; the casts are
    confined here so no caller has to reach blindly into it.
    """

    risk = cast(Mapping[str, object], readout["selective_risk"])
    discrimination = cast(Mapping[str, Mapping[str, object]], readout["discrimination"])
    return {
        "permitted_by_base_risk": risk["acceptance_permitted_by_base_risk"],
        "oracle_ranking_empirical": risk["acceptance_under_loss_optimal_ranking"],
        "oracle_ranking_certified": risk["acceptance_certified_loss_optimal"],
        "delivered_empirical": risk["max_acceptance_within_alpha"],
        "delivered_certified": risk["acceptance_certified_score_ranked"],
        "normalized_aurc": risk["normalized_aurc"],
        "auroc_any_error": discrimination["any_error"]["auroc"],
    }


def calibration_artifact(
    readouts: Mapping[str, Mapping[str, Mapping[str, object]]],
    *,
    alpha: float,
    acceptance_floor: float,
    access: Mapping[str, object],
) -> dict[str, object]:
    """Assemble the §11.3 artifact (text-free, certifies nothing).

    ``readouts`` is indexed split -> system -> confidence candidate, so all three candidates are
    reported for all three systems rather than only the one the development gate selected. The
    two unselected candidates are the counterfactual the null needs: if a discarded score ranked
    materially better, the finding would be about candidate selection instead.
    """

    return {
        "schema_version": "1",
        "diagnostic_only": True,
        "certifies_nothing": True,
        "alpha": alpha,
        "acceptance_floor": acceptance_floor,
        "reverses_disposition": (
            "docs/plan3/sections-11-and-12-disposition.md descopes score-loss Spearman, "
            "AUROC/AUPRC and binned confidence/risk readouts. This artifact computes them and "
            "therefore proposes reversing those three rows. The reversal is NOT independently "
            "reviewed and nothing here may reach a public surface until it is."
        ),
        "interpretation": (
            "Group-level calibration diagnostics for all three confidence candidates on all "
            "three systems. Every statistic is descriptive: no threshold is selected, no "
            "certificate is issued and the frozen alpha=0.20 headline is untouched. THREE upper "
            "bounds on what any score could have delivered are reported and they must not be "
            "confused, in increasing strictness: acceptance_permitted_by_base_risk is the loose "
            "arithmetic bound 1-(mu-alpha)/(1-alpha), which assumes goodness can be concentrated "
            "arbitrarily and OVERSTATES what was available; "
            "acceptance_under_loss_optimal_ranking is the EMPIRICAL oracle over this exact "
            "population, carrying NO finite-sample penalty, and is the like-for-like comparison "
            "against max_acceptance_within_alpha that a SCORE-DISCRIMINATION claim may use; "
            "acceptance_certified_loss_optimal applies the certifier's own Hoeffding upper bound "
            "at certified_delta and is the ONLY figure here that licenses the word 'certified'. "
            "An independent review on 2026-08-02 refuted a claim that the empirical oracle "
            "'would clear the floor' -- it does at 0.2357 and does not once certified at 0.1139, "
            "and the measured score certifies 0.0000. Infeasibility is OVERDETERMINED by three "
            "separate barriers -- base risk, ranking quality, finite-sample penalty -- no one of "
            "which could be removed to rescue it. They are NOT all active on every system, and "
            "saying they each forbid the target is false: base risk alone settles zs and fs and "
            "permits qa 0.4911, so qa is settled by the other two. "
            "No reading of any figure here supports 'the target was reachable'. AUROC is oriented "
            "so higher is better and 0.5 is chance, and AUPRC must be read against "
            "failure_prevalence; where that prevalence is near 1 the AUROC rests on very few "
            "non-failing groups (3 for zs, 18 for fs) and is correspondingly unstable. The "
            "oracle-accepted set used for acceptance_lift is diagnostic and was never certified."
        ),
        "certification_access": dict(access),
        "splits": {split: dict(systems) for split, systems in readouts.items()},
    }
