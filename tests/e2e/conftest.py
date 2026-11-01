import urllib.error
import urllib.request

import pytest

# Single source of truth for the app URL used by all E2E tests.
# Port 5001, not 5000: macOS AirPlay Receiver listens on 5000 and answers 403.
BASE_URL = "http://127.0.0.1:5001"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session", autouse=True)
def require_running_app():
    """Abort the whole run unless the real Pet Adoption app is serving BASE_URL.

    Uses pytest.exit (not pytest.fail) so the problem can never be reported
    as an expected xfail.
    """
    message = (
        f"Flask app is not running at {BASE_URL}. "
        "Start it with: uv run python run.py"
    )
    try:
        with urllib.request.urlopen(BASE_URL + "/", timeout=5) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as exc:
        pytest.exit(f"{message} ({exc})", returncode=1)

    if status != 200 or "Second-Look" not in body:
        pytest.exit(
            f"{message} (got HTTP {status} without the 'Second-Look' marker; "
            "is another service on this port?)",
            returncode=1,
        )
