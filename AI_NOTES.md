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
