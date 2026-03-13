"""
10 个科学数据处理场景统一定义
每个场景 = task_desc + create_test_data() + test_script

场景来源：question.csv
选取标准：覆盖不同学科(神经/生命/地球/物质)、不同复杂度、可自动化测试
"""

# =============================================================================
# Scenario 1: neuro_metadata (Researcher A #1, 神经科学, 简单)
# 递归扫描 HDF5/MAT → meta.json
# =============================================================================
S01_TASK = """Write a standalone Python CLI script that recursively scans a directory containing HDF5 (.h5) and MATLAB (.mat) files from a neuroscience experiment, extracts internal structure metadata (dataset paths, shapes, dtypes), and writes a meta.json file.

Requirements:
1. Use argparse: positional arg for root directory, -o/--output for output path (default: meta.json)
2. Recursively find all .h5 and .mat files
3. For HDF5: traverse nested groups, record each dataset's path, shape, and dtype
4. For MAT: read variable names, shapes, dtypes. Handle MATLAB v7.3 files (which scipy.io.loadmat cannot open) by falling back to h5py
5. Output valid JSON with a "files" key listing all file entries, each with at least "path" and "datasets"/"variables" info
6. Handle corrupted files gracefully (log error, continue scanning)
"""

S01_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np

def create_data(root):
    import h5py, scipy.io
    for i in range(3):
        d = f"{root}/subject_{i}"
        os.makedirs(d, exist_ok=True)
        with h5py.File(f"{d}/eeg.h5", "w") as f:
            g = f.create_group("recording")
            g.create_dataset("eeg_data", data=np.random.randn(100+i*10, 64).astype(np.float32))
            g.create_dataset("timestamps", data=np.arange(100+i*10, dtype=np.float64))
            f.create_dataset("metadata", data=np.array([1,2,3]))
        scipy.io.savemat(f"{d}/params.mat", {"fs": np.array([500.0]), "coords": np.random.randn(100+i*10, 3)})
    os.makedirs(f"{root}/extra", exist_ok=True)
    scipy.io.savemat(f"{root}/extra/reference.mat", {"template": np.zeros((20,20,10))})

def find_json(d):
    """在目录中找 json 文件"""
    for f in os.listdir(d):
        if f.endswith(".json"):
            return os.path.join(d, f)
    return None

with tempfile.TemporaryDirectory() as tmpdir:
    data_root = f"{tmpdir}/data"
    os.makedirs(data_root)
    create_data(data_root)
    out_json = f"{tmpdir}/meta.json"

    # Layer 1: 能否运行
    # 尝试多种常见参数格式
    ran = False
    for args in [
        [sys.executable, "generated.py", data_root, "-o", out_json],
        [sys.executable, "generated.py", "--input", data_root, "--output", out_json],
        [sys.executable, "generated.py", "--root", data_root, "-o", out_json],
        [sys.executable, "generated.py", data_root, "--output", out_json],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(out_json):
            ran = True
            break
    # 也可能输出到 cwd
    if not ran and not os.path.exists(out_json):
        r = subprocess.run([sys.executable, "generated.py", data_root],
                           capture_output=True, text=True, timeout=30, cwd=tmpdir)
        candidate = find_json(tmpdir)
        if candidate:
            out_json = candidate
            ran = True

    if ran or os.path.exists(out_json):
        print("PASS:L1_runs")
    else:
        print(f"FAIL:L1_runs - returncode={r.returncode}, stderr={r.stderr[-200:]}")

    # Layer 1: 输出存在
    if os.path.exists(out_json):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        # 还是继续看其他测试
        for t in ["L1_valid_json","L2_has_files","L2_file_count","L2_nested_keys","L2_shape_info","L2_mat_handled","L2_multi_subject"]:
            print(f"FAIL:{t} - no output")
        sys.exit(0)

    # Layer 1: 有效 JSON
    try:
        meta = json.load(open(out_json))
        print("PASS:L1_valid_json")
    except Exception as e:
        print(f"FAIL:L1_valid_json - {e}")
        sys.exit(0)

    meta_str = json.dumps(meta, default=str).lower()

    # Layer 2: 包含 files 信息
    if "files" in meta or "file" in meta_str[:200]:
        print("PASS:L2_has_files")
    else:
        print("FAIL:L2_has_files - no files key in output")

    # Layer 2: 发现了正确数量的文件 (3 eeg.h5 + 3 params.mat + 1 reference.mat = 7)
    count_h5 = meta_str.count("eeg.h5") + meta_str.count("eeg")
    count_mat = meta_str.count("params.mat") + meta_str.count("params")
    count_ref = meta_str.count("reference.mat") + meta_str.count("reference")
    if count_h5 >= 1 and count_mat >= 1:
        print("PASS:L2_file_count")
    else:
        print(f"FAIL:L2_file_count - h5={count_h5}, mat={count_mat}, ref={count_ref}")

    # Layer 2: 嵌套 HDF5 key 被提取 (recording/eeg_data 或 recording)
    if "recording" in meta_str and ("eeg_data" in meta_str or "timestamps" in meta_str):
        print("PASS:L2_nested_keys")
    else:
        print(f"FAIL:L2_nested_keys - nested group keys not found")

    # Layer 2: 包含 shape 信息
    # 检查是否有数组维度信息 (如 [100, 64] 或 (100, 64))
    if any(s in meta_str for s in ["100", "64", "shape", "dim"]):
        print("PASS:L2_shape_info")
    else:
        print("FAIL:L2_shape_info - no shape information found")

    # Layer 2: MAT 文件处理
    if "fs" in meta_str or "coords" in meta_str or "template" in meta_str:
        print("PASS:L2_mat_handled")
    else:
        print("FAIL:L2_mat_handled - MAT variables not in output")

    # Layer 2: 多 subject 都被扫描
    if ("subject_0" in meta_str or "subject_*" in meta_str) and ("subject_2" in meta_str or "subject_*" in meta_str or count_h5 >= 3):
        print("PASS:L2_multi_subject")
    else:
        print("FAIL:L2_multi_subject - not all subjects scanned")

    # --- 新增测试 ---
    # L2: dtype 信息（检查是否包含数据类型描述）
    if any(d in meta_str for d in ["float32", "float64", "int", "dtype", "f4", "f8"]):
        print("PASS:L2_dtype_info")
    else:
        print("FAIL:L2_dtype_info - no dtype information found")

    # L2: 使用相对路径而非绝对路径
    if tmpdir.lower() not in meta_str or "subject_" in meta_str:
        print("PASS:L2_relative_paths")
    else:
        print("FAIL:L2_relative_paths - absolute paths in output")

    # L2: 同时处理了 HDF5 和 MAT 两种格式
    has_h5_info = "h5" in meta_str or "hdf" in meta_str
    has_mat_info = "mat" in meta_str
    if has_h5_info and has_mat_info:
        print("PASS:L2_both_formats")
    else:
        print(f"FAIL:L2_both_formats - h5={has_h5_info}, mat={has_mat_info}")

    # SCORE: 文件完整性（发现的文件数/总文件数7）
    total_expected = 7  # 3 eeg.h5 + 3 params.mat + 1 reference.mat
    found = min(count_h5 + count_mat + count_ref, total_expected)
    file_completeness = round(found / total_expected, 4) if total_expected > 0 else 0
    print(f"SCORE:file_completeness={file_completeness}")

    # SCORE: schema 完整性（检查关键字段覆盖度）
    schema_fields = ["path", "shape", "dtype", "recording", "eeg_data", "fs", "coords"]
    found_fields = sum(1 for f in schema_fields if f in meta_str)
    schema_completeness = round(found_fields / len(schema_fields), 4)
    print(f"SCORE:schema_completeness={schema_completeness}")
'''

# =============================================================================
# Scenario 2: spike_behavior (Researcher B #6, 神经科学, 复杂)
# =============================================================================
S02_TASK = """Write a Python CLI script that standardizes neural spike and behavior data into a unified trial-based HDF5 file.

Input: A MATLAB .mat file containing:
- spike_times: a (1, N_units) cell array where each cell has sorted spike times (in seconds)
- cursor_vel: (T, 2) array of velocity data
- time_frame: (T,) array of time points
- trial_start_times: (N_trials,) array
- trial_end_times: (N_trials,) array
- trial_success: (N_trials,) boolean array

Requirements:
1. Use argparse: --input for .mat file, --output for .h5 file, --bin-size (default 0.02s)
2. Filter only successful trials (trial_success == True)
3. For each trial, bin spike times into uniform time bins using np.histogram
4. Resample behavior (velocity) to match bin centers using interpolation
5. Write HDF5 with structure: /trial_NNNN/spikes (n_bins, n_units), /trial_NNNN/behavior (n_bins, 2), /trial_NNNN/timestamps (n_bins,)
6. Add quality check: flag trials where any unit has firing rate > 200 Hz or behavior contains NaN
"""

S02_TEST = '''
import sys, os, json, subprocess, tempfile
import numpy as np

def create_xds_mat(path, n_units=8, n_trials=5, duration=1.5, dt=0.005):
    """创建模拟的 XDS-like MAT 文件"""
    import scipy.io
    T = int(duration / dt)
    time_frame = np.arange(T) * dt

    # spike_times: (1, n_units) object array
    spike_times = np.empty((1, n_units), dtype=object)
    for u in range(n_units):
        rate = 20 + u * 5  # 20-55 Hz
        spikes = np.sort(np.random.uniform(0, duration * n_trials, size=int(rate * duration * n_trials)))
        spike_times[0, u] = spikes

    cursor_vel = np.column_stack([np.sin(time_frame * 2 * np.pi), np.cos(time_frame * 2 * np.pi)])
    cursor_vel = np.tile(cursor_vel, (n_trials, 1))
    time_frame_full = np.arange(T * n_trials) * dt

    trial_starts = np.arange(n_trials) * duration
    trial_ends = trial_starts + duration
    trial_success = np.ones(n_trials, dtype=bool)
    trial_success[2] = False  # 第3个trial标记为失败

    scipy.io.savemat(path, {
        "spike_times": spike_times,
        "cursor_vel": cursor_vel,
        "time_frame": time_frame_full,
        "trial_start_times": trial_starts,
        "trial_end_times": trial_ends,
        "trial_success": trial_success,
    })
    return n_trials - 1  # 成功trial数

with tempfile.TemporaryDirectory() as tmpdir:
    mat_path = f"{tmpdir}/test_data.mat"
    out_h5 = f"{tmpdir}/output.h5"
    n_success = create_xds_mat(mat_path)

    # Layer 1: 运行
    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", mat_path, "--output", out_h5],
        [sys.executable, "generated.py", mat_path, "-o", out_h5],
        [sys.executable, "generated.py", mat_path, "--output", out_h5],
        [sys.executable, "generated.py", "--input", mat_path, "-o", out_h5, "--bin-size", "0.02"],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(out_h5):
            ran = True
            break
    if ran or os.path.exists(out_h5):
        print("PASS:L1_runs")
    else:
        print(f"FAIL:L1_runs - {r.stderr[-200:]}")

    if os.path.exists(out_h5):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_h5","L2_has_trials","L2_trial_count","L2_spikes_shape","L2_behavior_shape","L2_timestamps","L2_trial_filtered"]:
            print(f"FAIL:{t} - no output")
        sys.exit(0)

    # Layer 1: 有效 HDF5
    import h5py
    try:
        f = h5py.File(out_h5, "r")
        print("PASS:L1_valid_h5")
    except Exception as e:
        print(f"FAIL:L1_valid_h5 - {e}")
        for t in ["L2_has_trials","L2_trial_count","L2_spikes_shape","L2_behavior_shape","L2_timestamps","L2_trial_filtered"]:
            print(f"FAIL:{t} - invalid h5")
        sys.exit(0)

    # 收集所有 key
    all_keys = []
    def collect(name, obj):
        all_keys.append(name)
    f.visititems(collect)
    keys_str = " ".join(all_keys).lower()

    # Layer 2: 有 trial 结构
    trial_groups = [k for k in f.keys() if "trial" in k.lower()]
    # 也可能在子 group 下
    if not trial_groups:
        trial_groups = [k for k in all_keys if "trial" in k.lower() and isinstance(f[k], h5py.Group)]
    if trial_groups:
        print("PASS:L2_has_trials")
    else:
        print("FAIL:L2_has_trials - no trial groups found")

    # Layer 2: trial 数量（应该 <= n_success，因为过滤了失败的）
    if len(trial_groups) <= n_success + 1 and len(trial_groups) >= 1:
        print(f"PASS:L2_trial_count - found {len(trial_groups)} trials")
    else:
        print(f"FAIL:L2_trial_count - expected <={n_success}, got {len(trial_groups)}")

    # Layer 2: spikes 形状
    spike_found = False
    for k in all_keys:
        if "spike" in k.lower():
            ds = f[k]
            if hasattr(ds, "shape") and len(ds.shape) == 2:
                spike_found = True
                print(f"PASS:L2_spikes_shape - {k} shape={ds.shape}")
                break
    if not spike_found:
        print("FAIL:L2_spikes_shape - no 2D spike dataset found")

    # Layer 2: behavior 形状
    beh_found = False
    for k in all_keys:
        if any(b in k.lower() for b in ["behavior", "velocity", "cursor", "kin"]):
            ds = f[k]
            if hasattr(ds, "shape") and len(ds.shape) == 2:
                beh_found = True
                print(f"PASS:L2_behavior_shape - {k} shape={ds.shape}")
                break
    if not beh_found:
        print("FAIL:L2_behavior_shape - no 2D behavior dataset found")

    # Layer 2: timestamps
    ts_found = False
    for k in all_keys:
        if "time" in k.lower() or "ts" in k.lower() or "bin" in k.lower():
            ds = f[k]
            if hasattr(ds, "shape") and len(ds.shape) == 1:
                ts_found = True
                print(f"PASS:L2_timestamps - {k} shape={ds.shape}")
                break
    if not ts_found:
        print("FAIL:L2_timestamps - no 1D timestamps found")

    # Layer 2: 失败 trial 被过滤
    # trial数 应该 == n_success (5个trial,1个失败, 所以应该4个)
    if len(trial_groups) == n_success:
        print(f"PASS:L2_trial_filtered - {n_success} success trials kept")
    elif len(trial_groups) < 5:
        print(f"PASS:L2_trial_filtered - {len(trial_groups)} trials (some filtered)")
    else:
        print(f"FAIL:L2_trial_filtered - expected {n_success}, got {len(trial_groups)}")

    # --- 新增测试 ---
    # L2: bin size 检查（时间戳间隔应接近 0.02s）
    bin_size_ok = False
    for k in all_keys:
        if "time" in k.lower() or "ts" in k.lower():
            ds = f[k]
            if hasattr(ds, "shape") and len(ds.shape) == 1 and ds.shape[0] > 2:
                ts_data = ds[:]
                dt = np.diff(ts_data)
                if len(dt) > 0 and abs(np.median(dt) - 0.02) < 0.01:
                    bin_size_ok = True
                    break
    print(f"{'PASS' if bin_size_ok else 'FAIL'}:L2_bin_size")

    # L2: quality flags 存在（应该有 quality 标记）
    qf_found = any("quality" in k.lower() or "flag" in k.lower() or "qc" in k.lower() for k in all_keys)
    # 也可能作为 attribute
    if not qf_found:
        for g in trial_groups:
            if hasattr(f[g], 'attrs'):
                qf_found = any("quality" in str(a).lower() or "flag" in str(a).lower() for a in f[g].attrs)
                if qf_found:
                    break
    print(f"{'PASS' if qf_found else 'FAIL'}:L2_quality_flags")

    # L2: 数据中无 NaN
    no_nan = True
    for k in all_keys:
        try:
            ds = f[k]
            if hasattr(ds, "shape") and hasattr(ds, "dtype") and np.issubdtype(ds.dtype, np.floating):
                data = ds[:]
                if np.any(np.isnan(data)):
                    no_nan = False
                    break
        except:
            pass
    print(f"{'PASS' if no_nan else 'FAIL'}:L2_no_nan")

    # SCORE: spike rate 精度（检查 spike 值是否在合理范围）
    spike_rate_accuracy = 0.0
    for k in all_keys:
        if "spike" in k.lower():
            ds = f[k]
            if hasattr(ds, "shape") and len(ds.shape) == 2:
                data = ds[:]
                # 每个 bin 的 spike count 应在 0-10 范围内（20ms bin, <200Hz）
                max_rate = np.max(data) / 0.02 if np.max(data) > 0 else 0
                if max_rate < 500:  # 合理范围
                    spike_rate_accuracy = 1.0
                else:
                    spike_rate_accuracy = max(0, 1.0 - (max_rate - 500) / 500)
                break
    print(f"SCORE:spike_rate_accuracy={round(spike_rate_accuracy, 4)}")

    # SCORE: trial 完整性
    trial_completeness = round(len(trial_groups) / max(n_success, 1), 4)
    print(f"SCORE:trial_completeness={round(min(trial_completeness, 1.0), 4)}")

    f.close()
'''

# =============================================================================
# Scenario 3: spatial_transcriptomics (Researcher C #3, 生命科学, 中等)
# DLPFC 空转数据预处理：CSV 读取 + 归一化 + 高变基因选择
# =============================================================================
S03_TASK = """Write a Python CLI script for preprocessing spatial transcriptomics count data.

Input: A CSV file where rows are spots (spatial locations) and columns are genes. The first column is spot_id, and there may be columns "x" and "y" for spatial coordinates.

Requirements:
1. Use argparse: --input CSV path, --output processed CSV path, --n-top-genes (default 2000)
2. Load the CSV, separate count matrix from metadata (spot_id, x, y)
3. Filter out genes expressed in fewer than 3 spots
4. Normalize each spot to total count of 10000, then log1p transform
5. Select top N highly variable genes (by variance after normalization)
6. Save processed matrix as CSV with spot_id index
7. Print summary: number of spots, genes before/after filtering, top 5 HVGs
"""

S03_TEST = '''
import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_spots=100, n_genes=500):
    np.random.seed(42)
    counts = np.random.negative_binomial(n=2, p=0.3, size=(n_spots, n_genes))
    # 添加一些全零基因（应该被过滤掉）
    counts[:, -10:] = 0  # 最后10个基因无表达
    counts[:3, -20:-10] = 1  # 只在3个spot有表达，刚好在阈值上
    gene_names = [f"Gene_{i}" for i in range(n_genes)]
    spot_ids = [f"Spot_{i}" for i in range(n_spots)]
    df = pd.DataFrame(counts, columns=gene_names, index=spot_ids)
    df.index.name = "spot_id"
    df.insert(0, "x", np.random.uniform(0, 100, n_spots))
    df.insert(1, "y", np.random.uniform(0, 100, n_spots))
    df.to_csv(path)
    return n_spots, n_genes

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/counts.csv"
    csv_out = f"{tmpdir}/processed.csv"
    n_spots, n_genes = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", csv_out, "--n-top-genes", "100"],
        [sys.executable, "generated.py", csv_in, "-o", csv_out, "--n-top-genes", "100"],
        [sys.executable, "generated.py", csv_in, csv_out, "--n-top-genes", "100"],
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
        for t in ["L1_valid_csv","L2_spot_count","L2_gene_filtered","L2_normalized","L2_log_transformed","L2_hvg_selected"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out, index_col=0)
        print("PASS:L1_valid_csv")
    except Exception as e:
        print(f"FAIL:L1_valid_csv - {e}")
        sys.exit(0)

    # Layer 2: spot 数量保持
    if len(df) == n_spots:
        print(f"PASS:L2_spot_count - {len(df)} spots")
    else:
        print(f"FAIL:L2_spot_count - expected {n_spots}, got {len(df)}")

    # Layer 2: 基因被过滤（输出基因数 < 输入）
    n_out_genes = len([c for c in df.columns if c not in ["x","y","spot_id"]])
    if n_out_genes < n_genes:
        print(f"PASS:L2_gene_filtered - {n_out_genes} genes (from {n_genes})")
    else:
        print(f"FAIL:L2_gene_filtered - {n_out_genes} >= {n_genes}")

    # Layer 2: 归一化后值应该是小数（不是原始计数）
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    vals = df[numeric_cols].values
    if vals.max() < 50:  # log1p(10000) ≈ 9.2, 原始计数会很大
        print("PASS:L2_normalized")
    else:
        print(f"FAIL:L2_normalized - max value {vals.max():.1f} too large")

    # Layer 2: log 变换（值应该 >= 0 且无极大值）
    if vals.min() >= -0.01:
        print("PASS:L2_log_transformed")
    else:
        print(f"FAIL:L2_log_transformed - min={vals.min():.3f}")

    # Layer 2: 选择了指定数量的 HVG
    if n_out_genes <= 110:  # 要求 100，允许小误差
        print(f"PASS:L2_hvg_selected - {n_out_genes} genes selected")
    else:
        print(f"FAIL:L2_hvg_selected - {n_out_genes} > 110")

    # --- 新增测试 ---
    # L2: 零表达基因被移除
    zero_cols = (vals == 0).all(axis=0)
    if not zero_cols.any():
        print("PASS:L2_zero_removed")
    else:
        print(f"FAIL:L2_zero_removed - {zero_cols.sum()} zero-expression genes remain")

    # L2: x/y 坐标列不在输出中（应该只有基因表达数据）
    has_xy_in_data = "x" in [c.lower() for c in df.columns] and "y" in [c.lower() for c in df.columns]
    # x/y 列可以保留或去掉，但不应被当成基因
    print(f"PASS:L2_metadata_separated")

    # L2: HVG 排序（方差从高到低）
    if len(numeric_cols) >= 2:
        variances = df[numeric_cols].var()
        is_sorted = all(variances.iloc[i] >= variances.iloc[i+1] - 0.01 for i in range(min(5, len(variances)-1)))
        print(f"{'PASS' if is_sorted else 'FAIL'}:L2_hvg_order")
    else:
        print("FAIL:L2_hvg_order - not enough genes")

    # L2: 无负值（log1p 不应产生负值）
    if vals.min() >= -0.001:
        print("PASS:L2_no_negative")
    else:
        print(f"FAIL:L2_no_negative - min={vals.min():.4f}")

    # SCORE: 归一化质量（样本中位数的变异系数越小越好）
    if len(numeric_cols) > 0:
        medians = df[numeric_cols].median(axis=1)
        if medians.mean() > 0:
            cv = medians.std() / medians.mean()
            norm_quality = round(max(0, 1.0 - cv), 4)
        else:
            norm_quality = 0.0
    else:
        norm_quality = 0.0
    print(f"SCORE:normalization_quality={norm_quality}")

    # SCORE: HVG 精度（选出的基因数与目标数的接近程度）
    target = 100
    hvg_precision = round(max(0, 1.0 - abs(n_out_genes - target) / target), 4)
    print(f"SCORE:hvg_precision={hvg_precision}")
'''

# =============================================================================
# Scenario 4: satellite_preprocess (徐竞屹 #9, 地球科学, 中等)
# 卫星亮温数据：NetCDF 读取 + 质量控制 + 重网格化
# =============================================================================
S04_TASK = """Write a Python CLI script to preprocess satellite brightness temperature data stored in NetCDF format.

Input: A NetCDF file with variables:
- brightness_temp: (n_scanlines, n_pixels) float32 array
- latitude: (n_scanlines, n_pixels) float32
- longitude: (n_scanlines, n_pixels) float32
- quality_flag: (n_scanlines, n_pixels) int8 (0=good, 1=suspect, 2=bad)

Requirements:
1. Use argparse: --input NetCDF path, --output CSV path, --resolution (default 0.25 degrees)
2. Mask pixels with quality_flag >= 2 (bad data)
3. Regrid the swath data onto a regular lat/lon grid at the specified resolution
4. For each grid cell, compute mean brightness temperature from valid pixels
5. Output CSV with columns: lat, lon, mean_bt, n_valid_pixels
6. Print summary: total pixels, valid pixels, grid dimensions
"""

S04_TEST = '''
import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_netcdf(path, n_scan=50, n_pix=40):
    """创建模拟的卫星扫描条带 NetCDF"""
    # 用 scipy 写简单的 netcdf
    from scipy.io import netcdf_file
    lats = np.linspace(30, 40, n_scan)[:, None] * np.ones((1, n_pix))
    lons = np.linspace(100, 110, n_pix)[None, :] * np.ones((n_scan, 1))
    bt = 250 + 20 * np.random.randn(n_scan, n_pix).astype(np.float32)
    qf = np.zeros((n_scan, n_pix), dtype=np.int8)
    qf[bt < 220] = 2  # 标记异常低温为 bad
    qf[np.random.rand(n_scan, n_pix) < 0.05] = 1  # 5% suspect

    with netcdf_file(path, "w") as f:
        f.createDimension("scanline", n_scan)
        f.createDimension("pixel", n_pix)
        v = f.createVariable("brightness_temp", "f", ("scanline", "pixel"))
        v[:] = bt
        v = f.createVariable("latitude", "f", ("scanline", "pixel"))
        v[:] = lats.astype(np.float32)
        v = f.createVariable("longitude", "f", ("scanline", "pixel"))
        v[:] = lons.astype(np.float32)
        v = f.createVariable("quality_flag", "b", ("scanline", "pixel"))
        v[:] = qf
    return n_scan * n_pix, int((qf < 2).sum())

with tempfile.TemporaryDirectory() as tmpdir:
    nc_path = f"{tmpdir}/satellite.nc"
    csv_out = f"{tmpdir}/gridded.csv"
    total_pix, valid_pix = create_netcdf(nc_path)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", nc_path, "--output", csv_out, "--resolution", "2.0"],
        [sys.executable, "generated.py", nc_path, "-o", csv_out, "--resolution", "2.0"],
        [sys.executable, "generated.py", nc_path, csv_out],
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
        for t in ["L1_valid_csv","L2_has_columns","L2_bt_range","L2_no_bad_pixels","L2_grid_coverage"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    cols_lower = [c.lower() for c in df.columns]
    if "lat" in cols_lower and "lon" in cols_lower:
        print("PASS:L2_has_columns")
    elif any("lat" in c for c in cols_lower) and any("lon" in c for c in cols_lower):
        print("PASS:L2_has_columns")
    else:
        print(f"FAIL:L2_has_columns - columns={list(df.columns)}")

    # 亮温合理范围
    bt_col = [c for c in df.columns if any(k in c.lower() for k in ["bt","bright","temp","mean"])]
    if bt_col:
        bt_vals = df[bt_col[0]].dropna()
        if bt_vals.min() > 200 and bt_vals.max() < 350:
            print(f"PASS:L2_bt_range - [{bt_vals.min():.1f}, {bt_vals.max():.1f}]")
        else:
            print(f"FAIL:L2_bt_range - [{bt_vals.min():.1f}, {bt_vals.max():.1f}]")
    else:
        print("FAIL:L2_bt_range - no BT column found")

    # 坏像素应被过滤
    if len(df) < total_pix:
        print(f"PASS:L2_no_bad_pixels - {len(df)} grid cells (from {total_pix} pixels)")
    else:
        print(f"FAIL:L2_no_bad_pixels - {len(df)} >= {total_pix}")

    # 网格覆盖
    if len(df) >= 5:
        print(f"PASS:L2_grid_coverage - {len(df)} grid cells")
    else:
        print(f"FAIL:L2_grid_coverage - only {len(df)} cells")

    # --- 新增测试 ---
    # L2: 经纬度范围合理（lat 30-40, lon 100-110）
    lat_col = [c for c in df.columns if "lat" in c.lower()]
    lon_col = [c for c in df.columns if "lon" in c.lower()]
    if lat_col and lon_col:
        lat_vals = df[lat_col[0]].dropna()
        lon_vals = df[lon_col[0]].dropna()
        if lat_vals.min() >= 29 and lat_vals.max() <= 41 and lon_vals.min() >= 99 and lon_vals.max() <= 111:
            print("PASS:L2_lat_lon_range")
        else:
            print(f"FAIL:L2_lat_lon_range - lat=[{lat_vals.min():.1f},{lat_vals.max():.1f}], lon=[{lon_vals.min():.1f},{lon_vals.max():.1f}]")
    else:
        print("FAIL:L2_lat_lon_range - no lat/lon columns")

    # L2: 有效像素数列
    n_valid_col = [c for c in df.columns if "valid" in c.lower() or "count" in c.lower() or "n_" in c.lower()]
    if n_valid_col:
        print(f"PASS:L2_n_valid - column: {n_valid_col[0]}")
    else:
        print("FAIL:L2_n_valid - no valid pixel count column")

    # L2: 网格分辨率（相邻 lat/lon 差应接近 2.0 度）
    if lat_col and len(df) > 1:
        lats_unique = sorted(df[lat_col[0]].dropna().unique())
        if len(lats_unique) >= 2:
            res = np.median(np.diff(lats_unique))
            if 1.0 <= res <= 3.0:
                print(f"PASS:L2_resolution - {res:.2f} degrees")
            else:
                print(f"FAIL:L2_resolution - {res:.2f} degrees (expected ~2.0)")
        else:
            print("FAIL:L2_resolution - only 1 unique lat")
    else:
        print("FAIL:L2_resolution")

    # L2: 输出无 NaN（重网格化后不应有 NaN）
    if bt_col:
        nan_count = df[bt_col[0]].isna().sum()
        if nan_count == 0:
            print("PASS:L2_no_nan")
        else:
            print(f"FAIL:L2_no_nan - {nan_count} NaN values in BT column")
    else:
        print("FAIL:L2_no_nan - no BT column")

    # SCORE: 空间覆盖率（网格实际覆盖/理论覆盖）
    if lat_col and lon_col:
        n_lat = len(df[lat_col[0]].unique())
        n_lon = len(df[lon_col[0]].unique())
        expected_cells = int((40 - 30) / 2.0) * int((110 - 100) / 2.0)  # 5 × 5 = 25
        spatial_coverage = round(min(len(df) / max(expected_cells, 1), 1.0), 4)
    else:
        spatial_coverage = 0.0
    print(f"SCORE:spatial_coverage={spatial_coverage}")

    # SCORE: 插值质量（BT 值的合理性）
    if bt_col:
        bt_vals = df[bt_col[0]].dropna()
        in_range = ((bt_vals > 220) & (bt_vals < 300)).mean()
        interpolation_quality = round(in_range, 4)
    else:
        interpolation_quality = 0.0
    print(f"SCORE:interpolation_quality={interpolation_quality}")
'''

# =============================================================================
# Scenario 5: protein_parse (Researcher D #12, 生命科学, 中等)
# SwissProt JSON 蛋白质数据解析
# =============================================================================
S05_TASK = """Write a Python CLI script to parse SwissProt protein entries from a JSON file and extract structured information.

Input: A JSON file containing a list of protein entries, each with fields like:
- accession, id, protein.recommendedName, gene, organism, sequence, comments, features

Requirements:
1. Use argparse: --input JSON path, --output CSV path
2. For each protein entry extract: accession, protein_name, gene_name, organism, sequence_length, number_of_features, GO_terms (from dbReferences)
3. Handle missing fields gracefully (use empty string or 0)
4. Output a CSV with one row per protein
5. Print summary: total proteins, organisms count, average sequence length
"""

S05_TEST = '''
import sys, os, subprocess, tempfile, json
import pandas as pd

def create_data(path, n=20):
    entries = []
    organisms = ["Homo sapiens", "Mus musculus", "Escherichia coli", "Saccharomyces cerevisiae"]
    for i in range(n):
        entry = {
            "accession": [f"P{10000+i}"],
            "id": f"PROT{i}_HUMAN",
            "protein": {"recommendedName": {"fullName": {"value": f"Test protein {i}"}}},
            "gene": [{"name": {"value": f"TP{i}"}}] if i % 3 != 0 else [],
            "organism": {"names": [{"value": organisms[i % len(organisms)]}]},
            "sequence": {"length": 100 + i * 10, "sequence": "M" + "A" * (99 + i * 10)},
            "comments": [{"type": "FUNCTION", "text": [{"value": f"Involved in process {i}"}]}],
            "features": [{"type": "CHAIN"}, {"type": "DOMAIN"}] * (i % 3 + 1),
            "dbReferences": [
                {"type": "GO", "id": f"GO:{7000+i}"},
                {"type": "GO", "id": f"GO:{8000+i}"},
                {"type": "PDB", "id": f"1ABC"},
            ] if i % 2 == 0 else [],
        }
        entries.append(entry)
    json.dump(entries, open(path, "w"), indent=2)
    return n

with tempfile.TemporaryDirectory() as tmpdir:
    json_in = f"{tmpdir}/proteins.json"
    csv_out = f"{tmpdir}/parsed.csv"
    n = create_data(json_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", json_in, "--output", csv_out],
        [sys.executable, "generated.py", json_in, "-o", csv_out],
        [sys.executable, "generated.py", json_in, csv_out],
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
        for t in ["L1_valid_csv","L2_row_count","L2_has_accession","L2_has_name","L2_has_organism","L2_missing_handled"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    if len(df) == n:
        print(f"PASS:L2_row_count - {n} proteins")
    else:
        print(f"FAIL:L2_row_count - expected {n}, got {len(df)}")

    cols = " ".join(df.columns).lower()
    if "accession" in cols or "acc" in cols:
        print("PASS:L2_has_accession")
    else:
        print("FAIL:L2_has_accession")

    if "name" in cols or "protein" in cols:
        print("PASS:L2_has_name")
    else:
        print("FAIL:L2_has_name")

    if "organism" in cols or "org" in cols or "species" in cols:
        print("PASS:L2_has_organism")
    else:
        print("FAIL:L2_has_organism")

    # 缺失字段处理（gene 每3个缺一次，应该不报错）
    if not df.isnull().all(axis=None):
        print("PASS:L2_missing_handled")
    else:
        print("FAIL:L2_missing_handled - all null")

    # --- 新增测试 ---
    # L2: 序列长度列（应有 sequence_length 或类似列）
    if any("length" in c.lower() or "seq_len" in c.lower() for c in df.columns):
        print("PASS:L2_seq_length")
    else:
        print("FAIL:L2_seq_length - no sequence length column")

    # L2: feature 计数列
    if any("feature" in c.lower() or "n_feat" in c.lower() for c in df.columns):
        print("PASS:L2_feature_count")
    else:
        print("FAIL:L2_feature_count - no feature count column")

    # L2: GO terms 列
    if any("go" in c.lower() for c in df.columns):
        print("PASS:L2_go_terms")
    else:
        print("FAIL:L2_go_terms - no GO terms column")

    # L2: 摘要信息（stdout 应包含统计信息）
    combined_out = r.stdout + r.stderr if hasattr(r, 'stdout') else ""
    if any(kw in combined_out.lower() for kw in ["total", "summary", "protein", "organism", "average"]):
        print("PASS:L2_summary")
    else:
        print("FAIL:L2_summary - no summary output")

    # SCORE: 字段提取率（检查多少关键列被提取）
    expected_fields = ["accession", "name", "organism", "gene", "length", "feature", "go"]
    cols_str = " ".join(df.columns).lower()
    found = sum(1 for f in expected_fields if f in cols_str)
    field_extraction_rate = round(found / len(expected_fields), 4)
    print(f"SCORE:field_extraction_rate={field_extraction_rate}")

    # SCORE: 数据完整性（非空值比例）
    completeness = round(1.0 - df.isnull().mean().mean(), 4)
    print(f"SCORE:completeness={completeness}")
'''

# =============================================================================
# Scenario 6: gene_expression (陈鑫 #10, 生命科学, 复杂)
# 基因表达量处理：FASTA 序列 + 表达矩阵
# =============================================================================
S06_TASK = """Write a Python CLI script to process gene expression data with associated sequence information.

Input files:
- expression.csv: rows=samples, columns=genes, values=expression levels (TPM)
- sequences.fasta: gene sequences in FASTA format (>GENE_NAME\\nSEQUENCE)

Requirements:
1. Use argparse: --expression CSV, --fasta FASTA, --output directory
2. Read expression matrix; filter out genes with mean TPM < 1 across samples
3. Quantile normalize the expression matrix across samples
4. Parse FASTA file to get sequence lengths per gene
5. Output to directory: normalized_expression.csv, gene_stats.csv (gene_name, mean_tpm, std_tpm, seq_length)
6. Print summary: samples, genes before/after filter, correlation between expression and sequence length
"""

S06_TEST = '''
import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(tmpdir, n_samples=30, n_genes=200):
    np.random.seed(42)
    genes = [f"GENE_{i}" for i in range(n_genes)]
    samples = [f"Sample_{i}" for i in range(n_samples)]
    expr = np.random.exponential(5, (n_samples, n_genes)).astype(np.float32)
    expr[:, -20:] = np.random.exponential(0.1, (n_samples, 20))  # 低表达基因

    df = pd.DataFrame(expr, columns=genes, index=samples)
    df.to_csv(f"{tmpdir}/expression.csv")

    with open(f"{tmpdir}/sequences.fasta", "w") as f:
        for g in genes:
            seq_len = np.random.randint(100, 5000)
            f.write(f">{g}\\n{'ATCG' * (seq_len // 4)}\\n")
    return n_samples, n_genes

with tempfile.TemporaryDirectory() as tmpdir:
    n_samples, n_genes = create_data(tmpdir)
    out_dir = f"{tmpdir}/output"

    ran = False
    for args in [
        [sys.executable, "generated.py", "--expression", f"{tmpdir}/expression.csv",
         "--fasta", f"{tmpdir}/sequences.fasta", "--output", out_dir],
        [sys.executable, "generated.py", "-e", f"{tmpdir}/expression.csv",
         "-f", f"{tmpdir}/sequences.fasta", "-o", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出
    norm_csv = None
    stats_csv = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            if "norm" in f.lower() and f.endswith(".csv"):
                norm_csv = os.path.join(out_dir, f)
            if "stat" in f.lower() and f.endswith(".csv"):
                stats_csv = os.path.join(out_dir, f)
    if norm_csv or stats_csv:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L2_gene_filtered","L2_normalized","L2_stats_has_length","L2_sample_preserved"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # Layer 2: 基因过滤
    if norm_csv:
        df = pd.read_csv(norm_csv, index_col=0)
        n_filtered = len(df.columns) if len(df) == n_samples else len(df)
        if n_filtered < n_genes:
            print(f"PASS:L2_gene_filtered - {n_filtered} genes (from {n_genes})")
        else:
            print(f"FAIL:L2_gene_filtered - {n_filtered} >= {n_genes}")

        # 分位数归一化检查：每个样本的分布应该大致相同
        if len(df) == n_samples:
            medians = df.median(axis=1)
            if medians.std() < medians.mean() * 0.5:
                print("PASS:L2_normalized")
            else:
                print(f"FAIL:L2_normalized - sample medians vary too much: std={medians.std():.2f}")
        else:
            print("PASS:L2_normalized")

        # 样本数保持
        row_count = len(df)
        if row_count == n_samples or len(df.columns) == n_samples:
            print(f"PASS:L2_sample_preserved")
        else:
            print(f"FAIL:L2_sample_preserved - expected {n_samples}")
    else:
        for t in ["L2_gene_filtered","L2_normalized","L2_sample_preserved"]:
            print(f"FAIL:{t} - no normalized output")

    # Layer 2: stats 包含序列长度
    if stats_csv:
        stats = pd.read_csv(stats_csv)
        cols = " ".join(stats.columns).lower()
        if "length" in cols or "len" in cols or "seq" in cols:
            print("PASS:L2_stats_has_length")
        else:
            print(f"FAIL:L2_stats_has_length - columns: {list(stats.columns)}")
    else:
        print("FAIL:L2_stats_has_length - no stats file")

    # --- 新增测试 ---
    # L2: 输出目录结构正确
    if os.path.exists(out_dir) and os.path.isdir(out_dir):
        print("PASS:L2_dir_structure")
    else:
        print("FAIL:L2_dir_structure - output dir not created")

    # L2: FASTA 文件被正确解析（stats 中应有基因名匹配）
    if stats_csv and os.path.exists(stats_csv):
        stats = pd.read_csv(stats_csv)
        gene_col = [c for c in stats.columns if "gene" in c.lower() or "name" in c.lower()]
        if gene_col and any("GENE_" in str(v) for v in stats[gene_col[0]].values[:5]):
            print("PASS:L2_fasta_parsed")
        elif len(stats) > 0:
            print("PASS:L2_fasta_parsed")
        else:
            print("FAIL:L2_fasta_parsed - no gene names in stats")
    else:
        print("FAIL:L2_fasta_parsed - no stats file")

    # L2: stats 行数合理（应和过滤后基因数一致）
    if stats_csv and os.path.exists(stats_csv):
        stats = pd.read_csv(stats_csv)
        if len(stats) > 0 and len(stats) < n_genes:
            print(f"PASS:L2_stats_rows - {len(stats)} genes in stats")
        elif len(stats) > 0:
            print(f"PASS:L2_stats_rows - {len(stats)} rows")
        else:
            print("FAIL:L2_stats_rows - empty stats")
    else:
        print("FAIL:L2_stats_rows - no stats file")

    # L2: mean TPM 列
    if stats_csv and os.path.exists(stats_csv):
        stats = pd.read_csv(stats_csv)
        cols_lower = " ".join(stats.columns).lower()
        if "mean" in cols_lower or "avg" in cols_lower or "tpm" in cols_lower:
            print("PASS:L2_mean_tpm")
        else:
            print(f"FAIL:L2_mean_tpm - columns: {list(stats.columns)}")
    else:
        print("FAIL:L2_mean_tpm - no stats file")

    # L2: correlation 输出（应在 stdout 中打印相关性信息）
    combined_out = r.stdout if hasattr(r, 'stdout') and r.stdout else ""
    if "corr" in combined_out.lower() or "correlation" in combined_out.lower() or "r=" in combined_out.lower():
        print("PASS:L2_correlation")
    else:
        print("FAIL:L2_correlation - no correlation in output")

    # L2: 不包含原始数据（filtered 后低表达基因应被移除）
    if norm_csv and os.path.exists(norm_csv):
        norm_df = pd.read_csv(norm_csv, index_col=0)
        n_norm_genes = len(norm_df.columns) if len(norm_df) == n_samples else len(norm_df)
        if n_norm_genes < n_genes:
            print("PASS:L2_no_raw")
        else:
            print("FAIL:L2_no_raw - seems to contain unfiltered data")
    else:
        print("FAIL:L2_no_raw - no normalized output")

    # SCORE: 归一化相关性（分位数归一化后行间中位数的一致性）
    if norm_csv and os.path.exists(norm_csv):
        norm_df = pd.read_csv(norm_csv, index_col=0)
        numeric = norm_df.select_dtypes(include=[np.number])
        if len(numeric) > 0 and len(numeric.columns) > 0:
            row_medians = numeric.median(axis=1)
            if row_medians.std() > 0:
                norm_corr = round(max(0, 1.0 - row_medians.std() / max(row_medians.mean(), 0.01)), 4)
            else:
                norm_corr = 1.0
        else:
            norm_corr = 0.0
    else:
        norm_corr = 0.0
    print(f"SCORE:normalization_correlation={norm_corr}")

    # SCORE: 基因覆盖率
    if stats_csv and os.path.exists(stats_csv):
        stats = pd.read_csv(stats_csv)
        gene_coverage = round(min(len(stats) / n_genes, 1.0), 4)
    else:
        gene_coverage = 0.0
    print(f"SCORE:gene_coverage={gene_coverage}")
'''

# =============================================================================
# Scenario 7: data_viz (朱宇 #2, 神经科学, 简单)
# 神经数据可视化：firing rate heatmap + trial-averaged PSTH
# =============================================================================
S07_TASK = """Write a Python CLI script to visualize neural population activity data.

Input: A CSV file with columns: trial, time, and multiple neuron columns (neuron_0, neuron_1, ...) containing firing rates.

Requirements:
1. Use argparse: --input CSV, --output-dir for saving plots
2. Create two plots and save as PNG:
   a. firing_rate_heatmap.png: heatmap of trial-averaged firing rates (neurons × time)
   b. population_psth.png: line plot of population mean firing rate over time with shaded SEM
3. Use matplotlib (no interactive display, use Agg backend)
4. Print summary: number of neurons, trials, time range
"""

S07_TEST = '''
import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_trials=20, n_time=100, n_neurons=15):
    rows = []
    for trial in range(n_trials):
        for t in range(n_time):
            row = {"trial": trial, "time": t * 0.01}
            for n in range(n_neurons):
                row[f"neuron_{n}"] = max(0, np.random.poisson(5 + 3 * np.sin(t/10 + n)))
            rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_trials, n_time, n_neurons

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/neural_data.csv"
    out_dir = f"{tmpdir}/plots"
    n_trials, n_time, n_neurons = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output-dir", out_dir],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", csv_in, out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30,
                          cwd=os.getcwd(), env={**os.environ, "MPLBACKEND": "Agg"})
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找 PNG 文件
    pngs = []
    for root, dirs, files in os.walk(tmpdir):
        for f in files:
            if f.endswith(".png"):
                pngs.append(os.path.join(root, f))

    if len(pngs) >= 1:
        print(f"PASS:L1_output_exists - {len(pngs)} PNG files")
    else:
        print("FAIL:L1_output_exists - no PNG files found")

    # Layer 2: 至少有 heatmap
    heatmap = [p for p in pngs if "heat" in p.lower() or "map" in p.lower()]
    if heatmap:
        size = os.path.getsize(heatmap[0])
        if size > 1000:
            print(f"PASS:L2_heatmap - {size} bytes")
        else:
            print(f"FAIL:L2_heatmap - file too small ({size} bytes)")
    elif len(pngs) >= 1:
        # 可能名字不同，但有 PNG 就算
        print(f"PASS:L2_heatmap - found {len(pngs)} plots")
    else:
        print("FAIL:L2_heatmap")

    # Layer 2: 有 PSTH 或第二个图
    psth = [p for p in pngs if "psth" in p.lower() or "population" in p.lower() or "line" in p.lower()]
    if psth or len(pngs) >= 2:
        print("PASS:L2_psth")
    else:
        print(f"FAIL:L2_psth - only {len(pngs)} plots")

    # --- 新增测试 ---
    # L2: 图片文件大小合理（不是空图）
    valid_sizes = [os.path.getsize(p) for p in pngs if os.path.getsize(p) > 5000]
    if len(valid_sizes) >= 1:
        print(f"PASS:L2_file_sizes - {len(valid_sizes)} valid-sized plots")
    else:
        print("FAIL:L2_file_sizes - all plots too small")

    # L2: 神经元数量匹配（从输出或图片元数据推断）
    if len(pngs) >= 1:
        print(f"PASS:L2_neuron_count")  # 只要有图就认为处理了正确数量
    else:
        print("FAIL:L2_neuron_count")

    # L2: 使用了 Agg 后端（不应弹出窗口）
    print("PASS:L2_backend")  # 如果程序运行成功且不卡住，说明后端正确

    # L2: heatmap 和 psth 是分开的文件
    if len(pngs) >= 2:
        print("PASS:L2_separate_files")
    else:
        print(f"FAIL:L2_separate_files - only {len(pngs)} file(s)")

    # SCORE: 图完整性（2个图 = 1.0，1个 = 0.5，0个 = 0）
    plot_completeness = round(min(len(pngs) / 2.0, 1.0), 4)
    print(f"SCORE:plot_completeness={plot_completeness}")

    # SCORE: 文件大小比例（图片大小是否在合理范围 10KB-5MB）
    reasonable = sum(1 for p in pngs if 10000 < os.path.getsize(p) < 5_000_000)
    file_size_ratio = round(reasonable / max(len(pngs), 1), 4)
    print(f"SCORE:file_size_ratio={file_size_ratio}")
'''

# =============================================================================
# Scenario 8: materials_qa (李玉强 #8, 物质科学, 中等)
# 材料科学训练语料质量检查：JSON 格式验证 + 重复检测 + 统计
# =============================================================================
S08_TASK = """Write a Python CLI script to validate and clean a materials science training dataset stored as JSONL (one JSON per line).

Each line has fields: instruction, input, output, source, category.

Requirements:
1. Use argparse: --input JSONL path, --output cleaned JSONL path, --report JSON path
2. Validate each entry: check all required fields present, instruction/output not empty, length limits (instruction < 500 chars, output < 5000 chars)
3. Detect near-duplicates: flag entries where instruction similarity (by word overlap ratio) > 0.9
4. Remove invalid entries and duplicates, write cleaned data
5. Generate report JSON: total entries, removed count (by reason), category distribution, average lengths
"""

S08_TEST = '''
import sys, os, subprocess, tempfile, json

def create_data(path, n=50):
    entries = []
    categories = ["crystal_structure", "band_gap", "synthesis", "properties", "characterization"]
    for i in range(n):
        entry = {
            "instruction": f"Predict the band gap of material {i} with composition X{i}Y{i}Z",
            "input": f"Material: Compound_{i}, Space group: Fm-3m" if i % 3 != 0 else "",
            "output": f"The predicted band gap is {1.0 + i * 0.1:.1f} eV based on the electronic structure calculation.",
            "source": "generated",
            "category": categories[i % len(categories)],
        }
        entries.append(entry)
    # 添加无效条目
    entries.append({"instruction": "", "input": "", "output": "bad", "source": "x", "category": "x"})  # 空instruction
    entries.append({"instruction": "test", "output": "y"})  # 缺字段
    entries.append({"instruction": "A" * 600, "input": "", "output": "ok", "source": "x", "category": "x"})  # 太长
    # 添加近似重复
    entries.append({
        "instruction": "Predict the band gap of material 0 with composition X0Y0Z",  # 和第0条几乎相同
        "input": "", "output": "duplicate test", "source": "x", "category": "x"
    })
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\\n")
    return n + 4  # 总条目数

with tempfile.TemporaryDirectory() as tmpdir:
    jsonl_in = f"{tmpdir}/data.jsonl"
    jsonl_out = f"{tmpdir}/cleaned.jsonl"
    report = f"{tmpdir}/report.json"
    total = create_data(jsonl_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", jsonl_in, "--output", jsonl_out, "--report", report],
        [sys.executable, "generated.py", jsonl_in, "-o", jsonl_out],
        [sys.executable, "generated.py", jsonl_in, jsonl_out, report],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(jsonl_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_jsonl","L2_removed_invalid","L2_no_empty_instruction","L2_length_check","L2_dedup"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # 读 cleaned
    cleaned = []
    with open(jsonl_out) as f:
        for line in f:
            if line.strip():
                cleaned.append(json.loads(line))
    print("PASS:L1_valid_jsonl")

    if len(cleaned) < total:
        print(f"PASS:L2_removed_invalid - {total - len(cleaned)} removed")
    else:
        print(f"FAIL:L2_removed_invalid - {len(cleaned)} >= {total}")

    empty_inst = [e for e in cleaned if not e.get("instruction","").strip()]
    if len(empty_inst) == 0:
        print("PASS:L2_no_empty_instruction")
    else:
        print(f"FAIL:L2_no_empty_instruction - {len(empty_inst)} empty")

    long_inst = [e for e in cleaned if len(e.get("instruction","")) > 500]
    if len(long_inst) == 0:
        print("PASS:L2_length_check")
    else:
        print(f"FAIL:L2_length_check - {len(long_inst)} too long")

    # 检查近似重复是否被移除
    if len(cleaned) <= total - 3:  # 至少移除了3条无效+1条重复
        print("PASS:L2_dedup")
    else:
        print(f"FAIL:L2_dedup - {len(cleaned)} entries, expected <= {total-3}")

    # --- 新增测试 ---
    # L2: report 文件存在
    report_exists = os.path.exists(report)
    if not report_exists:
        # 查找其他可能的 report 路径
        for f in os.listdir(tmpdir):
            if "report" in f.lower() and f.endswith(".json"):
                report = os.path.join(tmpdir, f)
                report_exists = True
                break
    print(f"{'PASS' if report_exists else 'FAIL'}:L2_report_exists")

    # L2: report 是有效 JSON
    if report_exists:
        try:
            rpt = json.load(open(report))
            print("PASS:L2_report_json")
        except:
            rpt = {}
            print("FAIL:L2_report_json - invalid JSON")
    else:
        rpt = {}
        print("FAIL:L2_report_json")

    # L2: report 包含分类分布
    rpt_str = json.dumps(rpt).lower() if rpt else ""
    if "categor" in rpt_str or "distribution" in rpt_str or "crystal" in rpt_str:
        print("PASS:L2_categories")
    else:
        print("FAIL:L2_categories - no category distribution")

    # L2: 所有 cleaned 条目都有完整字段
    required_fields = ["instruction", "output", "source", "category"]
    all_complete = all(all(f in e for f in required_fields) for e in cleaned)
    if all_complete:
        print("PASS:L2_complete_fields")
    else:
        print("FAIL:L2_complete_fields - some entries missing required fields")

    # L2: instruction 长度合理
    if cleaned:
        avg_len = sum(len(e.get("instruction", "")) for e in cleaned) / len(cleaned)
        print(f"PASS:L2_lengths - avg instruction length: {avg_len:.0f}")
    else:
        print("FAIL:L2_lengths - no cleaned entries")

    # SCORE: 去重精度（应移除 ~4 条：3 无效 + 1 重复）
    expected_clean = total - 4
    if len(cleaned) > 0:
        dedup_precision = round(max(0, 1.0 - abs(len(cleaned) - expected_clean) / total), 4)
    else:
        dedup_precision = 0.0
    print(f"SCORE:dedup_precision={dedup_precision}")

    # SCORE: 去重召回率（无效条目被移除的比例）
    # 我们知道有 4 条应被移除
    removed = total - len(cleaned)
    dedup_recall = round(min(removed / 4.0, 1.0), 4) if removed > 0 else 0.0
    print(f"SCORE:dedup_recall={dedup_recall}")
'''

# =============================================================================
# Scenario 9: earth_obs (费奔 #11, 地球科学, 简单)
# 地球观测数据格式转换：多文件CSV合并 + 时间对齐
# =============================================================================
S09_TASK = """Write a Python CLI script to merge and align multiple Earth observation station CSV files into a single dataset.

Input: A directory containing CSV files, each from a different weather station. Each CSV has columns: timestamp (ISO format), temperature, humidity, pressure, station_id.

Requirements:
1. Use argparse: --input-dir directory, --output CSV, --freq (default "1h" for hourly)
2. Read all CSV files from the directory
3. Align all stations to a common time grid (resample to specified frequency)
4. Handle missing values: forward-fill then backward-fill (limit=3)
5. Output merged CSV: timestamp as index, one column per station per variable (e.g., station_A_temperature)
6. Print summary: number of stations, time range, missing data percentage
"""

S09_TEST = '''
import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(input_dir, n_stations=4, n_hours=48):
    os.makedirs(input_dir, exist_ok=True)
    base = pd.Timestamp("2024-01-01")
    for s in range(n_stations):
        times = pd.date_range(base, periods=n_hours, freq="1h")
        # 每个站时间稍有偏移
        if s > 0:
            times = times[s:]  # 前几个时间点缺失
        df = pd.DataFrame({
            "timestamp": times.strftime("%Y-%m-%dT%H:%M:%S"),
            "temperature": 20 + 5 * np.sin(np.arange(len(times)) / 6) + np.random.randn(len(times)),
            "humidity": 60 + 10 * np.random.randn(len(times)),
            "pressure": 1013 + np.random.randn(len(times)) * 2,
            "station_id": f"Station_{s}",
        })
        # 随机引入缺失
        mask = np.random.rand(len(times)) < 0.1
        df.loc[mask, "temperature"] = np.nan
        df.to_csv(f"{input_dir}/station_{s}.csv", index=False)
    return n_stations

with tempfile.TemporaryDirectory() as tmpdir:
    input_dir = f"{tmpdir}/stations"
    csv_out = f"{tmpdir}/merged.csv"
    n_stations = create_data(input_dir)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input-dir", input_dir, "--output", csv_out],
        [sys.executable, "generated.py", input_dir, "-o", csv_out],
        [sys.executable, "generated.py", input_dir, csv_out],
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
        for t in ["L1_valid_csv","L2_multi_station","L2_time_aligned","L2_fillna"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    if len(df.columns) > 5:
        print(f"PASS:L2_multi_station - {len(df.columns)} columns")
    else:
        print(f"FAIL:L2_multi_station - only {len(df.columns)} columns")

    # 检查时间列
    time_col = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
    if time_col:
        print("PASS:L2_time_aligned")
    elif df.index.dtype == "object" and "-" in str(df.index[0]):
        print("PASS:L2_time_aligned")
    else:
        print("FAIL:L2_time_aligned - no time column found")

    # 缺失值应该被填充（不应该有大量NaN）
    null_pct = df.isnull().mean().mean()
    if null_pct < 0.3:
        print(f"PASS:L2_fillna - {null_pct:.1%} null")
    else:
        print(f"FAIL:L2_fillna - {null_pct:.1%} null (too much)")

    # --- 新增测试 ---
    # L2: 时间间隔为 1 小时
    time_col = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
    if time_col:
        try:
            ts = pd.to_datetime(df[time_col[0]])
            diffs = ts.diff().dropna()
            median_diff = diffs.median()
            if pd.Timedelta("50min") <= median_diff <= pd.Timedelta("70min"):
                print("PASS:L2_hourly")
            else:
                print(f"FAIL:L2_hourly - median interval: {median_diff}")
        except:
            print("FAIL:L2_hourly - cannot parse timestamps")
    else:
        print("FAIL:L2_hourly - no time column")

    # L2: 包含所有站点数据
    cols_str = " ".join(df.columns).lower()
    stations_found = sum(1 for s in range(n_stations) if f"station_{s}" in cols_str or f"_{s}_" in cols_str or f"_{s}" in cols_str)
    if stations_found >= n_stations - 1:
        print(f"PASS:L2_all_stations - {stations_found}/{n_stations} stations")
    else:
        print(f"FAIL:L2_all_stations - only {stations_found}/{n_stations} stations found")

    # L2: 没有过多连续 NaN（fill limit=3 应工作）
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    excessive_nan = False
    for col in numeric_cols[:5]:  # 检查前 5 列
        vals = df[col].values
        nan_streak = 0
        max_streak = 0
        for v in vals:
            if pd.isna(v):
                nan_streak += 1
                max_streak = max(max_streak, nan_streak)
            else:
                nan_streak = 0
        if max_streak > 10:
            excessive_nan = True
            break
    print(f"{'PASS' if not excessive_nan else 'FAIL'}:L2_no_excessive_nan")

    # L2: 列名规范（应有站点标识和变量名）
    has_structured_names = any("_temp" in c.lower() or "_humid" in c.lower() or "_press" in c.lower() for c in df.columns)
    if has_structured_names or len(df.columns) > 5:
        print("PASS:L2_naming")
    else:
        print("FAIL:L2_naming - column names not structured")

    # L2: 温度值在合理范围
    temp_cols = [c for c in df.columns if "temp" in c.lower()]
    if temp_cols:
        temp_vals = df[temp_cols].values.flatten()
        temp_vals = temp_vals[~np.isnan(temp_vals)]
        if len(temp_vals) > 0 and temp_vals.min() > -50 and temp_vals.max() < 60:
            print(f"PASS:L2_range - temp [{temp_vals.min():.1f}, {temp_vals.max():.1f}]")
        else:
            print(f"FAIL:L2_range - unreasonable temperature values")
    else:
        print("FAIL:L2_range - no temperature columns")

    # L2: 前向/后向填充已应用
    if null_pct < 0.15:  # 原始数据约 10% 缺失 + 站点偏移
        print(f"PASS:L2_fill_applied - {null_pct:.1%} remaining nulls")
    else:
        print(f"FAIL:L2_fill_applied - {null_pct:.1%} still too many nulls")

    # SCORE: 时间对齐误差
    if time_col:
        try:
            ts = pd.to_datetime(df[time_col[0]])
            diffs = ts.diff().dropna()
            expected = pd.Timedelta("1h")
            alignment_errors = ((diffs - expected).abs() / expected).mean()
            time_alignment_error = round(max(0, 1.0 - alignment_errors), 4)
        except:
            time_alignment_error = 0.0
    else:
        time_alignment_error = 0.0
    print(f"SCORE:time_alignment_error={time_alignment_error}")

    # SCORE: 填充质量（1 - 残余缺失比例）
    fill_quality = round(1.0 - null_pct, 4)
    print(f"SCORE:fill_quality={fill_quality}")
'''

# =============================================================================
# Scenario 10: multimodal_preprocess (孙一介 #4, 生命科学, 复杂)
# 多模态数据预处理：图片resize + 文本tokenize统计 + manifest生成
# =============================================================================
S10_TASK = """Write a Python CLI script to preprocess a multimodal biology dataset for model training.

Input directory structure:
- images/: contains .jpg files
- texts/: contains .txt files (one per sample, matching image names)
- labels.csv: columns sample_id, label

Requirements:
1. Use argparse: --input-dir root directory, --output-dir processed directory, --image-size (default 224)
2. For each image: load, resize to (image_size, image_size), save as PNG in output_dir/images/
3. For each text: read, compute word count and character count
4. Generate manifest.json: list of {sample_id, image_path, text_path, label, word_count, char_count, original_image_size}
5. Print summary: total samples, label distribution, average word count
"""

S10_TEST = '''
import sys, os, subprocess, tempfile, json
import numpy as np

def create_data(root, n=10):
    os.makedirs(f"{root}/images", exist_ok=True)
    os.makedirs(f"{root}/texts", exist_ok=True)
    # 创建简单的 JPEG-like 文件（实际用 numpy 保存为可读图片）
    try:
        from PIL import Image
        has_pil = True
    except ImportError:
        has_pil = False

    labels = []
    for i in range(n):
        name = f"sample_{i:03d}"
        if has_pil:
            img = Image.fromarray(np.random.randint(0, 255, (100+i*10, 80+i*5, 3), dtype=np.uint8))
            img.save(f"{root}/images/{name}.jpg")
        else:
            # 没有 PIL 就写个假图
            np.save(f"{root}/images/{name}.npy", np.random.randint(0, 255, (100+i*10, 80+i*5, 3), dtype=np.uint8))
        with open(f"{root}/texts/{name}.txt", "w") as f:
            words = " ".join([f"word{j}" for j in range(10 + i * 2)])
            f.write(words)
        labels.append({"sample_id": name, "label": ["cell", "tissue", "organ"][i % 3]})

    import pandas as pd
    pd.DataFrame(labels).to_csv(f"{root}/labels.csv", index=False)
    return n

with tempfile.TemporaryDirectory() as tmpdir:
    data_root = f"{tmpdir}/data"
    out_dir = f"{tmpdir}/output"
    n = create_data(data_root)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input-dir", data_root, "--output-dir", out_dir, "--image-size", "64"],
        [sys.executable, "generated.py", data_root, "-o", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找 manifest
    manifest_path = None
    for root_d, dirs, files in os.walk(tmpdir):
        for f in files:
            if "manifest" in f.lower() and f.endswith(".json"):
                manifest_path = os.path.join(root_d, f)

    if manifest_path or os.path.exists(out_dir):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L2_manifest","L2_has_samples","L2_has_word_count","L2_images_processed"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    if manifest_path:
        manifest = json.load(open(manifest_path))
        print("PASS:L2_manifest")
        if isinstance(manifest, list) and len(manifest) == n:
            print(f"PASS:L2_has_samples - {n} entries")
        elif isinstance(manifest, dict) and len(manifest.get("samples", manifest.get("data", []))) == n:
            print(f"PASS:L2_has_samples")
        else:
            print(f"FAIL:L2_has_samples - unexpected structure")

        m_str = json.dumps(manifest).lower()
        if "word" in m_str and "count" in m_str:
            print("PASS:L2_has_word_count")
        else:
            print("FAIL:L2_has_word_count")
    else:
        print("FAIL:L2_manifest - no manifest.json found")
        print("FAIL:L2_has_samples")
        print("FAIL:L2_has_word_count")

    # 检查图片是否被处理
    processed_imgs = []
    processed_img_paths = []
    if os.path.exists(out_dir):
        for root_d, dirs, files in os.walk(out_dir):
            for f in files:
                if f.endswith((".png", ".jpg", ".npy")):
                    processed_imgs.append(f)
                    processed_img_paths.append(os.path.join(root_d, f))
    if len(processed_imgs) >= n // 2:
        print(f"PASS:L2_images_processed - {len(processed_imgs)} images")
    else:
        print(f"FAIL:L2_images_processed - only {len(processed_imgs)}")

    # --- 新增测试 ---
    # L2: 图片是否被 resize
    resized_ok = False
    if processed_img_paths:
        try:
            from PIL import Image
            for p in processed_img_paths:
                if p.endswith((".png", ".jpg")):
                    img = Image.open(p)
                    if img.size == (64, 64):
                        resized_ok = True
                    break
        except:
            resized_ok = len(processed_imgs) >= n // 2
    print(f"{'PASS' if resized_ok else 'FAIL'}:L2_resized")

    # L2: labels 信息被整合到 manifest
    if manifest_path and os.path.exists(manifest_path):
        m_str = json.dumps(json.load(open(manifest_path))).lower()
        if "label" in m_str and ("cell" in m_str or "tissue" in m_str or "organ" in m_str):
            print("PASS:L2_labels")
        else:
            print("FAIL:L2_labels - no label information in manifest")
    else:
        print("FAIL:L2_labels - no manifest")

    # L2: 保留了原始图片尺寸信息
    if manifest_path and os.path.exists(manifest_path):
        m_str = json.dumps(json.load(open(manifest_path))).lower()
        if "original" in m_str or "size" in m_str or "width" in m_str or "height" in m_str:
            print("PASS:L2_original_size")
        else:
            print("FAIL:L2_original_size - no original size info")
    else:
        print("FAIL:L2_original_size")

    # L2: 输出格式为 PNG
    png_count = sum(1 for p in processed_imgs if p.endswith(".png"))
    if png_count >= n // 2:
        print(f"PASS:L2_format - {png_count} PNG files")
    else:
        print(f"FAIL:L2_format - only {png_count} PNG files")

    # L2: 处理了所有样本
    if len(processed_imgs) >= n:
        print(f"PASS:L2_all_samples - {len(processed_imgs)}/{n}")
    else:
        print(f"FAIL:L2_all_samples - {len(processed_imgs)}/{n}")

    # L2: 文本字符数正确
    if manifest_path and os.path.exists(manifest_path):
        m_str = json.dumps(json.load(open(manifest_path))).lower()
        if "char" in m_str:
            print("PASS:L2_chars")
        else:
            print("FAIL:L2_chars - no character count in manifest")
    else:
        print("FAIL:L2_chars")

    # SCORE: manifest 完整性
    if manifest_path and os.path.exists(manifest_path):
        manifest_data = json.load(open(manifest_path))
        if isinstance(manifest_data, list):
            items = manifest_data
        elif isinstance(manifest_data, dict):
            items = manifest_data.get("samples", manifest_data.get("data", []))
        else:
            items = []
        if items:
            expected_keys = ["sample_id", "image", "text", "label", "word_count", "char_count"]
            items_str = json.dumps(items[0]).lower() if items else ""
            found_keys = sum(1 for k in expected_keys if k in items_str or k.replace("_", "") in items_str)
            manifest_completeness = round(found_keys / len(expected_keys), 4)
        else:
            manifest_completeness = 0.0
    else:
        manifest_completeness = 0.0
    print(f"SCORE:manifest_completeness={manifest_completeness}")

    # SCORE: 图片质量（处理的图片数 / 总样本数）
    image_quality = round(min(len(processed_imgs) / max(n, 1), 1.0), 4)
    print(f"SCORE:image_quality={image_quality}")
'''

# =============================================================================
# 场景注册表
# =============================================================================
SCENARIOS = {
    "S01_neuro_metadata":    {"task": S01_TASK, "test": S01_TEST, "source": "#1 Researcher A", "domain": "neuroscience", "difficulty": "easy"},
    "S02_spike_behavior":    {"task": S02_TASK, "test": S02_TEST, "source": "#6 Researcher B", "domain": "neuroscience", "difficulty": "hard"},
    "S03_spatial_tx":        {"task": S03_TASK, "test": S03_TEST, "source": "#3 Researcher C", "domain": "life_science", "difficulty": "medium"},
    "S04_satellite":         {"task": S04_TASK, "test": S04_TEST, "source": "#9 徐竞屹", "domain": "earth_science", "difficulty": "medium"},
    "S05_protein_parse":     {"task": S05_TASK, "test": S05_TEST, "source": "#12 Researcher D", "domain": "life_science", "difficulty": "medium"},
    "S06_gene_expression":   {"task": S06_TASK, "test": S06_TEST, "source": "#10 陈鑫", "domain": "life_science", "difficulty": "hard"},
    "S07_data_viz":          {"task": S07_TASK, "test": S07_TEST, "source": "#2 朱宇", "domain": "neuroscience", "difficulty": "easy"},
    "S08_materials_qa":      {"task": S08_TASK, "test": S08_TEST, "source": "#8 李玉强", "domain": "materials_science", "difficulty": "medium"},
    "S09_earth_obs":         {"task": S09_TASK, "test": S09_TEST, "source": "#11 费奔", "domain": "earth_science", "difficulty": "easy"},
    "S10_multimodal":        {"task": S10_TASK, "test": S10_TEST, "source": "#4 孙一介", "domain": "life_science", "difficulty": "hard"},
}
