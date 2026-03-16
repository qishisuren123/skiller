1. Install required dependencies: `pip install -r requirements.txt`
2. Run basic analysis: `python scripts/main.py`
3. Customize parameters: `python scripts/main.py --points 500 --max_stress 400 --max_strain 0.15`
4. Enable verbose logging: `python scripts/main.py --verbose`
5. Analyze brittle materials: `python scripts/main.py --max_strain 0.005 --max_stress 100`
6. Review generated plot file (default: tensile_curve.png)
7. Examine JSON results file (default: results.json)
8. Check log file (tensile_analysis.log) for detailed analysis steps
9. Validate results against expected material properties
10. Adjust parameters based on warnings in log output
