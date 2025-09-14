from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # <- ensures .env is loaded


class Settings(BaseSettings):
    PROJECT_NAME: str = "ChatBot-M2-Assignment"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "thisismysecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    MONGO_URI: str
    MONGO_DB: str

    class Config:
        env_file = ".env"


settings = Settings()
