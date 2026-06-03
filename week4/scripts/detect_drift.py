"""
Drift detection skeleton.

Write code to detect 4+ distinct drift patterns between baseline and new data.
Use statistical tests (KS, PSI, chi-square) to quantify drift.
"""

import pandas as pd
import numpy as np
from scipy.stats import ks_2samp


def detect_feature_drift(baseline_df: pd.DataFrame, new_df: pd.DataFrame, feature: str) -> dict:
    """
    Detect drift in a single feature.

    Use KS test to compare baseline vs new distribution.
    Return dict with test results and interpretation.
    """
    baseline_values = baseline_df[feature].dropna().values
    new_values = new_df[feature].dropna().values

    ks_statistic, p_value = ks_2samp(baseline_values, new_values)

    baseline_mean = float(np.mean(baseline_values))
    new_mean = float(np.mean(new_values))

    if baseline_mean != 0:
        mean_shift_pct = ((new_mean - baseline_mean) / baseline_mean) * 100
    else:
        mean_shift_pct = 0.0

    if p_value < 0.01:
        interpretation = 'significant drift'
    elif p_value < 0.05:
        interpretation = 'moderate drift'
    else:
        interpretation = 'no significant drift'

    return {
        'feature': feature,
        'ks_statistic': float(ks_statistic),
        'p_value': float(p_value),
        'drift_detected': p_value < 0.05,
        'baseline_mean': baseline_mean,
        'new_mean': new_mean,
        'mean_shift_pct': float(mean_shift_pct),
        'interpretation': interpretation
    }


def detect_concept_drift_by_segment(baseline_df: pd.DataFrame, new_df: pd.DataFrame) -> dict:
    """
    Detect concept drift (accuracy degradation by segment).

    Compare mean/accuracy by zone/hour between baseline and new data.
    Find segments where performance dropped.
    Return dict with findings.
    """
    baseline_by_zone = baseline_df.groupby('PULocationID')['trip_count'].mean()
    new_by_zone = new_df.groupby('PULocationID')['trip_count'].mean()

    zone_shifts = {}
    for zone in baseline_by_zone.index:
        if zone in new_by_zone.index:
            baseline_zone_mean = float(baseline_by_zone[zone])
            new_zone_mean = float(new_by_zone[zone])
            if baseline_zone_mean > 0:
                shift_pct = ((new_zone_mean - baseline_zone_mean) / baseline_zone_mean) * 100
            else:
                shift_pct = 0.0
            zone_shifts[int(zone)] = {
                'baseline_mean': baseline_zone_mean,
                'new_mean': new_zone_mean,
                'shift_pct': float(shift_pct)
            }

    baseline_by_hour = baseline_df.groupby('hour')['trip_count'].mean()
    new_by_hour = new_df.groupby('hour')['trip_count'].mean()

    hour_shifts = {}
    for hour in baseline_by_hour.index:
        if hour in new_by_hour.index:
            baseline_hour_mean = float(baseline_by_hour[hour])
            new_hour_mean = float(new_by_hour[hour])
            if baseline_hour_mean > 0:
                shift_pct = ((new_hour_mean - baseline_hour_mean) / baseline_hour_mean) * 100
            else:
                shift_pct = 0.0
            hour_shifts[int(hour)] = {
                'baseline_mean': baseline_hour_mean,
                'new_mean': new_hour_mean,
                'shift_pct': float(shift_pct)
            }

    sorted_zones = sorted(zone_shifts.items(), key=lambda zone_item: abs(zone_item[1]['shift_pct']), reverse=True)
    sorted_hours = sorted(hour_shifts.items(), key=lambda hour_item: abs(hour_item[1]['shift_pct']), reverse=True)

    return {
        'zone_shifts': zone_shifts,
        'hour_shifts': hour_shifts,
        'top_shifted_zones': sorted_zones[:5],
        'top_shifted_hours': sorted_hours[:5]
    }


def main():
    """Main drift detection analysis."""
    print("=" * 70)
    print("DRIFT DETECTION")
    print("=" * 70)

    # Load baseline and new data
    baseline_df = pd.read_parquet("data/demand_enriched_baseline.parquet")
    new_df = pd.read_parquet("data/demand_enriched_week4.parquet")

    # Run feature-level drift detection
    features_to_check = ['trip_count', 'hour', 'dayofweek', 'lag_1h']
    feature_results = {}
    for feature in features_to_check:
        result = detect_feature_drift(baseline_df, new_df, feature)
        feature_results[feature] = result
        print(f"\nPattern: {feature} drift")
        print("-" * 40)
        print(f"KS statistic: {result['ks_statistic']:.4f}")
        print(f"p-value: {result['p_value']:.6f}")
        print(f"Mean shift: {result['mean_shift_pct']:+.1f}%")
        print(f"Result: {result['interpretation']}")

    # Run concept drift detection
    print("\nConcept Drift By Segment")
    print("-" * 40)
    segment_results = detect_concept_drift_by_segment(baseline_df, new_df)

    print("\nTop 5 most shifted zones:")
    for zone, info in segment_results['top_shifted_zones']:
        print(f"Zone {zone}: baseline={info['baseline_mean']:.2f}, new={info['new_mean']:.2f}, shift={info['shift_pct']:+.1f}%")

    print("\nTop 5 most shifted hours:")
    for hour, info in segment_results['top_shifted_hours']:
        print(f"Hour {hour}: baseline={info['baseline_mean']:.2f}, new={info['new_mean']:.2f}, shift={info['shift_pct']:+.1f}%")

    # Summarize findings
    print("\nSummary")
    print("-" * 40)
    drift_count = 0
    for feature, result in feature_results.items():
        if result['drift_detected']:
            drift_count += 1
            print(f"Drift Detected: {feature} (p={result['p_value']:.6f}, shift={result['mean_shift_pct']:+.1f}%)")
    print(f"{drift_count} of {len(features_to_check)} features show significant drift.")


if __name__ == "__main__":
    main()

