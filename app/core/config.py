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

    # MongoDB (must come from env)
    MONGO_URI: str
    MONGO_DB: str

    class Config:
        env_file = ".env"  # optional for local dev


settings = Settings()
