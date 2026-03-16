1. Prepare observation data in JSON format with time, x, and y coordinate arrays
2. Execute the script: `python scripts/main.py --input observations.json --output results.json --plot orbit.png`
3. The tool loads observation data using flexible field name matching (time/timestamps, x/x_coordinates, y/y_coordinates)
4. Initial ellipse parameters are estimated using data spread and centroid calculations
5. Least-squares optimization fits elliptical curve with bounds to prevent invalid parameters
6. Orbital elements are calculated accounting for heliocentric coordinate system
7. R-squared statistics assess the quality of the elliptical fit
8. Results are saved to JSON file with orbital elements and fitting statistics
9. Visualization is generated showing observations, fitted orbit, Sun position, and orbit center
10. Validation checks ensure physically reasonable orbital parameters
