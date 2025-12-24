from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # IMPORTANTÍSSIMO: não quebra se existirem envs extras do Google/OS
    )

    APP_NAME: str = Field(default="car-mechanic-rag")
    ENV: str = Field(default="prod")
    LOG_LEVEL: str = Field(default="INFO")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8080)
    CORS_ORIGINS: str = Field(default="*")

    ADMIN_API_KEY: str = Field(default="change-me-admin-key")
    JWT_SECRET: str = Field(default="change-me-super-secret")
    JWT_ISSUER: str = Field(default="car-mechanic-rag")
    JWT_AUDIENCE: str = Field(default="car-mechanic-rag-users")
    JWT_EXPIRES_MINUTES: int = Field(default=43200)

    # Google / Gemini
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_GENAI_USE_VERTEXAI: bool = Field(default=False)
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: Optional[str] = None  # ex: "us-central1"

    ELEVEN_LABS_API_KEY: Optional[str] = None
    # DB
    DB_URL: str = Field(default="postgresql+psycopg://ai:ai@localhost:5432/ai")

    # KB / Embeddings
    KB_TABLE: str = Field(default="mechanic_kb")
    KB_MAX_RESULTS: int = Field(default=12)

    EMBED_MODEL: str = Field(default="models/text-embedding-004")
    EMBED_DIMENSIONS: int = Field(default=768)
    EMBED_BATCH: bool = Field(default=True)
    EMBED_BATCH_SIZE: int = Field(default=100)

    DATASET_DIR: str = Field(default="/data/dataset_mecanica_full")
    INGEST_CONCURRENCY: int = Field(default=8)
    INGEST_SKIP_IF_EXISTS: bool = Field(default=True)

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

settings = Settings()
