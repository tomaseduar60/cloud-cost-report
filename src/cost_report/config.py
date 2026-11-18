"""Configuración del reporte: moneda, tipos de cambio, reglas de asignación y presupuestos."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    currency: str = "USD"
    rates: dict[str, Decimal] = field(default_factory=dict)  # 1 unidad de X = rate en currency
    # Si el recurso no tiene tag team, se asigna por cuenta (suscripción/proyecto).
    account_owners: dict[str, str] = field(default_factory=dict)
    budgets: dict[str, Decimal] = field(default_factory=dict)  # equipo -> presupuesto mensual
    alert_threshold: Decimal = Decimal("0.8")

    def to_report_currency(self, amount: Decimal, currency: str) -> Decimal:
        if currency == self.currency:
            return amount
        if currency not in self.rates:
            raise ConfigError(f"No hay tipo de cambio para {currency} -> {self.currency}.")
        return amount * self.rates[currency]


def load_config(path: Path) -> Config:
    data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    return Config(
        currency=str(data.get("currency", "USD")),
        rates={k: Decimal(str(v)) for k, v in (data.get("rates") or {}).items()},
        account_owners={str(k): str(v) for k, v in (data.get("account_owners") or {}).items()},
        budgets={k: Decimal(str(v)) for k, v in (data.get("budgets") or {}).items()},
        alert_threshold=Decimal(str(data.get("alert_threshold", "0.8"))),
    )
