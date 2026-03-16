#!/usr/bin/env python3
import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def bin_directions(directions):
    """Bin wind directions into 16 compass sectors"""
    sector_names = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                   'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    
    # Adjust directions to center bins on cardinal directions
    adjusted_dirs = (directions + 11.25) % 360
    sector_indices = (adjusted_dirs // 22.5).astype(int)
    
    return sector_indices, sector_names

def classify_wind_speeds(speeds):
    """Classify wind speeds into categories"""
    categories = np.zeros_like(speeds, dtype=int)
    categories[(speeds >= 0) & (speeds < 2)] = 0  # Calm
    categories[(speeds >= 2) & (speeds < 5)] = 1  # Light
    categories[(speeds >= 5) & (speeds < 8)] = 2  # Moderate
    categories[speeds >= 8] = 3  # Strong
    
    category_names = ['Calm', 'Light', 'Moderate', 'Strong']
    return categories, category_names

def auto_detect_columns(df, speed_col, direction_col):
    """Auto-detect column names if defaults not found"""
    available_cols = [col.lower() for col in df.columns]
    
    # Common speed column patterns
    speed_patterns = ['wind_speed_ms', 'windspeed', 'wind_speed', 'speed', 'ws', 'u_wind', 'wind_vel']
    direction_patterns = ['wind_direction_deg', 'winddirection', 'wind_direction', 'direction', 'dir', 'wd', 'wind_dir']
    
    detected_speed = None
    detected_direction = None
    
    # Try to find speed column
    if speed_col.lower() not in available_cols:
        for pattern in speed_patterns:
            for col in df.columns:
                if pattern in col.lower():
                    detected_speed = col
                    break
            if detected_speed:
                break
    else:
        detected_speed = speed_col
    
    # Try to find direction column
    if direction_col.lower() not in available_cols:
        for pattern in direction_patterns:
            for col in df.columns:
                if pattern in col.lower():
                    detected_direction = col
                    break
            if detected_direction:
                break
    else:
        detected_direction = direction_col
    
    return detected_speed, detected_direction

def load_data_from_csv(csv_file, speed_col, direction_col):
    """Load wind data from CSV file"""
    try:
        df = pd.read_csv(csv_file)
        logging.info(f"Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")
        
        # Auto-detect columns if needed
        detected_speed, detected_direction = auto_detect_columns(df, speed_col, direction_col)
        
        if detected_speed is None:
            available_cols_str = "', '".join(df.columns)
            raise ValueError(f"Speed column '{speed_col}' not found and could not auto-detect. "
                           f"Available columns: '{available_cols_str}'. "
                           f"Use --speed-column to specify the correct column name.")
        
        if detected_direction is None:
            available_cols_str = "', '".join(df.columns)
            raise ValueError(f"Direction column '{direction_col}' not found and could not auto-detect. "
                           f"Available columns: '{available_cols_str}'. "
                           f"Use --direction-column to specify the correct column name.")
        
        if detected_speed != speed_col:
            logging.info(f"Auto-detected speed column: '{detected_speed}' (was looking for '{speed_col}')")
        if detected_direction != direction_col:
            logging.info(f"Auto-detected direction column: '{detected_direction}' (was looking for '{direction_col}')")
        
        speeds = df[detected_speed].values
        directions = df[detected_direction].values
        
        # Remove any NaN values
        valid_mask = ~(np.isnan(speeds) | np.isnan(directions))
        speeds = speeds[valid_mask]
        directions = directions[valid_mask]
        
        invalid_count = len(df) - len(speeds)
        if invalid_count > 0:
            logging.info(f"Removed {invalid_count} rows with NaN values")
        
        logging.info(f"Loaded {len(speeds)} valid wind observations from CSV")
        return speeds, directions
        
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

def calculate_statistics(speeds, directions):
    """Calculate wind rose statistics and return frequency matrix for plotting"""
    sector_indices, sector_names = bin_directions(directions)
    speed_categories, category_names = classify_wind_speeds(speeds)
    
    stats = {}
    total_observations = len(speeds)
    calm_count = np.sum(speeds < 2)
    
    # Pre-calculate frequency matrix for memory-efficient plotting
    freq_matrix = np.zeros((16, 4))
    
    for i, sector in enumerate(sector_names):
        sector_mask = sector_indices == i
        sector_speeds = speeds[sector_mask]
        sector_speed_cats = speed_categories[sector_mask]
        
        if len(sector_speeds) > 0:
            freq_by_category = [np.sum(sector_speed_cats == j) for j in range(4)]
            mean_speed = np.mean(sector_speeds)
        else:
            freq_by_category = [0, 0, 0, 0]
            mean_speed = 0.0
        
        # Store in frequency matrix for plotting
        freq_matrix[i, :] = freq_by_category
        
        stats[sector] = {
            'total_frequency': int(np.sum(sector_mask)),
            'frequency_percent': float(np.sum(sector_mask) / total_observations * 100),
            'mean_wind_speed': float(mean_speed),
            'speed_categories': {
                category_names[j]: int(freq_by_category[j]) 
                for j in range(4)
            }
        }
    
    stats['calm_percentage'] = float(calm_count / total_observations * 100)
    
    return stats, freq_matrix

def create_wind_rose(freq_matrix, output_file):
    """Create wind rose plot from pre-calculated frequency matrix"""
    sector_names = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                   'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    category_names = ['Calm', 'Light', 'Moderate', 'Strong']
    
    # Use memory-efficient figure creation
    plt.ioff()  # Turn off interactive mode
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    colors = ['lightblue', 'yellow', 'orange', 'red']
    
    # Convert to percentages
    total_obs = np.sum(freq_matrix)
    freq_matrix_pct = freq_matrix / total_obs * 100
    
    # Create theta values for each sector (center of each bin)
    theta_centers = np.linspace(0, 2*np.pi, 16, endpoint=False)
    width = 2*np.pi/16
    
    # Create stacked bars
    bottom = np.zeros(16)
    for j in range(4):
        ax.bar(theta_centers, freq_matrix_pct[:, j], width=width, 
               bottom=bottom, label=category_names[j], color=colors[j], alpha=0.8)
        bottom = bottom + freq_matrix_pct[:, j]
    
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.arange(0, 360, 22.5), sector_names)
    ax.set_ylabel('Frequency (%)')
    ax.legend(loc='upper left', bbox_to_anchor=(1.1, 1))
    
    plt.title('Wind Rose', pad=20)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)  # Explicitly close figure to free memory
    plt.ion()  # Turn interactive mode back on

def main():
    parser = argparse.ArgumentParser(description='Generate wind rose statistics and visualizations')
    
    # Create mutually exclusive group for input methods
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--csv-file', type=str,
                           help='CSV file containing wind data')
    input_group.add_argument('--speeds', nargs='+', type=float,
                           help='Wind speeds in m/s (use with --directions)')
    
    parser.add_argument('--directions', nargs='+', type=float,
                       help='Wind directions in degrees (0-360, use with --speeds)')
    parser.add_argument('--speed-column', default='wind_speed_ms',
                       help='Column name for wind speed in CSV (default: wind_speed_ms)')
    parser.add_argument('--direction-column', default='wind_direction_deg',
                       help='Column name for wind direction in CSV (default: wind_direction_deg)')
    parser.add_argument('--output-stats', default='wind_stats.json',
                       help='Output JSON file for statistics')
    parser.add_argument('--output-plot', default='wind_rose.png',
                       help='Output PNG file for wind rose plot')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Load data based on input method
    if args.csv_file:
        speeds, directions = load_data_from_csv(args.csv_file, args.speed_column, args.direction_column)
    else:
        if not args.directions:
            parser.error("--directions is required when using --speeds")
        speeds = np.array(args.speeds)
        directions = np.array(args.directions)
        
        if len(speeds) != len(directions):
            raise ValueError("Number of speed and direction values must match")
        
        logging.info(f"Processing {len(speeds)} wind observations from command line")
    
    # Calculate statistics and get frequency matrix
    stats, freq_matrix = calculate_statistics(speeds, directions)
    
    # Save statistics to JSON
    with open(args.output_stats, 'w') as f:
        json.dump(stats, f, indent=2)
    logging.info(f"Statistics saved to {args.output_stats}")
    
    # Create wind rose plot using pre-calculated frequencies
    create_wind_rose(freq_matrix, args.output_plot)
    logging.info(f"Wind rose plot saved to {args.output_plot}")

if __name__ == "__main__":
    main()
