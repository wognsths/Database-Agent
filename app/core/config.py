import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class DBSettings(BaseSettings):
    POSTGRES_USER: str = os.getenv("DB_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    POSTGRES_HOST: str = os.getenv("DB_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("DB_PORT", "5432")
    POSTGRES_DB: str = os.getenv("DB_NAME", "postgres")

    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    DATABASE_AGENT_URL: str = os.getenv("DATABASE_AGENT_URL", "http://localhost:10001")  # ✅ 추가
    HOST_AGENT_URL: str = os.getenv("HOST_AGENT_URL", "http://localhost:10000")            # ✅ 추가

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = DBSettings()
