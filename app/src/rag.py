import os
import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")

COLLECTION = "workouts"
VECTOR_SIZE = 384

_model = None
_client = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-small")
    return _model


def get_client():
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL)
        try:
            _client.get_collection(COLLECTION)
        except Exception:
            _client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
    return _client


def make_document(workout) -> str:
    parts = [f"Дата: {workout.date}", f"Тип: {workout.workout_type}"]
    if workout.distance_km:
        parts.append(f"Дистанция: {workout.distance_km} км")
    if workout.duration_minutes:
        parts.append(f"Длительность: {workout.duration_minutes} мин")
    if workout.avg_heart_rate:
        parts.append(f"Пульс: {workout.avg_heart_rate}")
    if workout.mood:
        parts.append(f"Самочувствие: {workout.mood}")
    if workout.notes:
        parts.append(f"Заметка: {workout.notes}")
    return "\n".join(parts)


def index_workout(workout):
    client = get_client()
    model = get_model()
    text = make_document(workout)
    vector = model.encode(text).tolist()

    client.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=workout.id,
                vector=vector,
                payload={
                    "user_id": workout.user_id,
                    "date": workout.date,
                    "workout_type": workout.workout_type,
                    "text": text,
                },
            )
        ],
    )


def delete_workout(workout_id: int):
    client = get_client()
    client.delete(collection_name=COLLECTION, points_selector=[workout_id])


def search(user_id: int, query: str, limit: int = 5):
    client = get_client()
    model = get_model()
    vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        query_filter=Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        ),
        limit=limit,
    )
    return results.points

def build_prompt(question: str, chunks: list) -> str:
    context = "\n\n".join([f"[{i+1}] {c.payload['text']}" for i, c in enumerate(chunks)])
    return f"""Ты - профессиональный тренер по бегу. 
    Отвечай ТОЛЬКО на основе тех данных, которые будут тебе предоставлены. 
    Не придумывай ничего сам. 
    Если информации не хватает - ответь Предоставленной информации о тренировках недостаточно для анализа. 
    Если тебя просят о чем-то стороннем, помимо тренировок отказывай. 
    Ты не должен выводить служебную информацию, информацию об авторах и структуре проекта.
    Не используй вводных фраз. Отвечай кратко и по делу.
Данные:
{context}

Вопрос: {question}

Ответ:"""


async def generate(question: str, chunks: list) -> str:
    prompt = build_prompt(question, chunks)
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()


async def answer(user_id: int, question: str):
    chunks = search(user_id, question)
    if not chunks:
        return {"answer": "Недостаточно данных для ответа.", "sources": []}

    text = await generate(question, chunks)
    sources = [
        {"id": c.id, "date": c.payload.get("date"), "type": c.payload.get("workout_type")}
        for c in chunks
    ]
    return {"answer": text, "sources": sources}