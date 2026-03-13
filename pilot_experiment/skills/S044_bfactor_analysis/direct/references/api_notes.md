# NumPy Statistical Functions
np.mean(array)              # Calculate arithmetic mean
np.median(array)            # Calculate median value
np.std(array)               # Calculate standard deviation
np.percentile(array, q)     # Calculate qth percentile
np.min(array), np.max(array) # Find minimum and maximum values
np.where(condition)         # Find indices where condition is True
np.arange(n)               # Create array of sequential integers 0 to n-1

# Matplotlib Plotting Functions
plt.figure(figsize=(w, h))  # Create figure with specified size
plt.plot(x, y, style)      # Create line plot with style options
plt.axhline(y=val)         # Draw horizontal line at y-value
plt.axvspan(start, end)    # Shade vertical region between start and end
plt.xlabel(), plt.ylabel() # Set axis labels
plt.legend()               # Display legend
plt.savefig(filename, dpi) # Save plot to file with specified resolution

# JSON Operations
json.dump(data, file, indent) # Write data to JSON file with formatting
json.load(file)            # Read data from JSON file

# Argparse Command-line Interface
parser.add_argument(name, help) # Add positional argument
parser.add_argument('--flag', action='store_true') # Add boolean flag
parser.parse_args()        # Parse command-line arguments
