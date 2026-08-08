from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'Shadow AI Backend'
    app_version: str = '0.1.0'
    api_prefix: str = '/api/v1'
    environment: str = 'development'
    log_level: str = 'INFO'
    database_url: str = 'sqlite+aiosqlite:///./shadow_ai.db'
    plugin_directory: str = './plugins'

    model_config = SettingsConfigDict(env_file='.env', env_prefix='SHADOW_AI_', extra='ignore')

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
