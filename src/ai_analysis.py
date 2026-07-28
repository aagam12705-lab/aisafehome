"""
ai_analysis.py

AI photo analysis for AI SafeHome.

Default mode is fake/sample analysis so the app works without an API key.

Set AI_ANALYSIS_MODE=real and provide OPENAI_API_KEY + OPENAI_MODEL
to use real image analysis.
"""

import base64
import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from src.constants import CATEGORY_LABELS
from src.priorities import get_priority_for_hazard

load_dotenv()


SYSTEM_PROMPT = """
You are AI SafeHome, an educational home fall-hazard review assistant.

Your job:
Analyze a staged room photo as if you are mentally walking through the room from the point of view of a person moving through it.

Important:
You are NOT diagnosing a person.
You are NOT identifying a person.
You are NOT predicting an individual person's chance of falling.
You are only reviewing the physical room environment for possible fall hazards.

Core analysis method:
Use a 3D walkthrough mindset.

Imagine a person entering the room and moving through the most likely walking paths:
- from doorway to main furniture
- from doorway to bathroom/kitchen/stairs/bed/chair if visible
- through narrow paths between furniture
- around corners or turns
- across rugs, mats, thresholds, cords, shoes, clutter, or floor transitions
- toward objects they may reach for
- through low-light areas
- near stairs, steps, wet-looking floors, or unstable furniture

For every possible hazard, think about:
1. Foot path: Could a foot catch, slide, twist, or be blocked?
2. Body movement: Would the person need to turn sharply, squeeze through, step over, bend, or reach?
3. Balance support: Is there stable support nearby, or could furniture slide/wobble?
4. Visibility: Is the hazard easy to see from standing height?
5. 3D location: Is the hazard in the foreground, middle, background, left, center, right, floor level, ankle level, knee level, waist level, or near a transition?
6. Consequence path: If someone stumbled, what nearby object, edge, corner, stair, or hard surface could make it worse?
7. Uncertainty: What can you not confirm from this single photo?

What to look for:
- cords across walking paths
- loose rugs or mats
- clutter on the floor
- poor lighting
- slippery or wet-looking floors
- narrow or blocked walking paths
- stairs or step hazards
- missing or uncertain handrails
- bathroom areas without visible grab bars
- hard-to-reach items
- raised thresholds or floor transitions
- unstable furniture
- pet items in walking paths
- shoes or footwear in walking paths
- low seating
- poor contrast at steps or floor edges
- uneven floor surfaces
- loose door mats
- furniture blocking walking paths
- laundry or clothing on the floor
- open drawers or cabinet doors
- outdoor surfaces that appear uneven, wet, icy, cluttered, or poorly lit

Safety and privacy rules:
- Do not identify people.
- Do not describe faces, age, disability, health status, medical history, medications, or private documents.
- Do not mention names, addresses, mail, bills, labels, prescriptions, or personal information.
- Do not diagnose medical conditions.
- Do not predict an individual person's fall risk.
- Do not say the room is safe.
- Do not guarantee fall prevention.
- Do not assume a person is elderly, disabled, injured, or sick.
- Use neutral wording such as "a person walking through this area" or "someone using this path."

Judgment rules:
- Only list hazards visible or strongly suggested by the image.
- Do not invent hazards that are not supported by the image.
- If something is uncertain, include that uncertainty clearly.
- If a hazard is only partly visible, use lower confidence.
- Prefer practical, physical fixes.
- Keep recommendations simple and non-medical.
- Prefer 3 to 6 hazards.
- Only include more than 6 hazards if the image clearly contains many separate issues.
- If the image quality is poor, say what could not be evaluated in not_visible.

Allowed categories:
loose_rug, cords, clutter, poor_lighting, slippery_floor, narrow_pathway,
stairs, handrail, bathroom_grab_bars, hard_to_reach_items, threshold_trip,
unstable_furniture, pet_items, footwear, low_seating, poor_contrast,
uneven_floor, door_mat, furniture_in_path, outdoor_surface, laundry_on_floor,
open_drawers_cabinets, unclear

JSON rules:
- Return only valid JSON.
- Do not include markdown.
- Do not include explanation outside the JSON.
- Do not add extra top-level keys.
- Do not add extra hazard keys.
- Use exactly the JSON structure below.

Return JSON in this exact format:
{
  "summary": "1 to 2 sentence plain-language summary of the room's main safety concerns.",
  "hazards": [
    {
      "category": "one allowed category",
      "title": "short hazard title",
      "confidence": "high, medium, or low",
      "visibility": "visible, partly visible, or uncertain",
      "evidence": "specific visual evidence, including 3D location such as foreground/background, left/center/right, floor/ankle/knee/waist level, and walking-path position",
      "explanation": "explain the hazard from the viewpoint of someone walking through the room",
      "recommendation": "simple practical fix",
      "human_review_reason": "what a person should double-check in the real room"
    }
  ],
  "not_visible": [
    "important safety factors that cannot be confirmed from this photo"
  ],
  "safety_reminder": "AI may miss hazards. Human review is recommended."
}
""".strip()


ALLOWED_CATEGORIES = set(CATEGORY_LABELS.keys())


def get_env_value(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Reads from .env first, then Streamlit secrets.
    """

    value = os.getenv(name)

    if value is not None and value != "":
        return value

    try:
        import streamlit as st

        if name in st.secrets:
            secret_value = st.secrets[name]
            if secret_value is not None and secret_value != "":
                return str(secret_value)
    except Exception:
        pass

    return default


def get_ai_mode() -> str:
    """
    Returns fake or real.
    """

    mode = str(get_env_value("AI_ANALYSIS_MODE", "fake")).lower().strip()

    if mode == "real":
        return "real"

    return "fake"


def encode_uploaded_image(uploaded_file: Any) -> str:
    """
    Converts uploaded image to base64 string.
    """

    uploaded_file.seek(0)
    image_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    return base64.b64encode(image_bytes).decode("utf-8")


def get_uploaded_file_mime_type(uploaded_file: Any) -> str:
    """
    Gets safe MIME type for OpenAI image input.
    """

    file_type = getattr(uploaded_file, "type", None)

    if file_type in ["image/jpeg", "image/png", "image/webp"]:
        return file_type

    return "image/jpeg"


def build_user_prompt(room_type: str) -> str:
    categories = ", ".join(sorted(ALLOWED_CATEGORIES))

    return f"""
Room type selected by user:
{room_type}

Analyze this staged room photo for possible fall hazards.

Use the 3D walkthrough method:
- Imagine entering the room from the camera viewpoint.
- Identify the most likely walking path.
- Notice anything at foot level, ankle level, knee level, waist level, or eye level that affects movement.
- Look for objects that someone may need to step over, walk around, turn around, reach past, or avoid.
- Describe where each hazard is in the room using location words like foreground, background, left, center, right, floor level, near doorway, near furniture, near wall, or in walking path.
- Explain how the hazard could affect someone physically moving through the space.
- Include uncertainty when the image does not fully show the floor, lighting, rug edges, handrails, wetness, or stability.

Use only these category values:
{categories}

Output requirements:
- Return only valid JSON.
- Use the exact JSON structure from the system instructions.
- Do not add extra JSON fields.
- Keep the summary short.
- Each hazard must have one allowed category.
- Each hazard must include confidence, visibility, evidence, explanation, recommendation, and human_review_reason.
- confidence must be exactly one of: high, medium, low.
- visibility must be exactly one of: visible, partly visible, uncertain.
- evidence should include the hazard's 3D location and what visual clue supports it.
- explanation should be written from the viewpoint of a person walking through the room.
- recommendation should be a direct physical fix.
- human_review_reason should say what a real person should double-check in the actual room.
- Do not mention people, names, addresses, medication bottles, private documents, or medical information.
- Do not say the room is safe.
- Do not guarantee fall prevention.
""".strip()

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extracts JSON from a model response.
    """

    if not text:
        raise RuntimeError("AI returned an empty response.")

    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1).strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise RuntimeError("AI response did not contain JSON.")

    json_text = cleaned[start : end + 1]

    return json.loads(json_text)


def clean_ai_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes AI result so the app can safely render it.
    """

    summary = str(raw_result.get("summary", "")).strip()
    safety_reminder = str(
        raw_result.get("safety_reminder", "AI may miss hazards. Human review is recommended.")
    ).strip()

    raw_hazards = raw_result.get("hazards", [])

    if not isinstance(raw_hazards, list):
        raw_hazards = []

    hazards: List[Dict[str, Any]] = []

    for item in raw_hazards[:8]:
        if not isinstance(item, dict):
            continue

        category = str(item.get("category", "unclear")).strip()

        if category not in ALLOWED_CATEGORIES:
            category = "unclear"

        hazard = {
            "category": category,
            "title": str(item.get("title", "Possible hazard")).strip(),
            "explanation": str(
                item.get("explanation", "This area may need human review.")
            ).strip(),
            "recommendation": str(
                item.get("recommendation", "Review this area carefully.")
            ).strip(),
        }

        hazard["priority"] = get_priority_for_hazard(hazard)

        hazards.append(hazard)

    not_visible = raw_result.get("not_visible", [])

    if not isinstance(not_visible, list):
        not_visible = []

    clean_not_visible = [str(item).strip() for item in not_visible[:5] if str(item).strip()]

    if not clean_not_visible:
        clean_not_visible = [
            "Hazards outside the camera view cannot be checked.",
            "Floor slipperiness cannot be fully confirmed from a photo.",
        ]

    return {
        "summary": summary or "AI SafeHome found possible room safety concerns.",
        "hazards": hazards,
        "not_visible": clean_not_visible,
        "safety_reminder": safety_reminder,
    }


def get_fake_analysis(room_type: str) -> Dict[str, Any]:
    """
    Returns sample analysis for testing and fallback.
    """

    room = (room_type or "Other").lower()

    hazards = [
        {
            "category": "cords",
            "title": "Cord near walking path",
            "explanation": "A cord near a walking area can create a tripping hazard.",
            "recommendation": "Move the cord along the wall or secure it with a cord cover.",
        },
        {
            "category": "loose_rug",
            "title": "Possible loose rug",
            "explanation": "A rug can slide or catch someone's foot if it does not have non-slip backing.",
            "recommendation": "Use non-slip backing, tape down the edges, or remove the rug from the walking path.",
        },
        {
            "category": "clutter",
            "title": "Floor clutter",
            "explanation": "Objects on the floor can make walking paths harder to use safely.",
            "recommendation": "Clear small objects, bags, shoes, or boxes from the walking path.",
        },
    ]

    if room == "bathroom":
        hazards = [
            {
                "category": "bathroom_grab_bars",
                "title": "Bathroom without visible grab bars",
                "explanation": "This photo does not clearly show grab bars near bathroom areas.",
                "recommendation": "Consider properly installed grab bars near the toilet, shower, or bathtub.",
            },
            {
                "category": "slippery_floor",
                "title": "Possible slippery floor area",
                "explanation": "Bathroom floors can become slippery when wet.",
                "recommendation": "Use non-slip mats and keep the floor dry.",
            },
        ]

    elif room == "stairs":
        hazards = [
            {
                "category": "stairs",
                "title": "Stairs or step hazard",
                "explanation": "Steps can increase fall risk if edges are hard to see or the area is dim.",
                "recommendation": "Keep stairs clear, improve lighting, and make step edges easy to see.",
            },
            {
                "category": "handrail",
                "title": "Handrail should be checked",
                "explanation": "A missing, loose, or hard-to-grip handrail can make stairs less safe.",
                "recommendation": "Make sure the handrail is secure and easy to grip.",
            },
        ]

    elif room == "garage":
        hazards = [
            {
                "category": "clutter",
                "title": "Garage floor clutter",
                "explanation": "Tools, boxes, or stored items can block walking paths.",
                "recommendation": "Move stored items off the floor and keep a clear walkway.",
            },
            {
                "category": "uneven_floor",
                "title": "Possible uneven garage floor",
                "explanation": "Garage floors may have cracks or uneven surfaces.",
                "recommendation": "Mark or repair uneven areas and keep the walking path clear.",
            },
        ]

    elif room == "home office":
        hazards = [
            {
                "category": "cords",
                "title": "Office cord hazard",
                "explanation": "Computer or charger cords can create tripping hazards.",
                "recommendation": "Route cords along the wall or secure them with a cord cover.",
            },
            {
                "category": "open_drawers_cabinets",
                "title": "Open drawer or cabinet",
                "explanation": "Open drawers or cabinet doors can block walking space.",
                "recommendation": "Keep drawers and cabinets closed when not in use.",
            },
        ]

    for hazard in hazards:
        hazard["priority"] = get_priority_for_hazard(hazard)

    return {
        "summary": "Sample AI-style result. Use real AI mode later for actual photo analysis.",
        "hazards": hazards,
        "not_visible": [
            "Some hazards may be outside the camera view.",
            "Floor slipperiness cannot be fully confirmed from one photo.",
            "Whether a rug has non-slip backing cannot be confirmed from a photo alone.",
        ],
        "safety_reminder": "AI may miss hazards. Human review is recommended.",
    }


def analyze_photo_with_openai(uploaded_file: Any, room_type: str) -> Dict[str, Any]:
    """
    Uses OpenAI vision input for real analysis.
    """

    api_key = get_env_value("OPENAI_API_KEY")
    model = get_env_value("OPENAI_MODEL")

    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY.")

    if not model:
        raise RuntimeError("Missing OPENAI_MODEL. Set OPENAI_MODEL in .env or Streamlit secrets.")

    try:
        from openai import OpenAI
    except Exception as error:
        raise RuntimeError("The openai package is not installed.") from error

    image_base64 = encode_uploaded_image(uploaded_file)
    mime_type = get_uploaded_file_mime_type(uploaded_file)
    data_url = f"data:{mime_type};base64,{image_base64}"

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": build_user_prompt(room_type),
                    },
                    {
                        "type": "input_image",
                        "image_url": data_url,
                        "detail": "low",
                    },
                ],
            },
        ],
    )

    text = response.output_text
    raw_result = extract_json_from_text(text)

    return clean_ai_result(raw_result)


def analyze_photo(uploaded_file: Any, room_type: str) -> Dict[str, Any]:
    """
    Main app entry point.

    Fake mode always works.
    Real mode falls back to fake mode if something breaks.
    """

    if get_ai_mode() != "real":
        return get_fake_analysis(room_type)

    try:
        return analyze_photo_with_openai(uploaded_file, room_type)

    except Exception as error:
        fallback = get_fake_analysis(room_type)
        fallback["summary"] = (
            f"Real AI analysis failed, so sample results are shown instead. Error: {error}"
        )
        return fallback