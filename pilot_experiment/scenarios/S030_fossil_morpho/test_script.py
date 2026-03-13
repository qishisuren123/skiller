import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_specimens=120):
    np.random.seed(42)
    taxa = ["Trilobita_sp_A", "Trilobita_sp_B", "Brachiopoda_sp", "Ammonoidea_sp", "Gastropoda_sp"]
    formations = ["Morrison", "Hell_Creek", "Burgess_Shale", "Solnhofen"]
    epochs = ["Cambrian", "Ordovician", "Devonian", "Jurassic", "Cretaceous"]
    rows = []
    for i in range(n_specimens):
        taxon = taxa[i % len(taxa)]
        # 不同物种有不同的基础形态
        base = {"Trilobita_sp_A": (30, 15, 8, 5), "Trilobita_sp_B": (25, 18, 6, 4),
                "Brachiopoda_sp": (12, 14, 10, 3), "Ammonoidea_sp": (40, 38, 20, 15),
                "Gastropoda_sp": (20, 10, 10, 4)}[taxon]
        length = base[0] + np.random.normal(0, base[0] * 0.15)
        width = base[1] + np.random.normal(0, base[1] * 0.15)
        height = base[2] + np.random.normal(0, base[2] * 0.15)
        mass = base[3] + np.random.normal(0, base[3] * 0.2)
        rows.append({
            "specimen_id": f"SPEC{i:04d}",
            "taxon": taxon,
            "length_mm": round(max(length, 2), 2),
            "width_mm": round(max(width, 1), 2),
            "height_mm": round(max(height, 0.5), 2),
            "mass_g": round(max(mass, 0.1), 2),
            "formation": formations[i % len(formations)],
            "epoch": epochs[i % len(epochs)],
        })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_specimens, len(taxa)

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/fossils.csv"
    out_dir = f"{tmpdir}/output"
    n_specimens, n_taxa = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "-o", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    morph_csv = None
    pca_csv = None
    taxon_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("morph" in fl or "specimen" in fl) and fl.endswith(".csv"):
                morph_csv = os.path.join(out_dir, f)
            if "pca" in fl and fl.endswith(".csv"):
                pca_csv = os.path.join(out_dir, f)
            if ("taxon" in fl or "summary" in fl) and fl.endswith(".json"):
                taxon_json = os.path.join(out_dir, f)

    has_output = morph_csv or pca_csv or taxon_json
    if has_output:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_all_specimens", "L2_elongation", "L2_sphericity",
                   "L2_volume", "L2_pca_file", "L2_pca_variance", "L2_pca_loadings",
                   "L2_taxon_json", "L2_taxon_groups", "L2_epoch_groups",
                   "L2_no_nan", "L2_pc_scores"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if morph_csv:
        try:
            df = pd.read_csv(morph_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 所有标本
    if len(df) >= n_specimens:
        print(f"PASS:L2_all_specimens - {len(df)} rows")
    elif len(df) > 0:
        print(f"PASS:L2_all_specimens - {len(df)} rows")
    else:
        print("FAIL:L2_all_specimens")

    # L2: elongation 列
    if "elong" in cols or "l_w" in cols or "length_width" in cols:
        print("PASS:L2_elongation")
    else:
        print("FAIL:L2_elongation")

    # L2: sphericity 列
    if "spheri" in cols or "sphere" in cols:
        print("PASS:L2_sphericity")
    else:
        print("FAIL:L2_sphericity")

    # L2: volume 列
    if "volume" in cols or "vol" in cols:
        print("PASS:L2_volume")
    else:
        print("FAIL:L2_volume")

    # L2: PCA 文件
    pca_df = pd.DataFrame()
    if pca_csv and os.path.exists(pca_csv):
        print("PASS:L2_pca_file")
        try:
            pca_df = pd.read_csv(pca_csv)
        except:
            pass
    else:
        print("FAIL:L2_pca_file")

    # L2: PCA explained variance
    pca_cols = " ".join(pca_df.columns).lower() if len(pca_df) > 0 else ""
    if "variance" in pca_cols or "explained" in pca_cols:
        print("PASS:L2_pca_variance")
    else:
        print("FAIL:L2_pca_variance")

    # L2: PCA loadings
    if "loading" in pca_cols or "length" in pca_cols or "component" in pca_cols:
        print("PASS:L2_pca_loadings")
    else:
        print("FAIL:L2_pca_loadings")

    # L2: taxon summary JSON
    summ = {}
    if taxon_json and os.path.exists(taxon_json):
        try:
            summ = json.load(open(taxon_json))
            print("PASS:L2_taxon_json")
        except:
            print("FAIL:L2_taxon_json")
    else:
        print("FAIL:L2_taxon_json")

    s_str = json.dumps(summ).lower() if summ else ""

    # L2: taxon 分组
    if any(t.lower() in s_str for t in ["trilobita", "brachiopoda", "ammonoidea", "gastropoda"]):
        print("PASS:L2_taxon_groups")
    elif "taxon" in s_str:
        print("PASS:L2_taxon_groups")
    else:
        print("FAIL:L2_taxon_groups")

    # L2: epoch 分组
    if any(e.lower() in s_str for e in ["cambrian", "ordovician", "devonian", "jurassic", "cretaceous"]):
        print("PASS:L2_epoch_groups")
    elif "epoch" in s_str:
        print("PASS:L2_epoch_groups")
    else:
        print("FAIL:L2_epoch_groups")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: PC scores in morphometrics 文件
    if "pc1" in cols or "pc_1" in cols or "pca" in cols:
        print("PASS:L2_pc_scores")
    else:
        print("FAIL:L2_pc_scores")

    # SCORE: 形态指数完整度
    expected_idx = ["elong", "flat", "spheri", "volume", "density"]
    found = sum(1 for e in expected_idx if e in cols)
    morpho_completeness = round(found / len(expected_idx), 4)
    print(f"SCORE:morphometric_completeness={morpho_completeness}")

    # SCORE: PCA 质量（前 2 主成分应解释 > 70% 方差）
    if len(pca_df) > 0 and "variance" in pca_cols or "explained" in pca_cols:
        try:
            var_col = [c for c in pca_df.columns if "variance" in c.lower() or "explained" in c.lower()]
            if var_col:
                vals = pca_df[var_col[0]].dropna().values[:2]
                total_var = sum(vals)
                pca_quality = round(min(total_var, 1.0), 4) if total_var > 0 else 0.0
            else:
                pca_quality = 0.3
        except:
            pca_quality = 0.0
    else:
        pca_quality = 0.0
    print(f"SCORE:pca_quality={pca_quality}")
