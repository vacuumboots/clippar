# Legacy Flask entry point - use app_fastapi.py for FastAPI version
import warnings
warnings.warn(
    "Using legacy Flask app. Consider migrating to FastAPI version: python app_fastapi.py",
    DeprecationWarning,
    stacklevel=2
)

from app import app
