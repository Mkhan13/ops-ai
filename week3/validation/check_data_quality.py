"""
Data Quality Validation Framework Template

This file is a starting point for your validation code.
Modify or replace as needed based on the issues you identify.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class DataQualityValidator:
    """Validates data against quality expectations."""

    def __init__(self, baseline_df: pd.DataFrame = None):
        """
        Initialize validator.

        Args:
            baseline_df: Clean reference data for comparison
        """
        self.baseline = baseline_df
        self.issues = []

    def validate(self, df: pd.DataFrame) -> Dict:
        """
        Run all validation checks.

        Returns:
            Dictionary with:
            - is_valid: boolean
            - num_issues: count of issues found
            - issues: list of issue details
        """
        self.issues = []

        self.check_value_ranges(df)
        self.check_outliers(df)
        self.check_duplicates(df)

        return {
            "is_valid": len(self.issues) == 0,
            "num_issues": len(self.issues),
            "issues": self.issues,
        }

    def check_value_ranges(self, df: pd.DataFrame):
        """Check that trip_count is non-negative."""
        negatives = df[df["trip_count"] < 0]
        if len(negatives) > 0:
            self._add_issue(
                issue_type="negative_trip_count",
                severity="critical",
                description=(
                    f"{len(negatives)} rows have negative trip_count "
                    f"(min={df['trip_count'].min()}). "
                    "Negative demand is impossible and corrupts lag and rolling features."
                ),
                count=len(negatives),
            )

    def check_outliers(self, df: pd.DataFrame):
        """Check for extreme trip_count values beyond 10x the baseline maximum."""

        if self.baseline is not None:
            baseline_max = self.baseline["trip_count"].max()
        else:
            baseline_max = 310
        threshold = baseline_max * 10
        outliers = df[df["trip_count"] > threshold]
        if len(outliers) > 0:
            self._add_issue(
                issue_type="extreme_outliers",
                severity="high",
                description=(
                    f"{len(outliers)} rows have trip_count > {threshold:.0f} "
                    f"(baseline max={baseline_max:.0f}, corrupted max={df['trip_count'].max():.0f}). "
                    "Extreme values skew rolling means and model predictions."
                ),
                count=len(outliers),
            )

    def check_duplicates(self, df: pd.DataFrame):
        """Check for duplicate rows."""
        duplicates = int(df.duplicated().sum())
        if duplicates > 0:
            self._add_issue(
                issue_type="duplicate_rows",
                severity="high",
                description=(
                    f"{duplicates} duplicate rows found. "
                    "Duplicates over-weight certain time slots and inflate demand signals."
                ),
                count=duplicates,
            )

    def _add_issue(
        self,
        issue_type: str,
        severity: str,
        description: str,
        count: int = None,
        **details
    ):
        """Helper to add issue to list."""
        issue = {
            "type": issue_type,
            "severity": severity,  # 'critical', 'high', 'medium', 'low'
            "description": description,
            "count": count,
            **details,
        }
        self.issues.append(issue)


# Optional: Utility functions

def compare_distributions(
    baseline: pd.Series, current: pd.Series, threshold: float = 2.0
) -> bool:
    """
    Compare distributions using standard deviations.

    Returns True if distributions are significantly different.
    """
    # TODO: Implement comparison logic
    pass


def detect_outliers(
    series: pd.Series, baseline_series: pd.Series = None, sigma: float = 3.0
) -> pd.Series:
    """
    Detect outliers in a numeric series.

    Returns boolean Series indicating which values are outliers.
    """
    # TODO: Implement outlier detection
    pass
