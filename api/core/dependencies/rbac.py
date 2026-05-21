"""
RBAC Dependencies
File: api/core/dependencies/rbac.py

FastAPI dependencies for role-based access control.
Usage:
    @router.get("/admin-only", dependencies=[Depends(require_superadmin)])
    async def admin_endpoint(...):
        ...
"""

from fastapi import Depends, HTTPException, status
from api.utils.jwt_handler import get_current_user
from api.v1.models.users import User


async def require_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raise 403 if the current user is not a superadmin."""
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required.",
        )
    return current_user


async def require_vendor_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raise 403 if user is neither a vendor nor a superadmin."""
    if current_user.role not in ("vendor", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor or superadmin access required.",
        )
    return current_user


async def require_verified_vendor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raise 403 if user is not a verified vendor (or superadmin)."""
    if current_user.role == "superadmin":
        return current_user
    if current_user.role != "vendor" or not current_user.vendor_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified vendor access required.",
        )
    return current_user
