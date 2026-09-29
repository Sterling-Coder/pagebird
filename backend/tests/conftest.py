"""Keep the test suite away from production data.

`pagebirdy.config.load_env()` copies backend/.env into the environment on
import, and on a developer machine that file holds the production Supabase
credentials. With nothing in the way, every test that created a project,
job or segment wrote it into the production database (320 junk jobs and 135
"Testing" projects by 29 Sep 2026), and anything reaching `pagebirdy.storage`
would have written to — or deleted from — the production bucket.

This runs before any test module imports the app. `load_dotenv` never
overrides a variable that is already set, so pinning these here wins over
.env:

* The review store talks to `TEST_DATABASE_URL` when it is set (a local or
  throwaway Postgres), and to nothing otherwise: tests that need a database
  then fail with "SUPABASE_DB_URL is not set" instead of touching production.
* Storage gets no endpoint and no key, and every storage call is replaced with
  one that fails loudly, so no test can reach a real bucket.
"""

import os

import pytest

os.environ["SUPABASE_DB_URL"] = os.environ.get("TEST_DATABASE_URL", "")
for _name in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY",
              "PAGEBIRDY_S3_ENDPOINT", "PAGEBIRDY_S3_BUCKET", "PAGEBIRDY_S3_ACCESS_KEY",
              "PAGEBIRDY_S3_SECRET_KEY"):
    os.environ[_name] = ""


_NO_DB = "SUPABASE_DB_URL is not set"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """A review-store test with no test database is skipped, not failed: the
    missing database is the setup, not a defect in the code under test. Set
    TEST_DATABASE_URL to a non-production Postgres to run them."""
    outcome = yield
    report = outcome.get_result()
    excinfo = call.excinfo
    if (report.failed and excinfo is not None
            and excinfo.errisinstance(RuntimeError) and _NO_DB in str(excinfo.value)):
        report.outcome = "skipped"
        report.longrepr = (str(item.path), item.location[1] or 0,
                           "Skipped: needs TEST_DATABASE_URL (a non-production Postgres)")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "storage_module: exercises pagebirdy.storage itself against a fake client")


@pytest.fixture(autouse=True)
def _no_real_object_storage(request, monkeypatch):
    """Tests that exercise storage patch these themselves; everything else
    that reaches storage is a bug, not a request to use production."""
    from pagebirdy import storage

    if request.node.get_closest_marker("storage_module"):
        return

    def _refuse(*_args, **_kwargs):
        raise RuntimeError("tests must not reach Supabase Storage; patch pagebirdy.storage")

    for name in ("ensure_bucket", "upload_file", "download_to", "read_bytes",
                 "delete", "list_prefix", "delete_prefix"):
        monkeypatch.setattr(storage, name, _refuse)


@pytest.fixture(autouse=True)
def _sync_jobs(monkeypatch):
    """Uploads normally return 202 and translate in the background; most
    tests want the finished report back from the request itself."""
    monkeypatch.setenv("PAGEBIRDY_SYNC_JOBS", "1")
