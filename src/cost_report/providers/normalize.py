"""Normalizadores: convierten filas con el formato real de cada proveedor a CostRecord.

Los usan tanto los providers reales como el mock, así los datos de prueba pasan por
exactamente el mismo código que los de producción.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ..model import CostRecord
from ..services import normalize as normalize_service


def azure_row(row: dict[str, Any]) -> CostRecord:
    """Fila del export de Azure Cost Management (costo amortizado)."""
    tags = row.get("Tags") or {}
    if isinstance(tags, str):
        tags = json.loads(tags) if tags.strip() else {}
    raw_service = str(row["MeterCategory"])
    return CostRecord(
        provider="azure",
        account=str(row["SubscriptionName"]),
        service=normalize_service("azure", raw_service),
        raw_service=raw_service,
        day=_to_date(row["Date"]),
        cost=Decimal(str(row["CostInBillingCurrency"])),
        currency=str(row["BillingCurrency"]),
        tags={str(k).lower(): str(v) for k, v in tags.items()},
    )


def gcp_row(row: dict[str, Any]) -> CostRecord:
    """Fila del billing export de GCP en BigQuery. El costo neto descuenta los créditos."""
    credits = sum(Decimal(str(c.get("amount", 0))) for c in row.get("credits") or [])
    labels = {str(lbl["key"]).lower(): str(lbl["value"]) for lbl in row.get("labels") or []}
    raw_service = str(row["service"]["description"])
    return CostRecord(
        provider="gcp",
        account=str(row["project"]["id"]),
        service=normalize_service("gcp", raw_service),
        raw_service=raw_service,
        day=_to_date(row["usage_start_time"]),
        cost=Decimal(str(row["cost"])) + credits,  # los créditos vienen negativos
        currency=str(row["currency"]),
        tags=labels,
    )


def _to_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)
    if len(text) == 8 and text.isdigit():  # Azure: 20240131
        return date(int(text[:4]), int(text[4:6]), int(text[6:]))
    return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
