"""
Environment configuration module.
Loads and validates environment variables once, then exports them for use across the application.
"""

import os
from dotenv import load_dotenv
from typing import Optional


class EnvironmentConfig:
    """
    Centralized environment configuration class.
    Loads environment variables once and validates required variables.
    """
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Load and validate environment variables
        self.OPENAI_API_KEY = self._get_required("OPENAI_API_KEY")
        self.NOTION_API_KEY = self._get_required("NOTION_API_KEY")
        self.NOTION_DATABASE_ID = self._get_required("NOTION_DATABASE_ID")
        self.GITHUB_APP_ID = self._get_required("GITHUB_APP_ID")
        self.GITHUB_PRIVATE_KEY = self._get_required("GITHUB_PRIVATE_KEY")
        # Optional environment variables (add defaults if needed)
        self.DEBUG = self._get_optional("DEBUG", "False").lower() in ("true", "1", "yes")
        self.ENVIRONMENT = self._get_optional("ENVIRONMENT", "development")
    
    def _get_required(self, key: str) -> str:
        """
        Get a required environment variable.
        Raises ValueError if the variable is not set.
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Required environment variable '{key}' is not set. "
                f"Please add it to your .env file."
            )
        return value
    
    def _get_optional(self, key: str, default: str = "") -> str:
        """
        Get an optional environment variable with a default value.
        """
        return os.getenv(key, default)
    
    def __repr__(self) -> str:
        """String representation (hides sensitive values)"""
        return (
            f"EnvironmentConfig(\n"
            f"  OPENAI_API_KEY={'*' * 8 if self.OPENAI_API_KEY else 'NOT SET'},\n"
            f"  NOTION_API_KEY={'*' * 8 if self.NOTION_API_KEY else 'NOT SET'},\n"
            f"  NOTION_DATABASE_ID={'*' * 8 if self.NOTION_DATABASE_ID else 'NOT SET'},\n"
            f"  GITHUB_APP_ID={self.GITHUB_APP_ID if self.GITHUB_APP_ID else 'NOT SET'},\n"
            f"  GITHUB_PRIVATE_KEY={'*' * 8 if self.GITHUB_PRIVATE_KEY else 'NOT SET'},\n"
            f"  DEBUG={self.DEBUG},\n"
            f"  ENVIRONMENT={self.ENVIRONMENT}\n"
            f")"
        )


# Create a single instance of the configuration
# This ensures environment variables are loaded only once
env = EnvironmentConfig()

# Export individual variables for convenience
OPENAI_API_KEY = env.OPENAI_API_KEY
NOTION_API_KEY = env.NOTION_API_KEY
NOTION_DATABASE_ID = env.NOTION_DATABASE_ID
DEBUG = env.DEBUG
GITHUB_APP_ID = env.GITHUB_APP_ID
GITHUB_PRIVATE_KEY = env.GITHUB_PRIVATE_KEY
ENVIRONMENT = env.ENVIRONMENT

# You can now import like:
# from env import env, OPENAI_API_KEY, NOTION_API_KEY, etc.
