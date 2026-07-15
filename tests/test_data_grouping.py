from __future__ import annotations

from conformalextract.data import DataDocument, build_duplicate_groups, grouped_split


def _doc(identifier: str, text: str, source: str) -> DataDocument:
    return DataDocument(
        dataset="fixture",
        document_id=identifier,
        source_id=source,
        nominal_split="train",
        text=text,
    )


def test_exact_hash_and_source_id_are_union_constraints() -> None:
    documents = [
        _doc("a", "Caf\u00e9 attack report", "https://example.test/story/1?ref=a"),
        _doc("b", "Cafe\u0301  attack\r\nreport", "https://other.test/story/2"),
        _doc("c", "Entirely different words", "https://example.test/story/1#section"),
    ]

    groups = build_duplicate_groups(documents, threshold=0.9, permutations=32)
    assert groups["a"] == groups["b"] == groups["c"]


def test_five_gram_near_duplicates_are_grouped() -> None:
    base = "one two three four five six seven eight nine ten eleven twelve"
    near = "one two three four five six seven eight nine ten eleven changed"
    far = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    documents = [_doc("a", base, "a"), _doc("b", near, "b"), _doc("c", far, "c")]

    groups = build_duplicate_groups(documents, threshold=0.7, permutations=128)
    assert groups["a"] == groups["b"]
    assert groups["a"] != groups["c"]


def test_grouped_split_is_deterministic_and_never_splits_a_group() -> None:
    group_ids = {"a": "g1", "b": "g1", "c": "g2", "d": "g3", "e": "g4"}
    first = grouped_split(group_ids, seed=42)
    second = grouped_split(dict(reversed(list(group_ids.items()))), seed=42)
    assert first == second
    assert first["a"] == first["b"]
