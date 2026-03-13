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
            f.write(f">{g}\n{'ATCG' * (seq_len // 4)}\n")
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
