from os import environ
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = environ.get("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = environ.get("DEEPSEEK_API_KEY", "")
    SUPABASE_URL: str = environ.get("SUPABASE_URL", "")
    SUPABASE_KEY: str = environ.get("SUPABASE_KEY", "")
    LINKEDIN_COOKIE_DIR: str = environ.get("LINKEDIN_COOKIE_DIR", "./sessions")
    SCRAPING_TIMEOUT: int = int(environ.get("SCRAPING_TIMEOUT", "30000"))
    MAX_RETRIES: int = int(environ.get("MAX_RETRIES", "3"))
    HOST: str = environ.get("HOST", "0.0.0.0")
    PORT: int = int(environ.get("PORT", "8000"))


settings = Settings()
