import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(input_dir, n_stations=4, n_hours=48):
    os.makedirs(input_dir, exist_ok=True)
    base = pd.Timestamp("2024-01-01")
    for s in range(n_stations):
        times = pd.date_range(base, periods=n_hours, freq="1h")
        # 每个站时间稍有偏移
        if s > 0:
            times = times[s:]  # 前几个时间点缺失
        df = pd.DataFrame({
            "timestamp": times.strftime("%Y-%m-%dT%H:%M:%S"),
            "temperature": 20 + 5 * np.sin(np.arange(len(times)) / 6) + np.random.randn(len(times)),
            "humidity": 60 + 10 * np.random.randn(len(times)),
            "pressure": 1013 + np.random.randn(len(times)) * 2,
            "station_id": f"Station_{s}",
        })
        # 随机引入缺失
        mask = np.random.rand(len(times)) < 0.1
        df.loc[mask, "temperature"] = np.nan
        df.to_csv(f"{input_dir}/station_{s}.csv", index=False)
    return n_stations

with tempfile.TemporaryDirectory() as tmpdir:
    input_dir = f"{tmpdir}/stations"
    csv_out = f"{tmpdir}/merged.csv"
    n_stations = create_data(input_dir)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input-dir", input_dir, "--output", csv_out],
        [sys.executable, "generated.py", input_dir, "-o", csv_out],
        [sys.executable, "generated.py", input_dir, csv_out],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(csv_out):
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(csv_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_multi_station","L2_time_aligned","L2_fillna"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    if len(df.columns) > 5:
        print(f"PASS:L2_multi_station - {len(df.columns)} columns")
    else:
        print(f"FAIL:L2_multi_station - only {len(df.columns)} columns")

    # 检查时间列
    time_col = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
    if time_col:
        print("PASS:L2_time_aligned")
    elif df.index.dtype == "object" and "-" in str(df.index[0]):
        print("PASS:L2_time_aligned")
    else:
        print("FAIL:L2_time_aligned - no time column found")

    # 缺失值应该被填充（不应该有大量NaN）
    null_pct = df.isnull().mean().mean()
    if null_pct < 0.3:
        print(f"PASS:L2_fillna - {null_pct:.1%} null")
    else:
        print(f"FAIL:L2_fillna - {null_pct:.1%} null (too much)")

    # --- 新增测试 ---
    # L2: 时间间隔为 1 小时
    time_col = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
    if time_col:
        try:
            ts = pd.to_datetime(df[time_col[0]])
            diffs = ts.diff().dropna()
            median_diff = diffs.median()
            if pd.Timedelta("50min") <= median_diff <= pd.Timedelta("70min"):
                print("PASS:L2_hourly")
            else:
                print(f"FAIL:L2_hourly - median interval: {median_diff}")
        except:
            print("FAIL:L2_hourly - cannot parse timestamps")
    else:
        print("FAIL:L2_hourly - no time column")

    # L2: 包含所有站点数据
    cols_str = " ".join(df.columns).lower()
    stations_found = sum(1 for s in range(n_stations) if f"station_{s}" in cols_str or f"_{s}_" in cols_str or f"_{s}" in cols_str)
    if stations_found >= n_stations - 1:
        print(f"PASS:L2_all_stations - {stations_found}/{n_stations} stations")
    else:
        print(f"FAIL:L2_all_stations - only {stations_found}/{n_stations} stations found")

    # L2: 没有过多连续 NaN（fill limit=3 应工作）
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    excessive_nan = False
    for col in numeric_cols[:5]:  # 检查前 5 列
        vals = df[col].values
        nan_streak = 0
        max_streak = 0
        for v in vals:
            if pd.isna(v):
                nan_streak += 1
                max_streak = max(max_streak, nan_streak)
            else:
                nan_streak = 0
        if max_streak > 10:
            excessive_nan = True
            break
    print(f"{'PASS' if not excessive_nan else 'FAIL'}:L2_no_excessive_nan")

    # L2: 列名规范（应有站点标识和变量名）
    has_structured_names = any("_temp" in c.lower() or "_humid" in c.lower() or "_press" in c.lower() for c in df.columns)
    if has_structured_names or len(df.columns) > 5:
        print("PASS:L2_naming")
    else:
        print("FAIL:L2_naming - column names not structured")

    # L2: 温度值在合理范围
    temp_cols = [c for c in df.columns if "temp" in c.lower()]
    if temp_cols:
        temp_vals = df[temp_cols].values.flatten()
        temp_vals = temp_vals[~np.isnan(temp_vals)]
        if len(temp_vals) > 0 and temp_vals.min() > -50 and temp_vals.max() < 60:
            print(f"PASS:L2_range - temp [{temp_vals.min():.1f}, {temp_vals.max():.1f}]")
        else:
            print(f"FAIL:L2_range - unreasonable temperature values")
    else:
        print("FAIL:L2_range - no temperature columns")

    # L2: 前向/后向填充已应用
    if null_pct < 0.15:  # 原始数据约 10% 缺失 + 站点偏移
        print(f"PASS:L2_fill_applied - {null_pct:.1%} remaining nulls")
    else:
        print(f"FAIL:L2_fill_applied - {null_pct:.1%} still too many nulls")

    # SCORE: 时间对齐误差
    if time_col:
        try:
            ts = pd.to_datetime(df[time_col[0]])
            diffs = ts.diff().dropna()
            expected = pd.Timedelta("1h")
            alignment_errors = ((diffs - expected).abs() / expected).mean()
            time_alignment_error = round(max(0, 1.0 - alignment_errors), 4)
        except:
            time_alignment_error = 0.0
    else:
        time_alignment_error = 0.0
    print(f"SCORE:time_alignment_error={time_alignment_error}")

    # SCORE: 填充质量（1 - 残余缺失比例）
    fill_quality = round(1.0 - null_pct, 4)
    print(f"SCORE:fill_quality={fill_quality}")
