"""Tests for insights_parser module."""

import json
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from sky_lynx.insights_parser import (
    SessionInsight,
    WeeklyMetrics,
    aggregate_weekly_metrics,
    analyze_trends,
    calculate_percentage_change,
    calculate_satisfaction_trend,
    load_sessions_for_period,
    parse_session_file,
)


@pytest.fixture
def sample_session_data() -> dict:
    """Sample session data matching Claude Code facets format."""
    return {
        "underlying_goal": "Implement new feature",
        "goal_categories": {"feature_implementation": 2, "debugging": 1},
        "outcome": "mostly_achieved",
        "user_satisfaction_counts": {"likely_satisfied": 2},
        "claude_helpfulness": "essential",
        "session_type": "iterative_refinement",
        "friction_counts": {"buggy_code": 1, "unclear_requirements": 1},
        "friction_detail": "Tests failed due to missing dependency",
        "primary_success": "multi_file_changes",
        "brief_summary": "User implemented auth feature with Claude's help.",
        "session_id": "test-session-123",
    }


@pytest.fixture
def temp_facets_dir(sample_session_data: dict) -> Path:
    """Create a temporary facets directory with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        facets_dir = Path(tmpdir)

        # Create a few session files
        for i in range(3):
            data = sample_session_data.copy()
            data["session_id"] = f"session-{i}"
            if i == 1:
                data["friction_counts"] = {"context_overflow": 1}
                data["outcome"] = "partially_achieved"

            file_path = facets_dir / f"session-{i}.json"
            with open(file_path, "w") as f:
                json.dump(data, f)

        yield facets_dir


class TestParseSessionFile:
    """Tests for parse_session_file function."""

    def test_parse_valid_file(self, sample_session_data: dict):
        """Should parse a valid JSON file correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_session_data, f)
            f.flush()

            result = parse_session_file(Path(f.name))

            assert result is not None
            assert result.session_id == "test-session-123"
            assert result.outcome == "mostly_achieved"
            assert result.friction_counts == {"buggy_code": 1, "unclear_requirements": 1}
            assert result.claude_helpfulness == "essential"

    def test_parse_missing_fields(self):
        """Should handle missing optional fields gracefully."""
        minimal_data = {"session_id": "minimal-123"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(minimal_data, f)
            f.flush()

            result = parse_session_file(Path(f.name))

            assert result is not None
            assert result.session_id == "minimal-123"
            assert result.outcome == ""
            assert result.friction_counts == {}

    def test_parse_invalid_json(self):
        """Should return None for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            f.flush()

            result = parse_session_file(Path(f.name))

            assert result is None

    def test_parse_nonexistent_file(self):
        """Should return None for nonexistent file."""
        result = parse_session_file(Path("/nonexistent/file.json"))
        assert result is None


class TestAggregateWeeklyMetrics:
    """Tests for aggregate_weekly_metrics function."""

    def test_aggregate_empty_sessions(self):
        """Should handle empty session list."""
        now = datetime.now()
        metrics = aggregate_weekly_metrics([], now, now)

        assert metrics.total_sessions == 0
        assert sum(metrics.friction_counts.values()) == 0

    def test_aggregate_multiple_sessions(self, sample_session_data: dict):
        """Should correctly aggregate multiple sessions."""
        sessions = [
            SessionInsight(**sample_session_data),
            SessionInsight(
                session_id="session-2",
                outcome="partially_achieved",
                friction_counts={"context_overflow": 2},
                user_satisfaction_counts={"likely_satisfied": 1},
            ),
        ]

        now = datetime.now()
        metrics = aggregate_weekly_metrics(sessions, now, now)

        assert metrics.total_sessions == 2
        assert metrics.outcomes["mostly_achieved"] == 1
        assert metrics.outcomes["partially_achieved"] == 1
        assert metrics.friction_counts["buggy_code"] == 1
        assert metrics.friction_counts["context_overflow"] == 2
        assert metrics.satisfaction["likely_satisfied"] == 3

    def test_aggregate_friction_details(self, sample_session_data: dict):
        """Should collect all friction details."""
        sessions = [
            SessionInsight(**sample_session_data),
            SessionInsight(
                session_id="session-2",
                friction_detail="Another issue occurred",
            ),
        ]

        now = datetime.now()
        metrics = aggregate_weekly_metrics(sessions, now, now)

        assert len(metrics.friction_details) == 2
        assert "missing dependency" in metrics.friction_details[0]


class TestCalculatePercentageChange:
    """Tests for calculate_percentage_change function."""

    def test_positive_change(self):
        """Should calculate positive percentage correctly."""
        result = calculate_percentage_change(120, 100)
        assert result == 20.0

    def test_negative_change(self):
        """Should calculate negative percentage correctly."""
        result = calculate_percentage_change(80, 100)
        assert result == -20.0

    def test_zero_previous(self):
        """Should handle zero previous value."""
        assert calculate_percentage_change(10, 0) == 100.0
        assert calculate_percentage_change(0, 0) == 0.0

    def test_no_change(self):
        """Should return 0 for no change."""
        result = calculate_percentage_change(100, 100)
        assert result == 0.0


class TestCalculateSatisfactionTrend:
    """Tests for calculate_satisfaction_trend function."""

    def test_improving_trend(self):
        """Should detect improving satisfaction."""
        current = Counter({"likely_satisfied": 10, "neutral": 2})
        previous = Counter({"likely_satisfied": 5, "neutral": 5, "likely_unsatisfied": 2})

        result = calculate_satisfaction_trend(current, previous)
        assert result == "improving"

    def test_declining_trend(self):
        """Should detect declining satisfaction."""
        current = Counter({"likely_unsatisfied": 5, "neutral": 5})
        previous = Counter({"likely_satisfied": 8, "neutral": 2})

        result = calculate_satisfaction_trend(current, previous)
        assert result == "declining"

    def test_stable_trend(self):
        """Should detect stable satisfaction."""
        current = Counter({"likely_satisfied": 5, "neutral": 5})
        previous = Counter({"likely_satisfied": 5, "neutral": 5})

        result = calculate_satisfaction_trend(current, previous)
        assert result == "stable"

    def test_baseline_no_previous(self):
        """Should return baseline when no previous data."""
        current = Counter({"likely_satisfied": 5})
        result = calculate_satisfaction_trend(current, None)
        assert result == "baseline"


class TestAnalyzeTrends:
    """Tests for analyze_trends function."""

    def test_analyze_with_previous(self):
        """Should calculate all trends with previous data."""
        now = datetime.now()
        prev_week = now - timedelta(days=7)

        current = WeeklyMetrics(
            period_start=now,
            period_end=now,
            total_sessions=20,
            friction_counts=Counter({"buggy_code": 5}),
            satisfaction=Counter({"likely_satisfied": 15}),
        )
        previous = WeeklyMetrics(
            period_start=prev_week,
            period_end=prev_week,
            total_sessions=15,
            friction_counts=Counter({"buggy_code": 10}),
            satisfaction=Counter({"likely_satisfied": 10}),
        )

        result = analyze_trends(current, previous)

        assert result.session_count_change > 0  # 20 vs 15
        assert result.friction_change < 0  # 5 vs 10 (improvement)

    def test_analyze_first_run(self):
        """Should handle first run with no previous data."""
        now = datetime.now()
        current = WeeklyMetrics(
            period_start=now,
            period_end=now,
            total_sessions=10,
        )

        result = analyze_trends(current, None)

        assert result.previous is None
        assert result.satisfaction_trend == "baseline"
        assert result.session_count_change == 0.0


class TestLoadSessionsForPeriod:
    """Tests for load_sessions_for_period function."""

    def test_load_from_directory(self, temp_facets_dir: Path):
        """Should load all sessions from directory within date range."""
        # Use a wide date range to capture all files
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=1)

        sessions = load_sessions_for_period(start, end, temp_facets_dir)

        assert len(sessions) == 3

    def test_load_empty_directory(self):
        """Should return empty list for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            start = datetime.now() - timedelta(days=1)
            end = datetime.now()

            sessions = load_sessions_for_period(start, end, Path(tmpdir))

            assert sessions == []

    def test_load_nonexistent_directory(self):
        """Should return empty list for nonexistent directory."""
        start = datetime.now() - timedelta(days=1)
        end = datetime.now()

        sessions = load_sessions_for_period(start, end, Path("/nonexistent"))

        assert sessions == []
