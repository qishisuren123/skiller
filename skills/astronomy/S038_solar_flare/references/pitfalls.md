# Common Pitfalls and Solutions

## Matplotlib Legend Duplicate Labels Error

**Error:** `ValueError: The truth value of an array with more than one element is ambiguous`

**Root Cause:** Multiple flares of the same classification trying to add identical labels to the plot legend, causing matplotlib to receive duplicate label parameters.

**Fix:** Track added labels using a set and only add each classification label once to the legend.

## Array Index Out of Bounds with Different Resolutions

**Error:** `IndexError: index 1440 is out of bounds for axis 0 with size 288`

**Root Cause:** Flare generation code using duration values directly as array indices without accounting for different time resolutions, causing access beyond array bounds.

**Fix:** Convert all time-based parameters to data points using the resolution: `duration_points = int(duration_minutes / resolution_minutes)` and adjust array bounds accordingly.

## Empty Noise Estimation Array

**Error:** `RuntimeWarning: Degrees of freedom <= 0 for slice` or `np.std()` returning NaN

**Root Cause:** The condition `flux[flux < baseline_flux * 2]` returns empty array when there are many large flares or insufficient quiet periods, causing noise estimation to fail.

**Fix:** Implement robust threshold calculation with multiple fallback methods: quiet periods, percentile-based estimation, and known noise level fallback.

## Missing Flares at Data Boundaries

**Error:** Flares extending to the end of the observation period not being detected

**Root Cause:** Detection algorithm only triggers flare end when flux drops below threshold, missing flares that continue to the end of the dataset.

**Fix:** Add explicit check for active flares at the end of the data and handle them as a special case in the detection loop.
