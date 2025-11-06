from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from spaghettihub.common.workflows.constants import TASK_QUEUE_NAME
from spaghettihub.common.workflows.mirror_pr_comments.params import (
    FetchCommentsParams, FetchCommentsResult, FilterDeduplicateParams,
    FilterDeduplicateResult, MirrorCommentsResult,
    MirrorPullRequestCommentsParams, ParsedInputParams, PostCommentsParams,
    PostCommentsResult, RecordSyncParams)

with workflow.unsafe.imports_passed_through():
    pass


@workflow.defn(name="mirror-pr-comments-workflow", sandboxed=False)
class MirrorPullRequestCommentsWorkflow:

    @workflow.run
    async def run(self, params: MirrorPullRequestCommentsParams) -> MirrorCommentsResult:
        """Main workflow to mirror PR comments to Launchpad MP."""
        try:
            # Parse and validate input
            parsed_input: ParsedInputParams = await workflow.execute_activity(
                "parse-mirror-pr-comments-input",
                params,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )

            # Fetch comments from GitHub
            fetch_result: FetchCommentsResult = await workflow.execute_activity(
                "fetch-github-comments",
                FetchCommentsParams(
                    parsed_input=parsed_input,
                    include_outdated=params.include_outdated,
                    include_review_states=params.include_review_states,
                ),
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(seconds=30),
                ),
            )

            # Filter and deduplicate
            filter_result: FilterDeduplicateResult = await workflow.execute_activity(
                "filter-deduplicate-comments",
                FilterDeduplicateParams(
                    comments=fetch_result.comments,
                    mp_identifier=parsed_input.mp_identifier,
                ),
                start_to_close_timeout=timedelta(seconds=60),
            )

            # Post new comments to Launchpad
            post_result: PostCommentsResult = PostCommentsResult(
                posted_count=0, error_count=0, errors=[]
            )

            if filter_result.new_comments:
                post_result = await workflow.execute_activity(
                    "post-launchpad-comments",
                    PostCommentsParams(
                        comments=filter_result.new_comments,
                        mp_identifier=parsed_input.mp_identifier,
                        launchpad_mp_url=params.launchpad_mp_url,
                    ),
                    start_to_close_timeout=timedelta(seconds=300),
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        initial_interval=timedelta(seconds=10),
                        maximum_interval=timedelta(seconds=60),
                    ),
                )

                # Record sync metadata
                await workflow.execute_activity(
                    "record-sync-metadata",
                    RecordSyncParams(
                        comments=filter_result.new_comments,
                        mp_identifier=parsed_input.mp_identifier,
                        post_result=post_result,
                    ),
                    start_to_close_timeout=timedelta(seconds=60),
                )

            return MirrorCommentsResult(
                fetched_count=len(fetch_result.comments),
                posted_count=post_result.posted_count,
                skipped_count=filter_result.skipped_count,
                error_count=post_result.error_count,
                errors=post_result.errors,
            )

        except Exception as e:
            workflow.logger.error(f"Workflow failed: {str(e)}")
            return MirrorCommentsResult(
                fetched_count=0,
                posted_count=0,
                skipped_count=0,
                error_count=1,
                errors=[str(e)],
            )
