"""
KAN-58: Longest Substring Without Repeating Characters

Given a string, find the length of the longest substring without repeating characters.
Uses sliding window + set for O(n) time, O(min(n, alphabet)) space.
"""


def length_of_longest_substring(s: str) -> int:
    """
    Return the length of the longest substring without repeating characters.

    Examples:
        "abcabcbb" -> 3 ("abc")
        "bbbbb" -> 1 ("b")
        "pwwkew" -> 3 ("wke" or "kew")
    """
    if not s:
        return 0
    seen: set[str] = set()
    left = 0
    best = 0
    for right, c in enumerate(s):
        while c in seen:
            seen.discard(s[left])
            left += 1
        seen.add(c)
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("pwwkew") == 3
    assert length_of_longest_substring("") == 0
    assert length_of_longest_substring("a") == 1
    print("All tests passed.")
