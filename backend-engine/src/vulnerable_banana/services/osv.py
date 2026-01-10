"""OSV vulnerability database integration."""

import asyncio
from typing import Any

import httpx
import structlog

from vulnerable_banana.models import Package
from vulnerable_banana.models.vulnerabilities import Severity, ScanResult, Vulnerability

logger = structlog.get_logger()

OSV_API_URL = "https://api.osv.dev/v1/query"
OSV_TIMEOUT = 30.0  # seconds


def map_cvss_to_severity(score: float | None) -> Severity:
    """Map CVSS score to our Severity enum.

    Score ranges from 05-data-models.md:
    - CRITICAL: 9.0-10.0
    - HIGH: 7.0-8.9
    - MEDIUM: 4.0-6.9
    - LOW: 0.1-3.9
    - INFO: N/A (no score)
    """
    if score is None:
        return "INFO"
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    if score >= 0.1:
        return "LOW"
    return "INFO"


def map_osv_severity_string(severity_str: str | None) -> Severity:
    """Map OSV severity string to our Severity enum.

    OSV uses strings like "CRITICAL", "HIGH", "MODERATE", "LOW".
    """
    if not severity_str:
        return "INFO"
    severity_upper = severity_str.upper()
    if severity_upper == "CRITICAL":
        return "CRITICAL"
    if severity_upper == "HIGH":
        return "HIGH"
    if severity_upper in ("MODERATE", "MEDIUM"):
        return "MEDIUM"
    if severity_upper == "LOW":
        return "LOW"
    return "INFO"


def extract_severity(vuln_data: dict[str, Any]) -> Severity:
    """Extract severity from OSV vulnerability data.

    OSV can have severity in different formats:
    - severity[].score (numeric CVSS score)
    - severity[].score (CVSS vector string like "CVSS:3.1/AV:N/...")
    - database_specific.severity (string like "MODERATE", "HIGH")
    """
    # First, try to get a numeric CVSS score
    severity_list = vuln_data.get("severity", [])
    for sev in severity_list:
        score = sev.get("score")
        if isinstance(score, (int, float)):
            return map_cvss_to_severity(float(score))

    # Fall back to database_specific.severity (common in GitHub advisories)
    db_specific = vuln_data.get("database_specific", {})
    severity_str = db_specific.get("severity")
    if severity_str:
        return map_osv_severity_string(severity_str)

    return "INFO"


def extract_affected_versions(vuln_data: dict[str, Any], package_name: str) -> str:
    """Extract affected version range from OSV vulnerability data."""
    affected_list = vuln_data.get("affected", [])

    for affected in affected_list:
        pkg = affected.get("package", {})
        if pkg.get("name", "").lower() == package_name.lower():
            # Check for version ranges
            ranges = affected.get("ranges", [])
            for r in ranges:
                events = r.get("events", [])
                introduced = None
                fixed = None
                for event in events:
                    if "introduced" in event:
                        introduced = event["introduced"]
                    if "fixed" in event:
                        fixed = event["fixed"]

                if fixed:
                    if introduced and introduced != "0":
                        return f">={introduced}, <{fixed}"
                    return f"<{fixed}"
                elif introduced:
                    return f">={introduced}"

            # Check for explicit versions list
            versions = affected.get("versions", [])
            if versions:
                if len(versions) <= 3:
                    return ", ".join(versions)
                return f"{versions[0]} and {len(versions) - 1} more"

    return "unknown"


def parse_vulnerability(
    vuln_data: dict[str, Any], package: Package
) -> Vulnerability:
    """Parse OSV vulnerability response into our Vulnerability model."""
    vuln_id = vuln_data.get("id", "UNKNOWN")
    summary = vuln_data.get("summary", "No summary available")
    details = vuln_data.get("details")

    # Extract references
    references: list[str] = []
    for ref in vuln_data.get("references", []):
        url = ref.get("url")
        if url:
            references.append(url)

    # Get severity from CVSS or database_specific
    severity = extract_severity(vuln_data)

    # Get affected versions
    affected_versions = extract_affected_versions(vuln_data, package.name)

    return Vulnerability(
        vuln_id=vuln_id,
        package_name=package.name,
        package_version=package.version,
        affected_versions=affected_versions,
        severity=severity,
        summary=summary,
        details=details,
        references=references[:5],  # Limit to 5 references
    )


async def query_osv(package: Package) -> list[Vulnerability]:
    """Query OSV for vulnerabilities affecting a package.

    Args:
        package: Package to check

    Returns:
        List of Vulnerability objects found for this package
    """
    # Map ecosystem to OSV format
    ecosystem_map = {
        "npm": "npm",
        "pypi": "PyPI",
    }
    osv_ecosystem = ecosystem_map.get(package.ecosystem, package.ecosystem)

    payload = {
        "package": {
            "name": package.name,
            "ecosystem": osv_ecosystem,
        },
        "version": package.version,
    }

    async with httpx.AsyncClient(timeout=OSV_TIMEOUT) as client:
        try:
            response = await client.post(OSV_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            logger.warning("osv_timeout", package=package.name, version=package.version)
            return []
        except httpx.HTTPStatusError as e:
            logger.warning(
                "osv_http_error",
                package=package.name,
                status=e.response.status_code,
            )
            return []
        except Exception as e:
            logger.warning("osv_error", package=package.name, error=str(e))
            return []

    vulns = data.get("vulns", [])
    if not vulns:
        return []

    return [parse_vulnerability(v, package) for v in vulns]


async def scan_packages(packages: list[Package]) -> ScanResult:
    """Scan multiple packages against OSV for vulnerabilities.

    Queries all packages concurrently for efficiency.

    Args:
        packages: List of packages to scan

    Returns:
        ScanResult with vulnerabilities and clean count
    """
    logger.info("osv_scan_started", package_count=len(packages))

    # Query all packages concurrently
    tasks = [query_osv(pkg) for pkg in packages]
    results = await asyncio.gather(*tasks)

    # Flatten results and track packages with vulnerabilities
    all_vulnerabilities: list[Vulnerability] = []
    vulnerable_packages: set[str] = set()

    for pkg, vulns in zip(packages, results, strict=True):
        if vulns:
            all_vulnerabilities.extend(vulns)
            vulnerable_packages.add(f"{pkg.name}@{pkg.version}")

    clean_count = len(packages) - len(vulnerable_packages)

    logger.info(
        "osv_scan_complete",
        total_packages=len(packages),
        vulnerable_packages=len(vulnerable_packages),
        total_vulnerabilities=len(all_vulnerabilities),
        clean_packages=clean_count,
    )

    return ScanResult(
        package_count=len(packages),
        vulnerabilities=all_vulnerabilities,
        clean_count=clean_count,
    )
