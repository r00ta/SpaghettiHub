from sqlalchemy import (Column, DateTime, ForeignKey, Integer, LargeBinary,
                        MetaData, Table, Text)

from launchpadllm.common.db.sequences import (BugCommentSequence,
                                              EmbeddingSequence,
                                              MergeProposalsSequence,
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
    Column("description_id", Integer, ForeignKey(
        "text.id", ondelete="CASCADE")),
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

MergeProposalTable = Table(
    "merge_proposal",
    METADATA,
    Column("id", Integer, MergeProposalsSequence, primary_key=True),
    Column("date_merged", DateTime(timezone=True), nullable=False),
    Column("commit_message", Text, nullable=True),
    Column("source_git_path", Text, nullable=True),
    Column("target_git_path", Text, nullable=True),
    Column("registrant_name", Text, nullable=False),
    Column("web_link", Text, nullable=False),
)
