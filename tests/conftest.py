import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import db


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Omdirigerer alle db-kall til en midlertidig SQLite-database."""
    test_db_path = tmp_path / "test_grocery.db"
    monkeypatch.setattr(db, "DB_PATH", test_db_path)
    db._init()
    yield test_db_path
