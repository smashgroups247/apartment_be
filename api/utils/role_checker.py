"""Role-based access control dependencies"""

from fastapi import HTTPException, status, Depends
from api.utils.jwt_handler import get_current_user
from api.v1.models.users import User


def require_role(*roles):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    return role_checker