# Income Inequality Analysis Tool

Create a command-line tool that calculates the Gini coefficient and generates a Lorenz curve from income distribution data. The Gini coefficient is a measure of statistical dispersion intended to represent income inequality within a population, where 0 represents perfect equality and 1 represents maximum inequality.

Your script should accept income data parameters and produce both numerical results and visualizations for inequality analysis.

## Requirements

1. **Data Generation**: Generate synthetic income data using specified parameters including population size, income distribution type (uniform, normal, or exponential), and distribution parameters (mean, std for normal; scale for exponential; min/max for uniform).

2. **Gini Coefficient Calculation**: Implement the standard Gini coefficient formula: G = (2∑(i×y_i))/(n×∑y_i) - (n+1)/n, where y_i are income values sorted in ascending order, i is the rank, and n is population size.

3. **Lorenz Curve Generation**: Calculate cumulative population percentiles and corresponding cumulative income percentiles. The Lorenz curve plots these relationships, with perfect equality represented by the diagonal line y=x.

4. **Statistical Summary**: Output a JSON file containing the Gini coefficient, mean income, median income, income standard deviation, and the 90th/10th percentile ratio.

5. **Visualization**: Create a matplotlib plot showing the Lorenz curve with the line of equality, properly labeled axes, and the Gini coefficient displayed in the title.

6. **Income Quintile Analysis**: Calculate and include in the JSON output the income share held by each quintile (bottom 20%, second 20%, etc.) of the population.

## Command Line Interface
