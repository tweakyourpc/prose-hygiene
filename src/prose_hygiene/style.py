"""Deterministic style-aware punctuation rewriting for U+2014."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field


EM_DASH = "\u2014"
LIST_MARKER_RE = re.compile(r"^(?P<lead>\s*(?:[-*+]\s+|\d+\.\s+))(?P<body>.+)$")
SERIAL_SPLIT_RE = re.compile(r"\s*—\s*")
TRANSITION_PREFIXES = (
    "and",
    "at least",
    "because",
    "but",
    "especially",
    "even though",
    "for now",
    "instead",
    "just",
    "maybe",
    "perhaps",
    "rather",
    "so",
    "still",
    "then",
    "though",
    "while",
    "yet",
)
PARENTHETICAL_PREFIXES = (
    "as ",
    "which ",
    "who ",
    "whose ",
    "where ",
    "when ",
    "while ",
    "with ",
    "without ",
)
COLON_CUE_RE = re.compile(
    r"\b(is|are|was|were|means|meant|remains|remained|looks|looked|sounds|sounded|feels|felt|goal|result|plan|rule)\b",
    re.IGNORECASE,
)
ACTION_PREFIXES = (
    "by ",
    "just ",
    "paste ",
    "review ",
    "run ",
    "set up ",
    "to ",
    "use ",
)
SHORT_LABEL_TERMS = frozenset(
    {
        "guide",
        "logic",
        "priority",
        "reference",
        "sheet",
        "status",
        "tab",
        "tiers",
        "values",
    }
)


@dataclass(frozen=True)
class RewriteResult:
    """Outcome of one document rewrite pass."""

    text: str
    count: int
    strategies: dict[str, int] = field(default_factory=dict)


def _word_count(text: str) -> int:
    return len(text.split())


def _looks_parenthetical(middle: str) -> bool:
    lowered = middle.strip().lower()
    return (
        2 <= _word_count(middle) <= 14
        and not middle.endswith((".", "!", "?"))
        and any(lowered.startswith(prefix) for prefix in PARENTHETICAL_PREFIXES)
    )


def _looks_descriptor(label: str) -> bool:
    if _word_count(label) > 6:
        return False
    lowered = f" {label.lower()} "
    return not any(token in lowered for token in (" is ", " are ", " was ", " were ", " has ", " have "))


def _should_use_comma(right: str) -> bool:
    lowered = right.strip().lower()
    return any(lowered.startswith(prefix) for prefix in TRANSITION_PREFIXES)


def _should_use_colon(left: str, right: str) -> bool:
    right_lower = right.strip().lower()
    if "=" in right and 1 <= _word_count(left) <= 5:
        return True
    if "=" in left and 1 <= _word_count(right) <= 4:
        return True
    if any(right_lower.startswith(prefix) for prefix in ACTION_PREFIXES):
        return bool(COLON_CUE_RE.search(left))
    if right_lower.startswith(("for example", "namely", "specifically")):
        return True
    return False


def _is_title_fragment(text: str) -> bool:
    words = [word for word in re.split(r"\s+", text.strip()) if word]
    if not words or len(words) > 8:
        return False
    for word in words:
        stripped = word.strip("()[]{}:;,.'\"")
        if not stripped:
            continue
        if stripped[0].isdigit():
            continue
        if stripped[0].isupper():
            continue
        if stripped.lower() in {"and", "of", "the", "for", "in", "to", "&"}:
            continue
        return False
    return True


def _looks_heading_style(left: str, right: str, line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped != line:
        return False
    if stripped.endswith((".", "!", "?", ":", ";")):
        return False
    if "\t" in stripped or stripped.startswith(("-", "*", "+")):
        return False
    if left.lower().startswith("step ") and 1 <= _word_count(right) <= 10:
        return True
    if _is_title_fragment(left) and _is_title_fragment(right):
        return True
    left_words = left.split()
    if 1 <= len(left_words) <= 5 and left_words[-1].lower() in SHORT_LABEL_TERMS:
        return True
    return False


def _rewrite_single_dash(line: str) -> tuple[str, Counter[str]]:
    left, right = [part.strip() for part in line.split(EM_DASH, 1)]
    strategies: Counter[str] = Counter()

    list_match = LIST_MARKER_RE.match(line)
    if list_match is not None:
        body = list_match.group("body")
        if body.count(EM_DASH) == 1:
            label, detail = [part.strip() for part in body.split(EM_DASH, 1)]
            if _looks_descriptor(label):
                strategies["colon"] += 1
                return f"{list_match.group('lead')}{label}: {detail}", strategies

    if _looks_heading_style(left, right, line):
        strategies["colon"] += 1
        return f"{left}: {right}", strategies

    if _should_use_colon(left, right):
        strategies["colon"] += 1
        return f"{left}: {right}", strategies

    if _should_use_comma(right):
        strategies["comma"] += 1
        return f"{left}, {right}", strategies

    strategies["comma"] += 1
    return f"{left}, {right}", strategies


def _rewrite_parenthetical(line: str) -> tuple[str | None, Counter[str]]:
    parts = [part.strip() for part in SERIAL_SPLIT_RE.split(line)]
    if len(parts) != 3:
        return None, Counter()
    middle = parts[1]
    if not _looks_parenthetical(middle):
        return None, Counter()
    return f"{parts[0]} ({middle}) {parts[2]}", Counter({"parentheses": 2})


def _rewrite_serial_sequence(line: str) -> tuple[str | None, Counter[str]]:
    parts = [part.strip() for part in SERIAL_SPLIT_RE.split(line)]
    if len(parts) < 3:
        return None, Counter()
    if any(not part for part in parts):
        return None, Counter()
    if any(_word_count(part) > 10 for part in parts[:-1]):
        return None, Counter()
    return ", ".join(parts), Counter({"comma": len(parts) - 1})


def _normalize_heading_comma(line: str) -> tuple[str | None, Counter[str]]:
    if EM_DASH in line or line.count(",") != 1:
        return None, Counter()
    left, right = [part.strip() for part in line.split(",", 1)]
    if not left or not right:
        return None, Counter()
    if _looks_heading_style(left, right, line):
        return f"{left}: {right}", Counter({"colon": 1})
    return None, Counter()


def rewrite_line(line: str, normalize_heading_commas: bool = False) -> tuple[str, int, dict[str, int]]:
    """Rewrite one documentation line."""
    count = line.count(EM_DASH)
    if count == 0:
        if normalize_heading_commas:
            normalized, strategies = _normalize_heading_comma(line)
            if normalized is not None:
                return normalized, 1, dict(strategies)
        return line, 0, {}

    parenthetical, strategies = _rewrite_parenthetical(line)
    if parenthetical is not None:
        return parenthetical, count, dict(strategies)

    serial, strategies = _rewrite_serial_sequence(line)
    if serial is not None:
        return serial, count, dict(strategies)

    if count == 1:
        rewritten, strategies = _rewrite_single_dash(line)
        return rewritten, count, dict(strategies)

    rewritten = line.replace(EM_DASH, ",")
    return rewritten, count, {"comma": count}


def rewrite_document_text(text: str, normalize_heading_commas: bool = False) -> RewriteResult:
    """Rewrite a documentation-like string with deterministic punctuation heuristics."""
    total = 0
    strategies: Counter[str] = Counter()
    output_lines: list[str] = []
    in_fence = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            output_lines.append(line)
            continue

        if in_fence:
            output_lines.append(line)
            continue

        rewritten, count, line_strategies = rewrite_line(line, normalize_heading_commas=normalize_heading_commas)
        output_lines.append(rewritten)
        total += count
        strategies.update(line_strategies)

    suffix = "\n" if text.endswith("\n") else ""
    return RewriteResult(
        text="\n".join(output_lines) + suffix,
        count=total,
        strategies=dict(strategies),
    )
