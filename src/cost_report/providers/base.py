from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Protocol

from ..model import CostRecord


class CostProvider(Protocol):
    name: str

    def fetch(self, start: date, end: date) -> Iterator[CostRecord]: ...


def get_provider(name: str, *, mock_dir: Path | None = None) -> CostProvider:
    if name == "mock-azure":
        from .mock import MockAzure

        return MockAzure(mock_dir or Path("data/mock"))
    if name == "mock-gcp":
        from .mock import MockGcp

        return MockGcp(mock_dir or Path("data/mock"))
    if name == "azure":
        from .azure import AzureCostManagement

        return AzureCostManagement.from_env()
    if name == "gcp":
        from .gcp import GcpBillingExport

        return GcpBillingExport.from_env()
    raise ValueError(f"Proveedor desconocido: {name}")
