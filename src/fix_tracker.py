"""
fix_tracker.py

Tracks the status of Top 5 fixes during the current app session.
"""

import hashlib
import html
from typing import Any, Dict, List

import streamlit as st


FIX_STATUS_OPTIONS = [
    "Not started",
    "In progress",
    "Fixed",
    "Need help",
]


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def get_fix_key(fix: Dict[str, Any]) -> str:
    """
    Creates a stable key for one recommended fix.
    """

    raw = f"{fix.get('category', '')}|{fix.get('source', '')}|{fix.get('text', '')}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    return f"fix_{digest}"


def get_fix_statuses() -> Dict[str, str]:
    if "fix_statuses" not in st.session_state:
        st.session_state["fix_statuses"] = {}

    return st.session_state["fix_statuses"]


def get_fix_notes() -> Dict[str, str]:
    if "fix_notes" not in st.session_state:
        st.session_state["fix_notes"] = {}

    return st.session_state["fix_notes"]


def get_status_counts(fixes: List[Dict[str, Any]]) -> Dict[str, int]:
    statuses = get_fix_statuses()

    counts = {
        "Not started": 0,
        "In progress": 0,
        "Fixed": 0,
        "Need help": 0,
    }

    for fix in fixes:
        key = get_fix_key(fix)
        status = statuses.get(key, "Not started")

        if status not in counts:
            status = "Not started"

        counts[status] += 1

    return counts


def show_fix_tracker(fixes: List[Dict[str, Any]]) -> None:
    """
    Shows interactive fix status controls.
    """

    st.subheader("Fix Tracker")

    if not fixes:
        st.info("No fixes are available to track yet.")
        return

    statuses = get_fix_statuses()
    notes = get_fix_notes()

    counts = get_status_counts(fixes)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Not Started", counts["Not started"])
    col2.metric("In Progress", counts["In progress"])
    col3.metric("Fixed", counts["Fixed"])
    col4.metric("Need Help", counts["Need help"])

    st.caption(
        "Use this to track what has been fixed. This first version tracks fixes during the current session and includes them in the report."
    )

    for fix in fixes:
        key = get_fix_key(fix)

        if key not in statuses:
            statuses[key] = "Not started"

        if key not in notes:
            notes[key] = ""

        st.markdown(
            f"""
            <div class="plain-card">
                <strong>Fix {safe_text(fix.get("rank"))}: {safe_text(fix.get("priority"))}</strong><br>
                {safe_text(fix.get("text"))}<br>
                <span class="small-muted">Source: {safe_text(fix.get("source"))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_status = statuses.get(key, "Not started")

        if current_status not in FIX_STATUS_OPTIONS:
            current_status = "Not started"

        selected_status = st.selectbox(
            "Fix status",
            FIX_STATUS_OPTIONS,
            index=FIX_STATUS_OPTIONS.index(current_status),
            key=f"{key}_status_select",
        )

        statuses[key] = selected_status

        note = st.text_input(
            "Optional note",
            value=notes.get(key, ""),
            placeholder="Example: taped cord to wall, still need rug backing",
            key=f"{key}_note_input",
        )

        notes[key] = note

        st.divider()


def get_fix_tracker_text(fixes: List[Dict[str, Any]]) -> str:
    """
    Builds plain text version for reports and email summaries.
    """

    if not fixes:
        return "No fixes were tracked."

    statuses = get_fix_statuses()
    notes = get_fix_notes()

    lines = []

    for index, fix in enumerate(fixes, start=1):
        key = get_fix_key(fix)
        status = statuses.get(key, "Not started")
        note = notes.get(key, "")

        line = (
            f"{index}. [{status}] {fix.get('text')}\n"
            f"   Priority: {fix.get('priority')}\n"
            f"   Source: {fix.get('source')}"
        )

        if note:
            line += f"\n   Note: {note}"

        lines.append(line)

    return "\n".join(lines)