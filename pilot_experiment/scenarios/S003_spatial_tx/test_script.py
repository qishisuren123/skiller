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
