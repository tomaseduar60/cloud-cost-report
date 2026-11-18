"""Mapeo de servicios de cada proveedor a una categoría común."""

from __future__ import annotations

AZURE = {
    "virtual machines": "compute",
    "azure kubernetes service": "kubernetes",
    "storage": "storage",
    "azure cosmos db": "database",
    "sql database": "database",
    "azure database for postgresql": "database",
    "bandwidth": "network",
    "virtual network": "network",
    "load balancer": "network",
    "azure app service": "serverless",
    "functions": "serverless",
    "azure monitor": "observability",
    "log analytics": "observability",
}

GCP = {
    "compute engine": "compute",
    "kubernetes engine": "kubernetes",
    "cloud storage": "storage",
    "cloud sql": "database",
    "bigquery": "analytics",
    "cloud run": "serverless",
    "cloud functions": "serverless",
    "networking": "network",
    "cloud logging": "observability",
    "cloud monitoring": "observability",
    "secret manager": "security",
}


def normalize(provider: str, raw: str) -> str:
    table = AZURE if provider == "azure" else GCP
    return table.get(raw.strip().lower(), "other")
