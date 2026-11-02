"""Initial BorrowHub relational schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-31 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

from backend.app.core.database import Base
import backend.app.models  # Load all models

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    pass
