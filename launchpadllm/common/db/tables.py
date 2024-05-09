from sqlalchemy import (Column, DateTime, ForeignKey, Integer, LargeBinary,
                        MetaData, String, Table, Text)

from launchpadllm.common.db.sequences import (BugCommentSequence,
                                              EmbeddingSequence,
                                              LaunchpadToGithubWorkSequence,
                                              MergeProposalsSequence,
                                              MyTextSequence, UsersSequence)

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

LaunchpadToGithubWorkTable = Table(
    "launchpad_to_github_work",
    METADATA,
    Column("id", Integer, LaunchpadToGithubWorkSequence, primary_key=True),
    Column("requested_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("request_uuid", String(64), nullable=False),
    Column("status", String(64), nullable=False),
    Column("github_url", Text, nullable=True),
    Column("launchpad_url", Text, nullable=True),
)

UserTable = Table(
    "user_auth",
    METADATA,
    Column("id", Integer, UsersSequence, primary_key=True),
    Column("username", String(128), nullable=False),
    Column("password", Text, nullable=False)
)
