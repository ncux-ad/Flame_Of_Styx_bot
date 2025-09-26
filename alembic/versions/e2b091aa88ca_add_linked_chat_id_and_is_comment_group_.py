"""Add linked_chat_id and is_comment_group fields manually

Revision ID: e2b091aa88ca
Revises: 84664956487b
Create Date: 2025-09-13 03:00:12.757539

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2b091aa88ca"
down_revision: Union[str, Sequence[str], None] = "84664956487b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add linked_chat_id column
    op.add_column("channels", sa.Column("linked_chat_id", sa.Integer(), nullable=True))

    # Add is_comment_group column
    op.add_column(
        "channels", sa.Column("is_comment_group", sa.Boolean(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_comment_group column
    op.drop_column("channels", "is_comment_group")

    # Remove linked_chat_id column
    op.drop_column("channels", "linked_chat_id")
