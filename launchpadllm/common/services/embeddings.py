
from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.db.embeddings import EmbeddingsRepository
from launchpadllm.common.models.embeddings import Embedding
from launchpadllm.common.models.texts import MyText
from launchpadllm.common.services.base import Service
from launchpadllm.common.services.texts import TextsService


class EmbeddingsService(Service):

    def __init__(
        self,
        connection_provider: ConnectionProvider,
        embeddings_repository: EmbeddingsRepository,
        texts_service: TextsService,
    ):
        super().__init__(connection_provider)
        self.embeddings_repository = embeddings_repository
        self.texts_service = texts_service

    async def generate_and_store_embedding(
        self, tokenizer, model, text: MyText
    ) -> Embedding:
        inputs = tokenizer(
            text.content, return_tensors="pt", truncation=True, padding=True
        )
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        embedding = embeddings.cpu().detach().numpy()[0].tobytes()
        return await self.embeddings_repository.create(
            Embedding(
                id=await self.embeddings_repository.get_next_id(),
                text_id=text.id,
                embedding=embedding,
            )
        )
