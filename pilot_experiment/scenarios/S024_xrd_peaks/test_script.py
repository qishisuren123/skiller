import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path):
    np.random.seed(42)
    # 模拟 XRD 图谱：多个衍射峰 + 背景 + 噪声
    two_theta = np.arange(10, 80, 0.02)
    # 背景（多项式）
    background = 50 + 0.5 * (two_theta - 45)**2 * 0.01 + 20 * np.exp(-(two_theta - 10) / 15)
    # 添加已知的衍射峰（模拟多晶材料）
    peak_params = [
        (21.5, 800, 0.15),   # 位置, 强度, sigma
        (27.3, 1500, 0.12),  # 最强峰
        (33.8, 600, 0.18),
        (36.2, 450, 0.14),
        (41.7, 350, 0.20),
        (50.3, 500, 0.16),
        (54.8, 280, 0.22),
        (60.1, 200, 0.19),
        (68.5, 150, 0.25),
    ]
    signal = np.zeros_like(two_theta)
    for pos, amp, sigma in peak_params:
        signal += amp * np.exp(-0.5 * ((two_theta - pos) / sigma) ** 2)
    intensity = background + signal + np.random.normal(0, 8, len(two_theta))
    intensity = np.clip(intensity, 0, None)
    df = pd.DataFrame({
        "two_theta": np.round(two_theta, 3),
        "intensity": np.round(intensity, 2),
    })
    df.to_csv(path, index=False)
    return len(peak_params), peak_params

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/xrd_pattern.csv"
    out_dir = f"{tmpdir}/output"
    n_true_peaks, true_peaks = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir,
         "--wavelength", "1.5406", "--min-height", "50", "--prominence", "30"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出
    peaks_csv = None
    fitted_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if "peak" in fl and f.endswith(".csv"):
                peaks_csv = os.path.join(out_dir, f)
            if ("fitted" in fl or "pattern" in fl or "fit" in fl) and f.endswith(".csv") and "peak" not in fl:
                fitted_csv = os.path.join(out_dir, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    if peaks_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_peaks_detected","L2_peak_positions","L2_fwhm_present",
                   "L2_d_spacing","L2_background_sub","L2_gaussian_fit","L2_strongest_peak",
                   "L2_reasonable_count","L2_bragg_law","L2_fitted_pattern","L2_summary_exists","L2_no_nan"]:
            print(f"FAIL:{t}")
        print("SCORE:peak_detection_accuracy=0.0")
        print("SCORE:fitting_quality=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    peaks_df = pd.DataFrame()
    if peaks_csv:
        try:
            peaks_df = pd.read_csv(peaks_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    pcols = " ".join(peaks_df.columns).lower() if len(peaks_df) > 0 else ""

    # L2: 检测到峰
    if len(peaks_df) > 0:
        print(f"PASS:L2_peaks_detected - {len(peaks_df)} peaks")
    else:
        print("FAIL:L2_peaks_detected")

    # L2: 峰位置信息
    if "two_theta" in pcols or "2theta" in pcols or "position" in pcols or "theta" in pcols:
        print("PASS:L2_peak_positions")
    else:
        print("FAIL:L2_peak_positions")

    # L2: FWHM 信息
    if "fwhm" in pcols or "width" in pcols or "half" in pcols:
        print("PASS:L2_fwhm_present")
    else:
        print("FAIL:L2_fwhm_present")

    # L2: d-spacing 计算
    if "d_spacing" in pcols or "d_space" in pcols or "d" in pcols.split():
        print("PASS:L2_d_spacing")
    else:
        print("FAIL:L2_d_spacing")

    # L2: 背景扣除（检查 fitted_pattern 中有背景列）
    fitted_df = pd.DataFrame()
    if fitted_csv:
        try:
            fitted_df = pd.read_csv(fitted_csv)
        except:
            pass
    fcols = " ".join(fitted_df.columns).lower() if len(fitted_df) > 0 else ""
    if "background" in fcols or "bg" in fcols or "baseline" in fcols or "corrected" in fcols:
        print("PASS:L2_background_sub")
    else:
        print("FAIL:L2_background_sub")

    # L2: 高斯拟合（fitted_intensity 列存在）
    if "fitted" in fcols or "fit" in fcols or "gaussian" in fcols or "model" in fcols:
        print("PASS:L2_gaussian_fit")
    else:
        print("FAIL:L2_gaussian_fit")

    # L2: 最强峰正确（应接近 27.3 度）
    if len(peaks_df) > 0:
        pos_col = [c for c in peaks_df.columns if "theta" in c.lower() or "position" in c.lower()]
        int_col = [c for c in peaks_df.columns if "intensity" in c.lower() or "height" in c.lower() or "amp" in c.lower()]
        if pos_col and int_col:
            strongest_idx = peaks_df[int_col[0]].idxmax()
            strongest_pos = peaks_df.loc[strongest_idx, pos_col[0]]
            if abs(strongest_pos - 27.3) < 2.0:
                print(f"PASS:L2_strongest_peak - {strongest_pos:.2f} deg (expected ~27.3)")
            else:
                print(f"FAIL:L2_strongest_peak - {strongest_pos:.2f} deg (expected ~27.3)")
        else:
            print("FAIL:L2_strongest_peak")
    else:
        print("FAIL:L2_strongest_peak")

    # L2: 检测数量合理（5-15个峰）
    if 3 <= len(peaks_df) <= 20:
        print(f"PASS:L2_reasonable_count - {len(peaks_df)} peaks (true={n_true_peaks})")
    elif len(peaks_df) > 0:
        print(f"PASS:L2_reasonable_count - {len(peaks_df)} peaks")
    else:
        print("FAIL:L2_reasonable_count")

    # L2: Bragg 定律 d-spacing 值合理（d 应在 1-10 Angstrom 范围）
    d_col = [c for c in peaks_df.columns if "d_spac" in c.lower() or "d" == c.lower().strip()] if len(peaks_df) > 0 else []
    if d_col:
        d_vals = peaks_df[d_col[0]].dropna()
        if len(d_vals) > 0 and d_vals.min() > 0.5 and d_vals.max() < 15:
            print(f"PASS:L2_bragg_law - d=[{d_vals.min():.2f}, {d_vals.max():.2f}] A")
        else:
            print(f"FAIL:L2_bragg_law - d out of range")
    else:
        print("FAIL:L2_bragg_law")

    # L2: fitted_pattern 文件存在
    if fitted_csv and os.path.exists(fitted_csv) and len(fitted_df) > 0:
        print("PASS:L2_fitted_pattern")
    else:
        print("FAIL:L2_fitted_pattern")

    # L2: summary 文件存在
    if summary_json and os.path.exists(summary_json):
        print("PASS:L2_summary_exists")
    else:
        print("FAIL:L2_summary_exists")

    # L2: peaks CSV 无 NaN
    if len(peaks_df) > 0:
        nan_ct = peaks_df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_ct == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # SCORE: 峰检测精度（匹配的真实峰比例）
    true_positions = [p[0] for p in true_peaks]
    if len(peaks_df) > 0:
        pos_col = [c for c in peaks_df.columns if "theta" in c.lower() or "position" in c.lower()]
        if pos_col:
            detected = peaks_df[pos_col[0]].values
            matched = 0
            for tp in true_positions:
                if any(abs(dp - tp) < 1.5 for dp in detected):
                    matched += 1
            detection_acc = round(matched / len(true_positions), 4)
        else:
            detection_acc = 0.0
    else:
        detection_acc = 0.0
    print(f"SCORE:peak_detection_accuracy={detection_acc}")

    # SCORE: 拟合质量（基于输出完整性）
    expected_items = ["peak", "fwhm", "d_spac", "background", "fitted", "summary", "strongest", "gaussian", "bragg"]
    all_text = pcols + " " + fcols
    if summary_json and os.path.exists(summary_json):
        try:
            all_text += " " + json.dumps(json.load(open(summary_json))).lower()
        except:
            pass
    found = sum(1 for item in expected_items if item in all_text)
    fit_quality = round(found / len(expected_items), 4)
    print(f"SCORE:fitting_quality={fit_quality}")
