"""
scoring.py

This file contains the AI SafeHome fall-hazard scoring algorithm.

Important:
This score is not a medical diagnosis.
It is a simple educational home-safety hazard score.
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




def get_checklist_answer_points(answer):
    """
    Returns the points added by one checklist answer.
    """

    category = answer.get("category")
    response = answer.get("answer")
    points = HAZARD_POINTS.get(category, 0)

    if response == "yes":
        return points

    if response == "not_sure":
        return points * 0.5

    return 0



def calculate_score(ai_hazards, checklist_answers):
    """
    Combines AI hazards and checklist answers into a basic 0-100 score.

    AI hazards:
    - Each AI hazard adds its hazard point value.

    Checklist answers:
    - Yes = full points
    - Not sure = half points
    - No = 0 points
    - Not applicable = 0 points
    - Skipped = 0 points
    """

    score = 0

    for hazard in ai_hazards:
        category = hazard.get("category")
        score += HAZARD_POINTS.get(category, 0)

    for answer in checklist_answers:
        score += get_checklist_answer_points(answer)

    return min(round(score), 100)



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
    """

    ai_points = 0
    checklist_points = 0
    ai_items = []
    checklist_items = []

    for hazard in ai_hazards:
        category = hazard.get("category")
        points = HAZARD_POINTS.get(category, 0)
        ai_points += points

        if points > 0:
            ai_items.append(
                {
                    "source": "AI photo result",
                    "category": category,
                    "title": hazard.get("title", "Possible hazard"),
                    "points": points,
                }
            )

    for answer in checklist_answers:
        category = answer.get("category")
        points = get_checklist_answer_points(answer)
        checklist_points += points

        if points > 0:
            checklist_items.append(
                {
                    "source": "Checklist",
                    "category": category,
                    "question": answer.get("question", "Checklist item"),
                    "answer_label": answer.get("answer_label", answer.get("answer")),
                    "points": points,
                }
            )

    total_before_cap = ai_points + checklist_points
    final_score = min(round(total_before_cap), 100)

    return {
        "ai_points": round(ai_points, 1),
        "checklist_points": round(checklist_points, 1),
        "total_before_cap": round(total_before_cap, 1),
        "final_score": final_score,
        "ai_items": ai_items,
        "checklist_items": checklist_items,
    }