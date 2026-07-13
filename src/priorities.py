"""
priorities.py

Adds simple fix-priority labels to AI SafeHome hazards and recommendations.

This does not diagnose medical risk.
It only helps users decide which visible home-safety concerns to review first.
"""

PRIORITY_FIX_NOW = "Fix Now"
PRIORITY_FIX_SOON = "Fix Soon"
PRIORITY_WATCH_REVIEW = "Watch/Review"


CATEGORY_PRIORITY = {
    "cords": PRIORITY_FIX_NOW,
    "slippery_floor": PRIORITY_FIX_NOW,
    "stairs": PRIORITY_FIX_NOW,
    "handrail": PRIORITY_FIX_NOW,
    "bathroom_grab_bars": PRIORITY_FIX_NOW,

    "loose_rug": PRIORITY_FIX_SOON,
    "clutter": PRIORITY_FIX_SOON,
    "narrow_pathway": PRIORITY_FIX_SOON,
    "poor_lighting": PRIORITY_FIX_SOON,
    "hard_to_reach_items": PRIORITY_FIX_SOON,

    "unclear": PRIORITY_WATCH_REVIEW,
    "threshold_trip": PRIORITY_FIX_NOW,
    "uneven_floor": PRIORITY_FIX_NOW,
    "outdoor_surface": PRIORITY_FIX_NOW,
    "open_drawers_cabinets": PRIORITY_FIX_NOW,

    "unstable_furniture": PRIORITY_FIX_SOON,
    "door_mat": PRIORITY_FIX_SOON,
    "furniture_in_path": PRIORITY_FIX_SOON,
    "laundry_on_floor": PRIORITY_FIX_SOON,
    "low_seating": PRIORITY_FIX_SOON,
    "poor_contrast": PRIORITY_FIX_SOON,

    "pet_items": PRIORITY_WATCH_REVIEW,
    "footwear": PRIORITY_WATCH_REVIEW,
}


PRIORITY_ORDER = {
    PRIORITY_FIX_NOW: 1,
    PRIORITY_FIX_SOON: 2,
    PRIORITY_WATCH_REVIEW: 3,
}


def get_priority_for_category(category):
    """
    Returns a priority label for a hazard category.
    """

    return CATEGORY_PRIORITY.get(category, PRIORITY_WATCH_REVIEW)


def get_priority_for_hazard(hazard):
    """
    Returns a priority label for an AI hazard dictionary.
    """

    category = hazard.get("category", "unclear")
    return get_priority_for_category(category)


def get_priority_for_checklist_answer(answer):
    """
    Returns a priority label for a checklist concern.

    Not sure answers are marked Watch/Review because the user could not confirm the hazard.
    """

    response = answer.get("answer")
    category = answer.get("category", "unclear")

    if response == "not_sure":
        return PRIORITY_WATCH_REVIEW

    if response == "yes":
        return get_priority_for_category(category)

    return None


def get_priority_css_class(priority):
    """
    Converts a priority label into a CSS class name.
    """

    if priority == PRIORITY_FIX_NOW:
        return "priority-fix-now"

    if priority == PRIORITY_FIX_SOON:
        return "priority-fix-soon"

    return "priority-watch-review"


def sort_by_priority(items):
    """
    Sorts dictionaries that contain a 'priority' key.
    """

    return sorted(
        items,
        key=lambda item: PRIORITY_ORDER.get(
            item.get("priority", PRIORITY_WATCH_REVIEW),
            99,
        ),
    )