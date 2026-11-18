"""Genera data/mock con el formato real de los exports de Azure y GCP.

Semilla fija: los mismos datos en cada corrida. Incluye a propósito lo que hace difícil
un reporte real: recursos sin tag de equipo, créditos en GCP, una moneda distinta al
dólar y un pico de costo a mitad de mes.

    python scripts/generate_mock_data.py
"""

from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "mock"
START, DAYS = date(2024, 4, 1), 61  # abril y mayo, para comparar dos meses
rng = random.Random(42)

AZURE = [
    # (suscripción, meter category, costo diario base, tags, moneda)
    ("sub-platform-prd", "Azure Kubernetes Service", 110, {"team": "platform", "env": "prd"}, "USD"),
    ("sub-platform-prd", "Virtual Machines", 45, {"team": "platform", "env": "prd"}, "USD"),
    ("sub-platform-prd", "Log Analytics", 18, {"env": "prd"}, "USD"),  # sin team
    ("sub-platform-dev", "Azure Kubernetes Service", 30, {"team": "platform", "env": "dev"}, "USD"),
    ("sub-data-prd", "Azure Cosmos DB", 60, {"team": "data", "env": "prd"}, "USD"),
    ("sub-data-prd", "Storage", 14, {}, "USD"),  # se asigna por dueño de la cuenta
    ("sub-payments-prd", "Azure App Service", 22, {"team": "payments", "env": "prd"}, "EUR"),
    ("sub-payments-prd", "Bandwidth", 6, {"team": "payments", "env": "prd"}, "EUR"),
    ("sub-shared", "Virtual Network", 9, {}, "USD"),  # ni tag ni dueño: sin-asignar
]

GCP = [
    # (proyecto, servicio, costo diario base, labels, créditos %)
    ("shop-prd-4821", "Kubernetes Engine", 95, {"team": "commerce", "env": "prd"}, 0.10),
    ("shop-prd-4821", "Cloud SQL", 40, {"team": "commerce", "env": "prd"}, 0.0),
    ("shop-prd-4821", "Cloud Run", 12, {"env": "prd"}, 0.0),  # sin team: dueño de cuenta
    ("shop-qa-2290", "Kubernetes Engine", 25, {"team": "commerce", "env": "qa"}, 0.10),
    ("analytics-prd-1177", "BigQuery", 70, {"team": "data", "env": "prd"}, 0.0),
    ("analytics-prd-1177", "Cloud Storage", 11, {"team": "data", "env": "prd"}, 0.0),
    ("platform-shared-0042", "Cloud Logging", 8, {}, 0.0),  # sin-asignar
    ("platform-shared-0042", "Secret Manager", 1, {"team": "platform", "env": "prd"}, 0.0),
]


def daily(base: float, day: int) -> float:
    weekend = 0.85 if (START + timedelta(days=day)).weekday() >= 5 else 1.0
    growth = 1 + day * 0.002  # leve crecimiento mes a mes
    spike = 2.4 if 45 <= day <= 47 else 1.0  # incidente: autoscaling desbocado
    return round(base * weekend * growth * spike * rng.uniform(0.9, 1.1), 4)


def write_azure() -> None:
    with (OUT / "azure_cost_export.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["Date", "SubscriptionName", "ResourceGroup",
                                           "MeterCategory", "CostInBillingCurrency",
                                           "BillingCurrency", "Tags"])
        w.writeheader()
        for d in range(DAYS):
            for sub, meter, base, tags, cur in AZURE:
                cost = daily(base, d) if "Kubernetes" in meter else daily(base, min(d, 44))
                w.writerow({
                    "Date": (START + timedelta(days=d)).strftime("%Y%m%d"),
                    "SubscriptionName": sub,
                    "ResourceGroup": f"rg-{sub.removeprefix('sub-')}",
                    "MeterCategory": meter,
                    "CostInBillingCurrency": cost,
                    "BillingCurrency": cur,
                    "Tags": json.dumps(tags) if tags else "",
                })


def write_gcp() -> None:
    with (OUT / "gcp_billing_export.jsonl").open("w") as fh:
        for d in range(DAYS):
            for project, service, base, labels, credit in GCP:
                cost = daily(base, min(d, 44))
                row = {
                    "usage_start_time": f"{START + timedelta(days=d)}T00:00:00Z",
                    "project": {"id": project},
                    "service": {"description": service},
                    "cost": cost,
                    "currency": "USD",
                    "credits": [{"name": "CUD", "amount": round(-cost * credit, 4)}] if credit else [],
                    "labels": [{"key": k, "value": v} for k, v in labels.items()],
                }
                fh.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    write_azure()
    write_gcp()
    print(f"datos mock en {OUT}")
