# scripts/debug_delete.py
"""Debug script to check soft delete implementation."""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, text
from app.database import AsyncSessionLocal
from app.models.hostel import Hostel
from app.models.room import Room, Bed
from app.models.tenant import TenantProfile
from app.models.user import User


async def check_soft_delete_columns():
    """Verify soft delete columns exist in database."""
    async with AsyncSessionLocal() as db:
        print("\n🔍 Checking database structure...\n")
        
        tables_to_check = [
            ('hostels', Hostel),
            ('rooms', Room),
            ('beds', Bed),
            ('tenant_profiles', TenantProfile),
            ('users', User)
        ]
        
        for table_name, model in tables_to_check:
            # Check if columns exist in DB
            query = text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND column_name IN ('is_deleted', 'deleted_at')
                ORDER BY column_name;
            """)
            
            result = await db.execute(query)
            columns = result.fetchall()
            
            print(f"📋 Table: {table_name}")
            if columns:
                for col in columns:
                    print(f"   ✅ {col[0]}: {col[1]}")
            else:
                print(f"   ❌ NO SOFT DELETE COLUMNS FOUND!")
            
            # Check model attributes
            has_is_deleted = hasattr(model, 'is_deleted')
            has_deleted_at = hasattr(model, 'deleted_at')
            
            print(f"   Model has is_deleted: {has_is_deleted}")
            print(f"   Model has deleted_at: {has_deleted_at}")
            print()


async def test_soft_delete_operation():
    """Test soft delete operation end-to-end."""
    async with AsyncSessionLocal() as db:
        print("\n🧪 Testing soft delete operation...\n")
        
        # Create a test room
        from app.repositories.room import RoomRepository
        from app.models.room import RoomType
        
        room_repo = RoomRepository(Room, db)
        
        # Create test room
        test_room = await room_repo.create({
            "hostel_id": 1,
            "number": "TEST999",
            "floor": 99,
            "room_type": RoomType.SINGLE,
            "capacity": 1,
            "description": "Test room for delete verification"
        })
        await db.commit()
        
        print(f"✅ Created test room: ID={test_room.id}")
        print(f"   is_deleted: {test_room.is_deleted}")
        print(f"   deleted_at: {test_room.deleted_at}")
        
        # Perform soft delete
        print(f"\n🗑️  Performing soft delete...")
        deleted = await room_repo.soft_delete(test_room.id)
        await db.commit()
        
        print(f"   Soft delete returned: {deleted}")
        
        # Check in database directly
        query = text(f"""
            SELECT id, number, is_deleted, deleted_at 
            FROM rooms 
            WHERE id = {test_room.id}
        """)
        result = await db.execute(query)
        row = result.fetchone()
        
        if row:
            print(f"\n📊 Database state after soft delete:")
            print(f"   ID: {row[0]}")
            print(f"   Number: {row[1]}")
            print(f"   is_deleted: {row[2]}")
            print(f"   deleted_at: {row[3]}")
            
            if row[2] is True:
                print(f"\n✅ SOFT DELETE WORKING IN DATABASE!")
            else:
                print(f"\n❌ SOFT DELETE NOT APPLIED IN DATABASE!")
        
        # Try to fetch with repository
        print(f"\n🔍 Testing repository get (should return None)...")
        refetched = await room_repo.get(test_room.id)
        
        if refetched is None:
            print(f"   ✅ Repository correctly filters soft-deleted records")
        else:
            print(f"   ❌ Repository returned soft-deleted record!")
            print(f"      is_deleted: {refetched.is_deleted}")
        
        # Cleanup
        await db.execute(text(f"DELETE FROM rooms WHERE id = {test_room.id}"))
        await db.commit()
        print(f"\n🧹 Cleaned up test data")


async def check_migration_status():
    """Check if soft delete migration has been applied."""
    async with AsyncSessionLocal() as db:
        print("\n📜 Checking migration history...\n")
        
        # Check alembic version
        query = text("SELECT version_num FROM alembic_version")
        try:
            result = await db.execute(query)
            version = result.scalar()
            print(f"✅ Current migration version: {version}")
        except Exception as e:
            print(f"❌ Error checking migration: {e}")
        
        # Check if soft delete columns exist in key tables
        critical_tables = ['hostels', 'rooms', 'beds', 'tenant_profiles', 'users']
        
        for table in critical_tables:
            query = text(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND column_name IN ('is_deleted', 'deleted_at')
            """)
            result = await db.execute(query)
            count = result.scalar()
            
            status = "✅" if count == 2 else "❌"
            print(f"{status} {table}: {count}/2 columns present")


async def fix_missing_columns():
    """Add missing soft delete columns if needed."""
    async with AsyncSessionLocal() as db:
        print("\n🔧 Checking and fixing missing columns...\n")
        
        tables = ['hostels', 'rooms', 'beds', 'tenant_profiles', 'users']
        
        for table in tables:
            # Check if is_deleted exists
            query = text(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND column_name = 'is_deleted'
            """)
            result = await db.execute(query)
            has_is_deleted = result.scalar() > 0
            
            if not has_is_deleted:
                print(f"❌ {table} missing is_deleted column")
                print(f"   Adding column...")
                await db.execute(text(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE
                """))
                print(f"   ✅ Added is_deleted column")
            else:
                print(f"✅ {table}.is_deleted exists")
            
            # Check if deleted_at exists
            query = text(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND column_name = 'deleted_at'
            """)
            result = await db.execute(query)
            has_deleted_at = result.scalar() > 0
            
            if not has_deleted_at:
                print(f"❌ {table} missing deleted_at column")
                print(f"   Adding column...")
                await db.execute(text(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE
                """))
                print(f"   ✅ Added deleted_at column")
            else:
                print(f"✅ {table}.deleted_at exists")
            
            print()
        
        await db.commit()
        print("✅ All columns checked/added")


async def main():
    """Run all diagnostic checks."""
    print("=" * 60)
    print("SOFT DELETE DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Step 1: Check migration status
    await check_migration_status()
    
    # Step 2: Check database structure
    await check_soft_delete_columns()
    
    # Step 3: Ask if we should fix
    print("\n" + "=" * 60)
    response = input("Do you want to add missing columns? (yes/no): ").strip().lower()
    
    if response == 'yes':
        await fix_missing_columns()
        print("\n✅ Columns added. Please restart your server.")
    
    # Step 4: Test operation
    print("\n" + "=" * 60)
    response = input("Do you want to test soft delete? (yes/no): ").strip().lower()
    
    if response == 'yes':
        await test_soft_delete_operation()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())