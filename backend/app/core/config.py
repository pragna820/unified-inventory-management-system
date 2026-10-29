from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg2://inventory_user:CHANGE_ME@localhost:5432/unified_inventory"
    random_seed: int = 20261022
    reservation_ttl_minutes: int = 30
    atp_inbound_horizon_days: int = 7


settings = Settings()
