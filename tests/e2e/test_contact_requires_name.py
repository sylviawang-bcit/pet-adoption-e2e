# GitHub issue #4: "Contact form accepts an empty name and still shows 'Message Sent!'."
# Expected behavior: the server rejects an empty name with 400, and the page
# does not show "Message Sent!".
# Marked xfail(strict=True) until issue #4 is fixed; remove the marker then.
import re

import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# The app sends "Message Sent !" (with a space); match with or without it.
SUCCESS_TEXT = re.compile(r"Message Sent\s*!")


class EmptyNameAccepted(Exception):
    """Raised only when the server answered and accepted the empty name.

    Setup checks use expect()/assert (AssertionError) and a missing request
    raises Playwright's TimeoutError. Neither matches raises= below, so a
    broken selector or a page that never posts fails instead of xfailing.
    """


@pytest.mark.xfail(
    strict=True,
    raises=EmptyNameAccepted,
    reason="Issue #4: contact form accepts an empty name",
)
def test_contact_rejects_empty_name(page: Page):
    page.goto("/contact")

    form = page.locator("#contactForm")
    name_input = form.locator("input[name=name]")
    expect(name_input).to_be_visible()

    # Simulate a client that skips browser validation (like removing
    # "required" in DevTools): the server must not rely on the browser.
    name_input.evaluate("el => el.removeAttribute('required')")
    assert name_input.evaluate("el => !el.hasAttribute('required')")
    expect(name_input).to_have_value("")

    for selector, value in {
        "input[name=email]": "test.user@example.com",
        "textarea[name=message]": "Hello, I have a question about adoption.",
    }.items():
        expect(form.locator(selector)).to_be_visible()
        form.locator(selector).fill(value)

    # Make sure browser validation will not block the submit.
    assert form.evaluate("f => f.checkValidity()"), "form data is invalid"

    with page.expect_response(
        lambda response: response.request.method == "POST"
        and response.url.endswith("/contact"),
        timeout=3000,
    ) as response_info:
        form.get_by_role("button", name="Send").click()
    response = response_info.value

    problems = []
    if response.status != 400:
        problems.append(f"POST /contact returned {response.status}, expected 400")
    try:
        page.get_by_text(SUCCESS_TEXT).wait_for(state="visible", timeout=1500)
        problems.append('"Message Sent!" was shown')
    except PlaywrightTimeoutError:
        pass  # Not shown: correct.
    if problems:
        raise EmptyNameAccepted("; ".join(problems))
