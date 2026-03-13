# Crystal System Classification from Unit Cell Parameters

Create a CLI script that determines the crystal system of materials based on their unit cell parameters. Crystal systems are fundamental classifications in crystallography that describe the symmetry and geometric constraints of crystal lattices.

Your script should accept unit cell parameters (lattice constants a, b, c and angles α, β, γ) and classify crystals into one of the seven crystal systems: cubic, tetragonal, orthorhombic, hexagonal, trigonal, monoclinic, or triclinic.

## Requirements

1. **Input Processing**: Use argparse to accept either individual unit cell parameters (`--a`, `--b`, `--c`, `--alpha`, `--beta`, `--gamma`) or a CSV file containing multiple crystal structures (`--input-csv`). Angles should be in degrees.

2. **Crystal System Classification**: Implement the standard crystallographic rules to classify each crystal:
   - Cubic: a=b=c, α=β=γ=90°
   - Tetragonal: a=b≠c, α=β=γ=90°
   - Orthorhombic: a≠b≠c, α=β=γ=90°
   - Hexagonal: a=b≠c, α=β=90°, γ=120°
   - Trigonal: a=b=c, α=β=γ≠90° (and equal)
   - Monoclinic: a≠b≠c, α=γ=90°≠β
   - Triclinic: a≠b≠c, α≠β≠γ≠90°

3. **Tolerance Handling**: Use a tolerance parameter (`--tolerance`, default 0.01) for floating-point comparisons when checking parameter equality and angle values.

4. **Output Generation**: Save results to a JSON file (`--output`) containing crystal system classifications, input parameters, and confidence metrics.

5. **Statistics**: Calculate and include summary statistics: distribution of crystal systems, average unit cell volumes, and parameter ranges for each system.

6. **Validation**: Verify that input parameters are physically reasonable (positive lengths, angles between 0° and 180°) and warn about unusual values.
