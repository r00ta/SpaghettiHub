import asyncio
import multiprocessing
import time

from sqlalchemy.ext.asyncio import create_async_engine
from transformers import AutoModel, AutoTokenizer

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.services.collection import ServiceCollection


class EmbeddingWorker(multiprocessing.Process):
    def __init__(self, dsn, queue, daemon=True):
        super().__init__(daemon=daemon)
        self.text_queue = queue
        self.dsn = dsn

    async def process_embedding(self, model, tokenizer, engine, connection_provider, services, text):
        async with engine.connect() as conn:
            async with conn.begin():
                connection_provider.current_connection = conn
                await services.embeddings_service.generate_and_store_embedding(
                    tokenizer, model, text
                )

    async def _run(self):
        model = AutoModel.from_pretrained("BAAI/bge-large-en-v1.5")
        tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
        engine = create_async_engine(self.dsn)
        connection_provider = ConnectionProvider(current_connection=None)
        services = ServiceCollection.produce(connection_provider)

        while True:
            while not self.text_queue.empty():
                text = self.text_queue.get()
                await self.process_embedding(model, tokenizer, engine, connection_provider, services, text)

            await asyncio.sleep(0.5)  # Avoid unnecessary clock cycles

    def run(self):
        asyncio.run(self._run())
