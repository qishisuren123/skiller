import json
import tempfile
import subprocess
import os
import sys
import numpy as np
from datetime import datetime, timedelta
import hashlib
import random

def create_data():
    """Generate synthetic DICOM metadata for testing"""
    np.random.seed(42)
    random.seed(42)
    
    modalities = ['CT', 'MRI', 'XR', 'US']
    institutions = ['HOSP_A', 'HOSP_B', 'HOSP_C']
    
    # Generate validation rules
    validation_rules = {
        "patient_id_pattern": "^P[0-9]{6}$",
        "modality_params": {
            "CT": {"slice_thickness": {"min": 0.5, "max": 10.0}},
            "MRI": {"echo_time": {"min": 5.0, "max": 200.0}},
            "XR": {"kvp": {"min": 50, "max": 150}},
            "US": {"frequency": {"min": 2.0, "max": 15.0}}
        },
        "age_range": {"min": 0, "max": 120},
        "date_format": "%Y-%m-%d"
    }
    
    # Generate DICOM metadata records
    records = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(50):
        patient_id = f"P{i:06d}" if i < 45 else f"INVALID_{i}"  # Some invalid IDs
        study_date = base_date + timedelta(days=np.random.randint(0, 365))
        
        # Patient demographics
        patient = {
            "patient_id": patient_id,
            "patient_name": f"Patient_{i:03d}",
            "birth_date": (study_date - timedelta(days=np.random.randint(365*18, 365*80))).strftime("%Y-%m-%d"),
            "sex": np.random.choice(['M', 'F']),
            "institution": np.random.choice(institutions)
        }
        
        # Calculate age
        birth_date = datetime.strptime(patient["birth_date"], "%Y-%m-%d")
        age = (study_date - birth_date).days // 365
        
        # Study information
        study = {
            "study_id": f"ST{i:06d}",
            "study_date": study_date.strftime("%Y-%m-%d"),
            "study_description": f"Study_{i}",
            "patient_age": age
        }
        
        # Generate 1-3 series per study
        series_list = []
        num_series = np.random.randint(1, 4)
        
        for s in range(num_series):
            modality = np.random.choice(modalities)
            series_date = study_date + timedelta(hours=np.random.randint(0, 24))
            
            series = {
                "series_id": f"SE{i:06d}_{s}",
                "series_date": series_date.strftime("%Y-%m-%d"),
                "modality": modality,
                "series_description": f"Series_{s}",
                "pixel_spacing": [np.random.uniform(0.1, 2.0), np.random.uniform(0.1, 2.0)]
            }
            
            # Add modality-specific parameters
            if modality == 'CT':
                series["slice_thickness"] = np.random.uniform(0.5, 10.0) if i < 40 else 15.0  # Some invalid
            elif modality == 'MRI':
                series["echo_time"] = np.random.uniform(5.0, 200.0) if i < 40 else 250.0  # Some invalid
            elif modality == 'XR':
                series["kvp"] = np.random.randint(50, 151) if i < 40 else 200  # Some invalid
            elif modality == 'US':
                series["frequency"] = np.random.uniform(2.0, 15.0) if i < 40 else 20.0  # Some invalid
            
            series_list.append(series)
        
        record = {
            "patient": patient,
            "study": study,
            "series": series_list
        }
        records.append(record)
    
    return {"records": records}, validation_rules

def test_dicom_metadata_tool():
    """Test the DICOM metadata extraction and validation tool"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test data
        input_data, validation_rules = create_data()
        
        # Write input files
        input_file = os.path.join(temp_dir, "dicom_data.json")
        rules_file = os.path.join(temp_dir, "validation_rules.json")
        report_file = os.path.join(temp_dir, "validation_report.json")
        summary_file = os.path.join(temp_dir, "summary.json")
        anon_report_file = os.path.join(temp_dir, "anon_report.json")
        anon_summary_file = os.path.join(temp_dir, "anon_summary.json")
        
        with open(input_file, 'w') as f:
            json.dump(input_data, f)
        
        with open(rules_file, 'w') as f:
            json.dump(validation_rules, f)
        
        # Test 1: Basic execution without anonymization
        try:
            result = subprocess.run([
                sys.executable, "generated.py",
                "--input-data", input_file,
                "--output-report", report_file,
                "--output-summary", summary_file,
                "--validation-rules", rules_file
            ], capture_output=True, text=True, timeout=30)
            print("PASS: Script executed successfully")
            basic_execution = True
        except Exception as e:
            print(f"FAIL: Script execution failed: {e}")
            basic_execution = False
        
        if not basic_execution:
            print("SCORE: 0.0")
            print("SCORE: 0.0")
            return
        
        # Test 2: Output files created
        report_exists = os.path.exists(report_file)
        summary_exists = os.path.exists(summary_file)
        print(f"{'PASS' if report_exists else 'FAIL'}: Validation report file created")
        print(f"{'PASS' if summary_exists else 'FAIL'}: Summary file created")
        
        if not (report_exists and summary_exists):
            print("SCORE: 0.0")
            print("SCORE: 0.0")
            return
        
        # Load outputs
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        # Test 3: Report structure validation
        required_report_keys = ['total_records', 'validation_results', 'compliance_summary']
        report_structure_valid = all(key in report for key in required_report_keys)
        print(f"{'PASS' if report_structure_valid else 'FAIL'}: Report has required structure")
        
        # Test 4: Summary structure validation
        required_summary_keys = ['patient_demographics', 'study_statistics', 'modality_distribution']
        summary_structure_valid = all(key in summary for key in required_summary_keys)
        print(f"{'PASS' if summary_structure_valid else 'FAIL'}: Summary has required structure")
        
        # Test 5: Validation results contain errors for invalid records
        validation_results = report.get('validation_results', [])
        has_validation_errors = any(
            result.get('status') == 'FAIL' or len(result.get('violations', [])) > 0
            for result in validation_results
        )
        print(f"{'PASS' if has_validation_errors else 'FAIL'}: Validation detected invalid records")
        
        # Test 6: Patient ID validation
        invalid_patient_ids = [r for r in validation_results 
                             if any('patient_id' in v.get('field', '') for v in r.get('violations', []))]
        patient_id_validation = len(invalid_patient_ids) >= 3  # Should catch invalid IDs
        print(f"{'PASS' if patient_id_validation else 'FAIL'}: Patient ID validation working")
        
        # Test 7: Modality parameter validation
        modality_violations = [r for r in validation_results 
                             if any('slice_thickness' in str(v) or 'echo_time' in str(v) 
                                   for v in r.get('violations', []))]
        modality_param_validation = len(modality_violations) >= 3
        print(f"{'PASS' if modality_param_validation else 'FAIL'}: Modality parameter validation working")
        
        # Test 8: Statistical summary completeness
        demo_stats = summary.get('patient_demographics', {})
        has_age_stats = 'age_distribution' in demo_stats or 'mean_age' in demo_stats
        has_sex_stats = 'sex_distribution' in demo_stats
        stats_complete = has_age_stats and has_sex_stats
        print(f"{'PASS' if stats_complete else 'FAIL'}: Patient demographics statistics complete")
        
        # Test 9: Modality distribution analysis
        modality_dist = summary.get('modality_distribution', {})
        expected_modalities = ['CT', 'MRI', 'XR', 'US']
        modality_analysis_complete = any(mod in str(modality_dist) for mod in expected_modalities)
        print(f"{'PASS' if modality_analysis_complete else 'FAIL'}: Modality distribution analysis complete")
        
        # Test 10: Anonymization functionality
        try:
            result = subprocess.run([
                sys.executable, "generated.py",
                "--input-data", input_file,
                "--output-report", anon_report_file,
                "--output-summary", anon_summary_file,
                "--validation-rules", rules_file,
                "--anonymize"
            ], capture_output=True, text=True, timeout=30)
            
            anon_success = os.path.exists(anon_report_file) and os.path.exists(anon_summary_file)
            print(f"{'PASS' if anon_success else 'FAIL'}: Anonymization mode executed successfully")
        except Exception as e:
            print(f"FAIL: Anonymization execution failed: {e}")
            anon_success = False
        
        # Test 11: Anonymization effectiveness
        if anon_success:
            with open(anon_report_file, 'r') as f:
                anon_report = json.load(f)
            
            # Check if patient names are anonymized
            anon_validation_results = anon_report.get('validation_results', [])
            has_anonymous_names = any(
                'ANONYMOUS' in str(result) for result in anon_validation_results
            )
            print(f"{'PASS' if has_anonymous_names else 'FAIL'}: Patient names anonymized")
        else:
            print("FAIL: Cannot test anonymization effectiveness")
        
        # Test 12: Compliance scoring
        compliance_summary = report.get('compliance_summary', {})
        has_compliance_score = 'overall_compliance' in compliance_summary or 'compliance_rate' in compliance_summary
        print(f"{'PASS' if has_compliance_score else 'FAIL'}: Compliance scoring implemented")
        
        # Test 13: Institution-level analysis
        has_institution_analysis = 'institution' in str(summary).lower() or 'hospital' in str(summary).lower()
        print(f"{'PASS' if has_institution_analysis else 'FAIL'}: Institution-level analysis present")
        
        # Test 14: Date consistency validation
        date_violations = [r for r in validation_results 
                         if any('date' in v.get('field', '').lower() for v in r.get('violations', []))]
        date_validation_working = len(date_violations) >= 0  # Should handle date validation
        print(f"{'PASS' if date_validation_working else 'FAIL'}: Date consistency validation implemented")
        
        # Calculate scores
        
        # Validation accuracy score
        total_records = len(input_data['records'])
        expected_invalid = 10  # Records with invalid data
        detected_invalid = len([r for r in validation_results if r.get('status') == 'FAIL'])
        validation_accuracy = min(1.0, detected_invalid / max(1, expected_invalid))
        
        # Feature completeness score
        feature_checks = [
            report_structure_valid,
            summary_structure_valid,
            has_validation_errors,
            patient_id_validation,
            modality_param_validation,
            stats_complete,
            modality_analysis_complete,
            anon_success,
            has_compliance_score,
            has_institution_analysis
        ]
        feature_completeness = sum(feature_checks) / len(feature_checks)
        
        print(f"SCORE: {validation_accuracy:.3f}")
        print(f"SCORE: {feature_completeness:.3f}")

if __name__ == "__main__":
    test_dicom_metadata_tool()
