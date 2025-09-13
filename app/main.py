from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import auth, chat, health, chat_pdf
import uvicorn


def create_application() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)
    app.include_router(health.router, prefix=settings.API_V1_STR + "/health")
    app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth")
    app.include_router(chat.router, prefix=settings.API_V1_STR + "/chat")
    app.include_router(
        chat_pdf.router, prefix=settings.API_V1_STR + "/upload-pdf")

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )
