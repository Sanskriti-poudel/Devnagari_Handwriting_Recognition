from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class DocumentImage(Base):
    __tablename__ = "document_images"
    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String)
    saved_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class RecognizedText(Base):
    __tablename__ = "recognized_texts"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer)
    model_used = Column(String)
    text = Column(Text)
    confidence = Column(Float)
    processing_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)
