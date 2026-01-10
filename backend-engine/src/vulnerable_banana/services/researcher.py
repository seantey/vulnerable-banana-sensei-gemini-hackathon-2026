"""Security incident research using Gemini.

Two-tier research approach:
- Quick research (scan): Uses Gemini without Search Grounding for fast story cards
- Deep research (report): Uses Gemini WITH Search Grounding for thorough reports
"""

import asyncio
import hashlib

import structlog
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from vulnerable_banana.config import get_settings
from vulnerable_banana.models import HistoricalIncident, Package, StoryCard, StoryCardContent, StoryType, Vulnerability

logger = structlog.get_logger()

# Well-known packages with famous security incidents
# These are packages where Gemini is likely to have good knowledge
NOTABLE_PACKAGES = {
    "left-pad",  # The famous npm incident (2016)
    "event-stream",  # Cryptocurrency wallet attack (2018)
    "ua-parser-js",  # Cryptominer injection (2021)
    "colors",  # Intentional sabotage by author (2022)
    "faker",  # Intentional sabotage by author (2022)
    "node-ipc",  # Protestware (2022)
    "peacenotwar",  # Protestware (2022)
    "log4j",  # Log4Shell (2021)
    "lodash",  # Prototype pollution issues
    "moment",  # Deprecated, multiple ReDos issues
    "minimist",  # Prototype pollution
    "axios",  # SSRF vulnerabilities
    "express",  # Various security issues over time
    "jquery",  # XSS vulnerabilities
    "bootstrap",  # XSS vulnerabilities
    "angular",  # Security issues
    "react",  # Past issues
    "vue",  # Past issues
    "webpack",  # Path traversal issues
    "npm",  # Various security incidents
    "yarn",  # Various security incidents
}

# System prompt for the story card agent
STORY_CARD_SYSTEM_PROMPT = """You are a security educator who explains vulnerabilities in clear, accessible language.
Your goal is to help developers understand security issues without unnecessary jargon.
Be factual and educational, not alarmist.

When generating story card content:
- Create catchy, memorable titles (like "The Lodash Saga" not just "CVE-2021-23337")
- Explain what happened in simple terms developers can understand
- Focus on why this matters to someone using the affected package
- Provide actionable remediation steps they can take immediately
- If you know the approximate date of the incident, include it"""


def get_story_card_agent() -> Agent[None, StoryCardContent]:
    """Create a story card agent with configured API key."""
    settings = get_settings()
    provider = GoogleProvider(api_key=settings.gemini_api_key)
    model = GoogleModel("gemini-3-pro-preview", provider=provider)

    return Agent(
        model,
        output_type=StoryCardContent,
        system_prompt=STORY_CARD_SYSTEM_PROMPT,
    )


def generate_story_id(vuln: Vulnerability) -> str:
    """Generate a unique story ID from vulnerability data."""
    data = f"{vuln.vuln_id}:{vuln.package_name}:{vuln.package_version}"
    return f"story_{hashlib.sha256(data.encode()).hexdigest()[:12]}"


async def quick_research_single(
    agent: Agent[None, StoryCardContent],
    vuln: Vulnerability,
) -> StoryCardContent | None:
    """Generate story card content for a single vulnerability.

    Uses Gemini without Search Grounding - relies on model's training knowledge.
    This is fast (~2-5 seconds) and suitable for the initial scan.

    Args:
        agent: The configured story card agent
        vuln: Vulnerability to research

    Returns:
        StoryCardContent with educational content, or None if generation fails
    """
    prompt = f"""Generate educational content for this security vulnerability:

Package: {vuln.package_name}
Version: {vuln.package_version}
Vulnerability ID: {vuln.vuln_id}
Severity: {vuln.severity}
Summary: {vuln.summary}
{f"Details: {vuln.details[:1000]}..." if vuln.details and len(vuln.details) > 1000 else f"Details: {vuln.details}" if vuln.details else ""}

Generate:
1. A catchy, memorable title for this incident
2. 3-5 bullet points explaining what happened
3. 2-3 bullet points explaining why developers should care
4. 2-3 actionable remediation steps
5. The approximate incident date if known (format: "YYYY-MM" or null)"""

    try:
        result = await agent.run(prompt)
        return result.output

    except Exception as e:
        logger.warning(
            "quick_research_failed",
            vuln_id=vuln.vuln_id,
            package=vuln.package_name,
            error=str(e),
        )
        return None


def create_story_card(
    vuln: Vulnerability,
    content: StoryCardContent,
    story_type: StoryType = "ACTIVE",
) -> StoryCard:
    """Create a StoryCard from vulnerability and research content."""
    return StoryCard(
        id=generate_story_id(vuln),
        title=content.title,
        package_name=vuln.package_name,
        package_version=vuln.package_version,
        story_type=story_type,
        severity=vuln.severity,
        what_happened=content.what_happened,
        why_should_i_care=content.why_should_i_care,
        what_should_i_do=content.what_should_i_do,
        incident_date=content.incident_date,
        sources=vuln.references[:3],  # Include top 3 references
    )


def create_fallback_story_card(vuln: Vulnerability) -> StoryCard:
    """Create a minimal story card when LLM research fails.

    Uses the vulnerability data directly without LLM enhancement.
    """
    return StoryCard(
        id=generate_story_id(vuln),
        title=f"Security Issue in {vuln.package_name}",
        package_name=vuln.package_name,
        package_version=vuln.package_version,
        story_type="ACTIVE",
        severity=vuln.severity,
        what_happened=[vuln.summary],
        why_should_i_care=[f"Your version ({vuln.package_version}) is affected"],
        what_should_i_do=[f"Update {vuln.package_name} to a patched version"],
        incident_date=None,
        sources=vuln.references[:3],
    )


def dedupe_vulnerabilities(vulns: list[Vulnerability]) -> list[Vulnerability]:
    """Deduplicate vulnerabilities by package, keeping highest severity.

    Multiple CVEs for the same package are common. We want one story per package.
    """
    severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}

    best_by_package: dict[str, Vulnerability] = {}
    for vuln in vulns:
        key = vuln.package_name
        if key not in best_by_package:
            best_by_package[key] = vuln
        else:
            current = best_by_package[key]
            if severity_rank.get(vuln.severity, 0) > severity_rank.get(current.severity, 0):
                best_by_package[key] = vuln

    return list(best_by_package.values())


async def generate_story_cards(
    vulnerabilities: list[Vulnerability],
    max_stories: int = 3,
) -> list[StoryCard]:
    """Generate story cards for vulnerabilities using quick research.

    Deduplicates by package and limits to top N stories by severity.

    Args:
        vulnerabilities: List of vulnerabilities from OSV scan
        max_stories: Maximum number of story cards to generate

    Returns:
        List of StoryCard objects with educational content
    """
    if not vulnerabilities:
        logger.info("no_vulnerabilities_for_stories")
        return []

    # Dedupe to one vuln per package
    unique_vulns = dedupe_vulnerabilities(vulnerabilities)

    # Sort by severity (highest first) and take top N
    severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    sorted_vulns = sorted(
        unique_vulns,
        key=lambda v: severity_rank.get(v.severity, 0),
        reverse=True,
    )
    top_vulns = sorted_vulns[:max_stories]

    logger.info(
        "quick_research_started",
        total_vulns=len(vulnerabilities),
        unique_packages=len(unique_vulns),
        generating=len(top_vulns),
    )

    # Create the agent once and reuse for all research
    agent = get_story_card_agent()

    # Generate story cards concurrently
    tasks = [quick_research_single(agent, vuln) for vuln in top_vulns]
    results = await asyncio.gather(*tasks)

    # Build story cards, using fallback for failed research
    story_cards: list[StoryCard] = []
    for vuln, content in zip(top_vulns, results, strict=True):
        if content:
            story_cards.append(create_story_card(vuln, content))
        else:
            story_cards.append(create_fallback_story_card(vuln))

    logger.info(
        "quick_research_complete",
        stories_generated=len(story_cards),
        with_llm_content=sum(1 for c in results if c is not None),
    )

    return story_cards


# --- Historical Incident Research ---

HISTORICAL_SYSTEM_PROMPT = """You are a security historian who knows about famous npm/JavaScript package security incidents.
Your knowledge includes well-known incidents like:
- left-pad unpublishing (2016) - broke the internet
- event-stream attack (2018) - cryptocurrency wallet theft
- ua-parser-js hijacking (2021) - cryptominer injection
- colors/faker sabotage (2022) - author intentionally broke packages
- node-ipc protestware (2022) - geopolitical protest in code
- Log4Shell (2021) - one of the most severe vulnerabilities ever

When asked about a package, recall if there have been ANY notable security incidents, supply chain attacks,
maintainer drama, or interesting security stories. These don't have to be active vulnerabilities -
historical incidents that are now fixed are interesting too!

Be accurate. If you don't know of any notable incidents for a package, say so clearly.
Only report incidents you're confident actually happened."""


def get_historical_agent() -> Agent[None, HistoricalIncident]:
    """Create an agent for researching historical incidents."""
    settings = get_settings()
    provider = GoogleProvider(api_key=settings.gemini_api_key)
    model = GoogleModel("gemini-3-pro-preview", provider=provider)

    return Agent(
        model,
        output_type=HistoricalIncident,
        system_prompt=HISTORICAL_SYSTEM_PROMPT,
    )


async def research_historical_incident(
    agent: Agent[None, HistoricalIncident],
    package: Package,
) -> HistoricalIncident | None:
    """Research if a package has any notable historical security incidents.

    Args:
        agent: The configured historical incident agent
        package: Package to research

    Returns:
        HistoricalIncident with incident details, or None if research fails
    """
    prompt = f"""Research this npm package for historical security incidents:

Package: {package.name}
Version in user's project: {package.version}

Questions to answer:
1. Has this package ever had a notable security incident, supply chain attack, or maintainer drama?
2. If yes, what happened? When? What was the impact?
3. What can developers learn from this incident?

If there's NO notable incident for this package, set has_incident to false.
If there IS a notable incident, provide:
- A catchy title (like "The Left-Pad Incident" or "The Event-Stream Attack")
- 3-5 bullet points explaining what happened
- 2-3 bullet points on why developers should care
- 2-3 lessons learned / best practices
- The approximate date (YYYY-MM format)
- Set severity based on impact: CRITICAL (widespread damage), HIGH (significant), MEDIUM (moderate), LOW (minor), INFO (educational)"""

    try:
        result = await agent.run(prompt)
        return result.output

    except Exception as e:
        logger.warning(
            "historical_research_failed",
            package=package.name,
            error=str(e),
        )
        return None


def generate_historical_story_id(package_name: str) -> str:
    """Generate a unique story ID for a historical incident."""
    data = f"historical:{package_name}"
    return f"story_{hashlib.sha256(data.encode()).hexdigest()[:12]}"


def create_historical_story_card(
    package: Package,
    incident: HistoricalIncident,
) -> StoryCard:
    """Create a StoryCard from a historical incident."""
    # Map severity string to proper type
    severity_map = {
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
        "INFO": "INFO",
    }
    severity = severity_map.get(incident.severity or "INFO", "INFO")

    return StoryCard(
        id=generate_historical_story_id(package.name),
        title=incident.title or f"The {package.name} Story",
        package_name=package.name,
        package_version=package.version,
        story_type="HISTORICAL_YOURS",
        severity=severity,  # type: ignore
        what_happened=incident.what_happened,
        why_should_i_care=incident.why_should_i_care,
        what_should_i_do=incident.what_should_i_do,
        incident_date=incident.incident_date,
        sources=incident.sources[:3],
    )


async def generate_historical_story_cards(
    clean_packages: list[Package],
    max_stories: int = 2,
) -> list[StoryCard]:
    """Generate story cards for historical incidents in clean packages.

    Checks packages against known notable packages and researches their history.

    Args:
        clean_packages: Packages without current vulnerabilities
        max_stories: Maximum number of historical stories to generate

    Returns:
        List of StoryCard objects for historical incidents
    """
    if not clean_packages:
        return []

    # Filter to packages that might have interesting history
    # Prioritize well-known packages with famous incidents
    notable = [p for p in clean_packages if p.name.lower() in NOTABLE_PACKAGES]
    other = [p for p in clean_packages if p.name.lower() not in NOTABLE_PACKAGES]

    # Take notable packages first, then fill with others
    candidates = notable + other
    candidates = candidates[:max_stories + 2]  # Research a few extra in case some have no incidents

    if not candidates:
        return []

    logger.info(
        "historical_research_started",
        candidates=len(candidates),
        notable=[p.name for p in notable],
    )

    agent = get_historical_agent()

    # Research packages concurrently
    tasks = [research_historical_incident(agent, pkg) for pkg in candidates]
    results = await asyncio.gather(*tasks)

    # Build story cards for packages with incidents
    story_cards: list[StoryCard] = []
    for package, incident in zip(candidates, results, strict=True):
        if incident and incident.has_incident and incident.title:
            story_cards.append(create_historical_story_card(package, incident))
            if len(story_cards) >= max_stories:
                break

    logger.info(
        "historical_research_complete",
        researched=len(candidates),
        with_incidents=len(story_cards),
    )

    return story_cards
