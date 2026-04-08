def make_task(
    id: str,
    difficulty: str,
    title: str,
    function_name: str,
    buggy_code: str,
    hint: str,
    test_cases: list,
    edge_cases: list = None,
    max_attempts: int = 3,
    requires_validation: bool = False,
    requires_no_magic: bool = False,
    tags: list = None,
):
    """Creates a standardized task dictionary."""

    def normalize(tc_list):
        normalized = []
        for tc in tc_list:
            # Already correct format
            if isinstance(tc, dict):
                normalized.append(tc)
            else:
                # Convert tuple → dict
                args, expected = tc
                normalized.append({
                    "args": list(args),
                    "expected": expected,
                    "description": ""
                })
        return normalized

    return {
        "id": id,
        "difficulty": difficulty,
        "title": title,
        "function_name": function_name,
        "buggy_code": buggy_code,
        "hint": hint,
        "test_cases": normalize(test_cases),
        "edge_cases": normalize(edge_cases or []),
        "max_attempts": max_attempts,
        "requires_validation": requires_validation,
        "requires_no_magic": requires_no_magic,
        "tags": tags or [],
    }