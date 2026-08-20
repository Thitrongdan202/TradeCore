"""reversible passwords

Revision ID: 6a1214436e41
Revises: fb89c2190ceb
Create Date: 2026-08-20 17:34:23.770913+00:00

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a1214436e41'
down_revision: Union[str, None] = 'fb89c2190ceb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column
    op.alter_column('users', 'hashed_password', new_column_name='encrypted_password')
    
    # Import security dynamically since this script needs to use the key from environment
    # Note: the key needs to be available when migrating
    import os
    from cryptography.fernet import Fernet
    key = os.getenv("TRADECORE_PASSWORD_ENCRYPTION_KEY")
    if not key:
        raise ValueError("TRADECORE_PASSWORD_ENCRYPTION_KEY environment variable is required to run this migration")
        
    fernet = Fernet(key.encode('utf-8'))
    default_pass = fernet.encrypt(b"admin123").decode('utf-8')
    
    # Reset passwords so users can login (we don't know the plain passwords for old bcrypt hashes)
    op.execute(
        sa.text(f"UPDATE users SET encrypted_password = '{default_pass}'")
    )


def downgrade() -> None:
    op.alter_column('users', 'encrypted_password', new_column_name='hashed_password')

