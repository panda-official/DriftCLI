"""Configuration"""
import os
from pathlib import Path
from typing import Dict

import tomlkit as toml
from pydantic import BaseModel, Field


class Alias(BaseModel):
    """Alias of storage instance"""

    address: str
    bucket: str = Field(default="data")
    password: str


class Config(BaseModel):
    """Configuration as a dict"""

    aliases: Dict[str, Alias]


def write_config(path: Path, config: Config):
    """Write config to TOML file"""
    if not Path.exists(path):
        os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf8") as config_file:
        toml.dump(config.dict(), config_file)


def read_config(path: Path) -> Config:
    """Read config from TOML file"""
    with open(path, "r", encoding="utf8") as config_file:
        return Config.parse_obj(toml.load(config_file))
