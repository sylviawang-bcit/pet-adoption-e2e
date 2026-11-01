# Second-Look Pet Adoption: E2E Tests

[![E2E tests](https://github.com/sylviawang-bcit/pet-adoption-e2e/actions/workflows/e2e.yml/badge.svg)](https://github.com/sylviawang-bcit/pet-adoption-e2e/actions/workflows/e2e.yml)

## What this is

The Flask app in this repo is "Second-Look Pet Adoption", a team project from
the BCIT ACIT 2911 course (Scrum, May 2026). I did not build the whole app.
In this repo, I set it up to run locally, checked bugs by hand, wrote them up
as GitHub issues, and built an end-to-end (E2E) test suite for them with
Claude Code, using pytest and Playwright.

The original app was built by a team of 5 students. Original repo:
[marvinursua8/ACIT-2911---Agile-Development-Project](https://github.com/marvinursua8/ACIT-2911---Agile-Development-Project)

## Each test traces back to an issue

| Issue                                                              | Title                                                                         | How a user hits it                                                                                                                                     | Test file                                 | Status            |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- | ----------------- |
| [#1](https://github.com/sylviawang-bcit/pet-adoption-e2e/issues/1) | Forms page shows success but never sends the message                          | Fill in every field on `/Forms` and click Submit. A success alert shows, but nothing is sent to the server.                                            | `tests/e2e/test_forms_sends_message.py`   | xfail until fixed |
| [#2](https://github.com/sylviawang-bcit/pet-adoption-e2e/issues/2) | Admin pages open without login                                                | Open `/admin_dashboard` or `/add_pet` without logging in. Both pages open.                                                                             | `tests/e2e/test_admin_requires_login.py`  | xfail until fixed |
| [#3](https://github.com/sylviawang-bcit/pet-adoption-e2e/issues/3) | Invalid pet size crashes Add Pet with a 500 error and shows a debug traceback | On `/add_pet`, change the "small" option value to "huge" in DevTools and submit. The server returns 500 and shows a traceback.                         | `tests/e2e/test_add_pet_invalid_size.py`  | xfail until fixed |
| [#4](https://github.com/sylviawang-bcit/pet-adoption-e2e/issues/4) | Contact form accepts an empty name and still shows "Message Sent!"            | On `/contact`, remove `required` from the name field in DevTools, leave it empty, and send. The server returns 200 and the page shows "Message Sent!". | `tests/e2e/test_contact_requires_name.py` | xfail until fixed |

Each test file starts with a comment that links to its issue. Each test
checks the correct behavior, so it fails while the bug is there. When an
issue is fixed, remove the `xfail` marker from its test.

Issues #1 and #4 have comments explaining why a quick fix would not be enough.

## How the tests avoid false results

An `xfail` test that fails for the wrong reason still shows up as "xfailed",
so a broken test can look the same as a real bug. The suite guards against
this in three ways.

**`xfail(strict=True)` with a narrow `raises=`.**

- `strict=True`: if the bug is fixed and the test passes, the run fails, as
  a reminder to remove the marker.
- `raises=` lists the only exception that counts as the expected failure.
  Any other exception fails the run.
  - Issue #2 uses `AssertionError` from the URL check.
  - Issue #1 uses Playwright's `TimeoutError`, because no POST request is
    sent. This is not Python's built-in `TimeoutError`.
  - Issues #3 and #4 each define their own exception
    (`InvalidSizeNotHandled`, `EmptyNameAccepted`). The test raises it only
    after the server has actually answered the request.
- Setup steps fail with `AssertionError`, so they can't pass for the
  expected failure. Setup includes logging in, finding form fields, and
  checking the form is valid.
- Each test was also run against changed copies to confirm this: a
  misspelled selector, a simulated fix, and a form that never posts.

**Health check before any test.** `tests/e2e/conftest.py` asks the home page
for HTTP 200 and the text "Second-Look". If that fails, `pytest.exit` stops
the run before any test, so "the app is not running" can never look like an
expected failure.

**Port 5001, not 5000.** On macOS, the AirPlay Receiver listens on port 5000
and answers HTTP 403. When the app was on port 5000 and Flask was stopped,
the tests still loaded a page (AirPlay's 403). The URL check failed with
`AssertionError`, and the tests showed as "xfailed" without ever reaching the
app. The app now runs on port 5001, and the health check catches this case.

**No test depends on which pet is featured.** The home page shows one random
pet on each load (`fn.Random()` with `.limit(1)` in `index()`), so a check for
a specific pet there would pass or fail by chance. The health check only looks
for "Second-Look", which is always on the page.

## How to run

You need [uv](https://docs.astral.sh/uv/). uv installs the Python version in
`.python-version` (3.14).

```bash
uv sync                                  # install dependencies
uv run playwright install chromium       # install the test browser

mkdir -p instance                        # the database folder is not in git
uv run python seed.py                    # reset the database: 4 pets, 1 admin (admin / admin123)

uv run python run.py                     # start the app on http://127.0.0.1:5001
```

In a second terminal:

```bash
uv run pytest tests/e2e -v
```

Expected result: `5 xfailed`. Issue #2 has two test cases, one for each
page.

`seed.py` deletes all pets, images and admins and adds them again. Run it
whenever you want a clean database. Stop the app with Ctrl+C when you are
done. If port 5001 still answers after that, check for a leftover server with
`lsof -i :5001`.

### CI

`.github/workflows/e2e.yml` runs on every push and pull request:

1. Installs uv, Python, the dependencies and Playwright Chromium on
   `ubuntu-latest`.
2. Creates a fresh database with `seed.py`.
3. Starts the app in the background on `127.0.0.1:5001` with
   `flask --app run:app run`, not `python run.py`. That keeps debug mode and
   its auto-reloader out of CI.
4. Waits up to 30 seconds for the home page to answer. If it never does, the
   job fails with a clear message.
5. Runs `pytest tests/e2e`.
6. If the job fails, uploads the server log as the `server-log` artifact.

The CI run passes with `5 xfailed` in the "Run E2E tests" step.

## Other findings (not issues yet)

These come from reading the code. They are not GitHub issues and have no
tests yet.

- **Gender case mismatch.** `seed.py` stores "Male" and "Female", but the
  Add Pet form (`add_pet.html`) sends "male" and "female", so the database
  mixes both spellings. The page font makes them look the same, but filtering
  or counting by gender would miss some pets.
- **Image URL field.** The Image URL input on `/add_pet` is
  `type="text"`, and the server saves whatever is sent without checking that
  it is a URL. The value is placed inside `style="background-image:
url('...')"` on the home, adopt and gallery pages.
  When I added a pet with Image URL `abc`, the server saved it with no error,
  and the pet's card on `/adopt` showed an empty gray image area. The user
  gets no message that the image is invalid.
- **Loose email check.** The only email check is the browser's
  `type="email"`. It accepts addresses like `aaabbb@cccc`, which appears in
  the server log in issue #4. Neither `/contact` nor `/Forms` checks the
  email format on the server.

## Known limits

- **A green CI run does not prove there were exactly 5 xfails.** pytest
  exits with success for any mix of xfailed and passed tests. Check for
  `5 xfailed` in the "Run E2E tests" step of the log.
- **The "pet was not saved" check in the issue #3 test was never run against
  a real fix.** The simulated fixes faked the server's response in the
  browser, so the request never reached the database. On the current app the
  500 error rolls back the save, so nothing is stored either way.
- **The tests use the app's real database.** Most tests save nothing. If a
  future broken fix for issue #3 saved the pet, the test would catch it but
  would also leave that pet in the database. CI starts from a fresh database
  every run.

## AI use

This test suite was built with Claude Code. [AI_NOTES.md](AI_NOTES.md)
records each step: what I asked, what the AI got wrong, how I found it, and
the fix.
