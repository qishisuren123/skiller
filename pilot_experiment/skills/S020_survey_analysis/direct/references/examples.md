# Example 1: Basic reverse coding and composite calculation
import pandas as pd

# Sample data
data = {
    'respondent_id': [1, 2, 3],
    'age': [25, 30, 35],
    'gender': ['M', 'F', 'M'],
    'q1': [4, 3, 5], 'q2': [3, 4, 4], 'q3': [2, 1, 3],  # q3 reverse-coded
    'q4': [5, 4, 4], 'q5': [3, 2, 5], 'q6': [4, 5, 3],
    'q7': [1, 2, 2], 'q8': [4, 4, 5], 'q9': [3, 3, 4], 'q10': [5, 4, 4]
}
df = pd.DataFrame(data)

# Reverse code q3: 2→4, 1→5, 3→3
df['q3_r'] = 6 - df['q3']
df['q3'] = df['q3_r']  # Replace for composite calculation

# Calculate composites
df['scale_A'] = df[['q1', 'q2', 'q3', 'q4', 'q5']].mean(axis=1)
df['scale_B'] = df[['q6', 'q7', 'q8', 'q9', 'q10']].mean(axis=1)

# Example 2: Complete CLI usage
"""
# Create sample CSV file
python main.py --input survey_data.csv --output results/ --reverse-items "q3,q5,q7"

# Output files created:
# results/recoded_responses.csv - Original data + reversed items + composites
# results/reliability.json - Cronbach's alpha for each scale
# results/group_comparison.json - Gender group statistics

# Console output:
=== RELIABILITY ANALYSIS ===
Scale A Cronbach's Alpha: 0.847
Scale B Cronbach's Alpha: 0.792

=== GROUP MEANS ===
M (n=45):
  Scale A: M=3.24, SD=0.89
  Scale B: M=3.67, SD=0.76
F (n=52):
  Scale A: M=3.41, SD=0.94
  Scale B: M=3.52, SD=0.82
"""
