def get_common_prefix(codes: list[str]) -> str:
    """Find the longest common prefix of a list of strings."""
    if not codes:
        return ""

    # Sort to easily find common parts between extreme members
    codes = [str(c) for c in codes if c]
    if not codes:
        return ""

    codes.sort()

    first = codes[0]
    last = codes[-1]

    i = 0
    while i < len(first) and i < len(last) and first[i] == last[i]:
        i += 1

    return first[:i]


def detect_ambiguity(scores: list[float], threshold: float = 0.05) -> bool:
    """Detect if the top results are too close to be certain."""
    if len(scores) < 2:
        return False

    # If the gap between Top-1 and Top-2 is smaller than the threshold
    # relative to the Top-1 score.
    # We use a margin based on the highest score.
    margin = (scores[0] - scores[1]) / (scores[0] + 1e-9)
    return margin < threshold
