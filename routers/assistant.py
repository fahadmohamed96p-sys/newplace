from fastapi import APIRouter, Depends
from pydantic import BaseModel
from models.models import User
from routers.auth import get_current_user
from services.llm_service import chat_with_assistant
import uuid
import os
import httpx

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


@router.post("/chat")
async def chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    session_id = req.session_id or f"{current_user.id}_{uuid.uuid4().hex[:8]}"
    reply = await chat_with_assistant(req.message, session_id)
    return {"reply": reply, "session_id": session_id}


@router.get("/status")
async def ai_status():
    try:
        r = httpx.get(f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/tags", timeout=2.0)
        return {"online": r.status_code == 200}
    except Exception:
        return {"online": False}


@router.get("/suggestions")
async def get_suggestions(current_user: User = Depends(get_current_user)):
    return {
        "suggestions": [
            "Explain time & work problems",
            "TCS NQT important topics",
            "How to reduce filler words?",
            "Tips for coding interviews",
            "Binary search in Python",
            "HR interview questions",
            "How to introduce myself?",
            "What is ideal WPM for interviews?",
        ]
    }
