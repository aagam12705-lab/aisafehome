"""Keep the deployed AI SafeHome Streamlit app active with a real browser visit."""

import time

from playwright.sync_api import sync_playwright


APP_URL = "https://ai-safehome.streamlit.app/"
PAGE_LOAD_TIMEOUT_MS = 120_000
SESSION_WAIT_SECONDS = 30


def main() -> None:
    print(f"Opening AI SafeHome: {APP_URL}", flush=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(
                APP_URL,
                wait_until="domcontentloaded",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )

            print(f"Page title: {page.title()}", flush=True)
            print(f"Final URL: {page.url}", flush=True)

            # Keep the browser session open long enough for Streamlit to finish
            # establishing its WebSocket connection and loading the app.
            time.sleep(SESSION_WAIT_SECONDS)

            print("AI SafeHome keep-alive visit completed successfully.", flush=True)
        finally:
            browser.close()
            print("Browser closed cleanly.", flush=True)


if __name__ == "__main__":
    main()
