import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Base Configuration Class"""

    # Server Config
    HOST: str
    PORT: int
    APP_NAME: str = "MicroserviceAPI"
    TITLE: str = "Microservice FastAPI"
    DESCRIPTION: str = "Microservice handling GitHub commits and Kafka integration."
    VERSION: str = "1.0.0"

    # Kafka Configuration
    KAFKA_SERVER: str
    KAFKA_TOPIC: str

    # GitHub Configuration
    GITHUB_ACCESS_TOKEN: str
    REPO_NAME: str

    # Debug configuration
    DEBUG: bool = False
    TESTING: bool = False

    # Directories (Example: logs)
    APP_ROOT_DIRECTORY: str = os.getcwd()
    LOG_DIRECTORY: str = os.path.join(APP_ROOT_DIRECTORY, "logs")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

class ProductionConfig(Settings):
    pass

class DevelopmentConfig(Settings):
    DEBUG: bool = True

class TestingConfig(Settings):
    TESTING: bool = True
    DEBUG: bool = True

@lru_cache()
def get_config() -> Settings:
    """Get the current configuration object"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "development":
        return DevelopmentConfig()
    elif environment == "testing":
        return TestingConfig()
    elif environment == "production":
        return ProductionConfig()
    else:
        raise ValueError(f"Invalid environment: {environment}")

# Application setup
config = get_config()

