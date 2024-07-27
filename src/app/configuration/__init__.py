import os
from enum import Enum

from pydantic_settings import BaseSettings
from starlette.config import Config

current_file_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_file_dir, "..", "..", ".env")

config = Config(env_path)


class AppSettings(BaseSettings):
    APP_NAME: str = config("APP_NAME", default="Mada Job app")
    APP_DESCRIPTION: str | None = config("APP_DESCRIPTION", default=None)
    APP_VERSION: str | None = config("APP_VERSION", default=None)
    LICENSE_NAME: str | None = config("LICENSE", default=None)
    CONTACT_NAME: str | None = config("CONTACT_NAME", default=None)
    CONTACT_EMAIL: str | None = config("CONTACT_EMAIL", default=None)
    ADMIN_BASE_URL: str = config("ADMIN_BASE_URL")


class MailSettings(BaseSettings):
    MAIL_USERNAME: str = config("MAIL_USERNAME")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD")
    MAIL_FROM: str = config("MAIL_FROM")
    MAIL_PORT: int = config("MAIL_PORT", default=0)
    MAIL_SERVER: str = config("MAIL_SERVER")
    MAIL_FROM_NAME: str = config("MAIL_FROM_NAME")
    MAIL_STARTTLS: bool = config("MAIL_STARTTLS", default=False)
    MAIL_SSL_TLS: bool = config("MAIL_SSL_TLS", default=False)
    USE_CREDENTIALS: bool = config("USE_CREDENTIALS", default=False)
    VALIDATE_CERTS: bool = config("VALIDATE_CERTS", default=False)


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = config("CLIENT_CACHE_MAX_AGE", default=60)


class SecuritySettings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = config(
        "REFRESH_TOKEN_EXPIRE_MINUTES", default=30
    )
    TOKEN_TYPE: str = config("TOKEN_TYPE")


class DatabaseSettings(BaseSettings):
    DB_USER: str = config("DB_USER")
    DB_PASSWORD: str = config("DB_PASSWORD")
    DB_SERVER: str = config("DB_SERVER")
    DB_PORT: int = config("DB_PORT", cast=lambda x: int(x))
    DB_NAME: str = config("DB_NAME")
    DB_PREFIX: str = config("DB_PREFIX")
    DB_URI: str = f"{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}"
    DB_URL: str = f"{DB_PREFIX}{DB_URI}"
    CREATE_TABLE: bool = config("CREATE_TABLE", default=True)


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


def parse_environment(value: str) -> EnvironmentOption:
    """Parses the environment string value to an EnvironmentOption."""
    return EnvironmentOption[value.upper()]


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = config(
        "ENVIRONMENT", default="local", cast=parse_environment
    )


class Settings(
    AppSettings,
    DatabaseSettings,
    SecuritySettings,
    EnvironmentSettings,
    ClientSideCacheSettings,
    MailSettings,
):
    pass


settings = Settings()
