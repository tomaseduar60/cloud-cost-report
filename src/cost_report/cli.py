"""cost-report: arma el reporte de un período comparándolo con el período anterior.

    cost-report build --source mock --from 2024-05-01 --to 2024-05-31
    cost-report build --source azure --source gcp --from 2024-05-01 --to 2024-05-31 --out out/
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import click

from . import __version__
from .allocation import allocate
from .config import ConfigError, load_config
from .model import AllocatedCost, CostRecord
from .providers import get_provider
from .report import build_report
from .report.render import to_markdown, write_all

SOURCES = {"mock": ["mock-azure", "mock-gcp"], "azure": ["azure"], "gcp": ["gcp"]}


def _fetch(sources: tuple[str, ...], start: date, end: date, mock_dir: Path) -> list[CostRecord]:
    records: list[CostRecord] = []
    for source in sources:
        for name in SOURCES[source]:
            records.extend(get_provider(name, mock_dir=mock_dir).fetch(start, end))
    return records


@click.group()
@click.version_option(__version__, prog_name="cost-report")
def cli() -> None:
    """Visibilidad de costos multi-cloud (Azure + GCP)."""


@cli.command()
@click.option("--source", "sources", multiple=True, type=click.Choice(sorted(SOURCES)),
              default=("mock",), show_default=True, help="Origen de datos (repetible).")
@click.option("--from", "start_dt", type=click.DateTime(["%Y-%m-%d"]), required=True)
@click.option("--to", "end_dt", type=click.DateTime(["%Y-%m-%d"]), required=True)
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path),
              default="config.yaml", show_default=True)
@click.option("--mock-dir", type=click.Path(path_type=Path), default="data/mock",
              show_default=True)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None,
              help="Directorio para report.md, report.html y costs.csv.")
@click.option("--fail-on-alert", is_flag=True,
              help="Sale con código 3 si algún equipo pasa el umbral de presupuesto.")
def build(sources: tuple[str, ...], start_dt: datetime, end_dt: datetime, config_path: Path,
          mock_dir: Path, out_dir: Path | None, fail_on_alert: bool) -> None:
    """Genera el reporte del período y lo compara con el período anterior de igual largo."""
    start, end = start_dt.date(), end_dt.date()
    if end < start:
        raise click.BadParameter("--to no puede ser anterior a --from.")
    config = load_config(config_path)

    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length - 1)

    current: list[AllocatedCost] = list(allocate(_fetch(sources, start, end, mock_dir), config))
    previous = list(allocate(_fetch(sources, prev_start, prev_end, mock_dir), config))
    report = build_report(current, config, start, end, previous=previous)

    if out_dir:
        for path in write_all(report, current, out_dir):
            click.echo(f"escrito {path}", err=True)
    else:
        click.echo(to_markdown(report))

    if fail_on_alert and report.alerts:
        sys.exit(3)


def main() -> None:
    try:
        cli(standalone_mode=False)
    except click.ClickException as exc:
        exc.show()
        sys.exit(exc.exit_code)
    except click.exceptions.Abort:
        sys.exit(1)
    except ConfigError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
