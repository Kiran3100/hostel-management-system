"""initial schema

Revision ID: fd6b0d40560a
Revises: 042b5a5213a5
Create Date: 2025-10-07 17:xx:xx.xxxxxx

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd6b0d40560a'
down_revision = '042b5a5213a5'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns as nullable first
    op.add_column('tenant_profiles', 
        sa.Column('is_deleted', sa.Boolean(), nullable=True)
    )
    op.add_column('tenant_profiles', 
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    
    # Set default value for existing rows
    op.execute("UPDATE tenant_profiles SET is_deleted = FALSE WHERE is_deleted IS NULL")
    
    # Now alter the column to be NOT NULL
    op.alter_column('tenant_profiles', 'is_deleted',
                    existing_type=sa.Boolean(),
                    nullable=False,
                    server_default=sa.text('false'))
    
    # Create index
    op.create_index(
        'idx_tenant_profiles_is_deleted', 
        'tenant_profiles', 
        ['is_deleted'], 
        unique=False
    )


def downgrade():
    # Remove index
    op.drop_index('idx_tenant_profiles_is_deleted', table_name='tenant_profiles')
    
    # Remove columns
    op.drop_column('tenant_profiles', 'deleted_at')
    op.drop_column('tenant_profiles', 'is_deleted')