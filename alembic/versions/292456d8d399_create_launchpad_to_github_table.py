"""create launchpad_to_github_table

Revision ID: 292456d8d399
Revises: 5027467c966b
Create Date: 2024-05-07 22:17:05.471433

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.schema import CreateSequence, Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '292456d8d399'
down_revision: Union[str, None] = '5027467c966b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(CreateSequence(Sequence('launchpad_to_github_work_id_seq')))

    op.create_table(
        "launchpad_to_github_work",
        sa.Column("id", sa.Integer, server_default=sa.text(
            "nextval('launchpad_to_github_work_id_seq')"), primary_key=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_uuid", sa.String(64), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("github_url", sa.Text, nullable=True),
        sa.Column("launchpad_url", sa.Text, nullable=True),
    )


def downgrade() -> None:
    pass
