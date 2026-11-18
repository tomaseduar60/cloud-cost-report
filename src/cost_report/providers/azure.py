"""Azure Cost Management Query API (costo amortizado, agrupado por día y dimensiones).

Variables de entorno:
  AZURE_COST_SCOPE   ej. /providers/Microsoft.Billing/billingAccounts/<id>
                     o /subscriptions/<id>
Autenticación con DefaultAzureCredential (az login, managed identity o workload identity).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date
from typing import Any

from ..model import CostRecord
from .normalize import azure_row


class AzureCostManagement:
    name = "azure"

    def __init__(self, scope: str) -> None:
        self.scope = scope

    @classmethod
    def from_env(cls) -> AzureCostManagement:
        return cls(os.environ["AZURE_COST_SCOPE"])

    def fetch(self, start: date, end: date) -> Iterator[CostRecord]:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.costmanagement import CostManagementClient
        from azure.mgmt.costmanagement.models import (
            QueryAggregation,
            QueryDataset,
            QueryDefinition,
            QueryGrouping,
            QueryTimePeriod,
        )

        client = CostManagementClient(DefaultAzureCredential())
        query = QueryDefinition(
            type="AmortizedCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(from_property=start, to=end),
            dataset=QueryDataset(
                granularity="Daily",
                aggregation={
                    "cost": QueryAggregation(name="CostInBillingCurrency", function="Sum")
                },
                grouping=[
                    QueryGrouping(type="Dimension", name="SubscriptionName"),
                    QueryGrouping(type="Dimension", name="MeterCategory"),
                    QueryGrouping(type="TagKey", name="team"),
                    QueryGrouping(type="TagKey", name="env"),
                ],
            ),
        )
        result = client.query.usage(self.scope, query)
        columns = [c.name for c in result.columns]
        for values in result.rows:
            raw: dict[str, Any] = dict(zip(columns, values, strict=False))
            tags = {k: raw.pop(k) for k in ("team", "env") if raw.get(k)}
            yield azure_row(
                {
                    "Date": raw["UsageDate"],
                    "SubscriptionName": raw["SubscriptionName"],
                    "MeterCategory": raw["MeterCategory"],
                    "CostInBillingCurrency": raw["CostInBillingCurrency"],
                    "BillingCurrency": raw.get("Currency", "USD"),
                    "Tags": tags,
                }
            )
