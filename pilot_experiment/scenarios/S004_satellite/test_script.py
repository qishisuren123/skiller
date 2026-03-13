import sys, os, subprocess, tempfile
import numpy as np
import pandas as pd

def create_netcdf(path, n_scan=50, n_pix=40):
    """创建模拟的卫星扫描条带 NetCDF"""
    # 用 scipy 写简单的 netcdf
    from scipy.io import netcdf_file
    lats = np.linspace(30, 40, n_scan)[:, None] * np.ones((1, n_pix))
    lons = np.linspace(100, 110, n_pix)[None, :] * np.ones((n_scan, 1))
    bt = 250 + 20 * np.random.randn(n_scan, n_pix).astype(np.float32)
    qf = np.zeros((n_scan, n_pix), dtype=np.int8)
    qf[bt < 220] = 2  # 标记异常低温为 bad
    qf[np.random.rand(n_scan, n_pix) < 0.05] = 1  # 5% suspect

    with netcdf_file(path, "w") as f:
        f.createDimension("scanline", n_scan)
        f.createDimension("pixel", n_pix)
        v = f.createVariable("brightness_temp", "f", ("scanline", "pixel"))
        v[:] = bt
        v = f.createVariable("latitude", "f", ("scanline", "pixel"))
        v[:] = lats.astype(np.float32)
        v = f.createVariable("longitude", "f", ("scanline", "pixel"))
        v[:] = lons.astype(np.float32)
        v = f.createVariable("quality_flag", "b", ("scanline", "pixel"))
        v[:] = qf
    return n_scan * n_pix, int((qf < 2).sum())

with tempfile.TemporaryDirectory() as tmpdir:
    nc_path = f"{tmpdir}/satellite.nc"
    csv_out = f"{tmpdir}/gridded.csv"
    total_pix, valid_pix = create_netcdf(nc_path)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", nc_path, "--output", csv_out, "--resolution", "2.0"],
        [sys.executable, "generated.py", nc_path, "-o", csv_out, "--resolution", "2.0"],
        [sys.executable, "generated.py", nc_path, csv_out],
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
        for t in ["L1_valid_csv","L2_has_columns","L2_bt_range","L2_no_bad_pixels","L2_grid_coverage"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    cols_lower = [c.lower() for c in df.columns]
    if "lat" in cols_lower and "lon" in cols_lower:
        print("PASS:L2_has_columns")
    elif any("lat" in c for c in cols_lower) and any("lon" in c for c in cols_lower):
        print("PASS:L2_has_columns")
    else:
        print(f"FAIL:L2_has_columns - columns={list(df.columns)}")

    # 亮温合理范围
    bt_col = [c for c in df.columns if any(k in c.lower() for k in ["bt","bright","temp","mean"])]
    if bt_col:
        bt_vals = df[bt_col[0]].dropna()
        if bt_vals.min() > 200 and bt_vals.max() < 350:
            print(f"PASS:L2_bt_range - [{bt_vals.min():.1f}, {bt_vals.max():.1f}]")
        else:
            print(f"FAIL:L2_bt_range - [{bt_vals.min():.1f}, {bt_vals.max():.1f}]")
    else:
        print("FAIL:L2_bt_range - no BT column found")

    # 坏像素应被过滤
    if len(df) < total_pix:
        print(f"PASS:L2_no_bad_pixels - {len(df)} grid cells (from {total_pix} pixels)")
    else:
        print(f"FAIL:L2_no_bad_pixels - {len(df)} >= {total_pix}")

    # 网格覆盖
    if len(df) >= 5:
        print(f"PASS:L2_grid_coverage - {len(df)} grid cells")
    else:
        print(f"FAIL:L2_grid_coverage - only {len(df)} cells")

    # --- 新增测试 ---
    # L2: 经纬度范围合理（lat 30-40, lon 100-110）
    lat_col = [c for c in df.columns if "lat" in c.lower()]
    lon_col = [c for c in df.columns if "lon" in c.lower()]
    if lat_col and lon_col:
        lat_vals = df[lat_col[0]].dropna()
        lon_vals = df[lon_col[0]].dropna()
        if lat_vals.min() >= 29 and lat_vals.max() <= 41 and lon_vals.min() >= 99 and lon_vals.max() <= 111:
            print("PASS:L2_lat_lon_range")
        else:
            print(f"FAIL:L2_lat_lon_range - lat=[{lat_vals.min():.1f},{lat_vals.max():.1f}], lon=[{lon_vals.min():.1f},{lon_vals.max():.1f}]")
    else:
        print("FAIL:L2_lat_lon_range - no lat/lon columns")

    # L2: 有效像素数列
    n_valid_col = [c for c in df.columns if "valid" in c.lower() or "count" in c.lower() or "n_" in c.lower()]
    if n_valid_col:
        print(f"PASS:L2_n_valid - column: {n_valid_col[0]}")
    else:
        print("FAIL:L2_n_valid - no valid pixel count column")

    # L2: 网格分辨率（相邻 lat/lon 差应接近 2.0 度）
    if lat_col and len(df) > 1:
        lats_unique = sorted(df[lat_col[0]].dropna().unique())
        if len(lats_unique) >= 2:
            res = np.median(np.diff(lats_unique))
            if 1.0 <= res <= 3.0:
                print(f"PASS:L2_resolution - {res:.2f} degrees")
            else:
                print(f"FAIL:L2_resolution - {res:.2f} degrees (expected ~2.0)")
        else:
            print("FAIL:L2_resolution - only 1 unique lat")
    else:
        print("FAIL:L2_resolution")

    # L2: 输出无 NaN（重网格化后不应有 NaN）
    if bt_col:
        nan_count = df[bt_col[0]].isna().sum()
        if nan_count == 0:
            print("PASS:L2_no_nan")
        else:
            print(f"FAIL:L2_no_nan - {nan_count} NaN values in BT column")
    else:
        print("FAIL:L2_no_nan - no BT column")

    # SCORE: 空间覆盖率（网格实际覆盖/理论覆盖）
    if lat_col and lon_col:
        n_lat = len(df[lat_col[0]].unique())
        n_lon = len(df[lon_col[0]].unique())
        expected_cells = int((40 - 30) / 2.0) * int((110 - 100) / 2.0)  # 5 × 5 = 25
        spatial_coverage = round(min(len(df) / max(expected_cells, 1), 1.0), 4)
    else:
        spatial_coverage = 0.0
    print(f"SCORE:spatial_coverage={spatial_coverage}")

    # SCORE: 插值质量（BT 值的合理性）
    if bt_col:
        bt_vals = df[bt_col[0]].dropna()
        in_range = ((bt_vals > 220) & (bt_vals < 300)).mean()
        interpolation_quality = round(in_range, 4)
    else:
        interpolation_quality = 0.0
    print(f"SCORE:interpolation_quality={interpolation_quality}")
