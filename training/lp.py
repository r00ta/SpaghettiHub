import argparse
import pprint

import numpy as np
from launchpadlib.launchpad import Launchpad
from numpy.linalg import norm
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

CACHEDIR = "./cache"
BUG_STATES = [
    "New",
    "Triaged",
    "Confirmed",
    "In Progress",
    "Fix Committed",
    "Fix Released",
    "Incomplete",
    "Invalid",
    "Won't Fix",
]


def cosine_similarity(a: float, b: float):
    return np.dot(a, b) / (norm(a) * norm(b))


class Search:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.embeddings = []
        self.load_embeddings()

    def load_embeddings(self):
        self.embeddings = list(self.storage.get_embeddings())

    def find_similar_texts(self, prompt: str):
        q = self.storage.generate_embedding(prompt)
        return sorted(
            ((cosine_similarity(q, e), i) for i, e in self.embeddings), reverse=True
        )

    def _add_scores(self, nested_dict, score_mapping):
        if "text_id" in nested_dict:
            nested_dict["score"] = str(score_mapping[nested_dict["text_id"]])
        else:
            for v in nested_dict.values():
                if isinstance(v, dict):
                    self._add_scores(v, score_mapping)
                elif isinstance(v, list):
                    for item in v:
                        self._add_scores(item, score_mapping)

    def find_similar_issues(self, prompt: str, limit: int=10):
        top_scores = []
        unique_issues = set()
        matching_issues = []
        scores = self.find_similar_texts(prompt)
        for similarity, text_id in scores:
            bug_id = self.storage.get_issue_related_with_text_id(text_id)
            top_scores.append((text_id, str(similarity)))
            unique_issues.add(bug_id)
            if len(unique_issues) == limit:
                break
        text_id_to_score = {text_id: score for score, text_id in scores}
        for bug_id in unique_issues:
            issue = self.storage.get_bug(bug_id)
            self._add_scores(issue, text_id_to_score)
            matching_issues.append(issue)
        return {"scores": top_scores, "issues": matching_issues}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Launchpad Bug Triage Assistant",
    )
    parser.add_argument(
        "-p", "--project", default="maas", help="Launchpad project name"
    )
    subparsers = parser.add_subparsers(dest="command", help="commands")
    update_parser = subparsers.add_parser(
        "update", help="Update the database with the latest issues"
    )
    search_parser = subparsers.add_parser(
        "search", help="Search the database for matching issues"
    )
    search_parser.add_argument("query", type=str, help="Search prompt")
    search_parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of returned results"
    )
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        exit(1)

    st = Storage(args.project)
    if args.command == "update":
        st.update_database()
    elif args.command == "search":
        searcher = Search(st)
        pprint.pprint(searcher.find_similar_issues(args.query, limit=args.limit))
    st.close()
