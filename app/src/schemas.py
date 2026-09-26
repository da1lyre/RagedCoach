from pydantic import BaseModel
from typing import Optional, List


class AuthRequest(BaseModel):
    name: str


class UserOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class WorkoutIn(BaseModel):
    workout_type: str
    date: str
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    calories_burned: Optional[int] = None
    notes: Optional[str] = None
    mood: Optional[str] = None


class WorkoutOut(WorkoutIn):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class InsightOut(BaseModel):
    id: int
    type: Optional[str]
    title: Optional[str]
    description: Optional[str]
    confidence: Optional[int]

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []