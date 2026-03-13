# Kaplan-Meier Survival Analysis CLI Tool

Create a command-line tool that performs Kaplan-Meier survival analysis on patient data and generates comprehensive survival statistics and visualizations.

Your script should accept patient survival data and compute key survival metrics including survival probabilities, median survival time, and confidence intervals. The tool should also generate survival curves and summary statistics commonly used in medical research.

## Requirements

1. **Data Input**: Accept patient data via command-line arguments including survival times, event indicators (censored/uncensored), and optional group labels for comparative analysis.

2. **Kaplan-Meier Estimation**: Calculate survival probabilities at each time point using the Kaplan-Meier estimator. Handle both censored and uncensored observations correctly, accounting for patients lost to follow-up.

3. **Statistical Metrics**: Compute key survival statistics including median survival time, 95% confidence intervals for survival probabilities, and the number at risk at each time point.

4. **Survival Curves**: Generate publication-quality survival curve plots showing probability of survival over time. If multiple groups are provided, create comparative survival curves with different colors/styles for each group.

5. **Risk Tables**: Create at-risk tables showing the number of patients remaining in the study at regular time intervals (e.g., every 6 months or yearly).

6. **Output Generation**: Save results to JSON format containing all computed statistics, survival probabilities, confidence intervals, and summary metrics. Also save the survival curve plot as a PNG image.

The tool should handle typical medical scenarios including varying follow-up times, censored observations, and multiple treatment groups. Ensure proper statistical handling of tied survival times and appropriate confidence interval calculations using standard methods (e.g., Greenwood's formula for variance estimation).

Use argparse for command-line interface with clear options for input data, output files, and analysis parameters.
