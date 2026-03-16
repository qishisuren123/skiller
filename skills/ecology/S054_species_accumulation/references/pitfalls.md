## Integer Overflow in Binomial Coefficients

**Error**: `OverflowError: integer overflow in binomial coefficient` when computing rarefaction curves with large datasets (200+ sites, 500+ species).

**Root Cause**: The math.comb() function uses integer arithmetic which overflows when calculating large binomial coefficients like C(500,200).

**Fix**: Switch to scipy.special.comb() with exact=False parameter for floating-point calculations, and add try-except blocks with hypergeometric approximation fallbacks for extreme cases.

## Memory Issues with Large Randomizations

**Error**: Memory exhaustion when storing all accumulation curves for confidence interval calculations.

**Root Cause**: Creating large arrays (n_randomizations × n_sites) consumes excessive memory with high parameter values.

**Fix**: Implement streaming statistics to calculate confidence intervals without storing all curves, or add parameter validation to warn users about memory requirements.

## Invalid Chao2 Estimates

**Error**: Negative or infinite Chao2 estimates when species frequency data is unusual.

**Root Cause**: Division by zero when Q2=0 or mathematical instability with extreme frequency distributions.

**Fix**: Add conditional logic for Q2=0 case using modified Chao2 formula, and validate input data quality before estimation.
