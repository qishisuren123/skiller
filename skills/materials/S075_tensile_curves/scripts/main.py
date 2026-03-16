import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
import math
import logging

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('tensile_analysis.log')
        ]
    )

def validate_parameters(points, max_stress, max_strain):
    """Validate input parameters and warn about potential issues"""
    warnings = []
    
    if points < 50:
        warnings.append(f"Very few data points ({points}). Recommend at least 50 points for reliable results.")
    
    if points < 20:
        warnings.append("Extremely low point count may cause calculation failures.")
    
    if max_strain < 0.01:
        warnings.append(f"Low maximum strain ({max_strain}). May not capture full material behavior.")
    
    if max_strain < 0.002:
        warnings.append("Maximum strain below 0.2% offset - yield strength calculation will fail.")
    
    if max_stress <= 0:
        warnings.append("Maximum stress must be positive.")
    
    if max_stress > 2000:
        warnings.append(f"Very high maximum stress ({max_stress} MPa). Check if this is realistic for your material.")
    
    for warning in warnings:
        logging.warning(warning)
    
    return len(warnings) == 0

def generate_tensile_curve(n_points, max_stress, max_strain):
    """Generate a realistic tensile test stress-strain curve"""
    logging.info(f"Generating tensile curve: {n_points} points, max_stress={max_stress} MPa, max_strain={max_strain}")
    
    if n_points <= 0:
        raise ValueError("Number of points must be positive")
    
    strain = np.linspace(0, max_strain, n_points)
    stress = np.zeros_like(strain)
    
    # Handle very small strain ranges (brittle materials)
    if max_strain <= 0.005:
        logging.info("Detected brittle material behavior - using linear-only model")
        # Simple linear relationship for brittle materials
        E = min(200000, max_stress / max_strain * 2)  # Adaptive modulus
        stress = E * strain
        # Cap at max_stress
        stress = np.minimum(stress, max_stress)
        return strain, stress
    
    # Standard ductile material behavior
    E = 200000  # Young's modulus in MPa
    yield_strain = min(0.002, max_strain * 0.3)  # More flexible yield strain
    yield_stress = min(E * yield_strain, max_stress * 0.8)  # Ensure realistic yield
    
    logging.debug(f"Target yield strain: {yield_strain}, yield stress: {yield_stress} MPa")
    
    # Elastic region
    elastic_mask = strain <= yield_strain
    stress[elastic_mask] = E * strain[elastic_mask]
    
    # Plastic region with strain hardening
    plastic_mask = strain > yield_strain
    if np.any(plastic_mask):
        plastic_strain = strain[plastic_mask] - yield_strain
        stress[plastic_mask] = yield_stress + 800 * plastic_strain**0.2
        logging.debug(f"Generated {np.sum(plastic_mask)} points in plastic region")
    else:
        logging.warning("No plastic region in generated curve - all deformation is elastic")
    
    # Scale to match max_stress
    if np.max(stress) > 0:
        scale_factor = max_stress / np.max(stress)
        stress = stress * scale_factor
        logging.debug(f"Applied stress scaling factor: {scale_factor:.3f}")
    
    return strain, stress

def calculate_elastic_modulus(strain, stress, max_strain_fraction=0.2):
    """Calculate Young's modulus from linear portion"""
    logging.info("Calculating elastic modulus")
    
    max_strain_for_fit = np.max(strain) * max_strain_fraction
    linear_mask = (strain > 0.0001) & (strain <= max_strain_for_fit)
    
    n_linear_points = np.sum(linear_mask)
    logging.debug(f"Using {n_linear_points} points for elastic modulus calculation")
    
    if n_linear_points < 2:
        logging.error("Insufficient points for elastic modulus calculation")
        return float('nan')
    
    if n_linear_points < 5:
        logging.warning(f"Very few points ({n_linear_points}) for elastic modulus - results may be unreliable")
    
    linear_strain = strain[linear_mask]
    linear_stress = stress[linear_mask]
    
    elastic_modulus = np.sum(linear_strain * linear_stress) / np.sum(linear_strain**2)
    
    logging.info(f"Calculated elastic modulus: {elastic_modulus:.1f} MPa")
    
    if elastic_modulus < 1000 or elastic_modulus > 1000000:
        logging.warning(f"Elastic modulus ({elastic_modulus:.1f} MPa) seems unrealistic")
    
    return elastic_modulus

def calculate_yield_strength(strain, stress, elastic_modulus, offset=0.002):
    """Calculate 0.2% offset yield strength"""
    logging.info("Calculating yield strength using 0.2% offset method")
    
    if math.isnan(elastic_modulus) or elastic_modulus <= 0:
        logging.error("Cannot calculate yield strength - invalid elastic modulus")
        return float('nan')
    
    max_strain = np.max(strain)
    if offset >= max_strain:
        logging.error(f"Offset strain ({offset}) >= maximum strain ({max_strain}) - cannot calculate yield strength")
        return float('nan')
    
    valid_mask = strain >= offset
    n_valid_points = np.sum(valid_mask)
    
    logging.debug(f"Using {n_valid_points} points beyond offset strain for yield calculation")
    
    if n_valid_points < 2:
        logging.error("Insufficient points beyond offset strain for yield strength calculation")
        return float('nan')
    
    if n_valid_points < 5:
        logging.warning(f"Very few points ({n_valid_points}) for yield calculation - results may be unreliable")
    
    valid_strain = strain[valid_mask]
    valid_stress = stress[valid_mask]
    
    offset_line = elastic_modulus * (valid_strain - offset)
    differences = np.abs(valid_stress - offset_line)
    min_idx = np.argmin(differences)
    
    intersection_stress = valid_stress[min_idx]
    intersection_strain = valid_strain[min_idx]
    
    logging.info(f"Calculated yield strength: {intersection_stress:.1f} MPa at strain {intersection_strain:.6f}")
    
    return intersection_stress

def safe_float(value):
    """Convert numpy values to JSON-safe Python floats"""
    if isinstance(value, (np.integer, np.floating)):
        value = value.item()
    
    if math.isnan(value) or math.isinf(value):
        return None
    
    return float(value)

def main():
    parser = argparse.ArgumentParser(description='Analyze tensile test stress-strain curves')
    parser.add_argument('--points', type=int, default=1000, help='Number of data points')
    parser.add_argument('--max_stress', type=float, default=500, help='Maximum stress (MPa)')
    parser.add_argument('--max_strain', type=float, default=0.25, help='Maximum strain')
    parser.add_argument('--plot_file', type=str, default='tensile_curve.png', help='Output plot filename')
    parser.add_argument('--results_file', type=str, default='results.json', help='Output JSON filename')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logging.info("Starting tensile test analysis")
    logging.info(f"Parameters: points={args.points}, max_stress={args.max_stress}, max_strain={args.max_strain}")
    
    if not validate_parameters(args.points, args.max_stress, args.max_strain):
        logging.warning("Parameter validation failed - results may be unreliable")
    
    try:
        strain, stress = generate_tensile_curve(args.points, args.max_stress, args.max_strain)
        
        if len(strain) == 0 or len(stress) == 0:
            raise ValueError("Generated curve has no data points")
        
        elastic_modulus = calculate_elastic_modulus(strain, stress)
        yield_strength = calculate_yield_strength(strain, stress, elastic_modulus)
        ultimate_tensile_strength = np.max(stress)
        strain_at_failure = strain[-1]
        
        logging.info(f"Creating plot: {args.plot_file}")
        plt.figure(figsize=(10, 6))
        plt.plot(strain, stress, 'b-', linewidth=2, label='Stress-Strain Curve')
        
        offset = 0.002
        if not math.isnan(elastic_modulus) and args.max_strain > offset:
            offset_start = offset
            offset_end = min(offset + 0.008, args.max_strain * 0.8)
            
            if offset_end > offset_start:
                offset_strain = np.linspace(offset_start, offset_end, 100)
                offset_stress = elastic_modulus * (offset_strain - offset)
                plt.plot(offset_strain, offset_stress, 'r--', alpha=0.7, label='0.2% Offset Line')
        
        uts_idx = np.argmax(stress)
        plt.plot(strain[uts_idx], ultimate_tensile_strength, 'ro', markersize=8, 
                 label=f'UTS: {ultimate_tensile_strength:.1f} MPa')
        
        if not math.isnan(yield_strength):
            yield_idx = np.argmin(np.abs(stress - yield_strength))
            plt.plot(strain[yield_idx], yield_strength, 'go', markersize=8, 
                     label=f'Yield: {yield_strength:.1f} MPa')
        
        plt.xlabel('Strain')
        plt.ylabel('Stress (MPa)')
        plt.title('Tensile Test Stress-Strain Curve')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(args.plot_file, dpi=300, bbox_inches='tight')
        logging.info(f"Plot saved to {args.plot_file}")
        
        results = {
            'elastic_modulus': safe_float(elastic_modulus),
            'yield_strength': safe_float(yield_strength),
            'ultimate_tensile_strength': safe_float(ultimate_tensile_strength),
            'strain_at_failure': safe_float(strain_at_failure),
            'analysis_parameters': {
                'points': args.points,
                'max_stress': args.max_stress,
                'max_strain': args.max_strain
            }
        }
        
        with open(args.results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logging.info(f"Results saved to {args.results_file}")
        
        print(f"Analysis complete!")
        print(f"Elastic Modulus: {elastic_modulus:.1f} MPa" if not math.isnan(elastic_modulus) else "Elastic Modulus: Could not calculate")
        print(f"Yield Strength: {yield_strength:.1f} MPa" if not math.isnan(yield_strength) else "Yield Strength: Could not calculate")
        print(f"Ultimate Tensile Strength: {ultimate_tensile_strength:.1f} MPa")
        
        logging.info("Analysis completed successfully")
        
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
