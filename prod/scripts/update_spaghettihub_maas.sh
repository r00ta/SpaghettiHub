#!/bin/bash

set -e

REPO_DIR="/tmp/maas-mirror"

# Clone if repo doesn't exist
if [ ! -d "$REPO_DIR" ]; then
    git clone git@github.com:SpaghettiHub/maas.git "$REPO_DIR"
    cd "$REPO_DIR"
    git remote add lp https://git.launchpad.net/maas
    git remote update
else
    cd "$REPO_DIR"
fi

# Fetch latest changes
git fetch lp
git fetch origin

# Create a temporary branch based on origin/master
git checkout -B tmp-origin origin/master

# Rebase lp/master onto origin/master, one commit at a time
git rebase --onto tmp-origin origin/master lp/master

# Now push each commit one by one
while [ "$(git rev-list tmp-origin..HEAD | wc -l)" -gt 0 ]; do
    # Get the next commit hash
    NEXT_COMMIT=$(git rev-list --reverse tmp-origin..HEAD | head -n 1)

    # Checkout that commit
    git checkout "$NEXT_COMMIT"

    # Push it to origin/master
    git push origin HEAD:master

    # Update tmp-origin to this commit
    git branch -f tmp-origin "$NEXT_COMMIT"
done

# Switch back to master (or main) and delete tmp-origin
git checkout master
git branch -D tmp-origin