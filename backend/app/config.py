from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/tracking"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    sweego_api_key: str = ""
    app_base_url: str = "http://localhost:5173"
    smtp_from_email: str = "noreply@support.jonaskrauss.de"
    smtp_from_name: str = "Tracking Success"

    class Config:
        env_file = ".env"


settings = Settings()