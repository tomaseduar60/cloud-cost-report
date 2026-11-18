"""GCP Billing export en BigQuery.

Variables de entorno:
  GCP_BILLING_TABLE  ej. my-project.billing.gcp_billing_export_v1_XXXXXX
Autenticación con Application Default Credentials.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date

from ..model import CostRecord
from .normalize import gcp_row

SQL = """
SELECT
  DATE(usage_start_time) AS usage_start_time,
  STRUCT(project.id AS id) AS project,
  STRUCT(service.description AS description) AS service,
  SUM(cost) AS cost,
  currency,
  ARRAY_CONCAT_AGG(credits) AS credits,
  ANY_VALUE(labels) AS labels
FROM `{table}`
WHERE DATE(usage_start_time) BETWEEN @start AND @end
GROUP BY 1, 2, 3, 5, TO_JSON_STRING(labels)
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
            yield gcp_row(dict(row.items()))
