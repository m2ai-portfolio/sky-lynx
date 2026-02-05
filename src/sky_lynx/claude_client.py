"""Anthropic API client for Sky-Lynx analysis.

Wraps the Anthropic SDK with the Sky-Lynx persona system prompt.
"""

import os
from pathlib import Path

import yaml
from anthropic import Anthropic
from pydantic import BaseModel, Field

# Default model for analysis
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class Recommendation(BaseModel):
    """A single improvement recommendation."""

    title: str
    priority: str  # high, medium, low
    evidence: str
    suggested_change: str
    impact: str
    reversibility: str  # high, medium, low


class AnalysisResult(BaseModel):
    """Structured result from Claude analysis."""

    executive_summary: str
    friction_analysis: str
    recommendations: list[Recommendation] = Field(default_factory=list)
    whats_working: str
    raw_response: str = ""


def load_persona_prompt() -> str:
    """Load the Sky-Lynx persona and convert to system prompt.

    Returns:
        System prompt string for Claude API
    """
    persona_path = (
        Path.home()
        / "projects"
        / "agent-persona-academy"
        / "personas"
        / "sky-lynx"
        / "persona.yaml"
    )

    if not persona_path.exists():
        # Fallback to embedded prompt if persona file not found
        return _get_fallback_prompt()

    with open(persona_path) as f:
        persona = yaml.safe_load(f)

    # Build system prompt from persona
    identity = persona.get("identity", {})
    voice = persona.get("voice", {})
    frameworks = persona.get("frameworks", {})
    analysis = persona.get("analysis_patterns", {})

    prompt_parts = [
        f"You are {identity.get('name', 'Sky-Lynx')}, {identity.get('role', 'a continuous improvement analyst')}.",
        "",
        identity.get("background", ""),
        "",
        "## Voice and Style",
        "",
    ]

    # Add tone
    for tone in voice.get("tone", []):
        prompt_parts.append(f"- {tone}")

    prompt_parts.extend(["", "## Characteristic Phrases", ""])
    for phrase in voice.get("phrases", []):
        prompt_parts.append(f'- "{phrase}"')

    prompt_parts.extend(["", "## Communication Style", ""])
    for style in voice.get("style", []):
        prompt_parts.append(f"- {style}")

    prompt_parts.extend(["", "## Constraints (What you must NOT do)", ""])
    for constraint in voice.get("constraints", []):
        prompt_parts.append(f"- {constraint}")

    # Add frameworks
    prompt_parts.extend(["", "## Analytical Frameworks", ""])
    for name, framework in frameworks.items():
        prompt_parts.append(f"### {name.replace('_', ' ').title()}")
        prompt_parts.append(framework.get("description", ""))
        prompt_parts.append("")

    # Add output structure
    prompt_parts.extend(["", "## Output Structure", ""])
    for section in analysis.get("output_structure", []):
        prompt_parts.append(f"- **{section.get('section')}**: {section.get('purpose', '')}")

    prompt_parts.extend(["", analysis.get("synthesis_guidance", "")])

    return "\n".join(prompt_parts)


def _get_fallback_prompt() -> str:
    """Fallback system prompt if persona file not found."""
    return """You are Sky-Lynx, a continuous improvement analyst.

You analyze Claude Code usage insights and recommend CLAUDE.md improvements.

Key principles:
- Use data and evidence to support recommendations
- Propose small, incremental, reversible changes
- Use hedged language ("consider", "might", "suggest")
- Prioritize by impact, effort, and reversibility
- Focus on eliminating friction and waste

Output structure:
1. Executive Summary - High-level assessment
2. Friction Analysis - Breakdown of issues
3. Recommendations - Prioritized list with evidence
4. What's Working Well - Positive patterns to reinforce
"""


def build_analysis_prompt(metrics_summary: str, friction_details: list[str]) -> str:
    """Build the user prompt for analysis.

    Args:
        metrics_summary: Formatted string of weekly metrics
        friction_details: List of friction detail strings

    Returns:
        User prompt for Claude
    """
    prompt_parts = [
        "Please analyze this week's Claude Code usage data and provide improvement recommendations for CLAUDE.md.",
        "",
        "## Weekly Metrics",
        metrics_summary,
        "",
        "## Friction Details",
    ]

    if friction_details:
        for detail in friction_details:
            prompt_parts.append(f"- {detail}")
    else:
        prompt_parts.append("No friction details recorded this week.")

    prompt_parts.extend(
        [
            "",
            "## Your Task",
            "",
            "1. Analyze the friction patterns and identify root causes",
            "2. Distinguish between recurring patterns and one-time anomalies",
            "3. Generate prioritized recommendations for CLAUDE.md improvements",
            "4. Note what's working well that should be reinforced",
            "",
            "Format your response with clear sections for:",
            "- Executive Summary (2-3 sentences)",
            "- Friction Analysis",
            "- Recommendations (with priority: high/medium/low, evidence, suggested change, and reversibility)",
            "- What's Working Well",
        ]
    )

    return "\n".join(prompt_parts)


def parse_recommendations(response_text: str) -> list[Recommendation]:
    """Parse recommendations from Claude's response.

    This is a best-effort extraction - Claude's response format may vary.

    Args:
        response_text: Raw response from Claude

    Returns:
        List of parsed Recommendation objects
    """
    recommendations = []

    # Look for recommendation sections
    lines = response_text.split("\n")
    current_rec = None
    in_recommendations = False

    for line in lines:
        lower_line = line.lower()

        # Detect start of recommendations section
        if "recommendation" in lower_line and (
            line.startswith("#") or line.startswith("**")
        ):
            in_recommendations = True
            continue

        # Detect end of recommendations section
        if in_recommendations and "working well" in lower_line:
            in_recommendations = False
            if current_rec:
                recommendations.append(current_rec)
                current_rec = None
            continue

        if not in_recommendations:
            continue

        # Parse recommendation items
        # Look for numbered items or bold titles
        if (
            line.strip().startswith(("1.", "2.", "3.", "4.", "5."))
            or line.strip().startswith("**")
        ) and ("consider" in lower_line or "add" in lower_line or "update" in lower_line):
            # Save previous recommendation
            if current_rec and current_rec.title:
                recommendations.append(current_rec)

            # Start new recommendation
            title = line.strip().lstrip("0123456789.").strip()
            title = title.strip("*").strip()
            current_rec = Recommendation(
                title=title,
                priority="medium",
                evidence="",
                suggested_change="",
                impact="",
                reversibility="high",
            )

        elif current_rec:
            # Parse attributes
            if "priority" in lower_line or "high" in lower_line and "impact" not in lower_line:
                if "high" in lower_line:
                    current_rec.priority = "high"
                elif "low" in lower_line:
                    current_rec.priority = "low"

            if "evidence" in lower_line or "session" in lower_line:
                current_rec.evidence = line.strip().lstrip("-*").strip()

            if "suggest" in lower_line or "change" in lower_line:
                current_rec.suggested_change = line.strip().lstrip("-*").strip()

            if "reversib" in lower_line:
                if "high" in lower_line:
                    current_rec.reversibility = "high"
                elif "low" in lower_line:
                    current_rec.reversibility = "low"
                else:
                    current_rec.reversibility = "medium"

    # Don't forget the last one
    if current_rec and current_rec.title:
        recommendations.append(current_rec)

    return recommendations


def analyze_insights(
    metrics_summary: str,
    friction_details: list[str],
    dry_run: bool = False,
    api_key: str | None = None,
) -> AnalysisResult:
    """Run Claude analysis on the insights data.

    Args:
        metrics_summary: Formatted metrics summary
        friction_details: List of friction details
        dry_run: If True, skip API call and return mock result
        api_key: Optional API key override

    Returns:
        AnalysisResult with recommendations
    """
    if dry_run:
        return AnalysisResult(
            executive_summary="[DRY RUN] No API call made.",
            friction_analysis="[DRY RUN] Would analyze friction patterns here.",
            recommendations=[
                Recommendation(
                    title="[DRY RUN] Example recommendation",
                    priority="medium",
                    evidence="Example evidence",
                    suggested_change="Example change",
                    impact="Example impact",
                    reversibility="high",
                )
            ],
            whats_working="[DRY RUN] Would identify positive patterns here.",
            raw_response="[DRY RUN]",
        )

    # Get API key
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found in environment. "
            "Set it in .env or ~/.env.shared"
        )

    client = Anthropic(api_key=key)
    system_prompt = load_persona_prompt()
    user_prompt = build_analysis_prompt(metrics_summary, friction_details)

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract text from response
    content_block = response.content[0]
    raw_response = content_block.text if hasattr(content_block, "text") else str(content_block)

    # Parse sections from response
    sections = _parse_response_sections(raw_response)
    recommendations = parse_recommendations(raw_response)

    return AnalysisResult(
        executive_summary=sections.get("executive_summary", ""),
        friction_analysis=sections.get("friction_analysis", ""),
        recommendations=recommendations,
        whats_working=sections.get("whats_working", ""),
        raw_response=raw_response,
    )


def _parse_response_sections(response: str) -> dict[str, str]:
    """Parse named sections from Claude's response.

    Args:
        response: Raw response text

    Returns:
        Dict mapping section names to content
    """
    sections = {
        "executive_summary": "",
        "friction_analysis": "",
        "whats_working": "",
    }

    current_section: str | None = None
    current_content: list[str] = []

    for line in response.split("\n"):
        lower_line = line.lower()

        # Detect section headers
        if "executive" in lower_line and "summary" in lower_line:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "executive_summary"
            current_content = []
        elif "friction" in lower_line and "analysis" in lower_line:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "friction_analysis"
            current_content = []
        elif "working well" in lower_line:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "whats_working"
            current_content = []
        elif "recommendation" in lower_line and line.startswith("#"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = None
            current_content = []
        elif current_section:
            # Skip section headers
            if not line.startswith("#"):
                current_content.append(line)

    # Save last section
    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections
