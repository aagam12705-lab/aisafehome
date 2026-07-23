"""
trends.py

Score trend helpers for AI SafeHome.
"""

from typing import Any, Dict, List


def sort_checks_oldest_to_newest(checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(checks, key=lambda row: str(row.get("created_at", "")))


def build_score_trend_rows(checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ordered_checks = sort_checks_oldest_to_newest(checks)

    rows = []

    for index, check in enumerate(ordered_checks, start=1):
        rows.append(
            {
                "Check Number": index,
                "Saved At": str(check.get("created_at", "Unknown")).replace("T", " "),
                "Score": int(check.get("score") or 0),
                "Risk Label": check.get("risk_level", "Unknown"),
                "Check ID": check.get("id", ""),
            }
        )

    return rows


def get_trend_summary(checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = build_score_trend_rows(checks)

    if len(rows) < 2:
        return {
            "has_trend": False,
            "message": "Save at least two checks for this room to see a trend.",
            "first_score": None,
            "latest_score": None,
            "change": 0,
            "direction": "Not enough data",
        }

    first_score = rows[0]["Score"]
    latest_score = rows[-1]["Score"]
    change = latest_score - first_score

    if change < 0:
        direction = "Improving"
        message = f"Score improved by {abs(change)} points since the first saved check."
    elif change > 0:
        direction = "Needs attention"
        message = f"Score increased by {change} points since the first saved check."
    else:
        direction = "No change"
        message = "Score stayed the same since the first saved check."

    return {
        "has_trend": True,
        "message": message,
        "first_score": first_score,
        "latest_score": latest_score,
        "change": change,
        "direction": direction,
    }


def build_trend_summary_text(room_id: str, checks: List[Dict[str, Any]]) -> str:
    rows = build_score_trend_rows(checks)
    trend = get_trend_summary(checks)

    if not rows:
        return f"No saved checks found for {room_id}."

    lines = []

    for row in rows:
        lines.append(
            f"- Check {row['Check Number']}: {row['Score']}/100, "
            f"{row['Risk Label']}, saved at {row['Saved At']}"
        )

    return f"""
AI SafeHome Room Score Trend

Room ID:
{room_id}

Trend:
{trend["direction"]}

Summary:
{trend["message"]}

Score History:
{chr(10).join(lines)}

Reminder:
Lower scores mean fewer possible fall hazards. AI may miss hazards, so human review is still recommended.
""".strip()