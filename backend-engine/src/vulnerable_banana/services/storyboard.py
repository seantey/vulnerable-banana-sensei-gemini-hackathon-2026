"""Storyboard generation using Gemini.

Generates a complete comic storyboard from a story card, including:
- Archetype and art style selection
- Visual anchors for consistency
- Page-by-page panel descriptions
"""

import structlog
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from vulnerable_banana.config import get_settings
from vulnerable_banana.models import StoryCard, Storyboard

logger = structlog.get_logger()

# System prompt for the storyboard agent
STORYBOARD_SYSTEM_PROMPT = """You are a comic book writer and visual storyteller.
You create compelling visual narratives that educate while entertaining.
You understand comic pacing, visual storytelling, and how to make
technical concepts accessible through imagery.

CRITICAL - PAGE 1 MUST ESTABLISH CONTEXT:
The first page is the TITLE PAGE. It MUST immediately tell the reader:
1. The PACKAGE NAME prominently displayed (e.g., "LODASH", "AXIOS")
2. A clear TITLE that hints at what happened
3. A SUBTITLE or tagline explaining it's a security vulnerability story
4. The DATE/YEAR of the incident if known
5. Visual elements that preview the story's theme

Example first page structure:
- Panel 1: Large title card with package name, dramatic title, and "A Security Story" subtitle
- Panel 2-3: Brief setup showing the "before" state or introducing the threat

IMPORTANT RULES:
1. Always create CONCRETE visual descriptions - not abstract concepts
2. Characters must be visually distinctive and consistent
3. Each panel should be a single clear scene
4. Keep captions short (under 15 words)
5. End with a clear educational takeaway
6. PAGE 1 FIRST PANEL must have the package name and title clearly visible as text

ARCHETYPE SELECTION:
- HEIST (4-6 pages): For targeted attacks with clear attacker intent
- OOPS (3-4 pages): For accidental chaos or unintended consequences
- SAGA (6-10 pages): For multi-wave incidents that evolved over time
- LURKER (3-5 pages): For long-hidden vulnerabilities

ART STYLE SELECTION:
- EPIC_SCIFI: Grand scale, cosmic, Moebius-inspired - use for large-scale attacks
- NOIR_THRILLER: Dark, corporate espionage vibes - use for targeted attacks
- RETRO_COMIC: Classic superhero comic style - use for dramatic discoveries
- MINIMAL_XKCD: Simple, witty, stick figures - use for absurd/ironic incidents
- CYBERPUNK: Neon, glitch, hacker aesthetic - use for crypto/DeFi exploits
- PROPAGANDA_POSTER: Bold, protest art style - use for intentional sabotage

VISUAL ANCHORS:
- color_palette: 3-5 specific colors with hex codes
- characters: ALL recurring characters with detailed descriptions
- key_entities: Visual descriptions of important concepts
- atmosphere: Overall mood
- line_style: Drawing style notes"""


def get_storyboard_agent() -> Agent[None, Storyboard]:
    """Create a storyboard agent with configured API key."""
    settings = get_settings()
    provider = GoogleProvider(api_key=settings.gemini_api_key)
    model = GoogleModel("gemini-3-pro-preview", provider=provider)

    return Agent(
        model,
        output_type=Storyboard,
        system_prompt=STORYBOARD_SYSTEM_PROMPT,
    )


async def generate_storyboard(story_card: StoryCard) -> Storyboard:
    """Generate a complete storyboard from a story card.

    Uses Gemini to create:
    - Archetype and art style selection
    - Visual anchors for character/style consistency
    - Page-by-page panel descriptions

    Args:
        story_card: The story card with educational content

    Returns:
        Storyboard with complete visual description
    """
    logger.info(
        "storyboard_generation_started",
        story_id=story_card.id,
        title=story_card.title,
    )

    agent = get_storyboard_agent()

    # Build the prompt with story card content
    prompt = f"""Create a comic storyboard for this security incident:

TITLE: {story_card.title}
PACKAGE: {story_card.package_name}@{story_card.package_version}
SEVERITY: {story_card.severity}
STORY TYPE: {story_card.story_type}

WHAT HAPPENED:
{chr(10).join(f"• {item}" for item in story_card.what_happened)}

WHY IT MATTERS:
{chr(10).join(f"• {item}" for item in story_card.why_should_i_care)}

WHAT TO DO:
{chr(10).join(f"• {item}" for item in story_card.what_should_i_do)}

{f"INCIDENT DATE: {story_card.incident_date}" if story_card.incident_date else ""}

---

CRITICAL REQUIREMENT - PAGE 1 MUST BE A CLEAR TITLE PAGE:
The FIRST PAGE, FIRST PANEL must prominently display:
- The package name "{story_card.package_name.upper()}" in large text
- A dramatic title for this story
- A subtitle like "A Security Vulnerability Story" or "What Went Wrong"
- The year/date if known: {story_card.incident_date or "Unknown"}

The reader should know EXACTLY what this comic is about within 2 seconds of seeing page 1.

---

Create a compelling comic that:
1. Starts with a CLEAR TITLE PAGE that establishes the subject
2. Tells this security story in an engaging visual way
3. Educates the reader about what happened
4. Ends with clear actionable advice

Select the best archetype based on the incident type:
- If it's an active attack/compromise → HEIST or SAGA
- If it's accidental/maintainer action → OOPS
- If it's a long-hidden vulnerability → LURKER

Select an art style that matches the incident tone.

Create detailed visual_anchors for consistency:
- Define 3-5 colors with hex codes
- Describe ALL characters who will appear
- List key visual elements/metaphors
- Set the atmosphere and line style

Then create the page-by-page storyboard:

PAGE 1 (TITLE PAGE):
- Panel 1: MUST be a title card with "{story_card.package_name.upper()}" prominently displayed, story title, and "A Security Story" subtitle
- Remaining panels: Brief setup or preview of the threat

SUBSEQUENT PAGES:
- 2-4 panels per page (prefer fewer, larger panels)
- Clear scene descriptions
- Dialogue and/or captions as needed
- Appropriate layout

Make it educational but engaging. The reader should understand the security issue and remember it."""

    try:
        result = await agent.run(prompt)
        storyboard = result.output

        total_panels = sum(len(page.panels) for page in storyboard.pages)

        logger.info(
            "storyboard_generated",
            story_id=story_card.id,
            title=storyboard.title,
            archetype=storyboard.archetype,
            art_style=storyboard.art_style,
            pages=len(storyboard.pages),
            total_panels=total_panels,
        )

        return storyboard

    except Exception as e:
        logger.error(
            "storyboard_generation_failed",
            story_id=story_card.id,
            error=str(e),
        )
        raise
