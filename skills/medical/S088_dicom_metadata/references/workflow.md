1. Initialize DICOMMetadataProcessor with anonymization and batch size settings
2. Load validation rules from JSON file if provided (references/validation_rules.json)
3. Stream input data in configurable batches to manage memory usage
4. For each record batch:
   - Apply selective copying anonymization if enabled
   - Validate study-level and series-level data against DICOM standards
   - Update incremental statistics collectors
   - Force garbage collection after each batch
5. Calculate final parameter statistics (means, min/max, counts)
6. Generate validation report with pass/fail summary and detailed violations
7. Generate statistical summary with modality distributions and parameter analysis
8. Save both reports to specified output files
9. Log processing progress and completion status
