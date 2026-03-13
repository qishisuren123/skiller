"""
场景 1：神经科学数据元数据生成
来源：question.csv #1 Researcher A
"""

# 给 LLM 的任务描述（模拟真实用户输入）
TASK_DESC = """I have a directory of neuroscience data files (HDF5 and MATLAB .mat files) from a zebrafish whole-brain imaging experiment. The structure looks like:

```
dataset_root/
  Additional_mat_files/
    CustomColormaps.mat
    ReferenceBrain.mat
  Subjects/
    subject_0/
      TimeSeries.h5     (nested groups: /CellResp, /CellRespAvr, etc.)
      data_full.mat     (MATLAB v7.3, has keys: periods, fpsec, CellXYZ, ...)
    subject_1/
      TimeSeries.h5
      data_full.mat
    ... (15 subjects total)
```

Write a complete Python script that:
1. Recursively scans the directory to find all .h5 and .mat files
2. For each HDF5 file, reads all dataset paths, shapes, and dtypes (including nested groups)
3. For each .mat file, reads all variable names, shapes, and dtypes. IMPORTANT: some .mat files are MATLAB v7.3 format which scipy.io.loadmat cannot open - you must handle this.
4. Merges entries from repeated subject directories into wildcard patterns (e.g., subject_*/TimeSeries.h5)
5. Outputs a meta.json with a summary section and per-file details

The script should be a standalone CLI tool with argparse that takes the root directory as input and outputs meta.json.
Include proper error handling for corrupted files and permission errors.
"""

# 自动测评脚本
TEST_SCRIPT = '''
"""自动测评：运行生成的代码并检查输出"""
import sys
import os
import json
import tempfile
import importlib.util
import traceback
import numpy as np

# 创建合成测试数据
def create_test_data(root):
    """创建 3 个 subject，每个有 1 个 HDF5 + 1 个 MAT 文件"""
    import h5py
    import scipy.io

    os.makedirs(f"{root}/Subjects/subject_0", exist_ok=True)
    os.makedirs(f"{root}/Subjects/subject_1", exist_ok=True)
    os.makedirs(f"{root}/Subjects/subject_2", exist_ok=True)
    os.makedirs(f"{root}/Additional_mat_files", exist_ok=True)

    # HDF5 文件（嵌套 group）
    for i in range(3):
        n_neurons = 100 + i * 10
        with h5py.File(f"{root}/Subjects/subject_{i}/TimeSeries.h5", "w") as f:
            g = f.create_group("recording")
            g.create_dataset("CellResp", data=np.random.randn(n_neurons, 500).astype(np.float32))
            g.create_dataset("CellRespAvr", data=np.random.randn(n_neurons, 50).astype(np.float32))
            f.create_dataset("absIX", data=np.arange(n_neurons))

    # MAT 文件（v5 格式，scipy 可读）
    for i in range(3):
        scipy.io.savemat(f"{root}/Subjects/subject_{i}/data_full.mat", {
            "periods": np.array([100, 200, 150]),
            "fpsec": np.array([2.0]),
            "CellXYZ": np.random.randn(100 + i * 10, 3),
        })

    # 额外的 mat 文件
    scipy.io.savemat(f"{root}/Additional_mat_files/ReferenceBrain.mat", {
        "brain_template": np.zeros((50, 50, 20)),
    })


def run_tests():
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = os.path.join(tmpdir, "dataset")
        os.makedirs(data_root)
        create_test_data(data_root)
        output_json = os.path.join(tmpdir, "meta.json")

        # 加载生成的代码
        try:
            spec = importlib.util.spec_from_file_location("generated", "generated.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"FAIL:import - {e}")
            for t in ["import", "runs", "output_exists", "valid_json",
                       "has_summary", "lists_files", "nested_keys", "mat_handled"]:
                if t != "import":
                    print(f"FAIL:{t} - skipped due to import failure")
            return
        results.append(True)
        print("PASS:import")

        # 测试 1：能否用 --help 运行
        import subprocess
        r = subprocess.run(
            [sys.executable, "generated.py", "--help"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and ("usage" in r.stdout.lower() or "help" in r.stdout.lower()):
            print("PASS:has_argparse_help")
        else:
            print(f"FAIL:has_argparse_help - returncode={r.returncode}")

        # 测试 2：能否实际运行并生成输出
        r = subprocess.run(
            [sys.executable, "generated.py", data_root, "-o", output_json],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath("generated.py"))
        )
        # 也尝试其他常见参数格式
        if r.returncode != 0 and not os.path.exists(output_json):
            r = subprocess.run(
                [sys.executable, "generated.py", "--root", data_root, "--output", output_json],
                capture_output=True, text=True, timeout=30,
                cwd=os.path.dirname(os.path.abspath("generated.py"))
            )
        if r.returncode != 0 and not os.path.exists(output_json):
            r = subprocess.run(
                [sys.executable, "generated.py", data_root, "--output", output_json],
                capture_output=True, text=True, timeout=30,
                cwd=os.path.dirname(os.path.abspath("generated.py"))
            )
        if r.returncode == 0 or os.path.exists(output_json):
            print("PASS:runs_successfully")
        else:
            print(f"FAIL:runs_successfully - returncode={r.returncode} stderr={r.stderr[:300]}")

        # 测试 3：输出文件存在
        if os.path.exists(output_json):
            print("PASS:output_exists")
        else:
            print("FAIL:output_exists")
            # 还是尝试找其他输出
            for f in os.listdir(tmpdir):
                if f.endswith(".json"):
                    output_json = os.path.join(tmpdir, f)
                    break
            else:
                for remaining in ["valid_json", "has_summary", "lists_files",
                                  "nested_keys", "mat_handled"]:
                    print(f"FAIL:{remaining} - no output file")
                return

        # 测试 4：有效 JSON
        try:
            with open(output_json) as f:
                meta = json.load(f)
            print("PASS:valid_json")
        except Exception as e:
            print(f"FAIL:valid_json - {e}")
            for remaining in ["has_summary", "lists_files", "nested_keys", "mat_handled"]:
                print(f"FAIL:{remaining} - invalid JSON")
            return

        # 测试 5：有 summary 信息（文件数、大小等）
        meta_str = json.dumps(meta).lower()
        if any(k in meta_str for k in ["total", "summary", "count", "size"]):
            print("PASS:has_summary")
        else:
            print("FAIL:has_summary - no summary/count/total in output")

        # 测试 6：列出了文件
        if any(k in meta_str for k in ["timeseries", "data_full", "referencebrain", ".h5", ".mat"]):
            print("PASS:lists_files")
        else:
            print("FAIL:lists_files - no file names found in output")

        # 测试 7：能看到嵌套的 HDF5 keys（recording/CellResp）
        if "cellresp" in meta_str or "recording" in meta_str:
            print("PASS:nested_keys")
        else:
            print("FAIL:nested_keys - nested HDF5 group keys not found")

        # 测试 8：MAT 文件被处理
        if "cellxyz" in meta_str or "periods" in meta_str or "fpsec" in meta_str:
            print("PASS:mat_handled")
        else:
            print("FAIL:mat_handled - MAT file keys not in output")


if __name__ == "__main__":
    run_tests()
'''
