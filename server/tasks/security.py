SECURITY_TASKS = [
    {
        "id": "security",
        "title": "security_fix — sanitize_input",
        "buggy_code": (
            "def sanitize_input(user_input):\n"
            "    return user_input.replace(\"'\", \"\")"
        ),
        "hint": "Also handle ;, -- and None input",
        "test_cases": [
            (("hello",), "hello"),
            (("it's fine",), "its fine"),
            (("; DROP TABLE users--",), " DROP TABLE users"),
        ],
        "edge_cases": [
            ((None,), ""),
            (("'; DROP TABLE users; --",), " DROP TABLE users "),
        ],
        "max_attempts": 3
    }
]