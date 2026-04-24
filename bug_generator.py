"""
bug_generator.py — Recursive Skill Amplification Engine
Generates infinite LeetCode-style buggy Python challenges via LLM.
Easy → Medium → Hard → Extreme (LLM invents harder problems forever).

Bug complexity scales with difficulty:
  Easy    → single obvious bugs (off-by-one, wrong operator, missing return)
  Medium  → logic errors, edge cases, wrong data structures
  Hard    → subtle algorithmic bugs, DP errors, pointer mistakes
  Extreme → multi-bug, concurrency, complex state bugs
"""

import os
import json
import random
from openai import OpenAI

# ── LLM Config (Groq or HuggingFace router) ───────────────────────────────────
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
HF_KEY   = os.getenv("HF_TOKEN", os.getenv("API_KEY", ""))

if GROQ_KEY:
    client_llm = OpenAI(api_key=GROQ_KEY, base_url="https://api.groq.com/openai/v1")
    MODEL_NAME = "llama-3.3-70b-versatile"
else:
    client_llm = OpenAI(api_key=HF_KEY, base_url="https://router.huggingface.co/v1")
    MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# ── Per-difficulty bug types (complexity scales up) ───────────────────────────
BUG_TYPES = {
    "easy": [
        "off_by_one",        # range(1, n) instead of range(n)
        "wrong_operator",    # > instead of >=, + instead of -
        "missing_return",    # forgot return statement
        "wrong_index",       # lst[0] instead of lst[-1]
        "wrong_initial_value",  # total = 1 instead of 0
    ],
    "medium": [
        "wrong_condition",   # while left < right (should be <=)
        "missing_edge_case", # no check for empty input
        "mutation_bug",      # modifying list during iteration
        "wrong_accumulator", # float('-inf') vs 0 for max
        "dict_key_error",    # dict[key] += 1 without initialization
    ],
    "hard": [
        "wrong_dp_index",         # s1[i] instead of s1[i-1] in DP
        "incorrect_base_case",    # factorial(0) not handled
        "closure_capture_bug",    # lambda capturing loop var by ref
        "memoization_scope_error",# memo dict recreated every call
        "wrong_recurrence",       # dp[i][j] = wrong combination
    ],
    "extreme": [
        "generator_exhaustion",   # iterating generator twice
        "shallow_copy_bug",       # list copy not deep enough
        "off_by_one_in_dp_bounds",# dp array sized wrong
        "wrong_graph_traversal",  # BFS/DFS terminates early
        "missed_modulo_overflow", # large number without % MOD
    ],
}

# ── Topic pools (difficulty-gated) ────────────────────────────────────────────
TOPICS = {
    "easy": [
        "sum of a list", "check if palindrome", "count vowels in string",
        "find max in list", "reverse a string", "filter even numbers",
        "calculate factorial", "check if prime", "celsius to fahrenheit",
        "count character occurrences", "remove duplicates from list",
        "compute power of a number",
    ],
    "medium": [
        "binary search on sorted array", "two-pointer sum problem",
        "sliding window maximum", "valid parentheses checker",
        "merge two sorted arrays", "group anagrams",
        "longest substring without repeating chars",
        "product of array except self", "subarray sum equals k",
        "find all permutations of a string", "rotate matrix 90 degrees",
        "find duplicate number in array",
    ],
    "hard": [
        "longest common subsequence", "0/1 knapsack problem",
        "word break with dictionary", "minimum edit distance (Levenshtein)",
        "serialize/deserialize binary tree", "topological sort of DAG",
        "coin change with minimum coins", "burst balloons DP",
        "count unique BST structures", "regex pattern matching",
        "N-Queens backtracking", "maximum sum rectangle in 2D matrix",
    ],
    "extreme": [
        "implement trie with wildcard search",
        "alien dictionary order via topological sort",
        "minimum window substring with frequency constraint",
        "largest rectangle in histogram stack approach",
        "count of smaller numbers after self (merge sort)",
        "recover BST with exactly two swapped nodes",
        "max flow in network (Ford-Fulkerson)",
        "minimum cost to connect all points (Kruskal/Prim)",
    ],
}

SYSTEM_PROMPT = """You are an expert Python educator building RL training environments.
You generate buggy Python coding challenges in LeetCode style.
You MUST respond ONLY with a single valid JSON object.
No markdown fences, no explanation, no extra text — just raw JSON."""


def generate_bug_challenge(difficulty: str) -> dict:
    """
    Generate a fresh LeetCode-style buggy challenge at the given difficulty.
    Every call produces a unique problem (random topic + random bug type).
    Falls back to hardcoded only if LLM truly fails.
    """
    difficulty = difficulty if difficulty in BUG_TYPES else "easy"
    bug_type   = random.choice(BUG_TYPES[difficulty])
    topic      = random.choice(TOPICS[difficulty])

    # Difficulty-specific instructions so the LLM makes appropriately subtle bugs
    complexity_notes = {
        "easy":    "The bug must be immediately visible on inspection — a beginner mistake.",
        "medium":  "The bug is subtle — it passes most cases but fails edge cases or specific inputs.",
        "hard":    "The bug is algorithmic — wrong recurrence, wrong index in DP, or wrong base case. Looks almost correct.",
        "extreme": "The bug is deeply hidden — requires expert knowledge to spot. Could involve state, scope, or memory issues.",
    }

    prompt = f"""Generate a Python buggy coding challenge.

Difficulty : {difficulty.upper()}
Topic      : {topic}
Bug type   : {bug_type}
Style note : {complexity_notes[difficulty]}

Rules:
- buggy_code and correct_code differ by EXACTLY 1-2 lines
- Function must be completely self-contained (zero imports)
- The bug MUST be of type: {bug_type}
- Include exactly 3 test cases: basic, edge, stress
- hint guides without giving away the answer

Return ONLY this JSON:
{{
  "function_name": "snake_case_name",
  "description": "One sentence: what the function should do and return.",
  "buggy_code": "def function_name(...):\\n    <full function with the {bug_type} bug>\\n",
  "correct_code": "def function_name(...):\\n    <identical but bug fixed>\\n",
  "bug_type": "{bug_type}",
  "hint": "One sentence hint that points to the area without revealing the fix.",
  "difficulty": "{difficulty}",
  "topic": "{topic}",
  "test_cases": [
    {{"input": "args_as_string", "expected": "result_as_string", "label": "basic case"}},
    {{"input": "args_as_string", "expected": "result_as_string", "label": "edge case"}},
    {{"input": "args_as_string", "expected": "result_as_string", "label": "stress case"}}
  ]
}}"""

    try:
        response = client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=800,
            temperature=1.0,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip().startswith("```") else "\n".join(lines[1:])

        challenge = json.loads(raw)
        # Always enforce correct metadata
        challenge["difficulty"] = difficulty
        challenge["bug_type"]   = bug_type
        challenge["topic"]      = topic
        return challenge

    except Exception as e:
        print(f"⚠️  LLM generation failed ({e}), using hardcoded fallback for {difficulty}")
        return _fallback(difficulty)


# ── Hardcoded fallbacks — one per tier, all different bug types ───────────────

def _fallback(difficulty: str) -> dict:
    return {
        "easy": {
            "function_name": "sum_list",
            "description": "Return the sum of all elements in a list of numbers.",
            "buggy_code": (
                "def sum_list(nums):\n"
                "    total = 0\n"
                "    for i in range(1, len(nums)):  # BUG: off_by_one — skips index 0\n"
                "        total += nums[i]\n"
                "    return total\n"
            ),
            "correct_code": (
                "def sum_list(nums):\n"
                "    total = 0\n"
                "    for i in range(0, len(nums)):\n"
                "        total += nums[i]\n"
                "    return total\n"
            ),
            "bug_type": "off_by_one",
            "hint": "Check where the range starts — are you skipping any elements?",
            "difficulty": "easy",
            "topic": "sum of a list",
            "test_cases": [
                {"input": "[1, 2, 3]", "expected": "6",  "label": "basic case"},
                {"input": "[5]",       "expected": "5",  "label": "single element"},
                {"input": "[]",        "expected": "0",  "label": "empty list"},
            ],
        },
        "medium": {
            "function_name": "binary_search",
            "description": "Return the index of target in a sorted list, or -1 if not found.",
            "buggy_code": (
                "def binary_search(arr, target):\n"
                "    left, right = 0, len(arr)  # BUG: wrong_condition — should be len(arr)-1\n"
                "    while left < right:          # BUG: wrong_condition — should be <=\n"
                "        mid = (left + right) // 2\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        elif arr[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    return -1\n"
            ),
            "correct_code": (
                "def binary_search(arr, target):\n"
                "    left, right = 0, len(arr) - 1\n"
                "    while left <= right:\n"
                "        mid = (left + right) // 2\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        elif arr[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    return -1\n"
            ),
            "bug_type": "wrong_condition",
            "hint": "Check the initial value of 'right' and the while loop condition carefully.",
            "difficulty": "medium",
            "topic": "binary search on sorted array",
            "test_cases": [
                {"input": "[1,2,3,4,5], 3", "expected": "2",  "label": "found middle"},
                {"input": "[1,2,3,4,5], 5", "expected": "4",  "label": "found last"},
                {"input": "[1,2,3,4,5], 9", "expected": "-1", "label": "not found"},
            ],
        },
        "hard": {
            "function_name": "longest_common_subsequence",
            "description": "Return the length of the longest common subsequence of two strings.",
            "buggy_code": (
                "def longest_common_subsequence(s1, s2):\n"
                "    m, n = len(s1), len(s2)\n"
                "    dp = [[0] * (n + 1) for _ in range(m + 1)]\n"
                "    for i in range(1, m + 1):\n"
                "        for j in range(1, n + 1):\n"
                "            if s1[i] == s2[j]:  # BUG: wrong_dp_index — should be s1[i-1], s2[j-1]\n"
                "                dp[i][j] = dp[i-1][j-1] + 1\n"
                "            else:\n"
                "                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n"
                "    return dp[m][n]\n"
            ),
            "correct_code": (
                "def longest_common_subsequence(s1, s2):\n"
                "    m, n = len(s1), len(s2)\n"
                "    dp = [[0] * (n + 1) for _ in range(m + 1)]\n"
                "    for i in range(1, m + 1):\n"
                "        for j in range(1, n + 1):\n"
                "            if s1[i-1] == s2[j-1]:\n"
                "                dp[i][j] = dp[i-1][j-1] + 1\n"
                "            else:\n"
                "                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n"
                "    return dp[m][n]\n"
            ),
            "bug_type": "wrong_dp_index",
            "hint": "The DP table is 1-indexed but your strings are 0-indexed — check how you access characters.",
            "difficulty": "hard",
            "topic": "longest common subsequence",
            "test_cases": [
                {"input": "'abcde', 'ace'", "expected": "3", "label": "standard"},
                {"input": "'abc', 'abc'",   "expected": "3", "label": "identical"},
                {"input": "'abc', 'def'",   "expected": "0", "label": "no common"},
            ],
        },
        "extreme": {
            "function_name": "min_edit_distance",
            "description": "Return the minimum edit distance (insert/delete/replace) between two strings.",
            "buggy_code": (
                "def min_edit_distance(s1, s2):\n"
                "    m, n = len(s1), len(s2)\n"
                "    dp = [[0] * (n + 1) for _ in range(m + 1)]\n"
                "    for i in range(m + 1): dp[i][0] = i\n"
                "    for j in range(n + 1): dp[0][j] = j\n"
                "    for i in range(1, m + 1):\n"
                "        for j in range(1, n + 1):\n"
                "            if s1[i-1] == s2[j-1]:\n"
                "                dp[i][j] = dp[i-1][j-1]\n"
                "            else:\n"
                "                # BUG: wrong_recurrence — last arg should be dp[i-1][j-1] for replace\n"
                "                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i][j-1])\n"
                "    return dp[m][n]\n"
            ),
            "correct_code": (
                "def min_edit_distance(s1, s2):\n"
                "    m, n = len(s1), len(s2)\n"
                "    dp = [[0] * (n + 1) for _ in range(m + 1)]\n"
                "    for i in range(m + 1): dp[i][0] = i\n"
                "    for j in range(n + 1): dp[0][j] = j\n"
                "    for i in range(1, m + 1):\n"
                "        for j in range(1, n + 1):\n"
                "            if s1[i-1] == s2[j-1]:\n"
                "                dp[i][j] = dp[i-1][j-1]\n"
                "            else:\n"
                "                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])\n"
                "    return dp[m][n]\n"
            ),
            "bug_type": "wrong_recurrence",
            "hint": "The three operations in edit distance are delete, insert, and replace — are all three represented correctly?",
            "difficulty": "extreme",
            "topic": "minimum edit distance (Levenshtein)",
            "test_cases": [
                {"input": "'horse', 'ros'",         "expected": "3", "label": "standard"},
                {"input": "'intention', 'execution'","expected": "5", "label": "complex"},
                {"input": "'', 'abc'",              "expected": "3", "label": "empty string"},
            ],
        },
    }.get(difficulty, {})


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🐛 Bug Generator — Testing all difficulty tiers\n")
    for level in ["easy", "medium", "hard", "extreme"]:
        print(f"{'═'*55}")
        print(f"  {level.upper()}")
        print(f"{'═'*55}")
        ch = generate_bug_challenge(level)
        print(f"  Topic    : {ch.get('topic', 'N/A')}")
        print(f"  Function : {ch.get('function_name', 'N/A')}")
        print(f"  Bug Type : {ch.get('bug_type', 'N/A')}")
        print(f"  Hint     : {ch.get('hint', 'N/A')}")
        print(f"\n  Buggy Code:\n{ch.get('buggy_code', '')}")
        print()