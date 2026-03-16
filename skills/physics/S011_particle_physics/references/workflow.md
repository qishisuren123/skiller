# Particle Physics Analysis Workflow

1. **Data Loading**
   - Execute script with `python scripts/main.py --input data.csv --output results/`
   - Script attempts multiple encodings (utf-8, latin-1, cp1252, iso-8859-1)
   - Validates file format and rejects unsupported formats (.root, .hdf5)

2. **Data Cleaning**
   - Replace missing value indicators ("N/A", "-", "NULL") with NaN
   - Convert all numeric columns using pd.to_numeric(errors='coerce')
   - Remove rows with missing critical data (n_tracks, total_energy, leading_jet_eta)
   - Log data quality statistics for each column

3. **Quality Cuts Application**
   - Apply physics cuts: n_tracks >= 2, total_energy > 10, |leading_jet_eta| < 2.5
   - Track cut flow statistics (initial vs after cuts)
   - Create copy of filtered DataFrame to avoid view issues

4. **Event Classification**
   - Define signal region: mass window + n_leptons >= 2
   - Classify events as 'signal' or 'background'
   - Add event_type column to DataFrame

5. **Statistical Analysis**
   - Count signal and background events in mass window only
   - Calculate signal-to-noise ratio
   - Compute statistical significance: S / sqrt(S + B) for signal region

6. **Output Generation**
   - Save filtered events to CSV with event_type classification
   - Generate JSON summary with all statistics and cut flow
   - Print summary statistics to console
