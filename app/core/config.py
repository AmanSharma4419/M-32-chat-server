from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project details
    PROJECT_NAME: str = "ChatBot-M2-Assignment"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # JWT
    SECRET_KEY: str = "thisismysecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MongoDB
    MONGO_URI: str = "mongodb://admin:admin@mongo:27017"
    MONGO_DB: str = "chatbot"


settings = Settings()
