from datetime import date, datetime
from decimal import Decimal

from cost_report.providers.normalize import _to_date, azure_row, gcp_row
from cost_report.services import normalize


def test_azure_row() -> None:
    r = azure_row(
        {
            "Date": "20240131",
            "SubscriptionName": "sub-a",
            "MeterCategory": "Azure Kubernetes Service",
            "CostInBillingCurrency": "12.5",
            "BillingCurrency": "EUR",
            "Tags": '{"Team": "platform", "env": "prd"}',
        }
    )
    assert (r.provider, r.account, r.service, r.raw_service) == (
        "azure",
        "sub-a",
        "kubernetes",
        "Azure Kubernetes Service",
    )
    assert r.day == date(2024, 1, 31) and r.cost == Decimal("12.5") and r.currency == "EUR"
    assert r.team == "platform" and r.env == "prd"  # las keys de tags se normalizan


def test_azure_row_sin_tags() -> None:
    r = azure_row(
        {
            "Date": "2024-02-01",
            "SubscriptionName": "s",
            "MeterCategory": "Nuevo",
            "CostInBillingCurrency": 1,
            "BillingCurrency": "USD",
            "Tags": "",
        }
    )
    assert r.tags == {} and r.team is None and r.service == "other"


def test_gcp_row_descuenta_creditos() -> None:
    r = gcp_row(
        {
            "usage_start_time": "2024-03-05T00:00:00Z",
            "project": {"id": "p-1"},
            "service": {"description": "Kubernetes Engine"},
            "cost": 100,
            "currency": "USD",
            "credits": [{"amount": -10}, {"amount": "-2.5"}],
            "labels": [{"key": "team", "value": "commerce"}],
        }
    )
    assert r.cost == Decimal("87.5") and r.service == "kubernetes" and r.team == "commerce"
    assert r.day == date(2024, 3, 5)


def test_fechas_y_servicios() -> None:
    assert _to_date(datetime(2024, 1, 2, 10)) == date(2024, 1, 2)
    assert _to_date(date(2024, 1, 2)) == date(2024, 1, 2)
    assert normalize("gcp", "  BigQuery ") == "analytics"
    assert normalize("azure", "algo raro") == "other"
