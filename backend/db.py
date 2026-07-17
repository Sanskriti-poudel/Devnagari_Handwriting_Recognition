from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    university = Column(String, nullable=True)
    role = Column(String, default="Student")
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class DocumentImage(Base):
    __tablename__ = "document_images"
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String)
    saved_path = Column(String)
    uploaded_at = Column(DateTime, default=_utcnow)


class RecognizedText(Base):
    __tablename__ = "recognized_texts"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer)
    user_id = Column(Integer, index=True, nullable=True)
    model_used = Column(String)
    model_simulated = Column(Boolean, default=False)
    text = Column(Text)
    confidence = Column(Float)
    processing_time_ms = Column(Float)
    file_name = Column(String, default="")
    file_type = Column(String, default="image")  # "image" | "pdf"
    thumbnail = Column(Text, nullable=True)  # data: URI, small enough for SQLite TEXT
    num_chars = Column(Integer, default=0)
    num_lines = Column(Integer, default=0)
    status = Column(String, default="completed")  # "completed" | "failed"
    created_at = Column(DateTime, default=_utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)
