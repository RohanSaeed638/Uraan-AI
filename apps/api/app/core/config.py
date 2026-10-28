from pydantic import Field
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
    OPENAI_MODEL: str = "gpt-4.1-mini"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    ANTHROPIC_MODEL: str = "claude-haiku-5-5"

    # Which AI providers to try, in order, and how long to wait for each.
    # A provider without an API key is skipped.
    AI_PROVIDERS: str = "openai,gemini,anthropic"
    AI_REQUEST_TIMEOUT: float = 60.0

    # Optional: raises GitHub's rate limit for project reviews.
    GITHUB_TOKEN: str = ""

    SUPABASE_JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REDIS_URL: str

    # Web push (generate with `vapid --gen`). Push is disabled when unset;
    # in-app notifications still work.
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@example.com"

    # Email (Resend). With no key, no email is sent; in-app and push
    # notifications still work. For development, set EMAIL_OUTBOX_DIR to
    # write each email to a file instead of sending it.
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Uraan AI <onboarding@resend.dev>"
    EMAIL_OUTBOX_DIR: str = ""

    # Where the web app and this API are reachable from the outside, for the
    # links inside emails (open the app, unsubscribe).
    WEB_URL: str = "http://localhost:3000"
    API_PUBLIC_URL: str = "http://localhost:8000"

    # Websites allowed to call the API from a browser, comma separated.
    CORS_ORIGINS_RAW: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS_RAW.split(",") if o.strip()]

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