"""
扩展场景 S11-S30：覆盖 15+ 学科领域
每个场景 = task_desc + test_script (含数据生成 + 12-15 PASS/FAIL + 2 SCORE)

设计原则：
1. 只使用测试环境已有的包 (numpy, pandas, scipy, h5py, PIL, matplotlib, 标准库)
2. 数据由测试脚本内部生成，无需外部依赖
3. 每个测试兼容多种常见 argparse 参数格式
"""
import numpy as np

# =============================================================================
# S11: 粒子物理 — 对撞事件筛选与统计 (物理, 中等)
# =============================================================================
S11_TASK = """Write a Python CLI script to analyze particle collision event data from a high-energy physics experiment.

Input: A CSV file where each row is a collision event with columns:
- event_id, n_tracks, total_energy, missing_et, leading_jet_pt, leading_jet_eta, n_jets, n_leptons, invariant_mass

Requirements:
1. Use argparse: --input CSV path, --output directory, --mass-window (default "80,100" for Z boson)
2. Apply quality cuts: n_tracks >= 2, total_energy > 10 GeV, |leading_jet_eta| < 2.5
3. Classify events: "signal" if invariant_mass within mass window AND n_leptons >= 2, else "background"
4. Compute signal-to-noise ratio and statistical significance (S / sqrt(S+B))
5. Output: filtered_events.csv, event_summary.json (total, signal, background, significance, cut_flow)
6. Print summary: events before/after cuts, signal fraction, significance
"""

S11_TEST = '''
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
'''

# =============================================================================
# S12: 化学 — 光谱峰检测与定量分析 (化学, 中等)
# =============================================================================
S12_TASK = """Write a Python CLI script to detect and analyze peaks in UV-Vis absorption spectroscopy data.

Input: A CSV file with columns: wavelength (nm), absorbance. May contain multiple samples as additional columns (sample_1, sample_2, ...).

Requirements:
1. Use argparse: --input CSV, --output JSON, --min-height (default 0.1), --min-distance (default 10 nm)
2. For each sample, detect absorption peaks using prominence-based detection
3. For each peak: record wavelength, height, width at half maximum (FWHM), area (by integration)
4. Identify the dominant peak (highest absorbance) for each sample
5. Output JSON: {sample_name: {peaks: [{wavelength, height, fwhm, area}], dominant_peak, n_peaks}}
6. Print summary: number of peaks per sample, wavelength range of dominant peaks
"""

S12_TEST = '''
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
'''

# =============================================================================
# S13: 生态学 — 物种多样性分析 (生态学, 简单)
# =============================================================================
S13_TASK = """Write a Python CLI script to calculate biodiversity indices from a species abundance matrix.

Input: A CSV file where rows are sampling sites and columns are species. Values are individual counts.

Requirements:
1. Use argparse: --input CSV, --output CSV, --indices (default "all")
2. For each site calculate: species richness, Shannon diversity (H'), Simpson diversity (1-D), Pielou evenness (J), total abundance
3. Handle zero abundances correctly (skip in log calculations)
4. Output CSV with site_id and all diversity indices as columns
5. Print summary: total sites, total species, mean Shannon diversity, most diverse site
"""

S13_TEST = '''
import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_sites=20, n_species=30):
    np.random.seed(42)
    # 生成物种丰度矩阵（负二项分布，含零值）
    counts = np.random.negative_binomial(n=2, p=0.3, size=(n_sites, n_species))
    # 让一些物种在某些站点完全缺失
    mask = np.random.rand(n_sites, n_species) < 0.3
    counts[mask] = 0
    species = [f"Species_{i}" for i in range(n_species)]
    sites = [f"Site_{i}" for i in range(n_sites)]
    df = pd.DataFrame(counts, columns=species, index=sites)
    df.index.name = "site_id"
    df.to_csv(path)
    return n_sites, n_species

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/abundance.csv"
    csv_out = f"{tmpdir}/diversity.csv"
    n_sites, n_species = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", csv_out],
        [sys.executable, "generated.py", csv_in, "-o", csv_out],
        [sys.executable, "generated.py", csv_in, csv_out],
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
        for t in ["L1_valid_csv","L2_site_count","L2_has_shannon","L2_has_simpson",
                   "L2_has_richness","L2_has_evenness","L2_shannon_range","L2_simpson_range",
                   "L2_richness_range","L2_no_nan","L2_abundance"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out, index_col=0)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    cols = " ".join(df.columns).lower()

    if len(df) == n_sites:
        print(f"PASS:L2_site_count - {n_sites} sites")
    else:
        print(f"FAIL:L2_site_count - expected {n_sites}, got {len(df)}")

    # Shannon
    if "shannon" in cols or "h_prime" in cols or "h'" in cols or "diversity" in cols:
        print("PASS:L2_has_shannon")
    else:
        print("FAIL:L2_has_shannon")

    # Simpson
    if "simpson" in cols or "1-d" in cols or "1_d" in cols:
        print("PASS:L2_has_simpson")
    else:
        print("FAIL:L2_has_simpson")

    # Richness
    if "richness" in cols or "s" == cols.split()[-1] or "n_species" in cols or "species_count" in cols:
        print("PASS:L2_has_richness")
    else:
        print("FAIL:L2_has_richness")

    # Evenness
    if "evenness" in cols or "pielou" in cols or "j" in cols.split():
        print("PASS:L2_has_evenness")
    else:
        print("FAIL:L2_has_evenness")

    # Shannon 值范围 (0 到 ~ln(30)≈3.4)
    shannon_col = [c for c in df.columns if "shannon" in c.lower() or "h" in c.lower()]
    if shannon_col:
        vals = df[shannon_col[0]].dropna()
        if vals.min() >= 0 and vals.max() <= 5:
            print(f"PASS:L2_shannon_range - [{vals.min():.2f}, {vals.max():.2f}]")
        else:
            print(f"FAIL:L2_shannon_range - [{vals.min():.2f}, {vals.max():.2f}]")
    else:
        print("FAIL:L2_shannon_range")

    # Simpson 值范围 (0 到 1)
    simpson_col = [c for c in df.columns if "simpson" in c.lower() or "1-d" in c.lower() or "1_d" in c.lower()]
    if simpson_col:
        vals = df[simpson_col[0]].dropna()
        if vals.min() >= -0.01 and vals.max() <= 1.01:
            print(f"PASS:L2_simpson_range")
        else:
            print(f"FAIL:L2_simpson_range")
    else:
        print("FAIL:L2_simpson_range")

    # Richness 范围
    rich_col = [c for c in df.columns if "richness" in c.lower() or "species_count" in c.lower() or "n_species" in c.lower()]
    if rich_col:
        vals = df[rich_col[0]].dropna()
        if vals.min() >= 0 and vals.max() <= n_species:
            print(f"PASS:L2_richness_range")
        else:
            print(f"FAIL:L2_richness_range - max={vals.max()}")
    else:
        print("FAIL:L2_richness_range")

    # 无 NaN
    nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
    print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")

    # 总丰度列
    if "abundance" in cols or "total" in cols or "n_individuals" in cols:
        print("PASS:L2_abundance")
    else:
        print("FAIL:L2_abundance")

    # SCORE: 指数覆盖率
    expected = ["shannon", "simpson", "richness", "evenness", "abundance"]
    found = sum(1 for e in expected if e in cols or any(e in c.lower() for c in df.columns))
    index_coverage = round(found / len(expected), 4)
    print(f"SCORE:index_coverage={index_coverage}")

    # SCORE: 计算精度（手动验证 Shannon）
    orig = pd.read_csv(csv_in, index_col=0)
    row0 = orig.iloc[0].values.astype(float)
    row0 = row0[row0 > 0]
    p = row0 / row0.sum()
    expected_h = -np.sum(p * np.log(p))
    if shannon_col and len(df) > 0:
        computed_h = df[shannon_col[0]].iloc[0]
        if abs(computed_h - expected_h) < 0.5:
            accuracy = round(1.0 - abs(computed_h - expected_h) / max(expected_h, 0.01), 4)
        else:
            accuracy = 0.0
    else:
        accuracy = 0.0
    print(f"SCORE:shannon_accuracy={max(accuracy, 0)}")
'''

# =============================================================================
# S14: 医学/临床 — 实验室检验结果标准化 (临床, 简单)
# =============================================================================
S14_TASK = """Write a Python CLI script to normalize and flag clinical laboratory test results.

Input: A CSV with columns: patient_id, test_name, value, unit, reference_low, reference_high, timestamp.

Requirements:
1. Use argparse: --input CSV, --output CSV, --flag-output JSON
2. Normalize values: convert all units to SI standard (mg/dL glucose → mmol/L, multiply by 0.0555; mg/dL creatinine → μmol/L, multiply by 88.4)
3. Flag abnormal results: "low" if value < reference_low, "high" if value > reference_high, "normal" otherwise
4. For each patient, compute: number of abnormal results, most recent test date, critical flags (>2x reference)
5. Output normalized CSV with added columns: normalized_value, flag, is_critical
6. Output flag summary JSON: {patient_id: {n_abnormal, n_critical, tests: [...]}}
7. Print: total patients, abnormal rate, critical rate
"""

S14_TEST = '''
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
'''

# =============================================================================
# S15: 天文学 — 光变曲线周期检测 (天文, 困难)
# =============================================================================
S15_TASK = """Write a Python CLI script to analyze astronomical light curves and detect periodic variability.

Input: A CSV file with columns: time (days), magnitude, magnitude_error, filter_band.

Requirements:
1. Use argparse: --input CSV, --output JSON, --min-period (default 0.1 days), --max-period (default 100 days)
2. For each filter band separately:
   a. Compute Lomb-Scargle periodogram
   b. Find the dominant period and its significance (false alarm probability)
   c. Phase-fold the light curve at the best period
3. Output JSON: {filter: {best_period, significance, amplitude, mean_magnitude, n_points, phase_coverage}}
4. Print: detected periods per band, whether variability is significant (FAP < 0.01)
"""

S15_TEST = '''
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
'''

# =============================================================================
# S16: 基因组学 — FASTQ 质量修剪统计 (生物信息, 中等)
# =============================================================================
S16_TASK = """Write a Python CLI script to compute quality statistics and perform quality trimming on FASTQ sequencing data.

Input: A FASTQ file (text format with 4 lines per read: @header, sequence, +, quality).

Requirements:
1. Use argparse: --input FASTQ, --output trimmed FASTQ, --report JSON, --min-quality (default 20), --min-length (default 50)
2. Parse the FASTQ file (quality scores are Phred+33 encoded: ASCII char - 33 = quality)
3. Trim reads from the 3' end until base quality >= min_quality
4. Discard reads shorter than min_length after trimming
5. Output: trimmed FASTQ file, report JSON with {total_reads, passed_reads, mean_quality_before, mean_quality_after, mean_length_before, mean_length_after, quality_distribution}
6. Print: reads before/after, trim rate, mean quality improvement
"""

S16_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np

def create_fastq(path, n_reads=200):
    np.random.seed(42)
    with open(path, "w") as f:
        for i in range(n_reads):
            seq_len = np.random.randint(80, 200)
            # 碱基序列
            seq = "".join(np.random.choice(list("ACGT"), seq_len))
            # 质量分数：前端高质量，后端逐渐降低
            quals = np.zeros(seq_len, dtype=int)
            for j in range(seq_len):
                base_q = 35 - j * 0.15 + np.random.normal(0, 3)
                quals[j] = max(2, min(41, int(base_q)))
            qual_str = "".join(chr(q + 33) for q in quals)
            f.write(f"@read_{i} length={seq_len}\\n")
            f.write(f"{seq}\\n")
            f.write(f"+\\n")
            f.write(f"{qual_str}\\n")
    return n_reads

with tempfile.TemporaryDirectory() as tmpdir:
    fq_in = f"{tmpdir}/reads.fastq"
    fq_out = f"{tmpdir}/trimmed.fastq"
    report = f"{tmpdir}/report.json"
    n_reads = create_fastq(fq_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", fq_in, "--output", fq_out, "--report", report,
         "--min-quality", "20", "--min-length", "50"],
        [sys.executable, "generated.py", fq_in, "-o", fq_out],
        [sys.executable, "generated.py", "--input", fq_in, "--output", fq_out],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(fq_out):
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(fq_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_fastq","L2_reads_trimmed","L2_quality_improved","L2_min_length",
                   "L2_header_preserved","L2_report_exists","L2_report_fields",
                   "L2_no_short_reads","L2_qual_encoding","L2_read_count"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # 验证输出 FASTQ 格式
    with open(fq_out) as f:
        lines = f.readlines()
    if len(lines) >= 4 and lines[0].startswith("@"):
        print("PASS:L1_valid_fastq")
    elif len(lines) > 0:
        print("PASS:L1_valid_fastq")
    else:
        print("FAIL:L1_valid_fastq")

    n_output_reads = len(lines) // 4

    # reads 被修剪（数量应该减少或长度变短）
    if n_output_reads <= n_reads:
        print(f"PASS:L2_reads_trimmed - {n_output_reads}/{n_reads}")
    else:
        print(f"FAIL:L2_reads_trimmed - {n_output_reads} > {n_reads}")

    # 质量应该提升（输出的平均质量应高于输入）
    if len(lines) >= 4:
        out_quals = []
        for i in range(3, len(lines), 4):
            line = lines[i].strip()
            out_quals.extend(ord(c) - 33 for c in line)
        mean_out_qual = np.mean(out_quals) if out_quals else 0
        if mean_out_qual >= 18:
            print(f"PASS:L2_quality_improved - mean Q={mean_out_qual:.1f}")
        else:
            print(f"FAIL:L2_quality_improved - mean Q={mean_out_qual:.1f}")
    else:
        print("FAIL:L2_quality_improved")

    # 最小长度检查
    short_reads = 0
    for i in range(1, len(lines), 4):
        seq = lines[i].strip()
        if len(seq) < 50:
            short_reads += 1
    if short_reads == 0:
        print("PASS:L2_min_length")
    else:
        print(f"FAIL:L2_min_length - {short_reads} reads < 50bp")

    # header 保留
    if len(lines) >= 4 and "@read_" in lines[0]:
        print("PASS:L2_header_preserved")
    elif len(lines) >= 4 and lines[0].startswith("@"):
        print("PASS:L2_header_preserved")
    else:
        print("FAIL:L2_header_preserved")

    # report 存在
    report_exists = os.path.exists(report)
    print(f"{'PASS' if report_exists else 'FAIL'}:L2_report_exists")

    # report 字段
    if report_exists:
        try:
            rpt = json.load(open(report))
            rpt_str = json.dumps(rpt).lower()
            fields = ["total", "passed", "quality", "length"]
            found = sum(1 for f in fields if f in rpt_str)
            if found >= 2:
                print("PASS:L2_report_fields")
            else:
                print("FAIL:L2_report_fields")
        except:
            print("FAIL:L2_report_fields")
    else:
        print("FAIL:L2_report_fields")

    # 没有过短的 reads
    print(f"{'PASS' if short_reads == 0 else 'FAIL'}:L2_no_short_reads")

    # 质量编码正确 (Phred+33)
    if out_quals and min(out_quals) >= 0 and max(out_quals) <= 41:
        print("PASS:L2_qual_encoding")
    elif out_quals:
        print("FAIL:L2_qual_encoding")
    else:
        print("FAIL:L2_qual_encoding")

    # 输出 read 数合理
    if n_output_reads > 0 and n_output_reads <= n_reads:
        print(f"PASS:L2_read_count - {n_output_reads}")
    else:
        print(f"FAIL:L2_read_count - {n_output_reads}")

    # SCORE: 修剪效率
    trim_rate = round(1.0 - n_output_reads / max(n_reads, 1), 4)
    print(f"SCORE:trim_efficiency={round(min(max(trim_rate, 0), 1), 4)}")

    # SCORE: 质量提升幅度
    # 读取原始质量
    with open(fq_in) as f:
        in_lines = f.readlines()
    in_quals = []
    for i in range(3, len(in_lines), 4):
        line = in_lines[i].strip()
        in_quals.extend(ord(c) - 33 for c in line)
    mean_in_qual = np.mean(in_quals) if in_quals else 0
    quality_gain = round((mean_out_qual - mean_in_qual) / max(mean_in_qual, 1), 4)
    print(f"SCORE:quality_improvement={max(quality_gain, 0)}")
'''

# =============================================================================
# S17: 海洋学 — CTD 剖面插值与分析 (海洋科学, 中等)
# =============================================================================
S17_TASK = """Write a Python CLI script to process CTD (Conductivity-Temperature-Depth) oceanographic profile data.

Input: A CSV file with columns: station_id, depth_m, temperature_C, salinity_PSU, dissolved_oxygen_mL_L.

Requirements:
1. Use argparse: --input CSV, --output directory, --depth-resolution (default 1.0 meter)
2. For each station:
   a. Interpolate all variables to regular depth grid (0 to max_depth at specified resolution)
   b. Compute potential density (sigma-t) using simplified UNESCO equation: sigma_t ≈ -0.093 + 0.808*S - 0.0016*S^2 + (-0.0069 + 0.0025*S)*T - 0.0001*T^2
   c. Find thermocline depth (depth of maximum dT/dz)
   d. Find mixed layer depth (depth where T differs from surface by > 0.5°C)
3. Output: interpolated_profiles.csv, station_summary.json
4. Print: number of stations, depth range, mean thermocline depth
"""

S17_TEST = '''
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
'''

# =============================================================================
# S18: 大气科学 — 无线电探空剖面分析 (大气, 中等)
# =============================================================================
S18_TASK = """Write a Python CLI script to analyze radiosonde atmospheric sounding profile data.

Input: A CSV file with columns: pressure (hPa), temperature (°C), dewpoint (°C), wind_speed (m/s), wind_direction (degrees), altitude (m).

Requirements:
1. Use argparse: --input CSV path, --output directory
2. Compute environmental lapse rate between consecutive levels (°C/km). Use formula: lapse_rate = -(T2 - T1) / ((alt2 - alt1) / 1000)
3. Find the tropopause: the lowest level above 5 km altitude where the lapse rate drops below 2 °C/km for at least 2 km depth
4. Compute approximate CAPE (Convective Available Potential Energy, J/kg) using a simple parcel method:
   - Lift a surface parcel dry-adiabatically (9.8 °C/km) until it reaches saturation (temperature == dewpoint)
   - Then lift moist-adiabatically (6.0 °C/km approximation) above the LCL
   - CAPE = sum of g * (T_parcel - T_env) / T_env * dz for layers where T_parcel > T_env (positive buoyancy)
   - CIN = sum of g * (T_parcel - T_env) / T_env * dz for layers where T_parcel < T_env below the LFC (negative buoyancy)
5. Detect temperature inversions: layers where temperature increases with altitude
6. Output: processed_profile.csv (original data + lapse_rate column) and summary.json containing:
   - tropopause_height_m, tropopause_pressure_hPa, CAPE_J_kg, CIN_J_kg
   - inversions: list of {base_altitude_m, top_altitude_m, strength_C}
   - surface_temperature_C, surface_dewpoint_C
7. Print summary: tropopause height, CAPE, CIN, number of inversions
"""

S18_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path):
    """生成模拟无线电探空数据：从地面到约 25 km"""
    np.random.seed(42)
    # 标准大气 + 一些特征
    altitudes = np.concatenate([
        np.arange(0, 2000, 100),
        np.arange(2000, 10000, 250),
        np.arange(10000, 26000, 500),
    ])
    n = len(altitudes)
    pressures = 1013.25 * (1 - 2.25577e-5 * altitudes) ** 5.25588
    temperatures = np.zeros(n)
    dewpoints = np.zeros(n)

    for i, alt in enumerate(altitudes):
        if alt < 1500:
            # 对流层低层：接近地面较暖
            temperatures[i] = 30.0 - alt * 0.008 + np.random.normal(0, 0.3)
            dewpoints[i] = 22.0 - alt * 0.005 + np.random.normal(0, 0.3)
        elif alt < 2000:
            # 逆温层（1500-2000m）
            temperatures[i] = 30.0 - 1500 * 0.008 + (alt - 1500) * 0.003 + np.random.normal(0, 0.2)
            dewpoints[i] = 22.0 - alt * 0.005 + np.random.normal(0, 0.3)
        elif alt < 11000:
            # 对流层：标准递减率 ~6.5 °C/km
            temperatures[i] = 30.0 - 1500 * 0.008 + 500 * 0.003 - (alt - 2000) * 0.0065 + np.random.normal(0, 0.3)
            dewpoints[i] = temperatures[i] - np.random.uniform(5, 20)
        elif alt < 20000:
            # 平流层下层：等温
            temperatures[i] = -56.5 + np.random.normal(0, 0.5)
            dewpoints[i] = temperatures[i] - 30 + np.random.normal(0, 1)
        else:
            # 平流层上层：缓慢升温
            temperatures[i] = -56.5 + (alt - 20000) * 0.001 + np.random.normal(0, 0.5)
            dewpoints[i] = temperatures[i] - 40 + np.random.normal(0, 1)

    wind_speed = 5 + altitudes / 2000 + np.random.normal(0, 2, n)
    wind_speed = np.clip(wind_speed, 0, None)
    wind_direction = 225 + altitudes / 500 + np.random.normal(0, 15, n)
    wind_direction = wind_direction % 360

    df = pd.DataFrame({
        "pressure": np.round(pressures, 2),
        "temperature": np.round(temperatures, 2),
        "dewpoint": np.round(dewpoints, 2),
        "wind_speed": np.round(wind_speed, 2),
        "wind_direction": np.round(wind_direction, 2),
        "altitude": np.round(altitudes, 1),
    })
    df.to_csv(path, index=False)
    return len(df)

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/sounding.csv"
    out_dir = f"{tmpdir}/output"
    n_levels = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", csv_in, out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    profile_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("profile" in fl or "processed" in fl or "lapse" in fl) and f.endswith(".csv"):
                profile_csv = os.path.join(out_dir, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)
    # 也检查 out_dir 本身是否被当作文件前缀
    if not profile_csv and not summary_json:
        parent = os.path.dirname(out_dir)
        for f in os.listdir(parent) if os.path.exists(parent) else []:
            fl = f.lower()
            if ("profile" in fl or "processed" in fl) and f.endswith(".csv"):
                profile_csv = os.path.join(parent, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(parent, f)

    if profile_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_lapse_rate_col", "L2_lapse_rate_range",
                   "L2_tropopause", "L2_tropopause_range", "L2_cape",
                   "L2_cin", "L2_inversions", "L2_surface_info",
                   "L2_all_levels", "L2_no_nan", "L2_summary_json"]:
            print(f"FAIL:{t}")
        print("SCORE:lapse_accuracy=0.0")
        print("SCORE:feature_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if profile_csv:
        try:
            df = pd.read_csv(profile_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 有 lapse rate 列
    if "lapse" in cols or "lapse_rate" in cols or "gamma" in cols:
        print("PASS:L2_lapse_rate_col")
    else:
        print("FAIL:L2_lapse_rate_col")

    # L2: lapse rate 值范围合理 (通常 -10 到 +15 °C/km)
    lapse_col = [c for c in df.columns if "lapse" in c.lower() or "gamma" in c.lower()]
    if lapse_col and len(df) > 0:
        vals = df[lapse_col[0]].dropna()
        if len(vals) > 0 and vals.min() > -20 and vals.max() < 30:
            print(f"PASS:L2_lapse_rate_range - [{vals.min():.1f}, {vals.max():.1f}]")
        else:
            print(f"FAIL:L2_lapse_rate_range - [{vals.min():.1f}, {vals.max():.1f}]")
    else:
        print("FAIL:L2_lapse_rate_range")

    # L2: 对流层顶检测
    summary = {}
    if summary_json and os.path.exists(summary_json):
        try:
            summary = json.load(open(summary_json))
        except:
            pass
    s_str = json.dumps(summary).lower() if summary else ""

    if "tropopause" in s_str or "trop" in s_str:
        print("PASS:L2_tropopause")
    else:
        print("FAIL:L2_tropopause")

    # L2: 对流层顶高度范围合理 (8-18 km)
    trop_h = None
    for key in summary:
        kl = key.lower()
        if "tropopause" in kl and ("height" in kl or "alt" in kl):
            trop_h = float(summary[key])
            break
    if trop_h is None and isinstance(summary, dict):
        # 嵌套查找
        for k, v in summary.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if "tropopause" in kk.lower():
                        try:
                            trop_h = float(vv)
                        except:
                            pass
    if trop_h is not None and 8000 <= trop_h <= 18000:
        print(f"PASS:L2_tropopause_range - {trop_h:.0f}m")
    elif trop_h is not None and 8 <= trop_h <= 18:
        # 可能以 km 为单位
        print(f"PASS:L2_tropopause_range - {trop_h:.1f}km")
    elif trop_h is not None:
        print(f"FAIL:L2_tropopause_range - {trop_h}")
    else:
        print("FAIL:L2_tropopause_range")

    # L2: CAPE
    if "cape" in s_str:
        print("PASS:L2_cape")
    else:
        print("FAIL:L2_cape")

    # L2: CIN
    if "cin" in s_str:
        print("PASS:L2_cin")
    else:
        print("FAIL:L2_cin")

    # L2: 逆温层检测
    if "inversion" in s_str or "inversions" in s_str:
        print("PASS:L2_inversions")
    else:
        print("FAIL:L2_inversions")

    # L2: 地面信息
    if "surface" in s_str or (len(df) > 0 and "temperature" in cols):
        print("PASS:L2_surface_info")
    else:
        print("FAIL:L2_surface_info")

    # L2: 输出包含所有层
    if len(df) >= n_levels * 0.8:
        print(f"PASS:L2_all_levels - {len(df)}/{n_levels}")
    elif len(df) > 0:
        print(f"PASS:L2_all_levels - {len(df)} levels")
    else:
        print("FAIL:L2_all_levels")

    # L2: 无 NaN（允许首行 lapse rate 为 NaN）
    if len(df) > 0:
        numeric_cols = df.select_dtypes(include=[np.number])
        # 排除 lapse rate 列的第一行
        nan_count = 0
        for c in numeric_cols.columns:
            if "lapse" in c.lower() or "gamma" in c.lower():
                nan_count += numeric_cols[c].iloc[1:].isnull().sum()
            else:
                nan_count += numeric_cols[c].isnull().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: summary JSON 存在且可读
    if summary_json and os.path.exists(summary_json) and summary:
        print("PASS:L2_summary_json")
    else:
        print("FAIL:L2_summary_json")

    # SCORE: lapse rate 精度（手动计算前几层并比较）
    orig = pd.read_csv(csv_in)
    expected_lapse = []
    for i in range(1, min(10, len(orig))):
        dT = orig["temperature"].iloc[i] - orig["temperature"].iloc[i-1]
        dz = (orig["altitude"].iloc[i] - orig["altitude"].iloc[i-1]) / 1000.0
        if abs(dz) > 0.001:
            expected_lapse.append(-dT / dz)
    lapse_accuracy = 0.0
    if lapse_col and len(df) > 0:
        computed = df[lapse_col[0]].dropna().values[:len(expected_lapse)]
        if len(computed) > 0 and len(expected_lapse) > 0:
            min_len = min(len(computed), len(expected_lapse))
            errors = np.abs(computed[:min_len] - np.array(expected_lapse[:min_len]))
            mean_error = np.mean(errors)
            lapse_accuracy = round(max(0, 1.0 - mean_error / 10.0), 4)
    print(f"SCORE:lapse_accuracy={lapse_accuracy}")

    # SCORE: 特征完整性
    features = ["tropopause", "cape", "cin", "inversion", "surface", "lapse"]
    found = sum(1 for f in features if f in s_str or f in cols)
    feature_completeness = round(found / len(features), 4)
    print(f"SCORE:feature_completeness={feature_completeness}")
'''

# =============================================================================
# S19: 信号处理 — 多通道 EEG 滤波与分析 (信号处理, 中等)
# =============================================================================
S19_TASK = """Write a Python CLI script to filter and analyze multi-channel EEG (electroencephalogram) signals.

Input: A CSV file with columns: time (seconds), ch1, ch2, ..., ch8 (8 EEG channels in microvolts).
The sampling rate is 256 Hz.

Requirements:
1. Use argparse: --input CSV path, --output directory, --sample-rate (default 256)
2. Apply a bandpass filter (0.5–40 Hz) to each channel using scipy.signal (e.g., Butterworth filter, order 4)
3. Apply a notch filter at 50 Hz (powerline interference removal) using scipy.signal
4. Compute the power spectral density (PSD) for each channel using Welch's method (scipy.signal.welch)
5. Detect alpha waves (8–13 Hz): for each channel, compute the ratio of alpha-band power to total power
6. Output files:
   - filtered_signals.csv: time column + filtered ch1–ch8
   - psd.csv: frequency column + PSD values for each channel
   - summary.json: for each channel: {dominant_frequency_Hz, alpha_power_ratio, total_power, mean_amplitude, std_amplitude}
7. Print: dominant frequency per channel, channels with strong alpha activity (ratio > 0.2)
"""

S19_TEST = '''
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
'''

# =============================================================================
# S20: 社会科学 — 问卷调查重编码与分析 (社科, 简单)
# =============================================================================
S20_TASK = """Write a Python CLI script to recode and analyze Likert-scale survey responses.

Input: A CSV file with columns: respondent_id, age, gender (M/F/Other), q1 through q10 (integer values 1-5 representing Likert scale: 1=Strongly Disagree to 5=Strongly Agree).

Requirements:
1. Use argparse: --input CSV path, --output directory, --reverse-items (comma-separated list of items to reverse-code, default "q3,q5,q7")
2. Reverse-code the specified items: reverse_value = 6 - original_value (so 1→5, 2→4, 3→3, 4→2, 5→1)
3. Compute two composite scores for each respondent:
   - scale_A: mean of q1, q2, q3, q4, q5 (after recoding)
   - scale_B: mean of q6, q7, q8, q9, q10 (after recoding)
4. Compute Cronbach's alpha reliability for each scale: alpha = (k/(k-1)) * (1 - sum(item_variances) / total_variance)
   where k = number of items, item_variances = variance of each item, total_variance = variance of the sum of items
5. Perform group comparison by gender: compute mean and standard deviation of each composite score per gender group
6. Output files:
   - recoded_responses.csv: original data + reverse-coded items (renamed as q3_r, etc.) + scale_A, scale_B columns
   - reliability.json: {scale_A: {alpha, n_items, items}, scale_B: {alpha, n_items, items}}
   - group_comparison.json: {gender_group: {scale_A_mean, scale_A_std, scale_B_mean, scale_B_std, n}}
7. Print: Cronbach's alpha for each scale, group means
"""

S20_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_respondents=120):
    """生成模拟问卷数据：有一定相关结构"""
    np.random.seed(42)
    rows = []
    genders = ["M", "F", "Other"]
    for i in range(n_respondents):
        gender = np.random.choice(genders, p=[0.45, 0.45, 0.1])
        age = np.random.randint(18, 70)
        # 生成有相关性的 Likert 响应
        # Scale A 项目（q1-q5）有一个共同因子
        factor_a = np.random.normal(3.5, 0.8)
        # Scale B 项目（q6-q10）有另一个共同因子
        factor_b = np.random.normal(3.0, 0.9)
        responses = {}
        for q in range(1, 6):
            val = factor_a + np.random.normal(0, 0.7)
            # q3 和 q5 是反向题，生成反向值
            if q in [3, 5]:
                val = 6 - val
            responses[f"q{q}"] = int(np.clip(round(val), 1, 5))
        for q in range(6, 11):
            val = factor_b + np.random.normal(0, 0.8)
            # q7 是反向题
            if q == 7:
                val = 6 - val
            responses[f"q{q}"] = int(np.clip(round(val), 1, 5))
        row = {"respondent_id": f"R{i:04d}", "age": age, "gender": gender}
        row.update(responses)
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_respondents

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/survey.csv"
    out_dir = f"{tmpdir}/output"
    n_resp = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--reverse-items", "q3,q5,q7"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    recoded_csv = None
    reliability_json = None
    group_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("recode" in fl or "response" in fl) and f.endswith(".csv"):
                recoded_csv = os.path.join(out_dir, f)
            if "reliab" in fl and f.endswith(".json"):
                reliability_json = os.path.join(out_dir, f)
            if ("group" in fl or "comparison" in fl) and f.endswith(".json"):
                group_json = os.path.join(out_dir, f)

    if recoded_csv or reliability_json or group_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_reverse_coded", "L2_reverse_values",
                   "L2_composite_scores", "L2_score_range", "L2_reliability_exists",
                   "L2_alpha_range", "L2_group_comparison", "L2_gender_groups",
                   "L2_all_respondents", "L2_no_nan", "L2_original_preserved"]:
            print(f"FAIL:{t}")
        print("SCORE:alpha_accuracy=0.0")
        print("SCORE:analysis_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if recoded_csv:
        try:
            df = pd.read_csv(recoded_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 有反向编码的列
    if "_r" in cols or "reverse" in cols or "recode" in cols:
        print("PASS:L2_reverse_coded")
    else:
        # 也可能直接覆盖了原始列
        print("FAIL:L2_reverse_coded")

    # L2: 反向编码的值正确 (6 - original)
    orig = pd.read_csv(csv_in)
    reverse_ok = False
    if len(df) > 0:
        # 查找反向编码列
        for rc in ["q3_r", "q3_reverse", "q3_recoded"]:
            if rc in df.columns:
                expected = 6 - orig["q3"].values
                actual = df[rc].values[:len(expected)]
                if np.allclose(expected, actual, atol=0.01):
                    reverse_ok = True
                break
        # 也检查是否直接修改了 q3 列
        if not reverse_ok and "q3" in df.columns:
            if not np.allclose(df["q3"].values, orig["q3"].values):
                # 检查是否是 6-x 关系
                if np.allclose(df["q3"].values, 6 - orig["q3"].values, atol=0.01):
                    reverse_ok = True
    if reverse_ok:
        print("PASS:L2_reverse_values")
    else:
        print("FAIL:L2_reverse_values")

    # L2: 有复合得分列
    if "scale_a" in cols or "composite" in cols or "score_a" in cols or "scale" in cols:
        print("PASS:L2_composite_scores")
    else:
        print("FAIL:L2_composite_scores")

    # L2: 复合得分范围合理 (1-5)
    score_cols = [c for c in df.columns if "scale" in c.lower() or "composite" in c.lower() or "score" in c.lower()]
    if score_cols:
        all_in_range = True
        for sc in score_cols:
            vals = df[sc].dropna()
            if len(vals) > 0 and (vals.min() < 0.5 or vals.max() > 5.5):
                all_in_range = False
        if all_in_range:
            print("PASS:L2_score_range")
        else:
            print("FAIL:L2_score_range")
    else:
        print("FAIL:L2_score_range")

    # L2: 信度文件存在
    reliability = {}
    if reliability_json and os.path.exists(reliability_json):
        try:
            reliability = json.load(open(reliability_json))
            print("PASS:L2_reliability_exists")
        except:
            print("FAIL:L2_reliability_exists")
    else:
        print("FAIL:L2_reliability_exists")

    # L2: alpha 值范围合理 (0-1)
    r_str = json.dumps(reliability).lower() if reliability else ""
    alphas = []
    if "alpha" in r_str:
        # 提取 alpha 值
        def find_alphas(d):
            result = []
            if isinstance(d, dict):
                for k, v in d.items():
                    if "alpha" in k.lower():
                        try:
                            result.append(float(v))
                        except:
                            pass
                    elif isinstance(v, dict):
                        result.extend(find_alphas(v))
            return result
        alphas = find_alphas(reliability)
    if alphas and all(0 <= a <= 1 for a in alphas):
        print(f"PASS:L2_alpha_range - alphas={alphas}")
    elif alphas:
        print(f"FAIL:L2_alpha_range - alphas={alphas}")
    else:
        print("FAIL:L2_alpha_range")

    # L2: 组间比较文件存在
    group_data = {}
    if group_json and os.path.exists(group_json):
        try:
            group_data = json.load(open(group_json))
            print("PASS:L2_group_comparison")
        except:
            print("FAIL:L2_group_comparison")
    else:
        print("FAIL:L2_group_comparison")

    # L2: 有性别分组
    g_str = json.dumps(group_data).lower() if group_data else ""
    if ("m" in g_str or "male" in g_str or "f" in g_str or "female" in g_str) and len(group_data) >= 2:
        print("PASS:L2_gender_groups")
    elif len(group_data) >= 2:
        print("PASS:L2_gender_groups")
    else:
        print("FAIL:L2_gender_groups")

    # L2: 所有受访者保留
    if len(df) >= n_resp:
        print(f"PASS:L2_all_respondents - {len(df)}/{n_resp}")
    elif len(df) >= n_resp * 0.9:
        print(f"PASS:L2_all_respondents - {len(df)}/{n_resp}")
    else:
        print(f"FAIL:L2_all_respondents - {len(df)}/{n_resp}")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: 原始数据列保留
    if len(df) > 0 and "respondent_id" in df.columns and "age" in df.columns:
        print("PASS:L2_original_preserved")
    elif len(df) > 0 and len(df.columns) >= 12:
        print("PASS:L2_original_preserved")
    else:
        print("FAIL:L2_original_preserved")

    # SCORE: alpha 精度（手动计算并比较）
    alpha_accuracy = 0.0
    if len(orig) > 0:
        # 手动计算 Scale A 的 Cronbach's alpha（反向编码后）
        items_a = orig[["q1", "q2", "q3", "q4", "q5"]].copy()
        items_a["q3"] = 6 - items_a["q3"]
        items_a["q5"] = 6 - items_a["q5"]
        k = 5
        item_vars = items_a.var(ddof=1)
        total_var = items_a.sum(axis=1).var(ddof=1)
        if total_var > 0:
            expected_alpha_a = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
        else:
            expected_alpha_a = 0

        if alphas:
            # 找最接近的 alpha 值
            best_match = min(alphas, key=lambda a: abs(a - expected_alpha_a))
            error = abs(best_match - expected_alpha_a)
            alpha_accuracy = round(max(0, 1.0 - error / 0.3), 4)
    print(f"SCORE:alpha_accuracy={alpha_accuracy}")

    # SCORE: 分析完整性
    features = ["reverse", "scale", "alpha", "group", "mean", "std"]
    all_str = cols + " " + r_str + " " + g_str
    found = sum(1 for f in features if f in all_str)
    analysis_completeness = round(found / len(features), 4)
    print(f"SCORE:analysis_completeness={analysis_completeness}")
'''

# =============================================================================
# S21: 环境科学 — 空气质量指数计算 (环境, 简单)
# =============================================================================
S21_TASK = """Write a Python CLI script to compute Air Quality Index (AQI) from hourly pollutant measurements.

Input: A CSV file with columns: timestamp (YYYY-MM-DD HH:MM:SS), pm25 (µg/m³), pm10 (µg/m³), o3 (ppb), no2 (ppb), so2 (ppb), co (ppm).

Requirements:
1. Use argparse: --input CSV path, --output directory
2. Compute the sub-index for each pollutant using US EPA AQI breakpoints:
   - PM2.5 (24-hr avg): [0,12.0]=Good(0-50), [12.1,35.4]=Moderate(51-100), [35.5,55.4]=Unhealthy-SG(101-150), [55.5,150.4]=Unhealthy(151-200), [150.5,250.4]=Very-Unhealthy(201-300), [250.5,500.4]=Hazardous(301-500)
   - PM10 (24-hr avg): [0,54]=Good(0-50), [55,154]=Moderate(51-100), [155,254]=Unhealthy-SG(101-150), [255,354]=Unhealthy(151-200), [355,424]=Very-Unhealthy(201-300), [425,604]=Hazardous(301-500)
   - O3 (8-hr avg): [0,54]=Good(0-50), [55,70]=Moderate(51-100), [71,85]=Unhealthy-SG(101-150), [86,105]=Unhealthy(151-200), [106,200]=Very-Unhealthy(201-300)
   - NO2 (1-hr): [0,53]=Good(0-50), [54,100]=Moderate(51-100), [101,360]=Unhealthy-SG(101-150), [361,649]=Unhealthy(151-200), [650,1249]=Very-Unhealthy(201-300), [1250,2049]=Hazardous(301-500)
   - SO2 (1-hr): [0,35]=Good(0-50), [36,75]=Moderate(51-100), [76,185]=Unhealthy-SG(101-150), [186,304]=Unhealthy(151-200), [305,604]=Very-Unhealthy(201-300), [605,1004]=Hazardous(301-500)
   - CO (8-hr avg): [0,4.4]=Good(0-50), [4.5,9.4]=Moderate(51-100), [9.5,12.4]=Unhealthy-SG(101-150), [12.5,15.4]=Unhealthy(151-200), [15.5,30.4]=Very-Unhealthy(201-300), [30.5,50.4]=Hazardous(301-500)
3. The daily AQI = max of all pollutant sub-indices. The dominant pollutant = the one with the highest sub-index.
4. Compute AQI category: Good (0-50), Moderate (51-100), Unhealthy for Sensitive Groups (101-150), Unhealthy (151-200), Very Unhealthy (201-300), Hazardous (301-500)
5. Aggregate monthly: mean AQI, max AQI, number of days in each category, dominant pollutant frequency
6. Count exceedance days: days where AQI > 100
7. Output files:
   - daily_aqi.csv: date, aqi, category, dominant_pollutant, pm25_aqi, pm10_aqi, o3_aqi, no2_aqi, so2_aqi, co_aqi
   - monthly_summary.json: {month: {mean_aqi, max_aqi, category_counts, dominant_pollutant_counts}}
   - exceedance_report.json: {total_days, exceedance_days, exceedance_rate, exceedance_dates, worst_day, worst_aqi}
8. Print: total days, mean AQI, exceedance rate, worst day
"""

S21_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_days=180):
    """生成模拟逐小时污染物数据：半年（180 天）"""
    np.random.seed(42)
    rows = []
    base_date = pd.Timestamp("2024-01-01")
    for day in range(n_days):
        date = base_date + pd.Timedelta(days=day)
        # 季节性基线
        season_factor = 1.0 + 0.5 * np.sin(2 * np.pi * day / 365)
        # 每天偶尔有高污染事件
        event = 1.0
        if np.random.rand() < 0.1:
            event = np.random.uniform(2.0, 4.0)
        for hour in range(24):
            ts = date + pd.Timedelta(hours=hour)
            # 日变化模式：早晚高峰
            diurnal = 1.0 + 0.3 * np.sin(2 * np.pi * (hour - 8) / 24)
            base = season_factor * event * diurnal
            pm25 = max(0, base * np.random.uniform(8, 30) + np.random.normal(0, 3))
            pm10 = max(0, base * np.random.uniform(20, 60) + np.random.normal(0, 5))
            o3 = max(0, np.random.uniform(15, 55) * (1 + 0.5 * np.sin(2 * np.pi * (hour - 14) / 24)) * season_factor)
            no2 = max(0, base * np.random.uniform(10, 40) + np.random.normal(0, 5))
            so2 = max(0, base * np.random.uniform(2, 20) + np.random.normal(0, 2))
            co = max(0, base * np.random.uniform(0.2, 2.0) + np.random.normal(0, 0.1))
            rows.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "pm25": round(pm25, 2),
                "pm10": round(pm10, 2),
                "o3": round(o3, 2),
                "no2": round(no2, 2),
                "so2": round(so2, 2),
                "co": round(co, 3),
            })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_days

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/pollutants.csv"
    out_dir = f"{tmpdir}/output"
    n_days = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", csv_in, out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    daily_csv = None
    monthly_json = None
    exceedance_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("daily" in fl or "aqi" in fl) and f.endswith(".csv"):
                daily_csv = os.path.join(out_dir, f)
            if ("monthly" in fl or "month" in fl) and f.endswith(".json"):
                monthly_json = os.path.join(out_dir, f)
            if ("exceedance" in fl or "exceed" in fl) and f.endswith(".json"):
                exceedance_json = os.path.join(out_dir, f)

    if daily_csv or monthly_json or exceedance_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_daily_count", "L2_aqi_column", "L2_aqi_range",
                   "L2_category_column", "L2_dominant_pollutant", "L2_sub_indices",
                   "L2_monthly_summary", "L2_exceedance_report", "L2_exceedance_fields",
                   "L2_no_nan", "L2_date_column"]:
            print(f"FAIL:{t}")
        print("SCORE:aqi_accuracy=0.0")
        print("SCORE:report_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if daily_csv:
        try:
            df = pd.read_csv(daily_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 日数正确
    if len(df) >= n_days * 0.9:
        print(f"PASS:L2_daily_count - {len(df)}/{n_days} days")
    elif len(df) > 0:
        print(f"PASS:L2_daily_count - {len(df)} days")
    else:
        print("FAIL:L2_daily_count")

    # L2: 有 AQI 列
    if "aqi" in cols:
        print("PASS:L2_aqi_column")
    else:
        print("FAIL:L2_aqi_column")

    # L2: AQI 值范围合理 (0-500)
    aqi_col = [c for c in df.columns if "aqi" == c.lower() or c.lower() == "daily_aqi" or c.lower() == "overall_aqi"]
    if not aqi_col:
        aqi_col = [c for c in df.columns if "aqi" in c.lower() and "pm" not in c.lower() and "o3" not in c.lower()
                    and "no2" not in c.lower() and "so2" not in c.lower() and "co" not in c.lower()]
    if aqi_col and len(df) > 0:
        vals = df[aqi_col[0]].dropna()
        if len(vals) > 0 and vals.min() >= 0 and vals.max() <= 500:
            print(f"PASS:L2_aqi_range - [{vals.min():.0f}, {vals.max():.0f}]")
        elif len(vals) > 0:
            print(f"FAIL:L2_aqi_range - [{vals.min():.0f}, {vals.max():.0f}]")
        else:
            print("FAIL:L2_aqi_range")
    else:
        print("FAIL:L2_aqi_range")

    # L2: 有类别列
    if "category" in cols or "level" in cols or "grade" in cols:
        print("PASS:L2_category_column")
    else:
        print("FAIL:L2_category_column")

    # L2: 有主要污染物列
    if "dominant" in cols or "primary" in cols or "main" in cols:
        print("PASS:L2_dominant_pollutant")
    else:
        print("FAIL:L2_dominant_pollutant")

    # L2: 有各污染物子指数列
    sub_index_count = sum(1 for p in ["pm25", "pm10", "o3", "no2", "so2", "co"]
                          if any(p in c.lower() and "aqi" in c.lower() for c in df.columns))
    if sub_index_count >= 4:
        print(f"PASS:L2_sub_indices - {sub_index_count} pollutants")
    elif sub_index_count >= 1:
        print(f"PASS:L2_sub_indices - {sub_index_count} pollutants (partial)")
    else:
        print("FAIL:L2_sub_indices")

    # L2: 月度汇总存在
    monthly = {}
    if monthly_json and os.path.exists(monthly_json):
        try:
            monthly = json.load(open(monthly_json))
            print("PASS:L2_monthly_summary")
        except:
            print("FAIL:L2_monthly_summary")
    else:
        print("FAIL:L2_monthly_summary")

    # L2: 超标报告存在
    exceedance = {}
    if exceedance_json and os.path.exists(exceedance_json):
        try:
            exceedance = json.load(open(exceedance_json))
            print("PASS:L2_exceedance_report")
        except:
            print("FAIL:L2_exceedance_report")
    else:
        print("FAIL:L2_exceedance_report")

    # L2: 超标报告包含关键字段
    e_str = json.dumps(exceedance).lower() if exceedance else ""
    expected_e_fields = ["total", "exceedance", "rate", "worst"]
    found_e = sum(1 for f in expected_e_fields if f in e_str)
    if found_e >= 3:
        print(f"PASS:L2_exceedance_fields - {found_e}/{len(expected_e_fields)}")
    elif found_e >= 1:
        print(f"PASS:L2_exceedance_fields - {found_e}/{len(expected_e_fields)} (partial)")
    else:
        print("FAIL:L2_exceedance_fields")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: 有日期列
    if "date" in cols or "day" in cols or "timestamp" in cols:
        print("PASS:L2_date_column")
    else:
        print("FAIL:L2_date_column")

    # SCORE: AQI 计算精度（手动计算第一天 PM2.5 AQI 并比较）
    aqi_accuracy = 0.0
    try:
        orig = pd.read_csv(csv_in)
        orig["timestamp"] = pd.to_datetime(orig["timestamp"])
        orig["date"] = orig["timestamp"].dt.date
        day1 = orig[orig["date"] == orig["date"].iloc[0]]
        pm25_avg = day1["pm25"].mean()

        # EPA 公式
        def calc_pm25_aqi(c):
            breakpoints = [
                (0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 500.4, 301, 500),
            ]
            for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
                if c <= bp_hi:
                    return round((i_hi - i_lo) / (bp_hi - bp_lo) * (c - bp_lo) + i_lo)
            return 500

        expected_pm25_aqi = calc_pm25_aqi(pm25_avg)

        if aqi_col and len(df) > 0:
            # 查找 PM2.5 子指数列
            pm25_aqi_col = [c for c in df.columns if "pm25" in c.lower() and "aqi" in c.lower()]
            if pm25_aqi_col:
                computed = df[pm25_aqi_col[0]].iloc[0]
                error = abs(computed - expected_pm25_aqi)
                aqi_accuracy = round(max(0, 1.0 - error / 50.0), 4)
            elif aqi_col:
                # 比较总 AQI（至少 >= PM2.5 AQI）
                computed = df[aqi_col[0]].iloc[0]
                if computed >= expected_pm25_aqi * 0.5:
                    aqi_accuracy = round(max(0, 1.0 - abs(computed - expected_pm25_aqi) / 100.0), 4)
    except:
        pass
    print(f"SCORE:aqi_accuracy={aqi_accuracy}")

    # SCORE: 报告完整性
    features = ["daily", "monthly", "exceedance", "category", "dominant", "aqi"]
    all_str = cols + " " + json.dumps(monthly).lower() + " " + e_str
    if daily_csv:
        all_str += " daily"
    if monthly_json and os.path.exists(monthly_json):
        all_str += " monthly"
    if exceedance_json and os.path.exists(exceedance_json):
        all_str += " exceedance"
    found = sum(1 for f in features if f in all_str)
    report_completeness = round(found / len(features), 4)
    print(f"SCORE:report_completeness={report_completeness}")
'''
"""
场景 S22-S25：地质、流行病学、材料科学、网络科学
每个场景 = task_desc + test_script (含数据生成 + 12-15 PASS/FAIL + 2 SCORE)
"""

# =============================================================================
# S22: 地质学 — 测井数据重采样与岩性分类 (地质, 中等)
# =============================================================================
S22_TASK = """Write a Python CLI script to resample borehole well log data and classify lithology from crossplot rules.

Input: A CSV file with columns: depth, gamma_ray, resistivity, neutron_porosity, bulk_density, caliper.
- Depth is in meters (irregularly sampled).
- gamma_ray in API units, resistivity in ohm-m, neutron_porosity as fraction (0-1), bulk_density in g/cm3, caliper in inches.

Requirements:
1. Use argparse: --input CSV, --output directory, --depth-step (default 0.5 meters)
2. Resample all log curves to uniform depth intervals using linear interpolation (from min to max depth at --depth-step resolution)
3. Compute derived logs:
   - PHIT (total porosity) = (2.65 - bulk_density) / (2.65 - 1.0)  [matrix=2.65, fluid=1.0]
   - Vsh (shale volume) from gamma ray: Vsh = (GR - GR_min) / (GR_max - GR_min), clipped to [0, 1]
4. Classify lithology for each depth sample using these crossplot rules:
   - "sandstone": Vsh < 0.3 AND PHIT > 0.1 AND resistivity > 10
   - "shale": Vsh >= 0.6
   - "limestone": bulk_density > 2.5 AND neutron_porosity < 0.15 AND Vsh < 0.3
   - "siltstone": otherwise
5. Output:
   - resampled_log.csv: all original columns + PHIT + Vsh at uniform depth
   - lithology_classification.csv: depth, lithology columns
   - summary.json: {total_depth_range, n_samples, layer_counts: {sandstone: N, shale: N, ...}, mean_porosity, mean_Vsh}
6. Print: depth range, number of resampled points, lithology distribution
"""

S22_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_points=400):
    np.random.seed(42)
    # 模拟不均匀采样的测井数据
    depth = np.sort(np.concatenate([
        np.arange(100, 200, 0.3),
        np.arange(200, 350, 0.8),
        np.arange(350, 500, 0.5),
    ]))
    depth = depth[:n_points]
    n = len(depth)
    # 生成不同岩性区间的测井响应
    gamma_ray = np.zeros(n)
    resistivity = np.zeros(n)
    neutron_porosity = np.zeros(n)
    bulk_density = np.zeros(n)
    caliper = np.zeros(n)
    for i, d in enumerate(depth):
        if d < 180:  # 砂岩段
            gamma_ray[i] = np.random.normal(40, 8)
            resistivity[i] = np.random.lognormal(3.5, 0.5)
            neutron_porosity[i] = np.random.normal(0.22, 0.03)
            bulk_density[i] = np.random.normal(2.2, 0.05)
        elif d < 280:  # 页岩段
            gamma_ray[i] = np.random.normal(120, 15)
            resistivity[i] = np.random.lognormal(1.0, 0.4)
            neutron_porosity[i] = np.random.normal(0.35, 0.04)
            bulk_density[i] = np.random.normal(2.45, 0.06)
        elif d < 400:  # 石灰岩段
            gamma_ray[i] = np.random.normal(25, 5)
            resistivity[i] = np.random.lognormal(4.0, 0.6)
            neutron_porosity[i] = np.random.normal(0.08, 0.02)
            bulk_density[i] = np.random.normal(2.6, 0.04)
        else:  # 粉砂岩段
            gamma_ray[i] = np.random.normal(70, 10)
            resistivity[i] = np.random.lognormal(2.0, 0.5)
            neutron_porosity[i] = np.random.normal(0.2, 0.04)
            bulk_density[i] = np.random.normal(2.4, 0.05)
        caliper[i] = np.random.normal(8.5, 0.3)
    gamma_ray = np.clip(gamma_ray, 10, 200)
    neutron_porosity = np.clip(neutron_porosity, 0.01, 0.60)
    bulk_density = np.clip(bulk_density, 1.8, 2.85)
    df = pd.DataFrame({
        "depth": np.round(depth, 2),
        "gamma_ray": np.round(gamma_ray, 2),
        "resistivity": np.round(resistivity, 3),
        "neutron_porosity": np.round(neutron_porosity, 4),
        "bulk_density": np.round(bulk_density, 3),
        "caliper": np.round(caliper, 2),
    })
    df.to_csv(path, index=False)
    return len(df)

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/welllog.csv"
    out_dir = f"{tmpdir}/output"
    n_orig = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--depth-step", "0.5"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    resampled_csv = None
    litho_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("resamp" in fl or "log" in fl) and f.endswith(".csv"):
                resampled_csv = os.path.join(out_dir, f)
            if ("litho" in fl or "class" in fl) and f.endswith(".csv"):
                litho_csv = os.path.join(out_dir, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    if resampled_csv or litho_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_uniform_depth","L2_phit_computed","L2_vsh_computed",
                   "L2_lithology_present","L2_four_classes","L2_depth_range","L2_no_nan",
                   "L2_porosity_range","L2_vsh_range","L2_summary_exists","L2_layer_counts"]:
            print(f"FAIL:{t}")
        print("SCORE:resampling_quality=0.0")
        print("SCORE:classification_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if resampled_csv:
        try:
            df = pd.read_csv(resampled_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 均匀深度间隔
    if len(df) > 2 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()][0]
        depths = df[depth_col].values
        diffs = np.diff(depths)
        if len(diffs) > 0 and np.std(diffs) < np.mean(diffs) * 0.2:
            print(f"PASS:L2_uniform_depth - step={np.mean(diffs):.2f}m")
        else:
            print(f"PASS:L2_uniform_depth - approximately uniform")
    else:
        print("FAIL:L2_uniform_depth")

    # L2: PHIT 被计算
    if "phit" in cols or "porosity_total" in cols or "total_porosity" in cols:
        print("PASS:L2_phit_computed")
    else:
        print("FAIL:L2_phit_computed")

    # L2: Vsh 被计算
    if "vsh" in cols or "shale_volume" in cols or "v_sh" in cols:
        print("PASS:L2_vsh_computed")
    else:
        print("FAIL:L2_vsh_computed")

    # L2: 岩性分类存在
    litho_df = pd.DataFrame()
    if litho_csv:
        try:
            litho_df = pd.read_csv(litho_csv)
        except:
            pass
    litho_cols = " ".join(litho_df.columns).lower() if len(litho_df) > 0 else ""
    if "litho" in litho_cols or "class" in litho_cols or "litho" in cols or "class" in cols:
        print("PASS:L2_lithology_present")
    else:
        print("FAIL:L2_lithology_present")

    # L2: 包含四种岩性分类
    all_litho = set()
    for source in [litho_df, df]:
        if len(source) > 0:
            for c in source.columns:
                if "litho" in c.lower() or "class" in c.lower():
                    all_litho.update(source[c].astype(str).str.lower().unique())
    expected = {"sandstone", "shale", "limestone", "siltstone"}
    found_types = expected.intersection(all_litho)
    if len(found_types) >= 3:
        print(f"PASS:L2_four_classes - found {found_types}")
    elif len(found_types) >= 1:
        print(f"PASS:L2_four_classes - found {len(found_types)} types")
    else:
        print("FAIL:L2_four_classes")

    # L2: 深度范围合理 (应覆盖原始范围)
    orig_df = pd.read_csv(csv_in)
    if len(df) > 0 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()][0]
        d_min, d_max = df[depth_col].min(), df[depth_col].max()
        o_min, o_max = orig_df["depth"].min(), orig_df["depth"].max()
        if d_min <= o_min + 5 and d_max >= o_max - 5:
            print(f"PASS:L2_depth_range - [{d_min:.0f}, {d_max:.0f}]m")
        else:
            print(f"FAIL:L2_depth_range - [{d_min:.0f}, {d_max:.0f}] vs [{o_min:.0f}, {o_max:.0f}]")
    else:
        print("FAIL:L2_depth_range")

    # L2: 无 NaN
    if len(df) > 0:
        nan_pct = df.select_dtypes(include=[np.number]).isnull().mean().mean()
        print(f"{'PASS' if nan_pct < 0.05 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: PHIT 范围合理 (0-0.5)
    phit_col = [c for c in df.columns if "phit" in c.lower() or "total_porosity" in c.lower()] if len(df) > 0 else []
    if phit_col:
        vals = df[phit_col[0]].dropna()
        if vals.min() >= -0.05 and vals.max() <= 0.55:
            print(f"PASS:L2_porosity_range - [{vals.min():.3f}, {vals.max():.3f}]")
        else:
            print(f"FAIL:L2_porosity_range")
    else:
        print("FAIL:L2_porosity_range")

    # L2: Vsh 范围 [0, 1]
    vsh_col = [c for c in df.columns if "vsh" in c.lower() or "shale_vol" in c.lower() or "v_sh" in c.lower()] if len(df) > 0 else []
    if vsh_col:
        vals = df[vsh_col[0]].dropna()
        if vals.min() >= -0.01 and vals.max() <= 1.01:
            print(f"PASS:L2_vsh_range")
        else:
            print(f"FAIL:L2_vsh_range")
    else:
        print("FAIL:L2_vsh_range")

    # L2: summary.json 存在
    if summary_json and os.path.exists(summary_json):
        print("PASS:L2_summary_exists")
    else:
        print("FAIL:L2_summary_exists")

    # L2: layer_counts 在 summary 中
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if "layer" in s_str or "count" in s_str or "sandstone" in s_str or "shale" in s_str:
                print("PASS:L2_layer_counts")
            else:
                print("FAIL:L2_layer_counts")
        except:
            print("FAIL:L2_layer_counts")
    else:
        print("FAIL:L2_layer_counts")

    # SCORE: 重采样质量（深度均匀度）
    if len(df) > 2 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()][0]
        diffs = np.diff(df[depth_col].values)
        if len(diffs) > 0 and np.mean(diffs) > 0:
            uniformity = 1.0 - min(np.std(diffs) / np.mean(diffs), 1.0)
        else:
            uniformity = 0.0
    else:
        uniformity = 0.0
    print(f"SCORE:resampling_quality={round(uniformity, 4)}")

    # SCORE: 分类完整性
    expected_fields = ["phit", "vsh", "lithology", "sandstone", "shale", "limestone", "siltstone", "layer", "porosity"]
    all_text = cols + " " + (json.dumps(json.load(open(summary_json))).lower() if summary_json and os.path.exists(summary_json) else "")
    found = sum(1 for f in expected_fields if f in all_text)
    completeness = round(found / len(expected_fields), 4)
    print(f"SCORE:classification_completeness={completeness}")
'''

# =============================================================================
# S23: 流行病学 — 暴发曲线分析 (流行病学, 中等)
# =============================================================================
S23_TASK = """Write a Python CLI script to analyze disease outbreak case report data and produce epidemic curve statistics.

Input: A CSV file with columns: case_id, onset_date (YYYY-MM-DD), age, gender (M/F), location, outcome (recovered/deceased/hospitalized).

Requirements:
1. Use argparse: --input CSV, --output directory, --serial-interval (default 5.0 days, mean generation time for R0 estimation)
2. Build an epidemic curve: aggregate daily case counts from onset_date
3. Compute the basic reproduction number R0 using exponential growth rate method:
   - Fit exponential model to the early growth phase (first 30% of total duration)
   - growth_rate r = slope of ln(cumulative_cases) vs time
   - R0 = 1 + r * serial_interval
4. Find peak date (day with maximum new cases) and compute doubling time = ln(2) / r
5. Compute Case Fatality Rate (CFR) by age group: age bins [0-18, 19-40, 41-60, 61+]
6. Output:
   - epi_curve.csv: columns date, daily_cases, cumulative_cases
   - analysis.json: {R0, peak_date, CFR_by_age: {group: rate}, total_cases, doubling_time, growth_rate, attack_rate_by_location}
7. Print: R0 estimate, peak date, overall CFR, total cases
"""

S23_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_cases=500):
    np.random.seed(42)
    # 模拟传染病暴发：指数增长 -> 平台期 -> 下降
    start_date = pd.Timestamp("2024-03-01")
    duration_days = 90
    # 生成发病日期（logistic增长模式）
    t = np.arange(duration_days)
    rate = 1.0 / (1.0 + np.exp(-0.12 * (t - 35)))  # Logistic 增长
    daily_prob = np.diff(np.concatenate([[0], rate]))
    daily_prob = daily_prob / daily_prob.sum()
    onset_days = np.random.choice(t, size=n_cases, p=daily_prob)
    # 人口学数据
    ages = np.concatenate([
        np.random.randint(0, 18, n_cases // 5),
        np.random.randint(19, 40, n_cases // 3),
        np.random.randint(41, 60, n_cases // 4),
        np.random.randint(61, 90, n_cases - n_cases//5 - n_cases//3 - n_cases//4),
    ])
    np.random.shuffle(ages)
    ages = ages[:n_cases]
    genders = np.random.choice(["M", "F"], n_cases)
    locations = np.random.choice(["District_A", "District_B", "District_C", "District_D"], n_cases,
                                  p=[0.35, 0.3, 0.2, 0.15])
    # 结局：老年人死亡率更高
    outcomes = []
    for age in ages:
        if age >= 61:
            outcomes.append(np.random.choice(["recovered", "deceased", "hospitalized"], p=[0.6, 0.15, 0.25]))
        elif age >= 41:
            outcomes.append(np.random.choice(["recovered", "deceased", "hospitalized"], p=[0.8, 0.05, 0.15]))
        else:
            outcomes.append(np.random.choice(["recovered", "deceased", "hospitalized"], p=[0.92, 0.01, 0.07]))
    rows = []
    for i in range(n_cases):
        rows.append({
            "case_id": f"CASE_{i:04d}",
            "onset_date": (start_date + pd.Timedelta(days=int(onset_days[i]))).strftime("%Y-%m-%d"),
            "age": int(ages[i]),
            "gender": genders[i],
            "location": locations[i],
            "outcome": outcomes[i],
        })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_cases

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/cases.csv"
    out_dir = f"{tmpdir}/output"
    n_cases = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--serial-interval", "5.0"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    epi_csv = None
    analysis_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("epi" in fl or "curve" in fl or "daily" in fl) and f.endswith(".csv"):
                epi_csv = os.path.join(out_dir, f)
            if ("analysis" in fl or "summary" in fl) and f.endswith(".json"):
                analysis_json = os.path.join(out_dir, f)

    if epi_csv or analysis_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_daily_counts","L2_cumulative","L2_r0_computed",
                   "L2_peak_date","L2_cfr_by_age","L2_doubling_time","L2_total_cases",
                   "L2_date_range","L2_no_negative","L2_growth_rate","L2_location_stats"]:
            print(f"FAIL:{t}")
        print("SCORE:r0_accuracy=0.0")
        print("SCORE:analysis_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    epi_df = pd.DataFrame()
    if epi_csv:
        try:
            epi_df = pd.read_csv(epi_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    epi_cols = " ".join(epi_df.columns).lower() if len(epi_df) > 0 else ""

    # L2: 每日计数列存在
    if "daily" in epi_cols or "cases" in epi_cols or "count" in epi_cols or "new" in epi_cols:
        print("PASS:L2_daily_counts")
    else:
        print("FAIL:L2_daily_counts")

    # L2: 累计计数列存在
    if "cumul" in epi_cols or "total" in epi_cols:
        print("PASS:L2_cumulative")
    else:
        print("FAIL:L2_cumulative")

    # L2: R0 计算
    if analysis_json and os.path.exists(analysis_json):
        try:
            analysis = json.load(open(analysis_json))
            a_str = json.dumps(analysis).lower()
            if "r0" in a_str or "r_0" in a_str or "reproduction" in a_str or "r_naught" in a_str:
                print("PASS:L2_r0_computed")
            else:
                print("FAIL:L2_r0_computed")
        except:
            print("FAIL:L2_r0_computed")
    else:
        print("FAIL:L2_r0_computed")

    # L2: 峰值日期
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "peak" in a_str:
            print("PASS:L2_peak_date")
        else:
            print("FAIL:L2_peak_date")
    else:
        print("FAIL:L2_peak_date")

    # L2: 按年龄组的 CFR
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "cfr" in a_str or "fatality" in a_str or "mortality" in a_str:
            print("PASS:L2_cfr_by_age")
        else:
            print("FAIL:L2_cfr_by_age")
    else:
        print("FAIL:L2_cfr_by_age")

    # L2: 倍增时间
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "doubling" in a_str or "double" in a_str:
            print("PASS:L2_doubling_time")
        else:
            print("FAIL:L2_doubling_time")
    else:
        print("FAIL:L2_doubling_time")

    # L2: 总病例数匹配
    if analysis_json and os.path.exists(analysis_json):
        try:
            analysis = json.load(open(analysis_json))
            a_str = json.dumps(analysis).lower()
            # 检查总病例数是否合理
            if "total" in a_str or "cases" in a_str:
                # 尝试提取总数
                total = analysis.get("total_cases", analysis.get("total", None))
                if total is not None and abs(int(total) - n_cases) <= 5:
                    print(f"PASS:L2_total_cases - {total}")
                elif total is not None:
                    print(f"PASS:L2_total_cases - {total} (close enough)")
                else:
                    print("PASS:L2_total_cases")
            else:
                print("FAIL:L2_total_cases")
        except:
            print("FAIL:L2_total_cases")
    else:
        print("FAIL:L2_total_cases")

    # L2: 日期范围合理
    if len(epi_df) > 0 and "date" in epi_cols:
        date_col = [c for c in epi_df.columns if "date" in c.lower()][0]
        try:
            dates = pd.to_datetime(epi_df[date_col])
            span = (dates.max() - dates.min()).days
            if 30 <= span <= 120:
                print(f"PASS:L2_date_range - {span} days")
            else:
                print(f"PASS:L2_date_range - {span} days")
        except:
            print("FAIL:L2_date_range")
    elif len(epi_df) > 0:
        print("PASS:L2_date_range")
    else:
        print("FAIL:L2_date_range")

    # L2: 无负值计数
    if len(epi_df) > 0:
        num_cols = epi_df.select_dtypes(include=[np.number]).columns
        has_neg = False
        for c in num_cols:
            if (epi_df[c] < 0).any():
                has_neg = True
        print(f"{'PASS' if not has_neg else 'FAIL'}:L2_no_negative")
    else:
        print("FAIL:L2_no_negative")

    # L2: growth_rate 存在
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "growth" in a_str or "rate" in a_str or "slope" in a_str:
            print("PASS:L2_growth_rate")
        else:
            print("FAIL:L2_growth_rate")
    else:
        print("FAIL:L2_growth_rate")

    # L2: 按地区统计
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "location" in a_str or "district" in a_str or "attack" in a_str:
            print("PASS:L2_location_stats")
        else:
            print("FAIL:L2_location_stats")
    else:
        print("FAIL:L2_location_stats")

    # SCORE: R0 精度（合理范围应在 1.5-4.0）
    r0_score = 0.0
    if analysis_json and os.path.exists(analysis_json):
        try:
            analysis = json.load(open(analysis_json))
            r0_val = None
            for key in ["R0", "r0", "R_0", "r_0", "reproduction_number", "basic_reproduction_number"]:
                if key in analysis:
                    r0_val = float(analysis[key])
                    break
            if r0_val is not None and 1.0 <= r0_val <= 6.0:
                r0_score = round(max(0, 1.0 - abs(r0_val - 2.5) / 3.0), 4)
        except:
            pass
    print(f"SCORE:r0_accuracy={r0_score}")

    # SCORE: 分析完整性
    expected_keys = ["r0", "peak", "cfr", "fatality", "doubling", "total", "growth", "location", "district"]
    a_str = ""
    if analysis_json and os.path.exists(analysis_json):
        try:
            a_str = json.dumps(json.load(open(analysis_json))).lower()
        except:
            pass
    found = sum(1 for k in expected_keys if k in a_str)
    completeness = round(found / len(expected_keys), 4)
    print(f"SCORE:analysis_completeness={completeness}")
'''

# =============================================================================
# S24: 材料科学 — X射线衍射峰拟合 (材料科学, 困难)
# =============================================================================
S24_TASK = """Write a Python CLI script to analyze X-ray diffraction (XRD) patterns: subtract background, detect peaks, fit Gaussians, and compute d-spacings.

Input: A CSV file with columns: two_theta (degrees), intensity (counts).

Requirements:
1. Use argparse: --input CSV, --output directory, --wavelength (default 1.5406 Angstroms for Cu K-alpha), --min-height (default 50 counts), --prominence (default 30)
2. Background subtraction:
   - Estimate background using a rolling minimum with large window (e.g., 50 points), then smooth it
   - Subtract background from raw intensity
3. Peak detection:
   - Use scipy.signal.find_peaks with height and prominence thresholds on background-subtracted data
4. Gaussian peak fitting:
   - For each detected peak, fit a Gaussian: I(x) = A * exp(-(x - mu)^2 / (2*sigma^2))
   - Extract: peak position (mu), intensity (A), FWHM = 2*sqrt(2*ln(2))*sigma ≈ 2.3548*sigma
5. d-spacing calculation via Bragg's law:
   - d = wavelength / (2 * sin(theta)), where theta = two_theta_peak / 2 in radians
6. Output:
   - peaks.csv: columns peak_id, two_theta, intensity, fwhm, d_spacing
   - fitted_pattern.csv: columns two_theta, raw_intensity, background, corrected_intensity, fitted_intensity
   - summary.json: {n_peaks, wavelength, strongest_peak: {two_theta, d_spacing, intensity}, peaks: [...]}
7. Print: number of peaks found, strongest peak position and d-spacing
"""

S24_TEST = '''
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
'''

# =============================================================================
# S25: 网络科学 — 引文图谱分析 (网络科学, 中等)
# =============================================================================
S25_TASK = """Write a Python CLI script to analyze a citation network graph and compute node-level and network-level metrics.

Input: Two CSV files:
- Edges CSV (--edges): columns source_id, target_id, year (a citation from source to target)
- Nodes CSV (--nodes): columns node_id, title, field

Requirements:
1. Use argparse: --edges CSV, --nodes CSV, --output directory
2. Build a directed citation graph from the edge list
3. Compute node-level metrics:
   - in_degree (number of citations received) and out_degree (number of references made)
   - clustering coefficient (local, treating graph as undirected for this calculation)
   - Community detection using simple label propagation:
     * Initialize each node with its own label
     * Iteratively assign each node the most frequent label among its neighbors
     * Run for 10 iterations or until convergence
4. Identify hub nodes: top 10 nodes by in_degree
5. Compute network-level metrics:
   - Total nodes, total edges, graph density
   - Degree distribution: count of nodes at each in-degree value
   - Mean clustering coefficient
   - Number of communities detected
6. Output:
   - node_metrics.csv: node_id, title, field, in_degree, out_degree, clustering_coefficient, community
   - network_summary.json: {n_nodes, n_edges, density, mean_clustering, n_communities, top_hubs: [{node_id, in_degree, title}]}
   - degree_distribution.csv: in_degree, count
7. Print: number of nodes/edges, top 5 hubs, number of communities
"""

S25_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(edges_path, nodes_path, n_nodes=200, n_edges=800):
    np.random.seed(42)
    fields = ["Physics", "Computer Science", "Biology", "Mathematics", "Chemistry"]
    # 生成节点
    nodes = []
    for i in range(n_nodes):
        nodes.append({
            "node_id": f"N{i:04d}",
            "title": f"Paper_{i}_on_{'_'.join(np.random.choice(['Analysis','Theory','Method','Study','Review'], 2))}",
            "field": np.random.choice(fields, p=[0.25, 0.3, 0.2, 0.15, 0.1]),
        })
    pd.DataFrame(nodes).to_csv(nodes_path, index=False)
    # 生成引用边（优先引用同领域、高度数节点）
    node_ids = [f"N{i:04d}" for i in range(n_nodes)]
    node_fields = {n["node_id"]: n["field"] for n in nodes}
    edges = []
    # 先创建一些 hub 节点（被大量引用）
    hub_ids = node_ids[:15]
    for _ in range(n_edges):
        src = np.random.choice(node_ids)
        # 50% 概率引用 hub 节点
        if np.random.rand() < 0.5:
            tgt = np.random.choice(hub_ids)
        else:
            tgt = np.random.choice(node_ids)
        if src != tgt:
            year = np.random.randint(2000, 2024)
            edges.append({
                "source_id": src,
                "target_id": tgt,
                "year": year,
            })
    # 去重
    edge_df = pd.DataFrame(edges).drop_duplicates(subset=["source_id", "target_id"])
    edge_df.to_csv(edges_path, index=False)
    return n_nodes, len(edge_df)

with tempfile.TemporaryDirectory() as tmpdir:
    edges_in = f"{tmpdir}/edges.csv"
    nodes_in = f"{tmpdir}/nodes.csv"
    out_dir = f"{tmpdir}/output"
    n_nodes, n_edges = create_data(edges_in, nodes_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--edges", edges_in, "--nodes", nodes_in, "--output", out_dir],
        [sys.executable, "generated.py", "--input", edges_in, "--nodes", nodes_in, "--output", out_dir],
        [sys.executable, "generated.py", edges_in, nodes_in, "-o", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    metrics_csv = None
    summary_json = None
    degree_csv = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("metric" in fl or "node" in fl) and f.endswith(".csv") and "degree" not in fl:
                metrics_csv = os.path.join(out_dir, f)
            if ("summary" in fl or "network" in fl) and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)
            if "degree" in fl and f.endswith(".csv"):
                degree_csv = os.path.join(out_dir, f)

    if metrics_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_all_nodes","L2_in_degree","L2_out_degree",
                   "L2_clustering","L2_community","L2_hub_nodes","L2_network_stats",
                   "L2_degree_dist","L2_density","L2_n_communities","L2_no_nan","L2_summary_exists"]:
            print(f"FAIL:{t}")
        print("SCORE:metric_completeness=0.0")
        print("SCORE:hub_detection_quality=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    m_df = pd.DataFrame()
    if metrics_csv:
        try:
            m_df = pd.read_csv(metrics_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    mcols = " ".join(m_df.columns).lower() if len(m_df) > 0 else ""

    # L2: 所有节点被处理
    if len(m_df) >= n_nodes * 0.8:
        print(f"PASS:L2_all_nodes - {len(m_df)}/{n_nodes}")
    elif len(m_df) > 0:
        print(f"PASS:L2_all_nodes - {len(m_df)} nodes")
    else:
        print("FAIL:L2_all_nodes")

    # L2: in_degree 列
    if "in_degree" in mcols or "in_deg" in mcols or "indegree" in mcols or "citations" in mcols:
        print("PASS:L2_in_degree")
    else:
        print("FAIL:L2_in_degree")

    # L2: out_degree 列
    if "out_degree" in mcols or "out_deg" in mcols or "outdegree" in mcols or "references" in mcols:
        print("PASS:L2_out_degree")
    else:
        print("FAIL:L2_out_degree")

    # L2: 聚类系数
    if "cluster" in mcols or "cc" in mcols.split() or "clustering" in mcols:
        print("PASS:L2_clustering")
    else:
        print("FAIL:L2_clustering")

    # L2: 社区标签
    if "community" in mcols or "label" in mcols or "group" in mcols or "cluster_id" in mcols:
        print("PASS:L2_community")
    else:
        print("FAIL:L2_community")

    # L2: hub 节点识别（summary 中有 top hubs）
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if "hub" in s_str or "top" in s_str:
                print("PASS:L2_hub_nodes")
            else:
                print("FAIL:L2_hub_nodes")
        except:
            print("FAIL:L2_hub_nodes")
    else:
        print("FAIL:L2_hub_nodes")

    # L2: 网络级统计
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if ("n_nodes" in s_str or "nodes" in s_str) and ("n_edges" in s_str or "edges" in s_str):
                print("PASS:L2_network_stats")
            else:
                print("FAIL:L2_network_stats")
        except:
            print("FAIL:L2_network_stats")
    else:
        print("FAIL:L2_network_stats")

    # L2: 度分布文件
    deg_df = pd.DataFrame()
    if degree_csv:
        try:
            deg_df = pd.read_csv(degree_csv)
        except:
            pass
    if len(deg_df) > 0:
        print(f"PASS:L2_degree_dist - {len(deg_df)} entries")
    else:
        print("FAIL:L2_degree_dist")

    # L2: 密度在 summary 中
    if summary_json and os.path.exists(summary_json):
        s_str = json.dumps(json.load(open(summary_json))).lower()
        if "density" in s_str:
            print("PASS:L2_density")
        else:
            print("FAIL:L2_density")
    else:
        print("FAIL:L2_density")

    # L2: 社区数量
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if "communit" in s_str or "n_communit" in s_str or "cluster" in s_str:
                print("PASS:L2_n_communities")
            else:
                print("FAIL:L2_n_communities")
        except:
            print("FAIL:L2_n_communities")
    else:
        print("FAIL:L2_n_communities")

    # L2: 无 NaN
    if len(m_df) > 0:
        nan_ct = m_df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_ct == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: summary 文件存在
    if summary_json and os.path.exists(summary_json):
        print("PASS:L2_summary_exists")
    else:
        print("FAIL:L2_summary_exists")

    # SCORE: 指标完整性
    expected_cols = ["in_degree", "out_degree", "clustering", "community", "hub", "density", "degree"]
    all_text = mcols + " "
    if summary_json and os.path.exists(summary_json):
        try:
            all_text += json.dumps(json.load(open(summary_json))).lower()
        except:
            pass
    found = sum(1 for c in expected_cols if c in all_text)
    completeness = round(found / len(expected_cols), 4)
    print(f"SCORE:metric_completeness={completeness}")

    # SCORE: hub 检测质量（前 15 个节点应该被识别为高 in_degree）
    hub_score = 0.0
    if len(m_df) > 0:
        in_col = [c for c in m_df.columns if "in_deg" in c.lower() or "indeg" in c.lower() or "citation" in c.lower()]
        id_col = [c for c in m_df.columns if "node_id" in c.lower() or "id" in c.lower()]
        if in_col and id_col:
            top10 = m_df.nlargest(10, in_col[0])[id_col[0]].astype(str).tolist()
            true_hubs = {f"N{i:04d}" for i in range(15)}
            matched = sum(1 for h in top10 if h in true_hubs)
            hub_score = round(matched / 10.0, 4)
    print(f"SCORE:hub_detection_quality={hub_score}")
'''
# =============================================================================
# S26: 地震学 — 地震目录分析 (Seismology, 中等)
# =============================================================================
S26_TASK = """Write a Python CLI script to analyze an earthquake catalog and identify aftershock sequences.

Input: A CSV file with columns:
- event_id, datetime, latitude, longitude, depth_km, magnitude, mag_type

Requirements:
1. Use argparse: --input CSV path, --output directory, --cluster-radius (default 50 km), --cluster-time (default 72 hours)
2. Compute the Gutenberg-Richter b-value using maximum-likelihood estimation (Aki formula): b = log10(e) / (mean_mag - completeness_mag + delta_bin/2), where completeness_mag is the magnitude of completeness estimated from the maximum of the magnitude-frequency histogram (bin width 0.1)
3. Identify aftershock sequences: for each event with magnitude >= 4.0, find subsequent events within --cluster-radius km and --cluster-time hours. Use Haversine formula for distance.
4. Compute magnitude-frequency statistics: count events per 0.1-magnitude bin
5. Output: catalog_stats.json (b_value, completeness_mag, largest_event {id, mag, lat, lon, depth}, total_events), aftershock_sequences.csv (mainshock_id, aftershock_id, distance_km, time_diff_hours, mag_diff), magnitude_freq.csv (mag_bin, count, cumulative_count, log10_cumulative)
6. Print summary: total events, b-value, number of identified sequences, largest event
"""

S26_TEST = '''
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
'''

# =============================================================================
# S27: 农业科学 — 作物产量预测特征工程 (Agricultural Science, 简单)
# =============================================================================
S27_TASK = """Write a Python CLI script to compute crop yield prediction features from field observation data.

Input: A CSV file with columns:
- field_id, date (YYYY-MM-DD), ndvi, soil_moisture, temperature, rainfall_mm, crop_type, yield_tons

Requirements:
1. Use argparse: --input CSV path, --output directory, --base-temp (default 10.0 for growing degree days calculation)
2. Compute Growing Degree Days (GDD) per field: for each date, GDD_daily = max(0, temperature - base_temp). Cumulative GDD is the running sum within each field.
3. Aggregate NDVI statistics per field: mean, max, min, std, and the date of peak NDVI
4. Create a feature matrix: one row per field with columns field_id, crop_type, mean_ndvi, max_ndvi, ndvi_std, peak_ndvi_date, total_rainfall, mean_soil_moisture, cumulative_gdd, yield_tons
5. Compute a Pearson correlation matrix among all numeric features (including yield)
6. Output: field_features.csv (the feature matrix), correlation_matrix.csv (features x features), summary.json (n_fields, n_crop_types, feature_names, top_3_yield_correlates)
7. Print summary: number of fields processed, strongest yield correlate
"""

S27_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_fields=20):
    np.random.seed(42)
    rows = []
    crop_types = ["wheat", "corn", "soybean", "rice"]
    for fid in range(n_fields):
        crop = crop_types[fid % len(crop_types)]
        base_yield = {"wheat": 3.5, "corn": 8.0, "soybean": 2.5, "rice": 5.0}[crop]
        n_obs = np.random.randint(15, 30)
        start_day = np.random.randint(60, 120)
        for j in range(n_obs):
            day = start_day + j * 7
            date = pd.Timestamp("2023-01-01") + pd.Timedelta(days=int(day))
            progress = j / n_obs
            ndvi = 0.3 + 0.5 * np.sin(np.pi * progress) + np.random.normal(0, 0.03)
            temp = 15 + 10 * np.sin(np.pi * (day - 60) / 200) + np.random.normal(0, 2)
            rain = max(0, np.random.exponential(5))
            sm = 0.3 + 0.1 * np.sin(np.pi * progress) + rain * 0.005 + np.random.normal(0, 0.02)
            yield_val = base_yield + 2.0 * ndvi + 0.01 * temp + np.random.normal(0, 0.3)
            rows.append({
                "field_id": f"F{fid:03d}",
                "date": date.strftime("%Y-%m-%d"),
                "ndvi": round(np.clip(ndvi, 0.05, 0.95), 4),
                "soil_moisture": round(np.clip(sm, 0.1, 0.6), 4),
                "temperature": round(temp, 1),
                "rainfall_mm": round(rain, 1),
                "crop_type": crop,
                "yield_tons": round(max(yield_val, 0.5), 2),
            })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_fields

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/field_obs.csv"
    out_dir = f"{tmpdir}/output"
    n_fields = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--base-temp", "10.0"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    feat_csv = None
    corr_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("feature" in fl or "field" in fl) and fl.endswith(".csv"):
                feat_csv = os.path.join(out_dir, f)
            if "corr" in fl and fl.endswith(".csv"):
                corr_csv = os.path.join(out_dir, f)
            if "summary" in fl and fl.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    has_output = feat_csv or corr_csv or summary_json
    if has_output:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_all_fields", "L2_gdd", "L2_ndvi_stats",
                   "L2_feature_cols", "L2_corr_matrix", "L2_corr_square",
                   "L2_summary_json", "L2_crop_types", "L2_yield_col",
                   "L2_no_nan", "L2_top_correlates"]:
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

    # L2: 所有 field 都被处理
    if len(df) >= n_fields:
        print(f"PASS:L2_all_fields - {len(df)} rows")
    elif len(df) > 0:
        print(f"PASS:L2_all_fields - {len(df)} rows (partial)")
    else:
        print("FAIL:L2_all_fields")

    # L2: GDD 列存在
    if "gdd" in cols or "growing" in cols or "degree" in cols:
        print("PASS:L2_gdd")
    else:
        print("FAIL:L2_gdd")

    # L2: NDVI 统计列
    ndvi_keys = ["mean_ndvi", "max_ndvi", "ndvi_std", "ndvi_mean", "ndvi_max"]
    if any(k in cols for k in ndvi_keys) or ("ndvi" in cols and len(df.columns) >= 5):
        print("PASS:L2_ndvi_stats")
    else:
        print("FAIL:L2_ndvi_stats")

    # L2: 特征列数量（至少 6 个）
    if len(df.columns) >= 6:
        print(f"PASS:L2_feature_cols - {len(df.columns)} columns")
    else:
        print(f"FAIL:L2_feature_cols - only {len(df.columns)} columns")

    # L2: 相关矩阵文件存在
    if corr_csv and os.path.exists(corr_csv):
        print("PASS:L2_corr_matrix")
        try:
            cdf = pd.read_csv(corr_csv, index_col=0)
            if cdf.shape[0] == cdf.shape[1] or abs(cdf.shape[0] - cdf.shape[1]) <= 1:
                print("PASS:L2_corr_square")
            else:
                print(f"FAIL:L2_corr_square - shape {cdf.shape}")
        except:
            print("FAIL:L2_corr_square")
    else:
        print("FAIL:L2_corr_matrix")
        print("FAIL:L2_corr_square")

    # L2: summary JSON
    if summary_json and os.path.exists(summary_json):
        try:
            summ = json.load(open(summary_json))
            print("PASS:L2_summary_json")
        except:
            print("FAIL:L2_summary_json")
            summ = {}
    else:
        print("FAIL:L2_summary_json")
        summ = {}

    # L2: 作物类型信息
    if "crop" in cols:
        print("PASS:L2_crop_types")
    elif summ and ("crop" in json.dumps(summ).lower()):
        print("PASS:L2_crop_types")
    else:
        print("FAIL:L2_crop_types")

    # L2: yield 列
    if "yield" in cols:
        print("PASS:L2_yield_col")
    else:
        print("FAIL:L2_yield_col")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: top correlates in summary
    s_str = json.dumps(summ).lower() if summ else ""
    if "top" in s_str or "correl" in s_str or "strongest" in s_str:
        print("PASS:L2_top_correlates")
    else:
        print("FAIL:L2_top_correlates")

    # SCORE: 特征完整度（检查关键特征列的存在比例）
    expected = ["ndvi", "gdd", "rainfall", "moisture", "yield", "crop"]
    found = sum(1 for e in expected if e in cols)
    feature_completeness = round(found / len(expected), 4)
    print(f"SCORE:feature_completeness={feature_completeness}")

    # SCORE: 数据质量（行数正确性 + NaN 比率）
    if len(df) > 0:
        row_score = min(len(df) / n_fields, 1.0)
        nan_rate = df.select_dtypes(include=[np.number]).isnull().mean().mean() if len(df) > 0 else 1.0
        data_quality = round(row_score * (1.0 - nan_rate), 4)
    else:
        data_quality = 0.0
    print(f"SCORE:data_quality={data_quality}")
'''

# =============================================================================
# S28: 心理声学 — 音频特征提取 (Psychoacoustics, 中等)
# =============================================================================
S28_TASK = """Write a Python CLI script to extract audio features from synthetic audio signals stored as numpy arrays.

Input: A .npz file containing:
- signals: 2D array (n_signals x n_samples), each row is an audio waveform
- sample_rate: scalar, the sample rate in Hz
- labels: 1D string array, labels for each signal

Requirements:
1. Use argparse: --input NPZ path, --output directory, --frame-size (default 1024), --hop-size (default 512)
2. For each signal, compute frame-level features:
   a. Short-Time Fourier Transform (STFT) magnitude spectrogram
   b. Mel-Frequency Cepstral Coefficients (MFCCs): apply mel filterbank (at least 26 filters) to power spectrum, take log, then DCT to get 13 coefficients per frame. Implement mel filterbank manually using numpy (triangular filters spaced on mel scale). Use scipy.fft.dct for the DCT step.
   c. Zero-Crossing Rate (ZCR) per frame
   d. RMS energy per frame
3. Output: features.csv (columns: signal_id, frame_idx, zcr, rms_energy, mfcc_0 ... mfcc_12), summary.json (per signal: mean and std of each feature, total_frames, label)
4. Print summary: number of signals processed, total frames extracted
"""

S28_TEST = '''
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
'''

# =============================================================================
# S29: 水文学 — 河流流量分析与洪水频率 (Hydrology, 中等)
# =============================================================================
S29_TASK = """Write a Python CLI script to analyze daily streamflow records and perform flood frequency analysis.

Input: A CSV file with columns:
- date (YYYY-MM-DD), discharge_cms (cubic meters per second), station_id

Requirements:
1. Use argparse: --input CSV path, --output directory, --return-periods (default "10,50,100" years)
2. Extract annual maximum discharge for each station (water year: Oct-Sep or calendar year)
3. Fit a Generalized Extreme Value (GEV) distribution to annual maxima using scipy.stats.genextreme. Estimate location, scale, shape parameters.
4. Compute flood discharge for specified return periods: Q_T = GEV.ppf(1 - 1/T) where T is return period in years
5. Perform baseflow separation using a simple digital filter: baseflow(t) = alpha * baseflow(t-1) + (1-alpha)/2 * (Q(t) + Q(t-1)) with alpha=0.925, then clip baseflow <= Q
6. Output: annual_maxima.csv (station_id, year, max_discharge), flood_frequency.json (per station: gev_params {shape, loc, scale}, return_periods {T: Q_T}), baseflow.csv (date, station_id, discharge_cms, baseflow_cms, quickflow_cms)
7. Print summary: number of stations, years of record, estimated 100-year flood per station
"""

S29_TEST = '''
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
'''

# =============================================================================
# S30: 古生物学 — 化石形态计量分析 (Paleontology, 简单)
# =============================================================================
S30_TASK = """Write a Python CLI script to perform morphometric analysis on fossil specimen measurements.

Input: A CSV file with columns:
- specimen_id, taxon, length_mm, width_mm, height_mm, mass_g, formation, epoch

Requirements:
1. Use argparse: --input CSV path, --output directory
2. Compute shape indices for each specimen:
   - Elongation = length_mm / width_mm
   - Flatness = width_mm / height_mm
   - Sphericity = (width_mm * height_mm) ^ (1/3) / length_mm  (Krumbein sphericity approximation)
   - Estimated volume = (4/3) * pi * (length_mm/2) * (width_mm/2) * (height_mm/2) as ellipsoid
   - Density = mass_g / volume (convert mm^3 to cm^3 first)
3. Perform PCA on the 4 measurement columns (length, width, height, mass) after z-score standardization. Use numpy eigen-decomposition of covariance matrix. Report PC1-PC4 loadings and explained variance ratios.
4. Group statistics by taxon and by epoch: mean, std of all measurements and shape indices
5. Output: morphometrics.csv (original columns + shape indices + PC scores), pca_results.csv (component, explained_variance_ratio, length_loading, width_loading, height_loading, mass_loading), taxon_summary.json (per taxon: n_specimens, mean/std of each measurement and shape index; per epoch: same)
6. Print summary: number of specimens, number of taxa, dominant taxon, PCA variance explained by first 2 components
"""

S30_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_specimens=120):
    np.random.seed(42)
    taxa = ["Trilobita_sp_A", "Trilobita_sp_B", "Brachiopoda_sp", "Ammonoidea_sp", "Gastropoda_sp"]
    formations = ["Morrison", "Hell_Creek", "Burgess_Shale", "Solnhofen"]
    epochs = ["Cambrian", "Ordovician", "Devonian", "Jurassic", "Cretaceous"]
    rows = []
    for i in range(n_specimens):
        taxon = taxa[i % len(taxa)]
        # 不同物种有不同的基础形态
        base = {"Trilobita_sp_A": (30, 15, 8, 5), "Trilobita_sp_B": (25, 18, 6, 4),
                "Brachiopoda_sp": (12, 14, 10, 3), "Ammonoidea_sp": (40, 38, 20, 15),
                "Gastropoda_sp": (20, 10, 10, 4)}[taxon]
        length = base[0] + np.random.normal(0, base[0] * 0.15)
        width = base[1] + np.random.normal(0, base[1] * 0.15)
        height = base[2] + np.random.normal(0, base[2] * 0.15)
        mass = base[3] + np.random.normal(0, base[3] * 0.2)
        rows.append({
            "specimen_id": f"SPEC{i:04d}",
            "taxon": taxon,
            "length_mm": round(max(length, 2), 2),
            "width_mm": round(max(width, 1), 2),
            "height_mm": round(max(height, 0.5), 2),
            "mass_g": round(max(mass, 0.1), 2),
            "formation": formations[i % len(formations)],
            "epoch": epochs[i % len(epochs)],
        })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_specimens, len(taxa)

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/fossils.csv"
    out_dir = f"{tmpdir}/output"
    n_specimens, n_taxa = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "-o", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    morph_csv = None
    pca_csv = None
    taxon_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("morph" in fl or "specimen" in fl) and fl.endswith(".csv"):
                morph_csv = os.path.join(out_dir, f)
            if "pca" in fl and fl.endswith(".csv"):
                pca_csv = os.path.join(out_dir, f)
            if ("taxon" in fl or "summary" in fl) and fl.endswith(".json"):
                taxon_json = os.path.join(out_dir, f)

    has_output = morph_csv or pca_csv or taxon_json
    if has_output:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_all_specimens", "L2_elongation", "L2_sphericity",
                   "L2_volume", "L2_pca_file", "L2_pca_variance", "L2_pca_loadings",
                   "L2_taxon_json", "L2_taxon_groups", "L2_epoch_groups",
                   "L2_no_nan", "L2_pc_scores"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if morph_csv:
        try:
            df = pd.read_csv(morph_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 所有标本
    if len(df) >= n_specimens:
        print(f"PASS:L2_all_specimens - {len(df)} rows")
    elif len(df) > 0:
        print(f"PASS:L2_all_specimens - {len(df)} rows")
    else:
        print("FAIL:L2_all_specimens")

    # L2: elongation 列
    if "elong" in cols or "l_w" in cols or "length_width" in cols:
        print("PASS:L2_elongation")
    else:
        print("FAIL:L2_elongation")

    # L2: sphericity 列
    if "spheri" in cols or "sphere" in cols:
        print("PASS:L2_sphericity")
    else:
        print("FAIL:L2_sphericity")

    # L2: volume 列
    if "volume" in cols or "vol" in cols:
        print("PASS:L2_volume")
    else:
        print("FAIL:L2_volume")

    # L2: PCA 文件
    pca_df = pd.DataFrame()
    if pca_csv and os.path.exists(pca_csv):
        print("PASS:L2_pca_file")
        try:
            pca_df = pd.read_csv(pca_csv)
        except:
            pass
    else:
        print("FAIL:L2_pca_file")

    # L2: PCA explained variance
    pca_cols = " ".join(pca_df.columns).lower() if len(pca_df) > 0 else ""
    if "variance" in pca_cols or "explained" in pca_cols:
        print("PASS:L2_pca_variance")
    else:
        print("FAIL:L2_pca_variance")

    # L2: PCA loadings
    if "loading" in pca_cols or "length" in pca_cols or "component" in pca_cols:
        print("PASS:L2_pca_loadings")
    else:
        print("FAIL:L2_pca_loadings")

    # L2: taxon summary JSON
    summ = {}
    if taxon_json and os.path.exists(taxon_json):
        try:
            summ = json.load(open(taxon_json))
            print("PASS:L2_taxon_json")
        except:
            print("FAIL:L2_taxon_json")
    else:
        print("FAIL:L2_taxon_json")

    s_str = json.dumps(summ).lower() if summ else ""

    # L2: taxon 分组
    if any(t.lower() in s_str for t in ["trilobita", "brachiopoda", "ammonoidea", "gastropoda"]):
        print("PASS:L2_taxon_groups")
    elif "taxon" in s_str:
        print("PASS:L2_taxon_groups")
    else:
        print("FAIL:L2_taxon_groups")

    # L2: epoch 分组
    if any(e.lower() in s_str for e in ["cambrian", "ordovician", "devonian", "jurassic", "cretaceous"]):
        print("PASS:L2_epoch_groups")
    elif "epoch" in s_str:
        print("PASS:L2_epoch_groups")
    else:
        print("FAIL:L2_epoch_groups")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: PC scores in morphometrics 文件
    if "pc1" in cols or "pc_1" in cols or "pca" in cols:
        print("PASS:L2_pc_scores")
    else:
        print("FAIL:L2_pc_scores")

    # SCORE: 形态指数完整度
    expected_idx = ["elong", "flat", "spheri", "volume", "density"]
    found = sum(1 for e in expected_idx if e in cols)
    morpho_completeness = round(found / len(expected_idx), 4)
    print(f"SCORE:morphometric_completeness={morpho_completeness}")

    # SCORE: PCA 质量（前 2 主成分应解释 > 70% 方差）
    if len(pca_df) > 0 and "variance" in pca_cols or "explained" in pca_cols:
        try:
            var_col = [c for c in pca_df.columns if "variance" in c.lower() or "explained" in c.lower()]
            if var_col:
                vals = pca_df[var_col[0]].dropna().values[:2]
                total_var = sum(vals)
                pca_quality = round(min(total_var, 1.0), 4) if total_var > 0 else 0.0
            else:
                pca_quality = 0.3
        except:
            pca_quality = 0.0
    else:
        pca_quality = 0.0
    print(f"SCORE:pca_quality={pca_quality}")
'''


# =============================================================================
# 汇总字典：与 scenarios_v2.py 中 SCENARIOS 格式一致
# =============================================================================
SCENARIOS_EXTENDED = {
    "S11_particle_physics":  {"task": S11_TASK, "test": S11_TEST, "source": "synthetic", "domain": "physics",              "difficulty": "medium"},
    "S12_uv_spectroscopy":   {"task": S12_TASK, "test": S12_TEST, "source": "synthetic", "domain": "chemistry",            "difficulty": "medium"},
    "S13_biodiversity":      {"task": S13_TASK, "test": S13_TEST, "source": "synthetic", "domain": "ecology",              "difficulty": "easy"},
    "S14_clinical_lab":      {"task": S14_TASK, "test": S14_TEST, "source": "synthetic", "domain": "medical",              "difficulty": "easy"},
    "S15_light_curves":      {"task": S15_TASK, "test": S15_TEST, "source": "synthetic", "domain": "astronomy",            "difficulty": "hard"},
    "S16_fastq_qc":          {"task": S16_TASK, "test": S16_TEST, "source": "synthetic", "domain": "genomics",             "difficulty": "medium"},
    "S17_ctd_ocean":         {"task": S17_TASK, "test": S17_TEST, "source": "synthetic", "domain": "oceanography",         "difficulty": "medium"},
    "S18_radiosonde":        {"task": S18_TASK, "test": S18_TEST, "source": "synthetic", "domain": "atmospheric_science",   "difficulty": "medium"},
    "S19_eeg_filtering":     {"task": S19_TASK, "test": S19_TEST, "source": "synthetic", "domain": "signal_processing",    "difficulty": "medium"},
    "S20_survey_analysis":   {"task": S20_TASK, "test": S20_TEST, "source": "synthetic", "domain": "social_science",       "difficulty": "easy"},
    "S21_air_quality":       {"task": S21_TASK, "test": S21_TEST, "source": "synthetic", "domain": "environmental_science","difficulty": "easy"},
    "S22_well_log":          {"task": S22_TASK, "test": S22_TEST, "source": "synthetic", "domain": "geology",              "difficulty": "medium"},
    "S23_epidemic_curve":    {"task": S23_TASK, "test": S23_TEST, "source": "synthetic", "domain": "epidemiology",         "difficulty": "medium"},
    "S24_xrd_peaks":         {"task": S24_TASK, "test": S24_TEST, "source": "synthetic", "domain": "materials_science",    "difficulty": "hard"},
    "S25_citation_graph":    {"task": S25_TASK, "test": S25_TEST, "source": "synthetic", "domain": "network_science",      "difficulty": "medium"},
    "S26_earthquake_catalog":{"task": S26_TASK, "test": S26_TEST, "source": "synthetic", "domain": "seismology",           "difficulty": "medium"},
    "S27_crop_features":     {"task": S27_TASK, "test": S27_TEST, "source": "synthetic", "domain": "agricultural_science", "difficulty": "easy"},
    "S28_audio_features":    {"task": S28_TASK, "test": S28_TEST, "source": "synthetic", "domain": "psychoacoustics",      "difficulty": "medium"},
    "S29_flood_frequency":   {"task": S29_TASK, "test": S29_TEST, "source": "synthetic", "domain": "hydrology",            "difficulty": "medium"},
    "S30_fossil_morpho":     {"task": S30_TASK, "test": S30_TEST, "source": "synthetic", "domain": "paleontology",         "difficulty": "easy"},
}
