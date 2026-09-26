from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workout_type = Column(String(50), nullable=False)
    date = Column(String(20), nullable=False, index=True)
    duration_minutes = Column(Integer)
    distance_km = Column(Float)
    avg_heart_rate = Column(Integer)
    calories_burned = Column(Integer)
    notes = Column(Text)
    mood = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50))
    title = Column(String(200))
    description = Column(Text)
    confidence = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    sources = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())