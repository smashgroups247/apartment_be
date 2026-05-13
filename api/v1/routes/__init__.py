"""
API v1 Router
File: api/v1/routes/__init__.py

Registers all feature routers under /api/v1
"""

from fastapi import APIRouter

from api.v1.routes.auth_route import auth
from api.v1.routes.users import users
from api.v1.routes.support import support
from api.v1.routes.rides import rides

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(users)
api_version_one.include_router(support)
api_version_one.include_router(rides)