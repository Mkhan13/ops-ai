import json
import pandas as pd
from datetime import datetime
from metric_template import MetricComputer

baseline_df = pd.read_parquet("data/demand_enriched_baseline.parquet")
new_df = pd.read_parquet("data/demand_enriched_week4.parquet")
new_df = new_df[new_df['time_bucket'] >= '2026-02-02'] # Filter to the last week of data

computer = MetricComputer(baseline_df)
results = computer.compute_all_metrics(new_df)

ks = results["ks_test"]
psi = results["psi"]
dups = results["duplicate_rate"]
null_rates = results["null_rates"]

print(f"KS Test: statistic={ks['statistic']:.4f}, p-value={ks['p_value']:.6f}, drift={ks['drift_detected']}")
print(f"PSI: {psi:.4f}")
print(f"Duplicate Rate: {dups['rate']:.4f} ({dups['count']} rows)")

for col, rate in null_rates.items():
    print(f"Null Rate {col}: {rate:.4f}")

output_filename = f"metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
with open(output_filename, "w") as output_file:
    json.dump(results, output_file, indent=2, default=str)

print(f"Results written to {output_filename}")
