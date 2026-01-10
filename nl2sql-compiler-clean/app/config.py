"""
config.py
─────────
Centralised configuration loader.
Reads all settings from .env (or environment variables).
Import `cfg` anywhere in the project to access settings.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("OPENAI_MAX_TOKENS", "500")))
    temperature: float = field(default_factory=lambda: float(os.getenv("OPENAI_TEMPERATURE", "0.0")))


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("DB_NAME", "nl2sql_db"))


@dataclass(frozen=True)
class AppConfig:
    debug: bool = field(default_factory=lambda: os.getenv("APP_DEBUG", "False").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_query_results: int = field(default_factory=lambda: int(os.getenv("MAX_QUERY_RESULTS", "500")))
    log_file: str = "app/logs/query.log"


@dataclass(frozen=True)
class Config:
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    app: AppConfig = field(default_factory=AppConfig)


# Singleton instance — import this everywhere
cfg = Config()
