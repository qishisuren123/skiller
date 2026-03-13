# Election Forecast Aggregator

Create a CLI script that aggregates polling data and generates weighted election forecasts using advanced statistical methods.

Your script should accept polling data through command-line arguments and produce probabilistic forecasts for election outcomes. The system must handle multiple candidates, poll reliability weighting, temporal decay, and uncertainty quantification.

## Requirements

1. **Poll Data Processing**: Accept poll data as JSON string containing polls with fields: date (YYYY-MM-DD), sample_size, candidates (dict of candidate->percentage), pollster_rating (A+ to F scale). Parse and validate all input data.

2. **Temporal Weighting**: Implement exponential decay weighting where more recent polls have higher influence. Use a half-life parameter (default 14 days) where poll weights decay by 50% every half-life period from the election date.

3. **Quality Adjustment**: Convert pollster ratings to numeric weights (A+=1.0, A=0.9, A-=0.8, B+=0.7, B=0.6, B-=0.5, C+=0.4, C=0.3, C-=0.2, D=0.1, F=0.05) and combine with sample size weighting using sqrt(sample_size)/1000 as a multiplier.

4. **Bayesian Aggregation**: Compute weighted averages for each candidate, then apply Bayesian updating with a uniform prior. Calculate the posterior mean and standard deviation for each candidate's vote share, accounting for polling uncertainty.

5. **Monte Carlo Simulation**: Run 10,000 Monte Carlo simulations using the posterior distributions to estimate win probabilities. Each simulation should sample from normal distributions (bounded 0-100%) and normalize to ensure vote shares sum to 100%.

6. **Output Generation**: Save results as JSON file containing: aggregated vote shares, confidence intervals (95%), win probabilities, effective sample size, and simulation metadata. Also generate a summary CSV with candidate names, predicted vote share, and win probability.

Use argparse with arguments: `--polls` (JSON string), `--election-date` (YYYY-MM-DD), `--output-json`, `--output-csv`, and optional `--half-life` (days).
