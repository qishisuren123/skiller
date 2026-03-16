---
name: asteroid_orbit
description: "# Asteroid Orbital Elements Calculator

Create a CLI script that computes basic orbital elements for asteroids from simulated position observations.

## Background
Asteroids follow elliptical orbits around the Sun. This tool fits elliptical curves to observational position data and estimates key orbital parameters including semi-major axis, eccentricity, and orbital period."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: astronomy
---

# Asteroid Orbit

## Overview
This skill provides a complete CLI tool for calculating asteroid orbital elements from position observations. It fits elliptical orbits to x,y coordinate data and computes physically meaningful orbital parameters including semi-major axis, eccentricity, and orbital period using Kepler's laws.

## When to Use
- Analyzing asteroid observation data from telescopes or simulations
- Computing orbital elements for small solar system bodies
- Educational projects involving orbital mechanics
- Research requiring orbit determination from limited position data
- Validating theoretical orbital models against observational data

## Inputs
- JSON file containing observation data with time stamps and x,y coordinates
- Supported field names: 'time'/'timestamps', 'x'/'x_coordinates', 'y'/'y_coordinates'
- Minimum 3-5 observation points recommended for stable fitting
- Coordinates should be in astronomical units (AU) relative to the Sun

## Workflow
1. Execute `scripts/main.py` with required arguments for input data, output results, and visualization
2. The tool loads observations using flexible field name matching from `references/workflow.md`
3. Fits elliptical curve to position data using least-squares optimization with physical bounds
4. Calculates orbital elements accounting for Sun's position as ellipse focus
5. Generates R-squared statistics to assess fit quality
6. Saves results to JSON and creates orbital visualization plot
7. Validates results against physical constraints and logs warnings for unusual values

## Error Handling
The system includes comprehensive error handling for common issues. When the fitting algorithm encounters division by zero or invalid parameters, it applies bounds to prevent negative semi-axes and uses robust initial parameter estimation. The code will handle missing JSON fields gracefully and provide clear error messages for data format issues.

## Common Pitfalls
- Initial parameter estimation can fail with limited data points - use data range instead of standard deviation
- Geometric ellipse fitting doesn't account for orbital mechanics - must consider Sun at focus position
- Type errors in optimization when array lengths become floats - ensure integer conversion
- Unrealistic orbital elements when treating ellipse center as orbital center - adjust for heliocentric coordinates

## Output Format
JSON results file containing orbital_elements (semi_major_axis_au, semi_minor_axis_au, eccentricity, orbital_period_years) and fitting_statistics (r_squared). PNG visualization showing observation points, fitted elliptical orbit, Sun position, and orbit center with proper astronomical coordinate system.
