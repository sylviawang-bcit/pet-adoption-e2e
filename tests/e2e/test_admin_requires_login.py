# GitHub issue #2: "/admin_dashboard and /add_pet open without login."
# Expected behavior: anonymous users are redirected to /login.
# Marked xfail(strict=True) until issue #2 is fixed; remove the marker then.
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Issue #2: /admin_dashboard and /add_pet open without login",
)
@pytest.mark.parametrize("path", ["/admin_dashboard", "/add_pet"])
def test_admin_page_redirects_to_login_when_logged_out(page: Page, path: str):
    page.goto(path)

    expect(page).to_have_url(re.compile(r"/login(\?.*)?$"))
