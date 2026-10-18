import pytest

from app.services.gamification_service import GamificationService


@pytest.fixture(autouse=True)
def awards(monkeypatch):
    """Unit tests use fake sessions, so XP awards are recorded, not run."""
    given = []

    async def fake_award(self, profile, amount, reason, ref_id):
        given.append((reason, amount, ref_id))
        return True

    monkeypatch.setattr(GamificationService, "award", fake_award)
    return given
