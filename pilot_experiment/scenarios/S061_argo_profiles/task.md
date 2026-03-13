# Argo Float Profile Analysis

Create a CLI script that processes Argo float temperature and salinity profiles to compute mixed layer depth and generate oceanographic analysis outputs.

Argo floats are autonomous instruments that drift in the ocean, periodically diving to collect vertical profiles of temperature and salinity. The mixed layer depth (MLD) is a critical oceanographic parameter representing the depth of the well-mixed surface layer.

Your script should accept synthetic Argo profile data and perform the following analysis:

## Requirements

1. **Data Processing**: Read synthetic Argo float data containing pressure (dbar), temperature (°C), and salinity (PSU) measurements from multiple profiles. Handle missing values and apply basic quality control by removing measurements where temperature < -2°C or salinity < 30 PSU.

2. **Mixed Layer Depth Calculation**: Compute mixed layer depth using the temperature criterion method. Define MLD as the depth where temperature differs from the 10-dbar reference temperature by more than 0.2°C. If no such depth exists, set MLD to the maximum profile depth.

3. **Density Computation**: Calculate potential density (sigma-theta) using the simplified equation: σ_θ = 1000 + (1.05 - 0.0057*T) + 0.78*S - 1000, where T is temperature and S is salinity. This approximation is suitable for surface waters.

4. **Profile Statistics**: For each profile, compute and store: profile ID, latitude, longitude, maximum depth, mixed layer depth, mean temperature in mixed layer, mean salinity in mixed layer, and surface density.

5. **Quality Metrics**: Calculate the percentage of valid measurements per profile and flag profiles with less than 50% valid data as "poor quality".

6. **Output Generation**: Save results as both a CSV file with profile statistics and a JSON file containing detailed profile data including computed densities.

Use argparse to handle input parameters for synthetic data generation and output file specifications.
