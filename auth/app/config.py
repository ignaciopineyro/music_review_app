import os

from dotenv import load_dotenv

load_dotenv()


class Settings:

    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "Auth Service")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"

        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required")

        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


settings = Settings()
