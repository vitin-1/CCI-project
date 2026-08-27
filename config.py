from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Reconhecimento facial
    similarity_threshold: float = 0.40  # calibrado para buffalo_l
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
    secret_key: str = "changeme-secret"  # trocar em produção
    code_ttl_minutes: int = 5            # validade do código WhatsApp de verificação

    # Operação
    dry_run: bool = False


settings = Settings()
