HARD_TASKS = [
    {
        "id": "hard",
        "title": "refactor_and_fix — sieve_of_eratosthenes",
        "buggy_code": (
            "def sieve_of_eratosthenes(n):\n"
            "    primes = [True] * 100\n"
            "    primes[0] = primes[1] = False\n"
            "    for i in range(2, int(n**0.5) + 1):\n"
            "        if primes[i]:\n"
            "            for j in range(i*i, 100, i):\n"
            "                primes[j] = False\n"
            "    return [i for i in range(n+1) if primes[i]]"
        ),
        "hint": "Avoid hardcoded 100, use n instead",
        "test_cases": [
            ((10,), [2,3,5,7])
        ],
        "edge_cases": [
            ((1,), []),
            ((0,), [])
        ],
        "max_attempts": 5
    }
]