"""create user table

Revision ID: baf5839e8fee
Revises: 292456d8d399
Create Date: 2024-05-08 20:55:43.145273

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.schema import CreateSequence, Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'baf5839e8fee'
down_revision: Union[str, None] = '292456d8d399'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('user_auth_id_seq')))
    op.create_table(
        "user_auth",
        sa.Column("id", sa.Integer, server_default=sa.text(
            "nextval('user_auth_id_seq')"), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password", sa.Text, nullable=False),
    )


def downgrade() -> None:
    pass
