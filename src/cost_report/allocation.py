"""Asignación de costos a equipos.

Orden de prioridad: tag/label `team` del recurso → dueño de la cuenta en la config →
"sin-asignar". Lo sin asignar se reporta aparte: es la deuda de tagging a cerrar.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .config import Config
from .model import AllocatedCost, CostRecord

UNALLOCATED = "sin-asignar"


def allocate(records: Iterable[CostRecord], config: Config) -> Iterator[AllocatedCost]:
    for record in records:
        team = record.team or config.account_owners.get(record.account) or UNALLOCATED
        yield AllocatedCost(
            record=record,
            team=team,
            env=record.env or "sin-env",
            amount=config.to_report_currency(record.cost, record.currency),
        )
