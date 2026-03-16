## JSON Field Name Mismatch

**Error**: KeyError when loading observation data due to unexpected field names
**Root Cause**: Code expected specific field names ('timestamps', 'x_coordinates', 'y_coordinates') but user data used different names ('time', 'x', 'y')
**Fix**: Implement flexible field name matching in load_observations() function to handle multiple possible field name variations

## Division by Zero in Ellipse Fitting

**Error**: RuntimeWarning and division by zero when ellipse parameters become zero during optimization
**Root Cause**: Initial parameter estimates using standard deviation could be zero or very small with limited data points
**Fix**: Use data range instead of standard deviation for initial estimates and add bounds to optimization to prevent zero or negative semi-axes

## Unrealistic Orbital Elements

**Error**: Physically impossible results like 0.000 eccentricity and semi-major axis smaller than actual observation distances
**Root Cause**: Treating geometric ellipse parameters directly as orbital elements without considering orbital mechanics principles
**Fix**: Account for Sun's position at ellipse focus and adjust orbital element calculations to be heliocentric rather than geometric

## Type Error in Optimization

**Error**: TypeError when numpy.linspace receives float instead of integer for number of points
**Root Cause**: Optimization routine passes parameters as floats, but linspace expects integer for num parameter
**Fix**: Explicitly convert array length to integer using int() function before using in linspace calls
