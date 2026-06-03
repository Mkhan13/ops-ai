"""
Monitoring metrics skeleton.

Implement these metrics based on your 8+ metric design from Part 1.
Each metric should compute a specific health signal about your data/model.
"""

import pandas as pd
import numpy as np
from scipy.stats import ks_2samp


class MetricComputer:
    """Compute monitoring metrics for drift detection."""

    def __init__(self, baseline_df: pd.DataFrame):
        """Initialize with baseline data."""
        self.baseline_df = baseline_df

    def metric_1_accuracy(self, new_df: pd.DataFrame, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """
        Metric 1: Overall Accuracy
        
        Return fraction of correct predictions.
        """
        if predictions is None or actuals is None:
            return None
        return float(np.mean(predictions == actuals))

    def metric_2_accuracy_by_zone(self, new_df: pd.DataFrame, predictions: np.ndarray, actuals: np.ndarray) -> dict:
        """
        Metric 2: Accuracy by Zone

        Return dict mapping zone_id -> accuracy.
        """
        if predictions is None or actuals is None:
            return {}
        temp_df = new_df.copy()
        temp_df['correct'] = (predictions == actuals)
        accuracy_by_zone = {}
        for zone, group in temp_df.groupby('PULocationID'):
            accuracy_by_zone[int(zone)] = float(group['correct'].mean())
        return accuracy_by_zone

    def metric_3_null_rates(self, new_df: pd.DataFrame) -> dict:
        """
        Metric 3: Null Rates for Critical Fields

        Return dict of field -> null_rate for critical columns.
        """
        critical_cols = ['PULocationID', 'trip_count', 'lag_15min', 'lag_1h', 'roll_mean_1h', 'is_holiday']
        null_rates = {}
        for col in critical_cols:
            if col in new_df.columns:
                null_rates[col] = float(new_df[col].isna().mean())
        return null_rates

    def metric_4_ks_test(self, new_df: pd.DataFrame) -> dict:
        """
        Metric 4: KS Test for Distribution Shift

        Use scipy.stats.ks_2samp to compare trip_count distribution.
        Return dict with statistic and p-value.
        """
        stat, pvalue = ks_2samp(
            self.baseline_df['trip_count'].dropna(),
            new_df['trip_count'].dropna()
        )
        return {
            'statistic': float(stat),
            'p_value': float(pvalue),
            'drift_detected': pvalue < 0.05
        }

    def metric_5_psi(self, new_df: pd.DataFrame, bins: int = 10) -> float:
        """
        Metric 5: Population Stability Index

        PSI calculation. Compare baseline vs new distribution.
        Return single float value.
        """
        baseline_vals = self.baseline_df['trip_count'].dropna().values
        new_vals = new_df['trip_count'].dropna().values

        bin_edges = np.histogram_bin_edges(baseline_vals, bins=bins)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        baseline_counts = np.histogram(baseline_vals, bins=bin_edges)[0]
        new_counts = np.histogram(new_vals, bins=bin_edges)[0]

        baseline_pct = baseline_counts / len(baseline_vals)
        new_pct = new_counts / len(new_vals)

        baseline_pct = np.where(baseline_pct == 0, 1e-6, baseline_pct)
        new_pct = np.where(new_pct == 0, 1e-6, new_pct)

        psi = np.sum((new_pct - baseline_pct) * np.log(new_pct / baseline_pct))
        return float(psi)

    def metric_6_prediction_distribution(self, predictions: np.ndarray) -> dict:
        """
        Metric 6: Prediction Distribution Shift

        Check if model is collapsed (std very small).
        Return dict with mean, std, collapsed flag.
        """
        if predictions is None:
            return {}
        mean = float(np.mean(predictions))
        std = float(np.std(predictions))
        return {
            'mean': mean,
            'std': std,
            'collapsed': std < 0.1
        }

    def metric_7_data_freshness(self, new_df: pd.DataFrame) -> dict:
        """
        Metric 7: Data Freshness

        Check age of most recent record.
        Return dict with age in minutes, hours.
        """
        time_col = None
        for col in ['tpep_pickup_datetime', 'pickup_datetime', 'datetime', 'timestamp']:
            if col in new_df.columns:
                time_col = col
                break

        if time_col is None:
            return {'age_minutes': None, 'age_hours': None, 'stale': None}

        most_recent = pd.to_datetime(new_df[time_col]).max()
        age = pd.Timestamp.now() - most_recent
        age_minutes = age.total_seconds() / 60
        return {
            'age_minutes': float(age_minutes),
            'age_hours': float(age_minutes / 60),
            'stale': age_minutes > 60
        }

    def metric_8_duplicate_rate(self, new_df: pd.DataFrame) -> dict:
        """
        Metric 8: Duplicate Rate

        Check fraction of rows that are exact duplicates.
        Return dict with rate and count.
        """
        total = len(new_df)
        duplicate_count = int(new_df.duplicated().sum())
        if total > 0:
            rate = duplicate_count / total
        else:
            rate = 0.0
        return {
            'rate': float(rate),
            'count': duplicate_count,
            'alert': rate > 0.005
        }

    def compute_all_metrics(self, new_df: pd.DataFrame, predictions: np.ndarray = None, actuals: np.ndarray = None) -> dict:
        """
        Compute all metrics.
        Call each metric method and return results dict.
        """
        results = {
            'null_rates': self.metric_3_null_rates(new_df),
            'ks_test': self.metric_4_ks_test(new_df),
            'psi': self.metric_5_psi(new_df),
            'prediction_distribution': self.metric_6_prediction_distribution(predictions),
            'data_freshness': self.metric_7_data_freshness(new_df),
            'duplicate_rate': self.metric_8_duplicate_rate(new_df),
        }
        # Populate results
        if predictions is not None and actuals is not None:
            results['accuracy'] = self.metric_1_accuracy(new_df, predictions, actuals)
            results['accuracy_by_zone'] = self.metric_2_accuracy_by_zone(new_df, predictions, actuals)
        return results
 