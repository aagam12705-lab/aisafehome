"""
report_builder.py

Builds printable/shareable report text for AI SafeHome.
"""

from datetime import date
from typing import Any, Dict, List
from src.photo_quality import build_photo_quality_text
import streamlit as st
from src.constants import SAFETY_DISCLAIMER
from src.fixes import build_top_fixes_text, get_recommended_first_fixes
from src.priorities import get_priority_for_hazard
from src.scoring import format_score_explanation


def build_hazard_lines(hazards: List[Dict[str, Any]]) -> str:
    """
    Builds the hazard section of the report.
    """

    if not hazards:
        return "No possible AI hazards were listed."

    lines = []

    for index, hazard in enumerate(hazards, start=1):
        lines.append(
            f"{index}. [{get_priority_for_hazard(hazard)}] "
            f"{hazard.get('title', 'Possible hazard')}\n"
            f"   Why it matters: {hazard.get('explanation', '')}\n"
            f"   Suggested fix: {hazard.get('recommendation', '')}"
        )

    return "\n".join(lines)


def build_checklist_lines(checklist_answers: List[Dict[str, Any]]) -> str:
    """
    Builds the checklist section of the report.
    """

    lines = []

    for answer in checklist_answers:
        if answer.get("answer") in ["no", "not_sure"] or answer.get("answer_label") == "Skipped":
            lines.append(
                f"- {answer.get('question')} Answer: {answer.get('answer_label')}"
            )

    if not lines:
        return "No checklist concerns were marked Yes or Not sure."

    return "\n".join(lines)


def build_report_text() -> str:
    """
    Builds the main one-room safety report from Streamlit session state.
    """

    room_type = st.session_state.get("room_type", "Room")
    room_id = st.session_state.get("current_room_id") or "No Room ID"

    ai_result = st.session_state.get("ai_result") or {}
    hazards = ai_result.get("hazards", [])
    analysis_mode = ai_result.get("analysis_mode", "sample")
    checklist_answers = st.session_state.get("checklist_answers", [])

    score = st.session_state.get("score", 0)
    risk_level = st.session_state.get("risk_level", "Low Risk")
    score_breakdown = st.session_state.get("score_breakdown") or {}
    photo_quality = st.session_state.get("photo_quality") or {}
    photo_quality_text = build_photo_quality_text(photo_quality)
    score_explanation = format_score_explanation(score_breakdown)

    fixes = get_recommended_first_fixes(
        ai_hazards=hazards,
        checklist_answers=checklist_answers,
        limit=5,
    )
    analysis_note = (
        "Real AI analysis"
        if analysis_mode == "real"
        else "Sample analysis — these hazards are not findings from the uploaded photo."
    )
    return f"""
AI SafeHome Safety Report
Date: {date.today().strftime('%B %d, %Y')}

Room Checked:
{room_type}

Room ID:
{room_id}

Analysis Status:
{analysis_note}

Photo Quality:
{photo_quality_text}

Fall-Hazard Score:
{risk_level} — {score}/100

Score Explanation:
{score_explanation}

Possible Hazards Found by AI:
{build_hazard_lines(hazards)}

Checklist Concerns:
{build_checklist_lines(checklist_answers)}

Top 5 Fixes:
{build_top_fixes_text(fixes)}

Safety Disclaimer:
{SAFETY_DISCLAIMER}

Human Review Reminder:
AI may miss hazards or misunderstand a photo. Please review the room yourself and consider asking a qualified professional for serious safety concerns.

""".strip()
