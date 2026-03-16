1. **Data Loading**: Use load_spectrogram() function to handle various .npy file formats including object arrays and pickled data
2. **Data Cleaning**: Replace NaN and infinite values with minimum finite value to ensure numerical stability
3. **Normalization**: Create normalized version for peak finding while preserving original values for SNR calculation
4. **Sliding Window**: Process spectrogram in overlapping windows (50% overlap) across time dimension
5. **Peak Detection**: Find maximum power frequency bin at each time step within window using argmax
6. **Linear Regression**: Fit linear model to frequency trajectory using sklearn LinearRegression
7. **Confidence Calculation**: Combine R-squared linearity score with SNR-based signal strength weighting
8. **Filtering**: Apply threshold to confidence scores and collect valid chirp detections
9. **Output Generation**: Save results as JSON and create visualization with overlaid detection rectangles
10. **Validation**: Log statistics including candidate count, detection count, and average confidence scores
