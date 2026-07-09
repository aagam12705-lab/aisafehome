import streamlit as st
from PIL import Image, UnidentifiedImageError
from src.scoring import calculate_score, get_risk_level, get_score_breakdown
from src.ai_analysis import analyze_photo
from src.report import generate_report
from src.checklist import CHECKLIST_QUESTIONS, ANSWER_OPTIONS, ANSWER_VALUE_MAP
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

TEXT_SIZE_OPTIONS = {
    "Normal": 17,
    "Large": 20,
    "Extra Large": 23,
}

COLOR_SCHEME_OPTIONS = [
    "System",
    "Light",
    "Dark",
    "High Contrast",
]

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
GENERIC_RECOMMENDATIONS = {
    "loose_rug": "Add non-slip backing, tape down rug edges, or remove the rug from the walking path.",
    "cords": "Move cords along the wall or secure them with a cord cover.",
    "clutter": "Clear shoes, bags, boxes, and small objects from the floor.",
    "poor_lighting": "Add brighter lighting or night lights near walking paths.",
    "slippery_floor": "Keep the floor dry and use non-slip mats where needed.",
    "narrow_pathway": "Move furniture or objects to create a wider walking path.",
    "stairs": "Keep stairs clear, improve lighting, and make step edges easy to see.",
    "handrail": "Check that handrails are secure, easy to grip, and available where needed.",
    "bathroom_grab_bars": "Consider properly installed grab bars near the toilet, shower, or bathtub.",
    "hard_to_reach_items": "Move commonly used items to easy-to-reach shelves or counters.",
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

    if "checklist_answers" not in st.session_state:
        st.session_state["checklist_answers"] = []

    if "score" not in st.session_state:
        st.session_state["score"] = None

    if "risk_level" not in st.session_state:
        st.session_state["risk_level"] = None

    if "score_breakdown" not in st.session_state:
        st.session_state["score_breakdown"] = None  

    if "report_text" not in st.session_state:
        st.session_state["report_text"] = None  

    if "text_size" not in st.session_state:
        st.session_state["text_size"] = "Normal"

    if "color_scheme" not in st.session_state:
        st.session_state["color_scheme"] = "System"

    if "show_accessibility_panel" not in st.session_state:
        st.session_state["show_accessibility_panel"] = False   

def add_mobile_friendly_style():
    """
    Adds CSS for:
    - iPhone-friendly layout
    - large tap targets
    - accessibility text size
    - system/light/dark/high-contrast color schemes
    """

    text_size_name = st.session_state.get("text_size", "Normal")
    color_scheme_name = st.session_state.get("color_scheme", "System")

    base_font_size = TEXT_SIZE_OPTIONS.get(text_size_name, 17)

    if color_scheme_name == "Light":
        theme_variables = """
        --safehome-app-bg: #ffffff;
        --safehome-card-bg: #f9fafb;
        --safehome-card-alt: #ffffff;
        --safehome-text: #111827;
        --safehome-muted: #4b5563;
        --safehome-border: #d1d5db;
        --safehome-pill-bg: #e5e7eb;
        --safehome-primary: #2563eb;
        """
        system_dark_css = ""

    elif color_scheme_name == "Dark":
        theme_variables = """
        --safehome-app-bg: #111827;
        --safehome-card-bg: #1f2937;
        --safehome-card-alt: #374151;
        --safehome-text: #f9fafb;
        --safehome-muted: #d1d5db;
        --safehome-border: #6b7280;
        --safehome-pill-bg: #4b5563;
        --safehome-primary: #60a5fa;
        """
        system_dark_css = ""

    elif color_scheme_name == "High Contrast":
        theme_variables = """
        --safehome-app-bg: #000000;
        --safehome-card-bg: #000000;
        --safehome-card-alt: #111111;
        --safehome-text: #ffffff;
        --safehome-muted: #ffffff;
        --safehome-border: #ffffff;
        --safehome-pill-bg: #ffffff;
        --safehome-primary: #ffff00;
        """
        system_dark_css = ""

    else:
        # System default starts light, then switches to dark if device/browser prefers dark.
        theme_variables = """
        --safehome-app-bg: #ffffff;
        --safehome-card-bg: #f9fafb;
        --safehome-card-alt: #ffffff;
        --safehome-text: #111827;
        --safehome-muted: #4b5563;
        --safehome-border: #d1d5db;
        --safehome-pill-bg: #e5e7eb;
        --safehome-primary: #2563eb;
        """
        system_dark_css = """
        @media (prefers-color-scheme: dark) {
            :root {
                --safehome-app-bg: #111827;
                --safehome-card-bg: #1f2937;
                --safehome-card-alt: #374151;
                --safehome-text: #f9fafb;
                --safehome-muted: #d1d5db;
                --safehome-border: #6b7280;
                --safehome-pill-bg: #4b5563;
                --safehome-primary: #60a5fa;
            }
        }
        """

    st.markdown(
        f"""
        <style>
        :root {{
            {theme_variables}
        }}

        {system_dark_css}

        html, body, [class*="css"] {{
            font-size: {base_font_size}px;
            color: var(--safehome-text);
            background-color: var(--safehome-app-bg);
        }}

        .stApp {{
            background-color: var(--safehome-app-bg);
            color: var(--safehome-text);
        }}

        .block-container {{
            max-width: 560px;
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            padding-bottom: 2rem;
            color: var(--safehome-text);
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--safehome-text) !important;
        }}

        h1 {{
            font-size: 2rem !important;
            line-height: 1.15 !important;
            margin-bottom: 0.5rem !important;
        }}

        h2, h3 {{
            line-height: 1.25 !important;
        }}

        p, li, span, div {{
            line-height: 1.45;
        }}

        .stMarkdown,
        .stMarkdown p,
        .stMarkdown li {{
            color: var(--safehome-text);
        }}

        .stButton > button,
        .stDownloadButton > button {{
            width: 100%;
            min-height: 58px;
            font-size: {base_font_size + 1}px;
            font-weight: 800;
            border-radius: 14px;
            margin-top: 0.25rem;
            margin-bottom: 0.25rem;
        }}

        .big-tagline {{
            font-size: 1.35rem;
            font-weight: 800;
            line-height: 1.35;
            margin-bottom: 1rem;
            color: var(--safehome-text);
        }}

        .plain-card,
        .step-card,
        .checklist-card,
        .print-step-card {{
            border: 1px solid var(--safehome-border);
            border-radius: 16px;
            padding: 1rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
            background-color: var(--safehome-card-bg);
            color: var(--safehome-text);
            line-height: 1.45;
        }}

        .hazard-card {{
            border: 1px solid var(--safehome-border);
            border-radius: 16px;
            padding: 1rem;
            margin-top: 0.9rem;
            margin-bottom: 0.9rem;
            background-color: var(--safehome-card-alt);
            color: var(--safehome-text);
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
        }}

        .hazard-number {{
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--safehome-muted);
            margin-bottom: 0.3rem;
        }}

        .hazard-title {{
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 0.4rem;
            color: var(--safehome-text);
        }}

        .hazard-category {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.25rem 0.65rem;
            margin-bottom: 0.75rem;
            background-color: var(--safehome-pill-bg);
            color: var(--safehome-text);
            font-size: 0.85rem;
            font-weight: 700;
            border: 1px solid var(--safehome-border);
        }}

        .hazard-section-label {{
            font-weight: 800;
            margin-top: 0.6rem;
            margin-bottom: 0.15rem;
            color: var(--safehome-text);
        }}

        .hazard-text {{
            margin-top: 0;
            margin-bottom: 0.5rem;
            line-height: 1.45;
            color: var(--safehome-text);
        }}

        div[role="radiogroup"] label {{
            border: 1px solid var(--safehome-border);
            border-radius: 12px;
            padding: 0.9rem;
            margin-bottom: 0.5rem;
            background-color: var(--safehome-card-bg);
            color: var(--safehome-text);
            min-height: 48px;
        }}

        div[role="radiogroup"] label p {{
            color: var(--safehome-text) !important;
            font-size: {base_font_size}px;
        }}

        div[data-testid="stFileUploader"] {{
            border: 1px dashed var(--safehome-border);
            border-radius: 16px;
            padding: 0.75rem;
            background-color: var(--safehome-card-bg);
            color: var(--safehome-text);
        }}

        div[data-testid="stFileUploader"] * {{
            color: var(--safehome-text);
        }}

        .small-muted {{
            font-size: 0.95rem;
            color: var(--safehome-muted);
            line-height: 1.4;
        }}

        .print-report {{
            border: 1px solid var(--safehome-border);
            border-radius: 14px;
            padding: 1rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
            background-color: var(--safehome-card-alt);
            color: var(--safehome-text);
            white-space: pre-wrap;
            line-height: 1.45;
            font-family: Arial, sans-serif;
            font-size: 0.95rem;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }}

        textarea, input {{
            font-size: {base_font_size}px !important;
            color: var(--safehome-text) !important;
            background-color: var(--safehome-card-alt) !important;
        }}

        img {{
            border-radius: 12px;
        }}

        div[data-testid="stAlert"],
        div[data-testid="stAlert"] *,
        div[data-testid="stMetric"],
        div[data-testid="stMetric"] * {{
            color: var(--safehome-text);
        }}

        details {{
            color: var(--safehome-text);
            background-color: var(--safehome-card-alt);
            border-radius: 12px;
        }}

        details summary {{
            color: var(--safehome-text);
            font-weight: 700;
        }}

        @media screen and (max-width: 480px) {{
            .block-container {{
                padding-left: 0.85rem;
                padding-right: 0.85rem;
                padding-top: 0.75rem;
            }}

            h1 {{
                font-size: 1.8rem !important;
            }}

            .big-tagline {{
                font-size: 1.2rem;
            }}

            .plain-card,
            .hazard-card,
            .checklist-card,
            .print-step-card,
            .print-report,
            .step-card {{
                padding: 0.9rem;
                border-radius: 14px;
            }}

            .stButton > button,
            .stDownloadButton > button {{
                min-height: 60px;
                font-size: {base_font_size + 1}px;
            }}
        }}

        @media print {{
            header, footer, [data-testid="stToolbar"], [data-testid="stSidebar"] {{
                display: none !important;
            }}

            .stButton, .stDownloadButton {{
                display: none !important;
            }}

            .block-container {{
                max-width: 100%;
                padding: 1rem;
            }}

            .print-report {{
                border: none;
                font-size: 12pt;
                color: #000000;
                background-color: #ffffff;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def go_to_page(page_name):
    st.session_state["page"] = page_name
    st.rerun()

def show_accessibility_panel():
    """
    Shows a small accessibility icon button.
    Clicking it opens or closes the accessibility settings panel.
    """

    left_col, right_col = st.columns([5, 1])

    with right_col:
        if st.button("♿", help="Accessibility settings"):
            st.session_state["show_accessibility_panel"] = not st.session_state[
                "show_accessibility_panel"
            ]
            st.rerun()

    if st.session_state["show_accessibility_panel"]:
        with st.container():
            st.markdown(
                """
                <div class="plain-card">
                    <strong>Accessibility Settings</strong><br>
                    Adjust text size and color scheme.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.radio(
                "Text size",
                list(TEXT_SIZE_OPTIONS.keys()),
                key="text_size",
            )

            st.radio(
                "Color scheme",
                COLOR_SCHEME_OPTIONS,
                key="color_scheme",
            )

            st.caption(
                "System follows your device’s light or dark mode setting."
            )

def show_step_card(step_text):
    """
    Shows a simple mobile-friendly step label near the top of a page.
    """

    st.markdown(
        f"""
        <div class="step-card">
            {step_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    return CATEGORY_LABELS.get(category, "Possible Hazard")


def render_hazard_card(hazard, number):
    """
    Displays one hazard as a clean card without raw HTML.
    This avoids Streamlit showing HTML code on the screen.
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

    with st.container(border=True):
        st.caption(f"Hazard {number}")
        st.subheader(title)
        st.write(f"**Category:** {category_label}")
        st.write("**Why it matters:**")
        st.write(explanation)
        st.write("**Suggested fix:**")
        st.write(recommendation)


def render_hazard_summary(hazards):
    hazard_count = len(hazards)

    if hazard_count == 0:
        st.success("No obvious hazards were found in this sample result.")
    elif hazard_count == 1:
        st.warning("1 possible hazard found.")
    else:
        st.warning(f"{hazard_count} possible hazards found.")

def get_checklist_concerns(checklist_answers):
    """
    Returns checklist answers that add points to the score.
    """

    concerns = []

    for answer in checklist_answers:
        if answer.get("answer") in ["yes", "not_sure"]:
            concerns.append(answer)

    return concerns


def get_recommended_first_fixes(ai_hazards, checklist_answers):
    """
    Creates a short list of recommended first fixes.
    Uses AI recommendations first, then checklist-based generic fixes.
    """

    fixes = []
    seen_fixes = set()

    for hazard in ai_hazards:
        recommendation = hazard.get("recommendation")

        if recommendation and recommendation not in seen_fixes:
            fixes.append(recommendation)
            seen_fixes.add(recommendation)

    for answer in checklist_answers:
        if answer.get("answer") in ["yes", "not_sure"]:
            category = answer.get("category")
            recommendation = GENERIC_RECOMMENDATIONS.get(category)

            if recommendation and recommendation not in seen_fixes:
                fixes.append(recommendation)
                seen_fixes.add(recommendation)

    return fixes[:5]  
          
def get_report_file_name(room_type):
    """
    Creates a simple safe file name for the downloaded report.
    """

    if not room_type:
        room_type = "room"

    safe_room_name = room_type.lower().replace(" ", "_")
    return f"ai_safehome_{safe_room_name}_safety_report.txt"

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
    show_step_card("Step 1 of 6 — Choose the room you want to check.")
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
    show_step_card("Step 2 of 6 — Upload or take a staged room photo.")
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
    show_step_card("Step 3 of 6 — Review possible hazards found by the sample AI.")
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
        go_to_page("checklist")

    if st.button("Analyze Another Photo"):
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        go_to_page("photo_upload")

    if st.button("Start Over"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        go_to_page("landing")


def show_checklist_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Step 4: Safety Checklist")
    show_step_card("Step 4 of 6 — Answer checklist questions to add human review.")
    room_type = st.session_state.get("room_type")
    ai_result = st.session_state.get("ai_result")

    if not room_type:
        st.error("No room was selected. Please start again.")
        if st.button("Start Over"):
            go_to_page("landing")
        return

    if not ai_result:
        st.error("No AI result found. Please upload and analyze a photo first.")
        if st.button("Go to Photo Upload"):
            go_to_page("photo_upload")
        return

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Room checked:</strong> {room_type}<br>
            Answer these questions based on what you can see in the room.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Use the checklist to catch hazards the photo analysis may miss. "
        "Choose 'Not sure' if you cannot tell."
    )

    checklist_answers = []

    with st.form("safety_checklist_form"):
        for question_number, question in enumerate(CHECKLIST_QUESTIONS, start=1):
            st.markdown(
                f"""
                <div class="checklist-card">
                    <strong>Question {question_number}</strong><br>
                    {question["text"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

            selected_answer_label = st.radio(
                "Choose an answer",
                ANSWER_OPTIONS,
                index=0,
                key=f"checklist_{question['id']}",
                label_visibility="collapsed",
            )

            checklist_answers.append(
                {
                    "id": question["id"],
                    "category": question["category"],
                    "question": question["text"],
                    "answer": ANSWER_VALUE_MAP[selected_answer_label],
                    "answer_label": selected_answer_label,
                }
            )

        submitted = st.form_submit_button("Save Checklist", type="primary")

    if submitted:
        st.session_state["checklist_answers"] = checklist_answers
        go_to_page("checklist_summary")

    if st.button("← Back to Hazard Results"):
        go_to_page("ai_results")


def show_checklist_summary_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Checklist Saved")

    checklist_answers = st.session_state.get("checklist_answers", [])

    if not checklist_answers:
        st.error("No checklist answers were saved.")
        if st.button("Return to Checklist"):
            go_to_page("checklist")
        return

    yes_count = 0
    not_sure_count = 0

    for answer in checklist_answers:
        if answer["answer"] == "yes":
            yes_count += 1
        elif answer["answer"] == "not_sure":
            not_sure_count += 1

    st.success("Your checklist answers were saved.")

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Checklist concerns marked Yes:</strong> {yes_count}<br>
            <strong>Checklist items marked Not sure:</strong> {not_sure_count}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("Checklist answers:")

    for answer in checklist_answers:
        st.write(f"- **{answer['question']}** — {answer['answer_label']}")

    if st.button("Calculate Risk Score →", type="primary"):
        ai_result = st.session_state.get("ai_result") or {}
        hazards = ai_result.get("hazards", [])

        score = calculate_score(hazards, checklist_answers)
        risk_level = get_risk_level(score)
        score_breakdown = get_score_breakdown(hazards, checklist_answers)

        st.session_state["score"] = score
        st.session_state["risk_level"] = risk_level
        st.session_state["score_breakdown"] = score_breakdown

        go_to_page("risk_score")

    if st.button("Edit Checklist"):
        go_to_page("checklist")

    if st.button("Start Over"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        st.session_state["score"] = None
        st.session_state["risk_level"] = None
        st.session_state["score_breakdown"] = None
        go_to_page("landing")

def show_risk_score_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Step 5: Fall-Hazard Score")
    show_step_card("Step 5 of 6 — Review the score, risk label, and first fixes.")
    score = st.session_state.get("score")
    risk_level = st.session_state.get("risk_level")
    score_breakdown = st.session_state.get("score_breakdown")

    ai_result = st.session_state.get("ai_result") or {}
    ai_hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    if score is None or risk_level is None:
        st.error("No score was calculated yet.")
        if st.button("Return to Checklist"):
            go_to_page("checklist")
        return

    st.metric("Risk Score", f"{score}/100")

    st.progress(score)

    if risk_level == "Low Risk":
        st.success(f"{risk_level} — Few concerns were found in this demo check.")
    elif risk_level == "Moderate Risk":
        st.warning(f"{risk_level} — Some concerns should be reviewed and fixed.")
    else:
        st.error(f"{risk_level} — Several concerns should be reviewed carefully.")

    st.caption(
        "This is an educational home-safety hazard score. "
        "It is not a medical diagnosis and does not guarantee fall prevention."
    )

    st.subheader("Top Concerns")

    checklist_concerns = get_checklist_concerns(checklist_answers)

    top_concerns = []

    for hazard in ai_hazards:
        top_concerns.append(hazard.get("title", "Possible hazard"))

    for answer in checklist_concerns:
        category_label = get_category_label(answer.get("category"))
        answer_label = answer.get("answer_label", "Concern")
        top_concerns.append(f"{category_label} — {answer_label}")

    if not top_concerns:
        st.write("No major concerns were marked.")
    else:
        for index, concern in enumerate(top_concerns[:5], start=1):
            st.write(f"{index}. {concern}")

    st.subheader("Recommended First Fixes")

    fixes = get_recommended_first_fixes(ai_hazards, checklist_answers)

    if not fixes:
        st.write("No specific fixes were generated.")
    else:
        for index, fix in enumerate(fixes, start=1):
            st.write(f"{index}. {fix}")

    with st.expander("View score breakdown"):
        if score_breakdown:
            st.write(f"AI hazard points: **{score_breakdown['ai_points']}**")
            st.write(f"Checklist points: **{score_breakdown['checklist_points']}**")
            st.write(f"Total before 100-point cap: **{score_breakdown['total_before_cap']}**")
            st.write(f"Final score: **{score_breakdown['final_score']}/100**")

            st.write("AI items that added points:")
            if score_breakdown["ai_items"]:
                for item in score_breakdown["ai_items"]:
                    label = get_category_label(item["category"])
                    st.write(f"- {item['title']} — {label}: +{item['points']}")
            else:
                st.write("- None")

            st.write("Checklist items that added points:")
            if score_breakdown["checklist_items"]:
                for item in score_breakdown["checklist_items"]:
                    label = get_category_label(item["category"])
                    st.write(
                        f"- {label} — {item['answer_label']}: +{item['points']}"
                    )
            else:
                st.write("- None")

    st.warning(
        "AI may miss hazards. Please review the room yourself and consider asking "
        "a qualified professional for serious safety concerns."
    )

    if st.button("Create Safety Report →", type="primary"):
        report_text = generate_report(
            room_type=st.session_state.get("room_type"),
            hazards=ai_hazards,
            checklist_answers=checklist_answers,
            score=score,
            risk_level=risk_level,
            recommended_fixes=fixes,
            safety_disclaimer=SAFETY_DISCLAIMER,
        )

        st.session_state["report_text"] = report_text
        go_to_page("safety_report")

    if st.button("Edit Checklist"):
        go_to_page("checklist")

    if st.button("Start Over"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        st.session_state["score"] = None
        st.session_state["risk_level"] = None
        st.session_state["score_breakdown"] = None
        go_to_page("landing")        

def show_safety_report_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Step 6: Safety Report")
    show_step_card("Step 6 of 6 — Review, download, print, or save the report.")
    report_text = st.session_state.get("report_text")
    room_type = st.session_state.get("room_type")
    score = st.session_state.get("score")
    risk_level = st.session_state.get("risk_level")

    if not report_text:
        st.error("No safety report was created yet.")
        if st.button("Return to Risk Score"):
            go_to_page("risk_score")
        return

    st.success("Safety report created.")

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Room:</strong> {room_type}<br>
            <strong>Score:</strong> {score}/100<br>
            <strong>Risk Level:</strong> {risk_level}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(
        "This report is educational. It is not a medical diagnosis and does not guarantee fall prevention."
    )

    st.subheader("Report Preview")

    st.markdown(
        f"""
        <div class="print-report">
        {report_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        label="Download Report as Text File",
        data=report_text,
        file_name=get_report_file_name(room_type),
        mime="text/plain",
        type="primary",
    )

    st.subheader("Print or Save Instructions")

    st.markdown(
        """
        <div class="print-step-card">
            <strong>On Mac or Windows:</strong><br>
            1. Press <strong>Command + P</strong> on Mac or <strong>Ctrl + P</strong> on Windows.<br>
            2. Choose your printer, or choose <strong>Save as PDF</strong>.<br>
            3. Print or save the report.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="print-step-card">
            <strong>On iPhone Safari:</strong><br>
            1. Tap the <strong>Share</strong> button.<br>
            2. Choose <strong>Print</strong>.<br>
            3. Use the print preview options to save or share the report as a PDF.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "AI SafeHome does not save this report to a database. If you want to keep it, download, print, or save it yourself."
    )

    st.caption(
        "Privacy reminder: use staged, non-patient photos only. Do not upload faces, names, addresses, mail, bills, medication bottles, or medical documents."
    )

    if st.button("Back to Risk Score"):
        go_to_page("risk_score")

    if st.button("Start Another Room"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        st.session_state["score"] = None
        st.session_state["risk_level"] = None
        st.session_state["score_breakdown"] = None
        st.session_state["report_text"] = None
        go_to_page("room_selection")

    if st.button("Start Over"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        st.session_state["score"] = None
        st.session_state["risk_level"] = None
        st.session_state["score_breakdown"] = None
        st.session_state["report_text"] = None
        go_to_page("landing")

def main():
    setup_page()
    initialize_session_state()
    add_mobile_friendly_style()
    show_accessibility_panel()

    current_page = st.session_state["page"]

    if current_page == "landing":
        show_landing_page()
    elif current_page == "room_selection":
        show_room_selection_page()
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
    else:
        st.error("Unknown page. Returning to landing page.")
        st.session_state["page"] = "landing"
        st.rerun()


main()