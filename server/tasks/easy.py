EASY_TASKS = [
    {
        "id": "easy",
        "title": "syntax_fix — average",
        "buggy_code": "def average(lst): return sum(lst) / len(lst)",
        "hint": "Handle empty list",
        "test_cases": [
            (([1, 2, 3],), 2.0),
            (([5, 5],), 5.0)
        ],
        "edge_cases": [
            (([],), 0.0)
        ],
        "max_attempts": 1
    }
]