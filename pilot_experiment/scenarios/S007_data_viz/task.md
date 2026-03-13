Write a Python CLI script to visualize neural population activity data.

Input: A CSV file with columns: trial, time, and multiple neuron columns (neuron_0, neuron_1, ...) containing firing rates.

Requirements:
1. Use argparse: --input CSV, --output-dir for saving plots
2. Create two plots and save as PNG:
   a. firing_rate_heatmap.png: heatmap of trial-averaged firing rates (neurons × time)
   b. population_psth.png: line plot of population mean firing rate over time with shaded SEM
3. Use matplotlib (no interactive display, use Agg backend)
4. Print summary: number of neurons, trials, time range
