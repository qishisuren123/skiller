"""
3 个 few-shot 范例，用于 baseline 实验中的 few_shot_1 和 few_shot_3 条件。
这些范例不与 S01-S10 重叠，但属于类似的科学数据处理领域。
"""

# 范例 1: 气象站数据格式转换（类似 S09 但不同任务）
EXAMPLE_1 = {
    "task": """Convert a set of weather station JSON files into a unified Parquet file.
Each JSON has: station_id, readings (list of {timestamp, wind_speed, wind_direction}).
Output: a Parquet file with columns station_id, timestamp, wind_speed, wind_direction, sorted by timestamp.""",

    "solution": """```python
import argparse
import json
import pandas as pd
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    all_rows = []
    for f in Path(args.input_dir).glob("*.json"):
        data = json.loads(f.read_text())
        sid = data["station_id"]
        for r in data["readings"]:
            all_rows.append({
                "station_id": sid,
                "timestamp": pd.Timestamp(r["timestamp"]),
                "wind_speed": float(r["wind_speed"]),
                "wind_direction": float(r["wind_direction"]),
            })

    df = pd.DataFrame(all_rows).sort_values("timestamp").reset_index(drop=True)
    df.to_parquet(args.output, index=False)
    print(f"Wrote {len(df)} rows from {df['station_id'].nunique()} stations")

if __name__ == "__main__":
    main()
```""",
}

# 范例 2: 基因组 BED 文件区间合并（类似 S06 但完全不同操作）
EXAMPLE_2 = {
    "task": """Merge overlapping genomic intervals from a BED file.
Input: tab-separated BED file with columns chrom, start, end, name, score.
Output: merged BED file where overlapping intervals on the same chromosome are combined.
Print: number of intervals before and after merging.""",

    "solution": """```python
import argparse
import pandas as pd

def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input, sep="\\t", header=None,
                     names=["chrom", "start", "end", "name", "score"])
    n_before = len(df)

    results = []
    for chrom, group in df.groupby("chrom"):
        intervals = list(zip(group["start"], group["end"]))
        for start, end in merge_intervals(intervals):
            results.append({"chrom": chrom, "start": start, "end": end})

    out_df = pd.DataFrame(results)
    out_df.to_csv(args.output, sep="\\t", header=False, index=False)
    print(f"Merged {n_before} -> {len(out_df)} intervals")

if __name__ == "__main__":
    main()
```""",
}

# 范例 3: 图像数据增强统计（类似 S10 但不同任务）
EXAMPLE_3 = {
    "task": """Analyze a directory of microscopy images and generate augmentation statistics.
Input: directory of .tif images.
Output: JSON report with per-image stats (mean intensity, std, dimensions) and
dataset-level summary (total images, intensity distribution, size distribution).""",

    "solution": """```python
import argparse
import json
import numpy as np
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    from PIL import Image
    stats = []
    for img_path in sorted(Path(args.input_dir).glob("*.tif")):
        img = np.array(Image.open(img_path))
        stats.append({
            "filename": img_path.name,
            "shape": list(img.shape),
            "mean_intensity": float(np.mean(img)),
            "std_intensity": float(np.std(img)),
            "min": int(np.min(img)),
            "max": int(np.max(img)),
        })

    report = {
        "total_images": len(stats),
        "per_image": stats,
        "summary": {
            "mean_intensity": float(np.mean([s["mean_intensity"] for s in stats])) if stats else 0,
            "mean_std": float(np.mean([s["std_intensity"] for s in stats])) if stats else 0,
        },
    }
    Path(args.output).write_text(json.dumps(report, indent=2))
    print(f"Analyzed {len(stats)} images, mean intensity={report['summary']['mean_intensity']:.1f}")

if __name__ == "__main__":
    main()
```""",
}

# 导出
FEW_SHOT_EXAMPLES = [EXAMPLE_1, EXAMPLE_2, EXAMPLE_3]


def format_few_shot(n: int = 1) -> str:
    """格式化 few-shot 范例为 prompt 文本"""
    examples = FEW_SHOT_EXAMPLES[:n]
    parts = []
    for i, ex in enumerate(examples):
        parts.append(f"## Example {i+1}\n\n**Task:** {ex['task']}\n\n**Solution:**\n{ex['solution']}")
    header = "Here are some examples of similar data processing tasks and their solutions:\n\n"
    footer = "\n\nNow solve the following task using a similar approach:\n\n"
    return header + "\n\n---\n\n".join(parts) + footer
