# tests/test_grader.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.grader import execute_code, check_code_quality, grade
from server.tasks import get_task, TASK_EASY, TASK_MEDIUM, TASK_HARD


class TestExecuteCode:
    def test_correct_code_executes(self):
        code = "def average(lst):\n    if not lst:\n        return 0.0\n    return sum(lst)/len(lst)"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["executes"] == True

    def test_syntax_error_caught(self):
        code = "def average(lst)\n    return 0"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["executes"] == False
        assert "SyntaxError" in result["exec_error"]

    def test_blocked_import_os(self):
        code = "import os\ndef average(lst):\n    return 0.0"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["executes"] == False
        assert "SecurityError" in result["exec_error"]

    def test_blocked_import_sys(self):
        code = "import sys\ndef average(lst):\n    return 0.0"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["executes"] == False

    def test_blocked_import_subprocess(self):
        code = "import subprocess\ndef average(lst):\n    return 0.0"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["executes"] == False

    def test_missing_function_caught(self):
        code = "def wrong_name(lst):\n    return 0.0"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["executes"] == False
        assert "not found" in result["exec_error"]

    def test_all_tests_pass_correct_code(self):
        code = "def average(lst):\n    if not lst:\n        return 0.0\n    return sum(lst)/len(lst)"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["tests_passed"] == result["total_tests"]

    def test_buggy_code_fails_tests(self):
        code = "def average(lst):\n    return sum(lst)/len(lst)"
        result = execute_code(code, "average", TASK_EASY.test_cases)
        assert result["tests_passed"] < result["total_tests"]

    def test_fibonacci_correct(self):
        code = "def fibonacci(n):\n    if n < 0: raise ValueError('negative')\n    if n == 0: return 0\n    a, b = 0, 1\n    for _ in range(1, n): a, b = b, a+b\n    return b"
        result = execute_code(code, "fibonacci", TASK_MEDIUM.test_cases)
        assert result["tests_passed"] == result["total_tests"]

    def test_fibonacci_buggy(self):
        code = "def fibonacci(n):\n    if n == 0: return 0\n    a, b = 0, 0\n    for _ in range(1, n): a, b = b, a+b\n    return b"
        result = execute_code(code, "fibonacci", TASK_MEDIUM.test_cases)
        assert result["tests_passed"] < result["total_tests"]


class TestCodeQuality:
    def test_has_docstring(self):
        code = 'def foo(x):\n    """This is a docstring."""\n    return x'
        result = check_code_quality(code)
        assert result["has_docstring"] == True

    def test_no_docstring(self):
        code = "def foo(x):\n    return x"
        result = check_code_quality(code)
        assert result["has_docstring"] == False

    def test_has_validation(self):
        code = "def foo(x):\n    if x < 0:\n        raise ValueError('negative')\n    return x"
        result = check_code_quality(code)
        assert result["has_input_validation"] == True

    def test_magic_number_detected(self):
        code = "def foo(n):\n    return [True] * 100"
        result = check_code_quality(code)
        assert result["no_magic_numbers"] == False

    def test_no_magic_numbers(self):
        code = "def foo(n):\n    return [True] * (n + 1)"
        result = check_code_quality(code)
        assert result["no_magic_numbers"] == True

    def test_quality_score_range(self):
        code = 'def foo(x):\n    """doc"""\n    if x < 0: raise ValueError()\n    return x'
        result = check_code_quality(code)
        assert 0.0 <= result["quality_score"] <= 1.0

    def test_syntax_error_returns_zero(self):
        code = "def foo(x)\n    return x"
        result = check_code_quality(code)
        assert result["quality_score"] == 0.0


class TestGrade:
    def test_grade_easy_perfect(self):
        task = get_task("easy")
        code = "def average(lst):\n    if not lst:\n        return 0.0\n    return sum(lst)/len(lst)"
        result = grade(task, code, attempt_number=1)
        assert result["reward"] == 1.0

    def test_grade_easy_buggy(self):
        task = get_task("easy")
        code = "def average(lst):\n    return sum(lst)/len(lst)"
        result = grade(task, code, attempt_number=1)
        assert result["reward"] < 1.0

    def test_grade_returns_feedback(self):
        task = get_task("easy")
        code = "def average(lst):\n    if not lst: return 0.0\n    return sum(lst)/len(lst)"
        result = grade(task, code)
        assert "feedback" in result
        assert len(result["feedback"]) > 0

    def test_grade_attempt_penalty(self):
        task = get_task("medium")
        code = "def fibonacci(n):\n    if n==0: return 0\n    a,b=0,1\n    for _ in range(1,n): a,b=b,a+b\n    return b"
        result1 = grade(task, code, attempt_number=1)
        result2 = grade(task, code, attempt_number=2)
        assert result2["reward"] < result1["reward"]

    def test_grade_never_returns_none(self):
        task = get_task("easy")
        result = grade(task, "def average(lst): return 0.0")
        assert result is not None
        assert "reward" in result

    def test_grade_reward_in_range(self):
        task = get_task("hard")
        code = "def sieve_of_eratosthenes(n):\n    if n<0: raise ValueError()\n    if n<2: return []\n    p=[True]*(n+1)\n    p[0]=p[1]=False\n    for i in range(2,int(n**0.5)+1):\n        if p[i]:\n            for j in range(i*i,n+1,i): p[j]=False\n    return [i for i in range(n+1) if p[i]]"
        result = grade(task, code)
        assert 0.0 <= result["reward"] <= 1.0