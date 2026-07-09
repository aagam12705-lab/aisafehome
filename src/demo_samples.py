"""
demo_samples.py

Built-in demo scenarios for AI SafeHome.

These are used when the user wants to demo the app without uploading a real photo.
No personal data, no patient photos, and no stored images are used.
"""


DEMO_SAMPLE_OPTIONS = [
    "Living room with cord, rug, and clutter",
    "Bathroom with slippery floor and no visible grab bars",
    "Stairs with handrail concern",
    "Hallway with poor lighting and narrow path",
    "Safe room with no obvious hazards",
]


def get_demo_sample_result(sample_name):
    """
    Returns a fake AI-style analysis result for a selected demo scenario.
    """

    if sample_name == "Bathroom with slippery floor and no visible grab bars":
        return {
            "summary": (
                "Demo sample: This bathroom scenario shows possible bathroom safety concerns."
            ),
            "hazards": [
                {
                    "category": "bathroom_grab_bars",
                    "title": "Bathroom without visible grab bars",
                    "explanation": (
                        "Grab bars may help people steady themselves near a toilet, shower, "
                        "or bathtub. This demo scenario does not show visible grab bars."
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
            ],
            "not_visible": [
                "Actual floor slipperiness cannot be confirmed without human review.",
                "Some bathroom hazards may be outside the camera view.",
            ],
            "safety_reminder": (
                "AI may miss hazards. Human review is recommended."
            ),
        }

    if sample_name == "Stairs with handrail concern":
        return {
            "summary": (
                "Demo sample: This stairs scenario shows possible step and handrail concerns."
            ),
            "hazards": [
                {
                    "category": "stairs",
                    "title": "Stairs or step hazard",
                    "explanation": (
                        "Steps can increase fall risk, especially if the edges are hard to see "
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
                        "Make sure the handrail is secure, easy to grip, and available along the stairs."
                    ),
                },
            ],
            "not_visible": [
                "Handrail strength cannot be verified from one image.",
                "Step surface condition may need in-person review.",
            ],
            "safety_reminder": (
                "AI may miss hazards. Human review is recommended."
            ),
        }

    if sample_name == "Hallway with poor lighting and narrow path":
        return {
            "summary": (
                "Demo sample: This hallway scenario shows lighting and walking-path concerns."
            ),
            "hazards": [
                {
                    "category": "poor_lighting",
                    "title": "Possible poor lighting",
                    "explanation": (
                        "Dim lighting can make it harder to see objects, floor changes, "
                        "or tripping hazards."
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
            ],
            "not_visible": [
                "Lighting can look different in a photo than it does in person.",
                "Some hallway hazards may be outside the camera view.",
            ],
            "safety_reminder": (
                "AI may miss hazards. Human review is recommended."
            ),
        }

    if sample_name == "Safe room with no obvious hazards":
        return {
            "summary": (
                "Demo sample: No obvious fall hazards were listed in this simple safe-room scenario."
            ),
            "hazards": [],
            "not_visible": [
                "A photo cannot confirm whether floors are slippery.",
                "A photo cannot confirm whether rugs or furniture are secure.",
                "Human review is still recommended.",
            ],
            "safety_reminder": (
                "AI may miss hazards. Human review is recommended."
            ),
        }

    return {
        "summary": (
            "Demo sample: This living room scenario shows common walking-path hazards."
        ),
        "hazards": [
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
                    "A rug can slide or catch someone’s foot if it does not have a non-slip backing."
                ),
                "recommendation": (
                    "Use non-slip backing, tape down the edges, or remove the rug from the walking path."
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
        ],
        "not_visible": [
            "Lighting level cannot be fully judged from one demo scenario.",
            "Floor slipperiness cannot be confirmed without human review.",
            "Some hazards may be outside the camera view.",
        ],
        "safety_reminder": (
            "AI may miss hazards. Human review is recommended."
        ),
    }