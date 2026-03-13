import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_events=600):
    np.random.seed(42)
    rows = []
    base_time = pd.Timestamp("2023-01-01")
    # 背景地震活动（小震）
    for i in range(n_events - 50):
        t = base_time + pd.Timedelta(hours=np.random.uniform(0, 8760))
        mag = np.random.exponential(0.8) + 1.0
        rows.append({
            "event_id": f"EQ{i:04d}",
            "datetime": t.isoformat(),
            "latitude": 35.0 + np.random.normal(0, 0.5),
            "longitude": -118.0 + np.random.normal(0, 0.5),
            "depth_km": np.random.uniform(2, 30),
            "magnitude": round(min(mag, 6.0), 1),
            "mag_type": "ML",
        })
    # 主震 + 余震序列（2 个序列）
    for seq_idx in range(2):
        main_lat = 35.0 + seq_idx * 0.3
        main_lon = -118.0 + seq_idx * 0.2
        main_time = base_time + pd.Timedelta(days=60 + seq_idx * 120)
        main_mag = 5.5 + seq_idx * 0.5
        eid = n_events - 50 + seq_idx * 25
        rows.append({
            "event_id": f"EQ{eid:04d}",
            "datetime": main_time.isoformat(),
            "latitude": main_lat,
            "longitude": main_lon,
            "depth_km": 10.0,
            "magnitude": round(main_mag, 1),
            "mag_type": "ML",
        })
        # 余震
        for j in range(1, 25):
            dt = np.random.exponential(5) + 0.1
            t = main_time + pd.Timedelta(hours=dt)
            mag = main_mag - np.random.exponential(1.0) - 0.5
            rows.append({
                "event_id": f"EQ{eid + j:04d}",
                "datetime": t.isoformat(),
                "latitude": main_lat + np.random.normal(0, 0.05),
                "longitude": main_lon + np.random.normal(0, 0.05),
                "depth_km": np.random.uniform(5, 20),
                "magnitude": round(max(mag, 1.0), 1),
                "mag_type": "ML",
            })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return len(df)

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/earthquakes.csv"
    out_dir = f"{tmpdir}/output"
    n = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--cluster-radius", "50", "--cluster-time", "72"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    stats_json = None
    aftershock_csv = None
    magfreq_csv = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("stat" in fl or "catalog" in fl) and fl.endswith(".json"):
                stats_json = os.path.join(out_dir, f)
            if "aftershock" in fl and fl.endswith(".csv"):
                aftershock_csv = os.path.join(out_dir, f)
            if ("freq" in fl or "magnitude" in fl) and fl.endswith(".csv"):
                magfreq_csv = os.path.join(out_dir, f)

    has_output = stats_json or aftershock_csv or magfreq_csv
    if has_output:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_json", "L2_b_value", "L2_completeness", "L2_largest_event",
                   "L2_aftershock_file", "L2_aftershock_content", "L2_magfreq_file",
                   "L2_magfreq_cumulative", "L2_total_events", "L2_haversine",
                   "L2_sequence_count", "L2_no_nan"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # L1: 有效 JSON
    stats = {}
    if stats_json and os.path.exists(stats_json):
        try:
            stats = json.load(open(stats_json))
            print("PASS:L1_valid_json")
        except:
            print("FAIL:L1_valid_json")
    else:
        print("FAIL:L1_valid_json")

    s_str = json.dumps(stats).lower() if stats else ""

    # L2: b-value 计算（合理范围 0.5-2.0）
    b_val = stats.get("b_value", stats.get("b", None))
    if b_val is not None and 0.3 <= float(b_val) <= 2.5:
        print(f"PASS:L2_b_value - b={b_val}")
    elif "b_value" in s_str or "b" in s_str:
        print("PASS:L2_b_value")
    else:
        print("FAIL:L2_b_value")

    # L2: 完备震级
    if "completeness" in s_str or "mc" in s_str or "complete" in s_str:
        print("PASS:L2_completeness")
    else:
        print("FAIL:L2_completeness")

    # L2: 最大事件
    if "largest" in s_str or "max" in s_str or "biggest" in s_str:
        print("PASS:L2_largest_event")
    else:
        print("FAIL:L2_largest_event")

    # L2: 余震文件存在
    if aftershock_csv and os.path.exists(aftershock_csv):
        print("PASS:L2_aftershock_file")
        try:
            adf = pd.read_csv(aftershock_csv)
            acols = " ".join(adf.columns).lower()
            if len(adf) > 0 and ("mainshock" in acols or "main" in acols or "sequence" in acols):
                print("PASS:L2_aftershock_content")
            elif len(adf) > 5:
                print("PASS:L2_aftershock_content")
            else:
                print("FAIL:L2_aftershock_content")
        except:
            print("FAIL:L2_aftershock_content")
    else:
        print("FAIL:L2_aftershock_file")
        print("FAIL:L2_aftershock_content")

    # L2: 震级频率文件
    if magfreq_csv and os.path.exists(magfreq_csv):
        print("PASS:L2_magfreq_file")
        try:
            mdf = pd.read_csv(magfreq_csv)
            mcols = " ".join(mdf.columns).lower()
            if "cumul" in mcols or "log" in mcols:
                print("PASS:L2_magfreq_cumulative")
            else:
                print("FAIL:L2_magfreq_cumulative")
        except:
            print("FAIL:L2_magfreq_cumulative")
    else:
        print("FAIL:L2_magfreq_file")
        print("FAIL:L2_magfreq_cumulative")

    # L2: 总事件数
    if "total" in s_str or "count" in s_str or "n_events" in s_str:
        print("PASS:L2_total_events")
    else:
        print("FAIL:L2_total_events")

    # L2: 距离计算（haversine — 检查余震文件中有距离列）
    if aftershock_csv and os.path.exists(aftershock_csv):
        try:
            adf = pd.read_csv(aftershock_csv)
            acols = " ".join(adf.columns).lower()
            if "dist" in acols or "km" in acols or "radius" in acols:
                print("PASS:L2_haversine")
            else:
                print("FAIL:L2_haversine")
        except:
            print("FAIL:L2_haversine")
    else:
        print("FAIL:L2_haversine")

    # L2: 检测到至少 1 个序列
    if aftershock_csv and os.path.exists(aftershock_csv):
        try:
            adf = pd.read_csv(aftershock_csv)
            id_col = [c for c in adf.columns if "main" in c.lower() or "sequence" in c.lower()]
            if id_col:
                n_seq = adf[id_col[0]].nunique()
                print(f"PASS:L2_sequence_count - {n_seq} sequences" if n_seq >= 1 else "FAIL:L2_sequence_count")
            elif len(adf) > 5:
                print("PASS:L2_sequence_count")
            else:
                print("FAIL:L2_sequence_count")
        except:
            print("FAIL:L2_sequence_count")
    else:
        print("FAIL:L2_sequence_count")

    # L2: 无 NaN
    nan_ok = True
    for fpath in [aftershock_csv, magfreq_csv]:
        if fpath and os.path.exists(fpath):
            try:
                tdf = pd.read_csv(fpath)
                if tdf.select_dtypes(include=[np.number]).isnull().any().any():
                    nan_ok = False
            except:
                pass
    print(f"{'PASS' if nan_ok else 'FAIL'}:L2_no_nan")

    # SCORE: b-value 精度（与理论值比较）
    if b_val is not None:
        try:
            orig = pd.read_csv(csv_in)
            mags = orig["magnitude"].values
            mc_est = np.round(mags.min() + 0.1 * np.argmax(np.bincount((mags * 10).astype(int))), 1)
            above = mags[mags >= mc_est]
            b_true = np.log10(np.e) / (above.mean() - mc_est + 0.05)
            b_err = abs(float(b_val) - b_true) / b_true
            b_score = round(max(0, 1.0 - b_err), 4)
        except:
            b_score = 0.3
    else:
        b_score = 0.0
    print(f"SCORE:b_value_accuracy={b_score}")

    # SCORE: 余震检测完整度
    if aftershock_csv and os.path.exists(aftershock_csv):
        try:
            adf = pd.read_csv(aftershock_csv)
            detection_ratio = round(min(len(adf) / 48.0, 1.0), 4)
        except:
            detection_ratio = 0.0
    else:
        detection_ratio = 0.0
    print(f"SCORE:aftershock_detection={detection_ratio}")
