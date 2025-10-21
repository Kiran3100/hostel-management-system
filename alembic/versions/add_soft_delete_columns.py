# alembic/versions/add_soft_delete_columns.py
"""add soft delete columns to all tables

Revision ID: add_soft_delete_001
Revises: 1d6c9e43a807
Create Date: 2025-10-09 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_soft_delete_001'
down_revision = '1d6c9e43a807'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add soft delete columns to all tables that need them."""
    
    tables = ['hostels', 'rooms', 'beds', 'tenant_profiles', 'users']
    
    for table in tables:
        # Add is_deleted column if it doesn't exist
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = 'is_deleted'
                ) THEN
                    ALTER TABLE {table} 
                    ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
                END IF;
            END $$;
        """)
        
        # Add deleted_at column if it doesn't exist
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = 'deleted_at'
                ) THEN
                    ALTER TABLE {table} 
                    ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """)
        
        # Create index on is_deleted for better performance
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = '{table}' AND indexname = 'idx_{table}_is_deleted'
                ) THEN
                    CREATE INDEX idx_{table}_is_deleted ON {table}(is_deleted);
                END IF;
            END $$;
        """)


def downgrade() -> None:
    """Remove soft delete columns."""
    
    tables = ['hostels', 'rooms', 'beds', 'tenant_profiles', 'users']
    
    for table in tables:
        # Drop index
        op.execute(f"""
            DROP INDEX IF EXISTS idx_{table}_is_deleted;
        """)
        
        # Drop columns
        op.execute(f"""
            ALTER TABLE {table} 
            DROP COLUMN IF EXISTS is_deleted,
            DROP COLUMN IF EXISTS deleted_at;
        """)