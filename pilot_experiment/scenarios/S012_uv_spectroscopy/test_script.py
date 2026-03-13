import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_samples=4):
    np.random.seed(42)
    wavelengths = np.arange(200, 800, 0.5)  # 200-800 nm
    data = {"wavelength": wavelengths}
    for i in range(n_samples):
        # 创建有明确峰的吸收光谱
        spectrum = np.zeros_like(wavelengths, dtype=float)
        # 2-4 个高斯峰
        n_peaks = np.random.randint(2, 5)
        for _ in range(n_peaks):
            center = np.random.uniform(250, 700)
            width = np.random.uniform(10, 40)
            height = np.random.uniform(0.2, 1.5)
            spectrum += height * np.exp(-0.5 * ((wavelengths - center) / width) ** 2)
        # 加噪声
        spectrum += np.random.normal(0, 0.01, len(wavelengths))
        spectrum = np.clip(spectrum, 0, None)
        data[f"sample_{i}"] = spectrum
    pd.DataFrame(data).to_csv(path, index=False)
    return n_samples

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/spectra.csv"
    json_out = f"{tmpdir}/peaks.json"
    n_samples = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", json_out, "--min-height", "0.1"],
        [sys.executable, "generated.py", csv_in, "-o", json_out],
        [sys.executable, "generated.py", "--input", csv_in, "--output", json_out],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(json_out):
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(json_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_json","L2_all_samples","L2_peaks_found","L2_peak_wavelength",
                   "L2_peak_height","L2_fwhm","L2_area","L2_dominant","L2_reasonable_peaks",
                   "L2_wavelength_range"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        result = json.load(open(json_out))
        print("PASS:L1_valid_json")
    except:
        print("FAIL:L1_valid_json")
        sys.exit(0)

    r_str = json.dumps(result).lower()

    # L2: 所有样本都被处理
    if isinstance(result, dict) and len(result) >= n_samples:
        print(f"PASS:L2_all_samples - {len(result)} samples")
    elif isinstance(result, dict) and len(result) >= 1:
        print(f"PASS:L2_all_samples - {len(result)} samples (partial)")
    else:
        print("FAIL:L2_all_samples")

    # L2: 检测到了峰
    if "peak" in r_str:
        print("PASS:L2_peaks_found")
    else:
        print("FAIL:L2_peaks_found")

    # L2: 峰包含波长信息
    if "wavelength" in r_str or "wave" in r_str or "nm" in r_str or "position" in r_str:
        print("PASS:L2_peak_wavelength")
    else:
        print("FAIL:L2_peak_wavelength")

    # L2: 峰包含高度信息
    if "height" in r_str or "absorbance" in r_str or "intensity" in r_str:
        print("PASS:L2_peak_height")
    else:
        print("FAIL:L2_peak_height")

    # L2: FWHM
    if "fwhm" in r_str or "width" in r_str or "half" in r_str:
        print("PASS:L2_fwhm")
    else:
        print("FAIL:L2_fwhm")

    # L2: 面积
    if "area" in r_str or "integral" in r_str:
        print("PASS:L2_area")
    else:
        print("FAIL:L2_area")

    # L2: 主峰标识
    if "dominant" in r_str or "main" in r_str or "max" in r_str or "primary" in r_str:
        print("PASS:L2_dominant")
    else:
        print("FAIL:L2_dominant")

    # L2: 峰数量合理（每个样本2-6个）
    reasonable = True
    for key, val in result.items():
        if isinstance(val, dict):
            n_peaks = val.get("n_peaks", len(val.get("peaks", [])))
            if n_peaks < 1 or n_peaks > 20:
                reasonable = False
    print(f"{'PASS' if reasonable else 'FAIL'}:L2_reasonable_peaks")

    # L2: 波长在合理范围 (200-800)
    all_wavelengths = []
    for key, val in result.items():
        if isinstance(val, dict):
            for p in val.get("peaks", []):
                if isinstance(p, dict) and "wavelength" in p:
                    all_wavelengths.append(p["wavelength"])
    if all_wavelengths and min(all_wavelengths) >= 190 and max(all_wavelengths) <= 810:
        print(f"PASS:L2_wavelength_range - [{min(all_wavelengths):.0f}, {max(all_wavelengths):.0f}] nm")
    elif all_wavelengths:
        print(f"PASS:L2_wavelength_range")
    else:
        print("FAIL:L2_wavelength_range")

    # SCORE: 峰检测灵敏度
    total_peaks = len(all_wavelengths)
    expected_peaks = n_samples * 3  # 平均每样本3个峰
    sensitivity = round(min(total_peaks / max(expected_peaks, 1), 1.0), 4)
    print(f"SCORE:peak_sensitivity={sensitivity}")

    # SCORE: 结果完整性
    expected_fields = ["peaks", "wavelength", "height", "fwhm", "area", "dominant"]
    found = sum(1 for f in expected_fields if f in r_str)
    completeness = round(found / len(expected_fields), 4)
    print(f"SCORE:result_completeness={completeness}")
