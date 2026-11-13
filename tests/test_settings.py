from library_catalog.core.config import Settings


def make_settings(**overrides):
    values = {
        "debug": False,
        "database_url": "postgresql+asyncpg://postgres:postgres@localhost/catalog",
        "jwt_secret_key": "a" * 32,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_database_pool_settings_have_safe_defaults() -> None:
    settings = make_settings()

    assert settings.database_pool_size == 20
    assert settings.database_max_overflow == 10
    assert settings.database_pool_timeout == 30
    assert settings.database_pool_recycle == 1800
    assert settings.database_pool_pre_ping is True


def test_database_ssl_can_be_enabled_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_SSL", "true")

    settings = make_settings()

    assert settings.database_ssl is True
