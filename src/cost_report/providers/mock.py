"""Proveedores con datos de ejemplo en data/mock, con el mismo formato que los exports reales."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path

from ..model import CostRecord
from .normalize import azure_row, gcp_row


class MockAzure:
    name = "azure"

    def __init__(self, directory: Path) -> None:
        self.path = directory / "azure_cost_export.csv"

    def fetch(self, start: date, end: date) -> Iterator[CostRecord]:
        with self.path.open(newline="") as fh:
            for row in csv.DictReader(fh):
                record = azure_row(row)
                if start <= record.day <= end:
                    yield record


class MockGcp:
    name = "gcp"

    def __init__(self, directory: Path) -> None:
        self.path = directory / "gcp_billing_export.jsonl"

    def fetch(self, start: date, end: date) -> Iterator[CostRecord]:
        with self.path.open() as fh:
            for line in fh:
                if line.strip():
                    record = gcp_row(json.loads(line))
                    if start <= record.day <= end:
                        yield record
