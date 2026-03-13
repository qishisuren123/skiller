import sys, os, subprocess, tempfile, json
import pandas as pd

def create_data(path, n=20):
    entries = []
    organisms = ["Homo sapiens", "Mus musculus", "Escherichia coli", "Saccharomyces cerevisiae"]
    for i in range(n):
        entry = {
            "accession": [f"P{10000+i}"],
            "id": f"PROT{i}_HUMAN",
            "protein": {"recommendedName": {"fullName": {"value": f"Test protein {i}"}}},
            "gene": [{"name": {"value": f"TP{i}"}}] if i % 3 != 0 else [],
            "organism": {"names": [{"value": organisms[i % len(organisms)]}]},
            "sequence": {"length": 100 + i * 10, "sequence": "M" + "A" * (99 + i * 10)},
            "comments": [{"type": "FUNCTION", "text": [{"value": f"Involved in process {i}"}]}],
            "features": [{"type": "CHAIN"}, {"type": "DOMAIN"}] * (i % 3 + 1),
            "dbReferences": [
                {"type": "GO", "id": f"GO:{7000+i}"},
                {"type": "GO", "id": f"GO:{8000+i}"},
                {"type": "PDB", "id": f"1ABC"},
            ] if i % 2 == 0 else [],
        }
        entries.append(entry)
    json.dump(entries, open(path, "w"), indent=2)
    return n

with tempfile.TemporaryDirectory() as tmpdir:
    json_in = f"{tmpdir}/proteins.json"
    csv_out = f"{tmpdir}/parsed.csv"
    n = create_data(json_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", json_in, "--output", csv_out],
        [sys.executable, "generated.py", json_in, "-o", csv_out],
        [sys.executable, "generated.py", json_in, csv_out],
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
        for t in ["L1_valid_csv","L2_row_count","L2_has_accession","L2_has_name","L2_has_organism","L2_missing_handled"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    try:
        df = pd.read_csv(csv_out)
        print("PASS:L1_valid_csv")
    except:
        print("FAIL:L1_valid_csv")
        sys.exit(0)

    if len(df) == n:
        print(f"PASS:L2_row_count - {n} proteins")
    else:
        print(f"FAIL:L2_row_count - expected {n}, got {len(df)}")

    cols = " ".join(df.columns).lower()
    if "accession" in cols or "acc" in cols:
        print("PASS:L2_has_accession")
    else:
        print("FAIL:L2_has_accession")

    if "name" in cols or "protein" in cols:
        print("PASS:L2_has_name")
    else:
        print("FAIL:L2_has_name")

    if "organism" in cols or "org" in cols or "species" in cols:
        print("PASS:L2_has_organism")
    else:
        print("FAIL:L2_has_organism")

    # 缺失字段处理（gene 每3个缺一次，应该不报错）
    if not df.isnull().all(axis=None):
        print("PASS:L2_missing_handled")
    else:
        print("FAIL:L2_missing_handled - all null")

    # --- 新增测试 ---
    # L2: 序列长度列（应有 sequence_length 或类似列）
    if any("length" in c.lower() or "seq_len" in c.lower() for c in df.columns):
        print("PASS:L2_seq_length")
    else:
        print("FAIL:L2_seq_length - no sequence length column")

    # L2: feature 计数列
    if any("feature" in c.lower() or "n_feat" in c.lower() for c in df.columns):
        print("PASS:L2_feature_count")
    else:
        print("FAIL:L2_feature_count - no feature count column")

    # L2: GO terms 列
    if any("go" in c.lower() for c in df.columns):
        print("PASS:L2_go_terms")
    else:
        print("FAIL:L2_go_terms - no GO terms column")

    # L2: 摘要信息（stdout 应包含统计信息）
    combined_out = r.stdout + r.stderr if hasattr(r, 'stdout') else ""
    if any(kw in combined_out.lower() for kw in ["total", "summary", "protein", "organism", "average"]):
        print("PASS:L2_summary")
    else:
        print("FAIL:L2_summary - no summary output")

    # SCORE: 字段提取率（检查多少关键列被提取）
    expected_fields = ["accession", "name", "organism", "gene", "length", "feature", "go"]
    cols_str = " ".join(df.columns).lower()
    found = sum(1 for f in expected_fields if f in cols_str)
    field_extraction_rate = round(found / len(expected_fields), 4)
    print(f"SCORE:field_extraction_rate={field_extraction_rate}")

    # SCORE: 数据完整性（非空值比例）
    completeness = round(1.0 - df.isnull().mean().mean(), 4)
    print(f"SCORE:completeness={completeness}")
