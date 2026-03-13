import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_days=180):
    """生成模拟逐小时污染物数据：半年（180 天）"""
    np.random.seed(42)
    rows = []
    base_date = pd.Timestamp("2024-01-01")
    for day in range(n_days):
        date = base_date + pd.Timedelta(days=day)
        # 季节性基线
        season_factor = 1.0 + 0.5 * np.sin(2 * np.pi * day / 365)
        # 每天偶尔有高污染事件
        event = 1.0
        if np.random.rand() < 0.1:
            event = np.random.uniform(2.0, 4.0)
        for hour in range(24):
            ts = date + pd.Timedelta(hours=hour)
            # 日变化模式：早晚高峰
            diurnal = 1.0 + 0.3 * np.sin(2 * np.pi * (hour - 8) / 24)
            base = season_factor * event * diurnal
            pm25 = max(0, base * np.random.uniform(8, 30) + np.random.normal(0, 3))
            pm10 = max(0, base * np.random.uniform(20, 60) + np.random.normal(0, 5))
            o3 = max(0, np.random.uniform(15, 55) * (1 + 0.5 * np.sin(2 * np.pi * (hour - 14) / 24)) * season_factor)
            no2 = max(0, base * np.random.uniform(10, 40) + np.random.normal(0, 5))
            so2 = max(0, base * np.random.uniform(2, 20) + np.random.normal(0, 2))
            co = max(0, base * np.random.uniform(0.2, 2.0) + np.random.normal(0, 0.1))
            rows.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "pm25": round(pm25, 2),
                "pm10": round(pm10, 2),
                "o3": round(o3, 2),
                "no2": round(no2, 2),
                "so2": round(so2, 2),
                "co": round(co, 3),
            })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_days

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/pollutants.csv"
    out_dir = f"{tmpdir}/output"
    n_days = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", csv_in, out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    daily_csv = None
    monthly_json = None
    exceedance_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("daily" in fl or "aqi" in fl) and f.endswith(".csv"):
                daily_csv = os.path.join(out_dir, f)
            if ("monthly" in fl or "month" in fl) and f.endswith(".json"):
                monthly_json = os.path.join(out_dir, f)
            if ("exceedance" in fl or "exceed" in fl) and f.endswith(".json"):
                exceedance_json = os.path.join(out_dir, f)

    if daily_csv or monthly_json or exceedance_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_daily_count", "L2_aqi_column", "L2_aqi_range",
                   "L2_category_column", "L2_dominant_pollutant", "L2_sub_indices",
                   "L2_monthly_summary", "L2_exceedance_report", "L2_exceedance_fields",
                   "L2_no_nan", "L2_date_column"]:
            print(f"FAIL:{t}")
        print("SCORE:aqi_accuracy=0.0")
        print("SCORE:report_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if daily_csv:
        try:
            df = pd.read_csv(daily_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 日数正确
    if len(df) >= n_days * 0.9:
        print(f"PASS:L2_daily_count - {len(df)}/{n_days} days")
    elif len(df) > 0:
        print(f"PASS:L2_daily_count - {len(df)} days")
    else:
        print("FAIL:L2_daily_count")

    # L2: 有 AQI 列
    if "aqi" in cols:
        print("PASS:L2_aqi_column")
    else:
        print("FAIL:L2_aqi_column")

    # L2: AQI 值范围合理 (0-500)
    aqi_col = [c for c in df.columns if "aqi" == c.lower() or c.lower() == "daily_aqi" or c.lower() == "overall_aqi"]
    if not aqi_col:
        aqi_col = [c for c in df.columns if "aqi" in c.lower() and "pm" not in c.lower() and "o3" not in c.lower()
                    and "no2" not in c.lower() and "so2" not in c.lower() and "co" not in c.lower()]
    if aqi_col and len(df) > 0:
        vals = df[aqi_col[0]].dropna()
        if len(vals) > 0 and vals.min() >= 0 and vals.max() <= 500:
            print(f"PASS:L2_aqi_range - [{vals.min():.0f}, {vals.max():.0f}]")
        elif len(vals) > 0:
            print(f"FAIL:L2_aqi_range - [{vals.min():.0f}, {vals.max():.0f}]")
        else:
            print("FAIL:L2_aqi_range")
    else:
        print("FAIL:L2_aqi_range")

    # L2: 有类别列
    if "category" in cols or "level" in cols or "grade" in cols:
        print("PASS:L2_category_column")
    else:
        print("FAIL:L2_category_column")

    # L2: 有主要污染物列
    if "dominant" in cols or "primary" in cols or "main" in cols:
        print("PASS:L2_dominant_pollutant")
    else:
        print("FAIL:L2_dominant_pollutant")

    # L2: 有各污染物子指数列
    sub_index_count = sum(1 for p in ["pm25", "pm10", "o3", "no2", "so2", "co"]
                          if any(p in c.lower() and "aqi" in c.lower() for c in df.columns))
    if sub_index_count >= 4:
        print(f"PASS:L2_sub_indices - {sub_index_count} pollutants")
    elif sub_index_count >= 1:
        print(f"PASS:L2_sub_indices - {sub_index_count} pollutants (partial)")
    else:
        print("FAIL:L2_sub_indices")

    # L2: 月度汇总存在
    monthly = {}
    if monthly_json and os.path.exists(monthly_json):
        try:
            monthly = json.load(open(monthly_json))
            print("PASS:L2_monthly_summary")
        except:
            print("FAIL:L2_monthly_summary")
    else:
        print("FAIL:L2_monthly_summary")

    # L2: 超标报告存在
    exceedance = {}
    if exceedance_json and os.path.exists(exceedance_json):
        try:
            exceedance = json.load(open(exceedance_json))
            print("PASS:L2_exceedance_report")
        except:
            print("FAIL:L2_exceedance_report")
    else:
        print("FAIL:L2_exceedance_report")

    # L2: 超标报告包含关键字段
    e_str = json.dumps(exceedance).lower() if exceedance else ""
    expected_e_fields = ["total", "exceedance", "rate", "worst"]
    found_e = sum(1 for f in expected_e_fields if f in e_str)
    if found_e >= 3:
        print(f"PASS:L2_exceedance_fields - {found_e}/{len(expected_e_fields)}")
    elif found_e >= 1:
        print(f"PASS:L2_exceedance_fields - {found_e}/{len(expected_e_fields)} (partial)")
    else:
        print("FAIL:L2_exceedance_fields")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: 有日期列
    if "date" in cols or "day" in cols or "timestamp" in cols:
        print("PASS:L2_date_column")
    else:
        print("FAIL:L2_date_column")

    # SCORE: AQI 计算精度（手动计算第一天 PM2.5 AQI 并比较）
    aqi_accuracy = 0.0
    try:
        orig = pd.read_csv(csv_in)
        orig["timestamp"] = pd.to_datetime(orig["timestamp"])
        orig["date"] = orig["timestamp"].dt.date
        day1 = orig[orig["date"] == orig["date"].iloc[0]]
        pm25_avg = day1["pm25"].mean()

        # EPA 公式
        def calc_pm25_aqi(c):
            breakpoints = [
                (0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 500.4, 301, 500),
            ]
            for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
                if c <= bp_hi:
                    return round((i_hi - i_lo) / (bp_hi - bp_lo) * (c - bp_lo) + i_lo)
            return 500

        expected_pm25_aqi = calc_pm25_aqi(pm25_avg)

        if aqi_col and len(df) > 0:
            # 查找 PM2.5 子指数列
            pm25_aqi_col = [c for c in df.columns if "pm25" in c.lower() and "aqi" in c.lower()]
            if pm25_aqi_col:
                computed = df[pm25_aqi_col[0]].iloc[0]
                error = abs(computed - expected_pm25_aqi)
                aqi_accuracy = round(max(0, 1.0 - error / 50.0), 4)
            elif aqi_col:
                # 比较总 AQI（至少 >= PM2.5 AQI）
                computed = df[aqi_col[0]].iloc[0]
                if computed >= expected_pm25_aqi * 0.5:
                    aqi_accuracy = round(max(0, 1.0 - abs(computed - expected_pm25_aqi) / 100.0), 4)
    except:
        pass
    print(f"SCORE:aqi_accuracy={aqi_accuracy}")

    # SCORE: 报告完整性
    features = ["daily", "monthly", "exceedance", "category", "dominant", "aqi"]
    all_str = cols + " " + json.dumps(monthly).lower() + " " + e_str
    if daily_csv:
        all_str += " daily"
    if monthly_json and os.path.exists(monthly_json):
        all_str += " monthly"
    if exceedance_json and os.path.exists(exceedance_json):
        all_str += " exceedance"
    found = sum(1 for f in features if f in all_str)
    report_completeness = round(found / len(features), 4)
    print(f"SCORE:report_completeness={report_completeness}")
