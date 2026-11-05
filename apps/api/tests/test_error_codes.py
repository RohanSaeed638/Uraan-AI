"""Error messages carry a code the web app can translate."""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_codes import error_code, fixed_messages
from app.core.exceptions import http_exception_handler

API = Path(__file__).resolve().parents[1]
EN = API.parent / "web" / "messages" / "en.json"


def test_codes_are_the_message_as_words():
    assert error_code("Profile not found") == "profile_not_found"
    assert error_code("Invalid or expired session. Please sign in again.") == (
        "invalid_or_expired_session_please_sign_in_again"
    )


def test_long_messages_are_cut_without_a_trailing_underscore():
    code = error_code("word " * 40)

    assert len(code) <= 80 and not code.endswith("_")


def test_every_fixed_message_can_be_translated():
    """A new HTTPException message must be added to the web app's `errors`
    messages: run `python scripts/sync_error_messages.py`."""
    errors = json.loads(EN.read_text(encoding="utf-8")).get("errors", {})
    missing = {
        code: text for code, text in fixed_messages(API / "app").items() if errors.get(code) != text
    }

    assert not missing, f"Run scripts/sync_error_messages.py. Missing: {sorted(missing)}"


def app():
    api = FastAPI()
    api.add_exception_handler(StarletteHTTPException, http_exception_handler)

    @api.get("/missing")
    def missing():
        raise HTTPException(status_code=404, detail="Profile not found")

    @api.get("/locked")
    def locked():
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TestClient(api)


def test_responses_keep_detail_and_status_and_add_a_code():
    response = app().get("/missing")

    body = response.json()

    assert response.status_code == 404
    assert body["detail"] == body["message"] == "Profile not found"
    assert body["error_code"] == "profile_not_found" and body["code"] == "NOT_FOUND_001"
    assert "request_id" in body


def test_headers_survive():
    response = app().get("/locked")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error_code"] == "invalid_or_expired_session_please_sign_in_again"


def test_unknown_routes_still_answer_404():
    assert app().get("/nope").status_code == 404
