import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path):
    """生成模拟无线电探空数据：从地面到约 25 km"""
    np.random.seed(42)
    # 标准大气 + 一些特征
    altitudes = np.concatenate([
        np.arange(0, 2000, 100),
        np.arange(2000, 10000, 250),
        np.arange(10000, 26000, 500),
    ])
    n = len(altitudes)
    pressures = 1013.25 * (1 - 2.25577e-5 * altitudes) ** 5.25588
    temperatures = np.zeros(n)
    dewpoints = np.zeros(n)

    for i, alt in enumerate(altitudes):
        if alt < 1500:
            # 对流层低层：接近地面较暖
            temperatures[i] = 30.0 - alt * 0.008 + np.random.normal(0, 0.3)
            dewpoints[i] = 22.0 - alt * 0.005 + np.random.normal(0, 0.3)
        elif alt < 2000:
            # 逆温层（1500-2000m）
            temperatures[i] = 30.0 - 1500 * 0.008 + (alt - 1500) * 0.003 + np.random.normal(0, 0.2)
            dewpoints[i] = 22.0 - alt * 0.005 + np.random.normal(0, 0.3)
        elif alt < 11000:
            # 对流层：标准递减率 ~6.5 °C/km
            temperatures[i] = 30.0 - 1500 * 0.008 + 500 * 0.003 - (alt - 2000) * 0.0065 + np.random.normal(0, 0.3)
            dewpoints[i] = temperatures[i] - np.random.uniform(5, 20)
        elif alt < 20000:
            # 平流层下层：等温
            temperatures[i] = -56.5 + np.random.normal(0, 0.5)
            dewpoints[i] = temperatures[i] - 30 + np.random.normal(0, 1)
        else:
            # 平流层上层：缓慢升温
            temperatures[i] = -56.5 + (alt - 20000) * 0.001 + np.random.normal(0, 0.5)
            dewpoints[i] = temperatures[i] - 40 + np.random.normal(0, 1)

    wind_speed = 5 + altitudes / 2000 + np.random.normal(0, 2, n)
    wind_speed = np.clip(wind_speed, 0, None)
    wind_direction = 225 + altitudes / 500 + np.random.normal(0, 15, n)
    wind_direction = wind_direction % 360

    df = pd.DataFrame({
        "pressure": np.round(pressures, 2),
        "temperature": np.round(temperatures, 2),
        "dewpoint": np.round(dewpoints, 2),
        "wind_speed": np.round(wind_speed, 2),
        "wind_direction": np.round(wind_direction, 2),
        "altitude": np.round(altitudes, 1),
    })
    df.to_csv(path, index=False)
    return len(df)

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/sounding.csv"
    out_dir = f"{tmpdir}/output"
    n_levels = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", csv_in, out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    profile_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("profile" in fl or "processed" in fl or "lapse" in fl) and f.endswith(".csv"):
                profile_csv = os.path.join(out_dir, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)
    # 也检查 out_dir 本身是否被当作文件前缀
    if not profile_csv and not summary_json:
        parent = os.path.dirname(out_dir)
        for f in os.listdir(parent) if os.path.exists(parent) else []:
            fl = f.lower()
            if ("profile" in fl or "processed" in fl) and f.endswith(".csv"):
                profile_csv = os.path.join(parent, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(parent, f)

    if profile_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_lapse_rate_col", "L2_lapse_rate_range",
                   "L2_tropopause", "L2_tropopause_range", "L2_cape",
                   "L2_cin", "L2_inversions", "L2_surface_info",
                   "L2_all_levels", "L2_no_nan", "L2_summary_json"]:
            print(f"FAIL:{t}")
        print("SCORE:lapse_accuracy=0.0")
        print("SCORE:feature_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if profile_csv:
        try:
            df = pd.read_csv(profile_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 有 lapse rate 列
    if "lapse" in cols or "lapse_rate" in cols or "gamma" in cols:
        print("PASS:L2_lapse_rate_col")
    else:
        print("FAIL:L2_lapse_rate_col")

    # L2: lapse rate 值范围合理 (通常 -10 到 +15 °C/km)
    lapse_col = [c for c in df.columns if "lapse" in c.lower() or "gamma" in c.lower()]
    if lapse_col and len(df) > 0:
        vals = df[lapse_col[0]].dropna()
        if len(vals) > 0 and vals.min() > -20 and vals.max() < 30:
            print(f"PASS:L2_lapse_rate_range - [{vals.min():.1f}, {vals.max():.1f}]")
        else:
            print(f"FAIL:L2_lapse_rate_range - [{vals.min():.1f}, {vals.max():.1f}]")
    else:
        print("FAIL:L2_lapse_rate_range")

    # L2: 对流层顶检测
    summary = {}
    if summary_json and os.path.exists(summary_json):
        try:
            summary = json.load(open(summary_json))
        except:
            pass
    s_str = json.dumps(summary).lower() if summary else ""

    if "tropopause" in s_str or "trop" in s_str:
        print("PASS:L2_tropopause")
    else:
        print("FAIL:L2_tropopause")

    # L2: 对流层顶高度范围合理 (8-18 km)
    trop_h = None
    for key in summary:
        kl = key.lower()
        if "tropopause" in kl and ("height" in kl or "alt" in kl):
            trop_h = float(summary[key])
            break
    if trop_h is None and isinstance(summary, dict):
        # 嵌套查找
        for k, v in summary.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if "tropopause" in kk.lower():
                        try:
                            trop_h = float(vv)
                        except:
                            pass
    if trop_h is not None and 8000 <= trop_h <= 18000:
        print(f"PASS:L2_tropopause_range - {trop_h:.0f}m")
    elif trop_h is not None and 8 <= trop_h <= 18:
        # 可能以 km 为单位
        print(f"PASS:L2_tropopause_range - {trop_h:.1f}km")
    elif trop_h is not None:
        print(f"FAIL:L2_tropopause_range - {trop_h}")
    else:
        print("FAIL:L2_tropopause_range")

    # L2: CAPE
    if "cape" in s_str:
        print("PASS:L2_cape")
    else:
        print("FAIL:L2_cape")

    # L2: CIN
    if "cin" in s_str:
        print("PASS:L2_cin")
    else:
        print("FAIL:L2_cin")

    # L2: 逆温层检测
    if "inversion" in s_str or "inversions" in s_str:
        print("PASS:L2_inversions")
    else:
        print("FAIL:L2_inversions")

    # L2: 地面信息
    if "surface" in s_str or (len(df) > 0 and "temperature" in cols):
        print("PASS:L2_surface_info")
    else:
        print("FAIL:L2_surface_info")

    # L2: 输出包含所有层
    if len(df) >= n_levels * 0.8:
        print(f"PASS:L2_all_levels - {len(df)}/{n_levels}")
    elif len(df) > 0:
        print(f"PASS:L2_all_levels - {len(df)} levels")
    else:
        print("FAIL:L2_all_levels")

    # L2: 无 NaN（允许首行 lapse rate 为 NaN）
    if len(df) > 0:
        numeric_cols = df.select_dtypes(include=[np.number])
        # 排除 lapse rate 列的第一行
        nan_count = 0
        for c in numeric_cols.columns:
            if "lapse" in c.lower() or "gamma" in c.lower():
                nan_count += numeric_cols[c].iloc[1:].isnull().sum()
            else:
                nan_count += numeric_cols[c].isnull().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: summary JSON 存在且可读
    if summary_json and os.path.exists(summary_json) and summary:
        print("PASS:L2_summary_json")
    else:
        print("FAIL:L2_summary_json")

    # SCORE: lapse rate 精度（手动计算前几层并比较）
    orig = pd.read_csv(csv_in)
    expected_lapse = []
    for i in range(1, min(10, len(orig))):
        dT = orig["temperature"].iloc[i] - orig["temperature"].iloc[i-1]
        dz = (orig["altitude"].iloc[i] - orig["altitude"].iloc[i-1]) / 1000.0
        if abs(dz) > 0.001:
            expected_lapse.append(-dT / dz)
    lapse_accuracy = 0.0
    if lapse_col and len(df) > 0:
        computed = df[lapse_col[0]].dropna().values[:len(expected_lapse)]
        if len(computed) > 0 and len(expected_lapse) > 0:
            min_len = min(len(computed), len(expected_lapse))
            errors = np.abs(computed[:min_len] - np.array(expected_lapse[:min_len]))
            mean_error = np.mean(errors)
            lapse_accuracy = round(max(0, 1.0 - mean_error / 10.0), 4)
    print(f"SCORE:lapse_accuracy={lapse_accuracy}")

    # SCORE: 特征完整性
    features = ["tropopause", "cape", "cin", "inversion", "surface", "lapse"]
    found = sum(1 for f in features if f in s_str or f in cols)
    feature_completeness = round(found / len(features), 4)
    print(f"SCORE:feature_completeness={feature_completeness}")
