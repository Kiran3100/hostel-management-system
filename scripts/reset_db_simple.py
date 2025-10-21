"""Force reset database by dropping and recreating it."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.database import Base
from app.models import *  # Import all models at module level


async def force_reset_database():
    """Force reset by dropping and recreating the database."""
    
    # Parse connection string to get database name and base URL
    db_url = str(settings.database_url)
    db_name = db_url.split('/')[-1]
    base_url = db_url.rsplit('/', 1)[0]
    
    print(f"\n🗑️  Force resetting database: {db_name}")
    
    # Connect to postgres database (not our app database)
    postgres_url = f"{base_url}/postgres"
    engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")
    
    async with engine.connect() as conn:
        # Terminate existing connections
        print("   Terminating existing connections...")
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
        """))
        
        # Drop database
        print(f"   Dropping database {db_name}...")
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        
        # Create database
        print(f"   Creating database {db_name}...")
        await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    
    await engine.dispose()
    
    # Now create tables using SQLAlchemy
    print("\n✨ Creating tables...")
    
    app_engine = create_async_engine(db_url, echo=False)
    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await app_engine.dispose()
    
    print("\n✅ Database reset complete!")
    print(f"\nNext step:")
    print(f"  python scripts/seed.py")


if __name__ == "__main__":
    print("⚠️  WARNING: This will DELETE ALL DATA and recreate the database!")
    response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    
    if response == "yes":
        asyncio.run(force_reset_database())
        print("\n✅ Done! Now run: python scripts/seed.py")
    else:
        print("❌ Database reset cancelled.")
        sys.exit(0)