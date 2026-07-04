import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_database(tmp_path_factory, monkeypatch):
    from backend.app.database import Base, get_db
    from backend.app.main import app
    from backend.app import venue_storage

    database_dir = tmp_path_factory.mktemp("database")
    engine = create_engine(f"sqlite:///{database_dir / 'test.db'}", connect_args={"check_same_thread": False})
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(venue_storage, "ATTACHMENT_ROOT", (database_dir / "attachments").resolve())

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    engine.dispose()
