from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .db import get_db, init_db
from .models import User, Workout, Insight, ChatLog
from .schemas import (
    AuthRequest, UserOut, WorkoutIn, WorkoutOut,
    InsightOut, ChatRequest, ChatResponse,
)
from . import rag
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rag.get_client()
    rag.get_model()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/auth", response_model=UserOut)
def auth(payload: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == payload.name).first()
    if not user:
        user = User(name=payload.name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@app.get("/api/workouts", response_model=List[WorkoutOut])
def list_workouts(user_id: int, db: Session = Depends(get_db)):
    return db.query(Workout).filter(Workout.user_id == user_id).order_by(Workout.date.desc()).all()


@app.post("/api/workouts", response_model=WorkoutOut)
def create_workout(user_id: int, payload: WorkoutIn, db: Session = Depends(get_db)):
    w = Workout(user_id=user_id, **payload.model_dump())
    db.add(w)
    db.commit()
    db.refresh(w)
    rag.index_workout(w)
    return w


@app.put("/api/workouts/{workout_id}", response_model=WorkoutOut)
def update_workout(workout_id: int, user_id: int, payload: WorkoutIn, db: Session = Depends(get_db)):
    w = db.query(Workout).filter(Workout.id == workout_id, Workout.user_id == user_id).first()
    if not w:
        raise HTTPException(404, "Not found")
    for k, v in payload.model_dump().items():
        setattr(w, k, v)
    db.commit()
    db.refresh(w)
    rag.index_workout(w)
    return w


@app.delete("/api/workouts/{workout_id}")
def delete_workout(workout_id: int, user_id: int, db: Session = Depends(get_db)):
    w = db.query(Workout).filter(Workout.id == workout_id, Workout.user_id == user_id).first()
    if not w:
        raise HTTPException(404, "Not found")
    db.delete(w)
    db.commit()
    rag.delete_workout(workout_id)
    return {"ok": True}



@app.get("/api/insights", response_model=List[InsightOut])
def list_insights(user_id: int, db: Session = Depends(get_db)):
    return db.query(Insight).filter(Insight.user_id == user_id).all()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(user_id: int, payload: ChatRequest, db: Session = Depends(get_db)):
    result = await rag.answer(user_id, payload.message)
    log = ChatLog(user_id=user_id, question=payload.message,
                  answer=result["answer"], sources=result["sources"])
    db.add(log)
    db.commit()
    return result

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))