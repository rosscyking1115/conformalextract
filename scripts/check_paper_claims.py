"""Every paper figure must resolve to an artifact carrying its value AND its configuration.

This is the guard `claims.verify_ledger` is not. `verify_ledger` checks that a claim's cited
evidence **paths exist and are git-tracked**; it never opens a file, never compares a number, and
never sees the configuration that produced one. A claim quoting a figure that appears nowhere in
its own evidence returns ``ok``, because the metric is satisfied by absence. That gap is the
recorded mechanism behind five quoting errors in the reported claims, and behind their common
direction.

Four properties are load-bearing. A claims guard missing any of them passes documents it should
fail, and this repository has now shipped two that could not have caught the class:

1. **It opens both.** The artifact and the document, and compares values across them.
2. **The paper is the population, not the artifacts.** A figure with no backing entry FAILS. It is
   not exempted by being absent from a list --- a scope defined by what an artifact already
   contains cannot see a figure that was never written into it, which is how a sensitivity
   artifact came to stamp four quantities while the write-up quoted several it had never heard of.
3. **A configuration mismatch fails even when the value matches.** This is the whole defect class.
   ``0.0925`` is a Hoeffding radius at an allocation the Hoeffding construction never ran; an
   acceptance bound of ``0.2017`` is correct at one δ allocation and false at the one the sentence
   named. Every value-only check passes both.
4. **It refuses to pass on an empty claim list**, or on an empty figure extraction. A checker with
   nothing to check passes vacuously, which is the absence failure applied to the checker itself.

Usage::

    uv run python scripts/check_paper_claims.py             # exit 1 on any failure
    uv run python scripts/check_paper_claims.py --list      # show what resolves
    uv run python scripts/check_paper_claims.py --json      # machine-readable report

**This guard does not decide whether a figure is the right figure to quote.** It checks that a
written number matches a recorded one computed under the configuration the entry declares. A
manifest entry pointing at a real value under a truthfully-declared configuration that is
nonetheless the wrong quantity for the sentence will pass. That is a reviewer's job and is stated
here rather than left to be discovered.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paper_figures import Figure, extract_figures

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence" / "plan4" / "paper_claims.json"

UNBACKED = "UNBACKED"
ARTIFACT_MISSING = "ARTIFACT_MISSING"
POINTER_MISSING = "POINTER_MISSING"
VALUE_MISMATCH = "VALUE_MISMATCH"
CONFIG_ABSENT = "CONFIG_ABSENT"
CONFIG_MISMATCH = "CONFIG_MISMATCH"


@dataclass
class Failure:
    kind: str
    figure: str
    detail: str
    where: str = ""

    def line(self) -> str:
        loc = f"  [{self.where}]" if self.where else ""
        return f"{self.kind:<16} {self.figure:<14} {self.detail}{loc}"


_SEGMENT = re.compile(
    r"""
      \[ '([^']*)' \]        # ['literal key'] -- for keys containing dots, e.g. ['1.00']
    | \[ (-?\d+) \]          # [3] list index
    | ([^.\[\]]+)            # bare key
    """,
    re.VERBOSE,
)


def resolve(data: Any, pointer: str) -> Any:
    """Resolve a pointer, raising KeyError if any step is absent.

    Segments are dot-separated bare keys, ``[i]`` list indices, or ``['literal']`` for keys that
    contain a dot themselves --- the grounded-fraction strata are keyed ``'1.00'``, and splitting
    those on the dot silently addresses nothing.
    """

    current = data
    position = 0
    while position < len(pointer):
        if pointer[position] == ".":
            position += 1
            continue
        match = _SEGMENT.match(pointer, position)
        if match is None:
            raise KeyError(pointer)
        position = match.end()
        literal, index, bare = match.groups()
        if index is not None:
            if not isinstance(current, list):
                raise KeyError(pointer)
            offset = int(index)
            if not -len(current) <= offset < len(current):
                raise KeyError(pointer)
            current = current[offset]
            continue
        key = literal if literal is not None else bare
        if not isinstance(current, dict) or key not in current:
            raise KeyError(pointer)
        current = current[key]
    return current


def render(value: Any, spec: str) -> str:
    """Turn an artifact value into the string the paper writes.

    Operations chain with ``|``: ``abs`` (drop sign, for figures the paper prints as $-$0.403),
    ``pctN`` (multiply by 100, N decimals), ``roundN``, ``int``, ``raw``.
    """

    current: Any = value
    for op in spec.split("|"):
        if op == "abs":
            current = abs(float(current))
        elif op == "int":
            current = str(round(float(current)))
        elif op == "raw":
            current = str(current)
        elif op.startswith("pct"):
            current = f"{float(current) * 100:.{int(op[3:])}f}"
        elif op.startswith("round"):
            current = f"{float(current):.{int(op[5:])}f}"
        else:
            raise ValueError(f"unknown render op: {op!r}")
    return str(current)


def load_manifest(path: Path = MANIFEST) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["claims"]
    by_figure: dict[str, dict[str, Any]] = {}
    for entry in entries:
        by_figure[str(entry["figure"])] = entry
    return by_figure


def check(
    figures: list[Figure], manifest: dict[str, dict[str, Any]]
) -> tuple[list[Failure], list[tuple[str, str]]]:
    failures: list[Failure] = []
    passed: list[tuple[str, str]] = []
    cache: dict[str, Any] = {}

    for figure in sorted(figures, key=lambda f: f.value):
        entry = manifest.get(figure.value)
        where = f"line {figure.lines[0]}"
        if entry is None:
            failures.append(
                Failure(UNBACKED, figure.token, "no manifest entry: no artifact carries it", where)
            )
            continue

        relative = entry["artifact"]
        if relative not in cache:
            path = ROOT / relative
            if not path.exists():
                failures.append(Failure(ARTIFACT_MISSING, figure.token, relative, where))
                cache[relative] = None
                continue
            cache[relative] = json.loads(path.read_text(encoding="utf-8"))
        artifact = cache[relative]
        if artifact is None:
            failures.append(Failure(ARTIFACT_MISSING, figure.token, relative, where))
            continue

        pointer = entry["pointer"]
        try:
            value = resolve(artifact, pointer)
        except KeyError:
            failures.append(
                Failure(POINTER_MISSING, figure.token, f"{relative} :: {pointer}", where)
            )
            continue

        rendered = render(value, entry.get("render", "raw"))
        if rendered != figure.value:
            failures.append(
                Failure(
                    VALUE_MISMATCH,
                    figure.token,
                    f"paper says {figure.value}, {relative} :: {pointer} renders {rendered}",
                    where,
                )
            )
            continue

        # A configuration mismatch fails even when the value matches. Each key is a pointer into
        # the SAME artifact, so a configuration the artifact does not record cannot be declared.
        bad_config = False
        for config_pointer, expected in (entry.get("configuration") or {}).items():
            try:
                actual = resolve(artifact, config_pointer)
            except KeyError:
                failures.append(
                    Failure(
                        CONFIG_ABSENT,
                        figure.token,
                        f"{relative} does not record {config_pointer}",
                        where,
                    )
                )
                bad_config = True
                continue
            if actual != expected:
                failures.append(
                    Failure(
                        CONFIG_MISMATCH,
                        figure.token,
                        f"{config_pointer} is {actual!r}, entry declares {expected!r}",
                        where,
                    )
                )
                bad_config = True
        if not bad_config:
            passed.append((figure.token, f"{relative} :: {pointer}"))

    return failures, passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="print what resolves and exit 0")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--paper", type=Path, default=None)
    args = parser.parse_args()

    figures = extract_figures(args.paper) if args.paper else extract_figures()
    if not figures:
        print("FAIL: no figures extracted from the paper; the check would be vacuous")
        return 1

    if not args.manifest.exists():
        print(f"FAIL: manifest missing: {args.manifest}")
        return 1
    manifest = load_manifest(args.manifest)
    if not manifest:
        print("FAIL: manifest defines no claims; the check would be vacuous")
        return 1

    failures, passed = check(figures, manifest)

    if args.json:
        print(
            json.dumps(
                {
                    "figures": len(figures),
                    "backed": len(passed),
                    "failures": [f.__dict__ for f in failures],
                },
                indent=2,
            )
        )
        return 1 if failures else 0

    if args.list:
        for token, source in passed:
            print(f"  {token:<14} {source}")
        print(
            f"\n{len(passed)} of {len(figures)} figures resolve to an artifact "
            "carrying its configuration"
        )
        return 0

    by_kind: dict[str, list[Failure]] = {}
    for failure in failures:
        by_kind.setdefault(failure.kind, []).append(failure)
    for kind in (
        VALUE_MISMATCH,
        CONFIG_MISMATCH,
        CONFIG_ABSENT,
        POINTER_MISSING,
        ARTIFACT_MISSING,
        UNBACKED,
    ):
        for failure in by_kind.get(kind, []):
            print(failure.line())

    if failures:
        print(
            f"\nFAIL: {len(failures)} of {len(figures)} figures in the paper are unbacked or "
            f"disagree with the artifact that should carry them ({len(passed)} pass)."
        )
        return 1
    print(
        f"ok: all {len(figures)} figures resolve to an artifact carrying value and configuration."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
