1. Prepare CSV file with wavelength column and sample absorbance columns
2. Run script with: python scripts/main.py --input data.csv --output results.json
3. Add verbosity flags (-v or -vv) for detailed logging output
4. Adjust peak detection parameters (--min-height, --min-distance) as needed
5. Script loads CSV data and converts all columns to numeric format
6. For each sample column, detect peaks using scipy.signal.find_peaks
7. Calculate FWHM using peak_widths with error handling for zero-width peaks
8. Compute baseline-corrected areas using trapezoidal integration
9. Save results as JSON with peak properties and sample summaries
10. Review output for dominant peak wavelengths and peak counts per sample
