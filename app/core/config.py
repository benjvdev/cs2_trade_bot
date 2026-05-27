import json
import os
from pydantic import BaseModel, Field, SecretStr
from typing import Optional

class Settings(BaseModel):
    min_roi: float = Field(..., ge=0)
    max_budget: float = Field(..., ge=0)
    buff_session: str
    steam_limit: int = Field(50, gt=0)
    csfloat_limit: int = Field(50, gt=0)
    rmb_to_usd: float = Field(0.14, gt=0)
    csfloat_api_key: Optional[str] = None
    batch_size: int = Field(100, gt=0)
    batch_sleep: float = Field(1.0, ge=0)

def load_settings(config_path: str = "config.json") -> Settings:
    """Loads and validates settings from a JSON file."""
    if not os.path.exists(config_path):
        # Return default settings if file doesn't exist (or raise error)
        # Based on task 2 requirement, we should read config.json
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
    with open(config_path, "r") as f:
        config_data = json.load(f)
        
    return Settings(**config_data)
