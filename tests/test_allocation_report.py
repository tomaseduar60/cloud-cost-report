from datetime import date
from decimal import Decimal

import pytest
from conftest import record

from cost_report.allocation import UNALLOCATED, allocate
from cost_report.config import Config, ConfigError
from cost_report.report import build_report


def test_prioridad_tag_luego_dueño_luego_sin_asignar(config: Config) -> None:
    costs = list(
        allocate(
            [
                record(account="sub-data-prd", team="platform"),  # el tag gana
                record(account="sub-data-prd"),  # dueño de la cuenta
                record(account="huérfana"),
            ],
            config,
        )
    )
    assert [c.team for c in costs] == ["platform", "data", UNALLOCATED]
    assert costs[2].env == "sin-env"


def test_conversion_de_moneda(config: Config) -> None:
    [c] = allocate([record(cost="100", currency="EUR", team="x")], config)
    assert c.amount == Decimal("108.00")
    with pytest.raises(ConfigError, match="JPY"):
        list(allocate([record(currency="JPY", team="x")], config))


def test_reporte_totales_alertas_y_variacion() -> None:
    config = Config(
        budgets={"a": Decimal("100"), "b": Decimal("1000")}, alert_threshold=Decimal("0.8")
    )
    current = list(
        allocate(
            [
                record(provider="azure", cost="90", team="a", env="prd", day=date(2024, 5, 1)),
                record(
                    provider="gcp", service="analytics", cost="50", team="b", day=date(2024, 5, 2)
                ),
                record(provider="gcp", cost="10", day=date(2024, 5, 2)),
            ],
            config,
        )
    )
    previous = list(allocate([record(cost="45", team="a")], config))
    r = build_report(current, config, date(2024, 5, 1), date(2024, 5, 31), previous=previous)

    assert r.total == Decimal("150.00")
    assert r.by_provider == {"azure": Decimal("90.00"), "gcp": Decimal("60.00")}
    assert list(r.by_team) == ["a", "b", UNALLOCATED]  # ordenado de mayor a menor
    assert r.unallocated == Decimal("10.00")
    assert round(r.unallocated_pct, 2) == Decimal("6.67")
    assert r.daily[date(2024, 5, 2)] == {"gcp": Decimal("60.00")}
    assert [a.team for a in r.alerts] == ["a"]  # 90 de 100

    movers = {m.key: m for m in r.movers}
    assert movers["a"].delta == Decimal("45.00") and movers["a"].pct == Decimal("100")
    assert movers["b"].pct is None  # equipo nuevo en el período


def test_reporte_vacio() -> None:
    r = build_report([], Config(), date(2024, 1, 1), date(2024, 1, 2))
    assert r.total == 0 and r.unallocated_pct == 0 and r.alerts == []
