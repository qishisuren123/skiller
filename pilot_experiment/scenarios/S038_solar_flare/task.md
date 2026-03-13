# Solar Flare Detection and Classification

Create a CLI script that detects and classifies solar flare events from synthetic X-ray light curve data.

Solar flares are sudden releases of electromagnetic energy from the Sun's surface, observable as intensity spikes in X-ray measurements. Your task is to analyze time-series X-ray flux data to identify flare events and classify them by magnitude.

## Requirements

1. **Data Generation**: Generate synthetic X-ray light curve data spanning 24 hours with 1-minute resolution. Include a baseline flux level with random noise and inject 3-8 artificial flare events of varying intensities and durations.

2. **Flare Detection**: Implement a threshold-based detection algorithm that identifies flare events when the flux exceeds 3 standard deviations above the baseline for at least 5 consecutive minutes.

3. **Flare Classification**: Classify detected flares into three categories based on peak intensity:
   - Class C: 1-10x baseline flux
   - Class M: 10-100x baseline flux  
   - Class X: >100x baseline flux

4. **Peak Analysis**: For each detected flare, determine the start time, peak time, end time, peak flux value, and total duration in minutes.

5. **Output Generation**: Save results to a JSON file containing a list of detected flares with their properties (start_time, peak_time, end_time, peak_flux, duration, classification).

6. **Visualization**: Generate a matplotlib plot showing the light curve with detected flares highlighted and labeled by class. Save as PNG format.

## Command Line Interface
