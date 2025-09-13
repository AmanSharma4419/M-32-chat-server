from fastapi import APIRouter, Depends, HTTPException
from app.chat_utils import get_bot_response
from app.api.v1.auth import get_current_user
from app.api.v1.schemas import UserDB, ChatRequest, ChatResponse
import uuid

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest,
                       current_user: UserDB = Depends(get_current_user)):
    try:
        user_id = current_user.id
        session_id = chat_request.session_id

        if not session_id:
            session_id = str(uuid.uuid4())

        bot_reply = await get_bot_response(
            user_id=user_id,
            session_id=session_id,
            user_input=chat_request.user_input
        )

        return ChatResponse(
            session_id=session_id,
            response=bot_reply
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}")
