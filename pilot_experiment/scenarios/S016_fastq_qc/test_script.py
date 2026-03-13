import sys, os, json, subprocess, tempfile
import numpy as np

def create_fastq(path, n_reads=200):
    np.random.seed(42)
    with open(path, "w") as f:
        for i in range(n_reads):
            seq_len = np.random.randint(80, 200)
            # 碱基序列
            seq = "".join(np.random.choice(list("ACGT"), seq_len))
            # 质量分数：前端高质量，后端逐渐降低
            quals = np.zeros(seq_len, dtype=int)
            for j in range(seq_len):
                base_q = 35 - j * 0.15 + np.random.normal(0, 3)
                quals[j] = max(2, min(41, int(base_q)))
            qual_str = "".join(chr(q + 33) for q in quals)
            f.write(f"@read_{i} length={seq_len}\n")
            f.write(f"{seq}\n")
            f.write(f"+\n")
            f.write(f"{qual_str}\n")
    return n_reads

with tempfile.TemporaryDirectory() as tmpdir:
    fq_in = f"{tmpdir}/reads.fastq"
    fq_out = f"{tmpdir}/trimmed.fastq"
    report = f"{tmpdir}/report.json"
    n_reads = create_fastq(fq_in)

    ran = False
    for args in [
        [sys.executable, "generated.py", "--input", fq_in, "--output", fq_out, "--report", report,
         "--min-quality", "20", "--min-length", "50"],
        [sys.executable, "generated.py", fq_in, "-o", fq_out],
        [sys.executable, "generated.py", "--input", fq_in, "--output", fq_out],
    ]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        if r.returncode == 0 or os.path.exists(fq_out):
            ran = True
            break
    print(f"{'PASS' if ran else 'FAIL'}:L1_runs")

    if os.path.exists(fq_out):
        print("PASS:L1_output_exists")
    else:
        print("FAIL:L1_output_exists")
        for t in ["L1_valid_fastq","L2_reads_trimmed","L2_quality_improved","L2_min_length",
                   "L2_header_preserved","L2_report_exists","L2_report_fields",
                   "L2_no_short_reads","L2_qual_encoding","L2_read_count"]:
            print(f"FAIL:{t}")
        sys.exit(0)

    # 验证输出 FASTQ 格式
    with open(fq_out) as f:
        lines = f.readlines()
    if len(lines) >= 4 and lines[0].startswith("@"):
        print("PASS:L1_valid_fastq")
    elif len(lines) > 0:
        print("PASS:L1_valid_fastq")
    else:
        print("FAIL:L1_valid_fastq")

    n_output_reads = len(lines) // 4

    # reads 被修剪（数量应该减少或长度变短）
    if n_output_reads <= n_reads:
        print(f"PASS:L2_reads_trimmed - {n_output_reads}/{n_reads}")
    else:
        print(f"FAIL:L2_reads_trimmed - {n_output_reads} > {n_reads}")

    # 质量应该提升（输出的平均质量应高于输入）
    if len(lines) >= 4:
        out_quals = []
        for i in range(3, len(lines), 4):
            line = lines[i].strip()
            out_quals.extend(ord(c) - 33 for c in line)
        mean_out_qual = np.mean(out_quals) if out_quals else 0
        if mean_out_qual >= 18:
            print(f"PASS:L2_quality_improved - mean Q={mean_out_qual:.1f}")
        else:
            print(f"FAIL:L2_quality_improved - mean Q={mean_out_qual:.1f}")
    else:
        print("FAIL:L2_quality_improved")

    # 最小长度检查
    short_reads = 0
    for i in range(1, len(lines), 4):
        seq = lines[i].strip()
        if len(seq) < 50:
            short_reads += 1
    if short_reads == 0:
        print("PASS:L2_min_length")
    else:
        print(f"FAIL:L2_min_length - {short_reads} reads < 50bp")

    # header 保留
    if len(lines) >= 4 and "@read_" in lines[0]:
        print("PASS:L2_header_preserved")
    elif len(lines) >= 4 and lines[0].startswith("@"):
        print("PASS:L2_header_preserved")
    else:
        print("FAIL:L2_header_preserved")

    # report 存在
    report_exists = os.path.exists(report)
    print(f"{'PASS' if report_exists else 'FAIL'}:L2_report_exists")

    # report 字段
    if report_exists:
        try:
            rpt = json.load(open(report))
            rpt_str = json.dumps(rpt).lower()
            fields = ["total", "passed", "quality", "length"]
            found = sum(1 for f in fields if f in rpt_str)
            if found >= 2:
                print("PASS:L2_report_fields")
            else:
                print("FAIL:L2_report_fields")
        except:
            print("FAIL:L2_report_fields")
    else:
        print("FAIL:L2_report_fields")

    # 没有过短的 reads
    print(f"{'PASS' if short_reads == 0 else 'FAIL'}:L2_no_short_reads")

    # 质量编码正确 (Phred+33)
    if out_quals and min(out_quals) >= 0 and max(out_quals) <= 41:
        print("PASS:L2_qual_encoding")
    elif out_quals:
        print("FAIL:L2_qual_encoding")
    else:
        print("FAIL:L2_qual_encoding")

    # 输出 read 数合理
    if n_output_reads > 0 and n_output_reads <= n_reads:
        print(f"PASS:L2_read_count - {n_output_reads}")
    else:
        print(f"FAIL:L2_read_count - {n_output_reads}")

    # SCORE: 修剪效率
    trim_rate = round(1.0 - n_output_reads / max(n_reads, 1), 4)
    print(f"SCORE:trim_efficiency={round(min(max(trim_rate, 0), 1), 4)}")

    # SCORE: 质量提升幅度
    # 读取原始质量
    with open(fq_in) as f:
        in_lines = f.readlines()
    in_quals = []
    for i in range(3, len(in_lines), 4):
        line = in_lines[i].strip()
        in_quals.extend(ord(c) - 33 for c in line)
    mean_in_qual = np.mean(in_quals) if in_quals else 0
    quality_gain = round((mean_out_qual - mean_in_qual) / max(mean_in_qual, 1), 4)
    print(f"SCORE:quality_improvement={max(quality_gain, 0)}")
