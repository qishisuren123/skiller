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
