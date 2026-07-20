from typing import Any, Dict, List, Optional

from src.constants import (
    CATEGORY_PRIORITY,
    PRIORITY_FIX_NOW,
    PRIORITY_FIX_SOON,
    PRIORITY_ORDER,
    PRIORITY_WATCH_REVIEW,
)


def get_priority_for_category(category: Optional[str]) -> str:
    return CATEGORY_PRIORITY.get(category or "unclear", PRIORITY_WATCH_REVIEW)


def get_priority_for_hazard(hazard: Dict[str, Any]) -> str:
    return get_priority_for_category(hazard.get("category"))


def get_priority_css_class(priority: str) -> str:
    if priority == PRIORITY_FIX_NOW:
        return "priority-fix-now"

    if priority == PRIORITY_FIX_SOON:
        return "priority-fix-soon"

    return "priority-watch-review"


def sort_by_priority(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: PRIORITY_ORDER.get(
            item.get("priority", PRIORITY_WATCH_REVIEW),
            99,
        ),
    )