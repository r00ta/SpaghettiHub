from sqlalchemy import Sequence

MyTextSequence = Sequence("text_id_seq", start=1)
BugSequence = Sequence("bug_id_seq", start=1)
BugCommentSequence = Sequence("bug_comment_id_seq", start=1)
EmbeddingSequence = Sequence("embedding_id_seq", start=1)
MergeProposalsSequence = Sequence("merge_proposals_id_seq", start=1)
