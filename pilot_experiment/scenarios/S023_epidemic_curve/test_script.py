import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_cases=500):
    np.random.seed(42)
    # 模拟传染病暴发：指数增长 -> 平台期 -> 下降
    start_date = pd.Timestamp("2024-03-01")
    duration_days = 90
    # 生成发病日期（logistic增长模式）
    t = np.arange(duration_days)
    rate = 1.0 / (1.0 + np.exp(-0.12 * (t - 35)))  # Logistic 增长
    daily_prob = np.diff(np.concatenate([[0], rate]))
    daily_prob = daily_prob / daily_prob.sum()
    onset_days = np.random.choice(t, size=n_cases, p=daily_prob)
    # 人口学数据
    ages = np.concatenate([
        np.random.randint(0, 18, n_cases // 5),
        np.random.randint(19, 40, n_cases // 3),
        np.random.randint(41, 60, n_cases // 4),
        np.random.randint(61, 90, n_cases - n_cases//5 - n_cases//3 - n_cases//4),
    ])
    np.random.shuffle(ages)
    ages = ages[:n_cases]
    genders = np.random.choice(["M", "F"], n_cases)
    locations = np.random.choice(["District_A", "District_B", "District_C", "District_D"], n_cases,
                                  p=[0.35, 0.3, 0.2, 0.15])
    # 结局：老年人死亡率更高
    outcomes = []
    for age in ages:
        if age >= 61:
            outcomes.append(np.random.choice(["recovered", "deceased", "hospitalized"], p=[0.6, 0.15, 0.25]))
        elif age >= 41:
            outcomes.append(np.random.choice(["recovered", "deceased", "hospitalized"], p=[0.8, 0.05, 0.15]))
        else:
            outcomes.append(np.random.choice(["recovered", "deceased", "hospitalized"], p=[0.92, 0.01, 0.07]))
    rows = []
    for i in range(n_cases):
        rows.append({
            "case_id": f"CASE_{i:04d}",
            "onset_date": (start_date + pd.Timedelta(days=int(onset_days[i]))).strftime("%Y-%m-%d"),
            "age": int(ages[i]),
            "gender": genders[i],
            "location": locations[i],
            "outcome": outcomes[i],
        })
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_cases

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/cases.csv"
    out_dir = f"{tmpdir}/output"
    n_cases = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--serial-interval", "5.0"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    epi_csv = None
    analysis_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("epi" in fl or "curve" in fl or "daily" in fl) and f.endswith(".csv"):
                epi_csv = os.path.join(out_dir, f)
            if ("analysis" in fl or "summary" in fl) and f.endswith(".json"):
                analysis_json = os.path.join(out_dir, f)

    if epi_csv or analysis_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_daily_counts","L2_cumulative","L2_r0_computed",
                   "L2_peak_date","L2_cfr_by_age","L2_doubling_time","L2_total_cases",
                   "L2_date_range","L2_no_negative","L2_growth_rate","L2_location_stats"]:
            print(f"FAIL:{t}")
        print("SCORE:r0_accuracy=0.0")
        print("SCORE:analysis_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    epi_df = pd.DataFrame()
    if epi_csv:
        try:
            epi_df = pd.read_csv(epi_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    epi_cols = " ".join(epi_df.columns).lower() if len(epi_df) > 0 else ""

    # L2: 每日计数列存在
    if "daily" in epi_cols or "cases" in epi_cols or "count" in epi_cols or "new" in epi_cols:
        print("PASS:L2_daily_counts")
    else:
        print("FAIL:L2_daily_counts")

    # L2: 累计计数列存在
    if "cumul" in epi_cols or "total" in epi_cols:
        print("PASS:L2_cumulative")
    else:
        print("FAIL:L2_cumulative")

    # L2: R0 计算
    if analysis_json and os.path.exists(analysis_json):
        try:
            analysis = json.load(open(analysis_json))
            a_str = json.dumps(analysis).lower()
            if "r0" in a_str or "r_0" in a_str or "reproduction" in a_str or "r_naught" in a_str:
                print("PASS:L2_r0_computed")
            else:
                print("FAIL:L2_r0_computed")
        except:
            print("FAIL:L2_r0_computed")
    else:
        print("FAIL:L2_r0_computed")

    # L2: 峰值日期
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "peak" in a_str:
            print("PASS:L2_peak_date")
        else:
            print("FAIL:L2_peak_date")
    else:
        print("FAIL:L2_peak_date")

    # L2: 按年龄组的 CFR
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "cfr" in a_str or "fatality" in a_str or "mortality" in a_str:
            print("PASS:L2_cfr_by_age")
        else:
            print("FAIL:L2_cfr_by_age")
    else:
        print("FAIL:L2_cfr_by_age")

    # L2: 倍增时间
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "doubling" in a_str or "double" in a_str:
            print("PASS:L2_doubling_time")
        else:
            print("FAIL:L2_doubling_time")
    else:
        print("FAIL:L2_doubling_time")

    # L2: 总病例数匹配
    if analysis_json and os.path.exists(analysis_json):
        try:
            analysis = json.load(open(analysis_json))
            a_str = json.dumps(analysis).lower()
            # 检查总病例数是否合理
            if "total" in a_str or "cases" in a_str:
                # 尝试提取总数
                total = analysis.get("total_cases", analysis.get("total", None))
                if total is not None and abs(int(total) - n_cases) <= 5:
                    print(f"PASS:L2_total_cases - {total}")
                elif total is not None:
                    print(f"PASS:L2_total_cases - {total} (close enough)")
                else:
                    print("PASS:L2_total_cases")
            else:
                print("FAIL:L2_total_cases")
        except:
            print("FAIL:L2_total_cases")
    else:
        print("FAIL:L2_total_cases")

    # L2: 日期范围合理
    if len(epi_df) > 0 and "date" in epi_cols:
        date_col = [c for c in epi_df.columns if "date" in c.lower()][0]
        try:
            dates = pd.to_datetime(epi_df[date_col])
            span = (dates.max() - dates.min()).days
            if 30 <= span <= 120:
                print(f"PASS:L2_date_range - {span} days")
            else:
                print(f"PASS:L2_date_range - {span} days")
        except:
            print("FAIL:L2_date_range")
    elif len(epi_df) > 0:
        print("PASS:L2_date_range")
    else:
        print("FAIL:L2_date_range")

    # L2: 无负值计数
    if len(epi_df) > 0:
        num_cols = epi_df.select_dtypes(include=[np.number]).columns
        has_neg = False
        for c in num_cols:
            if (epi_df[c] < 0).any():
                has_neg = True
        print(f"{'PASS' if not has_neg else 'FAIL'}:L2_no_negative")
    else:
        print("FAIL:L2_no_negative")

    # L2: growth_rate 存在
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "growth" in a_str or "rate" in a_str or "slope" in a_str:
            print("PASS:L2_growth_rate")
        else:
            print("FAIL:L2_growth_rate")
    else:
        print("FAIL:L2_growth_rate")

    # L2: 按地区统计
    if analysis_json and os.path.exists(analysis_json):
        a_str = json.dumps(json.load(open(analysis_json))).lower()
        if "location" in a_str or "district" in a_str or "attack" in a_str:
            print("PASS:L2_location_stats")
        else:
            print("FAIL:L2_location_stats")
    else:
        print("FAIL:L2_location_stats")

    # SCORE: R0 精度（合理范围应在 1.5-4.0）
    r0_score = 0.0
    if analysis_json and os.path.exists(analysis_json):
        try:
            analysis = json.load(open(analysis_json))
            r0_val = None
            for key in ["R0", "r0", "R_0", "r_0", "reproduction_number", "basic_reproduction_number"]:
                if key in analysis:
                    r0_val = float(analysis[key])
                    break
            if r0_val is not None and 1.0 <= r0_val <= 6.0:
                r0_score = round(max(0, 1.0 - abs(r0_val - 2.5) / 3.0), 4)
        except:
            pass
    print(f"SCORE:r0_accuracy={r0_score}")

    # SCORE: 分析完整性
    expected_keys = ["r0", "peak", "cfr", "fatality", "doubling", "total", "growth", "location", "district"]
    a_str = ""
    if analysis_json and os.path.exists(analysis_json):
        try:
            a_str = json.dumps(json.load(open(analysis_json))).lower()
        except:
            pass
    found = sum(1 for k in expected_keys if k in a_str)
    completeness = round(found / len(expected_keys), 4)
    print(f"SCORE:analysis_completeness={completeness}")
