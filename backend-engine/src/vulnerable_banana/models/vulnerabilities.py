"""Vulnerability models."""

from typing import Literal

from pydantic import Field

from vulnerable_banana.models.base import ApiModel

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


class Vulnerability(ApiModel):
    """A vulnerability from OSV.

    Maps OSV vulnerability data to our internal model.
    """

    vuln_id: str  # e.g., "CVE-2025-12345" or "GHSA-xxxx"
    package_name: str
    package_version: str  # The version that was queried
    affected_versions: str  # e.g., "<4.17.22"
    severity: Severity
    summary: str
    details: str | None = None
    references: list[str] = Field(default_factory=list)


class ScanResult(ApiModel):
    """Result of scanning packages against OSV."""

    package_count: int
    vulnerabilities: list[Vulnerability]
    clean_count: int  # Packages without vulnerabilities
