import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(path, n_respondents=120):
    """生成模拟问卷数据：有一定相关结构"""
    np.random.seed(42)
    rows = []
    genders = ["M", "F", "Other"]
    for i in range(n_respondents):
        gender = np.random.choice(genders, p=[0.45, 0.45, 0.1])
        age = np.random.randint(18, 70)
        # 生成有相关性的 Likert 响应
        # Scale A 项目（q1-q5）有一个共同因子
        factor_a = np.random.normal(3.5, 0.8)
        # Scale B 项目（q6-q10）有另一个共同因子
        factor_b = np.random.normal(3.0, 0.9)
        responses = {}
        for q in range(1, 6):
            val = factor_a + np.random.normal(0, 0.7)
            # q3 和 q5 是反向题，生成反向值
            if q in [3, 5]:
                val = 6 - val
            responses[f"q{q}"] = int(np.clip(round(val), 1, 5))
        for q in range(6, 11):
            val = factor_b + np.random.normal(0, 0.8)
            # q7 是反向题
            if q == 7:
                val = 6 - val
            responses[f"q{q}"] = int(np.clip(round(val), 1, 5))
        row = {"respondent_id": f"R{i:04d}", "age": age, "gender": gender}
        row.update(responses)
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)
    return n_respondents

with tempfile.TemporaryDirectory() as tmpdir:
    csv_in = f"{tmpdir}/survey.csv"
    out_dir = f"{tmpdir}/output"
    n_resp = create_data(csv_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir, "--reverse-items", "q3,q5,q7"],
        [sys.executable, "generated.py", csv_in, "-o", out_dir],
        [sys.executable, "generated.py", "--input", csv_in, "--output", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    recoded_csv = None
    reliability_json = None
    group_json = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("recode" in fl or "response" in fl) and f.endswith(".csv"):
                recoded_csv = os.path.join(out_dir, f)
            if "reliab" in fl and f.endswith(".json"):
                reliability_json = os.path.join(out_dir, f)
            if ("group" in fl or "comparison" in fl) and f.endswith(".json"):
                group_json = os.path.join(out_dir, f)

    if recoded_csv or reliability_json or group_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv", "L2_reverse_coded", "L2_reverse_values",
                   "L2_composite_scores", "L2_score_range", "L2_reliability_exists",
                   "L2_alpha_range", "L2_group_comparison", "L2_gender_groups",
                   "L2_all_respondents", "L2_no_nan", "L2_original_preserved"]:
            print(f"FAIL:{t}")
        print("SCORE:alpha_accuracy=0.0")
        print("SCORE:analysis_completeness=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    df = pd.DataFrame()
    if recoded_csv:
        try:
            df = pd.read_csv(recoded_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    cols = " ".join(df.columns).lower() if len(df) > 0 else ""

    # L2: 有反向编码的列
    if "_r" in cols or "reverse" in cols or "recode" in cols:
        print("PASS:L2_reverse_coded")
    else:
        # 也可能直接覆盖了原始列
        print("FAIL:L2_reverse_coded")

    # L2: 反向编码的值正确 (6 - original)
    orig = pd.read_csv(csv_in)
    reverse_ok = False
    if len(df) > 0:
        # 查找反向编码列
        for rc in ["q3_r", "q3_reverse", "q3_recoded"]:
            if rc in df.columns:
                expected = 6 - orig["q3"].values
                actual = df[rc].values[:len(expected)]
                if np.allclose(expected, actual, atol=0.01):
                    reverse_ok = True
                break
        # 也检查是否直接修改了 q3 列
        if not reverse_ok and "q3" in df.columns:
            if not np.allclose(df["q3"].values, orig["q3"].values):
                # 检查是否是 6-x 关系
                if np.allclose(df["q3"].values, 6 - orig["q3"].values, atol=0.01):
                    reverse_ok = True
    if reverse_ok:
        print("PASS:L2_reverse_values")
    else:
        print("FAIL:L2_reverse_values")

    # L2: 有复合得分列
    if "scale_a" in cols or "composite" in cols or "score_a" in cols or "scale" in cols:
        print("PASS:L2_composite_scores")
    else:
        print("FAIL:L2_composite_scores")

    # L2: 复合得分范围合理 (1-5)
    score_cols = [c for c in df.columns if "scale" in c.lower() or "composite" in c.lower() or "score" in c.lower()]
    if score_cols:
        all_in_range = True
        for sc in score_cols:
            vals = df[sc].dropna()
            if len(vals) > 0 and (vals.min() < 0.5 or vals.max() > 5.5):
                all_in_range = False
        if all_in_range:
            print("PASS:L2_score_range")
        else:
            print("FAIL:L2_score_range")
    else:
        print("FAIL:L2_score_range")

    # L2: 信度文件存在
    reliability = {}
    if reliability_json and os.path.exists(reliability_json):
        try:
            reliability = json.load(open(reliability_json))
            print("PASS:L2_reliability_exists")
        except:
            print("FAIL:L2_reliability_exists")
    else:
        print("FAIL:L2_reliability_exists")

    # L2: alpha 值范围合理 (0-1)
    r_str = json.dumps(reliability).lower() if reliability else ""
    alphas = []
    if "alpha" in r_str:
        # 提取 alpha 值
        def find_alphas(d):
            result = []
            if isinstance(d, dict):
                for k, v in d.items():
                    if "alpha" in k.lower():
                        try:
                            result.append(float(v))
                        except:
                            pass
                    elif isinstance(v, dict):
                        result.extend(find_alphas(v))
            return result
        alphas = find_alphas(reliability)
    if alphas and all(0 <= a <= 1 for a in alphas):
        print(f"PASS:L2_alpha_range - alphas={alphas}")
    elif alphas:
        print(f"FAIL:L2_alpha_range - alphas={alphas}")
    else:
        print("FAIL:L2_alpha_range")

    # L2: 组间比较文件存在
    group_data = {}
    if group_json and os.path.exists(group_json):
        try:
            group_data = json.load(open(group_json))
            print("PASS:L2_group_comparison")
        except:
            print("FAIL:L2_group_comparison")
    else:
        print("FAIL:L2_group_comparison")

    # L2: 有性别分组
    g_str = json.dumps(group_data).lower() if group_data else ""
    if ("m" in g_str or "male" in g_str or "f" in g_str or "female" in g_str) and len(group_data) >= 2:
        print("PASS:L2_gender_groups")
    elif len(group_data) >= 2:
        print("PASS:L2_gender_groups")
    else:
        print("FAIL:L2_gender_groups")

    # L2: 所有受访者保留
    if len(df) >= n_resp:
        print(f"PASS:L2_all_respondents - {len(df)}/{n_resp}")
    elif len(df) >= n_resp * 0.9:
        print(f"PASS:L2_all_respondents - {len(df)}/{n_resp}")
    else:
        print(f"FAIL:L2_all_respondents - {len(df)}/{n_resp}")

    # L2: 无 NaN
    if len(df) > 0:
        nan_count = df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_count == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: 原始数据列保留
    if len(df) > 0 and "respondent_id" in df.columns and "age" in df.columns:
        print("PASS:L2_original_preserved")
    elif len(df) > 0 and len(df.columns) >= 12:
        print("PASS:L2_original_preserved")
    else:
        print("FAIL:L2_original_preserved")

    # SCORE: alpha 精度（手动计算并比较）
    alpha_accuracy = 0.0
    if len(orig) > 0:
        # 手动计算 Scale A 的 Cronbach's alpha（反向编码后）
        items_a = orig[["q1", "q2", "q3", "q4", "q5"]].copy()
        items_a["q3"] = 6 - items_a["q3"]
        items_a["q5"] = 6 - items_a["q5"]
        k = 5
        item_vars = items_a.var(ddof=1)
        total_var = items_a.sum(axis=1).var(ddof=1)
        if total_var > 0:
            expected_alpha_a = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
        else:
            expected_alpha_a = 0

        if alphas:
            # 找最接近的 alpha 值
            best_match = min(alphas, key=lambda a: abs(a - expected_alpha_a))
            error = abs(best_match - expected_alpha_a)
            alpha_accuracy = round(max(0, 1.0 - error / 0.3), 4)
    print(f"SCORE:alpha_accuracy={alpha_accuracy}")

    # SCORE: 分析完整性
    features = ["reverse", "scale", "alpha", "group", "mean", "std"]
    all_str = cols + " " + r_str + " " + g_str
    found = sum(1 for f in features if f in all_str)
    analysis_completeness = round(found / len(features), 4)
    print(f"SCORE:analysis_completeness={analysis_completeness}")
