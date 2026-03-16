1. Data Loading and Validation
   - Load temperature CSV file with flexible column name handling
   - Load humidity CSV file with flexible column name handling
   - Validate required columns exist ('date'/'datetime', 'temp_f'/'temperature', 'rh_percent'/'humidity')
   - Merge datasets on datetime with inner join

2. Heat Index Calculation
   - Apply full National Weather Service heat index formula
   - Handle temperatures below 80°F (use air temperature)
   - Apply humidity adjustments for low RH (<13%) and high RH (>85%)
   - Use vectorized numpy operations for efficiency

3. Climatological Baseline Establishment
   - Group data by date to get daily maximum heat index
   - For each day of year (1-366), create 15-day window
   - Use most recent baseline_years of historical data
   - Calculate percentile threshold for each day of year

4. Heat Wave Detection
   - Identify consecutive days exceeding threshold
   - Apply minimum duration filter
   - Calculate event statistics (duration, intensity, excess)
   - Merge events separated by single days

5. Output Generation
   - Create time series CSV with heat index and thresholds
   - Generate JSON summary with heat wave events and statistics
   - Include processing parameters and summary metrics
