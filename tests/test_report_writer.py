"""Tests for report_writer module."""

import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest

from sky_lynx.claude_client import AnalysisResult, Recommendation
from sky_lynx.insights_parser import TrendAnalysis, WeeklyMetrics
from sky_lynx.report_writer import format_trend, write_weekly_report


@pytest.fixture
def sample_metrics() -> WeeklyMetrics:
    """Create sample weekly metrics."""
    return WeeklyMetrics(
        period_start=datetime(2026, 2, 1),
        period_end=datetime(2026, 2, 7),
        total_sessions=10,
        outcomes=Counter({"mostly_achieved": 7, "partially_achieved": 3}),
        satisfaction=Counter({"likely_satisfied": 8, "neutral": 2}),
        friction_counts=Counter({"buggy_code": 3, "context_overflow": 1}),
        friction_details=["Test failure", "Missing dependency"],
    )


@pytest.fixture
def sample_trend_analysis(sample_metrics: WeeklyMetrics) -> TrendAnalysis:
    """Create sample trend analysis."""
    return TrendAnalysis(
        current=sample_metrics,
        previous=None,
        session_count_change=0.0,
        friction_change=0.0,
        satisfaction_trend="baseline",
    )


@pytest.fixture
def sample_analysis_result() -> AnalysisResult:
    """Create sample analysis result."""
    return AnalysisResult(
        executive_summary="This week showed strong productivity with some friction.",
        friction_analysis="Buggy code was the main friction source.",
        recommendations=[
            Recommendation(
                title="Add pre-test checklist",
                priority="high",
                evidence="3 sessions with buggy code friction",
                suggested_change="Add testing guidelines to CLAUDE.md",
                impact="Reduce test failures",
                reversibility="high",
            ),
            Recommendation(
                title="Document common patterns",
                priority="medium",
                evidence="Recurring clarification requests",
                suggested_change="Add patterns section",
                impact="Reduce cognitive load",
                reversibility="high",
            ),
        ],
        whats_working="Iterative refinement sessions performed well.",
    )


class TestFormatTrend:
    """Tests for format_trend function."""

    def test_positive_trend(self):
        """Should format positive change with plus sign."""
        assert format_trend(12.5) == "+12%"

    def test_negative_trend(self):
        """Should format negative change with minus sign."""
        assert format_trend(-8.3) == "-8%"

    def test_zero_trend(self):
        """Should format zero as positive."""
        assert format_trend(0.0) == "+0%"


class TestWriteWeeklyReport:
    """Tests for write_weekly_report function."""

    def test_write_creates_file(
        self,
        sample_trend_analysis: TrendAnalysis,
        sample_analysis_result: AnalysisResult,
    ):
        """Should create a markdown file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            report_path = write_weekly_report(
                sample_trend_analysis, sample_analysis_result, output_dir
            )

            assert report_path.exists()
            assert report_path.suffix == ".md"
            assert "sky-lynx-report" in report_path.name

    def test_report_contains_sections(
        self,
        sample_trend_analysis: TrendAnalysis,
        sample_analysis_result: AnalysisResult,
    ):
        """Should include all required sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            report_path = write_weekly_report(
                sample_trend_analysis, sample_analysis_result, output_dir
            )

            content = report_path.read_text()

            assert "# Sky-Lynx Weekly Report" in content
            assert "## Executive Summary" in content
            assert "## Key Metrics" in content
            assert "## Friction Analysis" in content
            assert "## Recommendations" in content
            assert "## What's Working Well" in content

    def test_report_includes_metrics(
        self,
        sample_trend_analysis: TrendAnalysis,
        sample_analysis_result: AnalysisResult,
    ):
        """Should include session count and friction data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            report_path = write_weekly_report(
                sample_trend_analysis, sample_analysis_result, output_dir
            )

            content = report_path.read_text()

            assert "10" in content  # total sessions
            assert "buggy_code" in content
            assert "context_overflow" in content

    def test_report_includes_recommendations(
        self,
        sample_trend_analysis: TrendAnalysis,
        sample_analysis_result: AnalysisResult,
    ):
        """Should include recommendations with priorities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            report_path = write_weekly_report(
                sample_trend_analysis, sample_analysis_result, output_dir
            )

            content = report_path.read_text()

            assert "High Priority" in content
            assert "Medium Priority" in content
            assert "Add pre-test checklist" in content
            assert "Document common patterns" in content

    def test_report_handles_empty_recommendations(
        self,
        sample_trend_analysis: TrendAnalysis,
    ):
        """Should handle case with no recommendations."""
        empty_result = AnalysisResult(
            executive_summary="No issues this week.",
            friction_analysis="No friction recorded.",
            recommendations=[],
            whats_working="Everything worked well.",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            report_path = write_weekly_report(
                sample_trend_analysis, empty_result, output_dir
            )

            content = report_path.read_text()
            assert "No specific recommendations" in content
