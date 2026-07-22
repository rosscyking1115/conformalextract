"""Committed re-analysis artifacts must keep agreeing with the committed certification result.

Reviewer ruling R3: the ADR 0011 artifacts were checked by hand at authoring time and by the
independent reviewer, but nothing in the repo re-checked them afterwards. These tests close that
-- they read only committed evidence JSON (no private predictions, no RAMS archive, no gold), so
they run anywhere the repo is checked out and fail loudly if any artifact is regenerated in a way
that stops matching the certificate it claims to decompose.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conformalextract.certification import FROZEN_ACCEPTANCE_FLOOR, FROZEN_ALPHA
from conformalextract.reanalysis import CONTENT_CHANNEL, LOSS_CHANNELS, mean_loss_ceiling

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"
SYSTEMS = ("zs", "fs", "qa")


def _load(name: str) -> dict:
    path = EVIDENCE / "plan3" / name
    if not path.exists():  # pragma: no cover - artifact is committed
        pytest.skip(f"{name} not present")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def certification() -> dict:
    return _load("certification_result.json")


@pytest.fixture(scope="module")
def frontier() -> dict:
    return _load("alpha_frontier.json")


@pytest.fixture(scope="module")
def decomposition() -> dict:
    return _load("loss_decomposition.json")


@pytest.fixture(scope="module")
def diagnostic() -> dict:
    return _load("risk_coverage_diagnostic.json")


# --- the sweep must remain a re-reading of the committed single-alpha diagnostic --------


@pytest.mark.parametrize("split", ["development", "certification"])
@pytest.mark.parametrize("system", SYSTEMS)
def test_curve_at_the_frozen_alpha_reproduces_the_committed_diagnostic(
    frontier: dict, diagnostic: dict, split: str, system: str
) -> None:
    """If these ever diverge, the sweep has become a second statistic (ADR 0011 section 1)."""

    key = f"{FROZEN_ALPHA:.2f}"
    swept = frontier["splits"][split][system]["max_acceptance_by_alpha"][key]
    committed = diagnostic["splits"][split][system]["max_acceptance_within_alpha"]
    assert swept == pytest.approx(committed, abs=1e-12)


def test_the_frontier_reports_the_frozen_operating_point(frontier: dict) -> None:
    assert frontier["frozen_alpha"] == FROZEN_ALPHA
    assert frontier["acceptance_floor"] == FROZEN_ACCEPTANCE_FLOOR
    assert frontier["diagnostic_only"] is True
    assert frontier["certifies_nothing"] is True


def test_the_floor_crossing_is_far_above_the_frozen_target(frontier: dict) -> None:
    """The headline: no certificate below the crossing could have cleared the floor."""

    crossings = {
        system: frontier["splits"]["certification"][system]["alpha_star_at_floor"]
        for system in SYSTEMS
    }
    assert crossings["qa"] == pytest.approx(0.406, abs=0.001)
    assert crossings["fs"] == pytest.approx(0.930, abs=0.001)
    assert crossings["zs"] == pytest.approx(0.981, abs=0.001)
    for system, crossing in crossings.items():
        assert crossing > FROZEN_ALPHA, f"{system} would certify at the frozen target"


# --- the decomposition must keep summing to the quantity the certificate bounds ---------


@pytest.mark.parametrize("system", SYSTEMS)
def test_group_channels_sum_to_the_committed_unweighted_group_loss(
    decomposition: dict, certification: dict, system: str
) -> None:
    """ADR 0009: the certificate bounds the unweighted mean of group means. Decompose THAT."""

    entry = decomposition["splits"]["certification"][system]
    channel_sum = sum(c["group_level_contribution"] for c in entry["channels"].values())
    committed = certification["systems"][system]["loss_summary"]["unweighted_mean_loss"]
    assert channel_sum == pytest.approx(committed, abs=1e-12)
    assert entry["group_level_total_loss"] == pytest.approx(committed, abs=1e-12)


@pytest.mark.parametrize("system", SYSTEMS)
def test_document_channels_sum_to_the_committed_size_weighted_loss(
    decomposition: dict, certification: dict, system: str
) -> None:
    """The other total a reader naturally hears; reported so the gap is observed, not assumed."""

    entry = decomposition["splits"]["certification"][system]
    channel_sum = sum(c["document_level_contribution"] for c in entry["channels"].values())
    committed = certification["systems"][system]["loss_summary"]["size_weighted_mean_loss"]
    assert channel_sum == pytest.approx(committed, abs=1e-12)
    assert entry["document_level_total_loss"] == pytest.approx(committed, abs=1e-12)


@pytest.mark.parametrize("system", SYSTEMS)
def test_every_channel_is_present_and_accounts_for_every_document(
    decomposition: dict, system: str
) -> None:
    entry = decomposition["splits"]["certification"][system]
    assert set(entry["channels"]) == set(LOSS_CHANNELS)
    assert sum(c["documents"] for c in entry["channels"].values()) == entry["documents"]
    assert sum(c["document_share"] for c in entry["channels"].values()) == pytest.approx(1.0)


@pytest.mark.parametrize("system", SYSTEMS)
def test_group_count_matches_the_certification_run(
    decomposition: dict, certification: dict, system: str
) -> None:
    assert (
        decomposition["splits"]["certification"][system]["groups"]
        == certification["systems"][system]["group_count"]
    )


# --- the grounding-oracle conclusion must not rest on the counterfactual ----------------


def test_the_baselines_are_excluded_by_arithmetic_not_by_the_counterfactual(
    decomposition: dict,
) -> None:
    """Reviewer R5: the restriction is not uniformly generous, so the ceiling carries the claim."""

    ceiling = mean_loss_ceiling(alpha=FROZEN_ALPHA, acceptance_floor=FROZEN_ACCEPTANCE_FLOOR)
    assert ceiling == pytest.approx(0.84)
    for system in ("zs", "fs"):
        oracle = decomposition["splits"]["certification"][system]["grounding_oracle"]
        assert oracle["mean_loss_ceiling"] == pytest.approx(ceiling)
        assert oracle["restricted_mean_loss"] > ceiling
        assert oracle["excluded_by_ceiling"] is True
        assert oracle["floor_reachable_under_grounding_oracle"] is False


def test_qa_is_not_excluded_by_the_ceiling_so_the_measured_curve_decides(
    decomposition: dict,
) -> None:
    """The ceiling must be silent where it does not apply, or it would be proving too much."""

    oracle = decomposition["splits"]["certification"]["qa"]["grounding_oracle"]
    assert oracle["excluded_by_ceiling"] is False
    assert oracle["restricted_mean_loss"] < oracle["mean_loss_ceiling"]
    # It is the measurement, not arithmetic, that leaves QA short of the floor.
    assert oracle["conditional_max_acceptance"] < FROZEN_ACCEPTANCE_FLOOR
    assert oracle["floor_reachable_under_grounding_oracle"] is False


def test_the_restriction_is_recorded_as_not_uniformly_generous(decomposition: dict) -> None:
    """A non-zero count here is the evidence for dropping the 'most generous reading' claim."""

    worsened = {
        system: decomposition["splits"]["certification"][system]["grounding_oracle"][
            "groups_worsened_by_restriction"
        ]
        for system in SYSTEMS
    }
    assert worsened["fs"] > 0 and worsened["qa"] > 0


def test_the_qlora_system_has_solved_grounding_and_is_still_wrong(decomposition: dict) -> None:
    """The lead claim in one assertion set: grounding fixed, loss still in the scored channel."""

    entry = decomposition["splits"]["certification"]["qa"]
    grounding = entry["channels"]["grounding_failure"]
    content = entry["channels"][CONTENT_CHANNEL]
    assert grounding["document_share"] < 0.05  # grounding deficit essentially gone
    assert content["document_share"] > 0.85  # nearly every document reaches the scored channel
    share = content["group_level_contribution"] / entry["group_level_total_loss"]
    assert share > 0.85  # ... and that channel carries almost all the remaining loss


@pytest.mark.parametrize("system", ["zs", "fs"])
def test_the_baselines_lose_most_of_their_mass_before_the_scored_channel(
    decomposition: dict, system: str
) -> None:
    """The mirror image: the baselines' loss is dominated by never reaching the scored channel."""

    entry = decomposition["splits"]["certification"][system]
    forced = sum(
        entry["channels"][channel]["document_share"]
        for channel in ("structural_failure", "grounding_failure")
    )
    content = entry["channels"][CONTENT_CHANNEL]
    assert forced > 0.30  # a third or more never produce a scorable answer at all
    assert content["document_share"] < 0.45
    # ... and where they do produce one, it is almost always wrong -- which is why removing
    # the grounding deficit cannot rescue them.
    assert content["mean_loss_within_channel"] > 0.90


# --- sealed-label discipline survives regeneration --------------------------------------


@pytest.mark.parametrize("name", ["alpha_frontier.json", "loss_decomposition.json"])
def test_artifacts_disclose_a_verified_chain_and_no_sealed_reads(name: str) -> None:
    access = _load(name)["certification_access"]
    assert access["final_reads"] == 0
    assert access["shift_reads"] == 0
    assert access["certification_gold_read"] is True
    assert access["verified"] is True


def test_both_artifacts_read_exactly_the_documents_the_certifier_read(
    frontier: dict, decomposition: dict, certification: dict
) -> None:
    """A different head hash would mean a different set of documents was opened."""

    certifier = certification["certification_access"]
    for artifact in (frontier, decomposition):
        assert artifact["certification_access"]["head_hash"] == certifier["head_hash"]
        assert artifact["certification_access"]["documents_read"] == certifier["documents_read"]


@pytest.mark.parametrize("name", ["alpha_frontier.json", "loss_decomposition.json"])
def test_artifacts_declare_themselves_diagnostic(name: str) -> None:
    artifact = _load(name)
    assert artifact["diagnostic_only"] is True
    assert artifact["certifies_nothing"] is True
