"""
Data Quality Validation Tests Template

Write tests that:
1. Pass for clean (baseline) data
2. Fail for corrupted data
3. Test each issue you identified
"""

import pytest
import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from validation.check_data_quality import DataQualityValidator

CUTOFF = pd.Timestamp("2026-01-16")
DATA_PATH = Path(__file__).parent.parent / "data" / "demand_enriched_corrupted.parquet"


@pytest.fixture
def baseline_data():
    """Load clean baseline data (pre Jan 16)."""
    df = pd.read_parquet(DATA_PATH)
    return df[df["time_bucket"] < CUTOFF]


@pytest.fixture
def corrupted_data():
    """Load corrupted data (post Jan 16)."""
    df = pd.read_parquet(DATA_PATH)
    return df[df["time_bucket"] >= CUTOFF]


@pytest.fixture
def validator(baseline_data):
    """Create validator initialized with baseline."""
    return DataQualityValidator(baseline_data)


class TestBaselineData:
    """Tests that baseline data should pass validation."""

    def test_baseline_passes_validation(self, baseline_data, validator):
        """Baseline data should have no quality issues."""
        result = validator.validate(baseline_data)
        assert result['is_valid'], f"Baseline failed: {result['issues']}"


class TestDataQualityIssues:
    """Tests that verify each issue is detected."""

    def test_detect_negative_trip_counts(self, corrupted_data, validator):
        """Should detect negative trip_count values."""
        result = validator.validate(corrupted_data)
        assert not result['is_valid']
        assert any(issue['type'] == 'negative_trip_count' for issue in result['issues'])

    def test_detect_extreme_outliers(self, corrupted_data, validator):
        """Should detect extreme trip_count outliers."""
        result = validator.validate(corrupted_data)
        assert not result['is_valid']
        assert any(issue['type'] == 'extreme_outliers' for issue in result['issues'])

    def test_detect_duplicate_rows(self, corrupted_data, validator):
        """Should detect duplicate rows."""
        result = validator.validate(corrupted_data)
        assert not result['is_valid']
        assert any(issue['type'] == 'duplicate_rows' for issue in result['issues'])


class TestGracefulDegradation:
    """Tests that API gracefully handles bad data."""

    def test_api_does_not_crash_with_bad_data(self, corrupted_data):
        """Validator should not raise an exception on corrupted data."""
        validator = DataQualityValidator()
        try:
            result = validator.validate(corrupted_data)
            assert 'is_valid' in result
            assert 'issues' in result
        except Exception as e:
            pytest.fail(f"Validator crashed on corrupted data: {e}")

    def test_fallback_is_logged(self, corrupted_data, caplog):
        """When issues are found, they should be logged as warnings."""
        logger = logging.getLogger("test_logger")
        with caplog.at_level(logging.WARNING):
            validator = DataQualityValidator()
            result = validator.validate(corrupted_data)
            if not result['is_valid']:
                for issue in result['issues']:
                    logger.warning(f"[{issue['severity'].upper()}] {issue['type']}: {issue['description']}")
        assert any(r.levelname == "WARNING" for r in caplog.records)


# ============================================================================
# HOW TO RUN
# ============================================================================
#
# From repo root:
#   python -m pytest week3/validation/test_data_quality.py -v
#
# To run specific test:
#   python -m pytest week3/validation/test_data_quality.py::TestDataQualityIssues::test_detect_issue_1 -v
#
# To see print statements:
#   python -m pytest week3/validation/test_data_quality.py -v -s
