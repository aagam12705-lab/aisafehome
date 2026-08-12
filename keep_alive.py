"""Keep the deployed AI SafeHome Streamlit app active with a real browser visit."""

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

            # Wait for the browser load event and for the page to render useful
            # content. Streamlit's internal data-testid values can change
            # between releases, so do not depend on one private CSS selector.
            # Streamlit keeps a WebSocket open, so waiting for network-idle
            # would never reliably finish.
            page.wait_for_load_state("load", timeout=PAGE_LOAD_TIMEOUT_MS)
            page.locator("body").wait_for(
                state="visible",
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )
            page.wait_for_function(
                """
                () => {
                    const body = document.body;
                    if (!body) return false;
                    const text = (body.innerText || '').trim();
                    const hasStreamlitContent = Boolean(
                        document.querySelector('[data-testid^="st-"]') ||
                        document.querySelector('iframe') ||
                        document.querySelector('main')
                    );
                    return text.length > 0 || hasStreamlitContent;
                }
                """,
                timeout=PAGE_LOAD_TIMEOUT_MS,
            )

            print(f"Page title: {page.title()}", flush=True)
            print(f"Final URL: {page.url}", flush=True)

            # Keep the browser session open long enough for Streamlit to finish
            # establishing its WebSocket connection and loading the app.
            page.wait_for_timeout(SESSION_WAIT_SECONDS * 1000)

            print("AI SafeHome keep-alive visit completed successfully.", flush=True)
        finally:
            browser.close()
            print("Browser closed cleanly.", flush=True)


if __name__ == "__main__":
    main()
