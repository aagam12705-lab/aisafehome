"""
ui.py

Reusable Streamlit UI helpers and styling for AI SafeHome.
"""

import html
import re
from typing import Any, Dict, Optional

import streamlit as st

from src.constants import CATEGORY_LABELS
from src.priorities import get_priority_css_class, get_priority_for_hazard


def setup_page() -> None:
    st.set_page_config(
        page_title="AI SafeHome",
        page_icon="🏠",
        layout="centered",
    )


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
        :root {
            --safe-bg:#0f172a;
            --safe-surface:#111827;
            --safe-card:#1f2937;
            --safe-text:#f9fafb;
            --safe-muted:#d1d5db;
            --safe-border:#475569;
            --safe-soft:#334155;
        }
        """
    elif color_scheme == "High Contrast":
        theme_css = """
        :root {
            --safe-bg:#000000;
            --safe-surface:#000000;
            --safe-card:#000000;
            --safe-text:#ffffff;
            --safe-muted:#ffffff;
            --safe-border:#ffffff;
            --safe-soft:#111111;
        }
        """
    elif color_scheme == "Light":
        theme_css = """
        :root {
            --safe-bg:#ffffff;
            --safe-surface:#f8fafc;
            --safe-card:#ffffff;
            --safe-text:#111827;
            --safe-muted:#4b5563;
            --safe-border:#d1d5db;
            --safe-soft:#f1f5f9;
        }
        """
    else:
        theme_css = """
        :root {
            --safe-bg:#ffffff;
            --safe-surface:#f8fafc;
            --safe-card:#ffffff;
            --safe-text:#111827;
            --safe-muted:#4b5563;
            --safe-border:#d1d5db;
            --safe-soft:#f1f5f9;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --safe-bg:#0f172a;
                --safe-surface:#111827;
                --safe-card:#1f2937;
                --safe-text:#f9fafb;
                --safe-muted:#d1d5db;
                --safe-border:#475569;
                --safe-soft:#334155;
            }
        }
        """

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

        .block-container {{
            max-width:720px;
            padding:1rem 1rem 2rem 1rem;
        }}

        h1, h2, h3, h4, h5, h6, p, li, label, span, div {{
            color:var(--safe-text);
        }}

        h1 {{
            font-size:2rem !important;
            line-height:1.15 !important;
        }}

        p, li {{
            line-height:1.45;
        }}

        .stButton > button,
        .stDownloadButton > button {{
            width:100%;
            min-height:54px;
            font-size:{base_font_size}px;
            font-weight:700;
            border-radius:14px;
            margin:.25rem 0;
        }}

        .big-tagline {{
            font-size:1.25rem;
            font-weight:800;
            line-height:1.35;
            margin-bottom:1rem;
        }}

        .plain-card,
        .step-card,
        .hazard-card,
        .checklist-card,
        .print-report,
        .print-step-card {{
            border:1px solid var(--safe-border);
            border-radius:16px;
            padding:1rem;
            margin:1rem 0;
            background-color:var(--safe-card);
            color:var(--safe-text);
            line-height:1.45;
        }}

        .step-card {{
            background-color:var(--safe-surface);
            font-size:.95rem;
        }}

        .hazard-number {{
            font-size:.9rem;
            font-weight:700;
            color:var(--safe-muted);
            margin-bottom:.3rem;
        }}

        .hazard-title {{
            font-size:1.15rem;
            font-weight:800;
            margin-bottom:.4rem;
        }}

        .hazard-category,
        .priority-badge {{
            display:inline-block;
            border-radius:999px;
            padding:.25rem .65rem;
            margin:.2rem .2rem .55rem 0;
            background-color:var(--safe-soft);
            border:1px solid var(--safe-border);
            font-size:.85rem;
            font-weight:800;
            color:var(--safe-text);
        }}

        .priority-fix-now {{
            border-style:solid;
        }}

        .priority-fix-soon {{
            border-style:dashed;
        }}

        .priority-watch-review {{
            border-style:dotted;
        }}

        .hazard-section-label {{
            font-weight:800;
            margin-top:.6rem;
            margin-bottom:.15rem;
        }}

        .small-muted {{
            font-size:.95rem;
            color:var(--safe-muted);
            line-height:1.4;
        }}

        div[role="radiogroup"] label {{
            border:1px solid var(--safe-border);
            border-radius:12px;
            padding:.85rem;
            margin-bottom:.45rem;
            background-color:var(--safe-card);
            min-height:44px;
        }}

        div[data-testid="stFileUploader"] {{
            border:1px dashed var(--safe-border);
            border-radius:16px;
            padding:.75rem;
            background-color:var(--safe-surface);
        }}

        .print-report {{
            white-space:pre-wrap;
            font-family:Arial, sans-serif;
            overflow-wrap:break-word;
            word-wrap:break-word;
        }}

        textarea, input, select {{
            color:var(--safe-text) !important;
            background-color:var(--safe-card) !important;
        }}

        img {{
            border-radius:12px;
        }}

        .email-link-button {{
            display:inline-block;
            background:var(--safe-text);
            color:var(--safe-bg) !important;
            padding:.75rem 1rem;
            border-radius:999px;
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
    with st.expander("⚙️ Accessibility settings"):
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
    category = hazard.get("category", "unclear")
    category_label = get_category_label(category)

    priority = hazard.get("priority") or get_priority_for_hazard(hazard)
    priority_class = get_priority_css_class(priority)

    st.markdown(
        f"""
        <div class="hazard-card">
            <div class="hazard-number">Hazard {number}</div>
            <div class="hazard-title">{safe_text(hazard.get("title", "Possible hazard"))}</div>
            <div class="hazard-category">{safe_text(category_label)}</div>
            <div class="priority-badge {priority_class}">{safe_text(priority)}</div>

            <div class="hazard-section-label">Why it matters</div>
            <p>{safe_text(hazard.get("explanation", "This area may need human review."))}</p>

            <div class="hazard-section-label">Suggested fix</div>
            <p>{safe_text(hazard.get("recommendation", "Review this area carefully."))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
            AI hazard points: {safe_text(score_breakdown.get("ai_points", 0))}<br>
            Checklist concern points: {safe_text(score_breakdown.get("checklist_points", 0))}<br>
            Raw score before cap: {safe_text(raw_score)}<br>
            Final score: {safe_text(score_breakdown.get("final_score", 0))}/100<br>
            Risk label: {safe_text(score_breakdown.get("risk_level", "Unknown"))}<br><br>
            Higher score = more possible fall hazards.<br>
            Lower score = fewer possible fall hazards.
        </div>
        """,
        unsafe_allow_html=True,
    )