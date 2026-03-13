import sys, os, json, subprocess, tempfile
import numpy as np
import pandas as pd

def create_data(edges_path, nodes_path, n_nodes=200, n_edges=800):
    np.random.seed(42)
    fields = ["Physics", "Computer Science", "Biology", "Mathematics", "Chemistry"]
    # 生成节点
    nodes = []
    for i in range(n_nodes):
        nodes.append({
            "node_id": f"N{i:04d}",
            "title": f"Paper_{i}_on_{'_'.join(np.random.choice(['Analysis','Theory','Method','Study','Review'], 2))}",
            "field": np.random.choice(fields, p=[0.25, 0.3, 0.2, 0.15, 0.1]),
        })
    pd.DataFrame(nodes).to_csv(nodes_path, index=False)
    # 生成引用边（优先引用同领域、高度数节点）
    node_ids = [f"N{i:04d}" for i in range(n_nodes)]
    node_fields = {n["node_id"]: n["field"] for n in nodes}
    edges = []
    # 先创建一些 hub 节点（被大量引用）
    hub_ids = node_ids[:15]
    for _ in range(n_edges):
        src = np.random.choice(node_ids)
        # 50% 概率引用 hub 节点
        if np.random.rand() < 0.5:
            tgt = np.random.choice(hub_ids)
        else:
            tgt = np.random.choice(node_ids)
        if src != tgt:
            year = np.random.randint(2000, 2024)
            edges.append({
                "source_id": src,
                "target_id": tgt,
                "year": year,
            })
    # 去重
    edge_df = pd.DataFrame(edges).drop_duplicates(subset=["source_id", "target_id"])
    edge_df.to_csv(edges_path, index=False)
    return n_nodes, len(edge_df)

with tempfile.TemporaryDirectory() as tmpdir:
    edges_in = f"{tmpdir}/edges.csv"
    nodes_in = f"{tmpdir}/nodes.csv"
    out_dir = f"{tmpdir}/output"
    n_nodes, n_edges = create_data(edges_in, nodes_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--edges", edges_in, "--nodes", nodes_in, "--output", out_dir],
        [sys.executable, "generated.py", "--input", edges_in, "--nodes", nodes_in, "--output", out_dir],
        [sys.executable, "generated.py", edges_in, nodes_in, "-o", out_dir],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        if r.returncode == 0:
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    # 查找输出文件
    metrics_csv = None
    summary_json = None
    degree_csv = None
    if os.path.exists(out_dir):
        for f in os.listdir(out_dir):
            fl = f.lower()
            if ("metric" in fl or "node" in fl) and f.endswith(".csv") and "degree" not in fl:
                metrics_csv = os.path.join(out_dir, f)
            if ("summary" in fl or "network" in fl) and f.endswith(".json"):
                summary_json = os.path.join(out_dir, f)
            if "degree" in fl and f.endswith(".csv"):
                degree_csv = os.path.join(out_dir, f)

    if metrics_csv or summary_json:
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_csv","L2_all_nodes","L2_in_degree","L2_out_degree",
                   "L2_clustering","L2_community","L2_hub_nodes","L2_network_stats",
                   "L2_degree_dist","L2_density","L2_n_communities","L2_no_nan","L2_summary_exists"]:
            print(f"FAIL:{t}")
        print("SCORE:metric_completeness=0.0")
        print("SCORE:hub_detection_quality=0.0")
        sys.exit(0)

    # L1: 有效 CSV
    m_df = pd.DataFrame()
    if metrics_csv:
        try:
            m_df = pd.read_csv(metrics_csv)
            print("PASS:L1_valid_csv")
        except:
            print("FAIL:L1_valid_csv")
    else:
        print("FAIL:L1_valid_csv")

    mcols = " ".join(m_df.columns).lower() if len(m_df) > 0 else ""

    # L2: 所有节点被处理
    if len(m_df) >= n_nodes * 0.8:
        print(f"PASS:L2_all_nodes - {len(m_df)}/{n_nodes}")
    elif len(m_df) > 0:
        print(f"PASS:L2_all_nodes - {len(m_df)} nodes")
    else:
        print("FAIL:L2_all_nodes")

    # L2: in_degree 列
    if "in_degree" in mcols or "in_deg" in mcols or "indegree" in mcols or "citations" in mcols:
        print("PASS:L2_in_degree")
    else:
        print("FAIL:L2_in_degree")

    # L2: out_degree 列
    if "out_degree" in mcols or "out_deg" in mcols or "outdegree" in mcols or "references" in mcols:
        print("PASS:L2_out_degree")
    else:
        print("FAIL:L2_out_degree")

    # L2: 聚类系数
    if "cluster" in mcols or "cc" in mcols.split() or "clustering" in mcols:
        print("PASS:L2_clustering")
    else:
        print("FAIL:L2_clustering")

    # L2: 社区标签
    if "community" in mcols or "label" in mcols or "group" in mcols or "cluster_id" in mcols:
        print("PASS:L2_community")
    else:
        print("FAIL:L2_community")

    # L2: hub 节点识别（summary 中有 top hubs）
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if "hub" in s_str or "top" in s_str:
                print("PASS:L2_hub_nodes")
            else:
                print("FAIL:L2_hub_nodes")
        except:
            print("FAIL:L2_hub_nodes")
    else:
        print("FAIL:L2_hub_nodes")

    # L2: 网络级统计
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if ("n_nodes" in s_str or "nodes" in s_str) and ("n_edges" in s_str or "edges" in s_str):
                print("PASS:L2_network_stats")
            else:
                print("FAIL:L2_network_stats")
        except:
            print("FAIL:L2_network_stats")
    else:
        print("FAIL:L2_network_stats")

    # L2: 度分布文件
    deg_df = pd.DataFrame()
    if degree_csv:
        try:
            deg_df = pd.read_csv(degree_csv)
        except:
            pass
    if len(deg_df) > 0:
        print(f"PASS:L2_degree_dist - {len(deg_df)} entries")
    else:
        print("FAIL:L2_degree_dist")

    # L2: 密度在 summary 中
    if summary_json and os.path.exists(summary_json):
        s_str = json.dumps(json.load(open(summary_json))).lower()
        if "density" in s_str:
            print("PASS:L2_density")
        else:
            print("FAIL:L2_density")
    else:
        print("FAIL:L2_density")

    # L2: 社区数量
    if summary_json and os.path.exists(summary_json):
        try:
            s = json.load(open(summary_json))
            s_str = json.dumps(s).lower()
            if "communit" in s_str or "n_communit" in s_str or "cluster" in s_str:
                print("PASS:L2_n_communities")
            else:
                print("FAIL:L2_n_communities")
        except:
            print("FAIL:L2_n_communities")
    else:
        print("FAIL:L2_n_communities")

    # L2: 无 NaN
    if len(m_df) > 0:
        nan_ct = m_df.select_dtypes(include=[np.number]).isnull().sum().sum()
        print(f"{'PASS' if nan_ct == 0 else 'FAIL'}:L2_no_nan")
    else:
        print("FAIL:L2_no_nan")

    # L2: summary 文件存在
    if summary_json and os.path.exists(summary_json):
        print("PASS:L2_summary_exists")
    else:
        print("FAIL:L2_summary_exists")

    # SCORE: 指标完整性
    expected_cols = ["in_degree", "out_degree", "clustering", "community", "hub", "density", "degree"]
    all_text = mcols + " "
    if summary_json and os.path.exists(summary_json):
        try:
            all_text += json.dumps(json.load(open(summary_json))).lower()
        except:
            pass
    found = sum(1 for c in expected_cols if c in all_text)
    completeness = round(found / len(expected_cols), 4)
    print(f"SCORE:metric_completeness={completeness}")

    # SCORE: hub 检测质量（前 15 个节点应该被识别为高 in_degree）
    hub_score = 0.0
    if len(m_df) > 0:
        in_col = [c for c in m_df.columns if "in_deg" in c.lower() or "indeg" in c.lower() or "citation" in c.lower()]
        id_col = [c for c in m_df.columns if "node_id" in c.lower() or "id" in c.lower()]
        if in_col and id_col:
            top10 = m_df.nlargest(10, in_col[0])[id_col[0]].astype(str).tolist()
            true_hubs = {f"N{i:04d}" for i in range(15)}
            matched = sum(1 for h in top10 if h in true_hubs)
            hub_score = round(matched / 10.0, 4)
    print(f"SCORE:hub_detection_quality={hub_score}")
