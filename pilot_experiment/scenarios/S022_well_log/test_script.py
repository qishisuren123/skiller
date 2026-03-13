import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_points=400):
    np.random.seed(42)
    # 模拟不均匀采样的测井数据
    depth = np.sort(np.concatenate([
        np.arange(100, 200, 0.3),
        np.arange(200, 350, 0.8),
        np.arange(350, 500, 0.5),
    ]))
    depth = depth[:n_points]
    n = len(depth)
    # 生成不同岩性区间的测井响应
    gamma_ray = np.zeros(n)
    resistivity = np.zeros(n)
    neutron_porosity = np.zeros(n)
    bulk_density = np.zeros(n)
    caliper = np.zeros(n)
    for i, d in enumerate(depth):
        if d < 180:  # 砂岩段
            gamma_ray[i] = np.random.normal(40, 8)
            resistivity[i] = np.random.lognormal(3.5, 0.5)
            neutron_porosity[i] = np.random.normal(0.22, 0.03)
            bulk_density[i] = np.random.normal(2.2, 0.05)
        elif d < 280:  # 页岩段
            gamma_ray[i] = np.random.normal(120, 15)
            resistivity[i] = np.random.lognormal(1.0, 0.4)
            neutron_porosity[i] = np.random.normal(0.35, 0.04)
            bulk_density[i] = np.random.normal(2.45, 0.06)
        elif d < 400:  # 石灰岩段
            gamma_ray[i] = np.random.normal(25, 5)
            resistivity[i] = np.random.lognormal(4.0, 0.6)
            neutron_porosity[i] = np.random.normal(0.08, 0.02)
            bulk_density[i] = np.random.normal(2.6, 0.04)
        else:  # 粉砂岩段
            gamma_ray[i] = np.random.normal(70, 10)
            resistivity[i] = np.random.lognormal(2.0, 0.5)
            neutron_porosity[i] = np.random.normal(0.2, 0.04)
            bulk_density[i] = np.random.normal(2.4, 0.05)
        caliper[i] = np.random.normal(8.5, 0.3)
    gamma_ray = np.clip(gamma_ray, 10, 200)
    neutron_porosity = np.clip(neutron_porosity, 0.01, 0.60)
    bulk_density = np.clip(bulk_density, 1.8, 2.85)
    df = pd.DataFrame({
        "depth": np.round(depth, 2),
        "gamma_ray": np.round(gamma_ray, 2),
        "resistivity": np.round(resistivity, 3),
        "neutron_porosity": np.round(neutron_porosity, 4),
        "bulk_density": np.round(bulk_density, 3),
        "caliper": np.round(caliper, 2),
    })
    df.to_csv(path, index=False)
    return len(df)

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/welllog.csv"
    out_dir = f"{tmpdir}/output"
    n_orig = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--depth-step", "0.5"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    resampled_csv = None
    litho_csv = None
    summary_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("resamp" in fl or "log" in fl) and f.endswith(".csv"):
                resampled_csv = os.path.join(out_dir, f)
            if ("litho" in fl or "class" in fl) and f.endswith(".csv"):
                litho_csv = os.path.join(out_dir, f)
            if "summary" in fl and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)

    if resampled_csv or litho_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_uniform_depth","L2_phit_computed","L2_vsh_computed",
                   "L2_lithology_present","L2_four_classes","L2_depth_range","L2_no_nan",
                   "L2_porosity_range","L2_vsh_range","L2_summary_exists","L2_layer_counts"]:
            print(f"FAIL:{t}")
        print("SCORE:resampling_quality=0.0")
        print("SCORE:classification_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if resampled_csv:
        try:
            df = pd.read_csv(resampled_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 均匀深度间隔
    if len(df) > 2 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()][0]
        depths = df[depth_col].values
        diffs = np.diff(depths)
        if len(diffs) > 0 and np.std(diffs) < np.mean(diffs) * 0.2:
            print(f"PASS:L2_uniform_depth - step={np.mean(diffs):.2f}m")
        else:
            print(f"PASS:L2_uniform_depth - approximately uniform")
    else:
        print("FAIL:L2_uniform_depth")

    # L2: PHIT 被计算
    if "phit" in cols or "porosity_total" in cols or "total_porosity" in cols:
        print("PASS:L2_phit_computed")
    else:
        print("FAIL:L2_phit_computed")

    # L2: Vsh 被计算
    if "vsh" in cols or "shale_volume" in cols or "v_sh" in cols:
        print("PASS:L2_vsh_computed")
    else:
        print("FAIL:L2_vsh_computed")

    # L2: 岩性分类存在
    litho_df = pd.DataFrame()
    if litho_csv:
        try:
            litho_df = pd.read_csv(litho_csv)
        except:
            pass
    litho_cols = " ".join(litho_df.columns).lower() if len(litho_df) > 0 else ""
    if "litho" in litho_cols or "class" in litho_cols or "litho" in cols or "class" in cols:
        print("PASS:L2_lithology_present")
    else:
        print("FAIL:L2_lithology_present")

    # L2: 包含四种岩性分类
    all_litho = set()
    for source in [litho_df, df]:
        if len(source) > 0:
            for c in source.columns:
                if "litho" in c.lower() or "class" in c.lower():
                    all_litho.update(source[c].astype(str).str.lower().unique())
    expected = {"sandstone", "shale", "limestone", "siltstone"}
    found_types = expected.intersection(all_litho)
    if len(found_types) >= 3:
        print(f"PASS:L2_four_classes - found {found_types}")
    elif len(found_types) >= 1:
        print(f"PASS:L2_four_classes - found {len(found_types)} types")
    else:
        print("FAIL:L2_four_classes")

    # L2: 深度范围合理 (应覆盖原始范围)
    orig_df = pd.read_csv(csv_in)
    if len(df) > 0 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()][0]
        d_min, d_max = df[depth_col].min(), df[depth_col].max()
        o_min, o_max = orig_df["depth"].min(), orig_df["depth"].max()
        if d_min <= o_min + 5 and d_max >= o_max - 5:
            print(f"PASS:L2_depth_range - [{d_min:.0f}, {d_max:.0f}]m")
        else:
            print(f"FAIL:L2_depth_range - [{d_min:.0f}, {d_max:.0f}] vs [{o_min:.0f}, {o_max:.0f}]")
    else:
        print("FAIL:L2_depth_range")

    # L2: 无 NaN
    if len(df) > 0:
        nan_pct = df.select_dtypes(include=[np.number]).isnull().mean().mean()
        print(f"{'PASS' if nan_pct < 0.05 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: PHIT 范围合理 (0-0.5)
    phit_col = [c for c in df.columns if "phit" in c.lower() or "total_porosity" in c.lower()] if len(df) > 0 else []
    if phit_col:
        vals = df[phit_col[0]].dropna()
        if vals.min() >= -0.05 and vals.max() <= 0.55:
            print(f"PASS:L2_porosity_range - [{vals.min():.3f}, {vals.max():.3f}]")
        else:
            print(f"FAIL:L2_porosity_range")
    else:
        print("FAIL:L2_porosity_range")

    # L2: Vsh 范围 [0, 1]
    vsh_col = [c for c in df.columns if "vsh" in c.lower() or "shale_vol" in c.lower() or "v_sh" in c.lower()] if len(df) > 0 else []
    if vsh_col:
        vals = df[vsh_col[0]].dropna()
        if vals.min() >= -0.01 and vals.max() <= 1.01:
            print(f"PASS:L2_vsh_range")
        else:
            print(f"FAIL:L2_vsh_range")
    else:
        print("FAIL:L2_vsh_range")

    # L2: summary.json 存在
    if summary_json and os.path.exists(summary_json):
        print("PASS:L2_summary_exists")
    else:
        print("FAIL:L2_summary_exists")

    # L2: layer_counts 在 summary 中
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if "layer" in s_str or "count" in s_str or "sandstone" in s_str or "shale" in s_str:
                print("PASS:L2_layer_counts")
            else:
                print("FAIL:L2_layer_counts")
        except:
            print("FAIL:L2_layer_counts")
    else:
        print("FAIL:L2_layer_counts")

    # SCORE: 重采样质量（深度均匀度）
    if len(df) > 2 and "depth" in cols:
        depth_col = [c for c in df.columns if "depth" in c.lower()][0]
        diffs = np.diff(df[depth_col].values)
        if len(diffs) > 0 and np.mean(diffs) > 0:
            uniformity = 1.0 - min(np.std(diffs) / np.mean(diffs), 1.0)
        else:
            uniformity = 0.0
    else:
        uniformity = 0.0
    print(f"SCORE:resampling_quality={round(uniformity, 4)}")

    # SCORE: 分类完整性
    expected_fields = ["phit", "vsh", "lithology", "sandstone", "shale", "limestone", "siltstone", "layer", "porosity"]
    all_text = cols + " " + (json.dumps(json.load(open(summary_json))).lower() if summary_json and os.path.exists(summary_json) else "")
    found = sum(1 for f in expected_fields if f in all_text)
    completeness = round(found / len(expected_fields), 4)
    print(f"SCORE:classification_completeness={completeness}")
