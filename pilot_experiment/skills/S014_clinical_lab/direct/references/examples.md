# Example 1: Basic lab result processing
import pandas as pd

# Sample clinical data
data = {
    'patient_id': [1001, 1001, 1002],
    'test_name': ['glucose', 'creatinine', 'glucose'],
    'value': [180, 1.5, 95],
    'unit': ['mg/dL', 'mg/dL', 'mg/dL'],
    'reference_low': [70, 0.6, 70],
    'reference_high': [100, 1.2, 100],
    'timestamp': ['2024-01-15 09:30:00', '2024-01-15 09:30:00', '2024-01-16 08:15:00']
}

df = pd.DataFrame(data)

# Normalize glucose from mg/dL to mmol/L
df.loc[df['test_name'] == 'glucose', 'normalized_value'] = df['value'] * 0.0555

# Flag abnormal results
def flag_result(row):
    if row['normalized_value'] < row['reference_low']:
        return 'low'
    elif row['normalized_value'] > row['reference_high']:
        return 'high'
    return 'normal'

df['flag'] = df.apply(flag_result, axis=1)

# Example 2: Patient summary generation
patient_summaries = {}
for patient_id in df['patient_id'].unique():
    patient_tests = df[df['patient_id'] == patient_id]
    abnormal_count = len(patient_tests[patient_tests['flag'] != 'normal'])
    
    patient_summaries[patient_id] = {
        'n_abnormal': abnormal_count,
        'n_critical': len(patient_tests[patient_tests['is_critical'] == True]),
        'most_recent_test': patient_tests['timestamp'].max()
    }
