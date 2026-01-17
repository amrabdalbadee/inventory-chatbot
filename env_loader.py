"""Simple .env file loader using Python standard library."""
import os
from pathlib import Path


def load_env(env_path = ".env") -> dict[str, str]:
    """Load environment variables from a .env file.
    
    Only sets variables that are not already set in the environment.
    Returns dict of loaded variables.
    """
    loaded = {}
    env_file = Path(env_path)
    
    if not env_file.exists():
        return loaded
    
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse KEY=VALUE
            if "=" not in line:
                continue
            
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Only set if not already in environment and value is not empty
            if key and value and key not in os.environ:
                os.environ[key] = value
                loaded[key] = value
    
    return loaded


def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.environ.get(key, default)
