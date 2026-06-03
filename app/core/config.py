import json
import os
from pydantic import BaseModel, Field
from typing import Optional

class Settings(BaseModel):
    min_roi: float = Field(15.0, ge=0)
    max_budget: float = Field(50.0, ge=0)
    buff_session: str = ""
    steam_limit: int = Field(50, gt=0)
    csfloat_limit: int = Field(50, gt=0)
    rmb_to_usd: float = Field(0.14, gt=0)
    csfloat_api_key: Optional[str] = None
    skinport_api_key: Optional[str] = None
    skinbaron_api_key: Optional[str] = None
    batch_size: int = Field(100, gt=0)
    batch_sleep: float = Field(5.0, ge=0)
    max_price_age_hours: float = Field(24.0, gt=0)

def load_settings(config_path: str = "config.json") -> Settings:
    """Loads and validates settings from a JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    env_overrides = {
        "BUFF_SESSION": "buff_session",
        "CSFLOAT_API_KEY": "csfloat_api_key",
        "SKINPORT_API_KEY": "skinport_api_key",
        "SKINBARON_API_KEY": "skinbaron_api_key",
    }
    for env_name, field_name in env_overrides.items():
        env_value = os.environ.get(env_name)
        if env_value is not None:
            config_data[field_name] = env_value
        
    return Settings(**config_data)
