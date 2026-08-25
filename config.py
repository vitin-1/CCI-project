from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Reconhecimento facial
    similarity_threshold: float = 0.5
    embedding_ttl_days: int = 90

    # Storage
    storage_originals: Path = Path("storage/originals")
    storage_previews: Path = Path("storage/previews")
    faiss_index_path: Path = Path("storage/faiss.index")

    # Banco de dados
    db_url: str = "sqlite:///./storage/metadata.db"

    # API
    max_image_size_mb: float = 10.0
    cors_origins: list[str] = ["*"]
    admin_token: str = "changeme"

    # Operação
    dry_run: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
