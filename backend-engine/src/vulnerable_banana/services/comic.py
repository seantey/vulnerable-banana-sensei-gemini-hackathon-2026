"""Comic image generation using Gemini.

Uses chat mode for visual consistency across all pages.
The first message establishes the visual style, and subsequent
messages maintain that style throughout the comic.
"""

import hashlib
from datetime import datetime, timezone

import structlog
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from vulnerable_banana.config import get_settings
from vulnerable_banana.models import (
    ComicPage,
    GeneratedComic,
    GeneratedPage,
    Storyboard,
)
from vulnerable_banana.storage import get_storage_backend

logger = structlog.get_logger()

# Retry configuration for transient API errors
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=2, min=4, max=30),
    "retry": retry_if_exception_type((genai.errors.ServerError,)),
    "reraise": True,
}

# Art style base prompts for image generation
ART_STYLE_PROMPTS = {
    "EPIC_SCIFI": (
        "in the style of Moebius/Jean Giraud, epic science fiction illustration, "
        "sweeping vistas, dramatic lighting, cosmic scale, detailed linework"
    ),
    "NOIR_THRILLER": (
        "film noir comic style, high contrast black and white with selective color accents, "
        "dramatic shadows, 1940s detective aesthetic, moody atmosphere"
    ),
    "RETRO_COMIC": (
        "classic 1960s Marvel/DC comic book style, bold outlines, Ben-Day dots, "
        "dynamic poses, bright primary colors, action-packed"
    ),
    "MINIMAL_XKCD": (
        "simple clean line art, minimalist style, stick figures with expressive poses, "
        "clean white background, subtle visual humor"
    ),
    "CYBERPUNK": (
        "cyberpunk aesthetic, neon colors on dark backgrounds, glitch effects, "
        "rain-soaked streets, holographic displays, high-tech low-life atmosphere"
    ),
    "PROPAGANDA_POSTER": (
        "Soviet/WPA propaganda poster style, bold geometric shapes, "
        "limited color palette (3-4 colors), stylized heroic figures, strong typography"
    ),
}


def generate_comic_hash(title: str) -> str:
    """Generate a unique hash for the comic."""
    data = f"{title}:{datetime.now(timezone.utc).isoformat()}"
    return f"com_{hashlib.sha256(data.encode()).hexdigest()[:12]}"


def build_initial_prompt(storyboard: Storyboard) -> str:
    """Build the opening prompt that establishes visual style.

    This first message sets up the entire visual language for the comic.
    """
    base_style = ART_STYLE_PROMPTS[storyboard.art_style]
    anchors = storyboard.visual_anchors

    # Format character descriptions
    characters_text = "\n".join(
        f"- {c.name}: {c.appearance}"
        + (f" (props: {', '.join(c.recurring_props)})" if c.recurring_props else "")
        for c in anchors.characters
    )

    # Format first page panels
    page = storyboard.pages[0]
    panels_text = "\n\n".join(
        f"Panel {p.panel_number}: {p.scene_description}"
        + (f'\nCaption: "{p.caption}"' if p.caption else "")
        + (f'\nDialogue: "{p.dialogue}"' if p.dialogue else "")
        for p in page.panels
    )

    return f"""You are creating a {len(storyboard.pages)}-page comic called "{storyboard.title}".

STYLE: {base_style}
{storyboard.style_modifiers}

COLOR PALETTE: {', '.join(anchors.color_palette)}

CHARACTERS (maintain these designs throughout):
{characters_text}

KEY VISUAL ELEMENTS: {', '.join(anchors.key_entities)}

ATMOSPHERE: {anchors.atmosphere}
LINE STYLE: {anchors.line_style}

---

Generate PAGE 1 of {len(storyboard.pages)} - THIS IS THE TITLE PAGE.

CRITICAL: This first page must clearly establish what the comic is about.
The title "{storyboard.title}" MUST be prominently displayed as large, readable text.
Include a subtitle like "A Security Vulnerability Story" to give context.

Layout: {page.layout}

{panels_text}

Requirements:
- Single comic page image with {len(page.panels)} panels
- Clear panel borders
- LARGE, PROMINENT TITLE TEXT that is easy to read
- Professional comic lettering for all text
- 16:9 aspect ratio
- The reader must immediately understand this is a security story about the topic
- Establish the visual style that will continue throughout all pages"""


def build_continuation_prompt(storyboard: Storyboard, page: ComicPage) -> str:
    """Build prompt for pages 2+ that maintains consistency."""
    panels_text = "\n\n".join(
        f"Panel {p.panel_number}: {p.scene_description}"
        + (f'\nCaption: "{p.caption}"' if p.caption else "")
        + (f'\nDialogue: "{p.dialogue}"' if p.dialogue else "")
        for p in page.panels
    )

    return f"""Generate PAGE {page.page_number} of {len(storyboard.pages)}.
Layout: {page.layout}

CRITICAL: Maintain EXACT visual consistency with previous pages:
- Same character designs (faces, clothing, proportions)
- Same color palette and saturation
- Same line weight and art style
- Same atmosphere and lighting direction

{panels_text}

Requirements:
- Single comic page image with {len(page.panels)} panels
- Clear panel borders
- Professional comic lettering for all text
- 16:9 aspect ratio"""


async def extract_and_upload_page(
    response: types.GenerateContentResponse,
    page_number: int,
    comic_hash: str,
) -> GeneratedPage:
    """Extract image from response and upload to storage."""
    settings = get_settings()
    storage = get_storage_backend(settings)

    # Find the image in the response
    image_bytes = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        raise RuntimeError(f"No image generated for page {page_number}")

    # Generate filename and upload
    page_hash = hashlib.sha256(image_bytes).hexdigest()[:12]
    filename = f"pages/{comic_hash}_p{page_number:02d}_{page_hash}.png"

    image_url = await storage.upload(filename, image_bytes, "image/png")

    logger.debug(
        "page_uploaded",
        page_number=page_number,
        filename=filename,
        size_bytes=len(image_bytes),
    )

    return GeneratedPage(page_number=page_number, image_url=image_url)


@retry(**RETRY_CONFIG)
def _send_message_with_retry(chat, prompt: str, page_number: int):
    """Send message to chat with retry for transient errors."""
    logger.debug("sending_page_prompt", page=page_number)
    return chat.send_message(prompt)


async def generate_comic(storyboard: Storyboard) -> GeneratedComic:
    """Generate all comic pages sequentially in a chat session for consistency.

    Uses Gemini's chat mode to maintain visual consistency across pages.
    The first message establishes the style, and subsequent messages
    reference "previous pages" to maintain the look.

    Args:
        storyboard: Complete storyboard with visual descriptions

    Returns:
        GeneratedComic with all page images
    """
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)

    comic_hash = generate_comic_hash(storyboard.title)

    logger.info(
        "comic_generation_started",
        comic_hash=comic_hash,
        title=storyboard.title,
        pages=len(storyboard.pages),
    )

    # Image generation config
    image_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )

    # Create chat session for this comic
    chat = client.chats.create(
        model="gemini-3-pro-image-preview",
        config=image_config,
    )

    generated_pages: list[GeneratedPage] = []

    # Generate page 1 (establishes visual style)
    initial_prompt = build_initial_prompt(storyboard)

    try:
        response = _send_message_with_retry(chat, initial_prompt, page_number=1)
        page_1 = await extract_and_upload_page(response, page_number=1, comic_hash=comic_hash)
        generated_pages.append(page_1)

        logger.info("page_generated", page=1, total=len(storyboard.pages))

    except Exception as e:
        logger.error("page_generation_failed", page=1, error=str(e))
        raise

    # Generate remaining pages in the same chat session
    for page in storyboard.pages[1:]:
        try:
            prompt = build_continuation_prompt(storyboard, page)
            response = _send_message_with_retry(chat, prompt, page_number=page.page_number)
            generated_page = await extract_and_upload_page(
                response, page_number=page.page_number, comic_hash=comic_hash
            )
            generated_pages.append(generated_page)

            logger.info("page_generated", page=page.page_number, total=len(storyboard.pages))

        except Exception as e:
            logger.error("page_generation_failed", page=page.page_number, error=str(e))
            raise

    # Calculate totals
    total_panels = sum(len(page.panels) for page in storyboard.pages)

    comic = GeneratedComic(
        comic_hash=comic_hash,
        title=storyboard.title,
        archetype=storyboard.archetype,
        art_style=storyboard.art_style,
        page_count=len(storyboard.pages),
        total_panels=total_panels,
        pages=generated_pages,
        share_url=f"{settings.frontend_url}/c/{comic_hash}",
        generated_at=datetime.now(timezone.utc),
    )

    logger.info(
        "comic_complete",
        comic_hash=comic_hash,
        title=storyboard.title,
        pages=len(generated_pages),
        total_panels=total_panels,
    )

    return comic
