from pathlib import Path
import yaml

from utils import BASE_DIR

CONFIG_DIR = BASE_DIR / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "matching_rules.yaml"


def load_config(config_path: Path | None = None) -> dict:
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {path}")

    with open(path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config