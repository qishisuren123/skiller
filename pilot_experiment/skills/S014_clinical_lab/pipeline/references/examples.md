# Unit conversion examples
glucose_mmol = glucose_mgdl * 0.0555  # mg/dL to mmol/L
creatinine_umol = creatinine_mgdl * 88.4  # mg/dL to μmol/L

# Critical value detection
is_critical = value < (ref_low * 0.5) or value > (ref_high * 2.0)

# Flexible timestamp parsing
def parse_timestamp(ts):
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
        try:
            return datetime.strptime(ts.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse: {ts}")

# Error handling pattern
try:
    value = float(row['value'].strip())
    # Process data...
except (ValueError, KeyError) as e:
    print(f"Skipping row {row_num}: {e}")
    continue

# Patient summary tracking
if patient_id not in summary:
    summary[patient_id] = {
        'n_abnormal': 0,
        'n_critical': 0,
        'tests': [],
        'most_recent': timestamp
    }
