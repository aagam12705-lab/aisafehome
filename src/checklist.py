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
        "text": "Are handrails missing, loose, or hard to hold?",
    },
    {
        "id": "bathroom_grab_bars",
        "category": "bathroom_grab_bars",
        "text": "Is this a bathroom without visible grab bars?",
    },
    {
        "id": "hard_to_reach_items",
        "category": "hard_to_reach_items",
        "text": "Are commonly used items hard to reach?",
    },

    # New checklist questions
    {
        "id": "threshold_trip",
        "category": "threshold_trip",
        "text": "Are there raised thresholds or floor transitions that could catch someone's foot?",
    },
    {
        "id": "unstable_furniture",
        "category": "unstable_furniture",
        "text": "Is there furniture that looks unstable, wobbly, or easy to bump into?",
    },
    {
        "id": "pet_items",
        "category": "pet_items",
        "text": "Are pet bowls, toys, beds, or leashes in the walking path?",
    },
    {
        "id": "footwear",
        "category": "footwear",
        "text": "Are shoes, slippers, or sandals left in the walking path?",
    },
    {
        "id": "low_seating",
        "category": "low_seating",
        "text": "Is there very low seating that may be hard to sit in or stand up from?",
    },
    {
        "id": "poor_contrast",
        "category": "poor_contrast",
        "text": "Are step edges, thresholds, or floor changes hard to see?",
    },
    {
        "id": "uneven_floor",
        "category": "uneven_floor",
        "text": "Are there uneven floor areas, lifted edges, bumps, or damaged flooring?",
    },
    {
        "id": "door_mat",
        "category": "door_mat",
        "text": "Is there a loose door mat near an entrance?",
    },
    {
        "id": "furniture_in_path",
        "category": "furniture_in_path",
        "text": "Is furniture blocking or narrowing the walking path?",
    },
    {
        "id": "outdoor_surface",
        "category": "outdoor_surface",
        "text": "Are outdoor walking areas wet, icy, uneven, leafy, or blocked?",
    },
    {
        "id": "laundry_on_floor",
        "category": "laundry_on_floor",
        "text": "Is laundry, clothing, or a laundry basket on the floor?",
    },
    {
        "id": "open_drawers_cabinets",
        "category": "open_drawers_cabinets",
        "text": "Are drawers, cabinet doors, or appliance doors left open into the walking path?",
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