import csv
import io
from pathlib import Path

from click.testing import CliRunner

from cost_report.cli import cli
from cost_report.report.render import pct


def _args(root: Path, *rest: str) -> list[str]:
    return [
        "build",
        "--config",
        str(root / "config.yaml"),
        "--mock-dir",
        str(root / "data" / "mock"),
        *rest,
    ]


def test_build_markdown_con_mock(root: Path) -> None:
    out = CliRunner().invoke(cli, _args(root, "--from", "2024-05-01", "--to", "2024-05-31"))
    assert out.exit_code == 0, out.output
    assert "# Costos cloud 2024-05-01 → 2024-05-31" in out.output
    assert "azure" in out.output and "gcp" in out.output
    assert "sin-asignar" in out.output
    assert "Mayores variaciones" in out.output


def test_build_archivos(root: Path, tmp_path: Path) -> None:
    out = CliRunner().invoke(
        cli, _args(root, "--from", "2024-05-01", "--to", "2024-05-07", "--out", str(tmp_path))
    )
    assert out.exit_code == 0, out.output
    html = (tmp_path / "report.html").read_text()
    assert "<!doctype html>" in html and 'class="bar"' in html
    rows = list(csv.DictReader(io.StringIO((tmp_path / "costs.csv").read_text())))
    assert {r["provider"] for r in rows} == {"azure", "gcp"}
    assert {r["day"] for r in rows} >= {"2024-05-01", "2024-05-07"}


def test_fail_on_alert(root: Path) -> None:
    args = _args(root, "--from", "2024-05-01", "--to", "2024-05-31", "--fail-on-alert")
    assert CliRunner().invoke(cli, args).exit_code == 3


def test_fechas_invertidas(root: Path) -> None:
    out = CliRunner().invoke(cli, _args(root, "--from", "2024-05-10", "--to", "2024-05-01"))
    assert out.exit_code != 0 and "anterior" in out.output


def test_pct() -> None:
    assert pct(None) == "nuevo"
