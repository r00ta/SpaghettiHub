# Development

This document contains the instructions to setup your environment for development 

## Environment

Install LXD

```
sudo snap install lxd --channel=latest/stable
sudo lxd init --auto
```

Launch a new LXD container with 

```sh
lxc launch ubuntu:22.04 spaghettihub
```

Login into the container 

```sh
lxc shell spaghettihub
su ubuntu
```

Clone this repository 
```sh
git clone https://github.com/r00ta/SpaghettiHub.git ~/
```

## Setup
```sh
cd ~/spaghettihub
sudo apt get make python3-venv
make setup-dev
```

Configure git (you might want to replace the hardcoded username/email in the makefile!)

```sh
make git-config
```

You can now start the temporal server

```sh
make dev-start-temporal
```

the temporal worker
```sh
spaghettihubworker --gh_token <gh_token>
```

and the server
```sh
spaghettihubserver
```

## Environment Variables

The following environment variables are used by the application:

- `GITHUB_TOKEN` (or `--gh_token` for worker): GitHub personal access token with repo permissions for API access

## Using the Mirror PR Comments Tool

The mirror PR comments tool allows you to mirror all open comments from a GitHub Pull Request to a Launchpad Merge Proposal.

### API Endpoint

`POST /v1/tools/mirror-pr-comments`

**Request Body:**
```json
{
  "github_pr_url": "https://github.com/owner/repo/pull/123",
  "launchpad_mp_url": "https://code.launchpad.net/~owner/project/+merge/456",
  "include_outdated": false,
  "include_review_states": false
}
```

**Response:**
```json
{
  "workflow_id": "mirror-pr-comments-<hash>",
  "status": "started"
}
```

**Options:**
- `include_outdated` (bool): Include outdated review comments (default: false)
- `include_review_states` (bool): Include review approval/rejection states as comments (default: false)

The tool will:
1. Fetch all issue comments and review comments from the GitHub PR
2. Deduplicate against already mirrored comments (idempotent)
3. Post new comments to the Launchpad MP
4. Record sync metadata in the database

Please note that some configurations are hardcoded. Contributions to make the code generic are more than welcome
