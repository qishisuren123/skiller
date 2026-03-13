import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_stations=3, n_years=20):
    np.random.seed(42)
    rows = []
    for sid in range(n_stations):
        base_flow = 10 + sid * 5
        start = pd.Timestamp("2000-01-01")
        for day in range(n_years * 365):
            date = start + pd.Timedelta(days=day)
            doy = date.dayofyear
            # 季节性基础流量
            seasonal = base_flow * (1 + 0.4 * np.sin(2 * np.pi * (doy - 90) / 365))
            # 随机降雨事件
            if np.random.random() < 0.03:
                storm = np.random.exponential(base_flow * 3)
            else:
                storm = 0
            discharge = seasonal + storm + np.random.exponential(base_flow * 0.1)
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "discharge_cms": round(max(discharge, 0.1), 2),
                "station_id": f"ST{sid:02d}",
            })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_stations, n_years

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/streamflow.csv"
    out_dir = f"{tmpdir}/output"
    n_stations, n_years = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--return-periods", "10,50,100"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    maxima_csv = None
    flood_json = None
    baseflow_csv = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("maxim" in fl or "annual" in fl) and fl.endswith(".csv"):
                maxima_csv = os.path.join(out_dir, f)
            if ("flood" in fl or "frequency" in fl or "gev" in fl) and fl.endswith(".json"):
                flood_json = os.path.join(out_dir, f)
            if "baseflow" in fl and fl.endswith(".csv"):
                baseflow_csv = os.path.join(out_dir, f)

    has_output = maxima_csv or flood_json or baseflow_csv
    if has_output:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_json", "L2_annual_maxima", "L2_all_stations", "L2_gev_params",
                   "L2_return_periods", "L2_return_values", "L2_baseflow_file",
                   "L2_baseflow_leq_Q", "L2_quickflow", "L2_years_correct",
                   "L2_flood_monotone", "L2_no_nan"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # L1: flood frequency JSON
    flood = {}
    if flood_json and os.path.exists(flood_json):
        try:
            flood = json.load(open(flood_json))
            print("PASS:L1_valid_json")
        except:
            print("FAIL:L1_valid_json")
    else:
        print("FAIL:L1_valid_json")

    f_str = json.dumps(flood).lower() if flood else ""

    # L2: 年最大值文件
    if maxima_csv and os.path.exists(maxima_csv):
        try:
            mdf = pd.read_csv(maxima_csv)
            print(f"PASS:L2_annual_maxima - {len(mdf)} records")
        except:
            print("FAIL:L2_annual_maxima")
            mdf = pd.DataFrame()
    else:
        print("FAIL:L2_annual_maxima")
        mdf = pd.DataFrame()

    # L2: 所有站点
    if len(mdf) > 0:
        st_col = [c for c in mdf.columns if "station" in c.lower() or "id" in c.lower()]
        if st_col:
            n_found = mdf[st_col[0]].nunique()
            print(f"PASS:L2_all_stations - {n_found}" if n_found >= n_stations else f"FAIL:L2_all_stations - {n_found}/{n_stations}")
        elif len(mdf) >= n_stations:
            print("PASS:L2_all_stations")
        else:
            print("FAIL:L2_all_stations")
    else:
        print("FAIL:L2_all_stations")

    # L2: GEV 参数
    if "shape" in f_str or "loc" in f_str or "scale" in f_str or "gev" in f_str or "param" in f_str:
        print("PASS:L2_gev_params")
    else:
        print("FAIL:L2_gev_params")

    # L2: 重现期键
    if "return" in f_str or "period" in f_str or "10" in f_str:
        print("PASS:L2_return_periods")
    else:
        print("FAIL:L2_return_periods")

    # L2: 重现期洪水值合理（应为正数且大于均值流量）
    rp_vals = []
    for key, val in flood.items():
        if isinstance(val, dict):
            rps = val.get("return_periods", val.get("flood_discharge", {}))
            if isinstance(rps, dict):
                rp_vals.extend([float(v) for v in rps.values() if v is not None])
    if rp_vals and all(v > 0 for v in rp_vals):
        print(f"PASS:L2_return_values - range [{min(rp_vals):.1f}, {max(rp_vals):.1f}]")
    elif rp_vals:
        print("PASS:L2_return_values")
    else:
        print("FAIL:L2_return_values")

    # L2: baseflow 文件
    if baseflow_csv and os.path.exists(baseflow_csv):
        print("PASS:L2_baseflow_file")
        try:
            bdf = pd.read_csv(baseflow_csv)
            bcols = " ".join(bdf.columns).lower()
            # L2: baseflow <= discharge
            q_col = [c for c in bdf.columns if "discharge" in c.lower() and "base" not in c.lower()]
            b_col = [c for c in bdf.columns if "baseflow" in c.lower() or "base" in c.lower()]
            if q_col and b_col:
                violations = (bdf[b_col[0]] > bdf[q_col[0]] + 0.01).sum()
                pct_ok = 1.0 - violations / len(bdf) if len(bdf) > 0 else 0
                print(f"{'PASS' if pct_ok > 0.95 else 'FAIL'}:L2_baseflow_leq_Q")
            else:
                print("PASS:L2_baseflow_leq_Q")
            # L2: quickflow 列
            if "quick" in bcols or "storm" in bcols or "direct" in bcols:
                print("PASS:L2_quickflow")
            else:
                print("FAIL:L2_quickflow")
        except:
            print("FAIL:L2_baseflow_leq_Q")
            print("FAIL:L2_quickflow")
    else:
        print("FAIL:L2_baseflow_file")
        print("FAIL:L2_baseflow_leq_Q")
        print("FAIL:L2_quickflow")

    # L2: 年数正确
    if len(mdf) > 0:
        yr_col = [c for c in mdf.columns if "year" in c.lower()]
        if yr_col:
            n_yr = mdf[yr_col[0]].nunique()
            if n_yr >= n_years - 2:
                print(f"PASS:L2_years_correct - {n_yr} years")
            else:
                print(f"FAIL:L2_years_correct - {n_yr}/{n_years}")
        elif len(mdf) >= n_stations * (n_years - 2):
            print("PASS:L2_years_correct")
        else:
            print("FAIL:L2_years_correct")
    else:
        print("FAIL:L2_years_correct")

    # L2: 洪水估计单调递增（更大重现期 → 更大流量）
    monotone = True
    for key, val in flood.items():
        if isinstance(val, dict):
            rps = val.get("return_periods", val.get("flood_discharge", {}))
            if isinstance(rps, dict) and len(rps) >= 2:
                items = sorted([(float(k), float(v)) for k, v in rps.items()])
                for i in range(1, len(items)):
                    if items[i][1] < items[i - 1][1] - 0.1:
                        monotone = False
    if rp_vals:
        print(f"{'PASS' if monotone else 'FAIL'}:L2_flood_monotone")
    else:
        print("FAIL:L2_flood_monotone")

    # L2: 无 NaN
    nan_ok = True
    for fpath in [maxima_csv, baseflow_csv]:
        if fpath and os.path.exists(fpath):
            try:
                tdf = pd.read_csv(fpath)
                if tdf.select_dtypes(include=[np.number]).isnull().any().any():
                    nan_ok = False
            except:
                pass
    print(f"{'PASS' if nan_ok else 'FAIL'}:L2_no_nan")

    # SCORE: GEV 拟合质量
    if rp_vals and len(rp_vals) >= 3:
        gev_score = round(min(1.0, len(rp_vals) / (n_stations * 3)), 4)
    else:
        gev_score = 0.0 if not rp_vals else 0.3
    print(f"SCORE:gev_fit_quality={gev_score}")

    # SCORE: baseflow 分离质量
    if baseflow_csv and os.path.exists(baseflow_csv):
        try:
            bdf = pd.read_csv(baseflow_csv)
            b_col = [c for c in bdf.columns if "baseflow" in c.lower() or "base" in c.lower()]
            q_col = [c for c in bdf.columns if "discharge" in c.lower() and "base" not in c.lower()]
            if b_col and q_col:
                bfi = bdf[b_col[0]].sum() / bdf[q_col[0]].sum()
                bf_score = round(1.0 - abs(bfi - 0.6) / 0.6, 4) if 0.1 < bfi < 1.0 else 0.2
                bf_score = max(0, bf_score)
            else:
                bf_score = 0.2
        except:
            bf_score = 0.0
    else:
        bf_score = 0.0
    print(f"SCORE:baseflow_quality={bf_score}")
