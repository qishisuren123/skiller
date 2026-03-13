# Example 1: Basic transit detection run
"""
python main.py --num_points 2000 --noise_level 0.0005 --transit_depth 0.015 --output_file results.json --plot_file transit_plot.png

Expected output in results.json:
{
  "detection_significance": 8.2,
  "significant_detection": true,
  "fitted_transit_time": 5.001,
  "fitted_depth": 0.0149,
  "fitted_duration_hours": 2.98,
  "chi_squared": 1987.3,
  "reduced_chi_squared": 0.994,
  "fit_success": true
}
"""

# Example 2: Low signal-to-noise case with detection failure
"""
python main.py --num_points 500 --noise_level 0.005 --transit_depth 0.002 --output_file low_snr_results.json

Expected output for marginal detection:
{
  "detection_significance": 2.1,
  "significant_detection": false,
  "fit_success": false,
  "fit_error": "No significant transit detected"
}

# Key usage patterns:
# 1. Always check 'significant_detection' before using fitted parameters
# 2. Monitor 'reduced_chi_squared' - values >> 1 indicate poor fit or underestimated noise
# 3. Use detection_significance to assess reliability (>5σ for high confidence)
# 4. Fitted duration should be close to injected 3 hours for successful recovery
"""
