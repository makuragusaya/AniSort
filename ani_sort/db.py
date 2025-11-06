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
    UniqueConstraint,
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
    __table_args__ = (
        UniqueConstraint("name", "group_name", "season", name="uq_anime_unique"),
    )
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    season = Column(Integer, default=1)
    season_desc = Column(String)
    tmdb_id = Column(Integer)
    poster_path = Column(String, nullable=True)
    group_name = Column(String)
    output_path = Column(String)
    added_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime)
    status = Column(String, default="pending")  # done, failed, skipped

    tasks = relationship("Task", back_populates="anime")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    anime_id = Column(Integer, ForeignKey("anime.id"))
    input_path = Column(String)
    output_path = Column(String)
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime)
    success = Column(Boolean, default=False)
    status = Column(String)
    error_msg = Column(String)

    anime = relationship("Anime", back_populates="tasks")


class WatchedFolder(Base):
    __tablename__ = "watch_folders"
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True)
    detected_at = Column(DateTime, default=datetime.now)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    status = Column(String, default="detected")  # detected, processing, processed, removed


def get_or_create_anime(db, name, group, season, output_path, tmdb_id, poster_path):
    anime = (
        db.query(Anime).filter_by(name=name, group_name=group, season=season).first()
    )
    if not anime:
        anime = Anime(
            name=name,
            season=season,
            group_name=group,
            output_path=output_path,
            tmdb_id=tmdb_id,
            poster_path=poster_path,
        )
        db.add(anime)
        db.flush()  # 获取 anime.id
        db.refresh(anime)
    return anime


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(engine)
