# scripts/fix_soft_delete_simple.py
"""Simple script to add soft delete columns directly."""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import AsyncSessionLocal


async def fix_database():
    """Add soft delete columns to all tables."""
    print("\n🔧 FIXING DATABASE - Adding Soft Delete Columns\n")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            tables = ['hostels', 'rooms', 'beds', 'tenant_profiles', 'users']
            
            for table in tables:
                print(f"\n📋 Processing table: {table}")
                
                # Check if is_deleted exists
                check_query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name IN ('is_deleted', 'deleted_at')
                """)
                
                result = await db.execute(check_query)
                existing_columns = [row[0] for row in result.fetchall()]
                
                # Add is_deleted if missing
                if 'is_deleted' not in existing_columns:
                    print(f"   ➕ Adding is_deleted column...")
                    await db.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE
                    """))
                    print(f"   ✅ Added is_deleted")
                else:
                    print(f"   ✅ is_deleted already exists")
                
                # Add deleted_at if missing
                if 'deleted_at' not in existing_columns:
                    print(f"   ➕ Adding deleted_at column...")
                    await db.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE
                    """))
                    print(f"   ✅ Added deleted_at")
                else:
                    print(f"   ✅ deleted_at already exists")
                
                # Create index for performance
                print(f"   ➕ Creating index...")
                await db.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table}_is_deleted 
                    ON {table}(is_deleted)
                """))
                print(f"   ✅ Index created")
            
            await db.commit()
            
            print("\n" + "=" * 60)
            print("✅ ALL TABLES FIXED SUCCESSFULLY!")
            print("=" * 60)
            
            # Verify the fix
            print("\n🔍 VERIFICATION:")
            for table in tables:
                verify_query = text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name IN ('is_deleted', 'deleted_at')
                    ORDER BY column_name
                """)
                
                result = await db.execute(verify_query)
                columns = result.fetchall()
                
                if len(columns) == 2:
                    print(f"   ✅ {table}: {columns[0][0]} ({columns[0][1]}), {columns[1][0]} ({columns[1][1]})")
                else:
                    print(f"   ❌ {table}: MISSING COLUMNS!")
            
            print("\n" + "=" * 60)
            print("NEXT STEPS:")
            print("=" * 60)
            print("1. Restart your FastAPI server")
            print("2. Test delete operation in Swagger")
            print("3. Check PostgreSQL to verify records are marked as deleted")
            print("\nTest command:")
            print("SELECT id, number, is_deleted, deleted_at FROM rooms LIMIT 5;")
            print("=" * 60 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await db.rollback()
            import traceback
            traceback.print_exc()
            return False
    
    return True


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will modify your database structure!")
    print("Make sure you have a backup if needed.\n")
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        success = asyncio.run(fix_database())
        if success:
            print("\n🎉 Database fixed! Restart your server and test.")
            sys.exit(0)
        else:
            print("\n❌ Fix failed. Check errors above.")
            sys.exit(1)
    else:
        print("\n❌ Cancelled.")
        sys.exit(0)