1. Prepare CSV input file with columns: response_text, age_group, region
2. Ensure age groups follow format: "18-25", "26-40", "41-60", "60+"
3. Run: python scripts/main.py input_survey.csv
4. Script validates CSV format and required columns
5. Processes responses in batches (1000 at a time for large datasets)
6. Calculates sentiment scores using lexicon-based word matching
7. Groups responses by demographics and calculates statistics
8. Generates three output files: JSON summary, CSV scores, PNG charts
9. Review console output for processing progress and final summary
10. Check output files for detailed results and visualizations
