MEDIUM_TASKS = [
    {
        "id": "medium",
        "title": "logic_fix — fibonacci",
        "buggy_code": (
            "def fibonacci(n):\n"
            "    result = []\n"
            "    a, b = 0, 0\n"
            "    for _ in range(n):\n"
            "        result.append(a)\n"
            "        a, b = b, a + b\n"
            "    return result"
        ),
        "hint": "Check initial values of a and b",
        "test_cases": [
            ((5,), [0,1,1,2,3]),
            ((1,), [0])
        ],
        "edge_cases": [
            ((0,), [])
        ],
        "max_attempts": 3
    }
]