import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, duration=10, fs=256, n_channels=8):
    """生成模拟 EEG 数据：包含 alpha 波 + 噪声 + 50Hz 干扰"""
    np.random.seed(42)
    t = np.arange(0, duration, 1.0 / fs)
    n = len(t)
    data = {"time": np.round(t, 6)}
    for ch in range(n_channels):
        signal = np.zeros(n)
        # 基线低频漂移 (< 1 Hz)
        signal += 10 * np.sin(2 * np.pi * 0.3 * t + np.random.uniform(0, 2*np.pi))
        # Alpha 节律 (8-13 Hz) — 在一些通道中较强
        alpha_freq = np.random.uniform(9, 12)
        alpha_amp = np.random.uniform(15, 40) if ch in [2, 3, 5] else np.random.uniform(3, 8)
        signal += alpha_amp * np.sin(2 * np.pi * alpha_freq * t + np.random.uniform(0, 2*np.pi))
        # Beta 节律 (13-30 Hz)
        beta_freq = np.random.uniform(15, 25)
        signal += np.random.uniform(2, 8) * np.sin(2 * np.pi * beta_freq * t + np.random.uniform(0, 2*np.pi))
        # 50 Hz 电源干扰
        signal += 5.0 * np.sin(2 * np.pi * 50 * t + np.random.uniform(0, 2*np.pi))
        # 粉红噪声
        signal += np.random.normal(0, 5, n)
        data[f"ch{ch+1}"] = np.round(signal, 4)
    pd.DataFrame(data).to_csv(path, index=False)
    return duration, fs, n_channels

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/eeg_raw.csv"
    out_dir = f"{tmpdir}/output"
    duration, fs, n_channels = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--sample-rate", "256"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    filtered_csv = None
    psd_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("filter" in fl or "signal" in fl) and f.endswith(".csv"):
                filtered_csv = os.path.join(out_dir, f)
            if "psd" in fl and f.endswith(".csv"):
                psd_csv = os.path.join(out_dir, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    if filtered_csv or psd_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_filtered_csv", "L2_channels_present", "L2_same_length",
                   "L2_50hz_removed", "L2_low_freq_removed", "L2_psd_exists",
                   "L2_psd_frequencies", "L2_alpha_detection", "L2_dominant_freq",
                   "L2_summary_fields", "L2_amplitude_reduced", "L2_no_nan"]:
            print(f"FAIL:{t}")
        print("SCORE:noise_reduction=0.0")
        print("SCORE:analysis_completeness=0.0")
        sys.exit(0)

    # L1: 有效滤波后 CSV
    df_filt = pd.DataFrame()
    if filtered_csv:
        try:
            df_filt = pd.read_csv(filtered_csv)
            print("PASS:L1_valid_filtered_csv")
        except:
            print("FAIL:L1_valid_filtered_csv")
    else:
        print("FAIL:L1_valid_filtered_csv")

    # L2: 所有通道存在
    ch_cols = [c for c in df_filt.columns if "ch" in c.lower() or "channel" in c.lower() or c.lower().startswith("c")]
    if len(ch_cols) >= n_channels:
        print(f"PASS:L2_channels_present - {len(ch_cols)} channels")
    elif len(ch_cols) >= 1:
        print(f"PASS:L2_channels_present - {len(ch_cols)} channels (partial)")
    else:
        print("FAIL:L2_channels_present")

    # L2: 数据长度保持不变
    orig = pd.read_csv(csv_in)
    if len(df_filt) > 0 and abs(len(df_filt) - len(orig)) < 10:
        print(f"PASS:L2_same_length - {len(df_filt)} samples")
    elif len(df_filt) > 0:
        print(f"PASS:L2_same_length - {len(df_filt)} samples")
    else:
        print("FAIL:L2_same_length")

    # L2: 50Hz 已被去除（比较滤波前后 50Hz 功率）
    filt_50hz_ok = False
    if len(df_filt) > 0 and len(ch_cols) > 0:
        try:
            from scipy.signal import welch
            f_orig, pxx_orig = welch(orig["ch1"].values, fs=fs, nperseg=min(512, len(orig)))
            first_ch = ch_cols[0]
            f_filt, pxx_filt = welch(df_filt[first_ch].values, fs=fs, nperseg=min(512, len(df_filt)))
            # 找 50Hz 附近的功率
            idx_50_orig = np.argmin(np.abs(f_orig - 50))
            idx_50_filt = np.argmin(np.abs(f_filt - 50))
            if pxx_filt[idx_50_filt] < pxx_orig[idx_50_orig] * 0.5:
                filt_50hz_ok = True
                print("PASS:L2_50hz_removed")
            else:
                print("FAIL:L2_50hz_removed - 50Hz power not reduced enough")
        except:
            print("FAIL:L2_50hz_removed")
    else:
        print("FAIL:L2_50hz_removed")

    # L2: 低频漂移被移除（< 0.5 Hz 的功率降低）
    if len(df_filt) > 0 and len(ch_cols) > 0:
        try:
            from scipy.signal import welch
            f_orig, pxx_orig = welch(orig["ch1"].values, fs=fs, nperseg=min(512, len(orig)))
            first_ch = ch_cols[0]
            f_filt, pxx_filt = welch(df_filt[first_ch].values, fs=fs, nperseg=min(512, len(df_filt)))
            low_mask = f_orig < 0.5
            if np.any(low_mask) and np.sum(pxx_orig[low_mask]) > 0:
                low_mask_f = f_filt < 0.5
                ratio = np.sum(pxx_filt[low_mask_f]) / np.sum(pxx_orig[low_mask])
                if ratio < 0.5:
                    print("PASS:L2_low_freq_removed")
                else:
                    print(f"FAIL:L2_low_freq_removed - ratio={ratio:.2f}")
            else:
                print("PASS:L2_low_freq_removed")
        except:
            print("FAIL:L2_low_freq_removed")
    else:
        print("FAIL:L2_low_freq_removed")

    # L2: PSD 文件存在且可读
    df_psd = pd.DataFrame()
    if psd_csv and os.path.exists(psd_csv):
        try:
            df_psd = pd.read_csv(psd_csv)
            print("PASS:L2_psd_exists")
        except:
            print("FAIL:L2_psd_exists")
    else:
        print("FAIL:L2_psd_exists")

    # L2: PSD 有频率列
    if len(df_psd) > 0:
        psd_cols = " ".join(df_psd.columns).lower()
        if "freq" in psd_cols or "hz" in psd_cols or "f" in df_psd.columns[0].lower():
            print("PASS:L2_psd_frequencies")
        else:
            print("FAIL:L2_psd_frequencies")
    else:
        print("FAIL:L2_psd_frequencies")

    # L2: Alpha 波检测（summary 中有 alpha 信息）
    summary = {}
    if summary_json and os.path.exists(summary_json):
        try:
            summary = json.load(open(summary_json))
        except:
            pass
    s_str = json.dumps(summary).lower() if summary else ""

    if "alpha" in s_str:
        print("PASS:L2_alpha_detection")
    else:
        print("FAIL:L2_alpha_detection")

    # L2: 主频率信息
    if "dominant" in s_str or "peak" in s_str or "dominant_freq" in s_str:
        print("PASS:L2_dominant_freq")
    else:
        print("FAIL:L2_dominant_freq")

    # L2: summary 包含必要字段
    expected_fields = ["power", "amplitude", "frequency"]
    found_fields = sum(1 for f in expected_fields if f in s_str)
    if found_fields >= 2:
        print(f"PASS:L2_summary_fields - {found_fields}/{len(expected_fields)}")
    else:
        print(f"FAIL:L2_summary_fields - {found_fields}/{len(expected_fields)}")

    # L2: 滤波后振幅应该减小（去除了高频和低频噪声）
    if len(df_filt) > 0 and len(ch_cols) > 0:
        orig_std = orig["ch1"].std()
        filt_std = df_filt[ch_cols[0]].std()
        if filt_std < orig_std * 1.5:
            print(f"PASS:L2_amplitude_reduced - std {orig_std:.1f} -> {filt_std:.1f}")
        else:
            print(f"FAIL:L2_amplitude_reduced - std {orig_std:.1f} -> {filt_std:.1f}")
    else:
        print("FAIL:L2_amplitude_reduced")

    # L2: 无 NaN
    if len(df_filt) > 0:
        nan_count = df_filt.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # SCORE: 噪声抑制质量
    noise_reduction = 0.0
    if len(df_filt) > 0 and len(ch_cols) > 0:
        try:
            from scipy.signal import welch
            reductions = []
            for i, ch_name in enumerate(ch_cols[:n_channels]):
                orig_ch = f"ch{i+1}" if f"ch{i+1}" in orig.columns else orig.columns[i+1]
                f_o, p_o = welch(orig[orig_ch].values, fs=fs, nperseg=min(512, len(orig)))
                f_f, p_f = welch(df_filt[ch_name].values, fs=fs, nperseg=min(512, len(df_filt)))
                # 50Hz 功率降低比例
                idx50_o = np.argmin(np.abs(f_o - 50))
                idx50_f = np.argmin(np.abs(f_f - 50))
                if p_o[idx50_o] > 0:
                    reductions.append(max(0, 1.0 - p_f[idx50_f] / p_o[idx50_o]))
            if reductions:
                noise_reduction = round(np.mean(reductions), 4)
        except:
            pass
    print(f"SCORE:noise_reduction={noise_reduction}")

    # SCORE: 分析完整性
    features = ["filtered", "psd", "alpha", "dominant", "power", "amplitude"]
    all_str = s_str + " " + (" ".join(df_filt.columns).lower() if len(df_filt) > 0 else "")
    all_str += " " + ("filtered" if filtered_csv else "") + " " + ("psd" if psd_csv else "")
    found = sum(1 for f in features if f in all_str)
    analysis_completeness = round(found / len(features), 4)
    print(f"SCORE:analysis_completeness={analysis_completeness}")
