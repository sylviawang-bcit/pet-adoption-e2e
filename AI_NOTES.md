# AI Notes

Tools: Claude Code (writing tests), Claude chat (planning and code reading).
For each step: what I asked, what the AI got wrong, how I found it, and the fix.

## 1. Forms page bug: the AI's guess was wrong (Oct 31)

- Asked: an AI assistant read routes.py and guessed that /Forms would return
  "All fields are required" if the phone field was empty.
- Wrong: In the browser, the form always showed "Form submitted successfully!".
- How I found it: I watched the server log while submitting. There was no
  POST /Forms at all. form.html only calls alert() and never sends the data.
- Lesson: reading the backend was not enough. I had to test the real page.

## 2. First E2E test for issue #2 (Oct 31)

- Asked Claude Code for one Playwright test: /admin_dashboard should redirect
  to /login when not logged in.
- Result: no mistake. It checked the real routes and confirmed the 200 response
  against the running server before writing the test. The test failed as
  expected because the bug is real.

## 3. xfail could hide setup problems (Oct 31)

- After adding xfail(strict=True), Claude Code pointed out that xfail counts
  any error as "expected", even if the server is not running.
- It suggested raises=AssertionError so only the real bug counts.

## 4. raises=AssertionError did not work on macOS (Oct 31)

- Claude Code said a stopped server would now fail the run. It only checked
  the code and did not run it.
- I stopped Flask and ran the tests: still 2 xfailed.
- The browser showed HTTP 403 at 127.0.0.1:5000. The macOS AirPlay Receiver
  listens on port 5000. So page.goto loaded a page, the URL check failed with
  AssertionError, and xfail hid it. The tests looked fine but never reached
  our app.
- Also wrong: earlier I was told 127.0.0.1 avoids AirPlay. It only works while
  Flask is running.
- Fix: moved the app to port 5001, and added a health check before all tests
  (status 200 + "Second-Look" on the home page). If it fails, pytest.exit stops
  the run before any test.
- Verified: app running -> 2 xfailed; app stopped -> clear error, no tests ran;
  AirPlay on 5000 -> clear error (HTTP 403).

## 5. A leftover server from the AI's own testing (Oct 31)

- After the fix, I stopped Flask with Ctrl+C, but port 5001 still returned 200.
- Claude Code had started its own Flask server in the background while testing
  and did not stop it.
- How I found it: lsof -i :5001 showed another Python process. I killed it, and
  then the health check worked.

## 6. Issue #1 test: Forms must send a POST request (Oct 31)

- Asked Claude Code for a test that checks the real behavior: submitting /Forms
  must send a POST request. Checking the alert text would not catch the bug,
  because the alert itself is the bug.
- Good catches by the AI:
  - Playwright's TimeoutError is not Python's built-in TimeoutError, so it
    imported it as PlaywrightTimeoutError for raises=.
  - fill() and click() can also time out with the same error. It added
    visibility checks first, so a broken selector fails with AssertionError
    instead of hiding as xfail.
- It tested 3 cases on scratch copies: current app -> xfail; misspelled
  selector -> real failure; simulated fix -> strict XPASS failure.
- While simulating the fix, it found that removing preventDefault() is not
  enough: the `<form>` has no method, so it would send GET /Forms?name=...
  I added this as a comment on issue #1.
- Result: full suite 3 xfailed with the app running.

## 7. Issue #4 test: Contact must reject an empty name (Oct 31)

- The real bug and a setup problem could both raise `AssertionError`, so `xfail`
  could not tell them apart. I asked Claude Code how to separate them.
- It defined its own exception `EmptyNameAccepted` and used
  `raises=EmptyNameAccepted`. It is raised only after a real `POST /contact`
  response, when the status is not 400 or "Message Sent!" appears.
- It tested 5 cases on scratch copies, including a "half fix" (400, but the
  success message still shows), which still counts as the bug.
- Following that case, I read `contact.html`: the frontend only checks
  `data.status` and shows nothing on errors. A server-only fix would leave the
  user with no feedback. I added this as a comment on issue #4.
- Result: full suite 4 xfailed with the app running.

## 8. Issue #3 test: invalid size must not crash Add Pet (Oct 31)

- The test logs in as the seeded admin first, so it still works after issue #2
  adds login protection. A failed login raises `AssertionError` and is not hidden.
- Custom exception `InvalidSizeNotHandled` is raised only after the real
  `POST /add_pet` response and a check of `/pet_info`.
- Claude Code found two traps: `add_pet` returns early (no user, or age not a
  number) before checking size, and the "Size" label is always on the page, so
  the word "size" alone does not prove there is an error message.
- It tested 6 cases on scratch copies (real app, wrong password, broken selector,
  simulated fix, form never posts, half fix).
- Limit it reported: the "pet was not saved" check was never really run against
  a fix. Tests use the live database, so CI should start from a fresh seeded
  database each run.
- Result: full suite 5 xfailed with the app running.

## 9. README: a false finding (Oct 31)

- Claude Code wrote that the home page has no limit and shows every pet.
- Wrong: `index()` has `.limit(1)` on the next line, so it shows one random pet.
  Its search output showed only the `fn.Random()` line, and it did not open the
  whole function to check.
- How I found it: `grep -n -A 20 "def index" web/api/routes.py | grep limit`
  showed `.limit(1)`.
- Fix: removed the finding, and added a note that no test should depend on
  which pet is featured.
- Lesson: "I checked the code" from the AI still needs a second look,
  especially when it only read search results.

## 10. CI failed in cleanup, not in tests.

- The workflow started Flask in the background with uv run and never stopped it.
- In the post-job step, setup-uv waited 300s for the uv cache lock and failed. Same kind of problem as the leftover local server in note 5.
