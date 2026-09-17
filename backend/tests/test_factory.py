"""Tests for the app factory and its Alembic wiring.

The lifespan runs Alembic migrations at startup. The production failure
"alembic.util.exc.CommandError: No 'script_location' key found in
configuration" was caused by pointing Alembic's Config at
`backend/app/alembic.ini`, which does not exist. These tests guard the
path resolution so the ini file is always found and its `script_location`
points at a directory that exists.
"""
import os

from app.factory import ALEMBIC_INI, create_app
from alembic.config import Config


def test_alembic_ini_path_exists():
    assert os.path.isfile(ALEMBIC_INI)


def test_alembic_script_location_resolves():
    cfg = Config(ALEMBIC_INI)
    script_location = cfg.get_main_option("script_location")
    assert script_location and os.path.isdir(script_location)
    assert os.path.isfile(os.path.join(script_location, "env.py"))


def test_create_app_wires_lifespan():
    app = create_app()
    assert app.router.lifespan_context is not None