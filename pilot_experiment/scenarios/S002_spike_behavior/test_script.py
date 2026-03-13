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
