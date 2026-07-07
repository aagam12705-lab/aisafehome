import streamlit as st

from src.safety_text import (
    APP_NAME,
    TAGLINE,
    LANDING_EXPLANATION,
    SAFETY_DISCLAIMER,
    PRIVACY_REMINDER,
)


def setup_page():
    """
    Sets basic browser/page settings for the Streamlit app.
    This should run before anything is displayed.
    """
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🏠",
        layout="centered",
    )


def add_mobile_friendly_style():
    """
    Adds simple CSS to make the app easier to use on iPhone.
    Do not worry if you do not fully understand CSS yet.
    This mainly makes buttons larger and spacing cleaner.
    """
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
            background-color: #000000;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_landing_page():
    """
    Displays the first screen of AI SafeHome.
    Later, the Start button will move the user to room selection.
    """

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

    start_clicked = st.button("Start Safety Check", type="primary")

    if start_clicked:
        st.success(
            "Start button works. In Milestone 3, this will take you to room selection."
        )

    st.caption(
        "Version 1 will use staged, non-patient photos only. No login. No database. No stored photos."
    )


def main():
    setup_page()
    add_mobile_friendly_style()
    show_landing_page()


main()