"""create maas continuous integration table

Revision ID: cea232fe4aef
Revises: baf5839e8fee
Create Date: 2024-05-08 20:55:43.145273

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.schema import CreateSequence, Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cea232fe4aef'
down_revision: Union[str, None] = 'baf5839e8fee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('maas_id_seq')))
    op.create_table(
        "maas",
        sa.Column("id", sa.Integer, server_default=sa.text("nextval('maas_id_seq')"), primary_key=True),
        sa.Column("commit_sha", sa.String(64), nullable=False),
        sa.Column("commit_message", sa.Text, nullable=True),
        sa.Column("committer_username", sa.String(128), nullable=True),
        sa.Column("commit_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("continuous_delivery_test_deb_status", sa.String(64), nullable=True),
        sa.Column("continuous_delivery_test_snap_status", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    pass
