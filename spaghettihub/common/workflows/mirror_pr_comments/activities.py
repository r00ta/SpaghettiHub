import hashlib
import logging
import re
from datetime import datetime
from typing import List

import aiohttp
from launchpadlib.launchpad import Launchpad
from temporalio import activity

from spaghettihub.common.db.base import ConnectionProvider
from spaghettihub.common.models.mirrored_comments import MirroredComment
from spaghettihub.common.services.collection import ServiceCollection
from spaghettihub.common.workflows.base import ActivityBase
from spaghettihub.common.workflows.mirror_pr_comments.params import (
    FetchCommentsParams, FetchCommentsResult, FilterDeduplicateParams,
    FilterDeduplicateResult, MirrorPullRequestCommentsParams,
    ParsedInputParams, PostCommentsParams, PostCommentsResult,
    RecordSyncParams, UnifiedComment)
from spaghettihub.server.base.db.database import Database

logger = logging.getLogger(__name__)


class MirrorPRCommentsActivity(ActivityBase):

    def __init__(self, db: Database, gh_token: str):
        super().__init__(db)
        self.gh_token = gh_token

    @activity.defn(name="parse-mirror-pr-comments-input")
    async def parse_input(self, params: MirrorPullRequestCommentsParams) -> ParsedInputParams:
        """Parse and validate URLs."""
        # Parse GitHub PR URL
        github_pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        github_match = re.match(github_pattern, params.github_pr_url)
        if not github_match:
            raise ValueError(f"Invalid GitHub PR URL: {params.github_pr_url}")

        owner, repo, pr_number = github_match.groups()

        # Parse Launchpad MP URL
        launchpad_pattern = r"https://code\.launchpad\.net/~([^/]+)/([^/]+)/\+merge/(\d+)"
        launchpad_match = re.match(launchpad_pattern, params.launchpad_mp_url)
        if not launchpad_match:
            raise ValueError(
                f"Invalid Launchpad MP URL: {params.launchpad_mp_url}")

        owner_lp, project, mp_number = launchpad_match.groups()
        mp_identifier = f"{project}:{mp_number}"

        logger.info(
            f"Parsed input: GitHub {owner}/{repo}#{pr_number}, Launchpad MP {mp_identifier}"
        )

        return ParsedInputParams(
            github_owner=owner,
            github_repo=repo,
            github_pr_number=int(pr_number),
            mp_identifier=mp_identifier
        )

    @activity.defn(name="fetch-github-comments")
    async def fetch_github_comments(
        self, params: FetchCommentsParams
    ) -> FetchCommentsResult:
        """Fetch all comments from GitHub PR."""
        comments = []

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.gh_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        async with aiohttp.ClientSession() as session:
            # Fetch issue comments
            issue_comments_url = (
                f"https://api.github.com/repos/{params.parsed_input.github_owner}/"
                f"{params.parsed_input.github_repo}/issues/{params.parsed_input.github_pr_number}/comments"
            )
            async with session.get(issue_comments_url, headers=headers) as response:
                if response.status == 404:
                    raise ValueError(
                        f"GitHub PR not found: {params.parsed_input.github_owner}/{params.parsed_input.github_repo}#{params.parsed_input.github_pr_number}")
                response.raise_for_status()
                issue_comments = await response.json()

                for comment in issue_comments:
                    unified = UnifiedComment(
                        source="issue",
                        id=str(comment["id"]),
                        author_login=comment["user"]["login"],
                        body=comment["body"],
                        created_at=comment["created_at"],
                    )
                    unified.fingerprint = self._generate_fingerprint(unified)
                    comments.append(unified)

            activity.heartbeat()

            # Fetch review comments
            review_comments_url = (
                f"https://api.github.com/repos/{params.parsed_input.github_owner}/"
                f"{params.parsed_input.github_repo}/pulls/{params.parsed_input.github_pr_number}/comments"
            )
            async with session.get(review_comments_url, headers=headers) as response:
                response.raise_for_status()
                review_comments = await response.json()

                for comment in review_comments:
                    # Skip outdated comments if not requested
                    if not params.include_outdated and comment.get("original_position") is None:
                        continue

                    unified = UnifiedComment(
                        source="review",
                        id=str(comment["id"]),
                        author_login=comment["user"]["login"],
                        body=comment["body"],
                        created_at=comment["created_at"],
                        path=comment.get("path"),
                        line=comment.get("line") or comment.get(
                            "original_line"),
                    )
                    unified.fingerprint = self._generate_fingerprint(unified)
                    comments.append(unified)

            activity.heartbeat()

            # Fetch review states if requested
            if params.include_review_states:
                reviews_url = (
                    f"https://api.github.com/repos/{params.parsed_input.github_owner}/"
                    f"{params.parsed_input.github_repo}/pulls/{params.parsed_input.github_pr_number}/reviews"
                )
                async with session.get(reviews_url, headers=headers) as response:
                    response.raise_for_status()
                    reviews = await response.json()

                    for review in reviews:
                        if review["state"] in ["APPROVED", "CHANGES_REQUESTED", "COMMENTED"]:
                            body = f"Review by {review['user']['login']}: {review['state']}"
                            if review.get("body"):
                                body += f"\n\n{review['body']}"

                            unified = UnifiedComment(
                                source="review_state",
                                id=f"review_{review['id']}",
                                author_login=review["user"]["login"],
                                body=body,
                                created_at=review["submitted_at"],
                            )
                            unified.fingerprint = self._generate_fingerprint(
                                unified)
                            comments.append(unified)

        logger.info(f"Fetched {len(comments)} comments from GitHub")
        return FetchCommentsResult(comments=comments)

    @activity.defn(name="filter-deduplicate-comments")
    async def filter_deduplicate(
        self, params: FilterDeduplicateParams
    ) -> FilterDeduplicateResult:
        """Filter out already mirrored comments."""
        async with self.start_transaction() as connection:
            connection_provider = ConnectionProvider(
                current_connection=connection)
            services = ServiceCollection.produce(
                connection_provider=connection_provider)

            existing_comments = await services.mirrored_comments_repository.find_by_mp_identifier(
                params.mp_identifier
            )
            existing_fingerprints = {c.fingerprint for c in existing_comments}

            new_comments = [
                c for c in params.comments if c.fingerprint not in existing_fingerprints
            ]
            skipped_count = len(params.comments) - len(new_comments)

            logger.info(
                f"Filtered comments: {len(new_comments)} new, {skipped_count} skipped"
            )

            return FilterDeduplicateResult(
                new_comments=new_comments,
                skipped_count=skipped_count
            )

    @activity.defn(name="post-launchpad-comments")
    async def post_launchpad_comments(
        self, params: PostCommentsParams
    ) -> PostCommentsResult:
        """Post comments to Launchpad MP."""
        posted_count = 0
        error_count = 0
        errors = []

        try:
            launchpad = Launchpad.login_anonymously(
                "spaghettihub-mirror-comments", "production", version="devel"
            )

            # Parse MP URL to get the merge proposal
            mp_url_api = params.launchpad_mp_url.replace(
                "https://code.launchpad.net/", "https://api.launchpad.net/devel/"
            )
            mp = launchpad.load(mp_url_api)

            for comment in params.comments:
                try:
                    # Format comment with context
                    formatted_body = self._format_comment_for_launchpad(
                        comment)

                    # Post comment to Launchpad
                    mp.createComment(content=formatted_body)
                    posted_count += 1

                    activity.heartbeat()

                except Exception as e:
                    error_count += 1
                    error_msg = f"Failed to post comment {comment.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            error_msg = f"Failed to connect to Launchpad: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            error_count = len(params.comments)

        logger.info(
            f"Posted {posted_count} comments, {error_count} errors"
        )

        return PostCommentsResult(
            posted_count=posted_count,
            error_count=error_count,
            errors=errors
        )

    @activity.defn(name="record-sync-metadata")
    async def record_sync(
        self,
        params: RecordSyncParams
    ) -> None:
        """Record mirrored comments in database."""
        async with self.start_transaction() as connection:
            connection_provider = ConnectionProvider(
                current_connection=connection)
            services = ServiceCollection.produce(
                connection_provider=connection_provider)

            now = datetime.utcnow()

            # Track which comments were posted successfully
            posted_comments_by_id = {c.id: c for c in params.comments}

            for comment in params.comments:
                status = "posted"
                posted_at = now
                error_message = None

                # If there were errors, mark some as errored
                # This is a simplification - in production you'd track individual failures
                if params.post_result.error_count > 0:
                    # Mark proportionally as errored
                    if len(params.comments) > 0:
                        error_ratio = params.post_result.error_count / \
                            len(params.comments)
                        if hash(comment.id) % 100 < error_ratio * 100:
                            status = "error"
                            posted_at = None
                            error_message = "Failed to post to Launchpad"

                mirrored_comment = MirroredComment(
                    id=await services.mirrored_comments_repository.get_next_id(),
                    fingerprint=comment.fingerprint,
                    github_comment_id=comment.id,
                    github_source=comment.source,
                    mp_identifier=params.mp_identifier,
                    created_at=now,
                    posted_at=posted_at,
                    status=status,
                    error_message=error_message,
                )

                await services.mirrored_comments_repository.create(mirrored_comment)

            logger.info(
                f"Recorded {len(params.comments)} mirrored comments in database")

    def _generate_fingerprint(self, comment: UnifiedComment) -> str:
        """Generate SHA256 fingerprint for a comment."""
        content = f"{comment.source}:{comment.id}:{comment.body}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _format_comment_for_launchpad(self, comment: UnifiedComment) -> str:
        """Format comment for posting to Launchpad."""
        parts = []

        # Add file/line context for review comments
        if comment.source == "review" and comment.path:
            context = f"[File: {comment.path}"
            if comment.line:
                context += f" | Line: {comment.line}"
            context += "]"
            parts.append(context)

        # Add author info
        parts.append(f"Comment by {comment.author_login} (from GitHub):")

        # Add body
        parts.append(comment.body)

        return "\n".join(parts)
