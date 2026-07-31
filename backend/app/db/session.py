from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


def init_db() -> None:
    from app.db import models  # noqa: F401 ensures models are registered
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
