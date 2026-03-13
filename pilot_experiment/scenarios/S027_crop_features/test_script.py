import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_fields=20):
    np.random.seed(42)
    rows = []
    crop_types = ["wheat", "corn", "soybean", "rice"]
    for fid in range(n_fields):
        crop = crop_types[fid % len(crop_types)]
        base_yield = {"wheat": 3.5, "corn": 8.0, "soybean": 2.5, "rice": 5.0}[crop]
        n_obs = np.random.randint(15, 30)
        start_day = np.random.randint(60, 120)
        for j in range(n_obs):
            day = start_day + j * 7
            date = pd.Timestamp("2023-01-01") + pd.Timedelta(days=int(day))
            progress = j / n_obs
            ndvi = 0.3 + 0.5 * np.sin(np.pi * progress) + np.random.normal(0, 0.03)
            temp = 15 + 10 * np.sin(np.pi * (day - 60) / 200) + np.random.normal(0, 2)
            rain = max(0, np.random.exponential(5))
            sm = 0.3 + 0.1 * np.sin(np.pi * progress) + rain * 0.005 + np.random.normal(0, 0.02)
            yield_val = base_yield + 2.0 * ndvi + 0.01 * temp + np.random.normal(0, 0.3)
            rows.append({
                "field_id": f"F{fid:03d}",
                "date": date.strftime("%Y-%m-%d"),
                "ndvi": round(np.clip(ndvi, 0.05, 0.95), 4),
                "soil_moisture": round(np.clip(sm, 0.1, 0.6), 4),
                "temperature": round(temp, 1),
                "rainfall_mm": round(rain, 1),
                "crop_type": crop,
                "yield_tons": round(max(yield_val, 0.5), 2),
            })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_fields

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/field_obs.csv"
    out_dir = f"{tmpdir}/output"
    n_fields = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--base-temp", "10.0"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    feat_csv = None
    corr_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("feature" in fl or "field" in fl) and fl.endswith(".csv"):
                feat_csv = os.path.join(out_dir, f)
            if "corr" in fl and fl.endswith(".csv"):
                corr_csv = os.path.join(out_dir, f)
            if "summary" in fl and fl.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    has_output = feat_csv or corr_csv or summary_json
    if has_output:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_all_fields", "L2_gdd", "L2_ndvi_stats",
                   "L2_feature_cols", "L2_corr_matrix", "L2_corr_square",
                   "L2_summary_json", "L2_crop_types", "L2_yield_col",
                   "L2_no_nan", "L2_top_correlates"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if feat_csv:
        try:
            df = pd.read_csv(feat_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 所有 field 都被处理
    if len(df) >= n_fields:
        print(f"PASS:L2_all_fields - {len(df)} rows")
    elif len(df) > 0:
        print(f"PASS:L2_all_fields - {len(df)} rows (partial)")
    else:
        print("FAIL:L2_all_fields")

    # L2: GDD 列存在
    if "gdd" in cols or "growing" in cols or "degree" in cols:
        print("PASS:L2_gdd")
    else:
        print("FAIL:L2_gdd")

    # L2: NDVI 统计列
    ndvi_keys = ["mean_ndvi", "max_ndvi", "ndvi_std", "ndvi_mean", "ndvi_max"]
    if any(k in cols for k in ndvi_keys) or ("ndvi" in cols and len(df.columns) >= 5):
        print("PASS:L2_ndvi_stats")
    else:
        print("FAIL:L2_ndvi_stats")

    # L2: 特征列数量（至少 6 个）
    if len(df.columns) >= 6:
        print(f"PASS:L2_feature_cols - {len(df.columns)} columns")
    else:
        print(f"FAIL:L2_feature_cols - only {len(df.columns)} columns")

    # L2: 相关矩阵文件存在
    if corr_csv and os.path.exists(corr_csv):
        print("PASS:L2_corr_matrix")
        try:
            cdf = pd.read_csv(corr_csv, index_col=0)
            if cdf.shape[0] == cdf.shape[1] or abs(cdf.shape[0] - cdf.shape[1]) <= 1:
                print("PASS:L2_corr_square")
            else:
                print(f"FAIL:L2_corr_square - shape {cdf.shape}")
        except:
            print("FAIL:L2_corr_square")
    else:
        print("FAIL:L2_corr_matrix")
        print("FAIL:L2_corr_square")

    # L2: summary JSON
    if summary_json and os.path.exists(summary_json):
        try:
            summ = json.load(open(summary_json))
            print("PASS:L2_summary_json")
        except:
            print("FAIL:L2_summary_json")
            summ = {}
    else:
        print("FAIL:L2_summary_json")
        summ = {}

    # L2: 作物类型信息
    if "crop" in cols:
        print("PASS:L2_crop_types")
    elif summ and ("crop" in json.dumps(summ).lower()):
        print("PASS:L2_crop_types")
    else:
        print("FAIL:L2_crop_types")

    # L2: yield 列
    if "yield" in cols:
        print("PASS:L2_yield_col")
    else:
        print("FAIL:L2_yield_col")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: top correlates in summary
    s_str = json.dumps(summ).lower() if summ else ""
    if "top" in s_str or "correl" in s_str or "strongest" in s_str:
        print("PASS:L2_top_correlates")
    else:
        print("FAIL:L2_top_correlates")

    # SCORE: 特征完整度（检查关键特征列的存在比例）
    expected = ["ndvi", "gdd", "rainfall", "moisture", "yield", "crop"]
    found = sum(1 for e in expected if e in cols)
    feature_completeness = round(found / len(expected), 4)
    print(f"SCORE:feature_completeness={feature_completeness}")

    # SCORE: 数据质量（行数正确性 + NaN 比率）
    if len(df) > 0:
        row_score = min(len(df) / n_fields, 1.0)
        nan_rate = df.select_dtypes(include=[np.number]).isnull().mean().mean() if len(df) > 0 else 1.0
        data_quality = round(row_score * (1.0 - nan_rate), 4)
    else:
        data_quality = 0.0
    print(f"SCORE:data_quality={data_quality}")
