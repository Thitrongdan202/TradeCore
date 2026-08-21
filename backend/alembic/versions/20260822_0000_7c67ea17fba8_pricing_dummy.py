"""dummy migration for pricing extensions

Revision ID: 7c67ea17fba8
Revises: 6a1214436e41
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7c67ea17fba8'
down_revision: Union[str, None] = '6a1214436e41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
