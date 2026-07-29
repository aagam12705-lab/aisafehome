"""
ui.py

Reusable Streamlit UI helpers and styling for AI SafeHome.
"""

import html
import json
import re
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components

from src.constants import CATEGORY_LABELS
from src.priorities import get_priority_for_hazard


def setup_page() -> None:
    st.set_page_config(
        page_title="AI SafeHome",
        page_icon="🏠",
        layout="centered",
    )


def add_mobile_friendly_style() -> None:
    text_size = st.session_state.get("text_size", "Standard")
    color_scheme = st.session_state.get("color_scheme", "System")

    # A comfortable default helps users who may not know to open the settings
    # panel before beginning their first check.
    base_font_size = 18

    if text_size == "Large":
        base_font_size = 21
    elif text_size == "Extra Large":
        base_font_size = 24

    light_theme = """
    --safe-bg:#ffffff; --safe-surface:#f8fafc; --safe-card:#ffffff;
    --safe-text:#111827; --safe-muted:#4b5563; --safe-border:#94a3b8;
    --safe-soft:#f1f5f9; --safe-primary:#075985; --safe-primary-text:#ffffff;
    --safe-secondary:#e0edf8; --safe-secondary-text:#0f172a; --safe-input:#ffffff;
    --safe-focus:#1d4ed8; --safe-link:#075985;
    """
    dark_theme = """
    --safe-bg:#111827; --safe-surface:#172033; --safe-card:#1f2937;
    --safe-text:#f8fafc; --safe-muted:#dbe4f0; --safe-border:#94a3b8;
    --safe-soft:#334155; --safe-primary:#7dd3fc; --safe-primary-text:#082f49;
    --safe-secondary:#334155; --safe-secondary-text:#f8fafc; --safe-input:#0f172a;
    --safe-focus:#facc15; --safe-link:#bae6fd;
    """
    high_contrast_theme = """
    --safe-bg:#000000; --safe-surface:#000000; --safe-card:#000000;
    --safe-text:#ffffff; --safe-muted:#ffffff; --safe-border:#ffffff;
    --safe-soft:#000000; --safe-primary:#ffff00; --safe-primary-text:#000000;
    --safe-secondary:#000000; --safe-secondary-text:#ffffff; --safe-input:#000000;
    --safe-focus:#00ffff; --safe-link:#ffff00;
    """

    if color_scheme == "Dark":
        theme_css = f":root, body, .stApp, [data-testid=\"stAppViewContainer\"] {{ {dark_theme} }}"
        dropdown_css = "#0f172a|#f8fafc|#7dd3fc|#082f49"
    elif color_scheme == "High Contrast":
        theme_css = f":root, body, .stApp, [data-testid=\"stAppViewContainer\"] {{ {high_contrast_theme} }}"
        dropdown_css = "#000000|#ffffff|#ffff00|#000000"
    elif color_scheme == "Light":
        theme_css = f":root, body, .stApp, [data-testid=\"stAppViewContainer\"] {{ {light_theme} }}"
        dropdown_css = "#ffffff|#111827|#075985|#ffffff"
    else:
        theme_css = f"""
        :root, body, .stApp, [data-testid="stAppViewContainer"] {{ {light_theme} }}
        @media (prefers-color-scheme: dark) {{
            :root, body, .stApp, [data-testid="stAppViewContainer"] {{ {dark_theme} }}
        }}
        """
        dropdown_css = "#ffffff|#111827|#075985|#ffffff"

    dropdown_background, dropdown_text, dropdown_selected, dropdown_selected_text = dropdown_css.split("|")

    st.markdown(
        f"""
        <style>
        {theme_css}

        html, body, [class*="css"] {{
            font-size:{base_font_size}px;
        }}

        .stApp {{
            background-color:var(--safe-bg);
            color:var(--safe-text);
        }}

        .stApp, .plain-card, .step-card, [data-testid="stExpander"],
        .stButton > button, input, textarea {{
            transition:background-color .16s ease, color .16s ease, border-color .16s ease;
        }}

        /* Hide Streamlit's development toolbar so it does not cover app controls. */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {{
            display:none !important;
        }}

        .block-container {{
            max-width:760px;
            padding:1.75rem 1.1rem 2.5rem 1.1rem;
        }}

        h1, h2, h3, h4, h5, h6, p, li, label {{
            color:var(--safe-text);
        }}

        a {{ color:var(--safe-link) !important; }}

        h1 {{
            font-size:2rem !important;
            line-height:1.15 !important;
        }}

        p, li {{
            line-height:1.6;
        }}

        .stButton > button,
        .stDownloadButton > button,
        button[kind="secondary"] {{
            width:100%;
            min-height:60px;
            font-size:{base_font_size}px;
            font-weight:700;
            border-radius:12px;
            margin:.45rem 0;
            padding:.7rem 1rem;
            white-space:normal;
            line-height:1.25;
            background:var(--safe-secondary) !important;
            border:2px solid var(--safe-border) !important;
            color:var(--safe-secondary-text) !important;
        }}

        .stButton > button[kind="primary"] {{
            background:var(--safe-primary) !important;
            border-color:var(--safe-primary) !important;
            color:var(--safe-primary-text) !important;
        }}

        .stButton > button *,
        .stDownloadButton > button * {{
            color:inherit !important;
        }}

        button:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        [role="radio"]:focus-visible {{
            outline:3px solid var(--safe-focus) !important;
            outline-offset:3px;
        }}

        .big-tagline {{
            font-size:1.25rem;
            font-weight:800;
            line-height:1.35;
            margin-bottom:1rem;
        }}

        .plain-card,
        .step-card,
        .checklist-card,
        .print-report,
        .print-step-card {{
            border:1px solid var(--safe-border);
            border-radius:16px;
            padding:1.15rem;
            margin:1.1rem 0;
            background-color:var(--safe-card);
            color:var(--safe-text);
            line-height:1.45;
        }}

        .step-card {{
            background-color:var(--safe-surface);
            font-size:1rem;
            font-weight:700;
        }}

        .small-muted {{
            font-size:.95rem;
            color:var(--safe-muted);
            line-height:1.4;
        }}

        div[role="radiogroup"] label {{
            border:1px solid var(--safe-border);
            border-radius:12px;
            padding:1rem;
            margin-bottom:.65rem;
            background-color:var(--safe-card);
            min-height:56px;
            display:flex;
            align-items:center;
            font-weight:600;
            line-height:1.35;
        }}

        div[role="radiogroup"] label:hover {{
            border-width:2px;
        }}

        [data-testid="stCheckbox"] label {{
            min-height:48px;
            align-items:center;
            line-height:1.45;
        }}

        [data-testid="stTabs"] button {{
            min-height:52px;
            font-size:{base_font_size}px;
            font-weight:700;
        }}

        [data-testid="stTabs"] button[aria-selected="true"] {{
            color:var(--safe-primary-text) !important;
            background-color:var(--safe-primary) !important;
        }}

        [data-testid="stMetricValue"] {{
            font-size:1.45rem;
        }}

        div[data-testid="stFileUploader"] {{
            border:1px dashed var(--safe-border);
            border-radius:16px;
            padding:.75rem;
            background-color:var(--safe-surface);
        }}

        div[data-testid="stFileUploader"] button {{
            min-height:52px;
            font-size:{base_font_size}px;
            font-weight:700;
        }}

        div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploader"] [data-testid="stCaptionContainer"] {{
            color:var(--safe-muted) !important;
        }}

        .print-report {{
            white-space:pre-wrap;
            font-family:Arial, sans-serif;
            overflow-wrap:break-word;
            word-wrap:break-word;
        }}

        textarea, input, select {{
            color:var(--safe-text) !important;
            background-color:var(--safe-input) !important;
            border-color:var(--safe-border) !important;
        }}

        input::placeholder,
        textarea::placeholder,
        [data-baseweb="input"] input::placeholder {{
            color:var(--safe-muted) !important;
            opacity:1 !important;
        }}

        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div {{
            color:var(--safe-text) !important;
            background-color:var(--safe-input) !important;
            border-color:var(--safe-border) !important;
        }}

        [data-baseweb="select"] > div *,
        [data-baseweb="input"] > div * {{
            color:var(--safe-text) !important;
        }}

        /* Help question marks and their popovers must remain readable in all modes. */
        button[data-testid="stTooltipIcon"],
        button[aria-label^="Help for"] {{
            color:var(--safe-text) !important;
            background:var(--safe-soft) !important;
            border:2px solid var(--safe-border) !important;
            border-radius:50% !important;
        }}

        button[data-testid="stTooltipIcon"] svg,
        button[aria-label^="Help for"] svg {{
            fill:var(--safe-text) !important;
            color:var(--safe-text) !important;
        }}

        [data-testid="stTooltipIcon"],
        [data-testid="stTooltipHoverTarget"] {{
            color:var(--safe-text) !important;
        }}

        [data-baseweb="tooltip"],
        [role="tooltip"] {{
            color:var(--safe-text) !important;
            background:var(--safe-card) !important;
            border:2px solid var(--safe-border) !important;
            border-radius:10px !important;
            font-size:1rem !important;
            line-height:1.4 !important;
        }}

        [data-baseweb="tooltip"] *,
        [role="tooltip"] * {{
            color:var(--safe-text) !important;
        }}

        /* Streamlit mounts help text in a BaseWeb popover outside the widget. */
        [data-testid="stTooltipContent"],
        [data-testid="stTooltipContent"] > div,
        [data-baseweb="popover"]:has([data-testid="stTooltipContent"]) {{
            color:var(--safe-text) !important;
            background:var(--safe-card) !important;
            border-color:var(--safe-border) !important;
        }}

        [data-testid="stTooltipContent"] *,
        [data-baseweb="popover"]:has([data-testid="stTooltipContent"]) * {{
            color:var(--safe-text) !important;
        }}

        [data-baseweb="popover"],
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="popover"] [role="option"],
        [role="listbox"],
        [role="option"] {{
            color:{dropdown_text} !important;
            background:{dropdown_background} !important;
            border-color:var(--safe-border) !important;
        }}

        [data-baseweb="popover"] [role="option"] *,
        [role="listbox"] [role="option"] * {{
            color:{dropdown_text} !important;
        }}

        [data-baseweb="popover"] [role="option"][aria-selected="true"],
        [data-baseweb="popover"] [role="option"]:hover,
        [role="option"][aria-selected="true"],
        [role="option"]:hover {{
            color:{dropdown_selected_text} !important;
            background:{dropdown_selected} !important;
        }}

        [data-baseweb="popover"] [role="option"][aria-selected="true"] *,
        [data-baseweb="popover"] [role="option"]:hover *,
        [role="option"][aria-selected="true"] *,
        [role="option"]:hover * {{
            color:{dropdown_selected_text} !important;
        }}

        [data-testid="stAlert"],
        [data-testid="stExpander"] {{
            color:var(--safe-text) !important;
            background-color:var(--safe-surface) !important;
            border-color:var(--safe-border) !important;
        }}

        /* The accessibility control is a Streamlit expander (the gear row),
           not a select-menu option. Give its closed and open headers explicit
           colors so they remain readable in every color mode. */
        [data-testid="stExpander"] summary {{
            color:{dropdown_text} !important;
            background:{dropdown_background} !important;
            border:2px solid var(--safe-border) !important;
            border-radius:10px;
            min-height:52px;
            padding:.8rem 1rem;
        }}

        [data-testid="stExpander"] summary *,
        [data-testid="stExpander"] summary svg {{
            color:{dropdown_text} !important;
            fill:{dropdown_text} !important;
        }}

        [data-testid="stExpander"] summary:hover,
        [data-testid="stExpander"][open] > summary,
        [data-testid="stExpander"] details[open] > summary {{
            color:{dropdown_selected_text} !important;
            background:{dropdown_selected} !important;
        }}

        [data-testid="stExpander"] summary:hover *,
        [data-testid="stExpander"][open] > summary *,
        [data-testid="stExpander"] details[open] > summary *,
        [data-testid="stExpander"] summary:hover svg,
        [data-testid="stExpander"][open] > summary svg,
        [data-testid="stExpander"] details[open] > summary svg {{
            color:{dropdown_selected_text} !important;
            fill:{dropdown_selected_text} !important;
        }}

        img {{
            border-radius:12px;
        }}

        .email-link-button {{
            display:inline-block;
            background:var(--safe-primary);
            color:var(--safe-primary-text) !important;
            padding:.75rem 1rem;
            border-radius:999px;
            border:2px solid var(--safe-primary);
            text-decoration:none !important;
            font-weight:800;
            margin:.5rem 0;
        }}

        @media screen and (max-width:480px) {{
            .block-container {{
                padding-left:.85rem;
                padding-right:.85rem;
            }}

            h1 {{
                font-size:1.8rem !important;
            }}
        }}

        @media print {{
            header,
            footer,
            [data-testid="stToolbar"],
            [data-testid="stSidebar"],
            .stButton,
            .stDownloadButton {{
                display:none !important;
            }}

            .block-container {{
                max-width:100%;
                padding:1rem;
            }}

            .print-report {{
                border:none;
                color:#000;
                background:#fff;
                font-size:12pt;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_accessibility_panel() -> None:
    with st.expander("⚙️ Accessibility", expanded=True):
        st.caption("Choose a text size and color setting. Your choice applies right away.")
        st.selectbox(
            "Text size",
            ["Standard", "Large", "Extra Large"],
            key="text_size",
        )

        st.selectbox(
            "Color scheme",
            ["System", "Light", "Dark", "High Contrast"],
            key="color_scheme",
        )

        st.checkbox(
            "Show Read Aloud buttons",
            key="show_read_aloud",
            help="Lets the device read important results and instructions aloud.",
        )


def show_read_aloud_button(text_to_read: str, key: str) -> None:
    """Shows an optional browser-based read-aloud button."""
    if not st.session_state.get("show_read_aloud") or not text_to_read.strip():
        return

    button_id = safe_filename_part(key).lower()
    # JSON encoding keeps quotes and line breaks safe inside the small
    # browser script that passes the text to the device's speech engine.
    speech_text = json.dumps(str(text_to_read))
    components.html(
        f"""
        <button id="{button_id}" style="min-height:44px;padding:8px 14px;border-radius:10px;border:2px solid #075985;background:#e0edf8;color:#0f172a;font-size:16px;font-weight:700;cursor:pointer;">Read Aloud</button>
        <script>
        document.getElementById("{button_id}").onclick = () => {{
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(new SpeechSynthesisUtterance({speech_text}));
        }};
        </script>
        """,
        height=56,
    )


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


def safe_filename_part(value: Any) -> str:
    cleaned = str(value or "summary").strip().upper()
    cleaned = re.sub(r"[^A-Z0-9-]+", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")

    return cleaned or "SUMMARY"


def show_step_card(step_text: str) -> None:
    st.markdown(
        f'<div class="step-card">{html.escape(step_text)}</div>',
        unsafe_allow_html=True,
    )


def show_current_home_and_room_status() -> None:
    home_id = st.session_state.get("home_id")
    room_id = st.session_state.get("current_room_id")

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Home ID:</strong> {safe_text(home_id or "Not selected")}<br>
            <strong>Room ID:</strong> {safe_text(room_id or "Not selected")}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hazard_card(hazard: Dict[str, Any], number: int) -> None:
    """
    Displays one hazard using native Streamlit controls.

    Native controls keep model-provided text safe and avoid HTML source being
    shown as visible text on the results page.
    """

    category = hazard.get("category", "unclear")
    category_label = get_category_label(category)

    priority = hazard.get("priority") or get_priority_for_hazard(hazard)

    with st.container(border=True):
        st.caption(f"Hazard {number} · {category_label}")
        st.subheader(str(hazard.get("title", "Possible hazard")))
        st.caption(
            f"Hazard score: {hazard.get('risk_points', 0)}/25 "
            f"({hazard.get('risk_points_source', 'category backup')})"
        )

        if priority == "Fix Now":
            st.error(f"Priority: {priority}")
        elif priority == "Fix Soon":
            st.warning(f"Priority: {priority}")
        else:
            st.info(f"Priority: {priority}")

        st.write("**Why it matters**")
        st.write(str(hazard.get("explanation", "This area may need human review.")))
        st.write("**Suggested fix**")
        st.write(str(hazard.get("recommendation", "Review this area carefully.")))


def show_score_explanation_card(score_breakdown: Dict[str, Any]) -> None:
    if not score_breakdown:
        st.info("No score breakdown is available yet.")
        return

    raw_score = score_breakdown.get(
        "raw_score",
        score_breakdown.get("total_before_cap", 0),
    )

    st.markdown(
        f"""
        <div class="plain-card">
            <strong>Why this score?</strong><br><br>
            AI hazard points: {safe_text(score_breakdown.get("ai_points", 0))} ({safe_text(score_breakdown.get("ai_assessed_hazards", 0))} AI-assessed, {safe_text(score_breakdown.get("backup_scored_hazards", 0))} category backup)<br>
            Checklist concern points: {safe_text(score_breakdown.get("checklist_points", 0))}<br>
            Skipped follow-up buffer: {safe_text(score_breakdown.get("skip_buffer_points", 0))}<br>
            Raw score before cap: {safe_text(raw_score)}<br>
            Final score: {safe_text(score_breakdown.get("final_score", 0))}/100<br>
            Risk label: {safe_text(score_breakdown.get("risk_level", "Unknown"))}<br><br>
            Higher score = more possible fall hazards.<br>
            Lower score = fewer possible fall hazards.
        </div>
        """,
        unsafe_allow_html=True,
    )
