"""Application setup and one clear route table for AI SafeHome."""

import importlib

import streamlit as st

from src.app_state import go_to_page, initialize_session_state
import src.page_handlers as _page_handlers

# Keep local page and UI edits visible during Streamlit development reruns.
importlib.reload(_page_handlers)

from src.page_handlers import (
    show_after_fixes_photo_page,
    show_ai_results_page,
    show_checklist_page,
    show_checklist_summary_page,
    show_landing_page,
    show_photo_upload_page,
    show_risk_score_page,
    show_room_id_selection_page,
    show_room_selection_page,
    show_room_stats_page,
    show_safety_report_page,
    show_saved_results_page,
)
from src.ui import add_mobile_friendly_style, setup_page, show_accessibility_panel


PAGES = {
    "landing": show_landing_page,
    "room_selection": show_room_selection_page,
    "room_id_selection": show_room_id_selection_page,
    "photo_upload": show_photo_upload_page,
    "ai_results": show_ai_results_page,
    "checklist": show_checklist_page,
    "checklist_summary": show_checklist_summary_page,
    "risk_score": show_risk_score_page,
    "safety_report": show_safety_report_page,
    "after_fixes_photo": show_after_fixes_photo_page,
    "saved_results": show_saved_results_page,
    "room_stats": show_room_stats_page,
}


def run_app() -> None:
    setup_page()
    initialize_session_state()
    add_mobile_friendly_style()
    show_accessibility_panel()

    current_page = st.session_state.get("page", "landing")
    if current_page != "landing" and st.button("← Back to Landing Page", key="global_back_to_landing"):
        go_to_page("landing")

    handler = PAGES.get(current_page)
    if handler is None:
        st.session_state["page"] = "landing"
        handler = show_landing_page
    handler()
