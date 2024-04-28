# Basic semantic search for Launchpad issues

This is a work-in -progress utility that makes it easier for me to find relevant issues on Launchpad.

# Setup
```
python3 - m venv .venv
. .venv/bin/activate
pip3 install - r requirements.txt
```

# Running the tool
There are two modes of operation: updating the local database with texts, and semantic querying. If you don't specify the launchpad project name, the script will use `maas` as the default project.

### Updating
```
python3 lp.py -p <launchpad_project_name> update
```
The tool can be interrupted at any time. The first update may take a long time if there are many issues. Consecutive updates download only the changes.

### Querying
```
python3 lp.py -p <launchpad_project_name> search "<your query>" --limit 1
```
Limit is optional.

There's also a clunky web front-end that can be run using `python3 server.py`, which is easier than reading json output.

## How it works
The tool downloads all texts associated with all issues in a specified project and stores them in a local sqlite3 database. After the texts are downloaded, it calculates a vector embedding of each of these texts and stores them in the database as well. 
These vector embeddings have an interesting characteristic - they represent semantic meaning of the text, so similar texts should have similar embeddings. The tool uses cosine similarity as the measure of how close in meaning the query and each of the texts are,
and produces a list of issues with the highest similarities. This lets you query the issue database for e.g. "user confused about the UI", or "unexpected behavior related to storage provisioning" and get issues related to these queries, instead of
specifying the exact keywords in your searches.

## Status
This is a very early work-in-progress script, which has to meet two goals: be simple, and make searching issues more efficient for me.
