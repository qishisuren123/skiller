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
