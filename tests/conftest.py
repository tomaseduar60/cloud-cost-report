from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from cost_report.config import Config, load_config
from cost_report.model import CostRecord

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def root() -> Path:
    return ROOT


@pytest.fixture
def config() -> Config:
    return load_config(ROOT / "config.yaml")


def record(
    provider: str = "azure",
    account: str = "sub-x",
    service: str = "kubernetes",
    day: date = date(2024, 5, 1),
    cost: str = "10",
    currency: str = "USD",
    **tags: str,
) -> CostRecord:
    return CostRecord(provider, account, service, day, Decimal(cost), currency, dict(tags))
