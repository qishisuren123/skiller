"""评估生成代码的质量：运行 + 自动断言检查"""
import json
import subprocess
import tempfile
import traceback
from pathlib import Path


def run_generated_code(code: str, test_script: str, timeout: int = 60) -> dict:
    """
    将生成的代码保存为临时文件，然后运行 test_script 来检验。
    test_script 会 import 生成的代码并执行断言。
    返回 {passed: bool, n_pass: int, n_total: int, details: [...], error: str|None}
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入生成的代码
        code_path = Path(tmpdir) / "generated.py"
        code_path.write_text(code)

        # 写入测试脚本
        test_path = Path(tmpdir) / "test_check.py"
        test_path.write_text(test_script)

        try:
            result = subprocess.run(
                ["python", str(test_path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=tmpdir,
                env={
                    "PATH": "/home/renyiming/.conda/envs/pilot_exp/bin:/root/miniconda3/envs/pilot_exp/bin:/usr/bin:/bin",
                    "HOME": tmpdir,
                    "PYTHONPATH": tmpdir,
                    "TMPDIR": tmpdir,
                }
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            # 解析测试输出（约定格式：每行 PASS:xxx 或 FAIL:xxx）
            details = []
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

            return {
                "passed": n_pass == n_total and n_total > 0,
                "n_pass": n_pass,
                "n_total": n_total,
                "details": details,
                "returncode": result.returncode,
                "stdout": stdout[-2000:],  # 截断
                "stderr": stderr[-2000:],
                "error": None if result.returncode == 0 else stderr[-500:],
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False, "n_pass": 0, "n_total": 0,
                "details": [], "returncode": -1,
                "stdout": "", "stderr": "TIMEOUT",
                "error": "Execution timed out after 60s",
            }
        except Exception as e:
            return {
                "passed": False, "n_pass": 0, "n_total": 0,
                "details": [], "returncode": -1,
                "stdout": "", "stderr": str(e),
                "error": traceback.format_exc(),
            }
