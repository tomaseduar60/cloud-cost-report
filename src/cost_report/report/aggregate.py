"""Agregaciones del reporte: totales, tendencia diaria, variación y alertas de presupuesto."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ..allocation import UNALLOCATED
from ..config import Config
from ..model import AllocatedCost

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class BudgetStatus:
    team: str
    spent: Decimal
    budget: Decimal

    @property
    def ratio(self) -> Decimal:
        return self.spent / self.budget if self.budget else Decimal(0)


@dataclass(frozen=True)
class Mover:
    key: str
    current: Decimal
    previous: Decimal

    @property
    def delta(self) -> Decimal:
        return self.current - self.previous

    @property
    def pct(self) -> Decimal | None:
        return (self.delta / self.previous * 100) if self.previous else None


@dataclass
class Report:
    start: date
    end: date
    currency: str
    total: Decimal = Decimal(0)
    by_provider: dict[str, Decimal] = field(default_factory=dict)
    by_team: dict[str, Decimal] = field(default_factory=dict)
    by_service: dict[str, Decimal] = field(default_factory=dict)
    by_env: dict[str, Decimal] = field(default_factory=dict)
    daily: dict[date, dict[str, Decimal]] = field(default_factory=dict)
    movers: list[Mover] = field(default_factory=list)
    budgets: list[BudgetStatus] = field(default_factory=list)
    alerts: list[BudgetStatus] = field(default_factory=list)

    @property
    def unallocated(self) -> Decimal:
        return self.by_team.get(UNALLOCATED, Decimal(0))

    @property
    def unallocated_pct(self) -> Decimal:
        return self.unallocated / self.total * 100 if self.total else Decimal(0)


def _sorted(totals: dict[str, Decimal]) -> dict[str, Decimal]:
    return {k: money(v) for k, v in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)}


KEYS: dict[str, Callable[[AllocatedCost], str]] = {
    "provider": lambda c: c.record.provider,
    "team": lambda c: c.team,
    "service": lambda c: c.record.service,
    "env": lambda c: c.env,
}


def _sum_by(costs: list[AllocatedCost], key: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for c in costs:
        totals[KEYS[key](c)] += c.amount
    return dict(totals)


def build_report(
    current: Iterable[AllocatedCost],
    config: Config,
    start: date,
    end: date,
    previous: Iterable[AllocatedCost] = (),
    top_movers: int = 5,
) -> Report:
    costs = list(current)
    report = Report(start=start, end=end, currency=config.currency)
    report.total = money(sum((c.amount for c in costs), Decimal(0)))
    report.by_provider = _sorted(_sum_by(costs, "provider"))
    report.by_team = _sorted(_sum_by(costs, "team"))
    report.by_service = _sorted(_sum_by(costs, "service"))
    report.by_env = _sorted(_sum_by(costs, "env"))

    daily: dict[date, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for c in costs:
        daily[c.record.day][c.record.provider] += c.amount
    report.daily = {d: {p: money(v) for p, v in daily[d].items()} for d in sorted(daily)}

    prev_by_team = _sum_by(list(previous), "team")
    keys = set(report.by_team) | set(prev_by_team)
    movers = [
        Mover(k, report.by_team.get(k, Decimal(0)), money(prev_by_team.get(k, Decimal(0))))
        for k in keys
    ]
    report.movers = sorted(movers, key=lambda m: abs(m.delta), reverse=True)[:top_movers]

    report.budgets = [
        BudgetStatus(team, report.by_team.get(team, Decimal(0)), budget)
        for team, budget in sorted(config.budgets.items())
    ]
    report.alerts = [b for b in report.budgets if b.ratio >= config.alert_threshold]
    return report
