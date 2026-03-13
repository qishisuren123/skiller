# NumPy - Core array operations and signal processing
np.zeros(N)                    # Initialize zero arrays for filter coefficients
np.linspace(start, stop, num)  # Generate time vectors for signal synthesis
np.sin(2 * np.pi * freq * t)   # Generate sinusoidal signals
np.random.randn(N)             # Generate Gaussian white noise
np.dot(w, x)                   # Vector dot product for filter output
np.roll(array, shift)          # Circular shift for signal delay
np.clip(array, min, max)       # Bound values to prevent instability
np.mean(array**2)              # Calculate signal power
np.log10(ratio)                # Logarithmic calculations for dB conversion
np.save(filename, array)       # Save NumPy arrays to disk

# JSON - Metrics serialization
json.dump(data, file, indent=2) # Save formatted JSON metrics

# Argparse - Command line interface
parser.add_argument('--param', type=float, default=0.01, help='description')
args = parser.parse_args()     # Parse command line arguments

# OS - File system operations
os.makedirs(path, exist_ok=True) # Create output directories
os.path.dirname(path)          # Extract directory from file path
os.path.abspath(path)          # Get absolute path
