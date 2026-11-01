# GitHub issue #3: "Invalid pet size crashes Add Pet with a 500 error and shows a debug traceback."
# Expected behavior: no 500, the user sees a clear error about size, and no
# pet is saved.
# Marked xfail(strict=True) until issue #3 is fixed; remove the marker then.
import re
import uuid

import pytest
from playwright.sync_api import Page, expect


class InvalidSizeNotHandled(Exception):
    """Raised only after the server answered the add-pet POST and handled the
    invalid size badly.

    Login and setup checks use expect()/assert (AssertionError) and a missing
    request raises Playwright's TimeoutError. Neither matches raises= below,
    so a failed login or a broken selector fails instead of xfailing.
    """


def pet_names(page: Page) -> list[str]:
    response = page.request.get("/pet_info")
    assert response.ok, f"/pet_info returned {response.status}"
    return [pet["name"] for pet in response.json()]


@pytest.mark.xfail(
    strict=True,
    raises=InvalidSizeNotHandled,
    reason="Issue #3: invalid pet size crashes Add Pet with a 500",
)
def test_add_pet_rejects_invalid_size(page: Page):
    # Log in first so this test keeps working once issue #2 protects /add_pet.
    page.goto("/login")
    page.locator("input[name=username]").fill("admin")
    page.locator("input[name=password]").fill("admin123")
    page.get_by_role("button", name="Sign In").click()
    expect(page).to_have_url(re.compile(r"/admin_dashboard$"))

    # add_pet returns early without checking size when no user exists.
    users = page.request.get("/user_info")
    assert users.ok and users.json(), "no users in the database"

    pet_name = f"E2E invalid size {uuid.uuid4().hex[:8]}"
    assert pet_name not in pet_names(page)

    page.goto("/add_pet")
    form = page.locator("form")
    for selector, value in {
        "input[name=name]": pet_name,
        "input[name=species]": "Dog",
        "input[name=breed]": "Beagle",
        "input[name=age]": "3",
        "input[name=color]": "Brown",
        "textarea[name=description]": "Friendly test dog.",
        "input[name=url]": "https://example.com/dog.jpg",
    }.items():
        expect(form.locator(selector)).to_be_visible()
        form.locator(selector).fill(value)
    form.locator("select[name=gender]").select_option("female")
    form.locator("select[name=house_trained]").select_option("House trained")

    # Simulate a client that sends a value the dropdown never offers (like
    # editing the option in DevTools): the server must not trust the form.
    size = form.locator("select[name=size]")
    size.locator("option[value=small]").evaluate("o => o.value = 'huge'")
    size.select_option(label="Small")
    expect(size).to_have_value("huge")

    # Make sure browser validation will not block the submit.
    assert form.evaluate("f => f.checkValidity()"), "form data is invalid"

    with page.expect_response(
        lambda response: response.request.method == "POST"
        and response.url.endswith("/add_pet"),
        timeout=5000,
    ) as response_info:
        form.get_by_role("button", name="Submit").click()
    response = response_info.value
    page.wait_for_load_state()

    body_text = page.locator("body").inner_text()
    saved = pet_name in pet_names(page)

    problems = []
    if response.status >= 500:
        problems.append(f"POST /add_pet returned {response.status}")
    if "Traceback" in body_text:
        problems.append("page shows a traceback")
    # The form label "Size" is always there; look for any other line about size.
    size_lines = [
        line for line in body_text.splitlines()
        if "size" in line.lower() and line.strip() != "Size"
    ]
    if not size_lines:
        problems.append("no error about size is shown")
    if saved:
        problems.append(f"pet {pet_name!r} was saved")
    if problems:
        raise InvalidSizeNotHandled("; ".join(problems))
