"""
email_ui.py

Streamlit email/share UI helpers.
"""

import html
import urllib.parse
import uuid

import streamlit as st

MAX_RECIPIENTS = 5

try:
    from src.email_service import (
        get_email_status_message,
        is_email_enabled,
        is_valid_email_address,
        send_summary_email,
    )
except Exception as email_import_error:
    EMAIL_IMPORT_ERROR_MESSAGE = str(email_import_error)

    def is_email_enabled() -> bool:
        return False

    def is_valid_email_address(email: str) -> bool:
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


def _recipient_field_key(key_prefix: str, recipient_id: str) -> str:
    return f"{key_prefix}_recipient_field_{recipient_id}"


def _current_recipient_emails(key_prefix: str, recipient_entries: list[dict]) -> list[str]:
    emails = []
    for entry in recipient_entries:
        value = str(st.session_state.get(_recipient_field_key(key_prefix, entry["id"]), entry.get("email", ""))).strip().lower()
        if value:
            emails.append(value)
    return emails


def show_email_summary_panel(
    summary_title: str,
    summary_text: str,
    default_subject: str,
    key_prefix: str,
) -> None:
    with st.container(border=True):
        st.subheader("Email this summary")

        st.caption(get_email_status_message())

        signed_in_email = str(st.session_state.get("home_id") or "").strip().lower()
        recipients_key = f"{key_prefix}_recipients"
        if recipients_key not in st.session_state:
            st.session_state[recipients_key] = [{
                "id": uuid.uuid4().hex,
                "email": signed_in_email if is_valid_email_address(signed_in_email) else "",
            }]

        recipient_entries = st.session_state[recipients_key]
        # Upgrade recipient state created by the earlier version of this UI.
        if recipient_entries and isinstance(recipient_entries[0], str):
            recipient_entries = [
                {"id": uuid.uuid4().hex, "email": email}
                for email in recipient_entries
            ]
            st.session_state[recipients_key] = recipient_entries
        if not recipient_entries:
            recipient_entries = [{"id": uuid.uuid4().hex, "email": ""}]
            st.session_state[recipients_key] = recipient_entries

        st.write("Recipients")

        for index, entry in enumerate(list(recipient_entries)):
            with st.container(key=f"recipient-row-{key_prefix}-{entry['id']}"):
                field_label = "Recipient email" if index == 0 else f"Additional recipient {index + 1}"
                st.caption(field_label)
                email_col, remove_col = st.columns([8, 1])
                field_key = _recipient_field_key(key_prefix, entry["id"])
                if field_key not in st.session_state:
                    st.session_state[field_key] = entry.get("email", "")
                email_col.text_input(
                    field_label,
                    placeholder="name@example.com",
                    key=field_key,
                    label_visibility="collapsed",
                )
                if remove_col.button("×", key=f"{key_prefix}_remove_recipient_{entry['id']}", help="Remove this email address"):
                    st.session_state[recipients_key] = [item for item in recipient_entries if item["id"] != entry["id"]]
                    st.rerun()

        if len(recipient_entries) < MAX_RECIPIENTS and st.button("Add new email address", key=f"{key_prefix}_add_recipient"):
            current_emails = _current_recipient_emails(key_prefix, recipient_entries)
            st.session_state[recipients_key] = [
                {"id": entry["id"], "email": email}
                for entry, email in zip(recipient_entries, current_emails)
            ] + [{"id": uuid.uuid4().hex, "email": ""}]
            st.rerun()
        elif len(recipient_entries) >= MAX_RECIPIENTS:
            st.caption("Up to 5 email addresses can receive this summary.")

        subject = st.text_input(
            "Email subject",
            value=default_subject,
            key=f"{key_prefix}_subject",
        )

        body = f"{summary_title}\n\n{summary_text}\n\n{build_email_footer()}".strip()

        with st.expander("Review email message"):
            st.text_area(
                "Email body preview",
                value=body,
                height=220,
                key=f"{key_prefix}_body",
            )

        if is_email_enabled():
            if st.button(
                "Send Email from AI SafeHome",
                key=f"{key_prefix}_server_send",
                type="primary",
            ):
                try:
                    recipients = _current_recipient_emails(key_prefix, recipient_entries)
                    if not recipients:
                        raise RuntimeError("Add at least one recipient email address.")
                    if any(not is_valid_email_address(email) for email in recipients):
                        raise RuntimeError("Enter a valid email address in every recipient box.")
                    if len(set(recipients)) != len(recipients):
                        raise RuntimeError("Each recipient email should appear only once.")

                    for recipient in recipients:
                        send_summary_email(
                            recipient_email=recipient,
                            subject=subject,
                            text_body=body,
                        )

                    st.success(
                        f"Email sent to {len(recipients)} recipient{'s' if len(recipients) != 1 else ''}. No uploaded photo was attached."
                    )

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

        recipients = _current_recipient_emails(key_prefix, recipient_entries)
        link = create_mailto_link(",".join(recipients), subject, body)

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
