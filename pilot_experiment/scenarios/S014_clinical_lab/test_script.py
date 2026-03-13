import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_patients=30, n_tests_per=5):
    np.random.seed(42)
    rows = []
    test_specs = [
        ("glucose", "mg/dL", 70, 100),
        ("creatinine", "mg/dL", 0.6, 1.2),
        ("hemoglobin", "g/dL", 12.0, 17.5),
        ("potassium", "mmol/L", 3.5, 5.0),
        ("sodium", "mmol/L", 136, 145),
    ]
    base_date = pd.Timestamp("2024-01-01")
    for pid in range(n_patients):
        for test_name, unit, ref_low, ref_high in test_specs[:n_tests_per]:
            # 大部分正常，一些异常
            if np.random.rand() < 0.2:
                value = ref_high * np.random.uniform(1.1, 2.5)  # 高值
            elif np.random.rand() < 0.1:
                value = ref_low * np.random.uniform(0.3, 0.9)  # 低值
            else:
                value = np.random.uniform(ref_low, ref_high)
            ts = base_date + pd.Timedelta(days=np.random.randint(0, 365))
            rows.append({
                "patient_id": f"P{pid:03d}",
                "test_name": test_name,
                "value": round(value, 2),
                "unit": unit,
                "reference_low": ref_low,
                "reference_high": ref_high,
                "timestamp": ts.strftime("%Y-%m-%d"),
            })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_patients

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/lab_results.csv"
    csv_out = f"{tmpdir}/normalized.csv"
    json_out = f"{tmpdir}/flags.json"
    n_patients = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", csv_out, "--flag-output", json_out],
        [sys.executable, "generated.py", csv_in, "-o", csv_out],
        [sys.executable, "generated.py", "--input", csv_in, "--output", csv_out],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(csv_out):
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(csv_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_all_rows","L2_has_flag","L2_has_normalized",
                   "L2_flags_correct","L2_critical","L2_patient_summary",
                   "L2_no_nan","L2_unit_conversion","L2_abnormal_rate"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    cols = " ".join(df.columns).lower()

    # 所有行保留
    expected_rows = n_patients * 5
    if len(df) >= expected_rows - 5:
        print(f"PASS:L2_all_rows - {len(df)} rows")
    else:
        print(f"FAIL:L2_all_rows - expected ~{expected_rows}, got {len(df)}")

    # flag 列
    if "flag" in cols or "status" in cols or "abnormal" in cols:
        print("PASS:L2_has_flag")
    else:
        print("FAIL:L2_has_flag")

    # normalized_value 列
    if "normalized" in cols or "si_value" in cols or "converted" in cols:
        print("PASS:L2_has_normalized")
    else:
        print("FAIL:L2_has_normalized")

    # flag 正确性（检查明显的高值是否被标记）
    flag_col = [c for c in df.columns if "flag" in c.lower() or "status" in c.lower()]
    if flag_col:
        flags = df[flag_col[0]].astype(str).str.lower()
        has_high = (flags.str.contains("high")).any()
        has_low = (flags.str.contains("low")).any()
        has_normal = (flags.str.contains("normal")).any()
        if has_high or has_low or has_normal:
            print("PASS:L2_flags_correct")
        else:
            print("FAIL:L2_flags_correct")
    else:
        print("FAIL:L2_flags_correct")

    # critical 标记
    if "critical" in cols or "is_critical" in cols:
        print("PASS:L2_critical")
    else:
        print("FAIL:L2_critical")

    # 患者摘要
    if os.path.exists(json_out):
        try:
            summary = json.load(open(json_out))
            if len(summary) >= n_patients // 2:
                print(f"PASS:L2_patient_summary - {len(summary)} patients")
            else:
                print(f"FAIL:L2_patient_summary")
        except:
            print("FAIL:L2_patient_summary")
    else:
        print("FAIL:L2_patient_summary")

    # 无 NaN
    nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
    print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")

    # 单位转换（glucose mg/dL → mmol/L: 乘以 0.0555）
    if "normalized" in cols or "converted" in cols or "si" in cols:
        norm_col = [c for c in df.columns if "normalized" in c.lower() or "si" in c.lower() or "converted" in c.lower()]
        if norm_col:
            glucose_rows = df[df["test_name"] == "glucose"] if "test_name" in df.columns else pd.DataFrame()
            if len(glucose_rows) > 0:
                orig_val = glucose_rows["value"].iloc[0]
                norm_val = glucose_rows[norm_col[0]].iloc[0]
                expected_norm = orig_val * 0.0555
                if abs(norm_val - expected_norm) < 1.0 or norm_val != orig_val:
                    print("PASS:L2_unit_conversion")
                else:
                    print("FAIL:L2_unit_conversion - no conversion detected")
            else:
                print("PASS:L2_unit_conversion")
        else:
            print("FAIL:L2_unit_conversion")
    else:
        print("FAIL:L2_unit_conversion")

    # 异常率输出
    combined = r.stdout.lower() if hasattr(r, 'stdout') and r.stdout else ""
    if "abnormal" in combined or "rate" in combined or "%" in combined:
        print("PASS:L2_abnormal_rate")
    else:
        print("FAIL:L2_abnormal_rate")

    # SCORE: flag 准确率
    if flag_col and "value" in df.columns and "reference_high" in df.columns:
        correct = 0
        total = 0
        for _, row in df.iterrows():
            try:
                v = float(row["value"])
                rh = float(row["reference_high"])
                rl = float(row["reference_low"])
                f = str(row[flag_col[0]]).lower()
                if v > rh and "high" in f:
                    correct += 1
                elif v < rl and "low" in f:
                    correct += 1
                elif rl <= v <= rh and "normal" in f:
                    correct += 1
                total += 1
            except:
                total += 1
        flag_accuracy = round(correct / max(total, 1), 4)
    else:
        flag_accuracy = 0.0
    print(f"SCORE:flag_accuracy={flag_accuracy}")

    # SCORE: 数据完整性
    completeness = round(1.0 - df.isnull().mean().mean(), 4)
    print(f"SCORE:data_completeness={completeness}")
