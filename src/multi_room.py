"""
multi_room.py

Creates a multi-room home safety summary for AI SafeHome.

This is still educational and non-medical.
It does not diagnose fall risk or guarantee fall prevention.
"""

from datetime import date


def get_home_priority_label(room_results):
    """
    Creates a simple home-level review label.

    This is not a medical risk label.
    It is only a home-safety review priority label.
    """

    if not room_results:
        return "No Rooms Checked"

    scores = [room["score"] for room in room_results]
    highest_score = max(scores)
    average_score = round(sum(scores) / len(scores))

    if highest_score >= 60 or average_score >= 60:
        return "High Priority Review"
    elif highest_score >= 30 or average_score >= 30:
        return "Moderate Priority Review"
    else:
        return "Low Priority Review"


def count_risk_levels(room_results):
    """
    Counts Low, Moderate, and High risk room labels.
    """

    counts = {
        "Low Risk": 0,
        "Moderate Risk": 0,
        "High Risk": 0,
    }

    for room in room_results:
        risk_level = room.get("risk_level", "Low Risk")

        if risk_level in counts:
            counts[risk_level] += 1

    return counts


def get_highest_scoring_room(room_results):
    """
    Finds the room with the highest score.
    """

    if not room_results:
        return None

    return max(room_results, key=lambda room: room.get("score", 0))


def get_unique_fixes(room_results, limit=10):
    """
    Combines recommended fixes across all rooms and removes duplicates.

    Handles both old string fixes and new dictionary fixes.
    """

    fixes = []
    seen = set()

    for room in room_results:
        for fix in room.get("recommended_fixes", []):
            if isinstance(fix, dict):
                fix_text = fix.get("text", "Review this area carefully.")
                priority = fix.get("priority", "Watch/Review")
                source = fix.get("source", room.get("room_type", "Room"))

                unique_key = fix_text

                if unique_key not in seen:
                    fixes.append(
                        {
                            "text": fix_text,
                            "priority": priority,
                            "source": source,
                        }
                    )
                    seen.add(unique_key)
            else:
                if fix not in seen:
                    fixes.append(
                        {
                            "text": fix,
                            "priority": "Watch/Review",
                            "source": room.get("room_type", "Room"),
                        }
                    )
                    seen.add(fix)

    priority_rank = {
        "Fix Now": 1,
        "Fix Soon": 2,
        "Watch/Review": 3,
    }

    fixes = sorted(
        fixes,
        key=lambda item: priority_rank.get(item.get("priority", "Watch/Review"), 99),
    )

    return fixes[:limit]

def get_repeated_concerns(room_results):
    """
    Counts hazard titles across rooms.
    """

    concern_counts = {}

    for room in room_results:
        for hazard in room.get("hazards", []):
            title = hazard.get("title", "Possible hazard")
            concern_counts[title] = concern_counts.get(title, 0) + 1

    sorted_concerns = sorted(
        concern_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return sorted_concerns


def build_home_summary(room_results, safety_disclaimer):
    """
    Creates a plain-English multi-room home safety summary.
    """

    today = date.today().strftime("%B %d, %Y")

    if not room_results:
        return "No rooms have been saved to the home summary yet."

    scores = [room["score"] for room in room_results]
    average_score = round(sum(scores) / len(scores))
    highest_room = get_highest_scoring_room(room_results)
    priority_label = get_home_priority_label(room_results)
    risk_counts = count_risk_levels(room_results)
    repeated_concerns = get_repeated_concerns(room_results)
    fixes = get_unique_fixes(room_results)

    room_lines = []

    for index, room in enumerate(room_results, start=1):
        room_lines.append(
            f"{index}. {room['room_type']} — "
            f"{room['risk_level']} — {room['score']}/100"
        )

    concern_lines = []

    if repeated_concerns:
        for concern, count in repeated_concerns[:8]:
            if count == 1:
                concern_lines.append(f"- {concern}")
            else:
                concern_lines.append(f"- {concern} appeared in {count} rooms")
    else:
        concern_lines.append("- No AI hazards were listed.")

    fix_lines = []

    if fixes:
        for index, fix in enumerate(fixes, start=1):
            fix_lines.append(
                f"{index}. [{fix.get('priority', 'Watch/Review')}] "
                f"{fix.get('text', 'Review this area carefully.')}"
            )
    else:
        fix_lines.append("No specific fixes were generated.")

    report = f"""
AI SafeHome Multi-Room Home Safety Summary
Date: {today}

Rooms Checked:
{chr(10).join(room_lines)}

Home Review Priority:
{priority_label}

Average Room Score:
{average_score}/100

Highest-Scoring Room:
{highest_room['room_type']} — {highest_room['risk_level']} — {highest_room['score']}/100

Room Risk Count:
Low Risk rooms: {risk_counts['Low Risk']}
Moderate Risk rooms: {risk_counts['Moderate Risk']}
High Risk rooms: {risk_counts['High Risk']}

Top Concerns Across Rooms:
{chr(10).join(concern_lines)}

Recommended First Fixes Across the Home:
{chr(10).join(fix_lines)}

Safety Disclaimer:
{safety_disclaimer}

Human Review Reminder:
AI may miss hazards or misunderstand a photo. Please review each room yourself and consider asking a qualified professional for serious safety concerns.

Privacy Reminder:
This app should be tested with staged, non-patient photos only. Do not upload faces, names, addresses, mail, bills, medication bottles, or medical documents.
""".strip()

    return report