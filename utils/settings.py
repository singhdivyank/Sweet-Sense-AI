"""Application configurations and settings."""

from pathlib import Path
from functools import lru_cache

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application settings"""

    model_config = ConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Paths
    base_dir: Path = Path(__file__).parent
    output_dir: Path = Field(default_factory=lambda: Path("./splits"))
    log_file: Path = Field(default_factory=lambda: Path("logs/project.log"))
    model_out_file: Path = Field(
        default_factory=lambda: Path("model/jsons/prepared_model.json")
    )

    # Log configurations
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_bytes: int = Field(default=5 * 1024 * 1024)
    backup_counts: int = Field(default=5)
    log_format: str = Field(
        default="%(asctime)s  %(levelname)-8s  %(name)s:%(lineno)d  %(message)s"
    )
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S")

    # BigQuery
    gcp_project: str = Field(alias="GCP_PROJECT")
    bq_dataset: str = Field(alias="BQ_DATASET")
    bq_table: str = Field(alias="BQ_TABLE")
    gcp_service_account: Path = Field(alias="GCP_SERVICE_ACCOUNT_PATH")
    gcp_scopes: list[str] = ["https://www.googleapis.com/auth/bigquery.readonly"]

    def setup_dir(self) -> None:
        """Create log directory if it does not exist"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.model_out_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""

    settings = Settings()
    settings.setup_dir()
    return settings
