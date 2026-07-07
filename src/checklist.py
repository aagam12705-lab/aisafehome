"""
checklist.py

This file stores the manual safety checklist questions.

The checklist is important because AI may miss hazards.
The user reviews the room and answers simple questions.
"""

CHECKLIST_QUESTIONS = [
    {
        "id": "loose_rug",
        "category": "loose_rug",
        "text": "Are there loose rugs or mats?",
    },
    {
        "id": "cords",
        "category": "cords",
        "text": "Are cords crossing a walking path?",
    },
    {
        "id": "clutter",
        "category": "clutter",
        "text": "Is there clutter on the floor?",
    },
    {
        "id": "poor_lighting",
        "category": "poor_lighting",
        "text": "Is the room dim or poorly lit?",
    },
    {
        "id": "slippery_floor",
        "category": "slippery_floor",
        "text": "Are floors slippery or wet?",
    },
    {
        "id": "narrow_pathway",
        "category": "narrow_pathway",
        "text": "Is the walking path narrow or blocked?",
    },
    {
        "id": "stairs",
        "category": "stairs",
        "text": "Are there stairs or steps nearby?",
    },
    {
        "id": "handrail",
        "category": "handrail",
        "text": "Are handrails missing or hard to hold?",
    },
    {
        "id": "bathroom_grab_bars",
        "category": "bathroom_grab_bars",
        "text": "Is this a bathroom without grab bars?",
    },
    {
        "id": "hard_to_reach_items",
        "category": "hard_to_reach_items",
        "text": "Are commonly used items hard to reach?",
    },
]


ANSWER_OPTIONS = [
    "No",
    "Yes",
    "Not sure",
    "Not applicable",
]


ANSWER_VALUE_MAP = {
    "Yes": "yes",
    "No": "no",
    "Not sure": "not_sure",
    "Not applicable": "not_applicable",
}