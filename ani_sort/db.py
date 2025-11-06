# ani_sort/db.py
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/anisort.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class Anime(Base):
    __tablename__ = "anime"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    group_name = Column(String)
    season = Column(Integer, default=1)
    output_path = Column(String)
    added_at = Column(DateTime, default=datetime.now)
    status = Column(String, default="done")  # done, failed, skipped

    tasks = relationship("Task", back_populates="anime")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    anime_id = Column(Integer, ForeignKey("anime.id"))
    input_path = Column(String)
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime)
    success = Column(Boolean, default=False)
    log_path = Column(String)
    status = Column(String)

    anime = relationship("Anime", back_populates="tasks")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(engine)
