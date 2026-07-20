import csv
import html
import io
import os
import re
import secrets
import string
import urllib.parse
from datetime import date
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from PIL import Image
try:
    from src.email_service import (
        get_email_status_message,
        is_email_enabled,
        send_summary_email,
    )
except Exception as email_import_error:
    EMAIL_IMPORT_ERROR_MESSAGE = str(email_import_error)

    def is_email_enabled() -> bool:
        return False

    def get_email_status_message() -> str:
        return f"Server-side email unavailable: {EMAIL_IMPORT_ERROR_MESSAGE}"

    def send_summary_email(*args, **kwargs):
        raise RuntimeError("Server-side email unavailable.")
try:
    from src.ai_analysis import analyze_photo as project_analyze_photo
except Exception:
    project_analyze_photo = None

try:
    from src.checklist import ANSWER_OPTIONS, ANSWER_VALUE_MAP, CHECKLIST_QUESTIONS
except Exception:
    ANSWER_OPTIONS = ["Yes", "No", "Not sure", "Not applicable"]
    ANSWER_VALUE_MAP = {
        "Yes": "yes",
        "No": "no",
        "Not sure": "not_sure",
        "Not applicable": "not_applicable",
    }
    CHECKLIST_QUESTIONS = [
        {"id": "loose_rug", "category": "loose_rug", "text": "Are there loose rugs or mats?"},
        {"id": "cords", "category": "cords", "text": "Are cords crossing a walking path?"},
        {"id": "clutter", "category": "clutter", "text": "Is there clutter on the floor?"},
        {"id": "poor_lighting", "category": "poor_lighting", "text": "Is the room dim or poorly lit?"},
        {"id": "slippery_floor", "category": "slippery_floor", "text": "Are floors slippery or wet?"},
        {"id": "narrow_pathway", "category": "narrow_pathway", "text": "Is the walking path narrow or blocked?"},
        {"id": "stairs", "category": "stairs", "text": "Are there stairs or steps nearby?"},
        {"id": "handrail", "category": "handrail", "text": "Are handrails missing, loose, or hard to hold?"},
        {"id": "bathroom_grab_bars", "category": "bathroom_grab_bars", "text": "Is this a bathroom without visible grab bars?"},
        {"id": "hard_to_reach_items", "category": "hard_to_reach_items", "text": "Are commonly used items hard to reach?"},
    ]

try:
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
except Exception as database_import_error:
    # Safe stubs so the app can still run if database.py is broken or Supabase is missing.
    DATABASE_IMPORT_ERROR_MESSAGE = str(database_import_error)

    def is_database_enabled() -> bool:
        return False

    def get_database_status_message() -> str:
        return f"Database unavailable: {DATABASE_IMPORT_ERROR_MESSAGE}"

    def is_valid_home_id(home_id: Optional[str]) -> bool:
        return False

    def create_home_id(home_id: str) -> str:
        raise RuntimeError("Database unavailable.")

    def home_id_exists(home_id: str) -> bool:
        return False

    def is_home_id_available(home_id: str) -> bool:
        return False

    def create_home_room(*args, **kwargs):
        raise RuntimeError("Database unavailable.")

    def fetch_rooms_for_home(*args, **kwargs):
        return []

    def get_next_room_id(*args, **kwargs):
        return "ROOM-1"

    def save_room_check(*args, **kwargs):
        raise RuntimeError("Database unavailable.")

    def fetch_room_checks_by_home_id(*args, **kwargs):
        return []

    def fetch_summary_stats_for_home(*args, **kwargs):
        return {}

    def fetch_room_check_by_id(*args, **kwargs):
        return None

    def fetch_room_check_details(*args, **kwargs):
        return []

    def fetch_all_room_stats_for_home(*args, **kwargs):
        return []

    def fetch_room_stats(*args, **kwargs):
        return {}

    def fetch_room_checks_by_room_id(*args, **kwargs):
        return []


APP_NAME = "AI SafeHome"
TAGLINE = "Find home fall hazards before they become accidents."
LANDING_EXPLANATION = (
    "Upload a staged room photo, answer a few simple questions, and AI SafeHome "
    "will help identify possible fall hazards such as loose rugs, cords, clutter, "
    "poor lighting, stairs, slippery floors, and bathroom risks."
)
SAFETY_DISCLAIMER = (
    "AI SafeHome is an educational home-safety tool. It does not diagnose medical "
    "conditions, predict individual fall risk, or guarantee fall prevention. AI may "
    "miss hazards. For serious safety concerns, ask a qualified professional to review the home."
)
PRIVACY_REMINDER = (
    "Use staged, non-patient photos only. Avoid faces, names, addresses, mail, bills, "
    "medication bottles, and medical documents."
)
PHOTO_UPLOAD_PRIVACY_WARNING = (
    "Before uploading, avoid including faces, names, addresses, medication bottles, "
    "mail, bills, or medical documents in the photo."
)
PHOTO_NOT_STORED_NOTE = (
    "Uploaded photos are used only during this app session. This app does not save photos to the database."
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

HAZARD_POINTS = {
    "loose_rug": 10,
    "cords": 12,
    "clutter": 10,
    "poor_lighting": 8,
    "slippery_floor": 12,
    "narrow_pathway": 8,
    "stairs": 15,
    "handrail": 15,
    "bathroom_grab_bars": 15,
    "hard_to_reach_items": 6,
    "threshold_trip": 10,
    "unstable_furniture": 10,
    "pet_items": 6,
    "footwear": 6,
    "low_seating": 8,
    "poor_contrast": 6,
    "uneven_floor": 12,
    "door_mat": 8,
    "furniture_in_path": 8,
    "outdoor_surface": 12,
    "laundry_on_floor": 8,
    "open_drawers_cabinets": 8,
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

PRIORITY_FIX_NOW = "Fix Now"
PRIORITY_FIX_SOON = "Fix Soon"
PRIORITY_WATCH_REVIEW = "Watch/Review"

CATEGORY_PRIORITY = {
    "cords": PRIORITY_FIX_NOW,
    "slippery_floor": PRIORITY_FIX_NOW,
    "stairs": PRIORITY_FIX_NOW,
    "handrail": PRIORITY_FIX_NOW,
    "bathroom_grab_bars": PRIORITY_FIX_NOW,
    "threshold_trip": PRIORITY_FIX_NOW,
    "uneven_floor": PRIORITY_FIX_NOW,
    "outdoor_surface": PRIORITY_FIX_NOW,
    "open_drawers_cabinets": PRIORITY_FIX_NOW,
    "loose_rug": PRIORITY_FIX_SOON,
    "clutter": PRIORITY_FIX_SOON,
    "narrow_pathway": PRIORITY_FIX_SOON,
    "poor_lighting": PRIORITY_FIX_SOON,
    "hard_to_reach_items": PRIORITY_FIX_SOON,
    "unstable_furniture": PRIORITY_FIX_SOON,
    "door_mat": PRIORITY_FIX_SOON,
    "furniture_in_path": PRIORITY_FIX_SOON,
    "laundry_on_floor": PRIORITY_FIX_SOON,
    "low_seating": PRIORITY_FIX_SOON,
    "poor_contrast": PRIORITY_FIX_SOON,
    "pet_items": PRIORITY_WATCH_REVIEW,
    "footwear": PRIORITY_WATCH_REVIEW,
    "unclear": PRIORITY_WATCH_REVIEW,
}

PRIORITY_ORDER = {
    PRIORITY_FIX_NOW: 1,
    PRIORITY_FIX_SOON: 2,
    PRIORITY_WATCH_REVIEW: 3,
}


def setup_page() -> None:
    st.set_page_config(page_title="AI SafeHome", page_icon="🏠", layout="centered")


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
        "room_results": [],
        "home_summary_text": None,
        "current_check_saved": False,
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_page(page_name: str) -> None:
    st.session_state["page"] = page_name
    st.rerun()


def add_mobile_friendly_style() -> None:
    text_size = st.session_state.get("text_size", "Standard")
    color_scheme = st.session_state.get("color_scheme", "System")

    base_font_size = 17
    if text_size == "Large":
        base_font_size = 19
    elif text_size == "Extra Large":
        base_font_size = 21

    if color_scheme == "Dark":
        theme_css = """
        :root { --safe-bg:#0f172a; --safe-surface:#111827; --safe-card:#1f2937; --safe-text:#f9fafb; --safe-muted:#d1d5db; --safe-border:#475569; --safe-soft:#334155; }
        """
    elif color_scheme == "High Contrast":
        theme_css = """
        :root { --safe-bg:#000000; --safe-surface:#000000; --safe-card:#000000; --safe-text:#ffffff; --safe-muted:#ffffff; --safe-border:#ffffff; --safe-soft:#111111; }
        """
    elif color_scheme == "Light":
        theme_css = """
        :root { --safe-bg:#ffffff; --safe-surface:#f8fafc; --safe-card:#ffffff; --safe-text:#111827; --safe-muted:#4b5563; --safe-border:#d1d5db; --safe-soft:#f1f5f9; }
        """
    else:
        theme_css = """
        :root { --safe-bg:#ffffff; --safe-surface:#f8fafc; --safe-card:#ffffff; --safe-text:#111827; --safe-muted:#4b5563; --safe-border:#d1d5db; --safe-soft:#f1f5f9; }
        @media (prefers-color-scheme: dark) {
            :root { --safe-bg:#0f172a; --safe-surface:#111827; --safe-card:#1f2937; --safe-text:#f9fafb; --safe-muted:#d1d5db; --safe-border:#475569; --safe-soft:#334155; }
        }
        """

    st.markdown(
        f"""
        <style>
        {theme_css}
        html, body, [class*="css"] {{ font-size:{base_font_size}px; }}
        .stApp {{ background-color:var(--safe-bg); color:var(--safe-text); }}
        .block-container {{ max-width:720px; padding:1rem 1rem 2rem 1rem; }}
        h1, h2, h3, h4, h5, h6, p, li, label, span, div {{ color:var(--safe-text); }}
        h1 {{ font-size:2rem !important; line-height:1.15 !important; }}
        p, li {{ line-height:1.45; }}
        .stButton > button, .stDownloadButton > button {{ width:100%; min-height:54px; font-size:{base_font_size}px; font-weight:700; border-radius:14px; margin:.25rem 0; }}
        .big-tagline {{ font-size:1.25rem; font-weight:800; line-height:1.35; margin-bottom:1rem; }}
        .plain-card, .step-card, .hazard-card, .checklist-card, .print-report, .print-step-card {{ border:1px solid var(--safe-border); border-radius:16px; padding:1rem; margin:1rem 0; background-color:var(--safe-card); color:var(--safe-text); line-height:1.45; }}
        .step-card {{ background-color:var(--safe-surface); font-size:.95rem; }}
        .hazard-number {{ font-size:.9rem; font-weight:700; color:var(--safe-muted); margin-bottom:.3rem; }}
        .hazard-title {{ font-size:1.15rem; font-weight:800; margin-bottom:.4rem; }}
        .hazard-category, .priority-badge {{ display:inline-block; border-radius:999px; padding:.25rem .65rem; margin:.2rem .2rem .55rem 0; background-color:var(--safe-soft); border:1px solid var(--safe-border); font-size:.85rem; font-weight:800; color:var(--safe-text); }}
        .priority-fix-now {{ border-style:solid; }}
        .priority-fix-soon {{ border-style:dashed; }}
        .priority-watch-review {{ border-style:dotted; }}
        .hazard-section-label {{ font-weight:800; margin-top:.6rem; margin-bottom:.15rem; }}
        .small-muted {{ font-size:.95rem; color:var(--safe-muted); line-height:1.4; }}
        div[role="radiogroup"] label {{ border:1px solid var(--safe-border); border-radius:12px; padding:.85rem; margin-bottom:.45rem; background-color:var(--safe-card); min-height:44px; }}
        div[data-testid="stFileUploader"] {{ border:1px dashed var(--safe-border); border-radius:16px; padding:.75rem; background-color:var(--safe-surface); }}
        .print-report {{ white-space:pre-wrap; font-family:Arial, sans-serif; overflow-wrap:break-word; word-wrap:break-word; }}
        textarea, input, select {{ color:var(--safe-text) !important; background-color:var(--safe-card) !important; }}
        img {{ border-radius:12px; }}
        .email-link-button {{ display:inline-block; background:var(--safe-text); color:var(--safe-bg) !important; padding:.75rem 1rem; border-radius:999px; text-decoration:none !important; font-weight:800; margin:.5rem 0; }}
        @media screen and (max-width:480px) {{ .block-container {{ padding-left:.85rem; padding-right:.85rem; }} h1 {{ font-size:1.8rem !important; }} }}
        @media print {{ header, footer, [data-testid="stToolbar"], [data-testid="stSidebar"], .stButton, .stDownloadButton {{ display:none !important; }} .block-container {{ max-width:100%; padding:1rem; }} .print-report {{ border:none; color:#000; background:#fff; font-size:12pt; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_accessibility_panel() -> None:
    with st.expander("⚙️ Accessibility settings"):
        st.selectbox("Text size", ["Standard", "Large", "Extra Large"], key="text_size")
        st.selectbox("Color scheme", ["System", "Light", "Dark", "High Contrast"], key="color_scheme")


def show_step_card(step_text: str) -> None:
    st.markdown(f'<div class="step-card">{html.escape(step_text)}</div>', unsafe_allow_html=True)


def safe_text(value: Any) -> str:
    if value is None:
        return "None"
    return html.escape(str(value))


def format_database_datetime(value: Any) -> str:
    if not value:
        return "Unknown time"
    return str(value).replace("T", " ").replace("+00:00", " UTC")


def get_category_label(category: Optional[str]) -> str:
    return CATEGORY_LABELS.get(category or "unclear", str(category or "Unclear"))


def get_priority_for_category(category: Optional[str]) -> str:
    return CATEGORY_PRIORITY.get(category or "unclear", PRIORITY_WATCH_REVIEW)


def get_priority_for_hazard(hazard: Dict[str, Any]) -> str:
    return get_priority_for_category(hazard.get("category"))


def get_priority_css_class(priority: str) -> str:
    if priority == PRIORITY_FIX_NOW:
        return "priority-fix-now"
    if priority == PRIORITY_FIX_SOON:
        return "priority-fix-soon"
    return "priority-watch-review"


def sort_by_priority(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda item: PRIORITY_ORDER.get(item.get("priority", PRIORITY_WATCH_REVIEW), 99))


def calculate_score(ai_hazards: List[Dict[str, Any]], checklist_answers: List[Dict[str, Any]]) -> int:
    score = 0
    for hazard in ai_hazards:
        score += HAZARD_POINTS.get(hazard.get("category"), 0)
    for answer in checklist_answers:
        category = answer.get("category")
        response = answer.get("answer")
        points = HAZARD_POINTS.get(category, 0)
        if response == "yes":
            score += points
        elif response == "not_sure":
            score += points * 0.5
    return min(round(score), 100)


def get_risk_level(score: int) -> str:
    if score < 30:
        return "Low Risk"
    if score < 60:
        return "Moderate Risk"
    return "High Risk"


def get_score_breakdown(ai_hazards: List[Dict[str, Any]], checklist_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    ai_points = sum(HAZARD_POINTS.get(hazard.get("category"), 0) for hazard in ai_hazards)
    checklist_points = 0
    for answer in checklist_answers:
        points = HAZARD_POINTS.get(answer.get("category"), 0)
        if answer.get("answer") == "yes":
            checklist_points += points
        elif answer.get("answer") == "not_sure":
            checklist_points += points * 0.5
    total = ai_points + checklist_points
    return {
        "ai_points": round(ai_points, 1),
        "checklist_points": round(checklist_points, 1),
        "total_before_cap": round(total, 1),
        "final_score": min(round(total), 100),
    }


def get_fake_analysis(room_type: str) -> Dict[str, Any]:
    room = (room_type or "Other").lower()
    hazards = [
        {"category": "cords", "title": "Cord near walking path", "explanation": "A cord near a walking area can create a tripping hazard.", "recommendation": "Move the cord along the wall or secure it with a cord cover."},
        {"category": "loose_rug", "title": "Possible loose rug", "explanation": "A rug can slide or catch someone's foot if it does not have non-slip backing.", "recommendation": "Use non-slip backing, tape down the edges, or remove the rug from the walking path."},
        {"category": "clutter", "title": "Floor clutter", "explanation": "Objects on the floor can make walking paths harder to use safely.", "recommendation": "Clear small objects, bags, shoes, or boxes from the walking path."},
    ]
    if room == "bathroom":
        hazards = [
            {"category": "bathroom_grab_bars", "title": "Bathroom without visible grab bars", "explanation": "This photo does not clearly show grab bars near bathroom areas.", "recommendation": "Consider properly installed grab bars near the toilet, shower, or bathtub."},
            {"category": "slippery_floor", "title": "Possible slippery floor area", "explanation": "Bathroom floors can become slippery when wet.", "recommendation": "Use non-slip mats and keep the floor dry."},
        ]
    elif room == "stairs":
        hazards = [
            {"category": "stairs", "title": "Stairs or step hazard", "explanation": "Steps can increase fall risk if edges are hard to see or the area is dim.", "recommendation": "Keep stairs clear, improve lighting, and make step edges easy to see."},
            {"category": "handrail", "title": "Handrail should be checked", "explanation": "A missing, loose, or hard-to-grip handrail can make stairs less safe.", "recommendation": "Make sure the handrail is secure and easy to grip."},
        ]
    elif room == "garage":
        hazards = [
            {"category": "clutter", "title": "Garage floor clutter", "explanation": "Tools, boxes, or stored items can block walking paths.", "recommendation": "Move stored items off the floor and keep a clear walkway."},
            {"category": "uneven_floor", "title": "Possible uneven garage floor", "explanation": "Garage floors may have cracks or uneven surfaces.", "recommendation": "Mark or repair uneven areas and keep the walking path clear."},
        ]
    elif room == "home office":
        hazards = [
            {"category": "cords", "title": "Office cord hazard", "explanation": "Computer or charger cords can create tripping hazards.", "recommendation": "Route cords along the wall or secure them with a cord cover."},
            {"category": "open_drawers_cabinets", "title": "Open drawer or cabinet", "explanation": "Open drawers or cabinet doors can block walking space.", "recommendation": "Keep drawers and cabinets closed when not in use."},
        ]

    for hazard in hazards:
        hazard["priority"] = get_priority_for_hazard(hazard)

    return {
        "summary": "Sample AI-style result. Use real AI mode later for actual photo analysis.",
        "hazards": hazards,
        "not_visible": ["Some hazards may be outside the camera view.", "Floor slipperiness cannot be fully confirmed from one photo."],
        "safety_reminder": "AI may miss hazards. Human review is recommended.",
    }


def analyze_photo(uploaded_file: Any, room_type: str) -> Dict[str, Any]:
    if project_analyze_photo is None:
        return get_fake_analysis(room_type)
    try:
        return project_analyze_photo(uploaded_file, room_type)
    except Exception as error:
        fallback = get_fake_analysis(room_type)
        fallback["summary"] = f"Photo analysis failed, so sample results are shown instead. Error: {error}"
        return fallback


def validate_uploaded_photo(uploaded_file: Any) -> tuple[bool, str]:
    if uploaded_file is None:
        return False, "No file uploaded."
    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File is too large. Maximum size is {MAX_FILE_SIZE_MB} MB."
    return True, ""


def render_hazard_card(hazard: Dict[str, Any], number: int) -> None:
    category = hazard.get("category", "unclear")
    category_label = get_category_label(category)
    priority = hazard.get("priority") or get_priority_for_hazard(hazard)
    priority_class = get_priority_css_class(priority)
    st.markdown(
        f"""
        <div class="hazard-card">
            <div class="hazard-number">Hazard {number}</div>
            <div class="hazard-title">{safe_text(hazard.get('title', 'Possible hazard'))}</div>
            <div class="hazard-category">{safe_text(category_label)}</div>
            <div class="priority-badge {priority_class}">{safe_text(priority)}</div>
            <div class="hazard-section-label">Why it matters</div>
            <p>{safe_text(hazard.get('explanation', 'This area may need human review.'))}</p>
            <div class="hazard-section-label">Suggested fix</div>
            <p>{safe_text(hazard.get('recommendation', 'Review this area carefully.'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_recommended_first_fixes(ai_hazards: List[Dict[str, Any]], checklist_answers: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    fixes: List[Dict[str, str]] = []
    seen = set()

    for hazard in ai_hazards:
        recommendation = hazard.get("recommendation")
        if recommendation and recommendation not in seen:
            fixes.append({"text": recommendation, "priority": get_priority_for_hazard(hazard), "source": hazard.get("title", "AI hazard")})
            seen.add(recommendation)

    for answer in checklist_answers:
        if answer.get("answer") in ["yes", "not_sure"]:
            category = answer.get("category")
            recommendation = GENERIC_RECOMMENDATIONS.get(category)
            priority = PRIORITY_WATCH_REVIEW if answer.get("answer") == "not_sure" else get_priority_for_category(category)
            if recommendation and recommendation not in seen:
                fixes.append({"text": recommendation, "priority": priority, "source": answer.get("question", "Checklist concern")})
                seen.add(recommendation)

    return sort_by_priority(fixes)[:8]


def build_report_text() -> str:
    room_type = st.session_state.get("room_type", "Room")
    room_id = st.session_state.get("current_room_id") or "No Room ID"
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])
    score = st.session_state.get("score", 0)
    risk_level = st.session_state.get("risk_level", "Low Risk")
    fixes = get_recommended_first_fixes(hazards, checklist_answers)

    hazard_lines = []
    if hazards:
        for index, hazard in enumerate(hazards, start=1):
            hazard_lines.append(
                f"{index}. [{get_priority_for_hazard(hazard)}] {hazard.get('title', 'Possible hazard')}\n"
                f"   Why it matters: {hazard.get('explanation', '')}\n"
                f"   Suggested fix: {hazard.get('recommendation', '')}"
            )
    else:
        hazard_lines.append("No possible AI hazards were listed.")

    checklist_lines = []
    for answer in checklist_answers:
        if answer.get("answer") in ["yes", "not_sure"] or answer.get("answer_label") == "Skipped":
            checklist_lines.append(f"- {answer.get('question')} Answer: {answer.get('answer_label')}")
    if not checklist_lines:
        checklist_lines.append("No checklist concerns were marked Yes or Not sure.")

    fix_lines = []
    if fixes:
        for index, fix in enumerate(fixes, start=1):
            fix_lines.append(f"{index}. [{fix.get('priority')}] {fix.get('text')}\n   Source: {fix.get('source')}")
    else:
        fix_lines.append("No specific fixes were generated.")

    return f"""
AI SafeHome Safety Report
Date: {date.today().strftime('%B %d, %Y')}

Room Checked:
{room_type}

Room ID:
{room_id}

Fall-Hazard Score:
{risk_level} — {score}/100

Possible Hazards Found by AI:
{chr(10).join(hazard_lines)}

Checklist Concerns:
{chr(10).join(checklist_lines)}

Recommended First Fixes:
{chr(10).join(fix_lines)}

Safety Disclaimer:
{SAFETY_DISCLAIMER}

Human Review Reminder:
AI may miss hazards or misunderstand a photo. Please review the room yourself and consider asking a qualified professional for serious safety concerns.

Privacy Reminder:
This app should be tested with staged, non-patient photos only. Do not upload faces, names, addresses, mail, bills, medication bottles, or medical documents.
""".strip()


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
    st.session_state["current_check_saved"] = False
    st.session_state["database_save_complete"] = False
    st.session_state["database_save_id"] = None
    st.session_state["current_room_id"] = None
    st.session_state["current_home_room_id"] = None


# -----------------------------------------------------------------------------
# Home ID UI helpers
# -----------------------------------------------------------------------------


def clean_home_id_input(home_id: Optional[str]) -> str:
    if not home_id:
        return ""
    return str(home_id).strip().upper()


def generate_home_id() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "HOME-" + "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3))


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
        st.session_state["home_login_error"] = "Invalid Home ID. Use a code like HOME-8K2M-Q9PA-W4ZT."
        st.session_state["home_login_message"] = None
        return False
    try:
        exists = home_id_exists(cleaned)
    except Exception as error:
        st.session_state["home_login_error"] = "Could not check this Home ID. Check your database connection."
        st.session_state["home_login_message"] = str(error)
        return False
    if not exists:
        st.session_state["home_login_error"] = "No saved Home ID was found with that code. Create it first or check your spelling."
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
        st.session_state["home_login_error"] = "Invalid Home ID. Use the format HOME-ABCD-1234-WXYZ."
        return False
    try:
        if not is_home_id_available(cleaned):
            st.session_state["home_login_error"] = "That Home ID is already taken. Choose a different one."
            return False
        created = create_home_id(cleaned)
        st.session_state["home_id"] = created
        st.session_state["last_created_home_id"] = created
        st.session_state["home_login_error"] = None
        st.session_state["home_login_message"] = "Custom Home ID created."
        return True
    except Exception as error:
        st.session_state["home_login_error"] = "Could not create this Home ID. Check your database connection."
        st.session_state["home_login_message"] = str(error)
        return False


def show_home_id_status(key_suffix: str = "main") -> None:
    home_id = get_logged_in_home_id()
    if home_id:
        st.success(f"Logged in with Home ID: {home_id}")
        st.caption("Save this Home ID somewhere safe. Anyone with this code can view checks saved under it.")
        if st.button("Log Out of Home ID", key=f"log_out_home_id_{key_suffix}"):
            log_out_home_id()
            st.rerun()
    else:
        st.info("No Home ID is logged in yet.")


def show_home_id_login_box(key_prefix: str = "home_id") -> None:
    st.subheader("Home ID Login")
    st.write("Use an anonymous Home ID to save and view checks for one home. Do not use a name or address.")
    st.warning("A Home ID is not a password. Anyone with the Home ID can view checks saved under it.")
    st.caption(get_database_status_message())

    if not is_database_enabled():
        st.info("Database saving is disabled. Enable DATABASE_ENABLED=true before creating or using Home IDs.")
        return

    if st.session_state.get("home_login_error"):
        st.error(st.session_state["home_login_error"])
    if st.session_state.get("home_login_message"):
        st.info(st.session_state["home_login_message"])

    tab1, tab2, tab3 = st.tabs(["Create Random ID", "Choose Custom ID", "Log In Existing ID"])
    with tab1:
        if st.button("Create Random Home ID", key=f"{key_prefix}_random", type="primary"):
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
        custom = st.text_input("Choose a Home ID", placeholder="HOME-SAFE-2026-DEMO", key=f"{key_prefix}_custom")
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
        if st.button("Create This Home ID", key=f"{key_prefix}_create_custom", type="primary"):
            if create_custom_home_id(custom):
                st.success(f"Created Home ID: {st.session_state['home_id']}")
                st.rerun()
    with tab3:
        existing = st.text_input("Enter existing Home ID", placeholder="HOME-8K2M-Q9PA-W4ZT", key=f"{key_prefix}_existing")
        if st.button("Log In with Home ID", key=f"{key_prefix}_login", type="primary"):
            if log_in_with_home_id(existing):
                st.success("Home ID login successful.")
                st.rerun()


def show_current_home_and_room_status() -> None:
    home_id = st.session_state.get("home_id")
    room_id = st.session_state.get("current_room_id")
    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Home ID:</strong> {safe_text(home_id or 'Not selected')}<br>
            <strong>Room ID:</strong> {safe_text(room_id or 'Not selected')}
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Email helpers
# -----------------------------------------------------------------------------


def shorten_email_body(text: str, max_length: int = 4500) -> str:
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n\n[Summary shortened for email draft. Use the copy box for the full text.]"


def create_mailto_link(to_email: str, subject: str, body: str) -> str:
    """
    Creates a mailto link that opens the user's email app.

    Uses %20 instead of + for spaces because some email apps show + signs literally.
    """

    clean_to_email = str(to_email or "").strip()
    clean_subject = str(subject or "").strip()
    clean_body = shorten_email_body(str(body or ""))

    encoded_to_email = urllib.parse.quote(clean_to_email, safe="@.,;:+-_")
    encoded_subject = urllib.parse.quote(clean_subject, safe="")
    encoded_body = urllib.parse.quote(clean_body, safe="")

    return f"mailto:{encoded_to_email}?subject={encoded_subject}&body={encoded_body}"

def build_email_footer() -> str:
    return """
---
AI SafeHome Reminder:
This summary is educational and does not diagnose medical risk, predict individual fall risk, or guarantee fall prevention.
AI may miss hazards. Human review is recommended.
Uploaded photos are not included in this email.
""".strip()


def show_email_summary_panel(
    summary_title: str,
    summary_text: str,
    default_subject: str,
    key_prefix: str,
) -> None:
    """
    Shows server-side email sending with mailto fallback.

    Server-side email:
    - sends through Brevo API
    - does not store recipient email
    - does not attach photos

    Mailto fallback:
    - opens user's own email app
    """

    with st.expander("Email this summary"):
        st.warning(
            "Only send privacy-safe summaries. Do not include names, addresses, "
            "medical history, medication lists, faces, mail, bills, medication bottles, "
            "or medical documents."
        )

        st.caption(get_email_status_message())

        recipient = st.text_input(
            "Recipient email",
            placeholder="example@email.com",
            key=f"{key_prefix}_recipient",
        )

        subject = st.text_input(
            "Email subject",
            value=default_subject,
            key=f"{key_prefix}_subject",
        )

        body = f"{summary_title}\n\n{summary_text}\n\n{build_email_footer()}".strip()

        st.text_area(
            "Email body preview",
            value=body,
            height=300,
            key=f"{key_prefix}_body",
        )

        privacy_confirmed = st.checkbox(
            "I confirm this email contains no personal, medical, or real patient information.",
            key=f"{key_prefix}_privacy_confirmed",
        )

        if is_email_enabled():
            if st.button(
                "Send Email from AI SafeHome",
                key=f"{key_prefix}_server_send",
                type="primary",
            ):
                if not privacy_confirmed:
                    st.error(
                        "Confirm the privacy checkbox before sending."
                    )
                    return

                try:
                    message_id = send_summary_email(
                        recipient_email=recipient,
                        subject=subject,
                        text_body=body,
                    )

                    st.success(
                        "Email sent. Uploaded photos were not included."
                    )

                    st.caption(f"Email provider message ID: {message_id}")

                except Exception as error:
                    st.error(
                        "Could not send the email. You can still use the email draft backup below."
                    )

                    with st.expander("Technical details"):
                        st.code(str(error))
        else:
            st.info(
                "Server-side email is disabled. Use the email draft backup below."
            )

        st.divider()

        st.write("Backup option: open an email draft")

        link = create_mailto_link(recipient, subject, body)

        st.markdown(
            f'<a href="{html.escape(link, quote=True)}" target="_blank" class="email-link-button">Open Email Draft</a>',
            unsafe_allow_html=True,
        )

        st.caption(
            "If the draft does not open, copy the email body above and paste it into your email app."
        )

def safe_filename_part(value: Any) -> str:
    """
    Converts text into a safe filename part.

    Example: BEDROOM-1 stays BEDROOM-1.
    """

    cleaned = str(value or "summary").strip().upper()
    cleaned = re.sub(r"[^A-Z0-9-]+", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "SUMMARY"


def show_share_summary_panel(
    summary_title: str,
    summary_text: str,
    file_name: str,
    key_prefix: str,
) -> None:
    """
    Shows privacy-safe sharing options for report/stat text.

    This does not create a public link and does not expose the Home ID.
    """

    with st.expander("Share / export this summary"):
        st.warning(
            "Share only with people who should see this summary. "
            "Do not add names, addresses, medical history, medication lists, faces, "
            "mail, bills, medication bottles, or medical documents."
        )

        st.caption(
            "This does not create a public web link. It only lets you copy or download "
            "the summary text from this browser session."
        )

        export_text = f"{summary_title}\n\n{summary_text}\n\n{build_email_footer()}".strip()

        st.download_button(
            label="Download Shareable Text File",
            data=export_text,
            file_name=file_name,
            mime="text/plain",
            key=f"{key_prefix}_download",
        )

        st.text_area(
            "Copyable share text",
            value=export_text,
            height=300,
            key=f"{key_prefix}_copy_text",
        )

        st.info(
            "For a quick phone share: download the text file, or copy the text above "
            "and paste it into Messages, email, or a document."
        )


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

    with st.expander("Database privacy notice"):
        st.write("If database saving is enabled, AI SafeHome saves anonymous room-check results only.")
        st.write("It does not save uploaded photos, names, addresses, medical history, medications, faces, mail, bills, or medical documents.")


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

    st.markdown(f'<div class="plain-card"><strong>Selected room type:</strong> {safe_text(room_type)}</div>', unsafe_allow_html=True)
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
        if st.button("Continue Without Room ID"):
            st.session_state["current_room_id"] = None
            st.session_state["current_home_room_id"] = None
            go_to_page("photo_upload")
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
            selected = st.selectbox("Choose existing Room ID", list(room_options.keys()), key="existing_room_id_select")
            if st.button("Use This Room ID →", type="primary"):
                selected_room = room_options[selected]
                st.session_state["current_room_id"] = selected_room["room_id"]
                st.session_state["current_home_room_id"] = selected_room["id"]
                go_to_page("photo_upload")
    with tab2:
        st.caption("Use IDs like BEDROOM-1, BEDROOM-2, BATHROOM-1. Do not use names or addresses.")
        new_room_id = st.text_input("New Room ID", value=suggested_room_id, key="new_room_id_input")
        if st.button("Create and Use This Room ID →", type="primary"):
            try:
                created_room = create_home_room(home_id=home_id, room_id=new_room_id, room_type=room_type)
                st.session_state["current_room_id"] = created_room["room_id"]
                st.session_state["current_home_room_id"] = created_room["id"]
                go_to_page("photo_upload")
            except Exception as error:
                st.error("Could not create that Room ID. It may already exist or have an invalid format.")
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

    st.markdown(f'<div class="plain-card"><strong>Room checked:</strong> {safe_text(room_type)}</div>', unsafe_allow_html=True)
    show_current_home_and_room_status()
    st.warning(PHOTO_UPLOAD_PRIVACY_WARNING)
    st.info(PHOTO_NOT_STORED_NOTE)

    uploaded_file = st.file_uploader("Upload or take a room photo", type=ALLOWED_FILE_TYPES, help="On iPhone, this may let you choose Photo Library or Take Photo.")

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
    else:
        st.session_state["photo_uploaded"] = False
        st.info("Upload a JPG, JPEG, PNG, or WEBP photo smaller than 5 MB.")

    if st.button("← Back"):
        go_to_page("room_id_selection")


def show_ai_results_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 3: Possible Hazards Found")
    show_step_card("Step 3 of 6 — Review possible hazards found by the AI/sample analysis.")

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    st.write(ai_result.get("summary", "The photo was reviewed for possible visible hazards."))

    if not hazards:
        st.success("No obvious hazards were listed by the analysis.")
    else:
        for index, hazard in enumerate(hazards, start=1):
            render_hazard_card(hazard, index)

    not_visible = ai_result.get("not_visible", [])
    if not_visible:
        with st.expander("Things the photo may not show"):
            for item in not_visible:
                st.write(f"- {item}")

    st.warning(ai_result.get("safety_reminder", "AI may miss hazards. Human review is recommended."))

    if st.button("Continue to Checklist →", type="primary"):
        reset_checklist_progress()
        go_to_page("checklist")

    if st.button("Skip Checklist and Score AI Only"):
        st.session_state["checklist_answers"] = []
        st.session_state["checklist_was_skipped"] = True
        go_to_page("checklist_summary")

    if st.button("← Back to Photo Upload"):
        go_to_page("photo_upload")



def save_checklist_answer(question: Dict[str, Any], answer_label: str) -> None:
    st.session_state["checklist_answers_by_id"][question["id"]] = {
        "id": question["id"],
        "category": question["category"],
        "question": question["text"],
        "answer": ANSWER_VALUE_MAP.get(answer_label, "not_applicable"),
        "answer_label": answer_label,
    }


def skip_checklist_question(question: Dict[str, Any]) -> None:
    st.session_state["checklist_answers_by_id"][question["id"]] = {
        "id": question["id"],
        "category": question["category"],
        "question": question["text"],
        "answer": "not_applicable",
        "answer_label": "Skipped",
    }


def build_ordered_checklist_answers() -> List[Dict[str, Any]]:
    return [st.session_state["checklist_answers_by_id"][q["id"]] for q in CHECKLIST_QUESTIONS if q["id"] in st.session_state["checklist_answers_by_id"]]


def finish_checklist() -> None:
    st.session_state["checklist_answers"] = build_ordered_checklist_answers()
    go_to_page("checklist_summary")


def show_checklist_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 4: Safety Checklist")
    show_step_card("Step 4 of 6 — Answer one checklist question at a time, or skip if needed.")
    st.info("The checklist helps catch hazards the photo analysis may miss. You may skip individual questions or skip the checklist entirely.")

    total = len(CHECKLIST_QUESTIONS)
    index = st.session_state.get("checklist_index", 0)
    if index >= total:
        finish_checklist()
        return

    question = CHECKLIST_QUESTIONS[index]
    number = index + 1
    st.progress(number / total)
    st.caption(f"Question {number} of {total}")
    st.markdown(f'<div class="checklist-card"><strong>{safe_text(question["text"])}</strong></div>', unsafe_allow_html=True)

    saved = st.session_state["checklist_answers_by_id"].get(question["id"])
    default_index = 0
    if saved and saved.get("answer_label") in ANSWER_OPTIONS:
        default_index = ANSWER_OPTIONS.index(saved["answer_label"])

    selected = st.radio("Choose an answer", ANSWER_OPTIONS, index=default_index, key=f"checklist_{question['id']}_{index}")

    if st.button("Save & Finish" if number == total else "Save & Next", type="primary"):
        save_checklist_answer(question, selected)
        if number == total:
            finish_checklist()
        else:
            st.session_state["checklist_index"] += 1
            st.rerun()

    if st.button("Skip This Question"):
        skip_checklist_question(question)
        if number == total:
            finish_checklist()
        else:
            st.session_state["checklist_index"] += 1
            st.rerun()

    if index > 0 and st.button("← Previous Question"):
        st.session_state["checklist_index"] -= 1
        st.rerun()

    if st.button("Skip Entire Checklist"):
        st.session_state["checklist_answers"] = []
        st.session_state["checklist_answers_by_id"] = {}
        st.session_state["checklist_index"] = 0
        st.session_state["checklist_was_skipped"] = True
        go_to_page("checklist_summary")


def calculate_and_store_score() -> None:
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])
    score = calculate_score(hazards, checklist_answers)
    st.session_state["score"] = score
    st.session_state["risk_level"] = get_risk_level(score)
    st.session_state["score_breakdown"] = get_score_breakdown(hazards, checklist_answers)
    st.session_state["current_check_saved"] = False
    st.session_state["database_save_complete"] = False
    st.session_state["database_save_id"] = None


def show_checklist_summary_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Checklist Summary")

    if st.session_state.get("checklist_was_skipped"):
        st.warning("Checklist was skipped. The risk score will be based only on AI photo hazards.")
    else:
        answers = st.session_state.get("checklist_answers", [])
        st.success(f"Checklist saved with {len(answers)} answered/skipped questions.")
        with st.expander("View checklist answers"):
            for answer in answers:
                st.write(f"- **{answer.get('question')}** — {answer.get('answer_label')}")

    if st.button("Calculate Risk Score →", type="primary"):
        calculate_and_store_score()
        go_to_page("risk_score")

    if st.button("Edit Checklist"):
        st.session_state["checklist_index"] = 0
        go_to_page("checklist")


def get_current_database_save_payload() -> Dict[str, Any]:
    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])
    return {
        "room_type": st.session_state.get("room_type"),
        "room_id": st.session_state.get("current_room_id"),
        "score": st.session_state.get("score"),
        "risk_level": st.session_state.get("risk_level"),
        "hazards": hazards,
        "checklist_answers": checklist_answers,
        "recommended_fixes": get_recommended_first_fixes(hazards, checklist_answers),
        "checklist_was_skipped": st.session_state.get("checklist_was_skipped", False),
        "using_demo_sample": False,
        "demo_sample_name": None,
    }


def show_database_save_panel() -> None:
    st.subheader("Save Anonymous Result")
    st.caption(get_database_status_message())

    if not is_database_enabled():
        st.info("Database saving is currently disabled. The app still works normally without saving results.")
        return

    if st.session_state.get("score") is None:
        st.warning("Calculate a risk score before saving a result.")
        return

    home_id = get_logged_in_home_id()
    if not home_id:
        st.warning("Create or enter a Home ID before saving.")
        show_home_id_login_box(key_prefix="save_panel_home_id")
        return

    show_home_id_status(key_suffix="save_panel")

    room_id = st.session_state.get("current_room_id")
    if not room_id:
        st.warning("Choose or create a Room ID before saving. This prevents confusing rooms like BEDROOM-1 and BEDROOM-2.")
        if st.button("Choose Room ID"):
            go_to_page("room_id_selection")
        return

    st.success(f"Saving under Room ID: {room_id}")

    if st.session_state.get("database_save_complete"):
        st.success("This room check has already been saved anonymously. No photo or personal information was stored.")
        if st.session_state.get("database_save_id"):
            st.caption(f"Saved Check ID: {st.session_state['database_save_id']}")
        return

    st.warning("This saves anonymous room-check results only. Uploaded photos are not stored.")
    confirmed = st.checkbox("I confirm this result contains no personal, medical, or real patient information.", key="database_safety_confirmed")

    if st.button("Save Anonymous Result", type="primary"):
        if not confirmed:
            st.error("Please confirm the result is anonymous before saving.")
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
                safety_confirmed=confirmed,
                using_demo_sample=payload["using_demo_sample"],
                demo_sample_name=payload["demo_sample_name"],
                room_id=payload["room_id"],
            )
            st.session_state["database_save_complete"] = True
            st.session_state["database_save_id"] = saved_id
            st.success("Anonymous room check saved. No photo or personal information was stored.")
        except Exception as error:
            st.error("Could not save this result. The app still works, but this check was not stored.")
            with st.expander("Technical details"):
                st.code(str(error))

    if st.button("View Saved Checks by Home ID"):
        go_to_page("saved_results")
    if st.button("View Room-by-Room Stats"):
        go_to_page("room_stats")


def show_risk_score_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 5: Fall-Hazard Score")
    show_step_card("Step 5 of 6 — Review the score, risk label, and first fixes.")

    score = st.session_state.get("score")
    risk_level = st.session_state.get("risk_level")
    if score is None or risk_level is None:
        st.error("No score calculated yet.")
        if st.button("Return to Checklist"):
            go_to_page("checklist")
        return

    st.metric("Risk Score", f"{score}/100")
    st.progress(score)
    if risk_level == "Low Risk":
        st.success(risk_level)
    elif risk_level == "Moderate Risk":
        st.warning(risk_level)
    else:
        st.error(risk_level)

    breakdown = st.session_state.get("score_breakdown") or {}
    with st.expander("View score breakdown"):
        st.write(f"AI hazard points: **{breakdown.get('ai_points', 0)}**")
        st.write(f"Checklist points: **{breakdown.get('checklist_points', 0)}**")
        st.write(f"Total before cap: **{breakdown.get('total_before_cap', 0)}**")

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    checklist_answers = st.session_state.get("checklist_answers", [])
    fixes = get_recommended_first_fixes(hazards, checklist_answers)

    st.subheader("Recommended First Fixes")
    if not fixes:
        st.write("No specific fixes were generated.")
    else:
        for index, fix in enumerate(fixes, start=1):
            priority = fix.get("priority", PRIORITY_WATCH_REVIEW)
            priority_class = get_priority_css_class(priority)
            st.markdown(
                f"""
                <div class="plain-card">
                    <strong>{index}. {safe_text(fix.get('text'))}</strong><br>
                    <div class="priority-badge {priority_class}">{safe_text(priority)}</div><br>
                    <span class="small-muted">Source: {safe_text(fix.get('source'))}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.warning("AI may miss hazards. Please review the room yourself and consider asking a qualified professional for serious safety concerns.")
    st.divider()
    show_database_save_panel()

    if st.button("Create Safety Report →", type="primary"):
        st.session_state["report_text"] = build_report_text()
        go_to_page("safety_report")

    if st.button("Edit Checklist"):
        go_to_page("checklist")


def get_report_file_name() -> str:
    room_type = st.session_state.get("room_type") or "room"
    room_id = st.session_state.get("current_room_id") or room_type
    safe_name = str(room_id).lower().replace(" ", "_").replace("/", "_")
    return f"ai_safehome_{safe_name}_safety_report.txt"


def show_safety_report_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Step 6: Safety Report")
    show_step_card("Step 6 of 6 — Review, download, print, or email the report.")

    report_text = st.session_state.get("report_text") or build_report_text()
    st.session_state["report_text"] = report_text

    st.markdown(f'<div class="print-report">{safe_text(report_text)}</div>', unsafe_allow_html=True)
    st.download_button("Download Report as Text File", data=report_text, file_name=get_report_file_name(), mime="text/plain", type="primary")
    show_email_summary_panel("AI SafeHome One-Room Safety Report", report_text, f"AI SafeHome Safety Report - {st.session_state.get('current_room_id') or st.session_state.get('room_type')}", "one_room_report_email")

    st.divider()
    show_database_save_panel()

    if st.button("Start Another Room"):
        reset_current_room_check()
        go_to_page("room_selection")
    if st.button("← Back to Risk Score"):
        go_to_page("risk_score")


def show_saved_results_metrics(stats: Dict[str, Any]) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Saved Checks", stats.get("total_checks", 0))
    with col2:
        st.metric("Average Score", f"{stats.get('average_score', 0)}/100")
    with col3:
        st.metric("High Risk Rooms", stats.get("high_risk_count", 0))
    with col4:
        st.metric("Most Common Room", stats.get("most_common_room") or "None")


def show_saved_results_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Saved Checks by Home ID")
    st.caption(get_database_status_message())
    st.warning("This page shows anonymous checks only for the entered Home ID. It does not show all database checks.")

    if not is_database_enabled():
        st.info("Database saving is disabled. Enable DATABASE_ENABLED=true to view saved checks.")
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
        st.error("Could not load checks for this Home ID.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    show_saved_results_metrics(stats)
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
                    Check ID: {safe_text(row.get('id'))}<br>
                    Room: {safe_text(row.get('room_type'))}<br>
                    Room ID: {safe_text(row.get('room_id') or 'No Room ID')}<br>
                    Score: {safe_text(row.get('score'))}/100<br>
                    Risk Label: {safe_text(row.get('risk_level'))}<br>
                    AI Mode: {safe_text(row.get('ai_mode'))}<br>
                    Hazards Saved: {safe_text(row.get('hazard_count'))}<br>
                    Saved At: {safe_text(format_database_datetime(row.get('created_at')))}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Look Up One Check by Check ID")
    check_id = st.text_input("Enter Check ID", placeholder="Paste a saved room_check UUID here")
    if st.button("Find Check by ID"):
        if not check_id.strip():
            st.error("Enter a Check ID first.")
        else:
            try:
                check = fetch_room_check_by_id(check_id=check_id, home_id=home_id)
                if not check:
                    st.error("No check found for that Check ID under this Home ID.")
                else:
                    details = fetch_room_check_details(check["id"])
                    st.success("Check found.")
                    st.markdown(
                        f"""
                        <div class="plain-card">
                            <strong>Check ID:</strong> {safe_text(check.get('id'))}<br>
                            Room: {safe_text(check.get('room_type'))}<br>
                            Room ID: {safe_text(check.get('room_id') or 'No Room ID')}<br>
                            Score: {safe_text(check.get('score'))}/100<br>
                            Risk Label: {safe_text(check.get('risk_level'))}<br>
                            Saved At: {safe_text(format_database_datetime(check.get('created_at')))}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("View check details"):
                        for detail in details:
                            if detail.get("detail_type") == "ai_hazard":
                                st.write(f"- Hazard: {detail.get('title')} ({detail.get('category')})")
                            elif detail.get("detail_type") == "checklist_answer":
                                st.write(f"- Checklist: {detail.get('checklist_question')} → {detail.get('checklist_answer')}")
                            elif detail.get("detail_type") == "recommended_fix":
                                st.write(f"- Fix: {detail.get('recommendation')}")
            except Exception as error:
                st.error("Could not look up that Check ID.")
                with st.expander("Technical details"):
                    st.code(str(error))

    if st.button("View Room-by-Room Stats"):
        go_to_page("room_stats")
    if st.button("Start New Safety Check"):
        reset_current_room_check()
        go_to_page("room_selection")


def show_room_stats_overview(room_stats_list: List[Dict[str, Any]]) -> None:
    total_rooms = len(room_stats_list)
    active_rooms = sum(1 for room in room_stats_list if room.get("check_count", 0) > 0)
    total_checks = sum(room.get("check_count", 0) for room in room_stats_list)
    avg_score = 0
    if total_checks:
        avg_score = round(sum(room.get("average_score", 0) * room.get("check_count", 0) for room in room_stats_list) / total_checks)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rooms Created", total_rooms)
    col2.metric("Rooms With Checks", active_rooms)
    col3.metric("Total Checks", total_checks)
    col4.metric("Home Avg Score", f"{avg_score}/100")


def format_score_value(value: Any) -> str:
    """
    Formats a score safely for email/export text.
    """

    if value is None:
        return "No saved score yet"

    return f"{value}/100"


def build_room_stats_email_text(room_stats: Dict[str, Any]) -> str:
    """
    Builds a plain-text summary for one room's saved stats.

    This is used for email drafts and export/copy text.
    It does not include Home ID, photos, names, addresses, or medical info.
    """

    hazard_counts = room_stats.get("hazard_counts", {})
    checklist_counts = room_stats.get("checklist_answer_counts", {})

    hazard_lines = [
        f"- {get_category_label(category)}: {count}"
        for category, count in sorted(
            hazard_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    if not hazard_lines:
        hazard_lines = ["- No saved hazards yet."]

    checklist_lines = [
        f"- {answer}: {count}"
        for answer, count in sorted(checklist_counts.items())
    ]

    if not checklist_lines:
        checklist_lines = ["- No saved checklist answers yet."]

    return f"""
Room ID:
{room_stats.get("room_id") or "Unknown Room ID"}

Room Type:
{room_stats.get("room_type") or "Unknown Room Type"}

Checks Saved:
{room_stats.get("check_count", 0)}

Average Score:
{format_score_value(room_stats.get("average_score"))}

Latest Score:
{format_score_value(room_stats.get("latest_score"))}

Highest Score:
{format_score_value(room_stats.get("highest_score"))}

Lowest Score:
{format_score_value(room_stats.get("lowest_score"))}

Latest Risk Label:
{room_stats.get("latest_risk_level") or "No saved risk label yet"}

Latest Check:
{format_database_datetime(room_stats.get("latest_created_at"))}

Risk Label Counts:
Low Risk: {room_stats.get("low_risk_count", 0)}
Moderate Risk: {room_stats.get("moderate_risk_count", 0)}
High Risk: {room_stats.get("high_risk_count", 0)}

Most Common Hazards:
{chr(10).join(hazard_lines)}

Checklist Answer Summary:
{chr(10).join(checklist_lines)}
""".strip()


def build_all_room_stats_csv(room_stats_list: List[Dict[str, Any]]) -> str:
    """
    Builds a CSV export for all rooms under the logged-in Home ID.

    This does not include the Home ID or uploaded photos.
    """

    output = io.StringIO()

    fieldnames = [
        "room_id",
        "room_type",
        "check_count",
        "average_score",
        "latest_score",
        "highest_score",
        "lowest_score",
        "latest_risk_level",
        "latest_created_at",
        "low_risk_count",
        "moderate_risk_count",
        "high_risk_count",
        "top_hazard",
        "recommended_fix_count",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for room in room_stats_list:
        writer.writerow(
            {
                "room_id": room.get("room_id"),
                "room_type": room.get("room_type"),
                "check_count": room.get("check_count", 0),
                "average_score": room.get("average_score", 0),
                "latest_score": room.get("latest_score"),
                "highest_score": room.get("highest_score"),
                "lowest_score": room.get("lowest_score"),
                "latest_risk_level": room.get("latest_risk_level"),
                "latest_created_at": format_database_datetime(room.get("latest_created_at")),
                "low_risk_count": room.get("low_risk_count", 0),
                "moderate_risk_count": room.get("moderate_risk_count", 0),
                "high_risk_count": room.get("high_risk_count", 0),
                "top_hazard": room.get("top_hazard"),
                "recommended_fix_count": room.get("recommended_fix_count", 0),
            }
        )

    return output.getvalue()


def show_all_room_stats_csv_export(room_stats_list: List[Dict[str, Any]]) -> None:
    """
    Shows a CSV export for all room stats on the stats page.
    """

    with st.expander("Export all room stats as CSV"):
        st.warning(
            "This CSV does not include Home ID, uploaded photos, names, addresses, "
            "medical history, medication lists, faces, mail, bills, or medical documents."
        )

        st.download_button(
            label="Download All Room Stats (.csv)",
            data=build_all_room_stats_csv(room_stats_list),
            file_name="ai_safehome_all_room_stats.csv",
            mime="text/csv",
            key="all_room_stats_csv_download",
        )

def get_check_display_label(check_row: Dict[str, Any]) -> str:
    """
    Creates a readable label for a saved room check.
    """

    created_at = format_database_datetime(check_row.get("created_at"))
    score = check_row.get("score", "None")
    risk_level = check_row.get("risk_level", "Unknown Risk")
    check_id = str(check_row.get("id", ""))[:8]

    return f"{created_at} — {score}/100 — {risk_level} — {check_id}"


def sort_checks_oldest_to_newest(check_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts saved checks from oldest to newest.
    Supabase timestamps sort correctly as strings.
    """

    return sorted(
        check_rows,
        key=lambda row: str(row.get("created_at") or ""),
    )


def get_hazard_categories_from_details(detail_rows: List[Dict[str, Any]]) -> set:
    """
    Extracts hazard categories from detail rows for one saved check.
    """

    categories = set()

    for detail in detail_rows:
        if detail.get("detail_type") == "ai_hazard":
            category = detail.get("category") or "unclear"
            categories.add(category)

    return categories


def get_hazard_titles_by_category(detail_rows: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Groups hazard titles by category.
    """

    grouped: Dict[str, List[str]] = {}

    for detail in detail_rows:
        if detail.get("detail_type") != "ai_hazard":
            continue

        category = detail.get("category") or "unclear"
        title = detail.get("title") or get_category_label(category)

        if category not in grouped:
            grouped[category] = []

        grouped[category].append(title)

    return grouped


def get_score_change_message(before_score: Any, after_score: Any) -> tuple[str, str]:
    """
    Returns a plain-English score comparison message.
    Lower score is better because it means fewer hazard points.
    """

    if before_score is None or after_score is None:
        return "Not enough score data.", "info"

    before_score = int(before_score)
    after_score = int(after_score)

    change = after_score - before_score

    if change < 0:
        return f"Improved by {abs(change)} points.", "success"

    if change > 0:
        return f"Score increased by {change} points. Review this room again.", "warning"

    return "No score change.", "info"


def show_hazard_category_list(title: str, categories: set) -> None:
    """
    Shows a small list of hazard categories.
    """

    st.write(f"**{title}**")

    if not categories:
        st.write("- None")
        return

    for category in sorted(categories):
        st.write(f"- {get_category_label(category)}")


def show_before_after_hazard_titles(
    label: str,
    categories: set,
    titles_by_category: Dict[str, List[str]],
) -> None:
    """
    Shows hazard titles for selected categories.
    """

    with st.expander(label):
        if not categories:
            st.write("None")
            return

        for category in sorted(categories):
            st.write(f"**{get_category_label(category)}**")

            titles = titles_by_category.get(category, [])

            if not titles:
                st.write("- No saved title")
            else:
                for title in titles:
                    st.write(f"- {title}")


def show_before_after_room_comparison(home_id: str, room_id: str) -> None:
    """
    Shows before/after comparison for one Room ID.

    Compares the first saved check and latest saved check by default.
    Also lets the user choose two checks manually.
    """

    st.subheader("Before / After Room Comparison")

    st.caption(
        "Lower scores are better. This compares saved checks for the same Room ID."
    )

    try:
        check_rows = fetch_room_checks_by_room_id(
            home_id=home_id,
            room_id=room_id,
            limit=100,
        )

    except Exception as error:
        st.error("Could not load saved checks for before/after comparison.")

        with st.expander("Technical details"):
            st.code(str(error))

        return

    if len(check_rows) < 2:
        st.info(
            "This room needs at least two saved checks before a before/after comparison can be shown."
        )
        return

    sorted_checks = sort_checks_oldest_to_newest(check_rows)

    first_check = sorted_checks[0]
    latest_check = sorted_checks[-1]

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Default comparison:</strong><br>
            Before = first saved check<br>
            After = latest saved check
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Choose different checks to compare"):
        check_options = {
            get_check_display_label(row): row
            for row in sorted_checks
        }

        before_label = st.selectbox(
            "Before check",
            list(check_options.keys()),
            index=0,
            key=f"{room_id}_before_check_select",
        )

        after_label = st.selectbox(
            "After check",
            list(check_options.keys()),
            index=len(check_options) - 1,
            key=f"{room_id}_after_check_select",
        )

        first_check = check_options[before_label]
        latest_check = check_options[after_label]

    before_score = first_check.get("score")
    after_score = latest_check.get("score")

    change_message, message_type = get_score_change_message(
        before_score,
        after_score,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Before Score",
            f"{before_score}/100",
        )

    with col2:
        st.metric(
            "After Score",
            f"{after_score}/100",
        )

    with col3:
        if before_score is not None and after_score is not None:
            delta_value = int(after_score) - int(before_score)
            st.metric(
                "Score Change",
                delta_value,
                delta=f"{delta_value} points",
            )
        else:
            st.metric("Score Change", "N/A")

    if message_type == "success":
        st.success(change_message)
    elif message_type == "warning":
        st.warning(change_message)
    else:
        st.info(change_message)

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Before Check</strong><br>
            Check ID: {safe_text(first_check.get("id"))}<br>
            Saved At: {safe_text(format_database_datetime(first_check.get("created_at")))}<br>
            Risk Label: {safe_text(first_check.get("risk_level"))}<br>
            Hazards Saved: {safe_text(first_check.get("hazard_count"))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>After Check</strong><br>
            Check ID: {safe_text(latest_check.get("id"))}<br>
            Saved At: {safe_text(format_database_datetime(latest_check.get("created_at")))}<br>
            Risk Label: {safe_text(latest_check.get("risk_level"))}<br>
            Hazards Saved: {safe_text(latest_check.get("hazard_count"))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        before_details = fetch_room_check_details(first_check["id"])
        after_details = fetch_room_check_details(latest_check["id"])

    except Exception as error:
        st.error("Could not load check details for before/after comparison.")

        with st.expander("Technical details"):
            st.code(str(error))

        return

    before_categories = get_hazard_categories_from_details(before_details)
    after_categories = get_hazard_categories_from_details(after_details)

    resolved_hazards = before_categories - after_categories
    still_present_hazards = before_categories & after_categories
    new_hazards = after_categories - before_categories

    st.subheader("Hazard Changes")

    col1, col2, col3 = st.columns(3)

    with col1:
        show_hazard_category_list("Resolved", resolved_hazards)

    with col2:
        show_hazard_category_list("Still Present", still_present_hazards)

    with col3:
        show_hazard_category_list("New", new_hazards)

    before_titles = get_hazard_titles_by_category(before_details)
    after_titles = get_hazard_titles_by_category(after_details)

    show_before_after_hazard_titles(
        "Before check hazard titles",
        before_categories,
        before_titles,
    )

    show_before_after_hazard_titles(
        "After check hazard titles",
        after_categories,
        after_titles,
    )

    comparison_text = f"""
AI SafeHome Before / After Room Comparison

Room ID: {room_id}

Before Check:
Date: {format_database_datetime(first_check.get("created_at"))}
Score: {before_score}/100
Risk Label: {first_check.get("risk_level")}

After Check:
Date: {format_database_datetime(latest_check.get("created_at"))}
Score: {after_score}/100
Risk Label: {latest_check.get("risk_level")}

Result:
{change_message}

Resolved Hazards:
{chr(10).join("- " + get_category_label(category) for category in sorted(resolved_hazards)) if resolved_hazards else "- None"}

Still Present Hazards:
{chr(10).join("- " + get_category_label(category) for category in sorted(still_present_hazards)) if still_present_hazards else "- None"}

New Hazards:
{chr(10).join("- " + get_category_label(category) for category in sorted(new_hazards)) if new_hazards else "- None"}

Reminder:
This comparison is based on saved room-check results. AI may miss hazards. Human review is recommended.
""".strip()

    show_email_summary_panel(
        summary_title="AI SafeHome Before / After Room Comparison",
        summary_text=comparison_text,
        default_subject=f"AI SafeHome Before/After Comparison - {room_id}",
        key_prefix=f"before_after_email_{safe_filename_part(room_id)}",
    )

    show_share_summary_panel(
        summary_title="AI SafeHome Before / After Room Comparison",
        summary_text=comparison_text,
        file_name=f"ai_safehome_before_after_{safe_filename_part(room_id)}.txt",
        key_prefix=f"before_after_share_{safe_filename_part(room_id)}",
    )

def show_room_stats_page() -> None:
    st.title("🏠 AI SafeHome")
    st.subheader("Room-by-Room Stats")
    st.caption(get_database_status_message())
    st.warning("This page shows anonymous stats only for the logged-in Home ID. It does not show all database results.")

    if not is_database_enabled():
        st.info("Database saving is disabled. Enable DATABASE_ENABLED=true to view room stats.")
        return

    show_home_id_status(key_suffix="room_stats_page")
    if not get_logged_in_home_id():
        show_home_id_login_box(key_prefix="room_stats_home_id")
        return

    home_id = get_logged_in_home_id()
    try:
        room_stats_list = fetch_all_room_stats_for_home(home_id)
    except Exception as error:
        st.error("Could not load room stats for this Home ID.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    show_room_stats_overview(room_stats_list)
    st.divider()

    st.subheader("All Rooms Under This Home ID")
    if not room_stats_list:
        st.info("No rooms have been created under this Home ID yet.")
        if st.button("Start New Safety Check"):
            reset_current_room_check()
            go_to_page("room_selection")
        return

    table_rows = [
        {
            "Room ID": room.get("room_id"),
            "Room Type": room.get("room_type"),
            "Checks": room.get("check_count"),
            "Average Score": room.get("average_score"),
            "Latest Score": room.get("latest_score"),
            "Highest Score": room.get("highest_score"),
            "Latest Risk": room.get("latest_risk_level"),
            "Top Hazard": get_category_label(room.get("top_hazard")) if room.get("top_hazard") else "None",
        }
        for room in room_stats_list
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    room_options = {f"{room.get('room_id')} — {room.get('room_type')}": room.get("room_id") for room in room_stats_list}
    selected_label = st.selectbox("Choose Room ID", list(room_options.keys()))
    selected_room_id = room_options[selected_label]

    try:
        selected_stats = fetch_room_stats(home_id=home_id, room_id=selected_room_id)
    except Exception as error:
        st.error("Could not load stats for that Room ID.")
        with st.expander("Technical details"):
            st.code(str(error))
        return

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Room ID:</strong> {safe_text(selected_stats.get('room_id'))}<br>
            <strong>Room Type:</strong> {safe_text(selected_stats.get('room_type'))}<br>
            <strong>Checks Saved:</strong> {safe_text(selected_stats.get('check_count', 0))}<br>
            <strong>Average Score:</strong> {safe_text(format_score_value(selected_stats.get('average_score')))}<br>
            <strong>Latest Score:</strong> {safe_text(format_score_value(selected_stats.get('latest_score')))}<br>
            <strong>Highest Score:</strong> {safe_text(format_score_value(selected_stats.get('highest_score')))}<br>
            <strong>Lowest Score:</strong> {safe_text(format_score_value(selected_stats.get('lowest_score')))}<br>
            <strong>Latest Risk Label:</strong> {safe_text(selected_stats.get('latest_risk_level'))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Most Common Hazards")
    hazard_counts = selected_stats.get("hazard_counts", {})
    if hazard_counts:
        st.dataframe([{"Hazard Category": get_category_label(cat), "Count": count} for cat, count in sorted(hazard_counts.items(), key=lambda x: x[1], reverse=True)], use_container_width=True, hide_index=True)
    else:
        st.info("No hazards have been saved for this room yet.")

    st.subheader("Checklist Answer Summary")
    checklist_counts = selected_stats.get("checklist_answer_counts", {})
    if checklist_counts:
        st.dataframe([{"Checklist Answer": answer, "Count": count} for answer, count in sorted(checklist_counts.items())], use_container_width=True, hide_index=True)
    else:
        st.info("No checklist answers have been saved for this room yet.")

    st.subheader("Check History for This Room")
    st.divider()

    show_before_after_room_comparison(
        home_id=home_id,
        room_id=selected_room_id,
    )
    try:
        history = fetch_room_checks_by_room_id(home_id=home_id, room_id=selected_room_id, limit=100)
    except Exception as error:
        st.error("Could not load check history.")
        with st.expander("Technical details"):
            st.code(str(error))
        history = []
    if history:
        st.dataframe([{"Saved At": format_database_datetime(row.get("created_at")), "Check ID": row.get("id"), "Score": row.get("score"), "Risk Label": row.get("risk_level"), "Hazards": row.get("hazard_count"), "Checklist Skipped": row.get("checklist_was_skipped")} for row in history], use_container_width=True, hide_index=True)
    else:
        st.info("No checks have been saved for this room yet.")

    room_stats_share_text = build_room_stats_email_text(selected_stats)
    room_stats_file_name = f"ai_safehome_room_stats_{safe_filename_part(selected_room_id)}.txt"

    show_email_summary_panel(
        "AI SafeHome Room Stats Summary",
        room_stats_share_text,
        f"AI SafeHome Room Stats - {selected_room_id}",
        "room_stats_email",
    )

    show_share_summary_panel(
        "AI SafeHome Room Stats Summary",
        room_stats_share_text,
        room_stats_file_name,
        "room_stats_share",
    )

    show_all_room_stats_csv_export(room_stats_list)

    if st.button("Analyze This Room Again"):
        st.session_state["room_type"] = selected_stats.get("room_type")
        st.session_state["current_room_id"] = selected_room_id
        st.session_state["photo_uploaded"] = False
        st.session_state["ai_result"] = None
        st.session_state["score"] = None
        st.session_state["risk_level"] = None
        st.session_state["score_breakdown"] = None
        st.session_state["report_text"] = None
        st.session_state["database_save_complete"] = False
        st.session_state["database_save_id"] = None
        reset_checklist_progress()
        go_to_page("photo_upload")

    if st.button("Create or Choose Another Room"):
        go_to_page("room_selection")


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
        st.error("Unknown page. Returning to landing page.")
        st.session_state["page"] = "landing"
        st.rerun()

    st.divider()
    st.caption(SAFETY_DISCLAIMER)


if __name__ == "__main__":
    main()