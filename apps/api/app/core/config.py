from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str

    DATABASE_URL: str

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    SUPABASE_JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()



# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):

#     APP_NAME: str

#     SUPABASE_URL: str
#     SUPABASE_SERVICE_ROLE_KEY: str
#     SUPABASE_JWT_SECRET: str

#     DATABASE_URL: str

#     class Config:
#         env_file = ".env"

# settings = Settings()