# Blood Cell Count Analysis Tool

Create a CLI tool that processes complete blood count (CBC) data to normalize values and flag abnormal results based on reference ranges.

Your script should accept CBC data containing patient measurements for different blood cell types and output normalized values along with clinical flags for abnormal results.

## Requirements

1. **Data Processing**: Read patient CBC data including white blood cells (WBC), red blood cells (RBC), hemoglobin (HGB), hematocrit (HCT), and platelet count (PLT). Handle missing values by interpolating using the patient's other available measurements.

2. **Age-Gender Normalization**: Apply age and gender-specific reference ranges to normalize each measurement to a z-score. Use pediatric ranges for patients under 18 and adult ranges for 18+, with separate male/female ranges where applicable.

3. **Clinical Flagging**: Flag measurements as 'LOW', 'NORMAL', or 'HIGH' based on clinical thresholds (typically ±2 standard deviations from reference mean). Generate severity scores (0-1) where 1 indicates the most extreme deviation.

4. **Statistical Summary**: Calculate population statistics including mean, standard deviation, and percentage of abnormal results for each CBC parameter across all patients.

5. **Risk Stratification**: Assign each patient an overall risk category ('LOW', 'MODERATE', 'HIGH') based on the number and severity of abnormal parameters. Export a summary report showing risk distribution.

6. **Output Generation**: Save results as both a detailed CSV file with individual patient results and a JSON summary containing population statistics and risk stratification counts.

## Usage
