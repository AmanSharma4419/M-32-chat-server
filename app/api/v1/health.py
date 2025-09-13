from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "M2 chatbot backend is running 🚀"}
