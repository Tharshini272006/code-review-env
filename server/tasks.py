# server/tasks.py
"""
All 3 task definitions with buggy code + hidden test cases.
Tasks: easy (syntax_fix), medium (logic_fix), hard (refactor_and_fix)
"""

from dataclasses import dataclass, field
from typing import List, Callable, Any, Dict


@dataclass
class TestCase:
    args: List[Any]
    kwargs: Dict[str, Any]
    expected: Any
    description: str


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    buggy_code: str
    function_name: str
    max_attempts: int
    test_cases: List[TestCase]
    hint: str = ""
    tags: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# TASK 1 — easy — syntax_fix
# Bug: no guard for empty list → ZeroDivisionError
# ─────────────────────────────────────────────
TASK_EASY = Task(
    task_id="easy",
    name="syntax_fix",
    description=(
        "Fix the Python function below. It is supposed to return the average "
        "of a list of numbers, but it crashes on certain inputs. "
        "Submit a corrected version of the entire function."
    ),
    buggy_code='''\
def average(lst):
    """Return the average of a list of numbers."""
    return sum(lst) / len(lst)
''',
    function_name="average",
    max_attempts=1,
    test_cases=[
        TestCase(args=[[1, 2, 3, 4, 5]], kwargs={}, expected=3.0,
                 description="normal list"),
        TestCase(args=[[]], kwargs={}, expected=0.0,
                 description="empty list returns 0.0"),
        TestCase(args=[[-2, 2]], kwargs={}, expected=0.0,
                 description="negative numbers"),
    ],
    hint="Think about what happens when the list is empty.",
    tags=["division", "guard-clause", "easy"],
)

# ─────────────────────────────────────────────
# TASK 2 — medium — logic_fix
# Bug: fibonacci returns wrong sequence (uses 0,0 instead of 0,1)
# ─────────────────────────────────────────────
TASK_MEDIUM = Task(
    task_id="medium",
    name="logic_fix",
    description=(
        "Fix the Python function below. It is supposed to return the n-th "
        "Fibonacci number (0-indexed: fib(0)=0, fib(1)=1, fib(2)=1, fib(3)=2 …), "
        "but it produces wrong results due to a logical bug. "
        "You have up to 3 attempts. Execution feedback is provided after each attempt."
    ),
    buggy_code='''\
def fibonacci(n):
    """Return the n-th Fibonacci number (0-indexed)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 0
    a, b = 0, 0          # BUG: second value should be 1
    for _ in range(1, n):
        a, b = b, a + b
    return b
''',
    function_name="fibonacci",
    max_attempts=3,
    test_cases=[
        TestCase(args=[0], kwargs={}, expected=0,
                 description="fib(0) = 0"),
        TestCase(args=[1], kwargs={}, expected=1,
                 description="fib(1) = 1"),
        TestCase(args=[6], kwargs={}, expected=8,
                 description="fib(6) = 8"),
        TestCase(args=[10], kwargs={}, expected=55,
                 description="fib(10) = 55"),
        TestCase(args=[2], kwargs={}, expected=1,
                 description="fib(2) = 1 (edge case)"),
    ],
    hint="Check the initial values of a and b before the loop.",
    tags=["fibonacci", "logic", "loop", "medium"],
)

# ─────────────────────────────────────────────
# TASK 3 — hard — refactor_and_fix
# Bugs: wrong base case AND no error handling AND magic number 100
# ─────────────────────────────────────────────
TASK_HARD = Task(
    task_id="hard",
    name="refactor_and_fix",
    description=(
        "The function below is supposed to return all prime numbers up to n "
        "(inclusive) using the Sieve of Eratosthenes. It has a bug AND poor "
        "code quality (magic numbers, no input validation, crashes on edge cases). "
        "Fix the bug AND improve the code: add input validation, remove hardcoded "
        "magic numbers, and handle edge cases gracefully. "
        "You have up to 5 attempts with feedback after each."
    ),
    buggy_code='''\
def sieve_of_eratosthenes(n):
    """Return list of primes up to n using Sieve of Eratosthenes."""
    primes = [True] * 100        # BUG + magic number: should be (n + 1)
    primes[0] = primes[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if primes[i]:
            for j in range(i * i, 100, i):   # BUG + magic: should use n+1
                primes[j] = False
    return [i for i in range(100) if primes[i]]  # magic number
''',
    function_name="sieve_of_eratosthenes",
    max_attempts=5,
    test_cases=[
        TestCase(args=[10], kwargs={}, expected=[2, 3, 5, 7],
                 description="primes up to 10"),
        TestCase(args=[1], kwargs={}, expected=[],
                 description="primes up to 1 → empty list"),
        TestCase(args=[2], kwargs={}, expected=[2],
                 description="primes up to 2"),
        TestCase(args=[20], kwargs={}, expected=[2, 3, 5, 7, 11, 13, 17, 19],
                 description="primes up to 20"),
        TestCase(args=[0], kwargs={}, expected=[],
                 description="primes up to 0 → empty list"),
    ],
    hint=(
        "The sieve array size must be n+1, not a fixed 100. "
        "Also validate that n >= 0 and handle n < 2 gracefully."
    ),
    tags=["sieve", "refactor", "validation", "hard"],
)
# ─────────────────────────────────────────────
# TASK 4 — medium2 — string_fix
# Bug: wrong slice step in string reversal
# ─────────────────────────────────────────────
TASK_MEDIUM2 = Task(
    task_id="medium2",
    name="string_fix",
    description=(
        "Fix the Python function below. It is supposed to reverse a string "
        "but returns wrong output due to a logical bug. "
        "You have up to 3 attempts with feedback after each."
    ),
    buggy_code='''\
def reverse_string(s):
    """Return the reverse of a string."""
    return s[::1]   # BUG: step should be -1, not 1
''',
    function_name="reverse_string",
    max_attempts=3,
    test_cases=[
        TestCase(args=["hello"], kwargs={}, expected="olleh",
                 description="reverse 'hello'"),
        TestCase(args=[""], kwargs={}, expected="",
                 description="empty string"),
        TestCase(args=["a"], kwargs={}, expected="a",
                 description="single character"),
        TestCase(args=["abcde"], kwargs={}, expected="edcba",
                 description="reverse 'abcde'"),
        TestCase(args=["racecar"], kwargs={}, expected="racecar",
                 description="palindrome"),
    ],
    hint="Check the slice step value — what does s[::1] do vs s[::-1]?",
    tags=["string", "slice", "medium"],
)

# ─────────────────────────────────────────────
# TASK 5 — hard2 — binary_search_fix
# Bug: off-by-one + no validation + magic numbers
# ─────────────────────────────────────────────
TASK_HARD2 = Task(
    task_id="hard2",
    name="binary_search_fix",
    description=(
        "Fix the Python function below. It is supposed to perform binary search "
        "and return the index of target in a sorted list, or -1 if not found. "
        "It has a bug AND poor code quality. "
        "Fix the bug AND add input validation. "
        "You have up to 5 attempts with feedback after each."
    ),
    buggy_code='''\
def binary_search(arr, target):
    """Return index of target in sorted arr, or -1 if not found."""
    left, right = 0, len(arr)    # BUG: should be len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
''',
    function_name="binary_search",
    max_attempts=5,
    test_cases=[
        TestCase(args=["alice"], kwargs={}, expected="alice",
                 description="normal input unchanged"),
        TestCase(args=["alice'"], kwargs={}, expected="alice",
                 description="single quote removed"),
        TestCase(args=["alice;"], kwargs={}, expected="alice",
                 description="semicolon removed"),
        TestCase(args=[None], kwargs={}, expected="",
                 description="None returns empty string"),
        TestCase(args=["test--"], kwargs={}, expected="test",
                 description="SQL comment marker removed"),
    ],
    hint="Check the initial value of right — should it be len(arr) or len(arr)-1?",
    tags=["binary-search", "off-by-one", "hard"],
)
TASK_SECURITY = Task(
    task_id="security",
    name="security_fix",
    description=(
        "The function below is supposed to sanitize user input by removing "
        "dangerous SQL characters, but it has a bug — it only removes single quotes "
        "but misses other dangerous characters like semicolons and comments (--). "
        "Fix it to properly sanitize ALL dangerous SQL characters and handle None input. "
        "You have up to 3 attempts with feedback after each."
    ),
    buggy_code='''\
def sanitize_input(user_input):
    """Remove dangerous SQL characters from user input."""
    if user_input is None:
        return ""
    return user_input.replace("\'", "")   # BUG: misses ; -- and other chars
''',
    function_name="sanitize_input",
    max_attempts=3,
    test_cases=[
        TestCase(args=["alice"], kwargs={}, expected="alice",
                 description="normal input unchanged"),
        TestCase(args=["alice'bobby"], kwargs={}, expected="alicebobby",
                 description="single quote removed"),
        TestCase(args=["alice;bobby"], kwargs={}, expected="alicebobby",
                 description="semicolon removed"),
        TestCase(args=[None], kwargs={}, expected="",
                 description="None returns empty string"),
        TestCase(args=["alice--bobby"], kwargs={}, expected="alicebobby",
                 description="SQL comment removed"),
    ],
    hint="Remove all of: single quotes ('), semicolons (;), and SQL comments (--).",
    tags=["security", "sanitization", "sql", "hard"],
)

# ─────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────
TASKS: Dict[str, Task] = {
    "easy":     TASK_EASY,
    "medium":   TASK_MEDIUM,
    "hard":     TASK_HARD,
    "medium2":  TASK_MEDIUM2,
    "hard2":    TASK_HARD2,
    "security": TASK_SECURITY,
}


def get_task(task_id: str) -> Task:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {list(TASKS.keys())}")
    return TASKS[task_id]


def list_tasks() -> List[Dict]:
    return [
        {
            "task_id":      t.task_id,
            "name":         t.name,
            "description":  t.description,
            "max_attempts": t.max_attempts,
            "tags":         t.tags,
        }
        for t in TASKS.values()
    ]
# ---------------------------------------------
# TASK 7 � multi_bug_fix (ultra hard)
# ---------------------------------------------
TASK_MULTI = Task(
    task_id="multi",
    name="multi_bug_fix",
    description=(
        "The function below calculates a discounted price but has MULTIPLE bugs: "
        "1) Wrong discount formula, "
        "2) No validation for negative price or discount, "
        "3) Returns wrong type for zero discount. "
        "Fix ALL bugs and add proper input validation. "
        "You have up to 5 attempts with detailed feedback after each."
    ),
    buggy_code='''\
def calculate_discount(price, discount_pct):
    """Calculate final price after applying discount percentage."""
    result = price * discount_pct
    return result
''',
    function_name="calculate_discount",
    max_attempts=5,
    test_cases=[
        TestCase(args=[100, 20], kwargs={}, expected=80.0,
                 description="100 with 20% discount = 80.0"),
        TestCase(args=[200, 50], kwargs={}, expected=100.0,
                 description="200 with 50% discount = 100.0"),
        TestCase(args=[100, 0], kwargs={}, expected=100.0,
                 description="0% discount returns original price"),
        TestCase(args=[50, 10], kwargs={}, expected=45.0,
                 description="50 with 10% discount = 45.0"),
        TestCase(args=[100, 100], kwargs={}, expected=0.0,
                 description="100% discount = 0.0"),
    ],
    hint=(
        "Formula should be: price * (1 - discount_pct / 100). "
        "Validate: price >= 0, 0 <= discount_pct <= 100. "
        "Always return float."
    ),
    tags=["multi-bug", "formula", "validation", "ultra-hard"],
)

TASKS = {
    "easy":     TASK_EASY,
    "medium":   TASK_MEDIUM,
    "hard":     TASK_HARD,
    "medium2":  TASK_MEDIUM2,
    "hard2":    TASK_HARD2,
    "security": TASK_SECURITY,
    "multi":    TASK_MULTI,
}


def get_task(task_id: str):
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {list(TASKS.keys())}")
    return TASKS[task_id]


def list_tasks():
    return [
        {
            "task_id":      t.task_id,
            "name":         t.name,
            "description":  t.description,
            "max_attempts": t.max_attempts,
            "tags":         t.tags,
        }
        for t in TASKS.values()
    ]
