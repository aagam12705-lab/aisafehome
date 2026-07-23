"""
photo_quality.py

Basic photo quality checks for AI SafeHome.

This uses simple image heuristics:
- resolution
- brightness
- contrast
- edge sharpness

It does not identify people, objects, addresses, or medical information.
"""

from typing import Any, Dict, List

from PIL import Image, ImageFilter, ImageStat


def get_photo_quality_label(issue_count: int, severe_count: int) -> str:
    if severe_count >= 2:
        return "Poor"

    if severe_count == 1 or issue_count >= 2:
        return "Caution"

    return "Good"


def analyze_uploaded_photo_quality(uploaded_file: Any) -> Dict[str, Any]:
    """
    Returns a photo quality summary.

    This function preserves the uploaded file pointer so Streamlit can still
    preview and analyze the image afterward.
    """

    if uploaded_file is None:
        return {
            "label": "No photo",
            "issues": ["No photo was uploaded."],
            "suggestions": ["Upload a staged room photo."],
            "metrics": {},
        }

    current_position = uploaded_file.tell()

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image.load()
    finally:
        uploaded_file.seek(current_position)

    width, height = image.size

    grayscale = image.convert("L")

    brightness_stat = ImageStat.Stat(grayscale)
    brightness = round(brightness_stat.mean[0], 1)
    contrast = round(brightness_stat.stddev[0], 1)

    edge_image = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edge_image)
    edge_score = round(edge_stat.stddev[0], 1)

    issues: List[str] = []
    suggestions: List[str] = []
    severe_count = 0

    if width < 400 or height < 300:
        issues.append("Photo resolution is very low.")
        suggestions.append("Use a larger, clearer room photo.")
        severe_count += 1
    elif width < 640 or height < 480:
        issues.append("Photo resolution is a little low.")
        suggestions.append("Move closer or use a higher-resolution photo.")

    if brightness < 45:
        issues.append("Photo appears very dark.")
        suggestions.append("Turn on lights or retake the photo with better lighting.")
        severe_count += 1
    elif brightness < 70:
        issues.append("Photo may be dark.")
        suggestions.append("Add more light so floor hazards are easier to see.")

    if brightness > 235:
        issues.append("Photo appears very bright or washed out.")
        suggestions.append("Retake the photo with less glare or direct light.")
        severe_count += 1
    elif brightness > 215:
        issues.append("Photo may be too bright.")
        suggestions.append("Reduce glare so floor edges and objects are easier to see.")

    if contrast < 15:
        issues.append("Photo has very low contrast.")
        suggestions.append("Use clearer lighting so objects and floor edges stand out.")
        severe_count += 1
    elif contrast < 25:
        issues.append("Photo may have low contrast.")
        suggestions.append("Improve lighting or camera focus before analysis.")

    if edge_score < 5:
        issues.append("Photo may be very blurry.")
        suggestions.append("Hold the camera steady and retake the photo.")
        severe_count += 1
    elif edge_score < 9:
        issues.append("Photo may be slightly blurry.")
        suggestions.append("Retake the photo if small hazards are hard to see.")

    label = get_photo_quality_label(
        issue_count=len(issues),
        severe_count=severe_count,
    )

    if not issues:
        issues.append("Photo quality looks usable.")
        suggestions.append("Continue to AI analysis, then review the room yourself.")

    return {
        "label": label,
        "issues": issues,
        "suggestions": suggestions,
        "metrics": {
            "width": width,
            "height": height,
            "brightness": brightness,
            "contrast": contrast,
            "edge_score": edge_score,
        },
    }


def build_photo_quality_text(quality: Dict[str, Any]) -> str:
    label = quality.get("label", "Unknown")
    issues = quality.get("issues", [])
    suggestions = quality.get("suggestions", [])
    metrics = quality.get("metrics", {})

    issue_text = "\n".join(f"- {item}" for item in issues) or "- None"
    suggestion_text = "\n".join(f"- {item}" for item in suggestions) or "- None"

    return f"""
Photo Quality: {label}

Issues:
{issue_text}

Suggestions:
{suggestion_text}

Metrics:
- Width: {metrics.get("width", "Unknown")}
- Height: {metrics.get("height", "Unknown")}
- Brightness: {metrics.get("brightness", "Unknown")}
- Contrast: {metrics.get("contrast", "Unknown")}
- Edge score: {metrics.get("edge_score", "Unknown")}
""".strip()