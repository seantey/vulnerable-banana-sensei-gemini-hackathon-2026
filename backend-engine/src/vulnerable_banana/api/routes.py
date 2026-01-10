"""API route handlers."""

import structlog
from fastapi import APIRouter, HTTPException, UploadFile

from vulnerable_banana.models import ComicMetadata, GeneratedComic, StoryCard
from vulnerable_banana.models.base import ApiModel
from vulnerable_banana.models.vulnerabilities import Vulnerability
from vulnerable_banana.services import (
    generate_comic,
    generate_historical_story_cards,
    generate_story_cards,
    generate_storyboard,
    parse_dependency_file,
    scan_packages,
)

router = APIRouter(prefix="/api")
logger = structlog.get_logger()

# In-memory storage for comic metadata (would use database in production)
_comic_store: dict[str, GeneratedComic] = {}


class HealthResponse(ApiModel):
    """Health check response."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns basic health status and version for monitoring.
    """
    from vulnerable_banana.config import get_settings

    settings = get_settings()
    return HealthResponse(status="healthy", version=settings.app_version)


# --- Scan Response Models ---


class ScanResponse(ApiModel):
    """Response from scanning a dependency file.

    Returns vulnerability scan results with story cards for education.
    """

    filename: str
    package_count: int
    story_cards: list[StoryCard]
    vulnerabilities: list[Vulnerability]
    clean_count: int


@router.post("/scan", response_model=ScanResponse)
async def scan_file(file: UploadFile) -> ScanResponse:
    """Upload and scan a dependency file for vulnerabilities.

    Parses the uploaded file, queries OSV for vulnerabilities,
    generates story cards with educational content, and returns results.
    Also researches historical incidents for packages without current vulnerabilities.

    Args:
        file: The dependency file (package.json, requirements.txt, pyproject.toml)

    Returns:
        ScanResponse with story cards, vulnerabilities, and clean count
    """
    filename = file.filename or "unknown"
    content = await file.read()

    logger.info("scan_started", filename=filename, size_bytes=len(content))

    # Parse the dependency file
    parsed = parse_dependency_file(content, filename)

    logger.info(
        "packages_parsed",
        filename=filename,
        count=len(parsed.packages),
        ecosystem=parsed.ecosystem,
        errors=len(parsed.parse_errors),
    )

    # Scan packages against OSV for vulnerabilities
    scan_result = await scan_packages(parsed.packages)

    logger.info(
        "osv_scan_complete",
        filename=filename,
        packages=scan_result.package_count,
        vulnerabilities=len(scan_result.vulnerabilities),
        clean=scan_result.clean_count,
    )

    # Generate story cards with educational content for current vulnerabilities
    story_cards = await generate_story_cards(scan_result.vulnerabilities)

    # Find clean packages (no current vulnerabilities)
    vulnerable_package_names = {v.package_name.lower() for v in scan_result.vulnerabilities}
    clean_packages = [
        pkg for pkg in parsed.packages
        if pkg.name.lower() not in vulnerable_package_names
    ]

    # Research historical incidents for clean packages
    historical_stories = await generate_historical_story_cards(clean_packages, max_stories=2)

    # Combine current and historical stories
    all_story_cards = story_cards + historical_stories

    logger.info(
        "scan_complete",
        filename=filename,
        packages=scan_result.package_count,
        vulnerabilities=len(scan_result.vulnerabilities),
        active_stories=len(story_cards),
        historical_stories=len(historical_stories),
        total_stories=len(all_story_cards),
        clean=scan_result.clean_count,
    )

    return ScanResponse(
        filename=parsed.filename,
        package_count=scan_result.package_count,
        story_cards=all_story_cards,
        vulnerabilities=scan_result.vulnerabilities,
        clean_count=scan_result.clean_count,
    )


# --- Comic Generation ---


class GenerateComicRequest(ApiModel):
    """Request to generate a comic from a story card."""

    story_card: StoryCard


@router.post("/generate-comic", response_model=GeneratedComic)
async def create_comic(request: GenerateComicRequest) -> GeneratedComic:
    """Generate a comic from a story card.

    Creates a storyboard and generates all comic pages sequentially.
    This is a long-running operation (~30-90 seconds).

    Args:
        request: Contains the story card to generate a comic for

    Returns:
        GeneratedComic with all page images and share URL
    """
    story_card = request.story_card

    logger.info(
        "comic_request_received",
        story_id=story_card.id,
        title=story_card.title,
    )

    # Generate storyboard from story card
    storyboard = await generate_storyboard(story_card)

    # Generate comic images
    comic = await generate_comic(storyboard)

    # Store comic metadata for retrieval
    _comic_store[comic.comic_hash] = comic

    logger.info(
        "comic_created",
        comic_hash=comic.comic_hash,
        title=comic.title,
        pages=comic.page_count,
    )

    return comic


@router.get("/comic/{comic_hash}", response_model=ComicMetadata)
async def get_comic(comic_hash: str) -> ComicMetadata:
    """Get comic metadata for OG tags and share pages.

    Args:
        comic_hash: The comic's unique hash

    Returns:
        ComicMetadata with title, description, and thumbnail

    Raises:
        HTTPException: If comic not found
    """
    comic = _comic_store.get(comic_hash)

    if not comic:
        logger.warning("comic_not_found", comic_hash=comic_hash)
        raise HTTPException(status_code=404, detail="Comic not found")

    # Build description from comic metadata
    description = f"A {comic.archetype.lower()} security comic about {comic.title}"

    return ComicMetadata(
        comic_hash=comic.comic_hash,
        title=comic.title,
        description=description,
        page_count=comic.page_count,
        pages=comic.pages,
        thumbnail_url=comic.pages[0].image_url if comic.pages else "",
        generated_at=comic.generated_at,
    )
