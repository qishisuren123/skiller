# Example 1: Basic LMS noise cancellation usage
python main.py \
  --input-signal ./data/noisy_input.npy \
  --output-signal ./data/cleaned_output.npy \
  --reference-noise ./data/reference_noise.npy \
  --step-size 0.01 \
  --filter-length 32 \
  --metrics-file ./results/metrics.json

# Example 2: Advanced usage with custom parameters for challenging noise
python main.py \
  --input-signal ./experiments/high_noise_input.npy \
  --output-signal ./experiments/cleaned_high_noise.npy \
  --reference-noise ./experiments/ref_noise.npy \
  --step-size 0.005 \
  --filter-length 64 \
  --metrics-file ./experiments/performance.json

# Loading and analyzing results
import numpy as np
import json

# Load processed signals
noisy_signal = np.load('./data/noisy_input.npy')
cleaned_signal = np.load('./data/cleaned_output.npy')
reference_noise = np.load('./data/reference_noise.npy')

# Load performance metrics
with open('./results/metrics.json', 'r') as f:
    metrics = json.load(f)

print(f"SNR improved by {metrics['snr_improvement_db']:.2f} dB")
print(f"MSE reduced by {metrics['mse_reduction_percent']:.1f}%")

# Verify signal properties
fs = metrics['parameters']['sampling_rate']
duration = len(cleaned_signal) / fs
print(f"Processed {duration:.1f}s of audio at {fs}Hz sampling rate")
