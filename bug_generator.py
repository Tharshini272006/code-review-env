"""
bug_generator.py
Dynamically generates buggy Python challenges using LLM.
Part of Theme 4 - Self Improvement Layer.
"""

import os
import json
from openai import OpenAI

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

client_llm = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ─── Prompts ────────────────────────────────────────────────────────────────

GENERATOR_SYSTEM_PROMPT = """You are an expert Python educator who creates buggy Python coding challenges for RL training.

You MUST respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.

JSON format:
{
  "function_name": "name of the function",
  "description": "one sentence what the function should do",
  "buggy_code": "the full Python function with exactly one bug introduced",
  "correct_code": "the full correct Python function",
  "bug_type": "one of: logic_error, edge_case, type_error, off_by_one, missing_check",
  "hint": "a subtle hint about what to look for",
  "test_cases": [
    {"input": "some_input", "expected": "expected_output", "label": "test label"},
    {"input": "some_input", "expected": "expected_output", "label": "test label"},
    {"input": "some_input", "expected": "expected_output", "label": "test label"}
  ]
}"""

DIFFICULTY_PROMPTS = {
    "easy": """Generate an EASY buggy Python function challenge.
Rules:
- Simple function (5-10 lines)
- Common bug like missing edge case (empty list, zero division)
- Beginner level
- Example topics: sum, average, reverse, count""",

    "medium": """Generate a MEDIUM buggy Python function challenge.
Rules:
- Moderate complexity (10-20 lines)
- Subtle bug like off-by-one error or wrong logic
- Intermediate level
- Example topics: sorting, searching, string manipulation, recursion""",

    "hard": """Generate a HARD buggy Python function challenge.
Rules:
- Complex function (20-35 lines)
- Tricky bug like wrong base case, incorrect boundary, subtle type mismatch
- Advanced level
- Example topics: dynamic programming, tree traversal, graph problems, complex algorithms"""
}

# ─── Generator ──────────────────────────────────────────────────────────────

def generate_bug_challenge(difficulty: str = "easy", topic: str = None) -> dict:
    """
    Generate a buggy Python challenge at the given difficulty level.
    Returns a dict with buggy_code, correct_code, hint, test_cases etc.
    """
    difficulty = difficulty.lower()
    if difficulty not in DIFFICULTY_PROMPTS:
        difficulty = "easy"

    user_msg = DIFFICULTY_PROMPTS[difficulty]
    if topic:
        user_msg += f"\n\nSpecific topic to use: {topic}"

    try:
        response = client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1024,
            temperature=0.7,  # higher = more creative/varied challenges
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])

        challenge = json.loads(raw)

        # Validate required fields
        required = ["function_name", "description", "buggy_code", "correct_code", "hint", "test_cases"]
        for field in required:
            if field not in challenge:
                raise ValueError(f"Missing field: {field}")

        challenge["difficulty"] = difficulty
        return challenge

    except json.JSONDecodeError as e:
        print(f"[BugGenerator] JSON parse error: {e}")
        return _fallback_challenge(difficulty)
    except Exception as e:
        print(f"[BugGenerator] Error: {e}")
        return _fallback_challenge(difficulty)


def _fallback_challenge(difficulty: str) -> dict:
    """
    Hardcoded fallback challenge if LLM fails.
    Ensures the loop never breaks.
    """
    fallbacks = {
        "easy": {
            "function_name": "average",
            "description": "Return the average of a list of numbers.",
            "buggy_code": "def average(lst):\n    return sum(lst) / len(lst)\n",
            "correct_code": "def average(lst):\n    if not lst:\n        return 0.0\n    return sum(lst) / len(lst)\n",
            "bug_type": "edge_case",
            "hint": "Think about what happens when the list is empty.",
            "test_cases": [
                {"input": "[1, 2, 3]", "expected": "2.0", "label": "normal list"},
                {"input": "[]", "expected": "0.0", "label": "empty list"},
                {"input": "[-1, 1]", "expected": "0.0", "label": "negatives"},
            ],
            "difficulty": "easy"
        },
        "medium": {
            "function_name": "binary_search",
            "description": "Return index of target in sorted list, or -1 if not found.",
            "buggy_code": "def binary_search(arr, target):\n    left, right = 0, len(arr)\n    while left < right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n",
            "correct_code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n",
            "bug_type": "off_by_one",
            "hint": "Check the initial value of right and the while condition.",
            "test_cases": [
                {"input": "[1,2,3,4,5], 3", "expected": "2", "label": "found middle"},
                {"input": "[1,2,3,4,5], 1", "expected": "0", "label": "found first"},
                {"input": "[1,2,3,4,5], 9", "expected": "-1", "label": "not found"},
            ],
            "difficulty": "medium"
        },
        "hard": {
            "function_name": "longest_common_subsequence",
            "description": "Return the length of the longest common subsequence of two strings.",
            "buggy_code": "def longest_common_subsequence(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n            if s1[i] == s2[j]:\n                dp[i][j] = dp[i-1][j-1] + 1\n            else:\n                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n    return dp[m][n]\n",
            "correct_code": "def longest_common_subsequence(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n    for i in range(1, m + 1):\n        for j in range(1, n + 1):\n            if s1[i-1] == s2[j-1]:\n                dp[i][j] = dp[i-1][j-1] + 1\n            else:\n                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n    return dp[m][n]\n",
            "bug_type": "off_by_one",
            "hint": "Check how you are indexing into the strings inside the loop.",
            "test_cases": [
                {"input": "'abcde', 'ace'", "expected": "3", "label": "standard"},
                {"input": "'abc', 'abc'", "expected": "3", "label": "identical"},
                {"input": "'abc', 'def'", "expected": "0", "label": "no common"},
            ],
            "difficulty": "hard"
        }
    }
    return fallbacks.get(difficulty, fallbacks["easy"])


# ─── Quick test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🐛 Testing Bug Generator...\n")
    for level in ["easy", "medium", "hard"]:
        print(f"--- {level.upper()} ---")
        challenge = generate_bug_challenge(level)
        print(f"Function : {challenge['function_name']}")
        print(f"Bug Type : {challenge['bug_type']}")
        print(f"Hint     : {challenge['hint']}")
        print(f"Buggy Code:\n{challenge['buggy_code']}")
        print()