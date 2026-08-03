"""Optional account and privacy controls used by saved room checks."""

from typing import Optional

import streamlit as st

from src.constants import PHOTO_NOT_STORED_NOTE
from src.database import (
    authenticate_home,
    create_password_reset_code,
    create_protected_home,
    is_database_enabled,
    is_home_id_available,
    reset_home_password,
)
from src.email_service import is_valid_email_address, send_summary_email


def clean_account_email(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().split())


def get_logged_in_home_id() -> Optional[str]:
    return st.session_state.get("home_id")


def log_out_home_id() -> None:
    for key in ("home_id", "home_login_error", "home_login_message", "last_created_home_id"):
        st.session_state[key] = None


def log_in_with_home_id(email: str, password: str) -> bool:
    cleaned = clean_account_email(email).lower()
    if not is_valid_email_address(cleaned):
        st.session_state["home_login_error"] = "Enter a valid email address."
        st.session_state["home_login_message"] = None
        return False

    try:
        if not authenticate_home(cleaned, password):
            st.session_state["home_login_error"] = "The email address or password is incorrect."
            st.session_state["home_login_message"] = None
            return False
    except Exception as error:
        st.session_state["home_login_error"] = "Could not sign in right now. Please try again."
        st.session_state["home_login_message"] = str(error)
        return False

    st.session_state["home_id"] = cleaned
    st.session_state["home_login_error"] = None
    st.session_state["home_login_message"] = "Signed in successfully."
    return True


def create_account(email: str, password: str) -> bool:
    cleaned = clean_account_email(email).lower()
    if not is_valid_email_address(cleaned):
        st.session_state["home_login_error"] = "Enter a valid email address."
        return False

    try:
        if not is_home_id_available(cleaned):
            st.session_state["home_login_error"] = "An account already exists with that email address."
            return False
        created = create_protected_home(cleaned, password, cleaned)
    except Exception as error:
        st.session_state["home_login_error"] = f"Could not create this user account: {error}"
        st.session_state["home_login_message"] = None
        return False

    st.session_state["home_id"] = created
    st.session_state["last_created_home_id"] = created
    st.session_state["home_login_error"] = None
    st.session_state["home_login_message"] = "User account created."
    return True


def show_home_id_status(key_suffix: str = "main", allow_logout: bool = False) -> None:
    email = get_logged_in_home_id()
    if not email:
        return
    st.success(f"Signed in as: {email}")
    if allow_logout and st.button("Log Out", key=f"log_out_home_id_{key_suffix}"):
        log_out_home_id()
        st.rerun()


def show_privacy_and_ai_info() -> None:
    with st.expander("Privacy and AI information"):
        st.write("**Your photo:** Use a room photo only. Leave out faces, mail, addresses, medicine bottles, and medical papers.")
        st.write("**Photo storage:** " + PHOTO_NOT_STORED_NOTE)
        st.write("**Saved checks:** If you choose to save, the app keeps your account email, Room Name, score, and check details so you can view progress later. Your password is stored as a secure hash, not as readable text.")
        st.write("**What AI can do:** It looks for possible visible room hazards. It can miss hazards or misunderstand a photo, and it cannot measure a person's medical fall risk.")
        st.write("**For serious concerns:** Review the room with a qualified home-safety professional.")


def show_home_id_login_box(key_prefix: str = "home_id") -> None:
    st.subheader("Sign In")
    st.write("Use your email and password to save and view room checks.")
    if not is_database_enabled():
        st.info("Saved room checks are not available right now.")
        return

    if st.session_state.get("home_login_error"):
        st.error(st.session_state["home_login_error"])
    if st.session_state.get("home_login_message"):
        st.info(st.session_state["home_login_message"])

    existing_tab, create_tab = st.tabs(["Use Existing Account", "Create New Account"])
    with existing_tab:
        existing = st.text_input("Email address", placeholder="name@example.com", key=f"{key_prefix}_existing")
        password = st.text_input("Password", type="password", key=f"{key_prefix}_login_password")
        if st.button("Sign In", key=f"{key_prefix}_login", type="primary") and log_in_with_home_id(existing, password):
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

    with create_tab:
        email = st.text_input("Email address", placeholder="name@example.com", key=f"{key_prefix}_custom")
        password = st.text_input("Create password", type="password", key=f"{key_prefix}_password")
        if st.button("Create Account", key=f"{key_prefix}_create_custom", type="primary") and create_account(email, password):
            st.success("Account created.")
            st.rerun()
