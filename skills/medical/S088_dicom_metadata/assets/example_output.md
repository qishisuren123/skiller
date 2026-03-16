{
  "summary": {
    "total_records": 150,
    "total_series": 425,
    "passed": 142,
    "failed": 8
  },
  "results": [
    {
      "record_id": "1.2.3.4.5",
      "patient_id": "ANON_a1b2c3d4",
      "series_count": 3,
      "violations": [
        {
          "field": "Series[1].SliceThickness",
          "severity": "WARNING",
          "message": "Unusual CT slice thickness: 12.5mm"
        }
      ],
      "status": "PASS"
    }
  ]
}

Statistical Summary:
{
  "total_records": 150,
  "total_series": 425,
  "modality_distribution": {
    "CT": 180,
    "MRI": 165,
    "US": 80
  },
  "parameter_stats": {
    "slice_thickness": {
      "mean": 2.8,
      "min": 0.5,
      "max": 5.0,
      "count": 180
    },
    "echo_time": {
      "mean": 45.2,
      "min": 8.0,
      "max": 120.0,
      "count": 165
    }
  }
}
