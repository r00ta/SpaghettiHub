"""add mirrored_comment table

Revision ID: d4f9a1b2c3e5
Revises: cea232fe4aef
Create Date: 2025-11-06 07:56:20.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.schema import CreateSequence, Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4f9a1b2c3e5'
down_revision: Union[str, None] = 'cea232fe4aef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('mirrored_comment_id_seq')))

    op.create_table(
        "mirrored_comment",
        sa.Column("id", sa.Integer, server_default=sa.text(
            "nextval('mirrored_comment_id_seq')"), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("github_comment_id", sa.String(64), nullable=False),
        sa.Column("github_source", sa.String(32), nullable=False),
        sa.Column("mp_identifier", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    op.create_unique_constraint(
        "uq_mirrored_comment_fingerprint",
        "mirrored_comment",
        ["fingerprint"]
    )

    op.create_index(
        "ix_mirrored_comment_mp_identifier",
        "mirrored_comment",
        ["mp_identifier"]
    )


def downgrade() -> None:
    pass
