from pydantic import BaseModel
from configparser import ConfigParser
from pathlib import Path
import os
import warnings

CONFIG_BASENAME = "provstor.config"


class Settings(BaseModel):
    minio_url: str = "http://localhost:9000"
    minio_access_key: str = "minio"
    minio_secret: str = "miniosecret"
    minio_bucket: str = "crates"
    fuseki_url: str = "http://localhost:3030"
    fuseki_dataset: str = "ds"

    def __init__(self, **kwargs):
        # Load from config files first
        config_values = self._load_from_config_files()
        # Override with any provided kwargs (including env vars)
        config_values.update(kwargs)
        super().__init__(**config_values)

    def _load_from_config_files(self):
        CONFIG_FILE_LOCATIONS = [Path.cwd() / CONFIG_BASENAME]

        if homeconf := os.getenv("XDG_CONFIG_HOME"):
            homeconf = Path(homeconf)
            CONFIG_FILE_LOCATIONS.insert(0, homeconf / CONFIG_BASENAME)
        else:
            try:
                HOME = Path.home()
                CONFIG_FILE_LOCATIONS.insert(0, HOME / ".config" / CONFIG_BASENAME)
            except RuntimeError as e:
                warnings.warn(f"cannot resolve home directory: {e}")

        CONFIG = ConfigParser()
        CONFIG.read(CONFIG_FILE_LOCATIONS)

        return {
            "fuseki_url": CONFIG.get("fuseki", "base_url", fallback="http://localhost:3030"),
            "fuseki_dataset": CONFIG.get("fuseki", "dataset", fallback="ds"),
            "minio_url": CONFIG.get("minio", "store", fallback="localhost:9000"),
            "minio_access_key": CONFIG.get("minio", "user", fallback="minio"),
            "minio_secret": CONFIG.get("minio", "secret", fallback="miniosecret"),
            "minio_bucket": CONFIG.get("minio", "bucket", fallback="crates")
        }

settings = Settings()
FUSEKI_BASE_URL = settings.fuseki_url
FUSEKI_DATASET = settings.fuseki_dataset
MINIO_STORE = settings.minio_url
MINIO_USER = settings.minio_access_key
MINIO_SECRET = settings.minio_secret
MINIO_BUCKET = settings.minio_bucket