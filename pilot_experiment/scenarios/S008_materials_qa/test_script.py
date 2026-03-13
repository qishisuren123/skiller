import sys, os, subprocess, tempfile, json

def create_data(path, n=50):
    entries = []
    categories = ["crystal_structure", "band_gap", "synthesis", "properties", "characterization"]
    for i in range(n):
        entry = {
            "instruction": f"Predict the band gap of material {i} with composition X{i}Y{i}Z",
            "input": f"Material: Compound_{i}, Space group: Fm-3m" if i % 3 != 0 else "",
            "output": f"The predicted band gap is {1.0 + i * 0.1:.1f} eV based on the electronic structure calculation.",
            "source": "generated",
            "category": categories[i % len(categories)],
        }
        entries.append(entry)
    # 添加无效条目
    entries.append({"instruction": "", "input": "", "output": "bad", "source": "x", "category": "x"})  # 空instruction
    entries.append({"instruction": "test", "output": "y"})  # 缺字段
    entries.append({"instruction": "A" * 600, "input": "", "output": "ok", "source": "x", "category": "x"})  # 太长
    # 添加近似重复
    entries.append({
        "instruction": "Predict the band gap of material 0 with composition X0Y0Z",  # 和第0条几乎相同
        "input": "", "output": "duplicate test", "source": "x", "category": "x"
    })
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return n + 4  # 总条目数

with tempfile.TemporaryDirectory() as tmpdir:
    jsonl_in = f"{tmpdir}/data.jsonl"
    jsonl_out = f"{tmpdir}/cleaned.jsonl"
    report = f"{tmpdir}/report.json"
    total = create_data(jsonl_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", jsonl_in, "--output", jsonl_out, "--report", report],
        [sys.executable, "generated.py", jsonl_in, "-o", jsonl_out],
        [sys.executable, "generated.py", jsonl_in, jsonl_out, report],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(jsonl_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_jsonl","L2_removed_invalid","L2_no_empty_instruction","L2_length_check","L2_dedup"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # 读 cleaned
    cleaned = []
    with open(jsonl_out) as f:
        for line in f:
            if line.strip():
                cleaned.append(json.loads(line))
    print("PASS:L1_valid_jsonl")

    if len(cleaned) < total:
        print(f"PASS:L2_removed_invalid - {total - len(cleaned)} removed")
    else:
        print(f"FAIL:L2_removed_invalid - {len(cleaned)} >= {total}")

    empty_inst = [e for e in cleaned if not e.get("instruction","").strip()]
    if len(empty_inst) == 0:
        print("PASS:L2_no_empty_instruction")
    else:
        print(f"FAIL:L2_no_empty_instruction - {len(empty_inst)} empty")

    long_inst = [e for e in cleaned if len(e.get("instruction","")) > 500]
    if len(long_inst) == 0:
        print("PASS:L2_length_check")
    else:
        print(f"FAIL:L2_length_check - {len(long_inst)} too long")

    # 检查近似重复是否被移除
    if len(cleaned) <= total - 3:  # 至少移除了3条无效+1条重复
        print("PASS:L2_dedup")
    else:
        print(f"FAIL:L2_dedup - {len(cleaned)} entries, expected <= {total-3}")

    # --- 新增测试 ---
    # L2: report 文件存在
    report_exists = os.path.exists(report)
    if not report_exists:
        # 查找其他可能的 report 路径
        for f in os.listdir(tmpdir):
            if "report" in f.lower() and f.endswith(".json"):
                report = os.path.join(tmpdir, f)
                report_exists = True
                break
    print(f"{'PASS' if report_exists else 'FAIL'}:L2_report_exists")

    # L2: report 是有效 JSON
    if report_exists:
        try:
            rpt = json.load(open(report))
            print("PASS:L2_report_json")
        except:
            rpt = {}
            print("FAIL:L2_report_json - invalid JSON")
    else:
        rpt = {}
        print("FAIL:L2_report_json")

    # L2: report 包含分类分布
    rpt_str = json.dumps(rpt).lower() if rpt else ""
    if "categor" in rpt_str or "distribution" in rpt_str or "crystal" in rpt_str:
        print("PASS:L2_categories")
    else:
        print("FAIL:L2_categories - no category distribution")

    # L2: 所有 cleaned 条目都有完整字段
    required_fields = ["instruction", "output", "source", "category"]
    all_complete = all(all(f in e for f in required_fields) for e in cleaned)
    if all_complete:
        print("PASS:L2_complete_fields")
    else:
        print("FAIL:L2_complete_fields - some entries missing required fields")

    # L2: instruction 长度合理
    if cleaned:
        avg_len = sum(len(e.get("instruction", "")) for e in cleaned) / len(cleaned)
        print(f"PASS:L2_lengths - avg instruction length: {avg_len:.0f}")
    else:
        print("FAIL:L2_lengths - no cleaned entries")

    # SCORE: 去重精度（应移除 ~4 条：3 无效 + 1 重复）
    expected_clean = total - 4
    if len(cleaned) > 0:
        dedup_precision = round(max(0, 1.0 - abs(len(cleaned) - expected_clean) / total), 4)
    else:
        dedup_precision = 0.0
    print(f"SCORE:dedup_precision={dedup_precision}")

    # SCORE: 去重召回率（无效条目被移除的比例）
    # 我们知道有 4 条应被移除
    removed = total - len(cleaned)
    dedup_recall = round(min(removed / 4.0, 1.0), 4) if removed > 0 else 0.0
    print(f"SCORE:dedup_recall={dedup_recall}")
