from typing import Any, Dict, List

from src.constants import HAZARD_POINTS


def get_points_for_category(category: str | None) -> float:
    return float(HAZARD_POINTS.get(category or "unclear", 0))


def calculate_ai_points(ai_hazards: List[Dict[str, Any]]) -> float:
    total = 0.0

    for hazard in ai_hazards:
        total += get_points_for_category(hazard.get("category"))

    return total


def calculate_checklist_points(checklist_answers: List[Dict[str, Any]]) -> float:
    total = 0.0

    for answer in checklist_answers:
        points = get_points_for_category(answer.get("category"))
        response = answer.get("answer")

        if response == "yes":
            total += points
        elif response == "not_sure":
            total += points * 0.5

    return total


def cap_score(raw_score: float) -> int:
    return min(round(raw_score), 100)


def get_risk_level(score: int) -> str:
    if score < 30:
        return "Low Risk"

    if score < 60:
        return "Moderate Risk"

    return "High Risk"


def calculate_score(
    ai_hazards: List[Dict[str, Any]],
    checklist_answers: List[Dict[str, Any]],
) -> int:
    raw_score = calculate_ai_points(ai_hazards) + calculate_checklist_points(checklist_answers)
    return cap_score(raw_score)


def get_score_breakdown(
    ai_hazards: List[Dict[str, Any]],
    checklist_answers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    ai_points = calculate_ai_points(ai_hazards)
    checklist_points = calculate_checklist_points(checklist_answers)
    raw_score = ai_points + checklist_points
    final_score = cap_score(raw_score)

    return {
        "ai_points": round(ai_points, 1),
        "checklist_points": round(checklist_points, 1),
        "raw_score": round(raw_score, 1),
        "total_before_cap": round(raw_score, 1),
        "final_score": final_score,
        "risk_level": get_risk_level(final_score),
        "capped_points": max(0, round(raw_score - final_score, 1)),
        "explanation": (
            "Higher score means more possible fall hazards. "
            "The score combines AI-detected hazards and checklist concerns, then caps at 100."
        ),
    }


def format_score_explanation(score_breakdown: Dict[str, Any]) -> str:
    if not score_breakdown:
        return "No score breakdown is available yet."

    return f"""
Why this score?

AI hazard points: {score_breakdown.get("ai_points", 0)}
Checklist concern points: {score_breakdown.get("checklist_points", 0)}
Raw score before cap: {score_breakdown.get("raw_score", score_breakdown.get("total_before_cap", 0))}
Final score: {score_breakdown.get("final_score", 0)}/100
Risk label: {score_breakdown.get("risk_level", "Unknown")}

Higher score = more possible fall hazards.
Lower score = fewer possible fall hazards.
""".strip()