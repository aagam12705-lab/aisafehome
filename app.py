import importlib
import io
from typing import Any, Dict, List, Optional

# Streamlit can retain an earlier version of a helper module after a source
# change. Reload this local module before importing its helpers so a live app
# cannot keep a partially loaded version that is missing newer functions.
import src.database as _database_module
import src.constants as _constants_module
import src.ai_analysis as _ai_analysis_module
import src.scoring as _scoring_module
import src.ui as _ui_module
import src.comparison as _comparison_module
import src.trends as _trends_module
import src.email_ui as _email_ui_module
import src.report_builder as _report_builder_module
import src.fixes as _fixes_module
import src.app_state as _app_state_module
import src.account_ui as _account_ui_module
import src.saved_checks as _saved_checks_module
import src.image_tools as _image_tools_module

importlib.reload(_database_module)
importlib.reload(_constants_module)
importlib.reload(_ai_analysis_module)
importlib.reload(_scoring_module)
importlib.reload(_ui_module)
importlib.reload(_comparison_module)
importlib.reload(_trends_module)
importlib.reload(_email_ui_module)
importlib.reload(_report_builder_module)
importlib.reload(_fixes_module)
importlib.reload(_app_state_module)
importlib.reload(_account_ui_module)
importlib.reload(_saved_checks_module)
importlib.reload(_image_tools_module)

from src.comparison import (
    build_before_after_summary_text,
    compare_hazard_categories,
    get_check_display_label,
    get_score_change_message,
    sort_checks_oldest_to_newest,
)
import streamlit as st
from PIL import Image, ImageDraw
from src.trends import (
    build_score_trend_rows,
    build_trend_summary_text,
    get_trend_summary,
)
from src.ai_analysis import analyze_photo
from src.checklist import ANSWER_OPTIONS, ANSWER_VALUE_MAP
from src.photo_quality import analyze_uploaded_photo_quality, build_photo_quality_text
from src.constants import (
    ALLOWED_FILE_TYPES,
    LANDING_EXPLANATION,
    PHOTO_UPLOAD_PRIVACY_WARNING,
    ROOM_OPTIONS,
    TAGLINE,
)
from src.database import (
    create_home_room,
    fetch_all_room_stats_for_home,
    fetch_room_check_details,
    fetch_room_checks_by_home_id,
    fetch_room_checks_by_room_id,
    fetch_room_stats,
    fetch_rooms_for_home,
    fetch_summary_stats_for_home,
    get_next_room_id,
    is_database_enabled,
)
from src.email_ui import show_email_summary_panel, show_share_summary_panel
from src.fixes import build_top_fixes_text, get_recommended_first_fixes
from src.priorities import get_priority_for_category, get_priority_for_hazard
from src.report_builder import build_report_text
from src.scoring import calculate_score, get_risk_level, get_score_breakdown
from src.app_state import (
    go_to_page,
    initialize_session_state,
    mark_new_room_check,
    reset_current_room_check,
    reset_follow_up_progress as reset_checklist_progress,
)
from src.account_ui import (
    get_logged_in_home_id,
    show_home_id_login_box,
    show_home_id_status,
    show_privacy_and_ai_info,
)
from src.saved_checks import automatically_save_current_room_check, show_database_save_panel
from src.image_tools import load_oriented_image, oriented_image_file, validate_uploaded_photo
from src.ui import (
    add_mobile_friendly_style,
    format_database_datetime,
    get_category_label,
    render_hazard_card,
    render_score_trend_chart,
    render_styled_table,
    safe_filename_part,
    safe_text,
    setup_page,
    show_accessibility_panel,
    show_read_aloud_button,
    show_risk_score_bar,
    show_score_explanation_card,
    show_step_card,
)


# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------


def show_landing_page() -> None:
    st.title("AI SafeHome")
    st.markdown(f'<div class="big-tagline">{TAGLINE}</div>', unsafe_allow_html=True)

    st.write(LANDING_EXPLANATION)
    st.caption("For home-safety guidance only — not medical advice.")

    st.markdown(
        """
        <div class="plain-card">
            <strong>How it works</strong><br><br>
            1. Choose a room.<br>
            2. Take or upload one photo.<br>
            3. Answer only the questions the photo cannot answer.<br>
            4. Get a score and a simple safety plan.
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_home_id_status(key_suffix="landing", allow_logout=True)
    show_privacy_and_ai_info()

    if st.button("Start Safety Check", type="primary"):
        reset_current_room_check()
        st.session_state["quick_mode"] = False
        go_to_page("room_selection")

    if get_logged_in_home_id() and st.button("My Saved Room Checks"):
        go_to_page("saved_results")

    if st.button("View Room-by-Room Stats", key="landing_view_room_stats"):
        go_to_page("room_stats")


def show_room_selection_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 1: Choose a Room")
    if st.session_state.get("quick_mode"):
        show_step_card("Continue without signing in — Choose the room. No account or Room Name is needed unless you decide to save later.")
    else:
        show_step_card("Step 1 of 6 — Choose the room you want to check.")

    selected_room = st.radio("Which room are you checking?", ROOM_OPTIONS, index=0)

    if st.button("Continue →", type="primary"):
        st.session_state["room_type"] = selected_room
        st.session_state["current_room_id"] = None
        st.session_state["current_home_room_id"] = None
        go_to_page("photo_upload" if st.session_state.get("quick_mode") else "room_id_selection")

    if st.button("← Back to Landing Page"):
        go_to_page("landing")


def show_room_id_selection_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Choose Room Name")

    room_type = st.session_state.get("room_type")

    if not room_type:
        st.error("No room type was selected.")
        if st.button("Back to Room Selection"):
            go_to_page("room_selection")
        return

    st.markdown(
        f'<div class="plain-card"><strong>Selected room type:</strong> {safe_text(room_type)}</div>',
        unsafe_allow_html=True,
    )

    st.info("Room Names keep repeated rooms separate, like Bedroom 1 and Bedroom 2.")

    if not is_database_enabled():
        st.warning("Saved room checks are not available right now.")

        if st.button("Continue Without Signing In →", type="primary", key="room_id_continue_without_signin_disabled"):
            st.session_state["current_room_id"] = None
            st.session_state["current_home_room_id"] = None
            go_to_page("photo_upload")

        return

    home_id = get_logged_in_home_id()

    if not home_id:
        st.warning("Sign in to save this room, or continue without signing in.")

        if st.button("Continue Without Signing In →", type="primary", key="room_id_continue_without_signin"):
            st.session_state["current_room_id"] = None
            st.session_state["current_home_room_id"] = None
            go_to_page("photo_upload")

        st.divider()
        show_home_id_login_box(key_prefix="room_id_page_home")

        return

    try:
        existing_rooms = fetch_rooms_for_home(home_id=home_id, room_type=room_type)
        suggested_room_id = get_next_room_id(home_id=home_id, room_type=room_type)
    except Exception as error:
        st.error("Could not load your saved rooms.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    def show_create_room_name_form() -> None:
        st.caption("Use a simple name like Bedroom 1, Bedroom 2, or Main Bathroom.")
        new_room_id = st.text_input(
            "New Room Name",
            value=suggested_room_id,
            key="new_room_id_input",
        )

        if st.button("Create and Use This Room Name →", type="primary"):
            try:
                created_room = create_home_room(
                    home_id=home_id,
                    room_id=new_room_id,
                    room_type=room_type,
                )
                st.session_state["current_room_id"] = created_room["room_id"]
                st.session_state["current_home_room_id"] = created_room["id"]
                go_to_page("risk_score" if st.session_state.get("ai_result") else "photo_upload")
            except Exception as error:
                st.error("Could not create that Room Name.")
                with st.expander("Technical details"):
                    st.code(str(error))

    # A first-time room type has nothing to select, so open directly on the
    # creation flow rather than showing an empty tab first.
    if not existing_rooms:
        st.subheader("Create New Room Name")
        show_create_room_name_form()
    else:
        tab1, tab2 = st.tabs(["Use Existing Room Name", "Create New Room Name"])
        with tab1:
            room_options = {room.get("room_id"): room for room in existing_rooms}
            selected = st.selectbox(
                "Choose existing Room Name",
                list(room_options.keys()),
                key="existing_room_id_select",
            )
            if st.button("Use This Room Name →", type="primary"):
                selected_room = room_options[selected]
                st.session_state["current_room_id"] = selected_room["room_id"]
                st.session_state["current_home_room_id"] = selected_room["id"]
                go_to_page("risk_score" if st.session_state.get("ai_result") else "photo_upload")
        with tab2:
            show_create_room_name_form()

    if st.button("← Back to Room Selection"):
        go_to_page("room_selection")

def show_photo_quality_card(quality: Dict[str, Any]) -> None:
    label = quality.get("label", "Unknown")

    if label == "Good":
        st.success("Photo quality looks usable for AI analysis.")
    elif label == "Caution":
        st.warning("Photo may be usable, but AI analysis could be less reliable.")
    elif label == "Poor":
        st.error("Photo quality may be poor. AI analysis may miss hazards.")
    else:
        st.info("Photo quality could not be checked.")

    metrics = quality.get("metrics", {})

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Photo Quality:</strong> {safe_text(label)}<br>
            <strong>Resolution:</strong> {safe_text(metrics.get("width", "Unknown"))} × {safe_text(metrics.get("height", "Unknown"))}<br>
            <strong>Brightness:</strong> {safe_text(metrics.get("brightness", "Unknown"))}<br>
            <strong>Contrast:</strong> {safe_text(metrics.get("contrast", "Unknown"))}<br>
            <strong>Sharpness estimate:</strong> {safe_text(metrics.get("edge_score", "Unknown"))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Photo quality details"):
        for issue in quality.get("issues", []):
            st.write(f"- {issue}")

        st.write("Suggestions:")
        for suggestion in quality.get("suggestions", []):
            st.write(f"- {suggestion}")


def render_hazard_location_guide(image_bytes: Optional[bytes], hazards: List[Dict[str, Any]]) -> None:
    """Displays approximate numbered markers tied to the hazard cards below."""
    if not image_bytes or not hazards:
        return

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (OSError, ValueError):
        return

    draw = ImageDraw.Draw(image)
    radius = max(18, min(image.size) // 22)
    plotted_hazards = 0

    for index, hazard in enumerate(hazards[:8], start=1):
        if isinstance(hazard.get("location_x"), int) and isinstance(hazard.get("location_y"), int):
            x_ratio = hazard["location_x"] / 100
            y_ratio = hazard["location_y"] / 100
        else:
            continue

        x, y = int(image.width * x_ratio), int(image.height * y_ratio)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="#2563eb", width=max(3, radius // 6))
        draw.text((x - radius // 4, y - radius // 2), str(index), fill="#1e3a8a")
        plotted_hazards += 1

    if plotted_hazards:
        st.image(image, caption="AI-marked hazard locations. Each numbered circle matches the hazard card below.", width="stretch")

def show_photo_upload_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 2: Upload Room Photo")
    show_step_card("Step 2 of 6 — Upload or take a room photo.")
    st.caption(PHOTO_UPLOAD_PRIVACY_WARNING)

    room_type = st.session_state.get("room_type")

    if not room_type:
        st.error("No room selected.")
        if st.button("Back to Room Selection"):
            go_to_page("room_selection")
        return

    st.markdown(
        f'<div class="plain-card"><strong>Room checked:</strong> {safe_text(room_type)}</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload or take one room photo (30 MB maximum)",
        type=ALLOWED_FILE_TYPES,
        accept_multiple_files=False,
        help="One JPG, PNG, or WEBP photo only. On iPhone, this may let you choose Photo Library or Take Photo.",
        key=f"room_photo_{st.session_state.get('upload_nonce', 0)}",
    )
    st.caption("One photo at a time • JPG, PNG, or WEBP • 30 MB maximum")

    if uploaded_file is not None:
        valid, error = validate_uploaded_photo(uploaded_file)

        if not valid:
            st.error(error)
            return

        try:
            image = load_oriented_image(uploaded_file)
            analysis_file = oriented_image_file(image)
        except (OSError, ValueError):
            st.error("This file could not be read as an image. Choose a valid JPG, PNG, or WEBP photo.")
            uploaded_file.seek(0)
            return

        st.image(image, caption=f"Preview of uploaded {room_type} photo", width="stretch")
        st.session_state["uploaded_photo_bytes"] = analysis_file.getvalue()
        analysis_file.seek(0)

        st.session_state["photo_uploaded"] = True
        st.success("Photo uploaded successfully.")
        quality = analyze_uploaded_photo_quality(analysis_file)
        st.session_state["photo_quality"] = quality
        show_photo_quality_card(quality)
        if st.button("Analyze Photo →", type="primary"):
            with st.spinner("Analyzing photo..."):
                analysis_file.seek(0)
                ai_result = analyze_photo(analysis_file, room_type)

                for hazard in ai_result.get("hazards", []):
                    hazard["priority"] = hazard.get("priority") or get_priority_for_hazard(hazard)

                st.session_state["ai_result"] = ai_result
                mark_new_room_check()

            go_to_page("checklist" if st.session_state.get("quick_mode") else "ai_results")

    if st.button("← Back"):
        go_to_page("room_selection" if st.session_state.get("quick_mode") else "room_id_selection")


def show_ai_results_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 3: AI Results")
    show_step_card("Step 3 of 6 — Review possible hazards found by AI.")

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])

    analysis_mode = ai_result.get("analysis_mode")
    if analysis_mode in {"sample", "fallback"}:
        st.info("These are sample results, not findings from the uploaded photo.")

    st.write(ai_result.get("summary", "No summary available."))

    read_aloud_text = "AI results. " + str(ai_result.get("summary", ""))
    show_read_aloud_button(read_aloud_text, "ai_results")

    if hazards:
        st.subheader("Hazard Locations in the Photo")
        render_hazard_location_guide(st.session_state.get("uploaded_photo_bytes"), hazards)
        for index, hazard in enumerate(hazards, start=1):
            render_hazard_card(hazard, index)
    else:
        st.info("No possible hazards were listed by AI.")

    st.warning(
        ai_result.get(
            "safety_reminder",
            "AI may miss hazards. Human review is recommended.",
        )
    )

    if st.button("Continue to Follow-Up Questions →", type="primary"):
        reset_checklist_progress()
        go_to_page("checklist")

    if st.button("← Back to Upload"):
        go_to_page("photo_upload")


def save_checklist_answer(question: Dict[str, Any], answer_label: str) -> None:
    answer_value = ANSWER_VALUE_MAP.get(answer_label, "not_sure")

    st.session_state["checklist_answers_by_id"][question["id"]] = {
        "id": question["id"],
        "category": question["category"],
        "question": question["text"],
        "answer": answer_value,
        "answer_label": answer_label,
        "priority": get_priority_for_category(question["category"]),
    }


def get_ai_checklist_questions() -> List[Dict[str, Any]]:
    ai_result = st.session_state.get("ai_result") or {}
    questions = ai_result.get("checklist_questions", [])
    return questions if isinstance(questions, list) else []


def build_ordered_checklist_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ordered = []

    for question in questions:
        saved = st.session_state["checklist_answers_by_id"].get(question["id"])
        if saved:
            ordered.append(saved)

    return ordered


def finish_checklist() -> None:
    st.session_state["checklist_answers"] = build_ordered_checklist_answers(
        get_ai_checklist_questions()
    )
    go_to_page("checklist_summary")


def skip_follow_up_questions() -> None:
    st.session_state["checklist_answers"] = []
    st.session_state["checklist_was_skipped"] = True
    go_to_page("checklist_summary")


def show_checklist_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 4: AI Follow-Up Questions")
    show_step_card("Step 4 of 6 — Answer only the questions the AI could not confirm from the photo.")

    index = st.session_state.get("checklist_index", 0)
    questions = get_ai_checklist_questions()

    if not questions:
        st.info("The AI did not identify any important uncertainties that need a follow-up question.")
        if st.button("Continue to Score →", type="primary"):
            finish_checklist()
        return

    if index >= len(questions):
        finish_checklist()
        return

    question = questions[index]

    st.progress((index + 1) / len(questions))
    st.write(f"Follow-up question {index + 1} of {len(questions)}")
    st.markdown(f"### {question['text']}")
    st.caption("Answer No if this safety condition is not met.")
    if question.get("reason"):
        st.caption(f"Why we are asking: {question['reason']}")

    show_read_aloud_button(
        f"Follow-up question {index + 1} of {len(questions)}. {question['text']}. "
        f"Why we are asking: {question.get('reason', 'The photo did not clearly show this.')}",
        f"follow_up_{question['id']}",
    )

    answer_label = st.radio(
        "Choose an answer",
        ANSWER_OPTIONS,
        key=f"checklist_answer_{question['id']}",
    )

    if st.button("Save and Next →", type="primary"):
        save_checklist_answer(question, answer_label)

        if index + 1 >= len(questions):
            finish_checklist()
        else:
            st.session_state["checklist_index"] = index + 1
            st.rerun()

    if st.button("Skip This Question"):
        st.session_state["checklist_answers_by_id"][question["id"]] = {
            "id": question["id"],
            "category": question["category"],
            "question": question["text"],
            "answer": "not_applicable",
            "answer_label": "Skipped",
            "priority": get_priority_for_category(question["category"]),
        }

        if index + 1 >= len(questions):
            finish_checklist()
        else:
            st.session_state["checklist_index"] = index + 1
            st.rerun()

    if st.button("Skip Follow-Up Questions"):
        skip_follow_up_questions()

    if index > 0:
        if st.button("← Previous Question"):
            st.session_state["checklist_index"] = max(0, index - 1)
            st.rerun()


def show_checklist_summary_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Follow-Up Summary")

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])
    skip_buffer_points = (
        int(ai_result.get("skip_buffer_points", 0))
        if st.session_state.get("checklist_was_skipped")
        else 0
    )

    if st.session_state.get("checklist_was_skipped"):
        st.info(f"Follow-up questions were skipped. An AI uncertainty buffer of {skip_buffer_points} points was added.")
    else:
        st.write(f"Follow-up answers saved: {len(checklist_answers)}")

    score = calculate_score(hazards, checklist_answers, skip_buffer_points)
    risk_level = get_risk_level(score)
    score_breakdown = get_score_breakdown(hazards, checklist_answers, skip_buffer_points)

    st.session_state["score"] = score
    st.session_state["risk_level"] = risk_level
    st.session_state["score_breakdown"] = score_breakdown
    st.session_state["report_text"] = build_report_text()

    st.metric("Risk Score", f"{score}/100")
    st.write(f"Risk label: **{risk_level}**")
    show_risk_score_bar(score)

    with st.expander("How this score was calculated"):
        show_score_explanation_card(score_breakdown)

    if st.button("View Your Safety Plan →", type="primary"):
        go_to_page("risk_score")


def show_top_5_fixes(limit: int = 5) -> List[Dict[str, Any]]:
    """Show the first three actions clearly, without hiding the remaining advice."""
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    fixes = get_recommended_first_fixes(
        ai_hazards=hazards,
        checklist_answers=checklist_answers,
        limit=limit,
    )

    st.subheader("Your 3-Step Safety Plan")
    st.caption("Start with these three changes. Small changes can make a walking path safer.")

    if not fixes:
        st.info("No specific fixes were generated.")
        return []

    action_labels = {
        "Fix Now": "Do this first",
        "Fix Soon": "Plan this next",
        "Watch / Review": "Check this with someone",
    }

    def show_fix(fix: Dict[str, Any]) -> None:
        impact_points = max(0, int(fix.get("points", 0) or 0))
        lower_impact = max(1, round(impact_points * 0.5)) if impact_points else 0
        needs_help = fix.get("category") in {"handrail", "bathroom_grab_bars", "stairs", "uneven_floor"}
        help_note = " Ask someone for help with this repair." if needs_help else ""
        action_label = action_labels.get(str(fix.get("priority")), "Consider this step")
        st.markdown(
            f"""
            <div class="plain-card">
                <strong>{fix.get("rank")}. {safe_text(action_label)}</strong><br>
                {safe_text(fix.get("text"))}<br>
                <span class="small-muted">May lower the risk score by about {lower_impact}–{impact_points} points if this concern is confirmed and resolved.{safe_text(help_note)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for fix in fixes[:3]:
        show_fix(fix)

    if len(fixes) > 3:
        with st.expander("See more suggested steps"):
            for fix in fixes[3:]:
                show_fix(fix)

    show_read_aloud_button(build_top_fixes_text(fixes), "top_fixes")
    return fixes


def show_current_check_comparison() -> None:
    """Compares a recheck to the latest saved result for the same Room Name."""
    home_id = get_logged_in_home_id()
    room_id = st.session_state.get("current_room_id")
    current_hazards = (st.session_state.get("ai_result") or {}).get("hazards", [])

    if not (is_database_enabled() and home_id and room_id and current_hazards):
        return

    try:
        previous_checks = fetch_room_checks_by_room_id(home_id, room_id, limit=1)
        if not previous_checks:
            return
        previous_check = previous_checks[0]
        previous_details = fetch_room_check_details(previous_check["id"], home_id)
    except Exception:
        st.info("A saved-room comparison will be available after this check is saved.")
        return

    current_details = [
        {"detail_type": "ai_hazard", "category": hazard.get("category")}
        for hazard in current_hazards
        if hazard.get("category")
    ]
    comparison = compare_hazard_categories(previous_details, current_details)
    resolved = [get_category_label(item) for item in sorted(comparison["resolved"])]
    still_present = [get_category_label(item) for item in sorted(comparison["still_present"])]
    new = [get_category_label(item) for item in sorted(comparison["new"])]

    st.subheader(f"Comparison with Your Last Saved {st.session_state.get('room_type', 'Room')} Check")
    col1, col2 = st.columns(2)
    col1.metric("Previous Score", f"{previous_check.get('score', 0)}/100")
    col2.metric("Current Score", f"{st.session_state.get('score', 0)}/100")
    st.caption("This compares the current photo with the latest saved check for this same Room Name.")

    for heading, items, display in [
        ("Hazards resolved", resolved, st.success),
        ("Still needing attention", still_present, st.warning),
        ("New hazards detected", new, st.error),
    ]:
        st.write(f"**{heading}:** " + (", ".join(items) if items else "None"))


def show_risk_score_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 5: Your Safety Plan")
    show_step_card("Step 5 of 6 — Review your score, then start with the three most important changes.")

    score = st.session_state.get("score")
    risk_level = st.session_state.get("risk_level")
    score_breakdown = st.session_state.get("score_breakdown")

    if score is None:
        st.error("No score is available yet.")
        if st.button("Back to Follow-Up Questions"):
            go_to_page("checklist")
        return

    st.metric("Risk Score", f"{score}/100")
    st.write(f"Risk label: **{risk_level}**")
    show_risk_score_bar(score)

    with st.expander("How this score was calculated"):
        show_score_explanation_card(score_breakdown)
    show_current_check_comparison()
    automatically_save_current_room_check()

    quick_mode = st.session_state.get("quick_mode")
    show_top_5_fixes(limit=3 if quick_mode else 5)

    if quick_mode:
        st.info("This check stays in this browser session unless you choose to save it.")
        if st.button("Save This Check"):
            st.session_state["quick_mode"] = False
            go_to_page("room_id_selection")
    else:
        st.divider()
        show_database_save_panel()

    if st.button("Open Full Safety Report →", type="primary"):
        st.session_state["report_text"] = build_report_text()
        go_to_page("safety_report")

    if st.session_state.get("uploaded_photo_bytes") and st.session_state.get("ai_result"):
        if st.button("Compare After Making Fixes"):
            st.session_state["before_fix_comparison"] = {
                "photo_bytes": st.session_state.get("uploaded_photo_bytes"),
                "hazards": st.session_state.get("ai_result", {}).get("hazards", []),
                "score": score,
            }
            st.session_state["after_fix_result"] = None
            go_to_page("after_fixes_photo")

    if st.button("View Room-by-Room Stats", key="risk_score_view_room_stats"):
        go_to_page("room_stats")


def show_safety_report_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 6: Your Safety Plan & Report")
    st.caption("Save, share, or read the complete plan when you are ready.")

    report_text = st.session_state.get("report_text") or build_report_text()
    st.session_state["report_text"] = report_text

    st.markdown(
        f'<div class="print-report">{safe_text(report_text)}</div>',
        unsafe_allow_html=True,
    )

    show_read_aloud_button(report_text, "safety_report")

    room_id = st.session_state.get("current_room_id") or "ROOM"
    file_name = f"ai_safehome_report_{safe_filename_part(room_id)}.txt"

    st.download_button(
        label="Download Report",
        data=report_text,
        file_name=file_name,
        mime="text/plain",
    )

    show_email_summary_panel(
        summary_title="AI SafeHome Safety Report",
        summary_text=report_text,
        default_subject=f"AI SafeHome Safety Report - {room_id}",
        key_prefix="safety_report_email",
    )

    show_share_summary_panel(
        summary_title="AI SafeHome Safety Report",
        summary_text=report_text,
        file_name=file_name,
        key_prefix="safety_report_share",
    )

    if st.button("Start New Safety Check"):
        reset_current_room_check()
        go_to_page("room_selection")

    if st.button("← Back to Landing Page"):
        go_to_page("landing")


def show_after_fixes_photo_page() -> None:
    """Lets a person photograph the room again and compare photo-based findings."""
    before = st.session_state.get("before_fix_comparison") or {}
    if not before.get("photo_bytes"):
        st.error("Start a safety check before creating a before-and-after comparison.")
        if st.button("Back to Risk Score"):
            go_to_page("risk_score")
        return

    st.title("AI SafeHome")
    st.subheader("Photo Comparison After Fixes")
    show_step_card("Take a new photo of the same room after making changes. AI SafeHome will compare possible hazards from both photos.")

    st.image(before["photo_bytes"], caption="Before: original room photo", width="stretch")
    after_photo = st.file_uploader(
        "Upload or take one new room photo (30 MB maximum)",
        type=ALLOWED_FILE_TYPES,
        accept_multiple_files=False,
        help="One JPG, PNG, or WEBP photo only.",
        key=f"after_fixes_photo_{st.session_state.get('upload_nonce', 0)}",
    )
    st.caption("One photo at a time • JPG, PNG, or WEBP • 30 MB maximum")

    if after_photo is None:
        if st.button("← Back to Risk Score"):
            go_to_page("risk_score")
        return

    valid, error = validate_uploaded_photo(after_photo)
    if not valid:
        st.error(error)
        return

    try:
        after_image = load_oriented_image(after_photo)
        after_analysis_file = oriented_image_file(after_image)
    except (OSError, ValueError):
        st.error("This file could not be read as an image. Choose a valid JPG, PNG, or WEBP photo.")
        return

    st.image(after_image, caption="After: new room photo", width="stretch")
    if st.button("Analyze and Compare Photos", type="primary"):
        with st.spinner("Analyzing the new photo and comparing results..."):
            after_analysis_file.seek(0)
            after_result = analyze_photo(after_analysis_file, st.session_state.get("room_type") or "Other")
            after_hazards = after_result.get("hazards", [])
            for hazard in after_hazards:
                hazard["priority"] = hazard.get("priority") or get_priority_for_hazard(hazard)
        st.session_state["after_fix_result"] = {
            "result": after_result,
            "photo_bytes": after_analysis_file.getvalue(),
        }

    saved_after = st.session_state.get("after_fix_result") or {}
    if saved_after.get("result"):
        after_result = saved_after["result"]
        after_hazards = after_result.get("hazards", [])
        before_hazards = before.get("hazards", [])
        before_categories = {item.get("category") for item in before_hazards if item.get("category")}
        after_categories = {item.get("category") for item in after_hazards if item.get("category")}
        resolved = sorted(before_categories - after_categories)
        still_present = sorted(before_categories & after_categories)
        new = sorted(after_categories - before_categories)
        after_score = calculate_score(after_hazards, [])

        st.subheader("Before-and-After Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Before Score", f"{before.get('score', 0)}/100")
        col2.metric("After Score", f"{after_score}/100")
        change = after_score - int(before.get("score", 0) or 0)
        col3.metric("Score Change", f"{change:+d} points")

        groups = [("Hazards Resolved", resolved, st.success), ("Still Needs Attention", still_present, st.warning), ("New Hazards", new, st.error)]
        for heading, categories, display in groups:
            st.markdown(f"### {heading}")
            if categories:
                for category in categories:
                    display(get_category_label(category))
            else:
                st.info("None found in this photo comparison.")

        st.subheader("New Photo: Approximate Hazard Locations")
        render_hazard_location_guide(saved_after.get("photo_bytes"), after_hazards)
        if st.button("Use This New Check as Current Results"):
            st.session_state["ai_result"] = after_result
            st.session_state["uploaded_photo_bytes"] = saved_after.get("photo_bytes")
            mark_new_room_check()
            reset_checklist_progress()
            go_to_page("checklist")

    if st.button("← Back to Risk Score"):
        go_to_page("risk_score")


def show_saved_results_page() -> None:
    st.title("AI SafeHome")
    st.subheader("My Saved Room Checks")

    if not is_database_enabled():
        st.info("Saved room checks are not available right now.")
        if st.button("← Back to Landing Page"):
            go_to_page("landing")
        return

    if not get_logged_in_home_id():
        show_home_id_login_box(key_prefix="saved_page_home_id")
        return

    home_id = get_logged_in_home_id()

    try:
        stats = fetch_summary_stats_for_home(home_id)
        rows = fetch_room_checks_by_home_id(home_id, limit=50)
    except Exception as error:
        st.error("Could not load saved checks.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Checks", stats.get("total_checks", 0))
    col2.metric("Average Score", f"{stats.get('average_score', 0)}/100")
    col3.metric("Most Common Room", stats.get("most_common_room") or "None")

    st.divider()
    st.subheader("My Saved Checks")

    if not rows:
        st.info("No checks have been saved to your account yet.")
    else:
        for index, row in enumerate(rows, start=1):
            st.markdown(
                f"""
                <div class="plain-card">
                    <strong>Check {index}</strong><br>
                    Room: {safe_text(row.get("room_type"))}<br>
                    Room Name: {safe_text(row.get("room_id") or "No Room Name")}<br>
                    Score: {safe_text(row.get("score"))}/100<br>
                    Risk Label: {safe_text(row.get("risk_level"))}<br>
                    Checked: {safe_text(format_database_datetime(row.get("created_at")))}
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.button("View Room-by-Room Stats", key="saved_results_view_room_stats"):
        go_to_page("room_stats")

    if st.button("← Back to Landing Page"):
        go_to_page("landing")


def build_room_stats_email_text(room_stats: Dict[str, Any]) -> str:
    hazard_counts = room_stats.get("hazard_counts", {})
    checklist_counts = room_stats.get("checklist_answer_counts", {})
    hazard_lines = [
        f"- {get_category_label(category)}: {count}"
        for category, count in sorted(hazard_counts.items(), key=lambda item: item[1], reverse=True)
    ] or ["- No saved hazards yet."]

    checklist_lines = [
        f"- {answer}: {count}"
        for answer, count in sorted(checklist_counts.items())
    ] or ["- No saved follow-up answers yet."]

    return f"""
Room Name: {room_stats.get("room_id")}
Room Type: {room_stats.get("room_type")}

Checks Saved: {room_stats.get("check_count", 0)}
Average Score: {room_stats.get("average_score", 0)}/100
Latest Score: {room_stats.get("latest_score")}/100
Highest Score: {room_stats.get("highest_score")}/100
Lowest Score: {room_stats.get("lowest_score")}/100
Latest Risk Label: {room_stats.get("latest_risk_level")}
Latest Check: {format_database_datetime(room_stats.get("latest_created_at"))}


Most Common Hazards:
{chr(10).join(hazard_lines)}

Follow-Up Answer Summary:
{chr(10).join(checklist_lines)}

""".strip()

def show_before_after_room_comparison(home_id: str, room_id: str) -> None:
    st.subheader("Before/After Room Comparison")

    try:
        checks = fetch_room_checks_by_room_id(home_id, room_id, limit=100)
    except Exception as error:
        st.error("Could not load checks for comparison.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    if len(checks) < 2:
        st.info(
            "Save at least two checks for this same Room Name to compare before and after results."
        )
        return

    ordered_checks = sort_checks_oldest_to_newest(checks)

    label_to_check = {
        get_check_display_label(check): check
        for check in ordered_checks
    }

    labels = list(label_to_check.keys())

    before_label = st.selectbox(
        "Choose before check",
        labels,
        index=0,
        key=f"before_check_{room_id}",
    )

    after_label = st.selectbox(
        "Choose after check",
        labels,
        index=len(labels) - 1,
        key=f"after_check_{room_id}",
    )

    before_check = label_to_check[before_label]
    after_check = label_to_check[after_label]

    if before_check.get("id") == after_check.get("id"):
        st.warning("Choose two different checks to compare.")
        return

    try:
        before_details = fetch_room_check_details(before_check["id"], home_id)
        after_details = fetch_room_check_details(after_check["id"], home_id)
    except Exception as error:
        st.error("Could not load check details for comparison.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    comparison = compare_hazard_categories(
        before_details=before_details,
        after_details=after_details,
    )

    resolved_labels = [
        get_category_label(category)
        for category in sorted(comparison["resolved"])
    ]

    still_present_labels = [
        get_category_label(category)
        for category in sorted(comparison["still_present"])
    ]

    new_labels = [
        get_category_label(category)
        for category in sorted(comparison["new"])
    ]

    before_score = before_check.get("score", 0)
    after_score = after_check.get("score", 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Before Score", f"{before_score}/100")
    col2.metric("After Score", f"{after_score}/100")
    col3.metric("Change", get_score_change_message(before_check, after_check))

    with st.container(border=True):
        st.write("**Before**")
        st.write(f"Checked: {format_database_datetime(before_check.get('created_at'))}")
        st.write(f"Score: {before_score}/100")
        st.write(f"Risk label: {before_check.get('risk_level', 'Unknown')}")
        st.divider()
        st.write("**After**")
        st.write(f"Checked: {format_database_datetime(after_check.get('created_at'))}")
        st.write(f"Score: {after_score}/100")
        st.write(f"Risk label: {after_check.get('risk_level', 'Unknown')}")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("### Resolved")
        if resolved_labels:
            for item in resolved_labels:
                st.success(item)
        else:
            st.info("None")

    with col_b:
        st.markdown("### Still Present")
        if still_present_labels:
            for item in still_present_labels:
                st.warning(item)
        else:
            st.info("None")

    with col_c:
        st.markdown("### New")
        if new_labels:
            for item in new_labels:
                st.error(item)
        else:
            st.info("None")

    comparison_text = build_before_after_summary_text(
        before_check=before_check,
        after_check=after_check,
        resolved_labels=resolved_labels,
        still_present_labels=still_present_labels,
        new_labels=new_labels,
    )

    with st.expander("Copy / share comparison summary"):
        st.text_area(
            "Before/after summary",
            value=comparison_text,
            height=280,
            key=f"before_after_text_{room_id}",
        )

        file_name = f"ai_safehome_before_after_{safe_filename_part(room_id)}.txt"

        st.download_button(
            label="Download Before/After Summary",
            data=comparison_text,
            file_name=file_name,
            mime="text/plain",
            key=f"before_after_download_{room_id}",
        )

    show_email_summary_panel(
        summary_title="AI SafeHome Before/After Comparison",
        summary_text=comparison_text,
        default_subject=f"AI SafeHome Before/After - {room_id}",
        key_prefix=f"before_after_email_{safe_filename_part(room_id)}",
    )

    show_share_summary_panel(
        summary_title="AI SafeHome Before/After Comparison",
        summary_text=comparison_text,
        file_name=f"ai_safehome_before_after_{safe_filename_part(room_id)}.txt",
        key_prefix=f"before_after_share_{safe_filename_part(room_id)}",
    )
def show_room_health_trend_chart(home_id: str, room_id: str) -> None:
    st.subheader("Room Health Trend")

    try:
        checks = fetch_room_checks_by_room_id(home_id, room_id, limit=100)
    except Exception as error:
        st.error("Could not load room score trend.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    if len(checks) < 2:
        st.info("Save at least two checks for this same Room Name to see a score trend.")
        return

    trend_rows = build_score_trend_rows(checks)
    trend_summary = get_trend_summary(checks)

    col1, col2, col3 = st.columns(3)
    col1.metric("First Score", f"{trend_summary.get('first_score')}/100")
    col2.metric("Latest Score", f"{trend_summary.get('latest_score')}/100")
    col3.metric("Trend", trend_summary.get("direction"))

    st.info(trend_summary.get("message"))

    chart_rows = [
        {
            "Check Number": row["Check Number"],
            "Score": row["Score"],
        }
        for row in trend_rows
    ]

    render_score_trend_chart(chart_rows)

    render_styled_table(trend_rows)

    trend_text = build_trend_summary_text(room_id, checks)

    with st.expander("Copy / download trend summary"):
        st.text_area(
            "Trend summary",
            value=trend_text,
            height=260,
            key=f"trend_text_{safe_filename_part(room_id)}",
        )

        st.download_button(
            label="Download Trend Summary",
            data=trend_text,
            file_name=f"ai_safehome_trend_{safe_filename_part(room_id)}.txt",
            mime="text/plain",
            key=f"trend_download_{safe_filename_part(room_id)}",
        )

    show_email_summary_panel(
        summary_title="AI SafeHome Room Health Trend",
        summary_text=trend_text,
        default_subject=f"AI SafeHome Room Trend - {room_id}",
        key_prefix=f"trend_email_{safe_filename_part(room_id)}",
    )
def show_room_stats_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Room-by-Room Stats")

    if not is_database_enabled():
        st.info("Saved room checks are not available right now.")
        if st.button("← Back to Landing Page"):
            go_to_page("landing")
        return

    if not get_logged_in_home_id():
        show_home_id_login_box(key_prefix="room_stats_home")
        return

    home_id = get_logged_in_home_id()

    try:
        room_stats_list = fetch_all_room_stats_for_home(home_id)
    except Exception as error:
        st.error("Could not load room stats.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    total_rooms = len(room_stats_list)
    total_checks = sum(room.get("check_count", 0) for room in room_stats_list)

    st.metric("Rooms Checked", sum(1 for room in room_stats_list if room.get("check_count", 0)))

    if not room_stats_list:
        st.info("No rooms have been added to your account yet.")
        if st.button("Start New Safety Check"):
            reset_current_room_check()
            go_to_page("room_selection")
        return

    all_hazard_counts: Dict[str, int] = {}
    for room in room_stats_list:
        for category, count in room.get("hazard_counts", {}).items():
            all_hazard_counts[category] = all_hazard_counts.get(category, 0) + count
    most_common_hazard = get_category_label(max(all_hazard_counts, key=all_hazard_counts.get)) if all_hazard_counts else "No hazards recorded yet"
    rooms_without_checks = [room for room in room_stats_list if not room.get("check_count", 0)]
    highest_score_room = max(room_stats_list, key=lambda room: room.get("latest_score") or 0)
    next_room = rooms_without_checks[0] if rooms_without_checks else highest_score_room
    improvement_rooms = [room for room in room_stats_list if room.get("check_count", 0) >= 2 and (room.get("latest_score") or 0) <= (room.get("average_score") or 0)]
    latest_improvement = improvement_rooms[0].get("room_id") if improvement_rooms else "Save another check to track improvement"

    st.subheader("Home Progress Dashboard")
    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Most common hazard:</strong> {safe_text(most_common_hazard)}<br>
            <strong>Latest improvement:</strong> {safe_text(latest_improvement)}<br>
            <strong>Next room to check:</strong> {safe_text(next_room.get('room_id'))} — {safe_text(next_room.get('room_type'))}<br>
            <span class="small-muted">Total saved checks: {total_checks}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("All Rooms")

    table_rows = []

    for room in room_stats_list:
        table_rows.append(
            {
                "Room Name": room.get("room_id"),
                "Room Type": room.get("room_type"),
                "Checks": room.get("check_count"),
                "Average Score": room.get("average_score"),
                "Latest Risk": room.get("latest_risk_level"),
                "Top Hazard": get_category_label(room.get("top_hazard")) if room.get("top_hazard") else "None",
            }
        )

    render_styled_table(table_rows)

    room_options = {
        f"{room.get('room_id')} — {room.get('room_type')}": room.get("room_id")
        for room in room_stats_list
    }

    selected_label = st.selectbox("Choose Room Name", list(room_options.keys()))
    selected_room_id = room_options[selected_label]

    selected_stats = fetch_room_stats(home_id, selected_room_id)

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Room Name:</strong> {safe_text(selected_stats.get("room_id"))}<br>
            <strong>Room Type:</strong> {safe_text(selected_stats.get("room_type"))}<br>
            <strong>Checks Saved:</strong> {safe_text(selected_stats.get("check_count"))}<br>
            <strong>Average Score:</strong> {safe_text(selected_stats.get("average_score"))}/100<br>
            <strong>Latest Score:</strong> {safe_text(selected_stats.get("latest_score"))}/100<br>
            <strong>Highest Score:</strong> {safe_text(selected_stats.get("highest_score"))}/100<br>
            <strong>Lowest Score:</strong> {safe_text(selected_stats.get("lowest_score"))}/100<br>
            <strong>Latest Risk Label:</strong> {safe_text(selected_stats.get("latest_risk_level"))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Most Common Hazards")

    hazard_counts = selected_stats.get("hazard_counts", {})

    if hazard_counts:
        hazard_rows = [
            {"Hazard": get_category_label(category)}
            for category, _count in sorted(hazard_counts.items(), key=lambda item: item[1], reverse=True)
        ]
        render_styled_table(hazard_rows)
    else:
        st.info("No saved hazards yet.")

    st.subheader("Check History")

    history_rows = fetch_room_checks_by_room_id(home_id, selected_room_id, limit=100)

    if history_rows:
        render_styled_table(
            [
                {
                    "Checked": format_database_datetime(row.get("created_at")),
                    "Score": row.get("score"),
                    "Risk Label": row.get("risk_level"),
                    "Hazards": row.get("hazard_count"),
                }
                for row in history_rows
            ]
        )
    else:
        st.info("No check history for this room yet.")
    show_room_health_trend_chart(home_id, selected_room_id)
    show_before_after_room_comparison(home_id, selected_room_id)
    room_stats_email_text = build_room_stats_email_text(selected_stats)

    show_email_summary_panel(
        summary_title="AI SafeHome Room Stats Summary",
        summary_text=room_stats_email_text,
        default_subject=f"AI SafeHome Room Stats - {selected_room_id}",
        key_prefix=f"room_stats_email_{safe_filename_part(selected_room_id)}",
    )

    if st.button("Analyze This Room Again"):
        st.session_state["room_type"] = selected_stats.get("room_type")
        st.session_state["current_room_id"] = selected_room_id
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["upload_nonce"] = st.session_state.get("upload_nonce", 0) + 1
        reset_checklist_progress()
        go_to_page("photo_upload")

    if st.button("← Back to Landing Page"):
        go_to_page("landing")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> None:
    setup_page()
    initialize_session_state()
    add_mobile_friendly_style()
    show_accessibility_panel()

    current_page = st.session_state.get("page", "landing")

    # Keep a predictable exit route on every workflow screen; signing out remains
    # intentionally limited to the landing page.
    if current_page != "landing" and st.button("← Back to Landing Page", key="global_back_to_landing"):
        go_to_page("landing")

    if current_page == "landing":
        show_landing_page()
    elif current_page == "room_selection":
        show_room_selection_page()
    elif current_page == "room_id_selection":
        show_room_id_selection_page()
    elif current_page == "photo_upload":
        show_photo_upload_page()
    elif current_page == "ai_results":
        show_ai_results_page()
    elif current_page == "checklist":
        show_checklist_page()
    elif current_page == "checklist_summary":
        show_checklist_summary_page()
    elif current_page == "risk_score":
        show_risk_score_page()
    elif current_page == "safety_report":
        show_safety_report_page()
    elif current_page == "after_fixes_photo":
        show_after_fixes_photo_page()
    elif current_page == "saved_results":
        show_saved_results_page()
    elif current_page == "room_stats":
        show_room_stats_page()
    else:
        st.session_state["page"] = "landing"
        show_landing_page()


if __name__ == "__main__":
    main()
