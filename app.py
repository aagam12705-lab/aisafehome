import html
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError
from src.scoring import (
    calculate_score,
    get_risk_level,
    get_score_breakdown,
)
from src.database import (
    fetch_recent_room_checks,
    fetch_summary_stats,
    get_database_status_message,
    is_database_enabled,
    save_room_check,
)
from src.multi_room import build_home_summary, get_home_priority_label
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
    AI_USE_DISCLOSURE,
    FINAL_PRIVACY_SUMMARY, 
)
from src.priorities import (
    get_priority_css_class,
    get_priority_for_checklist_answer,
    get_priority_for_hazard,
    sort_by_priority,
)

ROOM_OPTIONS = [
    "Living Room",
    "Bedroom",
    "Bathroom",
    "Kitchen",
    "Hallway",
    "Stairs",
    "Dining Room",
    "Laundry Room",
    "Garage",
    "Entryway / Foyer",
    "Basement",
    "Outdoor Walkway / Porch",
    "Closet / Storage Area",
    "Home Office",
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

    # New expanded labels
    "threshold_trip": "Raised Threshold or Floor Transition",
    "unstable_furniture": "Unstable Furniture",
    "pet_items": "Pet Items in Walking Path",
    "footwear": "Shoes or Footwear in Walking Path",
    "low_seating": "Low or Unsafe Seating",
    "poor_contrast": "Poor Contrast / Hard-to-See Edges",
    "uneven_floor": "Uneven Floor Surface",
    "door_mat": "Loose Door Mat",
    "furniture_in_path": "Furniture Blocking Walking Path",
    "outdoor_surface": "Outdoor Surface Hazard",
    "laundry_on_floor": "Laundry on Floor",
    "open_drawers_cabinets": "Open Drawers or Cabinets",

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

    # New expanded recommendations
    "threshold_trip": "Make floor transitions easier to see and keep thresholds clear.",
    "unstable_furniture": "Secure or replace furniture that may slide, wobble, or be hard to use for support.",
    "pet_items": "Move pet bowls, toys, beds, and leashes away from walking paths.",
    "footwear": "Store shoes and slippers away from walkways.",
    "low_seating": "Use stable chairs that are easier to sit in and stand up from.",
    "poor_contrast": "Improve contrast on step edges, thresholds, or floor changes so they are easier to see.",
    "uneven_floor": "Repair or clearly mark uneven flooring, bumps, or lifted edges.",
    "door_mat": "Use a non-slip mat or remove loose mats from entry areas.",
    "furniture_in_path": "Move furniture so walking paths are open and easy to navigate.",
    "outdoor_surface": "Clear leaves, ice, water, loose mats, or uneven areas from outdoor walking surfaces.",
    "laundry_on_floor": "Keep laundry baskets and loose clothing away from the floor and walking paths.",
    "open_drawers_cabinets": "Keep drawers and cabinet doors closed when not in use.",
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
        st.session_state["score_adjustment"] = None
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

    if "room_results" not in st.session_state:
        st.session_state["room_results"] = []

    if "home_summary_text" not in st.session_state:
        st.session_state["home_summary_text"] = None

    if "current_check_saved" not in st.session_state:
        st.session_state["current_check_saved"] = False   

    if "checklist_index" not in st.session_state:
        st.session_state["checklist_index"] = 0

    if "checklist_answers_by_id" not in st.session_state:
        st.session_state["checklist_answers_by_id"] = {}

    if "checklist_was_skipped" not in st.session_state:
        st.session_state["checklist_was_skipped"] = False   
    if "database_save_complete" not in st.session_state:
        st.session_state["database_save_complete"] = False

    if "database_save_id" not in st.session_state:
        st.session_state["database_save_id"] = None
  


def add_mobile_friendly_style():
    """
    Accessibility-aware style system for AI SafeHome.

    Fixes the color-scheme problems by using one set of CSS variables for
    every card, button, radio button, alert, input, uploader, expander, and
    report area. This prevents black-on-black and white-on-white text.
    """

    text_size_name = st.session_state.get("text_size", "Normal")
    color_scheme_name = st.session_state.get("color_scheme", "System")

    base_font_size = TEXT_SIZE_OPTIONS.get(text_size_name, 17)

    light_vars = """
        --safehome-bg: #ffffff;
        --safehome-surface: #f8fafc;
        --safehome-card: #ffffff;
        --safehome-card-alt: #f9fafb;
        --safehome-text: #111827;
        --safehome-muted: #374151;
        --safehome-border: #9ca3af;
        --safehome-soft-border: #d1d5db;

        --safehome-primary-bg: #2563eb;
        --safehome-primary-text: #ffffff;
        --safehome-button-bg: #ffffff;
        --safehome-button-text: #111827;
        --safehome-button-hover-bg: #f3f4f6;

        --safehome-input-bg: #ffffff;
        --safehome-input-text: #111827;
        --safehome-pill-bg: #e5e7eb;
        --safehome-pill-text: #111827;

        --safehome-alert-bg: #f8fafc;
        --safehome-alert-text: #111827;
        --safehome-alert-border: #64748b;

        --safehome-shadow: rgba(0, 0, 0, 0.08);
    """

    dark_vars = """
        --safehome-bg: #0b1220;
        --safehome-surface: #111827;
        --safehome-card: #1f2937;
        --safehome-card-alt: #273449;
        --safehome-text: #f9fafb;
        --safehome-muted: #e5e7eb;
        --safehome-border: #94a3b8;
        --safehome-soft-border: #64748b;

        --safehome-primary-bg: #93c5fd;
        --safehome-primary-text: #07111f;
        --safehome-button-bg: #111827;
        --safehome-button-text: #f9fafb;
        --safehome-button-hover-bg: #374151;

        --safehome-input-bg: #111827;
        --safehome-input-text: #f9fafb;
        --safehome-pill-bg: #334155;
        --safehome-pill-text: #f9fafb;

        --safehome-alert-bg: #111827;
        --safehome-alert-text: #f9fafb;
        --safehome-alert-border: #93c5fd;

        --safehome-shadow: rgba(0, 0, 0, 0.35);
    """

    high_contrast_vars = """
        --safehome-bg: #000000;
        --safehome-surface: #000000;
        --safehome-card: #000000;
        --safehome-card-alt: #000000;
        --safehome-text: #ffffff;
        --safehome-muted: #ffffff;
        --safehome-border: #ffffff;
        --safehome-soft-border: #ffffff;

        --safehome-primary-bg: #ffff00;
        --safehome-primary-text: #000000;
        --safehome-button-bg: #000000;
        --safehome-button-text: #ffffff;
        --safehome-button-hover-bg: #1a1a1a;

        --safehome-input-bg: #000000;
        --safehome-input-text: #ffffff;
        --safehome-pill-bg: #000000;
        --safehome-pill-text: #ffffff;

        --safehome-alert-bg: #000000;
        --safehome-alert-text: #ffffff;
        --safehome-alert-border: #ffff00;

        --safehome-shadow: rgba(255, 255, 255, 0.25);
    """

    if color_scheme_name == "Light":
        root_vars = light_vars
        system_dark_override = ""
        browser_color_scheme = "light"
    elif color_scheme_name == "Dark":
        root_vars = dark_vars
        system_dark_override = ""
        browser_color_scheme = "dark"
    elif color_scheme_name == "High Contrast":
        root_vars = high_contrast_vars
        system_dark_override = ""
        browser_color_scheme = "dark"
    else:
        root_vars = light_vars
        browser_color_scheme = "light dark"
        system_dark_override = f"""
        @media (prefers-color-scheme: dark) {{
            :root {{
                {dark_vars}
            }}
        }}
        """

    st.markdown(
        f"""
        <style>
        :root {{
            {root_vars}
            color-scheme: {browser_color_scheme};
        }}

        {system_dark_override}

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"] {{
            background-color: var(--safehome-bg) !important;
            color: var(--safehome-text) !important;
        }}

        html,
        body,
        .stApp {{
            font-size: {base_font_size}px !important;
        }}

        .block-container {{
            max-width: 560px !important;
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 2rem !important;
            color: var(--safehome-text) !important;
        }}

        /* Main readable text */
        h1, h2, h3, h4, h5, h6,
        p, li, span, div, label,
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] * {{
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

        p, li {{
            line-height: 1.45 !important;
        }}

        a, a * {{
            color: var(--safehome-primary-bg) !important;
        }}

        /* Custom app cards */
        .plain-card,
        .step-card,
        .checklist-card,
        .print-step-card,
        .hazard-card,
        .print-report {{
            border: 1px solid var(--safehome-border) !important;
            border-radius: 16px !important;
            padding: 1rem !important;
            margin-top: 1rem !important;
            margin-bottom: 1rem !important;
            background-color: var(--safehome-card) !important;
            color: var(--safehome-text) !important;
            line-height: 1.45 !important;
            overflow-wrap: break-word !important;
            word-wrap: break-word !important;
        }}

        .step-card,
        .checklist-card,
        .print-step-card {{
            background-color: var(--safehome-card-alt) !important;
        }}

        .print-report {{
            white-space: pre-wrap !important;
            font-family: Arial, sans-serif !important;
            font-size: 0.95rem !important;
        }}

        .big-tagline {{
            font-size: 1.35rem !important;
            font-weight: 800 !important;
            line-height: 1.35 !important;
            margin-bottom: 1rem !important;
            color: var(--safehome-text) !important;
        }}

        .small-muted,
        .stCaptionContainer,
        .stCaptionContainer * {{
            font-size: 0.95rem !important;
            color: var(--safehome-muted) !important;
            line-height: 1.4 !important;
        }}

        .accessibility-label {{
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            color: var(--safehome-text) !important;
            margin-top: 1rem !important;
            margin-bottom: 0.35rem !important;
        }}

        /* Streamlit containers, expanders, and bordered containers */
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stExpander"],
        details {{
            background-color: var(--safehome-card) !important;
            color: var(--safehome-text) !important;
            border-color: var(--safehome-border) !important;
            border-radius: 14px !important;
        }}

        [data-testid="stExpander"] *,
        details *,
        details summary {{
            color: var(--safehome-text) !important;
        }}

        /* Alerts: override Streamlit's pale alert backgrounds so dark/high-contrast text stays readable */
        div[data-testid="stAlert"] {{
            background-color: var(--safehome-alert-bg) !important;
            color: var(--safehome-alert-text) !important;
            border: 2px solid var(--safehome-alert-border) !important;
            border-radius: 14px !important;
        }}

        div[data-testid="stAlert"] * {{
            color: var(--safehome-alert-text) !important;
        }}

        /* Metrics */
        div[data-testid="stMetric"],
        div[data-testid="stMetric"] *,
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricLabel"] {{
            color: var(--safehome-text) !important;
        }}

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button,
        button[data-testid="baseButton-secondary"],
        button[data-testid="baseButton-primary"] {{
            width: 100% !important;
            min-height: 58px !important;
            font-size: {base_font_size + 1}px !important;
            font-weight: 800 !important;
            border-radius: 14px !important;
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
            background-color: var(--safehome-button-bg) !important;
            color: var(--safehome-button-text) !important;
            border: 2px solid var(--safehome-border) !important;
        }}

        .stButton > button *,
        .stDownloadButton > button *,
        button[data-testid="baseButton-secondary"] *,
        button[data-testid="baseButton-primary"] * {{
            color: inherit !important;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        button[data-testid="baseButton-secondary"]:hover,
        button[data-testid="baseButton-primary"]:hover {{
            background-color: var(--safehome-button-hover-bg) !important;
            border-color: var(--safehome-primary-bg) !important;
        }}

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {{
            background-color: var(--safehome-primary-bg) !important;
            color: var(--safehome-primary-text) !important;
            border: 2px solid var(--safehome-primary-bg) !important;
        }}

        .stButton > button[kind="primary"] *,
        .stDownloadButton > button[kind="primary"] *,
        button[data-testid="baseButton-primary"] * {{
            color: var(--safehome-primary-text) !important;
        }}

        /* Radio buttons and widget labels */
        div[data-testid="stWidgetLabel"],
        div[data-testid="stWidgetLabel"] *,
        div[data-testid="stRadio"],
        div[data-testid="stRadio"] *,
        div[data-baseweb="radio"],
        div[data-baseweb="radio"] *,
        label,
        label * {{
            color: var(--safehome-text) !important;
        }}

        div[data-testid="stRadio"] label {{
            border: 1px solid var(--safehome-border) !important;
            border-radius: 12px !important;
            padding: 0.9rem !important;
            margin-bottom: 0.5rem !important;
            background-color: var(--safehome-card) !important;
            color: var(--safehome-text) !important;
            min-height: 48px !important;
        }}

        div[data-testid="stRadio"] label:hover {{
            background-color: var(--safehome-card-alt) !important;
            border-color: var(--safehome-primary-bg) !important;
        }}

        div[data-testid="stRadio"] label p {{
            color: var(--safehome-text) !important;
            font-size: {base_font_size}px !important;
            font-weight: 650 !important;
        }}

        /* Inputs, text areas, uploader */
        textarea,
        input,
        [data-baseweb="input"],
        [data-baseweb="textarea"] {{
            font-size: {base_font_size}px !important;
            color: var(--safehome-input-text) !important;
            background-color: var(--safehome-input-bg) !important;
            border-color: var(--safehome-border) !important;
        }}

        textarea::placeholder,
        input::placeholder {{
            color: var(--safehome-muted) !important;
        }}

        div[data-testid="stFileUploader"],
        section[data-testid="stFileUploaderDropzone"],
        [data-testid="stFileUploaderDropzone"] {{
            border-color: var(--safehome-border) !important;
            border-radius: 16px !important;
            background-color: var(--safehome-card) !important;
            color: var(--safehome-text) !important;
        }}

        div[data-testid="stFileUploader"] *,
        section[data-testid="stFileUploaderDropzone"] *,
        [data-testid="stFileUploaderDropzone"] * {{
            color: var(--safehome-text) !important;
        }}

        /* Hazard card details */
        .hazard-number {{
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            color: var(--safehome-muted) !important;
            margin-bottom: 0.3rem !important;
        }}

        .hazard-title {{
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            margin-bottom: 0.4rem !important;
            color: var(--safehome-text) !important;
        }}

        .hazard-category {{
            display: inline-block !important;
            border-radius: 999px !important;
            padding: 0.25rem 0.65rem !important;
            margin-bottom: 0.75rem !important;
            background-color: var(--safehome-pill-bg) !important;
            color: var(--safehome-pill-text) !important;
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            border: 1px solid var(--safehome-border) !important;
        }}

        .hazard-section-label {{
            font-weight: 800 !important;
            margin-top: 0.6rem !important;
            margin-bottom: 0.15rem !important;
            color: var(--safehome-text) !important;
        }}

        .hazard-text {{
            margin-top: 0 !important;
            margin-bottom: 0.5rem !important;
            line-height: 1.45 !important;
            color: var(--safehome-text) !important;
        }}

        img {{
            border-radius: 12px !important;
        }}
        .priority-badge {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.25rem 0.65rem;
            margin-top: 0.25rem;
            margin-bottom: 0.55rem;
            font-size: 0.85rem;
            font-weight: 800;
            border: 2px solid var(--safe-border);
            color: var(--safe-text);
        }}

        .priority-fix-now {{
            background-color: var(--safe-soft);
            border-style: solid;
        }}

        .priority-fix-soon {{
            background-color: var(--safe-card);
            border-style: dashed;
        }}

        .priority-watch-review {{
            background-color: var(--safe-surface);
            border-style: dotted;
        }}
        /* Phone layout */
        @media screen and (max-width: 480px) {{
            .block-container {{
                padding-left: 0.85rem !important;
                padding-right: 0.85rem !important;
                padding-top: 0.75rem !important;
            }}

            h1 {{
                font-size: 1.8rem !important;
            }}

            .big-tagline {{
                font-size: 1.2rem !important;
            }}

            .plain-card,
            .hazard-card,
            .checklist-card,
            .print-step-card,
            .print-report,
            .step-card {{
                padding: 0.9rem !important;
                border-radius: 14px !important;
            }}

            .stButton > button,
            .stDownloadButton > button,
            button[data-testid="baseButton-secondary"],
            button[data-testid="baseButton-primary"] {{
                min-height: 60px !important;
                font-size: {base_font_size + 1}px !important;
            }}
        }}

        /* Print mode */
        @media print {{
            header,
            footer,
            [data-testid="stToolbar"],
            [data-testid="stSidebar"],
            .stButton,
            .stDownloadButton {{
                display: none !important;
            }}

            .block-container {{
                max-width: 100% !important;
                padding: 1rem !important;
            }}

            .print-report {{
                border: none !important;
                font-size: 12pt !important;
                color: #000000 !important;
                background-color: #ffffff !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def go_to_page(page_name):
    st.session_state["page"] = page_name
    st.rerun()
def reset_checklist_progress():
    """
    Clears checklist progress for a new room check.
    """

    st.session_state["checklist_index"] = 0
    st.session_state["checklist_answers_by_id"] = {}
    st.session_state["checklist_answers"] = []
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
        st.markdown(
            """
            <div class="plain-card">
                <strong>Accessibility Settings</strong><br>
                Adjust text size and color scheme.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='accessibility-label'>Text size</div>",
            unsafe_allow_html=True,
        )

        st.radio(
            "Text size",
            list(TEXT_SIZE_OPTIONS.keys()),
            key="text_size",
            label_visibility="collapsed",
        )

        st.markdown(
            "<div class='accessibility-label'>Color scheme</div>",
            unsafe_allow_html=True,
        )

        st.radio(
            "Color scheme",
            COLOR_SCHEME_OPTIONS,
            key="color_scheme",
            label_visibility="collapsed",
        )

        st.caption("System follows your device’s light or dark mode setting.")

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

def show_final_footer():
    """
    Shows final AI, privacy, and safety reminders at the bottom of the app.
    This helps make the project ready for judging and public demo.
    """

    st.divider()

    with st.expander("AI, privacy, and safety disclosure"):
        st.write(AI_USE_DISCLOSURE)
        st.write(FINAL_PRIVACY_SUMMARY)
        st.write(
            "This app is an educational home-safety tool. It does not diagnose "
            "medical conditions, predict individual medical fall risk, or guarantee "
            "fall prevention."
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


def save_checklist_answer(question, answer_label):
    """
    Saves one checklist answer.
    """

    st.session_state["checklist_answers_by_id"][question["id"]] = {
        "id": question["id"],
        "category": question["category"],
        "question": question["text"],
        "answer": ANSWER_VALUE_MAP[answer_label],
        "answer_label": answer_label,
    }


def skip_checklist_question(question):
    """
    Saves one skipped checklist question as Not applicable.
    This adds 0 points to the score.
    """

    st.session_state["checklist_answers_by_id"][question["id"]] = {
        "id": question["id"],
        "category": question["category"],
        "question": question["text"],
        "answer": "not_applicable",
        "answer_label": "Skipped",
    }


def build_ordered_checklist_answers():
    """
    Converts the answer dictionary into a list in the original checklist order.
    """

    ordered_answers = []

    for question in CHECKLIST_QUESTIONS:
        saved_answer = st.session_state["checklist_answers_by_id"].get(question["id"])

        if saved_answer:
            ordered_answers.append(saved_answer)

    return ordered_answers


def finish_checklist():
    """
    Saves checklist answers and moves to the summary page.
    """

    st.session_state["checklist_answers"] = build_ordered_checklist_answers()
    go_to_page("checklist_summary")


def skip_entire_checklist():
    """
    Skips the entire checklist.
    The score will use AI hazards only.
    """

    st.session_state["checklist_answers"] = []
    st.session_state["checklist_answers_by_id"] = {}
    st.session_state["checklist_index"] = 0
    st.session_state["checklist_was_skipped"] = True
    go_to_page("checklist_summary")
def open_uploaded_image_correct_orientation(uploaded_file):
    """
    Opens an uploaded image and fixes phone photo orientation.

    Some iPhone/phone photos are stored sideways with EXIF orientation data.
    ImageOps.exif_transpose() rotates the image so portrait photos stay portrait
    and landscape photos stay landscape.
    """

    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)
    uploaded_file.seek(0)

    return image

def get_category_label(category):
    return CATEGORY_LABELS.get(category, "Possible Hazard")


def render_hazard_card(hazard, number):
    """
    Displays one hazard as a clean Streamlit card.
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

    priority = get_priority_for_hazard(hazard)

    with st.container(border=True):
        st.caption(f"Hazard {number}")
        st.subheader(title)

        st.write(f"**Category:** {category_label}")

        if priority == "Fix Now":
            st.error(f"Priority: {priority}")
        elif priority == "Fix Soon":
            st.warning(f"Priority: {priority}")
        else:
            st.info(f"Priority: {priority}")

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
    Creates a short priority-ranked list of recommended first fixes.
    Uses AI recommendations first, then checklist-based generic fixes.
    """

    fixes = []
    seen_fixes = set()

    for hazard in ai_hazards:
        recommendation = hazard.get("recommendation")

        if recommendation and recommendation not in seen_fixes:
            fixes.append(
                {
                    "text": recommendation,
                    "priority": get_priority_for_hazard(hazard),
                    "source": hazard.get("title", "AI hazard"),
                }
            )
            seen_fixes.add(recommendation)

    for answer in checklist_answers:
        if answer.get("answer") in ["yes", "not_sure"]:
            category = answer.get("category")
            recommendation = GENERIC_RECOMMENDATIONS.get(category)
            priority = get_priority_for_checklist_answer(answer)

            if recommendation and recommendation not in seen_fixes:
                fixes.append(
                    {
                        "text": recommendation,
                        "priority": priority,
                        "source": answer.get("question", "Checklist concern"),
                    }
                )
                seen_fixes.add(recommendation)

    return sort_by_priority(fixes)[:5]
def get_report_file_name(room_type):
    """
    Creates a simple safe file name for the downloaded report.
    """

    if not room_type:
        room_type = "room"

    safe_room_name = room_type.lower().replace(" ", "_")
    return f"ai_safehome_{safe_room_name}_safety_report.txt"

def reset_current_room_check():
    """
    Clears the current room check but keeps the multi-room summary.
    """

    st.session_state["room_type"] = None
    st.session_state["photo_uploaded"] = False
    st.session_state["ai_result"] = None
    st.session_state["checklist_answers"] = []
    reset_checklist_progress()
    st.session_state["score"] = None
    st.session_state["risk_level"] = None
    st.session_state["score_breakdown"] = None
    st.session_state["report_text"] = None
    st.session_state["current_check_saved"] = False
    st.session_state["database_save_complete"] = False
    st.session_state["database_save_id"] = None

def clear_home_summary():
    """
    Clears all saved room results.
    """

    st.session_state["room_results"] = []
    st.session_state["home_summary_text"] = None
    st.session_state["current_check_saved"] = False


def get_current_room_result():
    """
    Builds a saved result dictionary for the current completed room.
    """

    ai_result = st.session_state.get("ai_result") or {}
    ai_hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])

    recommended_fixes = get_recommended_first_fixes(
        ai_hazards,
        checklist_answers,
    )

    return {
        "room_type": st.session_state.get("room_type", "Unknown Room"),
        "score": st.session_state.get("score", 0),
        "risk_level": st.session_state.get("risk_level", "Low Risk"),
        "hazards": ai_hazards,
        "checklist_answers": checklist_answers,
        "recommended_fixes": recommended_fixes,
        "checklist_was_skipped": st.session_state.get("checklist_was_skipped", False),
    }


def save_current_room_to_summary():
    """
    Saves the current completed room to the multi-room summary.

    Returns True if saved.
    Returns False if it was already saved.
    """

    if st.session_state.get("current_check_saved"):
        return False

    room_result = get_current_room_result()

    st.session_state["room_results"].append(room_result)
    st.session_state["current_check_saved"] = True

    return True


def show_room_results_count():
    """
    Shows how many rooms are saved so far.
    """

    saved_count = len(st.session_state.get("room_results", []))

    if saved_count == 0:
        st.info("No rooms have been saved to the home summary yet.")
    elif saved_count == 1:
        st.info("1 room has been saved to the home summary.")
    else:
        st.info(f"{saved_count} rooms have been saved to the home summary.")

def get_current_database_save_payload():
    """
    Collects the current completed room-check data for database saving.

    This does not include photos or personal information.
    """

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])

    checklist_answers = st.session_state.get("checklist_answers", [])
    score = st.session_state.get("score")
    risk_level = st.session_state.get("risk_level")
    room_type = st.session_state.get("room_type")

    recommended_fixes = get_recommended_first_fixes(
        hazards,
        checklist_answers,
    )

    return {
        "room_type": room_type,
        "score": score,
        "risk_level": risk_level,
        "hazards": hazards,
        "checklist_answers": checklist_answers,
        "recommended_fixes": recommended_fixes,
        "checklist_was_skipped": st.session_state.get("checklist_was_skipped", False),
        "using_demo_sample": st.session_state.get("using_demo_sample", False),
        "demo_sample_name": st.session_state.get("demo_sample_name"),
    }
    def safe_text(value):
    """
    Escapes text before showing it inside custom HTML.

    This keeps dashboard cards safer if database text contains unusual characters.
    """

    if value is None:
        return "None"

    return html.escape(str(value))


def format_database_datetime(value):
    """
    Makes a Supabase timestamp easier to read.
    """

    if not value:
        return "Unknown time"

    return str(value).replace("T", " ").replace("+00:00", " UTC")


def show_saved_results_metrics(stats):
    """
    Shows top-level saved-result metrics.
    """

    total_checks = stats.get("total_checks", 0)
    average_score = stats.get("average_score", 0)
    high_risk_count = stats.get("high_risk_count", 0)
    most_common_room = stats.get("most_common_room") or "None yet"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Saved Checks", total_checks)

    with col2:
        st.metric("Average Score", f"{average_score}/100")

    with col3:
        st.metric("High Risk Rooms", high_risk_count)

    with col4:
        st.metric("Most Common Room", most_common_room)


def show_saved_results_risk_breakdown(stats):
    """
    Shows low/moderate/high saved-result counts.
    """

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Risk Label Breakdown</strong><br>
            Low Risk: {stats.get("low_risk_count", 0)}<br>
            Moderate Risk: {stats.get("moderate_risk_count", 0)}<br>
            High Risk: {stats.get("high_risk_count", 0)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_recent_saved_room_checks(rows):
    """
    Shows recent anonymous saved room checks.
    """

    if not rows:
        st.info("No saved anonymous room checks yet.")
        return

    for index, row in enumerate(rows, start=1):
        created_at = format_database_datetime(row.get("created_at"))
        room_type = safe_text(row.get("room_type", "Unknown Room"))
        risk_level = safe_text(row.get("risk_level", "Unknown"))
        ai_mode = safe_text(row.get("ai_mode", "unknown"))

        score = row.get("score", 0)
        hazard_count = row.get("hazard_count", 0)
        checklist_was_skipped = row.get("checklist_was_skipped", False)
        safety_confirmed = row.get("safety_confirmed", False)

        checklist_text = "Yes" if checklist_was_skipped else "No"
        safety_text = "Yes" if safety_confirmed else "No"

        st.markdown(
            f"""
            <div class="plain-card">
                <strong>Saved Check {index}</strong><br>
                Room: {room_type}<br>
                Score: {score}/100<br>
                Risk Label: {risk_level}<br>
                AI Mode: {ai_mode}<br>
                Hazards Saved: {hazard_count}<br>
                Checklist Skipped: {checklist_text}<br>
                Anonymous Safety Confirmed: {safety_text}<br>
                Saved At: {safe_text(created_at)}
            </div>
            """,
            unsafe_allow_html=True,
        )
def get_home_summary_file_name():
    """
    Creates a simple download file.
    """

    return "ai_safehome_multi_room_summary.txt"

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

        image = open_uploaded_image_correct_orientation(uploaded_file)
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
        reset_checklist_progress()
        go_to_page("checklist")

    if st.button("Analyze Another Photo"):
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        reset_checklist_progress()
        go_to_page("photo_upload")

    if st.button("Start Over"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["checklist_answers"] = []
        reset_checklist_progress()
        go_to_page("landing")

def show_database_save_panel():
    """
    Shows the database save panel after a score has been calculated.

    Saves anonymous room-check results only.
    Does not save uploaded photos or personal information.
    """

    st.subheader("Save Anonymous Result")

    st.caption(get_database_status_message())

    if not is_database_enabled():
        st.info(
            "Database saving is currently disabled. "
            "The app still works normally without saving results."
        )
        return

    score = st.session_state.get("score")
    risk_level = st.session_state.get("risk_level")
    room_type = st.session_state.get("room_type")

    if score is None or risk_level is None or not room_type:
        st.warning("Calculate a risk score before saving a result.")
        return

    if st.session_state.get("database_save_complete"):
        st.success(
            "This room check has already been saved anonymously. "
            "No photo or personal information was stored."
        )

        saved_id = st.session_state.get("database_save_id")

        if saved_id:
            st.caption(f"Saved result ID: {saved_id}")

        return

    st.warning(
        "This saves anonymous room-check results only. "
        "Do not save real patient information, names, addresses, faces, "
        "mail, bills, medication bottles, medical documents, or medical history. "
        "Uploaded photos are not stored."
    )

    safety_confirmed = st.checkbox(
        "I confirm this result contains no personal, medical, or real patient information.",
        key="database_safety_confirmed",
    )

    if st.button("Save Anonymous Result", type="primary"):
        if not safety_confirmed:
            st.error(
                "Please confirm that this result contains no personal, medical, "
                "or real patient information before saving."
            )
            return

        payload = get_current_database_save_payload()

        try:
            saved_id = save_room_check(
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
            )

            st.session_state["database_save_complete"] = True
            st.session_state["database_save_id"] = saved_id

            st.success(
                "Anonymous room check saved. "
                "No photo or personal information was stored."
            )

        except Exception as error:
            st.error(
                "Could not save this result. "
                "The app still works, but this check was not stored."
            )

            with st.expander("Technical details"):
                st.code(str(error))
        if st.button("View Saved Results Dashboard"):
            go_to_page("saved_results")            
def show_saved_results_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Saved Results Dashboard")

    st.caption(get_database_status_message())

    st.warning(
        "This dashboard shows anonymous room-check results only. "
        "Uploaded photos, names, addresses, medical history, medication lists, "
        "faces, mail, bills, and medical documents should not be stored."
    )

    if not is_database_enabled():
        st.info(
            "Database saving is disabled. Enable DATABASE_ENABLED=true to view saved results."
        )

        if st.button("← Back to Landing Page"):
            go_to_page("landing")

        return

    try:
        stats = fetch_summary_stats()
        recent_rows = fetch_recent_room_checks(limit=25)

    except Exception as error:
        st.error(
            "Could not load saved results. Check your Supabase settings and database tables."
        )

        with st.expander("Technical details"):
            st.code(str(error))

        if st.button("← Back to Landing Page"):
            go_to_page("landing")

        return

    show_saved_results_metrics(stats)

    st.divider()

    show_saved_results_risk_breakdown(stats)

    st.divider()

    st.subheader("Recent Anonymous Room Checks")

    show_recent_saved_room_checks(recent_rows)

    st.divider()

    if st.button("Refresh Dashboard"):
        st.rerun()

    if st.button("Start New Safety Check"):
        if "reset_current_room_check" in globals():
            reset_current_room_check()

        go_to_page("room_selection")

    if st.button("← Back to Landing Page"):
        go_to_page("landing")
def show_checklist_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Step 4: Safety Checklist")

    show_step_card("Step 4 of 6 — Answer one checklist question at a time, or skip if needed.")

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
        "The checklist helps catch hazards the photo analysis may miss. "
        "You may skip individual questions or skip the checklist entirely."
    )

    total_questions = len(CHECKLIST_QUESTIONS)
    current_index = st.session_state.get("checklist_index", 0)

    if current_index >= total_questions:
        finish_checklist()
        return

    current_question = CHECKLIST_QUESTIONS[current_index]
    question_number = current_index + 1

    st.progress(question_number / total_questions)

    st.caption(f"Question {question_number} of {total_questions}")

    st.markdown(
        f"""
        <div class="checklist-card">
            <strong>{current_question["text"]}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saved_answer = st.session_state["checklist_answers_by_id"].get(
        current_question["id"]
    )

    if saved_answer and saved_answer.get("answer_label") in ANSWER_OPTIONS:
        default_index = ANSWER_OPTIONS.index(saved_answer["answer_label"])
    else:
        default_index = 0

    selected_answer_label = st.radio(
        "Choose an answer",
        ANSWER_OPTIONS,
        index=default_index,
        key=f"checklist_wizard_{current_question['id']}_{current_index}",
    )

    save_label = "Save & Finish" if question_number == total_questions else "Save & Next"

    if st.button(save_label, type="primary"):
        save_checklist_answer(current_question, selected_answer_label)

        if question_number == total_questions:
            finish_checklist()
        else:
            st.session_state["checklist_index"] += 1
            st.rerun()

    if st.button("Skip This Question"):
        skip_checklist_question(current_question)

        if question_number == total_questions:
            finish_checklist()
        else:
            st.session_state["checklist_index"] += 1
            st.rerun()

    if current_index > 0:
        if st.button("← Previous Question"):
            st.session_state["checklist_index"] -= 1
            st.rerun()

    if st.button("Skip Entire Checklist"):
        skip_entire_checklist()

    if st.button("← Back to Hazard Results"):
        go_to_page("ai_results")

def show_checklist_summary_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Checklist Summary")

    checklist_answers = st.session_state.get("checklist_answers", [])
    checklist_was_skipped = st.session_state.get("checklist_was_skipped", False)

    if checklist_was_skipped:
        st.warning(
            "Checklist was skipped. The risk score will be based only on AI photo hazards."
        )

        if st.button("Calculate Risk Score →", type="primary"):
            ai_result = st.session_state.get("ai_result") or {}
            hazards = ai_result.get("hazards", [])

            score = calculate_score(hazards, [])
            risk_level = get_risk_level(score)
            score_breakdown = get_score_breakdown(hazards, [])

            st.session_state["score"] = score
            st.session_state["risk_level"] = risk_level
            st.session_state["score_breakdown"] = score_breakdown
            st.session_state["current_check_saved"] = False

            go_to_page("risk_score")

        if st.button("Answer Checklist Instead"):
            reset_checklist_progress()
            go_to_page("checklist")

        if st.button("Start Over"):
            st.session_state["room_type"] = None
            st.session_state["photo_uploaded"] = False
            st.session_state["ai_result"] = None
            reset_checklist_progress()
            st.session_state["score"] = None
            st.session_state["risk_level"] = None
            st.session_state["score_breakdown"] = None
            st.session_state["report_text"] = None
            go_to_page("landing")

        return

    if not checklist_answers:
        st.error("No checklist answers were saved.")

        if st.button("Return to Checklist"):
            reset_checklist_progress()
            go_to_page("checklist")

        if st.button("Skip Checklist and Score AI Results Only"):
            skip_entire_checklist()

        return

    yes_count = 0
    not_sure_count = 0
    skipped_count = 0
    not_applicable_count = 0

    for answer in checklist_answers:
        if answer["answer"] == "yes":
            yes_count += 1
        elif answer["answer"] == "not_sure":
            not_sure_count += 1
        elif answer.get("answer_label") == "Skipped":
            skipped_count += 1
        elif answer["answer"] == "not_applicable":
            not_applicable_count += 1

    st.success("Your checklist answers were saved.")

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Yes:</strong> {yes_count}<br>
            <strong>Not sure:</strong> {not_sure_count}<br>
            <strong>Skipped:</strong> {skipped_count}<br>
            <strong>Not applicable:</strong> {not_applicable_count}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("View checklist answers"):
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
        st.session_state["current_check_saved"] = False

        go_to_page("risk_score")

    if st.button("Edit Checklist"):
        st.session_state["checklist_index"] = 0
        go_to_page("checklist")

    if st.button("Skip Checklist Instead"):
        skip_entire_checklist()

    if st.button("Start Over"):
        st.session_state["room_type"] = None
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        reset_checklist_progress()
        st.session_state["score"] = None
        st.session_state["risk_level"] = None
        st.session_state["score_breakdown"] = None
        st.session_state["report_text"] = None
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

    if st.session_state.get("checklist_was_skipped"):
        st.info(
            "Review completeness: AI-only review. "
            "The checklist was skipped, so this score may miss hazards that are not visible in the photo."
        )
    else:
        checklist_answers = st.session_state.get("checklist_answers", [])

        real_answer_count = 0

        for answer in checklist_answers:
            if answer.get("answer_label") != "Skipped":
                real_answer_count += 1

        if real_answer_count == 0:
            st.info(
                "Review completeness: AI-only review. "
                "No checklist questions were answered."
            )
        elif real_answer_count < len(CHECKLIST_QUESTIONS):
            st.info(
                f"Review completeness: Partial checklist review. "
                f"{real_answer_count} of {len(CHECKLIST_QUESTIONS)} checklist questions were answered."
            )
        else:
            st.success("Review completeness: AI photo review + checklist review.")
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
            priority = fix.get("priority", "Watch/Review")
            priority_class = get_priority_css_class(priority)

            st.markdown(
                f"""
                <div class="plain-card">
                    <strong>{index}. {fix.get("text")}</strong><br>
                    <div class="priority-badge {priority_class}">{priority}</div><br>
                    <span class="small-muted">Source: {fix.get("source")}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("View score breakdown"):
        if score_breakdown:
            st.write(f"AI hazard points: **{score_breakdown['ai_points']}**")
            if st.session_state.get("checklist_was_skipped"):
                st.write("Checklist status: **Skipped**")
            else:
                st.write("Checklist status: **Completed or partially completed**")
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
    st.divider()
    show_database_save_panel()
    st.subheader("Multi-Room Home Summary")

    show_room_results_count()

    if st.button("Save This Room to Home Summary"):
        saved = save_current_room_to_summary()

        if saved:
            st.success("This room was saved to the home summary.")
        else:
            st.info("This room is already saved. Edit the checklist and recalculate if you want to save a new version.")

    if st.button("Check Another Room"):
        reset_current_room_check()
        go_to_page("room_selection")

    if st.session_state.get("room_results"):
        if st.button("View Home Summary"):
            go_to_page("home_summary")
    if st.button("Create Safety Report →", type="primary"):
        report_text = generate_report(
        room_type=st.session_state.get("room_type"),
        hazards=ai_hazards,
        checklist_answers=checklist_answers,
        score=score,
        risk_level=risk_level,
        recommended_fixes=fixes,
        safety_disclaimer=SAFETY_DISCLAIMER,
        checklist_was_skipped=st.session_state.get("checklist_was_skipped", False),
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
        reset_checklist_progress()
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
        "AI SafeHome does not save uploaded photos. "
        "If database saving is enabled, the app can save anonymous room-check results only."
    )
    st.divider()
    show_database_save_panel()
    st.subheader("Multi-Room Home Summary")

    show_room_results_count()

    if st.button("Save This Room to Home Summary"):
        saved = save_current_room_to_summary()

        if saved:
            st.success("This room was saved to the home summary.")
        else:
            st.info("This room is already saved.")

    if st.button("Check Another Room"):
        reset_current_room_check()
        go_to_page("room_selection")

    if st.session_state.get("room_results"):
        if st.button("View Home Summary"):
            go_to_page("home_summary")
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
        reset_checklist_progress()
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
        reset_checklist_progress()
        st.session_state["score"] = None
        st.session_state["risk_level"] = None
        st.session_state["score_breakdown"] = None
        st.session_state["report_text"] = None
        go_to_page("landing")
def show_home_summary_page():
    st.title("🏠 AI SafeHome")
    st.subheader("Multi-Room Home Summary")

    room_results = st.session_state.get("room_results", [])

    if not room_results:
        st.error("No rooms have been saved yet.")

        if st.button("Check a Room"):
            go_to_page("room_selection")

        return

    priority_label = get_home_priority_label(room_results)

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Rooms saved:</strong> {len(room_results)}<br>
            <strong>Home review priority:</strong> {priority_label}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(
        "This is an educational home-safety summary. It is not a medical diagnosis "
        "and does not guarantee fall prevention."
    )

    st.subheader("Saved Rooms")

    for index, room in enumerate(room_results, start=1):
        st.markdown(
            f"""
            <div class="plain-card">
                <strong>Room {index}: {room["room_type"]}</strong><br>
                Score: {room["score"]}/100<br>
                Risk Level: {room["risk_level"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        hazards = room.get("hazards", [])

        if hazards:
            st.write("Possible hazards:")
            for hazard in hazards:
                st.write(f"- {hazard.get('title', 'Possible hazard')}")
        else:
            st.write("Possible hazards: none listed.")

        fixes = room.get("recommended_fixes", [])

        if fixes:
            st.write("Recommended fixes:")
            for fix in fixes[:3]:
                if isinstance(fix, dict):
                    priority = fix.get("priority", "Watch/Review")
                    st.write(f"- [{priority}] {fix.get('text')}")
                else:
                    st.write(f"- {fix}")

        st.divider()

    home_summary_text = build_home_summary(
        room_results=room_results,
        safety_disclaimer=SAFETY_DISCLAIMER,
    )

    st.session_state["home_summary_text"] = home_summary_text

    st.subheader("Printable Multi-Room Summary")

    st.markdown(
        f"""
        <div class="print-report">
        {home_summary_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        label="Download Multi-Room Summary",
        data=home_summary_text,
        file_name=get_home_summary_file_name(),
        mime="text/plain",
        type="primary",
    )

    st.info(
        "This summary is not stored in a database. Download or print it if you want to keep it."
    )

    if st.button("Check Another Room"):
        reset_current_room_check()
        go_to_page("room_selection")

    if st.button("Back to Current Room Report"):
        go_to_page("safety_report")

    if st.button("Clear Home Summary"):
        clear_home_summary()
        st.success("Home summary cleared.")
        go_to_page("room_selection")

    if st.button("Start Over Completely"):
        reset_current_room_check()
        clear_home_summary()
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
    elif current_page == "home_summary":
        show_home_summary_page()     
    elif current_page == "saved_results":
        show_saved_results_page()    
    else:
        st.error("Unknown page. Returning to landing page.")
        st.session_state["page"] = "landing"
        st.rerun()
    show_final_footer()    


main()