{
  "changepoints": [2003, 2015],
  "segmented_regression": {
    "segments": [
      {
        "segment_id": 1,
        "start_year": 1988,
        "end_year": 2003,
        "slope": -0.234,
        "slope_ci_95": [-0.456, -0.012],
        "intercept": 125.67,
        "r_squared": 0.423,
        "n_points": 16,
        "mse": 12.34
      },
      {
        "segment_id": 2,
        "start_year": 2003,
        "end_year": 2015,
        "slope": 0.187,
        "slope_ci_95": [-0.089, 0.463],
        "intercept": 118.45,
        "r_squared": 0.156,
        "n_points": 13,
        "mse": 18.76
      },
      {
        "segment_id": 3,
        "start_year": 2015,
        "end_year": 2022,
        "slope": -0.512,
        "slope_ci_95": [-0.834, -0.190],
        "intercept": 132.89,
        "r_squared": 0.678,
        "n_points": 8,
        "mse": 8.92
      }
    ],
    "breakpoints": [
      {"year": 2003},
      {"year": 2015}
    ],
    "overall_mse": 13.67
  },
  "mann_kendall": {
    "statistic": -89,
    "z_score": -1.876,
    "p_value": 0.0607,
    "trend": "decreasing"
  },
  "climate_correlations": {
    "temperature": {
      "lag_0": {
        "pearson": {"r": -0.567, "p_value": 0.0012, "p_value_corrected": 0.0096},
        "spearman": {"r": -0.523, "p_value": 0.0034, "p_value_corrected": 0.0136}
      },
      "lag_1": {
        "pearson": {"r": -0.423, "p_value": 0.0234, "p_value_corrected": 0.0468},
        "spearman": {"r": -0.398, "p_value": 0.0345, "p_value_corrected": 0.0575}
      }
    },
    "precipitation": {
      "lag_0": {
        "pearson": {"r": 0.234, "p_value": 0.1234, "p_value_corrected": 0.1645},
        "spearman": {"r": 0.198, "p_value": 0.1876, "p_value_corrected": 0.2251}
      }
    }
  },
  "data_summary": {
    "n_observations": 35,
    "year_range": [1988, 2022],
    "mean_doy": 121.4,
    "std_doy": 8.7,
    "n_outliers": 3
  }
}
