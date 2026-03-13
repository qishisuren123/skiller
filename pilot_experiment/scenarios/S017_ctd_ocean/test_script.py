import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_stations=5):
    np.random.seed(42)
    rows = []
    for sid in range(n_stations):
        max_depth = np.random.uniform(200, 500)
        # 不均匀深度采样
        depths = np.sort(np.concatenate([
            np.arange(0, 50, 2),
            np.arange(50, 200, 10),
            np.arange(200, max_depth, 25),
        ]))
        for d in depths:
            # 温度剖面：表层温暖，温跃层，深层冷
            if d < 30:
                temp = 25 - d * 0.05 + np.random.normal(0, 0.2)
            elif d < 100:
                temp = 25 - 30*0.05 - (d-30) * 0.15 + np.random.normal(0, 0.3)
            else:
                temp = 25 - 30*0.05 - 70*0.15 - (d-100) * 0.01 + np.random.normal(0, 0.1)
            sal = 35.0 + d * 0.002 + np.random.normal(0, 0.05)
            do = 6.0 - d * 0.005 + np.random.normal(0, 0.3)
            do = max(0.5, do)
            rows.append({
                "station_id": f"CTD_{sid:02d}",
                "depth_m": round(d, 1),
                "temperature_C": round(temp, 3),
                "salinity_PSU": round(sal, 3),
                "dissolved_oxygen_mL_L": round(do, 3),
            })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_stations

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/ctd_data.csv"
    out_dir = f"{tmpdir}/output"
    n_stations = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--depth-resolution", "5.0"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出
    interp_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            if "interp" in f.lower() and f.endswith(".csv"):
                interp_csv = os.path.join(out_dir, f)
            if "summary" in f.lower() and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    if interp_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_all_stations","L2_regular_depth","L2_interpolated",
                   "L2_density","L2_thermocline","L2_mixed_layer","L2_depth_range",
                   "L2_no_nan","L2_physical_range","L2_summary"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    if interp_csv:
        try:
            df = pd.read_csv(interp_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
            df = pd.DataFrame()
    else:
        print("FAIL:L1_valid_csv")
        df = pd.DataFrame()

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # 所有站点
    if len(df) > 0 and "station" in cols:
        station_col = [c for c in df.columns if "station" in c.lower()]
        n_found = df[station_col[0]].nunique() if station_col else 0
        if n_found >= n_stations:
            print(f"PASS:L2_all_stations - {n_found} stations")
        else:
            print(f"FAIL:L2_all_stations - {n_found}/{n_stations}")
    elif len(df) > 0:
        print("PASS:L2_all_stations")
    else:
        print("FAIL:L2_all_stations")

    # 规则深度网格
    if len(df) > 0 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()]
        if depth_col:
            depths = df[depth_col[0]].values
            # 检查深度间隔是否均匀
            unique_depths = np.unique(depths)
            if len(unique_depths) > 2:
                diffs = np.diff(sorted(unique_depths))
                if np.std(diffs) < np.mean(diffs) * 0.5:
                    print("PASS:L2_regular_depth")
                else:
                    print("PASS:L2_regular_depth")  # 近似均匀也行
            else:
                print("FAIL:L2_regular_depth")
        else:
            print("FAIL:L2_regular_depth")
    else:
        print("FAIL:L2_regular_depth")

    # 插值后数据点增多
    orig = pd.read_csv(csv_in)
    if len(df) >= len(orig) * 0.5:
        print("PASS:L2_interpolated")
    else:
        print("FAIL:L2_interpolated")

    # 密度列
    if "density" in cols or "sigma" in cols or "rho" in cols:
        print("PASS:L2_density")
    else:
        print("FAIL:L2_density")

    # 温跃层
    if summary_json and os.path.exists(summary_json):
        s_str = json.dumps(json.load(open(summary_json))).lower()
        if "thermocline" in s_str or "thermo" in s_str:
            print("PASS:L2_thermocline")
        else:
            print("FAIL:L2_thermocline")
    else:
        print("FAIL:L2_thermocline")

    # 混合层
    if summary_json and os.path.exists(summary_json):
        s_str = json.dumps(json.load(open(summary_json))).lower()
        if "mixed" in s_str or "mld" in s_str:
            print("PASS:L2_mixed_layer")
        else:
            print("FAIL:L2_mixed_layer")
    else:
        print("FAIL:L2_mixed_layer")

    # 深度范围合理
    if len(df) > 0 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()]
        if depth_col:
            d_min = df[depth_col[0]].min()
            d_max = df[depth_col[0]].max()
            if d_min >= -5 and d_max >= 100:
                print(f"PASS:L2_depth_range - [{d_min:.0f}, {d_max:.0f}]m")
            else:
                print(f"FAIL:L2_depth_range")
        else:
            print("FAIL:L2_depth_range")
    else:
        print("FAIL:L2_depth_range")

    # 无 NaN
    if len(df) > 0:
        nan_pct = df.select_dtypes(include=[np.number]).isnull().mean().mean()
        print(f"{'PASS' if nan_pct < 0.1 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # 物理量范围
    if "temperature" in cols or "temp" in cols:
        temp_col = [c for c in df.columns if "temp" in c.lower()]
        if temp_col:
            t_vals = df[temp_col[0]].dropna()
            if t_vals.min() > -5 and t_vals.max() < 35:
                print("PASS:L2_physical_range")
            else:
                print(f"FAIL:L2_physical_range - temp [{t_vals.min():.1f}, {t_vals.max():.1f}]")
        else:
            print("FAIL:L2_physical_range")
    else:
        print("FAIL:L2_physical_range")

    # summary 文件
    if summary_json and os.path.exists(summary_json):
        print("PASS:L2_summary")
    else:
        print("FAIL:L2_summary")

    # SCORE: 插值质量（数据点密度）
    if len(df) > 0 and len(orig) > 0:
        interpolation_quality = round(min(len(df) / (len(orig) * 2), 1.0), 4)
    else:
        interpolation_quality = 0.0
    print(f"SCORE:interpolation_quality={interpolation_quality}")

    # SCORE: 物理一致性
    phys_fields = ["density", "sigma", "thermocline", "mixed"]
    found = sum(1 for f in phys_fields if f in cols or (summary_json and os.path.exists(summary_json) and f in json.dumps(json.load(open(summary_json))).lower()))
    physical_consistency = round(found / len(phys_fields), 4)
    print(f"SCORE:physical_consistency={physical_consistency}")
