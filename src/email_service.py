"""
email_service.py

Privacy-safe server-side email sending for AI SafeHome.

Uses Brevo transactional email API.
"""

import os
import re
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_SEND_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


def get_env_value(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)

    if value is not None and value != "":
        return value

    try:
        import streamlit as st

        if name in st.secrets:
            secret_value = st.secrets[name]

            if secret_value is not None and secret_value != "":
                return str(secret_value)
    except Exception:
        pass

    return default


def is_email_enabled() -> bool:
    value = get_env_value("EMAIL_ENABLED", "false")
    return str(value).lower().strip() == "true"


def get_email_status_message() -> str:
    if is_email_enabled():
        return "Server-side email is enabled."
    return "Server-side email is disabled."


def is_valid_email_address(email: str) -> bool:
    if not email:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email.strip()) is not None


def get_brevo_settings() -> dict:
    api_key = get_env_value("BREVO_API_KEY")
    sender_email = get_env_value("BREVO_SENDER_EMAIL")
    sender_name = get_env_value("BREVO_SENDER_NAME", "AI SafeHome")

    if not api_key:
        raise RuntimeError("Missing BREVO_API_KEY.")

    if not sender_email:
        raise RuntimeError("Missing BREVO_SENDER_EMAIL.")

    return {
        "api_key": api_key,
        "sender_email": sender_email,
        "sender_name": sender_name,
    }


def build_html_email_body(text_body: str) -> str:
    escaped = (
        str(text_body)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    escaped = escaped.replace("\n", "<br>")

    return f"""
<html>
  <body>
    <div style="font-family: Arial, sans-serif; line-height: 1.5;">
      {escaped}
    </div>
  </body>
</html>
""".strip()


def send_summary_email(
    recipient_email: str,
    subject: str,
    text_body: str,
) -> str:
    if not is_email_enabled():
        raise RuntimeError("Server-side email is disabled.")

    recipient_email = str(recipient_email or "").strip()

    if not is_valid_email_address(recipient_email):
        raise RuntimeError("Enter a valid recipient email address.")

    if not subject or not str(subject).strip():
        raise RuntimeError("Email subject is required.")

    if not text_body or not str(text_body).strip():
        raise RuntimeError("Email body is required.")

    settings = get_brevo_settings()

    payload = {
        "sender": {
            "name": settings["sender_name"],
            "email": settings["sender_email"],
        },
        "to": [
            {
                "email": recipient_email,
            }
        ],
        "subject": str(subject).strip(),
        "htmlContent": build_html_email_body(text_body),
        "textContent": str(text_body),
    }

    headers = {
        "accept": "application/json",
        "api-key": settings["api_key"],
        "content-type": "application/json",
    }

    response = requests.post(
        BREVO_SEND_EMAIL_URL,
        headers=headers,
        json=payload,
        timeout=20,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Email provider error {response.status_code}: {response.text}"
        )

    data = response.json()
    return str(data.get("messageId", "sent"))