"""
Shared FastAPI dependencies
"""

from api.utils.jwt_handler import get_current_user, get_current_active_user

__all__ = [
    "get_current_user",
    "get_current_active_user",
]
