"""
report.py

This file creates the plain-English AI SafeHome safety report.

The report is meant for education and family review.
It is not a medical report.
"""

from datetime import date


def format_hazards(hazards):
    """
    Converts AI hazard dictionaries into readable report lines.
    """

    if not hazards:
        return ["No possible AI hazards were listed."]

    lines = []

    for index, hazard in enumerate(hazards, start=1):
        title = hazard.get("title", "Possible hazard")
        explanation = hazard.get("explanation", "No explanation provided.")
        recommendation = hazard.get("recommendation", "Review this area carefully.")

        lines.append(
            f"{index}. {title}\n"
            f"   Why it matters: {explanation}\n"
            f"   Suggested fix: {recommendation}"
        )

    return lines


def format_checklist_concerns(checklist_answers):
    """
    Returns only checklist answers that were Yes or Not sure.
    """

    concerns = []

    for answer in checklist_answers:
        response = answer.get("answer")
        answer_label = answer.get("answer_label", response)

        if response in ["yes", "not_sure"]:
            question = answer.get("question", "Checklist concern")
            concerns.append(f"- {question} Answer: {answer_label}")

    if not concerns:
        return ["No checklist concerns were marked Yes or Not sure."]

    return concerns


def generate_report(
    room_type,
    hazards,
    checklist_answers,
    score,
    risk_level,
    recommended_fixes,
    safety_disclaimer,
):
    """
    Creates a plain-English report as a string.

    Args:
        room_type: Selected room type.
        hazards: List of AI hazard dictionaries.
        checklist_answers: List of checklist answer dictionaries.
        score: Numeric score from 0 to 100.
        risk_level: Low Risk, Moderate Risk, or High Risk.
        recommended_fixes: List of suggested fixes.
        safety_disclaimer: Safety disclaimer text.

    Returns:
        str: Full report text.
    """

    today = date.today().strftime("%B %d, %Y")

    hazard_lines = format_hazards(hazards)
    checklist_lines = format_checklist_concerns(checklist_answers)

    if recommended_fixes:
        fix_lines = [
            f"{index}. {fix}"
            for index, fix in enumerate(recommended_fixes, start=1)
        ]
    else:
        fix_lines = ["No specific fixes were generated."]

    report = f"""
AI SafeHome Safety Report
Date: {today}

Room Checked:
{room_type}

Fall-Hazard Score:
{risk_level} — {score}/100

Possible Hazards Found by AI:
{chr(10).join(hazard_lines)}

Checklist Concerns:
{chr(10).join(checklist_lines)}

Recommended First Fixes:
{chr(10).join(fix_lines)}

Safety Disclaimer:
{safety_disclaimer}

Human Review Reminder:
AI may miss hazards or misunderstand a photo. Please review the room yourself and consider asking a qualified professional for serious safety concerns.

Privacy Reminder:
This app should be tested with staged, non-patient photos only. Do not upload faces, names, addresses, mail, bills, medication bottles, or medical documents.
""".strip()

    return report