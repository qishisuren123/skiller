# Asteroid Orbital Elements Calculator

## Overview
This skill enables calculation of basic orbital elements (semi-major axis, eccentricity, period) from asteroid position observations using elliptical orbit fitting and Kepler's laws of planetary motion.

## Workflow
1. **Parse command-line arguments** for input observations file, output results file, and visualization plot file
2. **Load and validate observation data** from JSON file containing timestamps and x,y coordinates in astronomical units
3. **Fit elliptical orbit** to position data using least-squares optimization to determine ellipse parameters (center, semi-axes, rotation)
4. **Calculate orbital elements** including semi-major axis, eccentricity, and period using Kepler's third law
5. **Validate physical constraints** ensuring eccentricity is between 0-1 and semi-major axis is positive
6. **Generate orbital visualization** showing observations, fitted ellipse, and Sun position
7. **Save results** to JSON file with orbital elements and fitting statistics

## Common Pitfalls
- **Ellipse parameter confusion**: Semi-major axis 'a' must be the larger of the two fitted semi-axes, not necessarily the first parameter returned by fitting
- **Coordinate system assumptions**: Ensure the Sun is properly positioned at origin (0,0) and ellipse center offset is handled correctly
- **Eccentricity calculation order**: Always use e = sqrt(1 - b²/a²) where a > b, otherwise you'll get complex numbers
- **Unit consistency**: Input coordinates are in AU, periods should be in years, and Kepler's law constants must match these units
- **Insufficient data handling**: Need at least 5 observations to fit a 5-parameter ellipse reliably

## Error Handling
- Validate JSON structure and required fields before processing
- Check for minimum number of observations (≥5 points)
- Handle optimization convergence failures with multiple initial guesses
- Validate physical constraints and reject unphysical solutions
- Provide meaningful error messages for file I/O operations

## Quick Reference
