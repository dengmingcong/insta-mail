import os

from dotenv import load_dotenv


def load_env():
    """Load environment variables from the .env file in the project root directory."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(dotenv_path=env_path)
