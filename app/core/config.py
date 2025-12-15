"""
Complete configuration management for Graph Builder Service.
Uses Pydantic Settings for validation and environment variable loading.
"""
from functools import lru_cache
from typing import Any, List, Optional
from pathlib import Path
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings with validation.
    All settings can be overridden via environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ========================================================================
    # Application Settings
    # ========================================================================
    app_name: str = Field(
        default="GraphBuilderService",
        description="Application name"
    )

    debug: bool = Field(
        default=False,
        description="Debug mode"
    )

    environment: str = Field(
        default="production",
        description="Environment (development, staging, production)"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    api_version: str = Field(
        default="v1",
        description="API version"
    )

    # ========================================================================
    # Server Configuration
    # ========================================================================
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )

    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )

    workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of worker processes"
    )

    reload: bool = Field(
        default=False,
        description="Auto-reload on code changes"
    )

    # ========================================================================
    # Neo4j Configuration
    # ========================================================================
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )

    neo4j_username: str = Field(
        default="neo4j",
        description="Neo4j username"
    )

    neo4j_password: str = Field(
        default="cedia-neo4j",
        description="Neo4j password"
    )

    neo4j_database: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )

    neo4j_max_connection_lifetime: int = Field(
        default=3600,
        ge=60,
        description="Max connection lifetime in seconds"
    )

    neo4j_max_connection_pool_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Max connection pool size"
    )

    neo4j_connection_timeout: int = Field(
        default=60,
        ge=5,
        le=300,
        description="Connection timeout in seconds"
    )

    # ========================================================================
    # MySQL Configuration
    # ========================================================================
    mysql_host: str = Field(
        default="localhost",
        description="MySQL host"
    )

    mysql_port: int = Field(
        default=3306,
        ge=1,
        le=65535,
        description="MySQL port"
    )

    mysql_user: str = Field(
        default="root",
        description="MySQL username"
    )

    mysql_password: str = Field(
        default="password",
        description="MySQL password"
    )

    mysql_database: str = Field(
        default="input_db",
        description="MySQL database name"
    )

    mysql_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="MySQL connection pool size"
    )

    mysql_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="MySQL max overflow connections"
    )

    # ========================================================================
    # PostgreSQL Configuration
    # ========================================================================
    postgres_host: str = Field(
        default="localhost",
        description="PostgreSQL host"
    )

    postgres_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="PostgreSQL port"
    )

    postgres_user: str = Field(
        default="postgres",
        description="PostgreSQL username"
    )

    postgres_password: str = Field(
        default="password",
        description="PostgreSQL password"
    )

    postgres_database: str = Field(
        default="input_db",
        description="PostgreSQL database name"
    )

    postgres_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="PostgreSQL connection pool size"
    )

    postgres_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="PostgreSQL max overflow connections"
    )

    # ========================================================================
    # Oracle Configuration
    # ========================================================================
    oracle_host: str = Field(
        default="localhost",
        description="Oracle host"
    )

    oracle_port: int = Field(
        default=1521,
        ge=1,
        le=65535,
        description="Oracle port"
    )

    oracle_user: str = Field(
        default="system",
        description="Oracle username"
    )

    oracle_password: str = Field(
        default="password",
        description="Oracle password"
    )

    oracle_service_name: str = Field(
        default="XE",
        description="Oracle service name"
    )

    oracle_pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Oracle connection pool size"
    )

    oracle_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Oracle max overflow connections"
    )

    # ========================================================================
    # Session Management
    # ========================================================================
    session_timeout: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Session timeout in seconds (default: 1 hour)"
    )

    cache_dir: str = Field(
        default="cache_dir",
        description="Directory for session cache"
    )

    # ========================================================================
    # File Upload Settings
    # ========================================================================
    max_upload_size: int = Field(
        default=(5 * 104857600),  # 5 * 100MB = 500MB
        ge=10240,  # 10KB minimum
        le=1073741824,  # 1GB maximum
        description="Maximum upload file size in bytes"
    )

    allowed_extensions: str = Field(
        default="csv,tsv,dsv,xlsx,xls,json,parquet",
        description="Comma-separated list of allowed file extensions"
    )

    # ========================================================================
    # Security Settings
    # ========================================================================
    secret_key: str = Field(
        default=...,
        min_length=32,
        description="Secret key for cryptographic operations"
    )

    api_key_name: str = Field(
        default="Graph-Builder-API-Key",
        description="API key header name"
    )

    api_key: str = Field(
        default=...,
        min_length=16,
        description="API key for authentication"
    )

    # ========================================================================
    # CORS Settings
    # ========================================================================
    cors_origins: str = Field(
        default= "http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins"
    )

    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )

    # ========================================================================
    # Monitoring & Metrics
    # ========================================================================
    enable_metrics: bool = Field(
        default=False,
        description="Enable Prometheus metrics"
    )

    metrics_port: int = Field(
        default=9090,
        ge=1,
        le=65535,
        description="Port for metrics endpoint"
    )

    # ========================================================================
    # Optional: Sentry
    # ========================================================================
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )

    # ========================================================================
    # Optional: Redis
    # ========================================================================
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL for distributed caching"
    )

    # ========================================================================
    # Validators
    # ========================================================================

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "dev", "staging", "production", "prod", "test"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"Invalid environment. Must be one of: {', '.join(valid_envs)}")
        return v_lower

    @field_validator("allowed_extensions")
    @classmethod
    def parse_allowed_extensions(cls, v: str) -> List[str]:
        """Parse allowed extensions from comma-separated string."""
        if not v:
            return []
        return [ext.strip().lower() for ext in v.split(",") if ext.strip()]

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if v == "*":
            return ["*"]
        if not v:
            return []
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @computed_field
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return str(self.environment).lower() in ["dev", "development"]

    @computed_field
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return str(self.environment).lower() in ["prod", "production"]

    @computed_field
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return str(self.environment).lower() == "staging"

    @computed_field
    def neo4j_config(self) -> dict:
        """Get Neo4j configuration as dictionary."""
        return {
            "uri": self.neo4j_uri,
            "username": self.neo4j_username,
            "password": self.neo4j_password,
            "database": self.neo4j_database,
            "max_connection_lifetime": self.neo4j_max_connection_lifetime,
            "max_connection_pool_size": self.neo4j_max_connection_pool_size,
            "connection_timeout": self.neo4j_connection_timeout,
        }

    @computed_field
    def mysql_config(self) -> dict:
        """Get MySQL configuration as dictionary."""
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
            "pool_size": self.mysql_pool_size,
            "max_overflow": self.mysql_max_overflow,
        }

    @computed_field
    def postgres_config(self) -> dict:
        """Get PostgreSQL configuration as dictionary."""
        return {
            "host": self.postgres_host,
            "port": self.postgres_port,
            "user": self.postgres_user,
            "password": self.postgres_password,
            "database": self.postgres_database,
            "pool_size": self.postgres_pool_size,
            "max_overflow": self.postgres_max_overflow,
        }

    @computed_field
    def oracle_config(self) -> dict:
        """Get Oracle configuration as dictionary."""
        return {
            "host": self.oracle_host,
            "port": self.oracle_port,
            "user": self.oracle_user,
            "password": self.oracle_password,
            "service_name": self.oracle_service_name,
            "pool_size": self.oracle_pool_size,
            "max_overflow": self.oracle_max_overflow,
        }

    @computed_field
    def cache_path(self) -> Path:
        """Get cache directory as Path object."""
        path = Path(self.cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    def max_upload_size_mb(self) -> float:
        """Get max upload size in MB."""
        return round(self.max_upload_size / (1024 * 1024), 2)

    def get_database_url(self, db_type: str) -> str:
        """
        Get database connection URL.

        Args:
            db_type: Database type (mysql, postgres, oracle)

        Returns:
            Connection URL string
        """
        if db_type.lower() == "mysql":
            return (
                f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
                f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            )
        elif db_type.lower() in ["postgres", "postgresql"]:
            return (
                f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            )
        elif db_type.lower() == "oracle":
            return (
                f"oracle+cx_oracle://{self.oracle_user}:{self.oracle_password}"
                f"@{self.oracle_host}:{self.oracle_port}/?service_name={self.oracle_service_name}"
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def model_post_init(self, __context: Any) -> None:  # pylint: disable=arguments-differ
        """Post-initialization validation."""
        # Warn about insecure defaults in production
        if self.is_production:
            if self.secret_key == "change-me-in-production":
                import warnings
                warnings.warn(
                    "Using default SECRET_KEY in production! "
                    "Generate a secure key with: openssl rand -hex 32"
                )

            if self.api_key == "dev-api-key-change-in-production":
                import warnings
                warnings.warn(
                    "Using default API_KEY in production! "
                    "Generate a secure key with: openssl rand -hex 32"
                )

            if self.debug:
                import warnings
                warnings.warn("Debug mode is enabled in production!")


@lru_cache()
def get_settings() -> Settings:
    """
    Get settings singleton instance.
    Uses lru_cache to ensure settings are loaded only once.

    Returns:
        Settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
