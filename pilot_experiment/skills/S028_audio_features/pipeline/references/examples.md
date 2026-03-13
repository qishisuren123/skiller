# Mel Scale Conversion
def hz_to_mel(hz):
    return 2595 * np.log10(1 + hz / 700)

def mel_to_hz(mel):
    return 700 * (10**(mel / 2595) - 1)

# Frame-based Processing
def get_n_frames(signal_length, frame_size, hop_size):
    return (signal_length - frame_size) // hop_size + 1

# Zero Crossing Rate
def compute_zcr(sig, frame_size, hop_size):
    n_frames = get_n_frames(len(sig), frame_size, hop_size)
    zcr = np.zeros(n_frames)
    
    for i in range(n_frames):
        start = i * hop_size
        frame = sig[start:start + frame_size]
        zero_crossings = np.sum(np.abs(np.diff(np.sign(frame)))) / 2
        zcr[i] = zero_crossings / frame_size
    
    return zcr

# RMS Energy
def compute_rms_energy(sig, frame_size, hop_size):
    n_frames = get_n_frames(len(sig), frame_size, hop_size)
    rms = np.zeros(n_frames)
    
    for i in range(n_frames):
        start = i * hop_size
        frame = sig[start:start + frame_size]
        rms[i] = np.sqrt(np.mean(frame ** 2))
    
    return rms

# MFCC Computation
def compute_mfcc(spectrogram, sample_rate, n_mfcc=13, n_filters=26):
    filterbank = create_mel_filterbank(n_filters, (spectrogram.shape[0]-1)*2, sample_rate)
    power_spec = spectrogram ** 2
    mel_spec = np.dot(filterbank, power_spec)
    log_mel_spec = np.log(mel_spec + 1e-10)  # Add epsilon
    mfcc = dct(log_mel_spec, axis=0, norm='ortho')
    return mfcc[:n_mfcc].T  # Transpose for frames x coefficients
