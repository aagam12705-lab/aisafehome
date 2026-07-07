import streamlit as st

from src.safety_text import (
    APP_NAME,
    TAGLINE,
    LANDING_EXPLANATION,
    SAFETY_DISCLAIMER,
    PRIVACY_REMINDER,
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


def initialize_session_state():
    """
    Streamlit reruns the app whenever the user clicks something.
    Session state lets us remember what screen the user is on
    and what room they selected.
    """
    if "page" not in st.session_state:
        st.session_state["page"] = "landing"

    if "room_type" not in st.session_state:
        st.session_state["room_type"] = None


def add_mobile_friendly_style():
    """
    Adds simple CSS to make the app easier to use on iPhone.
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

        div[role="radiogroup"] label {
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 0.75rem;
            margin-bottom: 0.4rem;
            background-color: #000000;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def go_to_page(page_name):
    """
    Changes the current screen.
    """
    st.session_state["page"] = page_name
    st.rerun()


def show_landing_page():
    """
    Displays the first screen of AI SafeHome.
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

    if st.button("Start Safety Check", type="primary"):
        go_to_page("room_selection")

    st.caption(
        "Version 1 uses staged, non-patient photos only. "
        "No login. No database. No stored photos."
    )


def show_room_selection_page():
    """
    Displays the room selection screen.
    """

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
        go_to_page("room_confirmed")

    if st.button("← Back"):
        go_to_page("landing")


def show_room_confirmed_page():
    """
    Temporary page for Milestone 3.
    In Milestone 4, this will become the photo upload page.
    """

    st.title("🏠 AI SafeHome")
    st.subheader("Room Selected")

    room_type = st.session_state.get("room_type")

    st.success(f"You selected: {room_type}")

    st.write(
        "In Milestone 4, this screen will let you upload or take a room photo."
    )

    if st.button("Change Room"):
        go_to_page("room_selection")

    if st.button("Start Over"):
        st.session_state["room_type"] = None
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
    elif current_page == "room_confirmed":
        show_room_confirmed_page()
    else:
        st.error("Unknown page. Returning to landing page.")
        st.session_state["page"] = "landing"
        st.rerun()


main()