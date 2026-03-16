#!/usr/bin/env python3
import argparse
import json
import numpy as np
import logging
from typing import Dict, List, Tuple, Any
import sys
from pathlib import Path

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze protein structures for disulfide bonds'
    )
    parser.add_argument('--input', '--pdb', required=True,
                       help='Input PDB structure data (JSON format)')
    parser.add_argument('--output', '--out', required=True,
                       help='Output JSON file for analysis results')
    parser.add_argument('--distance-cutoff', '--cutoff', type=float, default=2.5,
                       help='Maximum distance threshold for disulfide bonds (Å)')
    parser.add_argument('--angle-tolerance', '--tolerance', type=float, default=20.0,
                       help='Angular tolerance for bond geometry validation (degrees)')
    parser.add_argument('--energy-model', '--model', choices=['simple', 'advanced'],
                       default='simple', help='Energy calculation model')
    return parser.parse_args()

def convert_numpy_to_serializable(obj):
    """Recursively convert numpy arrays and other non-serializable objects to JSON-compatible types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_serializable(item) for item in obj]
    else:
        return obj

class DisulfideBondAnalyzer:
    def __init__(self, distance_cutoff=2.5, angle_tolerance=20.0, energy_model='simple'):
        self.distance_cutoff = distance_cutoff
        self.angle_tolerance = angle_tolerance
        self.energy_model = energy_model
        self.expected_css_angle = 104.0  # Expected C-S-S bond angle in degrees
        self.logger = logging.getLogger(__name__)
        
    def load_pdb_data(self, filepath: str) -> Dict:
        """Load PDB structure data from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.logger.info(f"Loaded PDB data from {filepath}")
            return data
        except Exception as e:
            self.logger.error(f"Error loading PDB data: {e}")
            raise
    
    def extract_cysteine_residues(self, pdb_data: Dict) -> List[Dict]:
        """Extract cysteine residues with sulfur atoms from PDB data."""
        cysteines = []
        
        for chain_id, chain_data in pdb_data.get('chains', {}).items():
            for residue in chain_data.get('residues', []):
                if residue.get('name') == 'CYS':
                    # Find sulfur atom
                    sulfur_atom = None
                    carbon_atom = None
                    
                    for atom in residue.get('atoms', []):
                        if atom.get('name') == 'SG':  # Sulfur gamma
                            sulfur_atom = atom
                        elif atom.get('name') == 'CB':  # Carbon beta
                            carbon_atom = atom
                    
                    if sulfur_atom and carbon_atom:
                        cys_info = {
                            'chain_id': chain_id,
                            'residue_number': residue.get('number'),
                            'sulfur_coords': np.array([
                                sulfur_atom.get('x', 0),
                                sulfur_atom.get('y', 0),
                                sulfur_atom.get('z', 0)
                            ]),
                            'carbon_coords': np.array([
                                carbon_atom.get('x', 0),
                                carbon_atom.get('y', 0),
                                carbon_atom.get('z', 0)
                            ])
                        }
                        cysteines.append(cys_info)
        
        self.logger.info(f"Found {len(cysteines)} cysteine residues")
        return cysteines
    
    def calculate_distance(self, coords1: np.ndarray, coords2: np.ndarray) -> float:
        """Calculate Euclidean distance between two coordinate sets."""
        return np.linalg.norm(coords1 - coords2)
    
    def calculate_angle(self, point1: np.ndarray, vertex: np.ndarray, point2: np.ndarray) -> float:
        """Calculate angle in degrees between three points (vertex is the middle point)."""
        # Create vectors from vertex to the other two points
        vec1 = point1 - vertex
        vec2 = point2 - vertex
        
        # Calculate vector magnitudes
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        # Check for zero-length vectors
        if norm1 < 1e-10 or norm2 < 1e-10:
            self.logger.warning("Zero-length vector encountered in angle calculation")
            return np.nan
        
        # Calculate angle using dot product
        cos_angle = np.dot(vec1, vec2) / (norm1 * norm2)
        
        # Clamp to avoid numerical errors
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        # Check for NaN values
        if np.isnan(cos_angle):
            self.logger.warning("NaN encountered in angle calculation")
            return np.nan
        
        # Convert to degrees
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
    def validate_bond_geometry(self, bond: Dict) -> Dict:
        """Validate geometric constraints for a potential disulfide bond."""
        cys1 = bond['cys1']
        cys2 = bond['cys2']
        
        # Calculate C-S-S angles for both cysteines
        angle1 = self.calculate_angle(
            cys1['carbon_coords'], 
            cys1['sulfur_coords'], 
            cys2['sulfur_coords']
        )
        
        angle2 = self.calculate_angle(
            cys2['carbon_coords'], 
            cys2['sulfur_coords'], 
            cys1['sulfur_coords']
        )
        
        # Handle NaN angles
        if np.isnan(angle1) or np.isnan(angle2):
            self.logger.warning("Invalid angles calculated for bond geometry")
            return {
                'css_angle1': None,
                'css_angle2': None,
                'angle1_deviation': None,
                'angle2_deviation': None,
                'angle1_valid': False,
                'angle2_valid': False,
                'geometry_valid': False,
                'error': 'Invalid angle calculation'
            }
        
        # Check if angles are within tolerance
        angle1_valid = abs(angle1 - self.expected_css_angle) <= self.angle_tolerance
        angle2_valid = abs(angle2 - self.expected_css_angle) <= self.angle_tolerance
        
        geometry_valid = angle1_valid and angle2_valid
        
        validation_info = {
            'css_angle1': float(angle1),
            'css_angle2': float(angle2),
            'angle1_deviation': float(abs(angle1 - self.expected_css_angle)),
            'angle2_deviation': float(abs(angle2 - self.expected_css_angle)),
            'angle1_valid': angle1_valid,
            'angle2_valid': angle2_valid,
            'geometry_valid': geometry_valid
        }
        
        return validation_info
    
    def detect_potential_bonds(self, cysteines: List[Dict]) -> List[Dict]:
        """Detect potential disulfide bonds based on distance cutoff."""
        potential_bonds = []
        
        for i in range(len(cysteines)):
            for j in range(i + 1, len(cysteines)):
                cys1, cys2 = cysteines[i], cysteines[j]
                
                # Skip if same residue
                if (cys1['chain_id'] == cys2['chain_id'] and 
                    cys1['residue_number'] == cys2['residue_number']):
                    continue
                
                distance = self.calculate_distance(
                    cys1['sulfur_coords'], cys2['sulfur_coords']
                )
                
                if distance <= self.distance_cutoff:
                    bond_info = {
                        'cys1': cys1,
                        'cys2': cys2,
                        'distance': float(distance),
                        'is_inter_chain': cys1['chain_id'] != cys2['chain_id']
                    }
                    potential_bonds.append(bond_info)
        
        self.logger.info(f"Found {len(potential_bonds)} potential disulfide bonds")
        return potential_bonds
    
    def analyze_bonds(self, potential_bonds: List[Dict]) -> List[Dict]:
        """Analyze potential bonds with geometric validation."""
        analyzed_bonds = []
        
        for bond in potential_bonds:
            # Add geometric validation
            geometry = self.validate_bond_geometry(bond)
            
            # Create complete bond analysis
            bond_analysis = {
                'residue1': {
                    'chain': bond['cys1']['chain_id'],
                    'number': bond['cys1']['residue_number'],
                    'sulfur_coords': bond['cys1']['sulfur_coords'],
                    'carbon_coords': bond['cys1']['carbon_coords']
                },
                'residue2': {
                    'chain': bond['cys2']['chain_id'],
                    'number': bond['cys2']['residue_number'],
                    'sulfur_coords': bond['cys2']['sulfur_coords'],
                    'carbon_coords': bond['cys2']['carbon_coords']
                },
                'distance': bond['distance'],
                'is_inter_chain': bond['is_inter_chain'],
                'geometry': geometry,
                'validated': geometry['geometry_valid']
            }
            
            analyzed_bonds.append(bond_analysis)
        
        # Log validation statistics
        valid_bonds = sum(1 for bond in analyzed_bonds if bond['validated'])
        self.logger.info(f"Geometric validation: {valid_bonds}/{len(analyzed_bonds)} bonds passed")
        
        return analyzed_bonds

def main():
    setup_logging()
    args = parse_arguments()
    
    analyzer = DisulfideBondAnalyzer(
        distance_cutoff=args.distance_cutoff,
        angle_tolerance=args.angle_tolerance,
        energy_model=args.energy_model
    )
    
    try:
        # Load and analyze PDB data
        pdb_data = analyzer.load_pdb_data(args.input)
        cysteines = analyzer.extract_cysteine_residues(pdb_data)
        potential_bonds = analyzer.detect_potential_bonds(cysteines)
        analyzed_bonds = analyzer.analyze_bonds(potential_bonds)
        
        # Calculate summary statistics
        valid_bonds = [bond for bond in analyzed_bonds if bond['validated']]
        inter_chain_bonds = [bond for bond in valid_bonds if bond['is_inter_chain']]
        intra_chain_bonds = [bond for bond in valid_bonds if not bond['is_inter_chain']]
        
        results = {
            'analysis_parameters': {
                'distance_cutoff': args.distance_cutoff,
                'angle_tolerance': args.angle_tolerance,
                'energy_model': args.energy_model,
                'expected_css_angle': analyzer.expected_css_angle
            },
            'summary': {
                'total_cysteines': len(cysteines),
                'potential_bonds': len(potential_bonds),
                'validated_bonds': len(valid_bonds),
                'inter_chain_bonds': len(inter_chain_bonds),
                'intra_chain_bonds': len(intra_chain_bonds)
            },
            'bonds': analyzed_bonds
        }
        
        # Convert numpy arrays to JSON-serializable format
        results_serializable = convert_numpy_to_serializable(results)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(results_serializable, f, indent=2)
        
        logging.info(f"Analysis complete. Results saved to {args.output}")
        
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
