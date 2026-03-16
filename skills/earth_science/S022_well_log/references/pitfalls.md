# Scipy Interpolation Compatibility Error

**Error**: KeyError: 'linear_interpolation' when using scipy.interpolate.interp1d with kind='linear'

**Root Cause**: Version compatibility issues between different scipy installations where the interpolation method names may vary

**Fix**: Replace scipy.interpolate.interp1d with numpy.interp for better cross-version compatibility and simpler linear interpolation

# Negative Porosity Values

**Error**: PHIT values coming out negative, which is physically impossible for porosity measurements

**Root Cause**: Using incorrect matrix density assumption (2.65 g/cm3 for sandstone) when formation has higher bulk densities indicating denser matrix minerals like limestone or dolomite

**Fix**: Implement automatic matrix density estimation using 95th percentile of bulk density distribution plus small buffer, or allow user-specified matrix density parameter

# All Samples Classified as Single Lithology

**Error**: All 1196 samples classified as limestone with zero porosity values in classification rules

**Root Cause**: Matrix density too low causing all porosity calculations to be clipped to zero, making samples fail sandstone classification rule (PHIT > 0.1)

**Fix**: Use data-driven matrix density estimation and add debugging output to show parameter ranges and rule application statistics

# NaN Values in Summary Statistics

**Error**: Summary JSON showing "NaN" for mean_porosity and mean_Vsh fields

**Root Cause**: Using pandas .mean() method which returns NaN when any values in the series are NaN, rather than computing mean of valid values

**Fix**: Replace .mean() with numpy.nanmean() to properly handle NaN values and compute statistics from valid data points only
