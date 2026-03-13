"""
通用评估框架 v2：4层评估体系
Layer 1: Execution — 代码能否运行
Layer 2: Functional Correctness — 输出是否正确
Layer 3: LLM-as-Judge — 代码质量评分（见 llm_judge.py）
Layer 4: Code Metrics — 量化指标（行数、复杂度、防御性编码）
"""
import json
import subprocess
import tempfile
import traceback
import re
import os
import ast
from pathlib import Path


def classify_error(returncode: int, stdout: str, stderr: str, n_pass: int, n_total: int) -> str:
    """
    将执行失败分为 7 类错误类型：
    - success: 全部通过
    - syntax_error: 语法错误（代码无法解析）
    - import_error: 导入模块失败
    - runtime_error: 运行时异常（包括 TypeError, ValueError 等）
    - timeout: 超时
    - logic_error: 代码运行成功但测试不通过（逻辑错误）
    - format_error: 输出格式不符合预期
    """
    if stderr == "TIMEOUT":
        return "timeout"
    if n_pass == n_total and n_total > 0:
        return "success"
    stderr_lower = stderr.lower() if stderr else ""
    # 语法错误
    if "syntaxerror" in stderr_lower or "indentationerror" in stderr_lower:
        return "syntax_error"
    # 导入错误
    if "modulenotfounderror" in stderr_lower or "importerror" in stderr_lower:
        return "import_error"
    # 运行时错误（代码本身崩溃）
    runtime_keywords = ["traceback", "error", "exception", "typeerror", "valueerror",
                        "keyerror", "indexerror", "attributeerror", "filenotfounderror",
                        "zerodivisionerror", "oserror", "ioerror", "runtimeerror"]
    if returncode != 0 and any(kw in stderr_lower for kw in runtime_keywords):
        return "runtime_error"
    # 格式错误（代码运行了但输出格式不对，导致测试脚本解析失败）
    if n_total == 0 and returncode == 0:
        return "format_error"
    # 逻辑错误（代码运行了，测试也解析了，但不全通过）
    if n_total > 0 and n_pass < n_total:
        return "logic_error"
    # 兜底
    if returncode != 0:
        return "runtime_error"
    return "format_error"


def run_generated_code(code: str, test_script: str, timeout: int = 90) -> dict:
    """
    执行验证：将生成的代码和测试脚本都写入临时目录运行。
    测试脚本输出约定格式：
      PASS:<test_name> [detail]
      FAIL:<test_name> [detail]
      SCORE:<metric_name>=<value>
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = Path(tmpdir) / "generated.py"
        code_path.write_text(code)
        test_path = Path(tmpdir) / "test_check.py"
        test_path.write_text(test_script)

        try:
            result = subprocess.run(
                ["python", str(test_path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=tmpdir,
                env={
                    "PATH": "/home/renyiming/.conda/envs/pilot_exp/bin:"
                            "/root/miniconda3/envs/pilot_exp/bin:/usr/bin:/bin",
                    "HOME": tmpdir,
                    "PYTHONPATH": tmpdir,
                    "TMPDIR": tmpdir,
                    "HDF5_USE_FILE_LOCKING": "FALSE",
                }
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            details = []
            scores = {}
            n_pass = 0
            n_total = 0
            for line in stdout.split("\n"):
                line = line.strip()
                if line.startswith("PASS:"):
                    details.append({"test": line[5:].strip(), "pass": True})
                    n_pass += 1
                    n_total += 1
                elif line.startswith("FAIL:"):
                    details.append({"test": line[5:].strip(), "pass": False})
                    n_total += 1
                elif line.startswith("SCORE:"):
                    kv = line[6:].strip()
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        try:
                            scores[k.strip()] = float(v.strip())
                        except ValueError:
                            scores[k.strip()] = v.strip()

            error_type = classify_error(result.returncode, stdout, stderr, n_pass, n_total)
            return {
                "passed": n_pass == n_total and n_total > 0,
                "n_pass": n_pass,
                "n_total": n_total,
                "pass_rate": round(n_pass / n_total, 4) if n_total > 0 else 0,
                "details": details,
                "scores": scores,
                "error_type": error_type,
                "returncode": result.returncode,
                "stdout": stdout[-3000:],
                "stderr": stderr[-2000:],
                "error": None if result.returncode == 0 else stderr[-500:],
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False, "n_pass": 0, "n_total": 0, "pass_rate": 0,
                "details": [], "scores": {}, "error_type": "timeout",
                "returncode": -1,
                "stdout": "", "stderr": "TIMEOUT",
                "error": f"Execution timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "passed": False, "n_pass": 0, "n_total": 0, "pass_rate": 0,
                "details": [], "scores": {}, "error_type": "runtime_error",
                "returncode": -1,
                "stdout": "", "stderr": str(e),
                "error": traceback.format_exc()[-500:],
            }


def compute_code_metrics(code: str) -> dict:
    """Layer 4: 代码量化指标"""
    lines = code.split("\n")
    non_empty = [l for l in lines if l.strip()]
    comments = [l for l in lines if l.strip().startswith("#")]

    # try/except 计数（过度防御指标）
    try_count = len(re.findall(r'\btry\s*:', code))
    except_count = len(re.findall(r'\bexcept\b', code))

    # import 计数
    imports = len(re.findall(r'^(?:import |from \S+ import )', code, re.MULTILINE))

    # 函数/类计数
    functions = len(re.findall(r'^def \w+', code, re.MULTILINE))
    classes = len(re.findall(r'^class \w+', code, re.MULTILINE))

    # 是否有 argparse
    has_argparse = "argparse" in code or "ArgumentParser" in code

    # 是否有 if __name__
    has_main_guard = 'if __name__' in code

    return {
        "total_lines": len(lines),
        "non_empty_lines": len(non_empty),
        "comment_lines": len(comments),
        "comment_ratio": round(len(comments) / max(len(non_empty), 1), 3),
        "try_except_count": try_count,
        "import_count": imports,
        "function_count": functions,
        "class_count": classes,
        "has_argparse": has_argparse,
        "has_main_guard": has_main_guard,
        "defensive_ratio": round(try_count / max(functions, 1), 3),
    }
