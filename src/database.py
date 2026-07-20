"""
database.py

Supabase database helpers for AI SafeHome.

Stores anonymous room-check results only.
Does not store uploaded photos, names, addresses, medical history, or medication data.
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv

load_dotenv()


def get_env_value(name: str, default: Optional[str] = None) -> Optional[str]:
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


def is_database_enabled() -> bool:
    return str(get_env_value("DATABASE_ENABLED", "false")).lower().strip() == "true"


def get_database_status_message() -> str:
    if is_database_enabled():
        return "Database saving is enabled."
    return "Database saving is disabled."


def get_ai_mode() -> str:
    mode = str(get_env_value("AI_ANALYSIS_MODE", "fake")).lower().strip()
    if mode in ["fake", "real", "demo"]:
        return mode
    return "unknown"


def get_app_version() -> str:
    return str(get_env_value("APP_VERSION", "1.0")).strip()


def get_supabase_client():
    if not is_database_enabled():
        raise RuntimeError("Database saving is disabled.")

    supabase_url = get_env_value("SUPABASE_URL")
    supabase_key = get_env_value("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        raise RuntimeError("Missing SUPABASE_URL.")

    if not supabase_key:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY.")

    try:
        from supabase import create_client
    except Exception as error:
        raise RuntimeError(
            "The 'supabase' package is not installed. Add supabase to requirements.txt."
        ) from error

    return create_client(supabase_url, supabase_key)


# -----------------------------------------------------------------------------
# Home IDs
# -----------------------------------------------------------------------------


def normalize_home_id(home_id: Optional[str]) -> str:
    if not home_id:
        return ""
    return str(home_id).strip().upper()


def is_valid_home_id(home_id: Optional[str]) -> bool:
    normalized = normalize_home_id(home_id)
    pattern = r"^HOME-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
    return re.match(pattern, normalized) is not None


def validate_home_id_or_raise(home_id: Optional[str]) -> str:
    normalized = normalize_home_id(home_id)

    if not is_valid_home_id(normalized):
        raise RuntimeError("Invalid Home ID. Use a code like HOME-8K2M-Q9PA-W4ZT.")

    return normalized


def home_id_exists(home_id: str) -> bool:
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
    if not is_database_enabled():
        return False

    normalized_home_id = validate_home_id_or_raise(home_id)
    return not home_id_exists(normalized_home_id)


def create_home_id(home_id: str) -> str:
    if not is_database_enabled():
        raise RuntimeError("Database saving is disabled.")

    normalized_home_id = validate_home_id_or_raise(home_id)

    if home_id_exists(normalized_home_id):
        raise RuntimeError("That Home ID is already taken.")

    client = get_supabase_client()
    response = client.table("homes").insert({"home_id": normalized_home_id}).execute()

    if not response.data:
        raise RuntimeError("Could not create Home ID.")

    return response.data[0]["home_id"]


# -----------------------------------------------------------------------------
# Room IDs
# -----------------------------------------------------------------------------


def normalize_room_id(room_id: Optional[str]) -> str:
    if not room_id:
        return ""

    cleaned = str(room_id).strip().upper()
    cleaned = cleaned.replace(" ", "-").replace("_", "-")
    cleaned = re.sub(r"[^A-Z0-9-]", "", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")

    return cleaned


def is_valid_room_id(room_id: Optional[str]) -> bool:
    normalized = normalize_room_id(room_id)
    pattern = r"^[A-Z0-9-]{2,40}$"
    return re.match(pattern, normalized) is not None


def validate_room_id_or_raise(room_id: Optional[str]) -> str:
    normalized = normalize_room_id(room_id)

    if not is_valid_room_id(normalized):
        raise RuntimeError(
            "Invalid Room ID. Use something like BEDROOM-1, BEDROOM-2, or BATHROOM-1."
        )

    return normalized


def fetch_rooms_for_home(
    home_id: str,
    room_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
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


def get_home_room(home_id: str, room_id: str) -> Optional[Dict[str, Any]]:
    if not is_database_enabled():
        return None

    normalized_home_id = validate_home_id_or_raise(home_id)
    normalized_room_id = validate_room_id_or_raise(room_id)
    client = get_supabase_client()

    response = (
        client.table("home_rooms")
        .select("*")
        .eq("home_id", normalized_home_id)
        .eq("room_id", normalized_room_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_home_room(
    home_id: str,
    room_id: str,
    room_type: str,
    room_display_name: Optional[str] = None,
) -> Dict[str, Any]:
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
    existing_rooms = fetch_rooms_for_home(home_id=home_id, room_type=room_type)

    base = normalize_room_id(room_type) or "ROOM"
    number = len(existing_rooms) + 1

    while True:
        candidate = f"{base}-{number}"

        if not room_id_exists(home_id, candidate):
            return candidate

        number += 1


# -----------------------------------------------------------------------------
# Save helpers
# -----------------------------------------------------------------------------


def validate_anonymous_save_confirmation(confirmed: bool) -> Tuple[bool, str]:
    if confirmed:
        return True, ""

    return (
        False,
        "Please confirm that this result contains no personal, medical, or real patient information.",
    )


def count_checklist_answers(checklist_answers: List[Dict[str, Any]]) -> Dict[str, int]:
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
    hazards: List[Dict[str, Any]],
    checklist_answers: List[Dict[str, Any]],
    checklist_was_skipped: bool,
    safety_confirmed: bool,
    using_demo_sample: bool = False,
    demo_sample_name: Optional[str] = None,
    room_id: Optional[str] = None,
    home_room_id: Optional[str] = None,
) -> Dict[str, Any]:
    checklist_counts = count_checklist_answers(checklist_answers)

    return {
        "home_id": validate_home_id_or_raise(home_id),
        "room_id": validate_room_id_or_raise(room_id) if room_id else None,
        "home_room_id": home_room_id,
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
    hazard: Dict[str, Any],
) -> Dict[str, Any]:
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
    answer: Dict[str, Any],
) -> Dict[str, Any]:
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
    fix: Union[Dict[str, Any], str],
) -> Dict[str, Any]:
    if isinstance(fix, dict):
        recommendation = fix.get("text")
        priority = fix.get("priority")
        title = fix.get("source")
        category = fix.get("category")
    else:
        recommendation = str(fix)
        priority = None
        title = None
        category = None

    return {
        "room_check_id": room_check_id,
        "detail_type": "recommended_fix",
        "category": category,
        "title": title,
        "explanation": None,
        "recommendation": recommendation,
        "checklist_question": None,
        "checklist_answer": None,
        "priority": priority,
    }


def build_detail_rows(
    room_check_id: str,
    hazards: List[Dict[str, Any]],
    checklist_answers: List[Dict[str, Any]],
    recommended_fixes: List[Union[Dict[str, Any], str]],
) -> List[Dict[str, Any]]:
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
    hazards: List[Dict[str, Any]],
    checklist_answers: List[Dict[str, Any]],
    recommended_fixes: List[Union[Dict[str, Any], str]],
    checklist_was_skipped: bool,
    safety_confirmed: bool,
    using_demo_sample: bool = False,
    demo_sample_name: Optional[str] = None,
    room_id: Optional[str] = None,
) -> str:
    confirmed_ok, error_message = validate_anonymous_save_confirmation(safety_confirmed)

    if not confirmed_ok:
        raise RuntimeError(error_message)

    normalized_home_id = validate_home_id_or_raise(home_id)
    normalized_room_id = validate_room_id_or_raise(room_id) if room_id else None
    home_room_id = None

    if normalized_room_id:
        home_room = get_home_room(normalized_home_id, normalized_room_id)

        if not home_room:
            raise RuntimeError(
                "Room ID does not exist under this Home ID. Create or choose the room before saving."
            )

        home_room_id = home_room.get("id")

    client = get_supabase_client()

    room_check_payload = build_room_check_payload(
        home_id=normalized_home_id,
        room_type=room_type,
        score=score,
        risk_level=risk_level,
        hazards=hazards,
        checklist_answers=checklist_answers,
        checklist_was_skipped=checklist_was_skipped,
        safety_confirmed=safety_confirmed,
        using_demo_sample=using_demo_sample,
        demo_sample_name=demo_sample_name,
        room_id=normalized_room_id,
        home_room_id=home_room_id,
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


# -----------------------------------------------------------------------------
# Fetch checks and stats
# -----------------------------------------------------------------------------


def fetch_room_checks_by_home_id(
    home_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
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


def fetch_room_checks_by_room_id(
    home_id: str,
    room_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    if not is_database_enabled():
        return []

    normalized_home_id = validate_home_id_or_raise(home_id)
    normalized_room_id = validate_room_id_or_raise(room_id)
    client = get_supabase_client()

    response = (
        client.table("room_checks")
        .select("*")
        .eq("home_id", normalized_home_id)
        .eq("room_id", normalized_room_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return response.data or []


def fetch_room_check_by_id(
    check_id: str,
    home_id: str,
) -> Optional[Dict[str, Any]]:
    if not is_database_enabled():
        return None

    normalized_home_id = validate_home_id_or_raise(home_id)
    client = get_supabase_client()

    response = (
        client.table("room_checks")
        .select("*")
        .eq("id", str(check_id).strip())
        .eq("home_id", normalized_home_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def fetch_room_check_details(room_check_id: str) -> List[Dict[str, Any]]:
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


def fetch_room_details_for_checks(room_check_ids: List[str]) -> List[Dict[str, Any]]:
    detail_rows = []

    for room_check_id in room_check_ids:
        detail_rows.extend(fetch_room_check_details(room_check_id))

    return detail_rows


def fetch_summary_stats_for_home(home_id: str) -> Dict[str, Any]:
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
    moderate_risk_count = sum(1 for row in rows if row.get("risk_level") == "Moderate Risk")
    low_risk_count = sum(1 for row in rows if row.get("risk_level") == "Low Risk")

    room_counts: Dict[str, int] = {}

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


def build_room_stats_record(
    room_info: Dict[str, Any],
    check_rows: List[Dict[str, Any]],
    detail_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    room_id = room_info.get("room_id")
    room_type = room_info.get("room_type", "Unknown Room")
    room_display_name = room_info.get("room_display_name") or room_id
    check_count = len(check_rows)

    if check_count == 0:
        return {
            "room_id": room_id,
            "room_type": room_type,
            "room_display_name": room_display_name,
            "check_count": 0,
            "average_score": 0,
            "latest_score": None,
            "highest_score": None,
            "lowest_score": None,
            "latest_risk_level": None,
            "latest_created_at": None,
            "low_risk_count": 0,
            "moderate_risk_count": 0,
            "high_risk_count": 0,
            "hazard_counts": {},
            "top_hazard": None,
            "checklist_answer_counts": {},
            "recommended_fix_count": 0,
        }

    scores = [row.get("score", 0) for row in check_rows]
    latest_check = check_rows[0]

    hazard_counts: Dict[str, int] = {}
    checklist_answer_counts: Dict[str, int] = {}
    recommended_fix_count = 0

    for detail in detail_rows:
        detail_type = detail.get("detail_type")

        if detail_type == "ai_hazard":
            category = detail.get("category") or "unclear"
            hazard_counts[category] = hazard_counts.get(category, 0) + 1

        elif detail_type == "checklist_answer":
            answer = detail.get("checklist_answer") or "Unknown"
            checklist_answer_counts[answer] = checklist_answer_counts.get(answer, 0) + 1

        elif detail_type == "recommended_fix":
            recommended_fix_count += 1

    top_hazard = max(hazard_counts, key=hazard_counts.get) if hazard_counts else None

    return {
        "room_id": room_id,
        "room_type": room_type,
        "room_display_name": room_display_name,
        "check_count": check_count,
        "average_score": round(sum(scores) / check_count),
        "latest_score": latest_check.get("score"),
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "latest_risk_level": latest_check.get("risk_level"),
        "latest_created_at": latest_check.get("created_at"),
        "low_risk_count": sum(1 for row in check_rows if row.get("risk_level") == "Low Risk"),
        "moderate_risk_count": sum(1 for row in check_rows if row.get("risk_level") == "Moderate Risk"),
        "high_risk_count": sum(1 for row in check_rows if row.get("risk_level") == "High Risk"),
        "hazard_counts": hazard_counts,
        "top_hazard": top_hazard,
        "checklist_answer_counts": checklist_answer_counts,
        "recommended_fix_count": recommended_fix_count,
    }


def fetch_room_stats(home_id: str, room_id: str) -> Dict[str, Any]:
    normalized_home_id = validate_home_id_or_raise(home_id)
    normalized_room_id = validate_room_id_or_raise(room_id)

    rooms = fetch_rooms_for_home(home_id=normalized_home_id)

    matching_room = None

    for room in rooms:
        if room.get("room_id") == normalized_room_id:
            matching_room = room
            break

    if matching_room is None:
        matching_room = {
            "room_id": normalized_room_id,
            "room_type": "Unknown Room",
            "room_display_name": normalized_room_id,
        }

    check_rows = fetch_room_checks_by_room_id(
        home_id=normalized_home_id,
        room_id=normalized_room_id,
        limit=100,
    )

    check_ids = [row["id"] for row in check_rows if row.get("id")]
    detail_rows = fetch_room_details_for_checks(check_ids)

    return build_room_stats_record(
        room_info=matching_room,
        check_rows=check_rows,
        detail_rows=detail_rows,
    )


def fetch_all_room_stats_for_home(home_id: str) -> List[Dict[str, Any]]:
    normalized_home_id = validate_home_id_or_raise(home_id)

    rooms = fetch_rooms_for_home(home_id=normalized_home_id)
    all_checks = fetch_room_checks_by_home_id(home_id=normalized_home_id, limit=500)

    rooms_by_id: Dict[str, Dict[str, Any]] = {}

    for room in rooms:
        room_id = room.get("room_id")

        if room_id:
            rooms_by_id[room_id] = room

    for check in all_checks:
        room_id = check.get("room_id")

        if room_id and room_id not in rooms_by_id:
            rooms_by_id[room_id] = {
                "room_id": room_id,
                "room_type": check.get("room_type", "Unknown Room"),
                "room_display_name": room_id,
            }

    stats = []

    for room_id, room_info in rooms_by_id.items():
        check_rows = [row for row in all_checks if row.get("room_id") == room_id]
        check_ids = [row["id"] for row in check_rows if row.get("id")]
        detail_rows = fetch_room_details_for_checks(check_ids)

        stats.append(
            build_room_stats_record(
                room_info=room_info,
                check_rows=check_rows,
                detail_rows=detail_rows,
            )
        )

    return sorted(
        stats,
        key=lambda item: (
            item.get("room_type", ""),
            item.get("room_id", ""),
        ),
    )