#!/usr/bin/env python3
import json
import argparse
import logging
import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator
from collections import defaultdict, Counter
import sys
import gc

class DICOMMetadataProcessor:
    def __init__(self, anonymize=False, validation_rules=None, batch_size=100):
        self.anonymize = anonymize
        self.validation_rules = validation_rules or {}
        self.patient_date_offsets = {}  # For consistent date shifting
        self.batch_size = batch_size
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def stream_records(self, input_path: str) -> Iterator[Dict]:
        """Stream records from JSON file to avoid loading everything into memory"""
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Process in batches
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                for record in batch:
                    yield record
                # Force garbage collection after each batch
                del batch
                gc.collect()
                
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            sys.exit(1)

    def load_validation_rules(self, rules_path: str) -> Dict:
        """Load validation rules from JSON file"""
        try:
            with open(rules_path, 'r') as f:
                rules = json.load(f)
            self.logger.info(f"Loaded validation rules from {rules_path}")
            return rules
        except Exception as e:
            self.logger.warning(f"Failed to load validation rules: {e}")
            return {}

    def anonymize_patient_data(self, record: Dict) -> Dict:
        """Anonymize patient identifiers with selective copying for memory efficiency"""
        if not self.anonymize:
            return record
        
        # Create a new dictionary with anonymized data
        anonymized = {}
        
        # Hash patient ID consistently
        patient_id = record.get('PatientID', '')
        hashed_id = hashlib.md5(patient_id.encode()).hexdigest()[:8]
        
        # Copy all fields, anonymizing sensitive ones
        for key, value in record.items():
            if key == 'PatientID':
                anonymized[key] = f"ANON_{hashed_id}"
            elif key == 'PatientName':
                anonymized[key] = f"ANONYMOUS_{hashed_id[:3]}"
            elif key == 'StudyDate':
                anonymized[key] = self._shift_date(value, patient_id)
            elif key == 'Series':
                # Handle series array with date shifting
                anonymized[key] = []
                for series in value:
                    anonymized_series = {}
                    for series_key, series_value in series.items():
                        if series_key == 'SeriesDate':
                            anonymized_series[series_key] = self._shift_date(series_value, patient_id)
                        else:
                            anonymized_series[series_key] = series_value
                    anonymized[key].append(anonymized_series)
            else:
                # Copy non-sensitive data as-is
                anonymized[key] = value
        
        return anonymized

    def _shift_date(self, date_str: str, patient_id: str) -> str:
        """Helper method to shift dates consistently per patient"""
        if not date_str:
            return date_str
            
        # Get consistent date offset for this patient
        if patient_id not in self.patient_date_offsets:
            self.patient_date_offsets[patient_id] = random.randint(-365, 365)
        
        date_offset = self.patient_date_offsets[patient_id]
        
        try:
            original_date = datetime.strptime(date_str, '%Y%m%d')
            shifted_date = original_date + timedelta(days=date_offset)
            return shifted_date.strftime('%Y%m%d')
        except ValueError:
            self.logger.warning(f"Invalid date format: {date_str}")
            return date_str

    def validate_record(self, record: Dict) -> Dict:
        """Validate a single DICOM record with nested series"""
        violations = []
        
        # Patient ID format validation
        patient_id = record.get('PatientID', '')
        if not patient_id or len(patient_id) < 3:
            violations.append({
                'field': 'PatientID',
                'severity': 'ERROR',
                'message': 'Patient ID missing or too short'
            })
        
        # Study-level validation
        study_date = record.get('StudyDate')
        if not study_date:
            violations.append({
                'field': 'StudyDate',
                'severity': 'ERROR',
                'message': 'Study date is missing'
            })
        
        # Series validation
        series_list = record.get('Series', [])
        if not series_list:
            violations.append({
                'field': 'Series',
                'severity': 'WARNING',
                'message': 'No series found in study'
            })
        
        for i, series in enumerate(series_list):
            series_prefix = f"Series[{i}]"
            
            # Date consistency validation
            series_date = series.get('SeriesDate')
            if study_date and series_date:
                try:
                    study_dt = datetime.strptime(study_date, '%Y%m%d')
                    series_dt = datetime.strptime(series_date, '%Y%m%d')
                    if study_dt > series_dt:
                        violations.append({
                            'field': f'{series_prefix}.SeriesDate',
                            'severity': 'ERROR',
                            'message': 'Study date is after series date'
                        })
                except ValueError as e:
                    violations.append({
                        'field': f'{series_prefix}.Date',
                        'severity': 'ERROR',
                        'message': f'Invalid date format: {e}'
                    })
            
            # Modality-specific validation
            modality = series.get('Modality', '')
            if modality == 'CT':
                slice_thickness = series.get('SliceThickness')
                if slice_thickness and (slice_thickness < 0.1 or slice_thickness > 10):
                    violations.append({
                        'field': f'{series_prefix}.SliceThickness',
                        'severity': 'WARNING',
                        'message': f'Unusual CT slice thickness: {slice_thickness}mm'
                    })
            
            elif modality == 'MRI':
                echo_time = series.get('EchoTime')
                if echo_time and (echo_time < 1 or echo_time > 500):
                    violations.append({
                        'field': f'{series_prefix}.EchoTime',
                        'severity': 'WARNING',
                        'message': f'Unusual MRI echo time: {echo_time}ms'
                    })
        
        return {
            'record_id': record.get('StudyInstanceUID', 'Unknown'),
            'patient_id': record.get('PatientID', 'Unknown'),
            'series_count': len(series_list),
            'violations': violations,
            'status': 'PASS' if not any(v['severity'] == 'ERROR' for v in violations) else 'FAIL'
        }

    def update_statistics(self, record: Dict, stats: Dict):
        """Update statistics incrementally to avoid storing all data"""
        # Institution distribution (study level)
        institution = record.get('InstitutionName', 'Unknown')
        stats['institution_distribution'][institution] += 1
        
        # Patient age (study level)
        if record.get('PatientAge'):
            try:
                age = int(record['PatientAge'].replace('Y', ''))
                stats['patient_ages'].append(age)
            except (ValueError, AttributeError):
                pass
        
        # Process series data
        series_list = record.get('Series', [])
        stats['total_series'] += len(series_list)
        
        for series in series_list:
            # Modality distribution
            modality = series.get('Modality', 'Unknown')
            stats['modality_distribution'][modality] += 1
            
            # Collect parameter values
            if series.get('SliceThickness'):
                stats['slice_thicknesses'].append(series['SliceThickness'])
            
            if series.get('EchoTime'):
                stats['echo_times'].append(series['EchoTime'])

    def calculate_final_statistics(self, stats: Dict) -> Dict:
        """Calculate final statistics from collected data"""
        final_stats = {
            'total_records': stats['total_records'],
            'total_series': stats['total_series'],
            'modality_distribution': dict(stats['modality_distribution']),
            'institution_distribution': dict(stats['institution_distribution']),
            'parameter_stats': {}
        }
        
        # Calculate parameter statistics
        if stats['slice_thicknesses']:
            values = stats['slice_thicknesses']
            final_stats['parameter_stats']['slice_thickness'] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        if stats['echo_times']:
            values = stats['echo_times']
            final_stats['parameter_stats']['echo_time'] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        if stats['patient_ages']:
            values = stats['patient_ages']
            final_stats['parameter_stats']['patient_age'] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        return final_stats

    def process_data(self, input_path: str, output_report: str, output_summary: str, validation_rules_path: Optional[str] = None):
        """Main processing pipeline with streaming"""
        if validation_rules_path:
            self.validation_rules = self.load_validation_rules(validation_rules_path)
        
        # Initialize statistics collectors
        stats = {
            'total_records': 0,
            'total_series': 0,
            'modality_distribution': Counter(),
            'institution_distribution': Counter(),
            'slice_thicknesses': [],
            'echo_times': [],
            'patient_ages': []
        }
        
        validation_results = []
        processed_count = 0
        
        # Stream and process records
        for record in self.stream_records(input_path):
            # Anonymize if requested (selective copying)
            processed_record = self.anonymize_patient_data(record)
            
            # Validate record
            validation_result = self.validate_record(processed_record)
            validation_results.append(validation_result)
            
            # Update statistics incrementally
            self.update_statistics(processed_record, stats)
            stats['total_records'] += 1
            
            processed_count += 1
            if processed_count % self.batch_size == 0:
                self.logger.info(f"Processed {processed_count} records...")
                gc.collect()  # Force garbage collection periodically
        
        # Calculate final statistics
        final_statistics = self.calculate_final_statistics(stats)
        
        # Save validation report
        validation_report = {
            'summary': {
                'total_records': len(validation_results),
                'total_series': sum(r.get('series_count', 0) for r in validation_results),
                'passed': sum(1 for r in validation_results if r['status'] == 'PASS'),
                'failed': sum(1 for r in validation_results if r['status'] == 'FAIL')
            },
            'results': validation_results
        }
        
        with open(output_report, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        # Save statistical summary
        with open(output_summary, 'w') as f:
            json.dump(final_statistics, f, indent=2, default=str)
        
        self.logger.info(f"Processing complete. Processed {processed_count} records.")
        self.logger.info(f"Report saved to {output_report}, summary to {output_summary}")

def main():
    parser = argparse.ArgumentParser(description='DICOM Metadata Extraction and Validation Tool')
    parser.add_argument('--input-data', required=True, help='JSON file containing DICOM metadata')
    parser.add_argument('--output-report', required=True, help='Path for validation report (JSON)')
    parser.add_argument('--output-summary', required=True, help='Path for statistical summary (JSON)')
    parser.add_argument('--anonymize', action='store_true', help='Anonymize patient identifiers')
    parser.add_argument('--validation-rules', help='JSON file containing validation rules')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing (default: 100)')
    
    args = parser.parse_args()
    
    processor = DICOMMetadataProcessor(anonymize=args.anonymize, batch_size=args.batch_size)
    processor.process_data(
        args.input_data,
        args.output_report,
        args.output_summary,
        args.validation_rules
    )

if __name__ == '__main__':
    main()
