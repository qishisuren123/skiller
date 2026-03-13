"""
Skill Mutator: 向 skill 文本注入特定错误 (RQ2: Error Tolerance)。

5 种错误注入类型：
1. stale_api: 替换当前 API 为废弃版本
2. wrong_default: 改关键参数默认值
3. missing_edge_case: 删除某个 pitfall 段落
4. wrong_import: 替换 import 为不可用包
5. logic_error: 引入隐蔽算法错误

所有操作在序列化文本上进行，不改原始文件。
"""
import re
import random
from typing import Optional


# ============ 错误注入规则库 ============

# stale_api: 新旧 API 替换对（新→旧）
STALE_API_RULES = [
    # pandas
    ("df.ffill()", "df.fillna(method='ffill')"),
    ("df.bfill()", "df.fillna(method='bfill')"),
    (".to_frame()", ".reset_index()"),
    ("pd.concat(", "pd.append("),
    # numpy
    ("np.concatenate(", "np.append("),
    ("rng = np.random.default_rng(", "np.random.seed("),
    # scipy
    ("from scipy.signal import butter, sosfilt", "from scipy.signal import butter, lfilter"),
    ("sosfilt(sos,", "lfilter(b, a,"),
    # h5py
    ('with h5py.File(', 'f = h5py.File('),
    # matplotlib
    ("fig, ax = plt.subplots(", "fig = plt.figure("),
    # 标准库
    ("pathlib.Path(", "os.path.join("),
    ("json.loads(path.read_text())", "json.load(open(path))"),
]

# wrong_default: 参数默认值替换对
WRONG_DEFAULT_RULES = [
    # scipy.signal
    (r"butter\((\d+),", lambda m: f"butter(20,"),         # order 改为过高
    (r"order\s*=\s*\d+", "order=20"),
    # numpy
    (r"ddof\s*=\s*1", "ddof=0"),                          # 无偏→有偏
    (r"axis\s*=\s*0", "axis=1"),                           # 轴方向错误
    (r"keepdims\s*=\s*True", "keepdims=False"),
    # pandas
    (r"how\s*=\s*['\"]inner['\"]", "how='outer'"),
    (r"dropna\(\)", "dropna(how='all')"),
    # 通用
    (r"encoding\s*=\s*['\"]utf-8['\"]", "encoding='ascii'"),
    (r"timeout\s*=\s*\d+", "timeout=1"),                   # 超时设太短
]

# wrong_import: 替换已知可用的 import 为不可用的
WRONG_IMPORT_RULES = [
    ("import json", "import ujson as json"),
    ("import csv", "import unicodecsv as csv"),
    ("from scipy.io import loadmat", "from scipy.io import mmread as loadmat"),
    ("import h5py", "import hdf5storage as h5py"),
    ("from PIL import Image", "from cv2 import Image"),
    ("import yaml", "import ruamel.yaml as yaml"),
]

# logic_error: 隐蔽的逻辑错误
LOGIC_ERROR_RULES = [
    # off-by-one
    ("range(len(data))", "range(len(data)-1)"),
    ("range(n_trials)", "range(n_trials-1)"),
    ("range(len(files))", "range(len(files)-1)"),
    # 边界条件反转
    (">= 0", "> 0"),
    ("<= 0", "< 0"),
    # 索引错误
    ("[:, 0]", "[:, -1]"),
    ("[0, :]", "[-1, :]"),
    # 排序方向
    ("ascending=True", "ascending=False"),
    ("reverse=False", "reverse=True"),
    # 数学错误
    ("/ n", "/ (n - 1)"),
    ("* 2", "* 2.0 + 1"),
]


def mutate_skill(skill_text: str, mutation_type: str,
                 seed: Optional[int] = None, max_mutations: int = 3) -> tuple[str, list[str]]:
    """
    向 skill 文本注入特定类型的错误。

    参数:
        skill_text: 原始 skill 文本
        mutation_type: 错误类型 (stale_api, wrong_default, missing_edge_case, wrong_import, logic_error)
        seed: 随机种子（可复现）
        max_mutations: 最多注入几处错误

    返回:
        (mutated_text, list_of_changes): 变异后的文本和变更记录
    """
    if seed is not None:
        random.seed(seed)

    changes = []
    mutated = skill_text

    if mutation_type == "stale_api":
        # 替换当前 API 为废弃版本
        applicable = [(old, new) for old, new in STALE_API_RULES if old in mutated]
        random.shuffle(applicable)
        for old, new in applicable[:max_mutations]:
            mutated = mutated.replace(old, new, 1)
            changes.append(f"stale_api: '{old}' → '{new}'")

    elif mutation_type == "wrong_default":
        # 改关键参数默认值
        for pattern, replacement in WRONG_DEFAULT_RULES:
            matches = re.findall(pattern, mutated)
            if matches and len(changes) < max_mutations:
                old_match = re.search(pattern, mutated).group()
                if callable(replacement):
                    new_val = replacement(re.search(pattern, mutated))
                else:
                    new_val = replacement
                mutated = re.sub(pattern, new_val, mutated, count=1)
                changes.append(f"wrong_default: '{old_match}' → '{new_val}'")

    elif mutation_type == "missing_edge_case":
        # 删除 pitfall/warning 段落
        sections = re.split(r'(\n## [^\n]+)', mutated)
        pitfall_kw = ["pitfall", "warning", "edge case", "gotcha", "caveat",
                      "common issue", "important note"]
        removed = 0
        new_sections = []
        skip_next_content = False
        for i, section in enumerate(sections):
            is_header = section.strip().startswith("## ")
            if is_header and any(kw in section.lower() for kw in pitfall_kw):
                if removed < max_mutations:
                    changes.append(f"missing_edge_case: removed section '{section.strip()}'")
                    removed += 1
                    skip_next_content = True
                    continue
            if skip_next_content and not is_header:
                skip_next_content = False
                continue
            skip_next_content = False
            new_sections.append(section)
        mutated = "".join(new_sections)

    elif mutation_type == "wrong_import":
        # 替换 import 为不可用包
        applicable = [(old, new) for old, new in WRONG_IMPORT_RULES if old in mutated]
        random.shuffle(applicable)
        for old, new in applicable[:max_mutations]:
            mutated = mutated.replace(old, new, 1)
            changes.append(f"wrong_import: '{old}' → '{new}'")

    elif mutation_type == "logic_error":
        # 引入隐蔽算法错误
        applicable = [(old, new) for old, new in LOGIC_ERROR_RULES if old in mutated]
        random.shuffle(applicable)
        for old, new in applicable[:max_mutations]:
            mutated = mutated.replace(old, new, 1)
            changes.append(f"logic_error: '{old}' → '{new}'")

    else:
        raise ValueError(f"未知错误类型: {mutation_type}，"
                         f"可选: stale_api, wrong_default, missing_edge_case, wrong_import, logic_error")

    return mutated, changes


# 所有可用的错误注入类型
MUTATION_TYPES = ["stale_api", "wrong_default", "missing_edge_case", "wrong_import", "logic_error"]
