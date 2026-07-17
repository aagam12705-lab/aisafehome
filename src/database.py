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
import re
from typing import Any, Optional, Union
from uuid import UUID
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

def is_valid_uuid(value: str) -> bool:
    """
    Checks whether a value is a valid UUID string.

    Supabase room_checks IDs are UUIDs.
    """

    try:
        UUID(str(value))
        return True
    except ValueError:
        return False

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

def normalize_home_id(home_id: str | None) -> str:
    """
    Cleans a Home ID for lookup and saving.

    Home IDs are anonymous access codes, not personal identifiers.
    """

    if not home_id:
        return ""

    return str(home_id).strip().upper()


def is_valid_home_id(home_id: str | None) -> bool:
    """
    Checks whether a Home ID has a safe format.

    Example:
    HOME-8K2M-Q9PA-W4ZT
    """

    normalized = normalize_home_id(home_id)

    pattern = r"^HOME-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"

    return re.match(pattern, normalized) is not None

def normalize_room_id(room_id: str | None) -> str:
    """
    Cleans a Room ID.

    Examples:
    bedroom1 -> BEDROOM1
    Bedroom 1 -> BEDROOM-1
    bathroom-2 -> BATHROOM-2
    """

    if not room_id:
        return ""

    cleaned = str(room_id).strip().upper()
    cleaned = cleaned.replace(" ", "-")
    cleaned = cleaned.replace("_", "-")

    cleaned = re.sub(r"[^A-Z0-9-]", "", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned)

    return cleaned


def is_valid_room_id(room_id: str | None) -> bool:
    """
    Checks whether a Room ID is safe to store.
    """

    normalized = normalize_room_id(room_id)

    pattern = r"^[A-Z0-9-]{2,40}$"

    return re.match(pattern, normalized) is not None


def validate_room_id_or_raise(room_id: str | None) -> str:
    """
    Returns a normalized Room ID or raises a clear error.
    """

    normalized = normalize_room_id(room_id)

    if not is_valid_room_id(normalized):
        raise RuntimeError(
            "Invalid Room ID. Use something like BEDROOM-1, BEDROOM-2, or BATHROOM-1."
        )

    return normalized

def validate_home_id_or_raise(home_id: str | None) -> str:
    """
    Returns a normalized Home ID or raises a clear error.
    """

    normalized = normalize_home_id(home_id)

    if not is_valid_home_id(normalized):
        raise RuntimeError(
            "Invalid Home ID. Use a code like HOME-8K2M-Q9PA-W4ZT."
        )

    return normalized
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

def home_id_exists(home_id: str) -> bool:
    """
    Checks whether a Home ID already exists in the database.
    """

    if not is_database_enabled():
        return False

    normalized_home_id = validate_home_id_or_raise(home_id)

    client = get_supabase_client()

    response = (
        client.table("homes")
        .select("home_id")
        .eq("home_id", normalized_home_id)
        .limit(1)
        .execute()
    )

    return bool(response.data)


def is_home_id_available(home_id: str) -> bool:
    """
    Returns True if the Home ID is valid and not already taken.
    """

    normalized_home_id = validate_home_id_or_raise(home_id)

    return not home_id_exists(normalized_home_id)


def create_home_id(home_id: str) -> str:
    """
    Creates/reserves a new anonymous Home ID.
    """

    normalized_home_id = validate_home_id_or_raise(home_id)

    if home_id_exists(normalized_home_id):
        raise RuntimeError("That Home ID is already taken.")

    client = get_supabase_client()

    response = (
        client.table("homes")
        .insert({"home_id": normalized_home_id})
        .execute()
    )

    if not response.data:
        raise RuntimeError("Could not create Home ID.")

    return response.data[0]["home_id"]

def fetch_rooms_for_home(
    home_id: str,
    room_type: str | None = None,
) -> list[dict]:
    """
    Fetches rooms saved under one Home ID.

    If room_type is provided, only returns rooms of that type.
    Example: all Bedroom rooms under one Home ID.
    """

    if not is_database_enabled():
        return []

    normalized_home_id = validate_home_id_or_raise(home_id)

    client = get_supabase_client()

    query = (
        client.table("home_rooms")
        .select("*")
        .eq("home_id", normalized_home_id)
        .order("created_at", desc=False)
    )

    if room_type:
        query = query.eq("room_type", room_type)

    response = query.execute()

    return response.data or []


def room_id_exists(home_id: str, room_id: str) -> bool:
    """
    Checks whether a Room ID already exists under one Home ID.
    """

    if not is_database_enabled():
        return False

    normalized_home_id = validate_home_id_or_raise(home_id)
    normalized_room_id = validate_room_id_or_raise(room_id)

    client = get_supabase_client()

    response = (
        client.table("home_rooms")
        .select("id")
        .eq("home_id", normalized_home_id)
        .eq("room_id", normalized_room_id)
        .limit(1)
        .execute()
    )

    return bool(response.data)


def create_home_room(
    home_id: str,
    room_id: str,
    room_type: str,
    room_display_name: str | None = None,
) -> dict:
    """
    Creates one room under a Home ID.

    Example:
    Home ID: HOME-8K2M-Q9PA-W4ZT
    Room ID: BEDROOM-1
    Room Type: Bedroom
    """

    normalized_home_id = validate_home_id_or_raise(home_id)
    normalized_room_id = validate_room_id_or_raise(room_id)

    if not home_id_exists(normalized_home_id):
        raise RuntimeError("Home ID does not exist yet.")

    if room_id_exists(normalized_home_id, normalized_room_id):
        raise RuntimeError("That Room ID already exists under this Home ID.")

    client = get_supabase_client()

    payload = {
        "home_id": normalized_home_id,
        "room_id": normalized_room_id,
        "room_type": room_type,
        "room_display_name": room_display_name or normalized_room_id,
    }

    response = client.table("home_rooms").insert(payload).execute()

    if not response.data:
        raise RuntimeError("Could not create room.")

    return response.data[0]


def get_next_room_id(home_id: str, room_type: str) -> str:
    """
    Suggests the next Room ID for a selected room type.

    Example:
    Bedroom with no existing rooms -> BEDROOM-1
    Bedroom with BEDROOM-1 existing -> BEDROOM-2
    """

    existing_rooms = fetch_rooms_for_home(home_id=home_id, room_type=room_type)

    base = normalize_room_id(room_type)

    if not base:
        base = "ROOM"

    number = len(existing_rooms) + 1

    while True:
        candidate = f"{base}-{number}"

        if not room_id_exists(home_id, candidate):
            return candidate

        number += 1

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
    home_id: str,
    room_type: str,
    score: int,
    risk_level: str,
    hazards: list[dict[str, Any]],
    checklist_answers: list[dict[str, Any]],
    checklist_was_skipped: bool,
    safety_confirmed: bool,
    using_demo_sample: bool = False,
    demo_sample_name: Optional[str] = None,
    room_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Creates the main row for the room_checks table.

    This payload must stay anonymous.
    """

    checklist_counts = count_checklist_answers(checklist_answers)

    return {
        "home_id": validate_home_id_or_raise(home_id),
        "room_id": validate_room_id_or_raise(room_id) if room_id else None,
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
    home_id: str,
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
        home_id=home_id,
        room_type=room_type,
        score=score,
        risk_level=risk_level,
        hazards=hazards,
        checklist_answers=checklist_answers,
        checklist_was_skipped=checklist_was_skipped,
        safety_confirmed=safety_confirmed,
        using_demo_sample=using_demo_sample,
        demo_sample_name=demo_sample_name,
        room_id=room_id,
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

def fetch_room_checks_by_home_id(
    home_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Fetches saved room checks for one Home ID only.
    """

    if not is_database_enabled():
        return []

    normalized_home_id = validate_home_id_or_raise(home_id)

    client = get_supabase_client()

    response = (
        client.table("room_checks")
        .select("*")
        .eq("home_id", normalized_home_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return response.data or []


def fetch_room_check_by_id(
    check_id: str,
    home_id: str,
) -> dict[str, Any] | None:
    """
    Fetches one room check by Check ID and Home ID.

    Requiring both IDs prevents random Check ID lookup across homes.
    """

    if not is_database_enabled():
        return None

    normalized_home_id = validate_home_id_or_raise(home_id)

    cleaned_check_id = str(check_id).strip()

    if not cleaned_check_id:
        raise RuntimeError("Check ID is required.")

    client = get_supabase_client()

    response = (
        client.table("room_checks")
        .select("*")
        .eq("id", cleaned_check_id)
        .eq("home_id", normalized_home_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def fetch_room_check_details(room_check_id: str) -> list[dict[str, Any]]:
    """
    Fetches detail rows for one saved room check.
    """

    if not is_database_enabled():
        return []

    client = get_supabase_client()

    response = (
        client.table("room_check_details")
        .select("*")
        .eq("room_check_id", str(room_check_id).strip())
        .order("created_at", desc=False)
        .execute()
    )

    return response.data or []


def fetch_summary_stats_for_home(home_id: str) -> dict[str, Any]:
    """
    Returns summary stats for one Home ID only.
    """

    rows = fetch_room_checks_by_home_id(home_id=home_id, limit=500)

    if not rows:
        return {
            "database_enabled": is_database_enabled(),
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
        "database_enabled": is_database_enabled(),
        "total_checks": len(rows),
        "average_score": average_score,
        "high_risk_count": high_risk_count,
        "moderate_risk_count": moderate_risk_count,
        "low_risk_count": low_risk_count,
        "most_common_room": most_common_room,
    }
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

def fetch_room_check_by_id(room_check_id: str) -> dict[str, Any] | None:
    """
    Fetches one anonymous room check by ID.

    Returns None if no matching row exists.
    """

    if not is_database_enabled():
        return None

    if not is_valid_uuid(room_check_id):
        raise ValueError("Invalid saved result ID. Expected a UUID.")

    client = get_supabase_client()

    response = (
        client.table("room_checks")
        .select("*")
        .eq("id", room_check_id)
        .maybe_single()
        .execute()
    )

    return response.data


def fetch_room_check_details_by_id(room_check_id: str) -> list[dict[str, Any]]:
    """
    Fetches detail rows for one saved room check.
    """

    if not is_database_enabled():
        return []

    if not is_valid_uuid(room_check_id):
        raise ValueError("Invalid saved result ID. Expected a UUID.")

    client = get_supabase_client()

    response = (
        client.table("room_check_details")
        .select("*")
        .eq("room_check_id", room_check_id)
        .order("created_at", desc=False)
        .execute()
    )

    return response.data or []


def fetch_room_check_with_details(room_check_id: str) -> dict[str, Any] | None:
    """
    Fetches one saved room check plus its hazards, checklist answers, and fixes.
    """

    room_check = fetch_room_check_by_id(room_check_id)

    if not room_check:
        return None

    details = fetch_room_check_details_by_id(room_check_id)

    return {
        "room_check": room_check,
        "details": details,
    }
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