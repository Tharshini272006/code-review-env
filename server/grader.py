# server/grader.py
import ast
import sys
import io
import types
from typing import Any, Dict, List, Optional, Tuple


# Security configuration
BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "requests", "importlib",
    "builtins", "ctypes", "multiprocessing", "threading",
}

def _check_safety(code: str) -> Optional[str]:
    """Perform static analysis to block dangerous imports and attribute access."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"

    for node in ast.walk(tree):
        # 1. Check for blocked imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                if name in BLOCKED_IMPORTS:
                    return f"SecurityError: import of '{name}' is not allowed."
        
        # 2. Block dangerous dunder attribute access (e.g., __subclasses__)
        if isinstance(node, ast.Attribute):
            if node.attr in ("__subclasses__", "__globals__", "__builtins__"):
                return f"SecurityError: Access to '{node.attr}' is forbidden."
    return None

def _run_with_timeout(fn, timeout_seconds: int = 5):
    """Executes a function; in a real prod env, use multiprocessing for strict timeouts."""
    try:
        # Simple execution for hackathon scope
        result = fn()
        return result, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def execute_code(code: str, function_name: str, test_cases: list, timeout: int = 5) -> Dict:
    """Compiles and executes submitted code in a restricted namespace."""
    safety_err = _check_safety(code)
    if safety_err:
        return {"executes": False, "exec_error": safety_err, "stdout": "",
                "results": [], "tests_passed": 0, "total_tests": len(test_cases)}

    try:
        compiled = compile(code, "<submitted>", "exec")
    except SyntaxError as e:
        return {"executes": False, "exec_error": f"SyntaxError: {e}", "stdout": "",
                "results": [], "tests_passed": 0, "total_tests": len(test_cases)}

    # Build restricted builtins
    raw = __builtins__
    builtins_dict = raw if isinstance(raw, dict) else raw.__dict__
    
    safe_builtins = {k: v for k, v in builtins_dict.items()
                     if k not in ("__import__", "open", "exec", "eval", "compile",
                                  "input", "breakpoint", "quit", "exit")}

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
    # SUPPORT BOTH FORMATS
        if isinstance(tc, list):
            args = tc[0]
            expected = tc[1]
            description = ""
        else:
            args = tc["args"]
            expected = tc["expected"]
            description = tc.get("description", "")

    def _call():
        return fn(*args)

    got, err = _run_with_timeout(_call, timeout_seconds=timeout)

    if err:
        results.append({
            "passed": False,
            "expected": expected,
            "got": None,
            "error": err,
            "description": description
        })
    else:
        results.append({
            "passed": got == expected,
            "expected": expected,
            "got": got,
            "error": None,
            "description": description
        })

    tests_passed = sum(1 for r in results if r["passed"])
    return {"executes": True, "exec_error": None, "stdout": captured_stdout.getvalue(),
            "results": results, "tests_passed": tests_passed, "total_tests": len(test_cases)}

def check_code_quality(code: str) -> Dict:
    """Analyzes AST for best practices: docstrings, magic numbers, and validation."""
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
            # Check for docstring
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                has_docstring = True
        
        # Check for error handling or input checks
        if isinstance(node, (ast.Raise, ast.If)):
            has_validation = True
            
        # Check for magic numbers (integers > 2 used as constants)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            if node.value > 2:
                no_magic = False

    score = (0.35 if has_validation else 0.0) + (0.40 if no_magic else 0.0) + (0.25 if has_docstring else 0.0)
    return {"has_input_validation": has_validation, "no_magic_numbers": no_magic,
            "has_docstring": has_docstring, "quality_score": round(score, 3)}

# Reward Calculation logic
ATTEMPT_PENALTY = 0.90

def _attempt_multiplier(attempt_number: int) -> float:
    return ATTEMPT_PENALTY ** max(0, attempt_number - 1)

def compute_reward_easy(exec_result: Dict, attempt_number: int = 1) -> Tuple[float, str]:
    reward = 0.0
    if not exec_result["executes"]:
        return 0.0, f"exec_failed: {exec_result['exec_error']}"
    
    reward += 0.20  # Baseline for code that runs
    n, passed = exec_result["total_tests"], exec_result["tests_passed"]
    test_reward = (passed / n) * 0.80 if n > 0 else 0.0
    reward += test_reward
    
    total = min(1.0, reward) * _attempt_multiplier(attempt_number)
    return round(total, 4), f"exec(+0.20) | tests {passed}/{n}(+{test_reward:.2f})"

def compute_reward_medium(exec_result: Dict, attempt_number: int = 1) -> Tuple[float, str]:
    reward = 0.0
    if not exec_result["executes"]:
        return 0.0, f"exec_failed: {exec_result['exec_error']}"
    
    reward += 0.20
    results = exec_result["results"]
    # Logic: First 2 are 'basic', rest are 'edge'
    basic = results[:2] if len(results) >= 2 else results
    edge = results[2:] if len(results) > 2 else []
    
    b_p = sum(1 for r in basic if r["passed"])
    e_p = sum(1 for r in edge if r["passed"])
    
    b_reward = (b_p / len(basic)) * 0.40 if basic else 0.0
    e_reward = (e_p / len(edge)) * 0.40 if edge else 0.0
    reward += b_reward + e_reward
    
    total = min(1.0, reward) * _attempt_multiplier(attempt_number)
    return round(total, 4), f"exec(+0.2) | basic {b_p}(+{b_reward:.2f}) | edge {e_p}(+{e_reward:.2f})"

def compute_reward_hard(exec_result: Dict, quality: Dict, attempt_number: int = 1) -> Tuple[float, str]:
    reward = 0.0
    if not exec_result["executes"]:
        return 0.0, f"exec_failed: {exec_result['exec_error']}"
    
    reward += 0.20
    n, passed = exec_result["total_tests"], exec_result["tests_passed"]
    test_reward = (passed / n) * 0.20 if n > 0 else 0.0
    reward += test_reward
    
    # Quality markers
    v_reward = 0.20 if quality.get("has_input_validation") else 0.0
    m_reward = 0.20 if quality.get("no_magic_numbers") else 0.0
    q_reward = quality.get("quality_score", 0.0) * 0.20
    
    reward += (v_reward + m_reward + q_reward)
    total = min(1.0, reward) * _attempt_multiplier(attempt_number)
    return round(total, 4), f"tests {passed}/{n} | quality score: {quality.get('quality_score')}"

def grade(task: dict, submitted_code: str, attempt_number: int = 1) -> Dict:
    """Main entry point for the environment to grade a submission."""
    try:
        exec_result = execute_code(submitted_code, task["function_name"], task["test_cases"])
        quality = None
        
        if task["id"] == "easy":
            reward, breakdown = compute_reward_easy(exec_result, attempt_number)
        elif task["id"] in ("medium", "medium2"):
            reward, breakdown = compute_reward_medium(exec_result, attempt_number)
        elif task["id"] in ("hard", "hard2", "security"):
            quality = check_code_quality(submitted_code)
            reward, breakdown = compute_reward_hard(exec_result, quality, attempt_number)
        else:
            reward, breakdown = 0.0, "Unknown task"
            
    except Exception as e:
        return {
            "reward": 0.0, "breakdown": f"Grader Error: {str(e)}",
            "exec_result": {"executes": False, "exec_error": str(e)},
            "quality": None, "feedback": f"❌ Grader Error: {str(e)}"
        }

    # Generate Feedback String
    if not exec_result["executes"]:
        feedback = f"❌ Code failed to execute: {exec_result['exec_error']}"
    else:
        passed, total = exec_result["tests_passed"], exec_result["total_tests"]
        feedback_lines = [f"✅ Code executed. Tests passed: {passed}/{total}."]
        for r in exec_result["results"]:
            icon = "✅" if r["passed"] else "❌"
            if not r["passed"]:
                feedback_lines.append(f"   {icon} {r['description']}: expected {r['expected']!r}, got {r['got']!r}")
        
        if quality:
            feedback_lines.append(f"⭐ Quality: Val={quality['has_input_validation']}, NoMagic={quality['no_magic_numbers']}")
        feedback = "\n".join(feedback_lines)

    return {
        "reward": reward,
        "breakdown": breakdown,
        "exec_result": exec_result,
        "quality": quality,
        "feedback": feedback,
    }
