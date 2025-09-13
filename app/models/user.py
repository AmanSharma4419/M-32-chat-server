from pydantic import BaseModel
from typing import Optional

# Model for authetication


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserDB(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None


# Chatbot model session
class ChatRequest(BaseModel):
    session_id: str
    user_input: str


class ChatResponse(BaseModel):
    response: str
