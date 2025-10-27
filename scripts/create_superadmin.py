"""Create a super admin user."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def create_superadmin(email: str, password: str):
    """Create a super admin user."""
    db = AsyncSessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            logger.error(f"❌ User with email {email} already exists")
            return False

        # Create super admin
        admin = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()

        logger.info(f"✅ Super admin created successfully!")
        logger.info(f"   Email: {email}")
        logger.info(f"   Password: {password}")

        return True

    except Exception as e:
        logger.error(f"❌ Error creating super admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_superadmin.py <email> <password>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    success = create_superadmin(email, password)
    sys.exit(0 if success else 1)