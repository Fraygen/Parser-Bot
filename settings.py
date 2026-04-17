from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str
    BOT_TOKEN: str
    MY_CHAT_ID: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()