import subprocess
import tempfile
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

def create_data():
    """Generate synthetic CBC data and reference ranges"""
    np.random.seed(42)
    
    # Generate patient data
    n_patients = 100
    ages = np.random.randint(5, 80, n_patients)
    genders = np.random.choice(['M', 'F'], n_patients)
    
    # Generate CBC values with some correlation to age/gender
    patients = []
    for i in range(n_patients):
        age = ages[i]
        gender = genders[i]
        
        # Base values with age/gender effects
        if age < 18:  # Pediatric
            wbc_base = 8.0 + np.random.normal(0, 2)
            rbc_base = 4.2 + np.random.normal(0, 0.5)
            hgb_base = 12.0 + np.random.normal(0, 1.5)
            hct_base = 36 + np.random.normal(0, 4)
            plt_base = 300 + np.random.normal(0, 80)
        else:  # Adult
            wbc_base = 7.0 + np.random.normal(0, 2)
            if gender == 'M':
                rbc_base = 4.8 + np.random.normal(0, 0.6)
                hgb_base = 14.5 + np.random.normal(0, 1.5)
                hct_base = 42 + np.random.normal(0, 5)
            else:
                rbc_base = 4.3 + np.random.normal(0, 0.5)
                hgb_base = 12.5 + np.random.normal(0, 1.5)
                hct_base = 38 + np.random.normal(0, 4)
            plt_base = 250 + np.random.normal(0, 70)
        
        # Add some missing values (10% chance)
        wbc = wbc_base if np.random.random() > 0.1 else np.nan
        rbc = rbc_base if np.random.random() > 0.1 else np.nan
        hgb = hgb_base if np.random.random() > 0.1 else np.nan
        hct = hct_base if np.random.random() > 0.1 else np.nan
        plt = plt_base if np.random.random() > 0.1 else np.nan
        
        patients.append({
            'patient_id': f'P{i+1:03d}',
            'age': age,
            'gender': gender,
            'WBC': max(0.1, wbc) if not np.isnan(wbc) else np.nan,
            'RBC': max(0.1, rbc) if not np.isnan(rbc) else np.nan,
            'HGB': max(1.0, hgb) if not np.isnan(hgb) else np.nan,
            'HCT': max(5.0, hct) if not np.isnan(hct) else np.nan,
            'PLT': max(10, plt) if not np.isnan(plt) else np.nan
        })
    
    # Reference ranges
    reference_ranges = {
        'pediatric': {
            'WBC': {'mean': 8.0, 'std': 2.0, 'low_threshold': 4.0, 'high_threshold': 12.0},
            'RBC': {'mean': 4.2, 'std': 0.5, 'low_threshold': 3.2, 'high_threshold': 5.2},
            'HGB': {'mean': 12.0, 'std': 1.5, 'low_threshold': 9.0, 'high_threshold': 15.0},
            'HCT': {'mean': 36, 'std': 4, 'low_threshold': 28, 'high_threshold': 44},
            'PLT': {'mean': 300, 'std': 80, 'low_threshold': 140, 'high_threshold': 460}
        },
        'adult_male': {
            'WBC': {'mean': 7.0, 'std': 2.0, 'low_threshold': 3.0, 'high_threshold': 11.0},
            'RBC': {'mean': 4.8, 'std': 0.6, 'low_threshold': 3.6, 'high_threshold': 6.0},
            'HGB': {'mean': 14.5, 'std': 1.5, 'low_threshold': 11.5, 'high_threshold': 17.5},
            'HCT': {'mean': 42, 'std': 5, 'low_threshold': 32, 'high_threshold': 52},
            'PLT': {'mean': 250, 'std': 70, 'low_threshold': 110, 'high_threshold': 390}
        },
        'adult_female': {
            'WBC': {'mean': 7.0, 'std': 2.0, 'low_threshold': 3.0, 'high_threshold': 11.0},
            'RBC': {'mean': 4.3, 'std': 0.5, 'low_threshold': 3.3, 'high_threshold': 5.3},
            'HGB': {'mean': 12.5, 'std': 1.5, 'low_threshold': 9.5, 'high_threshold': 15.5},
            'HCT': {'mean': 38, 'std': 4, 'low_threshold': 30, 'high_threshold': 46},
            'PLT': {'mean': 250, 'std': 70, 'low_threshold': 110, 'high_threshold': 390}
        }
    }
    
    return pd.DataFrame(patients), reference_ranges

def test_blood_cell_count_analysis():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test data
        patient_data, reference_ranges = create_data()
        
        # Save input files
        input_file = tmpdir / "cbc_data.csv"
        ranges_file = tmpdir / "reference_ranges.json"
        output_csv = tmpdir / "results.csv"
        output_json = tmpdir / "summary.json"
        
        patient_data.to_csv(input_file, index=False)
        with open(ranges_file, 'w') as f:
            json.dump(reference_ranges, f)
        
        # Test different argument patterns
        cmd_patterns = [
            ["--input-data", str(input_file), "--output-csv", str(output_csv), 
             "--output-json", str(output_json), "--reference-ranges", str(ranges_file)],
            ["--input_data", str(input_file), "--output_csv", str(output_csv), 
             "--output_json", str(output_json), "--reference_ranges", str(ranges_file)],
            ["-i", str(input_file), "-c", str(output_csv), 
             "-j", str(output_json), "-r", str(ranges_file)]
        ]
        
        success = False
        for cmd_args in cmd_patterns:
            try:
                result = subprocess.run(
                    ["python", "generated.py"] + cmd_args,
                    cwd=tmpdir, capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        print(f"PASS: Script execution successful: {success}")
        if not success:
            return
        
        # Load results
        try:
            results_df = pd.read_csv(output_csv)
            with open(output_json, 'r') as f:
                summary_data = json.load(f)
        except Exception as e:
            print(f"FAIL: Could not load output files: {e}")
            return
        
        # Test 1: Check output files exist
        print(f"PASS: Output CSV file created: {output_csv.exists()}")
        print(f"PASS: Output JSON file created: {output_json.exists()}")
        
        # Test 2: Check CSV structure
        required_columns = ['patient_id', 'age', 'gender']
        csv_has_required = all(col in results_df.columns for col in required_columns)
        print(f"PASS: CSV contains required patient columns: {csv_has_required}")
        
        # Test 3: Check for z-scores or normalized values
        zscore_cols = [col for col in results_df.columns if 'zscore' in col.lower() or 'normalized' in col.lower()]
        has_normalization = len(zscore_cols) > 0
        print(f"PASS: Results include normalized/z-score values: {has_normalization}")
        
        # Test 4: Check for clinical flags
        flag_cols = [col for col in results_df.columns if 'flag' in col.lower() or any(val in str(results_df[col].iloc[0] if len(results_df) > 0 else '') for val in ['LOW', 'HIGH', 'NORMAL'] for col in results_df.columns)]
        has_flags = len(flag_cols) > 0 or any('LOW' in str(results_df[col].values) or 'HIGH' in str(results_df[col].values) for col in results_df.columns)
        print(f"PASS: Results include clinical flags (LOW/NORMAL/HIGH): {has_flags}")
        
        # Test 5: Check for severity scores
        severity_cols = [col for col in results_df.columns if 'severity' in col.lower() or 'score' in col.lower()]
        has_severity = len(severity_cols) > 0
        print(f"PASS: Results include severity scores: {has_severity}")
        
        # Test 6: Check missing value handling
        original_missing = patient_data.isnull().sum().sum()
        result_missing = results_df.isnull().sum().sum()
        handled_missing = original_missing > 0 and result_missing < original_missing
        print(f"PASS: Missing values were handled (interpolated): {handled_missing}")
        
        # Test 7: Check JSON summary structure
        has_population_stats = 'population_statistics' in summary_data or 'statistics' in summary_data or any('mean' in str(v) for v in summary_data.values())
        print(f"PASS: JSON contains population statistics: {has_population_stats}")
        
        # Test 8: Check risk stratification
        has_risk_categories = 'risk_distribution' in summary_data or any('risk' in k.lower() for k in summary_data.keys()) or any('LOW' in str(v) or 'HIGH' in str(v) for v in summary_data.values())
        print(f"PASS: JSON contains risk stratification: {has_risk_categories}")
        
        # Test 9: Check patient count consistency
        patient_count_consistent = len(results_df) == len(patient_data)
        print(f"PASS: Patient count consistent between input and output: {patient_count_consistent}")
        
        # Test 10: Check for CBC parameters
        cbc_params = ['WBC', 'RBC', 'HGB', 'HCT', 'PLT']
        has_cbc_results = any(any(param.lower() in col.lower() for param in cbc_params) for col in results_df.columns)
        print(f"PASS: Results include CBC parameters: {has_cbc_results}")
        
        # Test 11: Check age-gender specific processing
        has_age_gender_processing = len(results_df['age'].unique()) > 1 and len(results_df['gender'].unique()) > 1
        print(f"PASS: Age and gender data preserved for stratification: {has_age_gender_processing}")
        
        # Test 12: Check for abnormal result percentage
        has_abnormal_stats = any('abnormal' in str(v).lower() or 'percentage' in str(v).lower() for v in summary_data.values())
        print(f"PASS: Summary includes abnormal result statistics: {has_abnormal_stats}")
        
        # SCORE 1: Data completeness and processing quality
        completeness_score = 0.0
        if success: completeness_score += 0.3
        if csv_has_required: completeness_score += 0.2
        if has_normalization: completeness_score += 0.2
        if has_flags: completeness_score += 0.15
        if handled_missing: completeness_score += 0.15
        print(f"SCORE: Data processing completeness: {completeness_score:.3f}")
        
        # SCORE 2: Clinical analysis accuracy
        clinical_score = 0.0
        if has_severity: clinical_score += 0.25
        if has_population_stats: clinical_score += 0.25
        if has_risk_categories: clinical_score += 0.25
        if has_cbc_results: clinical_score += 0.15
        if has_abnormal_stats: clinical_score += 0.1
        print(f"SCORE: Clinical analysis accuracy: {clinical_score:.3f}")

if __name__ == "__main__":
    test_blood_cell_count_analysis()
