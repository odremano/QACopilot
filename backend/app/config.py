from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno (RNF-03)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    seed_examples: bool = True
    log_level: str = "INFO"

    # LLM (se usa a partir de S4; opcional en S3)
    llm_provider: str = "deepseek"
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    llm_api_key: SecretStr | None = None
    daily_generation_limit: int = 30

    # Sistema bajo prueba (se usa a partir de S5)
    sut_base_url: str = "https://www.saucedemo.com"
    evidencias_dir: str = "/data/evidencias"

    @property
    def llm_configurado(self) -> bool:
        if self.llm_provider == "demo":
            return True
        return bool(self.llm_api_key and self.llm_api_key.get_secret_value().strip())


settings = Settings()
