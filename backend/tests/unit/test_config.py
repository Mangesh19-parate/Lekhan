"""Unit tests for runtime configuration."""

from app.config import Settings, get_settings


def test_settings_defaults() -> None:
    """Verifies default settings configuration."""
    settings = get_settings()
    assert settings.ENV in ("dev", "test")
    assert "postgresql" in settings.DATABASE_URL
    assert settings.SESSION_IDLE_MINUTES == 30
    assert settings.SESSION_ABSOLUTE_HOURS == 12


def test_is_dev_and_is_test_flags() -> None:
    """Verifies environment convenience properties."""
    dev_settings = Settings(ENV="dev")
    assert dev_settings.is_dev is True
    assert dev_settings.is_test is False

    test_settings = Settings(ENV="test")
    assert test_settings.is_dev is False
    assert test_settings.is_test is True
