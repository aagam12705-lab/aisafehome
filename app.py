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

importlib.reload(_database_module)
importlib.reload(_constants_module)
importlib.reload(_ai_analysis_module)
importlib.reload(_scoring_module)
importlib.reload(_ui_module)
importlib.reload(_comparison_module)
importlib.reload(_trends_module)
importlib.reload(_email_ui_module)

from src.comparison import (
    build_before_after_summary_text,
    compare_hazard_categories,
    get_check_display_label,
    get_score_change_message,
    sort_checks_oldest_to_newest,
)
import streamlit as st
from PIL import Image, ImageDraw, ImageOps
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
    MAX_FILE_SIZE_MB,
    ROOM_OPTIONS,
    SAFETY_DISCLAIMER,
    TAGLINE,
)
from src.database import (
    authenticate_home,
    create_password_reset_code,
    create_protected_home,
    create_home_room,
    fetch_all_room_stats_for_home,
    fetch_room_check_details,
    fetch_room_checks_by_home_id,
    fetch_room_checks_by_room_id,
    fetch_room_stats,
    fetch_rooms_for_home,
    fetch_summary_stats_for_home,
    get_next_room_id,
    home_id_exists,
    is_database_enabled,
    is_home_id_available,
    reset_home_password,
    save_room_check,
)
from src.email_service import is_valid_email_address, send_summary_email
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
    render_score_trend_chart,
    render_styled_table,
    safe_filename_part,
    safe_text,
    setup_page,
    show_accessibility_panel,
    show_current_home_and_room_status,
    show_read_aloud_button,
    show_risk_score_bar,
    show_score_explanation_card,
    show_step_card,
)


# -----------------------------------------------------------------------------
# Session state fuctions
# -----------------------------------------------------------------------------


def initialize_session_state() -> None:
    defaults = {
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


def mark_new_room_check() -> None:
    """Marks a new analysis so it is saved once, rather than on every rerun."""
    st.session_state["check_run_nonce"] = st.session_state.get("check_run_nonce", 0) + 1
    st.session_state["database_save_complete"] = False
    st.session_state["database_save_id"] = None
    st.session_state["database_saved_run_nonce"] = None


def reset_current_room_check() -> None:
    st.session_state["room_type"] = None
    st.session_state["photo_uploaded"] = False
    st.session_state["photo_quality"] = None
    st.session_state["ai_result"] = None
    reset_checklist_progress()
    st.session_state["score"] = None
    st.session_state["risk_level"] = None
    st.session_state["score_breakdown"] = None
    st.session_state["report_text"] = None
    st.session_state["database_save_complete"] = False
    st.session_state["database_save_id"] = None
    st.session_state["database_saved_run_nonce"] = None
    st.session_state["current_room_id"] = None
    st.session_state["current_home_room_id"] = None
    st.session_state["uploaded_photo_bytes"] = None
    st.session_state["before_fix_comparison"] = None
    st.session_state["after_fix_result"] = None
    st.session_state["upload_nonce"] = st.session_state.get("upload_nonce", 0) + 1

# -----------------------------------------------------------------------------
# Account helpers (stored internally as home_id for database compatibility)
# -----------------------------------------------------------------------------


def clean_home_id_input(home_id: Optional[str]) -> str:
    if not home_id:
        return ""
    return " ".join(str(home_id).strip().split())


def get_logged_in_home_id() -> Optional[str]:
    return st.session_state.get("home_id")


def log_out_home_id() -> None:
    st.session_state["home_id"] = None
    st.session_state["home_login_error"] = None
    st.session_state["home_login_message"] = None
    st.session_state["last_created_home_id"] = None


def log_in_with_home_id(home_id: str, password: str) -> bool:
    cleaned = clean_home_id_input(home_id).lower()

    if not is_valid_email_address(cleaned):
        st.session_state["home_login_error"] = "Enter a valid email address."
        st.session_state["home_login_message"] = None
        return False

    try:
        exists = authenticate_home(cleaned, password)
    except Exception as error:
        st.session_state["home_login_error"] = (
            "Could not sign in right now. Please try again."
        )
        st.session_state["home_login_message"] = str(error)
        return False

    if not exists:
        st.session_state["home_login_error"] = (
            "The email address or password is incorrect."
        )
        st.session_state["home_login_message"] = None
        return False

    st.session_state["home_id"] = cleaned
    st.session_state["home_login_error"] = None
    st.session_state["home_login_message"] = "Signed in successfully."
    return True


def create_custom_home_id(email: str, password: str) -> bool:
    cleaned = clean_home_id_input(email).lower()

    if not is_valid_email_address(cleaned):
        st.session_state["home_login_error"] = "Enter a valid email address."
        return False

    try:
        if not is_home_id_available(cleaned):
            st.session_state["home_login_error"] = (
                "An account already exists with that email address."
            )
            return False

        created = create_protected_home(cleaned, password, cleaned)
        st.session_state["home_id"] = created
        st.session_state["last_created_home_id"] = created
        st.session_state["home_login_error"] = None
        st.session_state["home_login_message"] = "User account created."
        return True

    except Exception as error:
        st.session_state["home_login_error"] = (
            f"Could not create this user account: {error}"
        )
        st.session_state["home_login_message"] = None
        return False


def show_home_id_status(key_suffix: str = "main", allow_logout: bool = False) -> None:
    home_id = get_logged_in_home_id()

    if home_id:
        st.success(f"Signed in as: {home_id}")

        if allow_logout and st.button("Log Out", key=f"log_out_home_id_{key_suffix}"):
            log_out_home_id()
            st.rerun()


def show_home_id_login_box(key_prefix: str = "home_id") -> None:
    st.subheader("Sign In")
    st.write("Use your email and password to save and view room checks.")

    if not is_database_enabled():
        st.info(
            "Saved room checks are not available right now."
        )
        return

    if st.session_state.get("home_login_error"):
        st.error(st.session_state["home_login_error"])

    if st.session_state.get("home_login_message"):
        st.info(st.session_state["home_login_message"])

    tab1, tab2 = st.tabs(["Use Existing Account", "Create New Account"])

    with tab1:
        existing = st.text_input(
            "Email address",
            placeholder="name@example.com",
            key=f"{key_prefix}_existing",
        )
        password = st.text_input("Password", type="password", key=f"{key_prefix}_login_password")

        if st.button("Sign In", key=f"{key_prefix}_login", type="primary"):
            if log_in_with_home_id(existing, password):
                st.success("Signed in successfully.")
                st.rerun()

        with st.expander("Forgot password?"):
            if st.button("Email Reset Code", key=f"{key_prefix}_send_reset"):
                try:
                    email, code = create_password_reset_code(existing)
                    send_summary_email(email, "AI SafeHome password reset", f"Your reset code is {code}. It expires in 15 minutes.")
                    st.success("A reset code was sent to this account's email address.")
                except Exception as error:
                    st.error(str(error))
            reset_code = st.text_input("Reset code", key=f"{key_prefix}_reset_code")
            new_password = st.text_input("New password", type="password", key=f"{key_prefix}_new_password")
            if st.button("Reset Password", key=f"{key_prefix}_reset_password"):
                try:
                    reset_home_password(existing, reset_code, new_password)
                    st.success("Password reset. You can now sign in.")
                except Exception as error:
                    st.error(str(error))

    with tab2:
        custom = st.text_input(
            "Email address",
            placeholder="name@example.com",
            key=f"{key_prefix}_custom",
        )
        password = st.text_input("Create password", type="password", key=f"{key_prefix}_password")

        if st.button("Create Account", key=f"{key_prefix}_create_custom", type="primary"):
            if create_custom_home_id(custom, password):
                st.success("Account created.")
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


def load_oriented_image(uploaded_file: Any) -> Image.Image:
    """Open an uploaded photo and apply its camera orientation before display or AI use."""
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)
    image.load()
    return image.copy()


def oriented_image_file(image: Image.Image) -> io.BytesIO:
    """Provide the same upright pixels to both preview and analysis."""
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    buffer.name = "upright_room_photo.jpg"
    buffer.type = "image/jpeg"
    return buffer


def get_current_database_save_payload() -> Dict[str, Any]:
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    fixes = get_recommended_first_fixes(
        ai_hazards=hazards,
        checklist_answers=checklist_answers,
        limit=5,
    )
    analysis_mode = ai_result.get("analysis_mode", "sample")
    is_sample_result = analysis_mode != "real"

    return {
        "room_type": st.session_state.get("room_type"),
        "room_id": st.session_state.get("current_room_id"),
        "score": st.session_state.get("score"),
        "risk_level": st.session_state.get("risk_level"),
        "hazards": hazards,
        "checklist_answers": checklist_answers,
        "recommended_fixes": fixes,
        "checklist_was_skipped": st.session_state.get("checklist_was_skipped", False),
        "using_demo_sample": is_sample_result,
        "demo_sample_name": (
            "Built-in sample analysis"
            if analysis_mode == "sample"
            else "Fallback sample analysis"
            if analysis_mode == "fallback"
            else None
        ),
    }


def show_database_save_panel() -> None:
    st.subheader("Save Result")

    if not is_database_enabled():
        st.info("Saving is not available right now.")
        return

    home_id = get_logged_in_home_id()

    if not home_id:
        st.warning("Create or sign in to an account before saving.")
        show_home_id_login_box(key_prefix="save_panel_home")
        return

    room_id = st.session_state.get("current_room_id")

    if not room_id:
        st.warning("Choose or create a Room ID before saving.")
        if st.button("Choose Room ID"):
            go_to_page("room_id_selection")
        return

    if st.session_state.get("database_save_complete"):
        st.success("This check is in your room stats.")
        if st.button("View Updated Room Stats"):
            go_to_page("room_stats")
        return

    st.success(f"Saving to your account for Room ID {room_id}")

    if st.button("Save Result", type="primary"):

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
                safety_confirmed=True,
                using_demo_sample=payload["using_demo_sample"],
                demo_sample_name=payload["demo_sample_name"],
                room_id=payload["room_id"],
            )

            st.session_state["database_save_complete"] = True
            st.session_state["database_save_id"] = saved_id

            st.success("Saved to your room stats.")

        except Exception as error:
            st.error("Could not save this result.")
            with st.expander("Technical details"):
                st.code(str(error))


def automatically_save_current_room_check() -> None:
    """Adds each completed tracked room check to saved stats exactly once."""
    home_id = get_logged_in_home_id()
    if not is_database_enabled() or not home_id or not st.session_state.get("current_room_id"):
        return

    run_nonce = st.session_state.get("check_run_nonce", 0)
    if st.session_state.get("database_saved_run_nonce") == run_nonce:
        return

    payload = get_current_database_save_payload()
    if payload.get("score") is None or not payload.get("room_type"):
        return

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
            safety_confirmed=True,
            using_demo_sample=payload["using_demo_sample"],
            demo_sample_name=payload["demo_sample_name"],
            room_id=payload["room_id"],
        )
        st.session_state["database_save_complete"] = True
        st.session_state["database_save_id"] = saved_id
        st.session_state["database_saved_run_nonce"] = run_nonce
        st.success("This completed room check was added to your room stats.")
    except Exception:
        st.warning("This check could not be added to room stats yet. You can save it from the section below.")


# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------


def show_landing_page() -> None:
    st.title("AI SafeHome")
    st.markdown(f'<div class="big-tagline">{TAGLINE}</div>', unsafe_allow_html=True)

    st.write(LANDING_EXPLANATION)
    st.warning(SAFETY_DISCLAIMER)

    st.markdown(
        """
        <div class="plain-card">
            <strong>How it works</strong><br><br>
            1. Choose one room.<br>
            2. Upload a room photo.<br>
            3. Review possible hazards and answer simple questions.<br>
            4. Read your score, suggested fixes, and safety report.
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_home_id_status(key_suffix="landing", allow_logout=True)

    if st.button("Start Safety Check", type="primary"):
        reset_current_room_check()
        st.session_state["quick_mode"] = False
        go_to_page("room_selection")

    if get_logged_in_home_id() and st.button("My Saved Room Checks"):
        go_to_page("saved_results")

    if st.button("View Room-by-Room Stats"):
        go_to_page("room_stats")


def show_room_selection_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 1: Choose a Room")
    if st.session_state.get("quick_mode"):
        show_step_card("Continue without signing in — Choose the room. No account or Room ID is needed unless you decide to save later.")
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

    tab1, tab2 = st.tabs(["Use Existing Room ID", "Create New Room ID"])

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
                go_to_page("risk_score" if st.session_state.get("ai_result") else "photo_upload")

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
                go_to_page("risk_score" if st.session_state.get("ai_result") else "photo_upload")

            except Exception as error:
                st.error("Could not create that Room ID.")
                with st.expander("Technical details"):
                    st.code(str(error))

    show_current_home_and_room_status()

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
    st.subheader("Checklist Summary")

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
        st.write(f"Checklist answers saved: {len(checklist_answers)}")

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

    show_score_explanation_card(score_breakdown)

    if st.button("View Risk Score →", type="primary"):
        go_to_page("risk_score")


def show_top_5_fixes(limit: int = 5) -> List[Dict[str, Any]]:
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    fixes = get_recommended_first_fixes(
        ai_hazards=hazards,
        checklist_answers=checklist_answers,
        limit=limit,
    )

    st.subheader(f"Top {limit} Fixes")

    if not fixes:
        st.info("No specific fixes were generated.")
        return []

    for fix in fixes:
        impact_points = max(0, int(fix.get("points", 0) or 0))
        lower_impact = max(1, round(impact_points * 0.5)) if impact_points else 0
        help_note = " Ask someone for help with this installation or repair." if fix.get("category") in {"handrail", "bathroom_grab_bars", "stairs", "uneven_floor"} else ""
        st.markdown(
            f"""
            <div class="plain-card">
                <strong>{fix.get("rank")}. [{safe_text(fix.get("priority"))}]</strong><br>
                {safe_text(fix.get("text"))}<br>
                <span class="small-muted">Potential score impact: about {lower_impact}–{impact_points} points if this concern is confirmed and resolved. Helps make walking areas safer and clearer.{safe_text(help_note)}</span><br>
                <span class="small-muted">Source: {safe_text(fix.get("source"))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    show_read_aloud_button(build_top_fixes_text(fixes), "top_fixes")
    return fixes


def show_current_check_comparison() -> None:
    """Compares a recheck to the latest saved result for the same Room ID."""
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
    st.caption("This compares the current photo with the latest saved check for this same Room ID.")

    for heading, items, display in [
        ("Hazards resolved", resolved, st.success),
        ("Still needing attention", still_present, st.warning),
        ("New hazards detected", new, st.error),
    ]:
        st.write(f"**{heading}:** " + (", ".join(items) if items else "None"))


def show_risk_score_page() -> None:
    st.title("AI SafeHome")
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
    show_risk_score_bar(score)

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

    if st.button("Create Safety Report →", type="primary"):
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

    if st.button("View Room-by-Room Stats"):
        go_to_page("room_stats")


def show_safety_report_page() -> None:
    st.title("AI SafeHome")
    st.subheader("Step 6: Safety Report")

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
                    Room ID: {safe_text(row.get("room_id") or "No Room ID")}<br>
                    Score: {safe_text(row.get("score"))}/100<br>
                    Risk Label: {safe_text(row.get("risk_level"))}<br>
                    Checked: {safe_text(format_database_datetime(row.get("created_at")))}
                </div>
                """,
                unsafe_allow_html=True,
            )

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
            "Save at least two checks for this same Room ID to compare before and after results."
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
        st.info("Save at least two checks for this same Room ID to see a score trend.")
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
                "Room ID": room.get("room_id"),
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
