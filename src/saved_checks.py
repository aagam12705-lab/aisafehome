"""Saving and automatic-history helpers for completed room checks."""

from typing import Any, Dict

import streamlit as st

from src.account_ui import get_logged_in_home_id, show_home_id_login_box
from src.app_state import go_to_page
from src.database import is_database_enabled, save_room_check
from src.fixes import get_recommended_first_fixes


def get_current_database_save_payload() -> Dict[str, Any]:
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])
    analysis_mode = ai_result.get("analysis_mode", "sample")

    return {
        "room_type": st.session_state.get("room_type"),
        "room_id": st.session_state.get("current_room_id"),
        "score": st.session_state.get("score"),
        "risk_level": st.session_state.get("risk_level"),
        "hazards": hazards,
        "checklist_answers": checklist_answers,
        "recommended_fixes": get_recommended_first_fixes(hazards, checklist_answers, limit=5),
        "checklist_was_skipped": st.session_state.get("checklist_was_skipped", False),
        "using_demo_sample": analysis_mode != "real",
        "demo_sample_name": (
            "Built-in sample analysis" if analysis_mode == "sample"
            else "Fallback sample analysis" if analysis_mode == "fallback"
            else None
        ),
    }


def save_payload(payload: Dict[str, Any]) -> str:
    return save_room_check(
        home_id=get_logged_in_home_id(),
        room_type=payload["room_type"],
        score=payload["score"],
        risk_level=payload["risk_level"],
        hazards=payload["hazards"],
        checklist_answers=payload["checklist_answers"],
        recommended_fixes=payload["recommended_fixes"],
        checklist_was_skipped=payload["checklist_was_skipped"],
        safety_confirmed=True,
        using_demo_sample=payload["using_demo_sample"],
        demo_sample_name=payload["demo_sample_name"],
        room_id=payload["room_id"],
    )


def show_database_save_panel() -> None:
    if not is_database_enabled():
        return
    if not get_logged_in_home_id():
        st.subheader("Save This Check")
        st.warning("Create or sign in to an account before saving.")
        show_home_id_login_box(key_prefix="save_panel_home")
        return
    if not st.session_state.get("current_room_id"):
        st.subheader("Save This Check")
        st.warning("Choose or create a Room Name before saving.")
        if st.button("Choose Room Name"):
            go_to_page("room_id_selection")
        return
    if st.session_state.get("database_save_complete"):
        if st.button("View Room-by-Room Stats", key="saved_check_view_room_stats"):
            go_to_page("room_stats")
        return

    st.subheader("Save This Check")
    if st.button("Save Result", type="primary"):
        try:
            saved_id = save_payload(get_current_database_save_payload())
            st.session_state["database_save_complete"] = True
            st.session_state["database_save_id"] = saved_id
            st.rerun()
        except Exception as error:
            st.error("Could not save this result.")
            with st.expander("Technical details"):
                st.code(str(error))


def automatically_save_current_room_check() -> None:
    """Add each signed-in room check to history exactly once."""
    if not (is_database_enabled() and get_logged_in_home_id() and st.session_state.get("current_room_id")):
        return
    run_nonce = st.session_state.get("check_run_nonce", 0)
    if st.session_state.get("database_saved_run_nonce") == run_nonce:
        return

    payload = get_current_database_save_payload()
    if payload.get("score") is None or not payload.get("room_type"):
        return
    try:
        saved_id = save_payload(payload)
        st.session_state["database_save_complete"] = True
        st.session_state["database_save_id"] = saved_id
        st.session_state["database_saved_run_nonce"] = run_nonce
    except Exception:
        st.warning("This check could not be added to room stats yet. You can save it from the section below.")
