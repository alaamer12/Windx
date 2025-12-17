"""merge_rbac_indexes

Revision ID: 95aa64961de9
Revises: add_rbac_performance_indexes, c281549c872f
Create Date: 2025-12-17 01:19:08.949089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95aa64961de9'
down_revision: Union[str, None] = ('add_rbac_performance_indexes', 'c281549c872f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
