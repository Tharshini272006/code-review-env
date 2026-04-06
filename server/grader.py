# server/grader.py
import ast
import sys
import io
import builtins
from typing import Any, Dict, List, Optional, Tuple
from server.tasks import Task, TestCase

BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "requests", "importlib",
    "builtins", "ctypes", "multiprocessing", "threading",
}

def _check_safety(code: str) -> Optional[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                if name in BLOCKED_IMPORTS:
                    return f"SecurityError: import of '{name}' is not allowed."
    return None

def _run_with_timeout(fn, timeout_seconds: int = 5):
    try:
        result = fn()
        return result, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def execute_code(code: str, function_name: str, test_cases: List[TestCase], timeout: int = 5) -> Dict:
    safety_err = _check_safety(code)
    if safety_err:
        return {"executes": False, "exec_error": safety_err, "stdout": "",
                "results": [], "tests_passed": 0, "total_tests": len(test_cases)}
    try:
        compiled = compile(code, "<submitted>", "exec")
    except SyntaxError as e:
        return {"executes": False, "exec_error": f"SyntaxError: {e}", "stdout": "",
                "results": [], "tests_passed": 0, "total_tests": len(test_cases)}

    safe_builtins = {k: getattr(builtins, k) for k in dir(builtins)
                     if k not in ("__import__", "open", "exec", "eval",
                                  "compile", "input", "breakpoint", "quit", "exit")}

    namespace: Dict[str, Any] = {"__builtins__": safe_builtins}
    captured_stdout = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_stdout
    try:
        exec(compiled, namespace)
        sys.stdout = old_stdout
    except Exception as e:
        sys.stdout = old_stdout
        return {"executes": False, "exec_error": f"{type(e).__name__}: {e}",
                "stdout": captured_stdout.getvalue(), "results": [],
                "tests_passed": 0, "total_tests": len(test_cases)}

    if function_name not in namespace:
        return {"executes": False, "exec_error": f"Function '{function_name}' not found.",
                "stdout": captured_stdout.getvalue(), "results": [],
                "tests_passed": 0, "total_tests": len(test_cases)}

    fn = namespace[function_name]
    results = []
    for tc in test_cases:
        def _call(tc=tc):
            return fn(*tc.args, **tc.kwargs)
        got, err = _run_with_timeout(_call, timeout_seconds=timeout)
        if err is not None:
            results.append({"passed": False, "expected": tc.expected, "got": None,
                            "error": err, "description": tc.description})
        else:
            results.append({"passed": got == tc.expected, "expected": tc.expected,
                            "got": got, "error": None, "description": tc.description})

    tests_passed = sum(1 for r in results if r["passed"])
    return {"executes": True, "exec_error": None, "stdout": captured_stdout.getvalue(),
            "results": results, "tests_passed": tests_passed, "total_tests": len(test_cases)}

def check_code_quality(code: str) -> Dict:
    has_validation = False
    no_magic = True
    has_docstring = False
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"has_input_validation": False, "no_magic_numbers": False,
                "has_docstring": False, "quality_score": 0.0}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                has_docstring = True
        if isinstance(node, ast.Raise):
            has_validation = True
        if isinstance(node, ast.If):
            has_validation = True
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            if node.value > 2:
                no_magic = False
    score = (0.35 if has_validation else 0.0) + (0.40 if no_magic else 0.0) + (0.25 if has_docstring else 0.0)
    return {"has_input_validation": has_validation, "no_magic_numbers": no_magic,
            "has_docstring": has_docstring, "quality_score": round(score, 3)}

ATTEMPT_PENALTY = 0.90

def _attempt_multiplier(attempt_number: int) -> float:
    return ATTEMPT_PENALTY ** max(0, attempt_number - 1)

def compute_reward_easy(exec_result: Dict, attempt_number: int = 1) -> Tuple[float, str]:
    reward = 0.0
    breakdown = []
    if exec_result["executes"]:
        reward += 0.20
        breakdown.append("executes(+0.20)")
    else:
        breakdown.append(f"exec_failed: {exec_result['exec_error']}")
        return 0.0, " | ".join(breakdown)
    n = exec_result["total_tests"]
    passed = exec_result["tests_passed"]
    test_reward = (passed / n) * 0.80 if n > 0 else 0.0
    reward += test_reward
    breakdown.append(f"tests {passed}/{n}(+{test_reward:.2f})")
    reward = min(1.0, reward) * _attempt_multiplier(attempt_number)
    return round(min(1.0, reward), 4), " | ".join(breakdown)

def compute_reward_medium(exec_result: Dict, attempt_number: int = 1) -> Tuple[float, str]:
    reward = 0.0
    breakdown = []
    if exec_result["executes"]:
        reward += 0.20
        breakdown.append("executes(+0.20)")
    else:
        breakdown.append(f"exec_failed: {exec_result['exec_error']}")
        return 0.0, " | ".join(breakdown)
    results = exec_result["results"]
    basic = results[:2] if len(results) >= 2 else results
    edge = results[2:] if len(results) > 2 else []
    basic_passed = sum(1 for r in basic if r["passed"])
    edge_passed = sum(1 for r in edge if r["passed"])
    basic_reward = (basic_passed / len(basic)) * 0.40 if basic else 0.0
    edge_reward = (edge_passed / len(edge)) * 0.40 if edge else 0.0
    reward += basic_reward + edge_reward
    breakdown.append(f"basic {basic_passed}/{len(basic)}(+{basic_reward:.2f})")
    breakdown.append(f"edge {edge_passed}/{len(edge)}(+{edge_reward:.2f})")
    reward = min(1.0, reward) * _attempt_multiplier(attempt_number)
    return round(min(1.0, reward), 4), " | ".join(breakdown)

def compute_reward_hard(exec_result: Dict, quality: Dict, attempt_number: int = 1) -> Tuple[float, str]:
    reward = 0.0
    breakdown = []
    if exec_result["executes"]:
        reward += 0.20
        breakdown.append("executes(+0.20)")
    else:
        breakdown.append(f"exec_failed: {exec_result['exec_error']}")
        return 0.0, " | ".join(breakdown)
    n = exec_result["total_tests"]
    passed = exec_result["tests_passed"]
    test_reward = (passed / n) * 0.20 if n > 0 else 0.0
    reward += test_reward
    breakdown.append(f"tests {passed}/{n}(+{test_reward:.2f})")
    if quality.get("has_input_validation"):
        reward += 0.20
        breakdown.append("validation(+0.20)")
    if quality.get("no_magic_numbers"):
        reward += 0.20
        breakdown.append("no_magic(+0.20)")
    quality_score = quality.get("quality_score", 0.0) * 0.20
    reward += quality_score
    breakdown.append(f"quality(+{quality_score:.2f})")
    reward = min(1.0, reward) * _attempt_multiplier(attempt_number)
    return round(min(1.0, reward), 4), " | ".join(breakdown)

def grade(task: Task, submitted_code: str, attempt_number: int = 1) -> Dict:
    try:
        exec_result = execute_code(submitted_code, task.function_name, task.test_cases)
        quality = None
        if task.task_id == "easy":
            reward, breakdown = compute_reward_easy(exec_result, attempt_number)
        elif task.task_id in ("medium", "medium2"):
            reward, breakdown = compute_reward_medium(exec_result, attempt_number)
        elif task.task_id in ("hard", "hard2", "security", "multi"):
            quality = check_code_quality(submitted_code)
            reward, breakdown = compute_reward_hard(exec_result, quality, attempt_number)
        else:
            reward, breakdown = 0.0, "Unknown task"

        if not exec_result["executes"]:
            feedback = f"❌ Code failed to execute: {exec_result['exec_error']}"
        else:
            passed = exec_result["tests_passed"]
            total = exec_result["total_tests"]
            feedback_lines = [f"✅ Code executed. Tests passed: {passed}/{total}."]
            for r in exec_result["results"]:
                icon = "✅" if r["passed"] else "❌"
                desc = r.get("description", "")
                if r["passed"]:
                    feedback_lines.append(f"  {icon} {desc}")
                else:
                    got = r.get("got")
                    exp = r.get("expected")
                    err = r.get("error")
                    if err:
                        feedback_lines.append(f"  {icon} {desc}: Error — {err}")
                    else:
                        feedback_lines.append(f"  {icon} {desc}: expected {exp!r}, got {got!r}")
            if quality:
                feedback_lines.append(
                    f"Code quality: validation={quality['has_input_validation']}, "
                    f"no_magic={quality['no_magic_numbers']}, docstring={quality['has_docstring']}")
            feedback = "\n".join(feedback_lines)

        return {
            "reward": reward,
            "breakdown": breakdown,
            "exec_result": exec_result,
            "quality": quality,
            "feedback": feedback,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "reward": 0.0,
            "breakdown": f"grader exception: {e}",
            "exec_result": {"executes": False, "exec_error": str(e),
                           "stdout": "", "results": [],
                           "tests_passed": 0, "total_tests": 0},
            "quality": None,
            "feedback": f"❌ Grader error: {e}",
        }