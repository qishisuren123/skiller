"""
场景 2：神经 spike + behavior 数据标准化
来源：question.csv #6 Researcher B
"""

TASK_DESC = """I have neural spike and behavior data from multiple sources in different formats:

1. **XDS format (.mat)**: Contains a struct with fields like `spike_times` (cell array, one per unit), `cursor_vel` (Nx2 velocity), `trial_info_table` with success/failure labels.
2. **NWB format (.nwb)**: Contains `units` table with spike times and `acquisition` with hand position time series. Trial info in `intervals/trials`.

I need a Python script that:
1. Loads data from both XDS .mat files and NWB files
2. Filters only SUCCESSFUL trials (different formats use different field names for trial outcome)
3. Bins spike times into uniform time bins (default 20ms) using np.histogram
4. Resamples behavior data (velocity or position) to match spike bin centers
5. Writes everything to a standardized HDF5 file with structure:
   /dataset_name/session_name/trial_NNNN/timestamps
   /dataset_name/session_name/trial_NNNN/spikes  (n_bins, n_units)
   /dataset_name/session_name/trial_NNNN/behavior (n_bins, n_dims)

The script should handle the case where XDS MATLAB structs are wrapped in (1,1) numpy arrays.
Include quality checks: flag trials with zero units, NaN in behavior, or abnormal firing rates.
"""

TEST_SCRIPT = '''
"""自动测评：spike-behavior 标准化工具"""
import sys
import os
import json
import tempfile
import importlib.util
import subprocess
import traceback
import numpy as np

def run_tests():
    # 加载生成的代码
    try:
        spec = importlib.util.spec_from_file_location("generated", "generated.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print("PASS:import")
    except Exception as e:
        print(f"FAIL:import - {e}")
        for t in ["has_argparse", "has_bin_func", "has_filter_func",
                   "has_hdf5_write", "has_quality_check", "handles_mat_struct",
                   "has_resample"]:
            print(f"FAIL:{t} - skipped")
        return

    # 测试 1：有 argparse 或 CLI 入口
    import subprocess
    r = subprocess.run(
        [sys.executable, "generated.py", "--help"],
        capture_output=True, text=True, timeout=10
    )
    if r.returncode == 0:
        print("PASS:has_argparse")
    else:
        # 有些脚本不用 argparse 但有 main 函数
        src = open("generated.py").read()
        if "argparse" in src or "def main" in src:
            print("PASS:has_argparse")
        else:
            print("FAIL:has_argparse")

    # 读取源码做静态检查
    src = open("generated.py").read().lower()

    # 测试 2：有 spike binning 函数（np.histogram 或类似）
    if "histogram" in src or "bin_spike" in src or "digitize" in src:
        print("PASS:has_bin_func")
    else:
        print("FAIL:has_bin_func - no spike binning logic found")

    # 测试 3：有 trial 过滤逻辑（success/outcome）
    if ("success" in src or "outcome" in src or "filter" in src) and "trial" in src:
        print("PASS:has_filter_func")
    else:
        print("FAIL:has_filter_func - no trial filtering logic")

    # 测试 4：有 HDF5 写入
    if "h5py" in src and ("create_dataset" in src or "create_group" in src):
        print("PASS:has_hdf5_write")
    else:
        print("FAIL:has_hdf5_write - no HDF5 write logic")

    # 测试 5：有质量检查
    if ("quality" in src or "qc" in src or "flag" in src) and \
       ("nan" in src or "firing" in src or "rate" in src):
        print("PASS:has_quality_check")
    else:
        print("FAIL:has_quality_check - no quality check logic")

    # 测试 6：处理 MATLAB struct 解包（[0,0] 或 .flat[0]）
    if "[0,0]" in src or "[0][0]" in src or "flat[0]" in src or ".item()" in src or "squeeze" in src:
        print("PASS:handles_mat_struct")
    else:
        print("FAIL:handles_mat_struct - no MATLAB struct unpacking")

    # 测试 7：有重采样/插值逻辑
    if "resample" in src or "interp" in src or "interpolat" in src:
        print("PASS:has_resample")
    else:
        print("FAIL:has_resample - no resampling/interpolation logic")

    # 测试 8：能用合成数据端到端运行
    # 创建一个简单的合成 MAT 文件模拟 XDS
    try:
        import scipy.io
        import h5py
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建简单的 XDS-like mat
            n_units = 5
            spike_times = np.empty((1, n_units), dtype=object)
            for u in range(n_units):
                spike_times[0, u] = np.sort(np.random.uniform(0, 2, size=50))

            xds_data = {
                "spike_times": spike_times,
                "cursor_vel": np.random.randn(200, 2),
                "time_frame": np.linspace(0, 2, 200),
            }
            mat_path = os.path.join(tmpdir, "test_xds.mat")
            scipy.io.savemat(mat_path, xds_data)

            out_h5 = os.path.join(tmpdir, "output.h5")

            # 尝试找到合适的函数来运行
            ran = False
            # 方法 1：直接跑 CLI
            r = subprocess.run(
                [sys.executable, "generated.py", "--output", out_h5, mat_path],
                capture_output=True, text=True, timeout=30,
                cwd=os.path.dirname(os.path.abspath("generated.py"))
            )
            if r.returncode == 0 and os.path.exists(out_h5):
                ran = True

            if ran:
                # 验证 HDF5 输出结构
                with h5py.File(out_h5, "r") as f:
                    has_trial = any("trial" in k.lower() for k in _walk_h5_keys(f))
                    has_spikes = any("spike" in k.lower() for k in _walk_h5_keys(f))
                if has_trial and has_spikes:
                    print("PASS:e2e_synthetic")
                else:
                    print("FAIL:e2e_synthetic - HDF5 missing trial/spikes structure")
            else:
                print("FAIL:e2e_synthetic - CLI run failed or no output")
    except Exception as e:
        print(f"FAIL:e2e_synthetic - {e}")


def _walk_h5_keys(group, prefix=""):
    """递归获取 HDF5 所有 key"""
    keys = []
    for k in group:
        full = f"{prefix}/{k}"
        keys.append(full)
        if hasattr(group[k], "keys"):
            keys.extend(_walk_h5_keys(group[k], full))
    return keys


if __name__ == "__main__":
    run_tests()
'''
