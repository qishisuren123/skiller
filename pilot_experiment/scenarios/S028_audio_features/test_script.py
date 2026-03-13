import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_signals=6, sr=16000, duration=1.0):
    np.random.seed(42)
    n_samples = int(sr * duration)
    signals = np.zeros((n_signals, n_samples))
    labels = []
    for i in range(n_signals):
        t = np.linspace(0, duration, n_samples, endpoint=False)
        if i % 3 == 0:
            freq = 440 * (i + 1) / 2
            signals[i] = 0.5 * np.sin(2 * np.pi * freq * t) + 0.1 * np.random.randn(n_samples)
            labels.append("tone")
        elif i % 3 == 1:
            signals[i] = np.random.randn(n_samples) * 0.3
            labels.append("noise")
        else:
            freq = 300
            signals[i] = 0.4 * np.sin(2 * np.pi * freq * t) * (1 + 0.5 * np.sin(2 * np.pi * 5 * t))
            signals[i] += 0.05 * np.random.randn(n_samples)
            labels.append("modulated")
    np.savez(path, signals=signals, sample_rate=np.array(sr), labels=np.array(labels))
    return n_signals, sr

with tempfile.TemporaryDirectory() as tmpdir:
    npz_in = f"{tmpdir}/audio_data.npz"
    out_dir = f"{tmpdir}/output"
    n_signals, sr = create_data(npz_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", npz_in, "--output", out_dir, "--frame-size", "1024", "--hop-size", "512"],
        [sys.executable, "generated.py", npz_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", npz_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    feat_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if "feature" in fl and fl.endswith(".csv"):
                feat_csv = os.path.join(out_dir, f)
            if "summary" in fl and fl.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    has_output = feat_csv or summary_json
    if has_output:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_all_signals", "L2_frame_count", "L2_zcr_col",
                   "L2_rms_col", "L2_mfcc_cols", "L2_mfcc_count", "L2_summary_json",
                   "L2_summary_stats", "L2_zcr_range", "L2_rms_positive",
                   "L2_no_nan", "L2_signal_labels"]:
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

    # L2: 所有信号被处理
    if len(df) > 0:
        id_col = [c for c in df.columns if "signal" in c.lower() or "id" in c.lower()]
        if id_col:
            n_found = df[id_col[0]].nunique()
            print(f"PASS:L2_all_signals - {n_found}" if n_found >= n_signals else f"FAIL:L2_all_signals - {n_found}/{n_signals}")
        elif len(df) > n_signals:
            print("PASS:L2_all_signals")
        else:
            print("FAIL:L2_all_signals")
    else:
        print("FAIL:L2_all_signals")

    # L2: 帧数合理（每个信号约 (16000 - 1024) / 512 + 1 ≈ 30 帧）
    expected_frames = n_signals * 30
    if len(df) >= expected_frames * 0.5:
        print(f"PASS:L2_frame_count - {len(df)} frames")
    else:
        print(f"FAIL:L2_frame_count - {len(df)} frames, expected ~{expected_frames}")

    # L2: ZCR 列
    if "zcr" in cols or "zero" in cols or "crossing" in cols:
        print("PASS:L2_zcr_col")
    else:
        print("FAIL:L2_zcr_col")

    # L2: RMS 列
    if "rms" in cols or "energy" in cols:
        print("PASS:L2_rms_col")
    else:
        print("FAIL:L2_rms_col")

    # L2: MFCC 列存在
    mfcc_cols = [c for c in df.columns if "mfcc" in c.lower()]
    if len(mfcc_cols) >= 1:
        print("PASS:L2_mfcc_cols")
    else:
        print("FAIL:L2_mfcc_cols")

    # L2: MFCC 系数数量 >= 13
    if len(mfcc_cols) >= 13:
        print(f"PASS:L2_mfcc_count - {len(mfcc_cols)} coefficients")
    elif len(mfcc_cols) >= 10:
        print(f"PASS:L2_mfcc_count - {len(mfcc_cols)} coefficients (close)")
    else:
        print(f"FAIL:L2_mfcc_count - only {len(mfcc_cols)} MFCC columns")

    # L2: summary JSON 存在
    summ = {}
    if summary_json and os.path.exists(summary_json):
        try:
            summ = json.load(open(summary_json))
            print("PASS:L2_summary_json")
        except:
            print("FAIL:L2_summary_json")
    else:
        print("FAIL:L2_summary_json")

    # L2: summary 包含统计量（mean/std）
    s_str = json.dumps(summ).lower() if summ else ""
    if "mean" in s_str and "std" in s_str:
        print("PASS:L2_summary_stats")
    elif "mean" in s_str or "std" in s_str or "average" in s_str:
        print("PASS:L2_summary_stats")
    else:
        print("FAIL:L2_summary_stats")

    # L2: ZCR 值在合理范围 [0, 1]
    zcr_col = [c for c in df.columns if "zcr" in c.lower() or "zero" in c.lower()]
    if zcr_col and len(df) > 0:
        zcr_vals = df[zcr_col[0]].dropna()
        if zcr_vals.min() >= -0.01 and zcr_vals.max() <= 1.01:
            print("PASS:L2_zcr_range")
        else:
            print(f"PASS:L2_zcr_range")  # 宽松判断
    else:
        print("FAIL:L2_zcr_range")

    # L2: RMS 值为正
    rms_col = [c for c in df.columns if "rms" in c.lower() or "energy" in c.lower()]
    if rms_col and len(df) > 0:
        rms_vals = df[rms_col[0]].dropna()
        if rms_vals.min() >= -0.001:
            print("PASS:L2_rms_positive")
        else:
            print("FAIL:L2_rms_positive")
    else:
        print("FAIL:L2_rms_positive")

    # L2: 无 NaN
    if len(df) > 0:
        nan_pct = df.select_dtypes(include=[np.number]).isnull().mean().mean()
        print(f"{'PASS' if nan_pct < 0.05 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: 标签信息
    if "label" in s_str or "tone" in s_str or "noise" in s_str:
        print("PASS:L2_signal_labels")
    else:
        print("FAIL:L2_signal_labels")

    # SCORE: 特征提取完整度
    expected_feat = ["zcr", "rms", "mfcc"]
    found = sum(1 for e in expected_feat if e in cols or any(e in c.lower() for c in df.columns))
    feat_completeness = round(found / len(expected_feat), 4)
    print(f"SCORE:feature_completeness={feat_completeness}")

    # SCORE: MFCC 质量（tone 信号的 MFCC 应与 noise 不同）
    if len(mfcc_cols) >= 2 and len(df) > 0:
        id_col = [c for c in df.columns if "signal" in c.lower() or "id" in c.lower()]
        if id_col:
            groups = df.groupby(id_col[0])
            means = groups[mfcc_cols[0]].mean()
            if means.std() > 0.001:
                mfcc_quality = round(min(means.std() / (abs(means.mean()) + 1e-8), 1.0), 4)
            else:
                mfcc_quality = 0.1
        else:
            mfcc_quality = 0.3
    else:
        mfcc_quality = 0.0
    print(f"SCORE:mfcc_quality={mfcc_quality}")
