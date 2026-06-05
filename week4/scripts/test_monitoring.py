import numpy as np
import pandas as pd
from metric_template import MetricComputer
from detect_drift import detect_feature_drift

def make_baseline():
    """Small synthetic baseline dataframe with low trip counts"""
    n = 100
    return pd.DataFrame({
        'PULocationID': [1, 2] * (n // 2),
        'trip_count': list(range(n)),
        'lag_15min': [float(i) for i in range(n)],
        'lag_1h': [float(i) for i in range(n)],
        'roll_mean_1h': [float(i) for i in range(n)],
        'is_holiday': [0] * n,
        'hour': [i % 24 for i in range(n)],
        'time_bucket': pd.date_range('2026-01-01', periods=n, freq='15min')
    })

def make_new():
    """Small synthetic new dataframe with high trip counts to simulate drift"""
    n = 100
    return pd.DataFrame({
        'PULocationID': [1, 2] * (n // 2),
        'trip_count': [i + 500 for i in range(n)],
        'lag_15min': [float(i + 500) for i in range(n)],
        'lag_1h': [float(i + 500) for i in range(n)],
        'roll_mean_1h': [float(i + 500) for i in range(n)],
        'is_holiday': [0] * n,
        'hour': [i % 24 for i in range(n)],
        'time_bucket': pd.date_range('2026-02-01', periods=n, freq='15min')
    })

def test_null_rates_no_nulls():
    """Null rates should be 0 when no values are missing"""
    computer = MetricComputer(make_baseline())
    result = computer.metric_3_null_rates(make_new())
    for col, rate in result.items():
        assert rate == 0.0, f"Expected 0 null rate for {col}, got {rate}"

def test_null_rates_with_nulls():
    """Null rate should be 0.5 when half the trip_count values are missing."""
    computer = MetricComputer(make_baseline())
    df = make_new()
    df['trip_count'] = df['trip_count'].astype(float)
    df.loc[:49, 'trip_count'] = np.nan
    result = computer.metric_3_null_rates(df)
    assert result['trip_count'] == 0.5, f"Expected 0.5 null rate, got {result['trip_count']}"

def test_duplicate_rate_no_duplicates():
    """Duplicate rate should be 0 when all rows are unique."""
    computer = MetricComputer(make_baseline())
    result = computer.metric_8_duplicate_rate(make_new())
    assert result['rate'] == 0.0
    assert result['count'] == 0

def test_duplicate_rate_with_duplicates():
    """Duplicate rate should be 0.5 when the dataframe is doubled"""
    computer = MetricComputer(make_baseline())
    df = pd.concat([make_new(), make_new()], ignore_index=True)
    result = computer.metric_8_duplicate_rate(df)
    assert result['rate'] == 0.5
    assert result['count'] == 100

def test_ks_test_detects_drift():
    """KS test should flag drift when distributions are clearly different"""
    computer = MetricComputer(make_baseline())
    result = computer.metric_4_ks_test(make_new())
    assert result['drift_detected'] == True
    assert result['p_value'] < 0.05

def test_detect_feature_drift_detects():
    """detect_feature_drift should find drift and report a positive mean shift"""
    result = detect_feature_drift(make_baseline(), make_new(), 'trip_count')
    assert result['drift_detected'] == True
    assert result['mean_shift_pct'] > 0


if __name__ == "__main__":
    test_null_rates_no_nulls()
    test_null_rates_with_nulls()
    test_duplicate_rate_no_duplicates()
    test_duplicate_rate_with_duplicates()
    test_ks_test_detects_drift()
    test_detect_feature_drift_detects()
    print("All tests passed.")