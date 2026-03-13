# Thermal Analysis: DSC Curve Processing

Create a command-line tool that processes Differential Scanning Calorimetry (DSC) thermal analysis data to perform baseline correction and detect thermal transitions (peaks).

DSC measures heat flow as a function of temperature, revealing thermal events like melting, crystallization, and glass transitions. Raw DSC data often contains baseline drift that must be corrected before accurate peak analysis.

## Requirements

Your script should accept the following arguments:
- `--temperature-range`: Temperature range as "min,max" (°C)
- `--heating-rate`: Heating rate in °C/min
- `--num-points`: Number of data points to generate
- `--baseline-method`: Baseline correction method ("linear" or "polynomial")
- `--sensitivity`: Peak detection sensitivity (0.1-1.0, higher = more sensitive)
- `--output`: Output JSON file path

The script should:

1. **Generate synthetic DSC data** with realistic thermal events (endothermic/exothermic peaks) and baseline drift within the specified temperature range and heating rate.

2. **Apply baseline correction** using the specified method:
   - Linear: fit and subtract a linear baseline
   - Polynomial: fit and subtract a 2nd-order polynomial baseline

3. **Detect thermal peaks** in the corrected data using the sensitivity parameter. Identify both endothermic (negative) and exothermic (positive) peaks with their temperatures and magnitudes.

4. **Calculate thermal properties**:
   - Peak onset temperatures (extrapolated onset points)
   - Peak areas (enthalpy changes in J/g)
   - Peak widths at half maximum

5. **Output results** as JSON containing:
   - Processing parameters used
   - Detected peaks with properties (temperature, magnitude, onset, area, width)
   - Baseline correction statistics (R² value, correction range)

6. **Save processed data** as CSV with columns: temperature, raw_heat_flow, corrected_heat_flow, baseline

The tool should handle typical DSC temperature ranges (e.g., -50°C to 300°C) and heating rates (1-20°C/min).
