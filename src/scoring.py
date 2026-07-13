"""
scoring.py

This file contains the AI SafeHome fall-hazard scoring algorithm.

Important:
This score is not a medical diagnosis.
It is a simple educational home-safety hazard score.

Balanced scoring rule:
- Each hazard category is counted once.
- AI finding = full points.
- Checklist Yes = full points.
- Checklist Not sure = half points.
- If both AI and checklist identify the same category, use the higher value.
"""

HAZARD_POINTS = {
    "loose_rug": 10,
    "cords": 12,
    "clutter": 10,
    "poor_lighting": 8,
    "slippery_floor": 12,
    "narrow_pathway": 8,
    "stairs": 15,
    "handrail": 15,
    "bathroom_grab_bars": 15,
    "hard_to_reach_items": 6,

    # Expanded hazard categories
    "threshold_trip": 10,
    "unstable_furniture": 10,
    "pet_items": 6,
    "footwear": 6,
    "low_seating": 8,
    "poor_contrast": 6,
    "uneven_floor": 12,
    "door_mat": 8,
    "furniture_in_path": 8,
    "outdoor_surface": 12,
    "laundry_on_floor": 8,
    "open_drawers_cabinets": 8,
}


def get_checklist_points(category, response):
    """
    Converts one checklist answer into points.
    """

    base_points = HAZARD_POINTS.get(category, 0)

    if response == "yes":
        return base_points

    if response == "not_sure":
        return base_points * 0.5

    return 0


def calculate_score(ai_hazards, checklist_answers):
    """
    Combines AI hazards and checklist answers into a balanced 0-100 score.

    Important:
    The same hazard category is counted only once.

    Example:
    - AI finds cords: 12 points
    - Checklist says cords = Yes: 12 points
    - Final cords contribution: 12 points, not 24
    """

    category_scores = {}

    # Add AI findings
    for hazard in ai_hazards:
        category = hazard.get("category")
        points = HAZARD_POINTS.get(category, 0)

        if points > 0:
            category_scores[category] = max(
                category_scores.get(category, 0),
                points,
            )

    # Add checklist findings
    for answer in checklist_answers:
        category = answer.get("category")
        response = answer.get("answer")
        points = get_checklist_points(category, response)

        if points > 0:
            category_scores[category] = max(
                category_scores.get(category, 0),
                points,
            )

    total_score = sum(category_scores.values())

    return min(round(total_score), 100)


def get_risk_level(score):
    """
    Converts the numeric score into a simple risk label.
    """

    if score < 30:
        return "Low Risk"
    elif score < 60:
        return "Moderate Risk"
    else:
        return "High Risk"


def get_score_breakdown(ai_hazards, checklist_answers):
    """
    Creates a detailed score breakdown for display.

    This version explains balanced scoring:
    overlapping AI/checklist categories are not double counted.
    """

    ai_items = []
    checklist_items = []
    category_scores = {}
    category_sources = {}

    raw_ai_points = 0
    raw_checklist_points = 0

    # Track AI hazard points
    for hazard in ai_hazards:
        category = hazard.get("category")
        points = HAZARD_POINTS.get(category, 0)

        if points <= 0:
            continue

        raw_ai_points += points

        ai_items.append(
            {
                "source": "AI photo result",
                "category": category,
                "title": hazard.get("title", "Possible hazard"),
                "points": points,
            }
        )

        if points > category_scores.get(category, 0):
            category_scores[category] = points
            category_sources[category] = "AI"

    # Track checklist points
    for answer in checklist_answers:
        category = answer.get("category")
        response = answer.get("answer")
        points = get_checklist_points(category, response)

        if points <= 0:
            continue

        raw_checklist_points += points

        checklist_items.append(
            {
                "source": "Checklist",
                "category": category,
                "question": answer.get("question", "Checklist item"),
                "answer_label": answer.get("answer_label", response),
                "points": points,
            }
        )

        if points > category_scores.get(category, 0):
            category_scores[category] = points
            category_sources[category] = "Checklist"
        elif points == category_scores.get(category, 0):
            old_source = category_sources.get(category, "")
            if old_source == "AI":
                category_sources[category] = "AI + Checklist"

    total_before_cap = sum(category_scores.values())
    final_score = min(round(total_before_cap), 100)

    category_items = []

    for category, points in category_scores.items():
        category_items.append(
            {
                "category": category,
                "points": points,
                "source": category_sources.get(category, "Unknown"),
            }
        )

    category_items = sorted(
        category_items,
        key=lambda item: item["points"],
        reverse=True,
    )

    return {
        "ai_points": round(raw_ai_points, 1),
        "checklist_points": round(raw_checklist_points, 1),
        "total_before_cap": round(total_before_cap, 1),
        "final_score": final_score,
        "ai_items": ai_items,
        "checklist_items": checklist_items,
        "category_items": category_items,
        "scoring_note": (
            "Balanced scoring is used: each hazard category is counted once. "
            "If AI and checklist both identify the same category, the app uses the higher value instead of double counting."
        ),
    }