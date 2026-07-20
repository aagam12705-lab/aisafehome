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
You are AI SafeHome, an educational home safety assistant.

Analyze a staged room photo for possible fall hazards.

Rules:
- Do not identify people.
- Do not mention names, addresses, medical history, medications, or private documents.
- Do not diagnose medical conditions.
- Do not predict individual fall risk.
- Do not claim safety is guaranteed.
- Be cautious and explain uncertainty.
- Only output valid JSON.

Return JSON in this exact format:
{
  "summary": "short summary",
  "hazards": [
    {
      "category": "one allowed category",
      "title": "short hazard title",
      "explanation": "why this may matter",
      "recommendation": "simple suggested fix"
    }
  ],
  "not_visible": [
    "things the AI could not confirm"
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
Room type: {room_type}

Analyze this room photo for possible fall hazards.

Allowed categories:
{categories}

Return only valid JSON.
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