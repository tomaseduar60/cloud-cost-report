"""GCP Billing export en BigQuery.

Variables de entorno:
  GCP_BILLING_TABLE  ej. my-project.billing.gcp_billing_export_v1_XXXXXX
Autenticación con Application Default Credentials.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from datetime import date

from ..model import CostRecord
from .normalize import gcp_row

SQL = """
SELECT
  DATE(usage_start_time) AS day,
  project.id AS project_id,
  service.description AS service_description,
  currency,
  TO_JSON_STRING(labels) AS labels_json,
  SUM(cost) AS cost,
  SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) AS c), 0)) AS credits
FROM `{table}`
WHERE DATE(usage_start_time) BETWEEN @start AND @end
GROUP BY day, project_id, service_description, currency, labels_json
"""


class GcpBillingExport:
    name = "gcp"

    def __init__(self, table: str) -> None:
        self.table = table

    @classmethod
    def from_env(cls) -> GcpBillingExport:
        return cls(os.environ["GCP_BILLING_TABLE"])

    def fetch(self, start: date, end: date) -> Iterator[CostRecord]:
        from google.cloud import bigquery

        client = bigquery.Client()
        job = client.query(
            SQL.format(table=self.table),
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start", "DATE", start),
                    bigquery.ScalarQueryParameter("end", "DATE", end),
                ]
            ),
        )
        for row in job.result():
            yield gcp_row(
                {
                    "usage_start_time": row["day"],
                    "project": {"id": row["project_id"]},
                    "service": {"description": row["service_description"]},
                    "cost": row["cost"],
                    "currency": row["currency"],
                    "credits": [{"amount": row["credits"]}],
                    "labels": json.loads(row["labels_json"] or "[]"),
                }
            )
