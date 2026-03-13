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
