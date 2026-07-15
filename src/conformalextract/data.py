"""Restricted-text loaders and deterministic document grouping."""

from __future__ import annotations

import hashlib
import json
import random
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class DataDocument:
    dataset: str
    document_id: str
    source_id: str
    nominal_split: str
    text: str


def normalize_document_text(text: str) -> str:
    value = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    return " ".join(value.split())


def canonicalize_source_id(value: str) -> str:
    """Remove URL transport details while retaining the source-document identity."""

    parsed = urlsplit(value.strip())
    if parsed.scheme and parsed.netloc:
        path = parsed.path.rstrip("/") or "/"
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))
    return value.strip().casefold()


def normalized_text_hash(text: str) -> str:
    return hashlib.sha256(normalize_document_text(text).encode("utf-8")).hexdigest()


def rams_inclusive_to_half_open(start: int, end_inclusive: int) -> tuple[int, int]:
    if start < 0 or end_inclusive < start:
        raise ValueError("invalid RAMS inclusive span")
    return start, end_inclusive + 1


def half_open_to_rams_inclusive(start: int, end: int) -> tuple[int, int]:
    if start < 0 or end <= start:
        raise ValueError("invalid half-open span")
    return start, end - 1


def word_five_grams(text: str) -> frozenset[str]:
    words = normalize_document_text(text).casefold().split()
    if len(words) < 5:
        return frozenset([" ".join(words)]) if words else frozenset([""])
    return frozenset(" ".join(words[index : index + 5]) for index in range(len(words) - 4))


class _UnionFind:
    def __init__(self, keys: Iterable[str]) -> None:
        self.parent = {key: key for key in keys}

    def find(self, key: str) -> str:
        root = key
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[key] != key:
            next_key = self.parent[key]
            self.parent[key] = root
            key = next_key
        return root

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        parent, child = sorted((left_root, right_root))
        self.parent[child] = parent


def _union_buckets(union_find: _UnionFind, buckets: Mapping[str, Sequence[str]]) -> None:
    for values in buckets.values():
        if len(values) > 1:
            first = values[0]
            for other in values[1:]:
                union_find.union(first, other)


def build_duplicate_groups(
    documents: Sequence[DataDocument], *, threshold: float = 0.9, permutations: int = 128
) -> dict[str, str]:
    """Union source IDs, exact hashes, and verified MinHash five-gram candidates."""

    try:
        from datasketch import MinHash, MinHashLSH  # type: ignore[import-untyped]
    except ImportError as error:  # pragma: no cover - installation guard
        raise RuntimeError("install the 'data' extra to run duplicate grouping") from error

    identifiers = [document.document_id for document in documents]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("document identifiers must be unique")
    union_find = _UnionFind(identifiers)
    exact: dict[str, list[str]] = defaultdict(list)
    sources: dict[str, list[str]] = defaultdict(list)
    for document in documents:
        exact[normalized_text_hash(document.text)].append(document.document_id)
        sources[canonicalize_source_id(document.source_id)].append(document.document_id)
    _union_buckets(union_find, exact)
    _union_buckets(union_find, sources)

    lsh = MinHashLSH(threshold=threshold, num_perm=permutations)
    signatures: dict[str, MinHash] = {}
    shingles: dict[str, frozenset[str]] = {}
    for document in sorted(documents, key=lambda item: item.document_id):
        document_shingles = word_five_grams(document.text)
        signature = MinHash(num_perm=permutations, seed=42)
        for shingle in sorted(document_shingles):
            signature.update(shingle.encode("utf-8"))
        signatures[document.document_id] = signature
        shingles[document.document_id] = document_shingles
        lsh.insert(document.document_id, signature)

    for document_id in sorted(signatures):
        for candidate_id in sorted(lsh.query(signatures[document_id])):
            if candidate_id <= document_id:
                continue
            left = shingles[document_id]
            right = shingles[candidate_id]
            jaccard = len(left & right) / len(left | right)
            if jaccard >= threshold:
                union_find.union(document_id, candidate_id)

    members: dict[str, list[str]] = defaultdict(list)
    for document_id in sorted(identifiers):
        members[union_find.find(document_id)].append(document_id)
    result: dict[str, str] = {}
    for group_members in members.values():
        group_id = hashlib.sha256("\n".join(group_members).encode()).hexdigest()
        result.update(dict.fromkeys(group_members, group_id))
    return result


def grouped_split(
    document_groups: Mapping[str, str],
    *,
    seed: int,
    proportions: Mapping[str, float] | None = None,
) -> dict[str, str]:
    """Assign whole duplicate groups to deterministic research roles."""

    roles = proportions or {
        "train": 0.60,
        "development": 0.15,
        "certification": 0.10,
        "final": 0.10,
        "shift": 0.05,
    }
    if not roles or any(value < 0 for value in roles.values()):
        raise ValueError("split proportions must be non-negative")
    total = sum(roles.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError("split proportions must sum to one")

    groups = sorted(set(document_groups.values()))
    random.Random(seed).shuffle(groups)
    cumulative: list[tuple[str, float]] = []
    running = 0.0
    for role, proportion in roles.items():
        running += proportion
        cumulative.append((role, running))
    group_role: dict[str, str] = {}
    for index, group_id in enumerate(groups):
        position = (index + 0.5) / max(1, len(groups))
        group_role[group_id] = next(role for role, boundary in cumulative if position <= boundary)
    return {document_id: group_role[group_id] for document_id, group_id in document_groups.items()}


def _read_jsonlines(path: Path) -> Iterator[dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON in {path.name}:{line_number}") from error
            if not isinstance(record, dict):
                raise ValueError(f"expected object in {path.name}:{line_number}")
            yield record


def load_rams(root: Path) -> list[DataDocument]:
    documents: list[DataDocument] = []
    for split in ("train", "dev", "test"):
        path = root / "data" / f"{split}.jsonlines"
        for record in _read_jsonlines(path):
            document_id = str(record["doc_key"])
            sentences = record["sentences"]
            if not isinstance(sentences, list):
                raise ValueError(f"RAMS sentences must be a list: {document_id}")
            text = "\n".join(" ".join(map(str, sentence)) for sentence in sentences)
            source_id = str(record.get("source_url") or f"rams:{document_id}")
            documents.append(DataDocument("RAMS", f"rams:{document_id}", source_id, split, text))
    return documents


def load_wikievents(root: Path) -> list[DataDocument]:
    documents: list[DataDocument] = []
    for split in ("train", "dev", "test"):
        path = root / f"{split}.jsonl"
        for record in _read_jsonlines(path):
            document_id = str(record["doc_id"])
            documents.append(
                DataDocument(
                    "WikiEvents",
                    f"wikievents:{document_id}",
                    f"wikievents:{document_id}",
                    split,
                    str(record["text"]),
                )
            )
    return documents


def inventory_summary(
    documents: Sequence[DataDocument], groups: Mapping[str, str]
) -> dict[str, object]:
    by_dataset = Counter(document.dataset for document in documents)
    by_nominal_split = Counter(
        f"{document.dataset}:{document.nominal_split}" for document in documents
    )
    group_sizes = Counter(groups.values())
    exact_hashes = Counter(normalized_text_hash(document.text) for document in documents)
    return {
        "schema_version": "1",
        "document_count": len(documents),
        "independent_group_count": len(group_sizes),
        "by_dataset": dict(sorted(by_dataset.items())),
        "by_nominal_split": dict(sorted(by_nominal_split.items())),
        "exact_duplicate_cluster_count": sum(size > 1 for size in exact_hashes.values()),
        "multi_document_group_count": sum(size > 1 for size in group_sizes.values()),
        "largest_group_size": max(group_sizes.values(), default=0),
    }
