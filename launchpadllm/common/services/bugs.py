from typing import List, Optional

from launchpadllm.common.db.base import ConnectionProvider
from launchpadllm.common.db.bugs import BugsRepository
from launchpadllm.common.models.bugs import Bug, BugComment
from launchpadllm.common.services.base import Service
from launchpadllm.common.services.texts import TextsService


class BugsService(Service):

    def __init__(
        self,
        connection_provider: ConnectionProvider,
        bugs_repository: BugsRepository,
        texts_service: TextsService,
    ):
        super().__init__(connection_provider)
        self.bugs_repository = bugs_repository
        self.texts_service = texts_service

    async def process_launchpad_bug(self, b) -> Optional[Bug]:
        bug = await self.bugs_repository.find_by_id(b.bug.id)
        if not bug or bug.date_last_updated < b.bug.date_last_updated:
            title_text = await self.texts_service.create(b.bug.title)
            description_text = await self.texts_service.create(b.bug.description)
            if not bug:
                # bug is new
                await self.bugs_repository.create(
                    Bug(
                        id=b.bug.id,
                        date_created=b.bug.date_created,
                        date_last_updated=b.bug.date_last_updated,
                        web_link=b.bug.web_link,
                        title_id=title_text.id,
                        description_id=description_text.id,
                    )
                )
            else:
                # update the bug
                await self.texts_service.delete(bug.title_id)
                await self.texts_service.delete(bug.description_id)
                bug.title_id = title_text.id
                bug.description_id = description_text.id
                bug.date_last_updated = b.bug.date_last_updated
                await self.bugs_repository.update(bug)
            await self.delete_comments(b.bug.id)
            # skip the first, always equal to the description
            first = True
            for m in b.bug.messages:
                if first:
                    first = False
                    continue
                await self.add_comment(b.bug.id, m.content)

    async def delete_comments(self, bug_id: int) -> None:
        # embeddings and texts are cascaded
        await self.bugs_repository.delete_comments(bug_id)

    async def add_comment(self, bug_id: int, content: str) -> BugComment:
        comment_text = await self.texts_service.create(content)
        return await self.bugs_repository.add_comment(
            BugComment(
                id=await self.bugs_repository.get_next_comment_id(),
                bug_id=bug_id,
                text_id=comment_text.id,
            )
        )

    async def find_bug_by_text_id(self, text_id: int) -> Optional[Bug]:
        return await self.bugs_repository.find_by_text_id(text_id)

    async def get_bug_comments(self, bug_id: int) -> List[BugComment]:
        return await self.bugs_repository.find_bug_comments(bug_id)
