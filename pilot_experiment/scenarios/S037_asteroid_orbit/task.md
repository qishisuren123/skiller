# Asteroid Orbital Elements Calculator

Create a CLI script that computes basic orbital elements for asteroids from simulated position observations.

## Background
Asteroids follow elliptical orbits around the Sun. From a series of position observations (x, y coordinates in astronomical units), we can estimate key orbital parameters including the semi-major axis, eccentricity, and orbital period using simplified 2D orbital mechanics.

## Requirements

Your script should accept the following arguments:
- `--input` or `--observations`: JSON file containing asteroid observation data
- `--output` or `--results`: Output JSON file for computed orbital elements
- `--plot` or `--visualization`: Output PNG file showing the orbital fit

The script must:

1. **Load observation data** from the input JSON file containing timestamps, x-coordinates, and y-coordinates of asteroid positions in AU (astronomical units).

2. **Fit an elliptical orbit** to the position data using least-squares fitting. Assume the Sun is at the origin (0,0) and fit an ellipse of the form: `((x-h)/a)² + ((y-k)/b)² = 1` where (h,k) is the center offset.

3. **Calculate orbital elements** including:
   - Semi-major axis (a) in AU
   - Semi-minor axis (b) in AU  
   - Eccentricity (e = sqrt(1 - b²/a²))
   - Orbital period in years using Kepler's third law (T² = a³)

4. **Save results** to output JSON file with computed orbital elements and fitting statistics (R-squared value).

5. **Generate visualization** showing original observation points, fitted elliptical orbit, and Sun position at origin.

6. **Validate results** by ensuring eccentricity is between 0 and 1, and semi-major axis is positive.

The synthetic data will represent realistic asteroid observations with some measurement noise.
