import streamlit as st
from PIL import Image, UnidentifiedImageError

from src.ai_analysis import analyze_photo
from src.safety_text import (
    APP_NAME,
    TAGLINE,
    LANDING_EXPLANATION,
    SAFETY_DISCLAIMER,
    PRIVACY_REMINDER,
    PHOTO_UPLOAD_PRIVACY_WARNING,
    PHOTO_NOT_STORED_NOTE,
)


ROOM_OPTIONS = [
    "Living Room",
    "Bedroom",
    "Bathroom",
    "Kitchen",
    "Hallway",
    "Stairs",
    "Other",
]

ALLOWED_FILE_TYPES = ["jpg", "jpeg", "png", "webp"]
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


CATEGORY_LABELS = {
    "loose_rug": "Loose Rug or Mat",
    "cords": "Cord Hazard",
    "clutter": "Floor Clutter",
    "poor_lighting": "Poor Lighting",
    "slippery_floor": "Slippery or Wet Floor",
    "narrow_pathway": "Narrow or Blocked Pathway",
    "stairs": "Stairs or Step Hazard",
    "handrail": "Handrail Concern",
    "bathroom_grab_bars": "Bathroom Grab Bar Concern",
    "hard_to_reach_items": "Hard-to-Reach Items",
    "unclear": "Unclear Hazard",
}


def setup_page():
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🏠",
        layout="centered",
    )


def initialize_session_state():
    if "page" not in st.session_state:
        st.session_state["page"] = "landing"

    if "room_type" not in st.session_state:
        st.session_state["room_type"] = None

    if "photo_uploaded" not in st.session_state:
        st.session_state["photo_uploaded"] = False

    if "ai_result" not in st.session_state:
        st.session_state["ai_result"] = None


def add_mobile_friendly_style():
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 560px;
            padding-top: 1.2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .stButton > button {
            width: 100%;
            min-height: 52px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 12px;
        }

        .big-tagline {
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1.35;
            margin-bottom: 1rem;
        }

        .plain-card {
            border: 1px solid #ddd;
            border-radius: 14px;
            padding: 1rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
            background-color: #fafafa;
        }

        .hazard-card {
            border: 1px solid #d9d9d9;
            border-radius: 16px;
            padding: 1rem;
            margin-top: 0.9rem;
            margin-bottom: 0.9rem;
            background-color: #ffffff;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
        }

        .hazard-number {
            font-size: 0.9rem;
            font-weight: 700;
            color: #555;
            margin-bottom: 0.3rem;
        }

        .hazard-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 0.4rem;
        }

        .hazard-category {
            display: inline-block;
            border-radius: 999px;
            padding: 0.25rem 0.65rem;
            margin-bottom: 0.75rem;
            background-color: #f1f1f1;
            font-size: 0.85rem;
            font-weight: 700;
            color: #333;
        }

        .hazard-section-label {
            font-weight: 800;
            margin-top: 0.6rem;
            margin-bottom: 0.15rem;
        }

        .hazard-text {
            margin-top: 0;
            margin-bottom: 0.5rem;
            line-height: 1.45;
        }

        div[role="radiogroup"] label {
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 0.75rem;
            margin-bottom: 0.4rem;
            background-color: #fafafa;
        }

        .small-muted {
            font-size: 0.9rem;
            color: #555;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def go_to_page(page_name):
    st.session_state["page"] = page_name
    st.rerun()


def validate_uploaded_photo(uploaded_file):
    if uploaded_file is None:
        return False, "No photo was uploaded."

    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        return (
            False,
            f"The photo is too large. Please upload a file smaller than {MAX_FILE_SIZE_MB} MB.",
        )

    try:
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
    except UnidentifiedImageError:
        return False, "This file does not look like a valid image."
    except Exception:
        return False, "Something went wrong while reading the image."

    return True, ""


def get_category_label(category):
    """
    Converts an internal category like 'loose_rug'
    into a readable label like 'Loose Rug or Mat'.
    """
    return CATEGORY_LABELS.get(category, "Possible Hazard")


def render_hazard_card(hazard, number):
    """
    Displays one hazard as a clean mobile-friendly card.

    The .get() method prevents the app from crashing if a field is missing.
    This will matter later when real AI returns JSON.
    """

    title = hazard.get("title", "Possible hazard")
    category = hazard.get("category", "unclear")
    category_label = get_category_label(category)

    explanation = hazard.get(
        "explanation",
        "This item may need review because the app could not fully explain the concern.",
    )

    recommendation = hazard.get(
        "recommendation",
        "Review this area carefully and consider asking a qualified professional.",
    )

    st.markdown(
        f"""
        <div class="hazard-card">
            <div class="hazard-number">Hazard {number}</div>
            <div class="hazard-title">{title}</div>
            <div class="hazard-category">{category_label}</div>

            <div class="hazard-section-label">Why it matters</div>
            <p class="hazard-text">{explanation}</p>

            <div class="hazard-section-label">Suggested fix</div>
            <p class="hazard-text">{recommendation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hazard_summary(hazards):
    """
    Displays a short summary count before the cards.
    """

    hazard_count = len(hazards)

    if hazard_count == 0:
        st.success("No obvious hazards were found in this sample result.")
    elif hazard_count == 1:
        st.warning("1 possible hazard found.")
    else:
        st.warning(f"{hazard_count} possible hazards found.")


def show_landing_page():
    st.title("🏠 AI SafeHome")

    st.markdown(
        f"<div class='big-tagline'>{TAGLINE}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="plain-card">
            {LANDING_EXPLANATION}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(SAFETY_DISCLAIMER)
    st.info(PRIVACY_REMINDER)

    if st.button("Start Safety Check", type="primary"):
        go_to_page("room_selection")

    st.caption(
        "Version 1 uses staged, non-patient photos only. "
        "No login. No database. No stored photos."
    )


def show_room_selection_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Step 1: Choose a Room")

    st.write("Which room are you checking today?")

    selected_room = st.radio(
        "Room type",
        ROOM_OPTIONS,
        index=0,
        label_visibility="collapsed",
    )

    st.session_state["room_type"] = selected_room

    st.info(
        "Choose the room that best matches the photo you will upload in the next step."
    )

    if st.button("Continue →", type="primary"):
        go_to_page("photo_upload")

    if st.button("← Back"):
        go_to_page("landing")


def show_photo_upload_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Step 2: Upload Room Photo")

    room_type = st.session_state.get("room_type")

    if not room_type:
        st.error("No room was selected. Please choose a room first.")
        if st.button("Choose Room"):
            go_to_page("room_selection")
        return

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Selected room:</strong> {room_type}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(PHOTO_UPLOAD_PRIVACY_WARNING)
    st.info(PHOTO_NOT_STORED_NOTE)

    uploaded_file = st.file_uploader(
        "Upload or take a room photo",
        type=ALLOWED_FILE_TYPES,
        help="On iPhone, this may let you choose Photo Library or Take Photo.",
    )

    if uploaded_file is not None:
        is_valid, error_message = validate_uploaded_photo(uploaded_file)

        if not is_valid:
            st.error(error_message)
            st.session_state["photo_uploaded"] = False
            return

        st.session_state["photo_uploaded"] = True

        st.subheader("Photo Preview")

        image = Image.open(uploaded_file)
        st.image(
            image,
            caption=f"Preview of uploaded {room_type} photo",
            use_container_width=True,
        )

        st.success("Photo uploaded successfully.")

        st.markdown(
            """
            <p class="small-muted">
            This preview confirms the app can read the image. 
            The next button will show fake AI-style hazard results.
            </p>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Analyze Photo →", type="primary"):
            with st.spinner("Analyzing photo..."):
                ai_result = analyze_photo(uploaded_file, room_type)
                st.session_state["ai_result"] = ai_result
            go_to_page("ai_results")

    else:
        st.session_state["photo_uploaded"] = False
        st.info("Upload a JPG, JPEG, PNG, or WEBP photo smaller than 5 MB.")

    if st.button("← Back to Room Selection"):
        go_to_page("room_selection")


def show_ai_results_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Step 3: Possible Hazards Found")

    ai_result = st.session_state.get("ai_result")
    room_type = st.session_state.get("room_type")

    if not ai_result:
        st.error("No analysis result found. Please upload a photo first.")
        if st.button("Go to Photo Upload"):
            go_to_page("photo_upload")
        return

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Room checked:</strong> {room_type}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(ai_result.get("summary", "Sample AI-style hazard results are shown below."))

    hazards = ai_result.get("hazards", [])

    render_hazard_summary(hazards)

    for index, hazard in enumerate(hazards, start=1):
        render_hazard_card(hazard, index)

    with st.expander("What the photo may not show"):
        not_visible_items = ai_result.get("not_visible", [])

        if not_visible_items:
            for item in not_visible_items:
                st.write(f"- {item}")
        else:
            st.write("Some hazards may not be visible from one photo.")

    st.warning(
        ai_result.get(
            "safety_reminder",
            "AI may miss hazards. Human review is recommended.",
        )
    )

    st.caption(
        "Demo note: these are fake sample results. Real OpenAI vision analysis will be added later."
    )

    if st.button("Continue to Checklist →", type="primary"):
        st.success("Checklist will be added in Milestone 7.")

    if st.button("Analyze Another Photo"):
        st.session_state["ai_result"] = None
        go_to_page("photo_upload")

    if st.button("Start Over"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        go_to_page("landing")


def main():
    setup_page()
    initialize_session_state()
    add_mobile_friendly_style()

    current_page = st.session_state["page"]

    if current_page == "landing":
        show_landing_page()
    elif current_page == "room_selection":
        show_room_selection_page()
    elif current_page == "photo_upload":
        show_photo_upload_page()
    elif current_page == "ai_results":
        show_ai_results_page()
    else:
        st.error("Unknown page. Returning to landing page.")
        st.session_state["page"] = "landing"
        st.rerun()


main()