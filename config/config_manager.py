import os
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class TMDBConfig(BaseModel):
    api: str | None = None
    manual: bool = False


class AIConfig(BaseModel):
    provider: str
    api: str | None = None
    call: bool = False
    prompt1: str
    prompt2: str


class GeneralConfig(BaseModel):
    ignore_unknown: bool 
    comparison_table: bool
    ignore_file: bool
    chinese_traditional: bool
    default_output: str
    proxies: dict
    move_original: bool
    original_archive_dir: str


class AppConfig(BaseModel):
    general: GeneralConfig
    tmdb: TMDBConfig
    ai: AIConfig
    features: dict
    ignore_exts: list
    patterns: list[dict]


def load_config():
    load_dotenv(".env")

    def _env_expand(value):
        if isinstance(value, str) and value.startswith("!env "):
            return os.getenv(value.split()[1])
        return value

    with open("config/settings.yaml", "r") as f:
        settings = yaml.safe_load(f)

    with open("config/pattern_rules.yaml", "r", encoding="utf-8") as f:
        pattern_yaml = yaml.load(f, Loader=yaml.FullLoader)

    # 只取 "patterns" 键，避免传整个 dict
    patterns = pattern_yaml.get("patterns", [])

    # 环境变量展开
    for section in ["ai", "tmdb"]:
        for k, v in settings[section].items():
            settings[section][k] = _env_expand(v)

    conf = AppConfig(**settings, patterns=patterns)
    return conf
