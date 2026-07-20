"""
fixes.py

Top 5 fix recommendation logic for AI SafeHome.
"""

from typing import Any, Dict, List, Set

from src.constants import (
    GENERIC_RECOMMENDATIONS,
    HAZARD_POINTS,
    PRIORITY_ORDER,
    PRIORITY_WATCH_REVIEW,
)
from src.priorities import get_priority_for_category, get_priority_for_hazard


def get_recommended_first_fixes(
    ai_hazards: List[Dict[str, Any]],
    checklist_answers: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Builds Top 5 recommended fixes.

    Ranking preference:
    1. Fix Now before Fix Soon before Watch/Review
    2. Hazards found by both AI and checklist
    3. Higher-point categories
    4. Duplicate recommendations removed
    """

    fixes: List[Dict[str, Any]] = []
    seen_recommendations: Set[str] = set()

    ai_categories = {
        hazard.get("category")
        for hazard in ai_hazards
        if hazard.get("category")
    }

    checklist_concern_categories = {
        answer.get("category")
        for answer in checklist_answers
        if answer.get("answer") in ["yes", "not_sure"] and answer.get("category")
    }

    overlapping_categories = ai_categories & checklist_concern_categories

    for hazard in ai_hazards:
        recommendation = hazard.get("recommendation")
        category = hazard.get("category") or "unclear"

        if not recommendation or recommendation in seen_recommendations:
            continue

        priority = get_priority_for_hazard(hazard)

        fixes.append(
            {
                "priority": priority,
                "text": recommendation,
                "source": hazard.get("title", "AI hazard"),
                "category": category,
                "overlap": category in overlapping_categories,
                "points": HAZARD_POINTS.get(category, 0),
            }
        )

        seen_recommendations.add(recommendation)

    for answer in checklist_answers:
        if answer.get("answer") not in ["yes", "not_sure"]:
            continue

        category = answer.get("category") or "unclear"
        recommendation = GENERIC_RECOMMENDATIONS.get(category)

        if not recommendation or recommendation in seen_recommendations:
            continue

        if answer.get("answer") == "not_sure":
            priority = PRIORITY_WATCH_REVIEW
        else:
            priority = get_priority_for_category(category)

        fixes.append(
            {
                "priority": priority,
                "text": recommendation,
                "source": answer.get("question", "Checklist concern"),
                "category": category,
                "overlap": category in overlapping_categories,
                "points": HAZARD_POINTS.get(category, 0),
            }
        )

        seen_recommendations.add(recommendation)

    ranked = sorted(
        fixes,
        key=lambda item: (
            PRIORITY_ORDER.get(item.get("priority"), 99),
            0 if item.get("overlap") else 1,
            -int(item.get("points", 0)),
            str(item.get("text", "")),
        ),
    )

    top_fixes = ranked[:limit]

    for index, fix in enumerate(top_fixes, start=1):
        fix["rank"] = index

    return top_fixes


def build_top_fixes_text(fixes: List[Dict[str, Any]]) -> str:
    """
    Builds plain text for Top 5 fixes.
    """

    if not fixes:
        return "No specific fixes were generated."

    lines = []

    for index, fix in enumerate(fixes[:5], start=1):
        lines.append(
            f"{index}. [{fix.get('priority')}] {fix.get('text')}\n"
            f"   Source: {fix.get('source')}"
        )

    return "\n".join(lines)