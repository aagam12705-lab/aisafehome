"""
ai_analysis.py

This file handles photo analysis.

In Milestone 5, we are using fake/sample AI results.
Real OpenAI vision analysis will be added later after the full app flow works.
"""


def analyze_photo(image_file, room_type):
    """
    Returns fake AI-style hazard results.

    Args:
        image_file: The uploaded image file. Not actually analyzed yet.
        room_type: The room selected by the user.

    Returns:
        dict: A fake AI result with summary, hazards, not_visible, and safety reminder.
    """

    room_type_lower = room_type.lower()

    if room_type_lower == "bathroom":
        hazards = [
            {
                "category": "bathroom_grab_bars",
                "title": "Bathroom without visible grab bars",
                "explanation": (
                    "Grab bars may help people steady themselves near a toilet, shower, "
                    "or bathtub. This photo does not clearly show grab bars."
                ),
                "recommendation": (
                    "Consider adding properly installed grab bars near the toilet, shower, "
                    "or bathtub."
                ),
            },
            {
                "category": "slippery_floor",
                "title": "Possible slippery floor area",
                "explanation": (
                    "Bathroom floors can become slippery when wet, which may increase "
                    "the chance of slipping."
                ),
                "recommendation": (
                    "Use non-slip mats and keep the floor dry. Avoid loose towels or mats "
                    "in walking areas."
                ),
            },
        ]
    elif room_type_lower == "stairs":
        hazards = [
            {
                "category": "stairs",
                "title": "Stairs or step hazard",
                "explanation": (
                    "Steps can increase fall risk, especially if edges are hard to see "
                    "or the area is dim."
                ),
                "recommendation": (
                    "Keep stairs clear, improve lighting, and make step edges easy to see."
                ),
            },
            {
                "category": "handrail",
                "title": "Handrail should be checked",
                "explanation": (
                    "A missing, loose, or hard-to-grip handrail can make stairs less safe."
                ),
                "recommendation": (
                    "Make sure the handrail is secure, easy to grip, and available along "
                    "the stairs."
                ),
            },
        ]
    elif room_type_lower == "hallway":
        hazards = [
            {
                "category": "poor_lighting",
                "title": "Possible poor lighting",
                "explanation": (
                    "Dim lighting can make it harder to see objects, floor changes, or "
                    "tripping hazards."
                ),
                "recommendation": (
                    "Add brighter lighting or night lights, especially along walking paths."
                ),
            },
            {
                "category": "narrow_pathway",
                "title": "Narrow or blocked pathway",
                "explanation": (
                    "A narrow walking path can make it harder to move safely through the area."
                ),
                "recommendation": (
                    "Move furniture or objects so the walking path is wide and clear."
                ),
            },
        ]
    else:
        hazards = [
            {
                "category": "cords",
                "title": "Cord near walking path",
                "explanation": (
                    "A cord near a walking area can create a tripping hazard."
                ),
                "recommendation": (
                    "Move the cord along the wall or secure it with a cord cover."
                ),
            },
            {
                "category": "loose_rug",
                "title": "Possible loose rug",
                "explanation": (
                    "A rug can slide or catch someone’s foot if it does not have a "
                    "non-slip backing."
                ),
                "recommendation": (
                    "Use non-slip backing, tape down the edges, or remove the rug from "
                    "the walking path."
                ),
            },
            {
                "category": "clutter",
                "title": "Floor clutter",
                "explanation": (
                    "Objects on the floor can make walking paths harder to use safely."
                ),
                "recommendation": (
                    "Clear small objects, bags, shoes, or boxes from the walking path."
                ),
            },
        ]

    return {
        "summary": (
            "This is a sample AI-style result. The app is showing possible hazards "
            "for demo purposes, but the photo is not being analyzed yet."
        ),
        "hazards": hazards,
        "not_visible": [
            "Lighting level cannot be fully judged from one photo.",
            "Floor slipperiness cannot be confirmed from the image.",
            "Some hazards may be outside the camera view.",
        ],
        "safety_reminder": (
            "AI may miss hazards. Please review the room yourself and consider asking "
            "a qualified professional for serious safety concerns."
        ),
    }