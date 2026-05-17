from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Security
    SECRET_KEY: str = "changeme"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_FROM_NAME: str = "Etimad Tenders Monitor"

    # AI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Scraper
    SCRAPER_BASE_URL: str = "https://tenders.etimad.sa/Tender/AllTendersForVisitor"
    SCRAPER_INTERVAL_MINUTES: int = 60
    SCRAPER_HEADLESS: bool = True
    SCRAPER_TIMEOUT_MS: int = 30000

    # Company profile
    COMPANY_NAME: str = "شركة التقنية المتقدمة"
    COMPANY_ACTIVITIES: str = "تقنية المعلومات,برمجيات,استشارات تقنية"
    RELEVANCE_THRESHOLD: float = 0.6

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def company_activities_list(self) -> List[str]:
        return [a.strip() for a in self.COMPANY_ACTIVITIES.split(",") if a.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
