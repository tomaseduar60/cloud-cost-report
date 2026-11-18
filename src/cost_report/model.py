"""Modelo común. Cada proveedor se normaliza a CostRecord antes de agregar nada.

Azure habla de suscripciones, resource groups y meter categories; GCP de proyectos,
servicios y labels. El reporte no debería saber de ninguno de los dos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CostRecord:
    provider: str  # azure | gcp
    account: str  # suscripción (Azure) o proyecto (GCP)
    service: str  # categoría normalizada: compute, kubernetes, storage, ...
    day: date
    cost: Decimal  # en la moneda original
    currency: str
    tags: dict[str, str] = field(default_factory=dict)
    raw_service: str = ""  # nombre original del proveedor, para auditar el mapeo

    @property
    def team(self) -> str | None:
        return self.tags.get("team")

    @property
    def env(self) -> str | None:
        return self.tags.get("env")


@dataclass(frozen=True)
class AllocatedCost:
    """CostRecord ya convertido a la moneda del reporte y asignado a un equipo."""

    record: CostRecord
    team: str
    env: str
    amount: Decimal  # en moneda del reporte
