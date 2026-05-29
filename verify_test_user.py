#!/usr/bin/env python
"""
Quick utility to mark a user as email verified for testing.
Usage: python verify_test_user.py <email>
"""

import sys
from sqlalchemy import create_engine, select

from api.v1.models.users import User
from api.utils.settings import settings


def verify_user_email(email: str):
    """Mark a user as email verified."""
    # Convert async URL to sync URL for psycopg2
    db_url = settings.DB_URL.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(db_url, echo=False)

    with engine.begin() as conn:
        from sqlalchemy.orm import Session
        session = Session(engine)

        user = session.query(User).filter(User.email == email).first()

        if not user:
            print(f"❌ User with email '{email}' not found")
            engine.dispose()
            return False

        user.is_verified = True
        session.commit()
        print(f"✓ User '{email}' is now email verified!")
        print(f"  - is_verified: {user.is_verified}")
        session.close()
        engine.dispose()
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_test_user.py <email>")
        print("Example: python verify_test_user.py test@example.com")
        sys.exit(1)

    email = sys.argv[1]
    result = verify_user_email(email)
    sys.exit(0 if result else 1)
