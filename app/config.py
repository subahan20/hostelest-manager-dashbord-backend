import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration with shared defaults."""

    # Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY", "hostelest-default-secret-key-change-me")

    # SQLAlchemy Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/hostelest_db",
    )
    # Normalize postgres:// to postgresql:// for SQLAlchemy 1.4+ compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # JWT Settings
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "hostelest-jwt-super-secret-production-grade-encryption-key-2026-xyz",
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    )

    # CORS Settings
    cors_origins_env = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
    )
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    # Disable CSRF / extra checks if needed in testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=120)


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    ENV = "production"
    # Ensure production environment variables are properly set
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 20,
        "max_overflow": 10,
    }


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
