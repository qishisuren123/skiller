# Earth Observation Station Merging — Expert Notes

## What You're Building
Merge multiple weather station CSV files into one unified time-aligned dataset. Each station reports at slightly different times; you need to resample everything to a common hourly grid.

## Key Steps
1. Read all CSVs from the input directory
2. Parse timestamps, set as index
3. Resample each station to hourly frequency
4. Pivot/merge so each column is `{station}_{variable}`
5. Forward-fill then backward-fill (limit=3)
6. Output merged CSV

## Pitfalls from Real Projects
1. **Timestamp parsing**: Use `pd.to_datetime(df["timestamp"])` — it handles ISO format automatically. Set it as the index BEFORE resampling
2. **Resample then merge, not merge then resample**: If you merge first, you get a mess of misaligned timestamps. Resample each station independently, then `pd.concat` or `merge`
3. **Column naming**: After pivot, use descriptive names like `Station_0_temperature`. If you just merge DataFrames, you'll get duplicate column names
4. **Fill limit**: `df.fillna(method='ffill', limit=3).fillna(method='bfill', limit=3)` — the limit prevents filling across long gaps
5. **Station ID column**: Drop it after pivoting. Don't leave it as a data column

## Reference
```python
dfs = []
for csv_file in Path(input_dir).glob("*.csv"):
    df = pd.read_csv(csv_file, parse_dates=["timestamp"], index_col="timestamp")
    station = df["station_id"].iloc[0]
    df = df.drop(columns=["station_id"])
    df = df.resample("1h").mean()
    df.columns = [f"{station}_{c}" for c in df.columns]
    dfs.append(df)
merged = pd.concat(dfs, axis=1)
merged = merged.ffill(limit=3).bfill(limit=3)
merged.to_csv(output_path)
```
