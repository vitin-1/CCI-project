from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Reconhecimento facial
    similarity_threshold: float = 0.5
    embedding_ttl_days: int = 90

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""  # nunca usar anon key no backend
    supabase_bucket_originals: str = "originals"
    supabase_bucket_previews: str = "previews"

    # Banco de dados — connection string Postgres do Supabase
    db_url: str = ""

    # API
    max_image_size_mb: float = 10.0
    cors_origins: list[str] = ["*"]
    admin_token: str = "changeme"

    # Operação
    dry_run: bool = False


settings = Settings()
