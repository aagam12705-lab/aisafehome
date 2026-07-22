"""
comparison.py

Before/after comparison helpers for AI SafeHome.
"""

from typing import Any, Dict, List, Set


def sort_checks_oldest_to_newest(checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(checks, key=lambda row: str(row.get("created_at", "")))


def get_check_display_label(check: Dict[str, Any]) -> str:
    check_id = str(check.get("id", ""))[:8]
    created_at = str(check.get("created_at", "Unknown time")).replace("T", " ")
    score = check.get("score", "Unknown")
    risk_level = check.get("risk_level", "Unknown")

    return f"{created_at} | {score}/100 | {risk_level} | {check_id}"


def get_ai_hazard_details(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        detail
        for detail in details
        if detail.get("detail_type") == "ai_hazard"
    ]


def get_hazard_categories(details: List[Dict[str, Any]]) -> Set[str]:
    categories = set()

    for detail in get_ai_hazard_details(details):
        category = detail.get("category")

        if category:
            categories.add(category)

    return categories


def get_hazard_titles(details: List[Dict[str, Any]]) -> Set[str]:
    titles = set()

    for detail in get_ai_hazard_details(details):
        title = detail.get("title")

        if title:
            titles.add(str(title))

    return titles


def compare_hazard_categories(
    before_details: List[Dict[str, Any]],
    after_details: List[Dict[str, Any]],
) -> Dict[str, Set[str]]:
    before_categories = get_hazard_categories(before_details)
    after_categories = get_hazard_categories(after_details)

    return {
        "resolved": before_categories - after_categories,
        "still_present": before_categories & after_categories,
        "new": after_categories - before_categories,
    }


def get_score_delta(
    before_check: Dict[str, Any],
    after_check: Dict[str, Any],
) -> int:
    before_score = int(before_check.get("score") or 0)
    after_score = int(after_check.get("score") or 0)

    return after_score - before_score


def get_score_change_message(
    before_check: Dict[str, Any],
    after_check: Dict[str, Any],
) -> str:
    delta = get_score_delta(before_check, after_check)

    if delta < 0:
        return f"Score improved by {abs(delta)} points."

    if delta > 0:
        return f"Score increased by {delta} points, so this room may need more attention."

    return "Score stayed the same."


def build_before_after_summary_text(
    before_check: Dict[str, Any],
    after_check: Dict[str, Any],
    resolved_labels: List[str],
    still_present_labels: List[str],
    new_labels: List[str],
) -> str:
    before_score = before_check.get("score", "Unknown")
    after_score = after_check.get("score", "Unknown")

    resolved_text = "\n".join(f"- {item}" for item in resolved_labels) or "- None"
    still_text = "\n".join(f"- {item}" for item in still_present_labels) or "- None"
    new_text = "\n".join(f"- {item}" for item in new_labels) or "- None"

    return f"""
AI SafeHome Before/After Room Comparison

Before:
Score: {before_score}/100
Risk Label: {before_check.get("risk_level", "Unknown")}
Saved At: {before_check.get("created_at", "Unknown")}

After:
Score: {after_score}/100
Risk Label: {after_check.get("risk_level", "Unknown")}
Saved At: {after_check.get("created_at", "Unknown")}

Score Change:
{get_score_change_message(before_check, after_check)}

Resolved Hazard Categories:
{resolved_text}

Still Present Hazard Categories:
{still_text}

New Hazard Categories:
{new_text}

Reminder:
This comparison is educational. AI may miss hazards, and a human should review the room.
""".strip()