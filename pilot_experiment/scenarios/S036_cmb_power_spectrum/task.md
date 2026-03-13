# CMB Angular Power Spectrum Analysis

Create a command-line tool that computes the angular power spectrum from Cosmic Microwave Background (CMB) temperature maps using spherical harmonic analysis.

The angular power spectrum C_ℓ describes the statistical properties of CMB temperature fluctuations as a function of angular scale ℓ. Your script should process synthetic CMB temperature maps stored as HEALPix-like arrays and compute the corresponding power spectrum.

## Requirements

1. **Input Processing**: Accept a NumPy array file containing CMB temperature data in microkelvin (μK) units. The input should be a 1D array representing temperature values at HEALPix pixel locations.

2. **Spherical Harmonic Transform**: Implement or approximate a spherical harmonic decomposition to extract the a_ℓm coefficients from the temperature map. For this task, you may use a simplified approach suitable for small maps.

3. **Power Spectrum Calculation**: Compute the angular power spectrum C_ℓ = ⟨|a_ℓm|²⟩ for each multipole ℓ, where the average is taken over all m values for each ℓ.

4. **Multipole Range**: Calculate the power spectrum for multipoles ℓ from 2 to a maximum value determined by the map resolution (typically ℓ_max ≈ √(N_pixels/12) for HEALPix maps).

5. **Output Generation**: Save results as a JSON file containing multipole values (ℓ) and corresponding power spectrum values (C_ℓ) in μK² units. Also generate a matplotlib plot showing ℓ(ℓ+1)C_ℓ/(2π) vs ℓ.

6. **Statistical Analysis**: Include basic statistics in the output: total power (sum of all C_ℓ), peak multipole (ℓ value with maximum power), and RMS temperature fluctuation.

Use argparse to handle command-line arguments for input file path, output JSON file, output plot file, and optional parameters like maximum multipole.
