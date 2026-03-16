patient_id,test_name,value,unit,reference_low,reference_high,timestamp,normalized_value,normalized_ref_low,normalized_ref_high,flag,is_critical
P001,Glucose,180,mg/dL,70,100,2023-01-15 08:30:00,9.99,3.885,5.55,high,False
P001,Creatinine,0.2,mg/dL,0.6,1.2,2023-01-15 08:30:00,17.68,53.04,106.08,low,True
P002,Blood Glucose,65,mg/dL,70,100,2023-01-16 09:15:00,3.6075,3.885,5.55,low,False
P002,CREATININE,2.8,mg/dL,0.6,1.2,2023-01-16 09:15:00,247.52,53.04,106.08,high,True

Patient Summary JSON:
{
  "P001": {
    "n_abnormal": 2,
    "n_critical": 1,
    "most_recent_test": "2023-01-15 08:30:00",
    "tests": [
      {"test_name": "Glucose", "flag": "high", "is_critical": false},
      {"test_name": "Creatinine", "flag": "low", "is_critical": true}
    ]
  },
  "P002": {
    "n_abnormal": 2,
    "n_critical": 1,
    "most_recent_test": "2023-01-16 09:15:00",
    "tests": [
      {"test_name": "Blood Glucose", "flag": "low", "is_critical": false},
      {"test_name": "CREATININE", "flag": "high", "is_critical": true}
    ]
  }
}
