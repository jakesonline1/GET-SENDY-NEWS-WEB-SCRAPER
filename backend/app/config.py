from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Get Sendy Pipeline API'
    database_url: str = 'postgresql://postgres:postgres@db:5432/get_sendy'
    redis_url: str = 'redis://redis:6379/0'
    jwt_secret: str = 'dev-secret-change-me'
    jwt_algorithm: str = 'HS256'
    access_token_minutes: int = 60 * 12


settings = Settings()
