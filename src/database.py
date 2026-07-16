"""
database.py

Privacy-safe Supabase database access for AI SafeHome.

This file stores anonymous room-check results only.

Never store:
- uploaded photos
- base64 image data
- names
- addresses
- ages
- medical history
- medications
- insurance information
- patient IDs
- real patient photos
- faces
- mail
- bills
- medication bottles
- medical documents
"""

import os
from typing import Any, Optional, Union

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


def get_env_value(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Reads a setting from environment variables.

    Later, Streamlit Cloud secrets can also provide these values as environment
    variables, so this function keeps the database layer simple.
    """

    value = os.getenv(name)

    if value is None or value == "":
        return default

    return value


def is_database_enabled() -> bool:
    """
    Checks whether database saving is enabled.

    The app should work normally when this returns False.
    """

    value = get_env_value("DATABASE_ENABLED", "false")
    return str(value).lower().strip() == "true"


def get_database_status_message() -> str:
    """
    Returns a safe database status message.

    This must never expose keys, URLs, or secret values.
    """

    if is_database_enabled():
        return "Database saving is enabled."

    return "Database saving is disabled."


def get_ai_mode() -> str:
    """
    Returns the current AI mode in a database-safe format.
    """

    mode = str(get_env_value("AI_ANALYSIS_MODE", "fake")).lower().strip()

    if mode in ["fake", "real", "demo"]:
        return mode

    return "unknown"


def get_app_version() -> str:
    """
    Returns the app version saved with database rows.
    """

    return str(get_env_value("APP_VERSION", "1.0")).strip()


def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client.

    Raises a clear error if database saving is disabled or credentials are missing.
    """

    if not is_database_enabled():
        raise RuntimeError("Database saving is disabled.")

    supabase_url = get_env_value("SUPABASE_URL")
    supabase_key = get_env_value("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        raise RuntimeError("Missing SUPABASE_URL.")

    if not supabase_key:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY.")

    return create_client(supabase_url, supabase_key)


def validate_anonymous_save_confirmation(confirmed: bool) -> tuple[bool, str]:
    """
    Checks whether the user confirmed that no personal, medical,
    or real patient information is being saved.
    """

    if confirmed:
        return True, ""

    return (
        False,
        "Please confirm that this result contains no personal, medical, or real patient information.",
    )


def count_checklist_answers(checklist_answers: list[dict[str, Any]]) -> dict[str, int]:
    """
    Counts checklist answer types.
    """

    counts = {
        "yes": 0,
        "no": 0,
        "not_sure": 0,
        "not_applicable": 0,
        "skipped": 0,
    }

    for answer in checklist_answers:
        response = answer.get("answer")
        answer_label = answer.get("answer_label")

        if response in counts:
            counts[response] += 1

        if answer_label == "Skipped":
            counts["skipped"] += 1

    return counts


def build_room_check_payload(
    room_type: str,
    score: int,
    risk_level: str,
    hazards: list[dict[str, Any]],
    checklist_answers: list[dict[str, Any]],
    checklist_was_skipped: bool,
    safety_confirmed: bool,
    using_demo_sample: bool = False,
    demo_sample_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Creates the main row for the room_checks table.

    This payload must stay anonymous.
    """

    checklist_counts = count_checklist_answers(checklist_answers)

    return {
        "app_version": get_app_version(),
        "ai_mode": get_ai_mode(),
        "room_type": room_type,
        "score": int(score),
        "risk_level": risk_level,
        "checklist_was_skipped": bool(checklist_was_skipped),
        "using_demo_sample": bool(using_demo_sample),
        "demo_sample_name": demo_sample_name,
        "hazard_count": len(hazards),
        "checklist_yes_count": checklist_counts["yes"],
        "checklist_not_sure_count": checklist_counts["not_sure"],
        "checklist_skipped_count": checklist_counts["skipped"],
        "safety_confirmed": bool(safety_confirmed),
    }


def build_hazard_detail_row(
    room_check_id: str,
    hazard: dict[str, Any],
) -> dict[str, Any]:
    """
    Creates one ai_hazard row for room_check_details.
    """

    return {
        "room_check_id": room_check_id,
        "detail_type": "ai_hazard",
        "category": hazard.get("category"),
        "title": hazard.get("title"),
        "explanation": hazard.get("explanation"),
        "recommendation": hazard.get("recommendation"),
        "checklist_question": None,
        "checklist_answer": None,
        "priority": hazard.get("priority"),
    }


def build_checklist_detail_row(
    room_check_id: str,
    answer: dict[str, Any],
) -> dict[str, Any]:
    """
    Creates one checklist_answer row for room_check_details.
    """

    return {
        "room_check_id": room_check_id,
        "detail_type": "checklist_answer",
        "category": answer.get("category"),
        "title": None,
        "explanation": None,
        "recommendation": None,
        "checklist_question": answer.get("question"),
        "checklist_answer": answer.get("answer_label", answer.get("answer")),
        "priority": answer.get("priority"),
    }


def build_fix_detail_row(
    room_check_id: str,
    fix: Union[dict[str, Any], str],
) -> dict[str, Any]:
    """
    Creates one recommended_fix row for room_check_details.

    Supports both the old string format and the newer dictionary format from
    the priority-label milestone.
    """

    if isinstance(fix, dict):
        recommendation = fix.get("text")
        priority = fix.get("priority")
        title = fix.get("source")
    else:
        recommendation = str(fix)
        priority = None
        title = None

    return {
        "room_check_id": room_check_id,
        "detail_type": "recommended_fix",
        "category": None,
        "title": title,
        "explanation": None,
        "recommendation": recommendation,
        "checklist_question": None,
        "checklist_answer": None,
        "priority": priority,
    }


def build_detail_rows(
    room_check_id: str,
    hazards: list[dict[str, Any]],
    checklist_answers: list[dict[str, Any]],
    recommended_fixes: list[Union[dict[str, Any], str]],
) -> list[dict[str, Any]]:
    """
    Creates all room_check_details rows for one saved room check.
    """

    detail_rows = []

    for hazard in hazards:
        detail_rows.append(build_hazard_detail_row(room_check_id, hazard))

    for answer in checklist_answers:
        detail_rows.append(build_checklist_detail_row(room_check_id, answer))

    for fix in recommended_fixes:
        detail_rows.append(build_fix_detail_row(room_check_id, fix))

    return detail_rows


def save_room_check(
    room_type: str,
    score: int,
    risk_level: str,
    hazards: list[dict[str, Any]],
    checklist_answers: list[dict[str, Any]],
    recommended_fixes: list[Union[dict[str, Any], str]],
    checklist_was_skipped: bool,
    safety_confirmed: bool,
    using_demo_sample: bool = False,
    demo_sample_name: Optional[str] = None,
) -> str:
    """
    Saves one anonymous room check and its details.

    Returns the saved room_check id.
    """

    confirmed_ok, error_message = validate_anonymous_save_confirmation(
        safety_confirmed
    )

    if not confirmed_ok:
        raise RuntimeError(error_message)

    client = get_supabase_client()

    room_check_payload = build_room_check_payload(
        room_type=room_type,
        score=score,
        risk_level=risk_level,
        hazards=hazards,
        checklist_answers=checklist_answers,
        checklist_was_skipped=checklist_was_skipped,
        safety_confirmed=safety_confirmed,
        using_demo_sample=using_demo_sample,
        demo_sample_name=demo_sample_name,
    )

    room_response = client.table("room_checks").insert(room_check_payload).execute()

    if not room_response.data:
        raise RuntimeError("Supabase did not return a saved room check.")

    room_check_id = room_response.data[0]["id"]

    detail_rows = build_detail_rows(
        room_check_id=room_check_id,
        hazards=hazards,
        checklist_answers=checklist_answers,
        recommended_fixes=recommended_fixes,
    )

    if detail_rows:
        client.table("room_check_details").insert(detail_rows).execute()

    return room_check_id


def fetch_recent_room_checks(limit: int = 20) -> list[dict[str, Any]]:
    """
    Fetches recent saved room checks.

    Used later for a simple saved-results dashboard.
    """

    if not is_database_enabled():
        return []

    client = get_supabase_client()

    response = (
        client.table("room_checks")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return response.data or []


def fetch_summary_stats() -> dict[str, Any]:
    """
    Fetches simple summary stats for saved anonymous room checks.

    This keeps the logic beginner-friendly by calculating stats in Python.
    """

    if not is_database_enabled():
        return {
            "database_enabled": False,
            "total_checks": 0,
            "average_score": 0,
            "high_risk_count": 0,
            "moderate_risk_count": 0,
            "low_risk_count": 0,
            "most_common_room": None,
        }

    client = get_supabase_client()

    response = (
        client.table("room_checks")
        .select("*")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )

    rows = response.data or []

    if not rows:
        return {
            "database_enabled": True,
            "total_checks": 0,
            "average_score": 0,
            "high_risk_count": 0,
            "moderate_risk_count": 0,
            "low_risk_count": 0,
            "most_common_room": None,
        }

    scores = [row.get("score", 0) for row in rows]
    average_score = round(sum(scores) / len(scores))

    high_risk_count = sum(1 for row in rows if row.get("risk_level") == "High Risk")
    moderate_risk_count = sum(
        1 for row in rows if row.get("risk_level") == "Moderate Risk"
    )
    low_risk_count = sum(1 for row in rows if row.get("risk_level") == "Low Risk")

    room_counts = {}

    for row in rows:
        room_type = row.get("room_type", "Unknown")
        room_counts[room_type] = room_counts.get(room_type, 0) + 1

    most_common_room = max(room_counts, key=room_counts.get)

    return {
        "database_enabled": True,
        "total_checks": len(rows),
        "average_score": average_score,
        "high_risk_count": high_risk_count,
        "moderate_risk_count": moderate_risk_count,
        "low_risk_count": low_risk_count,
        "most_common_room": most_common_room,
    }