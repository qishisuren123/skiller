Write a Python CLI script to analyze particle collision event data from a high-energy physics experiment.

Input: A CSV file where each row is a collision event with columns:
- event_id, n_tracks, total_energy, missing_et, leading_jet_pt, leading_jet_eta, n_jets, n_leptons, invariant_mass

Requirements:
1. Use argparse: --input CSV path, --output directory, --mass-window (default "80,100" for Z boson)
2. Apply quality cuts: n_tracks >= 2, total_energy > 10 GeV, |leading_jet_eta| < 2.5
3. Classify events: "signal" if invariant_mass within mass window AND n_leptons >= 2, else "background"
4. Compute signal-to-noise ratio and statistical significance (S / sqrt(S+B))
5. Output: filtered_events.csv, event_summary.json (total, signal, background, significance, cut_flow)
6. Print summary: events before/after cuts, signal fraction, significance
