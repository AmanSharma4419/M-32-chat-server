from pydantic import BaseModel, Field
from typing import Optional
import uuid


class UserCreate(BaseModel):
    username: str
    password: str


class UserDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str | None = None
    username: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
