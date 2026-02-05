"""Weekly report writer for Sky-Lynx.

Generates markdown reports from analysis results.
"""

from datetime import datetime
from pathlib import Path

from .claude_client import AnalysisResult, Recommendation
from .insights_parser import TrendAnalysis


def get_reports_dir() -> Path:
    """Get the path to the reports directory.

    Returns:
        Path to ~/documentation/improvements/
    """
    reports_dir = Path.home() / "documentation" / "improvements"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def format_trend(value: float) -> str:
    """Format a percentage change with symbol.

    Args:
        value: Percentage change

    Returns:
        Formatted string like "+12%" or "-5%"
    """
    symbol = "+" if value >= 0 else ""
    return f"{symbol}{value:.0f}%"


def write_weekly_report(
    trend_analysis: TrendAnalysis,
    analysis_result: AnalysisResult,
    output_dir: Path | None = None,
) -> Path:
    """Write the weekly report to markdown file.

    Args:
        trend_analysis: TrendAnalysis from insights parser
        analysis_result: AnalysisResult from Claude
        output_dir: Optional override for output directory

    Returns:
        Path to the written report file
    """
    output_dir = output_dir or get_reports_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    current = trend_analysis.current

    # Build report content
    lines = [
        "# Sky-Lynx Weekly Report",
        "",
        f"**Generated**: {today}",
        f"**Period**: {current.period_start.strftime('%Y-%m-%d')} to {current.period_end.strftime('%Y-%m-%d')}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        analysis_result.executive_summary or "_No summary generated._",
        "",
        "---",
        "",
        "## Key Metrics",
        "",
        "| Metric | This Week | Trend |",
        "|--------|-----------|-------|",
    ]

    # Sessions row
    session_trend = (
        format_trend(trend_analysis.session_count_change)
        if trend_analysis.previous
        else "baseline"
    )
    lines.append(f"| Sessions | {current.total_sessions} | {session_trend} |")

    # Friction row
    total_friction = sum(current.friction_counts.values())
    friction_trend = (
        format_trend(trend_analysis.friction_change)
        if trend_analysis.previous
        else "baseline"
    )
    lines.append(f"| Friction Events | {total_friction} | {friction_trend} |")

    # Satisfaction row
    satisfied = current.satisfaction.get("likely_satisfied", 0)
    lines.append(
        f"| Satisfaction (likely_satisfied) | {satisfied} | {trend_analysis.satisfaction_trend} |"
    )

    lines.extend(
        [
            "",
            "### Outcomes Breakdown",
            "",
        ]
    )

    if current.outcomes:
        for outcome, count in current.outcomes.most_common():
            pct = (count / current.total_sessions * 100) if current.total_sessions > 0 else 0
            lines.append(f"- **{outcome}**: {count} ({pct:.0f}%)")
    else:
        lines.append("_No outcome data available._")

    lines.extend(
        [
            "",
            "### Friction Breakdown",
            "",
        ]
    )

    if current.friction_counts:
        for ftype, count in current.friction_counts.most_common():
            lines.append(f"- **{ftype}**: {count}")
    else:
        lines.append("_No friction recorded this week._")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Friction Analysis",
            "",
            analysis_result.friction_analysis or "_No friction analysis generated._",
            "",
        ]
    )

    # Add friction details if available
    if current.friction_details:
        lines.extend(
            [
                "### Friction Details",
                "",
            ]
        )
        for detail in current.friction_details:
            lines.append(f"- {detail}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Recommendations",
            "",
        ]
    )

    if analysis_result.recommendations:
        # Group by priority
        high_priority = [r for r in analysis_result.recommendations if r.priority == "high"]
        medium_priority = [r for r in analysis_result.recommendations if r.priority == "medium"]
        low_priority = [r for r in analysis_result.recommendations if r.priority == "low"]

        if high_priority:
            lines.append("### High Priority")
            lines.append("")
            for i, rec in enumerate(high_priority, 1):
                lines.extend(_format_recommendation(i, rec))

        if medium_priority:
            lines.append("### Medium Priority")
            lines.append("")
            for i, rec in enumerate(medium_priority, 1):
                lines.extend(_format_recommendation(i, rec))

        if low_priority:
            lines.append("### Low Priority")
            lines.append("")
            for i, rec in enumerate(low_priority, 1):
                lines.extend(_format_recommendation(i, rec))
    else:
        lines.append("_No specific recommendations generated._")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## What's Working Well",
            "",
            analysis_result.whats_working or "_No positive patterns identified._",
            "",
            "---",
            "",
            "*This report was generated by [Sky-Lynx](https://github.com/m2ai-portfolio/sky-lynx), "
            "a continuous improvement agent for Claude Code.*",
        ]
    )

    # Write to file
    report_path = output_dir / f"{today}-sky-lynx-report.md"
    report_path.write_text("\n".join(lines))

    return report_path


def _format_recommendation(index: int, rec: Recommendation) -> list[str]:
    """Format a single recommendation for markdown output.

    Args:
        index: Recommendation number
        rec: Recommendation object

    Returns:
        List of markdown lines
    """
    lines = [
        f"{index}. **{rec.title}**",
    ]

    if rec.evidence:
        lines.append(f"   - **Evidence**: {rec.evidence}")

    if rec.suggested_change:
        lines.append(f"   - **Suggested Change**: {rec.suggested_change}")

    if rec.impact:
        lines.append(f"   - **Impact**: {rec.impact}")

    lines.append(f"   - **Reversibility**: {rec.reversibility.title()}")
    lines.append("")

    return lines
