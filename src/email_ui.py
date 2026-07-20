"""
email_ui.py

Streamlit email/share UI helpers.
"""

import html
import urllib.parse

import streamlit as st

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


def shorten_email_body(text: str, max_length: int = 4500) -> str:
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return (
        text[:max_length]
        + "\n\n[Summary shortened for email draft. Use the copy box for the full text.]"
    )


def create_mailto_link(to_email: str, subject: str, body: str) -> str:
    params = urllib.parse.urlencode(
        {
            "subject": subject,
            "body": shorten_email_body(body),
        }
    )

    return f"mailto:{urllib.parse.quote(str(to_email or '').strip())}?{params}"


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
                    st.error("Confirm the privacy checkbox before sending.")
                    return

                try:
                    message_id = send_summary_email(
                        recipient_email=recipient,
                        subject=subject,
                        text_body=body,
                    )

                    st.success(
                        "Email sent. No uploaded photo was attached. Recipient email was not saved."
                    )

                    st.caption(f"Email provider message ID: {message_id}")

                except Exception as error:
                    st.error(
                        "Could not send the email. Use the email draft backup below."
                    )

                    with st.expander("Technical details"):
                        st.code(str(error))
        else:
            st.info("Server-side email is disabled. Use the email draft backup below.")

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


def show_share_summary_panel(
    summary_title: str,
    summary_text: str,
    file_name: str,
    key_prefix: str,
) -> None:
    with st.expander("Share / export this summary"):
        st.warning(
            "Share only with people who should see this summary. "
            "Do not add names, addresses, medical history, medication lists, faces, "
            "mail, bills, medication bottles, or medical documents."
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