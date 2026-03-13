# Basic Lomb-Scargle usage
times = np.array([1, 2, 3, 4, 5])
mags = np.array([1.2, 1.8, 1.1, 1.9, 1.0])
omega = np.linspace(0.1, 10, 1000) * 2 * np.pi
power = lombscargle(times, mags - np.mean(mags), omega, normalize=True)
best_period = 2 * np.pi / omega[np.argmax(power)]

# Array consistency pattern
mask = ~np.isnan(times) & ~np.isnan(mags)
times_clean = times[mask]
mags_clean = mags[mask]
sort_idx = np.argsort(times_clean)
times_final = times_clean[sort_idx]
mags_final = mags_clean[sort_idx]

# Harmonic detection
def is_harmonic(period1, period2, tolerance=0.05):
    ratio = period1 / period2
    return abs(ratio - round(ratio)) < tolerance

# Phase folding
phases = (times % period) / period
phase_bins = np.linspace(0, 1, 20)
binned_phases = np.digitize(phases, phase_bins)
