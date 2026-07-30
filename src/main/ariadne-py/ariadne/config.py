from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class StrapiConfig:
    base_url: str = "http://localhost:1337"
    api_token: str = ""


@dataclass
class DeepSeekConfig:
    api_key: str = ""
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"
    max_tokens: int = 4096


@dataclass
class SFTPConfig:
    host: str = ""
    port: int = 22
    username: str = ""
    password: str = ""
    remote_path: str = "/uploads"


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///ariadne.db"


@dataclass
class AppConfig:
    strapi: StrapiConfig = field(default_factory=StrapiConfig)
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    sftp: SFTPConfig = field(default_factory=SFTPConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    @classmethod
    def from_env(cls) -> AppConfig:
        return cls(
            strapi=StrapiConfig(
                base_url=os.getenv("STRAPI_BASE_URL", "http://localhost:1337"),
                api_token=os.getenv("STRAPI_API_TOKEN", ""),
            ),
            deepseek=DeepSeekConfig(
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            ),
            sftp=SFTPConfig(
                host=os.getenv("SFTP_HOST", ""),
                port=int(os.getenv("SFTP_PORT", "22")),
                username=os.getenv("SFTP_USER", ""),
                password=os.getenv("SFTP_PASSWORD", ""),
                remote_path=os.getenv("SFTP_REMOTE_PATH", "/uploads"),
            ),
            database=DatabaseConfig(
                url=os.getenv("DATABASE_URL", "sqlite:///ariadne.db"),
            ),
        )
