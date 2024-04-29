
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Base Configuration Class"""
    APP_NAME: str = "Kafka Consumer with OpenAI"
    TITLE: str = "Kafka Consumer Service"
    DESCRIPTION: str = "Service consuming Kafka topics and processing messages with OpenAI."
    MODEL_PROVIDER: str
    HOST: str
    PORT: int
    # Kafka Configuration
    KAFKA_SERVER: str
    KAFKA_TOPIC: str
    TEMPLATE: str
    # OpenAI Configuration
    OPENAI_API_KEY: str
    VECTORDB_TOPIC_NAME:str
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

