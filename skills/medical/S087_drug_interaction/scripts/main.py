#!/usr/bin/env python3
"""
Drug Interaction Analysis Tool
Analyzes prescription data to identify potential drug interactions and generate safety reports.
"""

import argparse
import json
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DrugInteractionAnalyzer:
    def __init__(self, custom_severity_scores=None):
        # Brand name to generic name mapping
        self.drug_name_mapping = {
            'coumadin': 'warfarin', 'jantoven': 'warfarin',
            'advil': 'ibuprofen', 'motrin': 'ibuprofen', 'nuprin': 'ibuprofen',
            'aspirin': 'aspirin', 'bayer': 'aspirin', 'bufferin': 'aspirin',
            'glucophage': 'metformin', 'fortamet': 'metformin', 'glumetza': 'metformin',
            'novolog': 'insulin', 'humalog': 'insulin', 'lantus': 'insulin', 'levemir': 'insulin',
            'lasix': 'furosemide', 'prinivil': 'lisinopril', 'zestril': 'lisinopril',
            'zocor': 'simvastatin', 'vytorin': 'simvastatin', 'norvasc': 'amlodipine',
            'prilosec': 'omeprazole', 'losec': 'omeprazole', 'plavix': 'clopidogrel',
            'lanoxin': 'digoxin', 'digitek': 'digoxin', 'k-dur': 'potassium', 'klor-con': 'potassium',
        }
        
        # Drug interaction database
        self.interaction_db = {
            ('warfarin', 'aspirin'): 'severe',
            ('warfarin', 'ibuprofen'): 'severe', 
            ('metformin', 'furosemide'): 'moderate',
            ('lisinopril', 'potassium'): 'moderate',
            ('simvastatin', 'amlodipine'): 'minor',
            ('omeprazole', 'clopidogrel'): 'moderate',
            ('digoxin', 'furosemide'): 'severe',
            ('insulin', 'metformin'): 'minor'
        }
        
        # Use custom severity scores if provided, otherwise use defaults
        self.severity_scores = custom_severity_scores or {'severe': 3, 'moderate': 2, 'minor': 1}
        
    def normalize_drug_name(self, drug_name):
        """Convert brand names to generic names and normalize."""
        normalized = drug_name.lower().strip()
        if normalized in self.drug_name_mapping:
            return self.drug_name_mapping[normalized]
        for brand_name, generic_name in self.drug_name_mapping.items():
            if brand_name in normalized or normalized in brand_name:
                return generic_name
        return normalized
    
    def load_prescription_data(self, filepath):
        """Load prescription data from CSV file."""
        try:
            df = pd.read_csv(filepath)
            date_formats = ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y']
            
            for date_format in date_formats:
                try:
                    df['prescription_date'] = pd.to_datetime(df['prescription_date'], format=date_format)
                    logger.info(f"Successfully parsed dates using format: {date_format}")
                    break
                except ValueError:
                    continue
            else:
                df['prescription_date'] = pd.to_datetime(df['prescription_date'], dayfirst=True)
                logger.info("Used pandas automatic date parsing with day-first format")
            
            logger.info(f"Loaded {len(df)} prescription records")
            return df
        except Exception as e:
            logger.error(f"Error loading prescription data: {e}")
            raise
    
    def find_concurrent_medications(self, df, window_days=30):
        """Find medications prescribed within the specified window for each patient."""
        concurrent_meds = defaultdict(list)
        df = df.copy()
        df['drug_name_normalized'] = df['drug_name'].apply(self.normalize_drug_name)
        
        logger.info("Sample drug name mappings:")
        sample_mappings = df[['drug_name', 'drug_name_normalized']].drop_duplicates().head(10)
        for _, row in sample_mappings.iterrows():
            logger.info(f"  {row['drug_name']} -> {row['drug_name_normalized']}")
        
        for patient_id in df['patient_id'].unique():
            patient_data = df[df['patient_id'] == patient_id].sort_values('prescription_date')
            
            if len(patient_data) < 2:
                continue
            
            unique_drugs = patient_data['drug_name_normalized'].unique()
            
            for i, drug1 in enumerate(unique_drugs):
                for drug2 in unique_drugs[i+1:]:
                    drug1_prescriptions = patient_data[patient_data['drug_name_normalized'] == drug1]
                    drug2_prescriptions = patient_data[patient_data['drug_name_normalized'] == drug2]
                    
                    min_diff = float('inf')
                    best_combination = None
                    
                    for _, row1 in drug1_prescriptions.iterrows():
                        date_diffs = np.abs((drug2_prescriptions['prescription_date'] - row1['prescription_date']).dt.days)
                        min_idx = date_diffs.idxmin()
                        min_diff_candidate = date_diffs.loc[min_idx]
                        
                        if min_diff_candidate <= window_days and min_diff_candidate < min_diff:
                            min_diff = min_diff_candidate
                            row2 = drug2_prescriptions.loc[min_idx]
                            best_combination = {
                                'drug1': drug1, 'drug2': drug2,
                                'date1': row1['prescription_date'], 'date2': row2['prescription_date'],
                                'dosage1': row1['dosage'], 'dosage2': row2['dosage'],
                                'original_drug1': row1['drug_name'], 'original_drug2': row2['drug_name']
                            }
                    
                    if best_combination:
                        concurrent_meds[patient_id].append(best_combination)
        
        return concurrent_meds
    
    def check_interactions(self, concurrent_meds):
        """Check for drug interactions in concurrent medications."""
        interactions = defaultdict(list)
        total_pairs_checked = 0
        interactions_found = 0
        
        for patient_id, med_pairs in concurrent_meds.items():
            seen_pairs = set()
            
            for pair in med_pairs:
                drug1, drug2 = pair['drug1'], pair['drug2']
                total_pairs_checked += 1
                
                pair_key = tuple(sorted([drug1, drug2]))
                
                if pair_key in seen_pairs:
                    continue
                
                seen_pairs.add(pair_key)
                
                if pair_key in self.interaction_db:
                    interaction_severity = self.interaction_db[pair_key]
                    interactions_found += 1
                    interactions[patient_id].append({
                        'drug1': drug1, 'drug2': drug2,
                        'original_drug1': pair['original_drug1'], 'original_drug2': pair['original_drug2'],
                        'severity': interaction_severity, 'score': self.severity_scores[interaction_severity],
                        'date1': pair['date1'], 'date2': pair['date2'],
                        'dosage1': pair['dosage1'], 'dosage2': pair['dosage2']
                    })
        
        logger.info(f"Checked {total_pairs_checked} drug pairs, found {interactions_found} interactions")
        return interactions
    
    def calculate_risk_scores(self, interactions):
        """Calculate risk scores for each patient."""
        risk_scores = {}
        for patient_id, patient_interactions in interactions.items():
            total_score = sum(interaction['score'] for interaction in patient_interactions)
            risk_scores[patient_id] = total_score
        logger.info(f"Calculated risk scores for {len(risk_scores)} patients")
        return risk_scores
    
    def filter_high_risk_patients(self, interactions, risk_scores, threshold):
        """Filter patients above risk threshold."""
        high_risk_patients = {}
        for patient_id, score in risk_scores.items():
            if score >= threshold:
                high_risk_patients[patient_id] = {
                    'risk_score': score,
                    'interactions': interactions[patient_id]
                }
        logger.info(f"Found {len(high_risk_patients)} patients above risk threshold {threshold}")
        return high_risk_patients
    
    def save_high_risk_report(self, high_risk_patients, output_path):
        """Save high-risk patients report."""
        with open(output_path, 'w') as f:
            json.dump({
                'analysis_date': datetime.now().isoformat(),
                'high_risk_patients': {
                    str(pid): {
                        'risk_score': data['risk_score'],
                        'interactions': [{
                            'drug1_generic': i['drug1'], 'drug2_generic': i['drug2'],
                            'drug1_original': i['original_drug1'], 'drug2_original': i['original_drug2'],
                            'severity': i['severity'], 'score': i['score'],
                            'date1': i['date1'].strftime('%Y-%m-%d'), 'date2': i['date2'].strftime('%Y-%m-%d'),
                            'dosage1': i['dosage1'], 'dosage2': i['dosage2']
                        } for i in data['interactions']]
                    } for pid, data in high_risk_patients.items()
                }
            }, f, indent=2)
        logger.info(f"High-risk patients report saved to {output_path}")
    
    def save_csv_report(self, interactions, output_path):
        """Save CSV report of all interactions."""
        rows = []
        for patient_id, patient_interactions in interactions.items():
            for interaction in patient_interactions:
                rows.append({
                    'patient_id': patient_id,
                    'drug1_generic': interaction['drug1'], 'drug2_generic': interaction['drug2'],
                    'drug1_original': interaction['original_drug1'], 'drug2_original': interaction['original_drug2'],
                    'severity': interaction['severity'], 'risk_score': interaction['score'],
                    'date1': interaction['date1'].strftime('%Y-%m-%d'), 'date2': interaction['date2'].strftime('%Y-%m-%d'),
                    'dosage1': interaction['dosage1'], 'dosage2': interaction['dosage2']
                })
        
        with open(output_path, 'w', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            else:
                headers = ['patient_id', 'drug1_generic', 'drug2_generic', 'drug1_original', 
                          'drug2_original', 'severity', 'risk_score', 'date1', 'date2', 'dosage1', 'dosage2']
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
        
        logger.info(f"CSV report saved to {output_path} with {len(rows)} interaction records")
    
    def create_risk_histogram(self, risk_scores, output_path):
        """Create histogram of patient risk scores."""
        if not risk_scores:
            logger.warning("No risk scores to plot - no interactions were found")
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, 'No Drug Interactions Found\nNo Risk Scores to Display', 
                    ha='center', va='center', transform=plt.gca().transAxes, fontsize=16)
            plt.title('Distribution of Patient Risk Scores')
            plt.xlabel('Patient Risk Score')
            plt.ylabel('Number of Patients')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Empty risk score plot saved to {output_path}")
            return
        
        scores = list(risk_scores.values())
        plt.figure(figsize=(10, 6))
        plt.hist(scores, bins=min(20, len(set(scores))), edgecolor='black', alpha=0.7)
        plt.xlabel('Patient Risk Score')
        plt.ylabel('Number of Patients')
        plt.title('Distribution of Patient Risk Scores')
        plt.grid(True, alpha=0.3)
        
        mean_score = np.mean(scores)
        plt.axvline(mean_score, color='red', linestyle='--', label=f'Mean Score: {mean_score:.1f}')
        plt.legend()
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Risk score histogram saved to {output_path} ({len(scores)} patients)")

def main():
    parser = argparse.ArgumentParser(description='Drug Interaction Analysis Tool')
    parser.add_argument('input_file', help='Input CSV file with prescription data')
    parser.add_argument('--output-dir', '-o', default='output', help='Output directory for reports')
    parser.add_argument('--window-days', '-w', type=int, default=30, help='Days window for concurrent medications')
    parser.add_argument('--severe-score', type=int, default=3, help='Score for severe interactions')
    parser.add_argument('--moderate-score', type=int, default=2, help='Score for moderate interactions')
    parser.add_argument('--minor-score', type=int, default=1, help='Score for minor interactions')
    parser.add_argument('--risk-threshold', '-t', type=float, help='Risk score threshold for high-risk patient report')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Custom severity scores
    custom_scores = {
        'severe': args.severe_score,
        'moderate': args.moderate_score,
        'minor': args.minor_score
    }
    
    analyzer = DrugInteractionAnalyzer(custom_scores)
    
    try:
        logger.info("Loading prescription data...")
        df = analyzer.load_prescription_data(args.input_file)
        
        logger.info("Finding concurrent medications...")
        concurrent_meds = analyzer.find_concurrent_medications(df, args.window_days)
        
        logger.info("Checking for drug interactions...")
        interactions = analyzer.check_interactions(concurrent_meds)
        
        logger.info("Calculating risk scores...")
        risk_scores = analyzer.calculate_risk_scores(interactions)
        
        # Generate standard outputs
        csv_path = output_dir / 'interactions.csv'
        hist_path = output_dir / 'risk_distribution.png'
        
        analyzer.save_csv_report(interactions, csv_path)
        analyzer.create_risk_histogram(risk_scores, hist_path)
        
        # Generate high-risk report if threshold specified
        if args.risk_threshold:
            high_risk_patients = analyzer.filter_high_risk_patients(interactions, risk_scores, args.risk_threshold)
            high_risk_path = output_dir / 'high_risk_patients.json'
            analyzer.save_high_risk_report(high_risk_patients, high_risk_path)
        
        logger.info("Analysis complete!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
