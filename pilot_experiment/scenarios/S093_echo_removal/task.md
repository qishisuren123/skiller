# Echo Removal from Audio Signals

Create a CLI script that removes echo artifacts from synthetic audio recordings using digital signal processing techniques.

Your script should implement an adaptive echo cancellation algorithm that identifies and removes delayed copies of the original signal. The echo typically appears as an attenuated and delayed version of the original audio signal.

## Requirements

1. **Input Processing**: Accept a NumPy array file (.npy) containing a 1D audio signal with echo artifacts. The signal should be normalized to the range [-1, 1].

2. **Echo Detection**: Implement autocorrelation analysis to detect the primary echo delay. Find the delay (in samples) where the autocorrelation shows a significant secondary peak, indicating the echo delay time.

3. **Echo Cancellation**: Remove the detected echo using an adaptive filtering approach. Implement a simple echo cancellation by subtracting the delayed and attenuated version of the signal from itself, with the delay and attenuation factor determined from the autocorrelation analysis.

4. **Quality Metrics**: Calculate and report two quality metrics:
   - Echo Return Loss Enhancement (ERLE): Measure the reduction in echo power after processing
   - Signal-to-Echo Ratio improvement: Compare the ratio before and after processing

5. **Output Generation**: Save the processed (echo-removed) audio signal as a NumPy array file (.npy) and generate a JSON report containing the detected echo delay, attenuation factor, and quality metrics.

6. **Visualization**: Create a comparison plot showing the original signal, echo-contaminated signal, and processed signal in the time domain, along with their respective autocorrelation functions.

The script should handle various echo delays and attenuation levels commonly found in acoustic environments (delays of 50-500 samples, attenuation factors of 0.2-0.7).

## Command Line Interface
