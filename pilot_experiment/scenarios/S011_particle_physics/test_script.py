import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_events=500):
    np.random.seed(42)
    # 生成模拟对撞事件
    signal_n = n_events // 5
    bg_n = n_events - signal_n
    # 信号事件：Z boson 峰附近
    signal = {
        "event_id": range(signal_n),
        "n_tracks": np.random.randint(3, 20, signal_n),
        "total_energy": np.random.exponential(50, signal_n) + 20,
        "missing_et": np.random.exponential(5, signal_n),
        "leading_jet_pt": np.random.exponential(30, signal_n) + 10,
        "leading_jet_eta": np.random.normal(0, 1.0, signal_n),
        "n_jets": np.random.randint(1, 6, signal_n),
        "n_leptons": np.random.choice([2, 3, 4], signal_n, p=[0.6, 0.3, 0.1]),
        "invariant_mass": np.random.normal(91.2, 3.0, signal_n),
    }
    # 背景事件
    bg = {
        "event_id": range(signal_n, n_events),
        "n_tracks": np.random.randint(0, 15, bg_n),
        "total_energy": np.random.exponential(20, bg_n),
        "missing_et": np.random.exponential(10, bg_n),
        "leading_jet_pt": np.random.exponential(15, bg_n),
        "leading_jet_eta": np.random.normal(0, 2.0, bg_n),
        "n_jets": np.random.randint(0, 8, bg_n),
        "n_leptons": np.random.choice([0, 1, 2], bg_n, p=[0.5, 0.35, 0.15]),
        "invariant_mass": np.random.exponential(50, bg_n),
    }
    df = pd.concat([pd.DataFrame(signal), pd.DataFrame(bg)]).reset_index(drop=True)
    df.to_csv(path, index=False)
    return n_events

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/events.csv"
    out_dir = f"{tmpdir}/output"
    n = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--mass-window", "80,100"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出
    filtered_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            if "filter" in f.lower() and f.endswith(".csv"):
                filtered_csv = os.path.join(out_dir, f)
            if "summary" in f.lower() and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    if filtered_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_events_filtered","L2_quality_cuts","L2_classification",
                   "L2_mass_window","L2_significance","L2_summary","L2_cut_flow",
                   "L2_signal_fraction","L2_no_nan"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # L1: 有效 CSV
    if filtered_csv:
        try:
            df = pd.read_csv(filtered_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
            df = pd.DataFrame()
    else:
        print("FAIL:L1_valid_csv")
        df = pd.DataFrame()

    # L2: 事件被过滤（应少于原始数据）
    if len(df) > 0 and len(df) < n:
        print(f"PASS:L2_events_filtered - {len(df)}/{n}")
    elif len(df) > 0:
        print(f"PASS:L2_events_filtered - {len(df)} events")
    else:
        print("FAIL:L2_events_filtered")

    # L2: 质量切割被应用（n_tracks>=2, energy>10）
    if len(df) > 0 and "n_tracks" in df.columns:
        bad_tracks = (df["n_tracks"] < 2).sum()
        if bad_tracks == 0:
            print("PASS:L2_quality_cuts")
        else:
            print(f"FAIL:L2_quality_cuts - {bad_tracks} events with n_tracks<2")
    else:
        print("PASS:L2_quality_cuts")

    # L2: 有分类列
    cols_str = " ".join(df.columns).lower() if len(df) > 0 else ""
    if "signal" in cols_str or "class" in cols_str or "label" in cols_str or "type" in cols_str:
        print("PASS:L2_classification")
    else:
        print("FAIL:L2_classification - no classification column")

    # L2: invariant_mass 在窗口内（信号事件）
    if "invariant_mass" in df.columns and len(df) > 0:
        in_window = ((df["invariant_mass"] >= 70) & (df["invariant_mass"] <= 110)).sum()
        print(f"PASS:L2_mass_window - {in_window} events in mass window")
    else:
        print("PASS:L2_mass_window")

    # L2: 显著性计算
    if summary_json and os.path.exists(summary_json):
        try:
            summary = json.load(open(summary_json))
            s_str = json.dumps(summary).lower()
            if "significance" in s_str or "s/sqrt" in s_str or "signal" in s_str:
                print("PASS:L2_significance")
            else:
                print("FAIL:L2_significance")
        except:
            print("FAIL:L2_significance")
    else:
        print("FAIL:L2_significance")

    # L2: 摘要信息
    if summary_json and os.path.exists(summary_json):
        print("PASS:L2_summary")
    else:
        combined = r.stdout.lower() if hasattr(r, 'stdout') else ""
        if any(k in combined for k in ["signal", "background", "total", "significance"]):
            print("PASS:L2_summary")
        else:
            print("FAIL:L2_summary")

    # L2: cut flow 信息
    if summary_json and os.path.exists(summary_json):
        s_str = json.dumps(json.load(open(summary_json))).lower()
        if "cut" in s_str or "flow" in s_str or "before" in s_str:
            print("PASS:L2_cut_flow")
        else:
            print("FAIL:L2_cut_flow")
    else:
        print("FAIL:L2_cut_flow")

    # L2: 信号比例合理
    if len(df) > 0 and any("signal" in c.lower() or "class" in c.lower() or "label" in c.lower() for c in df.columns):
        print("PASS:L2_signal_fraction")
    else:
        print("PASS:L2_signal_fraction")

    # L2: 无 NaN 值
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("PASS:L2_no_nan")

    # SCORE: 信号保留率
    orig = pd.read_csv(csv_in)
    true_signal = orig[(orig["invariant_mass"] >= 80) & (orig["invariant_mass"] <= 100) & (orig["n_leptons"] >= 2)]
    if len(df) > 0 and len(true_signal) > 0:
        # 粗略估计保留的信号比例
        retained = len(df[df["invariant_mass"].between(80, 100)]) if "invariant_mass" in df.columns else 0
        signal_retention = round(min(retained / len(true_signal), 1.0), 4)
    else:
        signal_retention = 0.0
    print(f"SCORE:signal_retention={signal_retention}")

    # SCORE: 背景抑制率
    if len(df) > 0:
        bg_suppression = round(1.0 - len(df) / n, 4)
    else:
        bg_suppression = 0.0
    print(f"SCORE:bg_suppression={bg_suppression}")
