import os
from importlib import reload

import src.config as config_module


def test_config_convierte_postgres_a_postgresql(monkeypatch):
    # simular entorno Heroku con postgres://
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/dbtest")

    # recargar el módulo para que se reejecute la clase Config
    reload(config_module)

    cfg = config_module.Config
    assert cfg.SQLALCHEMY_DATABASE_URI.startswith("postgresql://")
