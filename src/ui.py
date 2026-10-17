"""
ui.py

Reusable Streamlit UI helpers and styling for SafeHome AI.
"""

import base64
import html
import io
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st
import qrcode

from src.constants import CATEGORY_LABELS
from src.priorities import get_priority_for_hazard


DEFAULT_PUBLIC_APP_URL = "https://ai-safehome.streamlit.app/"


def show_open_on_phone_panel() -> None:
    """Show a compact QR code that opens the deployed app on another device."""
    public_url = os.getenv("SAFEHOME_PUBLIC_URL", DEFAULT_PUBLIC_APP_URL).strip()
    if not public_url:
        return

    qr = qrcode.QRCode(version=None, box_size=8, border=3)
    qr.add_data(public_url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#0f2747", back_color="#ffffff")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    with st.expander("Open SafeHome AI on a phone"):
        st.write("Scan this code with a phone camera to open the app.")
        left, center, right = st.columns([1, 1.2, 1])
        with center:
            st.image(buffer.getvalue(), width="stretch")
        st.link_button("Open SafeHome AI", public_url, width="stretch")


def show_html_frame(html_content: str, height: int) -> None:
    """Display self-contained HTML with Streamlit's supported iframe API."""
    encoded_html = base64.b64encode(html_content.encode("utf-8")).decode("ascii")
    st.iframe(
        f"data:text/html;base64,{encoded_html}",
        width="stretch",
        height=height,
        tab_index=-1,
    )


def setup_page() -> None:
    st.set_page_config(
        page_title="SafeHome AI",
        page_icon="🏠",
        layout="centered",
    )


def add_mobile_friendly_style() -> None:
    text_size = st.session_state.get("text_size", "Standard")
    color_scheme = st.session_state.get("color_scheme", "System")
    reduce_motion = st.session_state.get("reduce_motion", False)
    compact_spacing = st.session_state.get("compact_spacing", False)

    # A comfortable default helps users who may not know to open the settings
    # panel before beginning their first check.
    base_font_size = 18

    if text_size == "Large":
        base_font_size = 21
    elif text_size == "Extra Large":
        base_font_size = 24

    spacing_css = """
    .stMarkdown, [data-testid="stVerticalBlock"] > div { margin-bottom:.35rem !important; }
    """ if compact_spacing else ""
    motion_css = """
    *, *::before, *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
        scroll-behavior: auto !important;
    }
    """ if reduce_motion else ""

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

    system_dark_widget_css = ""
    if color_scheme == "System":
        system_dark_widget_css = """
        @media (prefers-color-scheme: dark) {
            [data-testid="stExpander"] summary {
                color:#f8fafc !important;
                background:#0f172a !important;
                border-color:#94a3b8 !important;
            }
            [data-testid="stExpander"] summary *,
            [data-testid="stExpander"] summary svg {
                color:#f8fafc !important;
                fill:#f8fafc !important;
            }
            [data-testid="stExpander"] summary:hover,
            [data-testid="stExpander"][open] > summary,
            [data-testid="stExpander"] details[open] > summary {
                color:#082f49 !important;
                background:#7dd3fc !important;
            }
            [data-testid="stExpander"] summary:hover *,
            [data-testid="stExpander"][open] > summary *,
            [data-testid="stExpander"] summary:hover svg,
            [data-testid="stExpander"][open] > summary svg {
                color:#082f49 !important;
                fill:#082f49 !important;
            }
        }
        """

    dropdown_background, dropdown_text, dropdown_selected, dropdown_selected_text = dropdown_css.split("|")

    st.markdown(
        f"""
        <style>
        {theme_css}
        {spacing_css}
        {motion_css}

        html, body, [class*="css"] {{
            font-size:{base_font_size}px;
        }}

        *, *::before, *::after {{
            box-sizing:border-box;
        }}

        .stApp {{
            background-color:var(--safe-bg);
            color:var(--safe-text);
            overflow-x:hidden;
        }}

        /* Streamlit scrolls the page inside stMain rather than the browser
           document. Keep touch momentum enabled for iOS and avoid trapping
           vertical swipes in the outer app container. */
        [data-testid="stMain"] {{
            -webkit-overflow-scrolling:touch;
            touch-action:pan-y;
            overscroll-behavior-y:contain;
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
            padding:2.15rem 1.1rem 3rem 1.1rem;
        }}

        h1, h2, h3, h4, h5, h6, p, li, label {{
            color:var(--safe-text);
        }}

        a {{ color:var(--safe-link) !important; }}

        h1 {{
            font-size:2.15rem !important;
            line-height:1.1 !important;
            letter-spacing:-.035em;
            margin-bottom:.45rem !important;
        }}

        h2 {{ letter-spacing:-.02em; margin-top:1.75rem !important; }}

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
            box-shadow:0 2px 0 rgba(15, 23, 42, .10);
            background:var(--safe-secondary) !important;
            border:2px solid var(--safe-border) !important;
            color:var(--safe-secondary-text) !important;
        }}

        .stButton > button[kind="primary"] {{
            background:var(--safe-primary) !important;
            border-color:var(--safe-primary) !important;
            color:var(--safe-primary-text) !important;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            transform:translateY(-1px);
            box-shadow:0 5px 12px rgba(15, 23, 42, .16);
        }}

        .stButton > button:active,
        .stDownloadButton > button:active {{ transform:translateY(0); }}

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
            box-shadow:0 8px 20px rgba(15, 23, 42, .08);
        }}

        .step-card {{
            background-color:var(--safe-surface);
            font-size:1rem;
            font-weight:700;
            border-left:5px solid var(--safe-primary);
        }}

        .small-muted {{
            font-size:.95rem;
            color:var(--safe-muted);
            line-height:1.4;
        }}

        .safe-table-wrap {{
            overflow-x:auto;
            margin:1rem 0;
            border:1px solid var(--safe-border);
            border-radius:14px;
            background:var(--safe-card);
        }}

        .safe-table {{
            width:100%;
            border-collapse:collapse;
            min-width:520px;
            color:var(--safe-text);
        }}

        .safe-table th {{
            background:var(--safe-primary);
            color:var(--safe-primary-text) !important;
            text-align:left;
            padding:.85rem 1rem;
            font-weight:800;
        }}

        .safe-table td {{
            padding:.8rem 1rem;
            border-top:1px solid var(--safe-border);
            color:var(--safe-text) !important;
            vertical-align:top;
            overflow-wrap:anywhere;
        }}

        .safe-table tr:nth-child(even) td {{
            background:var(--safe-surface);
        }}

        [data-testid="stArrowVegaLiteChart"] {{
            background:var(--safe-card);
            border:1px solid var(--safe-border);
            border-radius:14px;
            padding:.5rem;
            margin:1rem 0;
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
            font-size:1.6rem;
            font-weight:800;
            color:var(--safe-text) !important;
        }}

        [data-testid="stMetric"] {{
            background:var(--safe-card);
            border:1px solid var(--safe-border);
            border-radius:14px;
            padding:.85rem;
            box-shadow:0 4px 12px rgba(15, 23, 42, .06);
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

        input:disabled,
        textarea:disabled,
        [data-baseweb="input"] input:disabled {{
            color:var(--safe-text) !important;
            -webkit-text-fill-color:var(--safe-text) !important;
            opacity:1 !important;
            background-color:var(--safe-input) !important;
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
            border-radius:14px !important;
        }}

        /* The accessibility control is a Streamlit expander (the gear row),
           not a select-menu option. Give its closed and open headers explicit
           colors so they remain readable in every color mode. */
        [data-testid="stExpander"] summary {{
            color:var(--safe-text) !important;
            background:var(--safe-input) !important;
            border:2px solid var(--safe-border) !important;
            border-radius:10px;
            min-height:52px;
            padding:.8rem 1rem;
            white-space:normal;
        }}

        [data-testid="stExpander"] summary *,
        [data-testid="stExpander"] summary svg {{
            color:var(--safe-text) !important;
            fill:var(--safe-text) !important;
        }}

        [data-testid="stExpander"] summary:hover,
        [data-testid="stExpander"][open] > summary,
        [data-testid="stExpander"] details[open] > summary {{
            color:var(--safe-primary-text) !important;
            background:var(--safe-primary) !important;
        }}

        [data-testid="stExpander"] summary:hover *,
        [data-testid="stExpander"][open] > summary *,
        [data-testid="stExpander"] details[open] > summary *,
        [data-testid="stExpander"] summary:hover svg,
        [data-testid="stExpander"][open] > summary svg,
        [data-testid="stExpander"] details[open] > summary svg {{
            color:var(--safe-primary-text) !important;
            fill:var(--safe-primary-text) !important;
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
                width:100%;
                max-width:100%;
                padding-top:max(1.25rem, env(safe-area-inset-top));
                padding-right:max(.85rem, env(safe-area-inset-right));
                /* Mobile Safari and installed web apps can overlay controls
                   at the bottom of the viewport. The extra clearance lets
                   the final button scroll completely above that toolbar. */
                padding-bottom:max(7rem, calc(env(safe-area-inset-bottom) + 5rem));
                padding-left:max(.85rem, env(safe-area-inset-left));
            }}

            h1 {{
                font-size:1.8rem !important;
            }}

            h2 {{
                font-size:1.45rem !important;
                margin-top:1.25rem !important;
            }}

            h3 {{
                font-size:1.2rem !important;
            }}

            .plain-card,
            .step-card,
            .checklist-card,
            .print-report,
            .print-step-card {{
                padding:.9rem;
                margin:.8rem 0;
                border-radius:13px;
                overflow-wrap:anywhere;
            }}

            /* Streamlit keeps desktop columns side-by-side at some iPhone
               widths. Stack them so metrics and comparison cards remain
               readable without shrinking text or causing page overflow. */
            [data-testid="stHorizontalBlock"] {{
                flex-direction:column !important;
                gap:.55rem !important;
            }}

            [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
                width:100% !important;
                min-width:0 !important;
                flex:1 1 100% !important;
            }}

            [data-testid="stMetric"] {{
                width:100%;
                padding:.75rem;
            }}

            /* Long account-tab labels wrap into full-width touch targets. */
            [data-testid="stTabs"] [role="tablist"] {{
                display:flex !important;
                flex-wrap:wrap !important;
                gap:.4rem !important;
            }}

            [data-testid="stTabs"] [role="tab"] {{
                flex:1 1 10rem !important;
                width:auto !important;
                white-space:normal !important;
                line-height:1.25 !important;
            }}

            /* Keep the uploader usable when iOS supplies a long camera or
               Photo Library label. */
            [data-testid="stFileUploaderDropzone"] {{
                padding:.8rem !important;
            }}

            [data-testid="stFileUploaderDropzone"] > div {{
                min-width:0 !important;
                max-width:100% !important;
                flex-direction:column !important;
                align-items:stretch !important;
                gap:.65rem !important;
            }}

            [data-testid="stFileUploaderDropzone"] button {{
                width:100% !important;
                margin:0 !important;
                white-space:normal !important;
            }}

            input, textarea, [data-baseweb="select"] {{
                width:100% !important;
                max-width:100% !important;
                min-width:0 !important;
                font-size:{base_font_size}px !important;
            }}

            /* Convert wide statistics tables into labeled cards instead of
               requiring a horizontal swipe inside the page. */
            .safe-table-wrap {{
                overflow:visible;
                border:0;
                background:transparent;
            }}

            .safe-table {{
                display:block;
                min-width:0;
                width:100%;
            }}

            .safe-table thead {{
                position:absolute;
                width:1px;
                height:1px;
                padding:0;
                margin:-1px;
                overflow:hidden;
                clip:rect(0, 0, 0, 0);
                white-space:nowrap;
                border:0;
            }}

            .safe-table tbody,
            .safe-table tr,
            .safe-table td {{
                display:block;
                width:100%;
            }}

            .safe-table tr {{
                margin:0 0 .8rem;
                border:1px solid var(--safe-border);
                border-radius:13px;
                overflow:hidden;
                background:var(--safe-card);
                box-shadow:0 4px 12px rgba(15, 23, 42, .06);
            }}

            .safe-table td {{
                display:grid;
                grid-template-columns:minmax(7.5rem, 42%) minmax(0, 1fr);
                gap:.6rem;
                padding:.7rem .8rem;
                border-top:1px solid var(--safe-border);
            }}

            .safe-table td:first-child {{
                border-top:0;
            }}

            .safe-table td::before {{
                content:attr(data-label);
                font-weight:800;
                color:var(--safe-text);
            }}

            /* Recipient controls stay easy to use on a narrow phone: the
               remove button comes first, then the full-width email field. */
            [class*="st-key-recipient-row-"] [data-testid="stHorizontalBlock"] {{
                flex-direction:column-reverse !important;
                gap:.2rem !important;
            }}

            [class*="st-key-recipient-row-"] [data-testid="column"] {{
                width:100% !important;
                flex:1 1 100% !important;
            }}

            [class*="st-key-recipient-row-"] [data-testid="column"]:nth-child(2) {{
                display:flex !important;
                justify-content:flex-end !important;
                align-items:center !important;
            }}

            [class*="st-key-recipient-row-"] [data-testid="column"]:nth-child(2) .stButton,
            [class*="st-key-recipient-row-"] [data-testid="column"]:nth-child(2) button {{
                width:48px !important;
                min-width:48px !important;
                min-height:48px !important;
                margin:0 !important;
                padding:0 !important;
            }}

            .email-link-button {{
                display:block;
                width:100%;
                min-height:52px;
                text-align:center;
                border-radius:12px;
            }}
        }}

        @media (hover:none) and (pointer:coarse) {{
            .stButton > button:hover,
            .stDownloadButton > button:hover {{
                transform:none;
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
        {system_dark_widget_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_accessibility_panel() -> None:
    with st.expander("Accessibility", expanded=False):
        st.caption("Choose settings that make SafeHome AI easier to use. Changes apply right away.")
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

        st.checkbox(
            "Reduce motion and animations",
            key="reduce_motion",
            help="Removes most movement and animated transitions.",
        )

        st.checkbox(
            "Use compact spacing",
            key="compact_spacing",
            help="Reduces extra space so more information fits on the screen.",
        )


def show_how_it_works_panel() -> None:
    """Explain the app's AI, scoring, privacy, and fallback behavior."""
    with st.expander("How SafeHome AI works"):
        st.write(
            "SafeHome AI reviews visible room conditions from a photo. It does not "
            "diagnose a person or predict an individual person's fall risk."
        )
        st.markdown(
            """
            **1. See:** AI looks for visible hazards and marks their approximate location.

            **2. Ask:** If the photo cannot confirm an important detail, the app asks a short follow-up question.

            **3. Score:** Each confirmed concern receives a severity value, then the total is capped at 100.

            **4. Act:** The app gives practical fixes, highlights uncertainty, and recommends human review.

            **Why this approach is different:** Instead of making every person complete the same long form, the photo supplies visible evidence and the app asks only about important uncertainties. Saved rechecks then turn a one-time result into visible room progress.

            **Designed for seniors:** Large controls, plain language, four color modes, adjustable text, and optional Read Aloud make the same features easier to use without creating a separate reduced version of the app.

            **If AI or the database is unavailable:** the app shows a clearly labeled sample/fallback result and does not pretend it is a confirmed finding.

            **Privacy:** Photos are used during the current check and are not saved to the database by the app.
            """
        )


def show_read_aloud_button(text_to_read: str, key: str) -> None:
    """Shows an optional browser-based read-aloud button."""
    if not st.session_state.get("show_read_aloud") or not text_to_read.strip():
        return

    button_id = safe_filename_part(key).lower()
    # JSON encoding keeps quotes and line breaks safe inside the small
    # browser script that passes the text to the device's speech engine.
    speech_text = json.dumps(str(text_to_read))
    show_html_frame(
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


def render_styled_table(rows: list[Dict[str, Any]]) -> None:
    """Render saved data in the same high-contrast-safe style as app cards."""
    if not rows:
        return

    columns = list(rows[0].keys())
    header_html = "".join(f"<th>{safe_text(column)}</th>" for column in columns)
    body_html = "".join(
        "<tr>" + "".join(
            f'<td data-label="{safe_text(column)}">{safe_text(row.get(column, ""))}</td>'
            for column in columns
        ) + "</tr>"
        for row in rows
    )
    st.markdown(
        f'<div class="safe-table-wrap"><table class="safe-table"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def render_score_trend_chart(rows: list[Dict[str, Any]]) -> None:
    """Render a readable, themed SVG trend chart instead of Streamlit's default chart."""
    if not rows:
        return

    points: list[tuple[int, int]] = []
    for row in rows:
        try:
            points.append((int(row.get("Check Number", 0)), max(0, min(int(row.get("Score", 0)), 100))))
        except (TypeError, ValueError):
            continue
    if not points:
        return

    scheme = st.session_state.get("color_scheme", "System")
    use_system_theme = scheme == "System"
    if scheme == "High Contrast":
        background, text, grid, line, point = "#000000", "#ffffff", "#ffffff", "#ffff00", "#00ffff"
    elif scheme == "Dark":
        background, text, grid, line, point = "#1f2937", "#f8fafc", "#94a3b8", "#7dd3fc", "#facc15"
    else:
        background, text, grid, line, point = "#ffffff", "#111827", "#94a3b8", "#075985", "#1d4ed8"

    width, height = 720, 310
    left, right, top, bottom = 56, 24, 28, 52
    plot_width, plot_height = width - left - right, height - top - bottom
    count = len(points)

    def x_position(index: int) -> float:
        return left + (plot_width / max(count - 1, 1)) * index

    def y_position(score: int) -> float:
        return top + plot_height * (1 - score / 100)

    coordinates = [(x_position(index), y_position(score)) for index, (_number, score) in enumerate(points)]
    path = " ".join(
        f"{'M' if index == 0 else 'L'} {x:.1f} {y:.1f}"
        for index, (x, y) in enumerate(coordinates)
    )
    grid_lines = "".join(
        f'<line class="chart-grid" x1="{left}" y1="{y_position(level):.1f}" x2="{width-right}" y2="{y_position(level):.1f}" stroke="{grid}" stroke-width="1" opacity="0.55" />'
        f'<text class="chart-text" x="{left-12}" y="{y_position(level)+5:.1f}" fill="{text}" font-size="13" text-anchor="end">{level}</text>'
        for level in (0, 50, 100)
    )
    point_shapes = "".join(
        f'<circle class="chart-point" cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{point}" stroke="{background}" stroke-width="3" />'
        f'<text class="chart-score" x="{x:.1f}" y="{min(y + 25, height - 42):.1f}" fill="{text}" font-size="14" font-weight="700" text-anchor="middle">{score}/100</text>'
        f'<text class="chart-text" x="{x:.1f}" y="{height-20}" fill="{text}" font-size="13" text-anchor="middle">Check {number}</text>'
        for (number, score), (x, y) in zip(points, coordinates)
    )

    system_theme_css = ""
    if use_system_theme:
        system_theme_css = """
        @media (prefers-color-scheme: dark) {
          .chart-shell { background:#1f2937 !important; border-color:#94a3b8 !important; }
          .chart-text, .chart-score { fill:#f8fafc !important; }
          .chart-grid { stroke:#94a3b8 !important; }
          .chart-line { stroke:#7dd3fc !important; }
          .chart-point { fill:#facc15 !important; stroke:#1f2937 !important; }
        }
        """

    show_html_frame(
        f"""
        <style>
          .chart-shell {{ background:{background}; border:2px solid {grid}; border-radius:16px; padding:12px; }}
          {system_theme_css}
        </style>
        <div class="chart-shell">
          <svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Room risk score trend">
            <text class="chart-text" x="{left}" y="18" fill="{text}" font-size="17" font-weight="700">Risk score over time</text>
            {grid_lines}
            <path class="chart-line" d="{path}" fill="none" stroke="{line}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" />
            {point_shapes}
          </svg>
        </div>
        """,
        height=350,
    )


def format_database_datetime(value: Any) -> str:
    if not value:
        return "Unknown date"

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%b %-d, %Y at %-I:%M %p UTC")
    except (TypeError, ValueError):
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

        if priority == "Fix Now":
            st.error(f"Priority: {priority}")
        elif priority == "Fix Soon":
            st.warning(f"Priority: {priority}")
        else:
            st.info(f"Priority: {priority}")

        st.write("**Why it matters**")
        st.write(str(hazard.get("explanation", "This area may need human review.")))
        st.write("**What the app noticed**")
        st.write(str(hazard.get("evidence", "The photo provides limited visual evidence for this concern.")))
        st.write("**Suggested fix**")
        st.write(str(hazard.get("recommendation", "Review this area carefully.")))
        details = []
        if hazard.get("location"):
            details.append(f"Approximate location: {hazard['location']}")
        if hazard.get("confidence"):
            details.append(f"AI confidence: {str(hazard['confidence']).capitalize()}")
        if hazard.get("visibility"):
            details.append(f"Photo visibility: {str(hazard['visibility']).capitalize()}")
        if details:
            st.caption(" · ".join(details))
        if hazard.get("human_review_reason"):
            st.info(f"Double-check in the real room: {hazard['human_review_reason']}")


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
            Follow-up concern points: {safe_text(score_breakdown.get("checklist_points", 0))}<br>
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


def show_risk_score_bar(score: Any) -> None:
    """Shows the 0–100 risk score as both a number and a clear severity bar."""
    try:
        value = max(0, min(int(score), 100))
    except (TypeError, ValueError):
        value = 0

    if value < 30:
        color, label = "#15803d", "Low risk"
    elif value < 60:
        color, label = "#b45309", "Moderate risk"
    else:
        color, label = "#b91c1c", "High risk"

    st.markdown(
        f"""
        <div class="plain-card" aria-label="Risk score {value} out of 100, {label}">
            <strong>Risk score: {value}/100 — {label}</strong>
            <div style="height:18px; background:#d1d5db; border-radius:999px; margin-top:.65rem; overflow:hidden; border:1px solid #64748b;">
                <div style="height:100%; width:{value}%; min-width:{'4px' if value else '0'}; background:{color}; border-radius:999px;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:.85em; margin-top:.3rem;">
                <span>Low</span><span>Moderate</span><span>High</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
