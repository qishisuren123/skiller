# Example 1: Basic event analysis workflow
import pandas as pd
import numpy as np

# Load collision data
df = pd.read_csv('collision_events.csv')

# Apply detector acceptance cut
df_accepted = df[np.abs(df['leading_jet_eta']) < 2.5]

# Z boson mass window selection
z_candidates = df_accepted[
    (df_accepted['invariant_mass'].between(80, 100)) & 
    (df_accepted['n_leptons'] >= 2)
]

# Calculate significance
n_signal = len(z_candidates)
n_background = len(df_accepted) - n_signal
significance = n_signal / np.sqrt(n_signal + n_background)

print(f"Z boson candidates: {n_signal}")
print(f"Statistical significance: {significance:.2f}")

# Example 2: Cut flow analysis
def analyze_cut_flow(df):
    cuts = [
        ('initial', lambda x: x),
        ('tracks', lambda x: x[x['n_tracks'] >= 2]),
        ('energy', lambda x: x[x['total_energy'] > 10]),
        ('eta', lambda x: x[np.abs(x['leading_jet_eta']) < 2.5])
    ]
    
    cut_flow = {}
    current_df = df
    
    for cut_name, cut_func in cuts:
        current_df = cut_func(current_df)
        cut_flow[cut_name] = len(current_df)
        efficiency = len(current_df) / len(df) * 100
        print(f"{cut_name}: {len(current_df)} events ({efficiency:.1f}%)")
    
    return current_df, cut_flow
