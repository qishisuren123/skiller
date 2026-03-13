import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_points=300):
    np.random.seed(42)
    true_period = 5.73  # 天
    rows = []
    for band, offset in [("V", 0), ("B", 0.5), ("R", -0.3)]:
        times = np.sort(np.random.uniform(0, 100, n_points))
        # 正弦变光 + 噪声
        amplitude = 0.3 + np.random.uniform(-0.1, 0.1)
        phase = 2 * np.pi * times / true_period
        mag = 15.0 + offset + amplitude * np.sin(phase) + np.random.normal(0, 0.05, n_points)
        mag_err = np.abs(np.random.normal(0.05, 0.01, n_points))
        for t, m, e in zip(times, mag, mag_err):
            rows.append({"time": round(t, 4), "magnitude": round(m, 4),
                         "magnitude_error": round(e, 4), "filter_band": band})
    pd.DataFrame(rows).to_csv(path, index=False)
    return true_period

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/lightcurve.csv"
    json_out = f"{tmpdir}/periods.json"
    true_period = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", json_out],
        [sys.executable, "generated.py", csv_in, "-o", json_out],
        [sys.executable, "generated.py", "--input", csv_in, "--output", json_out, "--min-period", "0.5", "--max-period", "50"],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(json_out):
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(json_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_json","L2_all_bands","L2_period_found","L2_period_accurate",
                   "L2_significance","L2_amplitude","L2_mean_mag","L2_n_points",
                   "L2_phase_coverage","L2_reasonable_period","L2_multi_band"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        result = json.load(open(json_out))
        print("PASS:L1_valid_json")
    except:
        print("FAIL:L1_valid_json")
        sys.exit(0)

    r_str = json.dumps(result).lower()

    # 所有波段
    bands_found = [k for k in result.keys() if isinstance(result[k], dict)]
    if len(bands_found) >= 2:
        print(f"PASS:L2_all_bands - {len(bands_found)} bands")
    else:
        print(f"FAIL:L2_all_bands - only {len(bands_found)} bands")

    # 周期检测
    if "period" in r_str:
        print("PASS:L2_period_found")
    else:
        print("FAIL:L2_period_found")

    # 周期精度（应接近 5.73 天）
    periods = []
    for band, data in result.items():
        if isinstance(data, dict):
            p = data.get("best_period", data.get("period", None))
            if p is not None:
                periods.append(float(p))
    if periods and any(abs(p - true_period) < 1.0 for p in periods):
        print(f"PASS:L2_period_accurate - detected {periods[0]:.2f} (true={true_period})")
    elif periods:
        print(f"FAIL:L2_period_accurate - {periods[0]:.2f} vs true {true_period}")
    else:
        print("FAIL:L2_period_accurate")

    # 显著性
    if "significance" in r_str or "fap" in r_str or "false_alarm" in r_str or "p_value" in r_str:
        print("PASS:L2_significance")
    else:
        print("FAIL:L2_significance")

    # 振幅
    if "amplitude" in r_str or "amp" in r_str:
        print("PASS:L2_amplitude")
    else:
        print("FAIL:L2_amplitude")

    # 平均星等
    if "mean" in r_str or "average" in r_str:
        print("PASS:L2_mean_mag")
    else:
        print("FAIL:L2_mean_mag")

    # 数据点数
    if "n_points" in r_str or "count" in r_str or "n_obs" in r_str:
        print("PASS:L2_n_points")
    else:
        print("FAIL:L2_n_points")

    # 相位覆盖
    if "phase" in r_str or "coverage" in r_str:
        print("PASS:L2_phase_coverage")
    else:
        print("FAIL:L2_phase_coverage")

    # 周期在合理范围
    if periods and all(0.05 <= p <= 200 for p in periods):
        print("PASS:L2_reasonable_period")
    elif periods:
        print("FAIL:L2_reasonable_period")
    else:
        print("FAIL:L2_reasonable_period")

    # 多波段
    if len(bands_found) >= 3:
        print("PASS:L2_multi_band")
    elif len(bands_found) >= 1:
        print("PASS:L2_multi_band")
    else:
        print("FAIL:L2_multi_band")

    # SCORE: 周期精度
    if periods:
        best_err = min(abs(p - true_period) / true_period for p in periods)
        period_accuracy = round(max(0, 1.0 - best_err), 4)
    else:
        period_accuracy = 0.0
    print(f"SCORE:period_accuracy={period_accuracy}")

    # SCORE: 结果完整性
    expected_keys = ["period", "significance", "amplitude", "mean", "n_points", "phase"]
    found = sum(1 for k in expected_keys if k in r_str)
    completeness = round(found / len(expected_keys), 4)
    print(f"SCORE:result_completeness={completeness}")
