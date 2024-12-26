from functools import lru_cache
from typing import Dict, List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path
import platform
import re

def is_termux() -> bool:
    """Verifica se está rodando no Termux"""
    if platform.system() != "Linux":
        return False
    
    # Verifica se está no Android
    try:
        with open("/proc/version", "r") as f:
            return "Android" in f.read()
    except:
        return False

class APIKeys(BaseModel):
    """Configurações das chaves de API"""
    public_app_id: str = "94530663"  # Chave pública
    public_api_key: str = "d440851cb8c728f93ebe9a7252f7643e"  # Chave pública
    private_app_id: str = os.getenv("ADZUNA_APP_ID", "")
    private_api_key: str = os.getenv("ADZUNA_API_KEY", "")
    public_daily_limit: int = 5  # Limite para chave pública
    private_daily_limit: int = int(os.getenv("API_DAILY_LIMIT", "100"))

class AppConfig(BaseModel):
    """Configurações básicas da aplicação"""
    name: str = "JobSearch Pro"
    version: str = "1.0.0"
    description: str = "API profissional de busca de vagas com múltiplas fontes"

class ServerConfig(BaseModel):
    """Configurações do servidor"""
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    log_level: str = "INFO"

class APIConfig(BaseModel):
    """Configurações das APIs externas"""
    keys: APIKeys = APIKeys()
    api_usage_file: str = os.getenv("API_USAGE_FILE", "api_usage.json")
    adzuna_app_id: str = os.getenv("ADZUNA_APP_ID", "")
    adzuna_api_key: str = os.getenv("ADZUNA_API_KEY", "")
    daily_limit: int = int(os.getenv("API_DAILY_LIMIT", "100"))
    
    def get_credentials(self) -> tuple:
        """Retorna as credenciais apropriadas baseado no ambiente"""
        if is_termux():
            return self.keys.public_app_id, self.keys.public_api_key, self.keys.public_daily_limit
        return (
            self.keys.private_app_id or self.keys.public_app_id,
            self.keys.private_api_key or self.keys.public_api_key,
            self.keys.private_daily_limit
        )

class CacheConfig(BaseModel):
    """Configurações de cache"""
    ttl: int = int(os.getenv("CACHE_TTL", "3600"))
    max_size: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    enabled: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"

class ScraperConfig(BaseModel):
    """Configurações dos scrapers"""
    timeout: int = 30
    retry_attempts: int = 3
    batch_size: int = 50

class DatabaseConfig(BaseModel):
    """Configurações do banco de dados"""
    url: str = os.getenv("DATABASE_URL", "sqlite:///jobs.db")
    pool_size: int = 5
    max_overflow: int = 10

class Settings(BaseSettings):
    """Configurações principais da aplicação"""
    app: AppConfig = AppConfig()
    server: ServerConfig = ServerConfig()
    api: APIConfig = APIConfig()
    cache: CacheConfig = CacheConfig()
    scraper: ScraperConfig = ScraperConfig()
    db: DatabaseConfig = DatabaseConfig()
    
    # Fontes de dados
    default_sources: List[str] = ["adzuna"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    """Retorna uma instância cacheada das configurações"""
    return Settings()

# Instância global das configurações
settings = get_settings()
