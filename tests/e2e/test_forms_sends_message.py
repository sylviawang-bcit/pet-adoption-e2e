# GitHub issue #1: "Forms page shows success but never sends the message."
# Expected behavior: submitting /Forms sends a POST /Forms to the server.
# The success alert is not checked: form.html shows it without contacting the
# server, so it proves nothing.
# Marked xfail(strict=True) until issue #1 is fixed; remove the marker then.
import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Short wait: a real submit sends the request right away.
REQUEST_TIMEOUT_MS = 3000


@pytest.mark.xfail(
    strict=True,
    # Playwright's TimeoutError, not the built-in one. Setup checks below use
    # expect()/assert (AssertionError), so they cannot count as this xfail.
    raises=PlaywrightTimeoutError,
    reason="Issue #1: Forms page shows success but never sends the message",
)
def test_forms_submit_sends_post_request(page: Page):
    page.goto("/Forms")

    # Accept the native alert so it cannot block the page.
    page.on("dialog", lambda dialog: dialog.accept())

    form = page.locator("form")
    fields = {
        "input[name=name]": "Test User",
        "input[name=email]": "test.user@example.com",
        "input[name=phone]": "555-123-4567",
        "textarea[name=message]": "Hello, I would like to ask about adoption.",
    }
    for selector, value in fields.items():
        expect(form.locator(selector)).to_be_visible()
        form.locator(selector).fill(value)
    expect(form.locator("select[name=reason]")).to_be_visible()
    form.locator("select[name=reason]").select_option("adoption")

    # Make sure browser validation will not block the submit.
    assert form.evaluate("f => f.checkValidity()"), "form data is invalid"

    with page.expect_request(
        lambda request: request.method == "POST"
        and request.url.endswith("/Forms"),
        timeout=REQUEST_TIMEOUT_MS,
    ):
        form.get_by_role("button", name="Submit").click()
