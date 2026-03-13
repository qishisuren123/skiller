# NumPy - Array operations and mathematical functions
np.array(data)                    # Convert list to numpy array
np.mean(array)                    # Calculate mean
np.ptp(array)                     # Peak-to-peak (range) of array
np.linspace(start, stop, num)     # Generate evenly spaced numbers
np.cos(angle), np.sin(angle)      # Trigonometric functions
np.sqrt(value)                    # Square root
np.sum(array)                     # Sum of array elements
np.random.normal(mean, std)       # Generate random numbers from normal distribution
np.random.uniform(low, high)      # Generate random numbers from uniform distribution

# SciPy - Scientific computing and optimization
from scipy.optimize import least_squares
least_squares(fun, x0, args=())   # Solve nonlinear least-squares problem
result.x                          # Optimized parameters
result.success                    # Boolean indicating convergence
result.cost                       # Final cost function value

# Matplotlib - Plotting and visualization
plt.figure(figsize=(width, height))    # Create new figure
plt.scatter(x, y, c=colors, cmap=name) # Scatter plot with color mapping
plt.plot(x, y, style, linewidth=width) # Line plot
plt.colorbar(label='text')             # Add colorbar
plt.xlabel('text'), plt.ylabel('text') # Axis labels
plt.title('text')                      # Plot title
plt.legend()                           # Show legend
plt.grid(True, alpha=transparency)     # Add grid
plt.axis('equal')                      # Equal aspect ratio
plt.text(x, y, text, transform=trans)  # Add text annotation
plt.tight_layout()                     # Adjust spacing
plt.savefig(filename, dpi=resolution)  # Save figure
plt.close()                            # Close figure

# JSON - Data serialization
json.load(file_object)            # Load JSON from file
json.dump(data, file_object, indent=n) # Save data to JSON file
