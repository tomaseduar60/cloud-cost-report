"""Salidas del reporte: Markdown (para PRs/Slack), HTML (para compartir) y CSV (para planillas)."""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..model import AllocatedCost
from .aggregate import Report

_env = Environment(
    loader=PackageLoader("cost_report.report", "templates"),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def fmt(value: Decimal) -> str:
    return f"{value:,.2f}"


def pct(value: Decimal | None) -> str:
    return "nuevo" if value is None else f"{value:+.1f}%"


_env.filters["money"] = fmt
_env.filters["pct"] = pct


def to_markdown(report: Report) -> str:
    return _env.get_template("report.md.j2").render(r=report)


def to_html(report: Report) -> str:
    max_day = max((sum(v.values()) for v in report.daily.values()), default=Decimal(1))
    return _env.get_template("report.html.j2").render(r=report, max_day=max_day or Decimal(1))


def to_csv(costs: list[AllocatedCost], currency: str) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["day", "provider", "account", "service", "raw_service", "team", "env",
                     f"amount_{currency.lower()}", "original_cost", "original_currency"])
    for c in sorted(costs, key=lambda c: (c.record.day, c.record.provider, c.record.account)):
        r = c.record
        writer.writerow([r.day.isoformat(), r.provider, r.account, r.service, r.raw_service,
                         c.team, c.env, f"{c.amount:.4f}", f"{r.cost:.4f}", r.currency])
    return buf.getvalue()


def write_all(report: Report, costs: list[AllocatedCost], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "report.md": to_markdown(report),
        "report.html": to_html(report),
        "costs.csv": to_csv(costs, report.currency),
    }
    written = []
    for name, content in files.items():
        path = out_dir / name
        path.write_text(content)
        written.append(path)
    return written
