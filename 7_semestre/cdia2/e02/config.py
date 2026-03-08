from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str="Bella Tavola API"
    app_version: str="1.0.0"
    debug: bool=False
    max_mesas: int=20
    max_pessoas_por_mesas: int=10

    class Config:
        env_file=".env"
    
settings=Settings()