"""Shared test fixtures."""

import sqlite3
from pathlib import Path

import pytest

from memoryforge.config import Config
from memoryforge.db.connection import get_connection
from memoryforge.db.repository import Repository


@pytest.fixture
def test_config(tmp_path: Path) -> Config:
    """Config pointing to a temporary directory."""
    return Config(
        db_path=tmp_path / "test.db",
        uploads_dir=tmp_path / "uploads",
    )


@pytest.fixture
def test_db(test_config: Config) -> sqlite3.Connection:
    """Initialized test database connection."""
    test_config.ensure_dirs()
    conn = get_connection(test_config.db_path)
    return conn


@pytest.fixture
def repo(test_db: sqlite3.Connection) -> Repository:
    """Repository backed by the test database."""
    return Repository(test_db)
