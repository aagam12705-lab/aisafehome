"""
ai_analysis.py

This file handles photo analysis.

Modes:
- fake: returns sample demo hazards without calling OpenAI
- real: sends the uploaded room photo to OpenAI vision analysis

Use fake mode while practicing.
Use real mode when testing actual AI analysis.
"""

import base64
import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from src.prompts import SYSTEM_PROMPT, build_user_prompt


load_dotenv()


def get_fake_analysis(room_type):
    """
    Returns fake AI-style hazard results.
    This stays in the app as a safe fallback and demo mode.
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
                "explanation": "A cord near a walking area can create a tripping hazard.",
                "recommendation": "Move the cord along the wall or secure it with a cord cover.",
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


def get_error_fallback_analysis(room_type, error_message):
    """
    Returns fake results if real AI fails.
    This keeps the app demo from completely breaking.
    """

    result = get_fake_analysis(room_type)
    result["summary"] = (
        "Real AI analysis did not complete, so the app is showing sample fallback "
        "hazards instead. Error: "
        f"{error_message}"
    )
    return result


def encode_uploaded_image(uploaded_file):
    """
    Converts a Streamlit uploaded image file into a Base64 data URL.

    OpenAI accepts image input as a Base64 data URL.
    """

    uploaded_file.seek(0)
    image_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    mime_type = uploaded_file.type

    if not mime_type:
        mime_type = "image/jpeg"

    return f"data:{mime_type};base64,{base64_image}"


def extract_json_from_text(text):
    """
    Tries to parse JSON from the AI response.

    The prompt asks for only JSON, but this function adds protection in case
    the model accidentally wraps JSON in extra text or markdown.
    """

    if not text:
        raise ValueError("The AI returned an empty response.")

    cleaned_text = text.strip()

    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(r"^```json", "", cleaned_text, flags=re.IGNORECASE).strip()
        cleaned_text = re.sub(r"^```", "", cleaned_text).strip()
        cleaned_text = re.sub(r"```$", "", cleaned_text).strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)

        if not match:
            raise ValueError("The AI response did not contain valid JSON.")

        return json.loads(match.group(0))


def clean_ai_result(result):
    """
    Makes sure the AI result has the keys the Streamlit app expects.
    """

    if not isinstance(result, dict):
        raise ValueError("AI result was not a JSON object.")

    hazards = result.get("hazards", [])

    if not isinstance(hazards, list):
        hazards = []

    cleaned_hazards = []

    allowed_categories = {
        "loose_rug",
        "cords",
        "clutter",
        "poor_lighting",
        "slippery_floor",
        "narrow_pathway",
        "stairs",
        "handrail",
        "bathroom_grab_bars",
        "hard_to_reach_items",
        "unclear",
    }

    for hazard in hazards:
        if not isinstance(hazard, dict):
            continue

        category = hazard.get("category", "unclear")

        if category not in allowed_categories:
            category = "unclear"

        cleaned_hazards.append(
            {
                "category": category,
                "title": hazard.get("title", "Possible hazard"),
                "explanation": hazard.get(
                    "explanation",
                    "This area may need human review.",
                ),
                "recommendation": hazard.get(
                    "recommendation",
                    "Review this area carefully and consider a simple safety fix.",
                ),
            }
        )

    not_visible = result.get("not_visible", [])

    if not isinstance(not_visible, list):
        not_visible = ["Some hazards may not be visible from one photo."]

    return {
        "summary": result.get(
            "summary",
            "The photo was reviewed for possible visible home fall hazards.",
        ),
        "hazards": cleaned_hazards,
        "not_visible": not_visible,
        "safety_reminder": result.get(
            "safety_reminder",
            "AI may miss hazards. Human review is recommended.",
        ),
    }


def analyze_photo_with_openai(image_file, room_type):
    """
    Sends the uploaded photo to OpenAI and returns cleaned JSON hazard results.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")

    model_name = os.getenv("OPENAI_MODEL", "gpt-5.5")

    client = OpenAI(api_key=api_key)

    image_data_url = encode_uploaded_image(image_file)

    response = client.responses.create(
        model=model_name,
        instructions=SYSTEM_PROMPT,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": build_user_prompt(room_type),
                    },
                    {
                        "type": "input_image",
                        "image_url": image_data_url,
                        "detail": "low",
                    },
                ],
            }
        ],
        max_output_tokens=900,
    )

    raw_text = response.output_text
    parsed_result = extract_json_from_text(raw_text)
    return clean_ai_result(parsed_result)


def analyze_photo(image_file, room_type):
    """
    Main function used by app.py.

    If AI_ANALYSIS_MODE is fake, this returns fake results.
    If AI_ANALYSIS_MODE is real, this calls OpenAI.
    """

    mode = os.getenv("AI_ANALYSIS_MODE", "fake").lower().strip()

    if mode != "real":
        return get_fake_analysis(room_type)

    try:
        return analyze_photo_with_openai(image_file, room_type)
    except Exception as error:
        return get_error_fallback_analysis(room_type, str(error))