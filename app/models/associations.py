"""Association tables for many-to-many relationships."""

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.database import Base

# User-Hostel association table (many-to-many)
# Admins can manage multiple hostels, and hostels can have multiple admins
user_hostel_association = Table(
    'user_hostel_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('hostel_id', Integer, ForeignKey('hostels.id', ondelete='CASCADE'), primary_key=True, nullable=False),
)