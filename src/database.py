    """
    Checks whether database saving is enabled.

    The app should work normally when this returns False.
    """

    value = os.getenv("DATABASE_ENABLED", "false").lower().strip()
    return value == "true"


def get_database_status_message():
    """
    Returns a safe status message for the app or debugging.
    Does not expose secrets.
    """

    if is_database_enabled():
        return "Database saving is enabled."

    return "Database saving is disabled."


def validate_anonymous_save_confirmation(confirmed):
    """
    Checks whether the user confirmed that no personal, medical,
    or real patient information is being saved.
    """

    if confirmed:
        return True, ""

    return (
        False,
        "Please confirm that this result contains no personal, medical, or real patient information.",
    )