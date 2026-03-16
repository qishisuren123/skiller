field_features.csv:
field_id,crop_type,yield_tons,total_rainfall,mean_soil_moisture,cumulative_gdd,mean_ndvi,max_ndvi,min_ndvi,ndvi_std,peak_ndvi_date
1001,corn,8.5,245.6,0.42,1250.5,0.65,0.85,0.45,0.12,2023-07-15
1002,soybean,3.2,198.3,0.38,980.2,0.58,0.75,0.41,0.09,2023-08-02

correlation_matrix.csv:
,yield_tons,total_rainfall,mean_soil_moisture,cumulative_gdd,mean_ndvi,max_ndvi,min_ndvi,ndvi_std
yield_tons,1.0,0.45,-0.12,0.67,0.72,0.68,0.23,0.34
total_rainfall,0.45,1.0,0.23,0.56,0.41,0.38,0.15,0.22

summary.json:
{
  "n_fields": 2000,
  "n_crop_types": 3,
  "feature_names": ["yield_tons", "total_rainfall", "mean_soil_moisture", "cumulative_gdd", "mean_ndvi", "max_ndvi", "min_ndvi", "ndvi_std"],
  "top_3_yield_correlates": {
    "mean_ndvi": 0.72,
    "max_ndvi": 0.68,
    "cumulative_gdd": 0.67
  }
}
