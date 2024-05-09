"""create initial database for embeddings and merge proposals

Revision ID: 5027467c966b
Revises: 
Create Date: 2024-05-04 19:15:35.954494

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.schema import CreateSequence, Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5027467c966b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('text_id_seq')))
    op.execute(CreateSequence(Sequence('embedding_id_seq')))
    op.execute(CreateSequence(Sequence('bug_comment_id_seq')))
    op.execute(CreateSequence(Sequence('merge_proposals_id_seq')))

    op.create_table(
        "text",
        sa.Column("id", sa.Integer, server_default=sa.text(
            "nextval('text_id_seq')"), primary_key=True),
        sa.Column("content", sa.Text, nullable=False),
    )

    op.create_table(
        "embedding",
        sa.Column("id", sa.Integer, server_default=sa.text(
            "nextval('embedding_id_seq')"), primary_key=True),
        sa.Column("text_id", sa.Integer, sa.ForeignKey(
            "text.id", ondelete="CASCADE")),
        sa.Column("embedding", sa.LargeBinary, nullable=False),
    )

    op.create_table(
        "bug",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date_created", sa.DateTime(timezone=True)),
        sa.Column("date_last_updated", sa.DateTime(timezone=True)),
        sa.Column("web_link", sa.Text, nullable=False),
        sa.Column("title_id", sa.Integer, sa.ForeignKey(
            "text.id", ondelete="CASCADE")),
        sa.Column("description_id", sa.Integer, sa.ForeignKey(
            "text.id", ondelete="CASCADE")),
    )

    op.create_table(
        "bug_comment",
        sa.Column("id", sa.Integer, server_default=sa.text(
            "nextval('bug_comment_id_seq')"), primary_key=True),
        sa.Column("bug_id", sa.Integer, sa.ForeignKey(
            "bug.id")),
        sa.Column("text_id", sa.Integer, sa.ForeignKey(
            "text.id", ondelete="CASCADE")),
    )

    op.create_table(
        "last_update",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("last_updated", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "merge_proposal",
        sa.Column("id", sa.Integer, server_default=sa.text(
            "nextval('merge_proposals_id_seq')"), primary_key=True),
        sa.Column("date_merged", sa.DateTime(timezone=True), nullable=False),
        sa.Column("commit_message", sa.Text, nullable=True),
        sa.Column("source_git_path", sa.Text, nullable=False),
        sa.Column("target_git_path", sa.Text, nullable=False),
        sa.Column("registrant_name", sa.Text, nullable=False),
        sa.Column("web_link", sa.Text, nullable=False),
    )


def downgrade() -> None:
    pass
