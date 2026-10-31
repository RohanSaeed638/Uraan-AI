import pytest

from app.services.gamification_service import GamificationService


@pytest.fixture(autouse=True)
def awards(monkeypatch):
    """Unit tests use fake sessions, so XP awards are recorded, not run."""
    given = []

    async def fake_award(self, profile, amount, reason, ref_id, evaluate=True):
        given.append((reason, amount, ref_id))
        return True

    monkeypatch.setattr(GamificationService, "award", fake_award)
    return given


# The limits are exercised in tests/test_rate_limit.py with their own switch;
# everywhere else a test must not depend on how many requests came before it.
from app.core.config import settings as _settings  # noqa: E402

_settings.RATE_LIMIT_ENABLED = False
_settings.AUTH_CACHE_SECONDS = 0
