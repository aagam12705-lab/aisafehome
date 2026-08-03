"""Session-state and navigation helpers for AI SafeHome."""

import streamlit as st


DEFAULT_SESSION_STATE = {
    "page": "landing",
    "room_type": None,
    "photo_uploaded": False,
    "photo_quality": None,
    "ai_result": None,
    "checklist_answers": [],
    "checklist_index": 0,
    "checklist_answers_by_id": {},
    "checklist_was_skipped": False,
    "score": None,
    "risk_level": None,
    "score_breakdown": None,
    "report_text": None,
    "text_size": "Standard",
    "color_scheme": "System",
    "show_read_aloud": False,
    "database_save_complete": False,
    "database_save_id": None,
    "home_id": None,
    "home_login_error": None,
    "home_login_message": None,
    "last_created_home_id": None,
    "current_room_id": None,
    "current_home_room_id": None,
    "upload_nonce": 0,
    "uploaded_photo_bytes": None,
    "quick_mode": False,
    "before_fix_comparison": None,
    "after_fix_result": None,
    "check_run_nonce": 0,
    "database_saved_run_nonce": None,
}


def initialize_session_state() -> None:
    for key, value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_page(page_name: str) -> None:
    st.session_state["page"] = page_name
    st.rerun()


def reset_follow_up_progress() -> None:
    st.session_state["checklist_index"] = 0
    st.session_state["checklist_answers_by_id"] = {}
    st.session_state["checklist_answers"] = []
    st.session_state["checklist_was_skipped"] = False


def mark_new_room_check() -> None:
    """Mark a new analysis so it is saved once rather than on every rerun."""
    st.session_state["check_run_nonce"] = st.session_state.get("check_run_nonce", 0) + 1
    st.session_state["database_save_complete"] = False
    st.session_state["database_save_id"] = None
    st.session_state["database_saved_run_nonce"] = None


def reset_current_room_check() -> None:
    for key, value in {
        "room_type": None,
        "photo_uploaded": False,
        "photo_quality": None,
        "ai_result": None,
        "score": None,
        "risk_level": None,
        "score_breakdown": None,
        "report_text": None,
        "database_save_complete": False,
        "database_save_id": None,
        "database_saved_run_nonce": None,
        "current_room_id": None,
        "current_home_room_id": None,
        "uploaded_photo_bytes": None,
        "before_fix_comparison": None,
        "after_fix_result": None,
    }.items():
        st.session_state[key] = value

    reset_follow_up_progress()
    st.session_state["upload_nonce"] = st.session_state.get("upload_nonce", 0) + 1
