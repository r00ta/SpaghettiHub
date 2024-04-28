from sqlalchemy import (Column, DateTime, ForeignKey, Integer, LargeBinary,
                        MetaData, Table, Text)

from launchpadllm.common.db.sequences import (BugCommentSequence,
                                              EmbeddingSequence,
                                              MyTextSequence)

METADATA = MetaData()

MyTextTable = Table(
    "text",
    METADATA,
    Column("id", Integer, MyTextSequence, primary_key=True),
    Column("content", Text, nullable=False),
)

EmbeddingTable = Table(
    "embedding",
    METADATA,
    Column("id", Integer, EmbeddingSequence, primary_key=True),
    Column("text_id", Integer, ForeignKey("text.id", ondelete="CASCADE")),
    Column("embedding", LargeBinary, nullable=False),
)

BugTable = Table(
    "bug",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column("date_created", DateTime(timezone=True)),
    Column("date_last_updated", DateTime(timezone=True)),
    Column("web_link", Text, nullable=False),
    Column("title_id", Integer, ForeignKey("text.id", ondelete="CASCADE")),
    Column("description_id", Integer, ForeignKey("text.id", ondelete="CASCADE")),
)

BugCommentTable = Table(
    "bug_comment",
    METADATA,
    Column("id", Integer, BugCommentSequence, primary_key=True),
    Column("bug_id", Integer, ForeignKey("bug.id", ondelete="CASCADE")),
    Column("text_id", Integer, ForeignKey("text.id", ondelete="CASCADE")),
)

LastUpdateTable = Table(
    "last_update",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column("last_updated", DateTime(timezone=True)),
)
