# Example 1: Basic echo cancellation usage
import numpy as np

# Create synthetic echo-contaminated signal
original = np.random.randn(1000)
delay, attenuation = 100, 0.4
echo_signal = original.copy()
echo_signal[delay:] += attenuation * original[:-delay]

# Save test signal
np.save('test_audio.npy', echo_signal)

# Run echo cancellation
# python main.py test_audio.npy --output_dir results

# Example 2: Custom parameter detection and processing
def process_audio_with_custom_params():
    # Load signal
    signal = np.load('audio_with_echo.npy')
    
    # Manual parameter detection
    autocorr = np.correlate(signal, signal, mode='full')
    autocorr = autocorr[len(autocorr)//2:] / autocorr[len(autocorr)//2]
    
    # Find echo delay in specific range
    search_start, search_end = 75, 300
    delay_candidates = autocorr[search_start:search_end]
    delay = np.argmax(delay_candidates) + search_start
    attenuation = autocorr[delay]
    
    # Apply cancellation
    processed = signal.copy()
    for i in range(delay, len(signal)):
        processed[i] = signal[i] - attenuation * signal[i - delay]
    
    # Calculate improvement
    echo_power_orig = np.mean((attenuation * signal[:-delay])**2)
    echo_power_proc = np.mean((attenuation * processed[:-delay])**2)
    erle = 10 * np.log10(echo_power_orig / max(echo_power_proc, 1e-10))
    
    print(f"Echo delay: {delay} samples")
    print(f"Attenuation: {attenuation:.3f}")
    print(f"ERLE: {erle:.2f} dB")
    
    return processed
