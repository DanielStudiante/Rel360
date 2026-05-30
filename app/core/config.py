from __future__ import annotations

import os
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(ENV_PATH)


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    APP_NAME: str = "Rel360 API"


settings = Settings()