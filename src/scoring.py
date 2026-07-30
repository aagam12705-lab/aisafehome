from typing import Any, Dict, List

from src.constants import HAZARD_POINTS


def get_points_for_category(category: str | None) -> float:
    return float(HAZARD_POINTS.get(category or "unclear", 0))


def calculate_ai_points(ai_hazards: List[Dict[str, Any]]) -> float:
    total = 0.0

    for hazard in ai_hazards:
        category = hazard.get("category") or "unclear"
        try:
            points = int(hazard.get("risk_points"))
        except (TypeError, ValueError):
            points = int(HAZARD_POINTS.get(category, 8))

        # The category table remains the backup if a response is missing or
        # produces an unusable per-hazard assessment.
        if not 1 <= points <= 20:
            points = int(HAZARD_POINTS.get(category, 8))

        total += points

    return total


def calculate_checklist_points(checklist_answers: List[Dict[str, Any]]) -> float:
    total = 0.0

    for answer in checklist_answers:
        points = get_points_for_category(answer.get("category")) * 0.8
        response = answer.get("answer")

        # Follow-up questions are deliberately phrased as positive safety
        # conditions. A "No" therefore identifies the possible concern.
        if response == "no":
            total += points
        elif response == "not_sure":
            total += points * 0.35

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
    skip_buffer_points: int = 0,
) -> int:
    raw_score = calculate_ai_points(ai_hazards) + calculate_checklist_points(checklist_answers) + max(0, min(int(skip_buffer_points), 15))
    return cap_score(raw_score)


def get_score_breakdown(
    ai_hazards: List[Dict[str, Any]],
    checklist_answers: List[Dict[str, Any]],
    skip_buffer_points: int = 0,
) -> Dict[str, Any]:
    ai_points = calculate_ai_points(ai_hazards)
    ai_assessed_hazards = sum(
        1 for hazard in ai_hazards
        if hazard.get("risk_points_source") in {"AI assessment", "AI severity assessment"}
    )
    backup_scored_hazards = max(0, len(ai_hazards) - ai_assessed_hazards)
    checklist_points = calculate_checklist_points(checklist_answers)
    skip_buffer_points = max(0, min(int(skip_buffer_points), 15))
    raw_score = ai_points + checklist_points + skip_buffer_points
    final_score = cap_score(raw_score)

    return {
        "ai_points": round(ai_points, 1),
        "ai_assessed_hazards": ai_assessed_hazards,
        "backup_scored_hazards": backup_scored_hazards,
        "checklist_points": round(checklist_points, 1),
        "skip_buffer_points": skip_buffer_points,
        "raw_score": round(raw_score, 1),
        "total_before_cap": round(raw_score, 1),
        "final_score": final_score,
        "risk_level": get_risk_level(final_score),
        "capped_points": max(0, round(raw_score - final_score, 1)),
        "explanation": (
            "Higher score means more possible fall hazards. "
            "AI assigns points to each possible hazard separately. If an AI score is unavailable, the app uses the category value as a backup. Confirmed follow-up concerns and any AI-recommended uncertainty buffer are then added. The final score caps at 100."
        ),
    }


def format_score_explanation(score_breakdown: Dict[str, Any]) -> str:
    if not score_breakdown:
        return "No score breakdown is available yet."

    return f"""
Why this score?

AI hazard points: {score_breakdown.get("ai_points", 0)}
AI-assessed hazards: {score_breakdown.get("ai_assessed_hazards", 0)}
Category-backup hazards: {score_breakdown.get("backup_scored_hazards", 0)}
Checklist concern points: {score_breakdown.get("checklist_points", 0)}
Skipped follow-up buffer: {score_breakdown.get("skip_buffer_points", 0)}
Raw score before cap: {score_breakdown.get("raw_score", score_breakdown.get("total_before_cap", 0))}
Final score: {score_breakdown.get("final_score", 0)}/100
Risk label: {score_breakdown.get("risk_level", "Unknown")}

Higher score = more possible fall hazards.
Lower score = fewer possible fall hazards.
The final score cannot exceed 100.
""".strip()
