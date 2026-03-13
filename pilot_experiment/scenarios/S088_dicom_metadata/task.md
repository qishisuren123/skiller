# DICOM Metadata Extraction and Validation Tool

Create a CLI tool that processes synthetic DICOM-like medical imaging metadata to extract, validate, and analyze patient and study information across multiple imaging series.

Your script should accept the following arguments:
- `--input-data`: JSON file containing synthetic DICOM metadata records
- `--output-report`: Path for the validation report (JSON format)
- `--output-summary`: Path for the statistical summary (JSON format)
- `--anonymize`: Flag to anonymize patient identifiers in outputs
- `--validation-rules`: JSON file containing validation rules and constraints

## Requirements:

1. **Metadata Parsing**: Parse DICOM-like metadata records containing patient demographics, study information, series details, and image parameters. Handle nested structures and arrays of imaging series within studies.

2. **Multi-level Validation**: Implement comprehensive validation including patient ID format verification, date consistency checks (study date ≤ series date), modality-specific parameter validation (CT: slice thickness, MRI: echo time ranges), and cross-series consistency within studies.

3. **Anonymization Engine**: When anonymization is enabled, replace patient names with "ANONYMOUS_XXX" format, shift all dates by a consistent random offset per patient (maintaining relative timing), hash patient IDs while preserving uniqueness, and preserve all non-identifying medical parameters.

4. **Statistical Analysis**: Generate summary statistics including patient demographics distribution, study counts per modality, parameter value distributions (slice thickness, pixel spacing), and temporal analysis of study patterns.

5. **Compliance Reporting**: Create detailed validation reports showing per-record pass/fail status, specific violation descriptions, severity levels (ERROR/WARNING), and aggregate compliance scores by institution and modality.

6. **Advanced Filtering**: Support filtering records by date ranges, modalities, patient age groups, and institution codes. Apply filters before validation and analysis while maintaining referential integrity between studies and series.

The tool should handle malformed records gracefully and provide detailed error reporting for debugging purposes.
