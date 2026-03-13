#!/usr/bin/env python3
"""
创建合成神经科学测试数据，结构与 question.csv #1（Researcher A Zebrafish 数据）一致。
数据用随机值，规模小（100 neurons x 500 timepoints），但 key 名和结构与真实数据一致。

目录结构:
  test_data/
    Additional_mat_files/
      CustomColormaps.mat       (scipy v5 格式)
      FishOutline.mat           (scipy v5 格式)
    Subjects/
      subject_01/
        TimeSeries.h5           (含 CellResp, CellRespAvr 等 key)
        data_full.mat           (v5 格式)
      subject_02/
        TimeSeries.h5           (同结构，dim-0 不同)
        data_full.mat           (v7.3/HDF5 格式，触发 scipy fallback)
      subject_03/
        TimeSeries.h5 + data_full.mat (v5 格式)
"""

import os
import numpy as np
import h5py
import scipy.io as sio

# 基本参数
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
SUBJECTS = {
    "subject_01": {"num_neurons": 100, "num_timepoints": 500, "mat_format": "v5"},
    "subject_02": {"num_neurons": 120, "num_timepoints": 500, "mat_format": "v7.3"},
    "subject_03": {"num_neurons": 95,  "num_timepoints": 500, "mat_format": "v5"},
}
NUM_TIMEPOINTS_TRIAL = 50
NUM_STIMULI = 5
RNG = np.random.default_rng(42)


def create_additional_mat_files():
    """创建 Additional_mat_files/ 下的辅助 .mat 文件（v5 格式）"""
    out_dir = os.path.join(BASE_DIR, "Additional_mat_files")
    os.makedirs(out_dir, exist_ok=True)

    # CustomColormaps.mat - 自定义颜色映射
    colormaps = {
        "cluster_colors": RNG.random((10, 3)).astype(np.float64),
        "regression_colors": RNG.random((6, 3)).astype(np.float64),
        "anatomy_palette": RNG.random((20, 3)).astype(np.float64),
    }
    sio.savemat(os.path.join(out_dir, "CustomColormaps.mat"), colormaps)
    print(f"  Created CustomColormaps.mat (v5, {len(colormaps)} keys)")

    # FishOutline.mat - 鱼体轮廓坐标
    outline = {
        "outline_x": RNG.random((200,)).astype(np.float64),
        "outline_y": RNG.random((200,)).astype(np.float64),
        "outline_with_eyes": RNG.random((250, 2)).astype(np.float64),
    }
    sio.savemat(os.path.join(out_dir, "FishOutline.mat"), outline)
    print(f"  Created FishOutline.mat (v5, {len(outline)} keys)")


def create_timeseries_h5(subject_dir, num_neurons, num_timepoints):
    """创建 TimeSeries.h5，包含与 question.csv #1 一致的 key 结构"""
    filepath = os.path.join(subject_dir, "TimeSeries.h5")

    with h5py.File(filepath, "w") as f:
        # 神经活动数据 - DFF0
        f.create_dataset("CellResp", data=RNG.standard_normal((num_neurons, num_timepoints)).astype(np.float32))
        # 试次平均的神经活动
        f.create_dataset("CellRespAvr", data=RNG.standard_normal((num_neurons, NUM_TIMEPOINTS_TRIAL)).astype(np.float32))
        # Z-scored 试次平均
        f.create_dataset("CellRespAvrZ", data=RNG.standard_normal((num_neurons, NUM_TIMEPOINTS_TRIAL)).astype(np.float32))
        # Z-scored 神经活动
        f.create_dataset("CellRespZ", data=RNG.standard_normal((num_neurons, num_timepoints)).astype(np.float32))
        # 绝对索引
        f.create_dataset("absIX", data=np.arange(num_neurons, dtype=np.int32).reshape(-1, 1))

    print(f"  Created TimeSeries.h5 ({num_neurons} neurons x {num_timepoints} timepoints)")


def create_data_full_mat_v5(subject_dir, num_neurons, num_timepoints):
    """创建 data_full.mat（scipy v5 格式），包含元数据、解剖成像、坐标、行为数据等"""
    filepath = os.path.join(subject_dir, "data_full.mat")

    data = {
        # 实验参数
        "periods": np.array([100, 80, 60, 120, 140], dtype=np.float64),
        "fpsec": np.array([[2.0]], dtype=np.float64),
        "numcell_full": np.array([[num_neurons]], dtype=np.float64),
        # 时间列表（刺激类型对应的时间点索引）
        "timelists": np.zeros((1, NUM_STIMULI), dtype=object),
        "timelists_names": np.array(["phT", "OMR", "looming", "DF", "spont"], dtype=object).reshape(1, -1),
        # 空间坐标
        "CellXYZ": RNG.random((num_neurons, 3)).astype(np.float64) * 100,
        "CellXYZ_norm": RNG.random((num_neurons, 3)).astype(np.float64),
        # 解剖成像
        "anat_stack": RNG.integers(0, 255, (50, 60, 30), dtype=np.uint8),
        "anat_yx": RNG.integers(0, 255, (60, 80, 3), dtype=np.uint8),
        "anat_yz": RNG.integers(0, 255, (50, 30, 3), dtype=np.uint8),
        "anat_zx": RNG.integers(0, 255, (50, 80, 3), dtype=np.uint8),
        # 无效细胞索引
        "IX_inval_anat": RNG.integers(0, num_neurons, (5, 1), dtype=np.int32),
        "IX_inval_norm": RNG.integers(0, num_neurons, (3, 1), dtype=np.int32),
        # 刺激信息
        "stimuluskey_raw": RNG.integers(0, 5, (num_timepoints * 2,), dtype=np.int32),
        "stim_full": RNG.integers(0, 5, (num_timepoints,), dtype=np.int32),
        "stimAvr": RNG.integers(0, 5, (NUM_TIMEPOINTS_TRIAL,), dtype=np.int32),
        # 行为数据
        "Behavior_raw": RNG.standard_normal((1, num_timepoints * 2)).astype(np.float64),
        "Behavior_full": RNG.standard_normal((1, num_timepoints)).astype(np.float64),
        "BehaviorAvr": RNG.standard_normal((1, NUM_TIMEPOINTS_TRIAL)).astype(np.float64),
        # 眼球数据
        "Eye_full": RNG.standard_normal((2, num_timepoints)).astype(np.float64),
        "Eye_avr": RNG.standard_normal((2, NUM_TIMEPOINTS_TRIAL)).astype(np.float64),
        # 运动种子
        "Behavior_full_motorseed": RNG.standard_normal((2, num_timepoints)).astype(np.float64),
        "BehaviorAvr_motorseed": RNG.standard_normal((2, NUM_TIMEPOINTS_TRIAL)).astype(np.float64),
        "Eye_full_motorseed": RNG.standard_normal((2, num_timepoints)).astype(np.float64),
        "EyeAvr_motorseed": RNG.standard_normal((2, NUM_TIMEPOINTS_TRIAL)).astype(np.float64),
    }

    # 填充 timelists（每个刺激类型的时间点索引）
    for i in range(NUM_STIMULI):
        start = i * (num_timepoints // NUM_STIMULI)
        end = (i + 1) * (num_timepoints // NUM_STIMULI)
        data["timelists"][0, i] = np.arange(start, end, dtype=np.float64)

    sio.savemat(filepath, data)
    print(f"  Created data_full.mat (v5 format, {len(data)} keys)")


def create_data_full_mat_v73(subject_dir, num_neurons, num_timepoints):
    """创建 data_full.mat（v7.3/HDF5 格式），触发 scipy fallback 到 h5py"""
    filepath = os.path.join(subject_dir, "data_full.mat")

    with h5py.File(filepath, "w") as f:
        # 在 HDF5 文件中模拟 MATLAB v7.3 结构
        # 添加 MATLAB 文件标识属性
        f.attrs["MATLAB_class"] = "double"

        # 实验参数
        f.create_dataset("periods", data=np.array([100, 80, 60, 120, 140], dtype=np.float64))
        f.create_dataset("fpsec", data=np.array([[2.0]], dtype=np.float64))
        f.create_dataset("numcell_full", data=np.array([[num_neurons]], dtype=np.float64))

        # 空间坐标
        f.create_dataset("CellXYZ", data=RNG.random((num_neurons, 3)).astype(np.float64) * 100)
        f.create_dataset("CellXYZ_norm", data=RNG.random((num_neurons, 3)).astype(np.float64))

        # 解剖成像
        f.create_dataset("anat_stack", data=RNG.integers(0, 255, (50, 60, 30), dtype=np.uint8))
        f.create_dataset("anat_yx", data=RNG.integers(0, 255, (60, 80, 3), dtype=np.uint8))
        f.create_dataset("anat_yz", data=RNG.integers(0, 255, (50, 30, 3), dtype=np.uint8))
        f.create_dataset("anat_zx", data=RNG.integers(0, 255, (50, 80, 3), dtype=np.uint8))

        # 无效索引
        f.create_dataset("IX_inval_anat", data=RNG.integers(0, num_neurons, (5, 1), dtype=np.int32))

        # 刺激信息
        f.create_dataset("stimuluskey_raw", data=RNG.integers(0, 5, (num_timepoints * 2,), dtype=np.int32))
        f.create_dataset("stim_full", data=RNG.integers(0, 5, (num_timepoints,), dtype=np.int32))
        f.create_dataset("stimAvr", data=RNG.integers(0, 5, (NUM_TIMEPOINTS_TRIAL,), dtype=np.int32))

        # 行为数据
        f.create_dataset("Behavior_raw", data=RNG.standard_normal((1, num_timepoints * 2)).astype(np.float64))
        f.create_dataset("Behavior_full", data=RNG.standard_normal((1, num_timepoints)).astype(np.float64))
        f.create_dataset("BehaviorAvr", data=RNG.standard_normal((1, NUM_TIMEPOINTS_TRIAL)).astype(np.float64))

        # 眼球数据
        f.create_dataset("Eye_full", data=RNG.standard_normal((2, num_timepoints)).astype(np.float64))
        f.create_dataset("Eye_avr", data=RNG.standard_normal((2, NUM_TIMEPOINTS_TRIAL)).astype(np.float64))

        # 运动种子
        f.create_dataset("Behavior_full_motorseed", data=RNG.standard_normal((2, num_timepoints)).astype(np.float64))
        f.create_dataset("BehaviorAvr_motorseed", data=RNG.standard_normal((2, NUM_TIMEPOINTS_TRIAL)).astype(np.float64))
        f.create_dataset("Eye_full_motorseed", data=RNG.standard_normal((2, num_timepoints)).astype(np.float64))
        f.create_dataset("EyeAvr_motorseed", data=RNG.standard_normal((2, NUM_TIMEPOINTS_TRIAL)).astype(np.float64))

        # 刺激名称（字符串数据）
        dt = h5py.special_dtype(vlen=str)
        timelists_names = f.create_dataset("timelists_names", (5,), dtype=dt)
        timelists_names[:] = ["phT", "OMR", "looming", "DF", "spont"]

    print(f"  Created data_full.mat (v7.3/HDF5 format, triggers scipy fallback)")


def main():
    print(f"创建合成测试数据: {BASE_DIR}")
    print("=" * 60)

    # 清理旧数据
    if os.path.exists(BASE_DIR):
        import shutil
        shutil.rmtree(BASE_DIR)

    # 创建辅助 MAT 文件
    print("\n[1/2] Creating Additional_mat_files/")
    create_additional_mat_files()

    # 创建被试数据
    print("\n[2/2] Creating Subject directories")
    for subject_name, params in SUBJECTS.items():
        subject_dir = os.path.join(BASE_DIR, "Subjects", subject_name)
        os.makedirs(subject_dir, exist_ok=True)
        print(f"\n  --- {subject_name} (neurons={params['num_neurons']}, "
              f"tp={params['num_timepoints']}, mat={params['mat_format']}) ---")

        # TimeSeries.h5
        create_timeseries_h5(subject_dir, params["num_neurons"], params["num_timepoints"])

        # data_full.mat
        if params["mat_format"] == "v7.3":
            create_data_full_mat_v73(subject_dir, params["num_neurons"], params["num_timepoints"])
        else:
            create_data_full_mat_v5(subject_dir, params["num_neurons"], params["num_timepoints"])

    # 验证文件数量
    file_count = 0
    for root, dirs, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith((".h5", ".mat")):
                file_count += 1
                fpath = os.path.join(root, f)
                size = os.path.getsize(fpath)
                rel = os.path.relpath(fpath, BASE_DIR)
                print(f"  ✓ {rel} ({size:,} bytes)")

    print(f"\n{'=' * 60}")
    print(f"共创建 {file_count} 个测试文件")

    # 验证 v7.3 文件确实会触发 scipy fallback
    print("\n验证 v7.3 fallback:")
    v73_path = os.path.join(BASE_DIR, "Subjects", "subject_02", "data_full.mat")
    try:
        sio.loadmat(v73_path)
        print("  ⚠ scipy 成功读取了 v7.3 文件（未触发 fallback）")
    except (NotImplementedError, OSError, ValueError) as e:
        print(f"  ✓ scipy 正确抛出异常: {type(e).__name__}: {e}")
        # 验证 h5py 可以读取
        with h5py.File(v73_path, "r") as f:
            print(f"  ✓ h5py fallback 成功, keys: {list(f.keys())[:5]}...")


if __name__ == "__main__":
    main()
