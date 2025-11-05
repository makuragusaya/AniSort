import os
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class TMDBConfig(BaseModel):
    api: str | None = None
    selected: bool = False


class AIConfig(BaseModel):
    provider: str
    api: str | None = None
    call: bool = False


class GeneralConfig(BaseModel):
    ignore_unknown_files: bool
    generate_comparison_table: bool
    generate_ignore_file: bool
    trad_chinese: bool
    default_output: str
    proxies: dict


class AppConfig(BaseModel):
    general: GeneralConfig
    tmdb: TMDBConfig
    ai: AIConfig
    features: dict
    patterns: list[dict]


def load_config():
    load_dotenv(".env")

    def _env_expand(value):
        if isinstance(value, str) and value.startswith("!env "):
            return os.getenv(value.split()[1])
        return value

    with open("config/settings.yaml", "r") as f:
        settings = yaml.safe_load(f)
    with open("config/pattern_rules.yaml", "r") as f:
        patterns = yaml.safe_load(f)

    # 环境变量展开
    for section in ["ai", "tmdb"]:
        for k, v in settings[section].items():
            settings[section][k] = _env_expand(v)

    conf = AppConfig(**settings, patterns=patterns)
    return conf
