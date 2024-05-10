from typing import List

import numpy as np
from numpy.linalg import norm

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.db.embeddings import EmbeddingsRepository
from spaghettihub.common.models.bugs import (Bug, BugCommentWithScore,
                                             BugWithCommentsAndScores)
from spaghettihub.common.models.embeddings import Embedding
from spaghettihub.common.models.texts import MyText
from spaghettihub.common.services.base import Service
from spaghettihub.common.services.bugs import BugsService
from spaghettihub.common.services.texts import TextsService


class EmbeddingsCache:
    def __init__(self, tokenizer, model):
        self.cache: dict[int, np.ndarray] | None = None
        self.tokenizer = tokenizer
        self.model = model

    def get_cache(self) -> dict[int, np.ndarray] | None:
        return self.cache

    def set_cache(self, cache: dict[int, np.ndarray]) -> None:
        self.cache = cache

    def get_tokenizer(self):
        return self.tokenizer

    def get_model(self):
        return self.model


class EmbeddingsService(Service):

    def __init__(
        self,
        connection_provider: ConnectionProvider,
        embeddings_repository: EmbeddingsRepository,
        texts_service: TextsService,
        bugs_service: BugsService,
        embeddings_cache: EmbeddingsCache | None = None
    ):
        super().__init__(connection_provider)
        self.embeddings_repository = embeddings_repository
        self.texts_service = texts_service
        self.bugs_service = bugs_service
        self.embeddings_cache = embeddings_cache

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (norm(a) * norm(b))

    async def generate_and_store_embedding(
        self, tokenizer, model, text: MyText
    ) -> Embedding:
        embedding = await self.generate(tokenizer, model, text.content)
        return await self.embeddings_repository.create(
            Embedding(
                id=await self.embeddings_repository.get_next_id(),
                text_id=text.id,
                embedding=embedding.tobytes(),
            )
        )

    async def generate(self, tokenizer, model, content) -> np.ndarray:
        inputs = tokenizer(
            content, return_tensors="pt", truncation=True, padding=True
        )
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.cpu().detach().numpy()[0]

    async def find_similar_issues(self, search: str, limit: int) -> List[BugWithCommentsAndScores]:
        top_scores = []
        matching_issues = []
        embedding = await self.generate(self.embeddings_cache.get_tokenizer(), self.embeddings_cache.get_model(), search)
        if not self.embeddings_cache.get_cache():
            embeddings_cache_size = await self.embeddings_repository.list(1, 1)
            all_embeddings = await self.embeddings_repository.list(embeddings_cache_size.total, 1)
            self.embeddings_cache.set_cache(
                {
                    x.text_id: np.frombuffer(x.embedding, dtype=np.float32) for x in all_embeddings.items
                }
            )

        scores = sorted(
            ((self.cosine_similarity(embedding, e), text_id)
             for text_id, e in self.embeddings_cache.get_cache().items()),
            reverse=True
        )
        unique_bugs = set()
        unique_bugs_list = []
        for similarity, text_id in scores:
            bug = await self.bugs_service.find_bug_by_text_id(text_id)
            top_scores.append((text_id, str(similarity)))
            unique_bugs.add(bug.id)
            unique_bugs_list.append(bug)
            if len(unique_bugs) == limit:
                break

        text_id_to_score = {text_id: score for score, text_id in scores}
        for bug in unique_bugs_list:
            bug_comments = await self.bugs_service.get_bug_comments(bug.id)
            bug_with_score = BugWithCommentsAndScores(
                bug=bug,
                title_score=text_id_to_score[bug.title_id],
                description_score=text_id_to_score[bug.description_id],
                comments=[
                    BugCommentWithScore(
                        bug_comment=bug_comment,
                        score=text_id_to_score[bug_comment.text_id],
                    )
                    for bug_comment in bug_comments
                ]
            )
            matching_issues.append(bug_with_score)
        return matching_issues
