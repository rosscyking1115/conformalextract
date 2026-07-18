"""Text-free RAMS -> ExampleProfile generation (build-profiles)."""

from __future__ import annotations


def load_event_ontology(text: str) -> dict[str, tuple[str, ...]]:
    """Parse ``event_role_multiplicities.txt`` into event type -> allowed roles.

    Each line is ``<event_type> <role> <mult> <role> <mult> ...``; roles keep file order.
    """

    ontology: dict[str, tuple[str, ...]] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        event_type = parts[0]
        roles = tuple(parts[i] for i in range(1, len(parts), 2))
        ontology[event_type] = roles
    return ontology
