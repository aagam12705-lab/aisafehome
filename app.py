import secrets
import string
from typing import Any, Dict, List, Optional

import streamlit as st
from PIL import Image
from src.fix_tracker import get_fix_tracker_text, show_fix_tracker
from src.ai_analysis import analyze_photo
from src.checklist import ANSWER_OPTIONS, ANSWER_VALUE_MAP, CHECKLIST_QUESTIONS
from src.constants import (
    ALLOWED_FILE_TYPES,
    LANDING_EXPLANATION,
    MAX_FILE_SIZE_MB,
    PHOTO_NOT_STORED_NOTE,
    PHOTO_UPLOAD_PRIVACY_WARNING,
    PRIVACY_REMINDER,
    ROOM_OPTIONS,
    SAFETY_DISCLAIMER,
    TAGLINE,
)
from src.database import (
    create_home_id,
    create_home_room,
    fetch_all_room_stats_for_home,
    fetch_room_check_by_id,
    fetch_room_check_details,
    fetch_room_checks_by_home_id,
    fetch_room_checks_by_room_id,
    fetch_room_stats,
    fetch_rooms_for_home,
    fetch_summary_stats_for_home,
    get_database_status_message,
    get_next_room_id,
    home_id_exists,
    is_database_enabled,
    is_home_id_available,
    is_valid_home_id,
    save_room_check,
)
from src.email_ui import show_email_summary_panel, show_share_summary_panel
from src.fixes import build_top_fixes_text, get_recommended_first_fixes
from src.priorities import get_priority_for_category, get_priority_for_hazard
from src.report_builder import build_report_text
from src.scoring import calculate_score, get_risk_level, get_score_breakdown
from src.ui import (
    add_mobile_friendly_style,
    format_database_datetime,
    get_category_label,
    render_hazard_card,
    safe_filename_part,
    safe_text,
    setup_page,
    show_accessibility_panel,
    show_current_home_and_room_status,
    show_score_explanation_card,
    show_step_card,
)


# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------


def initialize_session_state() -> None:
    defaults = {
        "page": "landing",
        "room_type": None,
        "photo_uploaded": False,
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
        "database_save_complete": False,
        "database_save_id": None,
        "home_id": None,
        "home_login_error": None,
        "home_login_message": None,
        "last_created_home_id": None,
        "current_room_id": None,
        "current_home_room_id": None,
        "fix_statuses": {},
        "fix_notes": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_page(page_name: str) -> None:
    st.session_state["page"] = page_name
    st.rerun()


def reset_checklist_progress() -> None:
    st.session_state["checklist_index"] = 0
    st.session_state["checklist_answers_by_id"] = {}
    st.session_state["checklist_answers"] = []
    st.session_state["checklist_was_skipped"] = False


def reset_current_room_check() -> None:
    st.session_state["room_type"] = None
    st.session_state["photo_uploaded"] = False
    st.session_state["ai_result"] = None
    reset_checklist_progress()
    st.session_state["score"] = None
    st.session_state["risk_level"] = None
    st.session_state["score_breakdown"] = None
    st.session_state["report_text"] = None
    st.session_state["database_save_complete"] = False
    st.session_state["database_save_id"] = None
    st.session_state["current_room_id"] = None
    st.session_state["current_home_room_id"] = None
    st.session_state["fix_statuses"] = {}
    st.session_state["fix_notes"] = {}

# -----------------------------------------------------------------------------
# Home ID helpers
# -----------------------------------------------------------------------------


def clean_home_id_input(home_id: Optional[str]) -> str:
    if not home_id:
        return ""
    return str(home_id).strip().upper()


def generate_home_id() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "HOME-" + "-".join(
        "".join(secrets.choice(alphabet) for _ in range(4))
        for _ in range(3)
    )


def get_logged_in_home_id() -> Optional[str]:
    return st.session_state.get("home_id")


def log_out_home_id() -> None:
    st.session_state["home_id"] = None
    st.session_state["home_login_error"] = None
    st.session_state["home_login_message"] = None
    st.session_state["last_created_home_id"] = None


def log_in_with_home_id(home_id: str) -> bool:
    cleaned = clean_home_id_input(home_id)

    if not is_valid_home_id(cleaned):
        st.session_state["home_login_error"] = (
            "Invalid Home ID. Use a code like HOME-8K2M-Q9PA-W4ZT."
        )
        st.session_state["home_login_message"] = None
        return False

    try:
        exists = home_id_exists(cleaned)
    except Exception as error:
        st.session_state["home_login_error"] = (
            "Could not check this Home ID. Check your database connection."
        )
        st.session_state["home_login_message"] = str(error)
        return False

    if not exists:
        st.session_state["home_login_error"] = (
            "No saved Home ID was found with that code. Create it first or check your spelling."
        )
        st.session_state["home_login_message"] = None
        return False

    st.session_state["home_id"] = cleaned
    st.session_state["home_login_error"] = None
    st.session_state["home_login_message"] = "Home ID login successful."
    return True


def create_random_available_home_id() -> str:
    if not is_database_enabled():
        raise RuntimeError("Database saving is disabled, so a Home ID cannot be created.")

    for _ in range(10):
        candidate = generate_home_id()

        if is_home_id_available(candidate):
            created = create_home_id(candidate)
            st.session_state["home_id"] = created
            st.session_state["last_created_home_id"] = created
            st.session_state["home_login_error"] = None
            st.session_state["home_login_message"] = "New Home ID created."
            return created

    raise RuntimeError("Could not create a unique Home ID. Try again.")


def create_custom_home_id(home_id: str) -> bool:
    cleaned = clean_home_id_input(home_id)

    if not is_valid_home_id(cleaned):
        st.session_state["home_login_error"] = (
            "Invalid Home ID. Use the format HOME-ABCD-1234-WXYZ."
        )
        return False

    try:
        if not is_home_id_available(cleaned):
            st.session_state["home_login_error"] = (
                "That Home ID is already taken. Choose a different one."
            )
            return False

        created = create_home_id(cleaned)
        st.session_state["home_id"] = created
        st.session_state["last_created_home_id"] = created
        st.session_state["home_login_error"] = None
        st.session_state["home_login_message"] = "Custom Home ID created."
        return True

    except Exception as error:
        st.session_state["home_login_error"] = (
            "Could not create this Home ID. Check your database connection."
        )
        st.session_state["home_login_message"] = str(error)
        return False


def show_home_id_status(key_suffix: str = "main") -> None:
    home_id = get_logged_in_home_id()

    if home_id:
        st.success(f"Logged in with Home ID: {home_id}")
        st.caption(
            "Save this Home ID somewhere safe. Anyone with this code can view checks saved under it."
        )

        if st.button("Log Out of Home ID", key=f"log_out_home_id_{key_suffix}"):
            log_out_home_id()
            st.rerun()
    else:
        st.info("No Home ID is logged in yet.")


def show_home_id_login_box(key_prefix: str = "home_id") -> None:
    st.subheader("Home ID Login")
    st.write(
        "Use an anonymous Home ID to save and view checks for one home. "
        "Do not use a name or address."
    )

    st.warning(
        "A Home ID is not a password. Anyone with the Home ID can view checks saved under it."
    )

    st.caption(get_database_status_message())

    if not is_database_enabled():
        st.info(
            "Database saving is disabled. Enable DATABASE_ENABLED=true before creating or using Home IDs."
        )
        return

    if st.session_state.get("home_login_error"):
        st.error(st.session_state["home_login_error"])

    if st.session_state.get("home_login_message"):
        st.info(st.session_state["home_login_message"])

    tab1, tab2, tab3 = st.tabs(
        ["Create Random ID", "Choose Custom ID", "Log In Existing ID"]
    )

    with tab1:
        if st.button(
            "Create Random Home ID",
            key=f"{key_prefix}_random",
            type="primary",
        ):
            try:
                created = create_random_available_home_id()
                st.success(f"Created Home ID: {created}")
                st.warning("Copy this Home ID now. You need it later to view saved checks.")
                st.rerun()
            except Exception as error:
                st.error("Could not create a random Home ID.")
                with st.expander("Technical details"):
                    st.code(str(error))

    with tab2:
        custom = st.text_input(
            "Choose a Home ID",
            placeholder="HOME-SAFE-2026-DEMO",
            key=f"{key_prefix}_custom",
        )

        if st.button("Check Availability", key=f"{key_prefix}_check"):
            try:
                if not is_valid_home_id(custom):
                    st.error("Invalid format. Use something like HOME-ABCD-1234-WXYZ.")
                elif is_home_id_available(custom):
                    st.success("This Home ID is available.")
                else:
                    st.error("This Home ID is already taken.")
            except Exception as error:
                st.error("Could not check availability.")
                with st.expander("Technical details"):
                    st.code(str(error))

        if st.button(
            "Create This Home ID",
            key=f"{key_prefix}_create_custom",
            type="primary",
        ):
            if create_custom_home_id(custom):
                st.success(f"Created Home ID: {st.session_state['home_id']}")
                st.rerun()

    with tab3:
        existing = st.text_input(
            "Enter existing Home ID",
            placeholder="HOME-8K2M-Q9PA-W4ZT",
            key=f"{key_prefix}_existing",
        )

        if st.button(
            "Log In with Home ID",
            key=f"{key_prefix}_login",
            type="primary",
        ):
            if log_in_with_home_id(existing):
                st.success("Home ID login successful.")
                st.rerun()


# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------


def validate_uploaded_photo(uploaded_file: Any) -> tuple[bool, str]:
    if uploaded_file is None:
        return False, "No file uploaded."

    size_mb = uploaded_file.size / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB."

    return True, ""


def get_current_database_save_payload() -> Dict[str, Any]:
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    fixes = get_recommended_first_fixes(
        ai_hazards=hazards,
        checklist_answers=checklist_answers,
        limit=5,
    )

    return {
        "room_type": st.session_state.get("room_type"),
        "room_id": st.session_state.get("current_room_id"),
        "score": st.session_state.get("score"),
        "risk_level": st.session_state.get("risk_level"),
        "hazards": hazards,
        "checklist_answers": checklist_answers,
        "recommended_fixes": fixes,
        "checklist_was_skipped": st.session_state.get("checklist_was_skipped", False),
        "using_demo_sample": False,
        "demo_sample_name": None,
    }


def show_database_save_panel() -> None:
    st.subheader("Save Anonymous Result")

    st.caption(get_database_status_message())

    if not is_database_enabled():
        st.info("Database saving is disabled.")
        return

    home_id = get_logged_in_home_id()

    if not home_id:
        st.warning("Create or log in with a Home ID before saving.")
        show_home_id_login_box(key_prefix="save_panel_home")
        return

    room_id = st.session_state.get("current_room_id")

    if not room_id:
        st.warning("Choose or create a Room ID before saving.")
        if st.button("Choose Room ID"):
            go_to_page("room_id_selection")
        return

    if st.session_state.get("database_save_complete"):
        st.success(f"Already saved. Check ID: {st.session_state.get('database_save_id')}")
        return

    st.success(f"Saving under Home ID {home_id} and Room ID {room_id}")

    safety_confirmed = st.checkbox(
        "I confirm this result contains no personal, medical, or real patient information.",
        key="database_safety_confirmed",
    )

    if st.button("Save Anonymous Result", type="primary"):
        if not safety_confirmed:
            st.error("Confirm the privacy checkbox before saving.")
            return

        payload = get_current_database_save_payload()

        try:
            saved_id = save_room_check(
                home_id=home_id,
                room_type=payload["room_type"],
                score=payload["score"],
                risk_level=payload["risk_level"],
                hazards=payload["hazards"],
                checklist_answers=payload["checklist_answers"],
                recommended_fixes=payload["recommended_fixes"],
                checklist_was_skipped=payload["checklist_was_skipped"],
                safety_confirmed=safety_confirmed,
                using_demo_sample=payload["using_demo_sample"],
                demo_sample_name=payload["demo_sample_name"],
                room_id=payload["room_id"],
            )

            st.session_state["database_save_complete"] = True
            st.session_state["database_save_id"] = saved_id

            st.success(f"Saved. Check ID: {saved_id}")

        except Exception as error:
            st.error("Could not save this result.")
            with st.expander("Technical details"):
                st.code(str(error))


# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------


def show_landing_page() -> None:
    st.title("🏠 AI SafeHome")
    st.markdown(f'<div class="big-tagline">{TAGLINE}</div>', unsafe_allow_html=True)

    st.write(LANDING_EXPLANATION)
    st.warning(SAFETY_DISCLAIMER)
    st.info(PRIVACY_REMINDER)

    show_home_id_status(key_suffix="landing")

    if st.button("Start Safety Check", type="primary"):
        reset_current_room_check()
        go_to_page("room_selection")

    if st.button("Access Saved Checks by Home ID"):
        go_to_page("saved_results")

    if st.button("View Room-by-Room Stats"):
        go_to_page("room_stats")


def show_room_selection_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 1: Choose a Room")
    show_step_card("Step 1 of 6 — Choose the room you want to check.")

    selected_room = st.radio("Which room are you checking?", ROOM_OPTIONS, index=0)

    if st.button("Continue →", type="primary"):
        st.session_state["room_type"] = selected_room
        st.session_state["current_room_id"] = None
        st.session_state["current_home_room_id"] = None
        go_to_page("room_id_selection")

    if st.button("← Back to Landing Page"):
        go_to_page("landing")


def show_room_id_selection_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Choose Room ID")

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

    st.info("Room IDs keep repeated rooms separate, like BEDROOM-1 and BEDROOM-2.")

    if not is_database_enabled():
        st.warning("Database saving is disabled, so this check will not be attached to a Room ID.")

        if st.button("Continue Without Room ID →", type="primary"):
            st.session_state["current_room_id"] = None
            st.session_state["current_home_room_id"] = None
            go_to_page("photo_upload")

        return

    home_id = get_logged_in_home_id()

    if not home_id:
        st.warning("Create or log in with a Home ID before choosing a Room ID.")
        show_home_id_login_box(key_prefix="room_id_page_home")

        if st.button("Continue Without Database Room Tracking"):
            st.session_state["current_room_id"] = None
            st.session_state["current_home_room_id"] = None
            go_to_page("photo_upload")

        return

    show_home_id_status(key_suffix="room_id_page")

    try:
        existing_rooms = fetch_rooms_for_home(home_id=home_id, room_type=room_type)
        suggested_room_id = get_next_room_id(home_id=home_id, room_type=room_type)
    except Exception as error:
        st.error("Could not load rooms for this Home ID.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    if existing_rooms:
        st.write(f"Existing {room_type} rooms:")
        for room in existing_rooms:
            st.write(f"- {room.get('room_id')}")
    else:
        st.info(f"No existing {room_type} rooms found for this Home ID yet.")

    tab1, tab2 = st.tabs(["Use Existing Room", "Create New Room"])

    with tab1:
        if not existing_rooms:
            st.info(f"No existing {room_type} rooms are available yet.")
        else:
            room_options = {room.get("room_id"): room for room in existing_rooms}
            selected = st.selectbox(
                "Choose existing Room ID",
                list(room_options.keys()),
                key="existing_room_id_select",
            )

            if st.button("Use This Room ID →", type="primary"):
                selected_room = room_options[selected]
                st.session_state["current_room_id"] = selected_room["room_id"]
                st.session_state["current_home_room_id"] = selected_room["id"]
                go_to_page("photo_upload")

    with tab2:
        st.caption("Use IDs like BEDROOM-1, BEDROOM-2, BATHROOM-1. Do not use names or addresses.")

        new_room_id = st.text_input(
            "New Room ID",
            value=suggested_room_id,
            key="new_room_id_input",
        )

        if st.button("Create and Use This Room ID →", type="primary"):
            try:
                created_room = create_home_room(
                    home_id=home_id,
                    room_id=new_room_id,
                    room_type=room_type,
                )

                st.session_state["current_room_id"] = created_room["room_id"]
                st.session_state["current_home_room_id"] = created_room["id"]
                go_to_page("photo_upload")

            except Exception as error:
                st.error("Could not create that Room ID.")
                with st.expander("Technical details"):
                    st.code(str(error))

    show_current_home_and_room_status()

    if st.button("← Back to Room Selection"):
        go_to_page("room_selection")


def show_photo_upload_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 2: Upload Room Photo")
    show_step_card("Step 2 of 6 — Upload or take a staged room photo.")

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

    show_current_home_and_room_status()

    st.warning(PHOTO_UPLOAD_PRIVACY_WARNING)
    st.info(PHOTO_NOT_STORED_NOTE)

    uploaded_file = st.file_uploader(
        "Upload or take a room photo",
        type=ALLOWED_FILE_TYPES,
        help="On iPhone, this may let you choose Photo Library or Take Photo.",
    )

    if uploaded_file is not None:
        valid, error = validate_uploaded_photo(uploaded_file)

        if not valid:
            st.error(error)
            return

        image = Image.open(uploaded_file)
        st.image(image, caption=f"Preview of uploaded {room_type} photo", use_container_width=True)
        uploaded_file.seek(0)

        st.session_state["photo_uploaded"] = True
        st.success("Photo uploaded successfully.")

        if st.button("Analyze Photo →", type="primary"):
            with st.spinner("Analyzing photo..."):
                ai_result = analyze_photo(uploaded_file, room_type)

                for hazard in ai_result.get("hazards", []):
                    hazard["priority"] = hazard.get("priority") or get_priority_for_hazard(hazard)

                st.session_state["ai_result"] = ai_result

            go_to_page("ai_results")

    if st.button("← Back to Room ID"):
        go_to_page("room_id_selection")


def show_ai_results_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 3: AI Results")
    show_step_card("Step 3 of 6 — Review possible hazards found by AI.")

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])

    st.write(ai_result.get("summary", "No summary available."))

    if hazards:
        for index, hazard in enumerate(hazards, start=1):
            render_hazard_card(hazard, index)
    else:
        st.info("No possible hazards were listed by AI.")

    not_visible = ai_result.get("not_visible", [])

    if not_visible:
        with st.expander("AI could not confirm"):
            for item in not_visible:
                st.write(f"- {item}")

    st.warning(
        ai_result.get(
            "safety_reminder",
            "AI may miss hazards. Human review is recommended.",
        )
    )

    if st.button("Continue to Checklist →", type="primary"):
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


def build_ordered_checklist_answers() -> List[Dict[str, Any]]:
    ordered = []

    for question in CHECKLIST_QUESTIONS:
        saved = st.session_state["checklist_answers_by_id"].get(question["id"])
        if saved:
            ordered.append(saved)

    return ordered


def finish_checklist() -> None:
    st.session_state["checklist_answers"] = build_ordered_checklist_answers()
    go_to_page("checklist_summary")


def skip_entire_checklist() -> None:
    st.session_state["checklist_answers"] = []
    st.session_state["checklist_was_skipped"] = True
    go_to_page("checklist_summary")


def show_checklist_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 4: Safety Checklist")
    show_step_card("Step 4 of 6 — Answer one checklist question at a time.")

    index = st.session_state.get("checklist_index", 0)

    if index >= len(CHECKLIST_QUESTIONS):
        finish_checklist()
        return

    question = CHECKLIST_QUESTIONS[index]

    st.progress((index + 1) / len(CHECKLIST_QUESTIONS))
    st.write(f"Question {index + 1} of {len(CHECKLIST_QUESTIONS)}")
    st.markdown(f"### {question['text']}")

    answer_label = st.radio(
        "Choose an answer",
        ANSWER_OPTIONS,
        key=f"checklist_answer_{question['id']}",
    )

    if st.button("Save and Next →", type="primary"):
        save_checklist_answer(question, answer_label)

        if index + 1 >= len(CHECKLIST_QUESTIONS):
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

        if index + 1 >= len(CHECKLIST_QUESTIONS):
            finish_checklist()
        else:
            st.session_state["checklist_index"] = index + 1
            st.rerun()

    if st.button("Skip Entire Checklist"):
        skip_entire_checklist()

    if index > 0:
        if st.button("← Previous Question"):
            st.session_state["checklist_index"] = max(0, index - 1)
            st.rerun()


def show_checklist_summary_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Checklist Summary")

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    if st.session_state.get("checklist_was_skipped"):
        st.info("Checklist was skipped. Score uses AI hazards only.")
    else:
        st.write(f"Checklist answers saved: {len(checklist_answers)}")

    score = calculate_score(hazards, checklist_answers)
    risk_level = get_risk_level(score)
    score_breakdown = get_score_breakdown(hazards, checklist_answers)

    st.session_state["score"] = score
    st.session_state["risk_level"] = risk_level
    st.session_state["score_breakdown"] = score_breakdown
    st.session_state["report_text"] = build_report_text()

    st.metric("Risk Score", f"{score}/100")
    st.write(f"Risk label: **{risk_level}**")

    show_score_explanation_card(score_breakdown)

    if st.button("View Risk Score →", type="primary"):
        go_to_page("risk_score")


def show_top_5_fixes() -> List[Dict[str, Any]]:
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    fixes = get_recommended_first_fixes(
        ai_hazards=hazards,
        checklist_answers=checklist_answers,
        limit=5,
    )

    st.subheader("Top 5 Fixes")

    if not fixes:
        st.info("No specific fixes were generated.")
        return []

    for fix in fixes:
        st.markdown(
            f"""
            <div class="plain-card">
                <strong>{fix.get("rank")}. [{safe_text(fix.get("priority"))}]</strong><br>
                {safe_text(fix.get("text"))}<br>
                <span class="small-muted">Source: {safe_text(fix.get("source"))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return fixes
    st.subheader("Top 5 Fixes")

    if not fixes:
        st.info("No specific fixes were generated.")
        return

    for fix in fixes:
        st.markdown(
            f"""
            <div class="plain-card">
                <strong>{fix.get("rank")}. [{safe_text(fix.get("priority"))}]</strong><br>
                {safe_text(fix.get("text"))}<br>
                <span class="small-muted">Source: {safe_text(fix.get("source"))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_risk_score_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 5: Risk Score")
    show_step_card("Step 5 of 6 — Review score and first fixes.")

    score = st.session_state.get("score")
    risk_level = st.session_state.get("risk_level")
    score_breakdown = st.session_state.get("score_breakdown")

    if score is None:
        st.error("No score is available yet.")
        if st.button("Back to Checklist"):
            go_to_page("checklist")
        return

    st.metric("Risk Score", f"{score}/100")
    st.write(f"Risk label: **{risk_level}**")

    show_score_explanation_card(score_breakdown)

    fixes = show_top_5_fixes()
    show_fix_tracker(fixes)

    st.divider()
    show_database_save_panel()

    if st.button("Create Safety Report →", type="primary"):
        st.session_state["report_text"] = build_report_text()
        go_to_page("safety_report")

    if st.button("View Room-by-Room Stats"):
        go_to_page("room_stats")


def show_safety_report_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 6: Safety Report")

    report_text = st.session_state.get("report_text") or build_report_text()
    st.session_state["report_text"] = report_text

    st.markdown(
        f'<div class="print-report">{safe_text(report_text)}</div>',
        unsafe_allow_html=True,
    )

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


def show_saved_results_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Saved Checks by Home ID")

    st.caption(get_database_status_message())

    if not is_database_enabled():
        st.info("Database saving is disabled.")
        if st.button("← Back to Landing Page"):
            go_to_page("landing")
        return

    show_home_id_status(key_suffix="saved_results")

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
    st.subheader("Checks Saved Under This Home ID")

    if not rows:
        st.info("No checks have been saved under this Home ID yet.")
    else:
        for index, row in enumerate(rows, start=1):
            st.markdown(
                f"""
                <div class="plain-card">
                    <strong>Check {index}</strong><br>
                    Check ID: {safe_text(row.get("id"))}<br>
                    Room: {safe_text(row.get("room_type"))}<br>
                    Room ID: {safe_text(row.get("room_id") or "No Room ID")}<br>
                    Score: {safe_text(row.get("score"))}/100<br>
                    Risk Label: {safe_text(row.get("risk_level"))}<br>
                    Saved At: {safe_text(format_database_datetime(row.get("created_at")))}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Look Up One Check by Check ID")

    check_id = st.text_input("Enter Check ID")

    if st.button("Find Check by ID"):
        if not check_id.strip():
            st.error("Enter a Check ID first.")
        else:
            check = fetch_room_check_by_id(check_id, home_id)

            if not check:
                st.error("No check found for that Check ID under this Home ID.")
            else:
                st.success("Check found.")
                st.write(check)

                details = fetch_room_check_details(check["id"])
                with st.expander("Details"):
                    for detail in details:
                        st.write(detail)

    if st.button("View Room-by-Room Stats"):
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
    ] or ["- No saved checklist answers yet."]

    return f"""
Room ID: {room_stats.get("room_id")}
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

Checklist Answer Summary:
{chr(10).join(checklist_lines)}
""".strip()


def show_room_stats_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Room-by-Room Stats")

    st.caption(get_database_status_message())

    if not is_database_enabled():
        st.info("Database saving is disabled.")
        if st.button("← Back to Landing Page"):
            go_to_page("landing")
        return

    show_home_id_status(key_suffix="room_stats")

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

    col1, col2 = st.columns(2)
    col1.metric("Rooms Created", total_rooms)
    col2.metric("Total Checks", total_checks)

    if not room_stats_list:
        st.info("No rooms have been created under this Home ID yet.")
        if st.button("Start New Safety Check"):
            reset_current_room_check()
            go_to_page("room_selection")
        return

    st.subheader("All Rooms")

    table_rows = []

    for room in room_stats_list:
        table_rows.append(
            {
                "Room ID": room.get("room_id"),
                "Room Type": room.get("room_type"),
                "Checks": room.get("check_count"),
                "Average Score": room.get("average_score"),
                "Latest Risk": room.get("latest_risk_level"),
                "Top Hazard": get_category_label(room.get("top_hazard")) if room.get("top_hazard") else "None",
            }
        )

    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    room_options = {
        f"{room.get('room_id')} — {room.get('room_type')}": room.get("room_id")
        for room in room_stats_list
    }

    selected_label = st.selectbox("Choose Room ID", list(room_options.keys()))
    selected_room_id = room_options[selected_label]

    selected_stats = fetch_room_stats(home_id, selected_room_id)

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Room ID:</strong> {safe_text(selected_stats.get("room_id"))}<br>
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
            {
                "Hazard": get_category_label(category),
                "Count": count,
            }
            for category, count in sorted(hazard_counts.items(), key=lambda item: item[1], reverse=True)
        ]
        st.dataframe(hazard_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No saved hazards yet.")

    st.subheader("Check History")

    history_rows = fetch_room_checks_by_room_id(home_id, selected_room_id, limit=100)

    if history_rows:
        st.dataframe(
            [
                {
                    "Saved At": format_database_datetime(row.get("created_at")),
                    "Check ID": row.get("id"),
                    "Score": row.get("score"),
                    "Risk Label": row.get("risk_level"),
                    "Hazards": row.get("hazard_count"),
                }
                for row in history_rows
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No check history for this room yet.")

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
    elif current_page == "saved_results":
        show_saved_results_page()
    elif current_page == "room_stats":
        show_room_stats_page()
    else:
        st.session_state["page"] = "landing"
        show_landing_page()


if __name__ == "__main__":
    main()